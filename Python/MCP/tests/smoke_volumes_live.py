"""World volume authoring on a scratch map: prepare, restart, verify.

Usage: smoke_volumes_live.py prepare|verify|cleanup. Creates box volumes of every standard native type plus cylinder,
sphere and cone brushes (solid, hollow, tessellated, side-aligned), then drives the volume MCP tools: inventory and page
filters, point queries, physics/pain settings, pain damage type, brush collision (overlap events, mode, channel response,
object type, profile), cached overlaps, cull-distance entries/table/enabled, brush polygons, builder recipes, shape
replacement (box/cylinder/sphere/cone), wireframe color and deletion. Each edit is rejected with a stale expected value,
dry-run checked, then applied. The final volumes must survive a cold editor restart.
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
MAP = '/Game/UE5MCP_Test/MCP_Volumes'
DAMAGE_BP = '/Game/UE5MCP_Test/BP_MCP_Damage'
DAMAGE = DAMAGE_BP + '.BP_MCP_Damage_C'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'volumes.json'


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


def strip(d):
    return {k: v for k, v in d.items() if k not in ('scope', 'package_dirty')}


def actor(name):
    return f'{MAP}.MCP_Volumes:PersistentLevel.{name}'


def make(fn, vtype, name, *a, **kw):
    """Create a volume: unconfirmed and dry-run calls must leave the world unchanged."""
    count = lambda: ok(m.inspect_world_volume_page)['filtered_volume_count']
    n = count()
    bad(fn, vtype, name, *a, **kw)                                   # confirmation required
    d = ok(fn, vtype, name, *a, confirm=True, dry_run=True, **kw)
    assert d['dry_run'] and count() == n, d
    r = ok(fn, vtype, name, *a, confirm=True, dry_run=False, **kw)
    assert count() == n + 1 and r['actor_path'] == actor(name) and r['polygon_count'] > 0, r
    bad(fn, vtype, name, *a, confirm=True, dry_run=False, **kw)      # duplicate name
    return r


# ---------------------------------------------------------------- creation of every type and shape
def create_stage():
    for t in ('Physics', 'Pain', 'Blocking', 'Trigger', 'CameraBlocking', 'KillZ', 'CullDistance',
              'LightmassImportance', 'PrecomputedVisibility'):
        make(m.create_box_volume, t, t + 'V', [len(t) * 300, 0, 100], [100, 100, 100])
    bad(m.create_box_volume, 'Bogus', 'BogusV', [0, 0, 0], [100, 100, 100], confirm=True)
    bad(m.create_box_volume, 'Trigger', 'TinyV', [0, 0, 0], [0.5, 100, 100], confirm=True)
    bad(m.create_box_volume, 'Trigger', 'FarV', [2e9, 0, 0], [100, 100, 100], confirm=True)
    bad(m.create_box_volume, 'Trigger', 'Bad Name', [0, 0, 0], [100, 100, 100], confirm=True)
    bad(m.create_box_volume, 'Trigger', 'HollowTessV', [0, 0, 0], [100, 100, 100], confirm=True, hollow=True, wall_thickness=20, tessellated=True)
    bad(m.create_box_volume, 'Trigger', 'ThickV', [0, 0, 0], [100, 100, 100], confirm=True, hollow=True, wall_thickness=200)
    make(m.create_box_volume, 'Trigger', 'HollowBoxV', [0, 3000, 0], [100, 100, 100], hollow=True, wall_thickness=40)
    make(m.create_box_volume, 'Trigger', 'TessBoxV', [0, 3500, 0], [100, 100, 100], tessellated=True)
    make(m.create_cylinder_volume, 'Trigger', 'CylV', [0, 4000, 0], 150, 300, sides=12)
    make(m.create_cylinder_volume, 'Trigger', 'HollowCylV', [0, 4500, 0], 150, 300, sides=8, hollow=True, inner_radius=80, align_to_side=True)
    bad(m.create_cylinder_volume, 'Trigger', 'BoreV', [0, 0, 0], 150, 300, confirm=True, dry_run=False, hollow=True, inner_radius=150)
    bad(m.create_cylinder_volume, 'Trigger', 'SidesV', [0, 0, 0], 150, 300, sides=2, confirm=True, dry_run=False)
    make(m.create_sphere_volume, 'Trigger', 'SphereV', [0, 5000, 0], 200, tessellation=2)
    bad(m.create_sphere_volume, 'Trigger', 'Tess6V', [0, 0, 0], 200, tessellation=6, confirm=True, dry_run=False)
    make(m.create_cone_volume, 'Trigger', 'ConeV', [0, 5500, 0], 150, 300, sides=10)
    make(m.create_cone_volume, 'Trigger', 'HollowConeV', [0, 6000, 0], 150, 300, sides=6, hollow=True, inner_radius=60, inner_height=200, align_to_side=True)
    bad(m.create_cone_volume, 'Trigger', 'ConeHV', [0, 0, 0], 150, 300, hollow=True, inner_radius=60, inner_height=400, confirm=True, dry_run=False)
    B = lambda n: ok(m.inspect_volume_brush_builder, actor(n))
    assert B('HollowBoxV')['hollow'] and B('HollowBoxV')['wall_thickness'] == 40, B('HollowBoxV')
    assert B('TessBoxV')['tessellated'] and B('TessBoxV')['polygon_count'] > 6, B('TessBoxV')
    assert B('CylV')['shape'] == 'Cylinder' and B('SphereV')['shape'] == 'Sphere' and B('ConeV')['shape'] == 'Cone', (B('CylV'), B('SphereV'), B('ConeV'))
    assert B('HollowCylV')['hollow'] and B('HollowConeV')['hollow'], (B('HollowCylV'), B('HollowConeV'))
    return {n: strip(B(n)) for n in ('HollowBoxV', 'TessBoxV', 'CylV', 'HollowCylV', 'SphereV', 'ConeV', 'HollowConeV')}


# ---------------------------------------------------------------- inventory, pages, point queries, polygons
def query_stage():
    full = ok(m.inspect_world_volumes)
    page = ok(m.inspect_world_volume_page, 0, 3)
    assert len(page['volumes']) == 3 and page['has_more'] and page['next_start'] == 3, page
    rest = ok(m.inspect_world_volume_page, 3, 128)
    paths = [v['actor_path'] for v in page['volumes'] + rest['volumes']]
    assert paths == sorted(paths) and len(paths) == page['filtered_volume_count'], paths
    assert set(paths) <= {v['actor_path'] for v in full['volumes']}, 'page missing from inventory'
    trig = ok(m.inspect_world_volume_page, 0, 128, '/Script/Engine.TriggerVolume')['volumes']
    assert {v['actor_path'] for v in trig} >= {actor('TriggerV'), actor('CylV'), actor('ConeV')} and all(v['class_path'] == '/Script/Engine.TriggerVolume' for v in trig), trig
    bad(m.inspect_world_volume_page, 0, 0)
    bad(m.inspect_world_volume_page, 0, 10, '/Script/Engine.NotAClass')
    a = actor('PhysicsV')                                           # box centred (2100,0,100) half-extent 100
    assert ok(m.query_volume_point, a, [2100, 0, 100])['encompasses_point_or_sphere']
    far = ok(m.query_volume_point, a, [2100, 0, 500])
    assert not far['encompasses_point_or_sphere'] and far['native_distance_to_point'] > 0, far
    assert ok(m.query_volume_point, a, [2100, 0, 250], radius=100)['encompasses_point_or_sphere']
    bad(m.query_volume_point, a, [2100, 0, 100], radius=-1)
    bad(m.query_volume_point, a, [2e9, 0, 0])
    bad(m.query_volume_point, actor('Missing'), [0, 0, 0])
    polys = ok(m.inspect_volume_brush_polygons, actor('CylV'), 0, 128)
    assert polys['polygon_count'] == len(polys['polygons']) and not polys['has_more'], polys['polygon_count']
    assert all(p['vertex_count'] >= 3 for p in polys['polygons'])
    bad(m.inspect_volume_brush_polygons, actor('CylV'), 0, 0)
    return {'cyl_polygons': polys['polygon_count'], 'trigger_count': len(trig)}


# ---------------------------------------------------------------- physics and pain settings
def settings_stage():
    a = actor('PhysicsV')
    S = lambda: strip(ok(m.inspect_physics_volume, a))
    for field, cur, key, val in (('Priority', 0, 'priority', 5), ('TerminalVelocity', 4000, 'terminal_velocity', 2500),
                                 ('FluidFriction', S()['fluid_friction'], 'fluid_friction', 1.5)):
        bad(m.set_physics_volume_setting, a, field, cur + 1, scalar_value=val, confirm=True)
        edit(m.set_physics_volume_setting, S, a, field, cur, scalar_value=val)
        assert abs(S()[key] - val) < 1e-4, S()
    for field, key in (('WaterVolume', 'water_volume'), ('PhysicsOnContact', 'physics_on_contact')):
        bad(m.set_physics_volume_setting, a, field, 1, bool_value=True, confirm=True)
        edit(m.set_physics_volume_setting, S, a, field, 0, bool_value=True)
        assert S()[key] is True
    bad(m.set_physics_volume_setting, a, 'TerminalVelocity', 2500, scalar_value=-1, confirm=True)
    bad(m.set_physics_volume_setting, a, 'Gravity', 0, scalar_value=1, confirm=True)
    bad(m.set_physics_volume_setting, a, 'Priority', 5, scalar_value=6)              # confirmation required
    edit(m.set_physics_volume_setting, S, a, 'Priority', 5, scalar_value=5, changes=False)   # no-op
    p = actor('PainV')
    P = lambda: strip(ok(m.inspect_pain_volume, p))
    edit(m.set_pain_volume_setting, P, p, 'DamagePerSec', 1, scalar_value=25)
    edit(m.set_pain_volume_setting, P, p, 'PainInterval', 1, scalar_value=0.5)
    bad(m.set_pain_volume_setting, p, 'PainInterval', 0.5, scalar_value=0, confirm=True)
    bad(m.set_pain_volume_setting, p, 'DamagePerSec', 1, scalar_value=30, confirm=True)
    edit(m.set_pain_volume_setting, P, p, 'EntryPain', 1, bool_value=False)
    edit(m.set_pain_volume_setting, P, p, 'PainCausing', 1, bool_value=False)
    assert P()['damage_per_second'] == 25 and P()['pain_interval'] == 0.5 and not P()['entry_pain'] and not P()['pain_causing'], P()
    # Damage type: only UDamageType subclasses are accepted.
    cur = P()['damage_type_path']
    bad(m.set_pain_volume_damage_type, p, '/Script/Engine.Actor', '/Script/Engine.DamageType', confirm=True)
    bad(m.set_pain_volume_damage_type, p, cur, '/Script/Engine.Actor', confirm=True)
    bad(m.set_pain_volume_damage_type, p, cur, '', confirm=True)
    edit(m.set_pain_volume_damage_type, P, p, cur, '/Script/Engine.DamageType', changes=False)   # native base class, no-op
    m.create_blueprint(DAMAGE_BP, 'DamageType')
    httpx.post(BASE + '/assets/save', json={'AssetPath': DAMAGE_BP}, timeout=600)
    bad(m.set_pain_volume_damage_type, p, cur, DAMAGE_BP + '.BP_MCP_Damage', confirm=True)   # blueprint asset, not its class
    edit(m.set_pain_volume_damage_type, P, p, cur, DAMAGE)
    assert P()['damage_type_path'] == DAMAGE, P()
    return {'physics': S(), 'pain': P()}


# ---------------------------------------------------------------- brush collision
def collision_stage():
    a = actor('PhysicsV')
    C = lambda: strip(ok(m.inspect_volume_collision, a))
    comp = C()['component_path']
    resp = lambda ch: next(r['response'] for r in C()['channel_responses'] if r['channel'] == ch)
    bad(m.set_volume_overlap_events, a, comp, False, False, confirm=True)
    edit(m.set_volume_overlap_events, C, a, comp, True, False)
    assert not C()['generate_overlap_events']
    bad(m.set_volume_collision_enabled, a, comp, 3, 'QueryAndPhysics', confirm=True)
    bad(m.set_volume_collision_enabled, a, comp, 1, 'Everything', confirm=True)
    edit(m.set_volume_collision_enabled, C, a, comp, 1, 'QueryAndProbe')
    assert C()['collision_enabled'] == 5, C()['collision_enabled']
    bad(m.set_volume_collision_response, a, comp, 2, 2, 'Block', confirm=True)
    bad(m.set_volume_collision_response, a, comp, 32, 1, 'Block', confirm=True)
    edit(m.set_volume_collision_response, C, a, comp, 2, resp(2), 'Block')
    assert resp(2) == 2 and C()['collision_profile'] == 'Custom', C()['collision_profile']
    bad(m.set_volume_collision_object_type, a, comp, 7, 0, confirm=True)
    edit(m.set_volume_collision_object_type, C, a, comp, C()['object_type'], 0)
    assert C()['object_type'] == 0
    profiles = ok(m.inspect_volume_collision_profiles)
    assert profiles['profile_count'] > 0 and len(profiles['channels']) == 32, profiles['profile_count']
    names = {p['name'] for p in profiles['profiles']}
    assert {'BlockAll', 'OverlapAll'} <= names, names
    t = actor('TriggerV')
    T = lambda: strip(ok(m.inspect_volume_collision, t))
    tc = T()['component_path']
    bad(m.set_volume_collision_profile, t, tc, 'BlockAll', 'OverlapAll', confirm=True)
    bad(m.set_volume_collision_profile, t, tc, T()['collision_profile'], 'NoSuchProfile', confirm=True)
    edit(m.set_volume_collision_profile, T, t, tc, T()['collision_profile'], 'BlockAll')
    assert T()['collision_profile'] == 'BlockAll' and all(r['response'] == 2 for r in T()['channel_responses'][:3]), T()
    edit(m.set_volume_collision_profile, T, t, tc, 'BlockAll', 'BlockAll', changes=False)
    ov = ok(m.inspect_volume_cached_overlaps, a, comp)
    assert isinstance(ov['actors'] if 'actors' in ov else ov['overlapping_actors'], list), ov
    bad(m.inspect_volume_cached_overlaps, a, tc)
    return {'physics': C(), 'trigger': T()}


# ---------------------------------------------------------------- cull distance
def cull_stage():
    a = actor('CullDistanceV')
    C = lambda: strip(ok(m.inspect_cull_distance_volume, a))
    table = lambda: [[e['size'], e['cull_distance']] for e in C()['entries']]
    assert table() == [[0, 0], [10000, 0]], table()
    bad(m.set_cull_distance_volume_entry, a, 2, 1, 10000, 1, 10000, 5000, confirm=True)
    bad(m.set_cull_distance_volume_entry, a, 3, 1, 10000, 0, 10000, 5000, confirm=True)
    bad(m.set_cull_distance_volume_entry, a, 2, 2, 10000, 0, 10000, 5000, confirm=True)
    bad(m.set_cull_distance_volume_entry, a, 2, 1, 10000, 0, 10000, -1, confirm=True)
    edit(m.set_cull_distance_volume_entry, C, a, 2, 1, 10000, 0, 10000, 5000)
    assert table() == [[0, 0], [10000, 5000]], table()
    new = [[500, 2000], [0, 0], [10000, 5000], [500, 2000]]
    bad(m.replace_cull_distance_volume_table, a, [[0, 0]], new, confirm=True)
    edit(m.replace_cull_distance_volume_table, C, a, table(), new)
    assert table() == new, table()
    edit(m.replace_cull_distance_volume_table, C, a, new, [])
    assert table() == [] and C()['entry_count'] == 0
    edit(m.replace_cull_distance_volume_table, C, a, [], new[:3])
    page = ok(m.inspect_cull_distance_volume, a, 1, 1)
    assert [e['index'] for e in page['entries']] == [1] and page['more_entries'], page
    bad(m.set_cull_distance_volume_enabled, a, False, False, confirm=True)
    edit(m.set_cull_distance_volume_enabled, C, a, True, False)
    assert not C()['enabled']
    return C()


# ---------------------------------------------------------------- brush shape replacement and wireframe color
def brush_stage():
    a = actor('TriggerV')
    B = lambda: strip(ok(m.inspect_volume_brush_builder, a))
    poly = lambda: ok(m.inspect_volume_brush_polygons, a, 0, 128)
    inv = lambda: next(v for v in ok(m.inspect_world_volume_page, 0, 128)['volumes'] if v['actor_path'] == a)

    def replace(shape, extent, **kw):
        b, v = B(), inv()
        args = (a, v['actor_guid'], v['label'], b['model_path'], b['polygon_count'], shape, extent)
        bad(m.replace_volume_brush_shape, a, v['actor_guid'], v['label'], b['model_path'], b['polygon_count'] + 1, shape, extent, confirm=True, dry_run=False, **kw)
        bad(m.replace_volume_brush_shape, a, '0' * 32, v['label'], b['model_path'], b['polygon_count'], shape, extent, confirm=True, dry_run=False, **kw)
        bad(m.replace_volume_brush_shape, *args, dry_run=False, **kw)    # confirmation required
        before = poly()
        ok(m.replace_volume_brush_shape, *args, confirm=True, dry_run=True, **kw)
        assert poly() == before and B() == b, 'dry run replaced brush'
        r = ok(m.replace_volume_brush_shape, *args, confirm=True, dry_run=False, **kw)
        assert B()['shape'] == shape, B()
        return r

    replace('Cylinder', [120, 120, 80], sides=7)
    assert B()['polygon_count'] == 9, B()                      # 7 sides + 2 caps
    replace('Sphere', [90, 90, 90], tessellation=1)
    assert B()['polygon_count'] == 8, B()                      # octahedron
    replace('Cone', [100, 100, 150], sides=5)
    assert B()['polygon_count'] == 6, B()                      # 5 sides + base
    replace('Cone', [100, 100, 150], sides=6, hollow=True, inner_radius=40, inner_height=100)
    assert B()['hollow'], B()
    bad(m.replace_volume_brush_shape, a, inv()['actor_guid'], inv()['label'], B()['model_path'], B()['polygon_count'], 'Sphere', [90, 90, 90], tessellation=1, hollow=True, confirm=True, dry_run=False)
    bad(m.replace_volume_brush_shape, a, inv()['actor_guid'], inv()['label'], B()['model_path'], B()['polygon_count'], 'Torus', [90, 90, 90], confirm=True, dry_run=False)
    replace('Box', [60, 70, 80], hollow=True, wall_thickness=20)
    assert B()['size_x'] == 120 and B()['size_y'] == 140 and B()['size_z'] == 160 and B()['hollow'], B()
    assert inv()['bounds_extent'] == [60, 70, 80], inv()
    # Wireframe color.
    v = inv()
    col = lambda: (inv()['brush_color_bytes'], inv()['custom_brush_color_enabled'])
    bad(m.set_volume_brush_color, a, v['actor_guid'], v['label'], [1, 2, 3, 4], [255, 0, 0, 255], v['custom_brush_color_enabled'], True, confirm=True, dry_run=False)
    bad(m.set_volume_brush_color, a, v['actor_guid'], v['label'], v['brush_color_bytes'], [256, 0, 0, 255], v['custom_brush_color_enabled'], True, confirm=True, dry_run=False)
    edit(m.set_volume_brush_color, col, a, v['actor_guid'], v['label'], v['brush_color_bytes'], [255, 64, 0, 255], v['custom_brush_color_enabled'], True)
    assert col() == ([255, 64, 0, 255], True), col()
    edit(m.set_volume_brush_color, col, a, v['actor_guid'], v['label'], [255, 64, 0, 255], [255, 64, 0, 255], True, False)
    assert col() == ([255, 64, 0, 255], False), col()            # disabling keeps the stored bytes
    edit(m.set_volume_brush_color, col, a, v['actor_guid'], v['label'], [255, 64, 0, 255], [10, 20, 30, 255], False, True)
    return {'builder': B(), 'polygons': strip(poly())}


# ---------------------------------------------------------------- deletion
def delete_stage():
    a = actor('KillZV')
    c = ok(m.inspect_volume_collision, a)['component_path']
    cls = '/Script/Engine.KillZVolume'
    exists = lambda: any(v['actor_path'] == a for v in ok(m.inspect_world_volume_page, 0, 128)['volumes'])
    bad(m.delete_volume, a, c, '/Script/Engine.TriggerVolume', confirm=True)
    bad(m.delete_volume, a, actor('PainV') + '.BrushComponent0', cls, confirm=True)
    bad(m.delete_volume, a, c, cls)
    edit(m.delete_volume, exists, a, c, cls)
    assert not exists()
    bad(m.delete_volume, a, c, cls, confirm=True)
    return True


def snapshot():
    vols = ok(m.inspect_world_volume_page, 0, 128)['volumes']
    out = {}
    for v in vols:
        a = v['actor_path']
        if 'DefaultPhysicsVolume' in a:
            continue
        name = a.rsplit('.', 1)[1]
        e = {'inventory': {k: v[k] for k in ('class_path', 'label', 'actor_guid', 'custom_brush_color_enabled', 'brush_color_bytes', 'bounds_origin', 'bounds_extent')},
             'collision': {k: x for k, x in ok(m.inspect_volume_collision, a).items() if k not in ('scope', 'registered', 'physics_state_created')},
             'builder': {k: x for k, x in strip(ok(m.inspect_volume_brush_builder, a)).items() if k not in ('builder_path',)},
             'polygons': ok(m.inspect_volume_brush_polygons, a, 0, 128)['polygons']}
        if v['class_path'].endswith('.PhysicsVolume'):
            e['physics'] = strip(ok(m.inspect_physics_volume, a))
        if v['class_path'].endswith('.PainCausingVolume'):
            e['pain'] = strip(ok(m.inspect_pain_volume, a))
        if v['class_path'].endswith('.CullDistanceVolume'):
            e['cull'] = strip(ok(m.inspect_cull_distance_volume, a))
        out[name] = e
    return out


def prepare():
    cleanup()
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    out = {'create': create_stage(), 'query': query_stage(), 'settings': settings_stage(), 'collision': collision_stage(),
           'cull': cull_stage(), 'brush': brush_stage(), 'delete': delete_stage()}
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).is_success
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot(), 'stages': out}, indent=1))
    print('volumes prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot()))
    want = st['snapshot']
    diff = sorted(set(got) ^ set(want)) + [k for k in want if k in got and got[k] != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want.get(k)) for k in diff})[:3000])
    print('volumes identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': DAMAGE_BP}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
