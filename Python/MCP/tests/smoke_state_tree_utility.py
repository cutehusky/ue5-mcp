"""Native utility considerations, bindings, weights and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree_utility.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/state-trees/inspect',asset_path=path)
    def edit(path,method,route,**values):return call(method,'/state-trees/'+route,{'AssetPath':path}|values)
    def stable(s):return {k:v for k,v in s.items() if k not in ['affected_assets','selected_id','would_change','dry_run','saved','diagnostics','validation_compiled_copy']}
    def state(path,g):return next(s for s in inspect(path)['states'] if s['id']==g)
    def reject(path,method,route,**values):
        before=inspect(path);r=httpx.request(method,base+'/state-trees/'+route,json={'AssetPath':path}|values,timeout=180)
        assert r.status_code>=400,(r.status_code,r.text)
        assert inspect(path)==before,'Rejected utility edit changed source'
    def cleanup(path):call('POST','/assets/delete',{'AssetPath':path});STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());path=saved['path']
        if phase=='verify':
            s=inspect(path);assert stable(s)==saved['snapshot'],(s,saved['snapshot'])
            assert s['ready_to_run'] and not s['dirty'] and s['editor_hash']==s['compiled_hash']
            before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
            assert v['diagnostics'].startswith('success') and inspect(path)==before
            print('Cold utility consideration IDs/settings/bindings, selection policy, weights and compiled data: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior utility fixture'
    path=None;keep=False
    try:
        c=call('POST','/state-trees/create',{'AssetPath':'/Game/UE5MCP_Test/ST_Utility_'+uuid.uuid4().hex[:8]})
        path=c['asset_path'];root=c['states'][0]['id']
        edit(path,'PATCH','states',StateId=root,Properties={'SelectionBehavior':'TrySelectChildrenWithHighestUtility'})
        a=edit(path,'POST','states',Name='A',ParentId=root)['selected_id'];b=edit(path,'POST','states',Name='B',ParentId=root)['selected_id']
        for g in [a,b]:
            edit(path,'POST','nodes',StateId=g,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'Duration':'0.02','RandomDeviation':'0'})
            edit(path,'POST','transitions',StateId=g)
        score=edit(path,'POST','parameters',Name='Score',ParameterType='Float',bSetValue=True,Value='0.8')['selected_id']
        ca=edit(path,'POST','nodes',StateId=a,Kind='consideration',StructPath='/Script/StateTreeModule.StateTreeConstantConsideration',Bindings=[{'SourceId':'root','SourcePath':'Score','TargetId':'$new','TargetPath':'Constant'}])['selected_id']
        cb=edit(path,'POST','nodes',StateId=b,Kind='consideration',StructPath='/Script/StateTreeModule.StateTreeConstantConsideration',InstanceProperties={'Constant':'0.4'})['selected_id']
        before=inspect(path)
        edit(path,'PATCH','nodes',StateId=b,Kind='consideration',ItemId=cb,InstanceProperties={'Constant':'0.9'},bDryRun=True);assert inspect(path)==before
        assert not edit(path,'PATCH','nodes',StateId=b,Kind='consideration',ItemId=cb,InstanceProperties={'Constant':'0.4'})['would_change']
        reject(path,'PATCH','nodes',StateId=b,Kind='consideration',ItemId=cb,InstanceProperties={'Constant':'1.1'})
        reject(path,'POST','nodes',StateId=b,Kind='consideration',StructPath='/Script/StateTreeModule.StateTreeDelayTask')
        edit(path,'PATCH','nodes',StateId=b,Kind='consideration',ItemId=cb,InstanceProperties={'Constant':'0.9'})
        call('POST','/editor/transactions/undo');assert stable(inspect(path))==stable(before)
        call('POST','/editor/transactions/redo');assert state(path,b)['considerations'][0]['instance_properties']['Constant'].startswith('0.9')
        edit(path,'PATCH','states',StateId=b,Properties={'Weight':'0.5'})
        assert state(path,b)['properties']['Weight'].startswith('0.5')
        call('POST','/editor/transactions/undo');assert state(path,b)['properties']['Weight'].startswith('1.')
        edit(path,'DELETE','nodes',StateId=a,Kind='consideration',ItemId=ca,bConfirm=True)
        assert not state(path,a)['considerations'] and inspect(path)['binding_count']==0
        call('POST','/editor/transactions/undo');assert state(path,a)['considerations'][0]['id']==ca and inspect(path)['binding_count']==1
        multiplier=edit(path,'POST','nodes',StateId=a,Kind='consideration',StructPath='/Script/StateTreeModule.StateTreeConstantConsideration',InstanceProperties={'Constant':'0.25'},Operand='Multiply')['selected_id']
        assert state(path,a)['considerations'][-1]['id']==multiplier
        assert state(path,a)['considerations'][-1]['operand']=='Multiply'
        after=stable(inspect(path))
        call('POST','/editor/transactions/undo');assert len(state(path,a)['considerations'])==1
        call('POST','/editor/transactions/redo');assert stable(inspect(path))==after
        before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
        assert v['diagnostics'].startswith('success') and inspect(path)==before
        edit(path,'POST','compile',bSave=True);snapshot=inspect(path)
        assert not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash']
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('Utility consideration CRUD, bindings, weights, guards, dry-run/no-op, undo/redo and save: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
