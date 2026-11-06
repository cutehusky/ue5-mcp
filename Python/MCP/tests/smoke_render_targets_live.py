"""Live render-target authoring on scratch 2D/cube/volume/2D-array render targets.

prepare: create each target (dry run first), page and consumer discovery, edit every typed setting, resize and clear
color with value/size/snapshot guards, dry runs and undo/redo, range refusals, export and conversion dry runs plus the
GPU-readback refusal under -nullrhi; save and snapshot.
verify (fresh editor): load the targets, compare the authored snapshots, then delete.
"""
import argparse
import json
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'render_targets.json'
EXPORTS = PROJECT / 'Saved' / 'UE5_MCP' / 'Exports'
D = '/Game/UE5MCP_Test/'
E = '/Script/Engine.'
LIVE = {'bConfirm': True, 'bDryRun': False}
# Deleted packages stay in memory until garbage collection, so every run uses its own name tag.
TAG = None
TARGETS = {}


def use_tag(tag):
    global TAG, TARGETS
    TAG = tag
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    TARGETS = {'2d': n('RT_MCP_2D'), 'cube': n('RT_MCP_Cube'), 'volume': n('RT_MCP_Volume'), '2d-array': n('RT_MCP_Array')}


CLASS = {'2d': 'TextureRenderTarget2D', 'cube': 'TextureRenderTargetCube', 'volume': 'TextureRenderTargetVolume',
         '2d-array': 'TextureRenderTarget2DArray'}
CREATE = {'2d': {'SizeX': 64, 'SizeY': 32}, 'cube': {'SizeX': 32}, 'volume': {'SizeX': 8, 'SizeY': 8, 'SizeZ': 4},
          '2d-array': {'SizeX': 16, 'SizeY': 16, 'SizeZ': 3}}
# (field, value before, new value, snapshot text after); applied in order, so later guards see earlier edits.
EDITS = {
    '2d': [('TargetGamma', 0, 2.5, '2.500000'), ('RenderTargetFormat', 6, 2, 'RTF_RGBA8'), ('bGPUSharedFlag', 0, 1, 'True'),
           ('bSupportsUAV', 0, 1, 'True'), ('bAutoGenerateMips', 0, 1, 'True'), ('MipsSamplerFilter', 3, 1, 'TF_Bilinear'),
           ('MipsAddressU', 1, 0, 'TA_Wrap'), ('MipsAddressV', 1, 2, 'TA_Mirror')],
    'cube': [('SizeX', 32, 64, '64'), ('TargetGamma', 0, 1.5, '1.500000'), ('bHDR', 1, 0, 'False'), ('bSupportsUAV', 0, 1, 'True'),
             ('bAutoGenerateMips', 0, 1, 'True'), ('MipsSamplerFilter', 3, 0, 'TF_Nearest')],
    'volume': [('TargetGamma', 0, 2, '2.000000'), ('bHDR', 1, 0, 'False'), ('bSupportsUAV', 0, 1, 'True')],
    '2d-array': [('TargetGamma', 0, 3, '3.000000'), ('bHDR', 1, 0, 'False'), ('bSupportsUAV', 0, 1, 'True')],
}
RESIZE = {'2d': {'SizeX': 128, 'SizeY': 64}, 'volume': {'SizeX': 16, 'SizeY': 8, 'SizeZ': 2},
          '2d-array': {'SizeX': 32, 'SizeY': 8, 'SizeZ': 5}}
CLEAR = {'2d': [0.25, 0.5, 0.75, 0.5], 'cube': [1, 0, 0, 1], 'volume': [0, 0, 1, 1], '2d-array': [0.5, 0.5, 0.5, 1]}


def inspect(api, kind):
    return api.call('POST', f'/render-targets/{kind}/inspect', {'AssetPath': TARGETS[kind]})


def snap(api, kind):
    return json.loads(inspect(api, kind)['native_authored_snapshot'])


def sizes(s, kind=None):
    keys = {'SizeX': 'ExpectedSizeX', 'SizeY': 'ExpectedSizeY', 'SizeZ': 'ExpectedSizeZ', 'Slices': 'ExpectedSizeZ'}
    return {keys[k]: int(v) for k, v in s.items() if k in keys}


def color(text):
    return [float(part.split('=')[1]) for part in text.strip('()').split(',')]


def guard(api, kind):
    s = snap(api, kind)
    g = {'AssetPath': TARGETS[kind], 'ExpectedClassPath': E + CLASS[kind], **sizes(s, kind)}
    if kind == '2d':
        g['ExpectedFormat'] = [o['name'] for o in next(x for x in inspect(api, kind)['settings'] if x['name'] == 'RenderTargetFormat')['enum_options']].index(s['RenderTargetFormat'])
    else:
        g['ExpectedFormat'] = 1 if s['bHDR'] == 'True' else 0
    return s, g


def checked_edit(api, kind, route, body, expect, undo=False):
    """Dry run (no change), stale snapshot refusal, real edit with snapshot guard; returns the new snapshot."""
    before, g = guard(api, kind)
    raw = inspect(api, kind)['native_authored_snapshot']
    d = api.call('POST', route, {**g, **body, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and d['would_change'], d
    assert snap(api, kind) == before, (kind, route, 'dry run changed state')
    api.call('POST', route, {**g, **body, **LIVE, 'ExpectedAssetSnapshot': raw.replace('class_path', 'class_paths'), 'bRequireAssetSnapshot': True}, ok=False)
    api.call('POST', route, {**g, **body, **LIVE, 'ExpectedAssetSnapshot': raw, 'bRequireAssetSnapshot': True})
    after = snap(api, kind)
    for k, v in expect.items():
        assert after[k] == v, (kind, route, k, after[k], v)
    if undo:
        # SRGB is derived: native post-edit (and undo) recompute it, while the factory leaves its own initial value.
        authored = lambda s: {k: v for k, v in s.items() if k != 'SRGB'}
        api.undo()
        assert authored(snap(api, kind)) == authored(before), (kind, route, 'undo')
        api.redo()
        assert snap(api, kind) == after, (kind, route, 'redo')
    return after


def create_stage(api):
    for kind, path in TARGETS.items():
        body = {'AssetPath': path, **CREATE[kind]}
        d = api.call('POST', f'/render-targets/{kind}/create', {**body, 'bConfirm': True, 'bDryRun': True})
        assert not d['created'] and d['dry_run'], d
        api.call('POST', f'/render-targets/{kind}/inspect', {'AssetPath': path}, ok=False)
        d = api.call('POST', f'/render-targets/{kind}/create', {**body, **LIVE})
        assert d['created'] and d['class_path'] == E + CLASS[kind], d
        api.call('POST', f'/render-targets/{kind}/create', {**body, **LIVE}, ok=False)
        s = snap(api, kind)
        assert s['class_path'] == E + CLASS[kind] and sizes(s, kind) == {'Expected' + k: v for k, v in CREATE[kind].items()}, s
        page = api.call('POST', f'/render-targets/{kind}/inspect-page', {'PathFilter': TAG, 'Start': 0, 'Count': 8})
        assert [t['asset_path'] for t in page['targets']] == [path] and not page['has_more'], page
    for kind in ('2d', 'cube'):
        page = api.call('POST', f'/render-targets/{kind}/consumers/inspect-page', {'AssetPath': TARGETS[kind], 'Start': 0, 'Count': 8})
        assert page['matched_count'] == 0 and page['scene_capture_consumers'] == [], page
    # Out-of-range creation sizes are refused.
    api.call('POST', '/render-targets/2d/create', {'AssetPath': f'{D}RT_MCP_Big_{TAG}.RT_MCP_Big_{TAG}', 'SizeX': 4096, 'SizeY': 4, **LIVE}, ok=False)


def edit_stage(api):
    for kind, edits in EDITS.items():
        for i, (field, before, value, text) in enumerate(edits):
            route = f'/render-targets/{kind}/setting'
            _, g = guard(api, kind)
            api.call('POST', route, {**g, 'FieldName': field, 'Value': value, 'ExpectedValue': before + 7, **LIVE}, ok=False)
            checked_edit(api, kind, route, {'FieldName': field, 'Value': value, 'ExpectedValue': before}, {field: text}, undo=i == 0)
        _, g = guard(api, kind)
        api.call('POST', f'/render-targets/{kind}/setting', {**g, 'FieldName': 'TargetGamma', 'Value': 11, 'ExpectedValue': edits[0][2], **LIVE}, ok=False)
        if kind in RESIZE:
            expect = {('Slices' if kind == '2d-array' and k == 'SizeZ' else k): str(v) for k, v in RESIZE[kind].items()}
            checked_edit(api, kind, f'/render-targets/{kind}/resize', RESIZE[kind], expect, undo=True)
            _, g = guard(api, kind)
            api.call('POST', f'/render-targets/{kind}/resize', {**g, **{k: 4096 for k in RESIZE[kind]}, **LIVE}, ok=False)
        s, g = guard(api, kind)
        prior = color(s['ClearColor'])
        api.call('POST', f'/render-targets/{kind}/clear-color', {**g, 'Color': CLEAR[kind], 'ExpectedColor': [9, 9, 9, 9], **LIVE}, ok=False)
        api.call('POST', f'/render-targets/{kind}/clear-color', {**g, 'Color': [70000, 0, 0, 1], 'ExpectedColor': prior, **LIVE}, ok=False)
        after = checked_edit(api, kind, f'/render-targets/{kind}/clear-color', {'Color': CLEAR[kind], 'ExpectedColor': prior}, {}, undo=True)
        assert color(after['ClearColor']) == CLEAR[kind], after


GPU, CONVERTED = [], []   # GPU-backed results when the editor runs with a rendering RHI


def export_stage(api):
    converted_kinds = []
    for kind, path in TARGETS.items():
        raw = inspect(api, kind)['native_authored_snapshot']
        g = {'SourceTexturePath': path, 'ExpectedClassPath': E + CLASS[kind], 'ExpectedAssetSnapshot': raw, 'bConfirm': True}
        conv = api.call('POST', '/render-targets/conversion/inspect', {'SourceTexturePath': path})
        assert conv['native_authored_snapshot'] == raw and 'native_can_convert' in conv, conv
        dest = f'{D}T_MCP_FromRT_{kind.replace("-", "")}_{TAG}.T_MCP_FromRT_{kind.replace("-", "")}_{TAG}'
        if not conv['native_can_convert']:
            # The native compatibility message (e.g. unsupported volume format) is surfaced as the refusal.
            msg = api.call('POST', '/render-targets/conversion/create-texture', {**g, 'AssetPath': dest, 'bDryRun': True}, ok=False)
            assert conv['native_message'] and 'Unsupported format' in msg, (kind, conv['native_message'], msg)
            converted_kinds.append((kind, False))
        else:
            d = api.call('POST', '/render-targets/conversion/create-texture', {**g, 'AssetPath': dest, 'bDryRun': True})
            assert not d['converted'] and d['dry_run'], d
            converted_kinds.append((kind, True))
        api.call('POST', '/render-targets/conversion/create-texture', {**g, 'AssetPath': dest, 'ExpectedAssetSnapshot': raw + ' ', 'bDryRun': True}, ok=False)
        # Under -nullrhi there is no GPU resource to read back and the routes refuse; with a rendering RHI
        # (-RenderOffscreen) the conversion creates the texture and the update reads back into it.
        print('CONVERT', kind, json.dumps(json.loads(raw)), conv.get('source_format'), conv.get('pixel_format'), flush=True)
        r = httpx.post(api.base + '/render-targets/conversion/create-texture', json={**g, 'AssetPath': dest, 'bDryRun': False}, timeout=600)
        if not converted_kinds[-1][1]:
            assert r.status_code >= 400 and 'Unsupported format' in r.text, (kind, r.text[:300])
            api.call('GET', '/assets/describe', params={'asset_path': dest}, ok=False)
        elif 'Rendering-capable RHI' in r.text:
            api.call('GET', '/assets/describe', params={'asset_path': dest}, ok=False)
        else:
            assert r.is_success and r.json()['converted'], (kind, r.text[:400])
            GPU.append(kind)
            CONVERTED.append(dest)
            api.call('GET', '/assets/describe', params={'asset_path': dest})
            ident = api.call('POST', '/textures/source-identity/inspect', {'AssetPath': dest})
            assert ident['source_header_valid'], ident
            if kind == '2d':
                u = {'SourceTexturePath': path, 'AssetPath': dest, 'ExpectedClassPath': E + CLASS[kind], 'ExpectedAssetSnapshot': raw,
                     'ExpectedDestinationSnapshot': ident['native_authored_snapshot'], 'bConfirm': True}
                api.call('POST', '/render-targets/conversion/update-texture', {**u, 'ExpectedDestinationSnapshot': 'stale', 'bDryRun': False}, ok=False)
                assert api.call('POST', '/render-targets/conversion/update-texture', {**u, 'bDryRun': True})['dry_run']
                api.call('POST', '/render-targets/conversion/update-texture', {**u, 'bDryRun': False})
        slices = 1 if kind == '2d' else int(snap(api, kind).get('Slices', snap(api, kind).get('SizeZ', 6)))
        for fmt in (['png', 'exr', 'hdr', 'dds'] if kind == '2d' else ['png', 'dds']):
            name = f'rt_mcp_{kind.replace("-", "")}_{fmt}_{TAG}'
            body = {**g, 'FieldName': fmt, 'Name': name, 'SliceIndex': slices - 1}
            d = api.call('POST', '/render-targets/export-image', {**body, 'bDryRun': True})
            assert not d['exported'] and d['format'] == fmt and d['output_path'].endswith(f'{name}.{fmt}'), d
            assert d['source_slices'] == slices, (kind, d)
            if fmt != 'dds':
                api.call('POST', '/render-targets/export-image', {**body, 'SliceIndex': slices, 'bDryRun': True}, ok=False)
            r = httpx.post(api.base + '/render-targets/export-image', json={**body, 'bDryRun': False}, timeout=600)
            out = EXPORTS / f'{name}.{fmt}'
            if 'Rendering-capable RHI' in r.text or 'only be read back in float16' in r.text:
                # No renderer, or a non-HDR volume target (native volume readback is float16-only).
                assert r.status_code >= 400 and not out.exists(), (name, r.text[:200])
            else:
                assert r.is_success and r.json()['exported'] and out.is_file(), (kind, fmt, r.text[:300])
                head = out.read_bytes()[:16]
                magic = {'png': bytes([0x89]) + b'PNG', 'dds': b'DDS ', 'exr': bytes([0x76, 0x2f, 0x31, 0x01]), 'hdr': b'#?'}[fmt]
                assert head.startswith(magic), (fmt, head)
                api.call('POST', '/render-targets/export-image', {**body, 'bDryRun': False}, ok=False)   # no overwrite
                out.unlink()
                GPU.append(f'{kind}:{fmt}')
        api.call('POST', '/render-targets/export-image', {**g, 'FieldName': 'tga', 'Name': 'x', 'bDryRun': True}, ok=False)
    # Both outcomes must be exercised: convertible targets and the native-format refusal (non-HDR volume).
    assert {ok for _, ok in converted_kinds} == {True, False}, converted_kinds
    for p in CONVERTED:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    print('GPU-backed results:', GPU or 'none (no rendering RHI)')


def snapshot(api):
    out = {}
    for kind in TARGETS:
        d = inspect(api, kind)
        for k in ('package_dirty', 'scope', 'cached_mip_count'):
            d.pop(k, None)
        out[kind] = d
    return out


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'tag': tag}), encoding='utf-8')
    create_stage(api)
    edit_stage(api)
    export_stage(api)
    for path in TARGETS.values():
        api.call('POST', '/assets/save', {'AssetPath': path})
    STATE.write_text(json.dumps({'tag': tag, 'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared render-target authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for path in TARGETS.values():
            api.call('GET', '/assets/describe', params={'asset_path': path})
        cold = snapshot(api)
        for kind in TARGETS:
            assert state['snapshot'][kind] == cold[kind], (kind, json.dumps(state['snapshot'][kind])[:900], json.dumps(cold[kind])[:900])
        print('Cold reload of 2D/cube/volume/2D-array render-target settings, sizes and clear colors: OK')
    finally:
        cleanup(api)


def cleanup(api):
    if STATE.exists() and not TARGETS:
        use_tag(json.loads(STATE.read_text(encoding='utf-8')).get('tag', 'none'))
    for path in TARGETS.values():
        httpx.post(api.base + '/assets/delete', json={'AssetPath': path}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned render-target test assets')


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
