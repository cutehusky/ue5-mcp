"""Live parent Material settings test. Requires a running local UE API on 8080."""

import httpx

BASE = "http://127.0.0.1:8080"
SOURCE = "/Game/LevelPrototyping/Materials/M_PrototypeGrid.M_PrototypeGrid"
DEST = "/Game/UE5MCP_Test/M_MCP_CoreSmoke"


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def main():
    asset = None
    try:
        asset = call("POST", "/assets/duplicate", {"AssetPath": SOURCE, "DestinationPath": DEST})
        summary = call("GET", "/materials/summary", asset_path=asset)
        parameters = call("GET", "/materials/parameters", asset_path=asset)
        validation = call("POST", "/materials/validate", {"AssetPath": asset})
        assert validation["status"] in {"ok", "error", "compiling", "unavailable"}
        assert validation["valid"] == (validation["status"] == "ok")
        assert isinstance(validation["compile_errors"], list)
        assert summary["domain"] == "MD_Surface"
        assert summary["blend_mode"] == "BLEND_Opaque"
        assert summary["shading_models"]
        assert "bUsedWithSkeletalMesh" in summary["usage_flags"]
        assert "bUsedWithUI" not in summary["usage_flags"]
        assert any(p["name"] == "Grid" and p["type"] == "static_switch" for p in parameters["parameters"])
        edit = {"AssetPath": asset, "Domain": "MD_Surface", "BlendMode": "BLEND_Masked",
                "ShadingModel": "MSM_Unlit", "bSetTwoSided": True, "bTwoSided": not summary["two_sided"],
                "UsageFlags": {"bUsedWithSkeletalMesh": True}}
        assert call("PATCH", "/materials/core-settings", edit | {"bDryRun": True})["dry_run"]
        assert call("GET", "/materials/summary", asset_path=asset) == summary
        for invalid in (edit | {"BlendMode": "BLEND_Unknown"},
                        edit | {"UsageFlags": {"bUsedWithUnknown": True}}):
            response = httpx.patch(BASE + "/materials/core-settings", json=invalid, timeout=180)
            assert response.status_code >= 400
        assert call("GET", "/materials/summary", asset_path=asset) == summary
        assert call("PATCH", "/materials/core-settings", edit)["changed"]
        after = call("GET", "/materials/summary", asset_path=asset)
        assert after["domain"] == "MD_Surface"
        assert after["blend_mode"] == "BLEND_Masked"
        assert "MSM_Unlit" in after["shading_models"]
        assert after["two_sided"] != summary["two_sided"]
        assert after["usage_flags"]["bUsedWithSkeletalMesh"]
        assert not call("PATCH", "/materials/core-settings", edit)["changed"]
        print("Material summary, parameters, and core settings: OK")
    finally:
        if asset:
            call("POST", "/assets/delete", {"AssetPath": asset})


if __name__ == "__main__":
    main()
