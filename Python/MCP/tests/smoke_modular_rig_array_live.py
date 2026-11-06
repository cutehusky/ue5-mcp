"""Two-stage array connector smoke test.

Run --stage module, create_modular_rig_fixture.py in a restarted editor,
then run --stage rig against the API editor.
"""

import argparse
from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
MODULE = "/Game/UE5MCP_Test/CR_MCP_ArrayModule.CR_MCP_ArrayModule"
MODULE_FILE = PROJECT / "Content" / "UE5MCP_Test" / "CR_MCP_ArrayModule.uasset"
RIG = "/Game/UE5MCP_Test/MR_MCP_Fixture.MR_MCP_Fixture"
RIG_FILE = PROJECT / "Content" / "UE5MCP_Test" / "MR_MCP_Fixture.uasset"


def module_stage():
    assert not MODULE_FILE.exists(), MODULE_FILE
    asset = request("POST", "/assets/duplicate", {
        "AssetPath": "/ControlRig/Modules/Modules56/Root.Root",
        "DestinationPath": "/Game/UE5MCP_Test/CR_MCP_ArrayModule"})
    assert asset == MODULE, asset
    try:
        request("POST", "/control-rigs/hierarchy", {"AssetPath": MODULE,
            "Operation": "add", "ElementType": "connector", "Name": "MCP_Array",
            "ConnectorType": "secondary", "bIsArray": True})
        connector = next(item for item in request("GET", "/control-rigs/hierarchy",
            params={"asset_path": MODULE}) if item["name"] == "MCP_Array")
        assert connector["connector_type"] == "secondary" and connector["array"]
        compiled = request("POST", "/control-rigs/compile", {"AssetPath": MODULE, "bSave": True})
        assert compiled["valid"] and compiled["errors"] == 0 and compiled["saved"], compiled
        assert MODULE_FILE.exists(), MODULE_FILE
        print("Modular Rig array module stage passed")
    except BaseException:
        request("POST", "/assets/delete", {"AssetPath": MODULE})
        raise


def rig_stage():
    assert MODULE_FILE.exists() and RIG_FILE.exists(), "Both fixture assets are required"
    try:
        initial = request("GET", "/modular-rigs/modules", params={"asset_path": RIG})
        assert len(initial) == 1 and initial[0]["name"] == "Root", initial
        request("POST", "/modular-rigs/modules", {"AssetPath": RIG,
            "Operation": "add", "ModuleName": "MCP_ArrayModule", "ParentName": "Root",
            "ModuleClassPath": "/Game/UE5MCP_Test/CR_MCP_ArrayModule.CR_MCP_ArrayModule_C"})
        unresolved = request("GET", "/modular-rigs/connections",
                             params={"asset_path": RIG})["unresolved"]
        assert "MCP_ArrayModule/MCP_Array" in {item["name"] for item in unresolved}, unresolved

        for name in ("MCP_RootTarget", "MCP_ChildTarget", "MCP_ArrayA", "MCP_ArrayB"):
            request("POST", "/control-rigs/hierarchy", {"AssetPath": RIG,
                "Operation": "add", "ElementType": "null", "Name": name})
        for connector, target in (("Root/Root", "MCP_RootTarget"),
                                  ("MCP_ArrayModule/Root", "MCP_ChildTarget")):
            request("POST", "/modular-rigs/connections", {"AssetPath": RIG,
                "Operation": "connect", "ConnectorName": connector,
                "TargetType": "null", "TargetName": target})

        base = {"AssetPath": RIG, "ConnectorName": "MCP_ArrayModule/MCP_Array"}
        targets = [{"Name": "MCP_ArrayA", "Type": "null"},
                   {"Name": "MCP_ArrayB", "Type": "null"}]
        assert request("POST", "/modular-rigs/connections", {**base,
            "Operation": "set_targets", "Targets": targets,
            "bDryRun": True})["target_count"] == 2
        request("POST", "/modular-rigs/connections", {**base,
            "Operation": "set_targets", "Targets": targets})
        matching = next(item for item in request("GET", "/modular-rigs/connections",
            params={"asset_path": RIG})["connections"] if item["connector"] == base["ConnectorName"])
        assert [item["name"] for item in matching["targets"]] == ["MCP_ArrayA", "MCP_ArrayB"]

        request("POST", "/modular-rigs/connections", {**base,
            "Operation": "remove_target", "TargetType": "null", "TargetName": "MCP_ArrayB"})
        request("POST", "/modular-rigs/connections", {**base,
            "Operation": "add_target", "TargetType": "null", "TargetName": "MCP_ArrayB"})
        validated = request("GET", "/modular-rigs/validate", params={"asset_path": RIG})
        assert validated["valid"] and validated["required_unresolved"] == 0, validated
        compiled = request("POST", "/modular-rigs/compile", {"AssetPath": RIG, "bSave": True})
        assert compiled["valid"] and compiled["errors"] == 0 and compiled["saved"], compiled
        print("Modular Rig array connection stage passed")
    finally:
        request("POST", "/assets/delete", {"AssetPath": RIG})
        request("POST", "/assets/delete", {"AssetPath": MODULE})
        assert not RIG_FILE.exists() and not MODULE_FILE.exists(), "Array test assets were not deleted"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("module", "rig"), required=True)
    (module_stage if parser.parse_args().stage == "module" else rig_stage)()
