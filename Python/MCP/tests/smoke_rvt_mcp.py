"""Call every runtime-virtual-texture and virtual-texture-builder MCP tool through the registered FastMCP dispatcher.

Builds a scratch map (before any asset) with an RVT volume assigned an RVT and builder, a static-mesh writer and an
align actor, plus a scratch material with an RVT sample and an instance with an RVT override, all over REST.
Read-only tools run for real, mutating tools as confirmed dry runs; the RVT, builder, component, writer, sample and
instance overrides must be unchanged afterwards and no dry run may create an asset or actor.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_rvt_world_live as world

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}
SAMPLE_CLASS = '/Script/Engine.MaterialExpressionRuntimeVirtualTextureSampleParameter'
RVT_CLASS = '/Script/Engine.RuntimeVirtualTexture'
# The builder's mobile split works with the project's mobile virtual-texturing setting on; the streaming-mip build
# dry run is fine, but nothing here renders.
# create_runtime_virtual_texture_instance_override: the fixture already holds that override, and duplicates are refused
# (the real creation is covered by smoke_rvt_assets_live.py).
EXPECTED_GUARDS = {'create_runtime_virtual_texture_instance_override'}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(world.MAP), 'scratch RVT map is open; run smoke_rvt_world_live.py cleanup'
    tag = uuid.uuid4().hex[:6]
    n = lambda base: f'/Game/UE5MCP_Test/{base}_{tag}.{base}_{tag}'
    RVT, VTB, MAT, MI = n('RVT_Mcp'), n('VTB_Mcp'), n('M_McpRvt'), n('MI_McpRvt')
    world.RVT, world.VTB = RVT, VTB
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': world.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': world.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': world.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        wpath = api.call('GET', '/worlds/inspect')['world_path']
        assert wpath.startswith(world.MAP), wpath
        api.call('POST', '/runtime-virtual-textures/create', {'AssetPath': RVT, **LIVE})
        api.call('POST', '/virtual-texture-builders/create', {'AssetPath': VTB, **LIVE})
        vol = world.volume(api, 'MCP_RVTVolume', 0)
        writer_actor = world.spawn(api, '/Script/Engine.StaticMeshActor', 0)
        align_actor = world.spawn(api, '/Script/Engine.TargetPoint', 500)
        comp, writer = world.handles(api, {'volume': vol, 'writer': writer_actor})
        api.call('POST', '/runtime-virtual-textures/writers/list', {**writer.ids(), 'SourcePaths': [RVT], 'ExpectedSourcePaths': [], **LIVE})
        for field, path in (('VirtualTexture', RVT), ('StreamingTexture', VTB)):
            api.call('POST', '/runtime-virtual-textures/components/reference', {**comp.ids(), 'FieldName': field, 'AssetPath': path, 'ExpectedTargetPath': 'None', **LIVE})
        # Satisfy the native gates of the edits dispatched below.
        snap = api.call('POST', '/runtime-virtual-textures/inspect', {'AssetPath': RVT})['native_authored_snapshot']
        api.call('POST', '/runtime-virtual-textures/policy', {'AssetPath': RVT, 'ExpectedClassPath': RVT_CLASS, 'ExpectedAssetSnapshot': snap,
                                                              'FieldName': 'bUseCustomPriority', 'Value': 1, 'ExpectedValue': 0, **LIVE})
        api.call('POST', '/runtime-virtual-textures/components/flag', {**comp.ids(), 'FieldName': 'bUseStreamingMipsFixedColor', 'Value': 1, 'ExpectedValue': 0, **LIVE})
        api.call('POST', '/runtime-virtual-textures/components/numeric', {**comp.ids(), 'FieldName': 'StreamLowMips', 'Value': 2, 'ExpectedValue': 0, **LIVE})
        api.call('POST', '/runtime-virtual-textures/components/bounds-actor', {**comp.ids(), 'AssetPath': align_actor, 'ExpectedTargetPath': '', **LIVE})
        for src, dst in (('/Game/LevelPrototyping/Interactable/JumpPad/Assets/Materials/M_SimpleGlow', MAT),
                         ('/Game/LevelPrototyping/Interactable/JumpPad/Assets/Materials/MI_GlowNT', MI)):
            assert httpx.post(BASE + '/assets/duplicate', json={'AssetPath': src, 'DestinationPath': dst.split('.')[0]}, timeout=180).is_success
        assert httpx.post(BASE + '/materials/expressions', json={'AssetPath': MAT, 'ExpressionClass': SAMPLE_CLASS, 'ExpressionName': 'RVTSample'}, timeout=180).is_success
        assert httpx.patch(BASE + '/material-instances/parent', json={'AssetPath': MI, 'ParentPath': MAT}, timeout=180).is_success
        rinfo = api.call('POST', '/runtime-virtual-textures/inspect', {'AssetPath': RVT})
        rsnap = rinfo['native_authored_snapshot']
        sample = lambda: api.call('POST', '/runtime-virtual-textures/expressions/inspect', {'ExpressionPath': MAT + ':RVTSample', 'OwnerAssetPath': MAT})
        s = sample()
        sg = {'ExpressionPath': s['expression_path'], 'OwnerAssetPath': MAT, 'ExpectedClassPath': SAMPLE_CLASS, 'ExpressionGuid': s['expression_guid']}
        api.call('POST', '/runtime-virtual-textures/expressions/reference', {**sg, 'ExpectedChannels': s['type_packed_adaptive'], 'AssetPath': RVT,
                                                                            'ExpectedTargetPath': 'None', 'ExpectedRuntimeTextureSnapshot': rsnap, **LIVE})
        s = sample()
        dc = api.call('POST', '/runtime-virtual-textures/instance-parameters/declarations/inspect-page', {'OwnerAssetPath': MI, 'Count': 8})['declarations'][0]
        ovp = lambda: api.call('POST', '/runtime-virtual-textures/instance-parameters/inspect-page', {'OwnerAssetPath': MI, 'Count': 8})
        ov = ovp()
        api.call('POST', '/runtime-virtual-textures/instance-parameters/create', {'OwnerAssetPath': MI, 'AssetPath': RVT, 'ExpectedClassPath': ov['class_path'],
                                                                                   'ExpectedAssetSnapshot': ov['native_override_snapshot'], 'Start': dc['native_declaration_index'],
                                                                                   'ExpressionGuid': dc['parameter_guid'], 'Name': dc['parameter_name'],
                                                                                   'ParameterAssociation': dc['association'], 'ParameterIndex': dc['layer_index'], **LIVE})
        ov = ovp()
        o = json.loads(ov['native_override_snapshot'])['overrides'][0]
        ci, wi = comp.inspect(), writer.inspect()
        cid = dict(actor_path=comp.actor, component_path=comp.component, expected_class_path=ci['class_path'], actor_guid=ci['actor_guid'],
                   expected_label=ci['actor_label'], expected_asset_snapshot=ci['native_authored_snapshot'])
        wid = dict(actor_path=writer.actor, component_path=writer.component, expected_class_path=wi['class_path'], actor_guid=wi['actor_guid'],
                   expected_label=wi['actor_label'], expected_asset_snapshot=wi['native_authored_snapshot'])
        loc = [float(v.split('=')[1]) for v in ci['world_location'].split()]
        scale = [float(v.split('=')[1]) for v in ci['world_scale'].split()]
        tr = world.transform(loc, scale)
        contrib = [c['component_path'] for c in api.call('POST', '/runtime-virtual-textures/components/bounds-contributors/inspect-page', {**comp.ref(), 'Count': 16})['primitives']]
        b = api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})
        ra = dict(asset_path=RVT, expected_class_path=RVT_CLASS, expected_asset_snapshot=rsnap)
        sid = dict(expression_path=s['expression_path'], owner_asset_path=MAT, expected_class_path=SAMPLE_CLASS, expression_guid=s['expression_guid'])
        mi = dict(material_instance_path=MI, expected_class_path=ov['class_path'], expected_override_snapshot=ov['native_override_snapshot'])
        args = {
            'inspect_runtime_virtual_texture': dict(asset_path=RVT), 'inspect_loaded_runtime_virtual_textures': dict(path_substring=tag),
            'inspect_runtime_virtual_texture_layers': dict(asset_path=RVT),
            'create_runtime_virtual_texture': dict(asset_path=n('RVT_McpNew')),
            'set_runtime_virtual_texture_policy': dict(**ra, field_name='bAdaptive', expected_value=0, value=1),
            'set_runtime_virtual_texture_size': dict(**ra, field_name='TileSize', expected_value=2, value=3),
            'set_runtime_virtual_texture_priority': dict(**ra, expected_value=0, value=5),
            'set_runtime_virtual_texture_material_data': dict(**ra, expected_float4=[0, 0, 0, 0], float4=[1, 2, 3, 4]),
            'set_runtime_virtual_texture_layout': dict(**ra, field_name='MaterialType', expected_value=3, value=1),
            'duplicate_runtime_virtual_texture': dict(source_asset_path=RVT, asset_path=n('RVT_McpDup'), expected_class_path=RVT_CLASS, expected_asset_snapshot=rsnap),
            'inspect_runtime_virtual_texture_components': dict(asset_path=RVT), 'inspect_runtime_virtual_texture_writers': dict(asset_path=RVT),
            'inspect_runtime_virtual_texture_expressions': dict(asset_path=RVT), 'inspect_runtime_virtual_texture_overrides': dict(asset_path=RVT),
            'inspect_virtual_texture_builder': dict(asset_path=VTB), 'inspect_loaded_virtual_texture_builders': dict(path_substring=tag),
            'inspect_virtual_texture_builder_components': dict(asset_path=VTB),
            'create_virtual_texture_builder': dict(asset_path=n('VTB_McpNew')),
            'set_virtual_texture_builder_mobile_policy': dict(asset_path=VTB, expected_class_path=b['class_path'], expected_build_hash=b['build_hash_decimal'],
                                                              expected_texture_paths=['None', 'None'], expected_value=False, value=True),
            'inspect_runtime_virtual_texture_component_settings': dict(actor_path=comp.actor, component_path=comp.component),
            'set_runtime_virtual_texture_component_flag': dict(**cid, field_name='bHidePrimitives', expected_value=False, value=True),
            'set_runtime_virtual_texture_component_numeric': dict(**cid, field_name='ExpandBounds', expected_value=0, value=25),
            'set_runtime_virtual_texture_component_enum': dict(**cid, field_name='LossyCompressionAmount', expected_value=0, value=3),
            'set_runtime_virtual_texture_component_fixed_color': dict(**cid, expected_rgba=[0, 0, 0, 0], rgba=[1, 0, 0, 1]),
            'set_runtime_virtual_texture_component_reference': dict(**cid, field_name='VirtualTexture', expected_target_path=RVT, asset_path=''),
            'set_runtime_virtual_texture_bounds_actor': dict(**cid, expected_bounds_actor_path=align_actor, bounds_actor_path=''),
            'set_runtime_virtual_texture_component_platform': dict(**cid, operation='Override', platform_key='Mobile', expected_value=False, value=True),
            'inspect_runtime_virtual_texture_component_platforms': dict(actor_path=comp.actor, component_path=comp.component),
            'inspect_runtime_virtual_texture_writer_settings': dict(actor_path=writer.actor, component_path=writer.component),
            'set_runtime_virtual_texture_writer_numeric': dict(**wid, field_name='VirtualTextureCullMips', expected_value=0, value=2),
            'set_runtime_virtual_texture_writer_main_pass': dict(**wid, expected_value=1, value=0),
            'set_runtime_virtual_texture_writer_list': dict(**wid, expected_paths=[RVT], paths=[]),
            'discover_runtime_virtual_texture_components': dict(runtime_texture_path=RVT), 'discover_runtime_virtual_texture_writers': dict(runtime_texture_path=RVT),
            'create_runtime_virtual_texture_volume': dict(world_path=wpath, name='MCP_RVTVolumeNew', location=[0, 500, 0]),
            'delete_runtime_virtual_texture_volume': dict(world_path=wpath, **cid),
            'set_runtime_virtual_texture_volume_transform': dict(**cid, expected_transform=tr, transform=world.transform([10, 20, 30], [100, 100, 100])),
            'inspect_runtime_virtual_texture_bounds_contributors': dict(actor_path=comp.actor, component_path=comp.component),
            'align_runtime_virtual_texture_bounds': dict(**cid, expected_runtime_texture_snapshot=rsnap, expected_transform=tr, expected_contributor_paths=contrib),
            'build_runtime_virtual_texture_streaming_mips': dict(**cid, expected_runtime_texture_snapshot=rsnap, expected_transform=tr, expected_build_hash=b['build_hash_decimal'],
                                                                 expected_texture_paths=['None', 'None'], expected_builder_consumer_paths=[comp.component]),
            'inspect_runtime_virtual_texture_streaming_status': dict(actor_path=comp.actor, component_path=comp.component),
            'inspect_runtime_virtual_texture_sample': dict(expression_path=s['expression_path'], owner_asset_path=MAT),
            'synchronize_runtime_virtual_texture_sample': dict(**sid, runtime_texture_path=RVT, expected_runtime_texture_snapshot=rsnap, expected_type_packed_adaptive=s['type_packed_adaptive']),
            'set_runtime_virtual_texture_sample_reference': dict(**sid, expected_target_path=RVT, expected_type_packed_adaptive=s['type_packed_adaptive'], runtime_texture_path=''),
            'set_runtime_virtual_texture_sample_policy': dict(**sid, expected_asset_snapshot=s['native_authored_snapshot'], field_name='TextureAddressMode', expected_value=0, value=1),
            'inspect_runtime_virtual_texture_instance_parameters': dict(material_instance_path=MI),
            'inspect_runtime_virtual_texture_parameter_declarations': dict(material_instance_path=MI),
            'inspect_runtime_virtual_texture_effective_parameters': dict(material_instance_path=MI),
            'create_runtime_virtual_texture_instance_override': dict(**mi, native_declaration_index=dc['native_declaration_index'], parameter_name=dc['parameter_name'],
                                                                     association=dc['association'], layer_index=dc['layer_index'], parameter_guid=dc['parameter_guid'], runtime_texture_path=RVT),
            'set_runtime_virtual_texture_instance_parameter': dict(**mi, override_index=0, parameter_guid=o['expression_guid'], expected_target_path=RVT, runtime_texture_path=RVT),
            'remove_runtime_virtual_texture_instance_override': dict(**mi, override_index=0, parameter_guid=o['expression_guid'], expected_target_path=RVT),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        names = {t for t in tools if 'runtime_virtual_texture' in t or 'virtual_texture_builder' in t}
        assert names == set(args), sorted(names ^ set(args))
        assert len(args) == 51, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})

        def state():
            return (api.call('POST', '/runtime-virtual-textures/inspect', {'AssetPath': RVT})['native_authored_snapshot'],
                    api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})['separate_texture_for_mobile'],
                    comp.state(), writer.state(), sample()['native_authored_snapshot'], ovp()['native_override_snapshot'],
                    [c['actor_path'] for c in api.call('POST', '/runtime-virtual-textures/components/discover', {'Count': 8})['components']])
        before = state()
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
                outcome[name] = 'guard: ' + payload['errorMessage'][7:180]
            else:
                if 'dry_run' in props(name) and isinstance(payload, dict) and 'dry_run' in payload:
                    assert payload['dry_run'] is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        assert world.close(state(), before), 'dry runs changed RVT state'
        for created in ('RVT_McpNew', 'RVT_McpDup', 'VTB_McpNew'):
            assert httpx.get(BASE + '/assets/describe', params={'asset_path': n(created)}, timeout=60).status_code >= 400, created
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} runtime-VT MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); state unchanged')
        assert set(guarded) == EXPECTED_GUARDS, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': world.MAP}, timeout=180)
        for p in (MI, MAT, RVT, VTB):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
