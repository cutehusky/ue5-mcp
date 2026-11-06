"""Verify Physics Asset body and constraint edits survive an editor restart."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request
from smoke_sequencer_persistence import editor_status, start_editor, stop_editor


PROJECT = Path(__file__).resolve().parents[5]


def main():
    assert editor_status() is None, "Port 8080 already has an Unreal API listener"
    name = "PA_MCP_Persist_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    file_path = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    process = None
    asset = ""
    try:
        process = start_editor()
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin",
            "DestinationPath": destination})
        bodies = request("GET", "/physics-assets/bodies", params={"asset_path": asset})
        validation = request("GET", "/physics-assets/validate", params={"asset_path": asset})
        assert bodies and validation["unrepresented_bones"]
        new_bone = validation["unrepresented_bones"][0]
        parent_bone = bodies[0]["bone"]
        constraint_name = "MCP_PersistConstraint_" + uuid.uuid4().hex[:6]
        request("POST", "/physics-assets/bodies", {
            "AssetPath": asset, "Operation": "add", "BoneName": new_bone,
            "ShapeType": "sphere", "Radius": 4.0})
        request("POST", "/physics-assets/constraints", {
            "AssetPath": asset, "Operation": "add", "ConstraintName": constraint_name,
            "ChildBone": new_bone, "ParentBone": parent_bone,
            "LinearMotion": "limited", "LinearLimit": 7,
            "AngularMotion": "limited", "Swing1Limit": 25,
            "Swing2Limit": 25, "TwistLimit": 15})
        request("POST", "/assets/save-all-selected", {"AssetPath": asset})
        assert file_path.exists(), f"Physics Asset was not saved: {file_path}"

        stop_editor(process)
        process = start_editor()
        saved_bodies = request("GET", "/physics-assets/bodies", params={"asset_path": asset})
        assert any(x["bone"] == new_bone and x["sphere_count"] >= 1 for x in saved_bodies), saved_bodies
        saved_constraints = request("GET", "/physics-assets/constraints", params={"asset_path": asset})["constraints"]
        assert any(x["name"] == constraint_name and x["child_bone"] == new_bone
                   and x["parent_bone"] == parent_bone and x["linear_limit"] == 7
                   for x in saved_constraints), saved_constraints
        request("POST", "/assets/delete", {"AssetPath": asset})
        asset = ""
        assert not file_path.exists(), f"Test Physics Asset was not deleted: {file_path}"
        print("Physics Asset persistence smoke passed")
    finally:
        if asset and process is not None and process.poll() is None:
            try:
                request("POST", "/assets/delete", {"AssetPath": asset})
            except Exception as error:
                print(f"Physics Asset cleanup failed: {asset}: {error}")
        stop_editor(process)


if __name__ == "__main__":
    main()
