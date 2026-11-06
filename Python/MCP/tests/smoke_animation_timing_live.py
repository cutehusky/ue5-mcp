"""Live Animation Sequence frame-rate and resize test on a disposable duplicate."""

import math
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_TimingSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def inspect(asset):
    return call("GET", "/animation-sequences/inspect", asset_path=asset)


def key(asset, frame):
    return call("GET", "/animation-sequences/bone-track-keys", asset_path=asset,
                bone_name="pelvis", start_frame=frame, count=1)["keys"][0]


def timing(asset, operation, **extra):
    return call("PATCH", "/animation-sequences/timing", {
        "AssetPath": asset, "Operation": operation, **extra,
    })


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        before = inspect(asset)
        old_key = key(asset, 1)
        assert before["frame_rate"] == {"numerator": 30, "denominator": 1}
        assert timing(asset, "set_frame_rate", FrameRateNumerator=60,
                      FrameRateDenominator=1, bDryRun=True)["dry_run"]
        assert inspect(asset)["source_frames"] == before["source_frames"]
        bad = httpx.patch(BASE + "/animation-sequences/timing", json={
            "AssetPath": asset, "Operation": "set_frame_rate",
            "FrameRateNumerator": 24, "FrameRateDenominator": 1}, timeout=120)
        assert bad.status_code >= 400
        assert timing(asset, "set_frame_rate", FrameRateNumerator=60,
                      FrameRateDenominator=1)["changed"]
        doubled = inspect(asset)
        assert doubled["frame_rate"] == {"numerator": 60, "denominator": 1}
        assert doubled["source_frames"] == 2 * before["source_frames"]
        assert math.isclose(doubled["play_length"], before["play_length"], abs_tol=1e-5)
        assert math.isclose(key(asset, 2)["translation"]["x"], old_key["translation"]["x"], abs_tol=1e-4)
        assert call("POST", "/animation-sequences/validate", {"AssetPath": asset})["valid"]
        assert timing(asset, "set_frame_rate", FrameRateNumerator=30,
                      FrameRateDenominator=1)["changed"]
        assert timing(asset, "resize", SourceFrames=50)["changed"]
        assert inspect(asset)["source_keys"] == 51
        trim = httpx.patch(BASE + "/animation-sequences/timing", json={
            "AssetPath": asset, "Operation": "resize", "SourceFrames": 44}, timeout=120)
        assert trim.status_code >= 400
        assert timing(asset, "resize", SourceFrames=44, bConfirmTrim=True)["changed"]
        assert inspect(asset)["source_keys"] == 45
        assert call("POST", "/animation-sequences/validate", {"AssetPath": asset})["valid"]
        print("Animation timing frame-rate resample, resize, and validation: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
