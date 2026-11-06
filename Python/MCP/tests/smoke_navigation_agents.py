"""Real native PIE character/controller movement and bounded actor lifetime."""
import math
import json
import time
import httpx
from smoke_navigation_mesh import run as mesh_run, STATE


def run(base='http://127.0.0.1:8080'):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        try:return r.json()
        except ValueError:return r.text
    def control(id='walker',op='create',**kw):return call('POST','/navigation/agents',{'ProbeId':id,'Operation':op}|kw)
    def inspect(id='walker',**kw):return call('GET','/navigation/agents',probe_id=id,**kw)
    def until(fetch,predicate,seconds=25):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            s=fetch()
            if predicate(s):return s
            time.sleep(.1)
        raise AssertionError(s)
    def reject(**kw):
        r=httpx.post(base+'/navigation/agents',json={'ProbeId':'walker'}|kw,timeout=180)
        assert r.status_code>=400,r.text
    def play(start):
        call('POST','/editor/play',{'Operation':'start' if start else 'stop'})
        until(lambda:call('GET','/editor/status'),lambda s:s['is_playing']==start)
    assert not STATE.exists(),'Verify previous mesh fixture first'
    reject()
    try:
        mesh_run(base,'prepare');state=json.loads(STATE.read_text())
        call('POST','/worlds/load',{'WorldPath':state['map'],'DirtyPolicy':'discard','bConfirm':True})
        wall=call('POST','/editor/actors/spawn',{'AssetPath':'/Engine/BasicShapes/Cube.Cube','Location':{'X':0,'Y':0,'Z':150}})
        call('PATCH','/editor/actors/transform',{'ActorPath':wall,'bSetScale':True,'Scale':{'X':2,'Y':10,'Z':3}})
        until(lambda:call('GET','/navigation/inspect'),lambda s:s['running_build_tasks']==0)
        call('POST','/navigation/build',{'bConfirm':True,'bSave':True})
        before=call('GET','/worlds/settings')
        play(True)
        for kw in [{'Speed':0},{'DurationSeconds':121},{'ProbeId':'bad id'},{'Location':{'X':1e6,'Y':1e6,'Z':1e6}}]:reject(**kw)
        control(bDryRun=True,Location={'X':-600,'Y':0,'Z':40})
        assert httpx.get(base+'/navigation/agents',params={'probe_id':'walker'}).status_code>=400
        control(Location={'X':-600,'Y':0,'Z':40},DurationSeconds=60,Speed=300)
        initial=inspect();assert initial['pawn_alive'] and initial['state']=='active',initial
        reject();reject(Operation='move',FilterClass='/Script/Engine.Actor')
        assert inspect()['path_status'].endswith('Idle')
        control(op='move',Destination={'X':600,'Y':0,'Z':40},bDryRun=True)
        assert inspect()['path_status'].endswith('Idle')
        control(op='move',Destination={'X':600,'Y':0,'Z':40})
        moving=until(inspect,lambda s:s['path_status'].endswith('Moving') and math.dist([s['location']['X'],s['location']['Y']],[initial['location']['X'],initial['location']['Y']])>80)
        assert moving['last_submission']=='RequestSuccessful',moving
        control(op='pause');paused=inspect();assert paused['path_status'].endswith('Paused'),paused
        time.sleep(.4);still=inspect();assert math.dist([paused['location']['X'],paused['location']['Y']],[still['location']['X'],still['location']['Y']])<5,(paused,still)
        control(op='resume')
        positions=[]
        def sample():
            s=inspect();positions.append(s['location']);return s
        done=until(sample,lambda s:any(e['result'].endswith('Success') for e in s['events']))
        assert any(abs(p['Y'])>400 for p in positions),positions
        assert math.dist([done['location']['X'],done['location']['Y']],[600,0])<90,done
        assert done['path_status'].endswith('Idle') and not done['path_partial'],done
        first=done['events'][-1]['sequence']
        assert inspect(after_sequence=first)['events']==[]
        control(op='move',Destination={'X':-600,'Y':0,'Z':40})
        until(inspect,lambda s:s['path_status'].endswith('Moving'))
        control(op='stop')
        aborted=until(inspect,lambda s:any(e['sequence']>first and e['result'].endswith('Aborted') for e in s['events']))
        assert aborted['path_status'].endswith('Idle'),aborted
        page=inspect(limit=1);assert len(page['events'])==1,page
        next_page=inspect(after_sequence=page['next_sequence'],limit=1)
        assert len(next_page['events'])==1 and next_page['events'][0]['sequence']>page['next_sequence'],next_page
        control(op='release');assert httpx.get(base+'/navigation/agents',params={'probe_id':'walker'}).status_code>=400
        control('expiry',Location={'X':-600,'Y':0,'Z':40},DurationSeconds=.3)
        expired=until(lambda:inspect('expiry'),lambda s:s['state']=='expired')
        assert not expired['pawn_alive'],expired
        control('expiry','release')
        for i in range(16):control('bound_'+str(i),Location={'X':-600,'Y':0,'Z':40},DurationSeconds=.2)
        reject(ProbeId='overflow')
        for i in range(16):control('bound_'+str(i),'release')
        control('cleanup',Location={'X':-600,'Y':0,'Z':40})
        play(False)
        assert call('GET','/worlds/settings')==before,'Runtime probe changed editor settings/package'
        play(True)
        assert httpx.get(base+'/navigation/agents',params={'probe_id':'cleanup'}).status_code>=400
        control('cleanup',Location={'X':-600,'Y':0,'Z':40});control('cleanup','release')
        play(False)
        print('Native physical movement around a wall, pause/resume, completion/abort callbacks, event cursor, dry-run/preflight, expiry/release, editor isolation and two-PIE cleanup: OK')
    finally:
        if call('GET','/editor/status')['is_playing']:play(False)
        if STATE.exists():mesh_run(base,'cleanup')


if __name__=='__main__':run()
