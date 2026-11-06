"""Call every IK Rig / IK Retargeter MCP tool through the registered FastMCP dispatcher.

Run after `smoke_ik_retarget_live.py prepare` and before `verify`. Read-only tools run for real;
mutating tools run as confirmed dry runs, and the saved fixture definitions must be unchanged afterwards.
"""
import asyncio
import json
import sys

from smoke_ik_retarget_live import STATE, PROJECT, MANNY, QUINN, JOG, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
READ_ONLY_PREFIXES = ('inspect_', 'list_', 'check_', 'diagnose_', 'evaluate_')


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    state = json.loads(STATE.read_text(encoding='utf-8'))
    owned = state['owned']
    src = next(p for p in owned if '/IK_Src_' in p)
    dst = next(p for p in owned if '/IK_Dst_' in p)
    rtg = next(p for p in owned if '/RTG_' in p)
    root = rtg.rsplit('/', 1)[0]
    rig = api.rig(src)
    fbik = rig['solvers'][0]
    stype = next(v for k, v in fbik.items() if isinstance(v, str) and v.startswith('/Script/IKRig.'))
    rt = api.retargeter(rtg)
    op = lambda name: next(o for o in rt['operations'] if o['name'] == name)
    fk, pelvis, curves = op('FK Chains'), op('Pelvis Motion'), op('Remap Curves')
    O = lambda o: dict(asset_path=rtg, operation_index=o['index'], expected_type=o['struct_path'], expected_name=o['name'])
    S = dict(asset_path=src, solver_index=0, expected_type=stype)
    pose = rt['target']['current_pose']
    target_chain = next(c['name'] for c in api.rig(dst)['chains'] if 'left' in c['name'].lower() and 'leg' in c['name'].lower())
    first_float = lambda fields: next(f['path'] for f in fields if f['type'] in ('float', 'double') and f['writable'])
    pelvis_field = first_float(api.call('POST', '/ik-retargeters/operations/settings/inspect',
                                        {'AssetPath': rtg, 'SolverIndex': pelvis['index'], 'SolverType': pelvis['struct_path'], 'ExpectedName': pelvis['name']})['field_paths'])
    bone_field = first_float(api.call('POST', '/ik-rigs/solvers/bone-settings/inspect',
                                      {'AssetPath': src, 'SolverIndex': 0, 'SolverType': stype, 'BoneName': 'spine_01'})['field_paths'])

    args = {
        'inspect_ik_rig_definition': dict(asset_path=src),
        'inspect_ik_retargeter_definition': dict(asset_path=rtg),
        'create_ik_rig_retarget_chain': dict(asset_path=src, chain_name='Neck', start_bone='neck_01', end_bone='head'),
        'set_ik_rig_retarget_root': dict(asset_path=src, bone_name='spine_01'),
        'change_ik_rig_retarget_chain': dict(asset_path=src, chain_name='Spine', operation='rename', new_name='Back'),
        'edit_ik_rig_retarget_chain': dict(asset_path=src, chain_name='Spine', start_bone='spine_01', end_bone='spine_02'),
        'create_ik_rig_goal': dict(asset_path=src, goal_name='HandL', bone_name='hand_l'),
        'change_ik_rig_goal': dict(asset_path=src, goal_name='FootL', operation='rename', new_name='LeftFoot'),
        'set_ik_rig_goal_bone': dict(asset_path=src, goal_name='FootL', bone_name='ball_l'),
        'set_ik_rig_goal_weights': dict(asset_path=src, goal_name='FootL', position_alpha=0.1),
        'list_ik_rig_solver_types': dict(limit=4),
        'add_ik_rig_solver': dict(asset_path=src, solver_type='/Script/IKRig.IKRigLimbSolver'),
        'remove_ik_rig_solver': S,
        'move_ik_rig_solver': dict(S, target_index=0),
        'set_ik_rig_solver_enabled': dict(S, enabled=False),
        'connect_ik_rig_goal': dict(S, goal_name='FootL', connected=False),
        'set_ik_rig_solver_bone': dict(S, role='start', bone_name='spine_01'),
        'set_ik_rig_preview_mesh': dict(asset_path=src, mesh_path=QUINN),
        'set_ik_rig_bone_excluded': dict(asset_path=src, bone_name='ik_hand_root'),
        'set_ik_retargeter_rig': dict(asset_path=rtg, side='target', rig_path=src),
        'set_ik_retargeter_preview_mesh': dict(asset_path=rtg, side='target', mesh_path=MANNY),
        'set_ik_retargeter_current_pose': dict(asset_path=rtg, side='target', pose_name='Default Pose'),
        'create_ik_retargeter_pose': dict(asset_path=rtg, side='target', new_name='Extra'),
        'change_ik_retargeter_pose': dict(asset_path=rtg, side='target', pose_name=pose, operation='rename', new_name='Other'),
        'reset_ik_retargeter_pose': dict(asset_path=rtg, side='target', pose_name=pose, bones=['upperarm_l']),
        'set_ik_retargeter_root_offset': dict(asset_path=rtg, side='target', pose_name=pose, translation={'X': 0, 'Y': 0, 'Z': 1}),
        'set_ik_retargeter_bone_rotation': dict(asset_path=rtg, side='target', pose_name=pose, bone_name='upperarm_r', rotation={'Pitch': 0, 'Yaw': 0, 'Roll': 5}),
        'list_ik_retargeter_operation_types': dict(limit=4),
        'add_ik_retargeter_operation': dict(asset_path=rtg, operation_type='/Script/IKRig.IKRetargetFilterBoneOp'),
        'set_ik_retargeter_operation_enabled': dict(O(fk), enabled=False),
        'remove_ik_retargeter_operation': O(fk),
        'rename_ik_retargeter_operation': dict(O(fk), new_name='FK'),
        'set_ik_retargeter_operation_parent': dict(O(fk), parent_name='None'),
        'move_ik_retargeter_operation': dict(O(fk), target_index=0),
        'inspect_ik_retargeter_operation': O(fk),
        'inspect_ik_rig_solver': S,
        'inspect_ik_retargeter_chain_mapping': O(fk),
        'set_ik_retargeter_chain_mapping': dict(O(fk), target_chain=target_chain, source_chain='LeftLeg'),
        'auto_map_ik_retargeter_chains': dict(O(fk), mode='exact'),
        'refresh_ik_retargeter_chain_mapping': O(fk),
        'auto_align_ik_retargeter_pose': dict(asset_path=rtg, side='target', pose_name=pose, bones=['upperarm_l']),
        'snap_ik_retargeter_pose_to_ground': dict(asset_path=rtg, side='target', pose_name=pose),
        'inspect_ik_retargeter_pose': dict(asset_path=rtg, side='target', pose_name=pose, bones=['upperarm_l']),
        'set_ik_rig_goal_transform': dict(asset_path=src, goal_name='FootL', translation={'X': 0, 'Y': 0, 'Z': 2},
                                          rotation={'Pitch': 0, 'Yaw': 0, 'Roll': 0}, scale={'X': 1, 'Y': 1, 'Z': 1}),
        'inspect_ik_rig_goal_transform': dict(asset_path=src, goal_name='FootL'),
        'reset_ik_rig_goal_transforms': dict(asset_path=src),
        'inspect_ik_rig_solver_connections': S,
        'inspect_ik_rig_skeleton': dict(asset_path=src, bones=['pelvis']),
        'check_ik_rig_mesh_compatibility': dict(asset_path=src, mesh_path=QUINN),
        'refresh_ik_rig_initial_goal_transforms': dict(asset_path=src),
        'add_ik_retargeter_default_operations': dict(asset_path=rtg),
        'run_ik_retargeter_operation_setup': O(fk),
        'assign_ik_rig_to_retargeter_operations': dict(asset_path=rtg, side='target', rig_path=dst),
        'inspect_ik_retargeter_operation_hierarchy': dict(asset_path=rtg),
        'change_ik_rig_solver_bone_settings': dict(S, bone_name='spine_02', operation='add'),
        'inspect_ik_rig_solver_bone_settings': dict(S, bone_name='spine_01'),
        'inspect_ik_rig_solver_goal_settings': dict(S, goal_name='FootL'),
        'inspect_ik_rig_solver_settings': S,
        'inspect_ik_retargeter_operation_settings': O(pelvis),
        'reset_ik_retargeter_operation_settings': O(pelvis),
        'reset_ik_rig_solver_settings': S,
        'reset_ik_rig_solver_bone_settings': dict(S, bone_name='spine_01'),
        'reset_ik_rig_solver_goal_settings': dict(S, goal_name='FootL'),
        'set_ik_rig_solver_scalar': dict(S, field_name='Iterations', value=9),
        'set_ik_retargeter_operation_scalar': dict(O(pelvis), field_name=pelvis_field, value=0.5),
        'set_ik_rig_solver_bone_scalar': dict(S, bone_name='spine_01', field_name=bone_field, value=0.25),
        'set_ik_rig_solver_goal_scalar': dict(S, goal_name='FootL', field_name='StrengthAlpha', value=0.5),
        'set_ik_settings_spatial_value': dict(asset_path=src, scope='solver', index=0, expected_type=stype, field_name='RootBehavior', kind='vector', value={'X': 1, 'Y': 0, 'Z': 0}),
        'set_ik_settings_text_value': dict(asset_path=src, scope='solver', index=0, expected_type=stype, field_name='RootBone', kind='name', value='spine_01'),
        'reset_ik_settings_field': dict(asset_path=src, scope='solver', index=0, expected_type=stype, field_name='Iterations'),
        'set_ik_settings_name_list': dict(asset_path=src, scope='solver', index=0, expected_type=stype, field_name='Iterations', values=['a']),
        'set_ik_settings_asset_reference': dict(asset_path=src, scope='solver', index=0, expected_type=stype, field_name='Iterations', reference_path=MANNY),
        'set_ik_settings_number_list': dict(asset_path=src, scope='solver', index=0, expected_type=stype, field_name='Iterations', values=[1.0]),
        'set_ik_retargeter_curve_remap': dict(O(curves), source_curves=['X'], target_curves=['Y']),
        'inspect_ik_retargeter_curve_remap': O(curves),
        'copy_ik_retargeter_operation_settings': dict(asset_path=rtg, destination_index=fk['index'], expected_type=fk['struct_path'],
                                                      destination_name=fk['name'], source_index=fk['index'], source_name=fk['name']),
        'copy_ik_rig_solver_settings': dict(asset_path=src, destination_index=0, source_index=0, expected_type=stype),
        'copy_ik_rig_solver_bone_settings': dict(S, source_bone='spine_01', destination_bone='spine_01'),
        'copy_ik_rig_solver_goal_settings': dict(S, source_goal='FootL', destination_goal='RightFoot'),
        'reset_ik_retargeter_chain_settings': dict(asset_path=rtg, target_chain=target_chain),
        'auto_characterize_ik_rig': dict(asset_path=src),
        'auto_setup_ik_rig_fbik': dict(asset_path=src),
        'diagnose_ik_rig_definition': dict(asset_path=src),
        'diagnose_ik_retargeter_poses': dict(asset_path=rtg),
        'inspect_ik_retargeter_operation_warning': O(fk),
        'check_ik_retargeter_readiness': dict(asset_path=rtg),
        'evaluate_ik_retargeter_reference_pose': dict(asset_path=rtg, target_bones=['foot_l']),
        'evaluate_ik_retargeter_pose': dict(asset_path=rtg, source_bones=['pelvis'], source_local_transforms=[{}], target_bones=['foot_l']),
        'create_ik_asset': dict(asset_path=f'{root}/IK_McpDry.IK_McpDry', kind='rig'),
        'duplicate_ik_asset': dict(source_asset_path=src, destination_asset_path=f'{root}/IK_McpDup.IK_McpDup'),
        'export_ik_retargeter_sequences': dict(asset_path=rtg, animation_paths=[JOG.format('Bwd')], output_folder=f'{root}/McpExport'),
        'check_ik_rig_readiness': dict(asset_path=src, mesh_path=MANNY),
        'evaluate_ik_rig_reference_pose': dict(asset_path=src, mesh_path=MANNY, bones=['foot_l']),
    }

    tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
    ik = {n for n, t in tools.items() if n in args or ('ik_' in n and any(x in n for x in ('ik_rig', 'ik_retarget', 'ik_asset', 'ik_settings')))}
    assert ik == set(args), ('uncovered', sorted(ik - set(args)), 'unknown', sorted(set(args) - ik))
    props = lambda n: tools[n].inputSchema.get('properties', {})
    no_dry = sorted(n for n in args if not n.startswith(READ_ONLY_PREFIXES) and 'dry_run' not in props(n))
    assert not no_dry, ('mutating tools without dry_run', no_dry)

    def defs():
        return {p: (api.rig(p) if p.rsplit('/', 1)[1].startswith('IK_') else api.retargeter(p)) for p in (src, dst, rtg)}

    before = defs()
    outcome = {}
    for name, a in args.items():
        a = dict(a)
        if 'dry_run' in props(name):
            a.update(dry_run=True)
            if 'confirm' in props(name):
                a.update(confirm=True)
        result = await mcp_server.mcp.call_tool(name, a)
        blocks = result[0] if isinstance(result, tuple) else result
        text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            raise AssertionError((name, 'non-JSON response', text[:300]))
        if isinstance(payload, dict) and 'errorMessage' in payload:
            outcome[name] = 'guard: ' + payload['errorMessage'][7:100]
        else:
            if 'dry_run' in props(name):
                assert payload.get('dry_run') is True, (name, str(payload)[:300])
            outcome[name] = 'ok'
    after = defs()
    for p in before:
        a, b = dict(before[p]), dict(after[p])
        assert a == b, (p, 'dry runs changed the asset', sorted(k for k in a if a.get(k) != b.get(k)))
    guarded = {k: v for k, v in outcome.items() if v != 'ok'}
    print(json.dumps(guarded, indent=1))
    print(f'{len(args)} IK MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} native guard); fixtures unchanged')


if __name__ == '__main__':
    asyncio.run(run())
