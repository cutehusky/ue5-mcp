"""Exercise Modular Rig config overrides and module variable bindings."""

from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
ASSET = "/Game/UE5MCP_Test/MR_MCP_Fixture.MR_MCP_Fixture"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "MR_MCP_Fixture.uasset"


def variables(module, variable=""):
    return request("GET", "/modular-rigs/variables", params={
        "asset_path": ASSET, "module_name": module, "variable_name": variable})


def dependencies():
    return request("GET", "/modular-rigs/dependencies", params={"asset_path": ASSET})


def main():
    assert ASSET_FILE.exists(), "Create the fixture with create_modular_rig_fixture.py first"
    try:
        root = variables("Root")
        assert "Orient to World" in {item["name"] for item in root["variables"]}, root
        assert not root["overrides"]
        override = {"AssetPath": ASSET, "ModuleName": "Root",
                    "Operation": "set_override", "VariablePath": "Orient to World",
                    "Value": "False"}
        assert not request("POST", "/modular-rigs/variables", {
            **override, "bDryRun": True})["changed"]
        assert not variables("Root")["overrides"]
        request("POST", "/modular-rigs/variables", override)
        assert {item["path"]: item["value"] for item in variables("Root")["overrides"]}[
            "Orient to World"] == "False"
        request("POST", "/modular-rigs/variables", {**override,
            "Operation": "reset_override"})
        assert not variables("Root")["overrides"]

        settings_variable = next(item for item in root["variables"]
                                 if item["name"] == "Root Ctrl Settings")
        assert "FRigUnit_HierarchyAddControlTransform_Settings" in settings_variable["type"], settings_variable
        nested_path = "Root Ctrl Settings->bUsePreferredRotationOrder"
        nested_override = {"AssetPath": ASSET, "ModuleName": "Root",
                           "Operation": "set_override", "VariablePath": nested_path,
                           "Value": "True"}
        assert not request("POST", "/modular-rigs/variables", {
            **nested_override, "bDryRun": True})["changed"]
        assert not variables("Root")["overrides"]
        request("POST", "/modular-rigs/variables", nested_override)
        nested_values = {item["path"]: item["value"] for item in variables("Root")["overrides"]}
        assert nested_path in nested_values and nested_values[nested_path].lower() == "true", nested_values
        reported_overrides = {(item["module"], item["path"]): item["value"]
                              for item in dependencies()["config_overrides"]}
        assert reported_overrides[("Root", nested_path)].lower() == "true", reported_overrides
        request("POST", "/modular-rigs/variables", {**nested_override,
            "Operation": "reset_override"})
        assert not variables("Root")["overrides"]

        module_class = request("GET", "/modular-rigs/modules",
                               params={"asset_path": ASSET})[0]["class"]
        request("POST", "/modular-rigs/modules", {"AssetPath": ASSET,
            "Operation": "add", "ModuleName": "MCP_Child",
            "ParentName": "Root", "ModuleClassPath": module_class})
        child = variables("MCP_Child", "Root Control Scale")
        source = "Root/Root Control Scale"
        assert isinstance(child["possible_bindings"], list), child
        bind = {"AssetPath": ASSET, "ModuleName": "MCP_Child",
                "Operation": "bind_variable", "VariablePath": "Root Control Scale",
                "SourcePath": source}
        assert not request("POST", "/modular-rigs/variables", {
            **bind, "bDryRun": True})["changed"]
        request("POST", "/modular-rigs/variables", bind)
        assert {item["variable"]: item["source"] for item in variables(
            "MCP_Child")["bindings"]}["Root Control Scale"] == source
        binding_dependencies = [item for item in dependencies()["dependencies"]
                                if item["type"] == "variable_binding"]
        assert binding_dependencies == [{"type": "variable_binding", "module": "MCP_Child",
                                         "variable": "Root Control Scale", "source_path": source}], binding_dependencies
        request("POST", "/modular-rigs/variables", {**bind,
            "Operation": "unbind_variable"})
        assert not variables("MCP_Child")["bindings"]
        assert not [item for item in dependencies()["dependencies"]
                    if item["type"] == "variable_binding"]
        request("POST", "/modular-rigs/modules", {"AssetPath": ASSET,
            "Operation": "delete", "ModuleName": "MCP_Child", "bConfirm": True})
        request("POST", "/assets/save", {"AssetPath": ASSET})
        print("Modular Rig variable live smoke passed")
    finally:
        request("POST", "/assets/delete", {"AssetPath": ASSET})
        assert not ASSET_FILE.exists(), f"Test Modular Rig was not deleted: {ASSET_FILE}"


if __name__ == "__main__":
    main()
