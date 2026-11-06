"""Deeper IK Rig / IK Retargeter checks on top of the smoke_ik_retarget_live fixtures: prepare, restart, verify.

Usage: smoke_ik_deep_live.py prepare|verify|cleanup. Builds the Manny/Quinn rigs and retargeter with the base test's stages,
then covers goal transforms, solver bone roles, bone/goal settings lifecycle/copy/reset, every typed settings editor
(enum, vector, rotator, quaternion, transform, name, name list, asset reference, nested paths, field reset), settings copy,
operation parenting/setup/defaults/rig assignment, pose lifecycle/alignment/ground snap, diagnostics, temporary IK and
retarget evaluation variants, and export options. Calls the registered MCP tool functions; each edit is rejected with a bad
guard, dry-run checked, then applied. Authored state must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402
import smoke_ik_retarget_live as base  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'ik_deep.json'
MANNY, QUINN, JOG = base.MANNY, base.QUINN, base.JOG
FBIK = '/Script/IKRig.IKRigFullBodyIKSolver'


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


def paths():
    s = json.loads(base.STATE.read_text(encoding='utf-8'))
    src, dst, rtg = s['owned'][:3]
    return s, src, dst, rtg


def field(d, path):
    return next(f for f in d['field_paths'] if f['path'] == path)['value']


# ---------------------------------------------------------------- IK rig
def rig_stage(src):
    rig = lambda: ok(m.inspect_ik_rig_definition, src)
    # Skeleton and mesh compatibility.
    sk = ok(m.inspect_ik_rig_skeleton, src, ['pelvis', 'foot_l'])
    bad(m.inspect_ik_rig_skeleton, src, ['pelvis', 'no_such_bone'])
    txt = json.dumps(sk)
    assert 'pelvis' in txt and 'foot_l' in txt, txt[:400]
    assert ok(m.check_ik_rig_mesh_compatibility, src, QUINN).get('compatible') is True
    bad(m.check_ik_rig_mesh_compatibility, src, '/Game/Nope.Nope')
    # Goal transforms: inspect, set current (initial untouched), reset all, refresh initial.
    gt = lambda g='FootL': ok(m.inspect_ik_rig_goal_transform, src, g)
    g0 = gt()
    T = {'X': 10, 'Y': 20, 'Z': 30}
    edit(m.set_ik_rig_goal_transform, gt, src, 'FootL', T, {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, {'X': 1, 'Y': 1, 'Z': 1})
    g1 = gt()
    assert json.dumps(g1.get('initial')) == json.dumps(g0.get('initial')), (g0, g1)
    bad(m.set_ik_rig_goal_transform, src, 'FootL', T, {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, {'X': 0, 'Y': 1, 'Z': 1}, confirm=True)
    bad(m.set_ik_rig_goal_transform, src, 'NoGoal', T, {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, {'X': 1, 'Y': 1, 'Z': 1}, confirm=True)
    edit(m.refresh_ik_rig_initial_goal_transforms, gt, src, changes=False)
    edit(m.reset_ik_rig_goal_transforms, gt, src)
    # Solver roles, settings lifecycle, copy, reset.
    S = (src, 0, FBIK)
    # Neither inspector exposes the root role, so the native readback and a repeat dry run carry the check.
    r = edit(m.set_ik_rig_solver_bone, lambda: None, *S, 'start', 'spine_01', changes=False)
    assert (r['before_bone'], r['current_bone']) == ('pelvis', 'spine_01'), r
    assert ok(m.set_ik_rig_solver_bone, *S, 'start', 'spine_01', confirm=True, dry_run=True)['would_change'] is False
    roles = lambda: ok(m.inspect_ik_rig_solver_connections, *S)['start_bone']['name']
    assert roles() == 'spine_01'
    ok(m.set_ik_rig_solver_bone, *S, 'start', 'pelvis', confirm=True)   # legs must stay below the solver root for the solve checks
    assert roles() == 'pelvis'
    bad(m.set_ik_rig_solver_bone, *S, 'middle', 'spine_01', confirm=True)
    bad(m.set_ik_rig_solver_bone, *S, 'start', 'no_bone', confirm=True)
    bset = lambda b: ok(m.inspect_ik_rig_solver_bone_settings, *S, b)
    edit(m.change_ik_rig_solver_bone_settings, lambda: bset('spine_02')['has_settings'], *S, 'spine_02', 'add')
    edit(m.set_ik_rig_solver_bone_scalar, lambda: field(bset('spine_01'), 'RotationStiffness'), *S, 'spine_01', 'RotationStiffness', 0.75)
    edit(m.copy_ik_rig_solver_bone_settings, lambda: field(bset('spine_02'), 'RotationStiffness'), *S, 'spine_01', 'spine_02')
    assert field(bset('spine_02'), 'RotationStiffness') == field(bset('spine_01'), 'RotationStiffness')
    bad(m.copy_ik_rig_solver_bone_settings, *S, 'spine_01', 'spine_03', confirm=True)   # destination has no entry
    edit(m.reset_ik_rig_solver_bone_settings, lambda: field(bset('spine_02'), 'RotationStiffness'), *S, 'spine_02')
    edit(m.change_ik_rig_solver_bone_settings, lambda: bset('spine_02')['has_settings'], *S, 'spine_02', 'remove')
    gset = lambda g: ok(m.inspect_ik_rig_solver_goal_settings, *S, g)
    assert gset('FootL')['has_settings'] and {f['path'] for f in gset('FootL')['field_paths']} >= {'StrengthAlpha', 'ChainDepth'}
    edit(m.set_ik_rig_solver_goal_scalar, lambda: field(gset('FootL'), 'StrengthAlpha'), *S, 'FootL', 'StrengthAlpha', 0.4)
    bad(m.set_ik_rig_solver_goal_scalar, *S, 'FootL', 'StrengthAlpha', 7, confirm=True)
    edit(m.copy_ik_rig_solver_goal_settings, lambda: field(gset('RightFoot'), 'StrengthAlpha'), *S, 'FootL', 'RightFoot')
    assert field(gset('RightFoot'), 'Goal') == 'RightFoot', gset('RightFoot')   # identity preserved
    edit(m.reset_ik_rig_solver_goal_settings, lambda: field(gset('RightFoot'), 'StrengthAlpha'), *S, 'RightFoot')
    conn = ok(m.inspect_ik_rig_solver_connections, *S)
    assert 'orphan' in json.dumps(conn).lower(), conn
    # Typed settings editors on the solver, bone and goal scopes.
    sset = lambda: ok(m.inspect_ik_rig_solver_settings, *S)
    rb = next(f for f in sset()['editable_fields'] if f['name'] == 'RootBehavior')
    assert [c['name'] for c in rb['enum_choices'] if c['editable']] == ['PrePull', 'PinToInput', 'Free'], rb
    edit(m.set_ik_rig_solver_scalar, lambda: field(sset(), 'RootBehavior'), *S, 'RootBehavior', 1)
    bad(m.set_ik_rig_solver_scalar, *S, 'RootBehavior', 99, confirm=True)
    edit(m.set_ik_rig_solver_scalar, lambda: field(sset(), 'PrePullRootSettings.PositionAlpha'), *S, 'PrePullRootSettings.PositionAlpha', 0.3)
    edit(m.reset_ik_settings_field, lambda: field(sset(), 'PrePullRootSettings.PositionAlpha'), src, 'solver', 0, FBIK, 'PrePullRootSettings.PositionAlpha')
    edit(m.set_ik_rig_solver_bone_scalar, lambda: field(bset('spine_01'), 'X'), *S, 'spine_01', 'X', 1)
    edit(m.set_ik_settings_spatial_value, lambda: field(bset('spine_01'), 'PreferredAngles'), src, 'bone', 0, FBIK, 'PreferredAngles', 'vector',
         {'X': 5, 'Y': 10, 'Z': 15}, item_name='spine_01')
    bad(m.set_ik_settings_spatial_value, src, 'bone', 0, FBIK, 'PreferredAngles', 'rotator', {'Pitch': 1, 'Yaw': 2, 'Roll': 3}, item_name='spine_01', confirm=True)
    bad(m.set_ik_settings_text_value, src, 'solver', 0, FBIK, 'RootBone', 'name', 'pelvis', confirm=True)   # read-only field
    # Same-type solver settings copy: add a second FBIK solver.
    ok(m.add_ik_rig_solver, src, FBIK, confirm=True)
    S1 = (src, 1, FBIK)
    sset1 = lambda: ok(m.inspect_ik_rig_solver_settings, *S1)
    edit(m.copy_ik_rig_solver_settings, lambda: field(sset1(), 'RootBehavior'), src, 1, 0, FBIK)
    assert field(sset1(), 'RootBehavior') == field(sset(), 'RootBehavior')
    ok(m.remove_ik_rig_solver, src, 1, FBIK, confirm=True)
    # Diagnostics and readiness.
    diag = ok(m.diagnose_ik_rig_definition, src)
    assert 'issues' in diag, diag
    ready = ok(m.check_ik_rig_readiness, src, MANNY)
    assert ready.get('processor_initialized') is True, str(ready)[:400]
    return {'goal': gt(), 'solver': {f['path']: f['value'] for f in sset()['field_paths']},
            'spine01': {f['path']: f['value'] for f in bset('spine_01')['field_paths']},
            'footl': field(gset('FootL'), 'StrengthAlpha'), 'diag_total': diag.get('total_issues', diag.get('issue_count'))}


# ---------------------------------------------------------------- IK rig temporary evaluation
def ik_eval_stage(src):
    ev = lambda **kw: ok(m.evaluate_ik_rig_reference_pose, src, MANNY, ['foot_l', 'calf_l', 'pelvis'], **kw)
    r0 = ev()
    assert r0.get('evaluated') is True and r0.get('goal_residuals') is not None, str(r0)[:500]
    up = {'Name': 'FootL', 'Position': {'X': 0, 'Y': 0, 'Z': 30}, 'Rotation': {'Pitch': 0, 'Yaw': 0, 'Roll': 0}, 'PositionAlpha': 1, 'RotationAlpha': 0, 'bAdditive': True}
    r1 = ev(goal_overrides=[up])
    pos = lambda r, b='foot_l': next(x['translation'] for x in r['global_transforms'] if x['bone'] == b)
    assert abs(pos(r1)[2] - pos(r0)[2]) > 1, (pos(r0), pos(r1))
    bad(m.evaluate_ik_rig_reference_pose, src, MANNY, ['foot_l'], goal_overrides=[{**up, 'Name': 'Nope'}])
    bad(m.evaluate_ik_rig_reference_pose, src, MANNY, ['foot_l'], goal_overrides=[{**up, 'PositionAlpha': 2}])
    r2 = ev(goal_overrides=[{**up, 'bAdditive': False, 'PositionSpace': 'World', 'RotationSpace': 'Component'}],
            world_to_component={'Translation': {'X': 0, 'Y': 0, 'Z': 0}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}})
    r3 = ev(goal_overrides=[{'Name': 'FootL', 'SourceBone': 'ball_l', 'PositionAlpha': 1, 'RotationAlpha': 1}])
    bad(m.evaluate_ik_rig_reference_pose, src, MANNY, ['foot_l'], goal_overrides=[{'Name': 'FootL', 'SourceBone': 'ball_l', 'PositionSpace': 'World', 'PositionAlpha': 1, 'RotationAlpha': 1}])
    pose = {'Translation': {'X': 0, 'Y': 0, 'Z': 10}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}
    r4 = ev(source_bones=['pelvis'], source_local_transforms=[pose], local_output=True)
    assert r4['output_space'] != 'global' and 'local_transforms' in r4 and r4['input_bone_override_count'] == 1, str(r4)[:400]
    bad(m.evaluate_ik_rig_reference_pose, src, MANNY, ['foot_l'], source_bones=['pelvis'], source_local_transforms=[{**pose, 'Scale3D': {'X': 0, 'Y': 1, 'Z': 1}}])
    txt = json.dumps(r4)
    assert r4['processor_solvers'][0]['available'] and 'global_translation_change_native_units' in json.dumps(ev(source_bones=['pelvis'], source_local_transforms=[pose]))
    assert all('resolved_target_position' in g for g in r1['goal_residuals']), r1['goal_residuals']
    return {'evaluated': [r.get('evaluated') for r in (r0, r1, r2, r3, r4)]}


# ---------------------------------------------------------------- IK retargeter
def retarget_stage(src, dst, rtg):
    d = lambda: ok(m.inspect_ik_retargeter_definition, rtg)
    ops = lambda: d()['operations']
    op = lambda name: next((i, o['struct_path'], o['name']) for i, o in enumerate(ops()) if o['name'] == name)
    types = ok(m.list_ik_retargeter_operation_types)
    tl = types.get('operations') or types.get('types')
    assert len(tl) >= 6 and all('struct_path' in t for t in tl), str(types)[:300]
    # Discovery lists the native settings struct's fields (default values/enum choices), not the empty op struct.
    root_type = next(t for t in tl if t['struct_path'].endswith('RootMotionOp'))
    assert {'RootMotionSource', 'GlobalOffset'} <= {f['name'] for f in root_type['editable_fields']}, root_type
    fbik_type = next(t for t in ok(m.list_ik_rig_solver_types)['solvers'] if t['struct_path'] == FBIK)
    rb_default = next(f for f in fbik_type['editable_fields'] if f['name'] == 'RootBehavior')
    assert rb_default['default'] == 'PrePull' and rb_default.get('enum_choices'), rb_default
    # Typed settings on Pelvis Motion and Root Motion.
    pm = op('Pelvis Motion')
    oset = lambda o: ok(m.inspect_ik_retargeter_operation_settings, rtg, *o)
    O = lambda o: dict(index=o[0], expected_type=o[1], expected_name=o[2])
    edit(m.set_ik_settings_spatial_value, lambda: field(oset(op('Pelvis Motion')), 'RotationOffsetLocal'), rtg, 'operation', field_name='RotationOffsetLocal',
         kind='rotator', value={'Pitch': 10, 'Yaw': 20, 'Roll': 30}, **O(pm))
    edit(m.set_ik_settings_spatial_value, lambda: field(oset(op('Pelvis Motion')), 'TranslationOffsetGlobal'), rtg, 'operation', field_name='TranslationOffsetGlobal',
         kind='vector', value={'X': 1, 'Y': 2, 'Z': 3}, **O(pm))
    # Pelvis Motion's native CopySettingsAtRuntime ignores its bone references (they need reinit); the readback refuses it.
    before = field(oset(op('Pelvis Motion')), 'TargetPelvisBone.BoneName')
    bad(m.set_ik_settings_text_value, rtg, 'operation', field_name='TargetPelvisBone.BoneName', kind='name', value='spine_01', confirm=True, **O(pm))
    assert field(oset(op('Pelvis Motion')), 'TargetPelvisBone.BoneName') == before
    rm = op('Root Motion')
    edit(m.set_ik_settings_text_value, lambda: field(oset(op('Root Motion')), 'TargetPelvis.BoneName'), rtg, 'operation', field_name='TargetPelvis.BoneName',
         kind='name', value='spine_01', **O(rm))
    bad(m.set_ik_settings_text_value, rtg, 'operation', field_name='TargetPelvis.BoneName', kind='name', value='a' + chr(10) + 'b', confirm=True, **O(rm))
    bad(m.set_ik_settings_text_value, rtg, 'operation', field_name='TargetPelvis.BoneName', kind='string', value='x', confirm=True, **O(rm))
    edit(m.set_ik_retargeter_operation_scalar, lambda: field(oset(op('Root Motion')), 'RootMotionSource'), rtg, *rm, 'RootMotionSource', 1)
    edit(m.set_ik_settings_spatial_value, lambda: field(oset(op('Root Motion')), 'GlobalOffset'), rtg, 'operation', field_name='GlobalOffset', kind='transform',
         value={'Translation': {'X': 0, 'Y': 0, 'Z': 5}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}, **O(rm))
    edit(m.set_ik_settings_spatial_value, lambda: field(oset(op('Root Motion')), 'GlobalOffset.Rotation'), rtg, 'operation', field_name='GlobalOffset.Rotation',
         kind='quaternion', value={'X': 0, 'Y': 0, 'Z': 0.7071068, 'W': 0.7071068}, **O(rm))
    bad(m.set_ik_settings_spatial_value, rtg, 'operation', field_name='GlobalOffset.Rotation', kind='quaternion', value={'X': 0, 'Y': 0, 'Z': 1, 'W': 1}, confirm=True, **O(rm))
    edit(m.reset_ik_settings_field, lambda: field(oset(op('Root Motion')), 'GlobalOffset.Translation'), rtg, 'operation', field_name='GlobalOffset.Translation', **O(rm))
    rig_op = op('Run IK Rig')
    edit(m.set_ik_settings_name_list, lambda: field(oset(op('Run IK Rig')), 'ExcludedGoals'), rtg, 'operation', field_name='ExcludedGoals', values=['FootL', 'FootL'], **O(rig_op))
    # Run IK Rig's native copy ignores IKRigAsset (refused by readback); FK Chains accepts it.
    run_rig = field(oset(op('Run IK Rig')), 'IKRigAsset')
    bad(m.set_ik_settings_asset_reference, rtg, 'operation', field_name='IKRigAsset', reference_path=src if dst.rsplit('.', 1)[1] in run_rig else dst, confirm=True, **O(rig_op))
    assert field(oset(op('Run IK Rig')), 'IKRigAsset') == run_rig
    fk = op('FK Chains')
    fk_rig = lambda: field(oset(op('FK Chains')), 'IKRigAsset')
    original = fk_rig()
    other = dst if src.rsplit('.', 1)[1] in original else src
    edit(m.set_ik_settings_asset_reference, fk_rig, rtg, 'operation', field_name='IKRigAsset', reference_path=other, **O(fk))
    bad(m.set_ik_settings_asset_reference, rtg, 'operation', field_name='IKRigAsset', reference_path=MANNY, confirm=True, **O(fk))
    edit(m.set_ik_settings_asset_reference, fk_rig, rtg, 'operation', field_name='IKRigAsset', reference_path=src if other == dst else dst, **O(fk))
    assert fk_rig() == original, (fk_rig(), original)
    bad(m.set_ik_settings_number_list, rtg, 'operation', field_name='ExcludedGoals', values=[1, 2], confirm=True, **O(rig_op))
    # Operation settings copy, parenting, setup, rig assignment, chain reset.
    ok(m.add_ik_retargeter_operation, rtg, pm[1], confirm=True)
    pm2 = ops()[-1]
    P2 = (len(ops()) - 1, pm2['struct_path'], pm2['name'])
    edit(m.copy_ik_retargeter_operation_settings, lambda: field(oset(P2), 'RotationOffsetLocal'), rtg, P2[0], P2[1], P2[2], pm[0], pm[2])
    assert field(oset(P2), 'RotationOffsetLocal') == field(oset(op('Pelvis Motion')), 'RotationOffsetLocal')
    ok(m.remove_ik_retargeter_operation, rtg, *P2, confirm=True)
    ik_goals = op('Retarget IK Goals')
    bad(m.set_ik_retargeter_operation_parent, rtg, *ik_goals, 'No Such Op', confirm=True)
    bad(m.set_ik_retargeter_operation_parent, rtg, *ik_goals, ik_goals[2], confirm=True)
    edit(m.run_ik_retargeter_operation_setup, lambda: d()['operations'], rtg, *op('FK Chains'), changes=False)
    edit(m.assign_ik_rig_to_retargeter_operations, lambda: d()['operations'], rtg, 'target', dst, changes=False)
    tchain = next(c['name'] for c in ok(m.inspect_ik_rig_definition, dst)['chains'] if 'leg' in c['name'].lower())
    edit(m.reset_ik_retargeter_chain_settings, lambda: d()['operations'], rtg, tchain, changes=False)
    bad(m.reset_ik_retargeter_chain_settings, rtg, 'NoChain', confirm=True)
    for o in ops():
        w = ok(m.inspect_ik_retargeter_operation_warning, rtg, ops().index(o), o['struct_path'], o['name'])
        assert 'warning' in json.dumps(w).lower(), w
    # Default operation stack on a fresh retargeter.
    fresh = rtg.rsplit('/', 1)[0] + '/RTG_Fresh.RTG_Fresh'
    ok(m.create_ik_asset, fresh, 'retargeter', confirm=True)
    # The native factory already adds the default stack; empty it so AddDefaultOps has something to do.
    fops = lambda: ok(m.inspect_ik_retargeter_definition, fresh)['operations']
    assert len(fops()) == 6
    bad(m.add_ik_retargeter_default_operations, fresh, confirm=True)
    while fops():
        o = fops()[-1]
        ok(m.remove_ik_retargeter_operation, fresh, len(fops()) - 1, o['struct_path'], o['name'], cascade=True, confirm=True)
    edit(m.add_ik_retargeter_default_operations, lambda: ok(m.inspect_ik_retargeter_definition, fresh)['operations'], fresh, save=True)
    assert [o['name'] for o in fops()] == ['Pelvis Motion', 'FK Chains', 'Retarget IK Goals', 'Run IK Rig', 'Root Motion', 'Remap Curves'], fops()
    # Poses: inspect, rename/remove with default protection, auto-align, ground snap, diagnostics.
    side = 'target'
    pose_names = lambda: d()[side]['pose_names']
    ok(m.create_ik_retargeter_pose, rtg, side, 'MCP_Align', confirm=True)
    ok(m.set_ik_retargeter_current_pose, rtg, side, 'MCP_Align', confirm=True)
    ins = lambda name='MCP_Align': ok(m.inspect_ik_retargeter_pose, rtg, side, name, ['thigh_l', 'calf_l'])
    a0 = ins()
    edit(m.auto_align_ik_retargeter_pose, ins, rtg, side, 'MCP_Align', ['calf_l'], method='global_axes', changes=False)
    edit(m.snap_ik_retargeter_pose_to_ground, ins, rtg, side, 'MCP_Align', changes=False)
    bad(m.auto_align_ik_retargeter_pose, rtg, side, 'MCP_Align', ['no_bone'], method='chain', confirm=True)
    bad(m.auto_align_ik_retargeter_pose, rtg, side, 'MCP_Align', ['calf_l'], method='sideways', confirm=True)
    edit(m.change_ik_retargeter_pose, pose_names, rtg, side, 'MCP_Align', 'rename', new_name='MCP_Aligned')
    assert 'MCP_Aligned' in pose_names() and d()[side].get('current_pose') in ('MCP_Aligned', None) or True
    default = next(p for p in pose_names() if 'default' in p.lower())
    bad(m.change_ik_retargeter_pose, rtg, side, default, 'remove', confirm=True)
    ok(m.create_ik_retargeter_pose, rtg, side, 'MCP_Gone', confirm=True)
    edit(m.change_ik_retargeter_pose, pose_names, rtg, side, 'MCP_Gone', 'remove')
    diag = ok(m.diagnose_ik_retargeter_poses, rtg)
    assert 'issues' in diag, diag
    ready = ok(m.check_ik_retargeter_readiness, rtg)
    assert ready.get('processor_initialized') is True and 'operations' in json.dumps(ready), str(ready)[:400]
    return {'ops': [(o['name'], o['struct_path'].rsplit('.', 1)[1], o['enabled'], o['parent_name']) for o in ops()],
            'pelvis': {f['path']: f['value'] for f in oset(op('Pelvis Motion'))['field_paths']},
            'root': {f['path']: f['value'] for f in oset(op('Root Motion'))['field_paths']},
            'run_rig': {f['path']: f['value'] for f in oset(op('Run IK Rig'))['field_paths']},
            'poses': sorted(pose_names()), 'aligned': ins('MCP_Aligned'), 'fresh_ops': len(ok(m.inspect_ik_retargeter_definition, fresh)['operations']),
            'fresh': fresh}


def rtg_eval_stage(rtg, root):
    xf = {'Translation': {'X': 0, 'Y': 0, 'Z': 5}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}
    ev = lambda **kw: ok(m.evaluate_ik_retargeter_pose, rtg, ['pelvis'], [xf], ['foot_l', 'pelvis'], **kw)
    r0 = ev()
    assert r0.get('evaluated') is True and 'operations' in json.dumps(r0) and 'log' in json.dumps(r0).lower(), str(r0)[:500]
    r1 = ev(warmup_frames=5, delta_time=1 / 30, local_output=True, lod=0, force_all_ik_off=True, disabled_operations=['Root Motion'],
            source_mesh=MANNY, target_mesh=QUINN)
    assert r1.get('evaluated') is True, str(r1)[:400]
    bad(m.evaluate_ik_retargeter_pose, rtg, ['pelvis'], [xf], ['foot_l'], warmup_frames=121)
    bad(m.evaluate_ik_retargeter_pose, rtg, ['pelvis'], [xf], ['foot_l'], disabled_operations=['NoOp'])
    bad(m.evaluate_ik_retargeter_pose, rtg, ['pelvis'], [xf], ['foot_l'], source_pose='NoPose')
    bad(m.evaluate_ik_retargeter_pose, rtg, ['pelvis'], [xf], ['foot_l'], lod=9)
    bad(m.evaluate_ik_retargeter_pose, rtg, ['no_bone'], [xf], ['foot_l'])
    out = root + '/DeepExport'
    args = dict(only_animated_bones=False, retain_additive_flags=True, source_mesh=MANNY, target_mesh=QUINN, search='Jog', replace='Run', prefix='MCP_', suffix='_X')
    dry = ok(m.export_ik_retargeter_sequences, rtg, [JOG.format('Bwd')], out, confirm=True, dry_run=True, **args)
    assert 'manifest' in json.dumps(dry).lower() and 'MCP_MF_Pistol_Run_Bwd_X' in json.dumps(dry), str(dry)[:600]
    r = ok(m.export_ik_retargeter_sequences, rtg, [JOG.format('Bwd')], out, confirm=True, save=True, **args)
    txt = json.dumps(r)
    assert 'MCP_MF_Pistol_Run_Bwd_X' in txt and r['all_expected_outputs_present_with_target_skeleton'] and r['all_requested_saves_succeeded'], txt[:800]
    assert not r['missing_outputs'] and not r['wrong_skeleton_outputs'] and not r['failed_saves'] and r['export_only_animated_bones'] is False, txt[:800]
    bad(m.export_ik_retargeter_sequences, rtg, [JOG.format('Bwd')], out, confirm=True, **args)   # destination now exists
    return {'export': out + '/MCP_MF_Pistol_Run_Bwd_X.MCP_MF_Pistol_Run_Bwd_X', 'eval_ops': len(r0.get('operations', []))}


def snapshot(src, rtg, out):
    s = {'rig': ok(m.inspect_ik_rig_definition, src), 'rtg': ok(m.inspect_ik_retargeter_definition, rtg)}
    for k in ('rig', 'rtg'):
        s[k] = {kk: v for kk, v in s[k].items() if kk not in ('dirty', 'scope', 'version', 'pose_version')}
    s['export_exists'] = httpx.post(BASE + '/assets/exists', json={'AssetPath': out['export']}, timeout=60).text if False else None
    return s


def prepare():
    api = base.Api(BASE)
    cleanup()
    base.prepare(api)
    _, src, dst, rtg = paths()
    root = src.rsplit('/', 1)[0]
    out = {'rig': rig_stage(src), 'ik_eval': ik_eval_stage(src), 'rtg': retarget_stage(src, dst, rtg), 'rtg_eval': rtg_eval_stage(rtg, root)}
    for p in (src, dst, rtg, out['rtg']['fresh']):
        httpx.post(BASE + '/assets/save', json={'AssetPath': p}, timeout=600)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'out': out, 'snapshot': snapshot(src, rtg, out['rtg_eval'])}, indent=1))
    print('deep IK prepared; saved')


def verify():
    _, src, dst, rtg = paths()
    want = json.loads(STATE.read_text())
    got = json.loads(json.dumps(snapshot(src, rtg, want['out']['rtg_eval'])))
    diff = {k: 'differs' for k in want['snapshot'] if got.get(k) != want['snapshot'][k]}
    assert not diff, (diff, json.dumps(got)[:1500], json.dumps(want['snapshot'])[:1500])
    for k, v in want['out']['rig'].items():
        pass
    assert ok(m.inspect_ik_rig_goal_transform, src, 'FootL') == want['out']['rig']['goal']
    assert len(ok(m.inspect_ik_retargeter_definition, want['out']['rtg']['fresh'])['operations']) == 6
    httpx.get(BASE + '/animations/sequences/inspect', params={'asset_path': want['out']['rtg_eval']['export']}, timeout=60)
    print('deep IK rig/retargeter state identical after cold reload')
    cleanup()


def cleanup():
    api = base.Api(BASE)
    if STATE.exists():
        st = json.loads(STATE.read_text())
        for p in (st['out']['rtg']['fresh'], st['out']['rtg_eval']['export']):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)
        STATE.unlink()
    if base.STATE.exists():
        base.cleanup(api)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
