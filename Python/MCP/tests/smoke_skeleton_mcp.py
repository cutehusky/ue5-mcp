"""Call every Skeleton / skeletal-mesh socket MCP tool through the registered FastMCP dispatcher.

Run after `smoke_skeleton_live.py prepare` and before `verify`. Read-only tools run for real; mutating
tools run as confirmed dry runs against the duplicated fixtures, which must be unchanged afterwards.
"""
import asyncio
import json
import sys

from smoke_skeleton_live import STATE, PROJECT, ORIG_SKELETON, QUINN, PROP, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
READ_ONLY = ('inspect_', 'compare_')


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    sk, mesh = json.loads(STATE.read_text(encoding='utf-8'))['owned']
    s = api.skel(sk)
    vb = s['virtual_bones'][0]['name']
    pose = s['retarget_sources'][0]['pose_name']
    args = {
        'inspect_skeleton_structure': dict(asset_path=sk),
        'edit_skeleton_socket': dict(asset_path=sk, socket_name='McpDry', bone_name='head'),
        'delete_skeleton_socket': dict(asset_path=sk, socket_name='Weapon'),
        'create_skeleton_virtual_bone': dict(asset_path=sk, source_bone='hand_l', target_bone='foot_l'),
        'delete_skeleton_virtual_bones': dict(asset_path=sk, names=[vb]),
        'rename_skeleton_virtual_bone': dict(asset_path=sk, name=vb, new_name='VB McpDry'),
        'rename_skeleton_socket': dict(asset_path=sk, socket_name='Weapon', new_name='McpDry'),
        'edit_mesh_socket': dict(asset_path=mesh, socket_name='McpDry', bone_name='head'),
        'delete_mesh_socket': dict(asset_path=mesh, socket_name='MeshWeapon'),
        'rename_mesh_socket': dict(asset_path=mesh, socket_name='MeshWeapon', new_name='McpDry'),
        'inspect_mesh_sockets': dict(asset_path=mesh),
        'customize_mesh_socket': dict(asset_path=mesh, socket_name='HandGrip_R'),
        'promote_mesh_socket': dict(asset_path=mesh, socket_name='MeshWeapon'),
        'inspect_runtime_skeletal_socket': dict(component_path='/Game/Nope.Nope:Component', socket_name='Weapon'),
        'set_skeleton_translation_retargeting': dict(asset_path=sk, bones=['head'], mode='Skeleton'),
        'edit_skeleton_compatibility': dict(asset_path=sk, source_path=ORIG_SKELETON, operation='remove'),
        'set_skeleton_compatibility_retarget_policy': dict(asset_path=sk, enabled=False),
        'compare_skeleton_hierarchies': dict(target_path=sk, source_path=ORIG_SKELETON),
        'set_skeleton_blend_profile_scales': dict(asset_path=sk, profile_name='MCP_Upper', bones=['head'], scale=0.25),
        'create_skeleton_blend_profile': dict(asset_path=sk, profile_name='McpDry'),
        'rename_skeleton_blend_profile': dict(asset_path=sk, profile_name='MCP_Upper', new_name='McpDry'),
        'reset_skeleton_blend_profile_entries': dict(asset_path=sk, profile_name='MCP_Upper', bones=['spine_01']),
        'set_skeleton_blend_profile_mode': dict(asset_path=sk, profile_name='MCP_Upper', mode='WeightFactor'),
        'inspect_skeleton_blend_profile_references': dict(asset_path=sk, profile_name='MCP_Upper'),
        'delete_skeleton_blend_profile': dict(asset_path=sk, profile_name='MCP_Upper', allow_referenced=True),
        'inspect_skeleton_blend_profile_scales': dict(asset_path=sk, profile_name='MCP_Upper'),
        'inspect_skeleton_retarget_pose': dict(asset_path=sk, pose_name=pose, bones=['pelvis']),
        'edit_skeleton_retarget_source': dict(asset_path=sk, pose_name='McpDry', source_mesh_path=QUINN),
        'delete_skeleton_retarget_source': dict(asset_path=sk, pose_name=pose, allow_referenced=True),
        'rename_skeleton_retarget_source': dict(asset_path=sk, pose_name=pose, new_name='McpDry'),
        'duplicate_skeleton_retarget_source': dict(asset_path=sk, pose_name=pose, new_name='McpDry'),
        'edit_skeleton_stored_retarget_pose': dict(asset_path=sk, pose_name=pose, edits=[{'Bone': 'head', 'Rotation': {'Pitch': 0, 'Yaw': 5, 'Roll': 0}}]),
        'reset_skeleton_stored_retarget_pose': dict(asset_path=sk, pose_name=pose, bones=['head']),
        'edit_skeleton_curve_metadata': dict(asset_path=sk, name='McpDry'),
        'change_skeleton_curve_metadata': dict(asset_path=sk, name='MCP_Renamed', operation='rename', new_name='McpDry'),
        'edit_skeletal_preview_attachment': dict(asset_path=sk, preview_asset_path=PROP, attach_name='Weapon'),
    }
    tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
    family = {n for n in tools if any(k in n for k in ('skeleton', 'mesh_socket', 'skeletal_socket', 'skeletal_preview')) and '_ik_' not in n and 'pose_search' not in n}
    assert family == set(args), ('uncovered', sorted(family - set(args)), 'unknown', sorted(set(args) - family))
    props = lambda n: tools[n].inputSchema.get('properties', {})
    no_dry = sorted(n for n in args if not n.startswith(READ_ONLY) and 'dry_run' not in props(n))
    assert not no_dry, ('mutating tools without dry_run', no_dry)

    defs = lambda: (api.skel(sk), api.mesh_sockets(mesh), api.skel(ORIG_SKELETON))
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
            outcome[name] = 'guard: ' + payload['errorMessage'][7:110]
        else:
            if 'dry_run' in props(name):
                assert payload.get('dry_run') is True, (name, str(payload)[:300])
            outcome[name] = 'ok'
    assert defs() == before, 'dry runs changed the fixtures or the original skeleton'
    guarded = {k: v for k, v in outcome.items() if v != 'ok'}
    print(json.dumps(guarded, indent=1))
    print(f'{len(args)} Skeleton MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} native guard); fixtures unchanged')


if __name__ == '__main__':
    asyncio.run(run())
