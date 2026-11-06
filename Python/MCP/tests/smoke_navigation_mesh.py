"""Real native brush bounds, navmesh building, projection/pathfinding and persistence."""
import argparse
import json
import time
import uuid
from pathlib import Path
import httpx

PROJECT=Path(__file__).resolve().parents[5]
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'navigation_mesh.json'


def run(base,phase):
    def call(method,route,body=None):
        r=httpx.request(method,base+route,json=body,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        try: return r.json()
        except ValueError: return r.text
    def inspect(): return call('GET','/navigation/inspect')
    def until(fetch,predicate):
        end=time.monotonic()+60
        while time.monotonic()<end:
            s=fetch()
            if predicate(s): return s
            time.sleep(.1)
        raise AssertionError(s)
    def build(**kw):
        until(inspect,lambda s:not s['build_in_progress'])
        s=call('POST','/navigation/build',{'bConfirm':True}|kw)
        assert not s['build_in_progress'] and s['remaining_build_tasks']==0,s
        return s
    def query(**kw):
        return call('POST','/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40}}|kw)
    def bounds(op='create',**kw): return call('POST','/navigation/bounds',{'Operation':op}|kw)
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True}); assert s['success'],s
    def row(path): return next(x for x in inspect()['bounds'] if x['actor_path']==path)
    def reject(route,body):
        r=httpx.post(base+route,json=body,timeout=180); assert r.status_code>=400,r.text
    def cleanup(state):
        load(state['original']); call('POST','/assets/delete',{'AssetPath':state['map']}); STATE.unlink(missing_ok=True)
    assert not call('GET','/editor/status')['is_playing']
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup': cleanup(state);return
        try:
            load(state['map'])
            assert row(state['bounds'])['bounds_extent']=={'X':1000,'Y':1000,'Z':400},inspect()
            s=query(); assert s['success'] and not s['partial'] and abs(s['path_length']-state['length'])<1,s
            assert not inspect()['dirty'],inspect()
            build(bSave=True)
            rebuilt=query(); assert rebuilt['success'] and not rebuilt['search_limit_reached'],rebuilt
            print('Native bounds geometry and generated navmesh path survived cold restart: OK')
        finally: cleanup(state)
        return
    assert not STATE.exists(),'Verify previous fixture first'
    state={'original':call('GET','/worlds/inspect')['world_path'],'map':'/Game/UE5MCP_Test/MCP_Navigation_'+uuid.uuid4().hex[:8]}
    created=False;keep=False
    try:
        s=call('POST','/worlds/create',{'WorldPath':state['map'],'DirtyPolicy':'fail','bSave':True}); assert s['success'],s;created=True
        call('PATCH','/worlds/settings',{'bSetNavigation':True,'bConfirm':True,'Navigation':{
            'ConfigClass':'/Script/UE5_MCP.PersistentNavigationSystemConfig','bSetSystemClass':True,'SystemClass':'/Script/NavigationSystem.NavigationSystemV1',
            'bSetSupportedAgents':True,'SupportedAgentIndices':[0],'bSetDefaultAgentName':True,'DefaultAgentName':'',
            'BoolSettings':{'bAutoSpawnMissingNavData':False,'bStrictlyStatic':True}}})
        before=inspect()
        assert bounds(bDryRun=True)['changed'] and inspect()==before
        reject('/navigation/bounds',{'Operation':'create','Extent':{'X':0,'Y':100,'Z':100}})
        reject('/navigation/build',{})
        reject('/navigation/query',{})  # Never creates nav data as a query side effect.
        def cube(location,scale):
            actor=call('POST','/editor/actors/spawn',{'AssetPath':'/Engine/BasicShapes/Cube.Cube','Location':location})
            call('PATCH','/editor/actors/transform',{'ActorPath':actor,'bSetScale':True,'Scale':scale})
            return actor
        cube({'X':0,'Y':0,'Z':-50},{'X':20,'Y':20,'Z':1})
        wall=cube({'X':0,'Y':0,'Z':150},{'X':2,'Y':10,'Z':3})
        req={'Location':{'X':0,'Y':0,'Z':200},'Extent':{'X':1000,'Y':1000,'Z':400},'Label':'MCP_NavigationBounds'}
        s=bounds(**req); path=s['actor_path']; state['bounds']=path
        assert row(path)['bounds_extent']==req['Extent'],row(path)
        assert not bounds('update',ActorPath=path,**req)['changed']
        original_row=row(path)
        bounds('update',ActorPath=path,Location=req['Location'],Extent={'X':800,'Y':800,'Z':300})
        assert row(path)['bounds_extent']=={'X':800,'Y':800,'Z':300},row(path)
        call('POST','/editor/transactions/undo'); assert row(path)==original_row,row(path)
        call('POST','/editor/transactions/redo'); assert row(path)['bounds_extent']['X']==800,row(path)
        bounds('update',ActorPath=path,**req)
        s=build(bDryRun=True); assert not s['submitted'],s
        s=build(); assert s['submitted'] and s['nav_data_count']>=1,s
        blocked=query(); assert blocked['success'] and not blocked['partial'] and blocked['path_length']>1300,blocked
        assert any(abs(p['location']['Y'])>500 for p in blocked['points']),blocked
        projection=query(Operation='project'); assert projection['success'] and projection['start_projected'],projection
        assert abs(projection['start']['Z'])<30,projection
        truncated=query(MaxPoints=1); assert truncated['truncated'] and len(truncated['points'])==1 and truncated['point_count']>=3,truncated
        far=query(Start={'X':100000,'Y':100000,'Z':100000}); assert not far['success'] and not far['queried'],far
        chosen=query(NavDataPath=blocked['nav_data_path'],bProjectEndpoints=False); assert chosen['success'],chosen
        for kw in [{'MaxSearchNodes':0},{'MaxPoints':1025},{'CostLimit':0},{'FilterClass':'/Script/Engine.Actor'},{'NavDataPath':wall},{'WorldPath':'/Game/Wrong'}]:
            reject('/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40}}|kw)
        call('PATCH','/editor/actors/transform',{'ActorPath':wall,'bSetScale':True,'Scale':{'X':2,'Y':30,'Z':3}})
        build()
        partial=query(bAllowPartial=True); assert partial['success'] and partial['partial'],partial
        forbidden=query(bAllowPartial=False); assert not forbidden['success'],forbidden
        call('DELETE','/editor/actors',{'ActorPath':wall,'bConfirm':True})
        build()
        direct=query(); assert direct['success'] and direct['path_length']<blocked['path_length']-100,direct
        assert abs(direct['path_length']-1200)<10,direct
        reject('/navigation/bounds',{'Operation':'delete','ActorPath':path})
        bounds('delete',ActorPath=path,bConfirm=True,bDryRun=True); assert row(path)==original_row
        bounds('delete',ActorPath=path,bConfirm=True); assert not inspect()['bounds'],inspect()
        call('POST','/editor/transactions/undo'); assert row(path)==original_row,row(path)
        build(bSave=True)
        state['length']=query()['path_length']
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps(state))
        load(state['original']);keep=True
        print('Native brush bounds CRUD/undo, dry-run/guards, blocking build, real obstacle detour, projection, partial-path policy, query limits/truncation and rebuilt direct path: OK; restart and verify')
    finally:
        if created and not keep: cleanup(state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
