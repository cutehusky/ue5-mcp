"""Verify native Audio Component quantized playback in an idle running editor."""
import argparse
import time
import httpx
import uuid
from pathlib import Path
from smoke_sound_wave_import_live import write_wav


def run(base):
    clock_name = 'MCP_QSound_'+uuid.uuid4().hex[:8]
    no_audio_name = clock_name+'_NoAudio'
    source = Path(__file__).resolve().parents[5] / 'Saved' / 'UE5MCP_Test' / (clock_name+'.wav')
    sound_path = '/Game/UE5MCP_Test/'+clock_name+'.'+clock_name
    def call(method, path, body=None, **params):
        r = httpx.request(method, base+path, json=body, params=params, timeout=120)
        r.raise_for_status()
        return r.json()

    def event(id, op, **extra):
        return call('POST', '/audio/quartz/events', {'EventId': id, 'Operation': op,
                    'ClockName': clock_name, 'SoundPath': sound_path} | extra)

    def records(id):
        return call('GET', '/audio/quartz/events', event_id=id)

    def until(fetch, predicate):
        end = time.monotonic()+25
        while time.monotonic() < end:
            result = fetch()
            if predicate(result):
                return result
            time.sleep(.05)
        raise AssertionError(result)

    def reject(**extra):
        r = httpx.post(base+'/audio/quartz/events', json={'EventId': 'invalid', 'Operation': 'play_sound',
                       'ClockName': clock_name, 'SoundPath': sound_path} | extra, timeout=120)
        assert r.status_code >= 400, r.text

    assert not call('GET', '/editor/status')['is_playing']
    started = False
    imported = False
    extra_assets = []
    editor_parent = None
    for actor in call('GET', '/editor/actors', limit=10):
        components = call('GET', '/scene/actors/components', actor_path=actor['path'])['components']
        editor_parent = next((c['path'] for c in components if c['scene_component'] and c['registered']), None)
        if editor_parent:
            break
    assert editor_parent, 'Test requires a registered editor-world scene component'
    try:
        write_wav(source, 1)
        call('POST', '/audio/waves/import', {'SourceFilePath':str(source), 'DestinationPath':'/Game/UE5MCP_Test', 'AssetName':clock_name})
        imported = True
        for suffix, route in [('_Attenuation', '/audio/attenuations/create'), ('_Concurrency', '/audio/concurrencies/create')]:
            r = httpx.post(base+route, json={'AssetPath':'/Game/UE5MCP_Test/'+clock_name+suffix}, timeout=120)
            r.raise_for_status()
            extra_assets.append(r.text)
        attenuation, concurrency = extra_assets
        concurrency_before = call('GET', '/audio/concurrencies/inspect', asset_path=concurrency)
        attenuation_before = call('GET', '/audio/attenuations/settings', asset_path=attenuation)
        call('POST', '/editor/play', {'Operation': 'start'})
        started = True
        until(lambda:call('GET', '/editor/status'), lambda s:s['is_playing'])
        time.sleep(1)
        call('POST', '/audio/quartz/control', {'ClockName': clock_name, 'Operation': 'create'})
        call('POST', '/audio/quartz/control', {'ClockName': clock_name, 'Operation': 'start'})
        until(lambda:call('GET', '/audio/quartz/clock', clock_name=clock_name), lambda s:s['running'])
        reject(SoundPath='/Engine/NoSuchSound')
        reject(VolumeMultiplier=-1)
        reject(PitchMultiplier=0)
        reject(StartTime=-1)
        reject(FadeInDuration=-1)
        reject(Location={'X':1e12})
        reject(Rotation={'Yaw':1e9})
        reject(AttachSocket='missing')
        reject(AttachComponentPath='/Engine/EngineSounds/1kSineTonePing.1kSineTonePing')
        reject(AttachComponentPath=editor_parent)
        reject(AttenuationPath=sound_path)
        reject(ConcurrencyPath=sound_path)
        call('POST', '/audio/quartz/control', {'ClockName': no_audio_name, 'Operation': 'create', 'bUseAudioEngineClockManager': False})
        reject(ClockName=no_audio_name)
        assert not event('dry', 'play_sound', bDryRun=True)['submitted']
        assert httpx.get(base+'/audio/quartz/events', params={'event_id':'dry'}).status_code >= 400
        event('natural', 'play_sound', Quantization='QuarterNote', Multiplier=4,
              ReferencePoint='CurrentTimeRelative', PitchMultiplier=.125, VolumeMultiplier=.05, FadeInDuration=.05)
        s = until(lambda:records('natural'), lambda s:any(e['value']=='CommandOnStarted' for e in s['events']))
        queued = next(e for e in s['events'] if e['value']=='CommandOnQueued')
        played = next(e for e in s['events'] if e['value']=='CommandOnStarted')
        assert played['received_seconds']-queued['received_seconds'] > 1, s
        assert s['audio_component']['registered'] and s['audio_component']['playing'], s
        event('natural', 'pause_sound')
        assert records('natural')['audio_component']['play_state']=='Paused'
        assert not event('natural', 'resume_sound', bDryRun=True)['submitted']
        assert records('natural')['audio_component']['play_state']=='Paused'
        event('natural', 'resume_sound')
        s = until(lambda:records('natural'), lambda s:any(e['kind']=='native_audio_finished' for e in s['events']))
        assert not s['audio_component']['playing'], s
        event('natural', 'release')
        event('queued', 'play_sound', Quantization='QuarterNote', Multiplier=8, ReferencePoint='CurrentTimeRelative', VolumeMultiplier=.05)
        event('queued', 'stop_sound')
        time.sleep(5)
        s = records('queued')
        assert not s['audio_component']['playing'], s
        assert not any(e['value']=='CommandOnStarted' for e in s['events']), s
        event('queued', 'release')
        event('active', 'play_sound', Quantization='QuarterNote', Multiplier=1, ReferencePoint='CurrentTimeRelative', PitchMultiplier=.125, VolumeMultiplier=.05)
        until(lambda:records('active'), lambda s:any(e['value']=='CommandOnStarted' for e in s['events']))
        event('active', 'stop_sound')
        until(lambda:records('active'), lambda s:not s['audio_component']['playing'])
        event('active', 'release')
        event('release_pending', 'play_sound', Quantization='QuarterNote', Multiplier=8, ReferencePoint='CurrentTimeRelative', VolumeMultiplier=0)
        event('release_pending', 'release')
        assert httpx.get(base+'/audio/quartz/events', params={'event_id':'release_pending'}).status_code >= 400
        event('anchor', 'play_sound', Quantization='QuarterNote', Multiplier=64, ReferencePoint='CurrentTimeRelative', VolumeMultiplier=0,
              Location={'X':100, 'Y':200, 'Z':300})
        parent = records('anchor')['audio_component']['component_path']
        reject(AttachComponentPath=parent, AttachSocket='missing')
        assert not event('spatial_dry', 'play_sound', bDryRun=True, bSpatialized=True, AttachComponentPath=parent,
                         AttenuationPath=attenuation, ConcurrencyPath=concurrency)['submitted']
        assert httpx.get(base+'/audio/quartz/events', params={'event_id':'spatial_dry'}).status_code >= 400
        event('spatial', 'play_sound', Quantization='QuarterNote', Multiplier=1, ReferencePoint='CurrentTimeRelative', PitchMultiplier=.125, VolumeMultiplier=.05,
              bSpatialized=True, AttachComponentPath=parent, AttenuationPath=attenuation, ConcurrencyPath=concurrency,
              Location={'X':110, 'Y':220, 'Z':330}, Rotation={'Yaw':45})
        s = until(lambda:records('spatial'), lambda s:any(e['value']=='CommandOnStarted' for e in s['events']))
        a = s['audio_component']
        assert a['spatialization_allowed'] and not a['ui_sound'] and a['effective_attenuation']['spatialize'], a
        assert a['attenuation_path']==attenuation and a['concurrency_paths']==[concurrency], a
        assert a['attach_component_path']==parent and a['location']=={'x':110,'y':220,'z':330}, a
        assert abs(a['rotation']['yaw']-45)<.01, a
        event('spatial', 'move_sound', Location={'X':200,'Y':300,'Z':400}, Rotation={'Yaw':90}, bDryRun=True)
        assert records('spatial')['audio_component']['location']==a['location']
        event('spatial', 'move_sound', Location={'X':200,'Y':300,'Z':400}, Rotation={'Yaw':90})
        a = records('spatial')['audio_component']
        assert a['location']=={'x':200,'y':300,'z':400} and abs(a['rotation']['yaw']-90)<.01, a
        event('anchor', 'release')
        a = records('spatial')['audio_component']
        assert not a['attach_component_path'] and a['location']=={'x':200,'y':300,'z':400}, a
        event('spatial', 'release')
        assert call('GET', '/audio/concurrencies/inspect', asset_path=concurrency)==concurrency_before
        assert call('GET', '/audio/attenuations/settings', asset_path=attenuation)==attenuation_before
        event('teardown', 'play_sound', Quantization='QuarterNote', Multiplier=64, ReferencePoint='CurrentTimeRelative', VolumeMultiplier=0)
        call('POST', '/editor/play', {'Operation':'stop'})
        until(lambda:call('GET', '/editor/status'), lambda s:not s['is_playing'])
        call('POST', '/editor/play', {'Operation':'start'})
        until(lambda:call('GET', '/editor/status'), lambda s:s['is_playing'])
        time.sleep(1)
        assert httpx.get(base+'/audio/quartz/events', params={'event_id':'teardown'}).status_code >= 400
        print('Native quantized sound delay/start/finish, pause/resume, queued/active stop, spatial transforms/attachment/attenuation/concurrency, dry-run and PIE cleanup: OK')
    finally:
        if started:
            for name in [clock_name, no_audio_name]:
                httpx.post(base+'/audio/quartz/control', json={'ClockName':name, 'Operation':'delete', 'bConfirm':True}, timeout=120)
            call('POST', '/editor/play', {'Operation':'stop'})
            until(lambda:call('GET', '/editor/status'), lambda s:not s['is_playing'])
        if imported:
            call('POST', '/assets/delete', {'AssetPath':sound_path})
        for asset in extra_assets:
            call('POST', '/assets/delete', {'AssetPath':asset})
        source.unlink(missing_ok=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base-url', default='http://127.0.0.1:8080')
    run(p.parse_args().base_url)
