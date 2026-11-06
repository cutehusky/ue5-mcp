"""Live Niagara system-level authoring on a duplicate of NS_JumpPad (the original is never modified).

prepare: duplicate/create assets, then author emitters, warmup, user parameters, bounds, determinism, fixed tick,
effect type and renderers with guard/dry-run/undo checks; save and snapshot.
verify (fresh editor): compare the cold-loaded system, then delete the test assets.
"""
import argparse
import json
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'niagara_system.json'
SOURCE = '/Game/LevelPrototyping/Interactable/JumpPad/Assets/NS_JumpPad.NS_JumpPad'
SYS = '/Game/UE5MCP_Test/NS_MCP_Work.NS_MCP_Work'
NEW_SYS = '/Game/UE5MCP_Test/NS_MCP_Empty.NS_MCP_Empty'
EMITTER = '/Game/UE5MCP_Test/NE_MCP_Work.NE_MCP_Work'
EFFECT = '/Game/UE5MCP_Test/ET_MCP_Work.ET_MCP_Work'
ASSETS = (SYS, NEW_SYS, EMITTER, EFFECT)
C = {'AssetPath': SYS, 'bConfirm': True}


def system(api, path=SYS):
    return api.call('GET', '/niagara/systems/definition', params={'asset_path': path})


def handle(api, name):
    d = system(api)
    e = next(e for e in d['emitters'] if e['name'] == name)
    return {**C, 'EmitterIndex': e['index'], 'EmitterId': e['id']}, e


def users(api):
    return {u['name']: u.get('value') for u in system(api)['user_parameters']}


def renderer(api, emitter_name, cls):
    E, e = handle(api, emitter_name)
    r = next(r for r in e['renderers'] if r['class_path'].endswith(cls))
    return {**E, 'RendererIndex': r['index'], 'RendererPath': r['object_path']}, r


def field(api, R, name):
    i = api.call('POST', '/niagara/systems/renderers/inspect', R)
    return next(f['value'] for f in i['editable_fields'] if f['name'] == name)


def creation_stage(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    # Duplication and factory creation, with guards and dry runs.
    api.call('POST', '/niagara/systems/duplicate', {'AssetPath': SYS, 'SourceAssetPath': SOURCE}, ok=False)
    api.call('POST', '/niagara/systems/duplicate', {**C, 'SourceAssetPath': SOURCE, 'bDryRun': True})
    api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS}, ok=False)
    api.call('POST', '/niagara/systems/duplicate', {**C, 'SourceAssetPath': SOURCE, 'bSave': True})
    api.call('POST', '/niagara/systems/duplicate', {**C, 'SourceAssetPath': SOURCE}, ok=False)
    src = system(api, SOURCE)
    assert [e['name'] for e in system(api)['emitters']] == [e['name'] for e in src['emitters']]
    api.call('POST', '/niagara/systems', {'AssetPath': NEW_SYS, 'bConfirm': True, 'bSave': True})
    assert system(api, NEW_SYS)['emitter_count'] == 0
    api.call('POST', '/niagara/emitters', {'AssetPath': EMITTER, 'bConfirm': True, 'bSave': True})
    em = api.call('GET', '/niagara/emitters/definition', params={'asset_path': EMITTER})
    assert em['version_count'] == 1 and em['versions'][0]['exposed'], em
    api.call('POST', '/niagara/effect-types', {'AssetPath': EFFECT, 'bConfirm': True, 'bSave': True})
    return em


def emitter_stage(api, em):
    names = lambda: [e['name'] for e in system(api)['emitters']]
    base = names()
    E, e0 = handle(api, base[0])
    # Enable, rename (guard on unsafe names), undo/redo.
    api.call('PATCH', '/niagara/systems/emitters/enabled', {**E, 'EmitterId': '00000000-0000-0000-0000-000000000000', 'bEnabled': False}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/enabled', {**E, 'bEnabled': False, 'bDryRun': True})
    assert handle(api, base[0])[1]['enabled']
    api.call('PATCH', '/niagara/systems/emitters/enabled', {**E, 'bEnabled': False})
    assert not handle(api, base[0])[1]['enabled']
    api.call('PATCH', '/niagara/systems/emitters/name', {**E, 'NewName': 'bad name!'}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/name', {**E, 'NewName': 'MCP_Glow'})
    assert names()[0] == 'MCP_Glow'
    api.undo(); assert names()[0] == base[0]
    api.redo(); assert names()[0] == 'MCP_Glow'
    # Insert a versioned emitter asset, duplicate a handle, remove one.
    api.call('POST', '/niagara/systems/emitters', {**C, 'SourceAssetPath': EMITTER, 'VersionId': '11111111-1111-1111-1111-111111111111'}, ok=False)
    api.call('POST', '/niagara/systems/emitters', {**C, 'SourceAssetPath': EMITTER, 'VersionId': em['exposed_version_id']})
    assert len(names()) == len(base) + 1
    E, _ = handle(api, 'MCP_Glow')
    api.call('POST', '/niagara/systems/emitters/duplicate', {**E, 'NewName': 'MCP_GlowCopy'})
    assert names()[-1] == 'MCP_GlowCopy'
    E, _ = handle(api, base[1])
    api.call('DELETE', '/niagara/systems/emitters', {**E, 'bDryRun': True})
    assert base[1] in names()
    api.call('DELETE', '/niagara/systems/emitters', E)
    assert base[1] not in names() and len(names()) == len(base) + 1, names()


def system_settings_stage(api):
    # Warmup quantization, fixed bounds, determinism, fixed tick, effect type.
    r = api.call('PATCH', '/niagara/systems/warmup', {**C, 'WarmupTime': 1.05, 'WarmupDelta': 0.1})
    assert r['resolved_tick_count'] == 10, r
    api.call('PATCH', '/niagara/systems/warmup', {**C, 'WarmupTime': 1000.0, 'WarmupDelta': 0.1}, ok=False)
    d = system(api)
    assert d['warmup_tick_count'] == 10 and abs(d['warmup_time'] - 1.0) < 1e-4, d['warmup_time']
    api.call('PATCH', '/niagara/systems/fixed-bounds', {**C, 'bEnabled': True, 'BoundsMin': {'X': 5, 'Y': 0, 'Z': 0}, 'BoundsMax': {'X': -5, 'Y': 0, 'Z': 0}}, ok=False)
    api.call('PATCH', '/niagara/systems/fixed-bounds', {**C, 'bEnabled': True, 'BoundsMin': {'X': -5, 'Y': -6, 'Z': -7}, 'BoundsMax': {'X': 5, 'Y': 6, 'Z': 7}})
    d = system(api)
    assert d['fixed_bounds_enabled'] and d['authored_fixed_bounds']['min'] == [-5, -6, -7], d['authored_fixed_bounds']
    api.undo(); assert not system(api)['fixed_bounds_enabled']
    api.redo(); assert system(api)['fixed_bounds_enabled']
    api.call('PATCH', '/niagara/systems/determinism', {**C, 'bEnabled': True, 'RandomSeed': 42})
    api.call('PATCH', '/niagara/systems/fixed-tick', {**C, 'bEnabled': True, 'WarmupDelta': 0.02})
    s = {x['name']: x.get('value', x.get('value_text')) for x in system(api)['scalar_settings']}
    assert s['bDeterminism'] is True and s['RandomSeed'] == '42', s
    assert s['bFixedTickDelta'] is True and abs(s['FixedTickDeltaTime'] - 0.02) < 1e-6, s
    api.call('PATCH', '/niagara/systems/effect-type', {**C, 'SourceAssetPath': SOURCE}, ok=False)
    api.call('PATCH', '/niagara/systems/effect-type', {**C, 'SourceAssetPath': EFFECT})
    d = system(api)
    assert d['effect_type_path'] == EFFECT and d['effect_type_valid'] and d['effect_type_fields'], d['effect_type_path']
    # Compile request: dry run reports state only; the real request returns the native result.
    r = api.call('POST', '/niagara/systems/compile-request', {**C, 'bDryRun': True})
    assert r['native_request_result'] is None, r
    api.call('POST', '/niagara/systems/compile-request', {'AssetPath': SYS}, ok=False)
    r = api.call('POST', '/niagara/systems/compile-request', {**C, 'bForce': True})
    assert isinstance(r['native_request_result'], bool), r
    for sc in system(api)['system_scripts']:
        assert sc['last_compile_status_name'].startswith('NCS_'), sc


def user_stage(api):
    U = lambda **kw: {**C, **kw}
    api.call('POST', '/niagara/systems/user-parameters/scalar', U(ParameterName='MCP_F', ValueKind='float', ScalarValue=1), ok=False)
    api.call('POST', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_F', ValueKind='float', ScalarValue=2.5))
    api.call('POST', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_I', ValueKind='int', ScalarValue=7))
    api.call('POST', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_B', ValueKind='bool', ScalarValue=1))
    api.call('POST', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_I', ValueKind='float', ScalarValue=1), ok=False)
    api.call('POST', '/niagara/systems/user-parameters/vector', U(ParameterName='User.MCP_V', VectorValue={'X': 1, 'Y': 2, 'Z': 3}))
    api.call('POST', '/niagara/systems/user-parameters/color', U(ParameterName='User.MCP_C', ColorValue={'R': 2, 'G': 0.5, 'B': 0, 'A': 1}))
    api.call('POST', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_Gone', ValueKind='float', ScalarValue=1))
    u = users(api)
    assert u['User.MCP_F'] == 2.5 and u['User.MCP_I'] == 7 and u['User.MCP_B'] is True, u
    assert u['User.MCP_V'] == {'x': 1, 'y': 2, 'z': 3} and u['User.MCP_C'] == {'r': 2, 'g': 0.5, 'b': 0, 'a': 1}, u
    # Edit existing defaults.
    api.call('PATCH', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_I', ValueKind='int', ScalarValue=1.5), ok=False)
    api.call('PATCH', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_I', ValueKind='int', ScalarValue=9))
    api.call('PATCH', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_F', ValueKind='float', ScalarValue=4.25, bDryRun=True))
    assert users(api)['User.MCP_F'] == 2.5
    api.call('PATCH', '/niagara/systems/user-parameters/scalar', U(ParameterName='User.MCP_F', ValueKind='float', ScalarValue=4.25))
    api.undo(); assert users(api)['User.MCP_F'] == 2.5
    api.redo(); assert users(api)['User.MCP_F'] == 4.25
    api.call('PATCH', '/niagara/systems/user-parameters/vector', U(ParameterName='User.MCP_V', VectorValue={'X': 4, 'Y': 5, 'Z': 6}))
    api.call('PATCH', '/niagara/systems/user-parameters/color', U(ParameterName='User.MCP_C', ColorValue={'R': 0, 'G': 0, 'B': 3, 'A': 0.5}))
    api.call('PATCH', '/niagara/systems/user-parameters/color', U(ParameterName='User.MCP_V', ColorValue={'R': 0, 'G': 0, 'B': 3, 'A': 0.5}), ok=False)
    api.call('DELETE', '/niagara/systems/user-parameters', U(ParameterName='User.MCP_Gone', ValueKind='int'), ok=False)
    api.call('DELETE', '/niagara/systems/user-parameters', U(ParameterName='User.MCP_Gone', ValueKind='float'))
    u = users(api)
    assert 'User.MCP_Gone' not in u and u['User.MCP_I'] == 9 and u['User.MCP_V'] == {'x': 4, 'y': 5, 'z': 6}, u
    assert u['User.MCP_C'] == {'r': 0, 'g': 0, 'b': 3, 'a': 0.5}, u


def renderer_stage(api):
    em = 'MCP_Glow'
    types = api.call('GET', '/niagara/renderer-types', params={'search': ''})['renderer_types']
    sprite_t = next(t for t in types if t['class_path'].endswith('NiagaraSpriteRendererProperties'))
    assert sprite_t['supports_cpu'] and sprite_t['supports_gpu'], sprite_t
    R, r = renderer(api, em, 'NiagaraSpriteRendererProperties')
    i = api.call('POST', '/niagara/systems/renderers/inspect', R)
    assert i['supports_current_target'] and any(f['name'] == 'Alignment' and 'VelocityAligned' in f.get('enum_choices', []) for f in i['editable_fields'])
    api.call('PATCH', '/niagara/systems/renderers/enabled', {**R, 'bEnabled': not r['enabled']})
    api.call('PATCH', '/niagara/systems/renderers/scalar', {**R, 'FieldName': 'SortOrderHint', 'ScalarValue': 3})
    api.call('PATCH', '/niagara/systems/renderers/scalar', {**R, 'FieldName': 'MacroUVRadius', 'ScalarValue': 12.5})
    api.call('PATCH', '/niagara/systems/renderers/scalar', {**R, 'FieldName': 'bCastShadows', 'ScalarValue': 0})
    api.call('PATCH', '/niagara/systems/renderers/enum', {**R, 'FieldName': 'Alignment', 'NewName': 'NotAnAlignment'}, ok=False)
    api.call('PATCH', '/niagara/systems/renderers/enum', {**R, 'FieldName': 'Alignment', 'NewName': 'VelocityAligned'})
    api.call('PATCH', '/niagara/systems/renderers/enum', {**R, 'FieldName': 'SortMode', 'NewName': 'ViewDepth'})
    api.call('POST', '/niagara/systems/renderers/reset-field', {**R, 'FieldName': 'SortMode'})
    api.call('PATCH', '/niagara/systems/renderers/asset', {**R, 'FieldName': 'Material', 'SourceAssetPath': SOURCE}, ok=False)
    api.call('PATCH', '/niagara/systems/renderers/asset', {**R, 'FieldName': 'Material', 'SourceAssetPath': '/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial'})
    assert field(api, R, 'Alignment') == 'VelocityAligned' and field(api, R, 'SortMode') == 'None'
    assert 'DefaultMaterial.DefaultMaterial' in field(api, R, 'Material') and field(api, R, 'bCastShadows') == 'False'
    api.undo(); assert 'DefaultSpriteMaterial' in field(api, R, 'Material')
    api.redo(); assert 'DefaultMaterial.DefaultMaterial' in field(api, R, 'Material')
    M, _ = renderer(api, em, 'NiagaraMeshRendererProperties')
    api.call('PATCH', '/niagara/systems/renderers/vector', {**M, 'FieldName': 'LockedAxis', 'VectorValue': {'X': 0, 'Y': 1, 'Z': 0}})
    api.call('PATCH', '/niagara/systems/renderers/vector', {**M, 'FieldName': 'MeshBoundsScale', 'VectorValue': {'X': 2, 'Y': 2, 'Z': 2}})
    api.call('POST', '/niagara/systems/renderers/reset-field', {**M, 'FieldName': 'MeshBoundsScale'})
    assert field(api, M, 'LockedAxis').startswith('(X=0.000000,Y=1.000000'), field(api, M, 'LockedAxis')
    assert field(api, M, 'MeshBoundsScale').startswith('(X=1.000000'), field(api, M, 'MeshBoundsScale')
    # Add, reorder, duplicate, remove.
    E, e = handle(api, em)
    n = len(e['renderers'])
    api.call('POST', '/niagara/systems/renderers', {**E, 'RendererClass': '/Script/Niagara.NiagaraLightRendererProperties'})
    classes = lambda: [x['class_path'].rsplit('.', 1)[1] for x in handle(api, em)[1]['renderers']]
    assert len(classes()) == n + 1 and classes()[-1] == 'NiagaraLightRendererProperties'
    L, _ = renderer(api, em, 'NiagaraLightRendererProperties')
    api.call('PATCH', '/niagara/systems/renderers/order', {**L, 'TargetIndex': 0})
    assert classes()[0] == 'NiagaraLightRendererProperties', classes()
    api.call('PATCH', '/niagara/systems/renderers/order', {**L, 'TargetIndex': 0}, ok=False)  # stale index
    L, _ = renderer(api, em, 'NiagaraLightRendererProperties')
    api.call('POST', '/niagara/systems/renderers/duplicate', L)
    assert classes().count('NiagaraLightRendererProperties') == 2
    L, _ = renderer(api, em, 'NiagaraLightRendererProperties')
    api.call('DELETE', '/niagara/systems/renderers', L)
    assert classes().count('NiagaraLightRendererProperties') == 1 and len(classes()) == n + 1, classes()


def snapshot(api):
    d = system(api)
    for k in ('dirty', 'compile_requests_pending', 'compile_or_gpu_requests_pending', 'native_ready_to_run', 'system_scripts', 'scope'):
        d.pop(k, None)
    for e in d['emitters']:
        e.pop('scripts', None)
    rend = {}
    for e in d['emitters']:
        if e['name'] != 'MCP_Glow':
            continue
        for r in e['renderers']:
            R = {**C, 'EmitterIndex': e['index'], 'EmitterId': e['id'], 'RendererIndex': r['index'], 'RendererPath': r['object_path']}
            # Binding structs carry derived cache flags (bIsCachedParticleValue) that Niagara rebuilds on load.
            rend[r['object_path']] = {f['name']: f.get('value') for f in api.call('POST', '/niagara/systems/renderers/inspect', R)['editable_fields']
                                      if not f['name'].endswith('Binding')}
    em = api.call('GET', '/niagara/emitters/definition', params={'asset_path': EMITTER})
    em.pop('dirty', None)
    return {'system': d, 'renderers': rend, 'emitter_asset': em, 'empty_system_emitters': system(api, NEW_SYS)['emitter_count']}


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text('{}', encoding='utf-8')
    em = creation_stage(api)
    emitter_stage(api, em)
    system_settings_stage(api)
    user_stage(api)
    renderer_stage(api)
    for p in (SYS, EMITTER, EFFECT):
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared Niagara system authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api)
        for k in state['snapshot']:
            if k == 'renderers':
                a, b = state['snapshot'][k], cold[k]
                assert a.keys() == b.keys(), (sorted(a), sorted(b))
                diff = {(p, f): (a[p][f], b[p].get(f)) for p in a for f in a[p] if a[p][f] != b[p].get(f)}
                assert not diff, diff
            assert state['snapshot'][k] == cold[k], (k, json.dumps(state['snapshot'][k])[:600], json.dumps(cold[k])[:600])
        print('Cold reload of Niagara emitters, settings, user parameters, effect type and renderers: OK')
    finally:
        cleanup(api)


def cleanup(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned Niagara test assets')


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
