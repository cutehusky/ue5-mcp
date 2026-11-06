"""Call every render-target asset MCP tool through the registered FastMCP dispatcher.

Builds scratch 2D/cube/volume/2D-array render targets and a matching source-free Texture2D over REST. Read-only tools
run for real, mutating tools as confirmed dry runs; every target's authored snapshot and the texture must be unchanged.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
from smoke_textures_live import guards, load

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}
E = '/Script/Engine.'


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    tag = uuid.uuid4().hex[:6]
    n = lambda base: f'/Game/UE5MCP_Test/{base}_{tag}.{base}_{tag}'
    R2, RC, RV, RA, TEX = n('RT_Mcp2D'), n('RT_McpCube'), n('RT_McpVol'), n('RT_McpArr'), n('T_McpRT')
    assets = (R2, RC, RV, RA, TEX)
    try:
        api.call('POST', '/render-targets/2d/create', {'AssetPath': R2, 'SizeX': 64, 'SizeY': 32, **LIVE})
        api.call('POST', '/render-targets/cube/create', {'AssetPath': RC, 'SizeX': 16, **LIVE})
        api.call('POST', '/render-targets/volume/create', {'AssetPath': RV, 'SizeX': 8, 'SizeY': 8, 'SizeZ': 4, **LIVE})
        api.call('POST', '/render-targets/2d-array/create', {'AssetPath': RA, 'SizeX': 16, 'SizeY': 16, 'SizeZ': 3, **LIVE})
        api.call('POST', '/textures/create-2d', {'AssetPath': TEX, 'SizeX': 64, 'SizeY': 32, **LIVE})
        load(api, TEX)
        snap = lambda kind, p: api.call('POST', f'/render-targets/{kind}/inspect', {'AssetPath': p})['native_authored_snapshot']
        s2, sc, sv, sa = snap('2d', R2), snap('cube', RC), snap('volume', RV), snap('2d-array', RA)
        tex_snap = guards(api, TEX)['ExpectedAssetSnapshot']
        C2, CC, CV, CA = (E + c for c in ('TextureRenderTarget2D', 'TextureRenderTargetCube', 'TextureRenderTargetVolume', 'TextureRenderTarget2DArray'))
        green, black = [0, 1, 0, 1], [0, 0, 0, 1]
        args = {
            'inspect_render_target_2d': dict(asset_path=R2), 'inspect_render_target_cube': dict(asset_path=RC),
            'inspect_render_target_volume': dict(asset_path=RV), 'inspect_render_target_2d_array': dict(asset_path=RA),
            'inspect_loaded_render_targets_2d': dict(path_substring=tag), 'inspect_loaded_render_targets_cube': dict(path_substring=tag),
            'inspect_loaded_render_targets_volume': dict(path_substring=tag), 'inspect_loaded_render_targets_2d_array': dict(path_substring=tag),
            'inspect_render_target_2d_capture_consumers': dict(asset_path=R2), 'inspect_render_target_cube_capture_consumers': dict(asset_path=RC),
            'inspect_render_target_conversion': dict(render_target_path=R2),
            'create_render_target_2d': dict(asset_path=n('RT_McpNew2D'), size_x=32, size_y=32),
            'create_render_target_cube': dict(asset_path=n('RT_McpNewCube'), face_size=16),
            'create_render_target_volume': dict(asset_path=n('RT_McpNewVol'), size_x=4, size_y=4, size_z=4),
            'create_render_target_2d_array': dict(asset_path=n('RT_McpNewArr'), width=8, height=8, slices=2),
            'set_render_target_2d_setting': dict(asset_path=R2, expected_class_path=C2, field_name='TargetGamma', expected_value=0, value=2.2, expected_asset_snapshot=s2),
            'resize_render_target_2d': dict(asset_path=R2, expected_class_path=C2, expected_size_x=64, expected_size_y=32, size_x=128, size_y=16, expected_asset_snapshot=s2),
            'set_render_target_2d_clear_color': dict(asset_path=R2, expected_class_path=C2, expected_size_x=64, expected_size_y=32, expected_format=6,
                                                     expected_rgba=black, rgba=[1, 0, 0, 1], expected_asset_snapshot=s2),
            'set_render_target_cube_setting': dict(asset_path=RC, expected_class_path=CC, expected_face_size=16, field_name='bHDR', expected_value=1, value=0, expected_asset_snapshot=sc),
            'set_render_target_cube_clear_color': dict(asset_path=RC, expected_class_path=CC, expected_face_size=16, expected_hdr=True, expected_rgba=green,
                                                       rgba=[1, 0, 0, 1], expected_asset_snapshot=sc),
            'set_render_target_volume_setting': dict(asset_path=RV, expected_class_path=CV, expected_size_x=8, expected_size_y=8, expected_size_z=4,
                                                     field_name='bSupportsUAV', expected_value=0, value=1, expected_asset_snapshot=sv),
            'set_render_target_volume_clear_color': dict(asset_path=RV, expected_class_path=CV, expected_size_x=8, expected_size_y=8, expected_size_z=4,
                                                         expected_hdr=True, expected_rgba=green, rgba=[0, 0, 1, 1], expected_asset_snapshot=sv),
            'resize_render_target_volume': dict(asset_path=RV, expected_class_path=CV, expected_xyz=[8, 8, 4], xyz=[4, 4, 8], expected_asset_snapshot=sv),
            'set_render_target_2d_array_setting': dict(asset_path=RA, expected_class_path=CA, expected_size_x=16, expected_size_y=16, expected_slices=3,
                                                       field_name='TargetGamma', expected_value=0, value=1.5, expected_asset_snapshot=sa),
            'set_render_target_2d_array_clear_color': dict(asset_path=RA, expected_class_path=CA, expected_size_x=16, expected_size_y=16, expected_slices=3,
                                                           expected_hdr=True, expected_rgba=green, rgba=[0.5, 0.5, 0.5, 1], expected_asset_snapshot=sa),
            'resize_render_target_2d_array': dict(asset_path=RA, expected_class_path=CA, expected_xy_slices=[16, 16, 3], xy_slices=[8, 8, 6], expected_asset_snapshot=sa),
            'convert_render_target_to_texture': dict(render_target_path=R2, asset_path=n('T_McpConv'), expected_class_path=C2, expected_asset_snapshot=s2),
            'update_texture_from_render_target': dict(render_target_path=R2, texture_path=TEX, expected_class_path=C2, expected_target_snapshot=s2,
                                                      expected_destination_snapshot=tex_snap),
            'export_render_target_image': dict(render_target_path=RA, filename_stem=f'rt_mcp_{tag}', image_format='png', expected_class_path=CA,
                                               expected_asset_snapshot=sa, slice_index=2),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        assert {t for t in tools if 'render_target' in t} == set(args), sorted({t for t in tools if 'render_target' in t} ^ set(args))
        assert len(args) == 29, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})

        def state():
            return ([snap(k, p) for k, p in (('2d', R2), ('cube', RC), ('volume', RV), ('2d-array', RA))],
                    api.call('POST', '/textures/2d/settings/inspect', {'AssetPath': TEX})['native_authored_snapshot'],
                    guards(api, TEX)['ExpectedSourceId'])
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
        assert state() == before, 'dry runs changed the render targets or texture'
        for created in ('RT_McpNew2D', 'RT_McpNewCube', 'RT_McpNewVol', 'RT_McpNewArr', 'T_McpConv'):
            r = httpx.get(BASE + '/assets/describe', params={'asset_path': n(created)}, timeout=60)
            assert r.status_code >= 400, (created, 'dry run created an asset')
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} render-target MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); targets unchanged')
        assert not guarded, guarded
    finally:
        for p in assets:
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
