"""Saved create_asset and import_fbx results survive an editor restart. Run through Verification/niagara_cycle.ps1."""
import json
import sys

import httpx

phase = sys.argv[1]
sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
ROOT = '/Game/UE5MCP_Test/Persist'
FBX = 'C:/Programs/Unreal/UE_5.7/Engine/Content/FbxEditorAutomation/AnimatedCharacter.fbx'


def assets():
    return [a for a in str(m.list_assets(ROOT)).replace("'", '"').split('"') if a.startswith(ROOT + '/')]


if phase == 'prepare':
    for asset in assets():
        httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': asset}, timeout=120)
    char = json.loads(m.import_fbx(FBX, f'{ROOT}/SK_Char', import_materials=False, save=True))
    assert char['saved'], char
    anim = json.loads(m.import_fbx(FBX, f'{ROOT}/A_Char', kind='animation', skeleton_path=char['skeleton'], save=True))
    assert anim['saved'], anim
    assert json.loads(m.create_asset(f'{ROOT}/M_Base', 'material', save=True))['saved']
    assert json.loads(m.create_asset(f'{ROOT}/MI_Base', 'material_instance', parent_path=f'{ROOT}/M_Base', save=True))['saved']
    assert json.loads(m.create_asset(f'{ROOT}/AM_Char', 'montage', animation_path=anim['asset_path'], save=True))['saved']
    assert json.loads(m.create_asset(f'{ROOT}/BS_Char', 'blend_space', skeleton_path=char['skeleton'], save=True))['saved']
    assert json.loads(m.create_asset(f'{ROOT}/ABP_Char', 'anim_blueprint', skeleton_path=char['skeleton'], save=True))['saved']
    print('prepared', len(assets()))
else:
    found = assets()
    print('after restart:', found)
    for name in ('SK_Char', 'SK_Char_Skeleton', 'SK_Char_PhysicsAsset', 'A_Char', 'M_Base', 'MI_Base', 'AM_Char', 'BS_Char', 'ABP_Char'):
        assert any(a.split('/')[-1].split('.')[0] == name for a in found), name
    assert f'{ROOT}/M_Base' in m.list_material_instance_parameters(f'{ROOT}/MI_Base'), 'parent lost'
    compiled = m.compile_animation_blueprint(f'{ROOT}/ABP_Char')
    assert '"valid":true' in compiled.replace(' ', ''), compiled
    for asset in sorted(found, key=lambda a: ('ABP' not in a, 'AM_' not in a, 'BS_' not in a, 'MI_' not in a, 'A_Char' not in a)):
        httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': asset}, timeout=120)
    assert not assets(), assets()
    print('Persistence verified')
