"""Call every foliage MCP tool through the registered FastMCP dispatcher.

Builds a scratch map (before any asset) with two foliage types, a procedural spawner, an instanced foliage actor holding
one registered type with one instance, a procedural foliage volume and a blocking volume over REST. Read-only tools run
for real, mutating tools (including the create tools) as confirmed dry runs; foliage state must be unchanged.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_foliage_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP), 'scratch foliage map is open; run smoke_foliage_live.py cleanup'
    live.use_tag(uuid.uuid4().hex[:6])
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        assert api.call('GET', '/worlds/inspect')['world_path'].startswith(live.MAP)
        ft3 = live.FT.replace('FT_MCP_Cube', 'FT_MCP_Third')
        for path, mesh in ((live.FT, live.CUBE), (live.FT2, live.SPHERE), (ft3, live.CUBE)):
            api.call('POST', '/foliage/types/create', {'TypePath': path, 'AssetPath': mesh, **LIVE})
        api.call('POST', '/foliage/procedural/spawner/create', {'AssetPath': live.SP, **LIVE})
        r = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Foliage.InstancedFoliageActor', 'Location': {'X': 0, 'Y': 0, 'Z': 0}}, timeout=120)
        assert r.is_success, r.text
        for vt in ('ProceduralFoliage', 'ProceduralFoliageBlocking'):
            api.call('POST', '/volumes/create-box', {'VolumeType': vt, 'Name': 'MCP_' + vt, 'Position': {'X': 0, 'Y': 0, 'Z': 0}, 'Extent': {'X': 500, 'Y': 500, 'Z': 200}, **LIVE})
        ifa = live.ifa(api)
        api.call('POST', '/foliage/types/register', {'ActorPath': ifa, 'TypePath': live.FT, 'ExpectedUpdateGuid': live.guid(api), 'ExpectedTypeCount': 0, **LIVE})
        api.call('POST', '/foliage/types/register', {'ActorPath': ifa, 'TypePath': live.FT2, 'ExpectedUpdateGuid': live.guid(api, live.FT2), 'ExpectedTypeCount': 1, **LIVE})
        api.call('POST', '/foliage/types/materials', {'ActorPath': ifa, 'TypePath': live.FT, 'ExpectedUpdateGuid': live.guid(api), 'FieldName': 'OverrideMaterials',
                                                      'ExpectedAssetPaths': [], 'AssetPaths': [''], **LIVE})
        api.call('POST', '/foliage/instances/add', {'ActorPath': ifa, 'TypePath': live.FT, 'ExpectedUpdateGuid': live.guid(api), 'ExpectedInstanceCount': 0, 'Transform': live.xf(100), **LIVE})
        fo = live.falloff(api)
        api.call('POST', '/volumes/foliage-blocking/inline-falloff/linear-keys', {'ActorPath': live.blocking(api)['actor_path'], 'ActorGuid': fo['actor_guid'],
                 'ExpectedLabel': fo['label'], 'bExpectedBoolValue': fo['falloff_enabled'], 'ExpectedCurvePath': fo['external_curve_path'],
                 'ExpectedCurveText': fo['native_snapshot_text'], 'ExpectedPairs': [{'X': k['time'], 'Y': k['value']} for k in fo['keys']],
                 'Pairs': [{'X': 0, 'Y': 1}, {'X': 1, 'Y': 0}], **LIVE})
        before = live.settled(api)
        ft, sp, pc, bv, fo = live.ftype(api), api.call('POST', '/foliage/procedural/spawner/inspect', {'AssetPath': live.SP}), live.procedural(api), live.blocking(api), live.falloff(api)
        inst = live.instances(api)['instances'][0]
        t = dict(actor_path=ifa, type_path=live.FT, expected_update_guid=ft['update_guid'])
        cur = dict(**t, instance_index=0, expected_instance_count=1, expected_base_id=inst['base_id'], expected_location=inst['world_location'],
                   expected_rotation=inst['world_rotation_quaternion'], expected_scale=inst['world_scale'])
        p = dict(actor_path=pc['actor_path'], component_path=pc['component_path'], expected_procedural_guid=pc['procedural_guid'])
        b = dict(actor_path=bv['actor_path'], actor_guid=fo['actor_guid'], expected_label=fo['label'], expected_enabled=fo['falloff_enabled'],
                 expected_external_curve_path=fo['external_curve_path'])
        keys = [[k['time'], k['value']] for k in fo['keys']]
        pt = dict(type_path=live.FT, expected_update_guid=ft['update_guid'])
        args = {
            'inspect_world_foliage': {}, 'inspect_foliage_types': dict(actor_path=ifa), 'inspect_foliage_instances': dict(actor_path=ifa, type_path=live.FT),
            'inspect_foliage_type': dict(type_path=live.FT), 'inspect_world_procedural_foliage': {}, 'inspect_procedural_foliage_spawner': dict(spawner_path=live.SP),
            'inspect_procedural_foliage_blocking_volumes': {}, 'inspect_foliage_blocking_inline_falloff': dict(actor_path=bv['actor_path']),
            'create_foliage_type': dict(type_path=f'{live.D}FT_MCP_New.FT_MCP_New', mesh_path=live.CUBE),
            'create_procedural_foliage_spawner': dict(asset_path=f'{live.D}PFS_MCP_New.PFS_MCP_New'),
            'set_foliage_type_scalar': dict(**t, field='Density', expected_value=ft['density'], value=50),
            'set_foliage_type_bool': dict(**t, field='RandomYaw', expected_value=ft['random_yaw'], value=not ft['random_yaw']),
            'set_foliage_instance_transform': dict(**cur, location=[150, 50, 20], rotation=[0, 0, 0, 1], scale=[2, 2, 2]),
            'delete_foliage_instance': dict(**cur),
            'add_foliage_instance': dict(**t, expected_instance_count=1, location=[300, 0, 0], rotation=[0, 0, 0, 1], scale=[1, 1, 1]),
            'register_foliage_type': dict(actor_path=ifa, type_path=ft3, expected_update_guid=live.guid(api, ft3), expected_type_count=2),
            'set_foliage_type_scale_range': dict(**t, field='ScaleX', expected_range=ft['scale_x'], scale_range=[0.5, 1.5]),
            'set_foliage_type_cull_range': dict(**t, expected_range=[ft['cull_distance_min'], ft['cull_distance_max']], cull_range=[1000, 5000]),
            'set_foliage_type_scaling': dict(**t, expected_mode=ft['scaling'], mode=1),
            'set_foliage_type_mesh': dict(**t, expected_instance_count=1, expected_mesh_path=live.CUBE, mesh_path=live.SPHERE),
            'set_foliage_type_material_slot': dict(**t, field='OverrideMaterials', expected_slot_count=ft['override_materials']['count'], slot_index=0,
                                                   expected_material_path='', material_path=live.MAT),
            'replace_foliage_type_materials': dict(**t, field='OverrideMaterials', expected_material_paths=ft['override_materials']['paths'], material_paths=[live.MAT]),
            'unregister_empty_foliage_type': dict(actor_path=ifa, type_path=live.FT2, expected_update_guid=live.guid(api, live.FT2), expected_type_count=2),
            'set_foliage_type_placement_range': dict(**t, field='ZOffset', expected_range=ft['z_offset_range'], placement_range=[-5, 5]),
            'replace_foliage_type_landscape_layers': dict(**t, field='LandscapeLayers', expected_names=ft['landscape_layers']['names'], names=['Grass']),
            'set_procedural_foliage_spawner_setting': dict(spawner_path=live.SP, field='RandomSeed', expected_value=sp['random_seed'], value=7),
            'set_procedural_foliage_component_bool': dict(**p, field='bShowDebugTiles', expected_value=pc['show_debug_tiles'], value=not pc['show_debug_tiles']),
            'set_procedural_foliage_spawner': dict(**p, expected_spawner_path='', spawner_path=live.SP),
            'set_procedural_foliage_tile_overlap': dict(**p, expected_spawner_path='', expected_overlap=pc['tile_overlap'], overlap=250),
            'replace_procedural_foliage_spawner_types': dict(spawner_path=live.SP, expected_type_paths=[], type_paths=[live.FT, live.FT2]),
            'set_procedural_foliage_terrain_materials': dict(spawner_path=live.SP, expected_enabled=False, expected_material_paths=[], enabled=True, material_paths=[live.MAT]),
            'set_procedural_foliage_blocking_target': dict(actor_path=bv['actor_path'], expected_volume_path='', volume_path=pc['actor_path']),
            'set_procedural_foliage_blocking_falloff': dict(actor_path=bv['actor_path'], expected_enabled=False, expected_curve_path='', enabled=True, curve_path=live.CURVE),
            'set_foliage_type_procedural_setting': dict(**pt, field='CollisionRadius', expected_value=ft['procedural_settings']['CollisionRadius'], value=80),
            'set_foliage_type_procedural_bool': dict(**pt, field='bCanGrowInShade', expected_value=ft['procedural_settings']['bCanGrowInShade'],
                                                     value=not ft['procedural_settings']['bCanGrowInShade']),
            'set_foliage_type_procedural_curve': dict(**pt, field='ScaleCurve', expected_curve_path='', curve_path=live.CURVE),
            'set_foliage_type_procedural_scale': dict(**pt, expected_range=ft['procedural_settings']['procedural_scale'], scale_range=[0.5, 2]),
            'replace_foliage_blocking_linear_falloff': dict(**b, expected_keys=keys, keys=[[0, 1], [0.5, 0.8], [1, 0]], expected_curve_text=fo['native_snapshot_text']),
            'set_foliage_blocking_inline_curve_setting': dict(**b, field_name='DefaultValue', expected_value=fo['default_value'], value=0.5,
                                                              expected_curve_text=fo['native_snapshot_text']),
            'edit_foliage_blocking_inline_keys': dict(**b, expected_curve_text=fo['native_snapshot_text'], expected_key_count=len(keys), operation='Add', time=0.25, value=0.9),
            'set_foliage_blocking_inline_key_setting': dict(**b, expected_curve_text=fo['native_snapshot_text'], expected_key_count=len(keys), key_index=0,
                                                                   field_name='ArriveTangent', expected_value=fo['keys'][0]['arrive_tangent'], value=0.5),
        }
        tools = {tt.name: tt for tt in await mcp_server.mcp.list_tools()}
        names = {n for n in tools if 'foliage' in n}
        assert names == set(args), sorted(names ^ set(args))
        assert len(args) == 41, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})
        outcome = {}
        for name, aa in args.items():
            aa = dict(aa)
            if 'dry_run' in props(name):
                aa.update(dry_run=True)
            if 'confirm' in props(name):
                aa.update(confirm=True)
            result = await mcp_server.mcp.call_tool(name, aa)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(bb.text for bb in blocks if hasattr(bb, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:180]
            else:
                if 'dry_run' in props(name) and isinstance(payload, dict) and 'dry_run' in payload:
                    assert payload['dry_run'] is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        after = live.settled(api)
        assert live.close(after, before), ('dry runs changed foliage', [k for k in after if not live.close(after[k], before.get(k))])
        api.call('POST', '/foliage/types/asset/inspect', {'TypePath': f'{live.D}FT_MCP_New.FT_MCP_New'}, ok=False)
        api.call('POST', '/foliage/procedural/spawner/inspect', {'AssetPath': f'{live.D}PFS_MCP_New.PFS_MCP_New'}, ok=False)
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} foliage MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); foliage unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        for path in (live.MAP, live.FT, live.FT2, live.FT.replace('FT_MCP_Cube', 'FT_MCP_Third'), live.SP):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': path}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
