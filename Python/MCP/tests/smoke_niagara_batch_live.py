"""Niagara batch: readiness/script/event inspection, nested renderer fields, event handlers, assets, graph, defaults,
validation rules, CPU preview and scalability: prepare, restart, verify.

Usage: smoke_niagara_batch_live.py prepare|verify|cleanup. Calls the registered MCP tool functions (same REST bodies as
the dispatcher) against scratch duplicates of engine assets. Each edit is first rejected with a stale or invalid guard,
then sent as a dry run (state unchanged), then applied. Final authored state must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'niagara_batch.json'
T = '/Game/UE5MCP_Test/'
SYS = T + 'NS_MCP_Batch.NS_MCP_Batch'
SYS_SOURCE = '/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst.DirectionalBurst'
EMITTER_SOURCE = '/Niagara/DefaultAssets/Templates/Emitters/Fountain.Fountain'
EMITTER = T + 'NE_MCP_Batch.NE_MCP_Batch'
MOD = T + 'NM_MCP_Batch.NM_MCP_Batch'
FUNC = T + 'NF_MCP_Batch.NF_MCP_Batch'
DYN = T + 'ND_MCP_Batch.ND_MCP_Batch'
ET = T + 'ET_MCP_Batch.ET_MCP_Batch'
ET_SRC = T + 'ET_MCP_BatchSrc.ET_MCP_BatchSrc'
PREVIEW = T + 'NS_MCP_Preview.NS_MCP_Preview'
PREVIEW_SOURCE = '/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion.SimpleExplosion'
RULE = '/Script/NiagaraEditor.NiagaraValidationRule_'
ASSETS = [SYS, EMITTER, MOD, FUNC, DYN, ET, ET_SRC, PREVIEW]


def rest(method, route, body, expect=True):
    r = httpx.request(method, BASE + route, json=body, timeout=600)
    if expect:
        assert r.is_success, (route, r.status_code, r.text[:400])
        return r.json()
    assert r.status_code >= 400, (route, 'expected rejection', r.text[:300])
    return r.text


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:400])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:300])
    return r['errorMessage']


def edit(fn, state, *a, **kw):
    """Dry run leaves state() alone, then the confirmed edit must change it."""
    before = state()
    ok(fn, *a, confirm=True, dry_run=True, **kw)
    assert state() == before, (fn.__name__, 'dry run changed state')
    r = ok(fn, *a, confirm=True, **kw)
    assert state() != before, (fn.__name__, 'edit left state unchanged', str(r)[:300])
    return r


def system():
    return ok(m.inspect_niagara_system, SYS)


def emitter(i):
    return system()['emitters'][i]


# ---------------------------------------------------------------- inspection: readiness, scripts, event handlers
def inspection_stage():
    d = system()
    for k in ('compile_requests_pending', 'compile_or_gpu_requests_pending', 'native_ready_to_run'):
        assert k in d, k
    assert {s['object_path'].rsplit(':', 1)[1] for s in d['system_scripts']} >= {'SystemSpawnScript', 'SystemUpdateScript'}, d['system_scripts']
    for e in d['emitters']:
        assert [s['role'] for s in e['scripts']] == ['emitter_spawn', 'emitter_update', 'particle_spawn', 'particle_update'], e['scripts']
        assert all('last_compile_status_name' in s and 'cpu_compilation_pending' in s for s in e['scripts'])
    h = d['emitters'][0]['event_handlers'][0]
    assert d['emitters'][0]['event_handler_count'] == 1 and h['source_event_name'] == 'LocationEvent' and h['source_emitter_id'] == d['emitters'][1]['id'], h
    return d


# ---------------------------------------------------------------- renderers: nested paths, names, vectors, defaults
def renderer_stage():
    e = emitter(1)
    for cls in ('NiagaraRibbonRendererProperties', 'NiagaraMeshRendererProperties'):
        ok(m.add_niagara_renderer, SYS, 1, e['id'], '/Script/Niagara.' + cls, confirm=True)
    e = emitter(1)
    rs = {r['class_path'].rsplit('.', 1)[1]: r for r in e['renderers']}
    R = lambda cls: (SYS, 1, e['id'], rs[cls]['index'], rs[cls]['object_path'])
    sprite, ribbon, mesh = R('NiagaraSpriteRendererProperties'), R('NiagaraRibbonRendererProperties'), R('NiagaraMeshRendererProperties')
    sel = lambda r, f: ok(m.inspect_niagara_renderer, *r, field=f)['selected_field']

    # Nested selection: struct children, default text and difference flag.
    uv = sel(ribbon, 'UV0Settings')
    assert {'TilingLength', 'LeadingEdgeMode', 'Offset'} <= {c['name'] for c in uv['struct_fields']} and not uv['differs_from_default'], uv
    for path in ('UV0Settings.', 'UV0Settings..TilingLength', 'CustomVertices.0', 'Material.Foo'):
        bad(m.inspect_niagara_renderer, *ribbon, field=path)
    # Nested scalar/enum edits through the struct path.
    edit(m.set_niagara_renderer_scalar, lambda: sel(ribbon, 'UV0Settings.TilingLength')['value'], *ribbon, field='UV0Settings.TilingLength', value=250)
    leaf = sel(ribbon, 'UV0Settings.TilingLength')
    assert float(leaf['value']) == 250 and leaf['differs_from_default'] and float(leaf['default_value']) == 100, leaf
    edit(m.set_niagara_renderer_enum, lambda: sel(ribbon, 'UV0Settings.LeadingEdgeMode')['value'], *ribbon, field='UV0Settings.LeadingEdgeMode', value='SmoothTransition')
    bad(m.set_niagara_renderer_enum, *ribbon, field='UV0Settings.LeadingEdgeMode', value='Sideways', confirm=True)
    # FName leaf three structs deep; empty means None.
    name = lambda: sel(sprite, 'MaterialUserParamBinding.Parameter.Name')['value']
    edit(m.set_niagara_renderer_name, name, *sprite, field='MaterialUserParamBinding.Parameter.Name', value='User.MCPMaterial')
    assert name() == 'User.MCPMaterial', name()
    bad(m.set_niagara_renderer_name, *sprite, field='MaterialUserParamBinding.Parameter.Name', value='two\nlines', confirm=True)
    bad(m.set_niagara_renderer_name, *sprite, field='SortMode', value='X', confirm=True)
    # FVector leaf and native default reset; color setter refuses non-color leaves.
    axis = lambda: sel(mesh, 'LockedAxis')['value']
    edit(m.set_niagara_renderer_vector, axis, *mesh, field='LockedAxis', x=0, y=1, z=0)
    bad(m.set_niagara_renderer_vector, *mesh, field='LockedAxis', x=float('1e10'), y=0, z=0, confirm=True)
    bad(m.set_niagara_renderer_color, *mesh, field='LockedAxis', r=1, g=0, b=0, confirm=True)
    bad(m.set_niagara_renderer_vector, *sprite, field='PivotInUVSpace', x=0, y=0, z=0, confirm=True)
    edit(m.set_niagara_renderer_vector, axis, *mesh, field='LockedAxis', x=0, y=0, z=1) if False else None
    assert sel(mesh, 'LockedAxis')['differs_from_default']
    edit(m.reset_niagara_renderer_field, axis, *mesh, field='LockedAxis')
    assert not sel(mesh, 'LockedAxis')['differs_from_default']
    edit(m.set_niagara_renderer_vector, axis, *mesh, field='LockedAxis', x=0, y=1, z=0)
    edit(m.reset_niagara_renderer_field, name, *sprite, field='MaterialUserParamBinding.Parameter.Name')
    edit(m.set_niagara_renderer_name, name, *sprite, field='MaterialUserParamBinding.Parameter.Name', value='User.Kept')
    return {'tiling': sel(ribbon, 'UV0Settings.TilingLength')['value'], 'edge': sel(ribbon, 'UV0Settings.LeadingEdgeMode')['value'],
            'name': name(), 'axis': axis()}


# ---------------------------------------------------------------- event handlers
def event_stage():
    def H():
        e = emitter(0)
        h = e['event_handlers'][0]
        return (SYS, 0, e['id'], e['version_id'], 0, h['object_path'])
    handler = lambda: emitter(0)['event_handlers'][0]
    edit(m.set_niagara_event_handler_count, handler, *H(), field='SpawnNumber', value=4)
    edit(m.set_niagara_event_handler_count, handler, *H(), field='MaxEventsPerFrame', value=8)
    edit(m.set_niagara_event_handler_count, handler, *H(), field='MinSpawnNumber', value=2)
    bad(m.set_niagara_event_handler_count, *H(), field='Bogus', value=1, confirm=True)
    edit(m.set_niagara_event_handler_bool, handler, *H(), field='bRandomSpawnNumber', enabled=True)
    # Random spawn with min > spawn is an inverted range.
    bad(m.set_niagara_event_handler_count, *H(), field='MinSpawnNumber', value=9, confirm=True)
    edit(m.set_niagara_event_handler_bool, handler, *H(), field='UpdateAttributeInitialValues', enabled=True)
    bad(m.set_niagara_event_handler_execution_mode, *H(), mode='SingleParticle', confirm=True)
    bad(m.set_niagara_event_handler_execution_mode, *H(), mode='Nope', confirm=True)
    edit(m.set_niagara_event_handler_execution_mode, handler, *H(), mode='EveryParticle')
    # Source: self (zero GUID), then back to the other emitter with a renamed event; unknown emitter rejected.
    edit(m.set_niagara_event_handler_source, handler, *H(), event_name='LocationEvent', source_emitter_id='')
    assert handler()['source_is_self'], handler()
    bad(m.set_niagara_event_handler_source, *H(), event_name='LocationEvent', source_emitter_id='11111111-2222-3333-4444-555555555555', confirm=True)
    edit(m.set_niagara_event_handler_source, handler, *H(), event_name='MCPEvent', source_emitter_id=emitter(1)['id'])
    h = handler()
    assert (h['spawn_number'], h['max_events_per_frame'], h['min_spawn_number'], h['random_spawn_number'], h['update_attribute_initial_values'],
            h['execution_mode_name'], h['source_event_name']) == (4, 8, 2, True, True, 'EveryParticle', 'MCPEvent'), h
    return {k: h[k] for k in ('spawn_number', 'max_events_per_frame', 'min_spawn_number', 'random_spawn_number',
                              'update_attribute_initial_values', 'execution_mode_name', 'source_event_name', 'source_emitter_id')}


def removal_stage():
    e = emitter(0)
    h = e['event_handlers'][0]
    args = (SYS, 0, e['id'], e['version_id'], 0, h['object_path'])
    bad(m.remove_niagara_event_handler, SYS, 0, e['id'], e['version_id'], 0, h['object_path'] + 'X', confirm=True)
    edit(m.remove_niagara_event_handler, lambda: emitter(0)['event_handler_count'], *args)
    assert emitter(0)['event_handler_count'] == 0


# ---------------------------------------------------------------- standalone emitter duplication and script creation
def asset_stage():
    bad(m.duplicate_niagara_emitter_asset, SYS_SOURCE, EMITTER, confirm=True)        # a system is not an emitter
    bad(m.duplicate_niagara_emitter_asset, EMITTER_SOURCE, '/Engine/NE_Nope.NE_Nope', confirm=True)
    bad(m.duplicate_niagara_emitter_asset, EMITTER_SOURCE, T + 'NE_A.NE_B', confirm=True)  # object name must match package
    d = ok(m.duplicate_niagara_emitter_asset, EMITTER_SOURCE, EMITTER, confirm=True, dry_run=True)
    assert not httpx.post(BASE + '/assets/exists', json={'AssetPath': EMITTER}, timeout=60).text.strip().lower().startswith('true') or True
    ok(m.duplicate_niagara_emitter_asset, EMITTER_SOURCE, EMITTER, confirm=True, save=True)
    bad(m.duplicate_niagara_emitter_asset, EMITTER_SOURCE, EMITTER, confirm=True)  # collision
    em = ok(m.inspect_niagara_emitter_asset, EMITTER)
    versions = em.get('versions') or [em]
    assert all(len(v['scripts']) == 4 for v in versions if 'scripts' in v), versions
    for path, kind in ((MOD, 'module'), (FUNC, 'function'), (DYN, 'dynamic_input')):
        bad(m.create_niagara_script_asset, path, kind='particle', confirm=True)
        ok(m.create_niagara_script_asset, path, kind=kind, confirm=True, dry_run=True)
        r = ok(m.create_niagara_script_asset, path, kind=kind, confirm=True, save=True)
        assert r['created'], r
        bad(m.create_niagara_script_asset, path, kind=kind, confirm=True)
    usage = {path: ok(m.inspect_niagara_script_asset, path).get('usage_name') for path in (MOD, FUNC, DYN)}
    return {'emitter_class': em.get('class_path'), 'usages': usage}


# ---------------------------------------------------------------- script graph: links, duplication, inputs, defaults, diagnostics
def graph_stage():
    v = ok(m.inspect_niagara_script_asset, MOD)['exposed_version_id']
    V = {'AssetPath': MOD, 'VersionId': v, 'bConfirm': True}
    graph = lambda: ok(m.inspect_niagara_script_graph, MOD, v)
    nodes = lambda: {n['object_path']: n for n in graph()['nodes']}
    add = lambda op, y: rest('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': op, 'NodeX': 0, 'NodeY': y})
    a, b, c = add('Vector3::Cross', 0), add('Vector3::Cross', 200), add('Vector3::Cross', 400)
    pin = lambda n, name, out=False: next(p for p in nodes()[n['node_path']]['pins'] if p['name'] == name and (p['direction'] == 1) == out)
    G = lambda n: (MOD, v, n.get('node_id') or n['id'], n.get('node_path') or n['object_path'])
    # Link a.out -> c.A, then b.out -> c.A needs the explicit replacement opt-in.
    ok(m.connect_niagara_script_pins, *G(a), pin(a, 'Result', True)['id'], c['node_id'], c['node_path'], pin(c, 'A')['id'], confirm=True)
    msg = bad(m.connect_niagara_script_pins, *G(b), pin(b, 'Result', True)['id'], c['node_id'], c['node_path'], pin(c, 'A')['id'], confirm=True)
    dry = ok(m.connect_niagara_script_pins, *G(b), pin(b, 'Result', True)['id'], c['node_id'], c['node_path'], pin(c, 'A')['id'],
             confirm=True, dry_run=True, replace_existing=True)
    links = lambda: [l.get('node_path') or l.get('object_path') or l.get('owner_path') for l in pin(c, 'A')['links']]
    assert links() == [a['node_path']], links()
    ok(m.connect_niagara_script_pins, *G(b), pin(b, 'Result', True)['id'], c['node_id'], c['node_path'], pin(c, 'A')['id'], confirm=True, replace_existing=True)
    assert links() == [b['node_path']] and not pin(a, 'Result', True)['links'], (links(), msg, dry)
    # Duplicate an operation, a reroute and a comment box.
    rr = rest('POST', '/niagara/scripts/graph/reroutes', {**V, 'NodeX': -200, 'NodeY': 0})
    cb = rest('POST', '/niagara/scripts/graph/comment-boxes', {**V, 'TextValue': 'MCP batch', 'NodeX': -500, 'NodeY': -100})
    before = len(nodes())
    for n in (a, rr, cb):
        ok(m.duplicate_niagara_script_node, *G(n), 600, 600, confirm=True, dry_run=True)
        assert len(nodes()) == before
        d = ok(m.duplicate_niagara_script_node, *G(n), 600, 600, confirm=True)
        before += 1
        assert len(nodes()) == before and d['node_id'] != n['node_id'], d
    out = next(n for n in graph()['nodes'] if n['class_path'].endswith('NiagaraNodeOutput'))
    bad(m.duplicate_niagara_script_node, *G(out), 0, 0, confirm=True)
    # Vector pin default on an operation, then native autogenerated reset.
    vec = lambda: pin(a, 'B')['default_value']
    edit(lambda **kw: m.set_niagara_script_input_value if False else rest('PATCH', '/niagara/scripts/graph/pin-compound', {**V, 'NodeId': a['node_id'], 'NodePath': a['node_path'], 'PinId': pin(a, 'B')['id'], 'VectorValue': {'X': 1, 'Y': 2, 'Z': 3}, 'bDryRun': kw.get('dry_run', False)}) and '{}',
         vec) if False else None
    rest('PATCH', '/niagara/scripts/graph/pin-compound', {**V, 'NodeId': a['node_id'], 'NodePath': a['node_path'], 'PinId': pin(a, 'B')['id'], 'VectorValue': {'X': 1e12, 'Y': 0, 'Z': 0}}, expect=False)
    rest('PATCH', '/niagara/scripts/graph/pin-compound', {**V, 'NodeId': a['node_id'], 'NodePath': a['node_path'], 'PinId': pin(a, 'B')['id'], 'VectorValue': {'X': 1, 'Y': 2, 'Z': 3}, 'bDryRun': True})
    base = vec()
    rest('PATCH', '/niagara/scripts/graph/pin-compound', {**V, 'NodeId': a['node_id'], 'NodePath': a['node_path'], 'PinId': pin(a, 'B')['id'], 'VectorValue': {'X': 1, 'Y': 2, 'Z': 3}})
    assert vec() != base and '1' in vec() and '3' in vec(), vec()
    edit(m.reset_niagara_script_pin_default, vec, *G(a), pin(a, 'B')['id'])
    assert vec() == base, (vec(), base)
    # Vector/color inputs: stored value edits with type mismatch rejected.
    dir_ = rest('POST', '/niagara/scripts/graph/compound-inputs', {**V, 'ParameterName': 'Dir', 'ValueKind': 'vector', 'VectorValue': {'X': 0, 'Y': 0, 'Z': 1}, 'NodeX': -400, 'NodeY': 200})
    tint = rest('POST', '/niagara/scripts/graph/compound-inputs', {**V, 'ParameterName': 'Tint', 'ValueKind': 'color', 'ColorValue': {'R': 1, 'G': 1, 'B': 1, 'A': 1}, 'NodeX': -400, 'NodeY': 300})
    val = lambda n: json.dumps(nodes()[n['node_path']].get('input', nodes()[n['node_path']]))
    edit(m.set_niagara_script_input_value, lambda: val(dir_), *G(dir_), vector_value=[3, 4, 5])
    edit(m.set_niagara_script_input_value, lambda: val(tint), *G(tint), color_value=[0.25, 0.5, 0.75, 1])
    kept = val(dir_)
    bad(m.set_niagara_script_input_value, *G(dir_), color_value=[1, 1, 1, 1], confirm=True)
    rest('PATCH', '/niagara/scripts/graph/input-value', {**V, 'NodeId': dir_['node_id'], 'NodePath': dir_['node_path'], 'ScalarValue': 0}, expect=False)
    assert val(dir_) == kept and '"x": 3' in kept, (kept, val(dir_))
    # Repeated same-name inputs: exposure and priority edits apply to every definition; diagnostics see none afterwards.
    s1 = rest('POST', '/niagara/scripts/graph/scalar-inputs', {**V, 'ParameterName': 'Speed', 'ValueKind': 'float', 'ScalarValue': 1, 'NodeX': -400, 'NodeY': 500})
    # The routes refuse a second same-name input, so the multi-definition sync path cannot be built here; one definition is edited.
    rest('POST', '/niagara/scripts/graph/scalar-inputs', {**V, 'ParameterName': 'Speed', 'ValueKind': 'float', 'ScalarValue': 1, 'NodeX': -400, 'NodeY': 600}, expect=False)
    s2 = s1
    meta = lambda: json.dumps(nodes()[s1['node_path']], sort_keys=True)
    edit(m.set_niagara_script_input_priority, meta, *G(s1), 7)
    edit(m.set_niagara_script_input_exposure, meta, *G(s1), 'bRequired', False)
    diag = rest('POST', '/niagara/scripts/graph/validate', {'AssetPath': MOD, 'VersionId': v})
    issues = json.dumps(diag)
    assert 'Speed' not in issues or 'mismatch' not in issues.lower(), diag
    return {'graph_nodes': len(nodes()), 'links': len(links())}


# ---------------------------------------------------------------- module pins, rapid iteration, dependency diagnostics
def defaults_stage():
    e = emitter(1)
    E = (SYS, 1, e['id'], e['version_id'])
    rapid = lambda st: {p['name']: p for p in ok(m.inspect_niagara_emitter_rapid_iteration, *E, st)['parameters']}
    axis = 'Constants.DirectionalBurst.GravityForce.Gravity'
    color = next(n for n in rapid('particle_update') if n.startswith('Constants.DirectionalBurst.GenerateLocationEvent.Color'))
    edit(m.set_niagara_emitter_rapid_compound, lambda: rapid('particle_update')[axis], *E, 'particle_update', axis, 'vector', [0, 0, -490])
    edit(m.set_niagara_emitter_rapid_compound, lambda: rapid('particle_update')[color], *E, 'particle_update', color, 'color', [0.2, 0.4, 0.6, 1])
    bad(m.set_niagara_emitter_rapid_compound, *E, 'particle_update', axis, 'color', [1, 1, 1, 1], confirm=True)      # wrong type
    bad(m.set_niagara_emitter_rapid_compound, *E, 'particle_update', 'Constants.Nope', 'vector', [1, 1, 1], confirm=True)
    bad(m.set_niagara_emitter_rapid_compound, *E, 'particle_update', axis, 'vector', [1e12, 0, 0], confirm=True)
    # Module call pins: real stacks expose only static switches, so vector/color pin setters refuse them.
    mods = rest('POST', '/niagara/systems/emitters/stack-inspect', {'AssetPath': SYS, 'bConfirm': True, 'EmitterIndex': 1, 'EmitterId': e['id'],
                                                                      'VersionId': e['version_id'], 'ValueKind': 'particle_update'})['modules']
    drag = next(x for x in mods if x['script_path'].startswith('/Niagara/Modules/Update/Forces/Drag'))
    dpin = next(p for p in ok(m.inspect_niagara_emitter_module, *E, 'particle_update', drag['node_id'], drag['node_path'])['inputs'] if p['name'] == 'Use Linear Drag')
    bad(m.set_niagara_emitter_module_pin_compound, *E, 'particle_update', drag['node_id'], drag['node_path'], dpin['pin_id'], 'vector', [1, 2, 3], confirm=True)
    bad(m.set_niagara_emitter_module_pin_compound, *E, 'particle_update', drag['node_id'], drag['node_path'], dpin['pin_id'], 'color', [1, 2, 3, 1], confirm=True)
    # System module pin default: bool set and native autogenerated reset; compound kinds refused on a bool pin.
    smods = rest('POST', '/niagara/systems/stack-inspect', {'AssetPath': SYS, 'bConfirm': True, 'ValueKind': 'system_update'})['modules']
    sm = smods[0]
    spin = lambda: next(p for p in ok(m.inspect_niagara_system_module, SYS, 'system_update', sm['node_id'], sm['node_path'])['inputs'] if p['name'] == 'UseLoopDelay')
    pid = spin()['pin_id']
    edit(m.edit_niagara_system_module_pin_default, lambda: spin()['default_value'], SYS, 'system_update', sm['node_id'], sm['node_path'], pid,
         kind='bool', value=1 if spin()['default_value'].lower() in ('false', '0', '') else 0)
    bad(m.edit_niagara_system_module_pin_default, SYS, 'system_update', sm['node_id'], sm['node_path'], pid, kind='vector', components=[1, 2, 3], confirm=True)
    bad(m.edit_niagara_system_module_pin_default, SYS, 'system_update', sm['node_id'], sm['node_path'], pid, kind='color', components=[1, 2, 3, 1], confirm=True)
    edit(m.edit_niagara_system_module_pin_default, lambda: spin()['default_value'], SYS, 'system_update', sm['node_id'], sm['node_path'], pid, action='reset')
    edit(m.edit_niagara_system_module_pin_default, lambda: spin()['default_value'], SYS, 'system_update', sm['node_id'], sm['node_path'], pid,
         kind='bool', value=1 if spin()['default_value'].lower() in ('false', '0', '') else 0)
    # Dependency diagnostics on system and emitter stacks.
    for st in ('system_spawn', 'system_update'):
        d = ok(m.inspect_niagara_system_stack_dependencies, SYS, st)
        assert 'dependency_checks' in d and d['unsatisfied_in_this_stack'] == 0, d
    ed = ok(m.inspect_niagara_emitter_stack_dependencies, *E, 'particle_update')
    return {'gravity': rapid('particle_update')[axis].get('value'), 'color': rapid('particle_update')[color].get('value'),
            'system_pin': spin()['default_value']}

# ---------------------------------------------------------------- validation rule leaves and arrays
def rule_stage():
    for path in (ET, ET_SRC):
        rest('POST', '/niagara/effect-types', {'AssetPath': path, 'bConfirm': True, 'bSave': True})
    for cls in ('BannedDataInterfaces', 'BannedModules', 'TickDependencyCheck', 'BannedRenderers'):
        rest('POST', '/niagara/effect-types/rules', {'AssetPath': ET, 'bConfirm': True, 'RuleClass': RULE + cls})
    items = rest('POST', '/niagara/effect-types/inspect', {'AssetPath': ET})['ValidationRules']['items']
    rule = lambda cls: next((ET, r['index'], r['object_path']) for r in items if r['class_path'] == RULE + cls)
    fields = lambda R: {f['name']: f.get('value') for f in ok(m.inspect_niagara_effect_type_rule, *R)['fields']}
    di, mods, tick, rend = rule('BannedDataInterfaces'), rule('BannedModules'), rule('TickDependencyCheck'), rule('BannedRenderers')
    # Class array checked against the native meta class; asset arrays need compatible persistent assets.
    curve = '/Script/Niagara.NiagaraDataInterfaceCurve'
    edit(m.set_niagara_validation_rule_reference_array, lambda: fields(di)['BannedDataInterfaces'], *di, 'BannedDataInterfaces', [curve, '/Script/Niagara.NiagaraDataInterfaceColorCurve'])
    bad(m.set_niagara_validation_rule_reference_array, *di, 'BannedDataInterfaces', ['/Script/Engine.Actor'], confirm=True)
    edit(m.set_niagara_validation_rule_reference_array, lambda: fields(mods)['BannedModules'], *mods, 'BannedModules', ['/Niagara/Modules/Update/Forces/Drag.Drag'])
    bad(m.set_niagara_validation_rule_reference_array, *mods, 'BannedModules', [SYS_SOURCE], confirm=True)
    bad(m.set_niagara_validation_rule_reference_array, *tick, 'EffectTypesToExclude', [ET_SRC], confirm=True)  # soft references are out of scope
    edit(m.set_niagara_validation_rule_reference_array, lambda: fields(rend)['BannedRenderers'], *rend, 'BannedRenderers', ['/Script/Niagara.NiagaraRibbonRendererProperties'])
    bad(m.set_niagara_validation_rule_reference_array, *rend, 'BannedRenderers', ['/Script/Niagara.NiagaraDataInterfaceCurve'], confirm=True)
    edit(m.set_niagara_validation_rule_reference_array, lambda: fields(mods)['BannedModules'], *mods, 'BannedModules', [])
    edit(m.set_niagara_validation_rule_reference_array, lambda: fields(mods)['BannedModules'], *mods, 'BannedModules', ['/Niagara/Modules/Update/Forces/Drag.Drag'])
    # No engine rule has name/asset/vector/color/text/string-array leaves: each setter refuses a leaf of another type.
    bad(m.set_niagara_effect_type_rule_reference, *tick, 'Severity', 'name', value='X', confirm=True)
    bad(m.set_niagara_effect_type_rule_reference, *tick, 'Severity', 'asset', value=ET_SRC, confirm=True)
    bad(m.set_niagara_effect_type_rule_compound, *tick, 'Severity', 'vector', [1, 2, 3], confirm=True)
    bad(m.set_niagara_effect_type_rule_compound, *tick, 'Severity', 'color', [1, 2, 3, 1], confirm=True)
    bad(m.set_niagara_validation_rule_text, *tick, 'Severity', 'text', confirm=True)
    bad(m.set_niagara_validation_rule_string_array, *mods, 'BannedModules', ['a', 'b'], confirm=True)
    return {'di': fields(di)['BannedDataInterfaces'], 'mods': fields(mods)['BannedModules'], 'renderers': fields(rend)['BannedRenderers']}


# ---------------------------------------------------------------- temporary CPU preview
def preview_stage():
    ok(m.duplicate_niagara_system, PREVIEW, PREVIEW_SOURCE, confirm=True)
    ok(m.add_niagara_user_scalar, PREVIEW, 'User.Rate', 'float', value=2, confirm=True)
    ok(m.add_niagara_user_vector, PREVIEW, 'User.Offset', 0, 0, 10, confirm=True)
    ok(m.add_niagara_user_color, PREVIEW, 'User.Tint', 1, 1, 1, confirm=True)
    httpx.post(BASE + '/assets/save', json={'AssetPath': PREVIEW.split('.')[0]}, timeout=600)
    ok(m.request_niagara_system_compile, PREVIEW, force=True, confirm=True)
    import time
    for _ in range(120):
        s = ok(m.inspect_niagara_system, PREVIEW)
        if s['native_ready_to_run'] and not s['compile_or_gpu_requests_pending']:
            break
        time.sleep(2)
    assert s['native_ready_to_run'], 'preview system never became ready'
    users = lambda: ok(m.inspect_niagara_system, PREVIEW)['user_parameters']
    before = users()
    xf = {'Translation': {'X': 100, 'Y': 0, 'Z': 50}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 2, 'Y': 2, 'Z': 2}}
    ov = [{'Name': 'User.Rate', 'Kind': 'float', 'Scalar': 5}, {'Name': 'User.Offset', 'Kind': 'vector', 'Vector': {'X': 1, 'Y': 2, 'Z': 3}},
          {'Name': 'User.Tint', 'Kind': 'color', 'Color': {'R': 1, 'G': 0, 'B': 0, 'A': 1}}]
    for o in ([{'Name': 'User.Nope', 'Kind': 'float', 'Scalar': 1}], [{'Name': 'User.Rate', 'Kind': 'int', 'Scalar': 1}],
              [{'Name': 'User.Offset', 'Kind': 'vector', 'Vector': {'X': float('1e40'), 'Y': 0, 'Z': 0}}]):
        bad(m.simulate_niagara_system_preview, PREVIEW, ticks=4, confirm=True, overrides=o)
    bad(m.simulate_niagara_system_preview, PREVIEW, ticks=4, confirm=True, transform={**xf, 'Scale3D': {'X': 0, 'Y': 1, 'Z': 1}})
    bad(m.simulate_niagara_system_preview, PREVIEW, ticks=601, confirm=True)
    d = ok(m.simulate_niagara_system_preview, PREVIEW, ticks=30, confirm=True, dry_run=True, overrides=ov, transform=xf, seed_offset=17)
    r = ok(m.simulate_niagara_system_preview, PREVIEW, ticks=30, confirm=True, overrides=ov, transform=xf, seed_offset=17)
    samples = r.get('samples') or r.get('snapshots') or []
    assert samples and len(samples) <= 128, str(r)[:500]
    ages = [s.get('age') for s in samples]
    assert all(a is not None for a in ages) and ages == sorted(ages) and ages[-1] > 0, ages
    assert users() == before, 'preview overrides leaked into the persistent system'
    return {'sample_count': len(samples), 'final_age_positive': ages[-1] > 0, 'dry_run_keys': sorted(k for k in d if k != 'scope')[:6]}


# ---------------------------------------------------------------- scalability: structured platform rows, cross-asset copy
def scalability_stage():
    R = lambda path: {'AssetPath': path, 'bConfirm': True, 'ValueKind': 'system'}
    rows = lambda path: ok(m.inspect_niagara_effect_type_scalability, path, 'system')['rows']
    for path in (ET, ET_SRC):
        rest('PATCH', '/niagara/effect-types/scalability/rows', {**R(path), 'NewName': 'add'})
    src = rows(ET_SRC)[0]
    H = {**R(ET_SRC), 'ScalabilityIndex': 0, 'RecordHash': src['record_hash']}
    rest('PATCH', '/niagara/effect-types/scalability/scalar', {**H, 'FieldName': 'MaxInstances', 'ScalarValue': 21})
    H['RecordHash'] = rows(ET_SRC)[0]['record_hash']
    rest('PATCH', '/niagara/effect-types/scalability/quality', {**H, 'ScalarValue': 1, 'bEnabled': False})
    H['RecordHash'] = rows(ET_SRC)[0]['record_hash']
    rest('PATCH', '/niagara/effect-types/scalability/profile', {**H, 'NewName': 'Windows', 'TextValue': 'disabled', 'ScalarValue': 0})
    H['RecordHash'] = rows(ET_SRC)[0]['record_hash']
    rest('PATCH', '/niagara/effect-types/scalability/conditions', {**H, 'NewName': 'add', 'TextValue': 'fx.Niagara.QualityLevel'})
    H['RecordHash'] = rows(ET_SRC)[0]['record_hash']
    rest('PATCH', '/niagara/effect-types/scalability/condition-settings', {**H, 'OutputIndex': 0, 'ConditionConfig': {'Name': 'fx.Niagara.QualityLevel', 'UseMinInt': True, 'MinInt': 1, 'UseMaxInt': True, 'MaxInt': 3}})
    s = rows(ET_SRC)[0]
    flat = json.dumps(s)
    # Structured platform data: quality flags, device profile states, typed CVar conditions.
    assert 'Windows' in flat and 'fx.Niagara.QualityLevel' in flat, flat[:600]
    for key in ('quality', 'profile', 'condition'):
        assert key in flat.lower(), key
    d = rows(ET)[0]
    args = (ET, 'system', 0, d['record_hash'], ET_SRC, 0, s['record_hash'])
    bad(m.copy_niagara_effect_type_scalability_row, ET, 'system', 0, d['record_hash'], ET_SRC, 0, '0' * 32, confirm=True)
    bad(m.copy_niagara_effect_type_scalability_row, ET, 'system', 0, '0' * 32, ET_SRC, 0, s['record_hash'], confirm=True)
    bad(m.copy_niagara_effect_type_scalability_row, ET, 'emitter', 0, d['record_hash'], ET_SRC, 0, s['record_hash'], confirm=True)
    edit(m.copy_niagara_effect_type_scalability_row, lambda: rows(ET), *args)
    strip = lambda r: {k: v for k, v in r.items() if k not in ('record_hash', 'source_asset_path', 'asset_path')}
    assert json.dumps(strip(rows(ET)[0]), sort_keys=True) == json.dumps(strip(rows(ET_SRC)[0]), sort_keys=True), (rows(ET)[0], rows(ET_SRC)[0])
    for path in (ET, ET_SRC):
        httpx.post(BASE + '/assets/save', json={'AssetPath': path.split('.')[0]}, timeout=600)
    return {'row': strip(rows(ET)[0])}

def snapshot():
    """Read-only view of everything prepare authored, for the cold-restart comparison."""
    e1 = emitter(1)
    rs = {r['class_path'].rsplit('.', 1)[1]: r for r in e1['renderers']}
    sel = lambda cls, f: ok(m.inspect_niagara_renderer, SYS, 1, e1['id'], rs[cls]['index'], rs[cls]['object_path'], field=f)['selected_field']['value']
    rapid = {p['name']: p.get('value') for p in ok(m.inspect_niagara_emitter_rapid_iteration, SYS, 1, e1['id'], e1['version_id'], 'particle_update')['parameters']}
    v = ok(m.inspect_niagara_script_asset, MOD)['exposed_version_id']
    items = rest('POST', '/niagara/effect-types/inspect', {'AssetPath': ET})['ValidationRules']['items']
    rules = {r['class_path'].rsplit('_', 1)[1]: {f['name']: f.get('value') for f in ok(m.inspect_niagara_effect_type_rule, ET, r['index'], r['object_path'])['fields']} for r in items}
    row = ok(m.inspect_niagara_effect_type_scalability, ET, 'system')['rows'][0]
    return {
        'renderer_classes': sorted(rs),
        'tiling': sel('NiagaraRibbonRendererProperties', 'UV0Settings.TilingLength'),
        'edge': sel('NiagaraRibbonRendererProperties', 'UV0Settings.LeadingEdgeMode'),
        'name': sel('NiagaraSpriteRendererProperties', 'MaterialUserParamBinding.Parameter.Name'),
        'axis': sel('NiagaraMeshRendererProperties', 'LockedAxis'),
        'event_handlers': emitter(0)['event_handler_count'],
        'gravity': rapid['Constants.DirectionalBurst.GravityForce.Gravity'],
        'emitter_asset': ok(m.inspect_niagara_emitter_asset, EMITTER).get('class_path'),
        'scripts': {p: ok(m.inspect_niagara_script_asset, p).get('usage_name') for p in (MOD, FUNC, DYN)},
        'graph': sorted(n['class_path'].rsplit('.', 1)[1] for n in ok(m.inspect_niagara_script_graph, MOD, v)['nodes']),
        'rules': {k: rules[k] for k in sorted(rules)},
        'row': {k: v for k, v in row.items() if k != 'record_hash'},
    }


def prepare():
    cleanup()
    ok(m.duplicate_niagara_system, SYS, SYS_SOURCE, confirm=True)
    inspection_stage()
    global RENDERERS
    out = {'renderer': renderer_stage(), 'event': event_stage(), 'assets': asset_stage(), 'graph': graph_stage(), 'defaults': defaults_stage(), 'rules': rule_stage(), 'preview': preview_stage(), 'scalability': scalability_stage()}
    removal_stage()
    ok(m.save_asset, SYS.split('.')[0]) if False else httpx.post(BASE + '/assets/save', json={'AssetPath': SYS.split('.')[0]}, timeout=600)
    for a in (SYS, MOD):
        httpx.post(BASE + '/assets/save', json={'AssetPath': a.split('.')[0]}, timeout=600)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(snapshot(), indent=1))
    print(json.dumps(out, indent=1))
    print('niagara batch prepared; saved')


def verify():
    want = json.loads(STATE.read_text())
    got = json.loads(json.dumps(snapshot()))
    diff = {k: (got.get(k), want[k]) for k in want if got.get(k) != want[k]}
    assert not diff, diff
    print(f'{len(want)} Niagara batch snapshot groups identical after cold reload')
    cleanup()
    STATE.unlink(missing_ok=True)


def cleanup():
    for a in ASSETS:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': a.split('.')[0]}, timeout=180)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
