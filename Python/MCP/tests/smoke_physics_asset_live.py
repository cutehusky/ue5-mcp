"""Exercise Physics Asset body, shape, collision, and validation routes.

Requires the local editor API on port 8080. Mutations affect only a uniquely
named duplicate of the mannequin Physics Asset, which is removed afterward.
"""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]


def has_disabled_pair(pairs, first, second):
    return any({pair["bone_name"], pair["other_bone_name"]} == {first, second}
               for pair in pairs)


def main():
    name = "PA_MCP_Smoke_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin",
            "DestinationPath": destination})
        bodies = request("GET", "/physics-assets/bodies", params={"asset_path": asset})
        assert len(bodies) >= 2, bodies
        constraints = request("GET", "/physics-assets/constraints", params={"asset_path": asset})["constraints"]
        assert isinstance(constraints, list)
        validation = request("GET", "/physics-assets/validate", params={"asset_path": asset})
        assert isinstance(validation["errors"], list) and isinstance(validation["unrepresented_bones"], list)

        selected = next(x for x in bodies if x["sphere_count"] + x["box_count"] + x["sphyl_count"] + x["convex_count"] > 0)
        bone = selected["bone"]
        before = request("GET", "/physics-assets/shapes", params={"asset_path": asset, "bone_name": bone})["shapes"]
        add_shape = {"AssetPath": asset, "Operation": "add", "BoneName": bone,
                     "ShapeType": "sphere", "Radius": 3.0,
                     "Center": {"X": 1, "Y": 2, "Z": 3}}
        assert request("POST", "/physics-assets/shapes", {**add_shape, "bDryRun": True})["changed"] is False
        assert len(request("GET", "/physics-assets/shapes", params={"asset_path": asset, "bone_name": bone})["shapes"]) == len(before)
        shape_index = request("POST", "/physics-assets/shapes", add_shape)["shape_index"]
        shapes = request("GET", "/physics-assets/shapes", params={"asset_path": asset, "bone_name": bone})["shapes"]
        assert len(shapes) == len(before) + 1 and any(x["shape_type"] == "sphere" and x["shape_index"] == shape_index for x in shapes)
        remove_shape = {"AssetPath": asset, "BoneName": bone, "ShapeType": "sphere", "ShapeIndex": shape_index}
        request("DELETE", "/physics-assets/shapes", remove_shape, expect_error=True)
        assert request("DELETE", "/physics-assets/shapes", {**remove_shape, "bDryRun": True})["changed"] is False
        request("DELETE", "/physics-assets/shapes", {**remove_shape, "bConfirm": True})
        assert len(request("GET", "/physics-assets/shapes", params={"asset_path": asset, "bone_name": bone})["shapes"]) == len(before)

        first, second = bodies[0]["bone"], bodies[1]["bone"]
        disabled_before = request("GET", "/physics-assets/collision-pairs", params={"asset_path": asset})["disabled_pairs"]
        initially_disabled = has_disabled_pair(disabled_before, first, second)
        change_pair = {"AssetPath": asset, "BoneName": first,
                       "OtherBoneName": second, "bEnableCollision": initially_disabled}
        assert request("PATCH", "/physics-assets/collision-pairs", {**change_pair, "bDryRun": True})["changed"] is False
        request("PATCH", "/physics-assets/collision-pairs", change_pair)
        disabled_after = request("GET", "/physics-assets/collision-pairs", params={"asset_path": asset})["disabled_pairs"]
        assert has_disabled_pair(disabled_after, first, second) != initially_disabled
        request("PATCH", "/physics-assets/collision-pairs", {**change_pair, "bEnableCollision": not initially_disabled})

        if validation["unrepresented_bones"]:
            new_bone = validation["unrepresented_bones"][0]
            add_body = {"AssetPath": asset, "Operation": "add", "BoneName": new_bone,
                        "ShapeType": "sphere", "Radius": 4.0}
            assert request("POST", "/physics-assets/bodies", {**add_body, "bDryRun": True})["changed"] is False
            request("POST", "/physics-assets/bodies", add_body)
            assert any(x["bone"] == new_bone for x in request("GET", "/physics-assets/bodies", params={"asset_path": asset}))
            constraint_name = "MCP_SmokeConstraint_" + uuid.uuid4().hex[:6]
            constraint = {"AssetPath": asset, "Operation": "add",
                          "ConstraintName": constraint_name, "ChildBone": new_bone,
                          "ParentBone": first, "LinearMotion": "limited", "LinearLimit": 5,
                          "AngularMotion": "limited", "Swing1Limit": 30,
                          "Swing2Limit": 30, "TwistLimit": 20,
                          "Projection": "enabled"}
            assert request("POST", "/physics-assets/constraints", {**constraint, "bDryRun": True})["changed"] is False
            added = request("POST", "/physics-assets/constraints", constraint)
            assert added["linear_limit"] == 5 and added["projection_enabled"] is True, added
            listed = request("GET", "/physics-assets/constraints", params={"asset_path": asset})["constraints"]
            assert any(x["name"] == constraint_name and x["child_bone"] == new_bone for x in listed), listed
            edit_constraint = {"AssetPath": asset, "ConstraintName": constraint_name,
                               "LinearLimit": 10, "Projection": "disabled"}
            assert request("PATCH", "/physics-assets/constraints", {**edit_constraint, "bDryRun": True})["changed"] is False
            edited = request("PATCH", "/physics-assets/constraints", edit_constraint)
            assert edited["linear_limit"] == 10 and edited["projection_enabled"] is False, edited
            remove_constraint = {"AssetPath": asset, "ConstraintName": constraint_name}
            request("DELETE", "/physics-assets/constraints", remove_constraint, expect_error=True)
            assert request("DELETE", "/physics-assets/constraints", {**remove_constraint, "bDryRun": True})["changed"] is False
            request("DELETE", "/physics-assets/constraints", {**remove_constraint, "bConfirm": True})
            assert not any(x["name"] == constraint_name for x in request("GET", "/physics-assets/constraints", params={"asset_path": asset})["constraints"])
            request("POST", "/physics-assets/constraints", constraint)
            remove_body = {"AssetPath": asset, "BoneName": new_bone}
            request("DELETE", "/physics-assets/bodies", remove_body, expect_error=True)
            preview = request("DELETE", "/physics-assets/bodies", {**remove_body, "bDryRun": True})
            assert not preview["changed"] and constraint_name in preview["affected_constraints"], preview
            request("DELETE", "/physics-assets/bodies", {**remove_body, "bConfirm": True})
            assert not any(x["bone"] == new_bone for x in request("GET", "/physics-assets/bodies", params={"asset_path": asset}))
            assert not any(x["name"] == constraint_name for x in request("GET", "/physics-assets/constraints", params={"asset_path": asset})["constraints"])

        assert request("POST", "/physics-assets/refresh", {"AssetPath": asset})["changed"] is False
        print("Physics Asset live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
