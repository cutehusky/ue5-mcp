"""Two-session persistence test for Blend Space sample IDs.

Run --stage create, restart the editor, then run --stage verify.
"""

import argparse
import json
from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run"
ASSET = "/Game/UE5MCP_Test/BS_MCP_Ids_Fixture.BS_MCP_Ids_Fixture"
DESTINATION = "/Game/UE5MCP_Test/BS_MCP_Ids_Fixture"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "BS_MCP_Ids_Fixture.uasset"
STATE_FILE = PROJECT / "Saved" / "UE5MCP_BlendSpaceIdsState.json"


def list_samples():
    return request("GET", "/blend-spaces/samples", params={"asset_path": ASSET})


def create():
    assert not ASSET_FILE.exists() and not STATE_FILE.exists(), "fixture already exists"
    asset = request("POST", "/assets/duplicate", {
        "AssetPath": SOURCE, "DestinationPath": DESTINATION})
    assert asset == ASSET, asset
    try:
        samples = list_samples()
        assert len(samples) >= 3 and len({s["id"] for s in samples}) == len(samples), samples
        victim, target = samples[0], samples[-1]
        replacement = next(s["animation"] for s in samples
                           if s["animation"] and s["animation"] != target["animation"])
        request("POST", "/blend-spaces/samples", {"AssetPath": ASSET,
            "Operation": "delete", "SampleId": victim["id"], "bConfirm": True})
        shifted = next(s for s in list_samples() if s["id"] == target["id"])
        assert shifted["index"] == target["index"] - 1, (shifted, target)
        request("POST", "/blend-spaces/samples", {"AssetPath": ASSET,
            "Operation": "update", "SampleId": target["id"],
            "AnimationPath": replacement, "bSave": True})
        updated = next(s for s in list_samples() if s["id"] == target["id"])
        assert updated["animation"] == replacement, updated
        axes = request("GET", "/blend-spaces/axes", params={"asset_path": ASSET})
        before_ids = {s["id"] for s in list_samples()}
        request("POST", "/blend-spaces/axes", {"AssetPath": ASSET, "AxisIndex": 0,
            "Properties": {"grid_num": str(axes[0]["grid_num"] + 1)}, "bSave": True})
        assert {s["id"] for s in list_samples()} == before_ids
        STATE_FILE.write_text(json.dumps({"target_id": target["id"],
            "target_index": updated["index"], "replacement": replacement,
            "remaining_ids": sorted(before_ids)}), encoding="utf-8")
        assert ASSET_FILE.exists(), ASSET_FILE
        print("Blend Space sample ID create stage passed")
    except BaseException:
        request("POST", "/assets/delete", {"AssetPath": ASSET})
        STATE_FILE.unlink(missing_ok=True)
        raise


def verify():
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    try:
        samples = list_samples()
        assert sorted(s["id"] for s in samples) == state["remaining_ids"], samples
        target = next(s for s in samples if s["id"] == state["target_id"])
        assert target["index"] == state["target_index"]
        assert target["animation"] == state["replacement"]
        assert request("POST", "/blend-spaces/samples", {"AssetPath": ASSET,
            "Operation": "update", "SampleId": state["target_id"],
            "AnimationPath": state["replacement"], "bDryRun": True})["sample_id"] == state["target_id"]
        print("Blend Space sample ID reload stage passed")
    finally:
        request("POST", "/assets/delete", {"AssetPath": ASSET})
        STATE_FILE.unlink(missing_ok=True)
        assert not ASSET_FILE.exists(), ASSET_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("create", "verify"), required=True)
    stage = parser.parse_args().stage
    (create if stage == "create" else verify)()
