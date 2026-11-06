"""Live Animation Sequence inspection/validation test. Requires local UE API on 8080."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_SequenceSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=120)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main():
    inspect = call("GET", "/animation-sequences/inspect", asset_path=SOURCE)
    tracks = call("GET", "/animation-sequences/tracks", asset_path=SOURCE)
    timeline = call("GET", "/animation-sequences/timeline", asset_path=SOURCE)
    validation = call("POST", "/animation-sequences/validate", {"AssetPath": SOURCE})
    assert inspect["sampled_keys"] == inspect["source_keys"]
    assert inspect["bone_track_count"] == len(tracks["bone_tracks"])
    assert inspect["sync_marker_count"] == len(timeline["sync_markers"])
    assert all(track["skeleton_bone_index"] >= 0 for track in tracks["bone_tracks"])
    assert validation["valid"] and not validation["errors"]
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        compression = call("GET", "/animation-sequences/compression", asset_path=asset)
        assert compression["bone_settings_path"] and compression["curve_settings_path"]
        compression_edit = {"AssetPath": asset, "BoneSettingsPath": compression["bone_settings_path"],
                            "bSetAllowFrameStripping": True,
                            "bAllowFrameStripping": not compression["allow_frame_stripping"],
                            "bSetErrorThresholdScale": True, "ErrorThresholdScale": 1.25}
        assert call("PATCH", "/animation-sequences/compression", compression_edit | {"bDryRun": True})["dry_run"]
        assert call("GET", "/animation-sequences/compression", asset_path=asset)["allow_frame_stripping"] == compression["allow_frame_stripping"]
        bad_compression = httpx.patch(BASE + "/animation-sequences/compression",
                                      json=compression_edit | {"ErrorThresholdScale": 0.0}, timeout=120)
        assert bad_compression.status_code >= 400
        assert call("PATCH", "/animation-sequences/compression", compression_edit)["changed"]
        edited_compression = call("GET", "/animation-sequences/compression", asset_path=asset)
        assert edited_compression["allow_frame_stripping"] != compression["allow_frame_stripping"]
        assert edited_compression["error_threshold_scale"] == 1.25
        assert not call("PATCH", "/animation-sequences/compression", compression_edit)["changed"]
        bad_marker = httpx.post(BASE + "/animations/notifies", json={
            "AssetPath": asset, "Operation": "add_sync_marker", "NotifyName": "MCP_OutOfRange",
            "NotifyTrack": timeline["notify_tracks"][0], "Time": inspect["play_length"] + 1.0,
        }, timeout=120)
        assert bad_marker.status_code >= 400
        assert len(call("GET", "/animation-sequences/timeline", asset_path=asset)["sync_markers"]) == inspect["sync_marker_count"]
        call("PATCH", "/assets/properties", {"AssetPath": asset, "Properties": {
            "AuthoredSyncMarkers.0.Time": str(inspect["play_length"] + 1.0)}})
        invalid = call("POST", "/animation-sequences/validate", {"AssetPath": asset})
        assert not invalid["valid"]
        assert any("Sync marker lies outside" in error for error in invalid["errors"])
        print("Animation Sequence inspect, tracks, timeline, and validation: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
