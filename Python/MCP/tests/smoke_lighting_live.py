"""Live lighting and atmosphere authoring on a scratch map.

prepare: create a map with point/spot/rect/directional/sky lights, height fog, local fog, volumetric cloud and sky
atmosphere; edit them with expected-value guards, dry runs and undo/redo; save the map and snapshot every inspection.
verify (fresh editor): reload the map, compare the cold inspections, then delete the map.
"""
import argparse
import json
import math
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'lighting.json'
MAP = '/Game/UE5MCP_Test/MCP_Lighting'
# Loaded (never edited) when a run stopped with the scratch map open and no other map was recorded.
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson.Lvl_ThirdPerson'
CUBEMAP = '/Engine/EngineMaterials/DefaultCubemap.DefaultCubemap'
CLOUD_MATERIAL = '/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud.m_SimpleVolumetricCloud'
TYPES = ('point', 'spot', 'rect', 'directional', 'sky')


def close(a, b, tol=1e-3):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    return a == b


def snake(field, overrides={'DisabledBrightness': 'light_function_disabled_brightness', 'IESBrightnessScale': 'ies_brightness_scale'}):
    if field in overrides:
        return overrides[field]
    out = ''
    for i, ch in enumerate(field.lstrip('b') if field[:2] in ('bU', 'bA') else field):
        out += ('_' if ch.isupper() and i else '') + ch.lower()
    return out


def diff(before, after):
    return {k for k in set(before) | set(after) if not close(before.get(k), after.get(k))}


class Lights:
    def __init__(self, api):
        self.api = api

    def all(self):
        return {l['actor_path'].rsplit('.', 1)[1]: l for l in self.api.call('POST', '/lighting/components/inspect', {})['lights']}

    def sky(self):
        return {l['actor_path'].rsplit('.', 1)[1]: l for l in self.api.call('POST', '/lighting/sky/inspect', {})['sky_lights']}

    def ids(self, name, sky=False):
        l = (self.sky() if sky else self.all())[name]
        return {'bConfirm': True, 'ActorPath': l['actor_path'], 'ComponentPath': l['component_path']}

    def edit(self, route, name, body, expect_keys, sky=False, undo=False):
        """Apply an edit with a dry run first; the given readback keys (and only those, plus derived ones) must change."""
        get = self.sky if sky else self.all
        before = get()[name]
        r = self.api.call('POST', route, {**self.ids(name, sky), **body, 'bDryRun': True})
        assert r.get('dry_run') is True, r
        assert diff(before, get()[name]) == set(), (route, 'dry run changed state')
        self.api.call('POST', route, {**self.ids(name, sky), **body})
        after = get()[name]
        changed = diff(before, after)
        assert set(expect_keys) <= changed, (route, body, sorted(changed), {k: (before.get(k), after.get(k)) for k in expect_keys})
        if undo:
            self.api.undo(); assert diff(before, get()[name]) == set(), (route, 'undo did not restore')
            self.api.redo(); assert diff(after, get()[name]) == set(), (route, 'redo did not reapply')
        return before, after


def light_stage(api, L):
    for t in TYPES:
        api.call('POST', '/lighting/create', {'bConfirm': True, 'LightType': t, 'Name': f'MCP_{t}', 'Location': {'X': 0, 'Y': 0, 'Z': 300}})
    api.call('POST', '/lighting/create', {'bConfirm': True, 'LightType': 'laser', 'Name': 'MCP_bad'}, ok=False)
    api.call('POST', '/lighting/create', {'LightType': 'point', 'Name': 'MCP_unconfirmed'}, ok=False)
    api.call('POST', '/lighting/create', {'bConfirm': True, 'LightType': 'point', 'Name': 'MCP_dry', 'bDryRun': True})
    lights = L.all()
    assert {'MCP_point', 'MCP_spot', 'MCP_rect', 'MCP_directional'} <= set(lights) and 'MCP_dry' not in lights, sorted(lights)
    assert 'MCP_sky' in L.sky(), sorted(L.sky())
    p = lights['MCP_point']
    # Scalars with expected-value guards, per-type field gating, undo/redo.
    api.call('POST', '/lighting/scalar', {**L.ids('MCP_point'), 'FieldName': 'Intensity', 'ExpectedValue': p['intensity'] + 1, 'Value': 10}, ok=False)
    api.call('POST', '/lighting/scalar', {**L.ids('MCP_point'), 'FieldName': 'InnerConeAngle', 'ExpectedValue': 0, 'Value': 10}, ok=False)
    L.edit('/lighting/scalar', 'MCP_point', {'FieldName': 'Intensity', 'ExpectedValue': p['intensity'], 'Value': 1234}, ['intensity'], undo=True)
    for name, field, value in (('MCP_point', 'Temperature', 4000), ('MCP_point', 'AttenuationRadius', 750), ('MCP_point', 'SourceRadius', 12),
                               ('MCP_point', 'SoftSourceRadius', 6), ('MCP_point', 'SourceLength', 20), ('MCP_spot', 'InnerConeAngle', 10),
                               ('MCP_spot', 'OuterConeAngle', 30), ('MCP_rect', 'SourceWidth', 80), ('MCP_rect', 'SourceHeight', 40),
                               ('MCP_rect', 'BarnDoorAngle', 45), ('MCP_rect', 'BarnDoorLength', 15), ('MCP_directional', 'LightSourceAngle', 1.5),
                               ('MCP_directional', 'LightSourceSoftAngle', 0.5), ('MCP_point', 'IndirectLightingIntensity', 2),
                               ('MCP_point', 'VolumetricScatteringIntensity', 3), ('MCP_point', 'ShadowBias', 0.25), ('MCP_point', 'ShadowSlopeBias', 0.75),
                               ('MCP_point', 'ShadowSharpen', 0.5), ('MCP_point', 'ShadowResolutionScale', 2), ('MCP_point', 'ContactShadowLength', 0.2),
                               ('MCP_point', 'ContactShadowCastingIntensity', 0.5), ('MCP_point', 'ContactShadowNonCastingIntensity', 0.25),
                               ('MCP_point', 'MaxDrawDistance', 5000), ('MCP_point', 'MaxDistanceFadeRange', 500),
                               ('MCP_point', 'LightFunctionFadeDistance', 2000), ('MCP_point', 'DisabledBrightness', 0.25),
                               ('MCP_point', 'IESBrightnessScale', 2)):
        cur = L.all()[name]
        key = snake(field)
        assert key in cur, (field, key, sorted(cur))
        r = api.call('POST', '/lighting/scalar', {**L.ids(name), 'FieldName': field, 'ExpectedValue': cur[key], 'Value': value})
        assert r['would_change'] and close(r['requested_value'], value), (field, r)
    after = L.all()['MCP_point']
    assert close(after['temperature'], 4000) and close(after['contact_shadow_length'], 0.2) and close(after['max_draw_distance'], 5000), after
    assert close(L.all()['MCP_spot'].get('outer_cone_angle'), 30) and close(L.all()['MCP_rect'].get('source_width'), 80), (L.all()['MCP_spot'], L.all()['MCP_rect'])
    # Bools, stored color, visibility, mobility, channels.
    L.edit('/lighting/bool', 'MCP_directional', {'FieldName': 'bAtmosphereSunLight', 'bExpectedValue': True, 'bValue': False}, ['atmosphere_sun_light'])
    # IES brightness needs an assigned IES profile; the engine ships none, so only the guard is checked.
    api.call('POST', '/lighting/bool', {**L.ids('MCP_point'), 'FieldName': 'bUseIESBrightness', 'bExpectedValue': False, 'bValue': True}, ok=False)
    api.call('POST', '/lighting/color', {**L.ids('MCP_point'), 'ExpectedColor': [1, 2, 3, 4], 'Color': [255, 0, 0, 255]}, ok=False)
    L.edit('/lighting/color', 'MCP_point', {'ExpectedColor': L.all()['MCP_point']['stored_color_rgba'], 'Color': [255, 128, 0, 255]}, ['stored_color_rgba'], undo=True)
    L.edit('/lighting/visible', 'MCP_spot', {'bExpectedValue': True, 'bValue': False}, ['visible'])
    api.call('POST', '/lighting/mobility', {**L.ids('MCP_rect'), 'ExpectedMobility': L.all()['MCP_rect']['mobility'], 'Mobility': 'Wobbly'}, ok=False)
    L.edit('/lighting/mobility', 'MCP_rect', {'ExpectedMobility': L.all()['MCP_rect']['mobility'], 'Mobility': 'Movable'}, ['mobility'])
    L.edit('/lighting/channels', 'MCP_point', {'ExpectedChannels': L.all()['MCP_point']['lighting_channels'], 'Channels': [1, 1, 0]}, ['lighting_channels'])
    # Units/intensity pair, atmosphere index, function scale, transform.
    pu = L.all()['MCP_point']
    L.edit('/lighting/units-intensity', 'MCP_point', {'ExpectedUnits': pu['intensity_units'], 'ExpectedValue': pu['intensity'], 'Units': 'EV', 'Value': -2}, ['intensity', 'intensity_units'])
    assert L.all()['MCP_point']['intensity_units_name'] == 'EV', L.all()['MCP_point']['intensity_units_name']
    assert L.all()['MCP_point']['intensity'] < 0, 'negative EV not stored'
    pu = L.all()['MCP_point']
    api.call('POST', '/lighting/units-intensity', {**L.ids('MCP_point'), 'ExpectedUnits': pu['intensity_units'], 'ExpectedValue': pu['intensity'], 'Units': 'Lumens', 'Value': -2}, ok=False)
    L.edit('/lighting/bool', 'MCP_point', {'FieldName': 'bUseInverseSquaredFalloff', 'bExpectedValue': L.all()['MCP_point']['inverse_squared_falloff'], 'bValue': not L.all()['MCP_point']['inverse_squared_falloff']}, ['inverse_squared_falloff'])
    # Without inverse-squared falloff the engine forces Unitless, so a unit change must be refused rather than half-applied.
    pu = L.all()['MCP_point']
    api.call('POST', '/lighting/units-intensity', {**L.ids('MCP_point'), 'ExpectedUnits': pu['intensity_units'], 'ExpectedValue': pu['intensity'], 'Units': 'Candelas', 'Value': 10}, ok=False)
    assert L.all()['MCP_point']['intensity_units_name'] == 'Unitless' and close(L.all()['MCP_point']['intensity'], pu['intensity'])
    L.edit('/lighting/atmosphere-index', 'MCP_directional', {'ExpectedValue': 0, 'Value': 1}, ['atmosphere_sun_light_index'])
    L.edit('/lighting/function-scale', 'MCP_point', {'ExpectedScale': {'X': 1024, 'Y': 1024, 'Z': 1024}, 'Scale': {'X': 512, 'Y': 256, 'Z': 128}}, ['light_function_scale'])
    t = {'Translation': {'X': 100, 'Y': 200, 'Z': 300}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}
    cur = L.all()['MCP_point']
    exp = {'Translation': dict(zip('XYZ', cur['world_location'])), 'Rotation': dict(zip('XYZW', cur['world_rotation_quaternion'])), 'Scale3D': dict(zip('XYZ', cur['component_scale']))}
    L.edit('/lighting/transform', 'MCP_point', {'ExpectedTransform': exp, 'Transform': t}, ['world_location'], undo=True)
    # Light-function material and IES texture assignment (wrong-class guard).
    api.call('POST', '/lighting/texture', {**L.ids('MCP_point'), 'FieldName': 'LightFunctionMaterial', 'ExpectedAssetPath': 'None', 'AssetPath': '/Engine/EngineResources/DefaultTexture.DefaultTexture'}, ok=False)
    L.edit('/lighting/texture', 'MCP_point', {'FieldName': 'LightFunctionMaterial', 'ExpectedAssetPath': 'None', 'AssetPath': '/Engine/EngineMaterials/DefaultLightFunctionMaterial.DefaultLightFunctionMaterial'}, ['light_function_material_path'])
    rect = L.all()['MCP_rect']
    L.edit('/lighting/texture', 'MCP_rect', {'FieldName': 'SourceTexture', 'ExpectedAssetPath': rect.get('source_texture_path', 'None'), 'AssetPath': '/Engine/EngineResources/DefaultTexture.DefaultTexture'}, ['source_texture_path'])
    # Deletion: class guard, dry run, real delete of an extra light.
    api.call('POST', '/lighting/create', {'bConfirm': True, 'LightType': 'point', 'Name': 'MCP_doomed', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    D = L.ids('MCP_doomed')
    api.call('POST', '/lighting/delete', {**D, 'ExpectedClassPath': '/Script/Engine.SpotLight'}, ok=False)
    api.call('POST', '/lighting/delete', {**D, 'ExpectedClassPath': '/Script/Engine.PointLight', 'bDryRun': True})
    assert 'MCP_doomed' in L.all()
    api.call('POST', '/lighting/delete', {**D, 'ExpectedClassPath': '/Script/Engine.PointLight'})
    assert 'MCP_doomed' not in L.all()
    api.undo(); assert 'MCP_doomed' in L.all()
    api.redo(); assert 'MCP_doomed' not in L.all()


class Family:
    """One inspectable actor family (fog, local fog, clouds, atmosphere) keyed by actor name."""
    def __init__(self, api, route, key):
        self.api, self.route, self.key = api, route, key

    def all(self):
        return {x['actor_path'].rsplit('.', 1)[1]: x for x in self.api.call('POST', self.route, {})[self.key]}

    def ids(self, name):
        x = self.all()[name]
        return {'bConfirm': True, 'ActorPath': x['actor_path'], 'ComponentPath': x['component_path']}

    def edit(self, route, name, body, expect_keys, undo=False):
        before = self.all()[name]
        r = self.api.call('POST', route, {**self.ids(name), **body, 'bDryRun': True})
        assert r.get('dry_run') is True, r
        assert diff(before, self.all()[name]) == set(), (route, 'dry run changed state')
        self.api.call('POST', route, {**self.ids(name), **body})
        after = self.all()[name]
        changed = diff(before, after)
        assert set(expect_keys) <= changed, (route, body, sorted(changed))
        if undo:
            self.api.undo(); assert diff(before, self.all()[name]) == set(), (route, 'undo did not restore')
            self.api.redo(); assert diff(after, self.all()[name]) == set(), (route, 'redo did not reapply')
        return before, after


def transform_of(x):
    return {'Translation': dict(zip('XYZ', x['world_location'])), 'Rotation': dict(zip('XYZW', x['world_rotation_quaternion'])),
            'Scale3D': dict(zip('XYZ', x['component_scale']))}


MOVED = {'Translation': {'X': 50, 'Y': -50, 'Z': 1000}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 2, 'Y': 2, 'Z': 2}}


def sky_stage(api, L):
    s = L.sky()['MCP_sky']
    api.call('POST', '/lighting/sky/scalar', {**L.ids('MCP_sky', True), 'FieldName': 'Intensity', 'ExpectedValue': s['intensity'] + 5, 'Value': 2}, ok=False)
    L.edit('/lighting/sky/scalar', 'MCP_sky', {'FieldName': 'Intensity', 'ExpectedValue': s['intensity'], 'Value': 2.5}, ['intensity'], sky=True, undo=True)
    for field, value in (('IndirectLightingIntensity', 1.5), ('VolumetricScatteringIntensity', 0.5), ('SourceCubemapAngle', 90), ('SkyDistanceThreshold', 200000)):
        key = snake(field)
        L.edit('/lighting/sky/scalar', 'MCP_sky', {'FieldName': field, 'ExpectedValue': L.sky()['MCP_sky'][key], 'Value': value}, [key], sky=True)
    for field, key in (('bLowerHemisphereIsBlack', 'lower_hemisphere_solid_color'), ('bRealTimeCapture', 'real_time_capture')):
        cur = L.sky()['MCP_sky'][key]
        L.edit('/lighting/sky/bool', 'MCP_sky', {'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur}, [key], sky=True)
    s = L.sky()['MCP_sky']
    source = {'ExpectedSourceType': s['source_type'], 'ExpectedCubemapPath': s['cubemap_path'], 'SourceType': 'SpecifiedCubemap'}
    api.call('POST', '/lighting/sky/source', {**L.ids('MCP_sky', True), **source, 'CubemapPath': '/Engine/EngineResources/DefaultTexture.DefaultTexture'}, ok=False)
    L.edit('/lighting/sky/source', 'MCP_sky', {**source, 'CubemapPath': CUBEMAP}, ['source_type', 'cubemap_path'], sky=True)
    s = L.sky()['MCP_sky']
    L.edit('/lighting/sky/hemisphere-color', 'MCP_sky', {'ExpectedLinearColor': s['lower_hemisphere_color'], 'LinearColor': [0.1, 0.2, 0.3, 1]}, ['lower_hemisphere_color'], sky=True)
    # A capture needs a visible, non-real-time sky light.
    if L.sky()['MCP_sky']['real_time_capture']:
        L.edit('/lighting/sky/bool', 'MCP_sky', {'FieldName': 'bRealTimeCapture', 'bExpectedValue': True, 'bValue': False}, ['real_time_capture'], sky=True)
    capture = lambda: {**L.ids('MCP_sky', True), 'ExpectedSourceType': L.sky()['MCP_sky']['source_type'], 'ExpectedCubemapPath': L.sky()['MCP_sky']['cubemap_path'], 'bExpectedValue': False}
    assert api.call('POST', '/lighting/sky/queue-capture', {**capture(), 'bDryRun': True})['dry_run'] is True
    api.call('POST', '/lighting/sky/queue-capture', capture())
    L.edit('/lighting/visible', 'MCP_sky', {'bExpectedValue': True, 'bValue': False}, ['visible'], sky=True)
    api.call('POST', '/lighting/sky/queue-capture', capture(), ok=False)


FOG_KEYS = {'FullyDirectionalInscatteringColorDistance': 'fully_directional_color_distance', 'NonDirectionalInscatteringColorDistance': 'non_directional_color_distance',
            'InscatteringColorCubemapAngle': 'inscattering_cubemap_angle', 'VolumetricFogDistance': 'volumetric_distance',
            'VolumetricFogStartDistance': 'volumetric_start_distance', 'VolumetricFogExtinctionScale': 'volumetric_extinction_scale',
            'VolumetricFogScatteringDistribution': 'volumetric_scattering_distribution'}


def fog_stage(api, F):
    api.call('POST', '/fog/height/create', {'bConfirm': True, 'Name': 'MCP_fog', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    f = F.all()['MCP_fog']
    api.call('POST', '/fog/height/scalar', {**F.ids('MCP_fog'), 'FieldName': 'FogDensity', 'ExpectedValue': f['fog_density'], 'Value': -1}, ok=False)
    F.edit('/fog/height/scalar', 'MCP_fog', {'FieldName': 'FogDensity', 'ExpectedValue': f['fog_density'], 'Value': 0.05}, ['fog_density'], undo=True)
    for field, value in (('FogHeightFalloff', 0.5), ('FogMaxOpacity', 0.8), ('StartDistance', 100), ('EndDistance', 50000), ('FogCutoffDistance', 90000),
                         ('DirectionalInscatteringExponent', 8), ('DirectionalInscatteringStartDistance', 2000),
                         ('FullyDirectionalInscatteringColorDistance', 3000), ('NonDirectionalInscatteringColorDistance', 1500),
                         ('InscatteringColorCubemapAngle', 45), ('VolumetricFogDistance', 8000), ('VolumetricFogStartDistance', 10),
                         ('VolumetricFogExtinctionScale', 2), ('VolumetricFogScatteringDistribution', 0.3)):
        key = FOG_KEYS.get(field, snake(field))
        F.edit('/fog/height/scalar', 'MCP_fog', {'FieldName': field, 'ExpectedValue': F.all()['MCP_fog'][key], 'Value': value}, [key])
    F.edit('/fog/height/volumetric-enabled', 'MCP_fog', {'bExpectedValue': False, 'bValue': True}, ['enable_volumetric_fog'])
    f = F.all()['MCP_fog']
    F.edit('/fog/height/second-layer', 'MCP_fog', {
        # FVector: X density, Y height falloff, Z height offset.
        'ExpectedSecondLayer': {'X': f['second_fog_density'], 'Y': f['second_fog_height_falloff'], 'Z': f['second_fog_height_offset']},
        'SecondLayer': {'X': 0.01, 'Y': 0.1, 'Z': 500}}, ['second_fog_density', 'second_fog_height_offset'])
    for field in ('FogInscatteringLuminance', 'DirectionalInscatteringLuminance', 'InscatteringTextureTint', 'SkyAtmosphereAmbientContributionColorScale'):
        key = snake(field)
        F.edit('/fog/height/color', 'MCP_fog', {'FieldName': field, 'ExpectedColor': F.all()['MCP_fog'][key], 'Color': [0.25, 0.5, 0.75, 1]}, [key])
    F.edit('/fog/height/albedo', 'MCP_fog', {'ExpectedColor': F.all()['MCP_fog']['volumetric_albedo_rgba'], 'Color': [200, 100, 50, 255]}, ['volumetric_albedo_rgba'])
    cube = F.all()['MCP_fog']['inscattering_cubemap_path']
    api.call('POST', '/fog/height/cubemap', {**F.ids('MCP_fog'), 'ExpectedCubemapPath': cube, 'CubemapPath': '/Engine/EngineResources/DefaultTexture.DefaultTexture'}, ok=False)
    F.edit('/fog/height/cubemap', 'MCP_fog', {'ExpectedCubemapPath': cube, 'CubemapPath': CUBEMAP}, ['inscattering_cubemap_path'])
    for field in ('bHoldout', 'bRenderInMainPass', 'bOverrideLightColorsWithFogInscatteringColors'):
        key = snake(field[1:])
        cur = F.all()['MCP_fog'][key]
        F.edit('/fog/height/bool', 'MCP_fog', {'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur}, [key])
    F.edit('/fog/height/visible', 'MCP_fog', {'bExpectedValue': True, 'bValue': False}, ['visible'])
    F.edit('/fog/height/transform', 'MCP_fog', {'ExpectedTransform': transform_of(F.all()['MCP_fog']), 'Transform': MOVED}, ['world_location'], undo=True)
    api.call('POST', '/fog/height/create', {'bConfirm': True, 'Name': 'MCP_fog_doomed', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    api.call('POST', '/fog/height/delete', {**F.ids('MCP_fog_doomed'), 'bDryRun': True})
    assert 'MCP_fog_doomed' in F.all()
    api.call('POST', '/fog/height/delete', F.ids('MCP_fog_doomed'))
    assert 'MCP_fog_doomed' not in F.all()
    assert 'MCP_fog' in json.dumps(api.call('POST', '/fog/inspect-page', {'Start': 0, 'Count': 4}))


def local_fog_stage(api, LF):
    api.call('POST', '/fog/local/create', {'bConfirm': True, 'Name': 'MCP_localfog', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    for field, value in (('RadialFogExtinction', 2), ('HeightFogExtinction', 1.5), ('HeightFogFalloff', 500), ('HeightFogOffset', 50), ('FogPhaseG', 0.4)):
        key = snake(field)
        LF.edit('/fog/local/scalar', 'MCP_localfog', {'FieldName': field, 'ExpectedValue': LF.all()['MCP_localfog'][key], 'Value': value}, [key])
    LF.edit('/fog/local/color', 'MCP_localfog', {'FieldName': 'FogAlbedo', 'ExpectedColor': LF.all()['MCP_localfog']['fog_albedo'], 'Color': [0.5, 0.25, 0.125, 1]}, ['fog_albedo'])
    LF.edit('/fog/local/priority', 'MCP_localfog', {'ExpectedValue': LF.all()['MCP_localfog']['fog_sort_priority'], 'Value': 3}, ['fog_sort_priority'])
    LF.edit('/fog/local/visible', 'MCP_localfog', {'bExpectedValue': True, 'bValue': False}, ['visible'])
    LF.edit('/fog/local/transform', 'MCP_localfog', {'ExpectedTransform': transform_of(LF.all()['MCP_localfog']), 'Transform': MOVED}, ['world_location'])
    api.call('POST', '/fog/local/create', {'bConfirm': True, 'Name': 'MCP_localfog_doomed', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    api.call('POST', '/fog/local/delete', LF.ids('MCP_localfog_doomed'))
    assert 'MCP_localfog_doomed' not in LF.all()
    assert 'MCP_localfog' in json.dumps(api.call('POST', '/fog/local/inspect-page', {'Start': 0, 'Count': 4}))


def cloud_stage(api, CL):
    api.call('POST', '/clouds/create', {'bConfirm': True, 'Name': 'MCP_cloud', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    for field, value in (('LayerBottomAltitude', 3), ('LayerHeight', 8), ('TracingMaxDistance', 40), ('ViewSampleCountScale', 2), ('ShadowTracingDistance', 10)):
        CL.edit('/clouds/scalar', 'MCP_cloud', {'FieldName': field, 'ExpectedValue': CL.all()['MCP_cloud']['scalars'][field], 'Value': value}, ['scalars'])
    assert close(CL.all()['MCP_cloud']['scalars']['LayerHeight'], 8)
    for field in ('bUsePerSampleAtmosphericLightTransmittance', 'bHoldout', 'bRenderInMainPass', 'bVisibleInRealTimeSkyCaptures'):
        cur = CL.all()['MCP_cloud']['flags'][field]
        CL.edit('/clouds/bool', 'MCP_cloud', {'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur}, ['flags'])
    c = CL.all()['MCP_cloud']
    CL.edit('/clouds/ground-albedo', 'MCP_cloud', {'ExpectedColor': c['ground_albedo_rgba'], 'Color': [10, 20, 30, 255]}, ['ground_albedo_rgba'])
    CL.edit('/clouds/tracing-mode', 'MCP_cloud', {'ExpectedValue': c['tracing_max_distance_mode'], 'Value': 1 - c['tracing_max_distance_mode']}, ['tracing_max_distance_mode'])
    c = CL.all()['MCP_cloud']
    material = {'ExpectedMaterialPath': c['material_soft_path'], 'ExpectedResolvedMaterialPath': c['resolved_material_path']}
    api.call('POST', '/clouds/material', {**CL.ids('MCP_cloud'), **material, 'MaterialPath': CUBEMAP}, ok=False)
    CL.edit('/clouds/material', 'MCP_cloud', {**material, 'MaterialPath': CLOUD_MATERIAL}, ['material_soft_path'])
    CL.edit('/clouds/visible', 'MCP_cloud', {'bExpectedValue': True, 'bValue': False}, ['visible'])
    CL.edit('/clouds/transform', 'MCP_cloud', {'ExpectedTransform': transform_of(CL.all()['MCP_cloud']), 'Transform': MOVED}, ['world_location'])
    api.call('POST', '/clouds/create', {'bConfirm': True, 'Name': 'MCP_cloud_doomed', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    api.call('POST', '/clouds/delete', CL.ids('MCP_cloud_doomed'))
    assert 'MCP_cloud_doomed' not in CL.all() and 'MCP_cloud' in json.dumps(api.call('POST', '/clouds/inspect-page', {'Start': 0, 'Count': 4}))


def atmosphere_stage(api, AT):
    api.call('POST', '/atmosphere/create', {'bConfirm': True, 'Name': 'MCP_atmo', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    for field, value in (('BottomRadius', 6000), ('AtmosphereHeight', 80), ('MieAnisotropy', 0.7), ('RayleighScatteringScale', 0.05), ('MultiScatteringFactor', 0.5),
                         ('HeightFogContribution', 0.5), ('AerialPerspectiveStartDepth', 0.2), ('TransmittanceMinLightElevationAngle', -45)):
        AT.edit('/atmosphere/scalar', 'MCP_atmo', {'FieldName': field, 'ExpectedValue': AT.all()['MCP_atmo']['scalars'][field], 'Value': value}, ['scalars'])
    for field in ('RayleighScattering', 'MieScattering', 'MieAbsorption', 'OtherAbsorption', 'SkyLuminanceFactor', 'SkyAndAerialPerspectiveLuminanceFactor'):
        AT.edit('/atmosphere/color', 'MCP_atmo', {'FieldName': field, 'ExpectedColor': AT.all()['MCP_atmo'][field], 'Color': [0.2, 0.4, 0.6, 1]}, [field])
    a = AT.all()['MCP_atmo']
    AT.edit('/atmosphere/ground-albedo', 'MCP_atmo', {'ExpectedColor': a['ground_albedo_rgba'], 'Color': [60, 70, 80, 255]}, ['ground_albedo_rgba'])
    AT.edit('/atmosphere/absorption-tent', 'MCP_atmo', {
        # The tent is an FVector: X tip altitude, Y tip value, Z width.
        'ExpectedTent': {'X': a['absorption_tent_tip_altitude'], 'Y': a['absorption_tent_tip_value'], 'Z': a['absorption_tent_width']},
        'Tent': {'X': 30, 'Y': 0.5, 'Z': 20}}, ['absorption_tent_tip_altitude', 'absorption_tent_width'])
    for field in ('bHoldout', 'bRenderInMainPass'):
        cur = AT.all()['MCP_atmo']['flags'][field]
        AT.edit('/atmosphere/bool', 'MCP_atmo', {'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur}, ['flags'])
    a = AT.all()['MCP_atmo']
    AT.edit('/atmosphere/transform-mode', 'MCP_atmo', {'ExpectedValue': a['transform_mode'], 'Value': 2 if a['transform_mode'] != 2 else 1}, ['transform_mode'])
    a = AT.all()['MCP_atmo']
    AT.edit('/atmosphere/transform', 'MCP_atmo', {'ExpectedMode': a['transform_mode'], 'ExpectedTransform': transform_of(a), 'Transform': MOVED}, ['world_location'])
    AT.edit('/atmosphere/visible', 'MCP_atmo', {'bExpectedValue': True, 'bValue': False}, ['visible'])
    api.call('POST', '/atmosphere/create', {'bConfirm': True, 'Name': 'MCP_atmo_doomed', 'Location': {'X': 0, 'Y': 0, 'Z': 0}})
    api.call('POST', '/atmosphere/delete', AT.ids('MCP_atmo_doomed'))
    assert 'MCP_atmo_doomed' not in AT.all() and 'MCP_atmo' in json.dumps(api.call('POST', '/atmosphere/inspect-page', {'Start': 0, 'Count': 4}))


POLICIES = [  # (inspect route, set route, light)
    ('/lights/advanced-policy/inspect', '/lights/advanced-policy/set', 'MCP_point'),
    ('/lights/lightmass/inspect', '/lights/lightmass/set', 'MCP_point'),
    ('/lights/directional-shadows/inspect', '/lights/directional-shadows/set', 'MCP_directional'),
    ('/lights/directional-clouds/inspect', '/lights/directional-clouds/set', 'MCP_directional'),
    ('/lights/shafts/inspect', '/lights/shafts/set', 'MCP_directional'),
    ('/lights/ray-policy/inspect', '/lights/ray-policy/set', 'MCP_point'),
    ('/lights/sky/occlusion/inspect', '/lights/sky/occlusion/set', 'MCP_sky'),
    ('/lights/sky/capture-policy/inspect', '/lights/sky/capture-policy/set', 'MCP_sky'),
]


def policy_target(L, name):
    x = (L.sky() if name == 'MCP_sky' else L.all())[name]
    return {'ActorPath': x['actor_path'], 'ComponentPath': x['component_path']}


def next_value(f):
    """A different valid value for an inspected policy field: flip bools, step ints/floats inside the adapter range."""
    v, lo, hi = f['value'], f.get('adapter_min', 0), f.get('adapter_max', 1)
    if f.get('type') == 'bool' or (lo, hi) == (0, 1) and v in (0, 1) and f['name'][0] == 'b':
        return 1 - v
    if f['name'].endswith('Method') or f['name'] == 'CastRaytracedShadow':  # enums stored as an index
        return 1 if v != 1 else 2 if hi >= 2 else 0
    if f['name'].endswith(('Mode', 'PerPixel')):  # integers whose fields carry no type
        return v + 1 if v + 1 <= hi else v - 1
    if f.get('type') in ('int32', 'uint8', 'int'):
        return v + 1 if v + 1 <= hi else v - 1
    step = min(0.5, (hi - lo) / 4) if hi - lo < 1e6 else 100
    return v + step if v + step <= hi else v - step


def policy_stage(api, L):
    # Directional cloud/atmosphere shadow fields are only editable on an atmosphere sun light (the light stage cleared it).
    if not L.all()['MCP_directional']['atmosphere_sun_light']:
        L.edit('/lighting/bool', 'MCP_directional', {'FieldName': 'bAtmosphereSunLight', 'bExpectedValue': False, 'bValue': True}, ['atmosphere_sun_light'])
    # Distance-field occlusion fields need a Movable, shadow-casting sky light (and r.GenerateMeshDistanceFields).
    sky = L.sky()['MCP_sky']
    if sky['mobility'] != 2:
        api.call('POST', '/lighting/mobility', {'bConfirm': True, 'ActorPath': sky['actor_path'], 'ComponentPath': sky['component_path'],
                                                'ExpectedMobility': sky['mobility'], 'Mobility': 'Movable'})
    edited = {}
    for inspect, setter, name in POLICIES:
        t = policy_target(L, name)
        info = api.call('POST', inspect, t)
        ids = {'bConfirm': True, 'ActorPath': info['actor_path'], 'ActorGuid': info['actor_guid'], 'ComponentPath': info['component_path'], 'ExpectedLabel': info['label']}
        extra = {'ExpectedSettingsText': info['native_snapshot_text']} if 'native_snapshot_text' in info else {}
        fields = [f for f in info['fields'] if f.get('native_can_edit') and f.get('available', True) and isinstance(f.get('value'), (int, float))]
        assert fields, (inspect, info['fields'])
        first = fields[0]
        api.call('POST', setter, {**ids, **extra, 'ExpectedLabel': 'NotTheLabel', 'FieldName': first['name'], 'ExpectedValue': first['value'], 'Value': next_value(first)}, ok=False)
        api.call('POST', setter, {**ids, **extra, 'FieldName': first['name'], 'ExpectedValue': first['value'] + 1234, 'Value': next_value(first)}, ok=False)
        done = []
        for f in fields:
            cur = {x['name']: x for x in api.call('POST', inspect, t)['fields']}[f['name']]
            if not cur.get('native_can_edit'):
                continue  # an earlier edit in this group changed its edit condition
            info = api.call('POST', inspect, t)
            extra = {'ExpectedSettingsText': info['native_snapshot_text']} if 'native_snapshot_text' in info else {}
            value = next_value(cur)
            body = {**ids, **extra, 'FieldName': f['name'], 'ExpectedValue': cur['value'], 'Value': value}
            assert api.call('POST', setter, {**body, 'bDryRun': True})['dry_run'] is True
            api.call('POST', setter, body)
            after = {x['name']: x for x in api.call('POST', inspect, t)['fields']}[f['name']]
            assert close(after['value'], value), (setter, f['name'], cur['value'], value, after['value'])
            done.append(f['name'])
        edited[setter] = done
    # Explicit-shape setters.
    D = api.call('POST', '/lights/directional-clouds/inspect', policy_target(L, 'MCP_directional'))
    Dids = {'bConfirm': True, 'ActorPath': D['actor_path'], 'ActorGuid': D['actor_guid'], 'ComponentPath': D['component_path'], 'ExpectedLabel': D['label']}
    api.call('POST', '/lights/directional-clouds/color', {**Dids, 'FieldName': 'AtmosphereSunDiskColorScale', 'ExpectedLinearColor': D['atmosphere_sun_disk_color_scale'], 'LinearColor': [2, 1, 0.5, 1]})
    assert close(api.call('POST', '/lights/directional-clouds/inspect', policy_target(L, 'MCP_directional'))['atmosphere_sun_disk_color_scale'], [2, 1, 0.5, 1])
    S = api.call('POST', '/lights/shafts/inspect', policy_target(L, 'MCP_directional'))
    api.call('POST', '/lights/shafts/appearance', {**Dids, 'FieldName': 'BloomTint', 'ExpectedColor': S['bloom_tint_bytes'], 'Color': [255, 200, 100, 255]})
    api.call('POST', '/lights/shafts/appearance', {**Dids, 'FieldName': 'LightShaftOverrideDirection', 'ExpectedDirection': dict(zip('XYZ', S['override_direction'])),
                                                   'Direction': {'X': 0, 'Y': 0, 'Z': -1}})
    S = api.call('POST', '/lights/shafts/inspect', policy_target(L, 'MCP_directional'))
    assert S['bloom_tint_bytes'] == [255, 200, 100, 255] and close(S['override_direction'], [0, 0, -1]), S
    P = api.call('POST', '/lights/view-channels/inspect', policy_target(L, 'MCP_point'))
    Pids = {'bConfirm': True, 'ActorPath': P['actor_path'], 'ActorGuid': P['actor_guid'], 'ComponentPath': P['component_path'], 'ExpectedLabel': P['label']}
    api.call('POST', '/lights/view-channels/set', {**Pids, 'ExpectedChannels': P['view_channels'], 'Channels': [1, 0, 1, 0, 1]})
    assert api.call('POST', '/lights/view-channels/inspect', policy_target(L, 'MCP_point'))['view_channel_mask'] == 0b10101
    X = api.call('POST', '/lights/local-exposure/inspect', policy_target(L, 'MCP_point'))
    api.call('POST', '/lights/local-exposure/set', {**Pids, 'ExpectedValue': X['inverse_exposure_blend'], 'Value': 1.5}, ok=False)
    api.call('POST', '/lights/local-exposure/set', {**Pids, 'ExpectedValue': X['inverse_exposure_blend'], 'Value': 0.75})
    assert close(api.call('POST', '/lights/local-exposure/inspect', policy_target(L, 'MCP_point'))['inverse_exposure_blend'], 0.75)
    W = api.call('POST', '/lights/world-influence/inspect', policy_target(L, 'MCP_spot'))
    Wids = {'bConfirm': True, 'ActorPath': W['actor_path'], 'ActorGuid': W['actor_guid'], 'ComponentPath': W['component_path'], 'ExpectedLabel': W['label']}
    api.call('POST', '/lights/world-influence/set', {**Wids, 'bExpectedValue': W['affects_world'], 'bValue': not W['affects_world']})
    assert api.call('POST', '/lights/world-influence/inspect', policy_target(L, 'MCP_spot'))['affects_world'] is (not W['affects_world'])
    K = api.call('POST', '/lights/sky/occlusion/inspect', policy_target(L, 'MCP_sky'))
    Kids = {'bConfirm': True, 'ActorPath': K['actor_path'], 'ActorGuid': K['actor_guid'], 'ComponentPath': K['component_path'], 'ExpectedLabel': K['label']}
    # OcclusionTint (like Contrast) is only editable when the project generates mesh distance fields.
    tint = {**Kids, 'ExpectedColor': K['occlusion_tint_bytes'], 'Color': [10, 20, 30, 255]}
    if {f['name']: f for f in K['fields']}['Contrast']['native_can_edit']:
        api.call('POST', '/lights/sky/occlusion/tint', tint)
        assert api.call('POST', '/lights/sky/occlusion/inspect', policy_target(L, 'MCP_sky'))['occlusion_tint_bytes'] == [10, 20, 30, 255]
        print('distance-field occlusion fields editable: OcclusionTint edited')
    else:
        api.call('POST', '/lights/sky/occlusion/tint', tint, ok=False)
    Q = api.call('POST', '/lights/sky/capture-policy/inspect', policy_target(L, 'MCP_sky'))
    api.call('POST', '/lights/sky/color', {**Kids, 'ExpectedColor': [1, 2, 3, 4], 'Color': [200, 150, 100, 255]}, ok=False)
    api.call('POST', '/lights/sky/color', {**Kids, 'ExpectedColor': Q['light_color_bytes'], 'Color': [200, 150, 100, 255]})
    assert api.call('POST', '/lights/sky/capture-policy/inspect', policy_target(L, 'MCP_sky'))['light_color_bytes'] == [200, 150, 100, 255]
    pages = api.call('POST', '/lights/inspect-page', {'Start': 0, 'Count': 2}), api.call('POST', '/lights/sky/inspect-page', {'Start': 0, 'Count': 2})
    assert all('MCP_' in json.dumps(p) for p in pages), pages
    assert all(edited.values()), edited
    assert 'Contrast' in edited['/lights/sky/occlusion/set'], edited['/lights/sky/occlusion/set']   # distance-field fields reached
    return edited


def families(api):
    return {'fog': Family(api, '/fog/height/inspect', 'fog_components'), 'local_fog': Family(api, '/fog/local/inspect', 'local_fog_components'),
            'clouds': Family(api, '/clouds/inspect', 'cloud_components'), 'atmosphere': Family(api, '/atmosphere/inspect', 'atmosphere_components')}


def snapshot(api, L):
    # Registration and the processed sky capture are runtime state, not authored data.
    strip = lambda d: {k: v for k, v in d.items() if k not in ('registered', 'has_processed_sky_texture')}
    out = {'lights': {k: strip(v) for k, v in L.all().items()}, 'sky': {k: strip(v) for k, v in L.sky().items()}}
    for name, fam in families(api).items():
        out[name] = {k: strip(v) for k, v in fam.all().items()}
    routes = [(i, n) for i, _, n in POLICIES] + [('/lights/view-channels/inspect', 'MCP_point'), ('/lights/local-exposure/inspect', 'MCP_point'),
                                                 ('/lights/world-influence/inspect', 'MCP_spot')]
    volatile = ('scope', 'package_dirty', 'render_state_created', 'registered')
    out['policies'] = {f'{r}|{n}': {k: v for k, v in api.call('POST', r, policy_target(L, n)).items() if k not in volatile} for r, n in routes}
    return out


STAGES = [
    lambda api, L: light_stage(api, L),
    lambda api, L: sky_stage(api, L),
    lambda api, L: policy_stage(api, L),
    lambda api, L: fog_stage(api, families(api)['fog']),
    lambda api, L: local_fog_stage(api, families(api)['local_fog']),
    lambda api, L: cloud_stage(api, families(api)['clouds']),
    lambda api, L: atmosphere_stage(api, families(api)['atmosphere']),
]


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    original = api.call('GET', '/worlds/inspect')['world_path']
    if original.startswith(MAP):
        # A previous run stopped with the scratch map open; return to the map recorded then.
        original = json.loads(STATE.read_text(encoding='utf-8')).get('original', FALLBACK) if STATE.exists() else FALLBACK
        original = FALLBACK if original.startswith(MAP) else original
        assert api.call('POST', '/worlds/load', {'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    STATE.write_text(json.dumps({'original': original}), encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    # Deleting the open map used to crash the editor; it must now be refused (this targets only the scratch map).
    api.call('POST', '/assets/delete', {'AssetPath': MAP}, ok=False)
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    L = Lights(api)
    for stage in STAGES:
        stage(api, L)
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'snapshot': snapshot(api, L)}), encoding='utf-8')
    print('prepared lighting/atmosphere authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = snapshot(api, Lights(api))
        for group in state['snapshot']:
            a, b = state['snapshot'][group], cold[group]
            assert a.keys() == b.keys(), (group, sorted(a), sorted(b))
            for name in a:
                d = diff(a[name], b[name])
                assert not d, (group, name, {k: (a[name].get(k), b[name].get(k)) for k in d})
        print('Cold reload of lights, sky light, fog, clouds and sky atmosphere: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('original'):
        httpx.post(api.base + '/worlds/load', json={'WorldPath': state['original'], 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned lighting test map')


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
