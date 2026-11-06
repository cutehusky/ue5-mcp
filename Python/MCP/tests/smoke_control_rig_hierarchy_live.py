"""Exercise Control Rig hierarchy controller routes on a disposable copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body.CR_Mannequin_Body"


def main():
    name = "CR_MCP_Hierarchy_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        graphs = request("GET", "/control-rigs/graphs", params={"asset_path": asset})
        assert graphs and sum(len(graph["nodes"]) for graph in graphs) > 0, graphs
        assert not request("POST", "/control-rigs/compile", {
            "AssetPath": asset, "bDryRun": True})["compiled"]
        original = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        assert original and all("name" in item and "type" in item for item in original)
        names = {item["name"] for item in original}
        null_name = "MCP_Test_Null"
        bone_name = "MCP_Test_Bone"
        curve_name = "MCP_Test_Curve"
        control_name = "MCP_Test_Control"
        vector2d_name = "MCP_Test_Vector2D"
        rotator_name = "MCP_Test_Rotator"
        transform_name = "MCP_Test_Transform"
        enum_control_name = "MCP_Test_EnumControl"
        socket_name = "MCP_Test_Socket"
        assert not {null_name, bone_name, curve_name, control_name, vector2d_name,
                    rotator_name, transform_name, enum_control_name, socket_name} & names

        add_null = {"AssetPath": asset, "Operation": "add", "ElementType": "null",
                    "Name": null_name, "Translation": {"X": 10, "Y": 20, "Z": 30}}
        assert not request("POST", "/control-rigs/hierarchy", {
            **add_null, "bDryRun": True})["changed"]
        assert len(request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})) == len(original)
        request("POST", "/control-rigs/hierarchy", add_null)

        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "bone", "Name": bone_name,
            "ParentName": null_name, "ParentType": "null"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "curve", "Name": curve_name,
            "CurveValue": 0.75})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "control", "Name": control_name,
            "ParentName": null_name, "ParentType": "null",
            "ControlType": "float", "ControlValue": "0.25"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "control", "Name": vector2d_name,
            "ParentName": null_name, "ParentType": "null", "ControlType": "vector2d",
            "PrimaryAxis": "z", "Translation": {"X": 3, "Y": 4, "Z": 0}})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "control", "Name": rotator_name,
            "ParentName": null_name, "ParentType": "null", "ControlType": "rotator",
            "Rotation": {"Pitch": 10, "Yaw": 20, "Roll": 30}})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "control", "Name": transform_name,
            "ParentName": null_name, "ParentType": "null", "ControlType": "euler_transform",
            "Translation": {"X": 5, "Y": 6, "Z": 7},
            "Rotation": {"Pitch": 8, "Yaw": 9, "Roll": 10},
            "Scale": {"X": 1.1, "Y": 1.2, "Z": 1.3}})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "control", "Name": enum_control_name,
            "ParentName": null_name, "ParentType": "null", "ControlType": "integer",
            "ControlEnumPath": "/Script/Engine.EInputEvent", "ControlValue": "IE_Pressed"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "socket", "Name": socket_name,
            "ParentName": null_name, "ParentType": "null"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_transform", "ElementType": "null", "Name": null_name,
            "Translation": {"X": 42, "Y": 20, "Z": 30}, "bInitial": True})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_value", "ElementType": "control",
            "Name": control_name, "ControlValue": "0.75", "bInitial": True})
        limits = {"AssetPath": asset, "Operation": "set_control_limits",
                  "ElementType": "control", "Name": control_name,
                  "MinimumValue": "-1", "MaximumValue": "1"}
        assert not request("POST", "/control-rigs/hierarchy", {
            **limits, "bDryRun": True})["changed"]
        request("POST", "/control-rigs/hierarchy", {**limits,
            "MinimumValue": "2", "MaximumValue": "1"}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", limits)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_value", "ElementType": "control",
            "Name": enum_control_name, "ControlValue": "not_an_enum_member"}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_value", "ElementType": "control",
            "Name": enum_control_name, "ControlValue": "IE_MAX"}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_value", "ElementType": "control",
            "Name": enum_control_name, "ControlValue": "ie_released", "bInitial": True})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_limits", "ElementType": "control",
            "Name": enum_control_name, "MinimumValue": "0", "MaximumValue": "1"}, expect_error=True)
        vector_limits = {"AssetPath": asset, "Operation": "set_control_limits",
                         "ElementType": "control", "Name": vector2d_name,
                         "MinimumTransform": {"Translation": {"X": -5, "Y": -6, "Z": 0},
                             "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                             "Scale3D": {"X": 1, "Y": 1, "Z": 1}},
                         "MaximumTransform": {"Translation": {"X": 5, "Y": 6, "Z": 0},
                             "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                             "Scale3D": {"X": 1, "Y": 1, "Z": 1}},
                         "LimitDimensions": [1]}
        request("POST", "/control-rigs/hierarchy", {**vector_limits,
            "LimitDimensions": [2]}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", {**vector_limits,
            "MinimumTransform": {"Translation": {"X": 0, "Y": 7, "Z": 0},
                "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                "Scale3D": {"X": 1, "Y": 1, "Z": 1}},
            "MaximumTransform": {"Translation": {"X": 0, "Y": 6, "Z": 0},
                "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                "Scale3D": {"X": 1, "Y": 1, "Z": 1}}}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", vector_limits)
        transform_limits = {"AssetPath": asset, "Operation": "set_control_limits",
                            "ElementType": "control", "Name": transform_name,
                            "MinimumTransform": {"Translation": {"X": -10, "Y": -20, "Z": -30},
                                "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                                "Scale3D": {"X": 0.5, "Y": 0.5, "Z": 0.5}},
                            "MaximumTransform": {"Translation": {"X": 10, "Y": 20, "Z": 30},
                                "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                                "Scale3D": {"X": 2, "Y": 2, "Z": 2}},
                            "LimitDimensions": [0, 8]}
        request("POST", "/control-rigs/hierarchy", {**transform_limits,
            "MinimumTransform": {**transform_limits["MinimumTransform"],
                "Scale3D": {"X": 0.5, "Y": 0.5, "Z": 3}}}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", transform_limits)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_value", "ElementType": "control",
            "Name": vector2d_name,
            "Translation": {"X": 12, "Y": 2, "Z": 0}, "bInitial": True})
        current = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        added_bone = next(item for item in current if item["name"] == bone_name)
        assert added_bone["parent_name"] == null_name and added_bone["parent_type"] == "null"
        added_null = next(item for item in current if item["name"] == null_name)
        assert added_null["initial_global_transform"]["x"] == 42, added_null
        added_control = next(item for item in current if item["name"] == control_name)
        assert added_control["control_type"] == "float" and abs(added_control["initial_value"] - 0.75) < 1e-5
        assert added_control["limits"]["minimum_enabled"] and added_control["limits"]["maximum_enabled"]
        assert added_control["limits"]["minimum"] == -1 and added_control["limits"]["maximum"] == 1
        added_vector = next(item for item in current if item["name"] == vector2d_name)
        assert added_vector["control_type"] == "vector2d", added_vector
        assert added_vector["initial_value"]["translation"]["x"] == 12 and added_vector["initial_value"]["translation"]["y"] == 2, added_vector
        assert added_vector["limits"]["enabled_dimensions"] == [1], added_vector
        added_rotator = next(item for item in current if item["name"] == rotator_name)
        assert added_rotator["control_type"] == "rotator" and abs(added_rotator["initial_value"]["rotation"]["pitch"] - 10) < 1e-4, added_rotator
        added_transform = next(item for item in current if item["name"] == transform_name)
        assert added_transform["control_type"] == "euler_transform" and abs(added_transform["initial_value"]["scale"]["z"] - 1.3) < 1e-4, added_transform
        assert added_transform["limits"]["enabled_dimensions"] == [0, 8], added_transform
        added_enum = next(item for item in current if item["name"] == enum_control_name)
        assert added_enum["control_enum_path"] == "/Script/Engine.EInputEvent", added_enum
        assert added_enum["initial_value"] == 1 and added_enum["initial_enum_value"] == "IE_Released", added_enum
        assert added_enum["current_enum_value"] == "IE_Pressed", added_enum
        assert {member["name"] for member in added_enum["enum_members"]} == {
            "IE_Pressed", "IE_Released", "IE_Repeat", "IE_DoubleClick", "IE_Axis"}, added_enum

        control_shape = added_control["shape_name"] or "Default"
        style = {"AssetPath": asset, "Operation": "set_control_settings",
                 "ElementType": "control", "Name": control_name,
                 "ControlDisplayName": "Readable MCP Control", "ShapeName": control_shape,
                 "ShapeColor": "R=0.2,G=0.4,B=0.6,A=1",
                 "ShapeVisibility": "based_on_selection", "bSetShapeVisible": True,
                 "bShapeVisible": True, "bSetDrawLimits": True, "bDrawLimits": True,
                 "bSetGroupWithParentControl": True, "bGroupWithParentControl": True,
                 "bSetControlShapeTransform": True,
                 "ControlShapeTransform": {"Translation": {"X": 2, "Y": 3, "Z": 4},
                     "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                     "Scale3D": {"X": 1.5, "Y": 1.5, "Z": 1.5}}}
        request("POST", "/control-rigs/hierarchy", style)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_settings", "ElementType": "control",
            "Name": rotator_name, "PreferredRotationOrder": "zyx"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_settings", "ElementType": "control",
            "Name": vector2d_name, "ControlAnimationType": "animation_channel",
            "bSetShapeVisible": True, "bShapeVisible": False,
            "bSetGroupWithParentControl": True, "bGroupWithParentControl": True})
        proxy_name = "MCP_Test_Proxy"
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "control", "Name": proxy_name,
            "ControlType": "float", "ControlValue": "0.5",
            "ControlAnimationType": "proxy_control",
            "DrivenControlNames": [control_name, vector2d_name]})
        current = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        styled = next(item for item in current if item["name"] == control_name)
        assert styled["display_name"] == "Readable MCP Control", styled
        assert styled["shape_name"] == control_shape and styled["shape_visibility"] == "based_on_selection", styled
        assert styled["shape_visible"] and styled["draw_limits"] and styled["group_with_parent_control"], styled
        assert "R=0.2" in styled["shape_color"] and styled["shape_transform"]["translation"]["x"] == 2, styled
        assert next(item for item in current if item["name"] == rotator_name)["preferred_rotation_order"] == "zyx"
        channel = next(item for item in current if item["name"] == vector2d_name)
        assert channel["control_animation_type"] == "animation_channel" and not channel["shape_visible"], channel
        proxy = next(item for item in current if item["name"] == proxy_name)
        assert proxy["control_animation_type"] == "proxy_control"
        assert {item["name"] for item in proxy["driven_controls"]} == {control_name, vector2d_name}, proxy
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_control_settings", "ElementType": "control",
            "Name": control_name, "ControlAnimationType": "proxy_control",
            "DrivenControlNames": [proxy_name], "bSetDrivenControls": True}, expect_error=True)

        space_name = "MCP_Test_Space"
        secondary_space_name = "MCP_Test_Space_Secondary"
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "null", "Name": space_name,
            "Translation": {"X": 100, "Y": 0, "Z": 0}})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add", "ElementType": "null", "Name": secondary_space_name,
            "Translation": {"X": -100, "Y": 0, "Z": 0}})
        control_before_switch = next(item for item in current if item["name"] == control_name)
        control_before_location = control_before_switch["current_global_transform"]["x"]
        control_before_parent = control_before_switch["active_parent_name"]
        transform_before_space = next(item for item in current if item["name"] == transform_name)["current_global_transform"]["x"]
        float_space_add = {"AssetPath": asset, "Operation": "add_available_space",
                           "ElementType": "control", "Name": control_name,
                           "SpaceType": "null", "SpaceName": space_name,
                           "SpaceLabel": "Float Alternate"}
        assert not request("POST", "/control-rigs/hierarchy", {**float_space_add, "bDryRun": True})["changed"]
        request("POST", "/control-rigs/hierarchy", float_space_add)
        space_add = {"AssetPath": asset, "Operation": "add_available_space",
                     "ElementType": "control", "Name": transform_name,
                     "SpaceType": "null", "SpaceName": space_name,
                     "SpaceLabel": "Alternate"}
        assert not request("POST", "/control-rigs/hierarchy", {**space_add, "bDryRun": True})["changed"]
        request("POST", "/control-rigs/hierarchy", space_add)
        request("POST", "/control-rigs/hierarchy", {**space_add,
            "SpaceName": secondary_space_name, "SpaceLabel": "Secondary"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "label_available_space", "ElementType": "control",
            "Name": transform_name, "SpaceType": "null", "SpaceName": space_name,
            "SpaceLabel": "World Offset"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "reorder_available_space", "ElementType": "control",
            "Name": transform_name, "SpaceType": "null", "SpaceName": space_name,
            "SpaceIndex": 1})
        current = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        available = next(item for item in current if item["name"] == transform_name)["available_spaces"]
        assert available[0]["name"] == secondary_space_name and available[1]["name"] == space_name and available[1]["label"] == "World Offset", available
        float_switch_space = {"AssetPath": asset, "Operation": "switch_parent",
                        "ElementType": "control", "Name": control_name,
                        "SpaceType": "null", "SpaceName": space_name}
        request("POST", "/control-rigs/hierarchy", float_switch_space, expect_error=True)
        unchanged = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        unchanged_control = next(item for item in unchanged if item["name"] == control_name)
        assert unchanged_control["active_parent_name"] == control_before_parent, unchanged_control
        assert abs(unchanged_control["current_global_transform"]["x"] - control_before_location) < 0.001, unchanged_control
        switchable_transform_limits = {**transform_limits,
            "MinimumTransform": {**transform_limits["MinimumTransform"],
                "Translation": {**transform_limits["MinimumTransform"]["Translation"], "X": -1000}},
            "MaximumTransform": {**transform_limits["MaximumTransform"],
                "Translation": {**transform_limits["MaximumTransform"]["Translation"], "X": 1000}}}
        request("POST", "/control-rigs/hierarchy", switchable_transform_limits)
        switch_space = {"AssetPath": asset, "Operation": "switch_parent",
                        "ElementType": "control", "Name": transform_name,
                        "SpaceType": "null", "SpaceName": space_name}
        request("POST", "/control-rigs/hierarchy", switch_space)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_space_restriction", "ElementType": "control",
            "Name": transform_name, "bRestrictSpaceSwitching": True})
        current = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        space_control = next(item for item in current if item["name"] == transform_name)
        assert space_control["active_parent_name"] == space_name, space_control
        assert space_control["restrict_space_switching"], space_control
        assert abs(space_control["current_global_transform"]["x"] - transform_before_space) < 0.001, space_control
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "switch_parent", "ElementType": "control",
            "Name": transform_name, "SpaceType": "bone", "SpaceName": bone_name}, expect_error=True)
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "switch_parent", "ElementType": "control",
            "Name": transform_name, "SpaceType": "reference", "SpaceName": "DefaultParent"})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "set_space_restriction", "ElementType": "control",
            "Name": transform_name, "bRestrictSpaceSwitching": False})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "remove_available_space", "ElementType": "control",
            "Name": transform_name, "SpaceType": "null", "SpaceName": space_name})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "remove_available_space", "ElementType": "control",
            "Name": transform_name, "SpaceType": "null", "SpaceName": secondary_space_name})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "remove_available_space", "ElementType": "control",
            "Name": control_name, "SpaceType": "null", "SpaceName": space_name})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "add_channel_host", "ElementType": "control",
            "Name": vector2d_name, "SpaceType": "control", "SpaceName": rotator_name})
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "remove_channel_host", "ElementType": "control",
            "Name": vector2d_name, "SpaceType": "control", "SpaceName": rotator_name})
        spaces = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        assert not next(item for item in spaces if item["name"] == control_name)["available_spaces"]
        assert not next(item for item in spaces if item["name"] == transform_name)["available_spaces"]
        assert not next(item for item in spaces if item["name"] == vector2d_name)["available_spaces"]
        assert next(item for item in current if item["name"] == socket_name)["parent_name"] == null_name

        renamed = null_name + "_Renamed"
        request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
            "Operation": "rename", "ElementType": "null", "Name": null_name,
            "NewName": renamed})
        current = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        assert any(item["name"] == renamed for item in current)
        assert next(item for item in current if item["name"] == bone_name)["parent_name"] == renamed

        remove = {"AssetPath": asset, "Operation": "delete",
                  "ElementType": "null", "Name": renamed}
        assert request("POST", "/control-rigs/hierarchy", {
            **remove, "bDryRun": True})["affected_children"] >= 1
        request("POST", "/control-rigs/hierarchy", remove, expect_error=True)
        for kind, item in (("control", proxy_name), ("null", space_name), ("null", secondary_space_name),
                           ("control", enum_control_name), ("control", transform_name), ("control", rotator_name),
                           ("control", vector2d_name), ("control", control_name), ("socket", socket_name),
                           ("bone", bone_name), ("null", renamed), ("curve", curve_name)):
            request("POST", "/control-rigs/hierarchy", {"AssetPath": asset,
                "Operation": "delete", "ElementType": kind,
                "Name": item, "bConfirm": True})
        remaining = request("GET", "/control-rigs/hierarchy", params={"asset_path": asset})
        assert len(remaining) == len(original), (len(remaining), len(original))
        compiled = request("POST", "/control-rigs/compile", {"AssetPath": asset})
        assert compiled["compiled"] and compiled["valid"] and compiled["errors"] == 0, compiled
        request("POST", "/assets/save", {"AssetPath": asset})
        assert asset_file.exists(), asset_file
        print("Control Rig hierarchy live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Control Rig was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
