"""Exercise ordered generic asset batching against a running UE5_MCP API."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]


def main():
    name = "IA_MCP_Batch_" + uuid.uuid4().hex[:8]
    package = f"/Game/UE5MCP_Test/{name}"
    asset = f"{package}.{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    created = False
    try:
        assert request("POST", "/data-assets/create", {
            "AssetPath": package, "AssetClass": "/Script/EnhancedInput.InputAction"}) == package
        created = True

        def props():
            return request("GET", "/assets/properties", params={"asset_path": asset})

        original = props()
        assert original["bConsumeInput"] is True and original["bTriggerWhenPaused"] is False
        entries = [
            {"AssetPath": asset, "Operation": "set_properties", "Properties": {"bConsumeInput": "false"}},
            {"AssetPath": asset, "Operation": "set_properties", "Properties": {"bTriggerWhenPaused": "true"}},
        ]
        preview = request("POST", "/assets/batch", {"Operations": entries, "bDryRun": True})
        assert preview["success"] and len(preview["results"]) == 2, preview
        assert all(x["dry_run"] and not x["changed"] for x in preview["results"]), preview
        assert props()["bConsumeInput"] is True and props()["bTriggerWhenPaused"] is False

        invalid = {"AssetPath": asset, "Operation": "set_properties",
                   "Properties": {"bConsumeInput": "true", "zMissingField": "0"}}
        result = request("POST", "/assets/batch", {"Operations": [
            entries[0], invalid, entries[1],
        ]})
        assert not result["success"] and result["failure_count"] == 1, result
        assert [x["index"] for x in result["results"]] == [0, 1, 2], result
        assert [x["success"] for x in result["results"]] == [True, False, True], result
        assert props()["bConsumeInput"] is False and props()["bTriggerWhenPaused"] is True

        stopped = request("POST", "/assets/batch", {"Operations": [
            {"AssetPath": asset, "Properties": {"bConsumeInput": "true"}},
            invalid,
            {"AssetPath": asset, "Properties": {"bTriggerWhenPaused": "false"}},
        ], "bStopOnError": True})
        assert [x["skipped"] for x in stopped["results"]] == [False, False, True], stopped
        assert props()["bConsumeInput"] is True and props()["bTriggerWhenPaused"] is True

        legacy = request("POST", "/assets/batch", {"AssetPath": asset,
            "Properties": {"bConsumeInput": "false"}})
        assert legacy["Success"] is True and props()["bConsumeInput"] is False, legacy
        saved = request("POST", "/assets/batch", {"Operations": [
            {"AssetPath": asset, "Operation": "save"},
        ]})
        assert saved["success"] and saved["results"][0]["saved"], saved
        assert asset_file.exists(), asset_file
        print("Ordered asset batch smoke passed")
    finally:
        if created:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
