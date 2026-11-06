"""Live IK Rig and IK Retargeter authoring checks.

prepare: create owned IK rigs (Manny source, Quinn target) and a retargeter under
/Game/UE5MCP_Test/IK_<tag>, author them with guard/dry-run/undo checks, save and snapshot.
verify (fresh editor): compare the cold-loaded definitions, then delete the owned assets.
"""
import argparse
import json
import uuid
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'ik_retarget.json'
MESHES = '/Game/Characters/Mannequins/Meshes'
MANNY = f'{MESHES}/SKM_Manny_Simple.SKM_Manny_Simple'
QUINN = f'{MESHES}/SKM_Quinn_Simple.SKM_Quinn_Simple'
JOG = '/Game/Characters/Mannequins/Anims/Pistol/Jog/MF_Pistol_Jog_{0}.MF_Pistol_Jog_{0}'


class Api:
    def __init__(self, base):
        self.base = base

    def call(self, method, route, body=None, params=None, ok=True):
        r = httpx.request(method, self.base + route, json=body, params=params, timeout=300)
        if ok:
            assert r.is_success, (method, route, r.status_code, r.text[:1500])
            return r.json()
        assert r.status_code >= 400, (method, route, 'expected rejection', r.text[:800])
        return r.text

    def undo(self):
        self.call('POST', '/editor/transactions/undo', {})

    def redo(self):
        self.call('POST', '/editor/transactions/redo', {})

    def rig(self, path):
        return self.call('GET', '/ik-rigs/definition', params={'asset_path': path})

    def retargeter(self, path):
        return self.call('GET', '/ik-retargeters/definition', params={'asset_path': path})


def names(items):
    return [i.get('name', i.get('chain_name', i.get('goal_name'))) for i in items]


def rig_stage(api, rig, mesh, manual):
    R = {'AssetPath': rig, 'bConfirm': True}
    # Preview mesh and root.
    api.call('PATCH', '/ik-rigs/preview-mesh', {**R, 'MeshPath': '/Game/Nope.Nope'}, ok=False)
    api.call('PATCH', '/ik-rigs/preview-mesh', {**R, 'MeshPath': mesh})
    assert api.rig(rig)['preview_mesh'] == mesh
    api.call('POST', '/ik-rigs/mesh-compatibility', {**R, 'MeshPath': QUINN})
    api.call('POST', '/ik-rigs/skeleton/inspect', {**R, 'Bones': ['pelvis', 'foot_l']})
    api.call('PATCH', '/ik-rigs/root', {**R, 'RootBone': 'no_bone'}, ok=False)
    api.call('PATCH', '/ik-rigs/root', {**R, 'RootBone': 'pelvis'})
    assert api.rig(rig)['pelvis'] == 'pelvis'
    api.undo(); assert api.rig(rig)['pelvis'] == 'None'
    api.redo(); assert api.rig(rig)['pelvis'] == 'pelvis'
    if not manual:
        api.call('POST', '/ik-rigs/auto-characterize', R)
        assert api.rig(rig)['chain_count'] >= 5, api.rig(rig)['chain_count']
        api.call('POST', '/ik-rigs/auto-fbik', R)
        assert api.rig(rig)['solver_count'] >= 1
        return

    # Manual chains, goals and solvers.
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'LeftLeg', 'StartBone': 'thigh_l', 'EndBone': 'no_bone'}, ok=False)
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'LeftLeg', 'StartBone': 'thigh_l', 'EndBone': 'foot_l'})
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'LeftLeg', 'StartBone': 'thigh_r', 'EndBone': 'foot_r'}, ok=False)
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'RightLeg', 'StartBone': 'thigh_r', 'EndBone': 'foot_r'})
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'Spine', 'StartBone': 'spine_01', 'EndBone': 'spine_05'})
    chains = lambda: names(api.rig(rig)['chains'])
    assert chains() == ['LeftLeg', 'RightLeg', 'Spine'], api.rig(rig)['chains']
    api.undo(); assert chains() == ['LeftLeg', 'RightLeg']
    api.redo()
    api.call('PATCH', '/ik-rigs/chains', {**R, 'ChainName': 'Spine', 'StartBone': 'spine_01', 'EndBone': 'spine_03'})
    assert 'spine_03' in json.dumps(api.rig(rig)['chains'][2])
    api.call('POST', '/ik-rigs/chains/lifecycle', {**R, 'ChainName': 'Spine', 'NewName': 'Torso', 'Operation': 'rename'})
    api.call('POST', '/ik-rigs/chains/lifecycle', {**R, 'ChainName': 'Torso', 'Operation': 'remove'})
    assert chains() == ['LeftLeg', 'RightLeg']
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'Spine', 'StartBone': 'spine_01', 'EndBone': 'spine_05'})

    goals = lambda: names(api.rig(rig)['goals'])
    api.call('POST', '/ik-rigs/goals', {**R, 'GoalName': 'FootL', 'BoneName': 'foot_l'})
    api.call('POST', '/ik-rigs/goals', {**R, 'GoalName': 'FootL', 'BoneName': 'foot_r'}, ok=False)
    api.call('POST', '/ik-rigs/goals', {**R, 'GoalName': 'FootR', 'BoneName': 'hand_r'})
    api.call('PATCH', '/ik-rigs/goals/bone', {**R, 'GoalName': 'FootR', 'BoneName': 'foot_r'})
    assert 'foot_r' in json.dumps(api.rig(rig)['goals'][1])
    api.call('PATCH', '/ik-rigs/goals/weights', {**R, 'GoalName': 'FootL', 'PositionAlpha': 0.5, 'RotationAlpha': 0.25})
    assert '0.25' in json.dumps(api.rig(rig)['goals'][0])
    api.call('PATCH', '/ik-rigs/goals/weights', {**R, 'GoalName': 'FootL', 'PositionAlpha': 2}, ok=False)
    api.call('PATCH', '/ik-rigs/goals/transform', {**R, 'GoalName': 'FootL', 'Translation': {'X': 0, 'Y': 0, 'Z': 10}})
    assert api.call('POST', '/ik-rigs/goals/transform/inspect', {**R, 'GoalName': 'FootL'})
    api.call('POST', '/ik-rigs/goals/transform/reset', R)
    api.call('POST', '/ik-rigs/goals/transform/refresh-initial', R)
    api.call('POST', '/ik-rigs/goals/lifecycle', {**R, 'GoalName': 'FootR', 'NewName': 'RightFoot', 'Operation': 'rename'})
    assert goals() == ['FootL', 'RightFoot']
    api.call('PATCH', '/ik-rigs/chains', {**R, 'ChainName': 'LeftLeg', 'StartBone': 'thigh_l', 'EndBone': 'foot_l', 'GoalName': 'FootL'})
    api.call('PATCH', '/ik-rigs/chains', {**R, 'ChainName': 'RightLeg', 'StartBone': 'thigh_r', 'EndBone': 'foot_r', 'GoalName': 'RightFoot'})
    # Goal removal clears the chain's goal reference; dry run, undo/redo and an unknown goal are covered.
    api.call('POST', '/ik-rigs/goals', {**R, 'GoalName': 'HandL', 'BoneName': 'hand_l'})
    api.call('POST', '/ik-rigs/chains', {**R, 'ChainName': 'LeftArm', 'StartBone': 'upperarm_l', 'EndBone': 'hand_l'})
    api.call('PATCH', '/ik-rigs/chains', {**R, 'ChainName': 'LeftArm', 'StartBone': 'upperarm_l', 'EndBone': 'hand_l', 'GoalName': 'HandL'})
    arm = lambda: next(c for c in api.rig(rig)['chains'] if names([c]) == ['LeftArm'])
    assert 'HandL' in json.dumps(arm()), arm()
    api.call('POST', '/ik-rigs/goals/lifecycle', {**R, 'GoalName': 'NoGoal', 'Operation': 'remove'}, ok=False)
    before = api.rig(rig)
    plan = api.call('POST', '/ik-rigs/goals/lifecycle', {**R, 'GoalName': 'HandL', 'Operation': 'remove', 'bDryRun': True})
    assert api.rig(rig) == before, 'dry-run goal removal changed the rig'
    print('goal removal plan:', json.dumps(plan)[:300])
    api.call('POST', '/ik-rigs/goals/lifecycle', {**R, 'GoalName': 'HandL', 'Operation': 'remove'})
    assert 'HandL' not in goals() and 'HandL' not in json.dumps(arm()), (goals(), arm())
    api.undo(); assert 'HandL' in goals() and 'HandL' in json.dumps(arm())
    api.redo(); assert 'HandL' not in goals()
    api.call('POST', '/ik-rigs/chains/lifecycle', {**R, 'ChainName': 'LeftArm', 'Operation': 'remove'})

    types = api.call('GET', '/ik-rigs/solver-types', params={'limit': 64})
    tlist = [t['struct_path'] for t in types['solvers']]
    fbik = next(t for t in tlist if 'FBIK' in t or 'FullBody' in t)
    limb = next((t for t in tlist if 'Limb' in t), None) or next(t for t in tlist if t != fbik)
    S = lambda i, t, **kw: {**R, 'SolverIndex': i, 'SolverType': t, **kw}
    api.call('POST', '/ik-rigs/solvers', {**R, 'SolverType': '/Script/Engine.Actor'}, ok=False)
    api.call('POST', '/ik-rigs/solvers', {**R, 'SolverType': fbik})
    api.call('POST', '/ik-rigs/solvers', {**R, 'SolverType': limb})
    solvers = lambda: [s.get('type', s.get('class_path', s.get('solver_type'))) for s in api.rig(rig)['solvers']]
    assert len(solvers()) == 2, api.rig(rig)['solvers']
    api.call('POST', '/ik-rigs/solvers/inspect', S(0, fbik))
    api.call('POST', '/ik-rigs/solvers/inspect', S(0, limb), ok=False)
    api.call('PATCH', '/ik-rigs/solvers/order', S(1, limb, TargetIndex=0))
    api.call('PATCH', '/ik-rigs/solvers/order', S(0, limb, TargetIndex=1))
    api.call('PATCH', '/ik-rigs/solvers/enabled', S(1, limb, bEnabled=False))
    assert 'false' in json.dumps(api.rig(rig)['solvers'][1]).lower()
    api.call('PATCH', '/ik-rigs/solvers/bone', S(0, fbik, BoneName='pelvis', Operation='start'))
    api.call('POST', '/ik-rigs/solvers/goals', S(0, fbik, GoalName='FootL', Operation='connect'))
    api.call('POST', '/ik-rigs/solvers/goals', S(0, fbik, GoalName='RightFoot', Operation='connect'))
    conns = json.dumps(api.call('POST', '/ik-rigs/solvers/connections', S(0, fbik)))
    assert 'FootL' in conns and 'RightFoot' in conns, conns[:500]
    settings = api.call('POST', '/ik-rigs/solvers/settings/inspect', S(0, fbik))
    val = lambda d, name: next(f['value'] for f in d['field_paths'] if f['path'] == name)
    api.call('PATCH', '/ik-rigs/solvers/settings/scalar', S(0, fbik, FieldName='RootBone', ScalarValue=1), ok=False)
    api.call('PATCH', '/ik-rigs/solvers/settings/scalar', S(0, fbik, FieldName='Iterations', ScalarValue=5000), ok=False)
    api.call('PATCH', '/ik-rigs/solvers/settings/scalar', S(0, fbik, FieldName='Iterations', ScalarValue=7))
    assert val(api.call('POST', '/ik-rigs/solvers/settings/inspect', S(0, fbik)), 'Iterations') == '7'
    api.undo(); assert val(api.call('POST', '/ik-rigs/solvers/settings/inspect', S(0, fbik)), 'Iterations') == '20'
    api.redo()
    api.call('POST', '/ik-rigs/solvers/settings/reset', S(0, fbik))
    assert val(api.call('POST', '/ik-rigs/solvers/settings/inspect', S(0, fbik)), 'Iterations') == '20'
    api.call('POST', '/ik-rigs/solvers/goal-settings/inspect', S(0, fbik, GoalName='FootL'))
    api.call('POST', '/ik-rigs/solvers/bone-settings', S(0, fbik, BoneName='spine_01', Operation='add'))
    bset = api.call('POST', '/ik-rigs/solvers/bone-settings/inspect', S(0, fbik, BoneName='spine_01'))
    bfield = next(f for f in bset['field_paths'] if f['type'] == 'float' and f['writable'])
    default = bfield['value']
    api.call('PATCH', '/ik-rigs/solvers/bone-settings/scalar', S(0, fbik, BoneName='spine_01', FieldName=bfield['path'], ScalarValue=0.5))
    assert val(api.call('POST', '/ik-rigs/solvers/bone-settings/inspect', S(0, fbik, BoneName='spine_01')), bfield['path']) == '0.500000'
    api.call('POST', '/ik-rigs/solvers/bone-settings/reset', S(0, fbik, BoneName='spine_01'))
    assert val(api.call('POST', '/ik-rigs/solvers/bone-settings/inspect', S(0, fbik, BoneName='spine_01')), bfield['path']) == default
    api.call('PATCH', '/ik-rigs/bones/excluded', {**R, 'BoneName': 'ik_foot_root', 'bExcluded': True})
    assert 'ik_foot_root' in api.rig(rig)['excluded_bones']
    api.call('DELETE', '/ik-rigs/solvers', S(1, limb))
    assert len(solvers()) == 1
    api.call('GET', '/ik-rigs/diagnostics', params={'asset_path': rig})
    api.call('POST', '/ik-rigs/readiness', {**R, 'MeshPath': mesh})
    api.call('POST', '/ik-rigs/evaluate-reference-pose', {**R, 'MeshPath': mesh, 'Bones': ['foot_l']})


def retarget_stage(api, rtg, src, dst, owned, root, tag):
    T = {'AssetPath': rtg, 'bConfirm': True}
    api.call('PATCH', '/ik-retargeters/rig', {**T, 'Side': 'sideways', 'RigPath': src}, ok=False)
    api.call('PATCH', '/ik-retargeters/rig', {**T, 'Side': 'source', 'RigPath': '/Game/Nope.Nope'}, ok=False)
    api.call('PATCH', '/ik-retargeters/rig', {**T, 'Side': 'source', 'RigPath': src})
    api.call('PATCH', '/ik-retargeters/rig', {**T, 'Side': 'target', 'RigPath': dst})
    d = lambda: api.retargeter(rtg)
    assert d()['source']['rig_path'] == src and d()['target']['rig_path'] == dst
    api.undo(); assert d()['target']['rig_path'] != dst
    api.redo(); assert d()['target']['rig_path'] == dst
    api.call('PATCH', '/ik-retargeters/preview-mesh', {**T, 'Side': 'target', 'MeshPath': MANNY})
    assert d()['target']['preview_mesh'] == MANNY
    api.call('PATCH', '/ik-retargeters/preview-mesh', {**T, 'Side': 'target', 'MeshPath': QUINN})

    # Op stack.
    ops = lambda: [(o['name'], o['struct_path'].rsplit('.', 1)[1], o['enabled'], o['parent_name']) for o in d()['operations']]

    def O(name, **kw):
        o = next(o for o in d()['operations'] if o['name'] == name)
        return {**T, 'SolverIndex': o['index'], 'SolverType': o['struct_path'], 'ExpectedName': o['name'], **kw}

    base = ops()
    api.call('POST', '/ik-retargeters/operations/inspect', {**O('FK Chains'), 'ExpectedName': 'Wrong'}, ok=False)
    api.call('POST', '/ik-retargeters/operations', {**T, 'SolverType': '/Script/Engine.Actor'}, ok=False)
    api.call('POST', '/ik-retargeters/operations', {**T, 'SolverType': '/Script/IKRig.IKRetargetFilterBoneOp'})
    added = d()['operations'][-1]['name']
    assert len(ops()) == len(base) + 1
    api.undo(); assert ops() == base
    api.redo()
    api.call('PATCH', '/ik-retargeters/operations/name', O(added, NewName='Filter Test'))
    api.call('PATCH', '/ik-retargeters/operations/name', O('Filter Test', NewName='FK Chains'), ok=False)
    api.call('PATCH', '/ik-retargeters/operations/enabled', O('Filter Test', bEnabled=False))
    assert ('Filter Test', 'IKRetargetFilterBoneOp', False, 'None') in ops(), ops()
    api.call('PATCH', '/ik-retargeters/operations/order', O('Filter Test', TargetIndex=0))
    assert ops()[0][0] == 'Filter Test'
    api.call('POST', '/ik-retargeters/operations/inspect', O('Filter Test'))
    api.call('POST', '/ik-retargeters/operations/warning', O('Filter Test'))
    api.call('DELETE', '/ik-retargeters/operations', O('Filter Test'))
    assert ops() == base, ops()
    hierarchy = api.call('GET', '/ik-retargeters/operations/hierarchy', params={'asset_path': rtg})
    assert hierarchy['issues'] == [] and hierarchy['operation_count'] == len(base), hierarchy
    api.call('PATCH', '/ik-retargeters/operations/parent', O('Retarget IK Goals', ParentName='Nope'), ok=False)
    api.call('POST', '/ik-retargeters/operations/assign-rig', {**T, 'Side': 'target', 'RigPath': dst})
    api.call('POST', '/ik-retargeters/operations/setup', O('FK Chains'))

    # Chain mapping on the FK op.
    mapping = lambda: api.call('POST', '/ik-retargeters/operations/mapping/inspect', O('FK Chains'))
    api.call('POST', '/ik-retargeters/operations/mapping/auto', O('FK Chains', Operation='bogus'), ok=False)
    api.call('POST', '/ik-retargeters/operations/mapping/auto', O('FK Chains', Operation='fuzzy', bForceRemap=True))
    m = json.dumps(mapping())
    assert 'LeftLeg' in m, m[:800]
    target_chain = next(c['name'] for c in api.rig(dst)['chains'] if 'leg' in c['name'].lower() and 'left' in c['name'].lower())
    api.call('PATCH', '/ik-retargeters/operations/mapping', O('FK Chains', ChainName=target_chain, SourceChain='RightLeg'))
    assert '"RightLeg"' in json.dumps(mapping())
    api.call('PATCH', '/ik-retargeters/operations/mapping', O('FK Chains', ChainName=target_chain, SourceChain='NoSuchChain'), ok=False)
    api.call('POST', '/ik-retargeters/operations/mapping/refresh', O('FK Chains'))
    api.call('POST', '/ik-retargeters/chains/settings/reset', {**T, 'ChainName': target_chain})

    # Op settings: inspect, scalar, reset.
    settings = api.call('POST', '/ik-retargeters/operations/settings/inspect', O('Pelvis Motion'))
    field = next(f for f in settings['field_paths'] if f['type'] in ('float', 'double') and f['writable'])

    def val():
        fields = api.call('POST', '/ik-retargeters/operations/settings/inspect', O('Pelvis Motion'))['field_paths']
        return next(f['value'] for f in fields if f['path'] == field['path'])

    api.call('PATCH', '/ik-retargeters/operations/settings/scalar', O('Pelvis Motion', FieldName=field['path'], ScalarValue=0.75))
    assert val() == '0.750000', val()
    api.undo(); assert val() == field['value']
    api.redo()
    api.call('POST', '/ik-retargeters/operations/settings/reset', O('Pelvis Motion'))
    assert val() == field['value']

    # Curve remap op.
    api.call('PATCH', '/ik-retargeters/operations/curve-remap', O('Remap Curves', SourceCurves=['CurveA'], TargetCurves=['CurveB'], bCopyAllCurves=False))
    assert 'CurveB' in json.dumps(api.call('POST', '/ik-retargeters/operations/curve-remap/inspect', O('Remap Curves')))
    api.call('PATCH', '/ik-retargeters/operations/curve-remap', O('Remap Curves', SourceCurves=['A', 'B'], TargetCurves=['C']), ok=False)

    # Retarget poses.
    P = lambda side='target', **kw: {**T, 'Side': side, **kw}
    poses = lambda side='target': d()[side]['pose_names']
    api.call('POST', '/ik-retargeters/poses', P(NewName='Tuned', PoseName='Default Pose'))
    api.call('POST', '/ik-retargeters/poses', P(NewName='Tuned', PoseName='Default Pose'), ok=False)
    assert 'Tuned' in poses()
    api.call('PATCH', '/ik-retargeters/poses/current', P(PoseName='Tuned'))
    assert d()['target']['current_pose'] == 'Tuned'
    api.call('PATCH', '/ik-retargeters/poses/root-offset', P(PoseName='Tuned', Translation={'X': 0, 'Y': 0, 'Z': 5}))
    assert d()['target']['root_translation'] == [0, 0, 5], d()['target']['root_translation']
    api.call('PATCH', '/ik-retargeters/poses/bone-rotation', P(PoseName='Tuned', BoneName='upperarm_l', Rotation={'Pitch': 0, 'Yaw': 0, 'Roll': 30}))
    assert d()['target']['rotation_offset_count'] == 1
    api.call('PATCH', '/ik-retargeters/poses/bone-rotation', P(PoseName='Tuned', BoneName='no_bone', Rotation={'Pitch': 0, 'Yaw': 0, 'Roll': 30}), ok=False)
    assert api.call('POST', '/ik-retargeters/poses/inspect', P(PoseName='Tuned', Bones=['upperarm_l']))
    api.call('POST', '/ik-retargeters/poses/reset', P(PoseName='Tuned', Bones=['upperarm_l']))
    assert d()['target']['rotation_offset_count'] == 0
    api.undo(); assert d()['target']['rotation_offset_count'] == 1
    api.redo()
    api.call('POST', '/ik-retargeters/poses/auto-align', P(PoseName='Tuned', Operation='chain'))
    api.call('POST', '/ik-retargeters/poses/auto-align', P(PoseName='Tuned', Operation='bogus'), ok=False)
    api.call('POST', '/ik-retargeters/poses/snap-ground', P(PoseName='Tuned', BoneName='foot_l'))
    api.call('POST', '/ik-retargeters/poses/lifecycle', P(PoseName='Tuned', NewName='Final', Operation='rename'))
    assert 'Final' in poses() and 'Tuned' not in poses()
    api.call('GET', '/ik-retargeters/poses/diagnostics', params={'asset_path': rtg})

    # Readiness, evaluation, duplication and export.
    api.call('GET', '/ik-retargeters/readiness', params={'asset_path': rtg})
    ev = api.call('POST', '/ik-retargeters/evaluate-reference-pose', {**T, 'SourceMeshPath': MANNY, 'TargetMeshPath': QUINN, 'Bones': ['foot_l']})
    assert 'foot_l' in json.dumps(ev), json.dumps(ev)[:500]
    copy = f'{root}/RTG2_{tag}.RTG2_{tag}'
    api.call('POST', '/ik-assets/duplicate', {'AssetPath': copy, 'SourceAssetPath': rtg, 'bConfirm': True})
    owned.append(copy)
    assert api.retargeter(copy)['operation_count'] == d()['operation_count']
    out = f'{root}/Export'
    r = api.call('POST', '/ik-retargeters/export-sequences', {**T, 'AnimationPaths': [JOG.format('Fwd')], 'OutputFolder': out,
                                                             'SourceMeshPath': MANNY, 'TargetMeshPath': QUINN})
    exported = sorted({p for p in json.dumps(r).split('"') if p.startswith(out + '/') and '.' in p})
    assert exported, json.dumps(r)[:800]
    owned.extend(exported)


def prepare(api):
    assert not STATE.exists(), 'Run verify or cleanup first'
    tag = uuid.uuid4().hex[:8]
    root = f'/Game/UE5MCP_Test/IK_{tag}'
    src = f'{root}/IK_Src_{tag}.IK_Src_{tag}'
    dst = f'{root}/IK_Dst_{tag}.IK_Dst_{tag}'
    rtg = f'{root}/RTG_{tag}.RTG_{tag}'
    owned = []
    try:
        api.call('POST', '/ik-assets', {'AssetPath': src, 'Operation': 'rig'}, ok=False)
        api.call('POST', '/ik-assets', {'AssetPath': '/Engine/X.X', 'Operation': 'rig', 'bConfirm': True}, ok=False)
        assert not api.call('POST', '/ik-assets', {'AssetPath': src, 'Operation': 'rig', 'bConfirm': True, 'bDryRun': True}).get('created')
        for path, kind in ((src, 'rig'), (dst, 'rig'), (rtg, 'retargeter')):
            r = create(api, path, kind)
            owned.append(path)
        rig_stage(api, src, MANNY, manual=True)
        rig_stage(api, dst, QUINN, manual=False)
        retarget_stage(api, rtg, src, dst, owned, root, tag)
        for path in owned:
            api.call('POST', '/assets/save', {'AssetPath': path})
        snapshots = snapshot(api, owned)
        print('IK Rig/Retargeter authoring OK; restart the editor and run verify')
    finally:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'tag': tag, 'owned': owned, 'snapshots': locals().get('snapshots')}), encoding='utf-8')


def snapshot(api, owned):
    out = {}
    for path in owned:
        name = path.rsplit('/', 1)[1]
        if name.startswith('IK_'):
            out[path] = api.rig(path)
        elif name.startswith('RTG'):
            out[path] = api.retargeter(path)
    for s in out.values():
        assert not s.get('dirty'), ('saved asset still dirty', s['asset_path'])
    return out


def comparable(s):
    """Drop live-only fields: dirty flags, scope text and in-memory edit counters (version, pose_version)."""
    s = {k: v for k, v in s.items() if k not in ('dirty', 'scope', 'version')}
    for side in ('source', 'target'):
        if isinstance(s.get(side), dict):
            s[side] = {k: v for k, v in s[side].items() if k != 'pose_version'}
    return s


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshots'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api, state['owned'])
        for path, before in state['snapshots'].items():
            a, b = comparable(before), comparable(cold[path])
            diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            assert not diff, (path, diff, {k: (a.get(k), b.get(k)) for k in diff[:2]})
        exported = [p for p in state['owned'] if '/Export/' in p]
        for path in exported:
            package = path.split('.', 1)[0].replace('/Game/', '', 1)
            assert (PROJECT / 'Content' / (package + '.uasset')).exists(), path
        print('Cold reload of IK rig chains/goals/solvers/settings, retargeter rigs/ops/mapping/poses/settings '
              'and exported sequence: OK')
    finally:
        cleanup(api)


def create(api, path, kind):
    return api.call('POST', CREATE_ROUTE, {'AssetPath': path, 'Operation': kind, 'bConfirm': True})


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    for path in reversed(state['owned']):
        httpx.post(api.base + '/assets/delete', json={'AssetPath': path}, timeout=180)
    STATE.unlink()
    print('cleaned', len(state['owned']))


CREATE_ROUTE = '/ik-assets'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    p.add_argument('--base', default='http://127.0.0.1:8080')
    a = p.parse_args()
    api = Api(a.base)
    assert not api.call('GET', '/editor/status')['is_playing']
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[a.phase](api)


if __name__ == '__main__':
    main()
