"""Dynamic subtree default/tag authoring, preflight and persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'behavior_tree_dynamic.json'
TAG_FILE=PROJECT/'Config'/'Tags'/'UE5MCP_Test_Dynamic.ini'
TAG_TEXT='[/Script/GameplayTags.GameplayTagsList]\nGameplayTagList=(Tag="UE5MCP.Test.Dynamic",DevComment="Owned temporary REST fixture")\n'


def run(base,phase):
    if phase=='tags':
        assert not TAG_FILE.exists(),'Owned tag fixture already exists'
        TAG_FILE.parent.mkdir(parents=True,exist_ok=True);TAG_FILE.write_text(TAG_TEXT)
        print('Owned tag fixture prepared; start a fresh editor before prepare');return
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
        if TAG_FILE.exists() and TAG_FILE.read_text()==TAG_TEXT:TAG_FILE.unlink()
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='verify':
            for tree,want in state['trees'].items():
                snapshot=inspect(tree);assert persistent(snapshot)==want,(snapshot,want)
                assert snapshot['valid'] and not snapshot['dirty'],snapshot
            print('Cold dynamic default reference, registered tag, native task graph and source settings: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous dynamic fixture'
    assert TAG_FILE.exists() and TAG_FILE.read_text()==TAG_TEXT,'Run tags phase before starting this editor'
    paths=[];keep=False
    try:
        prefix='/Game/UE5MCP_Test/Dynamic_'+uuid.uuid4().hex[:8]
        board=call('POST','/blackboards/create',{'AssetPath':prefix+'/Board'});paths.append(board)
        call('POST','/blackboards/keys',{'AssetPath':board,'KeyName':'Gate','KeyType':'/Script/AIModule.BlackboardKeyType_Bool','bSave':True})
        def create(tree,cls,**kw):return edit(tree,'POST','nodes',ClassPath='/Script/AIModule.'+cls,**kw)['node_guid']
        def setup(name):
            tree=call('POST','/behavior-trees/create',{'AssetPath':prefix+'/'+name});paths.append(tree)
            root=edit(tree,'POST','graph')['root_guid'];edit(tree,'PATCH','settings',BlackboardPath=board,bConfirm=True)
            seq=create(tree,'BTComposite_Sequence');edit(tree,'POST','links',NodeGuid=root,TargetGuid=seq);return tree,seq
        child,croot=setup('Child');wait=create(child,'BTTask_Wait');edit(child,'POST','links',NodeGuid=croot,TargetGuid=wait);edit(child,'POST','compile',bSave=True)
        decorated,droot=setup('Decorated');wait=create(decorated,'BTTask_Wait');edit(decorated,'POST','links',NodeGuid=droot,TargetGuid=wait)
        create(decorated,'BTDecorator_Blackboard',ParentGuid=droot,BlackboardSelectors={'BlackboardKey':'Gate'});edit(decorated,'POST','compile',bSave=True)
        parent,proot=setup('Parent');tag='UE5MCP.Test.Dynamic'
        before=inspect(parent)
        create(parent,'BTTask_RunBehaviorDynamic',bSetSubtree=True,SubtreePath=child,bSetInjectionTag=True,InjectionTag=tag,bDryRun=True);assert inspect(parent)==before
        dynamic=create(parent,'BTTask_RunBehaviorDynamic',bSetSubtree=True,SubtreePath=child,bSetInjectionTag=True,InjectionTag=tag)
        edit(parent,'POST','links',NodeGuid=proot,TargetGuid=dynamic)
        snapshot=inspect(parent);assert snapshot['valid'],snapshot
        typed=node(snapshot,dynamic)['dynamic_subtree'];assert typed['tag_registered'] and typed['injection_tag']==tag and typed['default_asset_path'].startswith(child+'.')
        assert not edit(parent,'PATCH','nodes',NodeGuid=dynamic,bSetSubtree=True,SubtreePath=child,bSetInjectionTag=True,InjectionTag=tag)['would_change']
        reject(parent,'PATCH','nodes',NodeGuid=dynamic,bSetSubtree=True,SubtreePath=decorated)
        reject(parent,'PATCH','nodes',NodeGuid=dynamic,bSetSubtree=True,SubtreePath=parent)
        reject(parent,'PATCH','nodes',NodeGuid=dynamic,bSetInjectionTag=True,InjectionTag='UE5MCP.NotRegistered.Fixture')
        reject(parent,'PATCH','nodes',NodeGuid=dynamic,Properties={'InjectionTag':'(TagName="UE5MCP.NotRegistered.Fixture")'})
        reject(parent,'PATCH','nodes',NodeGuid=dynamic,Properties={'injectiontag':'(TagName="UE5MCP.NotRegistered.Fixture")'})
        parallel=create(parent,'BTComposite_SimpleParallel')
        reject(parent,'POST','links',NodeGuid=parallel,TargetGuid=dynamic,PinIndex=0,bConfirm=True)
        edit(parent,'DELETE','nodes',NodeGuid=parallel,bConfirm=True)
        edit(parent,'PATCH','nodes',NodeGuid=dynamic,bSetSubtree=True,SubtreePath='')
        assert not node(inspect(parent),dynamic)['dynamic_subtree']['default_asset_path']
        call('POST','/editor/transactions/undo');assert node(inspect(parent),dynamic)['dynamic_subtree']==typed
        call('POST','/editor/transactions/redo');assert not node(inspect(parent),dynamic)['dynamic_subtree']['default_asset_path']
        call('POST','/editor/transactions/undo')
        edit(parent,'PATCH','nodes',NodeGuid=dynamic,bSetInjectionTag=True,InjectionTag='')
        assert not inspect(parent)['valid']
        call('POST','/editor/transactions/undo');assert inspect(parent)['valid']
        edit(parent,'POST','compile',bSave=True)
        trees={tree:persistent(inspect(tree)) for tree in [child,decorated,parent]}
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'trees':trees},indent=2));keep=True
        print('Dynamic defaults/tags, dry-run/no-op, cycle/decorated-default/unknown-tag guards, clear and undo/redo: OK')
    finally:
        if not keep:cleanup(paths)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['tags','prepare','verify','cleanup']);p.add_argument('--base',default='http://127.0.0.1:8080')
    args=p.parse_args();run(args.base,args.phase)
