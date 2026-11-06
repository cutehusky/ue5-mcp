"""Live Niagara simulation-stage and versioned emitter-setting authoring on a duplicate of the engine's
RenderTargetTexturePainter template (four generic stages on a GPU emitter). The template is never modified.

prepare: author stages and emitter settings with guard/dry-run/undo checks, save and snapshot.
verify (fresh editor): compare the cold-loaded system, then delete the copy.
"""
import argparse
import json
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'niagara_stages.json'
SOURCE = '/Niagara/DefaultAssets/Templates/BehaviorExamples/RenderTargetTexturePainter.RenderTargetTexturePainter'
SYS = '/Game/UE5MCP_Test/NS_MCP_Stages.NS_MCP_Stages'
C = {'AssetPath': SYS, 'bConfirm': True}


def emitter(api):
    e = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})['emitters'][0]
    return {**C, 'EmitterIndex': 0, 'EmitterId': e['id'], 'VersionId': e['version_id']}, e


def stages(api):
    return emitter(api)[1]['simulation_stages']


def stage(api, name):
    E, e = emitter(api)
    s = next(s for s in e['simulation_stages'] if s['name'] == name)
    return {**E, 'StageIndex': s['index'], 'StagePath': s['object_path']}, s


def fields(s):
    return {f['name']: f.get('value') for f in s['editable_fields']}


def stage_stage(api):
    names = lambda: [s['name'] for s in stages(api)]
    assert names() == ['PaintToGrid', 'BlurGrid', 'AdvectGrid', 'RenderGridToRenderTarget'], names()
    S, s = stage(api, 'PaintToGrid')
    assert s['script']['usage_name'] == 'ParticleSimulationStageScript', s['script']
    # Enable flag: stale path guard, dry run, undo/redo.
    api.call('PATCH', '/niagara/systems/simulation-stages/enabled', {**S, 'StagePath': S['StagePath'] + 'X', 'bEnabled': False}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/enabled', {**S, 'bEnabled': False, 'bDryRun': True})
    assert stage(api, 'PaintToGrid')[1]['enabled']
    api.call('PATCH', '/niagara/systems/simulation-stages/enabled', {**S, 'bEnabled': False})
    assert not stage(api, 'PaintToGrid')[1]['enabled']
    api.undo(); assert stage(api, 'PaintToGrid')[1]['enabled']
    api.redo(); assert not stage(api, 'PaintToGrid')[1]['enabled']
    # Rename with duplicate-name guard.
    api.call('PATCH', '/niagara/systems/simulation-stages/name', {**S, 'NewName': 'BlurGrid'}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/name', {**S, 'NewName': 'MCP_Paint'})
    assert names()[0] == 'MCP_Paint'
    S, s = stage(api, 'MCP_Paint')
    # Enum, bool, particle-state range and integer default.
    api.call('PATCH', '/niagara/systems/simulation-stages/enum', {**S, 'FieldName': 'ExecuteBehavior', 'NewName': 'Sometimes'}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/enum', {**S, 'FieldName': 'ExecuteBehavior', 'NewName': 'OnSimulationReset'})
    api.call('PATCH', '/niagara/systems/simulation-stages/bool', {**S, 'FieldName': 'bDisablePartialParticleUpdate', 'bEnabled': True})
    api.call('PATCH', '/niagara/systems/simulation-stages/state-range', {**S, 'StateMin': 3, 'StateMax': 1}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/state-range', {**S, 'StateMin': 1, 'StateMax': 3})
    api.call('PATCH', '/niagara/systems/simulation-stages/integer-default', {**S, 'FieldName': 'NumIterations', 'ScalarValue': 1.5}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/integer-default', {**S, 'FieldName': 'NumIterations', 'ScalarValue': 4})
    f = fields(stage(api, 'MCP_Paint')[1])
    assert f['ExecuteBehavior'] == 'OnSimulationReset' and f['bDisablePartialParticleUpdate'] == 'True', f
    assert f['NumIterations'].startswith('(DefaultValue=(4,0,0,0)'), f['NumIterations']
    assert f['ParticleIterationStateRange'] == '(X=1,Y=3)', f
    # Enum choices and edit metadata, typed integer default bindings, and the dispatch enums.
    s = stage(api, 'MCP_Paint')[1]
    meta = {x['name']: x for x in s['editable_fields']}
    for name, enum, want in (('DirectDispatchType', 'ENiagaraGpuDispatchType', {'OneD', 'TwoD', 'ThreeD'}),
                             ('DirectDispatchElementType', 'ENiagaraDirectDispatchElementType', {'NumThreads', 'NumThreadsNoClipping'}),
                             ('ExecuteBehavior', 'ENiagaraSimStageExecuteBehavior', {'Always', 'OnSimulationReset'})):
        x = meta[name]
        assert x['enum_path'].endswith('.' + enum) and want <= {c['name'] for c in x['enum_choices']}, x
        assert all(c['qualified_name'] == f"{enum}::{c['name']}" and c['value_text'].isdigit() for c in x['enum_choices']), x
        assert not any(c['name'].endswith('MAX') for c in x['enum_choices']), x
    assert meta['ElementCountZ']['EditCondition'] == 'DirectDispatchType == ENiagaraGpuDispatchType::ThreeD', meta['ElementCountZ']
    assert meta['ElementCountY']['DisplayName'] == 'ElementCount Y' and meta['DirectDispatchType']['enum_choices_truncated'] is False, meta['ElementCountY']
    b = {x['field']: x for x in s['integer_default_bindings']}
    assert set(b) == {'NumIterations', 'ElementCountX', 'ElementCountY', 'ElementCountZ', 'OverrideGpuDispatchNumThreadsX',
                      'OverrideGpuDispatchNumThreadsY', 'OverrideGpuDispatchNumThreadsZ'} or len(b) == 7, sorted(b)
    assert b['NumIterations']['type_name'] == 'NiagaraInt32' and b['NumIterations']['int32_default_available'] and b['NumIterations']['default_value'] == 4, b['NumIterations']
    api.call('PATCH', '/niagara/systems/simulation-stages/enum', {**S, 'FieldName': 'DirectDispatchType', 'NewName': 'FourD'}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/enum', {**S, 'FieldName': 'DirectDispatchType', 'NewName': 'TwoD', 'bDryRun': True})
    assert fields(stage(api, 'MCP_Paint')[1])['DirectDispatchType'] == 'OneD'
    api.call('PATCH', '/niagara/systems/simulation-stages/enum', {**S, 'FieldName': 'DirectDispatchType', 'NewName': 'TwoD'})
    api.call('PATCH', '/niagara/systems/simulation-stages/enum', {**S, 'FieldName': 'DirectDispatchElementType', 'NewName': 'NumThreadsNoClipping'})
    f = fields(stage(api, 'MCP_Paint')[1])
    assert (f['DirectDispatchType'], f['DirectDispatchElementType']) == ('TwoD', 'NumThreadsNoClipping'), f
    api.call('PATCH', '/niagara/systems/simulation-stages/integer-default', {**S, 'FieldName': 'ElementCountY', 'ScalarValue': 16})
    assert {x['field']: x for x in stage(api, 'MCP_Paint')[1]['integer_default_bindings']}['ElementCountY']['default_value'] == 16
    # User integer binding, then reset of the binding.
    api.call('POST', '/niagara/systems/user-parameters/scalar', {**C, 'ParameterName': 'User.MCP_Iter', 'ValueKind': 'int', 'ScalarValue': 2})
    api.call('PATCH', '/niagara/systems/simulation-stages/user-integer-binding', {**S, 'FieldName': 'NumIterations', 'ParameterName': 'User.Missing'}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/user-integer-binding', {**S, 'FieldName': 'NumIterations', 'ParameterName': 'User.MCP_Iter'})
    assert 'MCP_Iter' in fields(stage(api, 'MCP_Paint')[1])['NumIterations']
    nb = {x['field']: x for x in stage(api, 'MCP_Paint')[1]['integer_default_bindings']}['NumIterations']
    assert nb['has_parameter_name'] and 'MCP_Iter' in nb['resolved_parameter'] + nb['aliased_parameter'], nb
    api.call('POST', '/niagara/systems/simulation-stages/reset-binding', {**S, 'FieldName': 'NumIterations'})
    assert 'MCP_Iter' not in fields(stage(api, 'MCP_Paint')[1])['NumIterations']
    api.undo(); assert 'MCP_Iter' in fields(stage(api, 'MCP_Paint')[1])['NumIterations']
    api.redo()
    # Reorder (final-index semantics), then remove one stage.
    api.call('PATCH', '/niagara/systems/simulation-stages/order', {**S, 'TargetIndex': 9}, ok=False)
    api.call('PATCH', '/niagara/systems/simulation-stages/order', {**S, 'TargetIndex': 2})
    assert names() == ['BlurGrid', 'AdvectGrid', 'MCP_Paint', 'RenderGridToRenderTarget'], names()
    B, _ = stage(api, 'BlurGrid')
    api.call('DELETE', '/niagara/systems/simulation-stages', {**B, 'bDryRun': True})
    assert len(names()) == 4
    api.call('DELETE', '/niagara/systems/simulation-stages', B)
    assert names() == ['AdvectGrid', 'MCP_Paint', 'RenderGridToRenderTarget'], names()
    api.undo(); assert len(names()) == 4
    api.redo(); assert names() == ['AdvectGrid', 'MCP_Paint', 'RenderGridToRenderTarget'], names()


def emitter_settings_stage(api):
    E, e = emitter(api)
    sim = lambda: emitter(api)[1]['simulation_settings']
    api.call('PATCH', '/niagara/systems/emitters/scalar', {**E, 'VersionId': '11111111-1111-1111-1111-111111111111', 'FieldName': 'bLocalSpace', 'ScalarValue': 1}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/scalar', {**E, 'FieldName': 'bLocalSpace', 'ScalarValue': 1, 'bDryRun': True})
    assert not sim()['local_space']
    api.call('PATCH', '/niagara/systems/emitters/scalar', {**E, 'FieldName': 'bLocalSpace', 'ScalarValue': 1})
    api.call('PATCH', '/niagara/systems/emitters/scalar', {**E, 'FieldName': 'bDeterminism', 'ScalarValue': 1})
    api.call('PATCH', '/niagara/systems/emitters/scalar', {**E, 'FieldName': 'RandomSeed', 'ScalarValue': 77})
    api.call('PATCH', '/niagara/systems/emitters/scalar', {**E, 'FieldName': 'RandomSeed', 'ScalarValue': 1.5}, ok=False)
    s = sim()
    assert s['local_space'] and s['determinism'] and s['random_seed'] == 77, s
    api.undo(); assert sim()['random_seed'] == 0
    api.redo(); assert sim()['random_seed'] == 77
    api.call('PATCH', '/niagara/systems/emitters/enum', {**E, 'FieldName': 'CalculateBoundsMode', 'NewName': 'Bogus'}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/enum', {**E, 'FieldName': 'CalculateBoundsMode', 'NewName': 'Fixed'})
    api.call('PATCH', '/niagara/systems/emitters/fixed-bounds', {**E, 'BoundsMin': {'X': 1, 'Y': 0, 'Z': 0}, 'BoundsMax': {'X': -1, 'Y': 0, 'Z': 0}}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/fixed-bounds', {**E, 'BoundsMin': {'X': -1, 'Y': -2, 'Z': -3}, 'BoundsMax': {'X': 1, 'Y': 2, 'Z': 3}})
    s = sim()
    assert s['bounds_mode_name'] == 'Fixed' and s['authored_fixed_bounds']['min'] == [-1, -2, -3], s
    assert s['authored_fixed_bounds']['max'] == [1, 2, 3], s


def snapshot(api):
    d = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})
    for k in ('dirty', 'compile_requests_pending', 'compile_or_gpu_requests_pending', 'native_ready_to_run', 'system_scripts', 'scope'):
        d.pop(k, None)
    for e in d['emitters']:
        e.pop('scripts', None)
        for s in e['simulation_stages']:
            s.pop('script', None)
            # Binding structs carry derived cache flags that Niagara rebuilds on load.
            s['editable_fields'] = [f for f in s['editable_fields'] if not f['type'].endswith('Binding')]
    return d


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text('{}', encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': SYS}, timeout=180)
    api.call('POST', '/niagara/systems/duplicate', {**C, 'SourceAssetPath': SOURCE})
    stage_stage(api)
    emitter_settings_stage(api)
    api.call('POST', '/assets/save', {'AssetPath': SYS})
    STATE.write_text(json.dumps({'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared Niagara stage/emitter-setting authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api)
        a, b = state['snapshot'], cold
        for i, (x, y) in enumerate(zip(a['emitters'], b['emitters'])):
            for j, (s, t) in enumerate(zip(x['simulation_stages'], y['simulation_stages'])):
                assert s == t, (i, j, json.dumps(s)[:800], json.dumps(t)[:800])
        assert a == b, (json.dumps(a)[:800], json.dumps(b)[:800])
        print('Cold reload of Niagara simulation stages and versioned emitter settings: OK')
    finally:
        cleanup(api)


def cleanup(api):
    httpx.post(api.base + '/assets/delete', json={'AssetPath': SYS}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned Niagara stage test asset')


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
