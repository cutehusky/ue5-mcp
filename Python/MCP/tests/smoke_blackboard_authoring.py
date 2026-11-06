"""Typed Blackboard hierarchy, transaction, guards and cold persistence."""
import argparse
import json
import time
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'blackboard_authoring.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        try:return r.json()
        except ValueError:return r.text
    def inspect(path):return call('GET','/blackboards/inspect',asset_path=path)
    def edit(path,key,**kw):return call('PATCH','/blackboards/keys',{'AssetPath':path,'KeyName':key}|kw)
    def add(path,key,type='Vector',**kw):return call('POST','/blackboards/keys',{'AssetPath':path,'KeyName':key,'KeyType':'/Script/AIModule.BlackboardKeyType_'+type}|kw)
    def parent(path,value='',**kw):return call('PATCH','/blackboards/settings',{'AssetPath':path,'bSetParent':True,'ParentPath':value}|kw)
    def keys(path):return {k['name']:k for k in inspect(path)['keys']}
    def reject(method,route,body):
        r=httpx.request(method,base+route,json=body,timeout=180);assert r.status_code>=400,r.text
    def undo():call('POST','/editor/transactions/undo')
    def redo():call('POST','/editor/transactions/redo')
    def save(path):call('POST','/assets/save',{'AssetPath':path})
    def cleanup(paths):
        for path in reversed(paths):call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['paths']);return
        for path,want in state['snapshots'].items():
            got=inspect(path)
            for field in ['parent_path','keys','inherited_keys','has_synchronized_keys','validation']:
                assert got[field]==want[field],(path,field,got[field],want[field])
            assert not got['dirty'],got
        print('Cold Blackboard hierarchy, IDs, metadata, type replacement and synchronization flags: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous Blackboard fixture'
    paths=[];keep=False
    try:
        for name in ['Root','Child','Other']:
            paths.append(call('POST','/blackboards/create',{'AssetPath':'/Game/UE5MCP_Test/BB_'+name+'_'+uuid.uuid4().hex[:8]}))
        root,child,other=paths
        before=inspect(root)
        add(root,'Target',bDryRun=True);assert inspect(root)==before
        add(root,'Target',bSetCategory=True,Category='Movement',bSetDescription=True,Description='Destination feet',bSetInstanceSynced=True,bInstanceSynced=True,bSave=True)
        target=keys(root)['Target'];assert target['category']=='Movement' and target['description']=='Destination feet' and target['instance_synced']
        assert inspect(root)['has_synchronized_keys']
        reject('POST','/blackboards/keys',{'AssetPath':root,'KeyName':'target','KeyType':'/Script/AIModule.BlackboardKeyType_Int'})
        before=inspect(root)
        reject('PATCH','/blackboards/keys',{'AssetPath':root,'KeyName':'Target','KeyType':'/Script/Engine.Actor','bSetDescription':True,'Description':'must not apply'})
        assert inspect(root)==before
        add(child,'Local','Float',bSave=True)
        dry=parent(child,root,bDryRun=True);assert dry['would_change'] and inspect(child)['parent_path']==''
        parent(child,root,bSave=True)
        inherited=inspect(child);assert inherited['parent_path']==root+'.'+root.rsplit('/',1)[1]
        assert {k['name'] for k in inherited['inherited_keys']}==set(keys(root))
        assert 'SelfActor' not in keys(child) and inherited['has_synchronized_keys']
        assert keys(child)['Local']['key_id']==len(keys(root))
        reject('PATCH','/blackboards/keys',{'AssetPath':child,'KeyName':'Target','NewKeyName':'Bad'})
        reject('POST','/blackboards/keys',{'AssetPath':child,'KeyName':'TARGET','KeyType':'/Script/AIModule.BlackboardKeyType_Int'})
        reject('PATCH','/blackboards/settings',{'AssetPath':root,'bSetParent':True,'ParentPath':child,'bConfirm':True})
        reject('POST','/blackboards/keys',{'AssetPath':root,'KeyName':'Local','KeyType':'/Script/AIModule.BlackboardKeyType_Int'})
        reject('PATCH','/blackboards/keys',{'AssetPath':root,'KeyName':'SelfActor','NewKeyName':'Bad'})
        dry=edit(root,'Target',NewKeyName='Goal',bDryRun=True)
        assert child in dry['referencer_packages'] and 'Target' in keys(root)
        reject('PATCH','/blackboards/keys',{'AssetPath':root,'KeyName':'Target','NewKeyName':'Goal'})
        edit(root,'Target',NewKeyName='Goal',bConfirm=True)
        assert 'Goal' in keys(root) and 'Goal' in {k['name'] for k in inspect(child)['inherited_keys']}
        undo();assert 'Target' in keys(root) and 'Target' in {k['name'] for k in inspect(child)['inherited_keys']}
        redo();assert 'Goal' in keys(root)
        edit(root,'Goal',bSetInstanceSynced=True,bInstanceSynced=False)
        assert not inspect(child)['has_synchronized_keys']
        undo();assert inspect(child)['has_synchronized_keys']
        redo();assert not inspect(child)['has_synchronized_keys']
        edit(root,'Goal',KeyType='/Script/AIModule.BlackboardKeyType_Int',bConfirm=True)
        assert keys(root)['Goal']['type'].endswith('BlackboardKeyType_Int')
        add(root,'Temporary','Bool')
        old_id=keys(child)['Local']['key_id']
        call('DELETE','/blackboards/keys',{'AssetPath':root,'KeyName':'Temporary','bConfirm':True})
        assert keys(child)['Local']['key_id']==old_id-1
        undo();assert 'Temporary' in keys(root) and keys(child)['Local']['key_id']==old_id
        redo();assert 'Temporary' not in keys(root)
        parent(child,'',bConfirm=True)
        assert inspect(child)['parent_path']=='' and 'SelfActor' in keys(child)
        undo();assert inspect(child)['parent_path'] and 'SelfActor' not in keys(child)
        redo();assert inspect(child)['parent_path']==''
        parent(child,root,bSave=True)
        add(other,'Local','Bool',bSave=True)
        reject('PATCH','/blackboards/settings',{'AssetPath':root,'bSetParent':True,'ParentPath':other,'bConfirm':True})
        snap=inspect(root);noop=edit(root,'Goal',bSetCategory=True,Category='Movement');assert not noop['would_change'] and inspect(root)==snap
        call('POST','/editor/play',{'Operation':'start'})
        end=time.monotonic()+20
        while not call('GET','/editor/status')['is_playing']:
            assert time.monotonic()<end;time.sleep(.1)
        reject('PATCH','/blackboards/keys',{'AssetPath':root,'KeyName':'Goal','bSetDescription':True,'Description':'PIE forbidden'})
        call('POST','/editor/play',{'Operation':'stop'})
        end=time.monotonic()+20
        while call('GET','/editor/status')['is_playing']:
            assert time.monotonic()<end;time.sleep(.1)
        snapshots={}
        for path in paths:
            save(path);s=inspect(path);assert s['validation']['valid'] and not s['dirty'];snapshots[path]=s
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'snapshots':snapshots}));keep=True
        print('Blackboard metadata/type/rename/parent preflight, inherited IDs/sync, native undo/redo, dependency confirmation, dry-run/no-op and PIE guards: OK; restart and verify')
    finally:
        if not keep:
            if call('GET','/editor/status')['is_playing']:call('POST','/editor/play',{'Operation':'stop'})
            cleanup(paths)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080');p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)

