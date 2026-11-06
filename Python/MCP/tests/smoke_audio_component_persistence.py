"""Run prepare, restart the editor, then verify for native Blueprint component persistence."""
import argparse
import json
import time
import uuid
from pathlib import Path
import httpx

PROJECT = Path(__file__).resolve().parents[5]
MANIFEST = PROJECT / 'Saved' / 'UE5MCP_Test' / 'audio_component_fixture.json'


def run(base, phase):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base+route, json=body, params=params, timeout=180)
        assert r.is_success, (r.status_code, r.text)
        return r.json()

    def inspect(bp):
        return call('GET', '/audio/components/settings', bp_path=bp, component_name='Audio')

    def edit(bp, **settings):
        return call('PATCH', '/audio/components/settings', {'BpPath':bp, 'ComponentName':'Audio'} | settings)

    def snapshot(s):
        return {k:s[k] for k in ['numeric_settings','bool_settings','references','concurrency_paths']}

    assert not call('GET','/editor/status')['is_playing']
    if phase == 'verify':
        fixture = json.loads(MANIFEST.read_text())
        try:
            actual = inspect(fixture['bp'])
            assert snapshot(actual)==fixture['expected'], actual
            assert not actual['dirty'], actual
            # Editing/clearing a saved template recompiles and persists native fields.
            assert edit(fixture['bp'], References={'Sound':'','AttenuationSettings':'','SoundClassOverride':''},
                        bSetConcurrency=True, ConcurrencyPaths=[], bSave=True)['changed']
            cleared = inspect(fixture['bp'])
            assert all(not p for p in cleared['references'].values()) and not cleared['concurrency_paths']
            print('Audio Component native settings survived editor restart; clear/recompile/save: OK')
        finally:
            for asset in fixture['assets']:
                call('POST','/assets/delete', {'AssetPath':asset})
            MANIFEST.unlink(missing_ok=True)
        return

    assert not MANIFEST.exists(), 'An existing persistence fixture needs verification first'
    name = 'BP_MCP_Audio_'+uuid.uuid4().hex[:8]
    assets = []
    keep = False
    try:
        result = call('POST','/blueprint', {'ParentClass':'Actor', 'BpPath':'/Game/UE5MCP_Test/'+name})
        bp = result.get('BpPath') or result['bpPath']
        assets.append(bp)
        call('POST','/blueprints/compile', {'BpPath':bp})
        call('POST','/blueprints/components', {'BpPath':bp, 'ComponentName':'Root', 'ComponentClass':'SceneComponent'})
        call('POST','/blueprints/components', {'BpPath':bp, 'ComponentName':'Audio', 'ComponentClass':'AudioComponent', 'AttachTo':'Root'})
        for suffix, route in [('_Attenuation','/audio/attenuations/create'), ('_Concurrency','/audio/concurrencies/create')]:
            r = httpx.post(base+route, json={'AssetPath':'/Game/UE5MCP_Test/'+name+suffix, 'bSave':True}, timeout=180)
            r.raise_for_status()
            assets.append(r.text)
        attenuation, concurrency = assets[1:]
        edit(bp, bSave=True)
        before = inspect(bp)
        request = {'NumericSettings':{'VolumeMultiplier':.35,'PitchMultiplier':.8,'LowPassFilterFrequency':4000,
                                     'HighPassFilterFrequency':120,'Priority':3,'SubtitlePriority':50},
                   'BoolSettings':{'bAutoActivate':False,'bAllowSpatialization':True,'bIsUISound':False,
                                   'bEnableLowPassFilter':True,'bEnableHighPassFilter':True,'bOverridePriority':True,
                                   'bOverrideSubtitlePriority':True,'bStopWhenOwnerDestroyed':True},
                   'References':{'Sound':'/Engine/EngineSounds/1kSineTonePing.1kSineTonePing',
                                 'AttenuationSettings':attenuation,'SoundClassOverride':'/Engine/EngineSounds/Master.Master'},
                   'bSetConcurrency':True,'ConcurrencyPaths':[concurrency]}
        preview = edit(bp, **request, bDryRun=True, bSave=True)
        assert preview['would_change'] and not preview['changed'] and not preview['saved']
        assert inspect(bp)==before
        invalid = [ {'NumericSettings':{'PitchMultiplier':0}}, {'BoolSettings':{'NotASetting':True}},
                    {'NumericSettings':{'VolumeMultiplier':.2},'References':{'Sound':attenuation}},
                    {'References':{'Unknown':concurrency}}, {'ConcurrencyPaths':[concurrency]},
                    {'bSetConcurrency':True,'ConcurrencyPaths':[concurrency,concurrency]} ]
        for bad in invalid:
            r = httpx.patch(base+'/audio/components/settings', json={'BpPath':bp,'ComponentName':'Audio'} | bad, timeout=180)
            assert r.status_code>=400, r.text
            assert inspect(bp)==before
        r = httpx.get(base+'/audio/components/settings', params={'bp_path':bp,'component_name':'Root'}, timeout=180)
        assert r.status_code>=400
        applied = edit(bp, **request)
        assert applied['changed'] and applied['dirty']
        expected = snapshot(inspect(bp))
        call('POST','/editor/transactions/undo')
        assert snapshot(inspect(bp))==snapshot(before)
        call('POST','/editor/transactions/redo')
        assert snapshot(inspect(bp))==expected
        assert not edit(bp, **request)['changed']
        saved = edit(bp, **request, bSave=True)
        assert saved['saved'] and not saved['changed'] and not saved['dirty']
        assert (PROJECT/'Content'/'UE5MCP_Test'/(name+'.uasset')).exists()
        call('POST','/editor/play', {'Operation':'start'})
        time.sleep(2)
        try:
            r = httpx.patch(base+'/audio/components/settings', json={'BpPath':bp,'ComponentName':'Audio','NumericSettings':{'VolumeMultiplier':.6}}, timeout=180)
            assert r.status_code>=400, r.text
            assert snapshot(inspect(bp))==expected
        finally:
            call('POST','/editor/play', {'Operation':'stop'})
            time.sleep(1)
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps({'bp':bp,'assets':assets,'expected':expected}))
        keep = True
        print('Audio Component validation atomicity, dry-run/no-op, transaction undo/redo, compile/save and PIE guard: OK; restart then verify')
    finally:
        if not keep:
            for asset in assets:
                call('POST','/assets/delete', {'AssetPath':asset})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base-url', default='http://127.0.0.1:8080')
    p.add_argument('--phase', choices=['prepare','verify'], required=True)
    args = p.parse_args()
    run(args.base_url, args.phase)
