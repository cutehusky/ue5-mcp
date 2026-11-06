"""Decal actors, render/fade settings, material, size/colour, placement, receivers and mobility; prepare, restart, verify.

prepare: in a scratch map, create two decal actors, edit every typed decal field (stale guard, dry run, real edit),
assign a deferred-decal material and page its users, author local size, linear colour, visibility, world transform,
a cube's receives-decals flag and decal mobility with hierarchy snapshots, delete the second decal; save the map.
verify (fresh editor): reload the map and compare the snapshot, then delete it.
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
MAP = '/Game/UE5MCP_Test/MCP_Decals'
WORLD = MAP + '.MCP_Decals'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'decals.json'
DECAL_MAT = '/Engine/EngineMaterials/DefaultDeferredDecalMaterial.DefaultDeferredDecalMaterial'
SURFACE_MAT = '/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial'
SETTINGS = {'SortOrder': 3, 'FadeScreenSize': 0.05, 'FadeStartDelay': 2, 'FadeDuration': 1.5, 'FadeInStartDelay': 0.5,
            'FadeInDuration': 0.25, 'bDestroyOwnerAfterFade': 0}
CUBE = {}


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


def actor(name):
    return f'{WORLD}:PersistentLevel.{name}'


def decal(name='MCP_DecalA'):
    d = ok(m.inspect_decals_page, 0, 8, actor(name))['decals']
    assert len(d) == 1, d
    d = d[0]
    d.pop('package_dirty', None)
    return d


def ids(name='MCP_DecalA'):
    d = decal(name)
    return d['actor_path'], d['component_path'], d['actor_guid'], d['label']


def receiver():
    r = ok(m.inspect_decal_receivers_page, 0, 8, CUBE['actor'], CUBE['component'])['receivers']
    assert len(r) == 1, r
    return r[0]


def hierarchy(name='MCP_DecalA'):
    a, c, *_ = ids(name)
    h = ok(m.inspect_decal_mobility, a, c)
    return [{'component_path': n['component_path'], 'parent_path': n['parent_path'], 'mobility': n['mobility']} for n in h['hierarchy']]


# ---------------------------------------------------------------- stages
def create_stage():
    ok(m.create_decal_actor, WORLD, 'MCP_DecalA', [0, 0, 100], confirm=True, dry_run=True)
    assert ok(m.inspect_decals_page, 0, 8)['decals'] == []
    bad(m.create_decal_actor, WORLD, 'MCP_DecalA', [0, 0, 2e9], confirm=True, dry_run=False)
    bad(m.create_decal_actor, WORLD, 'MCP Decal!', [0, 0, 0], confirm=True, dry_run=False)
    bad(m.create_decal_actor, WORLD, 'MCP_DecalA', [0, 0, 100], confirm=False, dry_run=False)
    for name, z in (('MCP_DecalA', 100), ('MCP_DecalB', 300)):
        r = ok(m.create_decal_actor, WORLD, name, [0, 0, z], confirm=True, dry_run=False)
        assert r['material_path'] == '' and r['actor_path'] == actor(name), r
    bad(m.create_decal_actor, WORLD, 'MCP_DecalA', [0, 0, 0], confirm=True, dry_run=False)  # name taken
    d = decal()
    assert d['world_location'] == [0, 0, 100] and d['local_decal_size'] == [128, 256, 256] and d['linear_color'] == [1, 1, 1, 1], d
    assert ok(m.inspect_decals_page, 0, 8)['component_count'] == 2


def settings_stage():
    for name, value in SETTINGS.items():
        cur = decal()['settings'][name]
        bad(m.set_decal_setting, *ids(), name, cur + 7, value, confirm=True, dry_run=False)
        edit(m.set_decal_setting, decal, *ids(), name, cur, value)
        assert abs(decal()['settings'][name] - value) < 1e-6, (name, decal()['settings'])
    s = decal()['settings']
    bad(m.set_decal_setting, *ids(), 'FadeScreenSize', s['FadeScreenSize'], 2, confirm=True, dry_run=False)
    bad(m.set_decal_setting, *ids(), 'FadeDuration', s['FadeDuration'], -1, confirm=True, dry_run=False)
    bad(m.set_decal_setting, *ids(), 'NoSuchField', 0, 1, confirm=True, dry_run=False)
    bad(m.set_decal_setting, *ids()[:3], 'WrongLabel', 'SortOrder', 3, 4, confirm=True, dry_run=False)
    # A same-value edit is a no-op.
    r = ok(m.set_decal_setting, *ids(), 'SortOrder', 3, 3, confirm=True, dry_run=False)
    assert decal()['settings']['SortOrder'] == 3, r


def material_stage():
    mats = ok(m.inspect_loaded_decal_materials, 'DefaultDeferredDecal', 0, 8)
    if not mats['materials']:
        httpx.get(BASE + '/assets/describe', params={'asset_path': DECAL_MAT}, timeout=120)
        mats = ok(m.inspect_loaded_decal_materials, 'DefaultDeferredDecal', 0, 8)
    assert [x['material_path'] for x in mats['materials']] == [DECAL_MAT], mats
    httpx.get(BASE + '/assets/describe', params={'asset_path': SURFACE_MAT}, timeout=120)
    assert ok(m.inspect_loaded_decal_materials, 'WorldGrid', 0, 8)['materials'] == []  # surface domain is not listed
    bad(m.set_decal_material, *ids(), '', SURFACE_MAT, confirm=True, dry_run=False)  # not a deferred-decal material
    bad(m.set_decal_material, *ids(), DECAL_MAT, DECAL_MAT, confirm=True, dry_run=False)  # stale current
    edit(m.set_decal_material, decal, *ids(), '', DECAL_MAT)
    assert decal()['material_path'] == DECAL_MAT
    users = ok(m.inspect_decal_material_users, DECAL_MAT, 0, 8)
    assert [u['actor_path'] for u in users['decals']] == [actor('MCP_DecalA')], users
    unassigned = ok(m.inspect_decal_material_users, '', 0, 8)
    assert [u['actor_path'] for u in unassigned['decals']] == [actor('MCP_DecalB')], unassigned
    assert ok(m.inspect_decal_material_users, DECAL_MAT, 0, 8, actor('MCP_DecalB'))['decals'] == []
    # Clear and reassign on the second decal (deleted later, so its material guard is exercised there).
    a, c, g, l = ids('MCP_DecalB')
    edit(m.set_decal_material, lambda: decal('MCP_DecalB'), a, c, g, l, '', DECAL_MAT)
    edit(m.set_decal_material, lambda: decal('MCP_DecalB'), a, c, g, l, DECAL_MAT, '')
    edit(m.set_decal_material, lambda: decal('MCP_DecalB'), a, c, g, l, '', DECAL_MAT)


def appearance_stage():
    d = decal()
    bad(m.set_decal_local_size, *ids(), [1, 1, 1], [64, 128, 128], confirm=True, dry_run=False)
    bad(m.set_decal_local_size, *ids(), d['local_decal_size'], [0, 128, 128], confirm=True, dry_run=False)
    edit(m.set_decal_local_size, decal, *ids(), d['local_decal_size'], [64, 128, 96])
    assert decal()['local_decal_size'] == [64, 128, 96] and decal()['component_scale'] == [1, 1, 1], decal()
    bad(m.set_decal_linear_color, *ids(), [0, 0, 0, 0], [0.5, 0.25, 1, 0.75], confirm=True, dry_run=False)
    bad(m.set_decal_linear_color, *ids(), d['linear_color'], [2000, 0, 0, 1], confirm=True, dry_run=False)
    edit(m.set_decal_linear_color, decal, *ids(), d['linear_color'], [0.5, 0.25, 4, 0.75])
    assert decal()['linear_color'] == [0.5, 0.25, 4, 0.75], decal()
    assert decal()['material_path'] == DECAL_MAT and decal()['settings']['SortOrder'] == 3  # siblings kept


def transform_of(d):
    v = lambda x: dict(zip('XYZ', x))
    return {'Translation': v(d['world_location']), 'Rotation': dict(zip('XYZW', d['world_rotation_quaternion'])), 'Scale3D': v(d['component_scale'])}


def placement_stage():
    bad(m.set_decal_visible, *ids(), False, False, confirm=True, dry_run=False)
    edit(m.set_decal_visible, decal, *ids(), True, False)
    assert decal()['visible'] is False
    d = decal()
    cur = transform_of(d)
    new = {'Translation': {'X': 100, 'Y': -50, 'Z': 25}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 2, 'Y': 1, 'Z': -1}}
    bad(m.set_decal_world_transform, *ids(), {**cur, 'Translation': {'X': 1, 'Y': 1, 'Z': 1}}, new, confirm=True, dry_run=False)
    bad(m.set_decal_world_transform, *ids(), cur, {**new, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 2}}, confirm=True, dry_run=False)
    bad(m.set_decal_world_transform, *ids(), cur, {**new, 'Scale3D': {'X': 0, 'Y': 1, 'Z': 1}}, confirm=True, dry_run=False)
    edit(m.set_decal_world_transform, decal, *ids(), cur, new)
    d = decal()
    assert d['world_location'] == [100, -50, 25] and d['component_scale'] == [2, 1, -1], d
    assert [round(q, 6) for q in d['world_rotation_quaternion']] == [0, 0, 0, 1], d
    assert d['local_decal_size'] == [64, 128, 96] and d['visible'] is False, d  # local size and visibility kept


def receiver_stage():
    path = httpx.post(BASE + '/editor/actors/spawn', json={'AssetPath': '/Engine/BasicShapes/Cube.Cube'}, timeout=300).text.strip().strip('"')
    r = ok(m.inspect_decal_receivers_page, 0, 8, path)['receivers']
    assert len(r) == 1 and r[0]['receives_decals'], r
    CUBE.update(actor=path, component=r[0]['component_path'])
    all_r = ok(m.inspect_decal_receivers_page, 0, 64)
    assert all_r['matched_count'] >= 2 and any(x['class_path'].endswith('BrushComponent') for x in all_r['receivers']), all_r
    g = r[0]
    bad(m.set_primitive_receives_decals, g['actor_path'], g['component_path'], g['actor_guid'], g['label'], False, False, confirm=True, dry_run=False)
    edit(m.set_primitive_receives_decals, receiver, g['actor_path'], g['component_path'], g['actor_guid'], g['label'], True, False)
    assert receiver()['receives_decals'] is False


def mobility_stage():
    h = hierarchy()
    assert len(h) >= 2 and all(n['mobility'] == 2 for n in h) and h[0]['parent_path'] == 'None', h
    d = decal()
    a, c, g, l = ids()
    children = d['direct_child_count']
    bad(m.set_decal_mobility, a, c, g, l, 2, 0, children + 1, confirm=True, dry_run=False)          # stale child count
    bad(m.set_decal_mobility, a, c, g, l, 2, 0, children, confirm=True, dry_run=False,
        expected_hierarchy=[{**n, 'mobility': 0} for n in h])                                         # stale snapshot
    bad(m.set_decal_mobility, a, c, g, l, 2, 3, children, confirm=True, dry_run=False)               # not a mobility
    edit(m.set_decal_mobility, hierarchy, a, c, g, l, 2, 0, children, expected_hierarchy=h)
    h = hierarchy()
    # Static on the root leaves the native children as they were.
    assert h[0]['mobility'] == 0 and all(n['mobility'] == 2 for n in h[1:]), h
    edit(m.set_decal_mobility, hierarchy, a, c, g, l, 0, 1, children, expected_hierarchy=h)
    assert hierarchy()[0]['mobility'] == 1
    # Back to Movable: the native children (already Movable) stay Movable with the root.
    h = hierarchy()
    edit(m.set_decal_mobility, hierarchy, a, c, g, l, 1, 2, children, expected_hierarchy=h)
    assert all(n['mobility'] == 2 for n in hierarchy()), hierarchy()


def delete_stage():
    a, c, g, l = ids('MCP_DecalB')
    bad(m.delete_decal_actor, WORLD, a, c, g, l, '', confirm=True, dry_run=False)           # stale material
    bad(m.delete_decal_actor, WORLD, a, c, '0' * 32, l, DECAL_MAT, confirm=True, dry_run=False)
    ok(m.delete_decal_actor, WORLD, a, c, g, l, DECAL_MAT, confirm=True, dry_run=True)
    assert ok(m.inspect_decals_page, 0, 8)['component_count'] == 2
    ok(m.delete_decal_actor, WORLD, a, c, g, l, DECAL_MAT, confirm=True, dry_run=False)
    assert [d['actor_path'] for d in ok(m.inspect_decals_page, 0, 8)['decals']] == [actor('MCP_DecalA')]
    assert ok(m.inspect_decal_material_users, DECAL_MAT, 0, 8)['decals'][0]['actor_path'] == actor('MCP_DecalA')


def snapshot():
    d = decal()
    d['world_rotation_quaternion'] = [round(q, 6) for q in d['world_rotation_quaternion']]
    d['settings'] = {k: round(v, 6) for k, v in d['settings'].items()}
    r = receiver()
    r.pop('package_dirty', None)
    return {'decal': d, 'receiver': r, 'hierarchy': hierarchy(), 'users': [u['actor_path'] for u in ok(m.inspect_decal_material_users, DECAL_MAT, 0, 8)['decals']]}


def prepare():
    cleanup()
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    for stage in (create_stage, settings_stage, material_stage, appearance_stage, placement_stage, receiver_stage, mobility_stage, delete_stage):
        stage()
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).is_success
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'cube': CUBE, 'snapshot': snapshot()}, indent=1))
    print('decals prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    CUBE.update(st['cube'])
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    httpx.get(BASE + '/assets/describe', params={'asset_path': DECAL_MAT}, timeout=120)
    got, want = json.loads(json.dumps(snapshot())), st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('decals, receivers and mobility identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
