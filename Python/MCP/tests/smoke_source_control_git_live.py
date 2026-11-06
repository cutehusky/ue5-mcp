"""Live add/submit/revert checks in the isolated SourceControlFixture project only."""

import struct
import subprocess
import zlib
from pathlib import Path

import httpx
from smoke_source_control_history_live import verify_history

BASE = "http://127.0.0.1:8080"
PROJECT = Path(__file__).resolve().parents[5]
ROOT = PROJECT / "Saved" / "UE5MCP_SourceControl_Test"
SOURCE = ROOT / "Saved" / "T_SC_Smoke.png"
ASSET = "/Game/SC_Test/T_SC_Smoke.T_SC_Smoke"


def git(*args):
    return subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(),
                                    "-C", str(ROOT), *args], text=True).strip()


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def operation(name, **options):
    return call("POST", "/editor/source-control/operation", {
        "AssetPaths": [ASSET], "Operation": name, **options})


def status():
    return call("POST", "/editor/source-control/status", {"AssetPaths": [ASSET]})


def main():
    assert Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT.resolve()
    assert not git("remote"), "The test repository must have no remotes"
    assert not git("ls-tree", "--name-only", "HEAD", "--", "Content/SC_Test/T_SC_Smoke.uasset"), "Recreate the fixture before rerunning a completed test"
    provider = call("GET", "/editor/source-control/provider")
    assert provider["provider"] == "Git" and provider["available"], provider
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    pixels = (b"\0" + bytes([40, 100, 160, 255]) * 2) * 2
    SOURCE.write_bytes(b"\x89PNG\r\n\x1a\n" +
        chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))
    imported = call("POST", "/textures/import", {
        "SourceFilePath": str(SOURCE), "DestinationPath": "/Game/SC_Test",
        "AssetName": "T_SC_Smoke", "bSave": True,
        "bReplaceExisting": True, "bConfirmReplace": True})
    assert imported["saved"]
    # Importers can stage new packages automatically; unstage only this new fixture file.
    git("reset", "--", "Content/SC_Test/T_SC_Smoke.uasset")
    initial = status()
    file = initial["files"][0]
    assert Path(file["filename"]).resolve().is_relative_to((ROOT / "Content").resolve()), initial
    assert not file["source_controlled"] and file["can_add"], initial
    before_commit = git("rev-parse", "HEAD")
    dry_add = operation("add", bDryRun=True)
    assert dry_add["success"] and not dry_add["executed"]
    added = operation("add")
    assert added["success"] and added["executed"] and status()["files"][0]["added"], added
    rejected = operation("submit", Description="UE5MCP source-control smoke")
    assert not rejected["executed"] and rejected["errors"], rejected
    missing_description = operation("submit", bConfirm=True)
    assert not missing_description["executed"] and missing_description["errors"], missing_description
    preview = operation("submit", Description="UE5MCP source-control smoke", bDryRun=True)
    assert preview["success"] and not preview["executed"], preview
    submitted = operation("submit", Description="UE5MCP source-control smoke", bConfirm=True)
    assert submitted["success"] and submitted["executed"], submitted
    committed = git("rev-parse", "HEAD")
    assert committed != before_commit and "UE5MCP source-control smoke" in git("log", "-1", "--format=%B")

    original = call("GET", "/assets/properties", asset_path=ASSET)["SRGB"]
    call("PATCH", "/textures/settings", {"AssetPath": ASSET, "Properties": {
        "SRGB": "False" if original else "True"}})
    dirty_revert = operation("revert", bConfirm=True)
    assert not dirty_revert["executed"] and any("unsaved" in error for error in dirty_revert["errors"]), dirty_revert
    call("POST", "/assets/save", {"AssetPath": ASSET})
    assert status()["files"][0]["modified"]
    unconfirmed = operation("revert")
    assert not unconfirmed["executed"] and unconfirmed["errors"], unconfirmed
    reverted = operation("revert", bConfirm=True)
    assert reverted["success"] and reverted["package_reload_requested"], reverted
    assert call("GET", "/assets/properties", asset_path=ASSET)["SRGB"] == original
    assert not git("status", "--porcelain", "--", "Content")
    assert git("rev-parse", "HEAD") == committed
    checkout = operation("checkout")
    assert not checkout["operation_supported"] and not checkout["executed"]
    call("PATCH", "/textures/settings", {"AssetPath": ASSET, "Properties": {
        "SRGB": "False" if original else "True"}, "bSave": True})
    second_submit = operation("submit", Description="UE5MCP history second revision", bConfirm=True)
    assert second_submit["success"], second_submit
    latest = git("rev-parse", "HEAD")
    verify_history(committed, latest)
    print("Isolated Git operations, package reload, confirmation guards, and paged revision history: OK")


if __name__ == "__main__":
    main()
