"""Two-session Anim Blueprint transition persistence test; write, restart, verify."""

import math
import sys
import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed"
DEST = "/Game/UE5MCP_Test/ABP_MCP_TransitionPersist"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def first_transition(asset):
    machine = call("GET", "/animation-blueprints/state-machines", asset_path=asset)["state_machines"][0]
    return machine, machine["transitions"][0]


def main(phase):
    if phase == "write":
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        try:
            machine, transition = first_transition(asset)
            original = first_transition(SOURCE)[1]
            result = call("PATCH", "/animation-blueprints/transitions", {
                "AssetPath": asset, "StateMachineGraphPath": machine["graph_path"],
                "TransitionId": transition["id"],
                "bSetCrossfadeDuration": True, "CrossfadeDuration": original["duration"] + 0.07,
                "bSetBlendMode": True, "BlendMode": "Linear", "bSave": True,
            })
            assert result["changed"] and result["saved"]
            assert call("POST", "/animation-blueprints/compile", {"AssetPath": asset, "bSave": True})["valid"]
            print("Saved disposable transition edit for reload check")
        except Exception:
            call("POST", "/assets/delete", {"AssetPath": asset})
            raise
    elif phase == "verify":
        try:
            original = first_transition(SOURCE)[1]
            _, transition = first_transition(DEST)
            assert math.isclose(transition["duration"], original["duration"] + 0.07, abs_tol=1e-5)
            assert transition["blend_mode_name"] == "Linear"
            assert call("POST", "/animation-blueprints/validate", {"AssetPath": DEST})["valid"]
            print("Transition blend edit survived editor reload")
        finally:
            call("POST", "/assets/delete", {"AssetPath": DEST})
    else:
        raise SystemExit("usage: smoke_animation_blueprint_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
