"""Two-session timing persistence test; run write, restart editor, then verify."""

import math
import sys
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_TimingPersist"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main(phase):
    if phase == "write":
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        try:
            result = call("PATCH", "/animation-sequences/timing", {
                "AssetPath": asset, "Operation": "set_frame_rate",
                "FrameRateNumerator": 60, "FrameRateDenominator": 1, "bSave": True,
            })
            assert result["changed"] and result["saved"]
            print("Saved disposable timing change for reload check")
        except Exception:
            call("POST", "/assets/delete", {"AssetPath": asset})
            raise
    elif phase == "verify":
        try:
            source = call("GET", "/animation-sequences/inspect", asset_path=SOURCE)
            result = call("GET", "/animation-sequences/inspect", asset_path=DEST)
            assert result["frame_rate"] == {"numerator": 60, "denominator": 1}
            assert result["source_frames"] == source["source_frames"] * 2
            assert math.isclose(result["play_length"], source["play_length"], abs_tol=1e-5)
            key = call("GET", "/animation-sequences/bone-track-keys", asset_path=DEST,
                       bone_name="pelvis", start_frame=2, count=1)["keys"][0]
            original = call("GET", "/animation-sequences/bone-track-keys", asset_path=SOURCE,
                            bone_name="pelvis", start_frame=1, count=1)["keys"][0]
            assert math.isclose(key["translation"]["x"], original["translation"]["x"], abs_tol=1e-4)
            assert call("POST", "/animation-sequences/validate", {"AssetPath": DEST})["valid"]
            print("Timing and resampled key survived editor reload")
        finally:
            call("POST", "/assets/delete", {"AssetPath": DEST})
    else:
        raise SystemExit("usage: smoke_animation_timing_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
