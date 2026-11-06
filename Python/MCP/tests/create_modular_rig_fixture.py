"""Create a temporary UE 5.7 Modular Rig for API smoke tests."""

import unreal


PATH = "/Game/UE5MCP_Test/MR_MCP_Fixture"
assert not unreal.EditorAssetLibrary.does_asset_exist(PATH), PATH
asset = unreal.ControlRigBlueprintFactory.create_new_control_rig_asset(PATH, True)
assert asset, "failed to create Modular Rig"
assert unreal.EditorAssetLibrary.save_loaded_asset(asset), "failed to save Modular Rig"
print(f"Created temporary Modular Rig: {asset.get_path_name()}")
