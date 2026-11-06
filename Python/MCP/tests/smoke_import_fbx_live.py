"""import_fbx against the running editor, using the engine's own FBX automation files."""
import json
import sys

import httpx

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
FBX = 'C:/Programs/Unreal/UE_5.7/Engine/Content/FbxEditorAutomation/'
ROOT = '/Game/UE5MCP_Test/ImportFbx'
MANNEQUIN = '/Game/Characters/Mannequins/Meshes/SK_Mannequin'
created = set()


def imported(**kwargs):
    result = json.loads(m.import_fbx(**kwargs))
    created.update(result['created_assets'])
    return result


def refused(**kwargs):
    text = m.import_fbx(**kwargs)
    try:
        ok = 'class' in json.loads(text) and json.loads(text)['class']
    except ValueError:
        ok = False
    assert not ok, (kwargs, text)
    return text


def cleanup():
    for name in sorted(created, key=lambda p: ('Anim' not in p, 'Mesh' in p)):
        httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': name}, timeout=120)
    remaining = [a for a in str(m.list_assets(ROOT)).split('"') if a.startswith(ROOT + '/')]
    for name in remaining:
        httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': name}, timeout=120)


cleanup()
try:
    dry = imported(source_file_path=FBX + 'SkinBasic.fbx', asset_path=f'{ROOT}/SK_Dry', dry_run=True)
    assert dry['dry_run'] and not dry['created_assets'] and 'SK_Dry' not in m.list_assets(ROOT), dry

    mesh = imported(source_file_path=FBX + 'SkinBasic.fbx', asset_path=f'{ROOT}/SK_Basic', save=True)
    print('skeletal:', mesh)
    assert mesh['class'].endswith('.SkeletalMesh') and mesh['saved'] and mesh['skeleton'], mesh
    assert any('PhysicsAsset' in p for p in mesh['created_assets']), mesh

    # A mesh reusing that skeleton creates no second one.
    again = imported(source_file_path=FBX + 'SkinBasic.fbx', asset_path=f'{ROOT}/SK_Basic2', skeleton_path=mesh['skeleton'], import_materials=False)
    print('reuse:', again)
    assert again['skeleton'] == mesh['skeleton'], again

    char = imported(source_file_path=FBX + 'AnimatedCharacter.fbx', asset_path=f'{ROOT}/SK_Char', import_animations=True)
    print('with animation:', char)
    assert char['class'].endswith('.SkeletalMesh'), char
    assert any('Anim' in p and p != char['asset_path'] for p in char['created_assets']), char

    anim = imported(source_file_path=FBX + 'AnimatedCharacter.fbx', asset_path=f'{ROOT}/A_Char', kind='animation', skeleton_path=char['skeleton'])
    print('animation:', anim)
    assert anim['class'].endswith('.AnimSequence'), anim

    # The result works in the rest of the pipeline.
    made = json.loads(m.create_asset(f'{ROOT}/AM_Char', 'montage', animation_path=anim['asset_path']))
    created.add(made['asset_path'])
    abp = json.loads(m.create_asset(f'{ROOT}/ABP_Char', 'anim_blueprint', skeleton_path=char['skeleton']))
    created.add(abp['asset_path'])

    static = imported(source_file_path=FBX + 'BlenderCube.fbx', asset_path=f'{ROOT}/SM_Cube', kind='static_mesh')
    print('static:', static)
    assert static['class'].endswith('.StaticMesh'), static

    assert 'already exists' in refused(source_file_path=FBX + 'SkinBasic.fbx', asset_path=f'{ROOT}/SK_Basic')
    refused(source_file_path=FBX + 'Nope.fbx', asset_path=f'{ROOT}/X1')
    refused(source_file_path='SkinBasic.fbx', asset_path=f'{ROOT}/X1')
    refused(source_file_path=FBX + 'SkinBasic.fbx', asset_path='/Engine/X1')
    refused(source_file_path=FBX + 'SkinBasic.fbx', asset_path=f'{ROOT}/X1', kind='widget')
    refused(source_file_path=FBX + 'AnimatedCharacter.fbx', asset_path=f'{ROOT}/X1', kind='animation')
    refused(source_file_path=FBX + 'BlenderCube.fbx', asset_path=f'{ROOT}/X1', kind='static_mesh', import_animations=True)

    # An animation for the wrong skeleton must fail or be clearly reported, not hang on a dialog.
    print('wrong skeleton:', m.import_fbx(FBX + 'AnimatedCharacter.fbx', f'{ROOT}/A_Wrong', kind='animation', skeleton_path=MANNEQUIN)[:300])
    # A mesh-free or wrong-type request reports failure.
    print('static file as skeletal:', m.import_fbx(FBX + 'BlenderCube.fbx', f'{ROOT}/SK_Bad')[:300])
    print('Import FBX verified')
finally:
    cleanup()
