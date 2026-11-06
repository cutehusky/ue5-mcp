"""Native random reachable/navigable points verified through real path queries."""
import json
import time
import httpx
from smoke_navigation_mesh import run as mesh_run, STATE


def run(base='http://127.0.0.1:8080'):
    def call(method,route,body=None):
        r=httpx.request(method,base+route,json=body,timeout=600)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def sample(**kw):
        return call('POST','/navigation/query',{'Operation':'random_reachable','Start':{'X':-600,'Y':0,'Z':40},'Radius':200,'SampleCount':32}|kw)
    assert not STATE.exists(),'Verify or clean the existing native mesh fixture first'
    try:
        mesh_run(base,'prepare');state=json.loads(STATE.read_text())
        call('POST','/worlds/load',{'WorldPath':state['map'],'DirtyPolicy':'discard','bConfirm':True})
        before=call('GET','/navigation/inspect')
        for op in ['random_reachable','random_navigable']:
            s=sample(Operation=op);assert s['queried'] and s['successful_samples']>0,s
            for point in s['samples']:
                if not point['success']:
                    assert 'location' not in point
                    continue
                p=point['location'];assert (p['X']+600)**2+p['Y']**2<=201**2,p
                q=call('POST','/navigation/query',{'Start':s['origin'],'End':p,'bProjectEndpoints':False})
                assert q['success'] and not q['partial'],q
        for body in [{'Radius':0},{'Radius':100001},{'SampleCount':0},{'SampleCount':33},{'WorldContext':'unknown'}]:
            r=httpx.post(base+'/navigation/query',json={'Operation':'random_reachable'}|body,timeout=180)
            assert r.status_code>=400,r.text
        failed=sample(Start={'X':100000,'Y':100000,'Z':100000})
        assert not failed['queried'] and failed['successful_samples']==0 and all('location' not in x for x in failed['samples']),failed
        assert call('GET','/navigation/inspect')['dirty']==before['dirty']
        # Split the floor with a real Null-area strip. Both sides remain
        # navigable, but there must be no path between them.
        call('POST','/navigation/modifiers',{'Operation':'create','Location':{'X':0,'Y':0,'Z':150},'Extent':{'X':120,'Y':1200,'Z':300},'AreaClass':'/Script/NavigationSystem.NavArea_Null'})
        end=time.monotonic()+60
        while call('GET','/navigation/inspect')['running_build_tasks']:
            assert time.monotonic()<end;time.sleep(.1)
        call('POST','/navigation/build',{'bConfirm':True})
        disconnected=call('POST','/navigation/query',{'Start':{'X':-600,'Y':0,'Z':40},'End':{'X':600,'Y':0,'Z':40}})
        assert not disconnected['success'],disconnected
        reachable=sample(Radius=1800)
        assert reachable['successful_samples']>0,reachable
        for point in reachable['samples']:
            if not point['success']:continue
            assert point['location']['X']<0,point
            q=call('POST','/navigation/query',{'Start':reachable['origin'],'End':point['location'],'bProjectEndpoints':False})
            assert q['success'] and not q['partial'],q
        # Native navigable sampling may return either island. Bound attempts
        # rather than forcing a seed or substituting generated coordinates.
        across=[]
        for _ in range(4):
            navigable=sample(Operation='random_navigable',Radius=1800)
            across.extend(p['location'] for p in navigable['samples'] if p['success'] and p['location']['X']>0)
            if across:break
        assert across,'No opposite-island observation in 128 native attempts; distribution gate inconclusive'
        for p in across:
            projected=call('POST','/navigation/query',{'Operation':'project','Start':p})
            assert projected['success'],projected
            q=call('POST','/navigation/query',{'Start':reachable['origin'],'End':p,'bProjectEndpoints':False})
            assert not q['success'],'Navigable island unexpectedly connected to origin'
        call('POST','/worlds/save',{})
        call('POST','/editor/play',{'Operation':'start'})
        try:
            for _ in range(100):
                if call('GET','/editor/status')['is_playing']:break
                time.sleep(.05)
            s=sample(WorldContext='pie');assert s['successful_samples']>0 and s['world_context']=='pie',s
            for point in s['samples']:
                if not point['success']:
                    assert 'location' not in point
                    continue
                q=call('POST','/navigation/query',{'WorldContext':'pie','Start':s['origin'],'End':point['location'],'bProjectEndpoints':False})
                assert q['success'],q
        finally:
            call('POST','/editor/play',{'Operation':'stop'})
            for _ in range(100):
                if not call('GET','/editor/status')['is_playing']:break
                time.sleep(.05)
        print('Native reachable/navigable sampling, disconnected-island distinction, actual path verification, planar radius, invalid bounds, failed projection and PIE queries: OK')
    finally:
        if STATE.exists():mesh_run(base,'cleanup')


if __name__=='__main__':run()
