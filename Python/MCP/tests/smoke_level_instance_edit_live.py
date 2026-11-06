"""Native Level Instance source-edit/commit/discard with two-session persistence."""

import argparse
import json

from smoke_level_instance_live import (BASE, PROJECT, STATE, SOURCE_B, PARENT, call, load,
                                      transform, instance, marker, operate, reject, cleanup, setup as lifecycle_setup)


def move(path, x):
    call("PATCH", "/editor/actors/transform", {
        "ActorPath": path, "Location": {"X": x, "Y": 0, "Z": 0}, "bSetLocation": True})


def setup():
    lifecycle_setup()
    saved = json.loads(STATE.read_text(encoding="utf-8"))
    actor = ""
    success = False
    try:
        load(PARENT)
        actor = next(item["actor_path"] for item in call("GET", "/levels/instances")["instances"]
                     if item["guid"] == saved["guid"])
        second = call("POST", "/levels/instances/create", {
            "WorldAssetPath": SOURCE_B, "Label": "LI_MCP_Second", "Transform": transform(1000), "bSave": True})
        assert second["success"] and second["saved"], second
        second_path = second["actor_path"]
        source_file = PROJECT / "Content" / "UE5MCP_Test" / "LI_Source_B.umap"
        before = source_file.read_bytes()
        preview = operate(actor, "enter_edit", bDryRun=True)
        assert not preview["changed"] and not instance(actor)["editing_source"]
        entered = operate(actor, "enter_edit")
        assert entered["changed"] and entered["instance"]["editing_source"] and entered["instance"]["has_loaded_content"], entered
        editing_actor = marker(instance(actor), "LI_Marker_B")["actor_path"]
        move(editing_actor, 275)
        dirty = instance(actor)
        assert dirty["editing_dirty"] and dirty["edit_dirty_packages"], dirty
        reject(actor, "unload", bConfirm=True)
        preview_commit = operate(actor, "commit", bDryRun=True)
        assert preview_commit["save_required"] and not preview_commit["changed"] and preview_commit["dirty_packages_before"]
        reject(actor, "commit")
        assert instance(actor)["editing_source"] and source_file.read_bytes() == before
        committed = operate(actor, "commit", bSave=True)
        assert committed["saved"] and committed["changed"] and committed["saved_packages"], committed
        assert not instance(actor)["editing_source"]
        assert abs(marker(instance(actor), "LI_Marker_B")["location"]["x"] - 275) < 0.01
        assert abs(marker(instance(second_path), "LI_Marker_B")["location"]["x"] - 1075) < 0.01
        committed_bytes = source_file.read_bytes()
        assert committed_bytes != before

        operate(actor, "enter_edit")
        move(marker(instance(actor), "LI_Marker_B")["actor_path"], 310)
        assert instance(actor)["editing_dirty"]
        reject(actor, "discard")
        preview_discard = operate(actor, "discard", bDryRun=True)
        assert preview_discard["confirmation_required"] and not preview_discard["changed"]
        discarded = operate(actor, "discard", bConfirm=True)
        assert discarded["discarded_changes"] and not discarded["saved"], discarded
        assert not instance(actor)["editing_source"] and source_file.read_bytes() == committed_bytes
        assert abs(marker(instance(actor), "LI_Marker_B")["location"]["x"] - 275) < 0.01

        operate(actor, "enter_edit")
        assert not instance(actor)["editing_dirty"]
        clean_exit = operate(actor, "commit")
        assert clean_exit["changed"] and not clean_exit["saved"] and not instance(actor)["editing_source"]
        load(saved["original"])
        success = True
        print("Level Instance source editing, explicit commit/save, shared-instance update, confirmed discard, and clean exit: OK; ready for restart")
    finally:
        if not success:
            if actor:
                try:
                    if instance(actor)["editing_source"]:
                        operate(actor, "discard", bConfirm=True)
                except Exception:
                    pass
            cleanup(saved["original"])


def verify():
    saved = json.loads(STATE.read_text(encoding="utf-8"))
    try:
        load(PARENT)
        current = call("GET", "/levels/instances")["instances"]
        assert len(current) == 2
        first = next(item for item in current if item["guid"] == saved["guid"])
        second = next(item for item in current if item["label"] == "LI_MCP_Second")
        first = operate(first["actor_path"], "load")["instance"]
        second = operate(second["actor_path"], "load")["instance"]
        assert abs(marker(first, "LI_Marker_B")["location"]["x"] - 275) < 0.01
        assert abs(marker(second, "LI_Marker_B")["location"]["x"] - 1075) < 0.01
        load(SOURCE_B)
        actors = call("GET", "/editor/actors", search="LI_Marker_B")
        assert len(actors) == 1 and abs(actors[0]["location"]["X"] - 75) < 0.01
        print("Level Instance committed source coordinates and both instances survived editor restart; discarded edit absent: OK")
    finally:
        cleanup(saved["original"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["setup", "verify"])
    mode = parser.parse_args().mode
    setup() if mode == "setup" else verify()
