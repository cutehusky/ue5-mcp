"""Native SimpleParallel pins, finish mode, role persistence and undo."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'behavior_tree_parallel.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        try:return r.json()
        except ValueError:return r.text
    def inspect(tree):return call('GET','/behavior-trees/inspect',asset_path=tree)
    def edit(tree,method,route,**kw):return call(method,'/behavior-trees/'+route,{'AssetPath':tree}|kw)
    def node(s,guid):return next(n for n in s['nodes'] if n['guid']==guid)
    def reject(tree,method,route,**kw):
        before=inspect(tree);r=httpx.request(method,base+'/behavior-trees/'+route,json={'AssetPath':tree}|kw,timeout=180)
        assert r.status_code>=400,r.text
        assert inspect(tree)==before,'Rejected request changed graph, native data or package state'
    def persistent(rows):
        rows=json.loads(json.dumps(rows))
        for n in rows:
            n.pop('execution_index',None)
            for k in n['blackboard_selectors']:k.pop('key_id',None)
        return rows
    def cleanup(paths):
        for path in reversed(paths):call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['paths']);return
        tree=state['paths'][-1];s=inspect(tree);want=state['tree']
        assert persistent(s['nodes'])==persistent(want['nodes']),(s,want)
        assert s['validation']==want['validation'] and s['valid'] and not s['dirty'],s
        p=node(s,state['parallel']);assert [c['node_guid'] for c in p['compiled_children']]==[state['main'],state['background']]
        assert p['parallel']['finish_mode']=='WaitForBackground'
        print('Cold SimpleParallel graph type, pin roles, finish mode, native child/auxiliary order and clean state: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous parallel fixture'
    paths=[];keep=False
    try:
        board=call('POST','/blackboards/create',{'AssetPath':'/Game/UE5MCP_Test/BB_Parallel_'+uuid.uuid4().hex[:8]});paths.append(board)
        call('POST','/blackboards/keys',{'AssetPath':board,'KeyName':'Done','KeyType':'/Script/AIModule.BlackboardKeyType_Bool','bSave':True})
        tree=call('POST','/behavior-trees/create',{'AssetPath':'/Game/UE5MCP_Test/BT_Parallel_'+uuid.uuid4().hex[:8]});paths.append(tree)
        root=edit(tree,'POST','graph')['root_guid'];edit(tree,'PATCH','settings',BlackboardPath=board,bConfirm=True)
        def create(cls,**kw):return edit(tree,'POST','nodes',ClassPath='/Script/AIModule.'+cls,**kw)['node_guid']
        before=inspect(tree);create('BTComposite_SimpleParallel',bDryRun=True);assert inspect(tree)==before
        parallel=create('BTComposite_SimpleParallel',Properties={'FinishMode':'WaitForBackground'},Y=200)
        edit(tree,'POST','links',NodeGuid=root,TargetGuid=parallel)
        s=inspect(tree);p=node(s,parallel)
        assert p['graph_node_class'].endswith('BehaviorTreeGraphNode_SimpleParallel') and not s['valid'],s
        outputs=[pin for pin in p['pins'] if pin['direction']=='output'];assert len(outputs)==2 and outputs[0]['category']!=outputs[1]['category']
        main=create('BTTask_Wait',X=900,Y=400,Properties={'WaitTime':'(DefaultValue=0.05,Key=None)'})
        background=create('BTComposite_Sequence',X=-900,Y=400)
        wait=create('BTTask_Wait',X=-1000,Y=600,Properties={'WaitTime':'(DefaultValue=0.30,Key=None)'})
        marker=create('BTTask_SetKeyValueBool',X=-800,Y=600,Properties={'Value':'(DefaultValue=True,Key=None)'},BlackboardSelectors={'BlackboardKey':'Done'})
        reject(tree,'POST','links',NodeGuid=parallel,TargetGuid=background,PinIndex=0)
        edit(tree,'POST','links',NodeGuid=parallel,TargetGuid=main,PinIndex=0)
        edit(tree,'POST','links',NodeGuid=parallel,TargetGuid=background,PinIndex=1)
        for child in [wait,marker]:edit(tree,'POST','links',NodeGuid=background,TargetGuid=child)
        create('BTService_DefaultFocus',ParentGuid=parallel,BlackboardSelectors={'BlackboardKey':'SelfActor'})
        decorator=create('BTDecorator_ForceSuccess',ParentGuid=main)
        s=inspect(tree);assert s['valid'],s
        p=node(s,parallel);assert [c['node_guid'] for c in p['compiled_children']]==[main,background]
        assert p['compiled_children'][0]['decorators']==[decorator] and p['parallel']=={'finish_mode':'WaitForBackground','main_guid':main,'background_guid':background}
        reject(tree,'PATCH','nodes',NodeGuid=parallel,Properties={'FinishMode':'99'})
        before=inspect(tree);edit(tree,'PATCH','nodes',NodeGuid=parallel,Properties={'FinishMode':'AbortBackground'},bDryRun=True);assert inspect(tree)==before
        edit(tree,'PATCH','nodes',NodeGuid=parallel,Properties={'FinishMode':'AbortBackground'})
        assert node(inspect(tree),parallel)['parallel']['finish_mode']=='AbortBackground'
        call('POST','/editor/transactions/undo');assert node(inspect(tree),parallel)['parallel']['finish_mode']=='WaitForBackground'
        call('POST','/editor/transactions/redo');assert node(inspect(tree),parallel)['parallel']['finish_mode']=='AbortBackground'
        edit(tree,'PATCH','nodes',NodeGuid=parallel,Properties={'FinishMode':'WaitForBackground'})
        before=inspect(tree);assert not edit(tree,'PATCH','nodes',NodeGuid=parallel,Properties={'FinishMode':'WaitForBackground'})['would_change'];assert inspect(tree)==before
        edit(tree,'POST','layout',Positions=[{'NodeGuid':main,'X':-900,'Y':400},{'NodeGuid':background,'X':900,'Y':400}])
        assert [c['node_guid'] for c in node(inspect(tree),parallel)['compiled_children']]==[main,background]
        # An incomplete main pin must never be reported ready just because the
        # background branch is the first element of the native child array.
        edit(tree,'DELETE','links',NodeGuid=parallel,TargetGuid=main,PinIndex=0)
        s=inspect(tree);assert not s['valid'] and node(s,parallel)['parallel']['main_guid']==''
        call('POST','/editor/transactions/undo');assert inspect(tree)['valid']
        alternate=create('BTTask_Wait',X=1500,Y=400)
        reject(tree,'POST','links',NodeGuid=parallel,TargetGuid=alternate,PinIndex=1)
        edit(tree,'POST','links',NodeGuid=parallel,TargetGuid=alternate,PinIndex=1,bConfirm=True)
        assert node(inspect(tree),parallel)['parallel']['background_guid']==alternate
        call('POST','/editor/transactions/undo')
        edit(tree,'DELETE','nodes',NodeGuid=alternate,bConfirm=True)
        s=edit(tree,'POST','compile',bSave=True);assert s['valid'] and not s['dirty'],s
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'tree':s,'parallel':parallel,'main':main,'background':background}));keep=True
        print('SimpleParallel native graph/pins, task/subtree roles, schema guards, finish mode dry-run/no-op/undo, incomplete validation, replacement confirmation, pin role versus X order and compile/save: OK; restart and verify')
    finally:
        if not keep:cleanup(paths)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080');p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
