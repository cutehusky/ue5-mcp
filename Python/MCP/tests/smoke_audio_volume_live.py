"""Live AudioVolume authoring on a scratch map.

prepare: create the scratch map and an AudioVolume. Edit enabled/priority, the three reverb settings, the reverb effect
reference and all eight interior scalars. Build submix override rows (add, crossfade, effect chain, target, reorder,
remove) and listener send rows with nested destination sends (add, numeric fields, control/stage/clamp, external curve,
target, inline curve linear keys, key add/remove, default/extrapolation, key interpolation/tangents, send reorder, row
listener state, row reorder, send removal, row removal). Every edit has a dry run and a stale-guard refusal; one edit per
route also undo/redo. Save and snapshot. Uses engine submix/reverb/curve assets only.
verify (fresh editor): reload, compare everything, then restore the original map and delete the scratch map.
"""
import argparse
import json
import math
import time
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'audio_volume.json'
MAP = '/Game/UE5MCP_Test/MCP_AudioVolume'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
LIVE = {'bConfirm': True, 'bDryRun': False}
SUB = '/Engine/EngineSounds/Submixes/'
SM, SM_EQ, SM_REV = (SUB + n + '.' + n for n in ('MasterSubmixDefault', 'MasterEQSubmixDefault', 'MasterReverbSubmixDefault'))
PRESET = SUB + 'MasterReverbEffectPreset.MasterReverbEffectPreset'
REVERB = '/Engine/EngineSounds/ReverbSettings/Cave.Cave'
CURVE = '/Engine/Tutorial/ContentIntroCurve.ContentIntroCurve'
VOLATILE = ('scope', 'package_dirty', 'actor_guid')


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-3)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return a == b


def strip(d):
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k not in VOLATILE}
    if isinstance(d, list):
        return [strip(v) for v in d]
    return d


def actor(api):
    return f'{MAP}.{MAP.rsplit("/", 1)[1]}:PersistentLevel.MCP_Audio'


def vol(api):
    return api.call('POST', '/volumes/audio/inspect', {'ActorPath': actor(api)})


def rows(api, collection='SubmixSendSettings'):
    return api.call('POST', '/volumes/audio/submix/inspect', {'ActorPath': actor(api), 'FieldName': collection, 'EntryStart': 0, 'EntryCount': 64})['rows']


def texts(api, collection='SubmixSendSettings'):
    return [r['native_snapshot_text'] for r in rows(api, collection)]


def curve(api, row=0, send=0):
    return api.call('POST', '/volumes/audio/submix/send-inline-curve/inspect', {'ActorPath': actor(api), 'EntryIndex': row, 'NestedIndex': send, 'EntryStart': 0, 'EntryCount': 64})


def full(api):
    out = {'volume': vol(api), 'sends': rows(api), 'overrides': rows(api, 'SubmixOverrideSettings')}
    for r in out['sends']:
        for s in r['sends']:
            out[f'curve_{r["index"]}_{s["index"]}'] = curve(api, r['index'], s['index'])
    return strip(out)


def settled(api):
    prev = full(api)
    for _ in range(20):
        time.sleep(0.2)
        cur = full(api)
        if close(cur, prev):
            return cur
        prev = cur
    raise AssertionError('audio volume state did not settle')


def edit(api, route, body, check, undo=False, stale=None):
    """body is a callable returning fresh guards (row snapshots change after every edit)."""
    before = settled(api)
    d = api.call('POST', route, {**body(), 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, d)
    assert close(settled(api), before), (route, 'dry run changed state')
    if stale:
        api.call('POST', route, {**body(), **stale, **LIVE}, ok=False)
    api.call('POST', route, {**body(), **LIVE})
    after = settled(api)
    assert check(before, after), (route, body(), json.dumps({k: after[k] for k in after if not close(after[k], before.get(k))})[:1500])
    if undo:
        api.undo()
        u = settled(api)
        assert close(u, before), (route, 'undo did not restore', [k for k in u if not close(u[k], before.get(k))])
        api.redo()
        r = settled(api)
        assert close(r, after), (route, 'redo did not reapply', [k for k in r if not close(r[k], after.get(k))])
    return after


def ident(api):
    v = vol(api)
    return {'ActorPath': actor(api), 'ActorGuid': v['actor_guid'], 'ExpectedLabel': v['label']}


STALE_LABEL = {'ExpectedLabel': 'NotTheLabel'}


def settings_stage(api):
    edit(api, '/volumes/audio/control', lambda: {**ident(api), 'FieldName': 'bEnabled', 'ExpectedScalarValue': float(vol(api)['enabled']), 'bBoolValue': False},
         lambda b, a: a['volume']['enabled'] is False, undo=True, stale=STALE_LABEL)
    edit(api, '/volumes/audio/control', lambda: {**ident(api), 'FieldName': 'bEnabled', 'ExpectedScalarValue': 0.0, 'bBoolValue': True},
         lambda b, a: a['volume']['enabled'] is True)
    edit(api, '/volumes/audio/control', lambda: {**ident(api), 'FieldName': 'Priority', 'ExpectedScalarValue': vol(api)['priority'], 'ScalarValue': 5},
         lambda b, a: close(a['volume']['priority'], 5), stale={'ExpectedScalarValue': 99})
    edit(api, '/volumes/audio/reverb', lambda: {**ident(api), 'FieldName': 'bApplyReverb', 'ExpectedScalarValue': float(vol(api)['reverb']['apply']), 'bBoolValue': False},
         lambda b, a: a['volume']['reverb']['apply'] is False, undo=True, stale=STALE_LABEL)
    for field, key, v in (('Volume', 'volume', 0.75), ('FadeTime', 'fade_time', 3)):
        edit(api, '/volumes/audio/reverb', lambda field=field, key=key, v=v: {**ident(api), 'FieldName': field, 'ExpectedScalarValue': vol(api)['reverb'][key], 'ScalarValue': v},
             lambda b, a, key=key, v=v: close(a['volume']['reverb'][key], v), stale={'ExpectedScalarValue': 42})
    edit(api, '/volumes/audio/reverb-object', lambda: {**ident(api), 'FieldName': 'ReverbEffect', 'ExpectedObjectPath': '', 'ObjectPath': REVERB},
         lambda b, a: a['volume']['reverb']['effect_path'] == REVERB, undo=True, stale={'ExpectedObjectPath': REVERB})
    api.call('POST', '/volumes/audio/reverb-object', {**ident(api), 'FieldName': 'ReverbEffect', 'ExpectedObjectPath': REVERB, 'ObjectPath': SM, **LIVE}, ok=False)
    interior = {'ExteriorVolume': ('exterior_volume', 0.5), 'InteriorVolume': ('interior_volume', 0.25), 'ExteriorTime': ('exterior_time', 1),
                'InteriorTime': ('interior_time', 1.5), 'ExteriorLPF': ('exterior_lpf', 8000), 'InteriorLPF': ('interior_lpf', 4000),
                'ExteriorLPFTime': ('exterior_lpf_time', 0.75), 'InteriorLPFTime': ('interior_lpf_time', 0.25)}
    for i, (field, (key, v)) in enumerate(interior.items()):
        edit(api, '/volumes/audio/interior', lambda field=field, key=key, v=v: {**ident(api), 'FieldName': field, 'ExpectedScalarValue': vol(api)['interior'][key], 'ScalarValue': v},
             lambda b, a, key=key, v=v: close(a['volume']['interior'][key], v), undo=i == 0, stale={'ExpectedScalarValue': 12345})


def override_stage(api):
    ov = lambda: rows(api, 'SubmixOverrideSettings')
    otext = lambda: texts(api, 'SubmixOverrideSettings')
    for i, sm in enumerate((SM, SM_EQ)):
        edit(api, '/volumes/audio/submix/override-add', lambda sm=sm: {**ident(api), 'ExpectedEntryCount': len(ov()), 'ObjectPath': sm, 'ExpectedRowTexts': otext()},
             lambda b, a, i=i, sm=sm: len(a['overrides']) == i + 1 and a['overrides'][i]['submix_path'] == sm, undo=i == 0, stale={'ExpectedEntryCount': 9})
    row = lambda i: {**ident(api), 'EntryIndex': i, 'ExpectedEntryCount': len(ov()), 'ExpectedObjectPath': ov()[i]['submix_path'], 'ExpectedRowTexts': otext()}
    edit(api, '/volumes/audio/submix/override-crossfade', lambda: {**row(0), 'ExpectedScalarValue': ov()[0]['crossfade_time'], 'ScalarValue': 1.5},
         lambda b, a: close(a['overrides'][0]['crossfade_time'], 1.5), undo=True, stale={'ExpectedRowTexts': ['()', '()']})
    edit(api, '/volumes/audio/submix/override-effects', lambda: {**row(0), 'ExpectedAssetPaths': ov()[0]['effect_paths'], 'AssetPaths': [PRESET]},
         lambda b, a: a['overrides'][0]['effect_paths'] == [PRESET], undo=True, stale={'ExpectedAssetPaths': [PRESET]})
    edit(api, '/volumes/audio/submix/override-target', lambda: {**row(1), 'ObjectPath': SM_REV},
         lambda b, a: a['overrides'][1]['submix_path'] == SM_REV, undo=True, stale={'ExpectedObjectPath': SM_REV})
    edit(api, '/volumes/audio/submix/override-reorder', lambda: {**ident(api), 'ExpectedEntryCount': 2, 'ExpectedAssetPaths': [r['submix_path'] for r in ov()],
                                                                   'EntryOrder': [1, 0], 'ExpectedRowTexts': otext()},
         lambda b, a: [r['submix_path'] for r in a['overrides']] == [SM_REV, SM], undo=True, stale={'ExpectedAssetPaths': [SM_REV, SM]})
    edit(api, '/volumes/audio/submix/override-remove', lambda: {**row(0), 'ExpectedAssetPaths': ov()[0]['effect_paths']},
         lambda b, a: [r['submix_path'] for r in a['overrides']] == [SM], undo=True, stale={'ExpectedAssetPaths': ['x']})


def send_stage(api):
    sr = lambda: rows(api)
    st = lambda: texts(api)
    for i, state in enumerate((0, 1)):
        edit(api, '/volumes/audio/submix/send-row-add', lambda state=state: {**ident(api), 'ExpectedEntryCount': len(sr()), 'ScalarValue': state, 'ExpectedRowTexts': st()},
             lambda b, a, i=i, state=state: len(a['sends']) == i + 1 and a['sends'][i]['listener_location_state'] == state, undo=i == 0, stale={'ExpectedEntryCount': 9})
    for i, sm in enumerate((SM, SM_EQ)):
        edit(api, '/volumes/audio/submix/send-add', lambda sm=sm: {**ident(api), 'EntryIndex': 0, 'ExpectedEntryCount': 2, 'ExpectedScalarValue': 0,
                                                                     'ExpectedNestedCount': sr()[0]['send_count'], 'ObjectPath': sm, 'ExpectedRowTexts': st()},
             lambda b, a, i=i, sm=sm: a['sends'][0]['send_count'] == i + 1 and a['sends'][0]['sends'][i]['submix_path'] == sm, undo=i == 0, stale={'ExpectedNestedCount': 9})
    send = lambda n=0, r=0: {**ident(api), 'EntryIndex': r, 'ExpectedEntryCount': len(sr()), 'ExpectedListenerState': sr()[r]['listener_location_state'], 'NestedIndex': n,
                             'ExpectedNestedCount': sr()[r]['send_count'], 'ExpectedObjectPath': sr()[r]['sends'][n]['submix_path'], 'ExpectedRowTexts': st()}
    s0 = lambda a: a['sends'][0]['sends'][0]
    numeric = {'SendLevel': ('send_level', 0.5), 'MinSendLevel': ('min_send_level', 0.1), 'MaxSendLevel': ('max_send_level', 0.9),
               'MinSendDistance': ('min_send_distance', 200), 'MaxSendDistance': ('max_send_distance', 2000)}
    for i, (field, (key, v)) in enumerate(numeric.items()):
        edit(api, '/volumes/audio/submix/send-numeric', lambda field=field, key=key, v=v: {**send(), 'FieldName': field, 'ExpectedScalarValue': sr()[0]['sends'][0][key], 'ScalarValue': v},
             lambda b, a, key=key, v=v: close(s0(a)[key], v), undo=i == 0, stale={'ExpectedScalarValue': 777})
    for i, (field, key, v) in enumerate((('SendLevelControlMethod', 'control_method', 1), ('SendStage', 'send_stage', 1), ('DisableManualSendClamp', 'disable_manual_clamp', 1))):
        edit(api, '/volumes/audio/submix/send-control', lambda field=field, key=key, v=v: {**send(), 'FieldName': field, 'ExpectedScalarValue': int(sr()[0]['sends'][0][key]), 'ScalarValue': v},
             lambda b, a, key=key, v=v: int(s0(a)[key]) == v, undo=i == 0, stale={'ExpectedRowTexts': ['()', '()']})
    edit(api, '/volumes/audio/submix/send-curve', lambda: {**send(), 'ExpectedCurvePath': '', 'CurvePath': CURVE},
         lambda b, a: s0(a)['external_curve_path'] == CURVE, undo=True, stale={'ExpectedCurvePath': CURVE})
    edit(api, '/volumes/audio/submix/send-curve', lambda: {**send(), 'ExpectedCurvePath': CURVE, 'CurvePath': ''},
         lambda b, a: s0(a)['external_curve_path'] == '')
    edit(api, '/volumes/audio/submix/send-target', lambda: {**send(1), 'ObjectPath': SM_REV},
         lambda b, a: a['sends'][0]['sends'][1]['submix_path'] == SM_REV, undo=True, stale={'ExpectedObjectPath': SM_REV})
    # Inline curve on send 0 (the external curve was cleared, so inline data is selected).
    cv = lambda: curve(api)
    inline = lambda: {**send(), 'ExpectedCurvePath': cv()['external_curve_path']}
    keys = lambda a: [[k['time'], k['value']] for k in a['curve_0_0']['keys']]
    edit(api, '/volumes/audio/submix/send-inline-curve/linear-keys', lambda: {**inline(), 'ExpectedPairs': [{'X': k['time'], 'Y': k['value']} for k in cv()['keys']],
                                                                                'Pairs': [{'X': 0, 'Y': 1}, {'X': 0.5, 'Y': 0.8}, {'X': 1, 'Y': 0}]},
         lambda b, a: close(keys(a), [[0, 1], [0.5, 0.8], [1, 0]]), undo=True, stale={'ExpectedPairs': [{'X': 0, 'Y': 0.5}]})
    edit(api, '/volumes/audio/submix/send-inline-curve/keys', lambda: {**inline(), 'ExpectedKeyCount': cv()['key_count'], 'KeyIndex': -1, 'FieldName': 'Add', 'Pair': {'X': 0.25, 'Y': 0.9}},
         lambda b, a: a['curve_0_0']['key_count'] == 4, undo=True, stale={'ExpectedKeyCount': 9})
    edit(api, '/volumes/audio/submix/send-inline-curve/keys', lambda: {**inline(), 'ExpectedKeyCount': cv()['key_count'], 'KeyIndex': 1, 'FieldName': 'Remove', 'Pair': {'X': 0, 'Y': 0}},
         lambda b, a: a['curve_0_0']['key_count'] == 3, stale={'ExpectedKeyCount': 9})
    for i, (field, key, v) in enumerate((('DefaultValue', 'default_value', 0.5), ('PreInfinityExtrap', 'pre_infinity', 1), ('PostInfinityExtrap', 'post_infinity', 2))):
        edit(api, '/volumes/audio/submix/send-inline-curve/setting', lambda field=field, key=key, v=v: {**inline(), 'FieldName': field, 'ExpectedScalarValue': cv()[key], 'ScalarValue': v},
             lambda b, a, key=key, v=v: close(a['curve_0_0'][key], v), undo=i == 0, stale={'ExpectedScalarValue': 3.5})
    for i, (field, key, v) in enumerate((('InterpMode', 'interpolation', 2), ('TangentMode', 'tangent_mode', 1), ('ArriveTangent', 'arrive_tangent', 0.5), ('LeaveTangent', 'leave_tangent', -0.5))):
        edit(api, '/volumes/audio/submix/send-inline-curve/key-setting',
             lambda field=field, key=key, v=v: {**inline(), 'KeyIndex': 1, 'ExpectedKeyCount': cv()['key_count'], 'FieldName': field, 'ExpectedScalarValue': cv()['keys'][1][key], 'ScalarValue': v},
             lambda b, a, key=key, v=v: close(a['curve_0_0']['keys'][1][key], v), undo=i == 0, stale={'ExpectedScalarValue': 3.5})
    # Reorders and removals, with the inline curve keys now present in the row snapshots.
    edit(api, '/volumes/audio/submix/send-reorder', lambda: {**ident(api), 'EntryIndex': 0, 'ExpectedEntryCount': 2, 'ExpectedListenerState': 0,
                                                               'ExpectedNestedCount': 2, 'ExpectedAssetPaths': [s['submix_path'] for s in sr()[0]['sends']],
                                                               'EntryOrder': [1, 0], 'ExpectedRowTexts': st()},
         lambda b, a: [s['submix_path'] for s in a['sends'][0]['sends']] == [SM_REV, SM], undo=True, stale={'ExpectedAssetPaths': [SM_REV, SM]})
    edit(api, '/volumes/audio/submix/send-row-listener', lambda: {**ident(api), 'EntryIndex': 1, 'ExpectedEntryCount': 2, 'ExpectedNestedCount': 0,
                                                                    'ExpectedListenerState': sr()[1]['listener_location_state'], 'ScalarValue': 0, 'ExpectedRowTexts': st()},
         lambda b, a: a['sends'][1]['listener_location_state'] == 0, undo=True, stale={'ExpectedListenerState': 0})
    edit(api, '/volumes/audio/submix/send-row-reorder', lambda: {**ident(api), 'ExpectedEntryCount': 2, 'ExpectedListenerStates': [r['listener_location_state'] for r in sr()],
                                                                   'EntryOrder': [1, 0], 'ExpectedRowTexts': st()},
         lambda b, a: a['sends'][1]['send_count'] == 2 and a['sends'][0]['send_count'] == 0, undo=True, stale={'ExpectedListenerStates': [1, 1]})
    edit(api, '/volumes/audio/submix/send-remove', lambda: send(0, 1), lambda b, a: a['sends'][1]['send_count'] == 1, undo=True, stale={'ExpectedObjectPath': SM})
    edit(api, '/volumes/audio/submix/send-row-remove', lambda: {**ident(api), 'EntryIndex': 0, 'ExpectedEntryCount': 2, 'ExpectedListenerState': sr()[0]['listener_location_state'],
                                                                  'ExpectedAssetPaths': [], 'ExpectedRowTexts': st()},
         lambda b, a: len(a['sends']) == 1 and a['sends'][0]['send_count'] == 1, undo=True, stale={'ExpectedAssetPaths': [SM]})
    items = api.call('POST', '/volumes/audio/submix/row-items', {'ActorPath': actor(api), 'FieldName': 'SubmixSendSettings', 'EntryIndex': 0, 'EntryStart': 0, 'EntryCount': 8})
    assert json.dumps(items).count('submix_path') >= 1, items


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    original = api.call('GET', '/worlds/inspect')['world_path']
    if original.startswith(MAP):
        original = json.loads(STATE.read_text(encoding='utf-8')).get('original', FALLBACK) if STATE.exists() else FALLBACK
        original = FALLBACK if original.startswith(MAP) else original
        assert api.call('POST', '/worlds/load', {'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    STATE.write_text(json.dumps({'original': original}), encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    # Everything below edits the open world; never continue unless it is the scratch map.
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    api.call('POST', '/volumes/create-box', {'VolumeType': 'Audio', 'Name': 'MCP_Audio', 'Position': {'X': 0, 'Y': 0, 'Z': 0}, 'Extent': {'X': 500, 'Y': 500, 'Z': 200}, **LIVE})
    settings_stage(api)
    override_stage(api)
    send_stage(api)
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'snapshot': settled(api)}), encoding='utf-8')
    print('prepared audio volume authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = settled(api)
        bad = [k for k in state['snapshot'] if not close(strip(state['snapshot'][k]), cold.get(k))]
        assert not bad, [(k, json.dumps(state['snapshot'][k])[:500], json.dumps(cold.get(k))[:500]) for k in bad[:3]]
        print('Cold reload of AudioVolume settings, reverb, interior, submix overrides, sends and inline send curve: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned audio volume test map')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    p.add_argument('--base', default='http://127.0.0.1:8080')
    a = p.parse_args()
    api = Api(a.base)
    assert not api.call('GET', '/editor/status')['is_playing']
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[a.phase](api)


if __name__ == '__main__':
    main()
