"""Native off-mesh point links: direction, areas/agents, undo and cold persistence."""
import argparse
import json
import time
import uuid
import httpx
from smoke_navigation_mesh import run as run_mesh, STATE as MESH_STATE, PROJECT

STATE=PROJECT/'Saved'/'UE5MCP_Test'/'navigation_links.json'
AREA='/Script/NavigationSystem.NavArea_Obstacle'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path=''):return call('GET','/navigation/links',actor_path=path)
    def row(path):return inspect(path)['proxies'][0]
    def edit(op='update',**kw):return call('POST','/navigation/links',{'Operation':op}|kw)
    def query(reverse=False,cls=''):
        return call('POST','/navigation/query',{'Start':{'X':600 if reverse else -600,'Y':0,'Z':40},'End':{'X':-600 if reverse else 600,'Y':0,'Z':40},'FilterClass':cls})
    def linked(s):return s['success'] and s['mesh_path_flags'] and any(p['off_mesh_connection'] for p in s['points'])
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True});assert s['success'],s
    def build(**kw):
        end=time.monotonic()+60
        while call('GET','/navigation/inspect')['running_build_tasks']:
            assert time.monotonic()<end;time.sleep(.1)
        return call('POST','/navigation/build',{'bConfirm':True}|kw)
    def cleanup(filter_path):
        if MESH_STATE.exists():run_mesh(base,'cleanup')
        if filter_path and httpx.get(base+'/navigation/filters',params={'asset_path':filter_path}).is_success:
            call('POST','/assets/delete',{'AssetPath':filter_path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['filter']);return
        try:
            mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
            assert row(state['actor'])==state['row'],row(state['actor'])
            assert linked(query()) and linked(query(True))
            assert not query(cls=state['filter_class'])['success']
            assert not inspect()['dirty']
            print('Native link proxy settings, bidirectional off-mesh connectivity and area filter survived cold restart: OK')
        finally:cleanup(state['filter'])
        return
    assert not STATE.exists() and not MESH_STATE.exists(),'Verify previous fixtures first'
    filter_path='/Game/UE5MCP_Test/MCP_LinkFilter_'+uuid.uuid4().hex[:8];keep=False
    try:
        run_mesh(base,'prepare');mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
        call('POST','/navigation/modifiers',{'Operation':'create','Location':{'X':0,'Y':0,'Z':150},'Extent':{'X':120,'Y':1200,'Z':300},'AreaClass':'/Script/NavigationSystem.NavArea_Null'})
        build();assert not query()['success'] and not query(True)['success']
        link={'Left':{'X':-250,'Y':0,'Z':40},'Right':{'X':250,'Y':0,'Z':40},'Direction':'LeftToRight','AreaClass':AREA,'bSetSupportedAgents':True,'SupportedAgentIndices':[0]}
        req={'PointLinks':[link],'Label':'MCP_GapConnection'}
        before=inspect();dry=edit('create',**req,bDryRun=True);assert dry['would_change'] and not dry['changed'] and inspect()==before
        s=edit('create',**req);path=s['proxies'][0]['actor_path'];original=row(path)
        assert original['point_links'][0]['requested_left_world']==link['Left'],original
        assert not edit(ActorPath=path,**req)['changed']
        for kw in [{'Direction':'bad'},{'AreaClass':'/Script/Engine.Actor'},{'SnapRadius':0},{'SupportedAgentIndices':[16]},{'Right':link['Left']}]:
            r=httpx.post(base+'/navigation/links',json={'ActorPath':path,'Location':{'X':99,'Y':0,'Z':0},'PointLinks':[link|kw]},timeout=180)
            assert r.status_code>=400,r.text
            assert row(path)==original,'Rejected link request partially changed actor/links'
        build();forward=query();assert linked(forward),forward
        assert not query(True)['success']
        both=link|{'Direction':'BothWays'}
        edit(ActorPath=path,PointLinks=[both]);build();assert linked(query()) and linked(query(True))
        edit(ActorPath=path,PointLinks=[link|{'Direction':'RightToLeft'}]);build()
        assert not query()['success'] and linked(query(True))
        call('POST','/editor/transactions/undo');assert row(path)['point_links'][0]['direction']=='BothWays'
        build();assert linked(query()) and linked(query(True))
        call('POST','/editor/transactions/redo');build();assert not query()['success'] and linked(query(True))
        edit(ActorPath=path,PointLinks=[both],Rotation={'Pitch':0,'Yaw':90,'Roll':0});build()
        assert abs(row(path)['point_links'][0]['requested_left_world']['Y']+250)<.01
        assert not query()['success'],'Rotated endpoints inside the gap must not create a connection'
        call('POST','/editor/transactions/undo');build();assert linked(query(True))
        edit(ActorPath=path,PointLinks=[both|{'SupportedAgentIndices':[]}]);build();assert not query()['success']
        call('POST','/editor/transactions/undo');build();assert linked(query(True))
        edit(ActorPath=path,PointLinks=[]);build();assert not query()['success'] and row(path)['point_link_count']==0
        call('POST','/editor/transactions/undo');build();assert linked(query(True))
        edit(ActorPath=path,PointLinks=[both]);build()
        f=call('POST','/navigation/filters',{'AssetPath':filter_path,'Operation':'create','bSetAreas':True,'Areas':[{'AreaClass':AREA,'bExcluded':True}],'bSave':True})
        assert not query(cls=f['filter_class'])['success'],'Excluding the link area must block connectivity'
        r=httpx.post(base+'/navigation/links',json={'Operation':'delete','ActorPath':path},timeout=180);assert r.status_code>=400
        edit('delete',ActorPath=path,bConfirm=True,bDryRun=True);assert row(path)['point_link_count']==1
        edit('delete',ActorPath=path,bConfirm=True);build();assert not query()['success']
        call('POST','/editor/transactions/undo');build();assert linked(query()) and linked(query(True))
        build(bSave=True)
        state={'actor':path,'row':row(path),'filter':filter_path,'filter_class':f['filter_class']}
        STATE.write_text(json.dumps(state));load(mesh['original']);keep=True
        print('Native simple links: real off-mesh connectivity, direction, agent masks, local/world rotation, empty-list disable, area exclusion, undo/rebuild, preflight/dry-run/no-op, delete/restore and save: OK; restart and verify')
    finally:
        if not keep:cleanup(filter_path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
