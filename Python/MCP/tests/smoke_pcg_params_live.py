"""Live PCG graph parameter and graph-instance authoring (part 2) on scratch PCG graphs.

prepare: create a base graph (and a second base for parent reassignment) with one parameter of every supported kind
(bool/int/int64/float/double, name/string/text, vector/rotator/transform, enum, hard/soft object, hard/soft class,
bool/int/float/double/name/string/vector arrays), dry runs and duplicate/invalid-name refusals first; set every
default; rename and remove a parameter; create a graph instance (dry run first), override values on the instance,
enable/disable/reset overrides, duplicate the instance and reassign its parent. Every edit has a dry run and a
stale-identity refusal; one edit per route also undo/redo. Save and snapshot.
verify (fresh editor): load the assets, compare both interfaces (values, overrides, arrays), then delete.
"""
import argparse
import json
import time
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api
from smoke_pcg_graph_live import diff, text_neutral

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'pcg_params.json'
D = '/Game/UE5MCP_Test/'
LIVE = {'bConfirm': True, 'bDryRun': False}
MESH = '/Engine/BasicShapes/Cube.Cube'
MESH_B = '/Engine/BasicShapes/Sphere.Sphere'
ENUM = '/Script/Engine.ECollisionChannel'
G = G2 = I = I2 = None
PI = '/pcg/graph-interfaces/parameters/'
KINDS = {'bool': None, 'int': None, 'int64': None, 'float': None, 'double': None, 'name': None, 'string': None, 'text': None, 'vector': None,
         'rotator': None, 'transform': None, 'bool_array': None, 'int_array': None, 'float_array': None, 'double_array': None, 'name_array': None,
         'string_array': None, 'vector_array': None, 'enum': {'SourceAssetPath': ENUM}, 'object': {'SettingsClass': '/Script/Engine.StaticMesh'},
         'soft_object': {'SettingsClass': '/Script/Engine.StaticMesh'}, 'class': {'SettingsClass': '/Script/Engine.Actor'},
         'soft_class': {'SettingsClass': '/Script/Engine.Actor'}}
ARRAYS = ('bool_array', 'int_array', 'float_array', 'double_array', 'name_array', 'string_array', 'vector_array')


def use_tag(tag):
    global G, G2, I, I2
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    G, G2, I, I2 = n('PCG_MCP_Params'), n('PCG_MCP_Params2'), n('PCGI_MCP_Inst'), n('PCGI_MCP_InstDup')


def iface(api, path):
    return api.call('POST', '/pcg/graph-interfaces/inspect', {'AssetPath': path})


def param(api, path, name):
    return next(p for p in iface(api, path)['parameters'] if p['name'] == name)


def pid(api, path, name):
    return {'AssetPath': path, 'ParameterName': name, 'ParameterId': param(api, path, name)['id']}


def arrays(api, path):
    out = {}
    for k in ARRAYS:
        p = next((p for p in iface(api, path)['parameters'] if p['name'] == f'P_{k}'), None)
        if p:
            out[k] = {kk: vv for kk, vv in api.call('POST', PI + 'array/inspect', {'AssetPath': path, 'ParameterName': p['name'], 'ParameterId': p['id'],
                                                                                   'ElementStart': 0, 'ElementCount': 64}).items() if kk not in ('scope', 'dirty')}
    return out


def full(api):
    out = {}
    for path in (G, G2, I, I2):
        r = httpx.post(api.base + '/pcg/graph-interfaces/inspect', json={'AssetPath': path}, timeout=60)
        if r.is_success:
            out[path] = {'interface': {k: v for k, v in r.json().items() if k not in ('scope', 'dirty')}, 'arrays': arrays(api, path)}
        elif 'not found' not in r.text.lower() and 'required' not in r.text.lower():
            out[path] = {'error': r.text[:300]}
        else:
            out[path] = {'missing': r.text[:200]}
    return text_neutral(out)


def settled(api):
    prev = full(api)
    for _ in range(20):
        time.sleep(0.2)
        cur = full(api)
        if cur == prev:
            return cur
        prev = cur
    raise AssertionError('PCG parameter state did not settle')


def edit(api, method, route, body, check, undo=False, stale=None):
    before = settled(api)
    d = api.call(method, route, {**body, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, body, d)
    assert settled(api) == before, (route, body, 'dry run changed state', diff(before, full(api))[:4])
    if stale:
        api.call(method, route, {**body, **stale, **LIVE}, ok=False)
    api.call(method, route, {**body, **LIVE})
    after = settled(api)
    assert check(before, after), (route, body, diff(before, after)[:6])
    if undo:
        api.undo()
        u = settled(api)
        assert u == before, (route, body, 'undo did not restore', diff(before, u)[:6])
        api.redo()
        r = settled(api)
        assert r == after, (route, body, 'redo did not reapply', diff(after, r)[:6])
    return after


STALE = {'ParameterId': '00000000-0000-0000-0000-000000000000'}


def create_stage(api):
    for path in (G, G2):
        api.call('POST', '/pcg/graphs', {'AssetPath': path, **LIVE})
    first = True
    for kind, extra in KINDS.items():
        body = {'AssetPath': G, 'ParameterName': f'P_{kind}', 'ValueKind': kind, **(extra or {})}
        if first:
            d = api.call('POST', '/pcg/graphs/parameters', {**body, 'bConfirm': True, 'bDryRun': True})
            assert d['dry_run'] and iface(api, G)['parameter_count'] == 0, d
            api.call('POST', '/pcg/graphs/parameters', {**body, 'ParameterName': 'bad name!', **LIVE}, ok=False)
            api.call('POST', '/pcg/graphs/parameters', {**body, 'ValueKind': 'quaternion', **LIVE}, ok=False)
        api.call('POST', '/pcg/graphs/parameters', {**body, **LIVE})
        first = False
    api.call('POST', '/pcg/graphs/parameters', {'AssetPath': G, 'ParameterName': 'P_bool', 'ValueKind': 'bool', **LIVE}, ok=False)
    api.call('POST', '/pcg/graphs/parameters', {'AssetPath': G, 'ParameterName': 'P_removeme', 'ValueKind': 'int', **LIVE})
    # The second base graph shares a subset so the instance can be reparented onto it.
    api.call('POST', '/pcg/graphs/parameters', {'AssetPath': G2, 'ParameterName': 'P_float', 'ValueKind': 'float', **LIVE})
    assert iface(api, G)['parameter_count'] == len(KINDS) + 1
    e = param(api, G, 'P_enum')
    names = [c['name'] for c in e['enum_choices']]
    assert e['enum_path'] == ENUM and 'ECC_Visibility' in names and all(c['supported_by_enum_setter'] for c in e['enum_choices'][:4]), e


def values(path):
    """(route, payload, expected native text check) per parameter kind for one value set."""
    is_inst = path == I
    k = 2 if is_inst else 1
    return {
        # The instance must differ from the inherited default: same-value requests are native no-ops (no override).
        'bool': ('scalar', {'ScalarValue': 0 if is_inst else 1}, lambda v: v == ('False' if is_inst else 'True')),
        'int': ('scalar', {'ScalarValue': 7 * k}, lambda v: v == str(7 * k)),
        'float': ('scalar', {'ScalarValue': 1.5 * k}, lambda v: float(v) == 1.5 * k),
        'double': ('scalar', {'ScalarValue': 2.25 * k}, lambda v: float(v) == 2.25 * k),
        'int64': ('int64', {'TextValue': str(9007199254740993 * k)}, lambda v: v == str(9007199254740993 * k)),
        'name': ('text', {'TextValue': f'MCPName{k}'}, lambda v: v == f'MCPName{k}'),
        'string': ('text', {'TextValue': f'MCP string {k}'}, lambda v: v == f'MCP string {k}'),
        'text': ('text', {'TextValue': f'MCP text {k}'}, lambda v: f'MCP text {k}' in v),
        'vector': ('vector', {'VectorValue': {'X': 1 * k, 'Y': 2, 'Z': 3}}, lambda v: v.startswith(f'(X={float(k):.6f}')),
        'rotator': ('rotator', {'RotatorValue': {'Pitch': 10 * k, 'Yaw': 20, 'Roll': 30}}, lambda v: f'Pitch={10.0 * k:.6f}' in v),
        'transform': ('transform', {'TransformValue': {'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Translation': {'X': 5 * k, 'Y': 6, 'Z': 7},
                                                       'Scale3D': {'X': 1, 'Y': 2, 'Z': 3}}}, lambda v: f'{5.0 * k:.6f}' in v),
        'enum': ('enum', {'EnumValue': 'ECC_Visibility' if k == 1 else 'ECC_Camera'}, lambda v: v.endswith('ECC_Visibility' if k == 1 else 'ECC_Camera')),
        'object': ('asset', {'SourceAssetPath': MESH if k == 1 else MESH_B}, lambda v: (MESH if k == 1 else MESH_B).split('.')[-1] in v),
        'soft_object': ('asset', {'SourceAssetPath': MESH if k == 1 else MESH_B}, lambda v: (MESH if k == 1 else MESH_B).split('.')[-1] in v),
        'class': ('class', {'SourceAssetPath': '/Script/Engine.StaticMeshActor' if k == 1 else '/Script/Engine.PointLight'},
                  lambda v: ('StaticMeshActor' if k == 1 else 'PointLight') in v),
        'soft_class': ('class', {'SourceAssetPath': '/Script/Engine.StaticMeshActor' if k == 1 else '/Script/Engine.PointLight'},
                       lambda v: ('StaticMeshActor' if k == 1 else 'PointLight') in v),
        'bool_array': ('scalar-array', {'ScalarValues': [1, 0, 1][:k + 1]}, None),
        'int_array': ('scalar-array', {'ScalarValues': [3, 4, 5][:k + 1]}, None),
        'float_array': ('scalar-array', {'ScalarValues': [0.5, 1.5, 2.5][:k + 1]}, None),
        'double_array': ('scalar-array', {'ScalarValues': [0.25, 0.75][:k]}, None),
        'name_array': ('string-array', {'StringValues': ['A', 'B', 'C'][:k + 1]}, None),
        'string_array': ('string-array', {'StringValues': ['x y', 'z'][:k]}, None),
        'vector_array': ('vector-array', {'VectorValues': [{'X': 1, 'Y': 2, 'Z': 3}, {'X': 4, 'Y': 5, 'Z': 6}][:k]}, None),
    }


def value_stage(api, path):
    seen = set()
    for kind, (route, payload, ok) in values(path).items():
        name = f'P_{kind}'
        if ok:
            check = lambda b, a, name=name, ok=ok: ok(next(p for p in a[path]['interface']['parameters'] if p['name'] == name)['value'])
        else:
            n_expected = len(next(iter(payload.values())))
            check = lambda b, a, kind=kind, n_expected=n_expected: json.dumps(a[path]['arrays'][kind]).count('"index"') == n_expected or \
                a[path]['arrays'][kind].get('element_count', a[path]['arrays'][kind].get('count')) == n_expected
        edit(api, 'PATCH', PI + route, {**pid(api, path, name), **payload}, check, undo=route not in seen, stale=STALE)
        seen.add(route)
    # Type and range refusals.
    api.call('PATCH', PI + 'scalar', {**pid(api, path, 'P_vector'), 'ScalarValue': 1, **LIVE}, ok=False)
    api.call('PATCH', PI + 'enum', {**pid(api, path, 'P_enum'), 'EnumValue': 'NoSuchValue', **LIVE}, ok=False)
    api.call('PATCH', PI + 'int64', {**pid(api, path, 'P_int64'), 'TextValue': '99999999999999999999', **LIVE}, ok=False)
    api.call('PATCH', PI + 'asset', {**pid(api, path, 'P_object'), 'SourceAssetPath': '/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial', **LIVE}, ok=False)


def rename_remove_stage(api):
    edit(api, 'PATCH', '/pcg/graphs/parameters/name', {**pid(api, G, 'P_removeme'), 'TextValue': 'P_renamed'},
         lambda b, a: any(p['name'] == 'P_renamed' for p in a[G]['interface']['parameters']), undo=True, stale=STALE)
    api.call('PATCH', '/pcg/graphs/parameters/name', {**pid(api, G, 'P_renamed'), 'TextValue': 'P_bool', **LIVE}, ok=False)
    edit(api, 'POST', '/pcg/graphs/parameters/remove', pid(api, G, 'P_renamed'),
         lambda b, a: a[G]['interface']['parameter_count'] == b[G]['interface']['parameter_count'] - 1, undo=True, stale=STALE)


def instance_stage(api):
    d = api.call('POST', '/pcg/graph-instances', {'AssetPath': I, 'SourceAssetPath': G, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'], d
    api.call('POST', '/pcg/graph-instances', {'AssetPath': I, 'SourceAssetPath': G, **LIVE})
    api.call('POST', '/pcg/graph-instances', {'AssetPath': I, 'SourceAssetPath': G, **LIVE}, ok=False)
    inst = iface(api, I)
    assert inst['is_instance'] and inst['parent_chain'] == [G] and inst['parameter_count'] == len(KINDS), inst['parent_chain']
    value_stage(api, I)
    ov = lambda a, name: next(p for p in a[I]['interface']['parameters'] if p['name'] == name)
    edit(api, 'PATCH', '/pcg/graph-instances/parameters/override', {**pid(api, I, 'P_int'), 'Action': 'disable_override'},
         lambda b, a: ov(b, 'P_int')['overridden'] and not ov(a, 'P_int')['overridden'], undo=True, stale=STALE)
    edit(api, 'PATCH', '/pcg/graph-instances/parameters/override', {**pid(api, I, 'P_int'), 'Action': 'enable_override'},
         lambda b, a: ov(a, 'P_int')['overridden'])
    edit(api, 'PATCH', '/pcg/graph-instances/parameters/override', {**pid(api, I, 'P_float'), 'Action': 'reset_value'},
         lambda b, a: not ov(a, 'P_float')['overridden_and_not_default'], undo=True)
    # Duplicate the instance, then reparent the duplicate onto the second base graph.
    d = api.call('POST', '/pcg/graph-instances/duplicate', {'SourceAssetPath': I, 'AssetPath': I2, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'], d
    api.call('POST', '/pcg/graph-instances/duplicate', {'SourceAssetPath': I, 'AssetPath': I2, **LIVE})
    strip_path = lambda x, p: json.loads(json.dumps(x).replace(p, 'X'))
    assert strip_path(full(api)[I2]['interface']['parameters'], I2) == strip_path(full(api)[I]['interface']['parameters'], I), 'instance duplicate differs'
    body = {'AssetPath': I2, 'SourceAssetPath': G2, 'RecordHash': iface(api, I2)['parent_hash']}
    edit(api, 'PATCH', '/pcg/graph-instances/parent', body, lambda b, a: a[I2]['interface']['parent_chain'] == [G2], undo=True, stale={'RecordHash': '0' * 32})
    api.call('PATCH', '/pcg/graph-instances/parent', {'AssetPath': I2, 'SourceAssetPath': I2, 'RecordHash': iface(api, I2)['parent_hash'], **LIVE}, ok=False)


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'tag': tag}), encoding='utf-8')
    create_stage(api)
    value_stage(api, G)
    rename_remove_stage(api)
    instance_stage(api)
    for p in (G, G2, I, I2):
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'tag': tag, 'snapshot': settled(api)}), encoding='utf-8')
    print('prepared PCG parameter/instance authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in (G, G2, I, I2):
            api.call('GET', '/assets/describe', params={'asset_path': p})
        cold = settled(api)
        d = diff(state['snapshot'], cold)
        assert not d, d[:10]
        print('Cold reload of PCG graph parameters (23 kinds), instance overrides, duplicate and reparented instance: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    for p in (I2, I, G, G2):
        if p:
            httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned PCG parameter test assets')


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
