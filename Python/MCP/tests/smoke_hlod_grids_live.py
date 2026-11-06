"""World Partition HLOD layers and RuntimeHashSet grids: prepare, restart, verify.

Usage: smoke_hlod_grids_live.py prepare|verify|cleanup. Creates HLOD Layer assets and drives generation type, builder/
actor/modifier classes, builder settings (field discovery, numeric, bool, enum, asset reference; string/name/int64
setters refuse non-matching leaves), parent and Custom HLOD Actor linked layers, linked chains and referencers. On an
OpenWorld template copy it edits the partition default HLOD layer, HLOD editor options, streaming enable, actor HLOD
assignment and grid/HLOD eligibility, then RuntimeHashSet authoring: main definition numeric/bool/bounds/origin/color/
rename/fields, HLOD setup add/reorder/remove/normalize/reference slots, and main definition add/reorder/class/remove.
Each edit is rejected with a stale expected value, dry-run checked, then applied. Authored state must survive a cold
editor restart.
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
MAP = '/Game/UE5MCP_Test/MCP_HLODGrids'
TEMPLATE = '/Engine/Maps/Templates/OpenWorld'
LAYERS = {n: f'/Game/UE5MCP_Test/HLOD_MCP_{n}' for n in ('Merge', 'Approx', 'Custom', 'Linked', 'Parent')}
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'hlod_grids.json'
MATERIAL = '/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial'


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


def obj(n):
    return LAYERS[n] + '.' + LAYERS[n].rsplit('/', 1)[1]


def L(n):
    return ok(m.inspect_world_partition_hlod_layer, obj(n))


def save():
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']
    for p in LAYERS.values():
        httpx.post(BASE + '/assets/save', json={'AssetPath': p}, timeout=600)


def wp():
    return ok(m.inspect_world_partition)['partition_path']


def field(n, path):
    l = L(n)
    struct = path.rsplit('.', 1)[0] if '.' in path else ''
    fs = ok(m.inspect_hlod_builder_setting_fields, obj(n), l['builder_settings_path'], struct, 0, 128)['fields']
    return next(f for f in fs if f['path'] == path)


# ---------------------------------------------------------------- HLOD layer assets
def layer_stage():
    for n, p in LAYERS.items():
        bad(m.create_world_partition_hlod_layer_asset, p)                       # confirmation required
        ok(m.create_world_partition_hlod_layer_asset, p, confirm=True, dry_run=True)
        assert 'errorMessage' in J(m.inspect_world_partition_hlod_layer(obj(n)))
        r = ok(m.create_world_partition_hlod_layer_asset, p, confirm=True)
        assert r['created'] and r['layer_type'] == 0, r
    bad(m.create_world_partition_hlod_layer_asset, LAYERS['Merge'], confirm=True)
    # Generation types: Merge=1, Approx=3, Custom HLOD Actor=5; Custom builder (4) needs a builder class first.
    for n, t in (('Merge', 1), ('Approx', 3), ('Custom', 5), ('Linked', 2)):
        l = L(n)
        bad(m.set_world_partition_hlod_layer_type, obj(n), l['layer_type_ordinal'], l['builder_settings_path'] + 'X', t, confirm=True)
        bad(m.set_world_partition_hlod_layer_type, obj(n), l['layer_type_ordinal'] + 1, l['builder_settings_path'], t, confirm=True)
        edit(m.set_world_partition_hlod_layer_type, lambda n=n: L(n), obj(n), l['layer_type_ordinal'], l['builder_settings_path'], t)
        assert L(n)['layer_type_ordinal'] == t, L(n)
    l = L('Parent')
    bad(m.set_world_partition_hlod_layer_type, obj('Parent'), 0, l['builder_settings_path'], 4, confirm=True)
    bad(m.set_world_partition_hlod_layer_type, obj('Parent'), 0, l['builder_settings_path'], 6, confirm=True)
    # Builder class then Custom type on Parent.
    bad(m.set_world_partition_hlod_layer_class, obj('Parent'), 0, l['builder_settings_path'], 'HLODBuilderClass', '', '/Script/Engine.Actor', confirm=True)
    edit(m.set_world_partition_hlod_layer_class, lambda: L('Parent'), obj('Parent'), 0, l['builder_settings_path'], 'HLODBuilderClass',
         '', '/Script/Engine.NullHLODBuilder')
    l = L('Parent')
    assert l['builder_class_path'].endswith('NullHLODBuilder'), l
    edit(m.set_world_partition_hlod_layer_type, lambda: L('Parent'), obj('Parent'), 0, l['builder_settings_path'], 4)
    l = L('Parent')
    bad(m.set_world_partition_hlod_layer_class, obj('Parent'), 4, l['builder_settings_path'], 'HLODActorClass', '/Script/Engine.Actor', '/Script/Engine.WorldPartitionHLOD', confirm=True)
    edit(m.set_world_partition_hlod_layer_class, lambda: L('Parent'), obj('Parent'), 4, l['builder_settings_path'], 'HLODActorClass',
         l['actor_class_path'], '', changes=l['actor_class_path'] not in ('', 'None'))
    # Builder settings on Merge (MeshMergeSettings) and Approx.
    m_ = L('Merge')
    S = m_['builder_settings_path']
    top = ok(m.inspect_hlod_builder_setting_fields, obj('Merge'), S, '', 0, 128)
    assert any(f['path'] == 'MeshMergeSettings' for f in top['fields']), top
    bad(m.inspect_hlod_builder_setting_fields, obj('Merge'), S + 'X', '', 0, 128)
    F = lambda p: (lambda: field('Merge', p))
    p = 'MeshMergeSettings.TargetLightMapResolution'
    cur = field('Merge', p)['value']
    bad(m.set_hlod_builder_numeric, obj('Merge'), 1, S, p, cur + 1, 512, confirm=True)
    bad(m.set_hlod_builder_numeric, obj('Merge'), 1, S, p, cur, 5000, confirm=True)             # ClampMax 4096
    edit(m.set_hlod_builder_numeric, F(p), obj('Merge'), 1, S, p, cur, 512)
    p = 'MeshMergeSettings.MaterialSettings.TargetTexelDensityPerMeter'
    edit(m.set_hlod_builder_numeric, F(p), obj('Merge'), 1, S, p, field('Merge', p)['value'], 12.5)
    p = 'MeshMergeSettings.MaterialSettings.bAllowTwoSidedMaterial'
    cur = field('Merge', p)['value']
    bad(m.set_hlod_builder_bool, obj('Merge'), 1, S, p, not cur, cur, confirm=True)
    edit(m.set_hlod_builder_bool, F(p), obj('Merge'), 1, S, p, cur, not cur)
    p = 'MeshMergeSettings.LODSelectionType'
    cur = field('Merge', p)['enum_name']
    bad(m.set_hlod_builder_enum, obj('Merge'), 1, S, p, 'AllLODs' if cur != 'AllLODs' else 'SpecificLOD', 'SpecificLOD', confirm=True)
    bad(m.set_hlod_builder_enum, obj('Merge'), 1, S, p, cur, 'NoSuchChoice', confirm=True)
    edit(m.set_hlod_builder_enum, F(p), obj('Merge'), 1, S, p, cur, 'AllLODs' if cur != 'AllLODs' else 'SpecificLOD')
    p = 'MeshMergeSettings.MaterialSettings.BlendMode'                                          # TEnumAsByte
    edit(m.set_hlod_builder_enum, F(p), obj('Merge'), 1, S, p, field('Merge', p)['enum_name'], 'BLEND_Masked')
    p = 'HLODMaterial'
    cur = field('Merge', p)['object_path']
    bad(m.set_hlod_builder_asset_reference, obj('Merge'), 1, S, p, '', MATERIAL, confirm=True)
    bad(m.set_hlod_builder_asset_reference, obj('Merge'), 1, S, p, cur, '/Engine/BasicShapes/Cube.Cube', confirm=True)  # wrong class
    edit(m.set_hlod_builder_asset_reference, F(p), obj('Merge'), 1, S, p, cur, MATERIAL)
    assert field('Merge', p)['object_path'] == MATERIAL
    # No engine builder exposes FString/FName/int64 leaves: each typed setter refuses a leaf of another type.
    bad(m.set_hlod_builder_string, obj('Merge'), 1, S, 'MeshMergeSettings.LODSelectionType', 'x', 'y', confirm=True)
    bad(m.set_hlod_builder_name, obj('Merge'), 1, S, 'MeshMergeSettings.TargetLightMapResolution', 'x', 'y', confirm=True)
    bad(m.set_hlod_builder_int64, obj('Merge'), 1, S, 'MeshMergeSettings.TargetLightMapResolution', '512', '7', confirm=True)
    bad(m.set_hlod_builder_numeric, obj('Merge'), 1, S, 'MeshMergeSettings.NaniteSettings.DisplacementMaps', 0, 1, confirm=True)  # array
    a = L('Approx')
    p = 'MeshApproximationSettings.OutputType'
    edit(m.set_hlod_builder_enum, lambda: field('Approx', p), obj('Approx'), 3, a['builder_settings_path'], p, field('Approx', p)['enum_name'], 'MeshShapeOnly')
    # Parent chain and linked layer.
    bad(m.set_world_partition_hlod_parent, obj('Merge'), obj('Parent'), obj('Parent'), confirm=True)
    bad(m.set_world_partition_hlod_parent, obj('Merge'), '', obj('Merge'), confirm=True)          # self
    edit(m.set_world_partition_hlod_parent, lambda: L('Merge'), obj('Merge'), '', obj('Parent'))
    edit(m.set_world_partition_hlod_parent, lambda: L('Parent'), obj('Parent'), '', obj('Approx'))
    bad(m.set_world_partition_hlod_parent, obj('Approx'), '', obj('Merge'), confirm=True)          # cycle
    assert L('Merge')['parent_chain_count'] == 3, L('Merge')
    c = L('Custom')
    bad(m.set_world_partition_hlod_linked_layer, obj('Merge'), 1, '', obj('Linked'), confirm=True)  # not CustomHLODActor
    bad(m.set_world_partition_hlod_linked_layer, obj('Custom'), 5, obj('Merge'), obj('Linked'), confirm=True)
    edit(m.set_world_partition_hlod_linked_layer, lambda: L('Custom'), obj('Custom'), 5, '', obj('Linked'))
    assert L('Custom')['linked_layer_path'] == obj('Linked'), L('Custom')
    chain = ok(m.inspect_world_partition_hlod_linked_chain, obj('Custom'))
    assert obj('Linked') in json.dumps(chain), chain
    refs = ok(m.inspect_world_partition_hlod_layer_referencers, obj('Parent'))
    assert obj('Merge') in json.dumps(refs), refs
    refs = ok(m.inspect_world_partition_hlod_layer_referencers, obj('Linked'))
    assert obj('Custom') in json.dumps(refs), refs
    return {n: L(n)['layer_type_ordinal'] for n in LAYERS}


# ---------------------------------------------------------------- partition HLOD options, default layer, actor assignment
def partition_stage():
    W = wp()
    D = lambda: ok(m.inspect_partition_default_hlod_layer, W)['default_hlod_layer_path']
    cur = D()
    bad(m.set_partition_default_hlod_layer, W, obj('Merge'), obj('Merge'), confirm=True)
    bad(m.set_partition_default_hlod_layer, W, cur, '/Engine/BasicShapes/Cube.Cube', confirm=True)
    edit(m.set_partition_default_hlod_layer, D, W, cur, obj('Merge'))
    assert D() == obj('Merge')
    O = lambda: ok(m.inspect_partition_hlod_options, W)['options']
    opt = lambda f: next(o['authored_value'] for o in O() if o['field_name'] == f)
    v = opt('bAllowShowingHLODsInEditor')
    bad(m.set_partition_hlod_option, W, 'bAllowShowingHLODsInEditor', not v, v, confirm=True)
    edit(m.set_partition_hlod_option, O, W, 'bAllowShowingHLODsInEditor', v, not v)
    if not ok(m.inspect_partition_hlod_options, W)['standalone_hlod_allowed']:
        bad(m.set_partition_hlod_option, W, 'bHasStandaloneHLOD', False, True, confirm=True)
    # Actor HLOD-layer assignment and eligibility.
    path = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.StaticMeshActor',
                      'Location': {'X': 500, 'Y': 500, 'Z': 100}}, timeout=60).text
    save()
    d = next(x for s in range(0, 2048, 128) for x in ok(m.inspect_world_partition_actor_descriptors, s, 128)['actor_descriptors'] if x['actor_soft_path'] == path)
    grid = ok(m.inspect_partition_runtime_definitions, W)['definitions'][0]['grid_name']
    ge = ok(m.inspect_partition_runtime_grid_eligibility, W, grid, '/Script/Engine.StaticMeshActor')
    assert 'valid' in json.dumps(ge).lower(), ge
    # HashSet: only layers referenced by a runtime HLOD setup are eligible (the template's own instancing layer).
    TPL = MAP + '_HLOD0_Instancing.' + MAP.rsplit('/', 1)[1] + '_HLOD0_Instancing'
    assert not ok(m.inspect_partition_runtime_hlod_eligibility, W, grid, obj('Approx'))['native_hlod_layer_eligible']
    assert ok(m.inspect_partition_runtime_hlod_eligibility, W, grid, TPL)['native_hlod_layer_eligible']
    A = lambda: next(x for s in range(0, 2048, 128) for x in ok(m.inspect_world_partition_actor_descriptors, s, 128)['actor_descriptors'] if x['actor_soft_path'] == path)['loaded_actor_hlod_layer_path']
    args = (W, d['container_path'], d['guid'], path)
    cur = d['loaded_actor_hlod_layer_path']
    cur = '' if cur in ('None',) else cur
    bad(m.set_loaded_partition_actor_hlod_layer, *args, obj('Linked'), d['loaded_actor_runtime_grid'], TPL, confirm=True)
    if cur == TPL:
        edit(m.set_loaded_partition_actor_hlod_layer, A, *args, cur, d['loaded_actor_runtime_grid'], '')   # explicit clear
        cur = ''
    bad(m.set_loaded_partition_actor_hlod_layer, *args, cur, d['loaded_actor_runtime_grid'], obj('Approx'), confirm=True)   # not in a runtime setup
    edit(m.set_loaded_partition_actor_hlod_layer, A, *args, cur, d['loaded_actor_runtime_grid'], TPL)
    assert A() == TPL, A()
    # Streaming enable lifecycle: disable then re-enable.
    St = lambda: ok(m.inspect_partition_streaming, W)['authored_enable_streaming']
    save()
    bad(m.set_partition_streaming, W, False, False, confirm=True)
    edit(m.set_partition_streaming, St, W, True, False)
    save()
    edit(m.set_partition_streaming, St, W, False, True)
    return {'actor': path, 'default': D()}


# ---------------------------------------------------------------- RuntimeHashSet definitions
def defs():
    return ok(m.inspect_partition_runtime_definitions, wp(), 0, 128)


def main(i=0):
    d = defs()
    return d['runtime_hash_path'], d['definitions'][i]['main_layer'], d['definition_count']


def grid_stage():
    W = wp()
    H, M, n = main()
    G = lambda: main()[1]
    ids = lambda: (W, H, G()['path'], G()['name'], -1, n)
    bad(m.set_partition_runtime_definition_numeric, W, H, M['path'], M['name'], -1, n + 1, 'LoadingRange', M['loading_range'], 50000, confirm=True)
    bad(m.set_partition_runtime_definition_numeric, *ids(), 'CellSize', G()['cell_size'], 100, confirm=True)       # below 1600
    edit(m.set_partition_runtime_definition_numeric, G, *ids(), 'LoadingRange', G()['loading_range'], 51200)
    edit(m.set_partition_runtime_definition_numeric, G, *ids(), 'CellSize', G()['cell_size'], 12800)
    edit(m.set_partition_runtime_definition_numeric, G, *ids(), 'Priority', G()['priority'], -2)
    for f, k in (('bBlockOnSlowStreaming', 'block_on_slow_streaming'), ('bClientOnlyVisible', 'client_only_visible'), ('bIs2D', 'is_2d')):
        bad(m.set_partition_runtime_definition_bool, *ids(), f, not G()[k], G()[k], confirm=True)
        edit(m.set_partition_runtime_definition_bool, G, *ids(), f, G()[k], not G()[k])
    bad(m.set_partition_runtime_definition_bounds_mode, *ids(), G()['bounds_method'], 3, confirm=True)
    edit(m.set_partition_runtime_definition_bounds_mode, G, *ids(), G()['bounds_method'], 0)
    bad(m.set_partition_runtime_definition_origin, *ids(), [1, 1, 1], [100, 200, 0], confirm=True)
    edit(m.set_partition_runtime_definition_origin, G, *ids(), G()['origin'], [100, 200, 0])
    bad(m.set_partition_runtime_definition_debug_color, *ids(), [0, 0, 0, 0], [1, 0, 0, 1], confirm=True)
    bad(m.set_partition_runtime_definition_debug_color, *ids(), G()['debug_color'], [2, 0, 0, 1], confirm=True)
    edit(m.set_partition_runtime_definition_debug_color, G, *ids(), G()['debug_color'], [1, 0.5, 0, 1])
    flds = ok(m.inspect_partition_runtime_definition_fields, *ids())
    assert any(f['name'] == 'CellSize' for f in flds['fields']), flds
    bad(m.rename_partition_runtime_definition, *ids(), '', confirm=True)
    edit(m.rename_partition_runtime_definition, G, *ids(), 'MCPGrid')
    assert G()['name'] == 'MCPGrid'
    # HLOD setups: add two spatial setups before the trailing persistent one, reorder, remove, normalize.
    S = lambda: ok(m.inspect_partition_runtime_hlod_setups, W, H, G()['path'], G()['name'], n)['setups']
    paths = lambda: [s['definition_path'] for s in S()]
    bad(m.add_partition_runtime_hlod_setup, W, H, G()['path'], G()['name'], n, [], confirm=True)
    for _ in range(2):
        edit(m.add_partition_runtime_hlod_setup, S, W, H, G()['path'], G()['name'], n, paths())
    assert len(S()) == 3 and not S()[-1]['spatially_loaded'], S()
    sp = paths()
    bad(m.reorder_partition_runtime_hlod_setups, W, H, G()['path'], G()['name'], n, sp, [sp[2], sp[0], sp[1]], confirm=True)  # persistent must stay last
    edit(m.reorder_partition_runtime_hlod_setups, S, W, H, G()['path'], G()['name'], n, sp, [sp[1], sp[0], sp[2]])
    # Reference slots on the first spatial setup.
    s0 = S()[0]
    R = lambda: ok(m.inspect_partition_runtime_hlod_layer_references, W, H, s0['definition_path'], s0['definition_name'], s0['hlod_index'], n)['references']
    refs = [r['layer_path'] for r in R()] if R() and isinstance(R()[0], dict) else R()
    bad(m.replace_partition_runtime_hlod_layer_references, W, H, s0['definition_path'], s0['definition_name'], s0['hlod_index'], n, ['x'], [obj('Merge')], confirm=True)
    edit(m.replace_partition_runtime_hlod_layer_references, R, W, H, s0['definition_path'], s0['definition_name'], s0['hlod_index'], n, refs, [obj('Merge'), obj('Approx')])
    edit(m.set_partition_runtime_hlod_layer_reference, R, W, H, s0['definition_path'], s0['definition_name'], s0['hlod_index'], n, 1, obj('Approx'), obj('Linked'))
    bad(m.set_partition_runtime_hlod_layer_reference, W, H, s0['definition_path'], s0['definition_name'], s0['hlod_index'], n, 5, '', obj('Merge'), confirm=True)
    # Remove the second spatial setup, then normalize indices.
    sp = paths()
    s1 = S()[1]
    r1 = ok(m.inspect_partition_runtime_hlod_layer_references, W, H, s1['definition_path'], s1['definition_name'], s1['hlod_index'], n)['references']
    r1 = [r['layer_path'] for r in r1] if r1 and isinstance(r1[0], dict) else r1
    bad(m.remove_partition_runtime_hlod_setup, W, H, s1['definition_path'], s1['definition_name'], s1['hlod_index'], n, sp[::-1], r1, confirm=True)
    edit(m.remove_partition_runtime_hlod_setup, S, W, H, s1['definition_path'], s1['definition_name'], s1['hlod_index'], n, sp, r1)
    idx = [s['hlod_index'] for s in S() if s['spatially_loaded']]
    edit(m.normalize_partition_runtime_hlod_indices, S, W, H, G()['path'], G()['name'], n, paths(), [s['hlod_index'] for s in S()],
         changes=idx != list(range(len(idx))))
    rename_target = S()[0]
    edit(m.rename_partition_runtime_definition, S, W, H, rename_target['definition_path'], rename_target['definition_name'], rename_target['hlod_index'], n, 'MCPHLOD0')
    # Main definitions: add, reorder, replace class, remove.
    dp = lambda: [d['main_layer']['path'] for d in defs()['definitions']]
    classes = ok(m.inspect_partition_runtime_classes, W, 0, 128)['classes']
    selectable = [c['class_path'] for c in classes if c['adapter_selectable']]
    assert '/Script/Engine.RuntimePartitionLHGrid' in selectable, selectable
    bad(m.add_partition_runtime_main_definition, W, H, dp()[:0], 'Second', confirm=True)
    bad(m.add_partition_runtime_main_definition, W, H, dp(), 'MCPGrid', confirm=True)          # duplicate name
    edit(m.add_partition_runtime_main_definition, dp, W, H, dp(), 'Second')
    p = dp()
    edit(m.reorder_partition_runtime_main_definitions, dp, W, H, p, p[::-1])
    p = dp()
    second = next(i for i, d in enumerate(defs()['definitions']) if d['grid_name'] == 'Second')
    other = [c for c in selectable if c != '/Script/Engine.RuntimePartitionLHGrid']
    if other:
        cls = lambda: defs()['definitions'][second]['main_layer']['class_path']
        sd = defs()['definitions'][second]['main_layer']
        ss = ok(m.inspect_partition_runtime_hlod_setups, W, H, sd['path'], sd['name'], len(p))['setups']
        sp, sr = [s['definition_path'] for s in ss], [r for s in ss for r in s['hlod_layer_paths']]
        bad(m.replace_partition_runtime_main_class, W, H, p, second, 'Second', '/Script/Engine.RuntimePartitionLHGrid', other[0], [], sr, confirm=True)
        edit(m.replace_partition_runtime_main_class, cls, W, H, p, second, 'Second', '/Script/Engine.RuntimePartitionLHGrid', other[0], sp, sr)
    p = dp()
    edit(m.reorder_partition_runtime_main_definitions, dp, W, H, p, p[::-1])
    assert defs()['definitions'][0]['grid_name'] == 'MCPGrid', [d['grid_name'] for d in defs()['definitions']]
    # Remove 'Second' (never the last remaining definition).
    p = dp()
    i = next(k for k, d in enumerate(defs()['definitions']) if d['grid_name'] == 'Second')
    sd = defs()['definitions'][i]['main_layer']
    ss = ok(m.inspect_partition_runtime_hlod_setups, W, H, sd['path'], sd['name'], len(p))['setups']
    sp, sr = [s['definition_path'] for s in ss], [r for s in ss for r in s['hlod_layer_paths']]
    bad(m.remove_partition_runtime_main_definition, W, H, p, i, 'Wrong', sp, sr, confirm=True)
    edit(m.remove_partition_runtime_main_definition, dp, W, H, p, i, 'Second', sp, sr)
    assert len(dp()) == 1
    only = defs()['definitions'][0]['main_layer']
    os_ = ok(m.inspect_partition_runtime_hlod_setups, W, H, only['path'], only['name'], 1)['setups']
    bad(m.remove_partition_runtime_main_definition, W, H, dp(), 0, 'MCPGrid', [s['definition_path'] for s in os_],
        [r for s in os_ for r in s['hlod_layer_paths']], confirm=True)                       # at least one must remain
    keep = defs()['definitions']
    return {'classes': selectable, 'class_replaced': bool(other), 'definitions': [d['grid_name'] for d in keep]}


def snapshot(actor):
    W = wp()
    d = defs()
    H, M, n = d['runtime_hash_path'], d['definitions'][0]['main_layer'], d['definition_count']
    setups = ok(m.inspect_partition_runtime_hlod_setups, W, H, M['path'], M['name'], n)['setups']
    return {'layers': {k: {a: b for a, b in L(k).items() if a not in ('package_dirty', 'scope')} for k in LAYERS},
            'fields': {p: field('Merge', p) for p in ('MeshMergeSettings.TargetLightMapResolution', 'MeshMergeSettings.LODSelectionType', 'HLODMaterial',
                                                      'MeshMergeSettings.MaterialSettings.BlendMode', 'MeshMergeSettings.MaterialSettings.bAllowTwoSidedMaterial')},
            'definitions': [{k: v for k, v in x.items() if k != 'hlod_setups'} for x in d['definitions']],
            # The trailing persistent setup's generated object name is not stable across reloads; compare its values only.
            'setups': [{k: v for k, v in s.items() if s['spatially_loaded'] or k != 'definition_path'} for s in setups],
            'default': ok(m.inspect_partition_default_hlod_layer, W)['default_hlod_layer_path'],
            'options': ok(m.inspect_partition_hlod_options, W)['options'],
            'streaming': ok(m.inspect_partition_streaming, W)['authored_enable_streaming'],
            'actor_hlod': next(x for s in range(0, 2048, 128) for x in ok(m.inspect_world_partition_actor_descriptors, s, 128)['actor_descriptors'] if x['actor_soft_path'] == actor)['hlod_layer_path']}


def prepare():
    cleanup()
    out = {'layers': layer_stage()}
    assert ok(m.create_editor_world, MAP, TEMPLATE, True, 'discard', True)['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    save()
    out['partition'] = partition_stage()
    save()
    out['grids'] = grid_stage()
    save()
    actor = out['partition']['actor']
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'actor': actor, 'snapshot': snapshot(actor), 'stages': out}, indent=1))
    print('hlod and grids prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    for k in LAYERS:                                   # HLOD inspection requires loaded assets; a cold editor has not loaded them
        ok(m.get_asset_properties, obj(k))
    got = json.loads(json.dumps(snapshot(st['actor'])))
    want = st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('hlod and grids identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    for p in [MAP, MAP + '_HLOD0_Instancing', *LAYERS.values()]:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
