"""Native audio-thread snapshots of real playback, immutable state and bounded lifecycle."""
import argparse
import time
import uuid
from pathlib import Path
import httpx
from smoke_sound_wave_import_live import write_wav

PROJECT=Path(__file__).resolve().parents[5]


def run(base):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()

    def until(fetch,predicate):
        end=time.monotonic()+20
        while time.monotonic()<end:
            s=fetch()
            if predicate(s):
                return s
            time.sleep(.05)
        raise AssertionError(s)

    def control(id,op='capture',**extra):
        return call('POST','/audio/diagnostics/captures',{'CaptureId':id,'Operation':op}|extra)

    def inspect(id):
        return call('GET','/audio/diagnostics/captures',capture_id=id)

    def capture(id=None,**extra):
        keep=id is not None
        id=id or 'probe_'+uuid.uuid4().hex[:8]
        control(id,**extra)
        s=until(lambda:inspect(id),lambda s:s['ready'])
        if not keep:
            control(id,'release')
        return s

    def reject(**extra):
        r=httpx.post(base+'/audio/diagnostics/captures',json={'CaptureId':'invalid'}|extra,timeout=180)
        assert r.status_code>=400,r.text

    name='MDA_MCP_'+uuid.uuid4().hex[:8]
    source=PROJECT/'Saved'/'UE5MCP_Test'/(name+'.wav')
    sound='/Game/UE5MCP_Test/'+name+'.'+name
    def event(id,op='play_sound',**extra):
        return call('POST','/audio/quartz/events',{'EventId':id,'Operation':op,'ClockName':name,'SoundPath':sound}|extra)

    def row(s,path):
        return next((x for x in s['sounds'] if x['component_path']==path),None)

    imported=False
    started=False
    assert not call('GET','/editor/status')['is_playing']
    reject()
    try:
        write_wav(source,12)
        call('POST','/audio/waves/import',{'SourceFilePath':str(source),'DestinationPath':'/Game/UE5MCP_Test','AssetName':name,'bSave':True})
        imported=True
        before=call('GET','/audio/waves/source',asset_path=sound)
        call('POST','/editor/play',{'Operation':'start'}); started=True
        until(lambda:call('GET','/editor/status'),lambda s:s['is_playing'])
        reject(CaptureId='bad id'); reject(Limit=0); reject(Limit=513)
        assert not control('dry',bDryRun=True)['command_submitted']
        assert httpx.get(base+'/audio/diagnostics/captures',params={'capture_id':'dry'}).status_code>=400
        baseline=capture('baseline')
        config=baseline['device_configuration_at_capture']
        assert config['mixer'] and config['sample_rate']>0 and config['output_channels']>0 and config['callback_frames']>0 and config['output_buffers']>0,baseline
        assert baseline['captured_seconds']>=baseline['requested_seconds'],baseline
        reject(CaptureId='baseline')
        control('baseline','release',bDryRun=True)
        assert inspect('baseline')==baseline
        control('baseline','release')
        call('POST','/audio/quartz/control',{'ClockName':name,'Operation':'create'})
        call('POST','/audio/quartz/control',{'ClockName':name,'Operation':'start'})
        until(lambda:call('GET','/audio/quartz/clock',clock_name=name),lambda s:s['running'])
        for id,pitch in [('one',.5),('two',.25)]:
            event(id,Quantization='QuarterNote',ReferencePoint='CurrentTimeRelative',VolumeMultiplier=.03,PitchMultiplier=pitch)
            until(lambda:call('GET','/audio/quartz/events',event_id=id),lambda s:any(e['value']=='CommandOnStarted' for e in s['events']))
        paths={id:call('GET','/audio/quartz/events',event_id=id)['audio_component']['component_path'] for id in ['one','two']}
        s=until(capture,lambda s:all(row(s,p) is not None for p in paths.values()))
        assert s['device_active_sound_count']>=s['world_active_sound_count']>=2,s
        for id,pitch in [('one',.5),('two',.25)]:
            r=row(s,paths[id])
            assert r['sound_path']==sound and r['ui_sound'] and not r['paused'],r
            assert abs(r['volume_multiplier']-.03)<1e-6 and abs(r['pitch_multiplier']-pitch)<1e-6,r
        first=capture('frozen')
        time.sleep(.3)
        assert inspect('frozen')==first
        later=capture()
        assert row(later,paths['one'])['playback_seconds']>row(first,paths['one'])['playback_seconds']
        truncated=capture(Limit=1)
        assert truncated['truncated'] and len(truncated['sounds'])==1 and truncated['world_active_sound_count']>=2,truncated
        event('one','pause_sound')
        paused=until(capture,lambda s:row(s,paths['one']) is not None and row(s,paths['one'])['paused'])
        assert not row(paused,paths['two'])['paused'],paused
        event('one','resume_sound')
        until(capture,lambda s:row(s,paths['one']) is not None and not row(s,paths['one'])['paused'])
        event('one','stop_sound')
        until(capture,lambda s:row(s,paths['one']) is None and row(s,paths['two']) is not None)
        # Old state remains frozen even as the real source stops.
        assert inspect('frozen')==first
        old=row(first,paths['one'])
        event('one','release')
        resolved=inspect('frozen')
        after=next(x for x in resolved['sounds'] if x['audio_component_id']==old['audio_component_id'])
        assert after['component_path']=='' and resolved['captured_seconds']==first['captured_seconds'],resolved
        assert {k:v for k,v in after.items() if k!='component_path'}=={k:v for k,v in old.items() if k!='component_path'},after
        control('frozen','release')
        # Releasing queued requests must keep native device lifetime safe.
        for i in range(8):
            control('queued_'+str(i)); control('queued_'+str(i),'release')
        for i in range(16):
            control('bound_'+str(i))
        reject(CaptureId='overflow')
        for i in range(16):
            control('bound_'+str(i),'release')
        assert call('GET','/audio/waves/source',asset_path=sound)==before
        control('cleanup')
        call('POST','/editor/play',{'Operation':'stop'})
        until(lambda:call('GET','/editor/status'),lambda s:not s['is_playing'])
        call('POST','/editor/play',{'Operation':'start'})
        until(lambda:call('GET','/editor/status'),lambda s:s['is_playing'])
        assert httpx.get(base+'/audio/diagnostics/captures',params={'capture_id':'cleanup'}).status_code>=400
        fresh=capture()
        assert not any(x['sound_path']==sound for x in fresh['sounds']),fresh
        print('Native audio-thread playback snapshots, device configuration, immutable state, pause/stop, truncation, resource limits, release and PIE cleanup: OK')
    finally:
        if started and call('GET','/editor/status')['is_playing']:
            clock=call('GET','/audio/quartz/clock',clock_name=name)
            if clock.get('exists'):
                call('POST','/audio/quartz/control',{'ClockName':name,'Operation':'delete','bConfirm':True})
            call('POST','/editor/play',{'Operation':'stop'})
            until(lambda:call('GET','/editor/status'),lambda s:not s['is_playing'])
        if imported:
            call('POST','/assets/delete',{'AssetPath':sound})
        source.unlink(missing_ok=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://127.0.0.1:8080')
    run(p.parse_args().base_url)
