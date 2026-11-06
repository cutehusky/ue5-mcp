"""World Settings default reverb, ambient zone and audio asset references: prepare, restart editor, verify.

Usage: smoke_world_audio_live.py prepare|verify|cleanup. Uses engine audio assets only; the scratch map is deleted after
verify. Dry runs, out-of-range values, wrong asset classes, stale guards and missing confirmation must leave the
settings unchanged; edits must undo/redo and survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
MAP = '/Game/UE5MCP_Test/MCP_WorldAudio'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'world_audio.json'
CAVE = '/Engine/EngineSounds/ReverbSettings/Cave.Cave'
MIX = '/Engine/EngineSounds/Duck_Normal_Attack_MixMod.Duck_Normal_Attack_MixMod'
SUBMIX = '/Engine/EngineSounds/Submixes/MasterSubmixDefault.MasterSubmixDefault'
NUMERIC = {'DefaultReverbSettings.Volume': 0.25, 'DefaultReverbSettings.FadeTime': 2.5,
           'DefaultAmbientZoneSettings.ExteriorVolume': 0.75, 'DefaultAmbientZoneSettings.InteriorVolume': 0.5,
           'DefaultAmbientZoneSettings.ExteriorTime': 1.5, 'DefaultAmbientZoneSettings.InteriorTime': 3,
           'DefaultAmbientZoneSettings.ExteriorLPF': 4000, 'DefaultAmbientZoneSettings.InteriorLPF': 8000,
           'DefaultAmbientZoneSettings.ExteriorLPFTime': 0.5, 'DefaultAmbientZoneSettings.InteriorLPFTime': 0.25}
OBJECTS = {'DefaultReverbSettings.ReverbEffect': CAVE, 'DefaultBaseSoundMix': MIX}
KEYS = ('numeric_settings', 'bool_settings', 'object_settings')


def audio(s):
    return {'numeric': {k: s['numeric_settings'][k] for k in NUMERIC},
            'apply': s['bool_settings']['DefaultReverbSettings.bApplyReverb'],
            'objects': {k: s['object_settings'][k] for k in ('DefaultReverbSettings.ReverbEffect', 'DefaultReverbSettings.ReverbPluginEffect', 'DefaultBaseSoundMix')}}


def prepare(api):
    assert not STATE.exists(), 'run verify or cleanup first'
    original = api.call('GET', '/worlds/inspect')['world_path']
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'original': original}))
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    ins = lambda: api.call('GET', '/worlds/settings')
    before = ins()
    assert before['object_constraints']['DefaultBaseSoundMix']['class_path'] == '/Script/Engine.SoundMix', before['object_constraints']
    start = audio(before)
    assert start['objects'] == {'DefaultReverbSettings.ReverbEffect': '', 'DefaultReverbSettings.ReverbPluginEffect': '', 'DefaultBaseSoundMix': ''}, start
    apply = not start['apply']

    def bad(body):
        r = httpx.patch(BASE + '/worlds/settings', json={'WorldPath': MAP, **body}, timeout=180)
        assert r.status_code >= 400, (body, r.text[:300])
        assert audio(ins()) == start, ('rejected request changed settings', body)
        return r.json().get('errorMessage', r.text)[:160]

    # Numeric/bool ranges, stale guards and whole-request preflight.
    bad({'NumericSettings': {'DefaultReverbSettings.Volume': 1.5}})
    bad({'NumericSettings': {'DefaultAmbientZoneSettings.ExteriorLPF': 10}})
    bad({'NumericSettings': {'DefaultReverbSettings.FadeTime': -1}})
    bad({'NumericSettings': {**NUMERIC, 'DefaultAmbientZoneSettings.InteriorLPF': 30000}})
    bad({'NumericSettings': NUMERIC, 'ExpectedNumericSettings': {'DefaultReverbSettings.Volume': start['numeric']['DefaultReverbSettings.Volume'] + 0.125}})
    bad({'BoolSettings': {'DefaultReverbSettings.bApplyReverb': apply}, 'ExpectedBoolSettings': {'DefaultReverbSettings.bApplyReverb': apply}})
    # Object references: confirmation, full expected map, stale guard, wrong class, missing asset.
    obj = {'ObjectSettings': OBJECTS, 'ExpectedObjectSettings': {k: '' for k in OBJECTS}, 'bConfirm': True}
    bad({**obj, 'bConfirm': False})
    bad({**obj, 'ExpectedObjectSettings': {'DefaultBaseSoundMix': ''}})
    bad({**obj, 'ExpectedObjectSettings': {**obj['ExpectedObjectSettings'], 'DefaultBaseSoundMix': MIX}})
    bad({**obj, 'ObjectSettings': {**OBJECTS, 'DefaultBaseSoundMix': SUBMIX}})
    bad({**obj, 'ObjectSettings': {**OBJECTS, 'DefaultReverbSettings.ReverbEffect': '/Engine/EngineSounds/ReverbSettings/Missing.Missing'}})
    bad({**obj, 'NumericSettings': {'DefaultReverbSettings.Volume': 2}})

    full = {'WorldPath': MAP, 'NumericSettings': NUMERIC, 'BoolSettings': {'DefaultReverbSettings.bApplyReverb': apply},
            'ExpectedNumericSettings': start['numeric'], 'ExpectedBoolSettings': {'DefaultReverbSettings.bApplyReverb': start['apply']}, **obj}
    dry = api.call('PATCH', '/worlds/settings', {**full, 'bDryRun': True})
    assert dry['changed'], dry
    assert audio(ins()) == start and not ins()['dirty'], 'dry run changed settings'
    done = api.call('PATCH', '/worlds/settings', full)
    assert done['changed'] and done['dirty'], done
    after = audio(ins())
    want = {'numeric': NUMERIC, 'apply': apply, 'objects': {**OBJECTS, 'DefaultReverbSettings.ReverbPluginEffect': ''}}
    assert after == want, after
    api.call('POST', '/editor/transactions/undo')
    assert audio(ins()) == start, ('undo', audio(ins()))
    api.call('POST', '/editor/transactions/redo')
    assert audio(ins()) == want, ('redo', audio(ins()))
    assert not api.call('PATCH', '/worlds/settings', {**full, 'ExpectedNumericSettings': NUMERIC, 'ExpectedBoolSettings': {'DefaultReverbSettings.bApplyReverb': apply},
                                                      'ExpectedObjectSettings': OBJECTS})['changed'], 'no-op mutated'
    # Clear and reassign the base mix.
    clear = {'WorldPath': MAP, 'bConfirm': True, 'ObjectSettings': {'DefaultBaseSoundMix': ''}, 'ExpectedObjectSettings': {'DefaultBaseSoundMix': MIX}}
    assert api.call('PATCH', '/worlds/settings', clear)['changed']
    assert ins()['object_settings']['DefaultBaseSoundMix'] == ''
    assert api.call('PATCH', '/worlds/settings', {**clear, 'ObjectSettings': {'DefaultBaseSoundMix': MIX}, 'ExpectedObjectSettings': {'DefaultBaseSoundMix': ''}, 'bSave': True})['saved']
    final = ins()
    assert audio(final) == want and not final['dirty'], audio(final)
    STATE.write_text(json.dumps({'original': original, 'want': want}))
    print('World Settings audio: range/stale/class/confirm guards, dry run, undo/redo, no-op, clear and save OK; restart and verify')


def verify(api):
    state = json.loads(STATE.read_text())
    try:
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        s = api.call('GET', '/worlds/settings')
        assert audio(s) == state['want'] and not s['dirty'], audio(s)
        print('World Settings audio survived cold restart: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if state.get('original'):
        httpx.post(BASE + '/worlds/load', json={'WorldPath': state['original'], 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    phase = sys.argv[1]
    api = Api(BASE)
    if phase == 'prepare':
        try:
            prepare(api)
        except BaseException:
            cleanup(api)
            raise
    else:
        {'verify': verify, 'cleanup': cleanup}[phase](api)
