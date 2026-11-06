"""Live landscape authoring on a scratch map, using the /landscapes/create fixture route.

prepare: create the scratch map, then a flat 2x2-component landscape with a new layer-info asset imported as paint
target "Grass" (dry run, invalid-label and duplicate-label refusals first). Inspect proxies, components, combined
heights, paint layers and weights; create/rename/reorder/toggle (visible/locked)/alpha-edit/delete edit layers;
patch heights and paint weights into an edit layer and read them back per layer and combined; edit the layer-info
blend, scalars, physical-material/texture references, debug colour and spline mask. Every edit has a dry run and a
stale-guard refusal; one edit per route also undo/redo. Save and snapshot.
verify (fresh editor): reload the map, compare everything, then restore the original map and delete the fixtures.
"""
import argparse
import json
import time
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'landscape.json'
MAP = '/Game/UE5MCP_Test/MCP_Landscape'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
D = '/Game/UE5MCP_Test/'
LIVE = {'bConfirm': True, 'bDryRun': False}
PHYS = '/Engine/EngineMaterials/DefaultPhysicalMaterial.DefaultPhysicalMaterial'
TEX = '/Engine/EngineResources/DefaultTexture.DefaultTexture'
LI = None
VOLATILE = ('scope', 'package_dirty')
RECT = {'X': 10, 'Y': 12, 'Width': 4, 'Height': 3}


def use_tag(tag):
    global LI
    LI = f'{D}LI_MCP_Grass_{tag}.LI_MCP_Grass_{tag}'


def strip(d):
    return {k: v for k, v in d.items() if k not in VOLATILE}


def actor(api):
    return api.call('POST', '/landscapes/inspect', {})['landscape_proxies'][0]['actor_path']


def layers(api):
    return api.call('POST', '/landscapes/edit-layers/inspect', {'ActorPath': actor(api), 'Count': 64})['edit_layers']


def layer(api, name):
    return next(l for l in layers(api) if l['name'] == name)


def lref(api, name):
    l = layer(api, name)
    return {'ActorPath': actor(api), 'EditLayerGuid': l['guid'], 'EditLayerPath': l['edit_layer_path']}


def order(api):
    return [l['guid'] for l in layers(api)]


def full(api):
    a = actor(api)
    out = {'proxies': [strip(p) for p in api.call('POST', '/landscapes/inspect', {})['landscape_proxies']],
           'edit_layers': [strip(l) for l in layers(api)],
           'heights': strip(api.call('POST', '/landscapes/heights/inspect', {'ActorPath': a, **RECT})),
           'weights': strip(api.call('POST', '/landscapes/weights/inspect', {'ActorPath': a, 'LayerInfoPath': LI, **RECT})),
           'paint': strip(api.call('POST', '/landscapes/paint-layers/inspect', {'ActorPath': a, 'Count': 16})),
           'layer_info': strip(api.call('POST', '/landscapes/layer-info/inspect', {'LayerInfoPath': LI}))}
    for l in layers(api):
        ref = {'ActorPath': a, 'EditLayerGuid': l['guid'], 'EditLayerPath': l['edit_layer_path'], **RECT}
        out['h_' + l['name']] = strip(api.call('POST', '/landscapes/edit-layers/heights/inspect', ref))
        out['w_' + l['name']] = strip(api.call('POST', '/landscapes/edit-layers/weights/inspect', {**ref, 'LayerInfoPath': LI}))
    return out


def settled(api):
    """Edit-layer merges finish on a later editor tick."""
    prev = full(api)
    for _ in range(30):
        time.sleep(0.3)
        cur = full(api)
        if cur == prev:
            return cur
        prev = cur
    raise AssertionError('landscape state did not settle')


def edit(api, route, body, check, undo=False, stale=None):
    before = settled(api)
    d = api.call('POST', route, {**body, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, d)
    assert settled(api) == before, (route, body, 'dry run changed the landscape')
    if stale:
        api.call('POST', route, {**body, **stale, **LIVE}, ok=False)
    api.call('POST', route, {**body, **LIVE})
    after = settled(api)
    assert check(before, after), (route, body, json.dumps({k: after[k] for k in after if k not in before or after[k] != before[k]})[:1500])
    if undo:
        api.undo()
        u = settled(api)
        assert u == before, (route, body, 'undo did not restore', [k for k in u if u[k] != before.get(k)])
        api.redo()
        r = settled(api)
        assert r == after, (route, body, 'redo did not reapply', [k for k in r if r[k] != after.get(k)])
    return after


def create_stage(api):
    body = {'Name': 'MCP_Land', 'Width': 2, 'Height': 2, 'Value': 32768, 'LayerInfoPath': LI, 'FieldName': 'Grass'}
    d = api.call('POST', '/landscapes/create', {**body, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and not d['actor_path'] and not api.call('POST', '/landscapes/inspect', {})['landscape_proxies'], d
    api.call('POST', '/landscapes/create', {**body, 'Name': 'bad name', **LIVE}, ok=False)
    api.call('POST', '/landscapes/create', {**body, 'Width': 9, **LIVE}, ok=False)
    d = api.call('POST', '/landscapes/create', {**body, **LIVE})
    assert d['component_count'] == 4 and d['size_x'] == 63 and d['layer_info_path'] == LI, d
    api.call('POST', '/landscapes/create', {**body, 'LayerInfoPath': '', **LIVE}, ok=False)
    p = api.call('POST', '/landscapes/inspect', {})['landscape_proxies']
    assert len(p) == 1 and p[0]['label'] == 'MCP_Land' and p[0]['component_count'] == 4, p
    comps = api.call('POST', '/landscapes/components/inspect', {'ActorPath': actor(api), 'Count': 2})
    assert comps['component_count'] == 4 and comps['has_more'] and len(comps['components']) == 2, comps
    h = api.call('POST', '/landscapes/heights/inspect', {'ActorPath': actor(api), **RECT})
    assert all(v == 32768 for row in h['raw_height_rows'] for v in row), h
    paint = api.call('POST', '/landscapes/paint-layers/inspect', {'ActorPath': actor(api)})['paint_layers']
    assert [(x['name'], x['layer_info_path'], x['valid_layer_info']) for x in paint] == [('Grass', LI, True)], paint


def edit_layer_stage(api):
    base = layers(api)[0]['name']
    d = api.call('POST', '/landscapes/edit-layers/create', {'ActorPath': actor(api), 'Name': 'MCP_Edit', 'ExpectedLayerOrder': order(api), 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and len(layers(api)) == 1, d
    edit(api, '/landscapes/edit-layers/create', {'ActorPath': actor(api), 'Name': 'MCP_Edit', 'ExpectedLayerOrder': order(api)},
         lambda b, a: [l['name'] for l in a['edit_layers']] == [base, 'MCP_Edit'], undo=True, stale={'ExpectedLayerOrder': []})
    api.call('POST', '/landscapes/edit-layers/create', {'ActorPath': actor(api), 'Name': 'MCP_Edit', 'ExpectedLayerOrder': order(api), **LIVE}, ok=False)
    api.call('POST', '/landscapes/edit-layers/create', {'ActorPath': actor(api), 'Name': 'MCP_Spare', 'ExpectedLayerOrder': order(api), **LIVE})
    edit(api, '/landscapes/edit-layers/rename', {**lref(api, 'MCP_Spare'), 'ExpectedName': 'MCP_Spare', 'Name': 'MCP_Spare2'},
         lambda b, a: 'MCP_Spare2' in [l['name'] for l in a['edit_layers']], undo=True, stale={'ExpectedName': 'Other'})
    edit(api, '/landscapes/edit-layers/reorder', {**lref(api, 'MCP_Spare2'), 'ExpectedLayerOrder': order(api), 'DestinationIndex': 0},
         lambda b, a: a['edit_layers'][0]['name'] == 'MCP_Spare2', undo=True, stale={'ExpectedLayerOrder': list(reversed(order(api)))})
    for field, key in (('Visible', 'visible'), ('Locked', 'locked')):
        cur = layer(api, 'MCP_Spare2')[key]
        edit(api, '/landscapes/edit-layers/bool', {**lref(api, 'MCP_Spare2'), 'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur},
             lambda b, a, key=key, cur=cur: next(l for l in a['edit_layers'] if l['name'] == 'MCP_Spare2')[key] is (not cur), undo=field == 'Visible', stale={'bExpectedValue': not cur})
    # A locked layer refuses alpha edits; unlock first.
    api.call('POST', '/landscapes/edit-layers/alpha', {**lref(api, 'MCP_Spare2'), 'FieldName': 'Heightmap', 'ExpectedValue': 1, 'Value': 0.5, **LIVE}, ok=False)
    api.call('POST', '/landscapes/edit-layers/bool', {**lref(api, 'MCP_Spare2'), 'FieldName': 'Locked', 'bExpectedValue': True, 'bValue': False, **LIVE})
    alpha = lambda a, i: next(l for l in a['edit_layers'] if l['name'] == 'MCP_Spare2')['targets'][i]['alpha']
    edit(api, '/landscapes/edit-layers/alpha', {**lref(api, 'MCP_Spare2'), 'FieldName': 'Heightmap', 'ExpectedValue': 1, 'Value': -0.5},
         lambda b, a: alpha(a, 0) == -0.5, undo=True, stale={'ExpectedValue': 0.25})
    edit(api, '/landscapes/edit-layers/alpha', {**lref(api, 'MCP_Spare2'), 'FieldName': 'Weightmap', 'ExpectedValue': 1, 'Value': 0.25}, lambda b, a: alpha(a, 1) == 0.25)
    api.call('POST', '/landscapes/edit-layers/alpha', {**lref(api, 'MCP_Spare2'), 'FieldName': 'Weightmap', 'ExpectedValue': 0.25, 'Value': -1, **LIVE}, ok=False)
    edit(api, '/landscapes/edit-layers/delete', {**lref(api, 'MCP_Spare2'), 'ExpectedName': 'MCP_Spare2', 'ExpectedLayerOrder': order(api)},
         lambda b, a: [l['name'] for l in a['edit_layers']] == [base, 'MCP_Edit'], undo=True, stale={'ExpectedName': 'Other'})


def patch_stage(api):
    n = RECT['Width'] * RECT['Height']
    ref = lref(api, 'MCP_Edit')
    cur_h = api.call('POST', '/landscapes/edit-layers/heights/inspect', {**ref, **RECT})
    flat = lambda rows: [v for row in rows for v in row]
    expected = flat(cur_h['raw_height_rows'])
    heights = [32768 + 256 * (i + 1) for i in range(n)]
    edit(api, '/landscapes/edit-layers/heights', {**ref, **RECT, 'ExpectedHeights': expected, 'Heights': heights},
         # Edit-layer data is asserted per layer: the merge into the combined heightmap runs on the GPU (absent under -nullrhi).
         lambda b, a: flat(a['h_MCP_Edit']['raw_height_rows']) == heights,
         undo=True, stale={'ExpectedHeights': heights})
    api.call('POST', '/landscapes/edit-layers/heights', {**ref, **RECT, 'ExpectedHeights': heights, 'Heights': [70000] * n, **LIVE}, ok=False)
    cur_w = api.call('POST', '/landscapes/edit-layers/weights/inspect', {**ref, **RECT, 'LayerInfoPath': LI})
    rows = cur_w.get('weight_rows', cur_w.get('raw_weight_rows'))
    weights = [min(255, 40 * (i % 7)) for i in range(n)]
    edit(api, '/landscapes/edit-layers/weights', {**ref, **RECT, 'LayerInfoPath': LI, 'ExpectedWeights': flat(rows), 'Weights': weights},
         lambda b, a: flat(a['w_MCP_Edit'].get('weight_rows', a['w_MCP_Edit'].get('raw_weight_rows'))) == weights, undo=True, stale={'ExpectedWeights': weights})
    api.call('POST', '/landscapes/edit-layers/weights', {**ref, **RECT, 'LayerInfoPath': LI, 'ExpectedWeights': weights, 'Weights': [300] * n, **LIVE}, ok=False)


def layer_info_stage(api):
    info = lambda a: a['layer_info']
    li = api.call('POST', '/landscapes/layer-info/inspect', {'LayerInfoPath': LI})
    edit(api, '/landscapes/layer-info/blend', {'LayerInfoPath': LI, 'ExpectedBlendMethod': li['blend_method'], 'ExpectedBlendGroup': li['blend_group'],
                                               'BlendMethod': 2, 'BlendGroup': 'MCPGroup'},
         lambda b, a: info(a)['blend_method'] == 2 and info(a)['blend_group'] == 'MCPGroup', undo=True, stale={'ExpectedBlendMethod': 1})
    for field, key, value in (('Hardness', 'hardness', 0.5), ('MinimumCollisionRelevanceWeight', 'minimum_collision_relevance_weight', 0.25),
                              ('SplineFalloffModulationTiling', 'spline_falloff_tiling', 2), ('SplineFalloffModulationBias', 'spline_falloff_bias', 0.25),
                              ('SplineFalloffModulationScale', 'spline_falloff_scale', 3)):
        cur = api.call('POST', '/landscapes/layer-info/inspect', {'LayerInfoPath': LI})[key]
        edit(api, '/landscapes/layer-info/scalar', {'LayerInfoPath': LI, 'FieldName': field, 'ExpectedValue': cur, 'Value': value},
             lambda b, a, key=key, value=value: abs(info(a)[key] - value) < 1e-6, undo=field == 'Hardness', stale={'ExpectedValue': cur + 1})
    api.call('POST', '/landscapes/layer-info/scalar', {'LayerInfoPath': LI, 'FieldName': 'Hardness', 'ExpectedValue': 0.5, 'Value': 5, **LIVE}, ok=False)
    edit(api, '/landscapes/layer-info/asset', {'LayerInfoPath': LI, 'FieldName': 'PhysicalMaterial', 'ExpectedAssetPath': '', 'AssetPath': PHYS},
         lambda b, a: info(a)['physical_material_path'] == PHYS, undo=True, stale={'ExpectedAssetPath': PHYS})
    edit(api, '/landscapes/layer-info/asset', {'LayerInfoPath': LI, 'FieldName': 'SplineFalloffModulationTexture', 'ExpectedAssetPath': '', 'AssetPath': TEX},
         lambda b, a: info(a)['spline_falloff_texture_path'] == TEX)
    api.call('POST', '/landscapes/layer-info/asset', {'LayerInfoPath': LI, 'FieldName': 'PhysicalMaterial', 'ExpectedAssetPath': PHYS, 'AssetPath': TEX, **LIVE}, ok=False)
    color = info(settled(api))['debug_color_rgba']
    edit(api, '/landscapes/layer-info/debug-color', {'LayerInfoPath': LI, 'ExpectedColor': color, 'Color': [0.1, 0.2, 0.3, 1]},
         lambda b, a: [round(v, 4) for v in info(a)['debug_color_rgba']] == [0.1, 0.2, 0.3, 1], undo=True, stale={'ExpectedColor': [0, 0, 0, 1]})
    edit(api, '/landscapes/layer-info/spline-mask', {'LayerInfoPath': LI, 'ExpectedValue': 0, 'Value': 2}, lambda b, a: info(a)['spline_falloff_color_mask'] == 2,
         undo=True, stale={'ExpectedValue': 3})
    api.call('POST', '/landscapes/layer-info/spline-mask', {'LayerInfoPath': LI, 'ExpectedValue': 2, 'Value': 7, **LIVE}, ok=False)


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    original = api.call('GET', '/worlds/inspect')['world_path']
    if original.startswith(MAP):
        original = json.loads(STATE.read_text(encoding='utf-8')).get('original', FALLBACK) if STATE.exists() else FALLBACK
        original = FALLBACK if original.startswith(MAP) else original
        assert api.call('POST', '/worlds/load', {'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'original': original, 'tag': tag}), encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    # Everything below edits the open world; never continue unless it is the scratch map.
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    create_stage(api)
    edit_layer_stage(api)
    patch_stage(api)
    layer_info_stage(api)
    api.call('POST', '/assets/save', {'AssetPath': LI})
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'tag': tag, 'snapshot': settled(api)}), encoding='utf-8')
    print('prepared landscape authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        api.call('GET', '/assets/describe', params={'asset_path': LI})
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = settled(api)
        bad = [k for k in state['snapshot'] if state['snapshot'][k] != cold.get(k)]
        assert not bad, [(k, json.dumps(state['snapshot'][k])[:500], json.dumps(cold.get(k))[:500]) for k in bad[:3]]
        print('Cold reload of landscape, edit layers, height/weight patches, paint layer and layer-info settings: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    if LI:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': LI}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned landscape test map and layer info')


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
