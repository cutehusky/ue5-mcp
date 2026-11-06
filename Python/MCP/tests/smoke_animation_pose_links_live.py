"""Live pose-link disconnect/reconnect test on a disposable Animation Blueprint."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed"
DEST = "/Game/UE5MCP_Test/ABP_MCP_PoseLinkSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def graph(asset):
    return call("GET", "/animation-blueprints/graphs", asset_path=asset, graph_path="AnimGraph")


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        before = graph(asset)
        root = next(n for n in before["nodes"] if n["class"].endswith("AnimGraphNode_Root"))
        result = next(p for p in root["pins"] if p["pose_link"] and p["direction"] == "input")
        linked = result["links"][0]
        request = {"AssetPath": asset, "GraphPath": "AnimGraph",
                   "OutputNodeId": linked["node_id"], "OutputPinName": linked["pin_name"],
                   "InputNodeId": root["id"], "InputPinName": result["name"]}
        assert call("PATCH", "/animation-blueprints/pose-links", request | {
            "Operation": "disconnect", "bDryRun": True})["dry_run"]
        assert graph(asset) == before
        assert call("PATCH", "/animation-blueprints/pose-links", request | {
            "Operation": "disconnect"})["changed"]
        disconnected = graph(asset)
        root_after = next(n for n in disconnected["nodes"] if n["id"] == root["id"])
        assert next(p for p in root_after["pins"] if p["name"] == result["name"])["links"] == []
        assert call("PATCH", "/animation-blueprints/pose-links", request | {
            "Operation": "connect", "bDryRun": True})["dry_run"]
        assert call("PATCH", "/animation-blueprints/pose-links", request | {
            "Operation": "connect"})["changed"]
        assert not call("PATCH", "/animation-blueprints/pose-links", request | {
            "Operation": "connect"})["changed"]
        alternative_node = next(n for n in before["nodes"] if n["id"] != linked["node_id"]
                                and any(p["pose_link"] and p["direction"] == "output" for p in n["pins"]))
        alternative_pin = next(p for p in alternative_node["pins"]
                               if p["pose_link"] and p["direction"] == "output")
        alternative = request | {"OutputNodeId": alternative_node["id"],
                                 "OutputPinName": alternative_pin["name"], "Operation": "connect"}
        refused = httpx.patch(BASE + "/animation-blueprints/pose-links", json=alternative, timeout=120)
        assert refused.status_code >= 400
        assert call("PATCH", "/animation-blueprints/pose-links", alternative | {
            "bConfirmReplace": True})["changed"]
        assert call("PATCH", "/animation-blueprints/pose-links", request | {
            "Operation": "connect", "bConfirmReplace": True})["changed"]
        assert call("POST", "/animation-blueprints/compile", {"AssetPath": asset})["valid"]
        assert call("POST", "/animation-blueprints/validate", {"AssetPath": asset})["valid"]
        print("Animation Blueprint pose-link disconnect/reconnect and compile: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
