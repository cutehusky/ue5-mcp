"""Live PCG graph authoring (part 1: graph structure) on scratch PCG graphs.

prepare: create a graph and a duplicate (dry runs first), discover node classes, add nodes, edit node presentation
(move/title/comment/comment display), duplicate and remove nodes, connect/disconnect labeled edges, edit node settings
of every kind (bool/float/int scalar, enum, name/string/text, vector/colour compound, soft asset reference, name
array, reset to default), point a subgraph node at the second graph, edit graph settings (scalar, enum, text, reset),
add/rename/configure/retype/move/remove graph IO pins, and run structural/dependency diagnostics. Every edit has a
dry run and a stale-hash refusal; one edit per route also undo/redo. Save and snapshot.
verify (fresh editor): load the graphs, compare graph, node settings and IO pins, then delete.
"""
import argparse
import json
import re
import time
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'pcg_graph.json'
D = '/Game/UE5MCP_Test/'
S = '/Script/PCG.'
MESH = '/Engine/BasicShapes/Cube.Cube'
LIVE = {'bConfirm': True, 'bDryRun': False}
G = G2 = None
VOLATILE = ('scope', 'dirty', 'saved')


def use_tag(tag):
    global G, G2
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    G, G2 = n('PCG_MCP_Graph'), n('PCG_MCP_Sub')


def graph(api, path=None):
    return api.call('POST', '/pcg/graphs/inspect', {'AssetPath': path or G})


def node(api, name, path=None):
    """Node record whose path ends with :name (internal nodes) or whose role is input/output."""
    for n in graph(api, path)['nodes']:
        if n['role'] == name or n['path'].endswith(':' + name):
            return n
    raise AssertionError((name, 'node not found'))


def nref(n):
    return {'AssetPath': G, 'NodeIndex': n['index'], 'NodePath': n['path']}


def settings(api, name):
    return api.call('POST', '/pcg/graphs/nodes/settings/inspect', nref(node(api, name)))


def field(s, path):
    return next(f for f in s['fields'] if f['field_path'] == path)


def pins(api, role):
    n = node(api, role)
    return api.call('POST', '/pcg/graphs/pins/inspect', {**nref(n), 'SettingsPath': n['settings_path']})


def strip(d):
    return {k: v for k, v in d.items() if k not in VOLATILE}


def text_neutral(d):
    """Undo/load re-serialize FText; a culture-invariant string can come back keyed as NSLOCTEXT("", "<key>", "..."),
    which exports differently without changing the text. Compare the text, not its export form."""
    if isinstance(d, dict):
        # record_hash covers the settings' export text, so it moves with the FText export form as well.
        return {k: text_neutral(v) for k, v in d.items() if k != 'record_hash'}
    if isinstance(d, list):
        return [text_neutral(v) for v in d]
    if isinstance(d, str):
        d = KEYED_TEXT.sub(r'\1', d)
        # An authored FText can also export as a quoted literal after re-serialization.
        return d[1:-1] if len(d) >= 2 and d[0] == d[-1] == '"' and '"' not in d[1:-1] else d
    return d


KEYED_TEXT = re.compile(r'NSLOCTEXT\("", "[0-9A-F]{32}", ("(?:[^"\\]|\\.)*")\)')


def full(api):
    return text_neutral(_full(api))


def _full(api):
    g = strip(graph(api))
    # Subgraph references live on an instanced UPCGGraphInstance; the dependency report is where they are visible.
    out = {'graph': g, 'dependencies': strip(api.call('POST', '/pcg/graph-interfaces/dependencies', {'AssetPath': G}))}
    for n in g['nodes']:
        if n['role'] == 'internal':
            out[n['path']] = strip(api.call('POST', '/pcg/graphs/nodes/settings/inspect', nref(n)))
        else:
            out['pins_' + n['role']] = strip(api.call('POST', '/pcg/graphs/pins/inspect', {**nref(n), 'SettingsPath': n['settings_path']}))
    return out


def diff(x, y, p=''):
    if isinstance(x, dict) and isinstance(y, dict):
        return [d for k in set(x) | set(y) for d in diff(x.get(k), y.get(k), p + '.' + k)]
    if isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        return [d for i, (u, v) in enumerate(zip(x, y)) for d in diff(u, v, f'{p}[{i}]')]
    return [] if x == y else [(p, str(x)[:200], str(y)[:200])]


def settled(api):
    """Some edits (e.g. bUnbounded changing pins) finish through native notifications on a later editor tick."""
    prev = full(api)
    for _ in range(20):
        time.sleep(0.25)
        cur = full(api)
        if cur == prev:
            return cur
        prev = cur
    raise AssertionError('PCG graph state did not settle')


def edit(api, method, route, body, check, undo=False, stale=None):
    """Dry run leaves the graph unchanged; optional stale body refused; the real edit satisfies check(before, after)."""
    before = settled(api)
    d = api.call(method, route, {**body, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, body, d)
    assert full(api) == before, (route, body, 'dry run changed the graph')
    if stale:
        api.call(method, route, {**body, **stale, **LIVE}, ok=False)
        assert full(api) == before, (route, 'refused edit changed the graph')
    api.call(method, route, {**body, **LIVE})
    after = settled(api)
    assert check(before, after), (route, body, json.dumps(after)[:1200])
    if undo:
        api.undo()
        u = settled(api)
        assert u == before, (route, body, 'undo did not restore', diff(before, u)[:6])
        api.redo()
        r = settled(api)
        assert r == after, (route, body, 'redo did not reapply', diff(after, r)[:6])
    return after


def create_stage(api):
    for path in (G, G2):
        d = api.call('POST', '/pcg/graphs', {'AssetPath': path, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'] and not d['created'], d
        api.call('POST', '/pcg/graphs/inspect', {'AssetPath': path}, ok=False)
        api.call('POST', '/pcg/graphs', {'AssetPath': path, **LIVE})
        api.call('POST', '/pcg/graphs', {'AssetPath': path, **LIVE}, ok=False)
    classes = [c['path'] for c in api.call('POST', '/pcg/node-classes', {})['classes']]
    assert S + 'PCGSurfaceSamplerSettings' in classes and len(classes) > 100, len(classes)
    data = api.call('POST', '/pcg/data-classes', {})['classes']
    assert any(c['name'] == 'PCGPointData' and c['type_identifier_valid'] for c in data), [c['name'] for c in data][:20]


def node_stage(api):
    add = lambda cls, x: api.call('POST', '/pcg/graphs/nodes', {'AssetPath': G, 'SettingsClass': S + cls, 'NodeX': x, 'NodeY': 0, **LIVE})['node_path'].rsplit(':', 1)[1]
    d = api.call('POST', '/pcg/graphs/nodes', {'AssetPath': G, 'SettingsClass': S + 'PCGSurfaceSamplerSettings', 'NodeX': 0, 'NodeY': 0, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and graph(api)['internal_node_count'] == 0, d
    api.call('POST', '/pcg/graphs/nodes', {'AssetPath': G, 'SettingsClass': S + 'PCGSettings', 'NodeX': 0, 'NodeY': 0, **LIVE}, ok=False)
    names = {'sampler': add('PCGSurfaceSamplerSettings', 200), 'transform': add('PCGTransformPointsSettings', 500), 'filter': add('PCGFilterByTagSettings', 800),
             'spawn': add('PCGSpawnActorSettings', 1100), 'sub': add('PCGSubgraphSettings', 1400), 'spare': add('PCGAddTagSettings', 1700)}
    assert graph(api)['internal_node_count'] == 6
    pres = '/pcg/graphs/nodes/presentation'
    ref = lambda key: nref(node(api, names[key]))
    edit(api, 'PATCH', pres, {**ref('sampler'), 'Action': 'move', 'NodeX': 250, 'NodeY': 40}, lambda b, a: (node(api, names['sampler'])['x'], node(api, names['sampler'])['y']) == (250, 40),
         undo=True, stale={'NodePath': node(api, names['transform'])['path']})
    edit(api, 'PATCH', pres, {**ref('sampler'), 'Action': 'title', 'Title': 'MCP Sampler'}, lambda b, a: node(api, names['sampler'])['authored_title'] == 'MCP Sampler', undo=True)
    edit(api, 'PATCH', pres, {**ref('sampler'), 'Action': 'comment', 'TextValue': 'Samples the surface'}, lambda b, a: node(api, names['sampler'])['comment'] == 'Samples the surface')
    edit(api, 'PATCH', pres, {**ref('sampler'), 'Action': 'comment_display', 'bCommentVisible': True, 'bCommentPinned': True},
         lambda b, a: node(api, names['sampler'])['comment_bubble_visible'] and node(api, names['sampler'])['comment_bubble_pinned'])
    api.call('PATCH', pres, {**ref('sampler'), 'Action': 'move', 'NodeX': 2e6, 'NodeY': 0, **LIVE}, ok=False)
    # Duplicate keeps settings and editor metadata (comment) on a new node; remove deletes the spare.
    before = graph(api)['internal_node_count']
    d = api.call('POST', '/pcg/graphs/nodes/duplicate', {**ref('sampler'), 'NodeX': 250, 'NodeY': 300, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and graph(api)['internal_node_count'] == before, d
    dup = api.call('POST', '/pcg/graphs/nodes/duplicate', {**ref('sampler'), 'NodeX': 250, 'NodeY': 300, **LIVE})
    names['dup'] = dup.get('node_path', dup.get('new_node_path', '')).rsplit(':', 1)[1]
    dn = node(api, names['dup'])
    assert dn['comment'] == 'Samples the surface' and dn['comment_bubble_visible'] and (dn['x'], dn['y']) == (250, 300), dn
    assert dn['settings_class'] == S + 'PCGSurfaceSamplerSettings' and dn['path'] != node(api, names['sampler'])['path']
    d = api.call('POST', '/pcg/graphs/nodes/remove', {**ref('spare'), 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and graph(api)['internal_node_count'] == before + 1, d
    api.call('POST', '/pcg/graphs/nodes/remove', {**ref('spare'), **LIVE})
    api.undo()
    assert graph(api)['internal_node_count'] == before + 1, 'node removal undo'
    api.redo()
    assert graph(api)['internal_node_count'] == before and not any(n['path'].endswith(':' + names['spare']) for n in graph(api)['nodes'])
    return names


def edge_stage(api, names):
    edges = lambda: sum(len(p.get('edges', p.get('connected', []))) if isinstance(p.get('edges', p.get('connected', [])), list) else 0
                        for n in graph(api)['nodes'] for p in n.get('output_pins', []))
    src, dst = node(api, names['sampler']), node(api, names['transform'])
    out_pin = src['output_pins'][0]['label']
    in_pin = dst['input_pins'][0]['label']
    body = {'AssetPath': G, 'Action': 'connect', 'NodeIndex': src['index'], 'NodePath': src['path'], 'FromPin': out_pin,
            'TargetNodeIndex': dst['index'], 'TargetNodePath': dst['path'], 'ToPin': in_pin}
    validate = lambda: api.call('POST', '/pcg/graphs/validate', {'AssetPath': G})['edge_count']
    edit(api, 'PATCH', '/pcg/graphs/edges', body, lambda b, a: validate() == 1, undo=True, stale={'ToPin': 'NoSuchPin'})
    io = node(api, 'input')
    edit(api, 'PATCH', '/pcg/graphs/edges', {**body, 'NodeIndex': io['index'], 'NodePath': io['path'], 'FromPin': io['output_pins'][0]['label'],
                                              'TargetNodeIndex': src['index'], 'TargetNodePath': src['path'], 'ToPin': src['input_pins'][0]['label']},
         lambda b, a: validate() == 2)
    edit(api, 'PATCH', '/pcg/graphs/edges', {**body, 'Action': 'disconnect'}, lambda b, a: validate() == 1)
    edit(api, 'PATCH', '/pcg/graphs/edges', body, lambda b, a: validate() == 2)
    api.call('PATCH', '/pcg/graphs/edges', {**body, 'TargetNodeIndex': src['index'], 'TargetNodePath': src['path'], 'ToPin': src['input_pins'][0]['label'], **LIVE}, ok=False)
    v = api.call('POST', '/pcg/graphs/validate', {'AssetPath': G})
    assert v['structurally_valid'] and v['cycle_dependency_residual_count'] == 0, v


def settings_edit(api, name, route, extra, check, undo=False, method='PATCH'):
    s = settings(api, name)
    n = node(api, name)
    body = {**nref(n), 'SettingsPath': s['settings_path'], 'RecordHash': s['record_hash'], **extra}
    edit(api, method, route, body, lambda b, a: check(settings(api, name)), undo=undo, stale={'RecordHash': '0' * 32})


def node_settings_stage(api, names):
    base = '/pcg/graphs/nodes/settings/'
    smp = names['sampler']
    settings_edit(api, smp, base + 'scalar', {'FieldName': 'PointsPerSquaredMeter', 'ScalarValue': 0.5}, lambda s: field(s, 'PointsPerSquaredMeter')['value'] == '0.500000', undo=True)
    settings_edit(api, smp, base + 'scalar', {'FieldName': 'bUnbounded', 'ScalarValue': 1}, lambda s: field(s, 'bUnbounded')['value'] == 'True')
    settings_edit(api, smp, base + 'scalar', {'FieldName': 'Seed', 'ScalarValue': 1234}, lambda s: field(s, 'Seed')['value'] == '1234')
    settings_edit(api, smp, base + 'scalar', {'FieldName': 'PointExtents.Z', 'ScalarValue': 25}, lambda s: field(s, 'PointExtents.Z')['value'] == '25.000000')
    s = settings(api, smp)
    api.call('PATCH', base + 'scalar', {**nref(node(api, smp)), 'SettingsPath': s['settings_path'], 'RecordHash': s['record_hash'], 'FieldName': 'PointSteepness', 'ScalarValue': 5, **LIVE}, ok=False)
    settings_edit(api, smp, base + 'compound', {'FieldName': 'PointExtents', 'ValueKind': 'vector', 'VectorValue': {'X': 10, 'Y': 20, 'Z': 30}},
                  lambda s: field(s, 'PointExtents')['value'] == '(X=10.000000,Y=20.000000,Z=30.000000)', undo=True)
    color = next((f['field_path'] for f in settings(api, smp)['fields'] if f['type'] == 'FLinearColor' and f['writable']), None)
    if color:
        settings_edit(api, smp, base + 'compound', {'FieldName': color, 'ValueKind': 'color', 'ColorValue': {'R': 0.25, 'G': 0.5, 'B': 0.75, 'A': 1}},
                      lambda s: field(s, color)['value'] == '(R=0.250000,G=0.500000,B=0.750000,A=1.000000)')
    settings_edit(api, smp, base + 'asset', {'FieldName': 'DebugSettings.PointMesh', 'SourceAssetPath': MESH}, lambda s: MESH in field(s, 'DebugSettings.PointMesh')['value'], undo=True)
    settings_edit(api, smp, base + 'reset-field', {'FieldName': 'PointsPerSquaredMeter'}, lambda s: field(s, 'PointsPerSquaredMeter')['value'] == '0.100000', undo=True)
    flt = names['filter']
    op = field(settings(api, flt), 'Operation')
    choices = op.get('enum_choices') or [c['name'] for c in op.get('enum_values', [])]
    new = next(c if isinstance(c, str) else c['name'] for c in choices if (c if isinstance(c, str) else c['name']) != op['value'])
    settings_edit(api, flt, base + 'enum', {'FieldName': 'Operation', 'EnumValue': new}, lambda s: field(s, 'Operation')['value'].endswith(new), undo=True)
    settings_edit(api, flt, base + 'text', {'FieldName': 'SelectedTags', 'TextValue': 'MCP_A,MCP_B'}, lambda s: field(s, 'SelectedTags')['value'] == 'MCP_A,MCP_B', undo=True)
    spn = names['spawn']
    settings_edit(api, spn, base + 'text', {'FieldName': 'SpawnAttribute', 'TextValue': 'MCPActor'}, lambda s: field(s, 'SpawnAttribute')['value'] == 'MCPActor')
    settings_edit(api, spn, base + 'text', {'FieldName': 'Category', 'TextValue': 'MCP Category'}, lambda s: 'MCP Category' in field(s, 'Category')['value'])
    settings_edit(api, spn, base + 'string-array', {'FieldName': 'PostSpawnFunctionNames', 'StringValues': ['FnA', 'FnB']},
                  lambda s: 'FnA' in field(s, 'PostSpawnFunctionNames')['value'] and 'FnB' in field(s, 'PostSpawnFunctionNames')['value'], undo=True)
    s = settings(api, spn)
    api.call('PATCH', base + 'enum', {**nref(node(api, spn)), 'SettingsPath': s['settings_path'], 'RecordHash': s['record_hash'], 'FieldName': 'Option', 'EnumValue': 'NoSuchValue', **LIVE}, ok=False)
    # Subgraph reference to the second graph.
    sub = names['sub']
    s = settings(api, sub)
    body = {**nref(node(api, sub)), 'SettingsPath': s['settings_path'], 'RecordHash': s['record_hash'], 'SourceAssetPath': G2}
    parent = lambda a: [r['to'] for r in a['dependencies']['references'] if r['kind'] == 'parent']
    edit(api, 'PATCH', '/pcg/graphs/nodes/subgraph', body, lambda b, a: parent(a) == [G2] and G2 not in parent(b), undo=True, stale={'RecordHash': '0' * 32})
    s = settings(api, sub)
    api.call('PATCH', '/pcg/graphs/nodes/subgraph', {**nref(node(api, sub)), 'SettingsPath': s['settings_path'], 'RecordHash': s['record_hash'], 'SourceAssetPath': G, **LIVE}, ok=False)
    deps = api.call('POST', '/pcg/graph-interfaces/dependencies', {'AssetPath': G})
    assert G2 in json.dumps(deps), json.dumps(deps)[:800]


def scalar_setting(g, name):
    return next(f for f in g['scalar_settings'] if f['name'] == name)


def graph_settings_stage(api):
    gs = '/pcg/graphs/settings/'
    hashed = lambda extra: {'AssetPath': G, 'RecordHash': graph(api)['record_hash'], **extra}
    stale = {'RecordHash': '0' * 32}
    edit(api, 'PATCH', gs + 'scalar', hashed({'FieldName': 'bUseHierarchicalGeneration', 'ScalarValue': 1}),
         lambda b, a: scalar_setting(graph(api), 'bUseHierarchicalGeneration')['value'] == 'True', undo=True, stale=stale)
    edit(api, 'PATCH', gs + 'scalar', hashed({'FieldName': 'HiGenExponential', 'ScalarValue': 3}), lambda b, a: scalar_setting(graph(api), 'HiGenExponential')['value'] == '3', stale=stale)
    api.call('PATCH', gs + 'scalar', {**hashed({'FieldName': 'HiGenExponential', 'ScalarValue': 20}), **LIVE}, ok=False)
    edit(api, 'PATCH', gs + 'enum', hashed({'FieldName': 'HiGenGridSize', 'EnumValue': 'Grid512'}), lambda b, a: scalar_setting(graph(api), 'HiGenGridSize')['value'] == 'Grid512',
         undo=True, stale=stale)
    edit(api, 'PATCH', gs + 'text', hashed({'FieldName': 'Description', 'TextValue': 'MCP test graph'}),
         lambda b, a: next(f for f in graph(api)['text_settings'] if f['name'] == 'Description')['value'] == 'MCP test graph', undo=True, stale=stale)
    edit(api, 'PATCH', gs + 'reset-field', hashed({'FieldName': 'HiGenExponential'}), lambda b, a: scalar_setting(graph(api), 'HiGenExponential')['value'] == '0', undo=True, stale=stale)


def pin_stage(api):
    # Pins store data types as type identifiers; data-class discovery gives the identifier for each class.
    point_type = next(c['type_identifier'] for c in api.call('POST', '/pcg/data-classes', {})['classes'] if c['name'] == 'PCGPointData')
    for role in ('input', 'output'):
        p = pins(api, role)
        n = node(api, role)
        key = lambda extra: {**nref(n), 'SettingsPath': n['settings_path'], 'RecordHash': pins(api, role)['record_hash'], **extra}
        labels = lambda: [x['label'] for x in pins(api, role)['pins']]
        stale = {'RecordHash': '0' * 32}
        start = labels()
        edit(api, 'POST', '/pcg/graphs/pins', key({'FromPin': f'MCP_{role}_A'}), lambda b, a: labels() == start + [f'MCP_{role}_A'], undo=True, stale=stale)
        edit(api, 'POST', '/pcg/graphs/pins', key({'FromPin': f'MCP_{role}_B'}), lambda b, a: labels() == start + [f'MCP_{role}_A', f'MCP_{role}_B'], stale=stale)
        idx = lambda label: labels().index(label)
        # A colliding label is not refused: native collision handling picks a unique one.
        d = api.call('POST', '/pcg/graphs/pins', {**key({'FromPin': f'MCP_{role}_A'}), **LIVE})
        assert d['actual_label'] != f'MCP_{role}_A' and d['actual_label'] in labels(), d
        api.call('PATCH', '/pcg/graphs/pins', {**key({'Action': 'remove', 'PinIndex': idx(d['actual_label']), 'FromPin': d['actual_label']}), **LIVE})
        assert labels() == start + [f'MCP_{role}_A', f'MCP_{role}_B'], labels()
        edit(api, 'PATCH', '/pcg/graphs/pins', key({'Action': 'rename', 'PinIndex': idx(f'MCP_{role}_A'), 'FromPin': f'MCP_{role}_A', 'TextValue': f'MCP_{role}_R'}),
             lambda b, a: f'MCP_{role}_R' in labels() and f'MCP_{role}_A' not in labels(), undo=True, stale=stale)
        edit(api, 'PATCH', '/pcg/graphs/pins', key({'Action': 'configure', 'PinIndex': idx(f'MCP_{role}_R'), 'FromPin': f'MCP_{role}_R', 'bAllowMultipleConnections': False,
                                                    'bAllowMultipleData': False, 'PinStatus': 'Advanced', 'TextValue': 'MCP tooltip'}),
             lambda b, a: 'MCP tooltip' in json.dumps(pins(api, role)), undo=True, stale=stale)
        edit(api, 'PATCH', '/pcg/graphs/pins', key({'Action': 'data_types', 'PinIndex': idx(f'MCP_{role}_R'), 'FromPin': f'MCP_{role}_R', 'StringValues': ['/Script/PCG.PCGPointData']}),
             lambda b, a: point_type in pins(api, role)['pins'][idx(f'MCP_{role}_R')]['value'], undo=True, stale=stale)
        edit(api, 'PATCH', '/pcg/graphs/pins', key({'Action': 'move', 'PinIndex': idx(f'MCP_{role}_B'), 'FromPin': f'MCP_{role}_B', 'TargetPinIndex': idx(f'MCP_{role}_R')}),
             lambda b, a: idx(f'MCP_{role}_B') < idx(f'MCP_{role}_R'), undo=True, stale=stale)
        edit(api, 'PATCH', '/pcg/graphs/pins', key({'Action': 'remove', 'PinIndex': idx(f'MCP_{role}_B'), 'FromPin': f'MCP_{role}_B'}),
             lambda b, a: f'MCP_{role}_B' not in labels(), undo=True, stale=stale)


def duplicate_stage(api, names):
    # A duplicate of the authored graph must carry all its nodes and settings (compared without asset paths).
    tag = G.rsplit('_', 1)[1].split('.')[0]
    dup = f'{D}PCG_MCP_Dup_{tag}.PCG_MCP_Dup_{tag}'
    d = api.call('POST', '/pcg/graphs/duplicate', {'SourceAssetPath': G, 'AssetPath': dup, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'], d
    api.call('POST', '/pcg/graphs/inspect', {'AssetPath': dup}, ok=False)
    api.call('POST', '/pcg/graphs/duplicate', {'SourceAssetPath': G, 'AssetPath': dup, **LIVE})
    a, b = graph(api), graph(api, dup)
    norm = lambda g, p: json.loads(json.dumps(strip(g)).replace(p.split('.')[0], 'GRAPH').replace(p.rsplit('.', 1)[1], 'GRAPH'))
    assert norm(a, G)['nodes'] == norm(b, dup)['nodes'], 'duplicate differs'
    api.call('POST', '/pcg/graphs/duplicate', {'SourceAssetPath': G, 'AssetPath': dup, **LIVE}, ok=False)
    return dup


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'tag': tag}), encoding='utf-8')
    create_stage(api)
    names = node_stage(api)
    edge_stage(api, names)
    node_settings_stage(api, names)
    graph_settings_stage(api)
    pin_stage(api)
    dup = duplicate_stage(api, names)
    for p in (G, G2, dup):
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'tag': tag, 'dup': dup, 'snapshot': settled(api)}), encoding='utf-8')
    print('prepared PCG graph authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in (G, G2, state['dup']):
            api.call('GET', '/assets/describe', params={'asset_path': p})
        cold = settled(api)
        bad = [k for k in state['snapshot'] if state['snapshot'][k] != cold.get(k)]
        assert not bad, [(k, json.dumps(state['snapshot'][k])[:600], json.dumps(cold.get(k))[:600]) for k in bad[:2]]
        print('Cold reload of PCG graph nodes, edges, node/graph settings, subgraph reference and IO pins: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    for p in (state.get('dup'), G, G2):
        if p:
            httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned PCG graph test assets')


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
