"""Live Animation Blueprint state-machine structural edit test on a duplicate."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed"
DEST = "/Game/UE5MCP_Test/ABP_MCP_StateMachineSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def machine(asset, graph_path=None):
    machines = call("GET", "/animation-blueprints/state-machines", asset_path=asset)["state_machines"]
    return next(m for m in machines if m["graph_path"] == graph_path) if graph_path else machines[0]


def edit(asset, graph_path, operation, **extra):
    return call("PATCH", "/animation-blueprints/state-machines", {
        "AssetPath": asset, "StateMachineGraphPath": graph_path,
        "Operation": operation, **extra,
    })


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        original = machine(asset)
        path = original["graph_path"]
        entry_id = original["entry_target_id"]
        assert edit(asset, path, "add_state", StateName="MCP_Temporary", bDryRun=True)["dry_run"]
        assert len(machine(asset, path)["states"]) == len(original["states"])
        duplicate = httpx.patch(BASE + "/animation-blueprints/state-machines", json={
            "AssetPath": asset, "StateMachineGraphPath": path,
            "Operation": "add_state", "StateName": original["states"][0]["name"]}, timeout=120)
        assert duplicate.status_code >= 400
        added = edit(asset, path, "add_state", StateName="MCP_Temporary", X=800, Y=300)
        assert added["changed"] and added["node_id"]
        new_id = added["node_id"]
        created = machine(asset, path)
        state = next(s for s in created["states"] if s["id"] == new_id)
        assert state["name"] == "MCP_Temporary" and state["bound_graph"]
        assert edit(asset, path, "rename_state", NodeId=new_id, StateName="MCP_Renamed")["changed"]
        assert edit(asset, path, "set_reset", NodeId=new_id, bAlwaysResetOnEntry=True)["changed"]
        renamed = next(s for s in machine(asset, path)["states"] if s["id"] == new_id)
        assert renamed["name"] == "MCP_Renamed" and renamed["always_reset_on_entry"]
        refused_entry_delete = httpx.patch(BASE + "/animation-blueprints/state-machines", json={
            "AssetPath": asset, "StateMachineGraphPath": path, "Operation": "remove_state",
            "NodeId": entry_id, "bConfirm": True}, timeout=120)
        assert refused_entry_delete.status_code >= 400
        linked = edit(asset, path, "add_transition", FromStateId=entry_id,
                      ToStateId=new_id, X=700, Y=200)
        assert linked["changed"] and linked["node_id"]
        transition = next(t for t in machine(asset, path)["transitions"] if t["id"] == linked["node_id"])
        assert transition["from_state_id"] == entry_id and transition["to_state_id"] == new_id
        assert transition["rule_graph"]
        unconfirmed = httpx.patch(BASE + "/animation-blueprints/state-machines", json={
            "AssetPath": asset, "StateMachineGraphPath": path, "Operation": "remove_transition",
            "NodeId": linked["node_id"]}, timeout=120)
        assert unconfirmed.status_code >= 400
        assert edit(asset, path, "remove_transition", NodeId=linked["node_id"], bConfirm=True)["changed"]
        assert edit(asset, path, "set_entry", NodeId=new_id)["changed"]
        assert machine(asset, path)["entry_target_id"] == new_id
        assert edit(asset, path, "set_entry", NodeId=entry_id)["changed"]
        assert machine(asset, path)["entry_target_id"] == entry_id
        assert edit(asset, path, "remove_state", NodeId=new_id, bConfirm=True)["changed"]
        restored = machine(asset, path)
        assert len(restored["states"]) == len(original["states"])
        assert len(restored["transitions"]) == len(original["transitions"])
        assert call("POST", "/animation-blueprints/compile", {"AssetPath": asset})["valid"]
        assert call("POST", "/animation-blueprints/validate", {"AssetPath": asset})["valid"]
        print("Animation Blueprint state/transition lifecycle and entry reassignment: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
