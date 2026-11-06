"""Cross-asset native StateTree dependencies, transactions, isolation and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree_assets.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/state-trees/inspect',asset_path=path)
    def edit(path,method,route,**values):return call(method,'/state-trees/'+route,{'AssetPath':path}|values)
    def stable(s):return {k:v for k,v in s.items() if k not in ['affected_assets','selected_id','would_change','dry_run','saved','diagnostics','validation_compiled_copy']}
    paths=[]
    def snapshots():return {p:inspect(p) for p in paths}
    def state(path,g):return next(s for s in inspect(path)['states'] if s['id']==g)
    def reject(path,method,route,**values):
        before=snapshots();r=httpx.request(method,base+'/state-trees/'+route,json={'AssetPath':path}|values,timeout=180)
        assert r.status_code>=400,(r.status_code,r.text)
        assert snapshots()==before,'Rejected dependency edit changed a source'
    def cleanup():
        for p in reversed(paths):call('POST','/assets/delete',{'AssetPath':p})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());paths.extend(saved['paths'])
        if phase=='verify':
            for p in paths:
                s=inspect(p);assert stable(s)==saved['snapshots'][p],(p,s,saved['snapshots'][p])
                assert s['ready_to_run'] and not s['dirty'] and s['editor_hash']==s['compiled_hash'],s
            before=snapshots()
            for p in paths:
                v=call('GET','/state-trees/validate',asset_path=p);assert v['diagnostics'].startswith('success'),v
                assert snapshots()==before,'Cold dependency validation changed source assets'
            print('Cold linked asset references, inherited/overridden fields, bindings, compiled hashes and clean packages: OK')
        cleanup();return
    assert not STATE.exists(),'Verify or clean prior cross-asset fixture'
    keep=False
    try:
        def create(name,schema=None):
            values={'AssetPath':'/Game/UE5MCP_Test/ST_Asset_'+name+'_'+uuid.uuid4().hex[:8]}
            if schema:values['SchemaPath']=schema
            c=call('POST','/state-trees/create',values);paths.append(c['asset_path']);return c['asset_path'],c['states'][0]['id']
        leaf,lr=create('Leaf');middle,mr=create('Middle');outer,ar=create('Outer')
        field=edit(leaf,'POST','parameters',Name='Duration',ParameterType='Float',bSetValue=True,Value='0.03')['selected_id']
        work=edit(leaf,'POST','states',Name='Leaf task',ParentId=lr)['selected_id']
        edit(leaf,'POST','nodes',StateId=work,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'RandomDeviation':'0'},Bindings=[{'SourceId':'root','SourcePath':'Duration','TargetId':'$new','TargetPath':'Duration'}])
        edit(leaf,'POST','transitions',StateId=work,TargetType='Succeeded')
        def link(parent,root,child):
            g=edit(parent,'POST','states',Name='Call',ParentId=root,StateType='LinkedAsset',LinkedAssetPath=child)['selected_id']
            edit(parent,'POST','transitions',StateId=g,TargetType='Succeeded');return g
        mc=link(middle,mr,leaf);ac=link(outer,ar,middle)
        before=snapshots();v=edit(leaf,'PATCH','parameters',ItemId=field,bSetValue=True,Value='0.16',bDryRun=True)
        assert set(v['affected_assets'])==set(paths) and snapshots()==before
        v=call('GET','/state-trees/validate',asset_path=leaf);assert v['diagnostics'].startswith('success') and snapshots()==before
        changed=edit(leaf,'PATCH','parameters',ItemId=field,bSetValue=True,Value='0.16')
        assert set(changed['affected_assets'])==set(paths)
        assert state(middle,mc)['parameters']['fields'][0]['value'].startswith('0.16')
        after=snapshots();call('POST','/editor/transactions/undo');assert snapshots()==before
        call('POST','/editor/transactions/redo');assert snapshots()==after
        edit(middle,'PATCH','parameters',StateId=mc,ItemId=field,bSetValue=True,Value='0.08')
        assert field in state(middle,mc)['parameter_overrides']
        edit(leaf,'PATCH','parameters',ItemId=field,bSetName=True,Name='WaitSeconds')
        assert state(middle,mc)['parameters']['fields'][0]['name']=='WaitSeconds'
        assert state(middle,mc)['parameters']['fields'][0]['value'].startswith('0.08')
        extra=edit(leaf,'POST','parameters',Name='Unused',ParameterType='Bool')['selected_id']
        assert any(f['id']==extra for f in state(middle,mc)['parameters']['fields'])
        edit(leaf,'DELETE','parameters',ItemId=extra,bConfirm=True)
        assert not any(f['id']==extra for f in state(middle,mc)['parameters']['fields'])
        reject(leaf,'POST','states',Name='Cycle',ParentId=lr,StateType='LinkedAsset',LinkedAssetPath=outer)
        reject(leaf,'POST','states',Name='Self',ParentId=lr,StateType='LinkedAsset',LinkedAssetPath=leaf)
        reject(middle,'POST','states',Name='Child',ParentId=mc)
        reject(middle,'POST','parameters',StateId=mc,Name='Wrong',ParameterType='Bool')
        reject(middle,'POST','links',StateId=mc,LinkedAssetPath=outer,bConfirm=True)
        other,orr=create('Other')
        reject(middle,'POST','links',StateId=mc,LinkedAssetPath=other)
        before=snapshots();edit(middle,'POST','links',StateId=mc,LinkedAssetPath=other,bConfirm=True)
        assert state(middle,mc)['linked_asset']==other
        call('POST','/editor/transactions/undo');assert snapshots()==before
        # A schema mismatch is rejected before native compiler mutation.
        incompatible,_=create('AI','/Script/GameplayStateTreeModule.StateTreeAIComponentSchema')
        reject(outer,'POST','links',StateId=ac,LinkedAssetPath=incompatible,bConfirm=True)
        edit(middle,'POST','parameters/reset',StateId=mc,ItemId=field,bConfirm=True)
        assert not state(middle,mc)['parameter_overrides']
        call('POST','/editor/transactions/undo');assert field in state(middle,mc)['parameter_overrides']
        # Save on the dependency also saves transitive callers, not just the leaf.
        edit(leaf,'POST','compile',bSave=True)
        for p in [other,incompatible]:edit(p,'POST','compile',bSave=True)
        snapshot=snapshots()
        for p,s in snapshot.items():assert not s['dirty'] and s['editor_hash']==s['compiled_hash'],(p,s)
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'snapshots':{p:stable(s) for p,s in snapshot.items()}},indent=2));keep=True
        print('Linked asset creation/retarget, transitive affected callers, preview isolation, schema/cycle guards, overrides/rename/layout, undo/redo and graph save: OK')
    finally:
        if not keep:cleanup()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
