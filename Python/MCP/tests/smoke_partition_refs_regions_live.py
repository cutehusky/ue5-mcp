"""World Partition descriptor references, editor loading regions, runtime-grid name syntax and runtime-cell routes;
prepare, restart, verify.

prepare: copy the OpenWorld template, place two static mesh actors and two physics-constraint actors whose
constraint fields form a chain (C1 -> A, C1 -> C2 -> B), save so descriptors carry the references, then check reverse
referencers and the bounded transitive graph; create, inspect, replace and release unloaded editor regions; reject
malformed runtime-grid names; check runtime-cell enumeration and refusals.
verify (fresh editor): reload the map, rebuild referencers and graph from saved descriptors and compare, then delete.
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
MAP = '/Game/UE5MCP_Test/MCP_WPRefs'
TEMPLATE = '/Engine/Maps/Templates/OpenWorld'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'partition_refs.json'
ACTORS = {}


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


def wp():
    return ok(m.inspect_world_partition)['partition_path']


def descriptors():
    out, start = [], 0
    while True:
        page = ok(m.inspect_world_partition_actor_descriptors, start, 128)
        out += page['actor_descriptors']
        if not page['has_more']:
            return {d['actor_soft_path']: d for d in out}
        start = page['next_start']


def spawn(label, cls, x):
    path = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': cls, 'Location': {'X': x, 'Y': 0, 'Z': 100}}, timeout=60).text.strip('"')
    assert path.startswith(MAP), path
    ACTORS[label] = path


def save():
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']


def label_of(path):
    return next(k for k, v in ACTORS.items() if v == path)


# ---------------------------------------------------------------- descriptor references
def references():
    """Referencers of every actor and the graph from C1, as labels."""
    W, D = wp(), descriptors()
    out = {}
    for label, path in sorted(ACTORS.items()):
        d = D[path]
        r = ok(m.inspect_partition_actor_referencers, W, d['container_path'], d['guid'])
        out[label] = sorted(label_of(x['actor_soft_path']) for x in r['referencers'])
        assert not r['has_more'] and all(not x['editor_only_reference'] for x in r['referencers']), r
    d = D[ACTORS['C1']]
    g = ok(m.inspect_partition_actor_reference_graph, W, d['container_path'], d['guid'])
    assert not g['truncated'] and all(n['descriptor_present'] for n in g['nodes']), g
    out['graph'] = sorted((label_of(n['actor_soft_path']), n['minimum_discovery_depth']) for n in g['nodes'])
    out['edges'] = g['edge_count']
    return out


def reference_stage():
    for label, cls, x in (('A', '/Script/Engine.StaticMeshActor', 0), ('B', '/Script/Engine.StaticMeshActor', 300),
                          ('C1', '/Script/Engine.PhysicsConstraintActor', 150), ('C2', '/Script/Engine.PhysicsConstraintActor', 450)):
        spawn(label, cls, x)
    for c, props in (('C1', {'ConstraintComp.ConstraintActor1': ACTORS['A'], 'ConstraintComp.ConstraintActor2': ACTORS['C2']}),
                     ('C2', {'ConstraintComp.ConstraintActor1': ACTORS['B']})):
        r = J(m.set_editor_actor_properties(ACTORS[c], props))
        assert 'errorMessage' not in r, r
    save()   # descriptors pick up references when the actor packages are saved
    refs = references()
    assert refs['A'] == ['C1'] and refs['B'] == ['C2'] and refs['C2'] == ['C1'] and refs['C1'] == [], refs
    assert refs['graph'] == [('A', 1), ('B', 2), ('C1', 0), ('C2', 1)] and refs['edges'] == 3, refs
    W, D = wp(), descriptors()
    d = D[ACTORS['C1']]
    # Depth and node limits truncate the graph explicitly.
    g = ok(m.inspect_partition_actor_reference_graph, W, d['container_path'], d['guid'], max_depth=1)
    assert g['depth_limit_reached'] and g['truncated'] and len(g['nodes']) == 3, g
    g = ok(m.inspect_partition_actor_reference_graph, W, d['container_path'], d['guid'], node_limit=2)
    assert g['node_limit_reached'] and len(g['nodes']) == 2, g
    # Editor-only references: none here.
    assert ok(m.inspect_partition_actor_referencers, W, d['container_path'], D[ACTORS['A']]['guid'], editor_only=True)['referencers'] == []
    bad(m.inspect_partition_actor_referencers, W, d['container_path'], '0' * 32)
    bad(m.inspect_partition_actor_referencers, W, d['container_path'] + 'X', d['guid'])
    bad(m.inspect_partition_actor_reference_graph, W, d['container_path'], d['guid'], max_depth=99)
    bad(m.inspect_partition_actor_reference_graph, W, d['container_path'], d['guid'], node_limit=0)
    # Paging the referencer scan.
    p = ok(m.inspect_partition_actor_referencers, W, d['container_path'], D[ACTORS['A']]['guid'], start=0, count=1)
    assert p['emitted_count'] <= 1, p
    return refs


# ---------------------------------------------------------------- editor loading regions
def regions():
    return ok(m.inspect_world_partition_editor_regions, 0, 128)


def region_stage():
    W = wp()
    n = regions()['registered_adapter_count']
    bad(m.create_world_partition_editor_region, W, n + 1, 'MCP_Region', [0, 0, 0], [1000, 1000, 1000], confirm=True)   # stale count
    bad(m.create_world_partition_editor_region, W, n, 'MCP_Region', [0, 0, 0], [0, 1000, 1000], confirm=True)          # empty box
    ok(m.create_world_partition_editor_region, W, n, 'MCP_Region', [0, 0, 0], [1000, 1000, 1000], confirm=True, dry_run=True)
    assert regions()['registered_adapter_count'] == n
    ok(m.create_world_partition_editor_region, W, n, 'MCP_Region', [0, 0, 0], [1000, 1000, 1000], confirm=True)
    r = regions()
    mine = [x for x in r['editor_regions'] if x['label'] == 'MCP_Region']
    assert r['registered_adapter_count'] == n + 1 and len(mine) == 1 and not mine[0]['loaded'] and mine[0]['user_created'], r
    adapter = mine[0]['adapter_path']
    d = ok(m.inspect_partition_editor_region, W, adapter)
    assert d['label'] == 'MCP_Region' and d['bounds_center'] == [0, 0, 0] and d['bounds_extent'] == [1000, 1000, 1000] and not d['loaded'], d
    assert d['registered_adapter_count'] == n + 1, d
    bad(m.inspect_partition_editor_region, W, adapter + 'X')
    # Replacement: stale label/box/count refused, dry run unchanged, then the identity changes and the old adapter is gone.
    old = dict(expected_count=n + 1, expected_label='MCP_Region', expected_center=[0, 0, 0], expected_extent=[1000, 1000, 1000])
    new = dict(label='MCP_Region2', center=[500, -500, 100], extent=[2000, 1000, 500])
    bad(m.replace_unloaded_partition_editor_region, W, adapter, **{**old, 'expected_label': 'Other'}, **new, confirm=True)
    bad(m.replace_unloaded_partition_editor_region, W, adapter, **{**old, 'expected_extent': [1, 1, 1]}, **new, confirm=True)
    bad(m.replace_unloaded_partition_editor_region, W, adapter, **{**old, 'expected_count': n}, **new, confirm=True)
    ok(m.replace_unloaded_partition_editor_region, W, adapter, **old, **new, confirm=True, dry_run=True)
    assert ok(m.inspect_partition_editor_region, W, adapter)['label'] == 'MCP_Region'
    ok(m.replace_unloaded_partition_editor_region, W, adapter, **old, **new, confirm=True)
    bad(m.inspect_partition_editor_region, W, adapter)   # released
    r = regions()
    mine = [x for x in r['editor_regions'] if x['label'] == 'MCP_Region2']
    assert r['registered_adapter_count'] == n + 1 and len(mine) == 1 and mine[0]['adapter_path'] != adapter, r
    d = ok(m.inspect_partition_editor_region, W, mine[0]['adapter_path'])
    assert d['bounds_center'] == [500, -500, 100] and d['bounds_extent'] == [2000, 1000, 500] and not d['loaded'], d
    # A loaded region is not replaceable.
    loaded = next(x for x in r['editor_regions'] if x['loaded'])
    bad(m.replace_unloaded_partition_editor_region, W, loaded['adapter_path'], n + 1, loaded['label'], loaded['bounds_center'],
        loaded['bounds_extent'], 'X', [0, 0, 0], [10, 10, 10], confirm=True)
    ok(m.release_unloaded_world_partition_editor_region, W, mine[0]['adapter_path'], n + 1, 'MCP_Region2', [500, -500, 100], [2000, 1000, 500], confirm=True)
    assert regions()['registered_adapter_count'] == n


# ---------------------------------------------------------------- runtime-grid name syntax, runtime cells
def grid_stage():
    W, D = wp(), descriptors()
    d = D[ACTORS['A']]
    cur = d.get('runtime_grid', 'None') or 'None'
    for name in (':', 'Main::Sub', 'Main:', ' Main', 'Ma\tin', '.Sub', 'Main..Sub:x'):
        bad(m.set_loaded_partition_actor_runtime_grid, W, d['container_path'], d['guid'], ACTORS['A'], cur, name, confirm=True)
    assert descriptors()[ACTORS['A']].get('runtime_grid', cur) in (cur, 'None', '')


def cell_stage():
    c = ok(m.inspect_world_partition_runtime_cells, 0, 8)
    # The editor runtime hash has no generated streaming cells without PIE or cook.
    assert c['runtime_cells'] == [] and c['emitted_count'] == 0 and not c['has_more'], c
    assert c['runtime_hash_class'].endswith('WorldPartitionRuntimeHashSet'), c
    bad(m.inspect_world_partition_runtime_cells, 0, 0)
    W = wp()
    fake = c['runtime_hash_path'] + '.NoSuchCell'
    bad(m.inspect_partition_runtime_cell_detail, W, fake, '0' * 32)
    bad(m.inspect_partition_runtime_cell_contents, W, fake, '0' * 32)
    bad(m.inspect_partition_runtime_cell_mappings, W, fake, '0' * 32)


def prepare():
    cleanup()
    assert ok(m.create_editor_world, MAP, TEMPLATE, True, 'discard', True)['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    refs = reference_stage()
    region_stage()
    grid_stage()
    cell_stage()
    save()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'actors': ACTORS, 'refs': refs}, indent=1))
    print('partition references, regions, grid syntax and cell routes prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    ACTORS.update(st['actors'])
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(references()))
    assert got == st['refs'], (got, st['refs'])
    cell_stage()
    print('descriptor referencers and reference graph identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    for p in (MAP, MAP + '_HLOD0_Instancing'):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
