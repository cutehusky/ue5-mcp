"""Live Animation Sequence bone-track test on a disposable duplicate."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_BoneTrackSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def track_keys(asset, start=0, count=2):
    return call("GET", "/animation-sequences/bone-track-keys", asset_path=asset,
                bone_name="pelvis", start_frame=start, count=count)


def edit(asset, operation, **extra):
    return call("PATCH", "/animation-sequences/bone-tracks", {
        "AssetPath": asset, "BoneName": "pelvis", "Operation": operation, **extra,
    })


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        before = track_keys(asset)
        count = len(call("GET", "/animation-sequences/tracks", asset_path=asset)["bone_tracks"])
        assert before["total_keys"] > 2 and len(before["keys"]) == 2
        replacement = {"FrameIndex": 1, "Translation": {"X": 12, "Y": 0, "Z": 0},
                       "Rotation": {"Pitch": 0, "Yaw": 0, "Roll": 0},
                       "Scale": {"X": 1, "Y": 1, "Z": 1}}
        assert edit(asset, "set_key", **replacement, bDryRun=True)["dry_run"]
        assert track_keys(asset)["keys"] == before["keys"]
        invalid = httpx.patch(BASE + "/animation-sequences/bone-tracks", json={
            "AssetPath": asset, "BoneName": "pelvis", "Operation": "set_key",
            "FrameIndex": before["total_keys"]}, timeout=120)
        assert invalid.status_code >= 400
        assert edit(asset, "set_key", **replacement)["changed"]
        assert track_keys(asset)["keys"][1]["translation"]["x"] == 12
        assert not edit(asset, "set_key", **replacement)["changed"]
        assert call("POST", "/animation-sequences/validate", {"AssetPath": asset})["valid"]
        assert edit(asset, "remove")["changed"]
        assert len(call("GET", "/animation-sequences/tracks", asset_path=asset)["bone_tracks"]) == count - 1
        assert edit(asset, "add")["changed"]
        assert len(call("GET", "/animation-sequences/tracks", asset_path=asset)["bone_tracks"]) == count
        assert track_keys(asset)["total_keys"] == before["total_keys"]
        assert call("POST", "/animation-sequences/validate", {"AssetPath": asset})["valid"]
        print("Animation bone tracks inspect, key edit, remove, and add: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
