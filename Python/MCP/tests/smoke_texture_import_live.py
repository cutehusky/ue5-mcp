"""Live guarded PNG import, source inspection, and reimport test."""

import struct
import zlib
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
ASSET = "/Game/UE5MCP_Test/T_MCP_ImportSmoke.T_MCP_ImportSmoke"
PROJECT = Path(__file__).resolve().parents[5]
SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "T_MCP_ImportSmoke.png"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "T_MCP_ImportSmoke.uasset"


def png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(red, green, blue):
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    row = bytes([0]) + bytes([red, green, blue, 255]) * 2
    data = (b"\x89PNG\r\n\x1a\n" +
            png_chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)) +
            png_chunk(b"IDAT", zlib.compress(row * 2)) + png_chunk(b"IEND", b""))
    SOURCE.write_bytes(data)


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main():
    assert not ASSET_FILE.exists(), f"Disposable test asset already exists: {ASSET_FILE}"
    write_png(255, 0, 0)
    try:
        request = {"SourceFilePath": str(SOURCE), "DestinationPath": "/Game/UE5MCP_Test",
                   "AssetName": "T_MCP_ImportSmoke"}
        dry = call("POST", "/textures/import", request | {"bDryRun": True})
        assert dry["dry_run"] and not dry["changed"]
        result = call("POST", "/textures/import", request | {"bSave": True})
        assert result["asset_path"] == ASSET and result["saved"]
        assert ASSET_FILE.exists()
        source = call("GET", "/textures/source", asset_path=ASSET)
        assert source["source_valid"] and source["width"] == 2 and source["height"] == 2
        assert source["source_files"][0]["exists"]
        duplicate = httpx.post(BASE + "/textures/import", json=request, timeout=120)
        assert duplicate.status_code >= 400
        write_png(0, 0, 255)
        replaced = call("POST", "/textures/import", request | {
            "bReplaceExisting": True, "bConfirmReplace": True, "bSave": True})
        assert replaced["changed"] and replaced["replaced"] and replaced["saved"]
        source = call("GET", "/textures/source", asset_path=ASSET)
        assert source["source_id"] != result["source_id"]
        before_id = source["source_id"]
        write_png(0, 255, 0)
        dry_reimport = call("POST", "/textures/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bDryRun": True})
        assert dry_reimport["dry_run"] and not dry_reimport["changed"]
        assert call("GET", "/textures/source", asset_path=ASSET)["source_id"] == before_id
        changed = call("POST", "/textures/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bSave": True})
        assert changed["changed"] and changed["saved"]
        after = call("GET", "/textures/source", asset_path=ASSET)
        assert after["source_valid"] and after["source_id"] != before_id
        print("Texture PNG import, source inspection, and reimport: OK")
    finally:
        if ASSET_FILE.exists():
            call("POST", "/assets/delete", {"AssetPath": ASSET})
        if SOURCE.exists():
            SOURCE.unlink()


if __name__ == "__main__":
    main()
