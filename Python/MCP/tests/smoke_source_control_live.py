"""Read-only source-control provider/status, path, and unavailable-provider guards."""

import httpx

BASE = "http://127.0.0.1:8080"
ASSET = "/Game/LevelPrototyping/Meshes/SM_Cube.SM_Cube"


def call(method, route, body=None):
    response = httpx.request(method, BASE + route, json=body, timeout=180)
    response.raise_for_status()
    return response.json()


def main():
    provider = call("GET", "/editor/source-control/provider")
    assert isinstance(provider["available"], bool) and provider["provider"]
    assert {"status", "checkout", "add", "revert", "submit"} <= provider["operations"].keys()
    status = call("POST", "/editor/source-control/status", {"AssetPaths": [ASSET, ASSET]})
    assert not status["executed"] and not status["changed"] and len(status["files"]) == 1
    assert status["files"][0]["exists"] and status["files"][0]["filename"].endswith("SM_Cube.uasset")
    history = call("POST", "/editor/source-control/history", {"AssetPaths": [ASSET]})
    assert not history["changed"] and len(history["files"]) == 1
    if not provider["available"]:
        assert not history["history_supported"] and history["errors"] and not history["files"][0]["revisions"]
    for operation in ["checkout", "add", "revert", "submit"]:
        preview = call("POST", "/editor/source-control/operation", {
            "AssetPaths": [ASSET], "Operation": operation, "Description": "Smoke test preview",
            "bDryRun": True})
        assert preview["dry_run"] and not preview["executed"] and not preview["changed"]
        if not provider["available"]:
            assert not preview["success"] and preview["errors"]
    if not provider["available"]:
        rejected = call("POST", "/editor/source-control/operation", {
            "AssetPaths": [ASSET], "Operation": "revert", "bConfirm": True})
        assert not rejected["executed"] and not rejected["changed"] and rejected["errors"]
    for request in [
        {"AssetPaths": ["/Engine/BasicShapes/Cube.Cube"]},
        {"AssetPaths": ["../../outside.uasset"]},
        {"AssetPaths": []},
        {"AssetPaths": [ASSET], "Operation": "run_command"},
    ]:
        response = httpx.post(BASE + "/editor/source-control/operation", json=request, timeout=180)
        assert response.status_code >= 400
    print(f"Source control provider/status and guards: OK (provider={provider['provider']}, available={provider['available']})")


if __name__ == "__main__":
    main()
