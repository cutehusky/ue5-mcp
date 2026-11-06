"""Verify the extra added-file revert confirmation in the isolated Git fixture."""

import subprocess
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
ROOT = PROJECT / "Saved" / "UE5MCP_SourceControl_Test"
ASSET = "/Game/SC_Test/T_SC_Added.T_SC_Added"
BASE = "http://127.0.0.1:8080"


def call(method, route, body=None):
    response = httpx.request(method, BASE + route, json=body, timeout=180)
    response.raise_for_status()
    return response.json()


def main():
    remotes = subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(),
                                      "-C", str(ROOT), "remote"], text=True)
    assert not remotes.strip()
    source = ROOT / "Saved" / "T_SC_Added.png"
    source.write_bytes((ROOT / "Saved" / "T_SC_Smoke.png").read_bytes())
    imported = call("POST", "/textures/import", {
        "SourceFilePath": str(source), "DestinationPath": "/Game/SC_Test",
        "AssetName": "T_SC_Added", "bSave": True})
    assert imported["saved"]
    status = call("POST", "/editor/source-control/status", {"AssetPaths": [ASSET]})
    assert status["provider"] == "Git" and status["files"][0]["added"]
    assert Path(status["files"][0]["filename"]).resolve().is_relative_to((ROOT / "Content").resolve())
    request = {"AssetPaths": [ASSET], "Operation": "revert", "bConfirm": True}
    rejected = call("POST", "/editor/source-control/operation", request)
    assert not rejected["executed"] and any("confirm_delete_added" in error for error in rejected["errors"])
    reverted = call("POST", "/editor/source-control/operation", request | {"bConfirmDeleteAdded": True})
    assert reverted["success"] and reverted["executed"], reverted
    after = call("POST", "/editor/source-control/status", {"AssetPaths": [ASSET]})
    assert not after["files"][0]["source_controlled"]
    print("Isolated Git added-file revert confirmation and unstage: OK")


if __name__ == "__main__":
    main()
