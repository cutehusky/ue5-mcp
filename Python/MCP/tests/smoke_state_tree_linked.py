"""Local native linked subtrees, inherited parameters, overrides and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree_linked.json'


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
        assert inspect(path)==before,'Rejected local linked edit changed source'
    def cleanup(path):call('POST','/assets/delete',{'AssetPath':path});STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());path=saved['path']
        if phase=='verify':
            s=inspect(path);assert stable(s)==saved['snapshot'],(s,saved['snapshot'])
            assert s['ready_to_run'] and not s['dirty'] and s['editor_hash']==s['compiled_hash']
            before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
            assert v['diagnostics'].startswith('success') and inspect(path)==before
            print('Cold native linked targets, parameter identities/layout/defaults/overrides, bindings and compiled data: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior local linked fixture'
    path=None;keep=False
    try:
        c=call('POST','/state-trees/create',{'AssetPath':'/Game/UE5MCP_Test/ST_Local_'+uuid.uuid4().hex[:8]})
        path=c['asset_path'];root=c['states'][0]['id']
        def worker(name,duration):
            sub=edit(path,'POST','states',Name=name,StateType='Subtree')['selected_id']
            field=edit(path,'POST','parameters',StateId=sub,Name='Duration',ParameterType='Float',bSetValue=True,Value=duration)['selected_id']
            scope=state(path,sub)['parameters']['id']
            child=edit(path,'POST','states',Name=name+' task',ParentId=sub)['selected_id']
            edit(path,'POST','nodes',StateId=child,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'RandomDeviation':'0'},Bindings=[{'SourceId':scope,'SourcePath':'Duration','TargetId':'$new','TargetPath':'Duration'}])
            edit(path,'POST','transitions',StateId=child,TargetType='Succeeded')
            return sub,field
        fast,field=worker('Fast','0.03');slow,_=worker('Slow','0.12')
        link=edit(path,'POST','states',Name='Call',ParentId=root,StateType='Linked',TargetStateId=fast)['selected_id']
        edit(path,'POST','transitions',StateId=link,TargetType='Succeeded')
        assert state(path,link)['linked_subtree_id']==fast
        assert state(path,link)['parameters']['fields'][0]['id']==field
        before=inspect(path);edit(path,'PATCH','parameters',StateId=link,ItemId=field,bSetValue=True,Value='0.08',bDryRun=True);assert inspect(path)==before
        edit(path,'PATCH','parameters',StateId=link,ItemId=field,bSetValue=True,Value='0.08')
        assert field in state(path,link)['parameter_overrides']
        call('POST','/editor/transactions/undo');assert not state(path,link)['parameter_overrides']
        call('POST','/editor/transactions/redo');assert field in state(path,link)['parameter_overrides']
        edit(path,'PATCH','parameters',StateId=fast,ItemId=field,bSetValue=True,Value='0.2')
        assert state(path,link)['parameters']['fields'][0]['value'].startswith('0.08')
        edit(path,'POST','parameters/reset',StateId=link,ItemId=field,bConfirm=True)
        assert not state(path,link)['parameter_overrides'] and state(path,link)['parameters']['fields'][0]['value'].startswith('0.2')
        edit(path,'PATCH','parameters',StateId=fast,ItemId=field,bSetName=True,Name='WaitSeconds')
        assert state(path,link)['parameters']['fields'][0]['name']=='WaitSeconds'
        extra=edit(path,'POST','parameters',StateId=fast,Name='Extra',ParameterType='Bool')['selected_id']
        assert any(f['id']==extra for f in state(path,link)['parameters']['fields'])
        edit(path,'DELETE','parameters',StateId=fast,ItemId=extra,bConfirm=True)
        assert not any(f['id']==extra for f in state(path,link)['parameters']['fields'])
        reject(path,'POST','states',Name='Cycle',ParentId=fast,StateType='Linked',TargetStateId=fast)
        reject(path,'POST','move',StateId=link,ParentId=fast)
        reject(path,'DELETE','states',StateId=fast,bConfirm=True)
        reject(path,'POST','states',Name='Invalid',ParentId=root,StateType='Linked',TargetStateId=root)
        reject(path,'POST','states',Name='Child',ParentId=link)
        reject(path,'POST','parameters',StateId=link,Name='Wrong',ParameterType='Bool')
        reject(path,'PATCH','parameters',StateId=link,ItemId=field,bSetName=True,Name='Wrong')
        reject(path,'POST','links',StateId=link,TargetStateId=slow)
        edit(path,'POST','links',StateId=link,TargetStateId=slow,bConfirm=True)
        call('POST','/editor/transactions/undo');assert state(path,link)['linked_subtree_id']==fast
        call('POST','/editor/transactions/redo');assert state(path,link)['linked_subtree_id']==slow
        edit(path,'POST','links',StateId=link,TargetStateId=fast,bConfirm=True)
        root_field=edit(path,'POST','parameters',Name='Delay',ParameterType='Float',bSetValue=True,Value='0.06')['selected_id']
        scope=state(path,link)['parameters']['id']
        edit(path,'POST','bindings',Binding={'SourceId':'root','SourcePath':'Delay','TargetId':scope,'TargetPath':'WaitSeconds'})
        assert field in state(path,link)['parameter_overrides']
        before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path);assert v['diagnostics'].startswith('success') and inspect(path)==before
        edit(path,'POST','parameters/reset',StateId=link,ItemId=field,bConfirm=True)
        assert not any(b['target_id']==scope for b in inspect(path)['bindings'])
        call('POST','/editor/transactions/undo');assert any(b['target_id']==scope for b in inspect(path)['bindings'])
        edit(path,'PATCH','states',StateId=fast,bSetName=True,Name='Fast renamed')
        assert state(path,link)['linked_subtree_name']=='Fast renamed'
        edit(path,'POST','compile',bSave=True);snapshot=inspect(path)
        assert not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash']
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('Native local links, inherited layout/defaults, overrides/reset, bindings, rename, guards, retarget and undo/redo: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
