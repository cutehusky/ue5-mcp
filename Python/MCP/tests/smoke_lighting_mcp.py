"""Call every lighting, fog, cloud and sky-atmosphere MCP tool through the registered FastMCP dispatcher.

Builds a scratch map with one actor of each kind over REST, then runs read-only tools for real and mutating tools as
confirmed dry runs, with expected values taken from the live inspections. The scene must be unchanged afterwards;
the original map is reloaded and the scratch map deleted. The sky-light occlusion tint reaches the native guard when
the project does not generate mesh distance fields, and the shaft bloom tint while light-shaft bloom is off.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
from smoke_lighting_live import CLOUD_MATERIAL, CUBEMAP, FALLBACK, Family, Lights, policy_target

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
MAP = '/Game/UE5MCP_Test/MCP_LightingMcp'


def xyz(v):
    return list(v)


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    original = FALLBACK if original.startswith(MAP) else original
    if api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP):
        api.call('POST', '/worlds/load', {'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True})
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    try:
        here = {'X': 0, 'Y': 0, 'Z': 0}
        for t in ('point', 'spot', 'directional', 'sky'):
            api.call('POST', '/lighting/create', {'bConfirm': True, 'LightType': t, 'Name': f'MCP_{t}', 'Location': here})
        for route, name in (('/fog/height/create', 'MCP_fog'), ('/fog/local/create', 'MCP_localfog'), ('/clouds/create', 'MCP_cloud'), ('/atmosphere/create', 'MCP_atmo')):
            api.call('POST', route, {'bConfirm': True, 'Name': name, 'Location': here})
        L = Lights(api)
        fog, lfog = Family(api, '/fog/height/inspect', 'fog_components').all()['MCP_fog'], Family(api, '/fog/local/inspect', 'local_fog_components').all()['MCP_localfog']
        cloud, atmo = Family(api, '/clouds/inspect', 'cloud_components').all()['MCP_cloud'], Family(api, '/atmosphere/inspect', 'atmosphere_components').all()['MCP_atmo']
        pt, sp, dl, sk = L.all()['MCP_point'], L.all()['MCP_spot'], L.all()['MCP_directional'], L.sky()['MCP_sky']
        I = lambda x: dict(actor_path=x['actor_path'], component_path=x['component_path'])
        T = lambda x, prefix='expected_': {f'{prefix}location': xyz(x['world_location']), f'{prefix}rotation': xyz(x['world_rotation_quaternion']), f'{prefix}scale': xyz(x['component_scale'])}
        MOVE = {'location': [10, 20, 30], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}

        def policy(route, x, name):
            info = api.call('POST', route, policy_target(L, name))
            return {**I(x), 'actor_guid': info['actor_guid'], 'expected_label': info['label']}, info

        def first_field(info):
            f = next(f for f in info['fields'] if f.get('native_can_edit') and isinstance(f.get('value'), (int, float)))
            v = f['value']
            new = 1 - v if f['name'][0] == 'b' and v in (0, 1) else (v + 1 if f.get('type') in ('int32',) or f['name'].endswith(('Mode', 'PerPixel', 'Method')) else (v - 0.1 if v > 0.5 else v + 0.1))
            return f['name'], v, new

        adv, advi = policy('/lights/advanced-policy/inspect', pt, 'MCP_point')
        lm, lmi = policy('/lights/lightmass/inspect', pt, 'MCP_point')
        ds, dsi = policy('/lights/directional-shadows/inspect', dl, 'MCP_directional')
        dc, dci = policy('/lights/directional-clouds/inspect', dl, 'MCP_directional')
        sh, shi = policy('/lights/shafts/inspect', dl, 'MCP_directional')
        vc, vci = policy('/lights/view-channels/inspect', pt, 'MCP_point')
        rp, rpi = policy('/lights/ray-policy/inspect', pt, 'MCP_point')
        le, lei = policy('/lights/local-exposure/inspect', pt, 'MCP_point')
        wi, wii = policy('/lights/world-influence/inspect', sp, 'MCP_spot')
        so, soi = policy('/lights/sky/occlusion/inspect', sk, 'MCP_sky')
        cp, cpi = policy('/lights/sky/capture-policy/inspect', sk, 'MCP_sky')
        F = lambda d, info: dict(zip(('field_name', 'expected_value', 'value'), first_field(info)))
        args = {
            'inspect_world_light_components': {}, 'inspect_world_sky_lights': {}, 'inspect_world_height_fog': {}, 'inspect_world_local_fog': {},
            'inspect_world_volumetric_clouds': {}, 'inspect_world_sky_atmospheres': {},
            'inspect_lights_page': dict(count=2), 'inspect_sky_lights_page': dict(count=2), 'inspect_height_fog_page': dict(count=2),
            'inspect_local_fog_page': dict(count=2), 'inspect_volumetric_clouds_page': dict(count=2), 'inspect_sky_atmospheres_page': dict(count=2),
            'set_light_scalar': {**I(pt), 'field': 'Intensity', 'expected_value': pt['intensity'], 'value': 777},
            'set_light_bool': {**I(dl), 'field': 'bAtmosphereSunLight', 'expected_value': dl['atmosphere_sun_light'], 'value': not dl['atmosphere_sun_light']},
            'set_light_stored_color': {**I(pt), 'expected_color': pt['stored_color_rgba'], 'color': [1, 2, 3, 255]},
            'set_sky_light_scalar': {**I(sk), 'field': 'Intensity', 'expected_value': sk['intensity'], 'value': 3},
            'set_sky_light_bool': {**I(sk), 'field': 'bLowerHemisphereIsBlack', 'expected_value': sk['lower_hemisphere_solid_color'], 'value': not sk['lower_hemisphere_solid_color']},
            'set_sky_light_source': {**I(sk), 'expected_source_type': sk['source_type'], 'expected_cubemap_path': sk['cubemap_path'], 'source_type': 'SpecifiedCubemap', 'cubemap_path': CUBEMAP},
            'set_light_visible': {**I(pt), 'expected_visible': True, 'visible': False},
            'create_light_actor': dict(light_type='rect', name='MCP_dry', location=[0, 0, 0]),
            'delete_light_actor': {**I(sp), 'expected_class_path': '/Script/Engine.SpotLight'},
            'set_sky_light_hemisphere_color': {**I(sk), 'expected_color': sk['lower_hemisphere_color'], 'color': [0.1, 0.1, 0.1, 1]},
            'set_light_transform': {**I(pt), **T(pt), **MOVE},
            'set_light_mobility': {**I(pt), 'expected_mobility': pt['mobility'], 'mobility': 'Static'},
            'set_directional_light_atmosphere_index': {**I(dl), 'expected_index': dl['atmosphere_sun_light_index'], 'index': 1},
            'set_local_light_units_intensity': {**I(pt), 'expected_units': pt['intensity_units'], 'expected_intensity': pt['intensity'], 'units': 'Lumens', 'intensity': 800},
            'set_light_texture': {**I(pt), 'field': 'LightFunctionMaterial', 'expected_asset_path': pt['light_function_material_path'],
                                  'asset_path': '/Engine/EngineMaterials/DefaultLightFunctionMaterial.DefaultLightFunctionMaterial'},
            'set_light_channels': {**I(pt), 'expected_channels': pt['lighting_channels'], 'channels': [0, 1, 0]},
            'queue_sky_light_capture': {**I(sk), 'expected_source_type': sk['source_type'], 'expected_cubemap_path': sk['cubemap_path'], 'expected_real_time': sk['real_time_capture']},
            'set_light_function_scale': {**I(pt), 'expected_scale': pt['light_function_scale'], 'scale': [2, 2, 2]},
            'set_height_fog_scalar': {**I(fog), 'field': 'FogDensity', 'expected_value': fog['fog_density'], 'value': 0.1},
            'set_height_fog_volumetric_enabled': {**I(fog), 'expected_enabled': fog['enable_volumetric_fog'], 'enabled': not fog['enable_volumetric_fog']},
            'set_height_fog_render_flag': {**I(fog), 'field': 'bHoldout', 'expected_enabled': fog['holdout'], 'enabled': not fog['holdout']},
            'set_height_fog_second_layer': {**I(fog), 'expected_values': [fog['second_fog_density'], fog['second_fog_height_falloff'], fog['second_fog_height_offset']], 'values': [0.01, 0.1, 10]},
            'create_height_fog': dict(name='MCP_fogdry', location=[0, 0, 0]),
            'delete_height_fog': I(fog),
            'set_height_fog_visible': {**I(fog), 'expected_visible': True, 'visible': False},
            'set_height_fog_color': {**I(fog), 'field': 'FogInscatteringLuminance', 'expected_color': fog['fog_inscattering_luminance'], 'color': [0.5, 0.5, 0.5, 1]},
            'set_height_fog_albedo': {**I(fog), 'expected_color': fog['volumetric_albedo_rgba'], 'color': [1, 2, 3, 255]},
            'set_height_fog_cubemap': {**I(fog), 'expected_cubemap_path': fog['inscattering_cubemap_path'], 'cubemap_path': CUBEMAP},
            'set_height_fog_transform': {**I(fog), **T(fog), **MOVE},
            'set_local_fog_scalar': {**I(lfog), 'field': 'FogPhaseG', 'expected_value': lfog['fog_phase_g'], 'value': 0.3},
            'set_local_fog_visible': {**I(lfog), 'expected_visible': True, 'visible': False},
            'set_local_fog_transform': {**I(lfog), **T(lfog), **MOVE},
            'set_local_fog_color': {**I(lfog), 'field': 'FogAlbedo', 'expected_color': lfog['fog_albedo'], 'color': [0.2, 0.2, 0.2, 1]},
            'set_local_fog_priority': {**I(lfog), 'expected_priority': lfog['fog_sort_priority'], 'priority': 2},
            'create_local_fog': dict(name='MCP_lfdry', location=[0, 0, 0]),
            'delete_local_fog': I(lfog),
            'set_volumetric_cloud_scalar': {**I(cloud), 'field': 'LayerHeight', 'expected_value': cloud['scalars']['LayerHeight'], 'value': 7},
            'set_volumetric_cloud_bool': {**I(cloud), 'field': 'bHoldout', 'expected_value': cloud['flags']['bHoldout'], 'value': not cloud['flags']['bHoldout']},
            'set_volumetric_cloud_ground_albedo': {**I(cloud), 'expected_color': cloud['ground_albedo_rgba'], 'color': [9, 9, 9, 255]},
            'set_volumetric_cloud_visible': {**I(cloud), 'expected_visible': True, 'visible': False},
            'set_volumetric_cloud_tracing_mode': {**I(cloud), 'expected_mode': cloud['tracing_max_distance_mode'], 'mode': 1 - cloud['tracing_max_distance_mode']},
            'set_volumetric_cloud_material': {**I(cloud), 'expected_material_path': cloud['material_soft_path'], 'expected_resolved_material_path': cloud['resolved_material_path'], 'material_path': CLOUD_MATERIAL},
            'create_volumetric_cloud': dict(name='MCP_clouddry', location=[0, 0, 0]),
            'delete_volumetric_cloud': I(cloud),
            'set_volumetric_cloud_transform': {**I(cloud), **T(cloud), **MOVE},
            'set_sky_atmosphere_scalar': {**I(atmo), 'field': 'BottomRadius', 'expected_value': atmo['scalars']['BottomRadius'], 'value': 6000},
            'set_sky_atmosphere_bool': {**I(atmo), 'field': 'bHoldout', 'expected_value': atmo['flags']['bHoldout'], 'value': not atmo['flags']['bHoldout']},
            'set_sky_atmosphere_color': {**I(atmo), 'field': 'MieScattering', 'expected_color': atmo['MieScattering'], 'color': [0.1, 0.1, 0.1, 1]},
            'set_sky_atmosphere_ground_albedo': {**I(atmo), 'expected_color': atmo['ground_albedo_rgba'], 'color': [5, 5, 5, 255]},
            'set_sky_atmosphere_absorption_tent': {**I(atmo), 'expected_tent': [atmo['absorption_tent_tip_altitude'], atmo['absorption_tent_tip_value'], atmo['absorption_tent_width']], 'tent': [20, 0.5, 10]},
            'set_sky_atmosphere_visible': {**I(atmo), 'expected_visible': True, 'visible': False},
            'set_sky_atmosphere_transform_mode': {**I(atmo), 'expected_mode': atmo['transform_mode'], 'mode': 1 if atmo['transform_mode'] != 1 else 2},
            'create_sky_atmosphere': dict(name='MCP_atmodry', location=[0, 0, 0]),
            'delete_sky_atmosphere': I(atmo),
            'set_sky_atmosphere_transform': {**I(atmo), 'expected_mode': atmo['transform_mode'], **T(atmo), **MOVE},
            'inspect_light_advanced_policy': I(pt), 'inspect_light_lightmass_settings': I(pt), 'inspect_directional_light_shadows': I(dl),
            'inspect_directional_light_clouds': I(dl), 'inspect_light_shaft_settings': I(dl), 'inspect_light_view_channels': I(pt),
            'inspect_light_ray_policy': I(pt), 'inspect_local_light_exposure': I(pt), 'inspect_sky_light_occlusion': I(sk),
            'inspect_sky_light_capture_policy': I(sk), 'inspect_light_world_influence': I(sp),
            'set_light_advanced_policy': {**adv, **F(adv, advi)},
            'set_light_lightmass_setting': {**lm, 'expected_settings_text': lmi['native_snapshot_text'], **F(lm, lmi)},
            'set_directional_light_shadow_setting': {**ds, **F(ds, dsi)},
            'set_directional_light_cloud_setting': {**dc, **F(dc, dci)},
            'set_directional_light_luminance_color': {**dc, 'field_name': 'AtmosphereSunDiskColorScale', 'expected_rgba': dci['atmosphere_sun_disk_color_scale'], 'rgba': [2, 2, 2, 1]},
            'set_light_shaft_setting': {**sh, **F(sh, shi)},
            'set_light_shaft_bloom_tint': {**sh, 'expected_rgba_bytes': shi['bloom_tint_bytes'], 'rgba_bytes': [9, 9, 9, 255]},
            'set_directional_light_shaft_override_direction': {**sh, 'expected_direction': shi['override_direction'], 'direction': [0, 0, -1]},
            'set_light_view_channels': {**vc, 'expected_channels': vci['view_channels'], 'channels': [0, 1, 0, 0, 0]},
            'set_light_ray_policy': {**rp, **F(rp, rpi)},
            'set_local_light_exposure_blend': {**le, 'expected_value': lei['inverse_exposure_blend'], 'value': 0.5},
            'set_sky_light_occlusion': {**so, **F(so, soi)},
            'set_sky_light_occlusion_tint': {**so, 'expected_rgba_bytes': soi['occlusion_tint_bytes'], 'rgba_bytes': [9, 9, 9, 255]},
            'set_sky_light_capture_policy': {**cp, **F(cp, cpi)},
            'set_sky_light_color': {**cp, 'expected_rgba_bytes': cpi['light_color_bytes'], 'rgba_bytes': [9, 9, 9, 255]},
            'set_light_world_influence': {**wi, 'expected_affects_world': wii['affects_world'], 'affects_world': not wii['affects_world']},
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        assert len(args) == 94, len(args)
        props = lambda n: tools[n].inputSchema.get('properties', {})
        assert all(n.startswith('inspect_') or 'dry_run' in props(n) for n in args), [n for n in args if not n.startswith('inspect_') and 'dry_run' not in props(n)]
        distance_fields = {f['name']: f for f in soi['fields']}['Contrast']['native_can_edit']
        expected_guard = set() if distance_fields else {'set_sky_light_occlusion_tint'}
        if not {f['name']: f for f in shi['fields']}['bEnableLightShaftBloom']['value']:
            expected_guard.add('set_light_shaft_bloom_tint')  # BloomTint is only editable with light-shaft bloom enabled

        def state():
            s = {'lights': L.all(), 'sky': L.sky()}
            for name, (route, key) in {'fog': ('/fog/height/inspect', 'fog_components'), 'lfog': ('/fog/local/inspect', 'local_fog_components'),
                                       'cloud': ('/clouds/inspect', 'cloud_components'), 'atmo': ('/atmosphere/inspect', 'atmosphere_components')}.items():
                s[name] = api.call('POST', route, {})[key]
            return json.loads(json.dumps(s).replace('"has_processed_sky_texture": true', '"has_processed_sky_texture": false'))
        before = state()
        outcome = {}
        for name, a in args.items():
            a = dict(a)
            if 'dry_run' in props(name):
                a.update(dry_run=True, confirm=True)
            result = await mcp_server.mcp.call_tool(name, a)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:160]
            else:
                if 'dry_run' in props(name) and isinstance(payload, dict) and 'dry_run' in payload:
                    assert payload['dry_run'] is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        after = state()
        assert after == before, 'dry runs changed the scene'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} lighting/atmosphere MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); scene unchanged')
        assert set(guarded) == expected_guard, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
