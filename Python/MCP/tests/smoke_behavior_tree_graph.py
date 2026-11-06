"""Native BT editor graph CRUD/schema/compile, undo and cold persistence."""
import argparse
import json
import time
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'behavior_tree_graph.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=240)
        assert r.is_success,(r.status_code,r.text)
        try:return r.json()
        except ValueError:return r.text
    def inspect(tree):return call('GET','/behavior-trees/inspect',asset_path=tree)
    def edit(tree,method,route,**kw):return call(method,'/behavior-trees/'+route,{'AssetPath':tree}|kw)
    def reject(tree,method,route,**kw):
        before=inspect(tree)
        r=httpx.request(method,base+'/behavior-trees/'+route,json={'AssetPath':tree}|kw,timeout=240)
        assert r.status_code>=400,r.text
        assert inspect(tree)==before,'Rejected request changed source graph/runtime data/package state'
    def node(s,guid):return next(n for n in s['nodes'] if n['guid']==guid)
    def cleanup(paths):
        for p in reversed(paths):call('POST','/assets/delete',{'AssetPath':p})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['paths']);return
        tree=state['paths'][-1];s=inspect(tree);want=state['tree']
        def persistent_nodes(rows):
            rows=json.loads(json.dumps(rows))
            for n in rows:
                n.pop('execution_index',None)
                for k in n['blackboard_selectors']:k.pop('key_id',None)
            return rows
        for field in ['blackboard_path','root_class','root_guid','validation','compiled_root_decorators']:
            assert s[field]==want[field],(field,s[field],want[field])
        assert persistent_nodes(s['nodes'])==persistent_nodes(want['nodes']),(s,want)
        assert not s['dirty'] and s['valid'],s
        edit(tree,'POST','compile',bDryRun=True);assert inspect(tree)==s
        rebuilt=edit(tree,'POST','compile')
        assert rebuilt['valid']
        assert [(n['guid'],n['execution_index']) for n in rebuilt['nodes']]==[(n['guid'],n['execution_index']) for n in want['nodes']]
        print('Cold native Behavior Tree graph GUIDs, subnodes, links, settings, selectors and compiled execution order: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous Behavior Tree fixture'
    paths=[];keep=False
    try:
        board=call('POST','/blackboards/create',{'AssetPath':'/Game/UE5MCP_Test/BB_Graph_'+uuid.uuid4().hex[:8]});paths.append(board)
        for key,typ in [('Goal','Vector'),('Done','Bool'),('Delay','Float')]:
            call('POST','/blackboards/keys',{'AssetPath':board,'KeyName':key,'KeyType':'/Script/AIModule.BlackboardKeyType_'+typ,'bSave':True})
        tree=call('POST','/behavior-trees/create',{'AssetPath':'/Game/UE5MCP_Test/BT_Graph_'+uuid.uuid4().hex[:8]});paths.append(tree)
        before=inspect(tree)
        edit(tree,'POST','graph',bDryRun=True);assert inspect(tree)==before
        s=edit(tree,'POST','graph');root=s['root_guid'];assert root and len(s['nodes'])==1 and not s['blackboard_path']
        assert not edit(tree,'POST','graph')['would_change']
        reject(tree,'PATCH','settings',BlackboardPath=board)
        before=inspect(tree);edit(tree,'PATCH','settings',BlackboardPath=board,bDryRun=True);assert inspect(tree)==before
        edit(tree,'PATCH','settings',BlackboardPath=board,bConfirm=True)
        def create(cls,**kw):return edit(tree,'POST','nodes',ClassPath='/Script/AIModule.'+cls,**kw)['node_guid']
        before=inspect(tree);create('BTComposite_Sequence',bDryRun=True);assert inspect(tree)==before
        seq=create('BTComposite_Sequence',X=0,Y=200)
        edit(tree,'POST','links',NodeGuid=root,TargetGuid=seq)
        wait=create('BTTask_Wait',X=-300,Y=400,Properties={'WaitTime':'(DefaultValue=0.05,Key=None)','RandomDeviation':'(DefaultValue=0.0,Key=None)'})
        setter=create('BTTask_SetKeyValueBool',X=0,Y=400,Properties={'Value':'(DefaultValue=True,Key=None)'},BlackboardSelectors={'BlackboardKey':'Done'})
        finish=create('BTTask_FinishWithResult',X=300,Y=400)
        for child in [wait,setter,finish]:edit(tree,'POST','links',NodeGuid=seq,TargetGuid=child)
        service=create('BTService_DefaultFocus',ParentGuid=seq,BlackboardSelectors={'BlackboardKey':'SelfActor'})
        decorator=create('BTDecorator_ForceSuccess',ParentGuid=wait)
        s=inspect(tree);assert s['valid'],s
        assert node(s,service)['parent_guid']==seq and node(s,decorator)['parent_guid']==wait
        assert node(s,wait)['execution_index']<node(s,setter)['execution_index']<node(s,finish)['execution_index']
        reject(tree,'POST','nodes',ClassPath='/Script/Engine.Actor')
        reject(tree,'POST','nodes',ClassPath='/Script/AIModule.BTService_DefaultFocus',ParentGuid=root)
        reject(tree,'POST','nodes',ClassPath='/Script/AIModule.BTTask_MoveTo',BlackboardSelectors={'BlackboardKey':'Done'})
        reject(tree,'POST','links',NodeGuid=seq,TargetGuid=seq)
        reject(tree,'POST','links',NodeGuid=root,TargetGuid=wait)
        reject(tree,'POST','links',NodeGuid=wait,TargetGuid=seq)
        reject(tree,'POST','links',NodeGuid=seq,TargetGuid=finish,PinIndex=8)
        reject(tree,'DELETE','nodes',NodeGuid=root,bConfirm=True)
        reject(tree,'PATCH','nodes',NodeGuid=wait,Properties={'WaitTime':'(DefaultValue=-1.0,Key=None)'})
        reject(tree,'PATCH','nodes',NodeGuid=wait,Properties={'NoSuchProperty':'bad'})
        before=inspect(tree);edit(tree,'PATCH','nodes',NodeGuid=wait,Properties={'WaitTime':'(DefaultValue=0.05,Key=None)'},bDryRun=True);assert inspect(tree)==before
        edit(tree,'PATCH','nodes',NodeGuid=wait,Properties={'WaitTime':'(DefaultValue=0.1,Key=None)'})
        s=inspect(tree);noop=edit(tree,'PATCH','nodes',NodeGuid=wait,Properties={'WaitTime':node(s,wait)['properties']['WaitTime']});assert not noop['would_change'] and inspect(tree)==s
        edit(tree,'PATCH','nodes',NodeGuid=wait,BlackboardSelectors={'WaitTime':'Delay'})
        assert next(k for k in node(inspect(tree),wait)['blackboard_selectors'] if k['property']=='WaitTime')['key']=='Delay'
        reject(tree,'PATCH','nodes',NodeGuid=wait,BlackboardSelectors={'WaitTime':'Done'})
        edit(tree,'PATCH','nodes',NodeGuid=wait,BlackboardSelectors={'WaitTime':''})
        # Deletion previews include attached decorators and linked parent/children.
        dry=edit(tree,'DELETE','nodes',NodeGuid=wait,bDryRun=True);assert decorator in dry['affected_nodes']
        reject(tree,'DELETE','nodes',NodeGuid=wait)
        edit(tree,'DELETE','nodes',NodeGuid=wait,bConfirm=True)
        assert wait not in {n['guid'] for n in inspect(tree)['nodes']} and decorator not in {n['guid'] for n in inspect(tree)['nodes']}
        call('POST','/editor/transactions/undo');s=inspect(tree);assert node(s,decorator)['parent_guid']==wait and s['valid'],s
        call('POST','/editor/transactions/redo');assert wait not in {n['guid'] for n in inspect(tree)['nodes']}
        call('POST','/editor/transactions/undo');assert inspect(tree)['valid']
        # X placement is native execution order, not merely visual decoration.
        edit(tree,'POST','layout',Positions=[{'NodeGuid':wait,'X':400,'Y':400},{'NodeGuid':finish,'X':-400,'Y':400}])
        s=inspect(tree);assert node(s,finish)['execution_index']<node(s,setter)['execution_index']<node(s,wait)['execution_index']
        call('POST','/editor/transactions/undo');s=inspect(tree);assert node(s,wait)['execution_index']<node(s,finish)['execution_index']
        other=create('BTComposite_Selector',X=800,Y=200)
        reject(tree,'POST','links',NodeGuid=other,TargetGuid=wait)
        dry=edit(tree,'POST','links',NodeGuid=other,TargetGuid=wait,bDryRun=True);assert dry['would_change']
        edit(tree,'POST','links',NodeGuid=other,TargetGuid=wait,bConfirm=True)
        edit(tree,'POST','links',NodeGuid=seq,TargetGuid=wait,bConfirm=True)
        edit(tree,'DELETE','nodes',NodeGuid=other,bConfirm=True)
        s=edit(tree,'POST','compile',bSave=True);assert s['valid'] and not s['dirty'],s
        # A graph mutation is rejected while PIE owns runtime copies.
        call('POST','/editor/play',{'Operation':'start'});end=time.monotonic()+20
        while not call('GET','/editor/status')['is_playing']:
            assert time.monotonic()<end;time.sleep(.1)
        reject(tree,'POST','compile')
        call('POST','/editor/play',{'Operation':'stop'});end=time.monotonic()+20
        while call('GET','/editor/status')['is_playing']:
            assert time.monotonic()<end;time.sleep(.1)
        s=inspect(tree);assert s['valid'] and not s['dirty'],s
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'tree':s}));keep=True
        print('Native Behavior Tree graph/task/service/decorator CRUD, selector/value binding compatibility, schema links/reparent guards, headless layout/order, compile/save, deletion undo/redo and PIE guard: OK; restart and verify')
    finally:
        if not keep:
            if call('GET','/editor/status')['is_playing']:call('POST','/editor/play',{'Operation':'stop'})
            cleanup(paths)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080');p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
