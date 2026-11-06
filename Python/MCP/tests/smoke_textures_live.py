"""Live texture-asset authoring on scratch textures created without source files.

prepare: create Texture2D/cube/array/cube-array/volume textures, edit every editable Texture2D setting through its
route with snapshot/source-id/value guards, dry runs and undo/redo, edit source mips (fill, patch, copy), export,
and author array/cube-array/volume sources and address modes; save and snapshot.
verify (fresh editor): load the textures, compare settings, source identity and source pixel statistics, then delete.

Texture routes only act on loaded textures; the test loads them through /assets/describe, including after restart.
"""
import argparse
import json
import math
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'textures.json'
EXPORTS = PROJECT / 'Saved' / 'UE5_MCP' / 'Exports'
D = '/Game/UE5MCP_Test/'
# Deleted packages stay in memory until garbage collection and block re-creation at the same path in one editor
# session, so every run uses its own name tag (kept in the state file for verify/cleanup).
T2D = T2D_COPY = T2D_B = T2D_C = CUBE = CUBE_B = ARRAY = ARRAY_SRC = CUBE_ARRAY = VOLUME = VOLUME_SRC = None
ASSETS = ()


def use_tag(tag):
    global T2D, T2D_COPY, T2D_B, T2D_C, CUBE, CUBE_B, ARRAY, ARRAY_SRC, CUBE_ARRAY, VOLUME, VOLUME_SRC, ASSETS
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    T2D, T2D_COPY, T2D_B, T2D_C = n('T_MCP_Tex'), n('T_MCP_TexCopy'), n('T_MCP_TexB'), n('T_MCP_TexC')
    CUBE, CUBE_B, ARRAY, ARRAY_SRC = n('TC_MCP_Cube'), n('TC_MCP_CubeB'), n('TA_MCP_Array'), n('TA_MCP_ArraySrc')
    CUBE_ARRAY, VOLUME, VOLUME_SRC = n('TCA_MCP_CubeArray'), n('TV_MCP_Volume'), n('TV_MCP_VolumeSrc')
    ASSETS = (T2D, T2D_COPY, T2D_B, T2D_C, CUBE, CUBE_B, ARRAY, ARRAY_SRC, CUBE_ARRAY, VOLUME, VOLUME_SRC)


LIVE = {'bConfirm': True, 'bDryRun': False}

ROUTES = {
    'PowerOfTwoMode': '/textures/2d/padding-policy',  # first: border-colour padding needs a padding mode
    # Legacy gamma needs sRGB on; normal-map compression (below) turns sRGB off, so it goes first.
    'bUseLegacyGamma': '/textures/sampling/setting',
    'AddressX': '/textures/2d/address', 'AddressY': '/textures/2d/address', 'Filter': '/textures/2d/filter',
    'MipGenSettings': '/textures/2d/mip-policy', 'LODBias': '/textures/2d/lod-limit', 'MaxTextureSize': '/textures/2d/lod-limit',
    'NumCinematicMipLevels': '/textures/2d/lod-limit', 'bFlipGreenChannel': '/textures/2d/processing-flag',
    'bPadWithBorderColor': '/textures/2d/processing-flag', 'bPreserveBorder': '/textures/2d/processing-flag',
    'MipLoadOptions': '/textures/2d/mip-load-policy',
    # Compression before sampling: normal normalization needs a normal-map compression mode (set explicitly below).
    'CompressionSettings': '/textures/compression/setting', 'CompressionQuality': '/textures/compression/setting',
    'LossyCompressionAmount': '/textures/compression/setting', 'CompressionNone': '/textures/compression/setting',
    'CompressionNoAlpha': '/textures/compression/setting', 'CompressionForceAlpha': '/textures/compression/setting',
    'SRGB': '/textures/sampling/setting', 'LODGroup': '/textures/sampling/setting', 'NeverStream': '/textures/sampling/setting',
    'bUseNewMipFilter': '/textures/sampling/setting', 'bNormalizeNormals': '/textures/sampling/setting',
    'DownscaleOptions': '/textures/sampling/setting',
    'VirtualTextureStreamingPriority': '/textures/virtual-policy/set', 'bUseVirtualTextureStreamingPriority': '/textures/virtual-policy/set',
    'VirtualTexturePrefetchMips': '/textures/virtual-policy/set',
}
ADJUST = {'AdjustBrightness': 1.5, 'AdjustBrightnessCurve': 1.2, 'AdjustHue': 30, 'AdjustMaxAlpha': 0.9, 'AdjustMinAlpha': 0.1,
          'AdjustRGBCurve': 1.1, 'AdjustSaturation': 0.8, 'AdjustVibrance': 0.3}
NUMBERS = {'CompressionSettings': 1,  # TC_Normalmap
           'LODBias': 1, 'MaxTextureSize': 32, 'NumCinematicMipLevels': 1, 'VirtualTexturePrefetchMips': 2}


def load(api, path):
    api.call('GET', '/assets/describe', params={'asset_path': path})


def guards(api, path):
    s = api.call('POST', '/textures/source-identity/inspect', {'AssetPath': path})
    return {'AssetPath': path, 'ExpectedClassPath': s['class_path'], 'ExpectedSourceId': s['source_attribute_id'], 'ExpectedAssetSnapshot': s['native_authored_snapshot']}


def settings(api, path=None):
    return {s['name']: s for s in api.call('POST', '/textures/2d/settings/inspect', {'AssetPath': path or T2D})['settings']}


def numeric(s):
    t = s['native_text']
    for e in s.get('enum_values', []):
        if e['name'] == t or e['name'].split('::')[-1] == t:
            return e['value']
    if t in ('True', 'False'):
        return 1 if t == 'True' else 0
    return float(t)


def target(s):
    if s['name'] in ADJUST:
        return ADJUST[s['name']]
    if s['name'] in NUMBERS:
        return NUMBERS[s['name']]
    if s.get('enum_values'):
        cur = numeric(s)
        choices = [e['value'] for e in s['enum_values'] if not e['hidden'] and not e['name'].endswith('MAX') and e['value'] != cur]
        return choices[0]
    return 1 - numeric(s)


def texture2d_stage(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D, 'bConfirm': True, 'SizeX': 64, 'SizeY': 32})  # dry run by default
    api.call('GET', '/assets/describe', params={'asset_path': T2D}, ok=False)
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D, **LIVE, 'SizeX': 48, 'SizeY': 32}, ok=False)  # not a power of two
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D, 'bDryRun': False, 'SizeX': 64, 'SizeY': 32}, ok=False)  # unconfirmed
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D, **LIVE, 'SizeX': 64, 'SizeY': 32})
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D, **LIVE, 'SizeX': 64, 'SizeY': 32}, ok=False)  # collision
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D_B, **LIVE, 'SizeX': 64, 'SizeY': 32})
    load(api, T2D); load(api, T2D_B)
    mips = api.call('POST', '/textures/source-mips/inspect', {'AssetPath': T2D, 'Count': 16})
    assert mips['mip_count'] == 7 and mips['mips'][0]['width'] == 64 and mips['mips'][0]['height'] == 32, mips
    # Every natively editable setting, through its own route. Sampling/compression fields are read from their own
    # inspections (numeric values with choices); the rest from the Texture2D settings inspection.
    def read(name, route):
        if route in ('/textures/sampling/setting', '/textures/compression/setting'):
            inspect = route.replace('/setting', '/inspect')
            e = next((x for x in api.call('POST', inspect, {'AssetPath': T2D})['settings'] if x['field_name'] == name), None)
            if e is None:
                return None
            v = e['value']
            choices = [c['value'] for c in e.get('choices', []) if not c['name'].endswith('MAX') and c['value'] != v]
            new = NUMBERS[name] if name in NUMBERS else choices[0] if choices else (1 - v if e.get('kind') in ('bool', 'boolean') else v + 1)
            return e.get('native_editable') and e.get('available', True), v, new, v
        if route == '/textures/virtual-policy/set':
            e = {x['name']: x for x in api.call('POST', '/textures/virtual-policy/inspect', {'AssetPath': T2D})['settings']}.get(name)
        else:
            e = settings(api).get(name)
        if e is None:
            return None
        return e['native_can_edit'], numeric(e), target(e), e['native_text']
    edited = []
    # VT policy fields need VirtualTextureStreaming, which only the generic texture-settings route switches on.
    r = httpx.patch(api.base + '/textures/settings', json={'AssetPath': T2D, 'Operation': 'set_properties', 'Properties': {'VirtualTextureStreaming': 'True'}}, timeout=300)
    assert r.is_success and 'errorMessage' not in r.text, r.text[:300]
    for name, route in ROUTES.items():
        r = read(name, route)
        if r is None or not r[0]:
            continue
        _, cur, value, shown = r
        if name == 'VirtualTextureStreamingPriority' and read('bUseVirtualTextureStreamingPriority', route)[1] == 0:
            # The priority value needs the override flag on first.
            api.call('POST', route, {**guards(api, T2D), **LIVE, 'FieldName': name, 'ExpectedValue': cur, 'Value': value}, ok=False)
            api.call('POST', route, {**guards(api, T2D), **LIVE, 'FieldName': 'bUseVirtualTextureStreamingPriority', 'ExpectedValue': 0, 'Value': 1})
            edited.append('bUseVirtualTextureStreamingPriority')
        if name == 'CompressionForceAlpha' and value == 1 and read('CompressionNoAlpha', route)[1] == 1:
            # The two alpha policies are exclusive: refused while NoAlpha is on, allowed once it is cleared.
            api.call('POST', route, {**guards(api, T2D), **LIVE, 'FieldName': name, 'ExpectedValue': cur, 'Value': 1}, ok=False)
            api.call('POST', route, {**guards(api, T2D), **LIVE, 'FieldName': 'CompressionNoAlpha', 'ExpectedValue': 1, 'Value': 0})
        body = {**guards(api, T2D), **LIVE, 'FieldName': name, 'ExpectedValue': cur, 'Value': value}
        if name == 'SRGB' and value == 1 and read('CompressionSettings', '/textures/compression/setting')[1] == 1:
            api.call('POST', route, body, ok=False)  # the engine clears sRGB on normal maps, so it is refused up front
            continue
        api.call('POST', route, {**body, 'ExpectedValue': cur + 77}, ok=False)
        api.call('POST', route, {**body, 'bDryRun': True})
        assert read(name, route)[3] == shown, (name, 'dry run changed it')
        r = httpx.post(api.base + route, json=body, timeout=300)
        assert r.is_success, (name, cur, value, r.text[:300])
        after = read(name, route)
        assert math.isclose(after[1], value, abs_tol=1e-4), (name, cur, value, after)
        edited.append(name)
    for name, value in ADJUST.items():
        cur = settings(api)[name]
        route = '/textures/2d/adjustment' if len(edited) % 2 else '/textures/color-adjustment'
        api.call('POST', route, {**guards(api, T2D), **LIVE, 'FieldName': name, 'ExpectedValue': numeric(cur), 'Value': value})
        assert math.isclose(numeric(settings(api)[name]), value, abs_tol=1e-4), name
        edited.append(name)
    api.call('POST', '/textures/2d/adjustment', {**guards(api, T2D), **LIVE, 'FieldName': 'AdjustHue', 'ExpectedValue': 30, 'Value': 400}, ok=False)
    assert len(edited) >= 30, edited
    # Undo/redo of one setting edit.
    cur = settings(api)['AddressX']
    api.call('POST', '/textures/2d/address', {**guards(api, T2D), **LIVE, 'FieldName': 'AddressX', 'ExpectedValue': numeric(cur), 'Value': 2 if numeric(cur) != 2 else 1})
    changed = settings(api)['AddressX']['native_text']
    api.undo(); assert settings(api)['AddressX']['native_text'] == cur['native_text']
    api.redo(); assert settings(api)['AddressX']['native_text'] == changed
    # Build resize, padding colour (both routes), alpha coverage, downscale override.
    # Padding colour needs a pad-to-power-of-two mode with border-colour padding off.
    def set_mode(path, suffix):
        mode = settings(api, path)['PowerOfTwoMode']
        want = next(e['value'] for e in mode['enum_values'] if e['name'].endswith(suffix))
        if numeric(mode) != want:
            api.call('POST', '/textures/2d/padding-policy', {**guards(api, path), **LIVE, 'FieldName': 'PowerOfTwoMode', 'ExpectedValue': numeric(mode), 'Value': want})
    for path in (T2D, T2D_B):
        if settings(api, path)['bPadWithBorderColor']['native_text'] == 'True':
            api.call('POST', '/textures/2d/processing-flag', {**guards(api, path), **LIVE, 'FieldName': 'bPadWithBorderColor', 'ExpectedValue': 1, 'Value': 0})
        set_mode(path, '::PadToPowerOfTwo' if '::' in settings(api, path)['PowerOfTwoMode']['enum_values'][1]['name'] else 'PadToPowerOfTwo')
    api.call('POST', '/textures/2d/padding-color', {**guards(api, T2D), **LIVE, 'ExpectedColor': [0, 0, 0, 255], 'Color': [10, 20, 30, 255]})
    api.call('POST', '/textures/padding-color', {**guards(api, T2D_B), **LIVE, 'ExpectedColor': [0, 0, 0, 255], 'Color': [40, 50, 60, 255]})
    assert settings(api)['PaddingColor']['native_text'] == '(B=30,G=20,R=10,A=255)', settings(api)['PaddingColor']
    # Explicit build dimensions need the ResizeToSpecificResolution padding mode.
    for path in (T2D, T2D_B):
        set_mode(path, 'ResizeToSpecificResolution')
    api.call('POST', '/textures/2d/build-resize', {**guards(api, T2D), **LIVE, 'ExpectedSizeX': 0, 'ExpectedSizeY': 0, 'SizeX': 5000, 'SizeY': 16}, ok=False)
    api.call('POST', '/textures/2d/build-resize', {**guards(api, T2D), **LIVE, 'ExpectedSizeX': 0, 'ExpectedSizeY': 0, 'SizeX': 32, 'SizeY': 16})
    api.call('POST', '/textures/build-resize', {**guards(api, T2D_B), **LIVE, 'ExpectedSizeX': 0, 'ExpectedSizeY': 0, 'SizeX': 16, 'SizeY': 16})
    s = settings(api)
    assert s['ResizeDuringBuildX']['native_text'] == '32' and s['ResizeDuringBuildY']['native_text'] == '16', (s['ResizeDuringBuildX'], s['ResizeDuringBuildY'])
    ac = api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': T2D})
    api.call('POST', '/textures/alpha-coverage', {**guards(api, T2D), **LIVE, 'bExpectedEnabled': ac['enabled'], 'ExpectedColor': ac['thresholds_rgba'],
                                                 'bEnabled': True, 'Color': [0.5, 0, 0, 0.25]})
    ac2 = api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': T2D})
    assert ac2['enabled'] and math.isclose(ac2['thresholds_rgba'][0], 0.5) and math.isclose(ac2['thresholds_rgba'][3], 0.25), ac2
    m = api.call('POST', '/textures/alpha-coverage/measure-source', {**guards(api, T2D), 'bConfirm': True, 'MipIndex': 0})
    assert 'coverage' in json.dumps(m).lower(), m
    # Downscale applies only to a Texture2D without generated mips: refused on T2D, authored on T2D_B after NoMipmaps.
    down = lambda p: api.call('POST', '/textures/downscale/inspect-page', {'AssetPath': p, 'Count': 8})
    assert not down(T2D)['native_downscale_editable']
    api.call('POST', '/textures/downscale/override', {**guards(api, T2D), **LIVE, 'FieldName': 'Default', 'ExpectedValue': down(T2D)['default_value'], 'Value': 2}, ok=False)
    mip = settings(api, T2D_B)['MipGenSettings']
    none = next(e['value'] for e in mip['enum_values'] if e['name'].endswith('NoMipmaps'))
    api.call('POST', '/textures/2d/mip-policy', {**guards(api, T2D_B), **LIVE, 'FieldName': 'MipGenSettings', 'ExpectedValue': numeric(mip), 'Value': none})
    assert down(T2D_B)['native_downscale_editable'], down(T2D_B)
    api.call('POST', '/textures/downscale/override', {**guards(api, T2D_B), **LIVE, 'FieldName': 'Default', 'Name': 'Windows', 'ExpectedValue': 0, 'Value': 2}, ok=False)
    api.call('POST', '/textures/downscale/override', {**guards(api, T2D_B), **LIVE, 'FieldName': 'Default', 'ExpectedValue': down(T2D_B)['default_value'], 'Value': 2})
    api.call('POST', '/textures/downscale/override', {**guards(api, T2D_B), **LIVE, 'FieldName': 'Override', 'Name': 'Windows', 'bExpectedEnabled': False, 'ExpectedValue': 0, 'Value': 3})
    api.call('POST', '/textures/downscale/override', {**guards(api, T2D_B), **LIVE, 'FieldName': 'Override', 'Name': 'Mac', 'bExpectedEnabled': False, 'ExpectedValue': 0, 'Value': 4})
    api.call('POST', '/textures/downscale/override', {**guards(api, T2D_B), **LIVE, 'FieldName': 'RemoveOverride', 'Name': 'Mac', 'bExpectedEnabled': True, 'ExpectedValue': 4, 'Value': 0})
    d = down(T2D_B)
    assert math.isclose(d['default_value'], 2) and d['override_count'] == 1 and 'Windows' in json.dumps(d['overrides']), d
    vp = api.call('POST', '/textures/virtual-policy/inspect', {'AssetPath': T2D})
    assert 'VirtualTexturePrefetchMips' in json.dumps(vp), vp
    return edited


def source_stage(api):
    G = lambda p=T2D: guards(api, p)
    stats = lambda p=T2D: {c['channel']: (c['min_byte'], c['max_byte']) for c in api.call('POST', '/textures/source-mips/statistics', {**G(p), 'bConfirm': True})['channels']}
    api.call('POST', '/textures/source-mips/fill', {**G(), **LIVE, 'Color': [300, 0, 0, 255], 'Start': 0}, ok=False)
    api.call('POST', '/textures/source-mips/fill', {**G(), **LIVE, 'Color': [10, 20, 30, 255], 'Start': 0})
    assert stats() == {'R': (10, 10), 'G': (20, 20), 'B': (30, 30), 'A': (255, 255)}, stats()
    api.undo(); assert stats()['R'] == (255, 255), stats()
    api.redo(); assert stats()['R'] == (10, 10)
    px = api.call('POST', '/textures/source-mips/pixels/inspect-page', {**G(), 'bConfirm': True, 'Count': 2})
    assert px['pixels'][0]['rgba'] == [10, 20, 30, 255], px['pixels'][0]
    api.call('POST', '/textures/source-mips/pixels/patch', {**G(), **LIVE, 'MipIndex': 0, 'Start': 0, 'ExpectedPixelBytes': [1, 1, 1, 1], 'PixelBytes': [1, 2, 3, 4]}, ok=False)
    api.call('POST', '/textures/source-mips/pixels/patch', {**G(), **LIVE, 'MipIndex': 0, 'Start': 0, 'ExpectedPixelBytes': [10, 20, 30, 255], 'PixelBytes': [1, 2, 3, 4]})
    px = api.call('POST', '/textures/source-mips/pixels/inspect-page', {**G(), 'bConfirm': True, 'Count': 2})
    assert px['pixels'][0]['rgba'] == [1, 2, 3, 4] and px['pixels'][1]['rgba'] == [10, 20, 30, 255], px['pixels']
    lin = api.call('POST', '/textures/source-mips/linear-statistics', {**G(), 'bConfirm': True})
    assert lin['pixel_count'] == 2048, lin
    assert len(api.call('POST', '/textures/source-mips/linear-pixels/inspect-page', {**G(), 'bConfirm': True, 'Count': 2})['pixels']) == 2
    v = api.call('POST', '/textures/source-mips/validate-payloads', {**G(), 'bConfirm': True})
    assert v['mip_count'] == 7 and all(mm.get('native_decode_succeeded', True) for mm in v['mips']), v
    # Duplicate, compare and copy one mip between textures.
    api.call('POST', '/textures/duplicate', {'AssetPath': T2D_COPY, **LIVE, 'SourceTexturePath': T2D, 'ExpectedClassPath': '/Script/Engine.Texture2D',
                                             'ExpectedSourceId': G()['ExpectedSourceId']})
    load(api, T2D_COPY)
    assert stats(T2D_COPY)['R'] == (1, 10), stats(T2D_COPY)
    other = G(T2D_B)['ExpectedSourceId']
    cmp = api.call('POST', '/textures/source-mips/compare', {**G(), 'bConfirm': True, 'SourceTexturePath': T2D_B, 'ExpectedOtherSourceId': other, 'MipIndex': 0})
    assert cmp['different_pixel_count'] == 2048 and not cmp['source_bytes_equal'], cmp  # white vs the filled/patched mip
    api.call('POST', '/textures/source-mips/copy', {**G(T2D_B), **LIVE, 'SourceTexturePath': T2D, 'ExpectedOtherSourceId': G()['ExpectedSourceId'], 'MipIndex': 0, 'Start': 0})
    assert stats(T2D_B)['R'] == (1, 10), stats(T2D_B)
    cmp = api.call('POST', '/textures/source-mips/compare', {**G(), 'bConfirm': True, 'SourceTexturePath': T2D_B, 'ExpectedOtherSourceId': G(T2D_B)['ExpectedSourceId'], 'MipIndex': 0})
    assert cmp['different_pixel_count'] == 0 and cmp['source_bytes_equal'], cmp
    # Exports (image and DDS) land in Saved/UE5_MCP/Exports.
    r = api.call('POST', '/textures/source/export-image', {**G(), **LIVE, 'Name': 'mcp_textures_test', 'FieldName': 'png'})
    assert r['exported'] and Path(r['output_path']).is_file(), r
    r = api.call('POST', '/textures/source/export-dds', {**G(), **LIVE, 'Name': 'mcp_textures_test'})
    assert r.get('exported', True) and Path(r['output_path']).is_file(), r
    for f in EXPORTS.glob('mcp_textures_test*'):
        f.unlink()
    # Read-only reports.
    for field in ('blocks', 'layers'):
        layout = api.call('POST', '/textures/source-layout/inspect-page', {'AssetPath': T2D, 'FieldName': field, 'Count': 8})
        assert '1' in json.dumps(layout), layout
    for route in ('/textures/streaming-state/inspect', '/textures/sampling/inspect', '/textures/compression/inspect'):
        api.call('POST', route, {'AssetPath': T2D})
    for route in ('/textures/material-overrides/inspect-page', '/textures/expression-references/inspect-page', '/textures/brush-assets/inspect-page'):
        api.call('POST', route, {'AssetPath': T2D, 'PathFilter': '/Game', 'Count': 8})


def dimensional_stage(api):
    G = lambda p: guards(api, p)
    api.call('POST', '/texture-cubes/create', {'AssetPath': CUBE, **LIVE, 'SizeX': 30}, ok=False)
    api.call('POST', '/texture-cubes/create', {'AssetPath': CUBE, **LIVE, 'SizeX': 32})
    api.call('POST', '/texture-cubes/create', {'AssetPath': CUBE_B, **LIVE, 'SizeX': 32})
    load(api, CUBE); load(api, CUBE_B)
    assert api.call('POST', '/texture-cubes/inspect', {'AssetPath': CUBE})['class_path'].endswith('TextureCube')
    # Arrays: solid creation, creation from Texture2D sources, source replacement/reordering, address mode.
    api.call('POST', '/texture-arrays/create-solid', {'AssetPath': ARRAY_SRC, **LIVE, 'SizeX': 32, 'SizeY': 32, 'SizeZ': 3})
    api.call('POST', '/texture-arrays/create', {'AssetPath': ARRAY, **LIVE, 'SourcePaths': [T2D_B]})
    load(api, ARRAY); load(api, ARRAY_SRC)
    src = lambda p: api.call('POST', '/texture-arrays/inspect', {'AssetPath': p})
    assert src(ARRAY_SRC)['class_path'].endswith('Texture2DArray'), src(ARRAY_SRC)
    cur = [x['path'] for x in src(ARRAY)['source_textures']]
    # The copy of T2D carries its edited gamma/compression, so it is refused; a plain 64x32 texture matches.
    api.call('POST', '/texture-arrays/sources/replace', {**G(ARRAY), **LIVE, 'ExpectedSourcePaths': cur, 'SourcePaths': [T2D_B, T2D_COPY]}, ok=False)
    api.call('POST', '/textures/create-2d', {'AssetPath': T2D_C, **LIVE, 'SizeX': 64, 'SizeY': 32})
    load(api, T2D_C)
    api.call('POST', '/texture-arrays/sources/replace', {**G(ARRAY), **LIVE, 'ExpectedSourcePaths': cur, 'SourcePaths': [T2D_B, T2D_C]})
    cur = [x['path'] for x in src(ARRAY)['source_textures']]
    assert cur == [T2D_B, T2D_C], cur
    api.call('POST', '/texture-arrays/sources/reorder', {**G(ARRAY), **LIVE, 'ExpectedSourcePaths': cur, 'SourceOrder': [1, 0]})
    cur = [x['path'] for x in src(ARRAY)['source_textures']]
    assert cur == [T2D_C, T2D_B], cur
    api.call('POST', '/texture-arrays/source-compatibility/inspect', {'AssetPath': ARRAY})
    api.call('POST', '/texture-arrays/address', {**G(ARRAY), **LIVE, 'FieldName': 'AddressX', 'ExpectedValue': src(ARRAY)['address_x'], 'Value': 1})
    api.call('POST', '/texture-arrays/address', {**G(ARRAY), **LIVE, 'FieldName': 'AddressZ', 'ExpectedValue': src(ARRAY)['address_z'], 'Value': 2})
    assert (src(ARRAY)['address_x'], src(ARRAY)['address_z']) == (1, 2), src(ARRAY)
    # Cube arrays.
    api.call('POST', '/texture-cube-arrays/create-solid', {'AssetPath': CUBE_ARRAY, **LIVE, 'SizeX': 16, 'SizeY': 16, 'SizeZ': 2})
    load(api, CUBE_ARRAY)
    ca = api.call('POST', '/texture-cube-arrays/inspect', {'AssetPath': CUBE_ARRAY})
    assert ca['class_path'].endswith('TextureCubeArray'), ca
    # Volume textures: solid creation, address mode.
    api.call('POST', '/volume-textures/create-solid', {'AssetPath': VOLUME_SRC, **LIVE, 'SizeX': 8, 'SizeY': 8, 'SizeZ': 4})
    load(api, VOLUME_SRC)
    vol = api.call('POST', '/volume-textures/inspect', {'AssetPath': VOLUME_SRC})
    assert vol['class_path'].endswith('VolumeTexture'), vol
    am = vol.get('address_mode', 0)
    api.call('POST', '/volume-textures/address', {**G(VOLUME_SRC), **LIVE, 'ExpectedValue': am if isinstance(am, (int, float)) else 0, 'Value': 1})
    # Volume texture from a Texture2D tile sheet: 64x32 source as two 32x32 tiles, then retile to 16x16 (eight slices).
    tile = {'SourceTexturePath': T2D_C, 'ExpectedFormat': 2, 'ExpectedSourceSizeX': 64, 'ExpectedSourceSizeY': 32}
    api.call('POST', '/volume-textures/create', {'AssetPath': VOLUME, **LIVE, **tile, 'SizeX': 24, 'SizeY': 32}, ok=False)
    api.call('POST', '/volume-textures/create', {'AssetPath': VOLUME, **LIVE, **tile, 'SizeX': 32, 'SizeY': 32})
    load(api, VOLUME)
    vol = api.call('POST', '/volume-textures/inspect', {'AssetPath': VOLUME})
    assert vol['source_2d_path'] == T2D_C and (vol['source_width'], vol['source_height'], vol['source_depth']) == (32, 32, 2), vol
    api.call('POST', '/volume-textures/tiles', {**G(VOLUME), **LIVE, **tile, 'ExpectedTargetPath': T2D_C, 'ExpectedSizeX': 32, 'ExpectedSizeY': 32, 'SizeX': 16, 'SizeY': 16})
    vol = api.call('POST', '/volume-textures/inspect', {'AssetPath': VOLUME})
    assert (vol['source_width'], vol['source_height'], vol['source_depth'], vol['authored_tile_count']) == (16, 16, 8, 8), vol
    for route in ('/texture-cubes/inspect-page', '/texture-arrays/inspect-page', '/texture-cube-arrays/inspect-page', '/volume-textures/inspect-page'):
        assert 'MCP' in json.dumps(api.call('POST', route, {'PathFilter': '/Game/UE5MCP_Test', 'Count': 32})), route


def snapshot(api):
    out = {}
    for p in ASSETS:
        if 'TC_' in p or 'TCA_' in p or 'TV_' in p or 'TA_' in p:
            route = {'TC_': '/texture-cubes/inspect', 'TCA': '/texture-cube-arrays/inspect', 'TV_': '/volume-textures/inspect', 'TA_': '/texture-arrays/inspect'}[p.split('/')[-1][:3]]
            d = api.call('POST', route, {'AssetPath': p})
        else:
            d = {'settings': {k: v['native_text'] for k, v in settings(api, p).items()},
                 'stats': api.call('POST', '/textures/source-mips/statistics', {**guards(api, p), 'bConfirm': True})['channels']}
        d.pop('package_dirty', None); d.pop('scope', None); d.pop('dirty', None)
        out[p] = d
    return out


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'tag': tag}), encoding='utf-8')
    texture2d_stage(api)
    source_stage(api)
    dimensional_stage(api)
    for p in ASSETS:
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'tag': tag, 'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared texture authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in ASSETS:
            load(api, p)
        cold = snapshot(api)
        for p in ASSETS:
            assert state['snapshot'][p] == cold[p], (p, json.dumps(state['snapshot'][p])[:700], json.dumps(cold[p])[:700])
        print('Cold reload of texture settings, source pixels, cube/array/cube-array/volume textures: OK')
    finally:
        cleanup(api)


def cleanup(api):
    if STATE.exists() and not ASSETS:
        use_tag(json.loads(STATE.read_text(encoding='utf-8')).get('tag', 'none'))
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned texture test assets')


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
