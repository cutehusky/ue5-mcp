"""Live built-in animation attribute smoke test. Requires local UE API on 8080."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd"
DEST = "/Game/UE5MCP_Test/AS_MCP_AttributeSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=120)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def attributes(asset):
    return call("GET", "/animation-sequences/attributes", asset_path=asset)["attributes"]


def edit(asset, operation, name, kind, **extra):
    return call("PATCH", "/animation-sequences/attributes", {
        "AssetPath": asset, "Operation": operation, "AttributeName": name,
        "BoneName": "pelvis", "AttributeType": kind, **extra,
    })


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        initial_count = len(attributes(asset))
        assert edit(asset, "add", "MCP_Weight", "float", bDryRun=True)["dry_run"]
        assert len(attributes(asset)) == initial_count
        invalid = httpx.patch(BASE + "/animation-sequences/attributes", json={
            "AssetPath": asset, "Operation": "add", "AttributeName": "MCP_Invalid",
            "BoneName": "MissingBone", "AttributeType": "float"}, timeout=120)
        assert invalid.status_code >= 400
        assert edit(asset, "add", "MCP_Weight", "float")["changed"]
        assert edit(asset, "set_key", "MCP_Weight", "float", Time=0.25, Value="2.5")["changed"]
        weight = next(a for a in attributes(asset) if a["name"] == "MCP_Weight")
        assert weight["bone_name"] == "pelvis" and weight["type"] == "float"
        assert weight["keys"] == [{"time": 0.25, "value": 2.5}]
        assert edit(asset, "add", "MCP_Offset", "vector")["changed"]
        assert edit(asset, "set_key", "MCP_Offset", "vector", Time=0.5, Value="X=1,Y=2,Z=3")["changed"]
        offset = next(a for a in attributes(asset) if a["name"] == "MCP_Offset")
        assert offset["type"] == "vector" and len(offset["keys"]) == 1
        assert edit(asset, "add", "MCP_Count", "integer")["changed"]
        assert edit(asset, "set_key", "MCP_Count", "integer", Time=0.75, Value="3")["changed"]
        assert next(a for a in attributes(asset) if a["name"] == "MCP_Count")["keys"] == [{"time": 0.75, "value": 3}]
        assert edit(asset, "add", "MCP_Label", "string")["changed"]
        assert edit(asset, "set_key", "MCP_Label", "string", Time=1.0, Value="footstep")["changed"]
        assert next(a for a in attributes(asset) if a["name"] == "MCP_Label")["keys"] == [{"time": 1, "value": "footstep"}]
        assert edit(asset, "add", "MCP_Pose", "transform")["changed"]
        assert edit(asset, "set_key", "MCP_Pose", "transform", Time=1.25,
                    Value="1,2,3|0,0,0|1,1,1")["changed"]
        pose = next(a for a in attributes(asset) if a["name"] == "MCP_Pose")
        assert pose["type"] == "transform" and len(pose["keys"]) == 1
        quat_type = "/Script/Engine.QuaternionAnimationAttribute"
        assert edit(asset, "add", "MCP_Quat", quat_type)["changed"]
        assert edit(asset, "set_key", "MCP_Quat", quat_type, Time=1.25,
                    Value="(Value=(X=0,Y=0,Z=0,W=1))")["changed"]
        quat = next(a for a in attributes(asset) if a["name"] == "MCP_Quat")
        assert quat["type"] == quat_type and quat["keys"][0]["value_text"]
        assert call("POST", "/animation-sequences/validate", {"AssetPath": asset})["valid"]
        assert edit(asset, "remove_key", "MCP_Weight", "float", Time=0.25)["changed"]
        assert next(a for a in attributes(asset) if a["name"] == "MCP_Weight")["keys"] == []
        assert edit(asset, "remove", "MCP_Weight", "float")["changed"]
        assert edit(asset, "remove", "MCP_Offset", "vector")["changed"]
        assert edit(asset, "remove", "MCP_Count", "integer")["changed"]
        assert edit(asset, "remove", "MCP_Label", "string")["changed"]
        assert edit(asset, "remove", "MCP_Pose", "transform")["changed"]
        assert edit(asset, "remove", "MCP_Quat", quat_type)["changed"]
        assert len(attributes(asset)) == initial_count
        print("Animation attributes add, key, inspect, validate, and remove: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
