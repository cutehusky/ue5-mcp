"""create_asset against the running editor: every kind, refusals, dry run, save, and real use of the created assets."""
import json
import sys

import httpx

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
ROOT = '/Game/UE5MCP_Test/CreateAsset'
SKELETON = '/Game/Characters/Mannequins/Meshes/SK_Mannequin'
ANIM = '/Game/Characters/Mannequins/Anims/Pistol/Jog/MF_Pistol_Jog_Fwd'
ROW = '/Script/GameplayTags.GameplayTagTableRow'
CASES = {
    'material': ('M_T', {}, 'Material'),
    'material_instance': ('MI_T', {'parent_path': f'{ROOT}/M_T'}, 'MaterialInstanceConstant'),
    'data_table': ('DT_T', {'struct_path': ROW}, 'DataTable'),
    'curve_float': ('C_F', {}, 'CurveFloat'),
    'curve_vector': ('C_V', {}, 'CurveVector'),
    'curve_linear_color': ('C_L', {}, 'CurveLinearColor'),
    'anim_blueprint': ('ABP_T', {'skeleton_path': SKELETON}, 'AnimBlueprint'),
    'blend_space': ('BS_T', {'skeleton_path': SKELETON}, 'BlendSpace'),
    'blend_space_1d': ('BS1_T', {'skeleton_path': SKELETON}, 'BlendSpace1D'),
    'montage': ('AM_T', {'animation_path': ANIM}, 'AnimMontage'),
    'physical_material': ('PM_T', {}, 'PhysicalMaterial'),
}


def delete(path):
    httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': path}, timeout=120)


def cleanup():
    for name, _, _ in reversed(list(CASES.values())):
        delete(f'{ROOT}/{name}')
    delete(f'{ROOT}/M_Dry')


def refused(**kwargs):
    text = m.create_asset(**kwargs)
    try:
        created = 'class' in json.loads(text)
    except ValueError:
        created = False
    assert not created, (kwargs, text)
    return text


def exists(path):
    return path in m.list_assets(ROOT)


cleanup()
try:
    assert json.loads(m.create_asset(f'{ROOT}/M_Dry', 'material', dry_run=True))['dry_run'] is True
    assert not exists(f'{ROOT}/M_Dry'), 'dry run created an asset'

    for kind, (name, extra, cls) in CASES.items():
        result = json.loads(m.create_asset(f'{ROOT}/{name}', kind, save=True, **extra))
        assert result['class'].endswith('.' + cls) and result['saved'] is True, (kind, result)
        assert exists(f'{ROOT}/{name}'), kind
        print('created', kind)

    # Refusals: overwrite, bad kind, bad path, missing or wrong inputs, inputs for another kind.
    assert 'already exists' in refused(asset_path=f'{ROOT}/M_T', kind='material')
    refused(asset_path=f'{ROOT}/X1', kind='widget')
    refused(asset_path='/Engine/X1', kind='material')
    refused(asset_path=f'{ROOT}/X1.X1', kind='material')
    refused(asset_path=f'{ROOT}/X1', kind='material_instance')
    refused(asset_path=f'{ROOT}/X1', kind='material_instance', parent_path=f'{ROOT}/DT_T')
    refused(asset_path=f'{ROOT}/X1', kind='data_table')
    refused(asset_path=f'{ROOT}/X1', kind='data_table', struct_path='/Script/CoreUObject.Vector')
    refused(asset_path=f'{ROOT}/X1', kind='anim_blueprint')
    refused(asset_path=f'{ROOT}/X1', kind='montage')
    refused(asset_path=f'{ROOT}/X1', kind='material', skeleton_path=SKELETON)
    assert not exists(f'{ROOT}/X1'), 'a refused call created an asset'

    # The assets work with the existing tools.
    assert m.get_data_table_rows(f'{ROOT}/DT_T') is not None
    row = m.upsert_data_table_row(f'{ROOT}/DT_T', 'Row1', '{"Tag":"Test.Tag"}')
    print('data table row:', row[:120])
    assert 'Row1' in m.get_data_table_rows(f'{ROOT}/DT_T'), row
    print('instance:', m.list_material_instance_parameters(f'{ROOT}/MI_T')[:120])
    compiled = m.compile_animation_blueprint(f'{ROOT}/ABP_T')
    print('anim blueprint:', compiled[:160])
    assert 'error' not in compiled.lower(), compiled
    print('Create asset verified')
finally:
    cleanup()
