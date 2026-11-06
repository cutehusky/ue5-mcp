"""Live post-process volume authoring on a scratch map.

prepare: create a post-process box volume (dry run first). Edit the blend controls; add, reweight and remove weighted
blendables; toggle overrides; then edit every override-backed bool/enum/float/int32/FVector4/FLinearColor setting
(dry run each, stale guard, undo/redo once per kind), hard object references, and reset one field of every kind to
its native default; save and snapshot all 244 discovered fields.
verify (fresh editor): reload the map, compare controls, blendables and every field, then restore the original map.
"""
import argparse
import json
import math
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'post_process.json'
MAP = '/Game/UE5MCP_Test/MCP_PostProcess'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
BLENDABLE = '/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial'
BLENDABLE_B = '/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial'
TEXTURE = '/Engine/EngineResources/DefaultTexture.DefaultTexture'
CUBEMAP = '/Engine/EngineMaterials/DefaultCubemap.DefaultCubemap'
LIVE = {'bConfirm': True, 'bDryRun': False}
P = '/volumes/post-process/'
ACTOR = None


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-4)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return a == b


def inspect(api):
    return {k: v for k, v in api.call('POST', P + 'inspect', {'ActorPath': ACTOR}).items() if k != 'scope'}


def fields(api):
    out, start = {}, 0
    while True:
        d = api.call('POST', P + 'fields', {'ActorPath': ACTOR, 'EntryStart': start, 'EntryCount': 128})
        out.update({f['name']: f for f in d['fields']})
        if not d['more_fields']:
            return out
        start = d['next_field_start']


def state(api):
    return {'volume': inspect(api), 'fields': fields(api)}


def edit(api, route, body, check, undo=False, stale=None):
    before = state(api)
    d = api.call('POST', P + route, {'ActorPath': ACTOR, **body, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, body, d)
    assert close(state(api), before), (route, body, 'dry run changed state')
    if stale:
        api.call('POST', P + route, {'ActorPath': ACTOR, **body, **stale, **LIVE}, ok=False)
    api.call('POST', P + route, {'ActorPath': ACTOR, **body, **LIVE})
    after = state(api)
    assert check(before, after), (route, body, json.dumps(after['fields'].get(body.get('FieldName', ''), after['volume']))[:900])
    changed = {k for k in after['fields'] if not close(before['fields'][k], after['fields'][k])}
    allowed = {'WeightedBlendables'} if route.startswith('blendable') else {body.get('FieldName')}
    assert changed <= allowed, (route, body, 'other fields changed', sorted(changed))
    if undo:
        api.undo()
        u = state(api)
        assert close(u, before), (route, body, 'undo', [(k, before['fields'][k], u['fields'][k]) for k in before['fields'] if not close(before['fields'][k], u['fields'][k])][:3],
                                  None if close(u['volume'], before['volume']) else (before['volume'], u['volume']))
        api.redo()
        assert close(state(api), after), (route, body, 'redo')
    return after


def control_stage(api):
    for i, (field, key, value) in enumerate((('Priority', 'priority', 5), ('BlendRadius', 'blend_radius', 250), ('BlendWeight', 'blend_weight', 0.75))):
        cur = inspect(api)[key]
        edit(api, 'control', {'FieldName': field, 'ExpectedScalarValue': cur, 'ScalarValue': value},
             lambda b, a, key=key, value=value: close(a['volume'][key], value), undo=i == 0, stale={'ExpectedScalarValue': cur + 1})
    for field, key in (('Unbound', 'unbound'), ('Enabled', 'enabled')):
        cur = inspect(api)[key]
        edit(api, 'control', {'FieldName': field, 'ExpectedScalarValue': int(cur), 'bBoolValue': not cur},
             lambda b, a, key=key, cur=cur: a['volume'][key] is (not cur), undo=field == 'Unbound', stale={'ExpectedScalarValue': int(not cur)})
    # Re-enable the volume so the final state is ordinary.
    edit(api, 'control', {'FieldName': 'Enabled', 'ExpectedScalarValue': 0, 'bBoolValue': True}, lambda b, a: a['volume']['enabled'] is True)
    api.call('POST', P + 'control', {'ActorPath': ACTOR, 'FieldName': 'BlendWeight', 'ExpectedScalarValue': 0.75, 'ScalarValue': 2, **LIVE}, ok=False)


def blendable_stage(api):
    blend = lambda: [(x['object_path'], x['weight']) for x in inspect(api)['blendables']]
    edit(api, 'blendable-add', {'ExpectedEntryCount': 0, 'ObjectPath': BLENDABLE, 'ScalarValue': 0.5}, lambda b, a: blend() == [(BLENDABLE, 0.5)], undo=True,
         stale={'ExpectedEntryCount': 1})
    edit(api, 'blendable-add', {'ExpectedEntryCount': 1, 'ObjectPath': BLENDABLE_B, 'ScalarValue': 1}, lambda b, a: len(blend()) == 2)
    api.call('POST', P + 'blendable-add', {'ActorPath': ACTOR, 'ExpectedEntryCount': 2, 'ObjectPath': BLENDABLE, 'ScalarValue': 1, **LIVE}, ok=False)
    edit(api, 'blendable-weight', {'ExpectedEntryCount': 2, 'EntryIndex': 0, 'ExpectedObjectPath': BLENDABLE, 'ExpectedScalarValue': 0.5, 'ScalarValue': 0.25},
         lambda b, a: close(blend()[0][1], 0.25), undo=True, stale={'ExpectedScalarValue': 0.4})
    edit(api, 'blendable-remove', {'ExpectedEntryCount': 2, 'EntryIndex': 1, 'ExpectedObjectPath': BLENDABLE_B, 'ExpectedScalarValue': 1},
         lambda b, a: blend() == [(BLENDABLE, 0.25)], undo=True, stale={'ExpectedObjectPath': BLENDABLE})


def plan(f):
    """Route and body that change this field's value, or None for kinds without a value route."""
    n, ov = f['name'], f.get('override_enabled', False)
    if 'bool_value' in f:
        return 'bool', {'FieldName': n, 'bExpectedBoolValue': f['bool_value'], 'bExpectedOverride': ov, 'bBoolValue': not f['bool_value']}, \
            lambda a: a['bool_value'] is (not f['bool_value'])
    if 'enum_value_name' in f:
        opts = [c['name'] for c in f['enum_choices'] if not c['hidden'] and not c['name'].endswith('_MAX') and c['name'] != f['enum_value_name']]
        return 'enum', {'FieldName': n, 'ExpectedEnumValue': f['enum_value_name'], 'bExpectedOverride': ov, 'EnumValue': opts[0]}, \
            lambda a: a['enum_value_name'] == opts[0]
    if 'scalar_value' in f:
        v = f['scalar_value']
        hi, lo = float(f.get('ClampMax', f.get('UIMax', v + 1))), float(f.get('ClampMin', f.get('UIMin', v - 1)))
        new = (v + hi) / 2 if hi > v else (v + lo) / 2
        return 'scalar', {'FieldName': n, 'ExpectedScalarValue': v, 'bExpectedBoolValue': ov, 'ScalarValue': new}, lambda a: close(a['scalar_value'], new)
    if 'integer_value' in f:
        v = int(f['integer_value'])
        new = v + 1 if v + 1 <= int(float(f.get('ClampMax', v + 1))) else v - 1
        return 'integer', {'FieldName': n, 'ExpectedScalarValue': v, 'bExpectedBoolValue': ov, 'ScalarValue': new}, lambda a: int(a['integer_value']) == new
    if 'vector_value' in f:
        new = [x * 0.5 + 0.1 for x in f['vector_value']]
        return 'vector', {'FieldName': n, 'ExpectedChannels': f['vector_value'], 'bExpectedOverride': ov, 'Channels': new}, lambda a: close(a['vector_value'], new)
    return None


def override_stage(api):
    for i, name in enumerate(('WhiteTemp', 'BloomIntensity')):
        f = fields(api)[name]
        edit(api, 'override', {'FieldName': name, 'bExpectedBoolValue': f['override_enabled'], 'bBoolValue': not f['override_enabled']},
             lambda b, a, name=name, cur=f['override_enabled']: a['fields'][name]['override_enabled'] is (not cur), undo=i == 0,
             stale={'bExpectedBoolValue': not f['override_enabled']})


def value_stage(api):
    """Every override-backed bool/enum/float/int32/vector setting (value setters keep the override flag as it is);
    returns the names of fields without a value route."""
    first, unsupported, refused = set(), [], []
    # Deprecated properties (UHT drops the _DEPRECATED suffix) are load-time upgrade sources: hidden and refused.
    assert 'LocalExposureContrastScale' not in fields(api)
    api.call('POST', P + 'scalar', {'ActorPath': ACTOR, 'FieldName': 'LocalExposureContrastScale', 'ExpectedScalarValue': 1, 'bExpectedBoolValue': False, 'ScalarValue': 1.5, **LIVE}, ok=False)
    api.call('POST', P + 'override', {'ActorPath': ACTOR, 'FieldName': 'LocalExposureContrastScale', 'bExpectedBoolValue': False, 'bBoolValue': True, **LIVE}, ok=False)
    for name, f in fields(api).items():
        p = plan(f)
        if p is None:
            unsupported.append(name)
            continue
        route, body, ok = p
        if not f.get('has_override'):
            assert 'with override required' in api.call('POST', P + route, {'ActorPath': ACTOR, **body, **LIVE}, ok=False), name
            refused.append(name)
            continue
        stale = {'bExpectedOverride': not body['bExpectedOverride']} if 'bExpectedOverride' in body else {'bExpectedBoolValue': not body['bExpectedBoolValue']}
        edit(api, route, body, lambda b, a, name=name, ok=ok: ok(a['fields'][name]) and a['fields'][name]['override_enabled'] == b['fields'][name]['override_enabled'],
             undo=route not in first, stale=stale)
        first.add(route)
    assert first == {'bool', 'enum', 'scalar', 'integer', 'vector'}, first
    return unsupported, refused


def object_stage(api):
    # AmbientCubemap has no bOverride_ flag, so the override-guarded object route refuses it.
    f = fields(api)['AmbientCubemap']
    assert 'with override required' in api.call('POST', P + 'object', {'ActorPath': ACTOR, 'FieldName': 'AmbientCubemap', 'ExpectedObjectPath': f['object_path'],
                                                                       'bExpectedOverride': False, 'ObjectPath': CUBEMAP, **LIVE}, ok=False)
    for i, (name, path) in enumerate((('BloomDirtMask', TEXTURE), ('AutoExposureMeterMask', TEXTURE))):
        f = fields(api)[name]
        edit(api, 'object', {'FieldName': name, 'ExpectedObjectPath': f['object_path'], 'bExpectedOverride': f['override_enabled'], 'ObjectPath': path},
             lambda b, a, name=name, path=path: a['fields'][name]['object_path'] == path and a['fields'][name]['override_enabled'] == b['fields'][name]['override_enabled'], undo=i == 0,
             stale={'ExpectedObjectPath': path})
    # Incompatible class (a cubemap for a UTexture2D reference) is refused.
    f = fields(api)['BloomConvolutionTexture']
    api.call('POST', P + 'object', {'ActorPath': ACTOR, 'FieldName': 'BloomConvolutionTexture', 'ExpectedObjectPath': f['object_path'],
                                    'bExpectedOverride': f['override_enabled'], 'ObjectPath': CUBEMAP, **LIVE}, ok=False)


def reset_stage(api):
    picks = {'scalar': 'WhiteTemp', 'integer': 'LumenMaxReflectionBounces', 'bool': 'bMobileHQGaussian', 'vector': 'ColorSaturation',
             'enum': 'BloomMethod', 'object': 'BloomDirtMask'}
    for kind, name in picks.items():
        f = fields(api)[name]
        assert not f['value_matches_native_default'], (name, 'needs an edited value to reset')
        body = {'FieldName': name}
        if kind in ('scalar', 'integer'):
            body.update(ExpectedScalarValue=f['scalar_value'] if kind == 'scalar' else int(f['integer_value']), bExpectedBoolValue=f['override_enabled'])
        elif kind == 'bool':
            body.update(bExpectedBoolValue=f['bool_value'], bExpectedOverride=f['override_enabled'])
        elif kind == 'vector':
            body.update(ExpectedChannels=f['vector_value'], bExpectedOverride=f['override_enabled'])
        elif kind == 'enum':
            body.update(ExpectedEnumValue=f['enum_value_name'], bExpectedOverride=f['override_enabled'])
        else:
            body.update(ExpectedObjectPath=f['object_path'], bExpectedOverride=f['override_enabled'])
        edit(api, f'{kind}/reset', body, lambda b, a, name=name: a['fields'][name]['value_matches_native_default'], undo=kind == 'scalar')


def prepare(api):
    global ACTOR
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
    # Everything below creates or edits actors in the open world; never continue unless it is the scratch map.
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    body = {'VolumeType': 'PostProcess', 'Name': 'MCP_PPV', 'Position': {'X': 0, 'Y': 0, 'Z': 0}, 'Extent': {'X': 200, 'Y': 200, 'Z': 200}}
    d = api.call('POST', '/volumes/create-box', {**body, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'], d
    ACTOR = api.call('POST', '/volumes/create-box', {**body, **LIVE})['actor_path']
    api.call('POST', '/volumes/create-box', {**body, **LIVE}, ok=False)
    control_stage(api)
    blendable_stage(api)
    override_stage(api)
    unsupported, refused = value_stage(api)
    object_stage(api)
    reset_stage(api)
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'actor': ACTOR, 'unsupported': unsupported, 'refused': refused, 'snapshot': state(api)}), encoding='utf-8')
    print(f'prepared post-process authoring; no override flag: {refused}; no value route: {len(unsupported)} fields; restart the editor and run verify')


def verify(api):
    global ACTOR
    st = json.loads(STATE.read_text(encoding='utf-8'))
    assert st.get('snapshot'), 'prepare did not finish; run cleanup'
    ACTOR = st['actor']
    try:
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = state(api)
        bad = [k for k in st['snapshot']['fields'] if not close(st['snapshot']['fields'][k], cold['fields'].get(k))]
        assert close(st['snapshot']['volume'], cold['volume']) and not bad, (bad[:10], st['snapshot']['volume'], cold['volume'])
        print(f"Cold reload of post-process controls, blendables and all {len(cold['fields'])} settings fields: OK")
    finally:
        cleanup(api)


def cleanup(api):
    st = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    httpx.post(api.base + '/worlds/load', json={'WorldPath': st.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned post-process test map')


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
