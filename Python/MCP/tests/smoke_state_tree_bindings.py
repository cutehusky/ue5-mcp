"""Native StateTree parameter bags and direct bindings, including cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree_bindings.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/state-trees/inspect',asset_path=path)
    def edit(path,method,route,**values):return call(method,'/state-trees/'+route,{'AssetPath':path}|values)
    def stable(s):return {k:v for k,v in s.items() if k not in ['affected_assets','selected_id','would_change','dry_run','saved','diagnostics','validation_compiled_copy']}
    def reject(path,method,route,**values):
        before=inspect(path);r=httpx.request(method,base+'/state-trees/'+route,json={'AssetPath':path}|values,timeout=180)
        assert r.status_code>=400,(r.status_code,r.text)
        assert inspect(path)==before,'Rejected parameter/binding edit changed source'
    def cleanup(path):call('POST','/assets/delete',{'AssetPath':path});STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());path=saved['path']
        if phase=='verify':
            snapshot=inspect(path);assert stable(snapshot)==saved['snapshot'],(snapshot,saved['snapshot'])
            assert snapshot['ready_to_run'] and not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash']
            before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
            assert v['diagnostics'].startswith('success') and inspect(path)==before,v
            print('Cold native parameter field IDs/types/defaults, root/state bags, binding paths and clean compiled data: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior binding fixture'
    path=None;keep=False
    try:
        c=call('POST','/state-trees/create',{'AssetPath':'/Game/UE5MCP_Test/ST_Bind_'+uuid.uuid4().hex[:8]})
        path=c['asset_path'];root=c['states'][0]['id']
        a=edit(path,'POST','states',Name='A',ParentId=root)['selected_id']
        b=edit(path,'POST','states',Name='B',ParentId=root)['selected_id']
        duration=edit(path,'POST','parameters',Name='Duration',ParameterType='Float',bSetValue=True,Value='0.03')['selected_id']
        flag=edit(path,'POST','parameters',Name='Flag',ParameterType='Bool',bSetValue=True,Value='False')['selected_id']
        edit(path,'POST','parameters',StateId=a,Name='Match',ParameterType='Bool',bSetValue=True,Value='False')
        local=next(s for s in inspect(path)['states'] if s['id']==a)['parameters']['id']
        task=edit(path,'POST','nodes',StateId=a,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'RandomDeviation':'0'},Bindings=[{'SourceId':'root','SourcePath':'Duration','TargetId':'$new','TargetPath':'Duration'}])['selected_id']
        condition=edit(path,'POST','nodes',StateId=a,Kind='enter_condition',StructPath='/Script/StateTreeModule.StateTreeCompareBoolCondition',InstanceProperties={'bRight':'False'},Bindings=[{'SourceId':'root','SourcePath':'Flag','TargetId':'$new','TargetPath':'bLeft'}])['selected_id']
        sources=call('GET','/state-trees/bindables',asset_path=path,target_id=condition)['sources']
        assert any(s['id']==local and any(p['name']=='Match' for p in s['properties']) for s in sources),sources
        edit(path,'POST','bindings',Binding={'SourceId':local,'SourcePath':'Match','TargetId':condition,'TargetPath':'bRight'})
        edit(path,'POST','nodes',StateId=b,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'Duration':'0.02'})
        edit(path,'POST','transitions',StateId=a,TargetType='GotoState',TargetStateId=b)
        edit(path,'POST','transitions',StateId=b,TargetType='Succeeded')
        # Typed bags: IDs and values must survive generated struct rebuilds.
        for name,typ,value,type_path in [('Count','Int32','-42',''),('Huge','Int64','123456789',''),('Ratio','Double','0.125',''),('Label','Name','Example',''),('Message','String','hello world',''),('Position','Struct','(X=1,Y=2,Z=3)','/Script/CoreUObject.Vector'),('Result','Enum','Running','/Script/StateTreeModule.EStateTreeRunStatus')]:
            edit(path,'POST','parameters',Name=name,ParameterType=typ,bSetValue=True,Value=value,TypePath=type_path)
        spare=edit(path,'POST','parameters',StateId=b,Name='Spare',ParameterType='Int32',bSetValue=True,Value='7')['selected_id']
        edit(path,'PATCH','parameters',StateId=b,ItemId=spare,bSetValue=True,Value='8')
        call('POST','/editor/transactions/undo')
        assert next(x for x in next(s for s in inspect(path)['states'] if s['id']==b)['parameters']['fields'] if x['id']==spare)['value']=='7'
        edit(path,'DELETE','parameters',StateId=b,ItemId=spare,bConfirm=True)
        assert not next(s for s in inspect(path)['states'] if s['id']==b)['parameters']['fields']
        call('POST','/editor/transactions/undo')
        assert next(s for s in inspect(path)['states'] if s['id']==b)['parameters']['fields'][0]['id']==spare
        call('POST','/editor/transactions/redo')
        before=inspect(path)
        edit(path,'PATCH','parameters',ItemId=duration,bSetValue=True,Value='0.2',bDryRun=True);assert inspect(path)==before
        assert not edit(path,'PATCH','parameters',ItemId=duration,bSetValue=True,Value='0.03')['would_change']
        assert not edit(path,'POST','bindings',Binding={'SourceId':'root','SourcePath':'Duration','TargetId':task,'TargetPath':'Duration'})['would_change']
        reject(path,'POST','parameters',Name='Flag',ParameterType='Float')
        reject(path,'PATCH','parameters',ItemId=duration,bSetValue=True,Value='nan')
        reject(path,'DELETE','parameters',ItemId=duration,bConfirm=True)
        reject(path,'POST','bindings',Binding={'SourceId':'root','SourcePath':'Missing','TargetId':task,'TargetPath':'Duration'})
        reject(path,'POST','bindings',Binding={'SourceId':'root','SourcePath':'Message','TargetId':task,'TargetPath':'Duration'},bConfirm=True)
        reject(path,'POST','bindings',Binding={'SourceId':task,'SourcePath':'Duration','TargetId':condition,'TargetPath':'bLeft'},bConfirm=True)
        reject(path,'DELETE','bindings',Binding={'TargetId':condition,'TargetPath':'bLeft'})
        before=inspect(path);edit(path,'PATCH','parameters',ItemId=duration,bSetName=True,Name='WaitSeconds')
        renamed=inspect(path);assert next(x for x in renamed['parameters']['fields'] if x['id']==duration)['name']=='WaitSeconds'
        assert next(x for x in renamed['bindings'] if x['target_id']==task)['source_path']=='WaitSeconds'
        call('POST','/editor/transactions/undo');assert stable(inspect(path))==stable(before)
        call('POST','/editor/transactions/redo');assert stable(inspect(path))==stable(renamed)
        edit(path,'PATCH','parameters',ItemId=flag,bSetValue=True,Value='True')
        call('POST','/editor/transactions/undo');assert next(x for x in inspect(path)['parameters']['fields'] if x['id']==flag)['value']=='False'
        # Optional input bindings can be removed; required ones stay compiler guarded.
        edit(path,'DELETE','bindings',Binding={'TargetId':condition,'TargetPath':'bRight'},bConfirm=True)
        call('POST','/editor/transactions/undo');assert inspect(path)['binding_count']==3
        edit(path,'DELETE','nodes',StateId=a,Kind='enter_condition',ItemId=condition,bConfirm=True)
        assert inspect(path)['binding_count']==1
        call('POST','/editor/transactions/undo');assert inspect(path)['binding_count']==3
        v=call('GET','/state-trees/validate',asset_path=path);assert v['diagnostics'].startswith('success')
        edit(path,'POST','compile',bSave=True);snapshot=inspect(path)
        assert not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash']
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('Native root/state bags, typed defaults, atomic required inputs, binding guards, rename, transactions and save: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
