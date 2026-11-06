"""Typed StateTree object/class and soft reference parameters, inheritance and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree_references.json'
TEXTURE='/Engine/EngineResources/DefaultTexture.DefaultTexture'
TEXTURE_CLASS='/Script/Engine.Texture2D'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/state-trees/inspect',asset_path=path)
    def edit(path,method,route,**values):return call(method,'/state-trees/'+route,{'AssetPath':path}|values)
    def stable(s):return {k:v for k,v in s.items() if k not in ['affected_assets','selected_id','would_change','dry_run','saved','diagnostics','validation_compiled_copy']}
    paths=[];blueprints=[]
    def snapshots():return {p:inspect(p) for p in paths}
    def fields(path):return {f['name']:f for f in inspect(path)['parameters']['fields']}
    def reject(path,method,route,**values):
        before=snapshots();r=httpx.request(method,base+'/state-trees/'+route,json={'AssetPath':path}|values,timeout=180)
        assert r.status_code>=400,(r.status_code,r.text)
        assert snapshots()==before,'Rejected reference edit changed a source'
    def cleanup():
        for p in reversed(paths):call('POST','/assets/delete',{'AssetPath':p})
        for p in reversed(blueprints):call('POST','/assets/delete',{'AssetPath':p})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());paths.extend(saved['paths']);blueprints.extend(saved.get('blueprints',[]))
        if phase=='verify':
            for p in paths:
                s=inspect(p);assert stable(s)==saved['snapshots'][p],(p,s,saved['snapshots'][p])
                assert s['ready_to_run'] and not s['dirty'] and s['editor_hash']==s['compiled_hash']
            before=snapshots()
            for p in paths:
                v=call('GET','/state-trees/validate',asset_path=p);assert v['diagnostics'].startswith('success'),v
                assert snapshots()==before
            print('Cold typed reference constraints/paths, object/class bindings, linked overrides and clean compiled data: OK')
        cleanup();return
    assert not STATE.exists(),'Verify or clean prior reference fixture'
    keep=False
    try:
        def create(name):
            c=call('POST','/state-trees/create',{'AssetPath':'/Game/UE5MCP_Test/ST_Ref_'+name+'_'+uuid.uuid4().hex[:8]})
            paths.append(c['asset_path']);return c['asset_path'],c['states'][0]['id']
        leaf,root=create('Leaf');caller,cr=create('Caller')
        ids={}
        for name,typ,constraint,value in [('Resource','Object',TEXTURE_CLASS,TEXTURE),('ResourceClass','Class','/Script/CoreUObject.Object',TEXTURE_CLASS),('SoftResource','SoftObject',TEXTURE_CLASS,TEXTURE),('SoftResourceClass','SoftClass','/Script/CoreUObject.Object',TEXTURE_CLASS)]:
            ids[name]=edit(leaf,'POST','parameters',Name=name,ParameterType=typ,TypePath=constraint,bSetValue=True,Value=value)['selected_id']
            assert fields(leaf)[name]['reference_path']==value
        bp_package='/Game/UE5MCP_Test/BP_StateRef_'+uuid.uuid4().hex[:8]
        created_bp=call('POST','/blueprint',{'BpPath':bp_package,'ParentClass':'/Script/Engine.Actor'})
        bp=bp_package+'.'+bp_package.rsplit('/',1)[-1]
        blueprints.append(bp)
        call('POST','/blueprints/compile',{'BpPath':bp});call('POST','/assets/save',{'AssetPath':bp})
        bp_class=bp+'_C'
        for name,typ,constraint in [('GeneratedActorClass','Class','/Script/Engine.Actor'),('SoftGeneratedActorClass','SoftClass','/Script/Engine.Actor'),('GeneratedConstraint','Class',bp_class)]:
            edit(leaf,'POST','parameters',Name=name,ParameterType=typ,TypePath=constraint,bSetValue=True,Value=bp_class)
            assert fields(leaf)[name]['reference_path']==bp_class
        a=edit(leaf,'POST','states',ParentId=root,Name='A')['selected_id'];b=edit(leaf,'POST','states',ParentId=root,Name='B')['selected_id']
        for g in [a,b]:
            edit(leaf,'POST','nodes',StateId=g,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'Duration':'0.02','RandomDeviation':'0'})
            edit(leaf,'POST','transitions',StateId=g)
        edit(leaf,'POST','nodes',StateId=a,Kind='enter_condition',StructPath='/Script/StateTreeModule.StateTreeObjectIsChildOfClassCondition',Bindings=[{'SourceId':'root','SourcePath':'Resource','TargetId':'$new','TargetPath':'Object'},{'SourceId':'root','SourcePath':'ResourceClass','TargetId':'$new','TargetPath':'Class'}])
        link=edit(caller,'POST','states',ParentId=cr,Name='Call',StateType='LinkedAsset',LinkedAssetPath=leaf)['selected_id']
        edit(caller,'POST','transitions',StateId=link)
        before=snapshots();edit(leaf,'PATCH','parameters',ItemId=ids['Resource'],bSetValue=True,Value='None',bDryRun=True);assert snapshots()==before
        assert not edit(leaf,'PATCH','parameters',ItemId=ids['Resource'],bSetValue=True,Value=TEXTURE)['would_change']
        reject(leaf,'PATCH','parameters',ItemId=ids['Resource'],bSetValue=True,Value='/Script/Engine.Material')
        reject(leaf,'PATCH','parameters',ItemId=ids['SoftResource'],bSetValue=True,Value='/Game/UE5MCP_Test/Missing.Missing')
        reject(leaf,'POST','parameters',Name='WrongClass',ParameterType='Class',TypePath='/Script/Engine.Actor',bSetValue=True,Value=TEXTURE_CLASS)
        reject(leaf,'POST','parameters',Name='WrongSoftClass',ParameterType='SoftClass',TypePath='/Script/Engine.Actor',bSetValue=True,Value=TEXTURE_CLASS)
        reject(leaf,'PATCH','parameters',ItemId=ids['Resource'],bSetValue=True,Value=TEXTURE+':Subobject')
        edit(leaf,'PATCH','parameters',ItemId=ids['ResourceClass'],bSetValue=True,Value='/Script/Engine.Material')
        call('POST','/editor/transactions/undo');assert snapshots()==before
        call('POST','/editor/transactions/redo');assert fields(leaf)['ResourceClass']['reference_path']=='/Script/Engine.Material'
        call('POST','/editor/transactions/undo')
        edit(caller,'PATCH','parameters',StateId=link,ItemId=ids['Resource'],bSetValue=True,Value='None')
        edit(leaf,'PATCH','parameters',ItemId=ids['Resource'],bSetName=True,Name='RenamedResource')
        linked=next(s for s in inspect(caller)['states'] if s['id']==link)
        assert next(f for f in linked['parameters']['fields'] if f['id']==ids['Resource'])['reference_path']==''
        edit(caller,'POST','parameters/reset',StateId=link,ItemId=ids['Resource'],bConfirm=True)
        linked=next(s for s in inspect(caller)['states'] if s['id']==link)
        assert next(f for f in linked['parameters']['fields'] if f['id']==ids['Resource'])['reference_path']==TEXTURE
        edit(leaf,'PATCH','parameters',ItemId=ids['SoftResource'],bSetValue=True,Value='None')
        assert fields(leaf)['SoftResource']['reference_path']==''
        call('POST','/editor/transactions/undo');assert fields(leaf)['SoftResource']['reference_path']==TEXTURE
        before=snapshots();v=call('GET','/state-trees/validate',asset_path=leaf);assert v['diagnostics'].startswith('success') and snapshots()==before
        edit(leaf,'POST','compile',bSave=True);snapshot=snapshots()
        for p,s in snapshot.items():assert not s['dirty'] and s['editor_hash']==s['compiled_hash'],(p,s)
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'blueprints':blueprints,'snapshots':{p:stable(s) for p,s in snapshot.items()}},indent=2));keep=True
        print('Typed object/class/soft references, paths/constraints, bindings, null/rename, caller overrides/reset, guards, transactions and save: OK')
    finally:
        if not keep:cleanup()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
