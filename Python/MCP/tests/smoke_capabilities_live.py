"""Check the shared capability matrix against a running UE5_MCP API."""

from smoke_sequencer_live import request


REQUIRED = {
    "world", "level", "scene", "level_sequence", "behavior_tree", "blackboard",
    "state_tree", "environment_query", "data_asset", "primary_data_asset",
    "data_registry", "sound_wave", "sound_cue", "metasound", "sound_class",
    "sound_mix", "sound_submix", "texture", "render_target", "texture_array",
    "landscape", "foliage", "niagara",
}
FLAGS = {
    "generic", "inspect", "edit", "spawn_or_create", "compile_or_rebuild",
    "validate", "adapter_available", "engine_available",
}


def main():
    response = request("GET", "/assets/capabilities")
    assert response["schema_version"] >= 2
    assert isinstance(response["asset_families"], list)
    assert isinstance(response["operations"], list)
    assert isinstance(response["world_operations"], list)
    families = response["families"]
    assert REQUIRED <= families.keys(), REQUIRED - families.keys()
    for name, entry in families.items():
        assert FLAGS <= entry.keys(), (name, FLAGS - entry.keys())
        assert all(isinstance(entry[flag], bool) for flag in FLAGS), (name, entry)
        assert entry["support_level"] in {"unavailable", "generic", "partial"}
        assert entry["adapter_available"] == any(entry[flag] for flag in
            ("inspect", "edit", "spawn_or_create", "compile_or_rebuild", "validate"))
    assert families["physics_asset"]["inspect"] and families["physics_asset"]["edit"] and families["physics_asset"]["validate"]
    assert families["level_sequence"]["edit"] and families["level_sequence"]["spawn_or_create"]
    assert families["texture_array"]["inspect"] and families["texture_array"]["edit"]
    assert families["state_tree"]["support_level"] == ("partial" if families["state_tree"]["engine_available"] else "unavailable")
    assert families["landscape"]["support_level"] == "unavailable"
    print("Capability matrix smoke passed")


if __name__ == "__main__":
    main()
