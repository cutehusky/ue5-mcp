"""Exercise Sound Cue graph creation, node authoring, links, layout, validation, and cleanup."""

import math
import struct
import uuid
import wave
from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]


def write_wav(path: Path, duration: float):
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    samples = [int(8000 * math.sin(2 * math.pi * 440 * n / sample_rate))
               for n in range(round(sample_rate * duration))]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def main():
    name = "SCue_MCP_Graph_" + uuid.uuid4().hex[:8]
    wave_package = f"/Game/UE5MCP_Test/{name}_Wave"
    wave_path = f"{wave_package}.{name}_Wave"
    wave_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}_Wave.uasset"
    source_file = PROJECT / "Saved" / "UE5MCP_Test" / f"{name}.wav"
    cue_package = f"/Game/UE5MCP_Test/{name}"
    cue_path = f"{cue_package}.{name}"
    cue_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    cue = ""
    sound_wave = ""
    try:
        write_wav(source_file, 0.12)
        imported = request("POST", "/audio/waves/import", {
            "SourceFilePath": str(source_file),
            "DestinationPath": "/Game/UE5MCP_Test",
            "AssetName": f"{name}_Wave",
            "bSave": True,
        })
        sound_wave = imported["asset_path"]
        assert sound_wave == wave_path and wave_file.exists()

        preview = request("POST", "/sound-cues/create", {
            "AssetPath": cue_package, "bDryRun": True})
        assert preview["would_create"] and preview["dry_run"], preview
        cue = request("POST", "/sound-cues/create", {
            "AssetPath": cue_package, "bSave": True})
        assert cue == cue_path and cue_file.exists()
        graph = request("GET", "/sound-cues/graph", params={"asset_path": cue})
        roots = [node for node in graph["nodes"] if node["kind"] == "root"]
        assert graph["graph_exists"] and len(roots) == 1, graph
        root_id = roots[0]["node_id"]

        wave_add = {"AssetPath": cue, "Operation": "add_node",
                    "NodeClass": "/Script/Engine.SoundNodeWavePlayer",
                    "WavePath": sound_wave, "bSetLooping": True, "bLooping": True,
                    "PositionX": -350, "PositionY": 0}
        dry_add = request("POST", "/sound-cues/graph", {**wave_add, "bDryRun": True})
        assert dry_add["would_change"] and not dry_add["changed"], dry_add
        player = request("POST", "/sound-cues/graph", {**wave_add, "bSave": True})
        player_id = player["node_id"]
        assert player["changed"] and player_id, player

        modulator = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "add_node",
            "NodeClass": "/Script/Engine.SoundNodeModulator",
            "Properties": {"PitchMin": "0.8", "PitchMax": "1.2",
                           "VolumeMin": "0.4", "VolumeMax": "0.9"},
            "PositionX": -650, "PositionY": 100,
        })
        modulator_id = modulator["node_id"]
        assert modulator["changed"] and modulator_id, modulator

        setting_preview = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "set_node_settings",
            "NodeId": modulator_id, "Properties": {"PitchMax": "1.35"},
            "bDryRun": True,
        })
        assert setting_preview["would_change"] and not setting_preview["changed"], setting_preview
        settings = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "set_node_settings",
            "NodeId": modulator_id, "Properties": {"PitchMax": "1.35"},
        })
        assert settings["changed"], settings

        request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "connect",
            "SourceNodeId": player_id, "TargetNodeId": modulator_id,
            "InputIndex": 0,
        })
        request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "connect",
            "SourceNodeId": modulator_id, "TargetNodeId": root_id,
            "InputIndex": 0, "bSave": True,
        })
        validation = request("POST", "/sound-cues/validate", {"AssetPath": cue})
        assert validation["valid"] and not validation["errors"], validation

        move = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "move_node", "NodeId": player_id,
            "PositionX": -500, "PositionY": 250,
        })
        assert move["changed"], move
        layout = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "layout", "bSave": True,
        })
        assert layout["changed"] and layout["saved"], layout

        delete_preview = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "delete_node", "NodeId": modulator_id,
            "bDryRun": True,
        })
        assert delete_preview["would_change"] and not delete_preview["changed"], delete_preview
        request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "delete_node", "NodeId": modulator_id,
        }, expect_error=True)
        request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "delete_node", "NodeId": modulator_id,
            "bConfirm": True,
        })
        request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "connect",
            "SourceNodeId": player_id, "TargetNodeId": root_id,
            "InputIndex": 0,
        })
        compiled = request("POST", "/sound-cues/graph", {
            "AssetPath": cue, "Operation": "compile", "bSave": True,
        })
        assert compiled["changed"] and compiled["saved"], compiled
        final_validation = request("POST", "/sound-cues/validate", {"AssetPath": cue})
        assert final_validation["valid"], final_validation
        final_graph = request("GET", "/sound-cues/graph", params={"asset_path": cue})
        assert len([node for node in final_graph["nodes"] if node["kind"] == "sound_node"]) == 1, final_graph
        print("Sound Cue graph authoring live smoke passed")
    finally:
        for asset in (cue, sound_wave):
            if asset:
                request("POST", "/assets/delete", {"AssetPath": asset})
        source_file.unlink(missing_ok=True)
        for asset_file in (cue_file, wave_file):
            assert not asset_file.exists(), f"Test Sound Cue fixture was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
