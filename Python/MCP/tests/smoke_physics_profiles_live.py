"""Exercise Physics Asset constraint profile lifecycle on a disposable copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"


def main():
    name = "PA_MCP_Profiles_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        constraints = request("GET", "/physics-assets/constraints",
                              params={"asset_path": asset})["constraints"]
        assert constraints, constraints
        constraint = constraints[0]["name"]
        before = request("GET", "/physics-assets/profiles", params={"asset_path": asset})
        existing = {item["name"] for item in before["profiles"]}
        first, second, renamed = "MCP_Profile_A", "MCP_Profile_B", "MCP_Profile_C"
        assert not {first, second, renamed} & existing

        add = {"AssetPath": asset, "Operation": "add", "ProfileName": first}
        preview = request("POST", "/physics-assets/profiles", {**add, "bDryRun": True})
        assert not preview["changed"] and len(preview["affected_constraints"]) == len(constraints)
        assert {item["name"] for item in request("GET", "/physics-assets/profiles",
            params={"asset_path": asset})["profiles"]} == existing
        request("POST", "/physics-assets/profiles", add)
        current = request("GET", "/physics-assets/profiles", params={"asset_path": asset})
        assert next(item for item in current["profiles"] if item["name"] == first)[
            "constraint_count"] == len(constraints)

        request("POST", "/physics-assets/profiles", {"AssetPath": asset,
            "Operation": "duplicate", "SourceProfileName": first, "ProfileName": second})
        request("POST", "/physics-assets/profiles", {"AssetPath": asset,
            "Operation": "rename", "ProfileName": second, "NewName": renamed})
        current_names = {item["name"] for item in request("GET", "/physics-assets/profiles",
            params={"asset_path": asset})["profiles"]}
        assert first in current_names and renamed in current_names and second not in current_names

        request("PATCH", "/physics-assets/drives", {"AssetPath": asset,
            "ConstraintName": constraint, "DriveType": "linear",
            "bPositionX": True, "Stiffness": 321.0,
            "Damping": 12.0, "ForceLimit": 800.0})
        request("POST", "/physics-assets/profiles", {"AssetPath": asset,
            "Operation": "capture", "ProfileName": renamed,
            "ConstraintName": constraint})
        selected = request("GET", "/physics-assets/profiles", params={
            "asset_path": asset, "constraint_name": constraint})["constraint_profiles"]
        assert next(item for item in selected if item["name"] == renamed)[
            "linear_stiffness_x"] == 321.0, selected

        delete = {"AssetPath": asset, "Operation": "delete", "ProfileName": renamed}
        request("POST", "/physics-assets/profiles", delete, expect_error=True)
        assert not request("POST", "/physics-assets/profiles", {**delete,
            "bDryRun": True})["changed"]
        request("POST", "/physics-assets/profiles", {**delete, "bConfirm": True})
        request("POST", "/physics-assets/profiles", {"AssetPath": asset,
            "Operation": "delete", "ProfileName": first,
            "bConfirm": True, "bSave": True})
        after = request("GET", "/physics-assets/profiles", params={"asset_path": asset})
        assert {item["name"] for item in after["profiles"]} == existing, after
        assert asset_file.exists(), asset_file
        print("Physics Asset profile live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Physics Asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
