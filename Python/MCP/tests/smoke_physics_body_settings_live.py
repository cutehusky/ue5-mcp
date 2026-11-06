"""Exercise typed Physics Asset body settings on a disposable copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"


def main():
    name = "PA_MCP_BodySettings_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        bone = request("GET", "/physics-assets/bodies", params={"asset_path": asset})[0]["bone"]
        params = {"asset_path": asset, "bone_name": bone}
        before = request("GET", "/physics-assets/body-settings", params=params)
        settings = {
            "physics_type": "kinematic" if before["physics_type"] != "kinematic" else "simulated",
            "collision_enabled": "none" if before["collision_enabled"] != "none" else "query_and_physics",
            "mass_scale": "1.75" if before["mass_scale"] != 1.75 else "2.5",
            "consider_for_bounds": str(not before["consider_for_bounds"]).lower(),
            "enable_gravity": str(not before["enable_gravity"]).lower(),
            "use_ccd": str(not before["use_ccd"]).lower(),
            "skip_scale_from_animation": str(not before["skip_scale_from_animation"]).lower(),
        }
        body = {"AssetPath": asset, "BoneName": bone, "Settings": settings}
        preview = request("PATCH", "/physics-assets/body-settings", {**body, "bDryRun": True})
        assert not preview["changed"] and preview["dry_run"]
        assert preview["physics_type"] == settings["physics_type"]
        assert request("GET", "/physics-assets/body-settings", params=params) == before
        request("PATCH", "/physics-assets/body-settings", {**body,
            "Settings": {"mass_scale": "-1"}}, expect_error=True)
        applied = request("PATCH", "/physics-assets/body-settings", {**body, "bSave": True})
        assert applied["changed"] and applied["saved"]
        after = request("GET", "/physics-assets/body-settings", params=params)
        assert after["physics_type"] == settings["physics_type"]
        assert after["collision_enabled"] == settings["collision_enabled"]
        assert abs(after["mass_scale"] - float(settings["mass_scale"])) < 1e-5
        assert after["consider_for_bounds"] != before["consider_for_bounds"]
        assert after["enable_gravity"] != before["enable_gravity"]
        assert after["use_ccd"] != before["use_ccd"]
        assert after["skip_scale_from_animation"] != before["skip_scale_from_animation"]
        assert asset_file.exists(), asset_file
        print("Physics Asset body settings live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Physics Asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
