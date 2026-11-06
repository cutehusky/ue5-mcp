"""Material metadata, expression defaults, texture-sample policies, enumerations and parameter collections; prepare, restart, verify.

Usage: smoke_material_metadata_live.py prepare|verify|cleanup. Duplicates a material, material instance and material
function, adds expressions and drives: parameter-group priority/entries, expression Group/SortPriority/Desc (material and
function owners), scalar slider range/control type/enumeration reference/enumeration index, primitive-data binding,
vector/texture channel labels, scalar/vector defaults, static bool/component-mask defaults, texture-sample policy fields,
sampler synchronization and texture/texture-object references, font sample defaults and atlas inspection, enumeration
entry/value resolution, instance enumeration slots, and Material Parameter Collections (create, add, defaults, rename,
reorder, expression reference, references, validation, discovery, world values set/reset, delete). Each edit is
rejected with stale guards, dry-run checked, then applied. Authored state must survive a cold editor restart.
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
T = '/Game/UE5MCP_Test/'
MAT, MI, MF, MPC = T + 'M_MCP_Meta', T + 'MI_MCP_Meta', T + 'MF_MCP_Meta', T + 'MPC_MCP_Meta'
A, AI, AF, AC = MAT + '.M_MCP_Meta', MI + '.MI_MCP_Meta', MF + '.MF_MCP_Meta', MPC + '.MPC_MCP_Meta'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'material_metadata.json'
TEX = '/Engine/EngineResources/DefaultTexture.DefaultTexture'
NORMAL = '/Engine/EngineMaterials/DefaultNormal.DefaultNormal'
FONT = '/Engine/EngineFonts/RobotoDistanceField.RobotoDistanceField'
ENUM, ENUM_CLASS = '/Script/Engine.EBlendMode', '/Script/CoreUObject.Enum'
KINDS = ('ScalarParameter', 'VectorParameter', 'TextureSampleParameter2D', 'TextureObject', 'StaticBoolParameter',
         'StaticComponentMaskParameter', 'FontSampleParameter', 'CollectionParameter', 'TextureSample', 'StaticSwitchParameter')


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


def edit(fn, state, *a, changes=True, **kw):
    before = state()
    ok(fn, *a, confirm=True, dry_run=True, **kw)
    assert state() == before, (fn.__name__, 'dry run changed state')
    r = ok(fn, *a, confirm=True, dry_run=False, **kw)
    if changes:
        assert state() != before, (fn.__name__, 'edit left state unchanged', str(r)[:300])
    return r


def expr(kind, owner=A):
    es = ok(m.discover_material_expression_metadata, owner, ':MCP_' if owner == A else '', '', 0, 128)['expressions']
    return next(e for e in es if e['class_path'].endswith('Expression' + kind)) if owner == A else es[0]


def ids(kind, owner=A):
    e = expr(kind, owner)
    return owner, e['expression_path'], e['node_guid']


def guard(kind, owner=A):
    """(expected_class_path, expected_metadata_snapshot) for the expression."""
    e = expr(kind, owner)
    return e['class_path'], e['metadata_snapshot']


def meta(kind, owner=A):
    return {f['name']: f.get('value', f.get('text')) for f in ok(m.inspect_material_expression_metadata, *ids(kind, owner))['fields']}


def strip(d):
    return {k: v for k, v in d.items() if k not in ('scope', 'would_change', 'written', 'dry_run', 'metadata_snapshot', 'package_dirty')}


def save(*paths):
    for p in paths:
        httpx.post(BASE + '/assets/save', json={'AssetPath': p}, timeout=600)


# ---------------------------------------------------------------- parameter groups
def group_stage():
    G = lambda: ok(m.inspect_material_parameter_groups, A, 0, 128)
    g = G()
    cls, snap = g['class_path'], g['group_snapshot']
    bad(m.edit_material_parameter_group_entry, A, 'Add', 'MCP Group', cls, snap + ' ', priority=5, confirm=True, dry_run=False)
    bad(m.edit_material_parameter_group_entry, A, 'Add', 'surface properties', cls, snap, priority=5, confirm=True, dry_run=False)  # case-insensitive duplicate
    edit(m.edit_material_parameter_group_entry, G, A, 'Add', 'MCP Group', cls, snap, priority=5)
    g = G()
    i = next(x['index'] for x in g['groups'] if x['name'] == 'MCP Group')
    bad(m.set_material_parameter_group_priority, A, i, 'MCP Group', 7, 4, cls, g['group_snapshot'], confirm=True, dry_run=False)
    bad(m.set_material_parameter_group_priority, A, i, 'MCP Group', 2000000, 5, cls, g['group_snapshot'], confirm=True, dry_run=False)
    edit(m.set_material_parameter_group_priority, G, A, i, 'MCP Group', 7, 5, cls, g['group_snapshot'])
    edit(m.edit_material_parameter_group_entry, G, A, 'Add', 'MCP Temp', cls, G()['group_snapshot'], priority=1)
    g = G()
    j = next(x['index'] for x in g['groups'] if x['name'] == 'MCP Temp')
    bad(m.edit_material_parameter_group_entry, A, 'Remove', 'MCP Temp', cls, g['group_snapshot'], group_index=j, expected_priority=9, confirm=True, dry_run=False)
    edit(m.edit_material_parameter_group_entry, G, A, 'Remove', 'MCP Temp', cls, g['group_snapshot'], group_index=j, expected_priority=1)
    return [x for x in G()['groups'] if x['name'] == 'MCP Group']


# ---------------------------------------------------------------- expression metadata (material and function owners)
def metadata_stage():
    k = 'ScalarParameter'
    for field, kw, check in (('Group', {'text': 'MCP Group', 'expected_text': 'None'}, 'MCP Group'),
                             ('SortPriority', {'value': 5, 'expected_value': 32}, 5),
                             ('Desc', {'text': 'MCP scalar', 'expected_text': ''}, 'MCP scalar')):
        cls, snap = guard(k)
        stale = dict(kw, **({'expected_text': 'nope'} if 'text' in kw else {'expected_value': 99}))
        bad(m.set_material_expression_metadata, *ids(k), field, cls, snap, confirm=True, dry_run=False, **stale)
        bad(m.set_material_expression_metadata, *ids(k), field, cls, snap + 'x', confirm=True, dry_run=False, **kw)
        edit(m.set_material_expression_metadata, lambda: meta(k), *ids(k), field, cls, snap, **kw)
        assert meta(k)[field] == check, meta(k)
    found = ok(m.discover_material_expression_metadata, A, '', 'MCP Group', 0, 128)['expressions']
    assert [e['expression_path'] for e in found] == [ids(k)[1]], found
    # Material Function owner: Desc on its first expression.
    cls, snap = guard(None, AF)
    cur = meta(None, AF)['Desc']
    edit(m.set_material_expression_metadata, lambda: meta(None, AF), *ids(None, AF), 'Desc', cls, snap, text='MCP function node', expected_text=cur)
    return {'scalar': meta(k), 'function': meta(None, AF)}


# ---------------------------------------------------------------- scalar controls, enumerations, primitive data
def scalar_stage():
    k = 'ScalarParameter'
    S = lambda: strip(ok(m.material_scalar_slider_range, *ids(k)))
    bad(m.material_scalar_slider_range, *ids(k), 'Set', [0, 10], [1, 1], *guard(k), confirm=True, dry_run=False)
    bad(m.material_scalar_slider_range, *ids(k), 'Set', [0, 1e6], [0, 0], *guard(k), confirm=True, dry_run=False)
    edit(m.material_scalar_slider_range, S, *ids(k), 'Set', [-2, 10], [0, 0], *guard(k))
    assert S()['bounds_enabled'] and S()['slider_max'] == 10, S()
    D = lambda: strip(ok(m.material_expression_parameter_default, *ids(k)))
    bad(m.material_expression_parameter_default, *ids(k), 'Set', 0.5, 1, [], [], *guard(k), confirm=True, dry_run=False)
    bad(m.material_expression_parameter_default, *ids(k), 'Set', 1e6, 0, [], [], *guard(k), confirm=True, dry_run=False)
    edit(m.material_expression_parameter_default, D, *ids(k), 'Set', 0.5, 0, [], [], *guard(k))
    # Enumeration control: control type, then the enumeration reference.
    E = lambda: strip(ok(m.material_scalar_enumeration_reference, *ids(k)))
    bad(m.material_scalar_enumeration_reference, *ids(k), 'Set', ENUM, '', *guard(k), confirm=True, dry_run=False)   # control type is Numeric
    edit(m.set_material_expression_metadata, lambda: meta(k), *ids(k), 'ControlType', *guard(k), value=1, expected_value=0)
    bad(m.material_scalar_enumeration_reference, *ids(k), 'Set', ENUM, 'X', *guard(k), confirm=True, dry_run=False)
    bad(m.material_scalar_enumeration_reference, *ids(k), 'Set', TEX, '', *guard(k), confirm=True, dry_run=False)   # not an enumeration
    edit(m.material_scalar_enumeration_reference, E, *ids(k), 'Set', ENUM, '', *guard(k))
    assert E()['enumeration_soft_path'] == ENUM, E()
    # Enumeration entries and value resolution.
    bad(m.inspect_material_enumeration_entries, ENUM, ENUM_CLASS, 0, 4)                                             # confirmation required
    bad(m.inspect_material_enumeration_entries, ENUM, '/Script/Engine.Material', 0, 4, confirm=True)
    en = ok(m.inspect_material_enumeration_entries, ENUM, ENUM_CLASS, 0, 4, confirm=True)
    assert 'BLEND_Opaque' in json.dumps(en) and en.get('has_more', True), en
    rv = ok(m.resolve_material_enumeration_value, ENUM, ENUM_CLASS, 'BLEND_Masked', -1, confirm=True)
    assert rv.get('found') and str(rv.get('value_decimal', rv.get('result'))) == '1', rv
    miss = ok(m.resolve_material_enumeration_value, ENUM, ENUM_CLASS, 'NoSuchEntry', -7, confirm=True)
    assert not miss.get('found') and str(miss.get('value_decimal', miss.get('result'))) == '-7', miss
    # EnumerationIndex control on a second scalar (the vector stays numeric).
    edit(m.set_material_expression_metadata, lambda: meta(k), *ids(k), 'ControlType', *guard(k), value=2, expected_value=1)
    bad(m.set_material_expression_metadata, *ids(k), 'EnumerationIndex', *guard(k), value=300, expected_value=0, confirm=True, dry_run=False)
    edit(m.set_material_expression_metadata, lambda: meta(k), *ids(k), 'EnumerationIndex', *guard(k), value=3, expected_value=0)
    edit(m.set_material_expression_metadata, lambda: meta(k), *ids(k), 'ControlType', *guard(k), value=1, expected_value=2)
    # Primitive-data binding for scalar and vector.
    for kind, idx in ((k, 3), ('VectorParameter', 8)):
        P = lambda kind=kind: strip(ok(m.material_parameter_primitive_data_binding, *ids(kind)))
        bad(m.material_parameter_primitive_data_binding, *ids(kind), 'Set', True, idx, True, 0, *guard(kind), confirm=True, dry_run=False)
        bad(m.material_parameter_primitive_data_binding, *ids(kind), 'Set', True, 999, False, 0, *guard(kind), confirm=True, dry_run=False)
        edit(m.material_parameter_primitive_data_binding, P, *ids(kind), 'Set', True, idx, False, 0, *guard(kind))
        assert P()['enabled'] and P()['float_index'] == idx, P()
    return {'slider': S(), 'default': D(), 'enum': E()}


# ---------------------------------------------------------------- vector/static defaults and labels
def vector_stage():
    v = 'VectorParameter'
    D = lambda: strip(ok(m.material_expression_parameter_default, *ids(v)))
    bad(m.material_expression_parameter_default, *ids(v), 'Set', 0, 0, [1, 0.5, 0.25, 1], [1, 1, 1, 1], *guard(v), confirm=True, dry_run=False)
    edit(m.material_expression_parameter_default, D, *ids(v), 'Set', 0, 0, [1, 0.5, 0.25, 1], [0, 0, 0, 0], *guard(v))
    for kind, fn in ((v, m.material_vector_channel_labels), ('TextureSampleParameter2D', m.material_texture_channel_labels)):
        L = lambda kind=kind, fn=fn: strip(ok(fn, *ids(kind)))
        bad(fn, *ids(kind), 'Set', ['R', 'G', 'B', 'A'], ['x', '', '', ''], *guard(kind), confirm=True, dry_run=False)
        bad(fn, *ids(kind), 'Set', ['R', 'G\n', 'B', 'A'], ['', '', '', ''], *guard(kind), confirm=True, dry_run=False)
        edit(fn, L, *ids(kind), 'Set', ['Red', 'Green', 'Blue', 'Alpha'], ['', '', '', ''], *guard(kind))
    b = 'StaticBoolParameter'
    B = lambda: strip(ok(m.material_static_parameter_default, *ids(b)))
    bad(m.material_static_parameter_default, *ids(b), 'Set', True, True, [], [], *guard(b), confirm=True, dry_run=False)
    edit(m.material_static_parameter_default, B, *ids(b), 'Set', True, False, [], [], *guard(b))
    s = 'StaticSwitchParameter'
    W = lambda: strip(ok(m.material_static_parameter_default, *ids(s)))
    edit(m.material_static_parameter_default, W, *ids(s), 'Set', True, W()['default_bits'][0] == 1, [], [], *guard(s))
    c = 'StaticComponentMaskParameter'
    C = lambda: strip(ok(m.material_static_parameter_default, *ids(c)))
    bad(m.material_static_parameter_default, *ids(c), 'Set', False, False, [0, 1, 1, 0], [0, 0, 0, 0], *guard(c), confirm=True, dry_run=False)
    bad(m.material_static_parameter_default, *ids(c), 'Set', False, False, [0, 2, 1, 0], [1, 0, 0, 0], *guard(c), confirm=True, dry_run=False)
    edit(m.material_static_parameter_default, C, *ids(c), 'Set', False, False, [0, 1, 1, 0], [1, 0, 0, 0], *guard(c))
    return {'vector': D(), 'bool': B(), 'switch': W(), 'mask': C()}


# ---------------------------------------------------------------- texture samples and objects
def texture_stage():
    t = 'TextureSampleParameter2D'
    P = lambda kind=t: strip(ok(m.material_texture_sample_policy, *ids(kind)))
    setting = lambda f, kind=t: next(x for x in P(kind)['settings'] if x['field_name'] == f)
    print('policy fields', [x['field_name'] for x in P()['settings']])
    for f, val in (('SamplerSource', 1), ('MipValueMode', 1), ('AutomaticViewMipBias', None), ('ConstCoordinate', 2)):
        cur = setting(f)['value']
        val = (0 if cur else 1) if val is None else val
        bad(m.material_texture_sample_policy, *ids(t), f, val, cur + 1, *guard(t), confirm=True, dry_run=False)
        edit(m.material_texture_sample_policy, P, *ids(t), f, val, cur, *guard(t))
    cur = setting('ConstMipValue')['value']
    bad(m.material_texture_sample_policy, *ids(t), 'ConstMipValue', 99, cur, *guard(t), confirm=True, dry_run=False)
    edit(m.material_texture_sample_policy, P, *ids(t), 'ConstMipValue', 4, cur, *guard(t))
    bad(m.material_texture_sample_policy, *ids(t), 'ConstCoordinate', 9, 2, *guard(t), confirm=True, dry_run=False)
    g = setting('GatherMode')
    edit(m.material_texture_sample_policy, P, *ids(t), 'GatherMode', 1, g['value'], *guard(t))
    edit(m.material_texture_sample_policy, P, *ids(t), 'GatherMode', 0, 1, *guard(t))
    # Reference change to a normal map, then explicit sampler synchronization.
    R = lambda kind=t: P(kind)['texture_path']
    cur = R()
    bad(m.set_material_texture_sample_reference, *ids(t), NORMAL, '/Engine/Nope.Nope', *guard(t), confirm=True, dry_run=False)
    bad(m.set_material_texture_sample_reference, *ids(t), '/Engine/BasicShapes/Cube.Cube', cur, *guard(t), confirm=True, dry_run=False)
    edit(m.set_material_texture_sample_reference, R, *ids(t), NORMAL, cur, *guard(t))
    sampler = setting('SamplerType')['value']
    sync = P()
    print('sync diag', {k: v for k, v in sync.items() if 'sampler' in k.lower() or 'verify' in k.lower()})
    expected = sync.get('expected_sampler_type', sync.get('native_expected_sampler_type', 3))
    edit(m.material_texture_sample_policy, P, *ids(t), 'SynchronizeSamplerType', expected, sampler, *guard(t), changes=expected != sampler)
    assert setting('SamplerType')['value'] == expected, P()
    edit(m.material_texture_sample_policy, P, *ids(t), 'SamplerType', 0, expected, *guard(t))
    o = 'TextureObject'
    O = lambda: json.loads(guard(o)[1]).get('Texture')
    print('texture object snapshot Texture =', O())
    cur_o = O() or ''
    cur_o = cur_o.split("'")[1] if "'" in cur_o else ('' if cur_o == 'None' else cur_o)
    target = NORMAL if cur_o != NORMAL else TEX
    bad(m.set_material_texture_sample_reference, *ids(o), target, '/Engine/Nope.Nope', *guard(o), confirm=True, dry_run=False)
    edit(m.set_material_texture_sample_reference, O, *ids(o), target, cur_o, *guard(o))
    s = 'TextureSample'
    cur_s = R(s)
    edit(m.set_material_texture_sample_reference, lambda: R(s), *ids(s), TEX if cur_s != TEX else NORMAL, cur_s, *guard(s))
    edit(m.set_material_texture_sample_reference, lambda: R(s), *ids(s), '', R(s), *guard(s))
    return {'param': P(), 'sample': P(s)}


# ---------------------------------------------------------------- font samples
def font_stage():
    f = 'FontSampleParameter'
    atlas = ok(m.inspect_material_font_atlas, FONT)
    assert atlas['offline_cache'] and atlas['atlas_page_count'] >= 1, atlas
    bad(m.inspect_material_font_atlas, '/Engine/EngineFonts/Nope.Nope')
    F = lambda: strip(ok(m.material_font_sample_default, *ids(f)))
    snap = atlas['font_snapshot']
    bad(m.material_font_sample_default, *ids(f), 'Set', FONT, 0, FONT, 0, *guard(f), snap, confirm=True, dry_run=False)
    bad(m.material_font_sample_default, *ids(f), 'Set', FONT, 5, 'None', 0, *guard(f), snap, confirm=True, dry_run=False)   # page out of range
    bad(m.material_font_sample_default, *ids(f), 'Set', FONT, 0, 'None', 0, *guard(f), snap + ' ', confirm=True, dry_run=False)
    edit(m.material_font_sample_default, F, *ids(f), 'Set', FONT, 0, 'None', 0, *guard(f), snap)
    assert F()['font_path'] == FONT, F()
    return F()


# ---------------------------------------------------------------- Material Parameter Collections
def collection_stage():
    bad(m.create_material_parameter_collection, MPC, confirm=True, dry_run=False)                       # needs Folder/Name.Name
    bad(m.create_material_parameter_collection, AC)                                                     # confirmation required
    ok(m.create_material_parameter_collection, AC, confirm=True, dry_run=True)
    assert 'errorMessage' in J(m.material_collection_defaults(AC))
    r = ok(m.create_material_parameter_collection, AC, confirm=True, dry_run=False)
    bad(m.create_material_parameter_collection, AC, confirm=True, dry_run=False)
    D = lambda: ok(m.material_collection_defaults, AC, 'Inspect', 0, 128)
    print('mpc keys', sorted(D()))
    cls = D().get('class_path', '/Script/Engine.MaterialParameterCollection')
    snap = lambda: D().get('defaults_snapshot', D().get('snapshot'))
    for kind, name, kw in (('Scalar', 'Wind', {'value': 0.25}), ('Scalar', 'Tint', {'value': 2}), ('Vector', 'Sun', {'rgba': [1, 0.9, 0.8, 1]})):
        bad(m.add_material_collection_parameter, AC, kind, name, cls, snap() + ' ', confirm=True, dry_run=False, **kw)
        edit(m.add_material_collection_parameter, snap, AC, kind, name, cls, snap(), **kw)
    bad(m.add_material_collection_parameter, AC, 'Scalar', 'Wind', cls, snap(), value=1, confirm=True, dry_run=False)   # duplicate
    params = lambda: D()['parameters']
    p = lambda name: next(x for x in params() if x['name'] == name)
    print('param row', p('Wind'))
    w = p('Wind')
    bad(m.material_collection_defaults, AC, 'Scalar', 0, 128, 'Wind', w['guid'], 0.75, 0.5, [], [], cls, snap(), confirm=True, dry_run=False)
    edit(m.material_collection_defaults, snap, AC, 'Scalar', 0, 128, 'Wind', w['guid'], 0.75, 0.25, [], [], cls, snap())
    s = p('Sun')
    edit(m.material_collection_defaults, snap, AC, 'Vector', 0, 128, 'Sun', s['guid'], 0, 0, [0.5, 0.5, 1, 1], s['default_components'], cls, snap())
    t = p('Tint')
    bad(m.rename_material_collection_parameter, AC, 'Scalar', t['index'], 'Tint', 'Wind', t['guid'], cls, snap(), confirm=True, dry_run=False)
    edit(m.rename_material_collection_parameter, snap, AC, 'Scalar', t['index'], 'Tint', 'Strength', t['guid'], cls, snap())
    assert p('Strength')['guid'] == t['guid']
    bad(m.reorder_material_collection_parameters, AC, 'Scalar', [0, 0], cls, snap(), confirm=True, dry_run=False)
    edit(m.reorder_material_collection_parameters, snap, AC, 'Scalar', [1, 0], cls, snap())
    assert [x['name'] for x in params() if x['kind'].lower() == 'scalar'] == ['Strength', 'Wind'], params()
    # Expression reference from the material.
    save(MPC)
    k = 'CollectionParameter'
    layout = ok(m.material_collection_parameter_reference, *ids(k), 'Inspect')
    C = lambda: strip(ok(m.material_collection_parameter_reference, *ids(k)))
    lay = D().get('layout_snapshot', snap())
    bad(m.material_collection_parameter_reference, *ids(k), 'Set', AC, 'Nope', 'None', 'None', *guard(k), lay, confirm=True, dry_run=False)
    edit(m.material_collection_parameter_reference, C, *ids(k), 'Set', AC, 'Wind', 'None', 'None', *guard(k), lay)
    assert C()['parameter_guid'] == p('Wind')['guid'], C()
    refs = ok(m.inspect_material_collection_references, AC, p('Wind')['guid'])
    assert ids(k)[1] in json.dumps(refs), refs
    rows = [r for r in json.loads(json.dumps(refs)).get('references', refs.get('expressions', [])) if r.get('expression_path') == ids(k)[1]]
    assert len(rows) == 1, refs
    r = rows[0]
    assert r.get('node_guid') == ids(k)[2] and A in json.dumps(r) and 'CollectionParameter' in json.dumps(r), r
    # A GUID filter that matches nothing, paging bounds, and the unfiltered page.
    none = ok(m.inspect_material_collection_references, AC, '0' * 31 + '1')
    assert ids(k)[1] not in json.dumps(none), none
    bad(m.inspect_material_collection_references, AC, p('Wind')['guid'], 0, 0)
    assert ids(k)[1] in json.dumps(ok(m.inspect_material_collection_references, AC))
    caps = json.loads(httpx.get(BASE + '/assets/capabilities', timeout=60).text)['families']
    assert caps['material_parameter_collection']['validate'] and caps['material_parameter_collection']['spawn_or_create'], caps['material_parameter_collection']
    assert caps['material_expression_metadata']['edit'] and not caps['material_expression_metadata']['spawn_or_create'], caps['material_expression_metadata']
    v = ok(m.validate_material_collection_structure, AC)
    assert v.get('valid', not v.get('errors')), v
    disc = ok(m.discover_material_parameter_collections, 'MPC_MCP_Meta')
    assert AC in json.dumps(disc), disc
    # World values on the current editor world: set an override, then reset.
    world = ok(m.inspect_editor_world_settings)['world_path']
    world = world + '.' + world.rsplit('/', 1)[1]
    bad(m.inspect_material_collection_world_values, AC, world)                                          # confirmation required
    wv = ok(m.inspect_material_collection_world_values, AC, world, 'Editor', 0, 128, confirm=True)
    print('world keys', sorted(wv))
    inst = wv.get('instance_path')
    WV = lambda: ok(m.inspect_material_collection_world_values, AC, world, 'Editor', 0, 128, confirm=True)['parameters']
    cw = next(x for x in WV() if x['name'] == 'Wind')
    eff = cw['effective_components'][0]
    bad(m.set_material_collection_world_value, AC, world, inst, 'Scalar', 'Wind', w['guid'], snap(), value=3, expected_value=eff + 1, confirm=True, dry_run=False)
    edit(m.set_material_collection_world_value, WV, AC, world, inst, 'Scalar', 'Wind', w['guid'], snap(), value=3, expected_value=eff)
    ws = ok(m.inspect_material_collection_world_values, AC, world, 'Editor', 0, 128, confirm=True)
    wsnap = ws['world_values_snapshot']
    edit(m.reset_material_collection_world_values, WV, AC, world, inst, snap(), wsnap)
    # Delete: the referenced parameter needs the exact loaded reference set and explicit allow flag.
    x = p('Wind')
    d = ok(m.delete_material_collection_parameter, AC, 'Scalar', x['index'], 'Wind', x['guid'], cls, snap(), confirm=True, dry_run=True)
    refs = d.get('loaded_reference_paths', d.get('expression_paths', []))
    bad(m.delete_material_collection_parameter, AC, 'Scalar', x['index'], 'Wind', x['guid'], cls, snap(), refs, False, confirm=True, dry_run=False)
    y = p('Strength')
    edit(m.delete_material_collection_parameter, snap, AC, 'Scalar', y['index'], 'Strength', y['guid'], cls, snap(), [], False)
    assert [q['name'] for q in params()] == ['Wind', 'Sun'] or sorted(q['name'] for q in params()) == ['Sun', 'Wind'], params()
    return {'params': params()}


# ---------------------------------------------------------------- material instance enumeration slots
def instance_stage():
    save(MAT)
    S = lambda: ok(m.material_instance_enumeration_slots, AI)
    s = S()
    print('slots keys', sorted(s))
    cls = s.get('class_path', '/Script/Engine.MaterialInstanceConstant')
    snap = s.get('enumeration_snapshot', s.get('snapshot'))
    assert s['local_slot_count'] == 0, s
    bad(m.material_instance_enumeration_slots, AI, 'Set', 0, 64, ENUM, True, ENUM, cls, snap, confirm=True, dry_run=False)
    edit(m.material_instance_enumeration_slots, S, AI, 'Set', 0, 64, ENUM, False, '', cls, snap)
    s = S()
    assert s['local_slot_count'] == 1, s
    bad(m.material_instance_enumeration_slots, AI, 'Set', 5, 64, ENUM, False, '', cls, s['enumeration_snapshot'], confirm=True, dry_run=False)  # no gaps
    edit(m.material_instance_enumeration_slots, S, AI, 'Set', 0, 64, '', True, ENUM, cls, s['enumeration_snapshot'])        # clear falls back to parent
    return {k: v for k, v in S().items() if k not in ('scope', 'package_dirty')}


def snapshot():
    out = {'groups': ok(m.inspect_material_parameter_groups, A, 0, 128)['groups'], 'function': meta(None, AF)}
    for k in KINDS:
        out[k] = json.loads(guard(k)[1])
    out['collection'] = {k: v for k, v in ok(m.material_collection_defaults, AC, 'Inspect', 0, 128).items() if k not in ('scope', 'package_dirty')}
    out['instance'] = {k: v for k, v in ok(m.material_instance_enumeration_slots, AI).items() if k not in ('scope', 'package_dirty')}
    return out


def prepare():
    cleanup()
    for src, dst in (('/Game/LevelPrototyping/Materials/M_PrototypeGrid.M_PrototypeGrid', MAT),
                     ('/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray', MI),
                     ('/Engine/Functions/Engine_MaterialFunctions02/Utility/AppendMany.AppendMany', MF)):
        assert httpx.post(BASE + '/assets/duplicate', json={'AssetPath': src, 'DestinationPath': dst}, timeout=300).is_success
    for k in KINDS:
        ok(m.create_material_expression, A, '/Script/Engine.MaterialExpression' + k, 'MCP_' + k) if False else m.create_material_expression(A, '/Script/Engine.MaterialExpression' + k, 'MCP_' + k)
    assert httpx.patch(BASE + '/material-instances/parent', json={'AssetPath': AI, 'ParentPath': A}, timeout=300).is_success
    out = {}
    for fn in (group_stage, metadata_stage, scalar_stage, vector_stage, texture_stage, font_stage, collection_stage, instance_stage):
        out[fn.__name__] = fn()
    save(MAT, MI, MF, MPC)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1))
    print('material metadata prepared; assets saved')


def verify():
    st = json.loads(STATE.read_text())
    for p in (A, AI, AF, AC):
        ok(m.get_asset_properties, p)
    got = json.loads(json.dumps(snapshot()))
    want = st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('material metadata identical after cold reload')
    cleanup()


def cleanup():
    for p in (MI, MAT, MF, MPC):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
