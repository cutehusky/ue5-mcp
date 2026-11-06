"""Exercise Physical Animation body profiles on a disposable Physics Asset."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"


def main():
    name = "PA_MCP_BodyProfiles_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        bodies = request("GET", "/physics-assets/bodies", params={"asset_path": asset})
        assert bodies, bodies
        bone = bodies[0]["bone"]
        before = request("GET", "/physics-assets/body-profiles", params={"asset_path": asset})
        original_names = {item["name"] for item in before["profiles"]}
        first, second, renamed = "MCP_Body_A", "MCP_Body_B", "MCP_Body_C"
        assert not {first, second, renamed} & original_names

        add = {"AssetPath": asset, "Operation": "add", "ProfileName": first}
        preview = request("POST", "/physics-assets/body-profiles", {**add, "bDryRun": True})
        assert not preview["changed"] and len(preview["affected_bodies"]) == len(bodies), preview
        request("POST", "/physics-assets/body-profiles", add)
        covered = request("GET", "/physics-assets/body-profiles", params={"asset_path": asset})
        assert next(item for item in covered["profiles"] if item["name"] == first)[
            "body_count"] == len(bodies)

        edit = {"AssetPath": asset, "Operation": "edit", "ProfileName": first,
                "BoneName": bone, "bLocalSimulation": False,
                "OrientationStrength": 12.0, "AngularVelocityStrength": 3.0,
                "PositionStrength": 4.0, "VelocityStrength": 5.0,
                "MaxLinearForce": 100.0, "MaxAngularForce": 200.0}
        request("POST", "/physics-assets/body-profiles", {**edit,
            "OrientationStrength": -1}, expect_error=True)
        assert not request("POST", "/physics-assets/body-profiles", {
            **edit, "bDryRun": True})["changed"]
        request("POST", "/physics-assets/body-profiles", edit)
        selected = request("GET", "/physics-assets/body-profiles", params={
            "asset_path": asset, "bone_name": bone})["body_profiles"]
        value = next(item for item in selected if item["name"] == first)
        assert not value["local_simulation"] and value["orientation_strength"] == 12.0, value
        assert value["max_angular_force"] == 200.0

        request("POST", "/physics-assets/body-profiles", {"AssetPath": asset,
            "Operation": "duplicate", "SourceProfileName": first, "ProfileName": second})
        selected = request("GET", "/physics-assets/body-profiles", params={
            "asset_path": asset, "bone_name": bone})["body_profiles"]
        assert next(item for item in selected if item["name"] == second)[
            "orientation_strength"] == 12.0
        request("POST", "/physics-assets/body-profiles", {"AssetPath": asset,
            "Operation": "rename", "ProfileName": second, "NewName": renamed})

        delete = {"AssetPath": asset, "Operation": "delete", "ProfileName": renamed}
        request("POST", "/physics-assets/body-profiles", delete, expect_error=True)
        assert not request("POST", "/physics-assets/body-profiles", {**delete,
            "bDryRun": True})["changed"]
        request("POST", "/physics-assets/body-profiles", {**delete, "bConfirm": True})
        request("POST", "/physics-assets/body-profiles", {"AssetPath": asset,
            "Operation": "delete", "ProfileName": first,
            "bConfirm": True, "bSave": True})
        after = request("GET", "/physics-assets/body-profiles", params={"asset_path": asset})
        assert {item["name"] for item in after["profiles"]} == original_names, after
        assert asset_file.exists(), asset_file
        print("Physics Asset body profile live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Physics Asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
