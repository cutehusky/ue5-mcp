"""Live guarded WAV import, source inspection, replacement, and reimport test."""

import math
import struct
import wave
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
ASSET = "/Game/UE5MCP_Test/SW_MCP_ImportSmoke.SW_MCP_ImportSmoke"
PROJECT = Path(__file__).resolve().parents[5]
SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "SW_MCP_ImportSmoke.wav"
OTHER_SOURCE = PROJECT / "Saved" / "UE5MCP_Test" / "SW_MCP_ImportSmoke_Alternate.wav"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "SW_MCP_ImportSmoke.uasset"


def write_wav(path, duration):
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    samples = [int(8000 * math.sin(2 * math.pi * 440 * n / sample_rate))
               for n in range(round(sample_rate * duration))]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def call(method, route, body=None, **params):
    response = httpx.request(method, BASE + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def main():
    assert not ASSET_FILE.exists(), f"Disposable test asset already exists: {ASSET_FILE}"
    write_wav(SOURCE, 0.10)
    try:
        request = {"SourceFilePath": str(SOURCE), "DestinationPath": "/Game/UE5MCP_Test",
                   "AssetName": "SW_MCP_ImportSmoke"}
        dry = call("POST", "/audio/waves/import", request | {"bDryRun": True})
        assert dry["dry_run"] and not dry["changed"] and dry["asset_path"] == ASSET
        imported = call("POST", "/audio/waves/import", request | {"bSave": True})
        assert imported["asset_path"] == ASSET and imported["saved"] and ASSET_FILE.exists()
        source = call("GET", "/audio/waves/source", asset_path=ASSET)
        assert source["channels"] == 1 and source["imported_sample_rate"] == 22050
        assert abs(source["duration_seconds"] - 0.10) < 0.02
        assert source["source_files"][0]["exists"]

        duplicate = httpx.post(BASE + "/audio/waves/import", json=request, timeout=120)
        assert duplicate.status_code >= 400
        write_wav(SOURCE, 0.15)
        replaced = call("POST", "/audio/waves/import", request | {
            "bReplaceExisting": True, "bConfirmReplace": True, "bSave": True})
        assert replaced["changed"] and replaced["replaced"] and replaced["saved"]
        assert abs(call("GET", "/audio/waves/source", asset_path=ASSET)["duration_seconds"] - 0.15) < 0.02

        write_wav(SOURCE, 0.20)
        dry_reimport = call("POST", "/audio/waves/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bDryRun": True})
        assert dry_reimport["dry_run"] and not dry_reimport["changed"]
        changed = call("POST", "/audio/waves/reimport", {
            "AssetPath": ASSET, "bConfirmReimport": True, "bSave": True})
        assert changed["changed"] and changed["saved"]
        assert abs(call("GET", "/audio/waves/source", asset_path=ASSET)["duration_seconds"] - 0.20) < 0.02

        write_wav(OTHER_SOURCE, 0.25)
        source_change = {"AssetPath": ASSET, "SourceFilePath": str(OTHER_SOURCE),
                         "bConfirmReimport": True}
        unconfirmed = httpx.post(BASE + "/audio/waves/reimport", json=source_change, timeout=120)
        assert unconfirmed.status_code >= 400
        switched = call("POST", "/audio/waves/reimport", source_change | {
            "bConfirmSourceChange": True, "bSave": True})
        assert switched["changed"] and switched["saved"]
        after = call("GET", "/audio/waves/source", asset_path=ASSET)
        assert abs(after["duration_seconds"] - 0.25) < 0.02
        assert Path(after["source_files"][0]["path"]).resolve() == OTHER_SOURCE.resolve()
        print("Sound Wave WAV import, source inspection, replacement, and reimport: OK")
    finally:
        if ASSET_FILE.exists():
            call("POST", "/assets/delete", {"AssetPath": ASSET})
        SOURCE.unlink(missing_ok=True)
        OTHER_SOURCE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
