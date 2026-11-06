"""Authored RuntimeSpatialHash grids and settings on a copy of the SpatialHash fixture map; prepare, restart, verify.

The fixture /Game/UE5MCP_Fixtures/SpatialHash/SH_Source comes from the engine WorldPartitionConvertCommandlet with
RuntimeHashClass=WorldPartitionRuntimeSpatialHash in its per-map ini (see Verification/fixtures/create_fixtures.py).
prepare: copy it, add/rename/reorder/remove grids and edit numeric, origin, blocking, debug colour, project overrides and
Z culling (stale guard, dry run, real edit); inspect grid-info actors; save and snapshot.
verify (fresh editor): reload the copy, compare, then delete it.
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
SOURCE = '/Game/UE5MCP_Fixtures/SpatialHash/SH_Source'
MAP = '/Game/UE5MCP_Test/MCP_SpatialHash'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'spatial_hash.json'


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


def W():
    return ok(m.inspect_world_partition)['partition_path']


def grids():
    return ok(m.inspect_partition_spatial_hash_grids, W(), 0, 64)


def names():
    return [g['name'] for g in grids()['grids']]


def H():
    return grids()['runtime_hash_path']


def settings():
    s = ok(m.inspect_partition_spatial_hash_settings, W())
    return {'overrides': {o['field_name']: o['authored_override'] for o in s['overrides']}, 'z': s['enable_z_culling']}


def edit(fn, state, *a, **kw):
    before = state()
    ok(fn, *a, **kw, confirm=True, dry_run=True)
    assert state() == before, (fn.__name__, 'dry run changed state')
    ok(fn, *a, **kw, confirm=True, dry_run=False)
    assert state() != before, (fn.__name__, 'edit left state unchanged')


def grid(name):
    return next(g for g in grids()['grids'] if g['name'] == name)


def ident(name):
    g = grids()
    i = next(x['index'] for x in g['grids'] if x['name'] == name)
    return W(), g['runtime_hash_path'], i, name, g['grid_count']


def grid_stage():
    assert names() == ['MainGrid'] and grids()['runtime_hash_class'].endswith('WorldPartitionRuntimeSpatialHash'), grids()
    bad(m.add_partition_spatial_hash_grid, W(), H(), ['Wrong'], 'MCP_Far', confirm=True)
    bad(m.add_partition_spatial_hash_grid, W(), H(), ['MainGrid'], 'MainGrid', confirm=True)      # duplicate
    for i, n in enumerate(('MCP_Far', 'MCP_Near')):
        edit(m.add_partition_spatial_hash_grid, names, W(), H(), names(), n)
    assert names() == ['MainGrid', 'MCP_Far', 'MCP_Near'], names()
    # Numeric fields.
    for field, key, value in (('CellSize', 'cell_size', 25600), ('LoadingRange', 'loading_range', 51200), ('Priority', 'priority', -3)):
        cur = grid('MCP_Far')[key]
        bad(m.set_partition_spatial_hash_grid_numeric, *ident('MCP_Far'), field, cur + 1, value, confirm=True)
        edit(m.set_partition_spatial_hash_grid_numeric, lambda: grid('MCP_Far'), *ident('MCP_Far'), field, cur, value)
        assert grid('MCP_Far')[key] == value, (field, grid('MCP_Far'))
    bad(m.set_partition_spatial_hash_grid_numeric, *ident('MCP_Far'), 'CellSize', 25600, 100, confirm=True)    # below 1600
    edit(m.set_partition_spatial_hash_grid_origin, lambda: grid('MCP_Far'), *ident('MCP_Far'), grid('MCP_Far')['origin_xy'], [1000, -2000])
    edit(m.set_partition_spatial_hash_grid_blocking, lambda: grid('MCP_Far'), *ident('MCP_Far'), False, True)
    bad(m.set_partition_spatial_hash_grid_blocking, *ident('MCP_Far'), False, False, confirm=True)
    color = grid('MCP_Far')['debug_color']
    edit(m.set_partition_spatial_hash_grid_debug_color, lambda: grid('MCP_Far'), *ident('MCP_Far'), color, [0.25, 0.5, 0.75, 1])
    bad(m.set_partition_spatial_hash_grid_debug_color, *ident('MCP_Far'), [0.25, 0.5, 0.75, 1], [2, 0, 0, 1], confirm=True)
    f = grid('MCP_Far')
    assert (f['origin_xy'], f['block_on_slow_streaming'], [round(c, 4) for c in f['debug_color']]) == ([1000, -2000], True, [0.25, 0.5, 0.75, 1]), f
    # Rename, reorder (the first grid becomes default), remove.
    bad(m.rename_partition_spatial_hash_grid, *ident('MCP_Near')[:4], 3, 'MCP_Far', confirm=True)        # duplicate name
    edit(m.rename_partition_spatial_hash_grid, names, *ident('MCP_Near')[:4], 3, 'MCP_Mid')
    bad(m.reorder_partition_spatial_hash_grids, W(), H(), names(), ['MCP_Far', 'MainGrid'], confirm=True)  # not a permutation
    edit(m.reorder_partition_spatial_hash_grids, names, W(), H(), names(), ['MCP_Far', 'MainGrid', 'MCP_Mid'])
    assert names() == ['MCP_Far', 'MainGrid', 'MCP_Mid'], names()
    i = names().index('MCP_Mid')
    bad(m.remove_partition_spatial_hash_grid, W(), H(), names(), i, 'Wrong', confirm=True)
    edit(m.remove_partition_spatial_hash_grid, names, W(), H(), names(), i, 'MCP_Mid')
    assert names() == ['MCP_Far', 'MainGrid'], names()


def settings_stage():
    for field in ('UseAlignedGridLevels', 'SnapNonAlignedGridLevelsToLowerLevels', 'PlaceSmallActorsUsingLocation', 'PlacePartitionActorsUsingLocation'):
        cur = settings()['overrides'][field]
        new = 2 if cur != 2 else 1
        bad(m.set_partition_spatial_hash_override, W(), H(), field, (cur + 1) % 3, new, confirm=True)
        edit(m.set_partition_spatial_hash_override, settings, W(), H(), field, cur, new)
    bad(m.set_partition_spatial_hash_override, W(), H(), 'UseAlignedGridLevels', settings()['overrides']['UseAlignedGridLevels'], 5, confirm=True)
    z = settings()['z']
    bad(m.set_partition_spatial_hash_z_culling, W(), H(), not z, z, confirm=True)
    edit(m.set_partition_spatial_hash_z_culling, settings, W(), H(), z, not z)
    info = ok(m.inspect_partition_spatial_hash_grid_info_actors, W(), 0, 8)
    assert isinstance(info.get('actors', info.get('grid_info_actors', [])), list), info


def snapshot():
    g = grids()
    rows = [{k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v] if isinstance(v, list) else v) for k, v in x.items()} for x in g['grids']]
    return {'grids': rows, 'settings': settings()}


def prepare():
    cleanup()
    assert ok(m.create_editor_world, MAP, SOURCE, True, 'discard', True)['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    grid_stage()
    settings_stage()
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1), encoding='utf-8')
    print('SpatialHash grids and settings prepared; map saved')


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot()))
    assert got == st['snapshot'], json.dumps({'got': got, 'want': st['snapshot']})[:3000]
    print('SpatialHash grids and settings identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    for p in (MAP, MAP + '_HLOD0_Instancing'):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
