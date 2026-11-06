"""Exercise convex Physics Asset shape authoring on a disposable copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"
TETRA = [
    {"X": -5, "Y": -5, "Z": -5},
    {"X": 5, "Y": -5, "Z": -5},
    {"X": 0, "Y": 5, "Z": -5},
    {"X": 0, "Y": 0, "Z": 5},
]
TETRA_UPDATED = [
    {"X": -4, "Y": -4, "Z": -4},
    {"X": 6, "Y": -4, "Z": -4},
    {"X": 1, "Y": 6, "Z": -4},
    {"X": 1, "Y": 1, "Z": 6},
]


def main():
    name = "PA_MCP_Convex_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        bone = request("GET", "/physics-assets/bodies", params={"asset_path": asset})[0]["bone"]
        params = {"asset_path": asset, "bone_name": bone}
        before = request("GET", "/physics-assets/shapes", params=params)["shapes"]
        original_convex = sum(shape["shape_type"] == "convex" for shape in before)
        add = {"AssetPath": asset, "Operation": "add", "BoneName": bone,
               "ShapeType": "convex", "Vertices": TETRA,
               "Center": {"X": 2, "Y": 3, "Z": 4},
               "bEnableCollision": True, "bContributeToMass": True}

        coplanar = [dict(vertex, Z=0) for vertex in TETRA]
        request("POST", "/physics-assets/shapes", {**add,
            "Vertices": coplanar}, expect_error=True)
        request("POST", "/physics-assets/shapes", {**add,
            "Vertices": [TETRA[0]] * 4}, expect_error=True)
        preview = request("POST", "/physics-assets/shapes", {**add, "bDryRun": True})
        assert not preview["changed"] and preview["shape_index"] == original_convex, preview
        assert request("GET", "/physics-assets/shapes", params=params)["shapes"] == before

        result = request("POST", "/physics-assets/shapes", {**add, "bSave": True})
        assert result["changed"] and result["saved"] and result["shape_index"] == original_convex
        shapes = request("GET", "/physics-assets/shapes", params=params)["shapes"]
        created = next(shape for shape in shapes if shape["shape_type"] == "convex"
                       and shape["shape_index"] == original_convex)
        assert created["vertex_count"] == 4 and len(created["vertices"]) == 4, created
        assert created["collision_enabled"] and created["contributes_to_mass"]
        assert asset_file.exists(), asset_file
        runtime = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_runtime_cook": "true"})
        runtime_body = next(body for body in runtime["body_runtime_states"]
                            if body["bone_name"] == bone)
        assert runtime["runtime_ready"] and runtime_body["ready"], runtime
        assert runtime_body["cooked_convex_count"] == runtime_body["convex_count"], runtime_body
        runtime_state = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_runtime_state": "true"})
        assert runtime_state["runtime_state_ready"], runtime_state
        convex_body_state = next(body for body in runtime_state["runtime_body_instances"]
                                 if body["bone_name"] == bone)
        assert convex_body_state["valid"], runtime_state

        replace = {"AssetPath": asset, "Operation": "replace_vertices", "BoneName": bone,
                   "ShapeType": "convex", "ShapeIndex": original_convex, "Vertices": TETRA_UPDATED}
        request("PATCH", "/physics-assets/shapes", {**replace,
            "Vertices": [dict(vertex, Z=0) for vertex in TETRA_UPDATED]}, expect_error=True)
        assert request("GET", "/physics-assets/shapes", params=params)["shapes"] == shapes
        preview = request("PATCH", "/physics-assets/shapes", {**replace, "bDryRun": True})
        assert not preview["changed"] and preview["shape_index"] == original_convex, preview
        assert request("GET", "/physics-assets/shapes", params=params)["shapes"] == shapes
        updated_result = request("PATCH", "/physics-assets/shapes", replace)
        assert updated_result["changed"] and updated_result["shape_index"] == original_convex, updated_result
        updated_shapes = request("GET", "/physics-assets/shapes", params=params)["shapes"]
        updated = next(shape for shape in updated_shapes if shape["shape_type"] == "convex"
                       and shape["shape_index"] == original_convex)
        expected_vertices = [{"x": vertex["X"], "y": vertex["Y"], "z": vertex["Z"]}
                             for vertex in TETRA_UPDATED]
        assert updated["vertices"] == expected_vertices and updated["vertex_count"] == 4, updated
        for field in ("center", "rotation", "collision_enabled", "contributes_to_mass"):
            assert updated[field] == created[field], {"before": created, "after": updated, "field": field}

        remove = {"AssetPath": asset, "BoneName": bone, "ShapeType": "convex",
                  "ShapeIndex": original_convex}
        request("DELETE", "/physics-assets/shapes", remove, expect_error=True)
        request("DELETE", "/physics-assets/shapes", {**remove, "bConfirm": True})
        assert request("GET", "/physics-assets/shapes", params=params)["shapes"] == before

        validation = request("GET", "/physics-assets/validate", params={"asset_path": asset})
        if validation["unrepresented_bones"]:
            new_bone = validation["unrepresented_bones"][0]
            create_body = {"AssetPath": asset, "Operation": "add",
                           "BoneName": new_bone, "ShapeType": "convex", "Vertices": TETRA}
            assert not request("POST", "/physics-assets/bodies", {
                **create_body, "bDryRun": True})["changed"]
            request("POST", "/physics-assets/bodies", create_body)
            new_shapes = request("GET", "/physics-assets/shapes", params={
                "asset_path": asset, "bone_name": new_bone})["shapes"]
            assert len(new_shapes) == 1 and new_shapes[0]["shape_type"] == "convex"
            request("DELETE", "/physics-assets/bodies", {"AssetPath": asset,
                "BoneName": new_bone, "bConfirm": True})
        print("Physics Asset convex live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Physics Asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
