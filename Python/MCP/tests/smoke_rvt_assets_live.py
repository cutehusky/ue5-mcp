"""Live runtime-virtual-texture asset authoring: RVT assets, a virtual-texture builder, an RVT sample expression in a
scratch material and RVT overrides in a scratch material instance.

prepare: create an RVT (dry run first) and edit every policy flag, tile size code, custom priority, material layout,
LOD group and custom material data with snapshot/value guards, dry runs and undo/redo; duplicate it; create a
builder and check the mobile-policy refusal; duplicate a project material and instance into the scratch folder, add a
RuntimeVirtualTextureSampleParameter, assign/synchronize the RVT and edit every sample policy; discover declarations,
create/set/remove local instance overrides and read effective values and override consumers; save and snapshot.
verify (fresh editor): load the assets, compare RVT/builder/sample/instance snapshots, then delete.
"""
import argparse
import json
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'rvt_assets.json'
D = '/Game/UE5MCP_Test/'
SRC_MATERIAL = '/Game/LevelPrototyping/Interactable/JumpPad/Assets/Materials/M_SimpleGlow'
SRC_INSTANCE = '/Game/LevelPrototyping/Interactable/JumpPad/Assets/Materials/MI_GlowNT'
SAMPLE_CLASS = '/Script/Engine.MaterialExpressionRuntimeVirtualTextureSampleParameter'
RVT_CLASS = '/Script/Engine.RuntimeVirtualTexture'
LIVE = {'bConfirm': True, 'bDryRun': False}
RVT = DUP = VTB = MAT = MI = None


def use_tag(tag):
    global RVT, DUP, VTB, MAT, MI
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    RVT, DUP, VTB, MAT, MI = n('RVT_MCP'), n('RVT_MCP_Dup'), n('VTB_MCP'), n('M_MCP_Rvt'), n('MI_MCP_Rvt')


def assets():
    return (RVT, DUP, VTB, MAT, MI)


def rvt(api, path=None):
    return api.call('POST', '/runtime-virtual-textures/inspect', {'AssetPath': path or RVT})


def texts(d):
    return json.loads(d['native_authored_snapshot'])


def numeric(setting):
    """Native text of a setting as the integer the setters take."""
    text = setting['native_text']
    if 'enum_values' in setting:
        return next(e['value'] for e in setting['enum_values'] if e['name'] == text or text.endswith('::' + e['name']))
    return {'True': 1, 'False': 0}.get(text, None) if text in ('True', 'False') else float(text)


def setting(d, name):
    return next(s for s in d['settings'] if s['name'] == name)


def edit_asset(api, route, body, expect, undo=False):
    """Dry run, stale-snapshot refusal, real edit; expect maps snapshot field -> native text afterwards."""
    before = rvt(api)
    g = {'AssetPath': RVT, 'ExpectedClassPath': RVT_CLASS}
    d = api.call('POST', route, {**g, **body, 'ExpectedAssetSnapshot': before['native_authored_snapshot'], 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and d['would_change'], (route, body, d)
    assert rvt(api)['native_authored_snapshot'] == before['native_authored_snapshot'], (route, 'dry run changed state')
    api.call('POST', route, {**g, **body, 'ExpectedAssetSnapshot': before['native_authored_snapshot'] + ' ', **LIVE}, ok=False)
    api.call('POST', route, {**g, **body, 'ExpectedAssetSnapshot': before['native_authored_snapshot'], **LIVE})
    after = rvt(api)
    for k, v in expect.items():
        assert texts(after)[k] == v, (route, body, k, texts(after)[k], v)
    if undo:
        api.undo()
        assert rvt(api)['native_authored_snapshot'] == before['native_authored_snapshot'], (route, 'undo')
        api.redo()
        assert rvt(api)['native_authored_snapshot'] == after['native_authored_snapshot'], (route, 'redo')
    return after


def rvt_stage(api):
    d = api.call('POST', '/runtime-virtual-textures/create', {'AssetPath': RVT, 'bConfirm': True, 'bDryRun': True})
    assert not d['created'] and d['dry_run'], d
    api.call('POST', '/runtime-virtual-textures/inspect', {'AssetPath': RVT}, ok=False)
    d = api.call('POST', '/runtime-virtual-textures/create', {'AssetPath': RVT, **LIVE})
    assert d['created'] and d['class_path'] == RVT_CLASS, d
    api.call('POST', '/runtime-virtual-textures/create', {'AssetPath': RVT, **LIVE}, ok=False)
    # Policy flags (bUseCustomPriority first: it gates CustomPriority).
    first = True
    for name in ('bUseCustomPriority', 'bClearTextures', 'bSinglePhysicalSpace', 'bPrivateSpace', 'bContinuousUpdate', 'bAdaptive', 'bCompressTextures'):
        cur = numeric(setting(rvt(api), name))
        edit_asset(api, '/runtime-virtual-textures/policy', {'FieldName': name, 'Value': 1 - cur, 'ExpectedValue': cur}, {name: 'False' if cur else 'True'}, undo=first)
        first = False
    edit_asset(api, '/runtime-virtual-textures/policy', {'FieldName': 'RemoveLowMips', 'Value': 2, 'ExpectedValue': 0}, {'RemoveLowMips': '2'})
    api.call('POST', '/runtime-virtual-textures/policy', {'AssetPath': RVT, 'ExpectedClassPath': RVT_CLASS, 'FieldName': 'RemoveLowMips', 'Value': 9, 'ExpectedValue': 2,
                                                          'ExpectedAssetSnapshot': rvt(api)['native_authored_snapshot'], **LIVE}, ok=False)
    # Encoded tile sizes.
    for name, value in (('TileCount', 7), ('TileSize', 3), ('TileBorderSize', 1)):
        cur = int(numeric(setting(rvt(api), name)))
        edit_asset(api, '/runtime-virtual-textures/size', {'FieldName': name, 'Value': value, 'ExpectedValue': cur}, {name: str(value)}, undo=name == 'TileCount')
    api.call('POST', '/runtime-virtual-textures/size', {'AssetPath': RVT, 'ExpectedClassPath': RVT_CLASS, 'FieldName': 'TileSize', 'Value': 9, 'ExpectedValue': 3,
                                                        'ExpectedAssetSnapshot': rvt(api)['native_authored_snapshot'], **LIVE}, ok=False)
    edit_asset(api, '/runtime-virtual-textures/priority', {'FieldName': 'CustomPriority', 'Value': 6, 'ExpectedValue': 0}, {'CustomPriority': 'High'}, undo=True)
    # Layout: BaseColor_Normal_Roughness enables the low-quality compression flag once compression is back on.
    edit_asset(api, '/runtime-virtual-textures/layout', {'FieldName': 'MaterialType', 'Value': 2, 'ExpectedValue': 3}, {'MaterialType': 'BaseColor_Normal_Roughness'}, undo=True)
    group = setting(rvt(api), 'LODGroup')
    want = next(e['value'] for e in group['enum_values'] if e['name'] == 'TEXTUREGROUP_Terrain_Heightmap')
    edit_asset(api, '/runtime-virtual-textures/layout', {'FieldName': 'LODGroup', 'Value': want, 'ExpectedValue': numeric(group)}, {'LODGroup': 'TEXTUREGROUP_Terrain_Heightmap'})
    edit_asset(api, '/runtime-virtual-textures/policy', {'FieldName': 'bCompressTextures', 'Value': 1, 'ExpectedValue': 0}, {'bCompressTextures': 'True'})
    edit_asset(api, '/runtime-virtual-textures/policy', {'FieldName': 'bUseLowQualityCompression', 'Value': 1, 'ExpectedValue': 0}, {'bUseLowQualityCompression': 'True'})
    edit_asset(api, '/runtime-virtual-textures/material-data', {'Color': [0.25, 0.5, 1, 2], 'ExpectedColor': [0, 0, 0, 0]},
               {'CustomMaterialData': '(X=0.250000,Y=0.500000,Z=1.000000,W=2.000000)'}, undo=True)
    layers = api.call('POST', '/runtime-virtual-textures/layers/inspect', {'AssetPath': RVT})
    assert layers['material_type'] == 2 and layers['layer_count'] == 2, layers
    # Duplicate.
    snap = rvt(api)['native_authored_snapshot']
    d = api.call('POST', '/runtime-virtual-textures/duplicate', {'AssetPath': DUP, 'SourceTexturePath': RVT, 'ExpectedClassPath': RVT_CLASS, 'ExpectedAssetSnapshot': snap, 'bConfirm': True, 'bDryRun': True})
    assert not d['duplicated'], d
    api.call('POST', '/runtime-virtual-textures/duplicate', {'AssetPath': DUP, 'SourceTexturePath': RVT, 'ExpectedClassPath': RVT_CLASS, 'ExpectedAssetSnapshot': snap, **LIVE})
    a, b = texts(rvt(api)), texts(rvt(api, DUP))
    assert a == b, (a, b)
    page = api.call('POST', '/runtime-virtual-textures/inspect-page', {'PathFilter': RVT.rsplit('_', 1)[1].split('.')[0], 'Count': 8})
    assert sorted(x['asset_path'] for x in page['assets']) == sorted([RVT, DUP]), page


def builder_stage(api):
    d = api.call('POST', '/virtual-texture-builders/create', {'AssetPath': VTB, 'bConfirm': True, 'bDryRun': True})
    assert not d['created'], d
    api.call('POST', '/virtual-texture-builders/create', {'AssetPath': VTB, **LIVE})
    b = api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})
    assert b['class_path'] == '/Script/Engine.VirtualTextureBuilder' and not b['separate_texture_for_mobile'], b
    page = api.call('POST', '/virtual-texture-builders/inspect-page', {'PathFilter': VTB.rsplit('.', 1)[1], 'Count': 8})
    assert [x['asset_path'] for x in page.get('builders', page.get('assets', []))] == [VTB], page
    comps = api.call('POST', '/virtual-texture-builders/components/inspect-page', {'AssetPath': VTB, 'Count': 8})
    assert json.dumps(comps).count('component_path') == 0, comps
    # The mobile split needs the project's mobile virtual-texturing setting (enabled in DefaultEngine.ini for this verification).
    body = {'AssetPath': VTB, 'ExpectedClassPath': b['class_path'], 'ExpectedSourceId': b['build_hash_decimal'], 'ExpectedSourcePaths': ['None', 'None'],
            'Value': 1, 'ExpectedValue': 0, **LIVE}
    api.call('POST', '/virtual-texture-builders/mobile-policy', {**body, 'ExpectedValue': 1}, ok=False)
    api.call('POST', '/virtual-texture-builders/mobile-policy', {**body, 'ExpectedSourceId': '1'}, ok=False)
    api.call('POST', '/virtual-texture-builders/mobile-policy', {**body, 'bDryRun': True})
    assert not api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})['separate_texture_for_mobile']
    api.call('POST', '/virtual-texture-builders/mobile-policy', body)
    assert api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})['separate_texture_for_mobile']


def sample(api):
    return api.call('POST', '/runtime-virtual-textures/expressions/inspect', {'ExpressionPath': MAT + ':RVTSample', 'OwnerAssetPath': MAT})


def sample_stage(api):
    pkg = lambda p: p.split('.')[0]
    for src, dst in ((SRC_MATERIAL, MAT), (SRC_INSTANCE, MI)):
        r = httpx.post(api.base + '/assets/duplicate', json={'AssetPath': src, 'DestinationPath': pkg(dst)}, timeout=180)
        assert r.is_success and r.text.strip().strip('"') == dst, r.text
    r = httpx.post(api.base + '/materials/expressions', json={'AssetPath': MAT, 'ExpressionClass': SAMPLE_CLASS, 'ExpressionName': 'RVTSample', 'NodePosX': -400}, timeout=180)
    assert r.is_success, r.text
    r = httpx.patch(api.base + '/material-instances/parent', json={'AssetPath': MI, 'ParentPath': MAT}, timeout=180)
    assert r.is_success, r.text
    s = sample(api)
    g = {'ExpressionPath': s['expression_path'], 'OwnerAssetPath': MAT, 'ExpectedClassPath': SAMPLE_CLASS, 'ExpressionGuid': s['expression_guid']}
    rs = rvt(api)['native_authored_snapshot']
    ref = {**g, 'ExpectedChannels': s['type_packed_adaptive'], 'AssetPath': RVT, 'ExpectedTargetPath': 'None', 'ExpectedRuntimeTextureSnapshot': rs}
    d = api.call('POST', '/runtime-virtual-textures/expressions/reference', {**ref, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and sample(api)['native_authored_snapshot'] == s['native_authored_snapshot'], d
    api.call('POST', '/runtime-virtual-textures/expressions/reference', {**ref, 'ExpectedTargetPath': DUP, **LIVE}, ok=False)
    api.call('POST', '/runtime-virtual-textures/expressions/reference', {**ref, **LIVE})
    s2 = sample(api)
    a = texts(s2)
    # Assigning the RVT synchronizes the sample's type/packed/adaptive flags to the asset (layout 2, adaptive on).
    assert a['runtime_vt_path'] == RVT and s2['type_packed_adaptive'] == [2, int(texts(rvt(api))['bSinglePhysicalSpace'] == 'True'), int(texts(rvt(api))['bAdaptive'] == 'True')], (a, s2['type_packed_adaptive'])
    api.undo()
    assert sample(api)['native_authored_snapshot'] == s['native_authored_snapshot'], 'reference undo'
    api.redo()
    assert sample(api)['native_authored_snapshot'] == s2['native_authored_snapshot'], 'reference redo'
    d = api.call('POST', '/runtime-virtual-textures/expressions/synchronize', {**g, 'ExpectedChannels': s2['type_packed_adaptive'], 'AssetPath': RVT, 'ExpectedRuntimeTextureSnapshot': rs, **LIVE})
    assert d['would_change'] is False, d
    api.call('POST', '/runtime-virtual-textures/expressions/synchronize', {**g, 'ExpectedChannels': [0, 0, 0], 'AssetPath': RVT, 'ExpectedRuntimeTextureSnapshot': rs, **LIVE}, ok=False)
    for name in ('bEnableFeedback', 'WorldPositionOriginType', 'TextureAddressMode', 'MipValueMode'):
        cur = sample(api)
        st = setting(cur, name)
        v = numeric(st)
        if 'enum_values' in st:
            opts = [e['value'] for e in st['enum_values'] if not e['hidden'] and not e['name'].endswith('MAX') and e['name'] != 'Count']
            new = opts[(opts.index(v) + 1) % len(opts)]
        else:
            new = 1 - v
        body = {**g, 'FieldName': name, 'Value': new, 'ExpectedValue': v, 'ExpectedAssetSnapshot': cur['native_authored_snapshot']}
        if not st['native_can_edit']:
            # bEnableFeedback is locked natively while the (synchronized) sample is adaptive.
            assert name == 'bEnableFeedback' and texts(cur)['bAdaptive'] == 'True', (name, texts(cur))
            assert 'Native editable bool/enum policy required' in api.call('POST', '/runtime-virtual-textures/expressions/policy', {**body, **LIVE}, ok=False)
            continue
        d = api.call('POST', '/runtime-virtual-textures/expressions/policy', {**body, 'bConfirm': True, 'bDryRun': True})
        assert d['would_change'] and sample(api)['native_authored_snapshot'] == cur['native_authored_snapshot'], d
        api.call('POST', '/runtime-virtual-textures/expressions/policy', {**body, 'ExpectedValue': v + 1, **LIVE}, ok=False)
        api.call('POST', '/runtime-virtual-textures/expressions/policy', {**body, **LIVE})
        assert numeric(setting(sample(api), name)) == new, (name, new)
    refs = api.call('POST', '/runtime-virtual-textures/expressions/inspect-page', {'AssetPath': RVT, 'Count': 8})
    assert [e['expression_path'] for e in refs['expressions']] == [s['expression_path']] and refs['expressions'][0]['matches_asset_material_type'], refs


def overrides(api):
    return api.call('POST', '/runtime-virtual-textures/instance-parameters/inspect-page', {'OwnerAssetPath': MI, 'Count': 8})


def instance_stage(api):
    decl = api.call('POST', '/runtime-virtual-textures/instance-parameters/declarations/inspect-page', {'OwnerAssetPath': MI, 'Count': 8})
    assert decl['declaration_count'] == 1, decl
    dc = decl['declarations'][0]
    ov = overrides(api)
    create = {'OwnerAssetPath': MI, 'AssetPath': RVT, 'ExpectedClassPath': ov['class_path'], 'ExpectedAssetSnapshot': ov['native_override_snapshot'],
              'Start': dc['native_declaration_index'], 'ExpressionGuid': dc['parameter_guid'], 'Name': dc['parameter_name'],
              'ParameterAssociation': dc['association'], 'ParameterIndex': dc['layer_index']}
    d = api.call('POST', '/runtime-virtual-textures/instance-parameters/create', {**create, 'bConfirm': True, 'bDryRun': True})
    assert d['would_change'] and overrides(api)['override_count'] == 0, d
    api.call('POST', '/runtime-virtual-textures/instance-parameters/create', {**create, 'Name': 'Other', **LIVE}, ok=False)
    api.call('POST', '/runtime-virtual-textures/instance-parameters/create', {**create, **LIVE})
    ov = overrides(api)
    assert ov['override_count'] == 1 and json.loads(ov['native_override_snapshot'])['overrides'][0]['value_path'] == RVT, ov
    api.call('POST', '/runtime-virtual-textures/instance-parameters/create', {**create, 'ExpectedAssetSnapshot': ov['native_override_snapshot'], **LIVE}, ok=False)
    o = json.loads(ov['native_override_snapshot'])['overrides'][0]
    sel = {'OwnerAssetPath': MI, 'ExpectedClassPath': ov['class_path'], 'Start': 0, 'ExpressionGuid': o['expression_guid']}
    setb = {**sel, 'AssetPath': DUP, 'ExpectedTargetPath': RVT, 'ExpectedAssetSnapshot': ov['native_override_snapshot']}
    d = api.call('POST', '/runtime-virtual-textures/instance-parameters/set', {**setb, 'bConfirm': True, 'bDryRun': True})
    assert d['would_change'] and overrides(api)['native_override_snapshot'] == ov['native_override_snapshot'], d
    api.call('POST', '/runtime-virtual-textures/instance-parameters/set', {**setb, 'ExpectedTargetPath': DUP, **LIVE}, ok=False)
    api.call('POST', '/runtime-virtual-textures/instance-parameters/set', {**setb, **LIVE})
    ov2 = overrides(api)
    assert json.loads(ov2['native_override_snapshot'])['overrides'][0]['value_path'] == DUP, ov2
    api.undo()
    assert overrides(api)['native_override_snapshot'] == ov['native_override_snapshot'], 'set undo'
    api.redo()
    rem = {**sel, 'ExpectedTargetPath': DUP, 'ExpectedAssetSnapshot': ov2['native_override_snapshot']}
    d = api.call('POST', '/runtime-virtual-textures/instance-parameters/remove', {**rem, 'bConfirm': True, 'bDryRun': True})
    assert d['would_change'] and overrides(api)['override_count'] == 1, d
    api.call('POST', '/runtime-virtual-textures/instance-parameters/remove', {**rem, **LIVE})
    assert overrides(api)['override_count'] == 0
    api.undo()
    assert overrides(api)['native_override_snapshot'] == ov2['native_override_snapshot'], 'remove undo'
    eff = api.call('POST', '/runtime-virtual-textures/instance-parameters/effective/inspect-page', {'OwnerAssetPath': MI, 'Count': 8})
    assert eff['declarations'][0]['effective_runtime_texture_path'] == DUP and eff['declarations'][0]['local_override_count'] == 1, eff
    cons = api.call('POST', '/runtime-virtual-textures/material-overrides/inspect-page', {'AssetPath': DUP, 'Count': 8})
    assert [o['material_instance_path'] for o in cons['overrides']] == [MI], cons
    assert api.call('POST', '/runtime-virtual-textures/material-overrides/inspect-page', {'AssetPath': RVT, 'Count': 8})['matching_override_count'] == 0


def snapshot(api):
    drop = lambda d: {k: v for k, v in d.items() if k not in ('scope', 'package_dirty')}
    return {
        'rvt': drop(rvt(api)), 'dup': drop(rvt(api, DUP)),
        'layers': drop(api.call('POST', '/runtime-virtual-textures/layers/inspect', {'AssetPath': RVT})),
        'builder': drop(api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})),
        'sample': drop(sample(api)),
        'overrides': drop(overrides(api)),
        'effective': drop(api.call('POST', '/runtime-virtual-textures/instance-parameters/effective/inspect-page', {'OwnerAssetPath': MI, 'Count': 8})),
    }


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'tag': tag}), encoding='utf-8')
    rvt_stage(api)
    builder_stage(api)
    sample_stage(api)
    instance_stage(api)
    for p in assets():
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'tag': tag, 'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared runtime-VT asset authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in assets():
            api.call('GET', '/assets/describe', params={'asset_path': p})
        cold = snapshot(api)
        for k in state['snapshot']:
            assert state['snapshot'][k] == cold[k], (k, json.dumps(state['snapshot'][k])[:900], json.dumps(cold[k])[:900])
        print('Cold reload of runtime-VT assets, duplicate, builder, material sample and instance overrides: OK')
    finally:
        cleanup(api)


def cleanup(api):
    if STATE.exists() and not RVT:
        use_tag(json.loads(STATE.read_text(encoding='utf-8')).get('tag', 'none'))
    for p in (MI, MAT, DUP, RVT, VTB):
        if p:
            httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned runtime-VT asset test assets')


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
