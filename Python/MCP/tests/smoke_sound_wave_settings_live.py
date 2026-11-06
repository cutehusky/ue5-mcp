"""Exercise typed Sound Wave settings, validation, platform-data rebuild, and cleanup."""

import math
import struct
import uuid
import wave
from pathlib import Path

import httpx

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
BASE = "http://127.0.0.1:8080"


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
    name = "SW_MCP_Settings_" + uuid.uuid4().hex[:8]
    wave_path = f"/Game/UE5MCP_Test/{name}.{name}"
    wave_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    source_file = PROJECT / "Saved" / "UE5MCP_Test" / f"{name}.wav"
    attenuation_package = f"/Game/UE5MCP_Test/{name}_Attenuation"
    attenuation_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}_Attenuation.uasset"
    concurrency_package = f"/Game/UE5MCP_Test/{name}_Concurrency"
    concurrency_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}_Concurrency.uasset"
    attenuation_path = ""
    concurrency_path = ""
    imported_path = ""
    try:
        write_wav(source_file, 0.12)
        attenuation_path = request("POST", "/audio/attenuations/create", {
            "AssetPath": attenuation_package, "bSave": True})
        concurrency_path = request("POST", "/audio/concurrencies/create", {
            "AssetPath": concurrency_package, "bSave": True})
        imported_path = request("POST", "/audio/waves/import", {
            "SourceFilePath": str(source_file),
            "DestinationPath": "/Game/UE5MCP_Test",
            "AssetName": name,
            "bSave": True,
        })["asset_path"]
        assert imported_path == wave_path and wave_file.exists()

        initial = request("GET", "/audio/waves/settings", params={"asset_path": wave_path})
        assert initial["channels"] == 1 and initial["imported_sample_rate"] == 22050, initial
        proposed = {
            "AssetPath": wave_path,
            "CompressionType": "PCM",
            "bSetCompressionQuality": True,
            "CompressionQuality": 87,
            "SampleRateQuality": "High",
            "bSetLooping": True,
            "bLooping": True,
            "LoadingBehavior": "LoadOnDemand",
            "bSetAttenuation": True,
            "AttenuationPath": attenuation_path,
            "bSetConcurrencyPaths": True,
            "ConcurrencyPaths": [concurrency_path],
        }
        preview = request("PATCH", "/audio/waves/settings", {**proposed, "bDryRun": True})
        assert preview["would_change"] and not preview["changed"] and preview["dry_run"], preview
        unchanged = request("GET", "/audio/waves/settings", params={"asset_path": wave_path})
        assert unchanged["looping"] is False and unchanged["attenuation_path"] == "", unchanged
        request("PATCH", "/audio/waves/settings", {
            "AssetPath": wave_path, "bSetCompressionQuality": True,
            "CompressionQuality": 101}, expect_error=True)

        changed = request("PATCH", "/audio/waves/settings", {**proposed, "bSave": True})
        assert changed["changed"] and changed["saved"] and not changed["dirty"], changed
        settings = request("GET", "/audio/waves/settings", params={"asset_path": wave_path})
        assert settings["compression_type"] == "PCM", settings
        assert settings["compression_quality"] == 87, settings
        assert settings["effective_compression_quality"] == 100, settings
        assert settings["sample_rate_quality"] == "High", settings
        assert settings["looping"] and settings["loading_behavior_override"] == "LoadOnDemand", settings
        assert settings["attenuation_path"] == attenuation_path, settings
        assert settings["concurrency_paths"] == [concurrency_path], settings

        validation = request("POST", "/audio/waves/validate", {"AssetPath": wave_path})
        assert validation["valid"] and not validation["errors"], validation
        rebuild_preview = request("POST", "/audio/waves/rebuild", {
            "AssetPath": wave_path, "bDryRun": True})
        assert rebuild_preview["would_rebuild"] and rebuild_preview["dry_run"], rebuild_preview
        response = httpx.post(f"{BASE}/audio/waves/rebuild", json={"AssetPath": wave_path}, timeout=180)
        response.raise_for_status()
        rebuild = response.json()
        assert rebuild["rebuilt"] and rebuild["completed"], rebuild
        print("Sound Wave typed settings, validation, and rebuild smoke passed")
    finally:
        for asset in (imported_path, attenuation_path, concurrency_path):
            if asset:
                request("POST", "/assets/delete", {"AssetPath": asset})
        source_file.unlink(missing_ok=True)
        for asset_file in (wave_file, attenuation_file, concurrency_file):
            assert not asset_file.exists(), f"Test Sound Wave asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
