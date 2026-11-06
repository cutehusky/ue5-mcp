"""Call every texture-asset MCP tool (except file import/reimport, covered by smoke_texture_import_live.py) through
the registered FastMCP dispatcher.

Builds scratch textures over REST: a Texture2D in pad-to-power-of-two mode, one in resize-to-specific-resolution mode
without mips (for build resize and downscale), a texture array, cube, cube array and a tiled volume texture. Read-only
tools run for real (decoding ones with confirm), mutating tools as confirmed dry runs; every texture's settings,
source identity and array/volume layout must be unchanged.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
from smoke_textures_live import guards, load, numeric, settings

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}
SKIP = {'import_texture', 'reimport_texture'}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    tag = uuid.uuid4().hex[:6]
    n = lambda base: f'/Game/UE5MCP_Test/{base}_{tag}.{base}_{tag}'
    A, B, ARR, CUBE, CUBE2, CARR, VOL = n('T_McpA'), n('T_McpB'), n('TA_Mcp'), n('TC_Mcp'), n('TC_Mcp2'), n('TCA_Mcp'), n('TV_Mcp')
    assets = (A, B, ARR, CUBE, CUBE2, CARR, VOL)
    try:
        for p in (A, B):
            api.call('POST', '/textures/create-2d', {'AssetPath': p, **LIVE, 'SizeX': 64, 'SizeY': 32})
            load(api, p)

        def mode(path, suffix):
            m = settings(api, path)['PowerOfTwoMode']
            want = next(e['value'] for e in m['enum_values'] if e['name'].endswith(suffix))
            api.call('POST', '/textures/2d/padding-policy', {**guards(api, path), **LIVE, 'FieldName': 'PowerOfTwoMode', 'ExpectedValue': numeric(m), 'Value': want})
        mode(A, 'PadToPowerOfTwo')
        mode(B, 'ResizeToSpecificResolution')
        mip = settings(api, B)['MipGenSettings']
        api.call('POST', '/textures/2d/mip-policy', {**guards(api, B), **LIVE, 'FieldName': 'MipGenSettings', 'ExpectedValue': numeric(mip),
                                                     'Value': next(e['value'] for e in mip['enum_values'] if e['name'].endswith('NoMipmaps'))})
        api.call('POST', '/texture-arrays/create', {'AssetPath': ARR, **LIVE, 'SourcePaths': [A]})
        api.call('POST', '/texture-cubes/create', {'AssetPath': CUBE, **LIVE, 'SizeX': 16})
        api.call('POST', '/texture-cubes/create', {'AssetPath': CUBE2, **LIVE, 'SizeX': 16})
        api.call('POST', '/texture-cube-arrays/create', {'AssetPath': CARR, **LIVE, 'SourcePaths': [CUBE]})
        api.call('POST', '/volume-textures/create', {'AssetPath': VOL, **LIVE, 'SourceTexturePath': A, 'ExpectedFormat': 2, 'ExpectedSourceSizeX': 64,
                                                     'ExpectedSourceSizeY': 32, 'SizeX': 32, 'SizeY': 32})
        for p in assets:
            load(api, p)
        ga, gb = guards(api, A), guards(api, B)
        sa, sb = settings(api, A), settings(api, B)
        ac = api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': A})
        arr = [x['path'] for x in api.call('POST', '/texture-arrays/inspect', {'AssetPath': ARR})['source_textures']]
        carr = api.call('POST', '/texture-cube-arrays/inspect', {'AssetPath': CARR})
        carr_src = [x['path'] for x in carr.get('source_cubes', carr.get('source_textures', []))]
        vol = api.call('POST', '/volume-textures/inspect', {'AssetPath': VOL})
        down = api.call('POST', '/textures/downscale/inspect-page', {'AssetPath': B, 'Count': 4})
        px = api.call('POST', '/textures/source-mips/pixels/inspect-page', {**ga, 'bConfirm': True, 'Count': 1})['pixels'][0]['rgba']
        G = lambda g: dict(expected_class_path=g['ExpectedClassPath'], expected_source_id=g['ExpectedSourceId'], expected_asset_snapshot=g['ExpectedAssetSnapshot'])
        G2 = lambda g: dict(expected_class_path=g['ExpectedClassPath'], expected_source_id=g['ExpectedSourceId'])
        V = lambda s, name: numeric(s[name])
        args = {
            'inspect_texture': dict(asset_path=A), 'inspect_texture_source': dict(asset_path=A), 'inspect_texture_2d_settings': dict(asset_path=A),
            'inspect_texture_2d_array': dict(asset_path=ARR), 'inspect_loaded_texture_2d_arrays': dict(path_substring=tag),
            'inspect_source_volume_texture': dict(asset_path=VOL), 'inspect_loaded_source_volume_textures': dict(path_substring=tag),
            'inspect_source_texture_cube': dict(asset_path=CUBE), 'inspect_loaded_source_texture_cubes': dict(path_substring=tag),
            'inspect_source_texture_cube_array': dict(asset_path=CARR), 'inspect_loaded_source_texture_cube_arrays': dict(path_substring=tag),
            'inspect_texture_array_source_compatibility': dict(asset_path=ARR), 'inspect_texture_source_mips': dict(asset_path=A),
            'inspect_texture_source_layout': dict(asset_path=A), 'inspect_texture_source_identity': dict(asset_path=A),
            'inspect_texture_streaming_state': dict(asset_path=A), 'inspect_texture_material_overrides': dict(asset_path=A),
            'inspect_texture_expression_references': dict(asset_path=A), 'inspect_texture_brush_assets': dict(asset_path=A),
            'inspect_texture_virtual_policy': dict(asset_path=A), 'inspect_texture_alpha_coverage': dict(asset_path=A),
            'inspect_texture_compression_settings': dict(asset_path=A), 'inspect_texture_sampling_settings': dict(asset_path=A),
            'inspect_texture_downscale_overrides': dict(asset_path=B),
            'inspect_texture_source_pixels': dict(asset_path=A, expected_source_id=ga['ExpectedSourceId'], count=2),
            'inspect_texture_source_mip_statistics': dict(asset_path=A, expected_source_id=ga['ExpectedSourceId']),
            'validate_texture_source_mip_payloads': dict(asset_path=A, expected_source_id=ga['ExpectedSourceId']),
            'inspect_texture_source_linear_pixels': dict(asset_path=A, expected_source_id=ga['ExpectedSourceId'], count=2),
            'inspect_texture_source_linear_statistics': dict(asset_path=A, expected_source_id=ga['ExpectedSourceId']),
            'compare_texture_source_mips': dict(texture_a=A, texture_b=B, expected_source_id_a=ga['ExpectedSourceId'], expected_source_id_b=gb['ExpectedSourceId']),
            'measure_texture_source_alpha_coverage': dict(asset_path=A, **G(ga)),
            # Mutations, all as confirmed dry runs.
            'set_texture_2d_array_address': dict(asset_path=ARR, expected_class_path='/Script/Engine.Texture2DArray', field_name='AddressX', expected_value=0, value=1),
            'set_source_volume_texture_address': dict(asset_path=VOL, expected_class_path='/Script/Engine.VolumeTexture', expected_value=vol['address_mode'], value=1),
            'reorder_texture_2d_array_sources': dict(asset_path=ARR, expected_class_path='/Script/Engine.Texture2DArray', expected_source_paths=arr, source_index_order=[0]),
            'replace_texture_2d_array_sources': dict(asset_path=ARR, expected_class_path='/Script/Engine.Texture2DArray', expected_source_paths=arr, source_paths=[A]),
            'set_source_volume_texture_tiles': dict(asset_path=VOL, expected_class_path='/Script/Engine.VolumeTexture', expected_source_path=A, expected_tile_xy=[32, 32],
                                                    tile_xy=[16, 16], expected_source_xy=[64, 32], expected_source_format=2),
            'set_source_volume_texture_source': dict(asset_path=VOL, expected_class_path='/Script/Engine.VolumeTexture', expected_source_path=A, source_texture_path=A,
                                                     expected_tile_xy=[32, 32], tile_xy=[16, 16], expected_source_xy=[64, 32], expected_source_format=2),
            'create_source_texture_2d_array': dict(asset_path=n('TA_McpNew'), source_paths=[A]),
            'create_source_volume_texture': dict(asset_path=n('TV_McpNew'), source_texture_path=A, tile_xy=[32, 32], expected_source_xy=[64, 32], expected_source_format=2),
            'replace_source_texture_cube_array_sources': dict(asset_path=CARR, expected_class_path='/Script/Engine.TextureCubeArray', expected_source_paths=carr_src, source_paths=[CUBE, CUBE2]),
            'reorder_source_texture_cube_array_sources': dict(asset_path=CARR, expected_class_path='/Script/Engine.TextureCubeArray', expected_source_paths=carr_src, source_index_order=[0]),
            'create_source_texture_cube_array': dict(asset_path=n('TCA_McpNew'), source_cube_paths=[CUBE, CUBE2]),
            'duplicate_source_texture': dict(source_texture_path=A, asset_path=n('T_McpDup'), expected_class_path=ga['ExpectedClassPath'], expected_source_id=ga['ExpectedSourceId']),
            'create_texture_2d_without_source_file': dict(asset_path=n('T_McpNew'), width=32, height=32),
            'create_texture_cube_without_source_file': dict(asset_path=n('TC_McpNew'), face_size=16),
            'create_volume_texture_without_source_file': dict(asset_path=n('TV_McpSolid'), width=8, height=8, depth=4),
            'create_texture_2d_array_without_source_file': dict(asset_path=n('TA_McpSolid'), width=16, height=16, slices=2),
            'create_texture_cube_array_without_source_file': dict(asset_path=n('TCA_McpSolid'), face_size=16, cube_count=2),
            'set_texture_virtual_policy': dict(asset_path=A, **G(ga), field_name='VirtualTexturePrefetchMips', expected_value=0, value=2),
            'set_texture_2d_address': dict(asset_path=A, **G(ga), field_name='AddressX', expected_value=V(sa, 'AddressX'), value=1),
            'set_texture_2d_filter': dict(asset_path=A, **G(ga), expected_value=V(sa, 'Filter'), value=1),
            'set_texture_2d_mip_policy': dict(asset_path=A, **G(ga), expected_value=V(sa, 'MipGenSettings'), value=2),
            'set_texture_2d_lod_limit': dict(asset_path=A, **G(ga), field_name='LODBias', expected_value=V(sa, 'LODBias'), value=1),
            'set_texture_2d_processing_flag': dict(asset_path=A, **G(ga), field_name='bFlipGreenChannel', expected_value=False, value=True),
            'set_texture_2d_adjustment': dict(asset_path=A, **G(ga), field_name='AdjustBrightness', expected_value=1.0, value=1.5),
            'set_texture_2d_mip_load_policy': dict(asset_path=A, **G(ga), expected_value=V(sa, 'MipLoadOptions'), value=1),
            'set_texture_2d_padding_policy': dict(asset_path=A, **G(ga), expected_value=V(sa, 'PowerOfTwoMode'), value=2),
            'set_texture_2d_build_resize': dict(asset_path=B, **G(gb), expected_xy=[0, 0], xy=[32, 16]),
            'set_texture_2d_padding_color': dict(asset_path=A, **G(ga), expected_rgba=[0, 0, 0, 255], rgba=[1, 2, 3, 255]),
            'fill_texture_source_mip': dict(asset_path=A, **G(ga), mip_index=0, rgba=[9, 9, 9, 255]),
            'patch_texture_source_mip': dict(asset_path=A, **G(ga), mip_index=0, start_pixel=0, expected_rgba_bytes=px, rgba_bytes=[1, 2, 3, 4]),
            'copy_texture_source_mip': dict(source_texture_path=B, destination_texture_path=A, expected_source_id=gb['ExpectedSourceId'], expected_destination_source_id=ga['ExpectedSourceId'],
                                            expected_destination_class=ga['ExpectedClassPath'], expected_destination_snapshot=ga['ExpectedAssetSnapshot']),
            'export_texture_source_dds': dict(asset_path=A, filename_stem='mcp_dry', **G(ga)),
            'export_texture_source_image': dict(asset_path=A, filename_stem='mcp_dry', image_format='png', **G(ga)),
            'set_texture_alpha_coverage': dict(asset_path=A, enabled=True, thresholds_rgba=[0.5, 0, 0, 0], expected_enabled=ac['enabled'],
                                               expected_thresholds_rgba=ac['thresholds_rgba'], **G(ga)),
            'set_texture_compression_setting': dict(asset_path=A, field_name='CompressionNoAlpha', value=1, expected_value=0, **G(ga)),
            'set_texture_sampling_setting': dict(asset_path=A, field_name='NeverStream', value=1, expected_value=0, **G(ga)),
            'set_texture_downscale_override': dict(asset_path=B, operation='Default', platform_key='', value=2, expected_value=down['default_value'],
                                                   expected_exists=False, **G(gb)),
            'set_texture_color_adjustment': dict(asset_path=A, field_name='AdjustHue', value=20, expected_value=0, **G(ga)),
            'set_texture_build_resize': dict(asset_path=B, width=16, height=16, expected_width=0, expected_height=0, **G(gb)),
            'set_texture_padding_color': dict(asset_path=A, rgba_bytes=[4, 5, 6, 255], expected_rgba_bytes=[0, 0, 0, 255], **G(ga)),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        texture_tools = {n_ for n_, t in tools.items() if any(k in (t.description or '') for k in ()) or n_ in args or n_ in SKIP}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        assert len(args) == 71, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})

        def state():
            out = {}
            for p in (A, B):
                out[p] = (api.call('POST', '/textures/2d/settings/inspect', {'AssetPath': p})['native_authored_snapshot'],
                          api.call('POST', '/textures/source-mips/statistics', {**guards(api, p), 'bConfirm': True})['channels'])
            out['arr'] = api.call('POST', '/texture-arrays/inspect', {'AssetPath': ARR})['source_textures']
            out['vol'] = {k: v for k, v in api.call('POST', '/volume-textures/inspect', {'AssetPath': VOL}).items() if k not in ('scope', 'package_dirty')}
            out['down'] = api.call('POST', '/textures/downscale/inspect-page', {'AssetPath': B, 'Count': 4})['overrides']
            return out
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
        assert state() == before, 'dry runs changed the textures'
        for created in ('T_McpNew', 'TC_McpNew', 'TV_McpSolid', 'TA_McpSolid', 'TCA_McpSolid', 'T_McpDup', 'TA_McpNew', 'TV_McpNew', 'TCA_McpNew'):
            r = httpx.get(BASE + '/assets/describe', params={'asset_path': n(created)}, timeout=60)
            assert r.status_code >= 400, (created, 'dry run created an asset')
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} texture MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); textures unchanged')
        # No texture route enables VirtualTextureStreaming, and the VT policy fields require it.
        assert set(guarded) == {'set_texture_virtual_policy'}, guarded
    finally:
        for p in assets:
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
