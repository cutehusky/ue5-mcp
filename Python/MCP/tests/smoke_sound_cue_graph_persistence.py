"""Two-session Sound Cue graph save/reload test; run write, restart editor, then verify."""

import math
import struct
import sys
import wave
from pathlib import Path

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
CUE = "/Game/UE5MCP_Test/SCue_MCP_Persist.SCue_MCP_Persist"
WAVE = "/Game/UE5MCP_Test/SW_MCP_CuePersist.SW_MCP_CuePersist"
SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "SW_MCP_CuePersist.wav"
CUE_FILE = PROJECT / "Content" / "UE5MCP_Test" / "SCue_MCP_Persist.uasset"
WAVE_FILE = PROJECT / "Content" / "UE5MCP_Test" / "SW_MCP_CuePersist.uasset"


def write_wav(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    samples = [int(8000 * math.sin(2 * math.pi * 440 * n / sample_rate))
               for n in range(round(sample_rate * 0.12))]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def find_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from find_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from find_strings(item)


def main(phase: str):
    if phase == "write":
        assert not CUE_FILE.exists() and not WAVE_FILE.exists(), "Persistence fixture already exists"
        write_wav(SOURCE)
        imported = request("POST", "/audio/waves/import", {
            "SourceFilePath": str(SOURCE), "DestinationPath": "/Game/UE5MCP_Test",
            "AssetName": "SW_MCP_CuePersist", "bSave": True})
        assert imported["asset_path"] == WAVE and WAVE_FILE.exists(), imported
        cue = request("POST", "/sound-cues/create", {"AssetPath": CUE[:-len(".SCue_MCP_Persist")], "bSave": True})
        assert cue == CUE and CUE_FILE.exists(), cue
        graph = request("GET", "/sound-cues/graph", params={"asset_path": CUE})
        root = next(node for node in graph["nodes"] if node["kind"] == "root")
        player = request("POST", "/sound-cues/graph", {
            "AssetPath": CUE, "Operation": "add_node",
            "NodeClass": "/Script/Engine.SoundNodeWavePlayer", "WavePath": WAVE,
            "PositionX": -350})
        modulator = request("POST", "/sound-cues/graph", {
            "AssetPath": CUE, "Operation": "add_node",
            "NodeClass": "/Script/Engine.SoundNodeModulator",
            "Properties": {"PitchMin": "0.75", "PitchMax": "1.4", "VolumeMin": "0.5"},
            "PositionX": -650})
        request("POST", "/sound-cues/graph", {
            "AssetPath": CUE, "Operation": "connect", "SourceNodeId": player["node_id"],
            "TargetNodeId": modulator["node_id"], "InputIndex": 0})
        request("POST", "/sound-cues/graph", {
            "AssetPath": CUE, "Operation": "connect", "SourceNodeId": modulator["node_id"],
            "TargetNodeId": root["node_id"], "InputIndex": 0})
        saved = request("POST", "/sound-cues/graph", {
            "AssetPath": CUE, "Operation": "compile", "bSave": True})
        assert saved["saved"], saved
        valid = request("POST", "/sound-cues/validate", {"AssetPath": CUE})
        assert valid["valid"], valid
        print("Saved Sound Cue graph for restart verification")
    elif phase == "verify":
        try:
            graph = request("GET", "/sound-cues/graph", params={"asset_path": CUE})
            assert graph["graph_exists"] and graph["first_node_path"], graph
            nodes = [node for node in graph["nodes"] if node["kind"] == "sound_node"]
            assert len(nodes) == 2, nodes
            modulator = next(node for node in nodes if node["node_class"] == "/Script/Engine.SoundNodeModulator")
            player = next(node for node in nodes if node["node_class"] == "/Script/Engine.SoundNodeWavePlayer")
            assert modulator["settings"]["PitchMax"] == 1.4, modulator
            assert any(WAVE in value for value in find_strings(player["settings"])), player
            root = next(node for node in graph["nodes"] if node["kind"] == "root")
            assert root["inputs"][0]["source_node_id"] == modulator["node_id"], root
            assert modulator["inputs"][0]["source_node_id"] == player["node_id"], modulator
            assert request("POST", "/sound-cues/validate", {"AssetPath": CUE})["valid"]
            print("Sound Cue graph links and Wave Player reference survived editor restart")
        finally:
            request("POST", "/assets/delete", {"AssetPath": CUE})
            request("POST", "/assets/delete", {"AssetPath": WAVE})
            SOURCE.unlink(missing_ok=True)
            assert not CUE_FILE.exists() and not WAVE_FILE.exists(), "Persistence assets were not removed"
    else:
        raise SystemExit("usage: smoke_sound_cue_graph_persistence.py write|verify")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
