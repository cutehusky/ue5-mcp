"""Live Static Mesh GLB import and reimport test with an embedded mesh fixture."""

import json
import struct
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
ASSET = "/Game/UE5MCP_Test/SM_MCP_GlbSmoke/StaticMeshes/SM_MCP_GlbSmoke.SM_MCP_GlbSmoke"
PROJECT = Path(__file__).resolve().parents[5]
SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "SM_MCP_GlbSmoke.glb"
DESTINATION_ROOT = PROJECT / "Content" / "UE5MCP_Test" / "SM_MCP_GlbSmoke"
ASSET_FILE = DESTINATION_ROOT / "StaticMeshes" / "SM_MCP_GlbSmoke.uasset"


def write_glb(triangle_count):
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]
    indices = [0, 1, 2] if triangle_count == 1 else [0, 1, 2, 1, 3, 2]
    positions = b"".join(struct.pack("<3f", *point) for point in points)
    triangles = struct.pack(f"<{len(indices)}H", *indices)
    binary = positions + triangles
    binary += b"\0" * (-len(binary) % 4)
    document = {
        "asset": {"version": "2.0", "generator": "UE5MCP smoke test"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(triangles), "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(points), "type": "VEC3",
             "min": [0, 0, 0], "max": [1, 1, 0]},
            {"bufferView": 1, "componentType": 5123, "count": len(indices), "type": "SCALAR"},
        ],
        "meshes": [{"name": "SM_MCP_GlbSmoke", "primitives": [
            {"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}],
        "nodes": [{"name": "SM_MCP_GlbSmoke", "mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    chunks = (struct.pack("<II", len(encoded), 0x4E4F534A) + encoded +
              struct.pack("<II", len(binary), 0x004E4942) + binary)
    SOURCE.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + len(chunks)) + chunks)


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def main():
    assert not ASSET_FILE.exists(), f"Disposable test asset already exists: {ASSET_FILE}"
    write_glb(1)
    try:
        request = {"SourceFilePath": str(SOURCE), "DestinationPath": "/Game/UE5MCP_Test",
                   "AssetName": "SM_MCP_GlbSmoke"}
        dry = call("POST", "/static-meshes/import", request | {"bDryRun": True})
        assert dry["dry_run"] and not dry["changed"]
        assert dry["destination_root"] == "/Game/UE5MCP_Test/SM_MCP_GlbSmoke"
        imported = call("POST", "/static-meshes/import", request | {"bSave": True})
        assert imported["asset_path"] == ASSET and imported["saved"] and ASSET_FILE.exists()
        assert ASSET in imported["created_assets"]
        before = call("GET", "/static-meshes/source", asset_path=ASSET)
        assert before["lods"][0]["triangles"] == 1
        duplicate = httpx.post(BASE + "/static-meshes/import", json=request, timeout=120)
        assert duplicate.status_code >= 400
        write_glb(2)
        reimported = call("POST", "/static-meshes/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bSave": True})
        assert reimported["changed"] and reimported["saved"]
        after = call("GET", "/static-meshes/source", asset_path=ASSET)
        assert after["lods"][0]["triangles"] == 2
        print("Static Mesh GLB import and reimport: OK")
    finally:
        if ASSET_FILE.exists():
            call("POST", "/assets/delete", {"AssetPath": ASSET})
        SOURCE.unlink(missing_ok=True)
        (DESTINATION_ROOT / "StaticMeshes").rmdir()
        DESTINATION_ROOT.rmdir()


if __name__ == "__main__":
    main()
