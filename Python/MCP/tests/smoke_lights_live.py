"""Light shadow flags, falloff exponent, IES profiles, Lightmass World Settings and remaining volume classes: prepare, restart, verify.

Usage: smoke_lights_live.py prepare|verify|cleanup. Imports a generated .ies light profile, then on a scratch map drives
point/spot falloff exponent, the four shadow-type flags, IES texture assignment and IES brightness, World Settings
Lightmass environment color, visibility cell size, volumetric-lightmap-only flag, time-dilation/frame-time limits with
the optional stale-value maps, and Audio/LightmassCharacterIndirectDetail/PrecomputedVisibilityOverride creation in
every brush shape. Each edit is rejected with a stale expected value, dry-run checked, then applied. The final state
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
MAP = '/Game/UE5MCP_Test/MCP_Lights2'
IES_PKG = '/Game/UE5MCP_Test/IES_MCP'
IES = IES_PKG + '.IES_MCP'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'lights2.json'
IES_FILE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'mcp_test.ies'
IES_TEXT = 'IESNA:LM-63-2002\n[TEST] MCP\nTILT=NONE\n1 1000 1 3 1 1 2 0 0 0\n1 1 100\n0 45 90\n0\n1000 800 0\n'


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
    return f'{MAP}.MCP_Lights2:PersistentLevel.{name}'


def light(name):
    return next(x for x in ok(m.inspect_world_light_components)['lights'] if x['actor_path'] == actor(name))


# ---------------------------------------------------------------- falloff exponent, shadow flags, IES
def light_stage():
    for t, n in (('Point', 'MCP_point'), ('Spot', 'MCP_spot'), ('Rect', 'MCP_rect')):
        ok(m.create_light_actor, t, n, [0, len(n) * 100, 300], confirm=True)
    for n in ('MCP_point', 'MCP_spot'):
        L = lambda n=n: light(n)
        c = L()['component_path']
        cur = L()['falloff_exponent']
        bad(m.set_light_scalar, actor(n), c, 'LightFalloffExponent', cur + 1, 4, confirm=True)
        bad(m.set_light_scalar, actor(n), c, 'LightFalloffExponent', cur, 0, confirm=True)       # must be positive
        bad(m.set_light_scalar, actor(n), c, 'LightFalloffExponent', cur, 1001, confirm=True)
        edit(m.set_light_scalar, L, actor(n), c, 'LightFalloffExponent', cur, 2.5)
        assert L()['falloff_exponent'] == 2.5 and L()['inverse_squared_falloff'], L()   # inverse-square flag untouched
    rc = light('MCP_rect')['component_path']
    bad(m.set_light_scalar, actor('MCP_rect'), rc, 'LightFalloffExponent', 8, 4, confirm=True)    # point family only
    # Shadow-type flags on the point light.
    P = lambda: light('MCP_point')
    pc = P()['component_path']
    for field, key in (('CastStaticShadows', 'cast_static_shadows'), ('CastDynamicShadows', 'cast_dynamic_shadows'),
                       ('bCastVolumetricShadow', 'cast_volumetric_shadow'), ('CastTranslucentShadows', 'cast_translucent_shadows')):
        cur = P()[key]
        bad(m.set_light_bool, actor('MCP_point'), pc, field, not cur, cur, confirm=True)
        edit(m.set_light_bool, P, actor('MCP_point'), pc, field, cur, not cur)
        assert P()[key] is (not cur) and P()['cast_shadows'], P()
        edit(m.set_light_bool, P, actor('MCP_point'), pc, field, not cur, not cur, changes=False)   # no-op
    # IES profile: brightness cannot be enabled before a profile is assigned.
    bad(m.set_light_bool, actor('MCP_spot'), light('MCP_spot')['component_path'], 'bUseIESBrightness', False, True, confirm=True)
    for n in ('MCP_point', 'MCP_spot'):
        L = lambda n=n: light(n)
        c = L()['component_path']
        bad(m.set_light_texture, actor(n), c, 'IESTexture', IES, IES, confirm=True)
        bad(m.set_light_texture, actor(n), c, 'IESTexture', '', '/Engine/EngineResources/DefaultTexture.DefaultTexture', confirm=True)  # not a light profile
        edit(m.set_light_texture, L, actor(n), c, 'IESTexture', '', IES)
        assert L()['ies_texture_path'] == IES, L()
        edit(m.set_light_bool, L, actor(n), c, 'bUseIESBrightness', False, True)
        assert L()['use_ies_brightness'], L()
        edit(m.set_light_scalar, L, actor(n), c, 'IESBrightnessScale', L()['ies_brightness_scale'], 3)
    S = lambda: light('MCP_spot')
    sc = S()['component_path']
    edit(m.set_light_texture, S, actor('MCP_spot'), sc, 'IESTexture', IES, '')                # clear the profile
    assert S()['ies_texture_path'] in ('', 'None'), S()
    edit(m.set_light_texture, S, actor('MCP_spot'), sc, 'IESTexture', '', IES)
    return {n: light(n) for n in ('MCP_point', 'MCP_spot', 'MCP_rect')}


# ---------------------------------------------------------------- World Settings Lightmass, visibility, time dilation
def ws():
    return ok(m.inspect_editor_world_settings)


def settings_state():
    w = ws()
    keys = ('VisibilityCellSize', 'MinGlobalTimeDilation', 'MaxGlobalTimeDilation', 'MinCinematicTimeDilation',
            'MaxCinematicTimeDilation', 'MinUndilatedFrameTime', 'MaxUndilatedFrameTime')
    return {'numeric': {k: w['numeric_settings'][k] for k in keys}, 'force_vlm': w['bool_settings']['bForceVolumetricLightmapsOnly'],
            'env': w['color_settings']['LightmassSettings.EnvironmentColor']}


def world_stage():
    W = ws()['world_path']
    S = settings_state
    E = 'LightmassSettings.EnvironmentColor'
    env = S()['env']
    new = {'R': 40, 'G': 80, 'B': 120, 'A': 255}
    bad(m.set_editor_world_settings, color_settings={E: new}, expected_color_settings={E: {**env, 'R': 1}}, world_path=W, confirm=True)
    bad(m.set_editor_world_settings, color_settings={E: new}, world_path=W, confirm=True)                    # expected map required
    bad(m.set_editor_world_settings, color_settings={E: {**new, 'G': 256}}, expected_color_settings={E: env}, world_path=W, confirm=True)
    bad(m.set_editor_world_settings, color_settings={E: new}, expected_color_settings={E: env}, world_path='/Game/Nope.Nope', confirm=True)
    edit(m.set_editor_world_settings, S, color_settings={E: new}, expected_color_settings={E: env}, world_path=W)
    assert S()['env'] == new, S()
    # Visibility cell size and volumetric-lightmap-only flag, with optional stale guards.
    n = S()['numeric']
    bad(m.set_editor_world_settings, numeric_settings={'VisibilityCellSize': 0}, world_path=W, confirm=True)
    bad(m.set_editor_world_settings, numeric_settings={'VisibilityCellSize': 300}, expected_numeric_settings={'VisibilityCellSize': n['VisibilityCellSize'] + 1}, world_path=W, confirm=True)
    bad(m.set_editor_world_settings, numeric_settings={'VisibilityCellSize': 300}, expected_numeric_settings={'MaxGlobalTimeDilation': n['MaxGlobalTimeDilation']}, world_path=W, confirm=True)  # guard key not requested
    edit(m.set_editor_world_settings, S, numeric_settings={'VisibilityCellSize': 300}, expected_numeric_settings={'VisibilityCellSize': n['VisibilityCellSize']}, world_path=W)
    bad(m.set_editor_world_settings, bool_settings={'bForceVolumetricLightmapsOnly': True}, expected_bool_settings={'bForceVolumetricLightmapsOnly': True}, world_path=W, confirm=True)
    edit(m.set_editor_world_settings, S, bool_settings={'bForceVolumetricLightmapsOnly': True}, expected_bool_settings={'bForceVolumetricLightmapsOnly': False}, world_path=W)
    # Time-dilation and frame-time limits: min<=max checked on the proposed pair before any edit.
    before = S()
    bad(m.set_editor_world_settings, numeric_settings={'MinGlobalTimeDilation': 30, 'VisibilityCellSize': 400}, world_path=W, confirm=True)   # 30 > max 20
    bad(m.set_editor_world_settings, numeric_settings={'MinUndilatedFrameTime': 0.5}, world_path=W, confirm=True)                      # > max 0.4
    bad(m.set_editor_world_settings, numeric_settings={'MaxCinematicTimeDilation': 20000}, world_path=W, confirm=True)
    assert S() == before, 'refused mixed request edited a field'
    limits = {'MinGlobalTimeDilation': 0.01, 'MaxGlobalTimeDilation': 8, 'MinCinematicTimeDilation': 0.05,
              'MaxCinematicTimeDilation': 4, 'MinUndilatedFrameTime': 0.001, 'MaxUndilatedFrameTime': 0.25}
    edit(m.set_editor_world_settings, S, numeric_settings=limits, expected_numeric_settings={k: before['numeric'][k] for k in limits}, world_path=W)
    got = S()['numeric']
    assert all(abs(got[k] - v) < 1e-6 for k, v in limits.items()) and got['VisibilityCellSize'] == 300, got
    return S()


# ---------------------------------------------------------------- remaining volume classes in every shape
def volume_stage():
    out = {}
    for t in ('Audio', 'LightmassCharacterIndirectDetail', 'PrecomputedVisibilityOverride'):
        for i, (fn, extra) in enumerate(((m.create_box_volume, ([100, 100, 100],)), (m.create_cylinder_volume, (100, 200)),
                                         (m.create_sphere_volume, (100,)), (m.create_cone_volume, (100, 200)))):
            name = f'{t[:12]}{i}'
            pos = [i * 400, len(t) * 50, 0]
            d = ok(fn, t, name, pos, *extra, confirm=True, dry_run=True)
            assert d['dry_run'], d
            r = ok(fn, t, name, pos, *extra, confirm=True, dry_run=False)
            out[name] = ok(m.inspect_volume_brush_builder, r['actor_path'])['shape']
    classes = {v['actor_path'].rsplit('.', 1)[1]: v['class_path'] for v in ok(m.inspect_world_volume_page, 0, 128)['volumes']}
    for name in out:
        want = {'Audio': 'AudioVolume', 'LightmassCha': 'LightmassCharacterIndirectDetailVolume', 'PrecomputedV': 'PrecomputedVisibilityOverrideVolume'}[name[:-1]]
        assert classes[name] == '/Script/Engine.' + want, (name, classes[name])
    return out


def snapshot():
    lights = {x['actor_path'].rsplit('.', 1)[1]: {k: v for k, v in x.items() if k != 'registered'} for x in ok(m.inspect_world_light_components)['lights']}
    vols = {v['actor_path'].rsplit('.', 1)[1]: [v['class_path'], v['bounds_extent'], ok(m.inspect_volume_brush_builder, v['actor_path'])['polygon_count']]
            for v in ok(m.inspect_world_volume_page, 0, 128)['volumes'] if 'DefaultPhysicsVolume' not in v['actor_path']}
    return {'lights': lights, 'settings': settings_state(), 'volumes': vols}


def prepare():
    cleanup()
    IES_FILE.parent.mkdir(parents=True, exist_ok=True)
    IES_FILE.write_text(IES_TEXT)
    ok(m.import_texture, str(IES_FILE), '/Game/UE5MCP_Test', 'IES_MCP', dry_run=True)
    ok(m.import_texture, str(IES_FILE), '/Game/UE5MCP_Test', 'IES_MCP', save=True)
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    light_stage()
    world_stage()
    volume_stage()
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).is_success
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1))
    print('lights prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot()))
    want = st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('lights, world settings and volumes identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': IES_PKG}, timeout=180)
    STATE.unlink(missing_ok=True)
    IES_FILE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
