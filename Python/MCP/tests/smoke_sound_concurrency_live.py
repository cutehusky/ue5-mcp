"""Exercise Sound Concurrency creation, settings, validation, save, and cleanup."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]


def main():
    name = "SC_MCP_Smoke_" + uuid.uuid4().hex[:8]
    package = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        preview = request("POST", "/audio/concurrencies/create", {
            "AssetPath": package, "bDryRun": True})
        assert preview["would_create"] and preview["dry_run"]
        assert not asset_file.exists()

        asset = request("POST", "/audio/concurrencies/create", {
            "AssetPath": package, "bSave": True})
        assert asset.endswith(f".{name}"), asset
        assert asset_file.exists(), asset_file
        assert request("POST", "/audio/validate", {"AssetPath": asset})["valid"]
        initial = request("GET", "/audio/concurrencies/inspect", params={
            "asset_path": asset})
        assert initial["Concurrency"]["RetriggerTime"] == 0.0, initial

        settings = {"Concurrency.RetriggerTime": "0.37",
                    "Concurrency.VolumeScaleAttackTime": "0.22"}
        request("PATCH", "/audio/assets/settings", {
            "AssetPath": asset, "Properties": settings, "bDryRun": True})
        after_preview = request("GET", "/audio/concurrencies/inspect", params={
            "asset_path": asset})
        assert after_preview["Concurrency"]["RetriggerTime"] == 0.0, after_preview

        request("PATCH", "/audio/assets/settings", {
            "AssetPath": asset, "Properties": settings, "bSave": True})
        updated = request("GET", "/audio/concurrencies/inspect", params={
            "asset_path": asset})["Concurrency"]
        assert abs(updated["RetriggerTime"] - 0.37) < 1e-5, updated
        assert abs(updated["VolumeScaleAttackTime"] - 0.22) < 1e-5, updated
        assert request("POST", "/audio/validate", {"AssetPath": asset})["valid"]
        print("Sound Concurrency live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Sound Concurrency was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
