"""Native compound expressions, replacement, transactions and persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'behavior_tree_compound.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=240)
        assert r.is_success,(r.status_code,r.text)
        try:return r.json()
        except ValueError:return r.text
    def inspect(tree):return call('GET','/behavior-trees/inspect',asset_path=tree)
    def edit(tree,method,route,**kw):return call(method,'/behavior-trees/'+route,{'AssetPath':tree}|kw)
    def node(s,guid):return next(n for n in s['nodes'] if n['guid']==guid)
    def persistent(s):
        s=json.loads(json.dumps(s))
        for n in s['nodes']:
            n.pop('execution_index',None)
            for k in n['blackboard_selectors']:k.pop('key_id',None)
        return {k:s[k] for k in ['blackboard_path','root_class','root_guid','nodes','compiled_root_decorators','validation']}
    def reject(tree,method,route,**kw):
        before=inspect(tree);r=httpx.request(method,base+'/behavior-trees/'+route,json={'AssetPath':tree}|kw,timeout=240)
        assert r.status_code>=400,r.text
        assert inspect(tree)==before,'Rejected subtree update changed source graph/data/dirty state'
    def cleanup(paths):
        for path in reversed(paths):call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='verify':
            s=inspect(state['tree']);assert persistent(s)==state['snapshot'],(s,state['snapshot'])
            assert s['valid'] and not s['dirty'],s
            print('Cold compound expression, inner GUIDs/pins, leaf settings and native operations: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous compound fixture'
    paths=[];keep=False
    try:
        prefix='/Game/UE5MCP_Test/Compound_'+uuid.uuid4().hex[:8]
        board=call('POST','/blackboards/create',{'AssetPath':prefix+'/Board'});paths.append(board)
        for key in ['A','B','C']:
            call('POST','/blackboards/keys',{'AssetPath':board,'KeyName':key,'KeyType':'/Script/AIModule.BlackboardKeyType_Bool','bSave':True})
        tree=call('POST','/behavior-trees/create',{'AssetPath':prefix+'/Tree'});paths.append(tree)
        root=edit(tree,'POST','graph')['root_guid'];edit(tree,'PATCH','settings',BlackboardPath=board,bConfirm=True)
        def create(cls):return edit(tree,'POST','nodes',ClassPath='/Script/AIModule.'+cls)['node_guid']
        seq=create('BTComposite_Sequence');task=create('BTTask_Wait')
        edit(tree,'POST','links',NodeGuid=root,TargetGuid=seq);edit(tree,'POST','links',NodeGuid=seq,TargetGuid=task)
        def test(key):return {'Operation':'test','ClassPath':'/Script/AIModule.BTDecorator_Blackboard','BlackboardSelectors':{'BlackboardKey':key}}
        expression=[{'Operation':'or','Children':2},{'Operation':'and','Children':2},test('A'),test('B'),{'Operation':'not','Children':1},test('C')]
        before=inspect(tree)
        edit(tree,'POST','decorator-logic',ParentGuid=task,Logic=expression,bDryRun=True)
        assert inspect(tree)==before
        group=edit(tree,'POST','decorator-logic',ParentGuid=task,Logic=expression,bSetCompoundName=True,CompoundName='Truth table')['node_guid']
        s=inspect(tree);assert s['valid'],s
        compound=node(s,group)['compound'];assert len(compound['tests'])==3 and len(compound['operations'])==6,compound
        assert len(compound['inner_nodes'])==7,compound
        assert not edit(tree,'PATCH','decorator-logic',NodeGuid=group,Logic=expression)['would_change']
        reject(tree,'PATCH','decorator-logic',NodeGuid=group,Logic=expression+[test('A')])
        reject(tree,'PATCH','decorator-logic',NodeGuid=group,Logic=[{'Operation':'not','Children':2},test('A'),test('B')])
        reject(tree,'PATCH','decorator-logic',NodeGuid=group,Logic=[test('Missing')])
        edit(tree,'PATCH','decorator-logic',NodeGuid=group,Logic=[{'Operation':'and','Children':2},test('A'),test('B')])
        assert len(node(inspect(tree),group)['compound']['tests'])==2
        call('POST','/editor/transactions/undo');assert len(node(inspect(tree),group)['compound']['tests'])==3
        call('POST','/editor/transactions/redo');assert len(node(inspect(tree),group)['compound']['tests'])==2
        edit(tree,'DELETE','nodes',NodeGuid=group,bConfirm=True)
        call('POST','/editor/transactions/undo');assert node(inspect(tree),group)['compound']
        edit(tree,'POST','compile',bSave=True)
        s=inspect(tree);assert s['valid'] and not s['dirty'],s
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps({'paths':paths,'tree':tree,'snapshot':persistent(s)},indent=2));keep=True
        print('Compound prefix authoring, dry-run/no-op, invalid input, replacement, delete/undo and save: OK')
    finally:
        if not keep:cleanup(paths)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','verify','cleanup']);p.add_argument('--base',default='http://127.0.0.1:8080')
    args=p.parse_args();run(args.base,args.phase)
