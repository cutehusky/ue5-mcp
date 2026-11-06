"""Static Mesh Nanite settings, diagnostics, component audit and force-disable override; prepare, restart, verify.

prepare: copy the engine cube, edit every typed Nanite setting through its hash guard (stale hash rejected, dry run
unchanged, real edit), reset fields to native defaults, build Nanite data and read its counters/resource sizes; place
the mesh in a scratch map for component discovery, the native material audit and the force-disable override; save.
verify (fresh editor): reload the asset and map, compare the snapshot, then delete both.
"""
import json
import sys
import time

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
PKG = '/Game/UE5MCP_Test/SM_MCP_Nanite'
SM = PKG + '.SM_MCP_Nanite'
MAP = '/Game/UE5MCP_Test/MCP_Nanite'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'nanite.json'
PLACED = {}
# field -> (kwargs for the edit, settings key, expected value after it)
EDITS = [
    ('Enabled', {'bool_value': True}, 'enabled', True),
    ('ExplicitTangents', {'bool_value': True}, 'explicit_tangents', True),
    ('LerpUVs', {'bool_value': False}, 'lerp_uvs', False),
    ('KeepPercentTriangles', {'scalar_value': 0.5}, 'keep_percent_triangles', 0.5),
    ('TrimRelativeError', {'scalar_value': 0.25}, 'trim_relative_error', 0.25),
    ('FallbackPercentTriangles', {'scalar_value': 0.75}, 'fallback_percent_triangles', 0.75),
    ('FallbackRelativeError', {'scalar_value': 2}, 'fallback_relative_error', 2),
    ('MaxEdgeLengthFactor', {'scalar_value': 4}, 'max_edge_length_factor', 4),
    ('GenerateFallback', {'enum_value': 'Enabled'}, 'fallback_generation', 1),
    ('FallbackTarget', {'enum_value': 'RelativeError'}, 'fallback_target', 2),
    ('PositionPrecision', {'scalar_value': 4}, 'position_precision', 4),
    ('NormalPrecision', {'scalar_value': 8}, 'normal_precision', 8),
    ('TangentPrecision', {'scalar_value': 6}, 'tangent_precision', 6),
    ('MinimumResidencyKB', {'scalar_value': 4096}, 'minimum_residency_kb', 4096),
]
REFUSED = [
    ('KeepPercentTriangles', {'scalar_value': 1.5}), ('MaxEdgeLengthFactor', {'scalar_value': -1}),
    ('GenerateFallback', {'enum_value': 'Sometimes'}), ('FallbackTarget', {'enum_value': 'Never'}),
    ('PositionPrecision', {'scalar_value': 99}), ('NormalPrecision', {'scalar_value': 2.5}),
    ('TangentPrecision', {'scalar_value': 40}), ('MinimumResidencyKB', {'scalar_value': -4}), ('NoSuchField', {'scalar_value': 1}),
]


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


def inspect():
    """Inspection once the asset has finished any asynchronous Nanite build."""
    for _ in range(240):
        r = ok(m.inspect_static_mesh_nanite, SM)
        if not r['compiling']:
            return r
        time.sleep(0.5)
    raise AssertionError('Nanite build did not finish')


def settings():
    return inspect()['settings']


def h():
    return inspect()['settings_hash']


def asset_stage():
    r = inspect()
    assert not r['native_nanite_enabled'] and not r['valid_nanite_data'] and r['input_triangles'] == 0, r
    assert r['material_slot_count'] == 1 and r['materials'][0]['native_supported_blend_mode'] and r['materials'][0]['native_supported_shading_models'], r
    assert r['render_lod_count'] == 1 and r['render_lods'][0]['triangles'] == 12 * 4, r
    assert r['settings']['position_precision'] == -2147483648 and r['settings']['normal_precision'] == -1, r['settings']  # Auto
    for field, kw, key, want in EDITS:
        before = settings()
        bad(m.set_static_mesh_nanite_setting, SM, 'f' * 32, field, confirm=True, **kw)                       # stale hash
        bad(m.set_static_mesh_nanite_setting, SM, h(), field, confirm=False, **kw)                          # unconfirmed
        ok(m.set_static_mesh_nanite_setting, SM, h(), field, confirm=True, dry_run=True, **kw)
        assert settings() == before, (field, 'dry run changed it')
        ok(m.set_static_mesh_nanite_setting, SM, h(), field, confirm=True, **kw)
        got = settings()[key]
        assert (abs(got - want) < 1e-6) if isinstance(want, float) else got == want, (field, got, want)
        # Every other field kept its value.
        assert {k: v for k, v in settings().items() if k != key} == {k: v for k, v in before.items() if k != key}, field
    for field, kw in REFUSED:
        bad(m.set_static_mesh_nanite_setting, SM, h(), field, confirm=True, **kw)
    # Same value: accepted without a hash change.
    before = h()
    ok(m.set_static_mesh_nanite_setting, SM, before, 'KeepPercentTriangles', scalar_value=0.5, confirm=True)
    assert h() == before
    # Auto precision through the enum form.
    ok(m.set_static_mesh_nanite_setting, SM, h(), 'TangentPrecision', enum_value='Auto', confirm=True)
    assert settings()['tangent_precision'] == -1
    ok(m.set_static_mesh_nanite_setting, SM, h(), 'TangentPrecision', scalar_value=6, confirm=True)
    # Per-field reset to native defaults: stale hash refused, dry run unchanged, then only that field changes.
    for field, key, default in (('MaxEdgeLengthFactor', 'max_edge_length_factor', 0), ('FallbackTarget', 'fallback_target', 0),
                                ('NormalPrecision', 'normal_precision', -1), ('LerpUVs', 'lerp_uvs', True)):
        before = settings()
        bad(m.reset_static_mesh_nanite_setting, SM, 'f' * 32, field, confirm=True)
        ok(m.reset_static_mesh_nanite_setting, SM, h(), field, confirm=True, dry_run=True)
        assert settings() == before
        ok(m.reset_static_mesh_nanite_setting, SM, h(), field, confirm=True)
        after = settings()
        assert after[key] == default and {k: v for k, v in after.items() if k != key} == {k: v for k, v in before.items() if k != key}, (field, after)
    bad(m.reset_static_mesh_nanite_setting, SM, h(), 'NoSuchField', confirm=True)
    # Enabled Nanite has been built: counters and resource accounting are populated.
    r = inspect()
    assert r['native_nanite_enabled'] and r['valid_nanite_data'], r
    assert r['input_triangles'] == 48 and r['input_vertices'] == 54 and r['clusters'] >= 1 and r['root_pages'] >= 1, r
    size = r['resource_size']
    assert int(size['total_bytes']) > 0 and int(size['total_bytes']) == sum(int(size[k]) for k in ('dedicated_system_bytes', 'dedicated_video_bytes', 'unknown_bytes')), size
    bad(m.inspect_static_mesh_nanite, '/Game/UE5MCP_Test/Nope.Nope')
    assert httpx.post(BASE + '/assets/save', json={'AssetPath': SM}, timeout=600).is_success


def component_stage():
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    actor = httpx.post(BASE + '/editor/actors/spawn', json={'AssetPath': SM}, timeout=300).text.strip().strip('"')
    comps = ok(m.inspect_world_static_mesh_nanite_components)
    mine = [c for c in comps['components'] if c['actor_path'] == actor]
    assert len(mine) == 1 and not comps.get('truncated'), comps
    c = mine[0]
    PLACED.update(actor=actor, component=c['component_path'])
    assert c['asset_path'] == SM and c['registered'] and c['visible'] and c['material_count'] == 1, c
    assert c['authored_nanite_enabled'] and c['native_nanite_enabled'] and c['valid_nanite_data'] and not c['disallow_nanite'], c
    a = audit()
    assert not a['has_any_error'] and a['entry_count'] == 1 and a['valid_allowing_masked'] and a['valid_disallowing_masked'], a
    assert not a['materials'][0]['has_error'] and not a['materials'][0]['unsupported_blend_mode'], a
    bad(m.audit_static_mesh_component_nanite_materials, actor, c['component_path'], '/Engine/BasicShapes/Cube.Cube')  # wrong asset
    cur = force()
    assert cur is False, c
    bad(m.set_static_mesh_component_force_disable_nanite, actor, c['component_path'], SM, True, True, confirm=True)  # stale
    ok(m.set_static_mesh_component_force_disable_nanite, actor, c['component_path'], SM, False, True, confirm=True, dry_run=True)
    assert force() is False
    ok(m.set_static_mesh_component_force_disable_nanite, actor, c['component_path'], SM, False, True, confirm=True)
    assert force() is True
    ok(m.set_static_mesh_component_force_disable_nanite, actor, c['component_path'], SM, True, True, confirm=True)  # no-op
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).is_success


def audit():
    return ok(m.audit_static_mesh_component_nanite_materials, PLACED['actor'], PLACED['component'], SM)


def force():
    c = next(c for c in ok(m.inspect_world_static_mesh_nanite_components)['components'] if c['actor_path'] == PLACED['actor'])
    return c['force_disable_nanite']


def snapshot():
    r = inspect()
    a = audit()
    for k in ('scope', 'package_dirty'):
        a.pop(k, None)
    return {'settings': r['settings'], 'hash': r['settings_hash'], 'valid': r['valid_nanite_data'], 'triangles': r['input_triangles'],
            'force_disable': force(), 'audit': a}


def prepare():
    cleanup()
    assert httpx.post(BASE + '/assets/duplicate', json={'AssetPath': '/Engine/BasicShapes/Cube.Cube', 'DestinationPath': PKG}, timeout=300).is_success
    asset_stage()
    component_stage()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'placed': PLACED, 'snapshot': snapshot()}, indent=1))
    print('nanite prepared; asset and map saved')


def verify():
    st = json.loads(STATE.read_text())
    PLACED.update(st['placed'])
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got, want = json.loads(json.dumps(snapshot())), st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('nanite settings, data and component override identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    for p in (MAP, SM):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
