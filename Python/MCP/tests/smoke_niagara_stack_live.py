"""Live Niagara module-stack and rapid-iteration authoring on a duplicate of NS_JumpPad (never modified).

prepare: insert engine modules into emitter and system stacks, edit module inputs/enable state and
rapid-iteration parameters with guard/dry-run/undo checks, save and snapshot.
verify (fresh editor): compare the cold-loaded stacks, module inputs and rapid-iteration stores, then delete.
"""
import argparse
import json
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api
from smoke_niagara_system_live import SOURCE

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'niagara_stack.json'
SYS = '/Game/UE5MCP_Test/NS_MCP_Stack.NS_MCP_Stack'
DRAG = '/Niagara/Modules/Update/Forces/Drag.Drag'
SYSTEM_MODULE = '/Niagara/Modules/System/CompleteIfUnused.CompleteIfUnused'
SYSTEM_STATE = '/Niagara/Modules/System/SystemState.SystemState'
C = {'AssetPath': SYS, 'bConfirm': True}
EMITTER_STACKS = ('emitter_spawn', 'emitter_update', 'particle_spawn', 'particle_update')
SYSTEM_STACKS = ('system_spawn', 'system_update')


def emitter(api):
    e = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})['emitters'][0]
    return {**C, 'EmitterIndex': 0, 'EmitterId': e['id'], 'VersionId': e['version_id']}


def stack(api, stack_name, E=None):
    if E is None:
        return api.call('POST', '/niagara/systems/stack-inspect', {**C, 'ValueKind': stack_name})['modules']
    return api.call('POST', '/niagara/systems/emitters/stack-inspect', {**E, 'ValueKind': stack_name})['modules']


def module(api, M, system=False):
    route = '/niagara/systems/modules/inspect' if system else '/niagara/systems/emitters/modules/inspect'
    return api.call('POST', route, M)


def rapid(api, stack_name, E=None):
    if E is None:
        return api.call('POST', '/niagara/systems/rapid-iteration/inspect', {**C, 'ValueKind': stack_name})['parameters']
    return api.call('POST', '/niagara/systems/emitters/rapid-iteration/inspect', {**E, 'ValueKind': stack_name})['parameters']


def script_version(api, path):
    return api.call('POST', '/niagara/scripts/inspect', {'AssetPath': path})['exposed_version_id']


def emitter_module_stage(api):
    E = emitter(api)
    S = {**E, 'ValueKind': 'particle_update'}
    base = [m['script_path'] for m in stack(api, 'particle_update', E)]
    dv = script_version(api, DRAG)
    add = {**S, 'SourceAssetPath': DRAG, 'SourceVersionId': dv, 'TargetIndex': len(base)}
    api.call('POST', '/niagara/systems/emitters/modules', {**add, 'ValueKind': 'not_a_stack'}, ok=False)
    api.call('POST', '/niagara/systems/emitters/modules', {**add, 'TargetIndex': len(base) + 5}, ok=False)
    api.call('POST', '/niagara/systems/emitters/modules', {**add, 'SourceVersionId': '11111111-1111-1111-1111-111111111111'}, ok=False)
    api.call('POST', '/niagara/systems/emitters/modules', {**add, 'bDryRun': True})
    assert [m['script_path'] for m in stack(api, 'particle_update', E)] == base
    # Insert at the front, then append; indices follow execution order.
    first = api.call('POST', '/niagara/systems/emitters/modules', {**add, 'TargetIndex': 0})
    order = [m['script_path'] for m in stack(api, 'particle_update', E)]
    assert order == [DRAG] + base, order
    api.undo(); assert [m['script_path'] for m in stack(api, 'particle_update', E)] == base
    api.redo()
    first = next(m for m in stack(api, 'particle_update', E) if m['script_path'] == DRAG)
    M = {**S, 'NodeId': first['node_id'], 'NodePath': first['node_path']}
    deps = api.call('POST', '/niagara/systems/emitters/stack-dependencies', S)
    assert any(d['dependency_id'] == 'SolveForcesAndVelocity' and not d['satisfied_in_this_stack'] for d in deps['dependency_checks']), deps
    # Module inputs: bool pin default (range guard, dry run, undo/redo) and reset.
    mi = module(api, M)
    assert mi['script_path'] == DRAG and mi['function_name'] == 'Drag'
    pin = next(p for p in mi['inputs'] if p['name'] == 'Use Linear Drag')
    P = {**M, 'PinId': pin['pin_id']}
    value = lambda: next(p for p in module(api, M)['inputs'] if p['pin_id'] == pin['pin_id'])['default_value']
    api.call('PATCH', '/niagara/systems/emitters/modules/pin-default', {**P, 'ScalarValue': 2}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/modules/pin-default', {**P, 'ScalarValue': 0, 'bDryRun': True})
    assert value() == 'true'
    api.call('PATCH', '/niagara/systems/emitters/modules/pin-default', {**P, 'ScalarValue': 0})
    assert value() == 'false'
    api.undo(); assert value() == 'true'
    api.redo(); assert value() == 'false'
    api.call('POST', '/niagara/systems/emitters/modules/reset-pin-default', P)
    assert value() == 'true'
    api.call('PATCH', '/niagara/systems/emitters/modules/pin-default', {**P, 'ScalarValue': 0})
    # Enable state.
    api.call('PATCH', '/niagara/systems/emitters/modules/enabled', {**M, 'bEnabled': False})
    m = next(x for x in stack(api, 'particle_update', E) if x['node_id'] == first['node_id'])
    assert m['desired_enabled_state'] != 0, m
    return M


def emitter_rapid_stage(api):
    E = emitter(api)
    found = {s: rapid(api, s, E) for s in EMITTER_STACKS}
    stack_name, params = next(((s, p) for s, p in found.items() if any(x['stored_input_value'].get('value_kind') == 'float' for x in p)), (None, None))
    assert stack_name, {s: len(p) for s, p in found.items()}
    R = {**E, 'ValueKind': stack_name}
    f = next(x for x in params if x['stored_input_value'].get('value_kind') == 'float')
    get = lambda name: next(x for x in rapid(api, stack_name, E) if x['name'] == name)['stored_input_value']['value']
    api.call('PATCH', '/niagara/systems/emitters/rapid-iteration/scalar', {**R, 'ParameterName': f['name'], 'FieldName': 'int', 'ScalarValue': 3}, ok=False)
    api.call('PATCH', '/niagara/systems/emitters/rapid-iteration/scalar', {**R, 'ParameterName': f['name'], 'FieldName': 'float', 'ScalarValue': 0.375, 'bDryRun': True})
    assert get(f['name']) == f['stored_input_value']['value']
    api.call('PATCH', '/niagara/systems/emitters/rapid-iteration/scalar', {**R, 'ParameterName': f['name'], 'FieldName': 'float', 'ScalarValue': 0.375})
    assert get(f['name']) == 0.375
    api.undo(); assert get(f['name']) == f['stored_input_value']['value']
    api.redo(); assert get(f['name']) == 0.375
    compound = next((x for x in rapid(api, stack_name, E) if x['stored_input_value'].get('value_kind') in ('vector3', 'color')), None)
    if compound:
        kind = 'vector' if compound['stored_input_value']['value_kind'] == 'vector3' else 'color'
        api.call('PATCH', '/niagara/systems/emitters/rapid-iteration/compound', {**R, 'ParameterName': compound['name'], 'FieldName': kind,
                                                                                 'VectorValue': {'X': 1, 'Y': 2, 'Z': 3}, 'ColorValue': {'R': 1, 'G': 2, 'B': 3, 'A': 1}})
    removable = next(x for x in rapid(api, stack_name, E) if x['name'] != f['name'] and x['stored_input_value'].get('value_kind') == 'float')
    n = len(rapid(api, stack_name, E))
    api.call('DELETE', '/niagara/systems/emitters/rapid-iteration', {**R, 'ParameterName': removable['name'], 'FieldName': 'int'}, ok=False)
    api.call('DELETE', '/niagara/systems/emitters/rapid-iteration', {**R, 'ParameterName': removable['name'], 'FieldName': 'float'})
    assert len(rapid(api, stack_name, E)) == n - 1
    return stack_name, compound is not None


def system_stage(api):
    base = [m['script_path'] for m in stack(api, 'system_update')]
    sv = script_version(api, SYSTEM_MODULE)
    add = {**C, 'ValueKind': 'system_update', 'SourceAssetPath': SYSTEM_MODULE, 'SourceVersionId': sv, 'TargetIndex': len(base)}
    api.call('POST', '/niagara/systems/modules', {**add, 'ValueKind': 'particle_update'}, ok=False)
    api.call('POST', '/niagara/systems/modules', add)
    mods = stack(api, 'system_update')
    assert [m['script_path'] for m in mods] == base + [SYSTEM_MODULE], mods
    new = mods[-1]
    M = {**C, 'ValueKind': 'system_update', 'NodeId': new['node_id'], 'NodePath': new['node_path']}
    mi = module(api, M, system=True)
    assert mi['script_path'] == SYSTEM_MODULE, mi
    scalar = next((p for p in mi['inputs'] if p['type'] in ('NiagaraFloat', 'NiagaraInt32', 'NiagaraBool') and p['link_count'] == 0), None)
    if scalar:
        v = {'NiagaraFloat': 2.5, 'NiagaraInt32': 3, 'NiagaraBool': 0 if scalar['default_value'] == 'true' else 1}[scalar['type']]
        api.call('PATCH', '/niagara/systems/modules/pin-default', {**M, 'PinId': scalar['pin_id'], 'ScalarValue': v})
    # SystemState has an unlinked bool pin: system module pin default with dry run, undo/redo and autogenerated reset.
    sv2 = script_version(api, SYSTEM_STATE)
    api.call('POST', '/niagara/systems/modules', {**add, 'SourceAssetPath': SYSTEM_STATE, 'SourceVersionId': sv2, 'TargetIndex': len(base) + 1})
    st = next(m for m in stack(api, 'system_update') if m['script_path'] == SYSTEM_STATE)
    M2 = {**C, 'ValueKind': 'system_update', 'NodeId': st['node_id'], 'NodePath': st['node_path']}
    pin = next(p for p in module(api, M2, system=True)['inputs'] if p['name'] == 'UseLoopDelay')
    assert pin['type'] == 'NiagaraBool' and pin['link_count'] == 0 and pin['default_value'] == 'false', pin
    P2 = {**M2, 'PinId': pin['pin_id']}
    value = lambda: next(p for p in module(api, M2, system=True)['inputs'] if p['pin_id'] == pin['pin_id'])['default_value']
    api.call('PATCH', '/niagara/systems/modules/pin-default', {**P2, 'ScalarValue': 2}, ok=False)
    api.call('PATCH', '/niagara/systems/modules/pin-default', {**P2, 'PinId': '0' * 32, 'ScalarValue': 1}, ok=False)
    api.call('PATCH', '/niagara/systems/modules/pin-default', {**P2, 'ScalarValue': 1, 'bDryRun': True})
    assert value() == 'false'
    api.call('PATCH', '/niagara/systems/modules/pin-default', {**P2, 'ScalarValue': 1})
    assert value() == 'true'
    api.undo(); assert value() == 'false'
    api.redo(); assert value() == 'true'
    api.call('POST', '/niagara/systems/modules/reset-pin-default', P2)
    assert value() == 'false'
    api.call('PATCH', '/niagara/systems/modules/pin-default', {**P2, 'ScalarValue': 1})
    assert value() == 'true'
    api.call('PATCH', '/niagara/systems/modules/enabled', {**M, 'bEnabled': False})
    assert next(m for m in stack(api, 'system_update') if m['node_id'] == new['node_id'])['desired_enabled_state'] != 0
    api.call('POST', '/niagara/systems/stack-dependencies', {**C, 'ValueKind': 'system_update'})
    # System rapid-iteration store.
    params = rapid(api, 'system_update')
    f = next(x for x in params if x['stored_input_value'].get('value_kind') == 'float')
    get = lambda: next(x for x in rapid(api, 'system_update') if x['name'] == f['name'])['stored_input_value']['value']
    api.call('PATCH', '/niagara/systems/rapid-iteration/scalar', {**C, 'ValueKind': 'system_update', 'ParameterName': 'Constants.Nope', 'FieldName': 'float', 'ScalarValue': 1}, ok=False)
    api.call('PATCH', '/niagara/systems/rapid-iteration/scalar', {**C, 'ValueKind': 'system_update', 'ParameterName': f['name'], 'FieldName': 'float', 'ScalarValue': 4.5})
    assert get() == 4.5
    api.undo(); assert get() == f['stored_input_value']['value']
    api.redo(); assert get() == 4.5
    removable = next(x for x in params if x['name'] != f['name'] and x['stored_input_value'].get('value_kind') == 'float')
    api.call('DELETE', '/niagara/systems/rapid-iteration', {**C, 'ValueKind': 'system_update', 'ParameterName': removable['name'], 'FieldName': 'float'})
    assert len(rapid(api, 'system_update')) == len(params) - 1
    return scalar is not None


def system_state_inputs(api):
    st = next(m for m in stack(api, 'system_update') if m['script_path'] == SYSTEM_STATE)
    M = {**C, 'ValueKind': 'system_update', 'NodeId': st['node_id'], 'NodePath': st['node_path']}
    return {p['name']: p['default_value'] for p in module(api, M, system=True)['inputs']}


def snapshot(api, M):
    E = emitter(api)
    out = {'emitter_stacks': {s: stack(api, s, E) for s in EMITTER_STACKS},
           'system_stacks': {s: stack(api, s) for s in SYSTEM_STACKS},
           'emitter_rapid': {s: rapid(api, s, E) for s in EMITTER_STACKS},
           'system_rapid': {s: rapid(api, s) for s in SYSTEM_STACKS},
           'drag_inputs': module(api, M)['inputs'],
           'system_state_inputs': system_state_inputs(api)}
    return json.loads(json.dumps(out))


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text('{}', encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': SYS}, timeout=180)
    api.call('POST', '/niagara/systems/duplicate', {**C, 'SourceAssetPath': SOURCE})
    M = emitter_module_stage(api)
    rapid_stack, compound = emitter_rapid_stage(api)
    system_pin = system_stage(api)
    api.call('POST', '/assets/save', {'AssetPath': SYS})
    STATE.write_text(json.dumps({'snapshot': snapshot(api, M), 'module': M}), encoding='utf-8')
    print(f'prepared Niagara stack authoring (emitter rapid stack {rapid_stack}, compound edit {compound}, system pin edit {system_pin}); restart and verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api, state['module'])
        for k in state['snapshot']:
            assert state['snapshot'][k] == cold[k], (k, json.dumps(state['snapshot'][k])[:700], json.dumps(cold[k])[:700])
        print('Cold reload of Niagara module stacks, module inputs and rapid-iteration stores: OK')
    finally:
        cleanup(api)


def cleanup(api):
    httpx.post(api.base + '/assets/delete', json={'AssetPath': SYS}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned Niagara stack test asset')


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
