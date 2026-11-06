"""Live Material Instance route smoke test. Requires a running local UE API on 8080."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray"
DEST = "/Game/UE5MCP_Test/MI_MCP_ParameterSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=120)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def parameters(asset):
    return call("GET", "/material-instances/parameters", asset_path=asset)


def find(rows, name, kind):
    return next(p for p in rows["parameters"] if p["name"] == name and p["type"] == kind)


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        before = parameters(asset)
        initial_validation = call("POST", "/material-instances/validate", {"AssetPath": asset})
        assert initial_validation["parent_path"] == before["parent_path"]
        assert initial_validation["orphaned_override_count"] == len(initial_validation["orphaned_overrides"])
        assert initial_validation["valid"] == (initial_validation["orphaned_override_count"] == 0)
        scalar = find(before, "Sub Grid Number", "scalar")
        switch = find(before, "Grid", "static_switch")
        assert not scalar["overridden"]
        edit = {"AssetPath": asset, "ParameterName": "Sub Grid Number", "ParameterType": "scalar", "Value": "7.5"}
        assert call("PATCH", "/material-instances/parameters", edit | {"bDryRun": True})["dry_run"]
        assert find(parameters(asset), "Sub Grid Number", "scalar") == scalar
        assert call("PATCH", "/material-instances/parameters", edit)["changed"]
        updated = find(parameters(asset), "Sub Grid Number", "scalar")
        assert updated["overridden"] and updated["value"] == 7.5
        switch_edit = {"AssetPath": asset, "ParameterName": "Grid", "ParameterType": "static_switch", "Value": str(not switch["value"]).lower()}
        assert call("PATCH", "/material-instances/parameters", switch_edit)["changed"]
        changed_switch = find(parameters(asset), "Grid", "static_switch")
        assert changed_switch["overridden"] and changed_switch["value"] != switch["value"]
        bad = httpx.patch(BASE + "/material-instances/parameters", json=edit | {"ParameterName": "Missing"}, timeout=120)
        assert bad.status_code >= 400
        cycle = httpx.patch(BASE + "/material-instances/parent", json={"AssetPath": asset, "ParentPath": asset}, timeout=120)
        assert cycle.status_code >= 400
        assert call("POST", "/material-instances/reset", {"AssetPath": asset, "bDryRun": True})["dry_run"]
        call("POST", "/material-instances/reset", {"AssetPath": asset})
        reset = parameters(asset)
        assert not find(reset, "Sub Grid Number", "scalar")["overridden"]
        assert find(reset, "Sub Grid Number", "scalar")["value"] == scalar["value"]
        assert not find(reset, "Grid", "static_switch")["overridden"]
        assert call("POST", "/material-instances/validate", {"AssetPath": asset})["valid"]
        parent = "/Game/LevelPrototyping/Materials/MI_DefaultColorway.MI_DefaultColorway"
        assert call("PATCH", "/material-instances/parent", {"AssetPath": asset, "ParentPath": parent, "bDryRun": True})["dry_run"]
        assert parameters(asset)["parent_path"] == before["parent_path"]
        assert call("PATCH", "/material-instances/parent", {"AssetPath": asset, "ParentPath": parent})["changed"]
        assert parameters(asset)["parent_path"] == parent
        assert call("POST", "/material-instances/validate", {"AssetPath": asset})["valid"]
        print("Material Instance parameters, static switch, reset, and parent routes: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
