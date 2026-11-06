"""Two-session state-machine persistence test; run write, restart editor, verify."""

import sys
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed"
DEST = "/Game/UE5MCP_Test/ABP_MCP_StatePersist"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def machine(asset):
    return call("GET", "/animation-blueprints/state-machines", asset_path=asset)["state_machines"][0]


def main(phase):
    if phase == "write":
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        try:
            before = machine(asset)
            common = {"AssetPath": asset, "StateMachineGraphPath": before["graph_path"]}
            added = call("PATCH", "/animation-blueprints/state-machines", common | {
                "Operation": "add_state", "StateName": "MCP_Persistent", "X": 800, "Y": 300})
            assert added["changed"]
            assert call("PATCH", "/animation-blueprints/state-machines", common | {
                "Operation": "set_reset", "NodeId": added["node_id"],
                "bAlwaysResetOnEntry": True})["changed"]
            linked = call("PATCH", "/animation-blueprints/state-machines", common | {
                "Operation": "add_transition", "FromStateId": before["entry_target_id"],
                "ToStateId": added["node_id"], "X": 700, "Y": 200})
            assert linked["changed"]
            assert call("POST", "/animation-blueprints/compile", {"AssetPath": asset, "bSave": True})["valid"]
            print("Saved disposable state and transition for reload check")
        except Exception:
            call("POST", "/assets/delete", {"AssetPath": asset})
            raise
    elif phase == "verify":
        try:
            saved = machine(DEST)
            state = next(s for s in saved["states"] if s["name"] == "MCP_Persistent")
            transition = next(t for t in saved["transitions"] if t["to_state_id"] == state["id"])
            assert state["bound_graph"] and state["always_reset_on_entry"] and transition["rule_graph"]
            assert transition["from_state_id"] == saved["entry_target_id"]
            assert call("POST", "/animation-blueprints/validate", {"AssetPath": DEST})["valid"]
            print("State and transition survived editor reload")
        finally:
            call("POST", "/assets/delete", {"AssetPath": DEST})
    else:
        raise SystemExit("usage: smoke_animation_state_machine_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
