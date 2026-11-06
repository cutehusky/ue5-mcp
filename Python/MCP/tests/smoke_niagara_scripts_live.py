"""Live Niagara script asset and script-graph authoring on scratch scripts created by the test.

prepare: create function/module scripts, author version metadata and graph nodes/pins/inputs/outputs with
guard/dry-run/undo checks, save and snapshot.
verify (fresh editor): compare the cold-loaded scripts and graphs, then delete them.
"""
import argparse
import json
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'niagara_scripts.json'
FN = '/Game/UE5MCP_Test/NF_MCP_Work.NF_MCP_Work'
CALLEE = '/Game/UE5MCP_Test/NF_MCP_Callee.NF_MCP_Callee'
MODULE = '/Game/UE5MCP_Test/NM_MCP_Work.NM_MCP_Work'
COPY = '/Game/UE5MCP_Test/NM_MCP_Copy.NM_MCP_Copy'
ASSETS = (FN, CALLEE, MODULE, COPY)


def script(api, path):
    return api.call('POST', '/niagara/scripts/inspect', {'AssetPath': path})


def ver(api, path):
    return {'AssetPath': path, 'bConfirm': True, 'VersionId': script(api, path)['exposed_version_id']}


def graph(api, V):
    return api.call('POST', '/niagara/scripts/graph/inspect', V)


def node(api, V, pred):
    return next(n for n in graph(api, V)['nodes'] if pred(n))


def ident(V, n):
    return {**V, 'NodeId': n['id'], 'NodePath': n['object_path']}


def creation_stage(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    api.call('POST', '/niagara/scripts', {'AssetPath': FN, 'bConfirm': True, 'ValueKind': 'shader'}, ok=False)
    api.call('POST', '/niagara/scripts', {'AssetPath': FN, 'bConfirm': True, 'ValueKind': 'function', 'bDryRun': True})
    api.call('POST', '/niagara/scripts/inspect', {'AssetPath': FN}, ok=False)
    for path, kind in ((FN, 'function'), (CALLEE, 'function'), (MODULE, 'module')):
        api.call('POST', '/niagara/scripts', {'AssetPath': path, 'bConfirm': True, 'ValueKind': kind})
    assert script(api, FN)['usage_name'] == 'Function' and script(api, MODULE)['usage_name'] == 'Module'
    s = script(api, MODULE)
    assert s['version_count'] == 1 and s['versions'][0]['exposed'], s


def metadata_stage(api):
    V = ver(api, MODULE)
    v = lambda: script(api, MODULE)['versions'][0]
    api.call('PATCH', '/niagara/scripts/text', {**V, 'VersionId': '11111111-1111-1111-1111-111111111111', 'FieldName': 'Category', 'TextValue': 'X'}, ok=False)
    api.call('PATCH', '/niagara/scripts/text', {**V, 'FieldName': 'Category', 'TextValue': 'MCP', 'bDryRun': True})
    assert v()['category']['text'] == 'Default'
    api.call('PATCH', '/niagara/scripts/text', {**V, 'FieldName': 'Category', 'TextValue': 'MCP'})
    api.call('PATCH', '/niagara/scripts/text', {**V, 'FieldName': 'Description', 'TextValue': 'Scratch module'})
    api.call('PATCH', '/niagara/scripts/text', {**V, 'FieldName': 'Keywords', 'TextValue': 'mcp test'})
    api.undo(); assert v()['keywords']['text'] == ''
    api.redo(); assert v()['keywords']['text'] == 'mcp test'
    api.call('PATCH', '/niagara/scripts/bool', {**V, 'FieldName': 'bSuggested', 'bEnabled': True})
    api.call('PATCH', '/niagara/scripts/bool', {**V, 'FieldName': 'bExperimental', 'bEnabled': True})
    api.call('PATCH', '/niagara/scripts/enum', {**V, 'FieldName': 'LibraryVisibility', 'NewName': 'Nope'}, ok=False)
    api.call('PATCH', '/niagara/scripts/enum', {**V, 'FieldName': 'LibraryVisibility', 'NewName': 'Library'})
    api.call('PATCH', '/niagara/scripts/usage-contexts', {**V, 'UsageNames': ['NotAUsage']}, ok=False)
    api.call('PATCH', '/niagara/scripts/usage-contexts', {**V, 'UsageNames': ['ParticleSpawnScript', 'ParticleUpdateScript']})
    api.call('PATCH', '/niagara/scripts/provided-dependencies', {**V, 'DependencyIds': ['MCPProvided']})
    api.call('PATCH', '/niagara/scripts/required-dependencies', {**V, 'RequiredDependencies': [{'Id': 'MCPRequired'}]})
    x = v()
    assert x['category']['text'] == 'MCP' and x['description']['text'] == 'Scratch module', x
    assert x['suggested'] and x['experimental'] and x['library_visibility_name'] == 'Library', x
    assert x['module_usage_bitmask'] == 40 and x['provided_dependencies'] == ['MCPProvided'], x
    assert x['required_dependency_count'] == 1 and 'MCPRequired' in json.dumps(x['required_dependencies']), x
    # Duplicate the module; a deprecation replacement must have matching usage and be another asset.
    api.call('POST', '/niagara/scripts/duplicate', {'AssetPath': COPY, 'SourceAssetPath': MODULE, 'bConfirm': True})
    assert script(api, COPY)['versions'][0]['category']['text'] == 'MCP'
    api.call('PATCH', '/niagara/scripts/deprecation-replacement', {**V, 'SourceAssetPath': MODULE}, ok=False)
    api.call('PATCH', '/niagara/scripts/deprecation-replacement', {**V, 'SourceAssetPath': FN}, ok=False)
    api.call('PATCH', '/niagara/scripts/deprecation-replacement', {**V, 'SourceAssetPath': COPY})
    assert v()['deprecation_recommendation_path'] == COPY, v()['deprecation_recommendation_path']


def graph_stage(api):
    V = ver(api, FN)
    count = lambda: len(graph(api, V)['nodes'])
    base = count()
    # Operations: discovery, creation (unknown-name guard), pins, comment, position.
    ops = [o['name'] for o in api.call('POST', '/niagara/scripts/graph/operation-types', V)['operations']]
    assert 'Integer::BitAnd' in ops and 'Numeric::Add' in ops
    api.call('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': 'Integer::Nope', 'NodeX': 0, 'NodeY': 0}, ok=False)
    api.call('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': 'Integer::BitAnd', 'NodeX': 0, 'NodeY': 0, 'bDryRun': True})
    assert count() == base
    op = api.call('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': 'Integer::BitAnd', 'NodeX': 0, 'NodeY': 0})
    O = {**V, 'NodeId': op['node_id'], 'NodePath': op['node_path']}
    pin = lambda name: next(p for p in node(api, V, lambda n: n['id'] == op['node_id'])['pins'] if p['name'] == name)
    api.call('PATCH', '/niagara/scripts/graph/pin-scalar', {**O, 'PinId': pin('A')['id'], 'ScalarValue': 1.5}, ok=False)
    api.call('PATCH', '/niagara/scripts/graph/pin-scalar', {**O, 'PinId': pin('A')['id'], 'ScalarValue': 5})
    api.call('PATCH', '/niagara/scripts/graph/pin-scalar', {**O, 'PinId': pin('B')['id'], 'ScalarValue': 12})
    assert pin('A')['default_value'] == '5' and pin('B')['default_value'] == '12'
    api.call('POST', '/niagara/scripts/graph/reset-pin-default', {**O, 'PinId': pin('B')['id']})
    assert pin('B')['default_value'] == '1', pin('B')
    api.undo(); assert pin('B')['default_value'] == '12'
    api.redo(); assert pin('B')['default_value'] == '1'
    api.call('PATCH', '/niagara/scripts/graph/node-comment', {**O, 'TextValue': 'mask'})
    api.call('PATCH', '/niagara/scripts/graph/node-position', {**O, 'NodeX': 2000000, 'NodeY': 0}, ok=False)
    api.call('PATCH', '/niagara/scripts/graph/node-position', {**O, 'NodeX': 64, 'NodeY': 96})
    n = node(api, V, lambda n: n['id'] == op['node_id'])
    assert n['comment'] == 'mask' and (n['x'], n['y']) == (64, 96), n
    # Vector op pins for compound defaults.
    cross = api.call('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': 'Vector3::Cross', 'NodeX': 0, 'NodeY': 200})
    X = {**V, 'NodeId': cross['node_id'], 'NodePath': cross['node_path']}
    cpin = lambda name: next(p for p in node(api, V, lambda n: n['id'] == cross['node_id'])['pins'] if p['name'] == name)
    api.call('PATCH', '/niagara/scripts/graph/pin-compound', {**X, 'PinId': cpin('A')['id'], 'VectorValue': {'X': 1, 'Y': 2, 'Z': 3}})
    assert cpin('A')['default_value'] == '(X=1.000000,Y=2.000000,Z=3.000000)', cpin('A')
    # Inputs: scalar and compound creation, value, priority, exposure, rename.
    api.call('POST', '/niagara/scripts/graph/scalar-inputs', {**V, 'ParameterName': 'Module.Speed', 'ValueKind': 'float', 'ScalarValue': 1, 'NodeX': -400, 'NodeY': 0}, ok=False)
    sp = api.call('POST', '/niagara/scripts/graph/scalar-inputs', {**V, 'ParameterName': 'Speed', 'ValueKind': 'int', 'ScalarValue': 3, 'NodeX': -400, 'NodeY': 0})
    S = {**V, 'NodeId': sp['node_id'], 'NodePath': sp['node_path']}
    api.call('POST', '/niagara/scripts/graph/compound-inputs', {**V, 'ParameterName': 'Dir', 'ValueKind': 'vector', 'VectorValue': {'X': 1, 'Y': 2, 'Z': 3}, 'NodeX': -400, 'NodeY': 200})
    api.call('POST', '/niagara/scripts/graph/compound-inputs', {**V, 'ParameterName': 'Tint', 'ValueKind': 'color', 'ColorValue': {'R': 1, 'G': 0.5, 'B': 0, 'A': 1}, 'NodeX': -400, 'NodeY': 300, 'bExposeInput': False})
    api.call('PATCH', '/niagara/scripts/graph/input-value', {**S, 'ScalarValue': 9})
    api.call('PATCH', '/niagara/scripts/graph/input-priority', {**S, 'ScalarValue': 4})
    api.call('PATCH', '/niagara/scripts/graph/input-exposure', {**S, 'FieldName': 'bRequired', 'bEnabled': False})
    api.call('PATCH', '/niagara/scripts/graph/input-name', {**S, 'NewName': 'Dir'}, ok=False)
    api.call('PATCH', '/niagara/scripts/graph/input-name', {**S, 'NewName': 'Rate'})
    inputs = {n['input_name']: n for n in graph(api, V)['nodes'] if n.get('input_name')}
    r = inputs['Rate']
    assert r['stored_input_value']['value'] == 9 and r['call_sort_priority'] == 4 and not r['input_required'], r
    assert inputs['Dir']['stored_input_value']['value_kind'] in ('vector3', 'vector') and not inputs['Tint']['input_exposed'], inputs['Tint']
    # Wire input -> op and reroute, then disconnect the reroute link.
    rout = next(p for p in r['pins'] if p['direction'] == 1)
    api.call('POST', '/niagara/scripts/graph/connect', {**S, 'PinId': rout['id'], 'TargetNodeId': op['node_id'], 'TargetNodePath': op['node_path'], 'TargetPinId': pin('A')['id']})
    assert pin('A')['link_count'] == 1
    rr = api.call('POST', '/niagara/scripts/graph/reroutes', {**V, 'NodeX': -200, 'NodeY': 0})
    rnode = node(api, V, lambda n: n['id'] == rr['node_id'])
    R = {**V, 'NodeId': rr['node_id'], 'NodePath': rr['node_path']}
    api.call('POST', '/niagara/scripts/graph/connect', {**S, 'PinId': rout['id'], 'TargetNodeId': rr['node_id'], 'TargetNodePath': rr['node_path'], 'TargetPinId': rnode['pins'][0]['id']})
    api.call('POST', '/niagara/scripts/graph/disconnect', {**S, 'PinId': rout['id'], 'TargetNodeId': rr['node_id'], 'TargetNodePath': rr['node_path'], 'TargetPinId': rnode['pins'][0]['id']})
    assert node(api, V, lambda n: n['id'] == rr['node_id'])['pins'][0]['link_count'] == 0
    again = api.call('POST', '/niagara/scripts/graph/disconnect', {**S, 'PinId': rout['id'], 'TargetNodeId': rr['node_id'], 'TargetNodePath': rr['node_path'], 'TargetPinId': rnode['pins'][0]['id']})
    assert again['would_change'] is False, again
    # Comment boxes, duplication, removal.
    cb = api.call('POST', '/niagara/scripts/graph/comment-boxes', {**V, 'TextValue': 'MCP group', 'NodeX': -500, 'NodeY': -100})
    B = {**V, 'NodeId': cb['node_id'], 'NodePath': cb['node_path']}
    api.call('PATCH', '/niagara/scripts/graph/comment-box-size', {**B, 'NodeWidth': 10, 'NodeHeight': 10}, ok=False)
    api.call('PATCH', '/niagara/scripts/graph/comment-box-size', {**B, 'NodeWidth': 640, 'NodeHeight': 320})
    c = node(api, V, lambda n: n['id'] == cb['node_id'])
    assert c['comment'] == 'MCP group' and (c['width'], c['height']) == (640, 320), c
    d = api.call('POST', '/niagara/scripts/graph/duplicate-node', {**R, 'NodeX': -150, 'NodeY': 50})
    assert d['node_id'] != rr['node_id']
    api.call('POST', '/niagara/scripts/graph/duplicate-node', {**S, 'NodeX': 0, 'NodeY': 0}, ok=False)  # inputs are not duplicable
    n_before = count()
    api.call('DELETE', '/niagara/scripts/graph/nodes', {**V, 'NodeId': d['node_id'], 'NodePath': d['node_path'], 'bDryRun': True})
    assert count() == n_before
    api.call('DELETE', '/niagara/scripts/graph/nodes', {**V, 'NodeId': d['node_id'], 'NodePath': d['node_path']})
    assert count() == n_before - 1
    api.undo(); assert count() == n_before
    api.redo(); assert count() == n_before - 1
    # Parameter maps and a function call to another function script.
    api.call('POST', '/niagara/scripts/graph/parameter-maps', {**V, 'ValueKind': 'set', 'NodeX': 300, 'NodeY': 300})
    CV = ver(api, CALLEE)
    api.call('POST', '/niagara/scripts/graph/function-calls', {**V, 'SourceAssetPath': FN, 'SourceVersionId': V['VersionId'], 'NodeX': 0, 'NodeY': 0}, ok=False)
    fc = api.call('POST', '/niagara/scripts/graph/function-calls', {**V, 'SourceAssetPath': CALLEE, 'SourceVersionId': CV['VersionId'], 'NodeX': 300, 'NodeY': 500})
    assert node(api, V, lambda n: n['id'] == fc['node_id'])['class_path'].endswith('NiagaraNodeFunctionCall')
    # Outputs: append, rename, move, remove.
    out = lambda: node(api, V, lambda n: n['class_path'].endswith('NiagaraNodeOutput'))
    U = ident(V, out())
    api.call('POST', '/niagara/scripts/graph/outputs', {**U, 'ParameterName': 'Mask', 'ValueKind': 'int'})
    api.call('POST', '/niagara/scripts/graph/outputs', {**U, 'ParameterName': 'Gone', 'ValueKind': 'float'})
    api.call('POST', '/niagara/scripts/graph/outputs', {**U, 'ParameterName': 'Mask', 'ValueKind': 'float'}, ok=False)
    names = lambda: [o['name'] for o in out()['outputs']]
    i = names().index('Mask')
    api.call('PATCH', '/niagara/scripts/graph/outputs', {**U, 'OutputIndex': i, 'ParameterName': 'Wrong', 'ValueKind': 'rename', 'NewName': 'Bits'}, ok=False)
    api.call('PATCH', '/niagara/scripts/graph/outputs', {**U, 'OutputIndex': i, 'ParameterName': 'Mask', 'ValueKind': 'rename', 'NewName': 'Bits'})
    api.call('PATCH', '/niagara/scripts/graph/outputs', {**U, 'OutputIndex': i, 'ParameterName': 'Bits', 'ValueKind': 'move', 'TargetIndex': 0})
    assert names()[0] == 'Bits', names()
    api.call('PATCH', '/niagara/scripts/graph/outputs', {**U, 'OutputIndex': names().index('Gone'), 'ParameterName': 'Gone', 'ValueKind': 'remove'})
    assert 'Gone' not in names(), names()
    # Structural validation finds no issues.
    v = api.call('POST', '/niagara/scripts/graph/validate', V)
    assert not v['structural_issues_found'] and v['nodes_checked'] == count(), v


def snapshot(api):
    out = {}
    for p in (FN, MODULE, COPY, CALLEE):
        s = script(api, p)
        for k in ('dirty', 'last_compile_status', 'last_compile_status_name', 'compile_error', 'compile_dirty',
                  'compile_has_warnings', 'cpu_compilation_pending', 'gpu_compilation_pending', 'scope'):
            s.pop(k, None)
        out[p] = s
    g = graph(api, ver(api, FN))
    g.pop('scope', None)
    # Calls to unversioned scripts reload with an empty selected version, which means the exposed one.
    for n in g['nodes']:
        if n.get('selected_script_version') == '00000000-0000-0000-0000-000000000000':
            n['selected_script_version'] = script(api, n['function_script_path'])['exposed_version_id']
    out['graph'] = g
    return out


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text('{}', encoding='utf-8')
    creation_stage(api)
    metadata_stage(api)
    graph_stage(api)
    for p in ASSETS:
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared Niagara script authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api)
        for k in state['snapshot']:
            if k == 'graph':
                a = {n['id']: n for n in state['snapshot'][k]['nodes']}
                b = {n['id']: n for n in cold[k]['nodes']}
                assert a.keys() == b.keys(), (sorted(a), sorted(b))
                diff = [(i, json.dumps(a[i])[:500], json.dumps(b[i])[:500]) for i in a if a[i] != b[i]]
                assert not diff, diff[:2]
            assert state['snapshot'][k] == cold[k], (k, json.dumps(state['snapshot'][k])[:600], json.dumps(cold[k])[:600])
        print('Cold reload of Niagara script metadata and script graph: OK')
    finally:
        cleanup(api)


def cleanup(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned Niagara script test assets')


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
