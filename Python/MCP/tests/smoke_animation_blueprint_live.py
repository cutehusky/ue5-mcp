"""Live Animation Blueprint inspection, layout, compile, and validation test."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed"
DEST = "/Game/UE5MCP_Test/ABP_MCP_AnimationSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main():
    summary = call("GET", "/animation-blueprints/inspect", asset_path=SOURCE)
    graphs = call("GET", "/animation-blueprints/graphs", asset_path=SOURCE)["graphs"]
    machines = call("GET", "/animation-blueprints/state-machines", asset_path=SOURCE)["state_machines"]
    variables = call("GET", "/animation-blueprints/variables", asset_path=SOURCE)["variables"]
    validation = call("POST", "/animation-blueprints/validate", {"AssetPath": SOURCE})
    assert summary["target_skeleton"] and summary["graph_count"] == len(graphs)
    assert summary["state_machine_count"] == len(machines)
    assert summary["variable_count"] == len(variables)
    assert all(m["states"] and m["entry_target_id"] for m in machines)
    assert validation["valid"] and not validation["errors"]
    detail = call("GET", "/animation-blueprints/graphs", asset_path=SOURCE, graph_path="AnimGraph")
    assert any(pin["pose_link"] for node in detail["nodes"] for pin in node["pins"])
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        before = call("GET", "/animation-blueprints/graphs", asset_path=asset, graph_path="AnimGraph")
        dry = call("POST", "/animation-blueprints/layout", {
            "AssetPath": asset, "GraphPath": "AnimGraph", "bDryRun": True})
        assert dry["dry_run"]
        assert call("GET", "/animation-blueprints/graphs", asset_path=asset, graph_path="AnimGraph") == before
        assert call("POST", "/animation-blueprints/layout", {
            "AssetPath": asset, "GraphPath": "AnimGraph"})["changed"]
        machine = call("GET", "/animation-blueprints/state-machines", asset_path=asset)["state_machines"][0]
        assert call("POST", "/animation-blueprints/layout", {
            "AssetPath": asset, "GraphPath": machine["graph_path"], "bDryRun": True})["dry_run"]
        assert call("POST", "/animation-blueprints/layout", {
            "AssetPath": asset, "GraphPath": machine["graph_path"]})["changed"]
        transition = machine["transitions"][0]
        change = {"AssetPath": asset, "StateMachineGraphPath": machine["graph_path"],
                  "TransitionId": transition["id"], "bSetCrossfadeDuration": True,
                  "CrossfadeDuration": transition["duration"] + 0.15,
                  "bSetPriorityOrder": True, "PriorityOrder": transition["priority"] + 1,
                  "bSetBlendMode": True, "BlendMode": "Linear",
                  "bSetDisabled": True, "bDisabled": not transition["disabled"]}
        assert call("PATCH", "/animation-blueprints/transitions", change | {"bDryRun": True})["dry_run"]
        assert call("GET", "/animation-blueprints/state-machines", asset_path=asset)["state_machines"][0]["transitions"][0] == transition
        invalid = httpx.patch(BASE + "/animation-blueprints/transitions",
                              json=change | {"CrossfadeDuration": -1}, timeout=120)
        assert invalid.status_code >= 400
        assert call("PATCH", "/animation-blueprints/transitions", change)["changed"]
        updated = call("GET", "/animation-blueprints/state-machines", asset_path=asset)["state_machines"][0]["transitions"][0]
        assert updated["duration"] == transition["duration"] + 0.15
        assert updated["priority"] == transition["priority"] + 1
        assert updated["blend_mode_name"] == "Linear"
        assert updated["disabled"] != transition["disabled"]
        assert not call("PATCH", "/animation-blueprints/transitions", change)["changed"]
        compiled = call("POST", "/animation-blueprints/compile", {"AssetPath": asset})
        assert compiled["valid"]
        assert call("POST", "/animation-blueprints/validate", {"AssetPath": asset})["valid"]
        print("Animation Blueprint graphs, states, transitions, layout, and compile: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
