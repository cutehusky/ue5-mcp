"""Two-session native Level Instance lifecycle and persistence test."""

import argparse
import json
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
PROJECT = Path(__file__).resolve().parents[5]
SOURCE_A = "/Game/UE5MCP_Test/LI_Source_A"
SOURCE_B = "/Game/UE5MCP_Test/LI_Source_B"
PARENT = "/Game/UE5MCP_Test/LI_Parent"
MAPS = [SOURCE_A, SOURCE_B, PARENT]
STATE = PROJECT / "Saved" / "UE5MCP_Test" / "level-instance-fixture.json"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def load(path):
    call("POST", "/worlds/load", {"WorldPath": path, "DirtyPolicy": "discard", "bConfirm": True})


def transform(x):
    return {"Translation": {"X": x, "Y": 0, "Z": 0},
            "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
            "Scale3D": {"X": 1, "Y": 1, "Z": 1}}


def instance(path):
    return call("GET", "/levels/instances", actor_path=path)["instances"][0]


def operate(path, operation, **options):
    result = call("POST", "/levels/instances/operation", {"ActorPath": path, "Operation": operation, **options})
    assert result["success"], result
    return result


def marker(state, label):
    matches = [actor for actor in state["loaded_actors"] if actor["label"] == label]
    assert matches, state
    return matches[0]


def reject(path, operation, **options):
    response = httpx.post(BASE + "/levels/instances/operation", json={
        "ActorPath": path, "Operation": operation, **options}, timeout=180)
    assert response.status_code >= 400


def cleanup(original):
    load(original)
    for package in reversed(MAPS):
        file = PROJECT / "Content" / (package.removeprefix("/Game/") + ".umap")
        if file.exists():
            call("POST", "/assets/delete", {"AssetPath": package + "." + package.rsplit("/", 1)[-1]})
    STATE.unlink(missing_ok=True)


def capabilities():
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f"Duplicate capability key: {key}"
            result[key] = value
        return result
    response = httpx.get(BASE + "/assets/capabilities", timeout=180)
    response.raise_for_status()
    family = json.loads(response.text, object_pairs_hook=unique_keys)["families"]["level_instance"]
    assert family["inspect"] and family["edit"] and family["spawn_or_create"] and family["validate"]
    assert family["adapter_available"] and family["support_level"] == "partial"
    print("Level Instance capability entry and unique JSON keys: OK")


def setup():
    capabilities()
    assert not STATE.exists()
    for package in MAPS:
        assert not (PROJECT / "Content" / (package.removeprefix("/Game/") + ".umap")).exists()
    original = call("GET", "/worlds/inspect")["world_path"]
    assert original.startswith("/Game/"), "The fixture expects an existing saved editor map to restore"
    success = False
    try:
        for package, label, x in [(SOURCE_A, "LI_Marker_A", 30), (SOURCE_B, "LI_Marker_B", 40)]:
            call("POST", "/worlds/create", {"WorldPath": package, "DirtyPolicy": "discard", "bConfirm": True, "bSave": True})
            actor = call("POST", "/editor/actors/spawn", {
                "ActorClass": "/Script/Engine.TargetPoint", "Location": {"X": x, "Y": 0, "Z": 0}}).strip()
            call("PATCH", "/editor/actors/transform", {"ActorPath": actor, "Label": label, "bSetLabel": True})
            call("POST", "/worlds/save", {})
        call("POST", "/worlds/create", {"WorldPath": PARENT, "DirtyPolicy": "discard", "bConfirm": True, "bSave": True})
        request = {"WorldAssetPath": SOURCE_A, "Label": "LI_MCP_Test", "Transform": transform(100)}
        dry = call("POST", "/levels/instances/create", request | {"bDryRun": True})
        assert dry["success"] and not dry["changed"] and dry["would_change_packages"]
        assert call("GET", "/levels/instances")["instance_count"] == 0
        created = call("POST", "/levels/instances/create", request | {"bSave": True})
        assert created["success"] and created["saved"] and created["transaction_created"], created
        actor = created["actor_path"]
        current = instance(actor)
        assert current["loaded"] and current["runtime_behavior"] == "standalone", current
        assert abs(marker(current, "LI_Marker_A")["location"]["x"] - 130) < 0.01
        assert call("GET", "/levels/instances/validate", actor_path=actor)["instances"][0]["valid"]
        preview = operate(actor, "transform", Transform=transform(200), bDryRun=True)
        assert not preview["changed"] and instance(actor)["transform"]["location"]["x"] == 100
        moved = operate(actor, "transform", Transform=transform(200), bSave=True)
        assert moved["saved"] and abs(marker(instance(actor), "LI_Marker_A")["location"]["x"] - 230) < 0.01
        reject(actor, "unload")
        assert not operate(actor, "unload", bDryRun=True)["changed"] and instance(actor)["loaded"]
        assert not operate(actor, "unload", bConfirm=True)["instance"]["loaded"]
        assert operate(actor, "load")["instance"]["loaded"]
        reject(actor, "set_asset", WorldAssetPath=SOURCE_B)
        changed = operate(actor, "set_asset", WorldAssetPath=SOURCE_B, bConfirm=True, bSave=True)
        assert changed["saved"] and abs(marker(instance(actor), "LI_Marker_B")["location"]["x"] - 240) < 0.01
        reject(actor, "set_asset", WorldAssetPath=PARENT, bConfirm=True)
        guid = instance(actor)["guid"]
        load(SOURCE_B)
        cycle = httpx.post(BASE + "/levels/instances/create", json={"WorldAssetPath": PARENT, "bDryRun": True}, timeout=180)
        assert cycle.status_code >= 400
        assert call("GET", "/levels/instances")["instance_count"] == 0
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({"original": original, "guid": guid}), encoding="utf-8")
        load(original)
        success = True
        print("Native Level Instance lifecycle, transforms, source replacement, and cycle guards: OK; saved fixture ready for restart")
    finally:
        if not success:
            cleanup(original)


def verify():
    saved = json.loads(STATE.read_text(encoding="utf-8"))
    try:
        load(PARENT)
        actors = call("GET", "/levels/instances")["instances"]
        current = next(actor for actor in actors if actor["guid"] == saved["guid"])
        actor = current["actor_path"]
        current = operate(actor, "load")["instance"]
        assert current["world_asset"] == SOURCE_B + ".LI_Source_B"
        assert current["transform"]["location"]["x"] == 200
        assert abs(marker(current, "LI_Marker_B")["location"]["x"] - 240) < 0.01
        assert call("GET", "/levels/instances/validate", actor_path=actor)["instances"][0]["valid"]
        preview = operate(actor, "remove", bDryRun=True)
        assert not preview["changed"] and preview["affected_actor_count"] > 0
        reject(actor, "remove")
        removed = operate(actor, "remove", bConfirm=True, bSave=True)
        assert removed["changed"] and removed["saved"]
        assert call("GET", "/levels/instances")["instance_count"] == 0
        load(saved["original"])
        load(PARENT)
        assert call("GET", "/levels/instances")["instance_count"] == 0
        print("Native Level Instance saved GUID/reference/transform, restart, and confirmed removal: OK")
    finally:
        cleanup(saved["original"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["setup", "verify", "capabilities"])
    mode = parser.parse_args().mode
    if mode == "setup":
        setup()
    elif mode == "verify":
        verify()
    else:
        capabilities()
