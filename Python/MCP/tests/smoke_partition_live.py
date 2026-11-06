"""World Partition descriptors, editor regions, actor flags, pins, streaming sources and LocationVolumes: prepare, restart, verify.

Usage: smoke_partition_live.py prepare|verify|cleanup. Copies the engine OpenWorld template to a scratch map, spawns
external actors and drives the partition MCP tools: descriptor pages/single lookup/references/box query, containers,
runtime cells, editor-region create/load/unload/release, spatial-loading flag, runtime grid, actor pins (single and
batch), streaming-source component create/enable/enums/target grids/shapes/debug color/visualizer range/previews/remove,
and LocationVolume creation/inspection/debug color/loading/brush replacement. Each edit is rejected with a stale expected
value, dry-run checked, then applied. Authored state must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, STAGE_ARGS, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), sys.argv[2:], []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
MAP = '/Game/UE5MCP_Test/MCP_Partition'
TEMPLATE = '/Engine/Maps/Templates/OpenWorld'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'partition.json'
ACTORS = {}   # 'MCP_A'/'MCP_B' -> spawned actor path


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


def save():
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']


def wp():
    return ok(m.inspect_world_partition)['partition_path']


def descriptors():
    out, start = [], 0
    while True:
        page = ok(m.inspect_world_partition_actor_descriptors, start, 128)
        out += page['actor_descriptors']
        if not page['has_more']:
            return out
        start = page['next_start']


def desc(label):
    return next(d for d in descriptors() if d['actor_soft_path'] == ACTORS[label])


def spawn(label, location):
    path = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.StaticMeshActor',
                      'Location': dict(zip('XYZ', location))}, timeout=60).text
    assert path.startswith(MAP), path
    ACTORS[label] = path
    return path


class Actor:
    """Descriptor identity for an actor addressed by label."""
    def __init__(self, label):
        d = desc(label)
        self.label, self.guid, self.container, self.path = label, d['guid'], d['container_path'], d['actor_soft_path']

    def d(self):
        return ok(m.inspect_world_partition_actor_descriptor, wp(), self.container, self.guid)


# ---------------------------------------------------------------- descriptors, containers, cells, box query
def descriptor_stage():
    W = wp()
    a, b = Actor('MCP_A'), Actor('MCP_B')
    d = a.d()
    assert d['actor_soft_path'] == ACTORS['MCP_A'] and d['loaded'] and d['spatially_loaded'], d
    bad(m.inspect_world_partition_actor_descriptor, W, a.container, '0' * 32)
    bad(m.inspect_world_partition_actor_descriptor, W, a.container + 'X', a.guid)
    page = ok(m.inspect_world_partition_actor_descriptors, 0, 5)
    assert len(page['actor_descriptors']) == 5 and page['has_more'], page['next_start']
    bad(m.inspect_world_partition_actor_descriptors, 0, 0)
    conts = ok(m.inspect_world_partition_containers, 0, 64, True)
    assert any(c['container_path'] == a.container for c in conts['containers']), conts
    cells = ok(m.inspect_world_partition_runtime_cells, 0, 8)
    assert isinstance(cells['runtime_cells'], list)
    # Box query: raw descriptor cursor, so walk every page and collect matches.
    def box(center, extent):
        found, start = [], 0
        while True:
            r = ok(m.inspect_world_partition_box_actors, W, center, extent, start, 128)
            found += [x['actor_soft_path'] for x in r['actor_descriptors']]
            if not r['has_more']:
                return found
            start = r['next_start']
    near = box([500, 500, 100], [200, 200, 200])
    assert ACTORS['MCP_A'] in near and ACTORS['MCP_B'] not in near, near
    assert ACTORS['MCP_B'] in box([-20000, 3000, 100], [200, 200, 200])
    bad(m.inspect_world_partition_box_actors, W, [0, 0, 0], [0, 1, 1])
    refs = ok(m.inspect_world_partition_actor_references, W, a.container, a.guid)
    assert isinstance(refs.get('references', []), list), refs
    ok(m.inspect_world_partition_actor_references, W, a.container, a.guid, editor_only=True)
    return {'a': d['actor_soft_path'], 'containers': conts['emitted_count'] if 'emitted_count' in conts else len(conts['containers'])}


# ---------------------------------------------------------------- spatial-loading flag and runtime grid
def flags_stage():
    W = wp()
    a = Actor('MCP_B')
    # Descriptors lag unsaved edits; the loaded actor's authored values are read back live.
    D = lambda: {'spatially_loaded': a.d()['loaded_actor_spatial_authored'], 'runtime_grid': a.d()['loaded_actor_runtime_grid']}
    bad(m.set_loaded_partition_actor_spatial, W, a.container, a.guid, a.path, False, False, confirm=True)
    bad(m.set_loaded_partition_actor_spatial, W, a.container, '0' * 32, a.path, True, False, confirm=True)
    edit(m.set_loaded_partition_actor_spatial, D, W, a.container, a.guid, a.path, True, False)
    assert D()['spatially_loaded'] is False, D()
    edit(m.set_loaded_partition_actor_spatial, D, W, a.container, a.guid, a.path, False, False, changes=False)
    edit(m.set_loaded_partition_actor_spatial, D, W, a.container, a.guid, a.path, False, True)
    grid = ok(m.inspect_partition_runtime_definitions, W)['definitions'][0]['grid_name']
    cur = D()['runtime_grid']
    bad(m.set_loaded_partition_actor_runtime_grid, W, a.container, a.guid, a.path, 'Wrong', grid, confirm=True)
    bad(m.set_loaded_partition_actor_runtime_grid, W, a.container, a.guid, a.path, cur, 'x' * 129, confirm=True)
    edit(m.set_loaded_partition_actor_runtime_grid, D, W, a.container, a.guid, a.path, cur, grid)
    assert D()['runtime_grid'] == grid, D()
    return D()


# ---------------------------------------------------------------- editor regions
def regions_stage():
    W = wp()
    R = lambda: ok(m.inspect_world_partition_editor_regions, 0, 128)
    n = R()['registered_adapter_count']
    center, extent = [500, 500, 0], [1000, 1000, 1000]
    bad(m.create_world_partition_editor_region, W, n + 1, 'MCP_Region', center, extent, confirm=True)
    bad(m.create_world_partition_editor_region, W, n, 'MCP_Region', center, [0, 1, 1], confirm=True)
    bad(m.create_world_partition_editor_region, W, n, 'MCP_Region', center, extent)               # confirmation required
    d = ok(m.create_world_partition_editor_region, W, n, 'MCP_Region', center, extent, confirm=True, dry_run=True)
    assert R()['registered_adapter_count'] == n, d
    ok(m.create_world_partition_editor_region, W, n, 'MCP_Region', center, extent, confirm=True)
    regs = R()['editor_regions']
    reg = next(r for r in regs if r['label'] == 'MCP_Region')
    assert R()['registered_adapter_count'] == n + 1 and not reg['loaded'] and reg['user_created'], reg
    c, e = reg['bounds_center'], reg['bounds_extent']
    A = reg['adapter_path']
    state = lambda: next(r for r in R()['editor_regions'] if r['adapter_path'] == A)['loaded']
    bad(m.load_world_partition_editor_region, W, A, n + 1, True, 'MCP_Region', c, e, confirm=True)
    bad(m.load_world_partition_editor_region, W, A, n + 1, False, 'Other', c, e, confirm=True)
    edit(m.load_world_partition_editor_region, state, W, A, n + 1, False, 'MCP_Region', c, e)
    assert state()
    bad(m.release_unloaded_world_partition_editor_region, W, A, n + 1, 'MCP_Region', c, e, confirm=True)  # loaded adapters refused
    blocked = ok(m.unload_world_partition_editor_region, W, A, n + 1, True, 'MCP_Region', c, e, confirm=True, dry_run=True)
    print('unload dry-run blockers:', str({k: v for k, v in blocked.items() if 'dirty' in k})[:300])
    save()                                                                         # unload needs globally clean packages
    edit(m.unload_world_partition_editor_region, state, W, A, n + 1, True, 'MCP_Region', c, e)
    assert not state()
    count = lambda: R()['registered_adapter_count']
    bad(m.release_unloaded_world_partition_editor_region, W, A, n + 1, 'MCP_Region', c, [1, 1, 1], confirm=True)
    edit(m.release_unloaded_world_partition_editor_region, count, W, A, n + 1, 'MCP_Region', c, e)
    assert count() == n and all(r['adapter_path'] != A for r in R()['editor_regions'])
    return True


# ---------------------------------------------------------------- pins
def pins_stage():
    W = wp()
    a, b = Actor('MCP_A'), Actor('MCP_B')
    P = lambda x: ok(m.inspect_partition_actor_pin, W, x.container, x.guid)
    pin = lambda x: P(x)['pinned']
    for x in (a, b):                                   # the editor pins newly spawned partition actors
        if pin(x):
            edit(m.set_partition_actor_pin, lambda: pin(x), W, x.container, x.guid, x.path, True, False, P(x)['loaded'])
    assert not pin(a) and not pin(b)
    loaded = P(a)['loaded']
    bad(m.set_partition_actor_pin, W, a.container, a.guid, a.path, True, True, loaded, confirm=True)
    bad(m.set_partition_actor_pin, W, a.container, a.guid, a.path, False, True, not loaded, confirm=True)
    edit(m.set_partition_actor_pin, lambda: pin(a), W, a.container, a.guid, a.path, False, True, loaded)
    assert pin(a)
    listed = ok(m.inspect_partition_actor_pins, W, True, 0, 128)
    assert a.guid in [x['guid'] for x in listed['actor_descriptors']], listed
    edit(m.set_partition_actor_pin, lambda: pin(a), W, a.container, a.guid, a.path, True, True, P(a)['loaded'], changes=False)
    entries = lambda pinned: [{'ContainerPath': x.container, 'ActorGuid': x.guid, 'ActorPath': x.path,
                               'bExpectedPinned': pinned[i], 'bExpectedLoaded': P(x)['loaded']} for i, x in enumerate((a, b))]
    both = lambda: (pin(a), pin(b))
    bad(m.set_partition_actor_pins, W, entries([False, False]), True, confirm=True)             # a is pinned
    bad(m.set_partition_actor_pins, W, entries([True, False]) * 2, True, confirm=True)          # duplicate GUIDs
    edit(m.set_partition_actor_pins, both, W, entries([True, False]), True)
    assert both() == (True, True)
    edit(m.set_partition_actor_pins, both, W, entries([True, True]), False)
    assert both() == (False, False)
    return True


# ---------------------------------------------------------------- streaming-source components
def sources_stage():
    W = wp()
    a = Actor('MCP_A')
    pin = ok(m.inspect_partition_actor_pin, W, a.container, a.guid)
    if not pin['loaded']:                              # unpinned actors outside a loaded region are unloaded
        ok(m.set_partition_actor_pin, W, a.container, a.guid, a.path, pin['pinned'], True, False, confirm=True)
    S = lambda: [s for s in ok(m.inspect_partition_streaming_source_components, W, 0, 128)['components'] if s['actor_guid'] == a.guid]
    n = len(ok(m.inspect_partition_streaming_source_components, W, 0, 128)['components'])
    bad(m.create_partition_streaming_source_component, W, a.container, a.guid, a.path, 'MCP_Src', n + 1, confirm=True)
    bad(m.create_partition_streaming_source_component, W, a.container, a.guid, a.path, 'MCP_Src', n)    # confirmation required
    for name in ('MCP_Src', 'MCP_Src2'):
        before = S()
        ok(m.create_partition_streaming_source_component, W, a.container, a.guid, a.path, name, n, confirm=True, dry_run=True)
        assert S() == before
        ok(m.create_partition_streaming_source_component, W, a.container, a.guid, a.path, name, n, confirm=True)
        n += 1
    bad(m.create_partition_streaming_source_component, W, a.container, a.guid, a.path, 'MCP_Src', n, confirm=True)  # duplicate name
    comp = next(s for s in S() if s['component_path'].endswith('.MCP_Src'))
    C = comp['component_path']
    cur = lambda: next(s for s in S() if s['component_path'] == C)
    en = cur()['enabled']
    bad(m.set_partition_streaming_source_enabled, W, C, a.path, a.guid, not en, en, confirm=True)
    edit(m.set_partition_streaming_source_enabled, cur, W, C, a.path, a.guid, en, not en)
    edit(m.set_partition_streaming_source_enabled, cur, W, C, a.path, a.guid, not en, en)
    for field, key, val in (('Priority', 'priority', 192), ('TargetBehavior', 'target_behavior', None), ('TargetState', 'target_state', None)):
        val = 1 - cur()[key] if val is None else val
        bad(m.set_partition_streaming_source_enum, W, C, a.path, a.guid, field, cur()[key] + 1, val, confirm=True)
        edit(m.set_partition_streaming_source_enum, cur, W, C, a.path, a.guid, field, cur()[key], val)
        assert cur()[key] == val, (field, cur())
    bad(m.set_partition_streaming_source_enum, W, C, a.path, a.guid, 'Priority', 192, 100, confirm=True)   # not a native priority
    beh = cur()['target_behavior']
    bad(m.replace_partition_streaming_source_target_grids, W, C, a.path, a.guid, beh, ['X'], ['MainGrid'], confirm=True)
    bad(m.replace_partition_streaming_source_target_grids, W, C, a.path, a.guid, beh, [], ['A', 'A'], confirm=True)
    edit(m.replace_partition_streaming_source_target_grids, cur, W, C, a.path, a.guid, beh, [], ['MainGrid', 'Other'])
    edit(m.replace_partition_streaming_source_target_grids, cur, W, C, a.path, a.guid, beh, ['MainGrid', 'Other'], ['Other', 'MainGrid'])
    pv = ok(m.preview_partition_streaming_source_grid_filter, W, C, a.path, a.guid, ['MainGrid', 'Third'])
    flat = json.dumps(pv)
    assert 'MainGrid' in flat and 'Third' in flat, flat[:400]
    shapes = lambda: [s['shape'] for s in ok(m.inspect_partition_streaming_source_shapes, W, C, a.path, a.guid)['shapes']]
    en = cur()['enabled']
    sh = [{'bUseGridLoadingRange': False, 'LoadingRangeScale': 1, 'Radius': 5000, 'bIsSector': False, 'SectorAngle': 360,
           'Location': {'X': 0, 'Y': 0, 'Z': 0}, 'Rotation': {'Pitch': 0, 'Yaw': 0, 'Roll': 0}},
          {'bUseGridLoadingRange': True, 'LoadingRangeScale': 0.5, 'Radius': 0, 'bIsSector': True, 'SectorAngle': 90,
           'Location': {'X': 1000, 'Y': 0, 'Z': 0}, 'Rotation': {'Pitch': 0, 'Yaw': 45, 'Roll': 0}}]
    bad(m.replace_partition_streaming_source_shapes, W, C, a.path, a.guid, en, sh, sh, confirm=True)
    bad(m.replace_partition_streaming_source_shapes, W, C, a.path, a.guid, en, [], [{**sh[0], 'SectorAngle': 400}], confirm=True)
    edit(m.replace_partition_streaming_source_shapes, shapes, W, C, a.path, a.guid, en, shapes(), sh)
    assert len(shapes()) == 2 and shapes()[1]['bIsSector'], shapes()
    prev = ok(m.preview_partition_streaming_source_shapes, W, C, a.path, a.guid, 25600)
    assert len(prev.get('shapes', [])) == 2, prev
    edit(m.replace_partition_streaming_source_shapes, shapes, W, C, a.path, a.guid, en, shapes(), shapes()[::-1])
    col = cur()['debug_color_bytes']
    bad(m.set_partition_streaming_source_debug_color, W, C, a.path, a.guid, [1, 2, 3, 4], [255, 0, 0, 255], confirm=True)
    edit(m.set_partition_streaming_source_debug_color, cur, W, C, a.path, a.guid, col, [255, 128, 0, 255])
    rng = cur()['visualizer_loading_range']
    bad(m.set_partition_streaming_source_visualizer_range, W, C, a.path, a.guid, rng + 1, 9000, confirm=True)
    bad(m.set_partition_streaming_source_visualizer_range, W, C, a.path, a.guid, rng, -1, confirm=True)
    edit(m.set_partition_streaming_source_visualizer_range, cur, W, C, a.path, a.guid, rng, 9000)
    # Remove the second source.
    s2 = next(s for s in S() if s['component_path'].endswith('.MCP_Src2'))
    total = lambda: len(ok(m.inspect_partition_streaming_source_components, W, 0, 128)['components'])
    args = (W, s2['component_path'], a.path, a.guid, total(), s2['enabled'], s2['shape_count'], len(s2['target_grids']))
    bad(m.remove_partition_streaming_source_component, *args[:4], total() + 1, *args[5:], confirm=True)
    edit(m.remove_partition_streaming_source_component, total, *args)
    assert len(S()) == 1
    return cur()


# ---------------------------------------------------------------- LocationVolume
def location_stage():
    W = wp()
    L = lambda: ok(m.inspect_partition_location_volumes, W, 0, 128)['volumes']
    bad(m.create_box_volume, 'Trigger', 'MCP_Trig', [0, 0, 0], [100, 100, 100], confirm=True)          # partition is Location-only
    ok(m.create_box_volume, 'Location', 'MCP_Loc', [500, 500, 0], [800, 800, 800], confirm=True, dry_run=True)
    assert not L()
    r = ok(m.create_box_volume, 'Location', 'MCP_Loc', [500, 500, 0], [800, 800, 800], confirm=True)
    ok(m.create_cylinder_volume, 'Location', 'MCP_LocCyl', [-3000, 0, 0], 600, 1200, confirm=True, dry_run=False)
    ok(m.create_sphere_volume, 'Location', 'MCP_LocSph', [-6000, 0, 0], 600, confirm=True, dry_run=False)
    ok(m.create_cone_volume, 'Location', 'MCP_LocCone', [-9000, 0, 0], 600, 1200, confirm=True, dry_run=False)
    assert len(L()) == 4, L()
    v = lambda: next(x for x in L() if x['actor_path'] == r['actor_path'])
    x = v()
    A, G, lab = x['actor_path'], x['actor_guid'], x['label']
    held = x['loaded_hold']
    col = x['debug_color_bytes']
    bad(m.set_partition_location_volume_debug_color, W, A, G, lab, held, [9, 9, 9, 9], [0, 255, 0, 255], confirm=True)
    bad(m.set_partition_location_volume_debug_color, W, A, G, lab, not held, col, [0, 255, 0, 255], confirm=True)
    edit(m.set_partition_location_volume_debug_color, v, W, A, G, lab, held, col, [0, 255, 0, 255])
    save()                                                                                            # loading needs clean packages
    x = v()
    c, e = x['bounds_center'], x['bounds_extent']
    loaded = lambda: v()['loaded_hold']
    bad(m.set_partition_location_volume_loading, W, A, G, lab, c, e, not held, not held, confirm=True)
    bad(m.set_partition_location_volume_loading, W, A, G, lab, c, [1, 1, 1], held, not held, confirm=True)
    edit(m.set_partition_location_volume_loading, loaded, W, A, G, lab, c, e, held, not held)
    edit(m.set_partition_location_volume_loading, loaded, W, A, G, lab, c, e, not held, held)
    # Unheld partition LocationVolume brush replacement.
    b = ok(m.inspect_volume_brush_builder, A)
    bad(m.replace_volume_brush_shape, A, G, lab, b['model_path'], b['polygon_count'], 'Sphere', [700, 700, 700], confirm=True, dry_run=False)   # partition_path required
    if not held:
        ok(m.replace_volume_brush_shape, A, G, lab, b['model_path'], b['polygon_count'], 'Sphere', [700, 700, 700], tessellation=2, confirm=True, dry_run=True, partition_path=W)
        ok(m.replace_volume_brush_shape, A, G, lab, b['model_path'], b['polygon_count'], 'Sphere', [700, 700, 700], tessellation=2, confirm=True, dry_run=False, partition_path=W)
        assert ok(m.inspect_volume_brush_builder, A)['shape'] == 'Sphere'
    return {'held_initially': held, 'volumes': len(L())}


def snapshot():
    W = wp()
    out = {}
    for lab in ('MCP_A', 'MCP_B'):
        d = Actor(lab).d()
        out[lab] = {k: d[k] for k in ('guid', 'actor_soft_path', 'native_class_path', 'runtime_grid', 'spatially_loaded')}
    out['sources'] = sorted(({k: v for k, v in s.items() if k not in ('registered',)} for s in ok(m.inspect_partition_streaming_source_components, W, 0, 128)['components']),
                            key=lambda s: s['component_path'])
    for s in out['sources']:
        s['shapes'] = [x['shape'] for x in ok(m.inspect_partition_streaming_source_shapes, W, s['component_path'], s['actor_path'], s['actor_guid'])['shapes']]
    out['locations'] = sorted(({k: v for k, v in x.items() if k not in ('loaded_hold', 'auto_load_pending', 'package_dirty', 'loader_available')}
                               for x in ok(m.inspect_partition_location_volumes, W, 0, 128)['volumes']), key=lambda x: x['actor_path'])
    for x in out['locations']:
        x['shape'] = ok(m.inspect_volume_brush_builder, x['actor_path'])['shape']
    return out


STAGES = {'descriptor': descriptor_stage, 'flags': flags_stage, 'regions': regions_stage, 'pins': pins_stage,
          'sources': sources_stage, 'location': location_stage}


def prepare():
    cleanup()
    assert ok(m.create_editor_world, MAP, TEMPLATE, True, 'discard', True)['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    spawn('MCP_A', [500, 500, 100])
    spawn('MCP_B', [-20000, 3000, 100])
    save()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'actors': ACTORS}))
    out = {}
    for name, fn in STAGES.items():
        out[name] = fn()
        save()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'actors': ACTORS, 'snapshot': snapshot(), 'stages': out}, indent=1))
    print('partition prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    ACTORS.update(st['actors'])
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot()))
    want = st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('partition authored state identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=300)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP + '_HLOD0_Instancing'}, timeout=300)   # created by the template copy
    STATE.unlink(missing_ok=True)


def stage():
    """Debug helper: run named stages against the currently loaded scratch map."""
    ACTORS.update(json.loads(STATE.read_text())['actors'])
    for name in STAGE_ARGS:
        print(name, json.dumps(STAGES[name]())[:300])
        save()


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup, 'stage': stage}[COMMAND]()
