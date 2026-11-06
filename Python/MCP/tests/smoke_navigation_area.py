"""Native project-defined areas: registration, costs/agents, undo and persistence."""
import argparse
import json
import time
import uuid
import httpx
from smoke_navigation_mesh import run as run_mesh, STATE as MESH_STATE, PROJECT

STATE=PROJECT/'Saved'/'UE5MCP_Test'/'navigation_area.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/navigation/areas',asset_path=path)
    def edit(path,**kw):return call('POST','/navigation/areas',{'AssetPath':path}|kw)
    def fields(s):return {k:s[k] for k in ['area_class','default_cost','entering_cost','draw_color','supported_agent_bits','supported_agent_indices','area_flags_read_only']}
    def registered(s):return any(x['registered'] for x in s['navigation_data_registration'])
    def query(cls=''):return call('POST','/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40},'FilterClass':cls})
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True});assert s['success'],s
    def build(**kw):
        end=time.monotonic()+60
        while call('GET','/navigation/inspect')['running_build_tasks']:
            assert time.monotonic()<end
            time.sleep(.1)
        return call('POST','/navigation/build',{'bConfirm':True}|kw)
    def cleanup(area,filter_path):
        if MESH_STATE.exists():run_mesh(base,'cleanup')
        for path in [filter_path,area]:
            if path and httpx.get(base+('/navigation/filters' if path==filter_path else '/navigation/areas'),params={'asset_path':path}).is_success:
                call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['area'],state['filter']);return
        try:
            mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
            s=inspect(state['area']);assert fields(s)==state['expected'] and not s['dirty'] and registered(s),s
            normal=query();filtered=query(state['filter_class'])
            assert normal['success'] and filtered['success'],(normal,filtered)
            assert abs(normal['path_cost']-state['cost'])<1,normal
            assert abs(filtered['path_length']-state['cheap_length'])<1,filtered
            print('Native custom area defaults, agent registration, modifier painting and filter behavior survived cold restart: OK')
        finally:cleanup(state['area'],state['filter'])
        return
    assert not STATE.exists() and not MESH_STATE.exists(),'Verify previous fixtures first'
    area='/Game/UE5MCP_Test/MCP_NavArea_'+uuid.uuid4().hex[:8];filter_path=area+'_Filter';keep=False
    try:
        run_mesh(base,'prepare');mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
        baseline=query();assert baseline['success']
        dry=edit(area,Operation='create',DefaultCost=1,bSetSupportedAgents=True,SupportedAgentIndices=[0],bDryRun=True)
        assert dry['would_change'] and not dry['changed'],dry
        assert httpx.get(base+'/navigation/areas',params={'asset_path':area}).status_code>=400
        s=edit(area,Operation='create',DefaultCost=1,EnteringCost=0,DrawColor=[30,180,220,255],bSetSupportedAgents=True,SupportedAgentIndices=[0],bSave=True)
        assert s['saved'] and s['validation']['valid'] and registered(s),s
        before=inspect(area);cls=s['area_class']
        bad=[{'Operation':'create'},{'DefaultCost':-2},{'EnteringCost':1e7},{'DrawColor':[1,2,3]},
             {'DrawColor':[0,256,0,255]},{'bSetSupportedAgents':True,'SupportedAgentIndices':[0,0]},
             {'bSetSupportedAgents':True,'SupportedAgentIndices':[16]},{'SupportedAgentIndices':[0]}]
        for kw in bad:
            r=httpx.post(base+'/navigation/areas',json={'AssetPath':area}|kw,timeout=180);assert r.status_code>=400,r.text
            assert inspect(area)==before,'Rejected area request partially changed defaults/registration'
        assert not edit(area,DefaultCost=1,EnteringCost=0,bSave=True)['changed']
        assert not edit(area,DefaultCost=1,EnteringCost=0,bSave=True)['saved']
        call('POST','/navigation/modifiers',{'Operation':'create','Location':{'X':0,'Y':0,'Z':150},'Extent':{'X':120,'Y':400,'Z':300},'AreaClass':cls})
        build();cheap=query();assert cheap['success'] and abs(cheap['path_length']-baseline['path_length'])<20,cheap
        edit(area,DefaultCost=40,bDryRun=True)
        assert fields(inspect(area))==fields(before)
        edit(area,DefaultCost=40);build();costly=query()
        assert costly['success'] and costly['path_length']>cheap['path_length']+100,costly
        call('POST','/editor/transactions/undo');assert inspect(area)['default_cost']==1
        build();undone=query();assert abs(undone['path_length']-cheap['path_length'])<20,undone
        call('POST','/editor/transactions/redo');assert inspect(area)['default_cost']==40
        build();assert query()['path_length']>cheap['path_length']+100
        edit(area,DefaultCost=1,EnteringCost=4000);build();entry=query()
        assert entry['success'] and entry['path_length']>cheap['path_length']+100,entry
        edit(area,bSetSupportedAgents=True,SupportedAgentIndices=[])
        none=inspect(area);assert none['supported_agent_indices']==[] and not registered(none),none
        edit(area,bSetSupportedAgents=True,SupportedAgentIndices=[0]);assert registered(inspect(area))
        final=edit(area,DefaultCost=25,EnteringCost=123,DrawColor=[200,40,80,255],bSave=True)
        build(bSave=True);normal=query();assert normal['success'] and normal['path_length']>cheap['path_length']+100,normal
        f=call('POST','/navigation/filters',{'AssetPath':filter_path,'Operation':'create','bSetAreas':True,'Areas':[{'AreaClass':cls,'bOverrideTravelCost':True,'TravelCost':1,'bOverrideEnteringCost':True,'EnteringCost':0}],'bSave':True})
        filtered=query(f['filter_class']);assert filtered['success'] and abs(filtered['path_length']-cheap['path_length'])<20,filtered
        call('POST','/editor/play',{'Operation':'start'})
        try:
            for _ in range(100):
                if call('GET','/editor/status')['is_playing']:break
                time.sleep(.05)
            r=httpx.post(base+'/navigation/areas',json={'AssetPath':area,'DefaultCost':1},timeout=180);assert r.status_code>=400
            assert fields(inspect(area))==fields(final)
        finally:
            call('POST','/editor/play',{'Operation':'stop'})
            for _ in range(100):
                if not call('GET','/editor/status')['is_playing']:break
                time.sleep(.05)
        state={'area':area,'filter':filter_path,'filter_class':f['filter_class'],'expected':fields(final),'cost':normal['path_cost'],'cheap_length':filtered['path_length']}
        STATE.write_text(json.dumps(state));load(mesh['original']);keep=True
        print('Native custom areas: cost/color/agent authoring, registration, preflight/dry-run/no-op, painted travel/entering costs, undo/redo refresh, filter override, save and PIE guards: OK; restart and verify')
    finally:
        if not keep:cleanup(area,filter_path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
