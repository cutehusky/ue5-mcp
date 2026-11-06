"""Exercise Modular Rig modules, connectors, validation, and compile on a fixture."""

from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
ASSET = "/Game/UE5MCP_Test/MR_MCP_Fixture.MR_MCP_Fixture"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "MR_MCP_Fixture.uasset"


def modules():
    return request("GET", "/modular-rigs/modules", params={"asset_path": ASSET})


def connections():
    return request("GET", "/modular-rigs/connections", params={"asset_path": ASSET})


def dependencies():
    return request("GET", "/modular-rigs/dependencies", params={"asset_path": ASSET})


def main():
    assert ASSET_FILE.exists(), "Create the fixture with create_modular_rig_fixture.py first"
    try:
        initial = modules()
        assert len(initial) == 1 and initial[0]["name"] == "Root", initial
        assert initial[0]["class"], initial
        initial_validation = request("GET", "/modular-rigs/validate",
                                     params={"asset_path": ASSET})
        assert not initial_validation["valid"] and initial_validation["required_unresolved"] == 1
        assert connections()["unresolved"][0]["name"] == "Root/Root"
        initial_dependencies = dependencies()
        assert initial_dependencies["module_count"] == 1, initial_dependencies
        assert initial_dependencies["unresolved_connector_count"] == 1, initial_dependencies
        assert initial_dependencies["unresolved_connectors"] == [
            {"name": "Root/Root", "module": "Root", "required": True}], initial_dependencies

        add = {"AssetPath": ASSET, "Operation": "add", "ModuleName": "MCP_Module",
               "ModuleClassPath": initial[0]["class"]}
        assert not request("POST", "/modular-rigs/modules", {**add, "bDryRun": True})["changed"]
        request("POST", "/modular-rigs/modules", add)
        request("POST", "/modular-rigs/modules", {"AssetPath": ASSET,
            "Operation": "reparent", "ModuleName": "MCP_Module", "ParentName": "Root"})
        request("POST", "/modular-rigs/modules", {"AssetPath": ASSET,
            "Operation": "rename", "ModuleName": "MCP_Module", "NewName": "MCP_Renamed"})
        renamed = next(m for m in modules() if m["name"] == "MCP_Renamed")
        assert renamed["parent"] == "Root", renamed
        assert len(connections()["unresolved"]) == 2
        parent_dependencies = dependencies()
        assert {(item["source_module"], item["target_module"])
                for item in parent_dependencies["dependencies"]
                if item["type"] == "module_parent"} == {("Root", "MCP_Renamed")}, parent_dependencies

        for name in ("MCP_Target_Root", "MCP_Target_Child"):
            request("POST", "/control-rigs/hierarchy", {"AssetPath": ASSET,
                "Operation": "add", "ElementType": "null", "Name": name})
        for connector, target in (("Root/Root", "MCP_Target_Root"),
                                  ("MCP_Renamed/Root", "MCP_Target_Child")):
            connect = {"AssetPath": ASSET, "Operation": "connect",
                       "ConnectorName": connector, "TargetType": "null",
                       "TargetName": target}
            assert not request("POST", "/modular-rigs/connections", {
                **connect, "bDryRun": True})["changed"]
            request("POST", "/modular-rigs/connections", connect)
        assert len(connections()["connections"]) == 2
        connected_dependencies = dependencies()
        connector_targets = {(item["connector_module"], item["connector"], item["target_name"])
                             for item in connected_dependencies["dependencies"]
                             if item["type"] == "connector_target"}
        assert connector_targets == {
            ("Root", "Root/Root", "MCP_Target_Root"),
            ("MCP_Renamed", "MCP_Renamed/Root", "MCP_Target_Child")}, connected_dependencies
        assert connected_dependencies["unresolved_connector_count"] == 0, connected_dependencies
        assert connected_dependencies["parent_dependency_count"] == 1, connected_dependencies
        assert connected_dependencies["connector_dependency_count"] == 2, connected_dependencies
        validated = request("GET", "/modular-rigs/validate", params={"asset_path": ASSET})
        assert validated["valid"] and validated["required_unresolved"] == 0, validated

        disconnect = {"AssetPath": ASSET, "Operation": "disconnect",
                      "ConnectorName": "MCP_Renamed/Root"}
        request("POST", "/modular-rigs/connections", disconnect, expect_error=True)
        request("POST", "/modular-rigs/connections", {**disconnect, "bConfirm": True})
        disconnected_dependencies = dependencies()
        assert disconnected_dependencies["unresolved_connector_count"] == 1, disconnected_dependencies
        assert disconnected_dependencies["unresolved_connectors"][0]["name"] == "MCP_Renamed/Root", disconnected_dependencies
        assert request("GET", "/modular-rigs/validate",
                       params={"asset_path": ASSET})["required_unresolved"] == 1
        request("POST", "/modular-rigs/connections", {"AssetPath": ASSET,
            "Operation": "connect", "ConnectorName": "MCP_Renamed/Root",
            "TargetType": "null", "TargetName": "MCP_Target_Child"})

        assert not request("POST", "/modular-rigs/compile", {
            "AssetPath": ASSET, "bDryRun": True})["compiled"]
        compiled = request("POST", "/modular-rigs/compile", {
            "AssetPath": ASSET, "bSave": True})
        assert compiled["compiled"] and compiled["valid"] and compiled["errors"] == 0, compiled
        assert ASSET_FILE.exists(), ASSET_FILE

        delete = {"AssetPath": ASSET, "Operation": "delete", "ModuleName": "MCP_Renamed"}
        preview = request("POST", "/modular-rigs/modules", {**delete, "bDryRun": True})
        assert preview["affected_connectors"] >= 1, preview
        assert preview["connected_connectors"] == 1, preview
        request("POST", "/modular-rigs/modules", delete, expect_error=True)
        request("POST", "/modular-rigs/modules", {**delete, "bConfirm": True}, expect_error=True)
        request("POST", "/modular-rigs/connections", {**disconnect, "bConfirm": True})
        request("POST", "/modular-rigs/modules", {**delete, "bConfirm": True})
        assert [m["name"] for m in modules()] == ["Root"]
        print("Modular Rig live smoke passed")
    finally:
        request("POST", "/assets/delete", {"AssetPath": ASSET})
        assert not ASSET_FILE.exists(), f"Test Modular Rig was not deleted: {ASSET_FILE}"


if __name__ == "__main__":
    main()
