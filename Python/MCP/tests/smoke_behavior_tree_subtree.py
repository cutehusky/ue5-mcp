"""Native RunBehavior references, injected previews, dependency guards and persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'behavior_tree_subtree.json'


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
        if phase=='cleanup':cleanup(state['paths']);return
        for path,want in state['trees'].items():
            s=inspect(path);assert persistent(s)==want,(path,s,want);assert s['valid'] and not s['dirty'],s
        parent=state['parent'];ids={n['guid'] for n in inspect(parent)['nodes'] if n['injected']}
        compiled=edit(parent,'POST','compile');assert compiled['valid']
        assert {n['guid'] for n in compiled['nodes'] if n['injected']}==ids
        for source in state['sources']:assert persistent(inspect(source))==state['trees'][source] and not inspect(source)['dirty']
        print('Cold subtree references, scoped injected GUIDs, read-only previews, native counts/roles and source isolation after refresh: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous subtree fixture'
    paths=[];keep=False
    try:
        prefix='/Game/UE5MCP_Test/Subtrees_'+uuid.uuid4().hex[:8]
        board=call('POST','/blackboards/create',{'AssetPath':prefix+'/Board'});paths.append(board)
        for key in ['Gate','Done','After']:call('POST','/blackboards/keys',{'AssetPath':board,'KeyName':key,'KeyType':'/Script/AIModule.BlackboardKeyType_Bool','bSave':True})
        derived=call('POST','/blackboards/create',{'AssetPath':prefix+'/Derived'});paths.append(derived)
        call('POST','/blackboards/keys',{'AssetPath':derived,'KeyName':'Local','KeyType':'/Script/AIModule.BlackboardKeyType_Int'})
        call('PATCH','/blackboards/settings',{'AssetPath':derived,'bSetParent':True,'ParentPath':board,'bSave':True})
        badboard=call('POST','/blackboards/create',{'AssetPath':prefix+'/Incompatible'});paths.append(badboard)
        call('POST','/blackboards/keys',{'AssetPath':badboard,'KeyName':'Other','KeyType':'/Script/AIModule.BlackboardKeyType_Int','bSave':True})
        def setup(path,bb):
            tree=call('POST','/behavior-trees/create',{'AssetPath':path});paths.append(tree)
            root=edit(tree,'POST','graph')['root_guid'];edit(tree,'PATCH','settings',BlackboardPath=bb,bConfirm=True)
            seq=create(tree,'BTComposite_Sequence');edit(tree,'POST','links',NodeGuid=root,TargetGuid=seq);return tree,seq
        def create(tree,cls,**kw):return edit(tree,'POST','nodes',ClassPath='/Script/AIModule.'+cls,**kw)['node_guid']
        def marker(tree,seq,key):
            n=create(tree,'BTTask_SetKeyValueBool',Properties={'Value':'(DefaultValue=True,Key=None)'},BlackboardSelectors={'BlackboardKey':key})
            edit(tree,'POST','links',NodeGuid=seq,TargetGuid=n);return n
        # Same short asset names exercise the native cache-name collision case.
        a,aroot=setup(prefix+'/A/Shared',board);marker(a,aroot,'Done')
        create(a,'BTDecorator_Blackboard',ParentGuid=aroot,BlackboardSelectors={'BlackboardKey':'Gate'})
        edit(a,'POST','compile',bSave=True)
        b,broot=setup(prefix+'/B/Shared',board);marker(b,broot,'Done')
        create(b,'BTDecorator_ForceSuccess',ParentGuid=broot);edit(b,'POST','compile',bSave=True)
        bad,badroot=setup(prefix+'/Bad',badboard)
        wait=create(bad,'BTTask_Wait');edit(bad,'POST','links',NodeGuid=badroot,TargetGuid=wait);edit(bad,'POST','compile',bSave=True)
        parent,proot=setup(prefix+'/Parent',derived)
        sources={p:inspect(p) for p in [a,b]}
        before=inspect(parent)
        create(parent,'BTTask_RunBehavior',bSetSubtree=True,SubtreePath=a,bDryRun=True)
        assert inspect(parent)==before
        first=create(parent,'BTTask_RunBehavior',X=-200,bSetSubtree=True,SubtreePath=a)
        second=create(parent,'BTTask_RunBehavior',X=0,bSetSubtree=True,SubtreePath=a)
        for task in [first,second]:edit(parent,'POST','links',NodeGuid=proot,TargetGuid=task)
        after=marker(parent,proot,'After');edit(parent,'POST','layout',Positions=[{'NodeGuid':after,'X':200,'Y':400}])
        s=inspect(parent);assert s['valid'],s
        injected=[n for n in s['nodes'] if n['injected']];assert len(injected)==2 and len({n['guid'] for n in s['nodes']})==len(s['nodes'])
        assert all(n['read_only'] for n in injected)
        for task in [first,second]:assert node(s,task)['subtree']['preview_count']==node(s,task)['subtree']['native_injected_count']==1
        for source in [a,b]:assert inspect(source)==sources[source]
        reject(parent,'PATCH','nodes',NodeGuid=first,bSetSubtree=True,SubtreePath=parent)
        reject(parent,'PATCH','nodes',NodeGuid=first,bSetSubtree=True,SubtreePath=bad)
        reject(parent,'PATCH','nodes',NodeGuid=first,bSetSubtree=True,SubtreePath='/Game/Missing.Tree')
        reject(a,'POST','nodes',ClassPath='/Script/AIModule.BTTask_RunBehavior',bSetSubtree=True,SubtreePath=parent)
        reject(parent,'PATCH','nodes',NodeGuid=injected[0]['guid'],Properties={'NodeName':'forbidden'})
        reject(parent,'DELETE','nodes',NodeGuid=injected[0]['guid'],bConfirm=True)
        before=inspect(parent);noop=edit(parent,'PATCH','nodes',NodeGuid=first,bSetSubtree=True,SubtreePath=a);assert not noop['would_change'] and inspect(parent)==before
        edit(parent,'PATCH','nodes',NodeGuid=first,bSetSubtree=True,SubtreePath=b)
        s=inspect(parent);copy=next(n for n in s['nodes'] if n['injected'] and n['parent_guid']==first)
        assert copy['class'].endswith('BTDecorator_ForceSuccess'),s
        call('POST','/editor/transactions/undo')
        assert node(inspect(parent),first)['subtree']['asset_path']==a+'.'+a.rsplit('/',1)[1]
        call('POST','/editor/transactions/redo')
        assert node(inspect(parent),first)['subtree']['asset_path']==b+'.'+b.rsplit('/',1)[1]
        edit(parent,'PATCH','nodes',NodeGuid=first,bSetSubtree=True,SubtreePath='')
        assert not inspect(parent)['valid'] and node(inspect(parent),first)['subtree']['preview_count']==0
        call('POST','/editor/transactions/undo');assert node(inspect(parent),first)['subtree']['preview_count']==1
        edit(parent,'POST','compile')
        for source in [a,b]:assert inspect(source)==sources[source]
        edit(parent,'POST','compile',bSave=True)
        snapshots={p:persistent(inspect(p)) for p in [a,b,parent]}
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'trees':snapshots,'parent':parent,'sources':[a,b]}));keep=True
        print('RunBehavior reference creation/update/clear, native injected previews, repeated-source GUID uniqueness, same-name switching, inherited Blackboard compatibility, cycle/mismatch/read-only guards, source preservation, no-op/dry-run and undo/redo: OK; restart and verify')
    finally:
        if not keep:cleanup(paths)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080');p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
