"""Rendered Audio Bus signal -> native envelope follower -> bounded live recordings."""
import argparse
import math
import struct
import time
import uuid
import wave
from pathlib import Path
import httpx

PROJECT=Path(__file__).resolve().parents[5]


def run(base):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()

    def until(fetch,predicate):
        end=time.monotonic()+25
        while time.monotonic()<end:
            s=fetch()
            if predicate(s):
                return s
            time.sleep(.05)
        raise AssertionError(s)

    def record(id,op='start',**extra):
        return call('POST','/audio/modulation/recordings',{'RecordingId':id,'Operation':op,'AssetPath':follower}|extra)

    def readings(id,**params):
        return call('GET','/audio/modulation/recordings',recording_id=id,**params)

    def event(id,op='play_sound',**extra):
        return call('POST','/audio/quartz/events',{'EventId':id,'Operation':op,'ClockName':name,'SoundPath':sound}|extra)

    def reject_record(**extra):
        r=httpx.post(base+'/audio/modulation/recordings',json={'RecordingId':'invalid','AssetPath':follower}|extra,timeout=180)
        assert r.status_code>=400,r.text

    def reject_event(id,op='play_sound',**extra):
        r=httpx.post(base+'/audio/quartz/events',json={'EventId':id,'Operation':op,'ClockName':name,'SoundPath':sound}|extra,timeout=180)
        assert r.status_code>=400,r.text

    created=[]
    started=False
    name='MFL_MCP_'+uuid.uuid4().hex[:8]
    source=PROJECT/'Saved'/'UE5MCP_Test'/(name+'.wav')
    sound='/Game/UE5MCP_Test/'+name+'.'+name
    def create(suffix,kind,**extra):
        asset=call('POST','/audio/modulation/create',{'AssetPath':'/Game/UE5MCP_Test/'+name+suffix,'AssetType':kind,'bSave':True}|extra)['asset_path']
        created.append(asset)
        return asset

    assert not call('GET','/editor/status')['is_playing']
    try:
        source.parent.mkdir(parents=True,exist_ok=True)
        rate=22050
        # Silence, sustained tone, silence: native follower must rise and decay.
        samples=[int(6000*math.sin(2*math.pi*440*i/rate)) if 1 <= i/rate < 3 else 0 for i in range(rate*6)]
        with wave.open(str(source),'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            w.writeframes(struct.pack('<'+'h'*len(samples),*samples))
        call('POST','/audio/waves/import',{'SourceFilePath':str(source),'DestinationPath':'/Game/UE5MCP_Test','AssetName':name,'bSave':True})
        created.append(sound)
        bus=create('_AudioBus','audio_bus')
        follower=create('_Follower','generator',GeneratorType='envelope_follower')
        empty=create('_EmptyFollower','generator',GeneratorType='envelope_follower')
        call('PATCH','/audio/modulation/generators/settings',{'AssetPath':follower,'bSetAudioBus':True,'AudioBusPath':bus,
             'Numeric':{'Gain':10,'AttackTime':.01,'ReleaseTime':.05},'bSave':True})
        before={a:call('GET','/audio/modulation/settings',asset_path=a) for a in [bus,follower,empty]}
        wave_before=call('GET','/audio/waves/source',asset_path=sound)
        call('POST','/editor/play',{'Operation':'start'}); started=True
        until(lambda:call('GET','/audio/modulation/runtime'),lambda s:s['modulation_available'])
        reject_record(AssetPath=empty)
        reject_record(AssetPath=sound)
        reject_record(RecordingId='bad id')
        reject_record(IntervalSeconds=0)
        reject_record(DurationSeconds=61)
        reject_record(DurationSeconds=60,IntervalSeconds=.01)
        assert not record('dry',bDryRun=True)['changed']
        assert httpx.get(base+'/audio/modulation/recordings',params={'recording_id':'dry'}).status_code>=400
        call('POST','/audio/quartz/control',{'ClockName':name,'Operation':'create'})
        call('POST','/audio/quartz/control',{'ClockName':name,'Operation':'start'})
        until(lambda:call('GET','/audio/quartz/clock',clock_name=name),lambda s:s['running'])
        send={'BusPath':bus,'SendLevel':1,'bPostEffect':False}
        reject_event('invalid',AudioBusSends=[send,send])
        reject_event('invalid',AudioBusSends=[send|{'BusPath':sound}])
        reject_event('invalid',AudioBusSends=[send|{'SendLevel':-1}])
        assert not event('sound_dry',AudioBusSends=[send],bDryRun=True)['submitted']
        assert httpx.get(base+'/audio/quartz/events',params={'event_id':'sound_dry'}).status_code>=400
        record('envelope',DurationSeconds=8,IntervalSeconds=.05)
        reject_record(RecordingId='envelope')
        event('signal',Quantization='QuarterNote',ReferencePoint='CurrentTimeRelative',VolumeMultiplier=.05,AudioBusSends=[send])
        until(lambda:call('GET','/audio/quartz/events',event_id='signal'),lambda s:any(e['value']=='CommandOnStarted' for e in s['events']))
        s=until(lambda:readings('envelope',limit=1024),lambda s:not s['running'])
        assert s['stop_reason']=='completed' and 20 < s['sample_count'] <= 1024,s
        assert s['audio_bus_path']==bus,s
        data=s['samples']
        assert all(0<=p['value_normalized']<=1 and math.isfinite(p['received_seconds']) for p in data)
        assert all(x['sequence']<y['sequence'] and x['received_seconds']<y['received_seconds'] for x,y in zip(data,data[1:])),data
        assert max(p['value_normalized'] for p in data if p['received_seconds']-s['started_seconds']>.5)>.02,s
        quiet=[p['value_normalized'] for p in data if .3 < p['received_seconds']-s['started_seconds'] < 1]
        assert len(quiet)>2 and max(quiet)<.01,s
        assert max(p['value_normalized'] for p in data[-10:])<.01,s
        page=readings('envelope',limit=1)
        next_page=readings('envelope',after_sequence=page['next_sequence'],limit=1)
        assert len(page['samples'])==1 and next_page['samples'][0]['sequence']==2
        assert not record('envelope','stop')['changed']
        record('envelope','release')
        assert httpx.get(base+'/audio/modulation/recordings',params={'recording_id':'envelope'}).status_code>=400
        # Live route updates should mute and restore real follower input while tone plays.
        record('routing',DurationSeconds=15,IntervalSeconds=.05)
        event('route_signal',Quantization='QuarterNote',ReferencePoint='CurrentTimeRelative',StartTime=1,PitchMultiplier=.25,VolumeMultiplier=.05,AudioBusSends=[send])
        until(lambda:readings('routing',limit=1024),lambda s:any(p['value_normalized']>.02 for p in s['samples'] if p['received_seconds']-s['started_seconds']>.5))
        reject_event('route_signal','set_audio_bus_sends',AudioBusSends=[send|{'SendLevel':0},send|{'BusPath':sound}])
        event('route_signal','set_audio_bus_sends',AudioBusSends=[send|{'SendLevel':0}],bDryRun=True)
        def latest():
            return call('GET','/audio/modulation/runtime',asset_path=follower)['value_normalized']
        until(latest,lambda v:v>.02)
        event('route_signal','set_audio_bus_sends',AudioBusSends=[send|{'SendLevel':0}])
        until(latest,lambda v:v<.01)
        event('route_signal','set_audio_bus_sends',AudioBusSends=[send])
        until(latest,lambda v:v>.02)
        record('routing','stop')
        n=readings('routing')['sample_count']; time.sleep(.2)
        assert readings('routing')['sample_count']==n
        record('routing','release')
        event('route_signal','release'); event('signal','release')
        for i in range(16):
            record('bound_'+str(i),DurationSeconds=.05,IntervalSeconds=.05)
        reject_record(RecordingId='overflow')
        for i in range(16):
            record('bound_'+str(i),'release')
        for a in before:
            assert call('GET','/audio/modulation/settings',asset_path=a)==before[a]
        assert call('GET','/audio/waves/source',asset_path=sound)==wave_before
        record('cleanup',DurationSeconds=60,IntervalSeconds=.1)
        call('POST','/editor/play',{'Operation':'stop'})
        until(lambda:call('GET','/editor/status'),lambda s:not s['is_playing'])
        call('POST','/editor/play',{'Operation':'start'})
        until(lambda:call('GET','/audio/modulation/runtime'),lambda s:s['modulation_available'])
        assert httpx.get(base+'/audio/modulation/recordings',params={'recording_id':'cleanup'}).status_code>=400
        print('Native rendered Audio Bus -> envelope follower recording, silence/rise/decay, live send mute/restore, cursor/lifecycle, dry-run, asset preservation and PIE cleanup: OK')
    finally:
        if started and call('GET','/editor/status')['is_playing']:
            clock=call('GET','/audio/quartz/clock',clock_name=name)
            if clock.get('exists'):
                call('POST','/audio/quartz/control',{'ClockName':name,'Operation':'delete','bConfirm':True})
            call('POST','/editor/play',{'Operation':'stop'})
            until(lambda:call('GET','/editor/status'),lambda s:not s['is_playing'])
        for a in reversed(created):
            call('POST','/assets/delete',{'AssetPath':a})
        source.unlink(missing_ok=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://127.0.0.1:8080')
    run(p.parse_args().base_url)
