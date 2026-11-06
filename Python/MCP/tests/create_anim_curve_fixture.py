"""Create the temporary sequence with a float curve used by smoke_animation_curves_live.py.

The REST API has no float-curve creation route, so this commandlet script duplicates a Mannequin
sequence and adds one float curve with three keys through the engine's AnimationBlueprintLibrary.
"""

import unreal


SOURCE = "/Game/Characters/Mannequins/Anims/Pistol/Jog/MF_Pistol_Jog_Fwd"
DESTINATION = "/Game/UE5MCP_Test/AS_MCP_CurveFixture"

assert not unreal.EditorAssetLibrary.does_asset_exist(DESTINATION), DESTINATION
asset = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DESTINATION)
assert asset, "failed to duplicate sequence"
lib = unreal.AnimationLibrary
lib.add_curve(asset, "MCP_Float", unreal.RawCurveTrackTypes.RCT_FLOAT, False)
lib.add_float_curve_keys(asset, "MCP_Float", [0.0, 0.2, 0.4], [0.0, 1.0, 0.5])
assert unreal.EditorAssetLibrary.save_loaded_asset(asset), "failed to save fixture sequence"
print(f"Created curve fixture: {asset.get_path_name()}")
