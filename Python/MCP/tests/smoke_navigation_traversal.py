"""Native smart-link reached multicast, owned-pawn wait/resume and cleanup."""
import json
import time
import httpx
from smoke_navigation_smart import run as smart_run, STATE
from smoke_navigation_mesh import STATE as MESH_STATE


def run(base='http://127.0.0.1:8080'):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base+route, json=body, params=params, timeout=600)
        assert r.is_success, (r.status_code, r.text)
        try: return r.json()
        except ValueError: return r.text
    def control(op, **kw):
        return call('POST', '/navigation/agents', {'ProbeId':'traverser','Operation':op}|kw)
    def inspect(): return call('GET','/navigation/agents',probe_id='traverser')
    def until(fetch, predicate, seconds=25):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            s=fetch()
            if predicate(s): return s
            time.sleep(.1)
        raise AssertionError(s)
    def reject(op, **kw):
        r=httpx.post(base+'/navigation/agents',json={'ProbeId':'traverser','Operation':op}|kw,timeout=180)
        assert r.status_code>=400,r.text
    def play(start):
        call('POST','/editor/play',{'Operation':'start' if start else 'stop'})
        until(lambda:call('GET','/editor/status'),lambda s:s['is_playing']==start)
    assert not STATE.exists() and not MESH_STATE.exists(),'Clean previous navigation fixtures first'
    try:
        smart_run(base,'prepare')
        mesh=json.loads(MESH_STATE.read_text()); saved=json.loads(STATE.read_text())
        call('POST','/worlds/load',{'WorldPath':mesh['map'],'DirtyPolicy':'discard','bConfirm':True})
        # Keep the lane clear of the default player pawn spawned at the origin.
        call('POST','/navigation/smart-links',{'Operation':'update','ActorPath':saved['actor'],'SmartLeft':{'X':-250,'Y':300,'Z':40},'SmartRight':{'X':250,'Y':300,'Z':40},'SmartDirection':'BothWays','bSmartLinkRelevant':True,'bEnabled':True})
        call('POST','/navigation/build',{'bConfirm':True,'bSave':True})
        before=call('GET','/navigation/links')
        play(True)
        links=call('GET','/navigation/links',world_context='pie')['proxies']
        link=next(x['actor_path'] for x in links if x['label']=='MCP_SmartGap')
        control('create',Location={'X':-600,'Y':300,'Z':40},Speed=100,DurationSeconds=90)
        reject('resume_link');reject('watch_link',SmartLinkPath=saved['actor'])
        control('watch_link',SmartLinkPath=link,bDryRun=True)
        assert inspect()['watched_smart_link']==''
        control('watch_link',SmartLinkPath=link)
        control('watch_link',SmartLinkPath=link)
        reject('watch_link',SmartLinkPath='/invalid')
        assert inspect()['watched_smart_link']==link
        control('move',Destination={'X':600,'Y':300,'Z':40})
        reached=until(inspect,lambda s:s['using_custom_link'] and any(e['kind']=='smart_link_reached' for e in s['events']))
        events=[e for e in reached['events'] if e['kind']=='smart_link_reached']
        assert len(events)==1 and events[0]['link_path']==link, reached
        reject('unwatch_link')
        control('resume_link',bDryRun=True);assert inspect()['using_custom_link']
        control('resume_link')
        done=until(inspect,lambda s:any(e['kind']=='move_completed' and e['result'].endswith('Success') for e in s['events']))
        assert abs(done['location']['X']-600)<90 and not done['using_custom_link'],done
        control('unwatch_link');assert inspect()['watched_smart_link']==''
        control('watch_link',SmartLinkPath=link)
        control('move',Destination={'X':-600,'Y':300,'Z':40})
        until(inspect,lambda s:s['using_custom_link'] and len([e for e in s['events'] if e['kind']=='smart_link_reached'])==2)
        control('release')
        control('create',Location={'X':-600,'Y':300,'Z':40},DurationSeconds=30)
        control('watch_link',SmartLinkPath=link)
        play(False)
        assert call('GET','/navigation/links')==before
        play(True)
        control('create',Location={'X':-600,'Y':300,'Z':40},DurationSeconds=3)
        fresh=next(x['actor_path'] for x in call('GET','/navigation/links',world_context='pie')['proxies'] if x['label']=='MCP_SmartGap')
        control('watch_link',SmartLinkPath=fresh)
        expired=until(inspect,lambda s:s['state']=='expired')
        assert not expired['pawn_alive'] and expired['watched_smart_link']==''
        control('release');play(False)
        print('Native smart-link callback/resume, single subscription, guards, release during traversal, PIE teardown and expiry: OK')
    finally:
        if call('GET','/editor/status')['is_playing']:play(False)
        if STATE.exists():smart_run(base,'cleanup')
        elif MESH_STATE.exists():
            from smoke_navigation_mesh import run as mesh_run
            mesh_run(base,'cleanup')

if __name__=='__main__':run()
