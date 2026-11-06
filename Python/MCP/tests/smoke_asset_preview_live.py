"""Verify shared previews preflight values without changing the source asset."""

from smoke_sequencer_live import request


ASSET = "/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run"
PROPERTY = "TargetWeightInterpolationSpeedPerSec"


def preview(properties=None, operation="set_properties", asset_class=""):
    return request("POST", "/assets/preview-operation", {
        "AssetPath": ASSET, "AssetClass": asset_class,
        "Operation": operation, "Properties": properties or {}})


def main():
    before_value = request("GET", "/assets/properties", params={"asset_path": ASSET})[PROPERTY]
    before_dirty = request("GET", "/assets/dirty-state", params={"asset_path": ASSET})["dirty"]
    different = 3.0 if before_value != 3.0 else 4.0

    unchanged = preview({PROPERTY: str(before_value)})
    assert unchanged["valid"] and not unchanged["would_change"], unchanged
    assert unchanged["changes"] == [{"path": PROPERTY, "input": str(before_value),
                                      "would_change": False}], unchanged

    changed = preview({PROPERTY: str(different)}, asset_class="/Script/Engine.BlendSpace")
    assert changed["valid"] and changed["would_change"] and changed["changes"][0]["would_change"]
    assert changed["dry_run"] and not changed["changed"] and not changed["saved"]

    invalid = preview({PROPERTY: str(different), "NoSuchProperty": "x"})
    assert not invalid["valid"] and any(e["field"] == "NoSuchProperty" for e in invalid["errors"])
    assert not invalid["would_change"], invalid
    bad_value = preview({PROPERTY: "not_a_number"})
    assert not bad_value["valid"] and bad_value["errors"][0]["field"] == PROPERTY
    bad_operation = preview(operation="delete")
    assert not bad_operation["valid"] and bad_operation["errors"][0]["field"] == "operation"
    save = preview(operation="save")
    assert save["valid"] and save["would_change"] == before_dirty, save

    assert request("GET", "/assets/properties", params={"asset_path": ASSET})[PROPERTY] == before_value
    assert request("GET", "/assets/dirty-state", params={"asset_path": ASSET})["dirty"] == before_dirty
    print("Shared asset preview live smoke passed")


if __name__ == "__main__":
    main()
