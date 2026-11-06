"""Live glTF scene import with two Static Meshes and a shared material."""

import base64
import json
import struct
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
PROJECT = Path(__file__).resolve().parents[5]
ROOT_PATH = "/Game/UE5MCP_Test/MCP_SceneSmoke"
ROOT_DIR = PROJECT / "Content" / "UE5MCP_Test" / "MCP_SceneSmoke"
SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "MCP_SceneSmoke.gltf"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def main():
    assert not ROOT_DIR.exists(), f"Disposable scene destination already exists: {ROOT_DIR}"
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    binary = struct.pack("<9f3H", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 2)
    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(binary), "uri": "data:application/octet-stream;base64," +
                     base64.b64encode(binary).decode("ascii")}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
                        {"buffer": 0, "byteOffset": 36, "byteLength": 6, "target": 34963}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
                       "min": [0, 0, 0], "max": [1, 1, 0]},
                      {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}],
        "materials": [{"name": "M_MCP_SceneSmoke", "pbrMetallicRoughness": {
            "baseColorFactor": [0.2, 0.5, 0.8, 1], "metallicFactor": 0, "roughnessFactor": 0.6}}],
        "meshes": [{"name": name, "primitives": [{"attributes": {"POSITION": 0},
                    "indices": 1, "material": 0, "mode": 4}]}
                   for name in ["SM_MCP_Scene_A", "SM_MCP_Scene_B"]],
        "nodes": [{"mesh": 0, "name": "SM_MCP_Scene_A"},
                  {"mesh": 1, "name": "SM_MCP_Scene_B", "translation": [2, 0, 0]}],
        "scenes": [{"nodes": [0, 1]}], "scene": 0,
    }
    SOURCE.write_text(json.dumps(document), encoding="utf-8")
    try:
        request = {"SourceFilePath": str(SOURCE), "DestinationPath": "/Game/UE5MCP_Test",
                   "AssetName": "MCP_SceneSmoke", "bSave": True}
        imported = call("POST", "/static-meshes/import", request)
        paths = imported["created_assets"]
        assert imported["saved"] and imported["destination_root"] == ROOT_PATH
        assert len(paths) >= 3 and all(path.startswith(ROOT_PATH + "/") for path in paths)
        meshes = [path for path in paths if "/StaticMeshes/" in path]
        assert len(meshes) == 2 and imported["asset_path"] in meshes
        for mesh in meshes:
            assert call("GET", "/static-meshes/source", asset_path=mesh)["lods"][0]["triangles"] == 1
        duplicate = httpx.post(BASE + "/static-meshes/import", json=request, timeout=120)
        assert duplicate.status_code >= 400
        print("glTF scene import, generated assets, and destination guard: OK")
    finally:
        if ROOT_DIR.exists():
            # This new test root has no preexisting files. Remove assets through the editor first.
            files = sorted(ROOT_DIR.rglob("*.uasset"), key=lambda path: "StaticMeshes" not in path.parts)
            for file in files:
                relative = file.relative_to(PROJECT / "Content").with_suffix("").as_posix()
                call("POST", "/assets/delete", {"AssetPath": "/Game/" + relative + "." + file.stem})
            for directory in sorted((path for path in ROOT_DIR.rglob("*") if path.is_dir()),
                                    key=lambda path: len(path.parts), reverse=True):
                directory.rmdir()
            ROOT_DIR.rmdir()
        SOURCE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
