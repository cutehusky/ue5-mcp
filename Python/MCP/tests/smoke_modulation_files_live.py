"""Native Sound Factory/WaveTable file transforms; formats, editing, sampling and reload."""
import argparse
import ctypes
import json
import math
import struct
import time
from pathlib import Path
import httpx
import smoke_sound_wave_formats_live as audio_formats

PROJECT = Path(__file__).resolve().parents[5]
SOURCES = PROJECT / "Saved" / "UE5MCP_ModulationFilesSmoke"
MANIFEST = PROJECT / "Saved" / "UE5MCP_ModulationFilesSmoke.json"
BUS = "/Game/UE5MCP_Test/CB_MCP_FileTransformSmoke.CB_MCP_FileTransformSmoke"
PATCH = "/Game/UE5MCP_Test/MPatch_MCP_FileTransformSmoke.MPatch_MCP_FileTransformSmoke"


def run(base, phase, dll):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base + route, json=body, params=params, timeout=180)
        r.raise_for_status()
        return r.json()

    def inspect():
        return call("GET", "/audio/modulation/settings", asset_path=PATCH)

    def info():
        return inspect()["inputs"][0]["file_transform"]

    def imported(**extra):
        return call("POST", "/audio/modulation/inputs/import", {"AssetPath":PATCH, "BusPath":BUS} | extra)

    def reject(**extra):
        r = httpx.post(base + "/audio/modulation/inputs/import", json={"AssetPath":PATCH, "BusPath":BUS} | extra, timeout=180)
        assert r.status_code >= 400, r.text

    def sample():
        return call("POST", "/audio/modulation/sample", {"AssetPath":PATCH, "BusPath":BUS, "Values":[0,.125,.25,.375,.5,.625,.75,.875,1]})["values"]

    def cleanup():
        for asset in [PATCH,BUS]:
            call("POST", "/assets/delete", {"AssetPath":asset})
        for p in SOURCES.iterdir():
            assert p.is_file()
            p.unlink()
        SOURCES.rmdir()
        MANIFEST.unlink(missing_ok=True)

    if phase == "verify":
        expected = json.loads(MANIFEST.read_text())
        try:
            state = inspect()
            assert not state["dirty"] and state["inputs"][0]["curve"] == "Shared"
            stored = info()
            assert stored["resolution"] == 128 and stored["bit_depth"] == "PCM_16" and stored["channel_index"] == 3
            assert stored["source_samples"] > 2 and stored["source_sample_rate"] == 48000
            assert all(math.isclose(x,y,abs_tol=1e-5) for x,y in zip(sample(),expected["values"]))
            assert call("POST", "/audio/validate", {"AssetPath":PATCH})["valid"]
            assert not imported(Operation="reimport", bConfirm=True)["changed"] and not inspect()["dirty"]
            source = Path(stored["source_file"])
            source.unlink()
            assert not info()["source_exists"] and sample() == expected["values"]
            assert call("POST", "/audio/validate", {"AssetPath":PATCH})["valid"]
            reject(Operation="reimport", bConfirm=True)
            # Switching away from a file transform clears its processed table cache.
            call("POST", "/audio/modulation/inputs", {"AssetPath":PATCH, "BusPath":BUS, "Curve":"Linear"})
            assert all(math.isclose(x,y,abs_tol=1e-5) for x,y in zip(sample(),[0,.125,.25,.375,.5,.625,.75,.875,1]))
            print("File transform source/cache/settings persisted; missing-source sampling, no-op reimport and curve replacement: OK")
        finally:
            cleanup()
        return

    assert dll and dll.is_file(), "Supply the installed UE libsndfile DLL"
    assert not SOURCES.exists(), "Reserved source fixture directory exists"
    SOURCES.mkdir(parents=True)
    encoder = audio_formats.Encoder(dll.resolve())
    files = {}
    for ext, fmt in audio_formats.FORMATS.items():
        p = SOURCES / ("source." + ext)
        sf = audio_formats.SFInfo(0,48000,2,fmt,0,0)
        assert encoder.lib.sf_format_check(ctypes.byref(sf))
        handle = encoder.lib.sf_open(str(p).encode(),0x20,ctypes.byref(sf))
        assert handle
        n = 4800
        data = (ctypes.c_float * (n*2))()
        for i in range(n):
            data[i*2] = .6 * math.sin(2*math.pi*i/n)
            data[i*2+1] = .3 * math.cos(4*math.pi*i/n)
        try:
            assert encoder.lib.sf_writef_float(handle,data,n) == n
        finally:
            assert encoder.lib.sf_close(handle) == 0
        files[ext] = p
    created = []
    try:
        for asset, kind in [(BUS,"bus"),(PATCH,"patch")]:
            r = call("POST", "/audio/modulation/create", {"AssetPath":asset.split(".")[0], "AssetType":kind, "bSave":True})
            assert r["asset_path"] == asset
            created.append(asset)
        before = inspect()
        assert imported(SourceFilePath=str(files["wav"]), bDryRun=True)["would_change"] and inspect() == before
        for extra in [{"SourceFilePath":"relative.wav"}, {"SourceFilePath":str(files["wav"]), "Resolution":17}, {"SourceFilePath":str(files["wav"]), "ChannelIndex":-1}, {"SourceFilePath":str(files["wav"]), "Top":.6,"Tail":.5}, {"SourceFilePath":str(files["wav"]), "BitDepth":"bad"}]:
            reject(**extra)
        bad = SOURCES / "invalid.flac"
        bad.write_bytes(b"invalid audio")
        reject(SourceFilePath=str(bad), bDryRun=True)
        bad_float = SOURCES / "invalid_float.wav"
        pcm = struct.pack("<ff",float("nan"),0)
        fmt = struct.pack("<HHIIHH",3,1,48000,192000,4,32)
        bad_float.write_bytes(b"RIFF" + struct.pack("<I",36+len(pcm)) + b"WAVEfmt " + struct.pack("<I",16) + fmt + b"data" + struct.pack("<I",len(pcm)) + pcm)
        reject(SourceFilePath=str(bad_float), bDryRun=True)
        assert inspect() == before
        for ext, p in files.items():
            imported(SourceFilePath=str(p), bConfirm=True)
            assert info()["source_exists"] and info()["resolution"] == 256
            assert all(math.isfinite(v) for v in sample())
            assert call("POST", "/audio/validate", {"AssetPath":PATCH})["valid"]
            print(f"{ext}: native decoded source and processed file transform OK")
        imported(SourceFilePath=str(files["wav"]), ChannelIndex=0, bConfirm=True)
        left = sample()
        assert left[2] > .9 and left[6] > .9 and abs(left[4]) < .05, left
        reject(Operation="reimport")
        assert not imported(Operation="reimport", bConfirm=True)["changed"]
        call("PATCH", "/audio/modulation/settings", {"AssetPath":PATCH,"bSetBypass":True,"bBypass":False})
        call("POST", "/editor/play", {"Operation":"start"})
        try:
            for _ in range(100):
                r = httpx.get(base + "/audio/modulation/runtime", timeout=180)
                if r.status_code == 200:
                    break
                time.sleep(.1)
            call("POST", "/audio/modulation/runtime", {"Operation":"create_destination","AssetPath":PATCH,"DestinationId":"file_patch"})
            call("POST", "/audio/modulation/runtime", {"Operation":"set_global","AssetPath":BUS,"TargetNormalized":.25,"FadeSeconds":0})
            for _ in range(100):
                runtime = call("GET", "/audio/modulation/runtime", asset_path=PATCH)
                if abs(runtime["value_normalized"]-left[2]) < .01:
                    break
                time.sleep(.1)
            else:
                raise AssertionError(runtime)
        finally:
            call("POST", "/editor/play", {"Operation":"stop"})
            for _ in range(100):
                if not call("GET", "/editor/status")["is_playing"]:
                    break
                time.sleep(.1)
        imported(SourceFilePath=str(files["wav"]), ChannelIndex=3, Resolution=128, BitDepth="PCM_16", Phase=.25, Top=.1, Tail=.2, FadeIn=.125, FadeOut=.25, bConfirm=True, bSave=True)
        stored = info()
        assert .24999 < stored["fade_out"] < .25 and stored["channel_index"] == 3
        assert not imported(Operation="reimport", bConfirm=True)["changed"] and not inspect()["dirty"]
        assert imported(Operation="reimport", SourceFilePath=str(files["flac"]), bConfirm=True, bSave=True)["changed"]
        assert info()["resolution"] == 128 and info()["bit_depth"] == "PCM_16" and info()["channel_index"] == 3
        call("POST", "/editor/transactions/undo")
        assert Path(info()["source_file"]).suffix == ".wav" and call("POST", "/audio/validate", {"AssetPath":PATCH})["valid"]
        call("POST", "/editor/transactions/redo")
        assert Path(info()["source_file"]).suffix == ".flac" and call("POST", "/audio/validate", {"AssetPath":PATCH})["valid"]
        call("POST", "/assets/save", {"AssetPath":PATCH})
        MANIFEST.write_text(json.dumps({"values":sample()}))
        print("Native format/channel imports, trim/phase/fades, PCM16 cache, source replacement and save: OK")
    except BaseException:
        for asset in reversed(created):
            call("POST", "/assets/delete", {"AssetPath":asset})
        for p in SOURCES.iterdir():
            p.unlink()
        SOURCES.rmdir()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", required=True, choices=["create","verify"])
    parser.add_argument("--sndfile-dll", type=Path)
    args = parser.parse_args()
    run(args.base,args.phase,args.sndfile_dll)
