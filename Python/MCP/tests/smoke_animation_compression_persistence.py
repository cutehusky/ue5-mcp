"""Two-session Animation Sequence compression test; run write, restart editor, run verify."""

import sys
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_CompressionPersist"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def compression(asset):
    return call("GET", "/animation-sequences/compression", asset_path=asset)


def main(phase):
    if phase == "write":
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        try:
            source = compression(SOURCE)
            changed = call("PATCH", "/animation-sequences/compression", {
                "AssetPath": asset, "bSetAllowFrameStripping": True,
                "bAllowFrameStripping": not source["allow_frame_stripping"],
                "bSetErrorThresholdScale": True, "ErrorThresholdScale": 1.75,
                "bSave": True,
            })
            assert changed["changed"] and changed["saved"]
            print("Saved disposable compression changes for reload check")
        except Exception:
            call("POST", "/assets/delete", {"AssetPath": asset})
            raise
    elif phase == "verify":
        try:
            source = compression(SOURCE)
            result = compression(DEST)
            assert result["allow_frame_stripping"] != source["allow_frame_stripping"]
            assert result["error_threshold_scale"] == 1.75
            assert call("POST", "/animation-sequences/validate", {"AssetPath": DEST})["valid"]
            print("Compression changes survived editor reload")
        finally:
            call("POST", "/assets/delete", {"AssetPath": DEST})
    else:
        raise SystemExit("usage: smoke_animation_compression_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
