"""Native condition expression updates, guards and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'state_tree_expressions.json'


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
        assert inspect(path)==before,'Rejected expression edit changed source'
    def cleanup(path):call('POST','/assets/delete',{'AssetPath':path});STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        saved=json.loads(STATE.read_text());path=saved['path']
        if phase=='verify':
            s=inspect(path);assert stable(s)==saved['snapshot'],(s,saved['snapshot'])
            assert s['ready_to_run'] and not s['dirty'] and s['editor_hash']==s['compiled_hash']
            before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
            assert v['diagnostics'].startswith('success') and inspect(path)==before
            print('Cold expression IDs/operands/indentation and compiled data: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior expression fixture'
    path=None;keep=False
    try:
        c=call('POST','/state-trees/create',{'AssetPath':'/Game/UE5MCP_Test/ST_Expression_'+uuid.uuid4().hex[:8]})
        path=c['asset_path'];root=c['states'][0]['id']
        a=edit(path,'POST','states',Name='A',ParentId=root)['selected_id'];b=edit(path,'POST','states',Name='B',ParentId=root)['selected_id']
        for g in [a,b]:
            edit(path,'POST','nodes',StateId=g,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'Duration':'0.02','RandomDeviation':'0'})
            edit(path,'POST','transitions',StateId=g)
        nodes=[]
        for value in ['1','0','0']:
            nodes.append(edit(path,'POST','nodes',StateId=a,Kind='enter_condition',StructPath='/Script/StateTreeModule.StateTreeRandomCondition',InstanceProperties={'Threshold':value})['selected_id'])
        before=inspect(path)
        edit(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],bSetExpression=True,Operand='Or',ExpressionIndent=1,bDryRun=True);assert inspect(path)==before
        edit(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],bSetExpression=True,Operand='Or',ExpressionIndent=1)
        def condition():return state(path,a)['enter_conditions'][1]
        assert condition()['operand']=='Or' and condition()['expression_indent']==1
        after=inspect(path);call('POST','/editor/transactions/undo');assert stable(inspect(path))==stable(before)
        call('POST','/editor/transactions/redo');assert stable(inspect(path))==stable(after)
        assert not edit(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],bSetExpression=True,Operand='Or',ExpressionIndent=1)['would_change']
        edit(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],InstanceProperties={'Threshold':'0'})
        assert condition()['operand']=='Or' and condition()['expression_indent']==1
        reject(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],bSetExpression=True,Operand='Or',ExpressionIndent=5)
        reject(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],bSetExpression=True,Operand='Copy')
        reject(path,'PATCH','nodes',StateId=a,Kind='enter_condition',ItemId=nodes[1],bSetExpression=True,Operand='Multiply')
        reject(path,'POST','nodes',StateId=a,Kind='enter_condition',StructPath='/Script/StateTreeModule.StateTreeRandomCondition',Operand='Multiply')
        before=inspect(path);v=call('GET','/state-trees/validate',asset_path=path)
        assert v['diagnostics'].startswith('success') and inspect(path)==before
        edit(path,'POST','compile',bSave=True);snapshot=inspect(path)
        assert not snapshot['dirty'] and snapshot['editor_hash']==snapshot['compiled_hash']
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('Expression operand/indent updates, grouping metadata, preservation, guards, dry-run/no-op, undo/redo and save: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
