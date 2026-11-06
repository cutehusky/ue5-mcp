"""Live guarded OBJ import, source inspection, replacement, and reimport test."""

from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
ASSET = "/Game/UE5MCP_Test/SM_MCP_ImportSmoke.SM_MCP_ImportSmoke"
PROJECT = Path(__file__).resolve().parents[5]
SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "SM_MCP_ImportSmoke.obj"
OTHER_SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "SM_MCP_ImportSmoke_Alternate.obj"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "SM_MCP_ImportSmoke.uasset"


def write_obj(path, triangle_count):
    path.parent.mkdir(parents=True, exist_ok=True)
    vertices = ["v 0 0 0", "v 100 0 0", "v 0 100 0", "v 0 0 100", "v 100 100 0"]
    faces = ["f 1 2 3", "f 1 4 2", "f 2 4 3", "f 3 4 1"]
    path.write_text("\n".join(["o SM_MCP_ImportSmoke", *vertices, *faces[:triangle_count], ""]),
                    encoding="ascii")


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def main():
    assert not ASSET_FILE.exists(), f"Disposable test asset already exists: {ASSET_FILE}"
    write_obj(SOURCE, 1)
    try:
        request = {"SourceFilePath": str(SOURCE), "DestinationPath": "/Game/UE5MCP_Test",
                   "AssetName": "SM_MCP_ImportSmoke"}
        dry = call("POST", "/static-meshes/import", request | {"bDryRun": True})
        assert dry["dry_run"] and not dry["changed"] and dry["asset_path"] == ASSET
        imported = call("POST", "/static-meshes/import", request | {"bSave": True})
        assert imported["asset_path"] == ASSET and imported["saved"] and ASSET_FILE.exists()
        source = call("GET", "/static-meshes/source", asset_path=ASSET)
        assert source["lod_count"] >= 1 and source["lods"][0]["triangles"] == 1
        assert source["source_files"][0]["exists"]

        duplicate = httpx.post(BASE + "/static-meshes/import", json=request, timeout=120)
        assert duplicate.status_code >= 400
        write_obj(SOURCE, 2)
        replaced = call("POST", "/static-meshes/import", request | {
            "bReplaceExisting": True, "bConfirmReplace": True, "bSave": True})
        assert replaced["changed"] and replaced["replaced"] and replaced["saved"]
        assert call("GET", "/static-meshes/source", asset_path=ASSET)["lods"][0]["triangles"] == 2

        write_obj(SOURCE, 3)
        dry_reimport = call("POST", "/static-meshes/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bDryRun": True})
        assert dry_reimport["dry_run"] and not dry_reimport["changed"]
        changed = call("POST", "/static-meshes/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bSave": True})
        assert changed["changed"] and changed["saved"]
        assert call("GET", "/static-meshes/source", asset_path=ASSET)["lods"][0]["triangles"] == 3

        write_obj(OTHER_SOURCE, 4)
        source_change = {"AssetPath": ASSET, "SourceFilePath": str(OTHER_SOURCE),
                         "bConfirmReimport": True}
        unconfirmed = httpx.post(BASE + "/static-meshes/reimport", json=source_change, timeout=120)
        assert unconfirmed.status_code >= 400
        switched = call("POST", "/static-meshes/reimport", source_change | {
            "bConfirmSourceChange": True, "bSave": True})
        assert switched["changed"] and switched["saved"]
        after = call("GET", "/static-meshes/source", asset_path=ASSET)
        assert after["lods"][0]["triangles"] == 4
        assert Path(after["source_files"][0]["path"]).resolve() == OTHER_SOURCE.resolve()
        print("Static Mesh OBJ import, source inspection, replacement, and reimport: OK")
    finally:
        if ASSET_FILE.exists():
            call("POST", "/assets/delete", {"AssetPath": ASSET})
        SOURCE.unlink(missing_ok=True)
        OTHER_SOURCE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
