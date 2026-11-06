"""Spline and spline-mesh component authoring on a scratch map: prepare, restart, verify.

Usage: smoke_splines_live.py prepare|verify|cleanup. Creates spline and spline-mesh instance components and drives every
spline MCP tool function: point position/type/tangents/scale/rotation, insert/remove/clear/replace, closed loop and closing
key, settings and default up vector, distance/time sampling, closest point, segment pages, spline-mesh endpoints, scales,
rolls, forward axis, up direction, offsets, boundaries, asset, smooth interpolation, slice sampling, segment fitting
(open and closed loop) and component removal. Each edit is rejected with a stale expected value, dry-run checked, then
applied. The final components must survive a cold editor restart.
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
MAP = '/Game/UE5MCP_Test/MCP_Splines'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'splines.json'
CUBE = '/Engine/BasicShapes/Cube.Cube'
CYL = '/Engine/BasicShapes/Cylinder.Cylinder'


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
    r = ok(fn, *a, confirm=True, **kw)
    if changes:
        assert state() != before, (fn.__name__, 'edit left state unchanged', str(r)[:300])
    return r


def close(a, b, eps=1e-3):
    return all(abs(x - y) <= eps for x, y in zip(a, b))


class World:
    def __init__(self, actor):
        self.actor = actor
        self.path = actor + '.Path'
        self.loop = actor + '.Loop'
        self.seg = actor + '.Seg'
        self.seg2 = actor + '.Seg2'

    def pts(self, c=None):
        return ok(m.inspect_spline_points, self.actor, c or self.path)

    def p(self, i, c=None):
        return self.pts(c)['points'][i]

    def n(self, c=None):
        return self.pts(c)['point_count']

    def settings(self, c=None):
        return ok(m.inspect_spline_settings, self.actor, c or self.path)

    def mesh(self, c=None):
        return next(x for x in ok(m.inspect_world_spline_mesh_components)['components'] if x['component_path'] == (c or self.seg))


def spline_stage(w):
    A, C = w.actor, w.path
    assert w.n() == 2
    # Insert, append, move, type, tangents, scale, rotation.
    edit(m.insert_spline_point, w.pts, A, C, 1, 2, w.p(1)['position'], [50, 50, 0])
    assert w.n() == 3 and close(w.p(1)['position'], [50, 50, 0]), w.pts()
    bad(m.insert_spline_point, A, C, 1, 2, w.p(1)['position'], [0, 0, 0], confirm=True)            # stale count
    edit(m.insert_spline_point, w.pts, A, C, 3, 3, w.p(2)['position'], [200, 0, 0])                  # append
    bad(m.set_spline_point_position, A, C, 3, 4, [0, 0, 0], [1, 1, 1], confirm=True)                  # stale position
    edit(m.set_spline_point_position, w.pts, A, C, 3, 4, w.p(3)['position'], [250, 20, 30])
    edit(m.set_spline_point_type, w.pts, A, C, 2, 4, w.p(2)['type'], point_type='Linear')
    bad(m.set_spline_point_type, A, C, 2, 4, w.p(2)['type'], point_type='Wobbly', confirm=True)
    ok(m.set_spline_point_type, A, C, 1, 4, w.p(1)['type'], point_type='CurveCustomTangent', confirm=True)
    p1 = w.p(1)
    edit(m.set_spline_point_tangents, w.pts, A, C, 1, 4, p1['type'], p1['arrive_tangent'], p1['leave_tangent'], [0, 150, 0], [0, 120, 0])
    assert close(w.p(1)['arrive_tangent'], [0, 150, 0]) and close(w.p(1)['leave_tangent'], [0, 120, 0])
    edit(m.set_spline_point_scale, w.pts, A, C, 1, 4, w.p(1)['scale'], [2, 1, 0.5])
    bad(m.set_spline_point_scale, A, C, 1, 4, w.p(1)['scale'], [0, float('1e12'), 1], confirm=True)
    q = [0.5, 0.5, 0.5, 0.5]   # yaw 90 (matches the tangent) plus roll 90
    edit(m.set_spline_point_rotation, w.pts, A, C, 1, 4, w.p(1)['rotation_quaternion'], q)
    bad(m.set_spline_point_rotation, A, C, 1, 4, w.p(1)['rotation_quaternion'], [0, 0, 1, 1], confirm=True)
    # Settings, default up, closed loop and closing key.
    s = w.settings()
    edit(m.set_spline_setting, w.settings, A, C, 4, 'ReparamStepsPerSegment', s['reparam_steps_per_segment'], scalar_value=20)
    edit(m.set_spline_setting, w.settings, A, C, 4, 'Duration', s['duration'], scalar_value=4)
    edit(m.set_spline_setting, w.settings, A, C, 4, 'StationaryEndpoints', 0, bool_value=True)
    bad(m.set_spline_setting, A, C, 4, 'Duration', 99, scalar_value=5, confirm=True)
    bad(m.set_spline_setting, A, C, 4, 'NoSuchField', 0, scalar_value=1, confirm=True)
    edit(m.set_spline_default_up_vector, w.settings, A, C, 4, w.settings()['default_up_vector'], [0, 1, 0])
    bad(m.set_spline_default_up_vector, A, C, 4, [0, 1, 0], [0, 0, 0], confirm=True)
    # Sampling, closest point, segment pages.
    d = ok(m.sample_spline_by_distance, A, C, sample_count=8)
    assert len(d['samples']) == 8, d
    t = ok(m.sample_spline_by_time, A, C, sample_count=5, constant_velocity=True)
    assert len(t['samples']) == 5, t
    bad(m.sample_spline_by_distance, A, C, sample_count=0)
    cp = ok(m.find_spline_closest_point, A, C, [200, 10, 0])
    assert 'input_key' in json.dumps(cp), cp
    segs = ok(m.inspect_spline_segments, A, C)
    assert len(segs['segments']) == 3, segs
    # Remove a point, then the closed-loop spline: loop, closing key set/reset, segments include the closing one.
    edit(m.remove_spline_point, w.pts, A, C, 2, 4, w.p(2)['position'])
    bad(m.remove_spline_point, A, C, 0, 3, [9, 9, 9], confirm=True)
    ok(m.add_spline_actor_component, A, 'Loop', confirm=True)
    L = w.loop
    edit(m.replace_spline_point_positions, lambda: w.pts(L), A, L, 2, [[0, 0, 0], [300, 0, 0], [300, 300, 0], [0, 300, 0]])
    assert w.n(L) == 4
    edit(m.set_spline_closed_loop, lambda: w.pts(L), A, L, 4, False, True)
    bad(m.set_spline_closed_loop, A, L, 4, False, True, confirm=True)
    assert len(ok(m.inspect_spline_segments, A, L)['segments']) == 4
    key = lambda: w.settings(L).get('closing_input_key', json.dumps(w.pts(L)))
    edit(m.set_spline_closing_key, lambda: w.pts(L), A, L, 4, 4.0, 5.0, changes=False)
    bad(m.set_spline_closing_key, A, L, 4, 4.0, 2.5, confirm=True)       # must exceed the last point key
    edit(m.reset_spline_closing_key, lambda: w.pts(L), A, L, 4, 5.0, changes=False)
    # Clear and removal on a throwaway spline.
    ok(m.add_spline_actor_component, A, 'Temp', confirm=True)
    tmp = A + '.Temp'
    edit(m.clear_spline_points, lambda: w.pts(tmp), A, tmp, 2)
    assert w.n(tmp) == 0
    bad(m.remove_spline_actor_component, A, tmp, 3, False, confirm=True)
    ok(m.remove_spline_actor_component, A, tmp, 0, False, confirm=True, dry_run=True)
    ok(m.remove_spline_actor_component, A, tmp, 0, False, confirm=True)
    assert all(not c['component_path'].endswith('.Temp') for c in ok(m.inspect_world_spline_components)['components'])
    return {'path': w.pts(), 'loop': w.pts(L), 'settings': w.settings()}


def mesh_stage(w):
    A, S = w.actor, w.seg
    ok(m.add_spline_mesh_actor_component, A, 'Seg', CUBE, confirm=True)
    bad(m.add_spline_mesh_actor_component, A, 'Seg', CUBE, confirm=True)
    mesh = lambda: w.mesh()
    x = mesh()
    edit(m.set_spline_mesh_endpoints, mesh, A, S, CUBE, x['start_position'], x['end_position'], x['start_tangent'], x['end_tangent'],
         [0, 0, 0], [300, 50, 0], [300, 0, 0], [300, 0, 0])
    bad(m.set_spline_mesh_endpoints, A, S, CUBE, [1, 1, 1], [300, 50, 0], [300, 0, 0], [300, 0, 0], [0, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], confirm=True)
    x = mesh()
    edit(m.set_spline_mesh_scales, mesh, A, S, CUBE, x['start_scale'], x['end_scale'], [1, 1], [0.5, 2])
    edit(m.set_spline_mesh_rolls, mesh, A, S, CUBE, 0, 0, 0.2, -0.3)
    edit(m.set_spline_mesh_forward_axis, mesh, A, S, CUBE, 0, 'Y')
    bad(m.set_spline_mesh_forward_axis, A, S, CUBE, 0, 'Z', confirm=True)        # stale expected axis
    edit(m.set_spline_mesh_forward_axis, mesh, A, S, CUBE, 1, 'X')
    edit(m.set_spline_mesh_up_direction, mesh, A, S, CUBE, mesh()['up_direction'], [0, 1, 0])
    edit(m.set_spline_mesh_offsets, mesh, A, S, CUBE, [0, 0], [0, 0], [5, 0], [0, -5])
    edit(m.set_spline_mesh_boundaries, mesh, A, S, CUBE, 0, 0, -10, 40)
    # Reversed boundaries are allowed by design (they reverse the mapping); only finite +/-1e9 is enforced.
    edit(m.set_spline_mesh_boundaries, mesh, A, S, CUBE, -10, 40, 50, 10)
    bad(m.set_spline_mesh_boundaries, A, S, CUBE, 50, 10, 0, 2e9, confirm=True)
    edit(m.set_spline_mesh_boundaries, mesh, A, S, CUBE, 50, 10, -10, 40)
    edit(m.set_spline_mesh_smooth_interpolation, mesh, A, S, CUBE, False, True)
    sl = ok(m.sample_spline_mesh_slices, A, S, CUBE, sample_count=6)
    assert len(sl['samples'] if 'samples' in sl else sl['slices']) == 6, str(sl)[:300]
    bad(m.sample_spline_mesh_slices, A, S, CUBE, alpha_start=0.9, alpha_end=0.1)
    edit(m.set_spline_mesh_asset, mesh, A, S, CUBE, CYL)
    bad(m.set_spline_mesh_asset, A, S, CUBE, CUBE, confirm=True)                     # stale expected asset
    # Fit to the open spline's segment 0 and the closed loop's closing segment.
    seg = lambda c, i: ok(m.inspect_spline_segments, A, c)['segments'][i]
    s0 = seg(w.path, 0)
    # Expected values guard the spline mesh's current endpoints/tangents; the source segment is selected by index.
    cur = lambda c: (lambda x: (x['start_position'], x['end_position'], x['start_tangent'], x['end_tangent']))(w.mesh(c))
    edit(m.fit_spline_mesh_to_segment, mesh, A, S, CYL, A, w.path, 3, False, 0, *cur(S))
    assert close(mesh()['end_position'], s0['end_position']) and close(mesh()['end_tangent'], s0['unit_interval_end_tangent']), (mesh(), s0)
    bad(m.fit_spline_mesh_to_segment, A, S, CYL, A, w.path, 3, False, 7, *cur(S), confirm=True)
    bad(m.fit_spline_mesh_to_segment, A, S, CYL, A, w.path, 4, False, 0, *cur(S), confirm=True)
    ok(m.add_spline_mesh_actor_component, A, 'Seg2', CUBE, confirm=True)
    s3 = seg(w.loop, 3)
    assert s3['closing_segment'], s3
    edit(m.fit_spline_mesh_to_segment, lambda: w.mesh(w.seg2), A, w.seg2, CUBE, A, w.loop, 4, True, 3, *cur(w.seg2))
    assert close(w.mesh(w.seg2)['end_position'], [0, 0, 0]) and close(w.mesh(w.seg2)['start_position'], [0, 300, 0]), w.mesh(w.seg2)
    # Removal of a throwaway spline mesh.
    ok(m.add_spline_mesh_actor_component, A, 'Gone', CUBE, confirm=True)
    bad(m.remove_spline_mesh_actor_component, A, A + '.Gone', CYL, confirm=True)
    ok(m.remove_spline_mesh_actor_component, A, A + '.Gone', CUBE, confirm=True)
    assert all(not c['component_path'].endswith('.Gone') for c in ok(m.inspect_world_spline_mesh_components)['components'])
    return {'seg': mesh(), 'seg2': w.mesh(w.seg2)}


def snapshot(w):
    meshes = {c['component_path'].rsplit('.', 1)[1]: {k: v for k, v in c.items() if k != 'registered'} for c in ok(m.inspect_world_spline_mesh_components)['components']}
    return {'path': w.pts(), 'loop': w.pts(w.loop), 'settings': w.settings(), 'loop_settings': w.settings(w.loop), 'meshes': meshes}


def prepare():
    cleanup()
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    actor = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.Actor'}, timeout=60).text
    w = World(actor)
    bad(m.add_spline_actor_component, actor, 'Path')          # confirmation required
    ok(m.add_spline_actor_component, actor, 'Path', confirm=True)
    out = {'spline': spline_stage(w), 'mesh': mesh_stage(w)}
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).is_success
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'actor': actor, 'snapshot': snapshot(w)}, indent=1))
    print('splines and spline meshes prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot(World(st['actor']))))
    diff = [k for k in st['snapshot'] if got.get(k) != st['snapshot'][k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), st['snapshot'][k]) for k in diff})[:2000])
    print('splines and spline meshes identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
