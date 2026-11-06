"""Two-session bone-track key persistence test; run write, restart editor, verify."""

import sys
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_BoneTrackPersist"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main(phase):
    if phase == "write":
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        try:
            result = call("PATCH", "/animation-sequences/bone-tracks", {
                "AssetPath": asset, "Operation": "set_key", "BoneName": "pelvis", "FrameIndex": 1,
                "Translation": {"X": 42, "Y": 0, "Z": 0},
                "Rotation": {"Pitch": 0, "Yaw": 0, "Roll": 0},
                "Scale": {"X": 1, "Y": 1, "Z": 1}, "bSave": True,
            })
            assert result["changed"] and result["saved"]
            print("Saved disposable bone-track key for reload check")
        except Exception:
            call("POST", "/assets/delete", {"AssetPath": asset})
            raise
    elif phase == "verify":
        try:
            result = call("GET", "/animation-sequences/bone-track-keys", asset_path=DEST,
                          bone_name="pelvis", start_frame=1, count=1)
            assert result["keys"][0]["translation"]["x"] == 42
            assert call("POST", "/animation-sequences/validate", {"AssetPath": DEST})["valid"]
            print("Bone-track key survived editor reload")
        finally:
            call("POST", "/assets/delete", {"AssetPath": DEST})
    else:
        raise SystemExit("usage: smoke_animation_bone_track_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
