"""Native Blueprint filter costs/exclusions, cache invalidation and cold persistence."""
import argparse
import json
import time
import uuid
import httpx
from smoke_navigation_mesh import run as run_mesh, STATE as MESH_STATE, PROJECT

STATE=PROJECT/'Saved'/'UE5MCP_Test'/'navigation_filter.json'
AREA='/Script/NavigationSystem.NavArea_Default'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path): return call('GET','/navigation/filters',asset_path=path)
    def edit(path,**kw): return call('POST','/navigation/filters',{'AssetPath':path}|kw)
    def query(cls='',**kw): return call('POST','/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40},'FilterClass':cls}|kw)
    def cost(cls=''):
        s=call('POST','/navigation/query',{'Operation':'inspect_filter','FilterClass':cls})
        assert 1<=s['area_capacity']<=256 and not s['truncated'],s
        assert s['include_flags']==(65535 if cls else 32767) and s['exclude_flags']==0,s
        return next(x for x in s['areas'] if x['area_class']==AREA)
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True});assert s['success'],s
    def settings(s): return {k:s[k] for k in ['areas','include_flags','exclude_flags','filter_class']}
    def area(cost=2,exclude=False): return {'AreaClass':AREA,'bOverrideTravelCost':True,'TravelCost':cost,'bExcluded':exclude}
    def cleanup(path):
        if MESH_STATE.exists(): run_mesh(base,'cleanup')
        r=httpx.get(base+'/navigation/filters',params={'asset_path':path},timeout=180)
        if r.is_success: call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    def unique(pairs):
        result={}
        for k,v in pairs:
            assert k not in result,'Duplicate JSON capability key: '+k
            result[k]=v
        return result
    capability=httpx.get(base+'/assets/capabilities',timeout=180)
    assert capability.is_success,capability.text
    caps=json.loads(capability.text,object_pairs_hook=unique)['families']
    for family in ['navigation','navigation_query_filter']:
        assert all(caps[family][flag] for flag in ['inspect','edit','spawn_or_create','compile_or_rebuild','validate','adapter_available']),caps[family]
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup': cleanup(state['asset']);return
        try:
            mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
            s=inspect(state['asset']);assert settings(s)==state['expected'] and not s['dirty'],s
            q=query(s['filter_class']);assert q['success'] and abs(q['path_cost']-state['cost'])<1,q
            assert abs(query()['path_cost']-state['baseline'])<1,'Custom filter changed native default filter'
            print('Native navigation filter Blueprint defaults and actual filtered path cost survived cold restart: OK')
        finally: cleanup(state['asset'])
        return
    assert not STATE.exists() and not MESH_STATE.exists(),'Verify previous fixtures first'
    path='/Game/UE5MCP_Test/MCP_NavigationFilter_'+uuid.uuid4().hex[:8]
    keep=False
    try:
        run_mesh(base,'prepare')
        mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
        baseline=query();assert baseline['success'],baseline
        dry=edit(path,Operation='create',bSetAreas=True,Areas=[area()],bDryRun=True)
        assert dry['would_change'] and not dry['changed'],dry
        assert httpx.get(base+'/navigation/filters',params={'asset_path':path}).status_code>=400
        s=edit(path,Operation='create',bSetAreas=True,Areas=[area()],bSave=True)
        assert s['changed'] and s['saved'] and not s['dirty'],s
        cls=s['filter_class'];before=inspect(path)
        doubled=query(cls);assert doubled['success'] and doubled['path_cost']>baseline['path_cost']*1.9,doubled
        assert cost(cls)['travel_cost']==2 and cost()['travel_cost']==1
        assert abs(doubled['path_length']-baseline['path_length'])<1,doubled
        assert not edit(path,bSetAreas=True,Areas=[area()],bSave=True)['changed']
        assert not edit(path,bSetAreas=True,Areas=[area()],bSave=True)['saved']
        bad=[{'Operation':'create'}, {'IncludeFlags':65536}, {'ExcludeFlags':-2}, {'Areas':[area()]},
             {'bSetAreas':True,'Areas':[area(),area()]}, {'bSetAreas':True,'Areas':[area(0)]},
             {'bSetAreas':True,'Areas':[{'AreaClass':'/Script/Engine.Actor'}]},
             {'bSetAreas':True,'Areas':[area() for _ in range(65)]}]
        for kw in bad:
            r=httpx.post(base+'/navigation/filters',json={'AssetPath':path}|kw,timeout=180)
            assert r.status_code>=400,r.text
            assert inspect(path)==before,'Rejected filter request mutated defaults/package state'
            assert abs(query(cls)['path_cost']-doubled['path_cost'])<1
        edit(path,bSetAreas=True,Areas=[area(5)],bDryRun=True)
        assert inspect(path)==before and abs(query(cls)['path_cost']-doubled['path_cost'])<1
        edit(path,bSetAreas=True,Areas=[area(5)])
        costly=query(cls);assert costly['success'] and costly['path_cost']>doubled['path_cost']*2.4,costly
        assert cost(cls)['travel_cost']==5
        call('POST','/editor/transactions/undo')
        assert inspect(path)['areas'][0]['travel_cost']==2,inspect(path)
        undone=query(cls);assert abs(undone['path_cost']-doubled['path_cost'])<1,undone
        assert cost(cls)['travel_cost']==2
        call('POST','/editor/transactions/redo')
        redone=query(cls);assert abs(redone['path_cost']-costly['path_cost'])<1,redone
        edit(path,bSetAreas=True,Areas=[area(5,True)])
        excluded=query(cls,bProjectEndpoints=False);assert not excluded['success'],excluded
        edit(path,bSetAreas=True,Areas=[])
        cleared=query(cls);assert cleared['success'] and abs(cleared['path_cost']-baseline['path_cost'])<1,cleared
        edit(path,IncludeFlags=0);assert not query(cls)['success']
        edit(path,IncludeFlags=65535,ExcludeFlags=65535);assert not query(cls)['success']
        final=area(3)|{'bOverrideEnteringCost':True,'EnteringCost':321}
        s=edit(path,bSetAreas=True,Areas=[final],IncludeFlags=65535,ExcludeFlags=0,bSave=True)
        q=query(cls);assert q['success'] and q['path_cost']>baseline['path_cost']*2.9,q
        native=cost(cls);assert native['travel_cost']==3 and native['entering_cost']==321,native
        assert abs(query()['path_cost']-baseline['path_cost'])<1,'Cached native default filter was mutated'
        call('POST','/editor/play',{'Operation':'start'})
        try:
            for _ in range(100):
                if call('GET','/editor/status')['is_playing']:break
                time.sleep(.05)
            r=httpx.post(base+'/navigation/filters',json={'AssetPath':path,'IncludeFlags':0},timeout=180)
            assert r.status_code>=400,r.text
            assert settings(inspect(path))==settings(s)
        finally:
            call('POST','/editor/play',{'Operation':'stop'})
            for _ in range(100):
                if not call('GET','/editor/status')['is_playing']:break
                time.sleep(.05)
        state={'asset':path,'expected':settings(s),'cost':q['path_cost'],'baseline':baseline['path_cost']}
        STATE.write_text(json.dumps(state));load(mesh['original']);keep=True
        print('Native Blueprint filter: travel costs, exclusion, include/exclude flags, clear, cache invalidation, dry-run/no-op/preflight, undo/redo, default-filter isolation, save and PIE guard: OK; restart and verify')
    finally:
        if not keep:cleanup(path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
