"""Exercise Blend Space sample add/update/move/confirmed-delete on a copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]


def coords(sample):
    return sample["x"], sample["y"], sample["z"]


def sample_value(values):
    return {"X": values[0], "Y": values[1], "Z": values[2]}


def main():
    name = "BS_MCP_Smoke_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run",
            "DestinationPath": destination})
        samples = request("GET", "/blend-spaces/samples", params={"asset_path": asset})
        assert len(samples) >= 3, samples
        first = next(x for x in samples if sum(coords(y) == coords(x) for y in samples) == 1)
        alternate = next(x for x in samples if x["animation"] and x["animation"] != first["animation"])
        original_coords = coords(first)
        original_count = len(samples)

        remove = {"AssetPath": asset, "Operation": "delete", "SampleIndex": first["index"]}
        request("POST", "/blend-spaces/samples", remove, expect_error=True)
        assert request("POST", "/blend-spaces/samples", {**remove, "bDryRun": True})["changed"] is False
        assert len(request("GET", "/blend-spaces/samples", params={"asset_path": asset})) == original_count
        request("POST", "/blend-spaces/samples", {**remove, "bConfirm": True})
        assert len(request("GET", "/blend-spaces/samples", params={"asset_path": asset})) == original_count - 1

        add = {"AssetPath": asset, "Operation": "add", "AnimationPath": first["animation"],
               "SampleValue": sample_value(original_coords)}
        assert request("POST", "/blend-spaces/samples", {**add, "bDryRun": True})["changed"] is False
        added_index = request("POST", "/blend-spaces/samples", add)["sample_index"]
        assert any(x["index"] == added_index and coords(x) == original_coords
                   for x in request("GET", "/blend-spaces/samples", params={"asset_path": asset}))

        update = {"AssetPath": asset, "Operation": "update", "SampleIndex": -1,
                  "AnimationPath": alternate["animation"], "SampleValue": sample_value(original_coords)}
        assert request("POST", "/blend-spaces/samples", {**update, "bDryRun": True})["changed"] is False
        request("POST", "/blend-spaces/samples", update)
        assert any(coords(x) == original_coords and x["animation"] == alternate["animation"]
                   for x in request("GET", "/blend-spaces/samples", params={"asset_path": asset}))

        candidates = request("GET", "/blend-spaces/samples", params={"asset_path": asset})
        destination_sample = next(x for x in candidates if coords(x) != original_coords
                                  and sum(coords(y) == coords(x) for y in candidates) == 1)
        destination_coords = coords(destination_sample)
        request("POST", "/blend-spaces/samples", {"AssetPath": asset,
            "Operation": "delete", "SampleIndex": destination_sample["index"], "bConfirm": True})
        remaining = request("GET", "/blend-spaces/samples", params={"asset_path": asset})
        moved_index = next(x["index"] for x in remaining if coords(x) == original_coords)
        move = {"AssetPath": asset, "Operation": "move", "SampleIndex": moved_index,
                "SampleValue": sample_value(destination_coords)}
        assert request("POST", "/blend-spaces/samples", {**move, "bDryRun": True})["changed"] is False
        request("POST", "/blend-spaces/samples", move)
        assert any(coords(x) == destination_coords and x["animation"] == alternate["animation"]
                   for x in request("GET", "/blend-spaces/samples", params={"asset_path": asset}))

        request("POST", "/blend-spaces/samples", {"AssetPath": asset,
            "Operation": "update", "SampleIndex": moved_index,
            "AnimationPath": alternate["animation"], "bSave": True})
        assert asset_file.exists(), asset_file
        print("Blend Space live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Blend Space was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
