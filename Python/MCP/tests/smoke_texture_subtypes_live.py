"""Live cube/volume/2D-array/cube-array texture authoring, texture consumers, HDR/grayscale sources; prepare, restart, verify.

prepare: create source-free cube/volume/array/cube-array textures with RGBA fills, edit every natively editable
sampling, mip, LOD, address, processing, colour-adjustment, padding and resize setting on each subtype (stale guard,
dry run, real edit), measure per-slice alpha coverage, author source-backed cube-array lists and volume sources,
inspect material/instance consumers and sampler diagnostics, streaming state, decoded-payload fingerprints,
grayscale/HDR linear sources and a Texture2DArray DDS export; save and snapshot.
verify (fresh editor): reload everything and compare the snapshot, then delete.
"""
import argparse
import json
import math
import struct
import sys
import uuid
import zlib
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
ARGV, sys.argv[1:] = sys.argv[1:], []  # mcp_server parses argv on import
import mcp_server as m  # noqa: E402
sys.argv[1:] = ARGV

STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'texture_subtypes.json'
IMAGES = PROJECT / 'Saved' / 'UE5MCP_Test' / 'texture_subtype_images'
EXPORTS = PROJECT / 'Saved' / 'UE5_MCP' / 'Exports'
D = '/Game/UE5MCP_Test/'
LIVE = {'bConfirm': True, 'bDryRun': False}
DEFAULT_TEX = '/Engine/EngineResources/DefaultTexture.DefaultTexture'
N = {}
ADJUST = {'AdjustBrightness': 1.5, 'AdjustBrightnessCurve': 1.2, 'AdjustVibrance': 0.3, 'AdjustSaturation': 0.8,
          'AdjustRGBCurve': 1.1, 'AdjustHue': 30, 'AdjustMinAlpha': 0.1, 'AdjustMaxAlpha': 0.9}
INTEGERS = {'LODBias': 1, 'MaxTextureSize': 32, 'NumCinematicMipLevels': 1}
# Handled separately: padding/resize need a padding mode, normal normalization a normal-map compression.
SKIP = {'DownscaleOptions', 'PowerOfTwoMode', 'ResizeDuringBuildX', 'ResizeDuringBuildY', 'bPadWithBorderColor', 'bNormalizeNormals'}


def use_tag(tag):
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    N.update(tag=tag, cube=n('TC_MCP_SubA'), cube_b=n('TC_MCP_SubB'), cube_c=n('TC_MCP_SubC'), vol=n('TV_MCP_Sub'),
             arr=n('TA_MCP_Sub'), carr=n('TCA_MCP_Sub'), carr_src=n('TCA_MCP_SubSrc'), vol_src=n('TV_MCP_SubSrc'),
             tile=n('T_MCP_SubTile'), tile_b=n('T_MCP_SubTileB'), tex=n('T_MCP_SubTex'),
             gray=n('T_MCP_SubGray'), hdr=n('T_MCP_SubHdr'), mat=n('M_MCP_Sub'), mi=n('MI_MCP_Sub'))


def assets():
    return [v for k, v in N.items() if k != 'tag']


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def load(api, path):
    api.call('GET', '/assets/describe', params={'asset_path': path})


def guards(api, path):
    s = api.call('POST', '/textures/source-identity/inspect', {'AssetPath': path})
    return {'AssetPath': path, 'ExpectedClassPath': s['class_path'], 'ExpectedSourceId': s['source_attribute_id'],
            'ExpectedAssetSnapshot': s['native_authored_snapshot']}


def sampling(api, path):
    return {s['field_name']: s for s in api.call('POST', '/textures/sampling/inspect', {'AssetPath': path})['settings']}


def stats(api, path):
    g = guards(api, path)
    return {c['channel']: (c['min_byte'], c['max_byte']) for c in
            api.call('POST', '/textures/source-mips/statistics', {**g, 'bConfirm': True})['channels']}


def fingerprints(api, path):
    g = guards(api, path)
    v = api.call('POST', '/textures/source-mips/validate-payloads', {'AssetPath': path, 'ExpectedSourceId': g['ExpectedSourceId'], 'bConfirm': True})
    assert v['all_selected_mips_decode_and_match_size'] and v['failed_mip_count'] == 0, v
    return [mm['decoded_payload_sha1'] for mm in v['mips']]


def setting(api, path, name, cur, value, route='/textures/sampling/setting'):
    """Stale guard rejected, dry run leaves the value, real edit lands."""
    body = {**guards(api, path), **LIVE, 'FieldName': name, 'ExpectedValue': cur, 'Value': value}
    api.call('POST', route, {**body, 'ExpectedValue': cur + 77}, ok=False)
    api.call('POST', route, {**body, 'bDryRun': True})
    assert math.isclose(sampling(api, path)[name]['value'], cur, abs_tol=1e-4), (path, name, 'dry run changed it')
    api.call('POST', route, body)
    after = sampling(api, path)[name]['value']
    assert math.isclose(after, value, abs_tol=1e-4), (path, name, cur, value, after)


def choice(s, suffix=None):
    names = [c for c in s['choices'] if not c['name'].endswith('MAX') and c['value'] != s['value']]
    return next(c['value'] for c in names if c['name'].endswith(suffix)) if suffix else names[0]['value']


# ---------------------------------------------------------------- creation with RGBA fills
FILLS = {'cube': [200, 100, 50, 128], 'cube_b': [10, 20, 30, 255], 'cube_c': [200, 100, 50, 128],
         'vol': [5, 6, 7, 8], 'arr': [90, 80, 70, 60], 'carr': [1, 2, 3, 4]}


def creation_stage(api):
    make = {'cube': ('/texture-cubes/create', {'SizeX': 16}), 'cube_b': ('/texture-cubes/create', {'SizeX': 16}),
            'cube_c': ('/texture-cubes/create', {'SizeX': 16}),
            'vol': ('/volume-textures/create-solid', {'SizeX': 8, 'SizeY': 8, 'SizeZ': 4}),
            'arr': ('/texture-arrays/create-solid', {'SizeX': 16, 'SizeY': 16, 'SizeZ': 3}),
            'carr': ('/texture-cube-arrays/create-solid', {'SizeX': 8, 'SizeY': 8, 'SizeZ': 2})}
    for key, (route, size) in make.items():
        api.call('POST', route, {'AssetPath': N[key], **LIVE, **size, 'Color': [256, 0, 0, 255]}, ok=False)
        api.call('POST', route, {'AssetPath': N[key], **LIVE, **size, 'Color': [1, 2, 3]}, ok=False)
        r = api.call('POST', route, {'AssetPath': N[key], 'bConfirm': True, 'bDryRun': True, **size, 'Color': FILLS[key]})
        assert r['source_fill_rgba_bytes'] == FILLS[key], r
        api.call('GET', '/assets/describe', params={'asset_path': N[key]}, ok=False)
        r = api.call('POST', route, {'AssetPath': N[key], **LIVE, **size, 'Color': FILLS[key]})
        assert r['source_fill_rgba_bytes'] == FILLS[key], r
        load(api, N[key])
        want = dict(zip('RGBA', ((c, c) for c in FILLS[key])))
        assert stats(api, N[key]) == want, (key, stats(api, N[key]))
    for key, size in (('tile', (64, 32)), ('tile_b', (32, 32)), ('tex', (16, 16))):
        api.call('POST', '/textures/create-2d', {'AssetPath': N[key], **LIVE, 'SizeX': size[0], 'SizeY': size[1], 'Color': [40, 80, 120, 255]})
        load(api, N[key])
    # Identical fills give identical decoded-payload fingerprints; a different fill does not.
    a, b, c = fingerprints(api, N['cube']), fingerprints(api, N['cube_b']), fingerprints(api, N['cube_c'])
    assert a == c and len(a) == 5 and all(x != y for x, y in zip(a, b)), (a, b, c)


# ---------------------------------------------------------------- cross-subtype sampling and processing
def sampling_stage(api):
    edited = {}
    for key in ('cube', 'vol', 'arr', 'carr'):
        path = N[key]
        s = sampling(api, path)
        done = []
        # Legacy gamma needs sRGB on, so it goes before the SRGB toggle.
        for name in sorted(s, key=lambda x: (x != 'bUseLegacyGamma', x)):
            e = s[name] = sampling(api, path)[name]
            if name in SKIP or name in ADJUST:
                continue
            if not e['available']:
                api.call('POST', '/textures/sampling/setting', {**guards(api, path), **LIVE, 'FieldName': name, 'ExpectedValue': 0, 'Value': 1}, ok=False)
                continue
            if not e['native_editable']:
                continue
            cur = e['value']
            new = INTEGERS[name] if name in INTEGERS else choice(e) if e['kind'] == 'enum' else 1 - cur
            setting(api, path, name, cur, new)
            done.append(name)
        # Normal normalization needs a normal-map compression mode: refused, then allowed once compression is set.
        nn = sampling(api, path)['bNormalizeNormals']
        api.call('POST', '/textures/sampling/setting', {**guards(api, path), **LIVE, 'FieldName': 'bNormalizeNormals', 'ExpectedValue': nn['value'], 'Value': 1}, ok=False)
        api.call('POST', '/textures/sampling/setting', {**guards(api, path), **LIVE, 'FieldName': 'LODBias', 'ExpectedValue': 1, 'Value': 40}, ok=False)
        api.call('POST', '/textures/sampling/setting', {**guards(api, path), **LIVE, 'FieldName': 'MaxTextureSize', 'ExpectedValue': 32, 'Value': 48}, ok=False)
        for name, value in ADJUST.items():
            setting(api, path, name, sampling(api, path)[name]['value'], value, route='/textures/color-adjustment')
            done.append(name)
        api.call('POST', '/textures/color-adjustment', {**guards(api, path), **LIVE, 'FieldName': 'AdjustHue', 'ExpectedValue': 30, 'Value': 400}, ok=False)
        assert len(done) >= 21, (key, done)
        edited[key] = done
    # Volume exposes the unified AddressMode, the array the three axes, cubes none.
    assert 'AddressMode' in edited['vol'] and {'AddressX', 'AddressY', 'AddressZ'} <= set(edited['arr']), edited
    assert not {'AddressX', 'AddressMode'} & set(edited['cube'] + edited['carr']), edited
    return edited


def padding_stage(api):
    # Border-colour padding and padding colour need a pad-to-power-of-two mode; resize needs ResizeToSpecificResolution.
    for key in ('cube', 'arr'):
        path = N[key]
        api.call('POST', '/textures/sampling/setting', {**guards(api, path), **LIVE, 'FieldName': 'bPadWithBorderColor', 'ExpectedValue': 0, 'Value': 1}, ok=False)
        api.call('POST', '/textures/padding-color', {**guards(api, path), **LIVE, 'ExpectedColor': [0, 0, 0, 255], 'Color': [1, 2, 3, 255]}, ok=False)
        mode = sampling(api, path)['PowerOfTwoMode']
        setting(api, path, 'PowerOfTwoMode', mode['value'], choice(mode, 'PadToPowerOfTwo'))
        body = {**guards(api, path), **LIVE, 'ExpectedColor': [0, 0, 0, 255], 'Color': [11, 22, 33, 44]}
        api.call('POST', '/textures/padding-color', {**body, 'ExpectedColor': [9, 9, 9, 9]}, ok=False)
        api.call('POST', '/textures/padding-color', {**body, 'Color': [11, 22, 33, 300]}, ok=False)
        api.call('POST', '/textures/padding-color', {**body, 'bDryRun': True})
        pc = lambda: api.call('POST', '/textures/sampling/inspect', {'AssetPath': path})['padding_color_rgba_bytes']
        assert pc() == [0, 0, 0, 255], pc()
        api.call('POST', '/textures/padding-color', body)
        assert pc() == [11, 22, 33, 44], pc()
        setting(api, path, 'bPadWithBorderColor', 0, 1)
        # With border-colour padding on, the fixed colour is refused.
        api.call('POST', '/textures/padding-color', {**guards(api, path), **LIVE, 'ExpectedColor': [11, 22, 33, 44], 'Color': [1, 1, 1, 1]}, ok=False)
        assert pc() == [11, 22, 33, 44], pc()
    # The engine keeps ResizeToSpecificResolution on Texture2D only, so the mode and the paired resize are refused here.
    for key in ('vol', 'carr'):
        path = N[key]
        mode = sampling(api, path)['PowerOfTwoMode']
        api.call('POST', '/textures/sampling/setting', {**guards(api, path), **LIVE, 'FieldName': 'PowerOfTwoMode', 'ExpectedValue': mode['value'],
                                                        'Value': choice(mode, 'ResizeToSpecificResolution')}, ok=False)
        api.call('POST', '/textures/build-resize', {**guards(api, path), **LIVE, 'ExpectedSizeX': 0, 'ExpectedSizeY': 0, 'SizeX': 8, 'SizeY': 4}, ok=False)
        assert sampling(api, path)['PowerOfTwoMode']['value'] == mode['value']


def coverage_stage(api):
    # Fill alpha 128 sits below a 0.6 alpha threshold on every face; pages walk the six faces.
    path = N['cube']
    ac = api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': path})
    body = {**guards(api, path), **LIVE, 'bExpectedEnabled': ac['enabled'], 'ExpectedColor': ac['thresholds_rgba'], 'bEnabled': True, 'Color': [0, 0, 0, 0.6]}
    api.call('POST', '/textures/alpha-coverage', {**body, 'bExpectedEnabled': not ac['enabled']}, ok=False)
    api.call('POST', '/textures/alpha-coverage', {**body, 'bDryRun': True})
    assert api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': path})['enabled'] == ac['enabled']
    api.call('POST', '/textures/alpha-coverage', body)
    ac = api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': path})
    assert ac['enabled'] and math.isclose(ac['thresholds_rgba'][3], 0.6, abs_tol=1e-6), ac
    pages, start = [], 0
    while True:
        r = api.call('POST', '/textures/alpha-coverage/measure-source', {**guards(api, path), 'bConfirm': True, 'Start': start, 'Count': 4})
        assert r['source_slice_count'] == 6 and r['coverage_scaling_enabled'], r
        pages.append(r)
        if not r['has_more']:
            break
        start = r['next_start']
    slices = [s['slice_index'] for p in pages for s in p['slices']]
    assert slices == list(range(6)) and len(pages) == 2, slices
    assert pages[0]['channels_rgba'][3]['finite_count'] == 4 * 256 and pages[1]['channels_rgba'][3]['finite_count'] == 2 * 256, pages[1]
    assert all(s['channels_rgba'][3]['covered_finite_count'] == 0 for p in pages for s in p['slices']), pages[0]['slices'][0]
    assert all(s['channels_rgba'][0]['finite_count'] == 256 for p in pages for s in p['slices'])
    end = api.call('POST', '/textures/alpha-coverage/measure-source', {**guards(api, path), 'bConfirm': True, 'Start': 6, 'Count': 4})
    assert end['slices'] == [] and end['pixel_count'] == 0 and not end['has_more'], end['slices']
    # The array and volume measure per layer / depth slice.
    for key, n in (('arr', 3), ('vol', 4)):
        r = api.call('POST', '/textures/alpha-coverage/measure-source', {**guards(api, N[key]), 'bConfirm': True, 'Count': 8})
        assert r['source_slice_count'] == n and len(r['slices']) == n and not r['has_more'], r


# ---------------------------------------------------------------- source-backed cube arrays and volumes
def source_stage(api):
    cls = '/Script/Engine.TextureCubeArray'
    srcs = lambda: [x['path'] for x in api.call('POST', '/texture-cube-arrays/inspect', {'AssetPath': N['carr_src']})['source_textures']]
    api.call('POST', '/texture-cube-arrays/create', {'AssetPath': N['carr_src'], **LIVE, 'SourcePaths': [N['cube_c'], N['cube_c']]}, ok=False)  # duplicate
    api.call('POST', '/texture-cube-arrays/create', {'AssetPath': N['carr_src'], **LIVE, 'SourcePaths': [N['cube_c']]})
    load(api, N['carr_src'])
    assert srcs() == [N['cube_c']], srcs()
    body = {'AssetPath': N['carr_src'], 'ExpectedClassPath': cls, **LIVE, 'ExpectedSourcePaths': [N['cube_c']], 'SourcePaths': [N['cube_c'], N['cube_b']]}
    api.call('POST', '/texture-cube-arrays/sources/replace', {**body, 'ExpectedSourcePaths': [N['cube_b']]}, ok=False)
    api.call('POST', '/texture-cube-arrays/sources/replace', {**body, 'SourcePaths': [N['cube_c'], N['tex']]}, ok=False)  # not a cube
    api.call('POST', '/texture-cube-arrays/sources/replace', {**body, 'SourcePaths': []}, ok=False)
    api.call('POST', '/texture-cube-arrays/sources/replace', {**body, 'bDryRun': True})
    assert srcs() == [N['cube_c']], srcs()
    api.call('POST', '/texture-cube-arrays/sources/replace', body)
    assert srcs() == [N['cube_c'], N['cube_b']], srcs()
    body = {'AssetPath': N['carr_src'], 'ExpectedClassPath': cls, **LIVE, 'ExpectedSourcePaths': srcs(), 'SourceOrder': [1, 0]}
    api.call('POST', '/texture-cube-arrays/sources/reorder', {**body, 'SourceOrder': [0, 0]}, ok=False)
    api.call('POST', '/texture-cube-arrays/sources/reorder', {**body, 'bDryRun': True})
    assert srcs() == [N['cube_c'], N['cube_b']], srcs()
    api.call('POST', '/texture-cube-arrays/sources/reorder', body)
    assert srcs() == [N['cube_b'], N['cube_c']], srcs()
    # Regenerated source: twelve faces, the first six from cube_b.
    g = guards(api, N['carr_src'])
    px = api.call('POST', '/textures/source-mips/statistics', {**g, 'bConfirm': True})
    assert px['source_slices'] == 12, px
    # Volume texture source reassignment with explicit tiles: 64x32 sheet as 32x32 tiles, then a 32x32 sheet as 16x16 tiles.
    vcls = '/Script/Engine.VolumeTexture'
    tile = {'SourceTexturePath': N['tile'], 'ExpectedFormat': 2, 'ExpectedSourceSizeX': 64, 'ExpectedSourceSizeY': 32}
    api.call('POST', '/volume-textures/create', {'AssetPath': N['vol_src'], **LIVE, **tile, 'SizeX': 32, 'SizeY': 32})
    load(api, N['vol_src'])
    vol = lambda: api.call('POST', '/volume-textures/inspect', {'AssetPath': N['vol_src']})
    body = {'AssetPath': N['vol_src'], 'ExpectedClassPath': vcls, 'ExpectedTargetPath': N['tile'], 'SourceTexturePath': N['tile_b'],
            'ExpectedSizeX': 32, 'ExpectedSizeY': 32, 'SizeX': 16, 'SizeY': 16, 'ExpectedSourceSizeX': 32, 'ExpectedSourceSizeY': 32,
            'ExpectedFormat': 2, **LIVE}
    api.call('POST', '/volume-textures/source', {**body, 'ExpectedTargetPath': N['tile_b']}, ok=False)
    api.call('POST', '/volume-textures/source', {**body, 'SizeX': 12}, ok=False)  # not divisible
    api.call('POST', '/volume-textures/source', {**body, 'ExpectedSourceSizeX': 64}, ok=False)
    api.call('POST', '/volume-textures/source', {**body, 'bDryRun': True})
    assert vol()['source_2d_path'] == N['tile'], vol()
    api.call('POST', '/volume-textures/source', body)
    v = vol()
    assert v['source_2d_path'] == N['tile_b'] and (v['source_width'], v['source_height'], v['source_depth']) == (16, 16, 4), v


def compatibility_stage(api):
    arr = N['arr'].replace('TA_MCP_Sub', 'TA_MCP_SubList')
    N['arr_list'] = arr
    api.call('POST', '/texture-arrays/create', {'AssetPath': arr, **LIVE, 'SourcePaths': [N['tile_b'], N['tex']]}, ok=False)  # size mismatch
    api.call('POST', '/texture-arrays/create', {'AssetPath': arr, **LIVE, 'SourcePaths': [N['tile_b']]})
    load(api, arr)
    c = api.call('POST', '/texture-arrays/source-compatibility/inspect', {'AssetPath': arr})
    flat = json.dumps(c)
    assert c['source_count'] == 1 and c['passes_header_policy'] and c['list_authoring_candidate'] and c['sources'][0]['issues'] == [], flat[:800]
    s = api.call('POST', '/texture-arrays/source-compatibility/inspect', {'AssetPath': N['arr']})
    assert s['source_count'] == 0 and not s['passes_header_policy'] and not s['list_authoring_candidate'], json.dumps(s)[:800]


# ---------------------------------------------------------------- consumers, streaming state
def consumer_stage(api):
    mat, mi = N['mat'].split('.')[0], N['mi'].split('.')[0]
    for src, dst in (('/Game/LevelPrototyping/Materials/M_PrototypeGrid.M_PrototypeGrid', mat),
                     ('/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray', mi)):
        assert httpx.post(api.base + '/assets/duplicate', json={'AssetPath': src, 'DestinationPath': dst}, timeout=300).is_success
    m.create_material_expression(N['mat'], '/Script/Engine.MaterialExpressionTextureSampleParameter2D', 'MCP_SubTex')
    e = J(m.discover_material_expression_metadata(N['mat'], ':MCP_SubTex', '', 0, 8))['expressions'][0]
    r = J(m.set_material_texture_sample_reference(N['mat'], e['expression_path'], e['node_guid'], N['tex'], DEFAULT_TEX,
                                                  e['class_path'], e['metadata_snapshot'], confirm=True, dry_run=False))
    assert 'errorMessage' not in r, r
    assert httpx.patch(api.base + '/material-instances/parent', json={'AssetPath': N['mi'], 'ParentPath': N['mat']}, timeout=300).is_success
    assert J(m.edit_material_instance_parameter(N['mi'], 'Param', 'texture', N['tex'])).get('changed'), 'override'
    page = lambda route, **kw: api.call('POST', route, {'AssetPath': N['tex'], 'PathFilter': kw.get('f', ''), 'Start': kw.get('s', 0), 'Count': kw.get('c', 8)})
    o = page('/textures/material-overrides/inspect-page')
    assert o['matching_override_count'] == 1 and o['overrides'][0]['material_instance_path'] == N['mi'] and o['overrides'][0]['parameter_name'] == 'Param', o
    assert page('/textures/material-overrides/inspect-page', f='NoSuchMaterial')['matching_override_count'] == 0
    x = page('/textures/expression-references/inspect-page')
    assert x['matching_expression_count'] == 1, x
    e = x['expressions'][0]
    assert e['owning_asset_path'] == N['mat'] and e['expression_path'].endswith(':MCP_SubTex'), e
    assert e['native_sampler_policy_available'] and e['passes_authored_sampler_policy'] and e['sampler_type'] == 0, e
    # A normal-map compression makes the authored colour sampler fail the native policy check.
    comp = {c['field_name']: c for c in api.call('POST', '/textures/compression/inspect', {'AssetPath': N['tex']})['settings']}['CompressionSettings']
    api.call('POST', '/textures/compression/setting', {**guards(api, N['tex']), **LIVE, 'FieldName': 'CompressionSettings', 'ExpectedValue': comp['value'], 'Value': 1})
    e = page('/textures/expression-references/inspect-page')['expressions'][0]
    assert not e['passes_authored_sampler_policy'] and e['expected_sampler_type'] != e['sampler_type'] and e['sampler_policy_message'], e
    b = page('/textures/brush-assets/inspect-page')
    assert b['matching_brush_asset_count'] == 0 and b['brush_assets'] == [], b
    for route in ('/textures/material-overrides/inspect-page', '/textures/expression-references/inspect-page', '/textures/brush-assets/inspect-page'):
        api.call('POST', route, {'AssetPath': N['tex'], 'Count': 500}, ok=False)
    # Streaming state: cached resource policy mirrors the authored NeverStream flag.
    for key in ('tex', 'vol', 'cube'):
        st = api.call('POST', '/textures/streaming-state/inspect', {'AssetPath': N[key]})
        never = sampling(api, N[key])['NeverStream']['value']
        assert st['never_stream'] == bool(never), (key, st, never)
        for k in ('resident_lod_count', 'requested_lod_count', 'max_lod_count', 'registered_with_streamer', 'supports_virtual_streaming'):
            assert k in st, (key, k)
        assert not st['supports_virtual_streaming'], st
    api.call('POST', '/textures/streaming-state/inspect', {'AssetPath': '/Game/UE5MCP_Test/Nope.Nope'}, ok=False)


# ---------------------------------------------------------------- grayscale / HDR sources, array DDS export
def write_images():
    IMAGES.mkdir(parents=True, exist_ok=True)
    w = h = 16
    raw = b''.join(b'\x00' + bytes((x * 16) & 255 for x in range(w)) for _ in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    (IMAGES / 'gray.png').write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
                                      + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
    # Radiance RGBE: mantissas 128/64/32 with exponent 130 decode to about (2, 1, 0.5).
    (IMAGES / 'hdr.hdr').write_bytes(b'#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y 8 +X 8\n' + bytes([128, 64, 32, 130]) * 64)


def hdr_stage(api):
    write_images()
    for key, f in (('gray', 'gray.png'), ('hdr', 'hdr.hdr')):
        name = N[key].split('.')[-1]
        r = J(m.import_texture(str(IMAGES / f), D.rstrip('/'), name))
        assert r.get('changed'), r
        load(api, N[key])
    g = guards(api, N['gray'])
    lin = lambda p, **kw: api.call('POST', '/textures/source-mips/linear-pixels/inspect-page', {**guards(api, p), 'bConfirm': True, 'Start': kw.get('s', 0), 'Count': kw.get('c', 2)})
    lst = lambda p: {c['channel']: c for c in api.call('POST', '/textures/source-mips/linear-statistics', {**guards(api, p), 'bConfirm': True})['channels']}
    api.call('POST', '/textures/source-mips/linear-pixels/inspect-page', {**g, 'Count': 2}, ok=False)  # unconfirmed
    api.call('POST', '/textures/source-mips/linear-pixels/inspect-page', {**g, 'ExpectedSourceId': '0' * 32, 'bConfirm': True}, ok=False)
    px = lin(N['gray'])
    # Grayscale byte 16 is sRGB, about 0.00518 linear; channels replicate, alpha is 1.
    assert px['pixel_count'] == 256 and px['pixels'][0]['linear_rgba'] == [0, 0, 0, 1], px['pixels'][0]
    v = px['pixels'][1]['linear_rgba']
    assert math.isclose(v[0], 0.00518, abs_tol=2e-4) and v[0] == v[1] == v[2] and v[3] == 1, v
    s = lst(N['gray'])
    assert s['R']['minimum'] == 0 and math.isclose(s['R']['maximum'], 0.8714, abs_tol=1e-3) and s['A']['population_standard_deviation'] == 0, s['R']
    assert s['R']['above_one_pixel_count'] == 0 and s['R']['finite_pixel_count'] == 256, s['R']
    # HDR: unclamped values above one, imported as a long-lat cube.
    px = lin(N['hdr'], s=63, c=4)
    assert px['pixel_count'] == 64 and len(px['pixels']) == 1 and not px['has_more'], px
    assert [round(c, 3) for c in px['pixels'][0]['linear_rgba']] == [2.008, 1.008, 0.508, 1], px['pixels'][0]
    s = lst(N['hdr'])
    assert s['R']['above_one_pixel_count'] == 64 and s['G']['above_one_pixel_count'] == 64 and s['B']['above_one_pixel_count'] == 0, s
    assert s['R']['population_standard_deviation'] == 0 and s['R']['nonfinite_pixel_count'] == 0, s['R']
    return {'gray_sha1': fingerprints(api, N['gray']), 'hdr_sha1': fingerprints(api, N['hdr'])}


def dds_stage(api):
    g = guards(api, N['arr'])
    stem = 'mcp_subtype_' + N['tag']
    for f in EXPORTS.glob(stem + '*'):
        f.unlink()
    body = {**g, **LIVE, 'Name': stem, 'BlockIndex': 0, 'LayerIndex': 0}
    api.call('POST', '/textures/source/export-dds', {**body, 'ExpectedSourceId': '0' * 32}, ok=False)
    r = api.call('POST', '/textures/source/export-dds', {**body, 'bDryRun': True})
    assert not list(EXPORTS.glob(stem + '*')), r
    r = api.call('POST', '/textures/source/export-dds', body)
    out = Path(r['output_path'])
    data = out.read_bytes()
    assert data[:4] == b'DDS ', data[:8]
    h, w, depth, mips = struct.unpack_from('<IIII', data, 12)[0], struct.unpack_from('<I', data, 16)[0], struct.unpack_from('<I', data, 24)[0], struct.unpack_from('<I', data, 28)[0]
    four = data[84:88]
    assert (h, w) == (16, 16) and four == b'DX10', (h, w, four)
    dxgi, dim, _, array_size = struct.unpack_from('<IIII', data, 128)
    assert dim == 3 and array_size == 3, (dxgi, dim, array_size)   # Texture2D, three slices
    api.call('POST', '/textures/source/export-dds', body, ok=False)  # no overwrite
    out.unlink()
    return {'dxgi': dxgi, 'mips': mips}


def capability_stage(api):
    c = api.call('GET', '/assets/capabilities')['families']
    rt = c['render_target']
    assert rt['dedicated_subtypes'] == ['2d', 'cube', 'volume', '2d_array'] and rt['implementation_status'] and rt['support_level'] == 'partial', rt
    assert not rt['compile_or_rebuild'] and not rt['validate'], rt
    ta = c['texture_array']
    assert 'replacement/reordering' in ta['notes'] and not ta['compile_or_rebuild'] and ta['spawn_or_create'], ta
    rvt = c['runtime_virtual_texture']
    assert rvt['spawn_or_create'] and not rvt['compile_or_rebuild'] and not rvt['validate'] and 'rendered_output_verified' in rvt, rvt


# ---------------------------------------------------------------- snapshot / phases
def snapshot(api):
    out = {}
    for key in ('cube', 'cube_b', 'vol', 'arr', 'carr', 'carr_src', 'vol_src'):
        s = api.call('POST', '/textures/sampling/inspect', {'AssetPath': N[key]})
        out[key] = {'settings': {k: v.get('value') for k, v in sampling(api, N[key]).items()},
                    'padding': s['padding_color_rgba_bytes'], 'stats': stats(api, N[key]), 'sha1': fingerprints(api, N[key])}
    out['carr_src_list'] = [x['path'] for x in api.call('POST', '/texture-cube-arrays/inspect', {'AssetPath': N['carr_src']})['source_textures']]
    v = api.call('POST', '/volume-textures/inspect', {'AssetPath': N['vol_src']})
    out['vol_src'].update(source=v['source_2d_path'], dims=[v['source_width'], v['source_height'], v['source_depth']])
    ac = api.call('POST', '/textures/alpha-coverage/inspect', {'AssetPath': N['cube']})
    out['coverage'] = [ac['enabled'], [round(x, 5) for x in ac['thresholds_rgba']]]
    o = api.call('POST', '/textures/material-overrides/inspect-page', {'AssetPath': N['tex'], 'Count': 8})['overrides']
    out['overrides'] = [(x['material_instance_path'], x['parameter_name']) for x in o]
    x = api.call('POST', '/textures/expression-references/inspect-page', {'AssetPath': N['tex'], 'Count': 8})['expressions']
    out['expressions'] = [(e['expression_path'], e['passes_authored_sampler_policy'], e['expected_sampler_type']) for e in x]
    for key in ('gray', 'hdr'):
        out[key] = {c['channel']: [c['minimum'], c['maximum'], c['above_one_pixel_count']] for c in
                    api.call('POST', '/textures/source-mips/linear-statistics', {**guards(api, N[key]), 'bConfirm': True})['channels']}
        out[key + '_sha1'] = fingerprints(api, N[key])
    return out


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    use_tag(uuid.uuid4().hex[:6])
    STATE.write_text(json.dumps({'tag': N['tag']}), encoding='utf-8')
    creation_stage(api)
    edited = sampling_stage(api)
    padding_stage(api)
    coverage_stage(api)
    source_stage(api)
    compatibility_stage(api)
    consumer_stage(api)
    hdr_stage(api)
    dds = dds_stage(api)
    capability_stage(api)
    for p in assets():
        httpx.post(api.base + '/assets/save', json={'AssetPath': p}, timeout=600)
    STATE.write_text(json.dumps({'tag': N['tag'], 'arr_list': N['arr_list'], 'snapshot': snapshot(api)}), encoding='utf-8')
    print('texture subtypes prepared; edited', {k: len(v) for k, v in edited.items()}, 'dds', dds)


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    N['arr_list'] = state['arr_list']
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in assets():
            load(api, p)
        cold = snapshot(api)
        for k in state['snapshot']:
            assert json.dumps(state['snapshot'][k]) == json.dumps(cold[k]), (k, json.dumps(state['snapshot'][k])[:600], json.dumps(cold[k])[:600])
        print('texture subtypes, consumers and HDR/grayscale sources identical after cold reload')
    finally:
        cleanup(api)


def cleanup(api):
    if not N and STATE.exists():
        state = json.loads(STATE.read_text(encoding='utf-8'))
        use_tag(state.get('tag', 'none'))
        if state.get('arr_list'):
            N['arr_list'] = state['arr_list']
    for p in assets():
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    for f in IMAGES.glob('*'):
        f.unlink()
    STATE.unlink(missing_ok=True)
    print('cleaned texture subtype assets')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    p.add_argument('--base', default='http://127.0.0.1:8080')
    a = p.parse_args()
    m.BASE_URL = a.base
    api = Api(a.base)
    assert not api.call('GET', '/editor/status')['is_playing']
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[a.phase](api)


if __name__ == '__main__':
    main()
