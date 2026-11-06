"""Exercise Blend Space axes, triangulation rebuild, and preview on a copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run"


def main():
    name = "BS_MCP_Axes_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        axes = request("GET", "/blend-spaces/axes", params={"asset_path": asset})
        assert len(axes) == 2, axes
        samples = request("GET", "/blend-spaces/samples", params={"asset_path": asset})
        assert samples, samples
        point = samples[0]
        preview = {"AssetPath": asset, "SampleValue": {
            "X": point["x"], "Y": point["y"], "Z": point["z"]}}
        sampled = request("POST", "/blend-spaces/preview", preview)
        assert sampled["valid"] and sampled["samples"], sampled
        assert abs(sum(x["weight"] for x in sampled["samples"]) - 1) < 1e-4, sampled

        axis = axes[0]
        edit = {"AssetPath": asset, "AxisIndex": 0, "Properties": {
            "display_name": "MCP Direction", "wrap_input": "true",
            "min": str(axis["min"] - 10), "max": str(axis["max"] + 10),
            "grid_num": str(axis["grid_num"] + 1)}}
        assert not request("POST", "/blend-spaces/axes", {**edit, "bDryRun": True})["changed"]
        assert request("GET", "/blend-spaces/axes", params={"asset_path": asset}) == axes
        request("POST", "/blend-spaces/axes", {**edit, "Properties": {
            "min": str(axis["max"] + 1)}}, expect_error=True)
        request("POST", "/blend-spaces/axes", edit)
        changed = request("GET", "/blend-spaces/axes", params={"asset_path": asset})[0]
        assert changed["display_name"] == "MCP Direction" and changed["wrap_input"]
        assert changed["min"] == axis["min"] - 10 and changed["max"] == axis["max"] + 10
        assert changed["grid_num"] == axis["grid_num"] + 1

        assert not request("POST", "/blend-spaces/rebuild", {
            "AssetPath": asset, "bDryRun": True})["changed"]
        rebuilt = request("POST", "/blend-spaces/rebuild", {
            "AssetPath": asset, "bSave": True})
        assert rebuilt["changed"] and rebuilt["saved"]
        assert rebuilt["segments"] + rebuilt["triangles"] > 0, rebuilt
        assert asset_file.exists(), asset_file
        print("Blend Space axes/rebuild/preview live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Blend Space was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
