"""Real painted nav areas, boundary costs, replacement, brush undo and persistence."""
import argparse
import json
import time
import uuid
import httpx
from smoke_navigation_mesh import run as run_mesh, STATE as MESH_STATE, PROJECT

STATE=PROJECT/'Saved'/'UE5MCP_Test'/'navigation_modifier.json'
OBSTACLE='/Script/NavigationSystem.NavArea_Obstacle'
NULL='/Script/NavigationSystem.NavArea_Null'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect():return call('GET','/navigation/inspect')
    def row(path):return next(x for x in inspect()['modifiers'] if x['actor_path']==path)
    def edit(op='create',**kw):return call('POST','/navigation/modifiers',{'Operation':op}|kw)
    def query(cls='',**kw):return call('POST','/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40},'FilterClass':cls}|kw)
    def build(**kw):
        end=time.monotonic()+60
        while inspect()['running_build_tasks']:
            assert time.monotonic()<end,'Native generation did not finish'
            time.sleep(.1)
        s=call('POST','/navigation/build',{'bConfirm':True}|kw)
        assert not s['build_in_progress'],s
        return s
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True});assert s['success'],s
    def cleanup(path):
        if MESH_STATE.exists():run_mesh(base,'cleanup')
        if path and httpx.get(base+'/navigation/filters',params={'asset_path':path}).is_success:
            call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['filter']);return
        try:
            mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
            assert row(state['actor'])==state['row'],row(state['actor'])
            assert not inspect()['dirty']
            normal=query();filtered=query(state['class'])
            assert normal['success'] and filtered['success'],(normal,filtered)
            assert abs(normal['path_length']-state['normal_length'])<1,normal
            assert abs(filtered['path_cost']-state['filtered_cost'])<1,filtered
            print('Native modifier geometry/area references, painted navmesh and boundary-cost filter behavior survived cold restart: OK')
        finally:cleanup(state['filter'])
        return
    assert not STATE.exists() and not MESH_STATE.exists(),'Verify previous fixtures first'
    filter_path='/Game/UE5MCP_Test/MCP_ModifierFilter_'+uuid.uuid4().hex[:8]
    keep=False
    try:
        run_mesh(base,'prepare')
        mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
        baseline=query();assert baseline['success'] and abs(baseline['path_length']-1200)<10,baseline
        req={'Location':{'X':0,'Y':0,'Z':150},'Extent':{'X':120,'Y':400,'Z':300},'AreaClass':OBSTACLE,'Label':'MCP_PaintedRegion'}
        before=inspect()
        assert edit(**req,bDryRun=True)['changed'] and inspect()==before
        s=edit(**req);path=s['actor_path'];original=row(path)
        assert original['area_class']==OBSTACLE and original['bounds_extent']==req['Extent'],original
        assert not edit('update',ActorPath=path,**req)['changed']
        for change in [{'AreaClass':'/Script/Engine.Actor'},{'AreaClassToReplace':'/Script/Engine.Actor'},{'Extent':{'X':0,'Y':1,'Z':1}},{'WorldPath':'/Game/Wrong'}]:
            r=httpx.post(base+'/navigation/modifiers',json={'Operation':'update','ActorPath':path}|req|{'Location':{'X':99,'Y':99,'Z':99}}|change,timeout=180)
            assert r.status_code>=400,r.text
            assert row(path)==original,'Rejected request partially modified brush/metadata'
        build();painted=query()
        assert painted['success'] and painted['path_length']>baseline['path_length']+100,painted
        def filter_cost(enter):
            return call('POST','/navigation/filters',{'AssetPath':filter_path,'Operation':'update','bSetAreas':True,'Areas':[{
                'AreaClass':OBSTACLE,'bOverrideTravelCost':True,'TravelCost':1,'bOverrideEnteringCost':True,'EnteringCost':enter}]})
        s=call('POST','/navigation/filters',{'AssetPath':filter_path,'Operation':'create'})
        cls=s['filter_class'];filter_cost(0)
        cheap=query(cls);assert cheap['success'] and cheap['path_length']<painted['path_length']-100,cheap
        assert abs(cheap['path_length']-baseline['path_length'])<20,cheap
        filter_cost(5000)
        entry=query(cls);assert entry['success'] and entry['path_length']>cheap['path_length']+100,entry
        assert any(abs(x['location']['Y'])>350 for x in entry['points']),entry
        # Replace-only mode must not repaint floor polygons with a different source area.
        edit('update',ActorPath=path,**req,AreaClassToReplace=NULL)
        build();unpainted=query();assert abs(unpainted['path_length']-baseline['path_length'])<20,unpainted
        call('POST','/editor/transactions/undo');assert row(path)==original,row(path)
        build();assert query()['path_length']>baseline['path_length']+100
        edit('update',ActorPath=path,**(req|{'AreaClass':''}))
        build();assert abs(query()['path_length']-baseline['path_length'])<20
        call('POST','/editor/transactions/undo');assert row(path)==original
        build()
        edit('update',ActorPath=path,**(req|{'AreaClass':NULL,'Extent':{'X':120,'Y':1200,'Z':300}}))
        build();assert not query()['success']
        partial=query(bAllowPartial=True);assert partial['success'] and partial['partial'],partial
        call('POST','/editor/transactions/undo');assert row(path)==original,row(path)
        build();assert query()['success'] and query()['path_length']>baseline['path_length']+100
        r=httpx.post(base+'/navigation/modifiers',json={'Operation':'delete','ActorPath':path},timeout=180);assert r.status_code>=400
        edit('delete',ActorPath=path,bConfirm=True,bDryRun=True);assert row(path)==original
        edit('delete',ActorPath=path,bConfirm=True);assert not inspect()['modifiers']
        build();assert abs(query()['path_length']-baseline['path_length'])<20
        call('POST','/editor/transactions/undo');assert row(path)==original,row(path)
        build(bSave=True)
        call('POST','/navigation/filters',{'AssetPath':filter_path,'bSave':True})
        state={'actor':path,'row':row(path),'filter':filter_path,'class':cls,'normal_length':query()['path_length'],'filtered_cost':query(cls)['path_cost']}
        STATE.write_text(json.dumps(state));load(mesh['original']);keep=True
        print('Native modifier painting: area/brush CRUD, preflight/dry-run/no-op, cost-sensitive route choice, boundary entering costs, replace-only/disable, Null-area blocking, native undo/rebuild and save: OK; restart and verify')
    finally:
        if not keep:cleanup(filter_path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
