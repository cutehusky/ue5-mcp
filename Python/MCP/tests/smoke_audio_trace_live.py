"""Native trace lifecycle and file identity during real Quartz playback."""
import argparse
import struct
import time
import uuid
from pathlib import Path
import httpx
from smoke_sound_wave_import_live import write_wav

PROJECT = Path(__file__).resolve().parents[5]


def run(base, external=False):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base+route, json=body, params=params, timeout=180)
        assert r.is_success, (r.status_code, r.text)
        return r.json()

    def until(fetch, predicate):
        end = time.monotonic()+25
        while time.monotonic() < end:
            s = fetch()
            if predicate(s):
                return s
            time.sleep(.05)
        raise AssertionError(s)

    def control(id, op='start', **extra):
        return call('POST', '/audio/profiling/traces', {'CaptureId': id, 'Operation': op}|extra)

    def inspect(id=''):
        return call('GET', '/audio/profiling/traces', capture_id=id)

    def reject(id, **extra):
        r = httpx.post(base+'/audio/profiling/traces', json={'CaptureId': id}|extra, timeout=180)
        assert r.status_code >= 400, r.text

    def channels():
        return {x['name']: x['enabled'] for x in inspect()['available_channels']}

    if external:
        before = inspect()
        assert before['native_connected'] and not before['owned_active_id'], before
        call('POST', '/editor/play', {'Operation': 'start'})
        try:
            until(lambda: call('GET', '/editor/status'), lambda s: s['is_playing'])
            reject('foreign_session_probe')
            reject('foreign_session_probe', Operation='stop')
            after = inspect()
            assert after['native_connected'] and after['native_destination'] == before['native_destination'], after
        finally:
            call('POST', '/editor/play', {'Operation': 'stop'})
            until(lambda: call('GET', '/editor/status'), lambda s: not s['is_playing'])
        assert inspect()['native_connected']
        print('Independently started native trace preserved across rejected start/stop and PIE teardown: OK')
        return

    def completed(id, reason):
        s = until(lambda: inspect(id), lambda s: s['state'] == 'completed')
        assert s['stop_reason'] == reason, s
        p = Path(s['path']); files.add(p)
        data = p.read_bytes()
        assert len(data) > 46 and data[:4] == b'2CRT', (s, data[:46])
        end = 6+struct.unpack_from('<H', data, 4)[0]
        offset = 6
        guids = {}
        while offset < end:
            descriptor = struct.unpack_from('<H', data, offset)[0]; offset += 2
            size, field = descriptor & 255, descriptor >> 8
            guids[field] = data[offset:offset+size]; offset += size
        guid = ''.join(f'{v:08X}' for v in struct.unpack('<4I', guids[2]))
        assert guid.lower() == s['trace_guid'].lower(), (guid, s)
        assert channels() == baseline, (channels(), baseline)
        control(id, 'release')
        assert p.exists(), 'Release must preserve the trace file'
        return s

    name = 'Trace_'+uuid.uuid4().hex[:10]
    source = PROJECT/'Saved'/'UE5MCP_Test'/(name+'.wav')
    sound = '/Game/UE5MCP_Test/'+name+'.'+name
    files = set(); imported = False; started = False
    assert not call('GET', '/editor/status')['is_playing']
    assert not inspect()['native_connected'], inspect()
    baseline = channels()
    reject(name)
    try:
        write_wav(source, 12)
        call('POST', '/audio/waves/import', {'SourceFilePath': str(source), 'DestinationPath': '/Game/UE5MCP_Test', 'AssetName': name, 'bSave': True}); imported = True
        call('POST', '/editor/play', {'Operation': 'start'}); started = True
        until(lambda: call('GET', '/editor/status'), lambda s: s['is_playing'])
        for extra in [{'CaptureId': '../bad'}, {'DurationSeconds': 0}, {'MaxFileMB': 0}, {'Channels': ['bad']}, {'Channels': ['audio', 'audio']}]:
            reject(extra.pop('CaptureId', name), **extra)
        control(name, bDryRun=True)
        assert channels() == baseline and not inspect()['native_connected']
        control(name, DurationSeconds=30, MaxFileMB=256)
        files.add(PROJECT/'Saved'/'Profiling'/'UE5MCP'/('Audio_'+name+'.utrace'))
        s = until(lambda: inspect(name), lambda s: s['state'] == 'recording' and int(s['trace_guid'], 16) != 0)
        assert all(channels()[c] for c in s['requested_channels']), s
        reject(name+'_second'); reject(name, Operation='release')
        control(name, 'stop', bDryRun=True)
        assert inspect(name)['state'] == 'recording'
        call('POST', '/audio/quartz/control', {'ClockName': name, 'Operation': 'create'})
        call('POST', '/audio/quartz/control', {'ClockName': name, 'Operation': 'start'})
        call('POST', '/audio/quartz/events', {'EventId': name, 'Operation': 'play_sound', 'ClockName': name, 'SoundPath': sound, 'Quantization': 'QuarterNote', 'ReferencePoint': 'CurrentTimeRelative', 'VolumeMultiplier': .03})
        until(lambda: call('GET', '/audio/quartz/events', event_id=name), lambda s: any(e['value'] == 'CommandOnStarted' for e in s['events']))
        initial = inspect(name)['file_size_bytes']
        until(lambda: inspect(name), lambda s: s['file_size_bytes'] > max(initial, 46))
        control(name, 'stop'); completed(name, 'manual_stop')
        reject(name)  # Existing file is never overwritten after metadata release.
        auto = name+'_auto'
        control(auto, DurationSeconds=.3); completed(auto, 'duration_limit')
        cleanup = name+'_cleanup'
        control(cleanup, DurationSeconds=30)
        until(lambda: inspect(cleanup), lambda s: s['state'] == 'recording')
        call('POST', '/editor/play', {'Operation': 'stop'})
        until(lambda: call('GET', '/editor/status'), lambda s: not s['is_playing'])
        completed(cleanup, 'world_cleanup')
        print('Native audio trace: real playback, enabled channels, file GUID identity, growth, manual/duration/PIE stop, channel restoration, dry-run and validation: OK')
    finally:
        active = inspect()['owned_active_id']
        if active:
            control(active, 'stop')
            until(lambda: inspect(active), lambda s: s['state'] == 'completed')
            files.add(Path(inspect(active)['path']))
            control(active, 'release')
        if started and call('GET', '/editor/status')['is_playing']:
            call('POST', '/editor/play', {'Operation': 'stop'})
            until(lambda: call('GET', '/editor/status'), lambda s: not s['is_playing'])
        if imported:
            call('POST', '/assets/delete', {'AssetPath': sound})
        source.unlink(missing_ok=True)
        for p in files:
            p.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    parser.add_argument('--external', action='store_true', help='Require an independently started native trace; never stop it')
    args = parser.parse_args()
    run(args.base_url, args.external)
