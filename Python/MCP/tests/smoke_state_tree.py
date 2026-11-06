"""Native StateTree authoring, compile preflight, transactions and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/state-trees/inspect',asset_path=path)
    def edit(path,method,route,**values):return call(method,'/state-trees/'+route,{'AssetPath':path}|values)
    def stable(s):return {k:v for k,v in s.items() if k not in ['affected_assets','selected_id','would_change','dry_run','saved','diagnostics','validation_compiled_copy']}
    def state(s,g):return next(v for v in s['states'] if v['id']==g)
    def reject(path,method,route,**values):
        before=inspect(path);r=httpx.request(method,base+'/state-trees/'+route,json={'AssetPath':path}|values,timeout=180)
        assert r.status_code>=400,(r.status_code,r.text)
        assert inspect(path)==before,'Rejected StateTree edit changed source'
    def cleanup(path):call('POST','/assets/delete',{'AssetPath':path});STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());path=saved['path']
        if phase=='verify':
            snapshot=inspect(path);assert stable(snapshot)==saved['snapshot'],(snapshot,saved['snapshot'])
            assert snapshot['ready_to_run'] and not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash'],snapshot
            before=inspect(path);validation=call('GET','/state-trees/validate',asset_path=path)
            assert validation['validation_compiled_copy'] and validation['diagnostics'].startswith('success'),validation
            assert inspect(path)==before
            print('Cold StateTree states/IDs/order, native tasks/conditions/transitions, compiled data/hash and clean source: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior StateTree fixture'
    path=None;keep=False
    try:
        package='/Game/UE5MCP_Test/ST_HTTP_'+uuid.uuid4().hex[:8]
        dry=call('POST','/state-trees/create',{'AssetPath':package,'bDryRun':True});assert dry['dry_run'] and dry['ready_to_run']
        created=call('POST','/state-trees/create',{'AssetPath':package});path=created['asset_path'];root=created['states'][0]['id']
        a=edit(path,'POST','states',ParentId=root,Name='A')['selected_id'];b=edit(path,'POST','states',ParentId=root,Name='B')['selected_id']
        task=edit(path,'POST','nodes',StateId=a,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'Duration':'0.03','RandomDeviation':'0'})['selected_id']
        edit(path,'POST','nodes',StateId=b,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'Duration':'0.02'})
        condition=edit(path,'POST','nodes',StateId=a,Kind='enter_condition',StructPath='/Script/StateTreeModule.StateTreeRandomCondition',InstanceProperties={'Threshold':'1'})['selected_id']
        ab=edit(path,'POST','transitions',StateId=a,TargetType='GotoState',TargetStateId=b)['selected_id']
        done=edit(path,'POST','transitions',StateId=b,TargetType='Succeeded')['selected_id']
        before=inspect(path)
        edit(path,'PATCH','nodes',StateId=a,ItemId=task,InstanceProperties={'Duration':'0.1'},bDryRun=True);assert inspect(path)==before
        assert not edit(path,'PATCH','nodes',StateId=a,ItemId=task,InstanceProperties={'Duration':'0.03'})['would_change']
        reject(path,'PATCH','nodes',StateId=a,ItemId=task,InstanceProperties={'Duration':'-1'})
        reject(path,'POST','move',StateId=root,ParentId=a)
        reject(path,'DELETE','states',StateId=b,bConfirm=True)
        reject(path,'POST','transitions',StateId=a,TargetType='GotoState',TargetStateId=uuid.uuid4().hex)
        reject(path,'POST','transitions',StateId=a,Trigger='OnEvent',EventTag='UE5MCP.NotRegistered.Fixture')
        reject(path,'POST','transitions',StateId=a,Delay=26)
        reject(path,'POST','nodes',StateId=a,StructPath='/Script/CoreUObject.Vector')
        reject(path,'DELETE','nodes',StateId=a,ItemId=task)
        before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
        assert v['diagnostics'].startswith('success') and inspect(path)==before
        edit(path,'PATCH','nodes',StateId=a,ItemId=task,InstanceProperties={'Duration':'0.2'})
        assert state(inspect(path),a)['tasks'][0]['instance_properties']['Duration'].startswith('0.2')
        call('POST','/editor/transactions/undo');assert state(inspect(path),a)['tasks'][0]['instance_properties']['Duration'].startswith('0.03')
        call('POST','/editor/transactions/redo');assert state(inspect(path),a)['tasks'][0]['instance_properties']['Duration'].startswith('0.2')
        call('POST','/editor/transactions/undo')
        edit(path,'PATCH','states',StateId=b,bSetName=True,Name='B renamed')
        assert state(inspect(path),b)['name']=='B renamed'
        call('POST','/editor/transactions/undo');assert state(inspect(path),b)['name']=='B'
        edit(path,'POST','move',StateId=b,ParentId=root,Index=0)
        assert state(inspect(path),root)['children'][0]==b
        call('POST','/editor/transactions/undo');assert state(inspect(path),root)['children'][0]==a
        edit(path,'DELETE','nodes',StateId=a,Kind='enter_condition',ItemId=condition,bConfirm=True)
        call('POST','/editor/transactions/undo');assert state(inspect(path),a)['enter_conditions'][0]['id']==condition
        edit(path,'DELETE','transitions',StateId=a,ItemId=ab,bConfirm=True)
        call('POST','/editor/transactions/undo');assert state(inspect(path),a)['transitions'][0]['id']==ab
        edit(path,'POST','compile',bSave=True);snapshot=inspect(path)
        assert snapshot['ready_to_run'] and not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash'],snapshot
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('StateTree native creation/states/nodes/transitions, compile preflight, dry-run/no-op, invalid input, order and undo/redo: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
