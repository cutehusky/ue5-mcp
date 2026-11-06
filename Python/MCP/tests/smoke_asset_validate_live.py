"""Verify shared asset validation reports errors without changing the asset."""

from smoke_sequencer_live import request


ASSET = "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run"
PROPERTY = "TargetWeightInterpolationSpeedPerSec"


def main():
    before_value = request("GET", "/assets/properties", params={"asset_path": ASSET})[PROPERTY]
    before_dirty = request("GET", "/assets/dirty-state", params={"asset_path": ASSET})["dirty"]

    valid = request("POST", "/assets/validate", {"AssetPath": ASSET,
        "AssetClass": "/Script/Engine.BlendSpace", "Properties": {PROPERTY: "3.0"}})
    assert valid["valid"] and valid["checked_property_count"] == 1, valid
    assert valid["scope"] == "property_preflight", valid

    invalid = request("POST", "/assets/validate", {"AssetPath": ASSET,
        "Properties": {PROPERTY: "3.0", "NotAProperty": "x"}})
    assert not invalid["valid"] and invalid["checked_property_count"] == 1, invalid
    assert any(e["field"] == "NotAProperty" for e in invalid["errors"]), invalid

    invalid_value = request("POST", "/assets/validate", {"AssetPath": ASSET,
        "Properties": {PROPERTY: "not_a_number"}})
    assert not invalid_value["valid"]
    assert any(e["field"] == PROPERTY for e in invalid_value["errors"]), invalid_value

    invalid_class = request("POST", "/assets/validate", {"AssetPath": ASSET,
        "AssetClass": "/Script/Engine.Texture"})
    assert not invalid_class["valid"] and invalid_class["errors"][0]["field"] == "asset_class"

    missing = request("POST", "/assets/validate", {
        "AssetPath": "/Game/UE5MCP_Test/NoSuchAsset.NoSuchAsset"})
    assert not missing["valid"] and missing["errors"][0]["field"] == "asset_path"

    assert request("GET", "/assets/properties", params={"asset_path": ASSET})[PROPERTY] == before_value
    assert request("GET", "/assets/dirty-state", params={"asset_path": ASSET})["dirty"] == before_dirty
    print("Shared asset validation live smoke passed")


if __name__ == "__main__":
    main()
