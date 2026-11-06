"""Project-file and missing-package source-control tests in the isolated Git fixture."""

import subprocess
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
ROOT = PROJECT / "Saved" / "UE5MCP_SourceControl_Test"
BASE = "http://127.0.0.1:8080"
CONFIG = ROOT / "Config" / "SC_Test.ini"
TEXTURE = ROOT / "Content" / "SC_Test" / "T_SC_Smoke.uasset"
ASSET = "/Game/SC_Test/T_SC_Smoke.T_SC_Smoke"


def git(*args):
    return subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(),
                                    "-C", str(ROOT), *args], text=True).strip()


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def operation(path, name, **options):
    return call("POST", "/editor/source-control/operation", {
        "FilePaths": [path], "Operation": name, **options})


def status(path):
    return call("POST", "/editor/source-control/status", {"FilePaths": [path]})


def main():
    assert Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT.resolve()
    assert not git("remote") and not CONFIG.exists()
    provider = call("GET", "/editor/source-control/provider")
    assert provider["provider"] == "Git" and provider["available"]
    config_path = "Config/SC_Test.ini"
    original = "[Fixture]\nValue=Original\n"
    CONFIG.write_text(original, encoding="utf-8")
    file = status(config_path)["files"][0]
    assert Path(file["filename"]).resolve() == CONFIG.resolve() and file["kind"] == "project_file" and file["dirty"] is None
    added = operation(config_path, "add")
    assert added["success"]
    submitted = operation(config_path, "submit", bConfirm=True, Description="Add isolated config")
    assert submitted["success"], submitted
    CONFIG.write_text("[Fixture]\nValue=Changed\n", encoding="utf-8")
    dry = operation(config_path, "revert", bDryRun=True)
    assert dry["success"] and not dry["executed"] and "Changed" in CONFIG.read_text()
    reverted = operation(config_path, "revert", bConfirm=True)
    assert reverted["success"] and not reverted["package_reload_requested"]
    assert CONFIG.read_text() == original

    CONFIG.unlink()
    missing = status(config_path)["files"][0]
    assert not missing["exists"] and missing["deleted"]
    history = call("POST", "/editor/source-control/history", {"FilePaths": [config_path]})
    assert history["success"] and history["files"][0]["history_total"] == 1, history
    preview = operation(config_path, "revert", bDryRun=True)
    assert preview["success"] and not preview["executed"] and not CONFIG.exists()
    restored = operation(config_path, "revert", bConfirm=True)
    assert restored["success"] and restored["restored_missing_files"], restored
    assert CONFIG.read_text() == original and not git("status", "--porcelain", "--", config_path)

    texture_path = "Content/SC_Test/T_SC_Smoke.uasset"
    before = TEXTURE.read_bytes()
    property_before = call("GET", "/assets/properties", asset_path=ASSET)["SRGB"]
    TEXTURE.unlink()
    assert not status(texture_path)["files"][0]["exists"]
    restored_texture = operation(texture_path, "revert", bConfirm=True)
    assert restored_texture["success"] and restored_texture["package_reload_requested"], restored_texture
    assert restored_texture["restored_missing_files"] and TEXTURE.read_bytes() == before
    assert call("GET", "/assets/properties", asset_path=ASSET)["SRGB"] == property_before

    CONFIG.unlink()
    deletion = operation(config_path, "submit", bConfirm=True, Description="Delete isolated config")
    assert deletion["success"] and not CONFIG.exists(), deletion
    assert not git("ls-tree", "--name-only", "HEAD", "--", config_path)
    deleted_history = call("POST", "/editor/source-control/history", {"FilePaths": [config_path]})
    assert deleted_history["success"] and deleted_history["files"][0]["history_total"] == 2, deleted_history
    assert deleted_history["files"][0]["revisions"][0]["action"] == "delete"

    for path in ["../outside.ini", str(PROJECT / "DemoForPlugin.uproject"), ".git/config",
                 "Saved/outside.ini", "Plugins/Any/Intermediate/file.txt", "Config", "Config/SC_Test.ini:stream"]:
        response = httpx.post(BASE + "/editor/source-control/status", json={"FilePaths": [path]}, timeout=180)
        assert response.status_code >= 400, path
    link = ROOT / "Config" / "LinkOutside"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(ROOT / "Saved")],
                   capture_output=True, text=True, check=True)
    try:
        response = httpx.post(BASE + "/editor/source-control/status", json={"FilePaths": ["Config/LinkOutside/file.ini"]}, timeout=180)
        assert response.status_code >= 400
    finally:
        link.rmdir()
    print("Isolated Git project files, missing text/package restore, deletion submit/history, and path guards: OK")


if __name__ == "__main__":
    main()
