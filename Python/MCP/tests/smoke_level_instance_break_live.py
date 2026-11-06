"""Two-session native recursive break, folders, transforms, and source preservation."""

import argparse
import hashlib
import json

import httpx

from smoke_level_instance_live import (
    BASE, PROJECT, SOURCE_A, SOURCE_B, PARENT, STATE, call, cleanup,
    instance, load, operate, reject, setup as lifecycle_setup, transform,
)


def source_hashes():
    return {package: hashlib.sha256((PROJECT / "Content" / (
        package.removeprefix("/Game/") + ".umap")).read_bytes()).hexdigest()
        for package in (SOURCE_A, SOURCE_B)}


def set_folder(actor, folder):
    call("PATCH", "/editor/actors/transform", {
        "ActorPath": actor, "FolderPath": folder, "bSetFolderPath": True})


def markers():
    return {actor["label"]: actor for actor in call("GET", "/scene/actors/query", search="LI_Marker")["actors"]}


def verify_markers(actors):
    for label, x in [("LI_Marker_A", 730), ("LI_Marker_B", 240)]:
        assert label in actors, actors
        actor = actors[label]
        assert actor["class"] == "/Script/Engine.TargetPoint", actor
        location = actor.get("transform", {}).get("location", actor.get("location"))
        assert abs(location.get("x", location.get("X")) - x) < 0.01, actor
        assert actor["folder"].startswith("Fixtures/LI_MCP_Test/"), actor


def setup():
    lifecycle_setup()
    saved = json.loads(STATE.read_text(encoding="utf-8"))
    success = False
    try:
        load(SOURCE_B)
        set_folder(markers()["LI_Marker_B"]["path"], "SourceB")
        child = call("POST", "/levels/instances/create", {
            "WorldAssetPath": SOURCE_A, "Label": "LI_Nested", "Transform": transform(500), "bSave": True})
        assert child["success"] and child["saved"], child
        set_folder(child["actor_path"], "NestedInstances")
        call("POST", "/worlds/save", {})
        load(PARENT)
        root = next(actor for actor in call("GET", "/levels/instances")["instances"] if actor["guid"] == saved["guid"])
        actor = root["actor_path"]
        set_folder(actor, "Fixtures")
        call("POST", "/worlds/save", {})
        saved["hashes"] = source_hashes()
        preview = operate(actor, "break", BreakDepth=2, bDryRun=True)
        assert preview["breakable_actor_count"] == 2, preview
        assert preview["would_change_packages"] == [PARENT], preview
        assert not preview["changed"] and not preview["instance_removed"] and not preview["undoable"]
        assert preview["resets_undo_history"] and instance(actor)["guid"] == saved["guid"]
        reject(actor, "break", BreakDepth=2)
        for depth in [0, 9]:
            reject(actor, "break", BreakDepth=depth, bConfirm=True)
        reject(actor, "break", bWait=False, bConfirm=True)
        operate(actor, "enter_edit")
        reject(actor, "break", BreakDepth=2, bConfirm=True)
        operate(actor, "discard", bConfirm=True)
        result = operate(actor, "break", BreakDepth=2, bConfirm=True, bSave=True)
        assert result["saved"] and result["instance_removed"] and result["moved_actor_count"] == 2, result
        assert all(a["in_owner_level"] and not a["transient"] for a in result["moved_actors"]), result
        assert not result["dirty_packages"] and not result["errors"], result
        verify_markers({a["label"]: a for a in result["moved_actors"]})
        saved["folders"] = {a["label"]: a["folder"] for a in result["moved_actors"]}
        assert all(a["owner_level"].startswith(PARENT + ".LI_Parent:") for a in result["moved_actors"]), result
        assert call("GET", "/levels/instances")["instance_count"] == 0
        undo = httpx.post(BASE + "/editor/transactions/undo", timeout=180)
        assert undo.status_code >= 400, undo.text
        assert source_hashes() == saved["hashes"]
        STATE.write_text(json.dumps(saved), encoding="utf-8")
        load(saved["original"])
        success = True
        print("Recursive Level Instance break: dry run, guards, native transforms/folders, save, undo reset, unchanged source maps: OK")
    finally:
        if not success:
            cleanup(saved["original"])


def verify():
    saved = json.loads(STATE.read_text(encoding="utf-8"))
    try:
        load(PARENT)
        assert call("GET", "/levels/instances")["instance_count"] == 0
        verify_markers(markers())
        if "folders" in saved:
            assert {label: actor["folder"] for label, actor in markers().items()} == saved["folders"]
        assert source_hashes() == saved["hashes"]
        # An unloaded shallow break preserves the nested instance and does not
        # save unless requested. With KeepFolders disabled, UE copies source folders.
        root = call("POST", "/levels/instances/create", {
            "WorldAssetPath": SOURCE_B, "Label": "LI_Shallow", "Transform": transform(1000), "bLoad": False})
        assert root["success"] and not root["instance"]["loaded"], root
        shallow = operate(root["actor_path"], "break", bConfirm=True, bKeepFolders=False)
        assert shallow["instance_removed"] and shallow["moved_actor_count"] == 2, shallow
        assert not shallow["saved"] and PARENT in shallow["dirty_packages"], shallow
        child = next(a for a in shallow["moved_actors"] if "LevelInstance" in a["class"])
        copied_b = next(a for a in shallow["moved_actors"] if a["label"] == "LI_Marker_B")
        assert copied_b["transform"]["location"]["x"] == 1040 and copied_b["folder"] == "SourceB", copied_b
        assert child["folder"] == "NestedInstances", child
        child_break = operate(child["actor_path"], "break", bConfirm=True, bKeepFolders=False)
        assert child_break["instance_removed"] and child_break["moved_actor_count"] == 1, child_break
        assert child_break["moved_actors"][0]["transform"]["location"]["x"] == 1530, child_break
        assert call("GET", "/levels/instances")["instance_count"] == 0
        # Exercise recursive result checks on this build with an unloaded root.
        root = call("POST", "/levels/instances/create", {
            "WorldAssetPath": SOURCE_B, "Label": "LI_Recursive", "Transform": transform(2000), "bLoad": False})
        recursive = operate(root["actor_path"], "break", BreakDepth=2, bConfirm=True, bSave=True, bKeepFolders=False)
        assert recursive["instance_removed"] and recursive["moved_actor_count"] == 2 and recursive["saved"], recursive
        recursive_actors = {a["label"]: a for a in recursive["moved_actors"]}
        assert recursive_actors["LI_Marker_A"]["transform"]["location"]["x"] == 2530, recursive
        assert recursive_actors["LI_Marker_B"]["transform"]["location"]["x"] == 2040, recursive
        assert call("GET", "/levels/instances")["instance_count"] == 0
        assert source_hashes() == saved["hashes"]
        print("Unloaded shallow/recursive break, retained nested instance, KeepFolders=false, and explicit saving: OK")
        load(SOURCE_B)
        assert any(a["label"] == "LI_Nested" for a in call("GET", "/levels/instances")["instances"])
        assert markers()["LI_Marker_B"]["location"]["X"] == 40
        print("Fresh-editor break persistence and retained nested source map: OK")
    finally:
        cleanup(saved["original"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["setup", "verify"])
    (setup if parser.parse_args().mode == "setup" else verify)()
