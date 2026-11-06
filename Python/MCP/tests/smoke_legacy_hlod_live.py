"""Legacy (non-partition) HLOD setup authoring on an ordinary scratch map: prepare, restart, verify.

Usage: smoke_legacy_hlod_live.py prepare|verify|cleanup. Drives the local HierarchicalLODSetup tools: level append,
duplicate, reorder, removal and native-default reset with full snapshot guards; top-level numeric/bool/simplification
method; nested field discovery and nested numeric (float/int/double), bool, enum (EnumProperty and TEnumAsByte), FIntPoint
and color leaves (name/string/object setters refuse non-matching leaves); setup-class discovery and override; base
material override; World Settings single-cluster and HLOD baking transform; manual HLOD cluster volume creation and
overlap/tier policy. Each edit is rejected with a stale expected value, dry-run checked, then applied. Authored state
must survive a cold editor restart.
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
W = '/Game/UE5MCP_Test/MCP_LegacyHLOD'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'legacy_hlod.json'
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


def levels():
    return ok(m.inspect_world_legacy_hlod_levels, W, 0, 128)


def texts():
    return [l['native_snapshot_text'] for l in levels()['levels']]


def n():
    return levels()['local_level_count']


def fld(level, path):
    struct, _, name = path.rpartition('.')
    fs = ok(m.inspect_world_legacy_hlod_fields, W, level, n(), struct, 0, 128)['fields']
    return next(f for f in fs if f['name'] == name)


def val(level, path):
    return fld(level, path)['native_text']


TOP = {'TransitionScreenSize': 'transition_screen_size', 'OverrideDrawDistance': 'override_draw_distance',
       'DesiredBoundRadius': 'desired_bound_radius', 'DesiredFillingPercentage': 'desired_filling_percentage',
       'MinNumberOfActorsToBuild': 'min_actors_to_build'}


def top(level, f):
    """Exact native top-level value (field text is rounded to 6 digits)."""
    return levels()['levels'][level][TOP[f]]


# ---------------------------------------------------------------- structural edits
def structure_stage():
    assert n() == 0, levels()
    bad(m.add_world_legacy_hlod_level, W, 1, confirm=True, dry_run=False)
    bad(m.add_world_legacy_hlod_level, W, 0, dry_run=False)                          # confirmation required
    edit(m.add_world_legacy_hlod_level, texts, W, 0, expected_level_texts=[])
    edit(m.add_world_legacy_hlod_level, texts, W, 1, expected_level_texts=texts())
    assert n() == 2 and levels()['stored_num_hlod_levels'] == 2, levels()
    bad(m.add_world_legacy_hlod_level, W, 2, confirm=True, dry_run=False, expected_level_texts=['x', 'y'])
    # Make level 1 distinct, duplicate it, reorder, remove.
    edit(m.set_world_legacy_hlod_numeric, texts, W, 1, 2, 'TransitionScreenSize', top(1, 'TransitionScreenSize'), 0.125, expected_level_text=texts()[1])
    bad(m.duplicate_world_legacy_hlod_level, W, 5, 2, confirm=True, dry_run=False, expected_level_texts=texts())
    edit(m.duplicate_world_legacy_hlod_level, texts, W, 1, 2, expected_level_texts=texts())
    assert n() == 3 and texts()[2] == texts()[1], texts()
    t = texts()
    bad(m.reorder_world_legacy_hlod_levels, W, 3, [0, 0, 1], confirm=True, dry_run=False, expected_level_texts=t)
    bad(m.reorder_world_legacy_hlod_levels, W, 3, [2, 0, 1], confirm=True, dry_run=False, expected_level_texts=t[::-1])
    edit(m.reorder_world_legacy_hlod_levels, texts, W, 3, [1, 0, 2], expected_level_texts=t)
    assert texts() == [t[1], t[0], t[2]]
    edit(m.remove_world_legacy_hlod_level, texts, W, 2, 3, expected_level_texts=texts())
    assert n() == 2
    # Reset level 0 (the edited one) to native defaults.
    t = texts()
    bad(m.reset_world_legacy_hlod_level, W, 0, 2, t[1] + 'X', confirm=True, dry_run=False)
    edit(m.reset_world_legacy_hlod_level, texts, W, 0, 2, t[0])
    assert abs(top(0, 'TransitionScreenSize') - 0.315) < 1e-6, texts()        # native default restored
    return n()


# ---------------------------------------------------------------- top-level and nested leaves on level 1
def leaf_stage():
    L = 1
    T = lambda: texts()[L]
    for f, v in (('TransitionScreenSize', 0.2), ('OverrideDrawDistance', 25000), ('DesiredBoundRadius', 3000),
                 ('DesiredFillingPercentage', 75), ('MinNumberOfActorsToBuild', 3)):
        cur = top(L, f)
        bad(m.set_world_legacy_hlod_numeric, W, L, 2, f, cur + 1, v, confirm=True, dry_run=False, expected_level_text=T())
        bad(m.set_world_legacy_hlod_numeric, W, L, 3, f, cur, v, confirm=True, dry_run=False, expected_level_text=T())
        edit(m.set_world_legacy_hlod_numeric, T, W, L, 2, f, cur, v, expected_level_text=T())
    bad(m.set_world_legacy_hlod_numeric, W, L, 2, 'TransitionScreenSize', top(L, 'TransitionScreenSize'), 5, confirm=True, dry_run=False, expected_level_text=T())  # clamp 1.0
    for f in ('bUseOverrideDrawDistance', 'bAllowSpecificExclusion', 'bOnlyGenerateClustersForVolumes', 'bReusePreviousLevelClusters'):
        cur = val(L, f) == 'True'
        bad(m.set_world_legacy_hlod_boolean, W, L, 2, f, not cur, cur, confirm=True, dry_run=False, expected_level_text=T())
        edit(m.set_world_legacy_hlod_boolean, T, W, L, 2, f, cur, not cur, expected_level_text=T())
    methods = {'None': 0, 'Merge': 1, 'Simplify': 2, 'Approximate': 3}
    cur = methods[val(L, 'SimplificationMethod')]
    bad(m.set_world_legacy_hlod_method, W, L, 2, cur, 9, confirm=True, dry_run=False, expected_level_text=T())
    edit(m.set_world_legacy_hlod_method, T, W, L, 2, cur, 3 if cur != 3 else 2, expected_level_text=T())
    # Nested leaves.
    for p, v in (('ProxySetting.ScreenSize', 600), ('ProxySetting.MaterialSettings.MeshMinDrawDistance', 5000),
                 ('MergeSetting.TargetLightMapResolution', 512)):
        cur = float(val(L, p))
        bad(m.set_world_legacy_hlod_nested_numeric, W, L, 2, p, cur + 1, v, confirm=True, dry_run=False, expected_level_text=T())
        edit(m.set_world_legacy_hlod_nested_numeric, T, W, L, 2, p, cur, v, expected_level_text=T())
    bad(m.set_world_legacy_hlod_nested_numeric, W, L, 2, 'ProxySetting.ScreenSize', 600, 5000, confirm=True, dry_run=False, expected_level_text=T())  # clamp 1200
    p = 'ProxySetting.bRecalculateNormals'
    cur = val(L, p) == 'True'
    edit(m.set_world_legacy_hlod_nested_boolean, T, W, L, 2, p, cur, not cur, expected_level_text=T())
    p = 'ProxySetting.MaterialSettings.TextureSizingType'                                     # TEnumAsByte
    edit(m.set_world_legacy_hlod_nested_enum, T, W, L, 2, p, 0, 1, expected_level_text=T())
    bad(m.set_world_legacy_hlod_nested_enum, W, L, 2, p, 1, 99, confirm=True, dry_run=False, expected_level_text=T())
    p = 'ProxySetting.MaterialSettings.TextureSize'
    edit(m.set_world_legacy_hlod_nested_enum, T, W, L, 2, 'ProxySetting.MaterialSettings.TextureSizingType', 1, 0, expected_level_text=T())
    bad(m.set_world_legacy_hlod_nested_int_point, W, L, 2, p, [1, 1], [512, 512], confirm=True, dry_run=False, expected_level_text=T())
    edit(m.set_world_legacy_hlod_nested_int_point, T, W, L, 2, p, [1024, 1024], [512, 256], expected_level_text=T())
    assert 'TextureSize=(X=512,Y=256)' in T(), T()
    # FColor leaf: the color setter targets linear colors; record whether it accepts byte colors.
    p = 'ProxySetting.UnresolvedGeometryColor'
    color = J(m.set_world_legacy_hlod_nested_color(W, L, 2, p, [0, 0, 0, 1], [1, 0, 0, 1], confirm=True, dry_run=True, expected_level_text=T()))
    # No local HLOD leaf is an FName, FString or object reference: each setter refuses other leaf types.
    bad(m.set_world_legacy_hlod_nested_name, W, L, 2, 'ProxySetting.ScreenSize', '600', 'X', confirm=True, dry_run=False, expected_level_text=T())
    bad(m.set_world_legacy_hlod_nested_string, W, L, 2, 'ProxySetting.ScreenSize', '600', 'X', confirm=True, dry_run=False, expected_level_text=T())
    bad(m.set_world_legacy_hlod_nested_object, W, L, 2, 'ProxySetting.ScreenSize', '', MATERIAL, confirm=True, dry_run=False, expected_level_text=T())
    return {'color_setter_accepts_fcolor': 'errorMessage' not in color, 'text': T()}


# ---------------------------------------------------------------- setup class, base material, World Settings, cluster volume
def settings_stage():
    O = lambda: {k: levels()[k] for k in ('setup_override_soft_class_path', 'base_material_override_soft_path')}
    classes = ok(m.inspect_world_legacy_hlod_setup_classes, W, 0, 128)['classes']
    base = next(c for c in classes if c['class_path'] == '/Script/Engine.HierarchicalLODSetup')
    assert base['selectable'], base
    bad(m.set_world_legacy_hlod_setup_override, W, '/Script/Engine.Actor', '/Script/Engine.HierarchicalLODSetup', confirm=True, dry_run=False)
    bad(m.set_world_legacy_hlod_setup_override, W, '', '/Script/Engine.Actor', confirm=True, dry_run=False)
    edit(m.set_world_legacy_hlod_setup_override, O, W, '', '/Script/Engine.HierarchicalLODSetup')
    # Local level edits are refused while a setup override is active.
    bad(m.set_world_legacy_hlod_numeric, W, 1, 2, 'TransitionScreenSize', top(1, 'TransitionScreenSize'), 0.3, confirm=True, dry_run=False, expected_level_text=texts()[1])
    edit(m.set_world_legacy_hlod_setup_override, O, W, '/Script/Engine.HierarchicalLODSetup', '')
    FLATTEN = '/Engine/EngineMaterials/FlattenMaterial.FlattenMaterial'
    bad(m.set_world_legacy_hlod_material_override, W, FLATTEN, FLATTEN, confirm=True, dry_run=False)
    bad(m.set_world_legacy_hlod_material_override, W, '', '/Engine/BasicShapes/Cube.Cube', confirm=True, dry_run=False)
    bad(m.set_world_legacy_hlod_material_override, W, '', MATERIAL, confirm=True, dry_run=False)   # not a flatten material
    edit(m.set_world_legacy_hlod_material_override, O, W, '', FLATTEN)
    # World Settings single-cluster flag and HLOD baking transform.
    S = lambda: {k: v for k, v in ok(m.inspect_editor_world_settings).items() if k in ('bool_settings', 'transform_settings')}
    ws = ok(m.inspect_editor_world_settings)
    single = ws['bool_settings']['bGenerateSingleClusterForLevel']
    edit(m.set_editor_world_settings, S, world_path=W, bool_settings={'bGenerateSingleClusterForLevel': not single},
         expected_bool_settings={'bGenerateSingleClusterForLevel': single})
    key = 'HLODBakingTransform' if 'HLODBakingTransform' in ws['transform_settings'] else next(iter(ws['transform_settings']))
    cur = ws['transform_settings'][key]
    new = {'Translation': {'X': 10, 'Y': 20, 'Z': 30}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 2, 'Y': 2, 'Z': 2}}
    bad(m.set_editor_world_settings, world_path=W, transform_settings={key: new}, confirm=True)                  # full expected map required
    edit(m.set_editor_world_settings, S, world_path=W, transform_settings={key: new}, expected_transform_settings={key: cur})
    # Manual HLOD cluster volume.
    r = ok(m.create_box_volume, 'HierarchicalLOD', 'MCP_HLODVol', [0, 0, 0], [500, 500, 500], confirm=True)
    A = r['actor_path']
    V = lambda: ok(m.inspect_hlod_cluster_volume, A)
    v = V()
    inv = next(x for x in ok(m.inspect_world_volume_page, 0, 128)['volumes'] if x['actor_path'] == A)
    g, lab = inv['actor_guid'], inv['label']
    ov, lv = v['include_overlapping_actors'] if 'include_overlapping_actors' in v else v['overlap'], v.get('hlod_levels', v.get('applies_to_levels', []))
    bad(m.set_hlod_cluster_volume_policy, A, g, lab, not ov, ov, lv, lv, confirm=True, dry_run=False)
    bad(m.set_hlod_cluster_volume_policy, A, g, lab, ov, ov, lv, [1, 1], confirm=True, dry_run=False)
    edit(m.set_hlod_cluster_volume_policy, V, A, g, lab, ov, not ov, lv, [0, 1])
    return {'overrides': O(), 'volume': V()}


def snapshot():
    ws = ok(m.inspect_editor_world_settings)
    vol = next((x['actor_path'] for x in ok(m.inspect_world_volume_page, 0, 128)['volumes'] if x['actor_path'].endswith('.MCP_HLODVol')), None)
    return {'levels': {k: v for k, v in levels().items() if k not in ('scope', 'package_dirty')},
            'single': ws['bool_settings']['bGenerateSingleClusterForLevel'], 'transform': ws['transform_settings'],
            'volume': {k: v for k, v in ok(m.inspect_hlod_cluster_volume, vol).items() if k not in ('scope', 'package_dirty')} if vol else None}


def prepare():
    cleanup()
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': W, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': W, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    out = {'structure': structure_stage(), 'leaves': leaf_stage(), 'settings': settings_stage()}
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': W, 'bConfirm': True}, timeout=600).json()['success']
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot(), 'stages': out}, indent=1))
    print('legacy hlod prepared; map saved; fcolor via color setter:', out['leaves']['color_setter_accepts_fcolor'])


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': W, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot()))
    want = st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('legacy hlod identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': W}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
