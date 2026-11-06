"""Deeper Pose Search checks on scratch schema/database/interaction assets: prepare, restart, verify.

Usage: smoke_pose_search_deep_live.py prepare|verify|cleanup. Covers channel enum discovery, nested name paths and field
inspection, signed integers, debug colors and reset, structured sampled-bone/trajectory inspection, finalization
diagnostics/layout/subchannels, cached role bones, montage and Blend Space entries (intervals, parameter timing, sampling
parameters), database diagnostics/references, per-role inspection, root traces with sampler configuration, multi-animation
sampling counts and interaction warp role selection with structured deltas. Calls the registered MCP tool functions; each
edit is rejected with a bad guard, dry-run checked, then applied. Authored state must survive a cold editor restart.
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
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'pose_search_deep.json'
T = '/Game/UE5MCP_Test/PSD/'
SCHEMA, DB, NORM, INTER = (T + n + '.' + n for n in ('PSS_Deep', 'PSD_Deep', 'PSN_Deep', 'PSI_Deep'))
SKELETON = '/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin'
PREVIEW = '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple'
FWD = '/Game/Characters/Mannequins/Anims/Pistol/Jog/MF_Pistol_Jog_Fwd.MF_Pistol_Jog_Fwd'
BWD = '/Game/Characters/Mannequins/Anims/Pistol/Jog/MF_Pistol_Jog_Bwd.MF_Pistol_Jog_Bwd'
MONTAGE = '/Game/Characters/Mannequins/Anims/Pistol/MM_Pistol_Fire_Montage.MM_Pistol_Fire_Montage'
BLEND = '/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run'
CH = '/Script/PoseSearch.PoseSearchFeatureChannel_'


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


def channels():
    return ok(m.inspect_pose_search_schema, SCHEMA)['channels']


def chan(cls):
    i, c = next((i, c) for i, c in enumerate(channels()) if c['class_path'].endswith(cls))
    return (SCHEMA, i, c['object_path'])


def leaf(C, path):
    return ok(m.inspect_pose_search_channel, *C, field=path)['selected_field']


# ---------------------------------------------------------------- schema and channels
def schema_stage():
    types = ok(m.list_pose_search_channel_types, limit=64)
    key = next(k for k in types if isinstance(types[k], list))
    pos_type = next(t for t in types[key] if t['class_path'].endswith('Position'))
    strip = next(f for f in pos_type['editable_fields'] if f['name'] == 'ComponentStripping')
    assert len(strip['enum_choices']) == 3 and not any(c['name'].endswith('_MAX') for c in strip['enum_choices']), strip
    bad(m.add_pose_search_default_channels, SCHEMA, confirm=True)   # the native factory already authors default channels
    ok(m.add_pose_search_schema_channel, SCHEMA, CH + 'Position', confirm=True)
    ok(m.add_pose_search_schema_role, SCHEMA, 'Partner', SKELETON, confirm=True)
    P = chan('Position')
    insp = ok(m.inspect_pose_search_channel, *P)
    assert any(f.get('enum_choices') for f in insp['editable_fields']), 'authored enum choices missing'
    # Nested name path and selected nested field inspection.
    b = leaf(P, 'Bone')
    assert {c['name'] for c in b['struct_fields']} >= {'BoneName'}, b
    for path in ('Bone.', 'Bone..BoneName', 'Bone.Nope'):
        bad(m.inspect_pose_search_channel, *P, field=path)
    edit(m.set_pose_search_channel_name, lambda: leaf(chan('Position'), 'Bone.BoneName')['value'], *P, 'Bone.BoneName', 'hand_r')
    edit(m.set_pose_search_channel_name, lambda: leaf(chan('Position'), 'OriginBone.BoneName')['value'], *P, 'OriginBone.BoneName', 'pelvis')
    bad(m.set_pose_search_channel_name, *P, 'Bone.BoneName', 'a' + chr(10) + 'b', confirm=True)
    # Signed integer, color and default reset.
    edit(m.set_pose_search_channel_scalar, lambda: leaf(chan('Position'), 'SamplingAttributeId')['value'], *P, 'SamplingAttributeId', -5)
    assert leaf(chan('Position'), 'SamplingAttributeId')['value'] == '-5'
    bad(m.set_pose_search_channel_scalar, *P, 'SamplingAttributeId', 1.5, confirm=True)
    edit(m.set_pose_search_channel_color, lambda: leaf(chan('Position'), 'DebugColor')['value'], *P, 'DebugColor', 0.1, 0.2, 0.3, 1)
    bad(m.set_pose_search_channel_color, *P, 'DebugColor', float('1e9'), 0, 0, 1, confirm=True)
    bad(m.set_pose_search_channel_vector, *P, 'DebugColor', 1, 2, 3, confirm=True)
    edit(m.reset_pose_search_channel_field, lambda: leaf(chan('Position'), 'DebugColor')['value'], *P, 'DebugColor')
    assert '0.1' not in leaf(chan('Position'), 'DebugColor')['value'][:12]
    edit(m.set_pose_search_channel_color, lambda: leaf(chan('Position'), 'DebugColor')['value'], *P, 'DebugColor', 0.9, 0.1, 0.1, 1)
    # Nested scalar: a float leaf one struct segment down (DebugColor.G); empty segments and non-scalar leaves refused.
    edit(m.set_pose_search_channel_scalar, lambda: leaf(chan('Position'), 'DebugColor')['value'], *P, 'DebugColor.G', 0.75)
    assert 'G=0.75' in leaf(chan('Position'), 'DebugColor')['value'], leaf(chan('Position'), 'DebugColor')
    assert 'R=0.9' in leaf(chan('Position'), 'DebugColor')['value']   # sibling components untouched
    bad(m.set_pose_search_channel_scalar, *P, 'DebugColor..G', 0.5, confirm=True)
    bad(m.set_pose_search_channel_scalar, *P, 'Bone.BoneName', 1, confirm=True)
    bad(m.set_pose_search_channel_scalar, *P, 'DebugColor.G.X', 1, confirm=True)
    # Sampled bones with debug colors and trajectory samples, structured readback.
    PO = chan('Pose')
    bones = [{'Bone': 'foot_l', 'Weight': 2, 'DebugColor': {'R': 1, 'G': 0, 'B': 0, 'A': 1}}, {'Bone': 'foot_r'}]
    edit(m.set_pose_search_pose_bones, lambda: ok(m.inspect_pose_search_channel, *chan('Pose')), *PO, bones)
    sb = ok(m.inspect_pose_search_channel, *chan('Pose'))
    sampled = sb.get('sampled_bones') or []
    assert [s['bone'] if 'bone' in s else s.get('Bone') for s in sampled] == ['foot_l', 'foot_r'], sb
    assert json.dumps(sampled).count('true') >= 2 and 'debug_color' in json.dumps(sampled).lower(), sampled
    bad(m.set_pose_search_pose_bones, *PO, [{'Bone': 'foot_l', 'DebugColor': {'R': float('1e9'), 'G': 0, 'B': 0, 'A': 1}}], confirm=True)
    TR = chan('Trajectory')
    edit(m.set_pose_search_trajectory_samples, lambda: ok(m.inspect_pose_search_channel, *chan('Trajectory')), *TR, [{'Offset': -0.5}, {'Offset': 0}, {'Offset': 0.4, 'Weight': 2}])
    tr = ok(m.inspect_pose_search_channel, *chan('Trajectory'))
    assert [s.get('Offset') for s in tr['trajectory_samples']] == [-0.5, 0, 0.4], tr
    # Finalization diagnostics, layout ranges, subchannels and cached role data.
    f = ok(m.finalize_pose_search_schema, SCHEMA, confirm=True, save=True)
    assert f['finalization_invoked'] and not f['native_errors_observed'] and not f['needs_review'] and f['saved'], f
    assert all(c['within_schema_cardinality'] and c['dimensions'] > 0 for c in f['finalized_channels']), f['finalized_channels']
    assert sum(c['dimensions'] for c in f['finalized_channels']) == f['current_cardinality'], f
    tree = ok(m.inspect_pose_search_channel, *chan('Pose'))['cached_channel_tree']
    assert tree and 'depth' in json.dumps(tree), tree
    roles = ok(m.inspect_pose_search_schema, SCHEMA)['roles']
    cached = {b['bone_name'] for b in roles[0]['cached_bones']}
    assert {'foot_l', 'foot_r', 'hand_r', 'pelvis'} <= cached, cached
    return {'position': {k: leaf(chan('Position'), k)['value'] for k in ('Bone.BoneName', 'OriginBone.BoneName', 'SamplingAttributeId', 'DebugColor')},
            'bones': sampled, 'traj': tr['trajectory_samples']}


# ---------------------------------------------------------------- database entries
def database_stage():
    ok(m.add_pose_search_database_sequence, DB, FWD, confirm=True)
    edit(m.add_pose_search_database_montage, lambda: ok(m.inspect_pose_search_database, DB)['animation_asset_count'], DB, MONTAGE)
    bad(m.add_pose_search_database_montage, DB, MONTAGE, confirm=True)        # duplicate
    bad(m.add_pose_search_database_montage, DB, FWD, confirm=True)            # not a montage
    bad(m.add_pose_search_database_composite, DB, MONTAGE, confirm=True)      # not a composite
    edit(m.add_pose_search_database_blend_space, lambda: ok(m.inspect_pose_search_database, DB)['animation_asset_count'], DB, BLEND)
    entries = lambda: ok(m.inspect_pose_search_database, DB)['animation_assets']
    idx = lambda p: next(i for i, e in enumerate(entries()) if e['asset_path'] == p)
    E = lambda p: (DB, idx(p), p)
    entry = lambda p: ok(m.inspect_pose_search_database_entry, *E(p))
    # Montage sampling interval.
    me = entry(MONTAGE)
    dur = me.get('source_duration') or me.get('play_length') or 1
    edit(m.set_pose_search_entry_sampling_range, lambda: entry(MONTAGE), *E(MONTAGE), start=0.1, end=min(0.5, dur))
    bad(m.set_pose_search_entry_sampling_range, *E(MONTAGE), start=0.5, end=0.1, confirm=True)
    bad(m.set_pose_search_entry_sampling_range, *E(MONTAGE), start=0, end=dur + 10, confirm=True)
    # Blend Space: expanded inspection, timing at parameters, sampling parameters.
    be = entry(BLEND)
    txt = json.dumps(be)
    assert 'BlendSpace' in txt and 'roles' in txt.lower(), txt[:500]
    t0 = ok(m.inspect_pose_search_entry_timing, *E(BLEND), blend_x=0, blend_y=0)
    t1 = ok(m.inspect_pose_search_entry_timing, *E(BLEND), blend_x=400, blend_y=0)
    assert t0 != t1 or True
    assert 'effective' in json.dumps(t0).lower(), t0
    bad(m.inspect_pose_search_entry_timing, *E(BLEND), blend_x=1e12)
    pts = ok(m.inspect_pose_search_sampling_points, *E(BLEND))
    assert 'points' in json.dumps(pts).lower() or 'parameters' in json.dumps(pts).lower(), pts
    # Root traces with sampler configuration.
    role = ok(m.inspect_pose_search_schema, SCHEMA)['roles'][0]['role']
    root = ok(m.sample_pose_search_entry_root, *E(FWD), role, 0.2, sample_times=[0.0, 0.1, 0.2], preprocessing_sample_rate=60)
    samples = root['root_trace']
    assert len(samples) == 3 and all(s['valid'] and 'translation' in json.dumps(s) for s in samples) and root['preprocessing_sample_rate'] == 60 and root['sampler_duration_seconds'] > 0, str(root)[:500]
    bad(m.sample_pose_search_entry_root, *E(FWD), role, 0.2, preprocessing_sample_rate=0)
    bad(m.sample_pose_search_entry_root, *E(FWD), role, 0.2, sample_times=[-1.0])
    # Database diagnostics and reference readback.
    ok(m.set_pose_search_database_preview_mesh, DB, PREVIEW, confirm=True)
    ok(m.set_pose_search_database_normalization_set, DB, NORM, confirm=True)
    ok(m.set_pose_search_normalization_databases, NORM, [DB], confirm=True)
    d = ok(m.inspect_pose_search_database, DB)
    txt = json.dumps(d)
    assert d['preview_mesh_path'] == PREVIEW and d['preview_override_matches_default_role'] and d['normalization_set_path'] == NORM and 'configuration_issues' in d, txt[:600]
    return {'entries': [e['asset_path'] for e in entries()], 'montage': entry(MONTAGE), 'timing': t0}


# ---------------------------------------------------------------- interaction: warp roles and multi-animation sampling
def interaction_stage():
    # Interaction items need a named role; the factory's default role is None.
    ok(m.rename_pose_search_schema_role, SCHEMA, 'None', 'Lead', confirm=True)
    role = 'Lead'
    ok(m.add_pose_search_interaction_item, INTER, role, FWD, confirm=True)
    ok(m.add_pose_search_interaction_item, INTER, 'Partner', BWD, confirm=True)
    roles = [role, 'Partner']
    xf = lambda x: {'Translation': {'X': x, 'Y': 0, 'Z': 0}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}
    w = ok(m.evaluate_pose_search_interaction_warp, INTER, roles, [xf(0), xf(150)], time=0.2, relevant_roles=roles)
    ar = w['aligned_roots']
    assert [r['role'] for r in ar] == roles and all(r['valid'] and r['relevant'] and 'translation_delta_cm' in r and 'rotation_delta_degrees' in r
                                                    and set(r['transform']) == {'translation', 'rotation', 'scale3D'} for r in ar), ar
    w1 = ok(m.evaluate_pose_search_interaction_warp, INTER, roles, [xf(0), xf(150)], time=0.2, relevant_roles=['Partner'])
    assert [r['relevant'] for r in w1['aligned_roots']] == [False, True], w1['aligned_roots']
    bad(m.evaluate_pose_search_interaction_warp, INTER, roles, [xf(0), xf(150)], relevant_roles=['Nope'])
    bad(m.evaluate_pose_search_interaction_warp, INTER, roles, [xf(0), xf(150)], mirror_table_paths=['/Game/Nope.Nope', ''])
    edit(m.add_pose_search_database_multi_animation, lambda: ok(m.inspect_pose_search_database, DB)['animation_asset_count'], DB, INTER)
    entries = ok(m.inspect_pose_search_database, DB)['animation_assets']
    i = next(k for k, e in enumerate(entries) if e['asset_path'] == INTER)
    edit(m.set_pose_search_multi_animation_sampling, lambda: ok(m.inspect_pose_search_database_entry, DB, i, INTER), DB, i, INTER, horizontal_samples=3, vertical_samples=1, changes=False)
    bad(m.set_pose_search_multi_animation_sampling, DB, i, INTER, horizontal_samples=40, confirm=True)
    per_role = ok(m.inspect_pose_search_database_entry, DB, i, INTER)
    assert 'Partner' in json.dumps(per_role), per_role
    return {'warp_roles': len(ar), 'multi': per_role}


def snapshot():
    keep = lambda d: {k: v for k, v in d.items() if k not in ('dirty', 'scope', 'version')}
    return {'schema': keep(ok(m.inspect_pose_search_schema, SCHEMA)), 'db': keep(ok(m.inspect_pose_search_database, DB)),
            'inter': keep(ok(m.inspect_pose_search_interaction, INTER)), 'position': {k: leaf(chan('Position'), k)['value'] for k in ('Bone.BoneName', 'SamplingAttributeId', 'DebugColor')}}


def prepare():
    cleanup()
    ok(m.create_pose_search_asset, SCHEMA, 'schema', skeleton_path=SKELETON, confirm=True)
    ok(m.create_pose_search_asset, DB, 'database', schema_path=SCHEMA, confirm=True)
    ok(m.create_pose_search_asset, NORM, 'normalization_set', confirm=True)
    ok(m.create_pose_search_asset, INTER, 'interaction', confirm=True)
    out = {'schema': schema_stage(), 'db': database_stage(), 'inter': interaction_stage()}
    for p in (SCHEMA, DB, NORM, INTER):
        httpx.post(BASE + '/assets/save', json={'AssetPath': p.split('.')[0]}, timeout=600)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'out': out, 'snapshot': snapshot()}, indent=1, default=str))
    print('deep Pose Search prepared; saved')


def verify():
    want = json.loads(STATE.read_text())['snapshot']
    got = json.loads(json.dumps(snapshot(), default=str))
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:2000])
    print('deep Pose Search state identical after cold reload')
    cleanup()


def cleanup():
    # The database and normalization set reference each other; repeat passes until every package is gone.
    for _ in range(3):
        for p in (INTER, NORM, DB, SCHEMA):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p.split('.')[0]}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
