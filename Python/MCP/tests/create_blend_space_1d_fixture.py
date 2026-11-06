"""Create the temporary 1D asset used by smoke_blend_space_1d_live.py."""

import unreal


SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run"
DESTINATION = "/Game/UE5MCP_Test/BS_MCP_1D_Fixture"

assert not unreal.EditorAssetLibrary.does_asset_exist(DESTINATION), DESTINATION
source = unreal.load_asset(SOURCE)
skeleton = source.get_editor_property("skeleton")
factory = unreal.BlendSpaceFactory1D()
factory.set_editor_property("target_skeleton", skeleton)
asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "BS_MCP_1D_Fixture", "/Game/UE5MCP_Test", unreal.BlendSpace1D, factory)
assert asset, "failed to create Blend Space 1D"
assert unreal.EditorAssetLibrary.save_loaded_asset(asset), "failed to save Blend Space 1D"
print(f"Created temporary Blend Space 1D: {asset.get_path_name()}")
