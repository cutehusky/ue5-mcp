"""Smart-only proxy authoring and native PIE area toggles without rebuilding."""
import argparse
import json
import time
import httpx
from smoke_navigation_mesh import run as run_mesh, STATE as MESH_STATE, PROJECT

STATE=PROJECT/'Saved'/'UE5MCP_Test'/'navigation_smart.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(context='editor',path=''):
        return call('GET','/navigation/links',actor_path=path,world_context=context)
    def row(path):return inspect(path=path)['proxies'][0]
    def edit(op='update',**kw):return call('POST','/navigation/smart-links',{'Operation':op}|kw)
    def query(context='editor',**kw):return call('POST','/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40},'WorldContext':context}|kw)
    def connected(s):return s['success'] and any(x['off_mesh_connection'] for x in s['points'])
    def build(**kw):
        end=time.monotonic()+60
        while call('GET','/navigation/inspect')['running_build_tasks']:
            assert time.monotonic()<end;time.sleep(.1)
        return call('POST','/navigation/build',{'bConfirm':True}|kw)
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True});assert s['success'],s
    def reject(route,body):
        r=httpx.post(base+route,json=body,timeout=180);assert r.status_code>=400,r.text
    def play(start):
        call('POST','/editor/play',{'Operation':'start' if start else 'stop'})
        end=time.monotonic()+20
        while call('GET','/editor/status')['is_playing']!=start:
            assert time.monotonic()<end;time.sleep(.05)
    def cleanup():
        if call('GET','/editor/status')['is_playing']:play(False)
        if MESH_STATE.exists():run_mesh(base,'cleanup')
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup();return
        diagnostics=STATE.with_name('navigation_smart_diagnostics.json')
        try:
            mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
            assert row(state['actor'])==state['row'],row(state['actor'])
            end=time.monotonic()+20
            while True:
                q=query();native=call('GET','/navigation/inspect')
                if connected(q) and not native['build_in_progress']:break
                assert time.monotonic()<end,(q,native,inspect())
                time.sleep(.1)
            after=inspect();assert not after['dirty'],after
            print('Smart-only proxy/component configuration and generated connectivity survived cold restart: OK')
        except Exception:
            # Preserve the exact saved reproduction instead of deleting it on a
            # failed cold-load assertion. Explicit cleanup remains available.
            snapshot={}
            for name,fetch in [('query',query),('navigation',lambda:call('GET','/navigation/inspect')),('links',inspect)]:
                try:snapshot[name]=fetch()
                except Exception as error:snapshot[name]={'inspection_error':str(error)}
            diagnostics.write_text(json.dumps(snapshot,indent=2))
            raise
        else:
            cleanup()
            diagnostics.unlink(missing_ok=True)
        return
    assert not STATE.exists() and not MESH_STATE.exists(),'Verify previous fixtures first'
    keep=False
    try:
        run_mesh(base,'prepare');mesh=json.loads(MESH_STATE.read_text());load(mesh['map'])
        call('POST','/navigation/modifiers',{'Operation':'create','Location':{'X':0,'Y':0,'Z':150},'Extent':{'X':120,'Y':1200,'Z':300},'AreaClass':'/Script/NavigationSystem.NavArea_Null'})
        build();assert not query()['success']
        req={'SmartLeft':{'X':-250,'Y':0,'Z':40},'SmartRight':{'X':250,'Y':0,'Z':40},'SmartDirection':'BothWays','bSmartLinkRelevant':True,'bEnabled':True,'bSetSmartAgents':True,'SmartAgentIndices':[0],'Label':'MCP_SmartGap'}
        before=inspect();dry=edit('create',**req,bDryRun=True);assert dry['would_change'] and not dry['changed'] and inspect()==before
        s=edit('create',**req);path=s['proxies'][0]['actor_path'];original=row(path)
        assert original['point_link_count']==0 and original['smart_link_relevant'] and original['smart_link']['enabled'],original
        assert not edit(ActorPath=path,**req)['changed']
        for change in [{'EnabledAreaClass':'/Script/Engine.Actor'},{'DisabledAreaClass':'/Script/Engine.Actor'},{'SmartDirection':'bad'},{'SmartAgentIndices':[16]},{'SmartRight':req['SmartLeft']}]:
            reject('/navigation/smart-links',{'ActorPath':path}|req|{'Location':{'X':99,'Y':0,'Z':0}}|change)
            assert row(path)==original,'Rejected smart request partially changed component/actor'
        build();assert connected(query()),query()
        edit(ActorPath=path,**(req|{'bEnabled':False}));build();assert not query()['success']
        call('POST','/editor/transactions/undo');assert row(path)['smart_link']['enabled']
        build();assert connected(query())
        call('POST','/editor/transactions/redo');build();assert not query()['success']
        edit(ActorPath=path,**(req|{'bSmartLinkRelevant':False}));build();assert not query()['success']
        edit(ActorPath=path,**req);build();assert connected(query())
        edit(ActorPath=path,**(req|{'SmartAgentIndices':[]}));build();assert not query()['success']
        call('POST','/editor/transactions/undo');build();assert connected(query())
        reject('/navigation/smart-links',{'Operation':'delete','ActorPath':path})
        edit('delete',ActorPath=path,bConfirm=True,bDryRun=True);assert row(path)['smart_link_relevant']
        edit('delete',ActorPath=path,bConfirm=True);build();assert not query()['success']
        call('POST','/editor/transactions/undo');build();assert connected(query())
        build(bSave=True);saved=row(path)
        reject('/navigation/query',{'WorldContext':'pie'})
        play(True)
        try:
            proxies=inspect('pie')['proxies'];runtime=next(x for x in proxies if x['label']==saved['label']);runtime_path=runtime['actor_path']
            assert runtime_path!=path and runtime['point_link_count']==0 and runtime['smart_link']['enabled'],runtime
            assert connected(query('pie'))
            editor_data=query()['nav_data_path']
            reject('/navigation/query',{'WorldContext':'pie','NavDataPath':editor_data})
            reject('/navigation/smart-links',{'Operation':'set_enabled','WorldContext':'pie','ActorPath':path,'bEnabled':False})
            reject('/navigation/query',{'WorldContext':'pie','PIEInstance':999})
            reject('/navigation/smart-links',{'ActorPath':path}|req)
            def toggle(enabled,**kw):return edit('set_enabled',WorldContext='pie',ActorPath=runtime_path,bEnabled=enabled,**kw)
            dry=toggle(False,bDryRun=True);assert dry['would_change'] and not dry['changed'] and connected(query('pie'))
            off=toggle(False);assert off['changed'] and off['runtime_only'] and off['running_build_tasks']==0,off
            assert not query('pie')['success'],'Native disabled area did not block PIE link'
            assert connected(query()) and row(path)['smart_link']['enabled'],'Runtime toggle changed editor proxy/data'
            assert not toggle(False)['changed']
            on=toggle(True);assert on['changed'] and on['running_build_tasks']==0 and connected(query('pie')),on
            assert row(path)==saved
            toggle(False)
        finally:play(False)
        assert row(path)==saved and not inspect()['dirty']
        play(True)
        try:
            fresh=next(x for x in inspect('pie')['proxies'] if x['label']==saved['label'])
            assert fresh['smart_link']['enabled'] and connected(query('pie')),'Runtime disabled state leaked into the next PIE session'
        finally:play(False)
        STATE.write_text(json.dumps({'actor':path,'row':saved}));load(mesh['original']);keep=True
        print('Native smart links: smart-only authoring/preflight/undo/relevance/agents, save, selected PIE queries, native no-rebuild enable/disable, editor isolation, no-op/dry-run and two-PIE cleanup: OK; restart and verify')
    finally:
        if not keep:cleanup()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
