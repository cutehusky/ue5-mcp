"""Exercise 1D Blend Space boundaries and interpolation on a temporary asset."""

from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
ASSET = "/Game/UE5MCP_Test/BS_MCP_1D_Fixture.BS_MCP_1D_Fixture"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run"


def main():
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / "BS_MCP_1D_Fixture.uasset"
    assert asset_file.exists(), "Create the fixture with create_blend_space_1d_fixture.py first"
    try:
        axes = request("GET", "/blend-spaces/axes", params={"asset_path": ASSET})
        assert len(axes) == 1, axes
        empty_validation = request("POST", "/blend-spaces/validate", {"AssetPath": ASSET})
        assert not empty_validation["valid"]
        assert any("no samples" in error for error in empty_validation["errors"]), empty_validation
        axis = axes[0]
        request("POST", "/blend-spaces/axes", {"AssetPath": ASSET,
            "AxisIndex": 1, "Properties": {"display_name": "Invalid"}}, expect_error=True)
        animations = list(dict.fromkeys(s["animation"] for s in request(
            "GET", "/blend-spaces/samples", params={"asset_path": SOURCE}) if s["animation"]))
        assert len(animations) >= 2, animations
        for value, animation in zip((axis["min"], axis["max"]), animations):
            add = {"AssetPath": ASSET, "Operation": "add", "AnimationPath": animation,
                   "SampleValue": {"X": value, "Y": 0, "Z": 0}}
            assert not request("POST", "/blend-spaces/samples", {**add, "bDryRun": True})["changed"]
            request("POST", "/blend-spaces/samples", add)
        bad = {"AssetPath": ASSET, "Operation": "add", "AnimationPath": animations[0],
               "SampleValue": {"X": (axis["min"] + axis["max"]) / 2, "Y": 1, "Z": 0}}
        request("POST", "/blend-spaces/samples", bad, expect_error=True)
        request("POST", "/blend-spaces/samples", {**bad, "SampleValue": {
            "X": bad["SampleValue"]["X"], "Y": 0, "Z": 1}}, expect_error=True)
        samples = request("GET", "/blend-spaces/samples", params={"asset_path": ASSET})
        assert len(samples) == 2, samples

        rebuilt = request("POST", "/blend-spaces/rebuild", {"AssetPath": ASSET})
        assert rebuilt["segments"] > 0 and rebuilt["triangles"] == 0, rebuilt
        valid_result = request("POST", "/blend-spaces/validate", {"AssetPath": ASSET})
        assert valid_result["valid"] and not valid_result["errors"], valid_result
        preview = request("POST", "/blend-spaces/preview", {"AssetPath": ASSET,
            "SampleValue": {"X": (axis["min"] + axis["max"]) / 2, "Y": 0, "Z": 0}})
        assert preview["valid"] and len(preview["samples"]) == 2, preview
        assert abs(sum(x["weight"] for x in preview["samples"]) - 1) < 1e-4, preview

        request("POST", "/blend-spaces/axes", {"AssetPath": ASSET, "AxisIndex": 0,
            "Properties": {"display_name": "MCP Speed", "max": str(axis["max"] + 25)},
            "bSave": True})
        changed = request("GET", "/blend-spaces/axes", params={"asset_path": ASSET})
        assert changed[0]["display_name"] == "MCP Speed" and changed[0]["max"] == axis["max"] + 25
        print("Blend Space 1D live smoke passed")
    finally:
        request("POST", "/assets/delete", {"AssetPath": ASSET})
        assert not asset_file.exists(), f"Test Blend Space 1D was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
