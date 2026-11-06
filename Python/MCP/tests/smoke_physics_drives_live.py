"""Exercise linear and angular Physics Asset drives on a disposable copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"


def main():
    name = "PA_MCP_Drives_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        constraints = request("GET", "/physics-assets/constraints",
                              params={"asset_path": asset})["constraints"]
        assert constraints, constraints
        constraint_name = constraints[0]["name"]
        params = {"asset_path": asset, "constraint_name": constraint_name}
        before = request("GET", "/physics-assets/drives", params=params)

        linear = {"AssetPath": asset, "ConstraintName": constraint_name,
                  "DriveType": "linear", "bPositionX": True, "bVelocityY": True,
                  "Stiffness": 120.0, "Damping": 14.0, "ForceLimit": 500.0,
                  "PositionTarget": {"X": 3, "Y": 4, "Z": 5},
                  "VelocityTarget": {"X": 0, "Y": 6, "Z": 0}}
        preview = request("PATCH", "/physics-assets/drives", {**linear, "bDryRun": True})
        assert not preview["changed"] and preview["dry_run"]
        assert preview["linear"]["position_x"] and preview["linear"]["velocity_y"]
        assert request("GET", "/physics-assets/drives", params=params) == before
        request("PATCH", "/physics-assets/drives", {**linear, "Stiffness": -1}, expect_error=True)
        applied = request("PATCH", "/physics-assets/drives", linear)
        assert applied["changed"] and applied["linear"]["stiffness"] == 120.0
        assert applied["linear"]["position_target_x"] == 3.0

        angular = {"AssetPath": asset, "ConstraintName": constraint_name,
                   "DriveType": "angular", "AngularMode": "slerp",
                   "bSlerpPosition": True, "bSlerpVelocity": True,
                   "Stiffness": 80.0, "Damping": 9.0, "ForceLimit": 200.0,
                   "OrientationTarget": {"Pitch": 10, "Yaw": 20, "Roll": 0},
                   "VelocityTarget": {"X": 1, "Y": 0, "Z": 0}, "bSave": True}
        applied = request("PATCH", "/physics-assets/drives", angular)
        assert applied["saved"] and applied["angular"]["mode"] == "slerp", applied
        assert applied["angular"]["slerp_position"] and applied["angular"]["slerp_velocity"]
        assert applied["angular"]["stiffness"] == 80.0
        assert asset_file.exists(), asset_file
        print("Physics Asset drive live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Physics Asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
