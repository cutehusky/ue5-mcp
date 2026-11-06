"""Two-session attribute persistence test; run write, restart editor, then verify."""

import sys
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_AttributePersist"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main(phase):
    if phase == "write":
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        try:
            common = {"AssetPath": asset, "AttributeName": "MCP_Persist",
                      "BoneName": "pelvis", "AttributeType": "float"}
            assert call("PATCH", "/animation-sequences/attributes", common | {"Operation": "add"})["changed"]
            result = call("PATCH", "/animation-sequences/attributes", common | {
                "Operation": "set_key", "Time": 0.25, "Value": "4.25"})
            assert result["changed"]
            transform = {"AssetPath": asset, "AttributeName": "MCP_TransformPersist",
                         "BoneName": "pelvis", "AttributeType": "transform"}
            assert call("PATCH", "/animation-sequences/attributes", transform | {"Operation": "add"})["changed"]
            assert call("PATCH", "/animation-sequences/attributes", transform | {
                "Operation": "set_key", "Time": 0.5, "Value": "1,2,3|0,0,0|1,1,1"})["changed"]
            quaternion = {"AssetPath": asset, "AttributeName": "MCP_QuatPersist",
                          "BoneName": "pelvis", "AttributeType": "/Script/Engine.QuaternionAnimationAttribute"}
            assert call("PATCH", "/animation-sequences/attributes", quaternion | {"Operation": "add"})["changed"]
            result = call("PATCH", "/animation-sequences/attributes", quaternion | {
                "Operation": "set_key", "Time": 0.75, "Value": "(Value=(X=0,Y=0,Z=0,W=1))", "bSave": True})
            assert result["changed"] and result["saved"]
            print("Saved disposable attribute for reload check")
        except Exception:
            call("POST", "/assets/delete", {"AssetPath": asset})
            raise
    elif phase == "verify":
        try:
            attributes = call("GET", "/animation-sequences/attributes", asset_path=DEST)["attributes"]
            item = next(a for a in attributes if a["name"] == "MCP_Persist")
            assert item["type"] == "float" and item["bone_name"] == "pelvis"
            assert item["keys"] == [{"time": 0.25, "value": 4.25}]
            transform = next(a for a in attributes if a["name"] == "MCP_TransformPersist")
            assert transform["type"] == "transform" and transform["keys"][0]["value"]
            quaternion = next(a for a in attributes if a["name"] == "MCP_QuatPersist")
            assert quaternion["type"] == "/Script/Engine.QuaternionAnimationAttribute"
            assert quaternion["keys"][0]["value_text"]
            assert call("POST", "/animation-sequences/validate", {"AssetPath": DEST})["valid"]
            print("Animation attribute survived editor reload")
        finally:
            call("POST", "/assets/delete", {"AssetPath": DEST})
    else:
        raise SystemExit("usage: smoke_animation_attribute_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
