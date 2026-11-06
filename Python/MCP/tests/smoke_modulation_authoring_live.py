"""Native generators, patch transforms, source/reference validation and save/reload."""
import argparse
import json
import math
from pathlib import Path
import httpx

PROJECT = Path(__file__).resolve().parents[5]
MANIFEST = PROJECT / "Saved" / "UE5MCP_ModulationAuthoringSmoke.json"


def asset(name):
    return f"/Game/UE5MCP_Test/{name}.{name}"


LFO, AD, FOLLOWER = [asset("MG_MCP_Smoke_" + kind) for kind in ("LFO", "AD", "Follower")]
AUDIO = asset("AB_MCP_GeneratorSmoke")
BUSES = [asset("CB_MCP_GeneratorSmoke_" + str(i)) for i in range(3)]
PATCH = asset("MPatch_MCP_GeneratorSmoke")
PARAMETER = asset("MParam_MCP_GeneratorSmoke")
PATHS = [LFO, AD, FOLLOWER, AUDIO, PARAMETER] + BUSES + [PATCH]
SHARED = "/Engine/Tutorial/ContentIntroCurve.ContentIntroCurve"
INVALID = "/Engine/EngineSounds/1kSineTonePing.1kSineTonePing"
KEYS = [{"Time": 0, "Value": 0}, {"Time": .5, "Value": .25}, {"Time": 1, "Value": 1}]


def run(base, phase):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base + route, json=body, params=params, timeout=180)
        r.raise_for_status()
        return r.json()

    def reject(route, body, method="POST"):
        r = httpx.request(method, base + route, json=body, timeout=180)
        assert r.status_code >= 400, r.text

    def inspect(path):
        return call("GET", "/audio/modulation/settings", asset_path=path)

    def edit(path, **extra):
        return call("PATCH", "/audio/modulation/settings", {"AssetPath": path} | extra)

    def gen(path, **extra):
        return call("PATCH", "/audio/modulation/generators/settings", {"AssetPath": path} | extra)

    def inp(bus=BUSES[0], **extra):
        return call("POST", "/audio/modulation/inputs", {"AssetPath": PATCH, "BusPath": bus} | extra)

    def sample(path, **extra):
        return call("POST", "/audio/modulation/sample", {"AssetPath": path} | extra)

    def near(actual, expected):
        assert len(actual) == len(expected)
        assert all(math.isclose(a, b, rel_tol=1e-4, abs_tol=1e-4) for a, b in zip(actual, expected)), (actual, expected)

    def cleanup():
        for path in reversed(PATHS):
            call("POST", "/assets/delete", {"AssetPath": path})
        MANIFEST.unlink(missing_ok=True)

    def verify():
        for path in PATHS:
            assert call("POST", "/audio/validate", {"AssetPath": path})["valid"]
            assert not inspect(path)["dirty"]
        assert inspect(LFO)["numeric"]["Frequency"] == 2 and inspect(LFO)["shape"] == "Sine"
        lfo = sample(LFO, Samples=32, StepSeconds=.02)
        assert "fresh_native" in lfo["scope"] and len(lfo["values"]) == 32
        assert all(math.isfinite(v) for v in lfo["values"]) and max(lfo["values"]) - min(lfo["values"]) > .1
        envelope = sample(AD, Samples=32, StepSeconds=.05)["values"]
        assert max(envelope) > .5 and envelope[-1] < .05, envelope
        assert inspect(FOLLOWER)["audio_bus_path"] == AUDIO and inspect(FOLLOWER)["flags"]["bInvert"]
        assert inspect(AUDIO)["channels"] == 2
        for path, generator in zip(BUSES, [LFO, AD, FOLLOWER]):
            assert inspect(path)["generator_paths"] == [generator]
        patch = inspect(PATCH)
        assert not patch["bypass"] and patch["parameter_path"] == PARAMETER and len(patch["inputs"]) == 3
        assert patch["inputs"][0]["curve"] == "Custom" and patch["inputs"][0]["sample_and_hold"]
        assert patch["inputs"][1]["curve"] == "Linear_Inv"
        assert patch["inputs"][2]["curve"] == "Shared" and patch["inputs"][2]["curve_path"] == SHARED
        near(sample(PATCH, BusPath=BUSES[0], Values=[0,.25,.5,.75,1])["values"], [0,.125,.25,.625,1])
        near(sample(PATCH, BusPath=BUSES[1], Values=[0,.25,.5,.75,1])["values"], [1,.75,.5,.25,0])
        assert all(math.isfinite(v) for v in sample(PATCH, BusPath=BUSES[2], Values=[0,.25,.5,.75,1])["values"])
        assert not gen(LFO, Numeric={"Frequency": 2})["changed"]
        assert not gen(FOLLOWER, bSetAudioBus=True, AudioBusPath=AUDIO)["changed"]
        assert not edit(AUDIO, Numeric={"Channels": 2})["changed"]
        assert not edit(PATCH, bSetBypass=True, bBypass=False)["changed"]
        assert not inp(Curve="Custom", Keys=KEYS, bSampleAndHold=True)["changed"]
        assert all(not inspect(path)["dirty"] for path in PATHS)
        assert not call("GET", "/assets/dirty-state", asset_path=SHARED)["dirty"]
        assert not call("GET", "/assets/dirty-state", asset_path=INVALID)["dirty"]
        print("Generator settings/native sampling, Audio Bus/follower, generator links, patch curves and clean no-ops: OK")

    if phase == "verify":
        assert MANIFEST.exists(), "Run create before restarting"
        try:
            verify()
            reject("/audio/modulation/inputs", {"AssetPath": PATCH, "Operation": "remove", "BusPath": BUSES[0]})
            assert inp(Operation="remove", bDryRun=True)["would_change"] and len(inspect(PATCH)["inputs"]) == 3
            assert inp(Operation="remove", bConfirm=True)["changed"]
            assert inp(Operation="clear", bConfirm=True)["changed"]
            assert not inp(Operation="clear", bConfirm=True)["changed"]
            reject("/audio/modulation/settings", {"AssetPath": BUSES[0], "bSetGenerators": True, "GeneratorPaths": []}, "PATCH")
            assert edit(BUSES[0], bSetGenerators=True, GeneratorPaths=[], bDryRun=True)["would_change"]
            assert inspect(BUSES[0])["generator_paths"] == [LFO]
            assert edit(BUSES[0], bSetGenerators=True, GeneratorPaths=[], bConfirm=True)["changed"]
            gen(FOLLOWER, bSetAudioBus=True, AudioBusPath="")
            assert not inspect(FOLLOWER)["has_audio_source"]
        finally:
            cleanup()
        print("Generator/patch save-reload, confirmed removal/clear, source clearing and cleanup: OK")
        return

    created = []

    def create(path, kind, **extra):
        r = call("POST", "/audio/modulation/create", {"AssetPath": path.split(".")[0], "AssetType": kind, "bSave": True} | extra)
        assert r["asset_path"] == path, "Fixture exists; clean it before testing"
        created.append(path)

    try:
        assert not call("POST", "/audio/modulation/create", {"AssetPath": LFO.split(".")[0], "AssetType": "generator", "bDryRun": True})["created"]
        reject("/audio/modulation/create", {"AssetPath": LFO.split(".")[0], "AssetType": "generator", "GeneratorType": "unknown"})
        for path, kind in [(LFO,"lfo"), (AD,"ad_envelope"), (FOLLOWER,"envelope_follower")]:
            create(path, "generator", GeneratorType=kind)
        create(AUDIO, "audio_bus")
        create(PARAMETER, "parameter", ParameterType="scaled")
        edit(PARAMETER, Numeric={"UnitMin": -1, "UnitMax": 1}, bSave=True)
        before = inspect(LFO)
        assert gen(LFO, Numeric={"Frequency": 2}, bDryRun=True)["would_change"] and inspect(LFO) == before
        for extra in [{"Numeric": {"Frequency": -1}}, {"Numeric": {"Gain": 2}}, {"Shape": "COUNT"}, {"Flags": {"bInvert": True}}, {"bSetAudioBus": True, "AudioBusPath": AUDIO}]:
            reject("/audio/modulation/generators/settings", {"AssetPath": LFO} | extra, "PATCH")
        assert inspect(LFO) == before
        gen(LFO, Numeric={"Frequency": 2, "Amplitude": .5, "Offset": .2, "Phase": .25}, Shape="Sine", bSave=True)
        gen(AD, Numeric={"AttackTime": .3, "DecayTime": .6}, Flags={"bLooping": False}, bSave=True)
        reject("/audio/modulation/generators/settings", {"AssetPath": AD, "Numeric": {"AttackTime": 0, "DecayTime": 0}, "Flags": {"bLooping": True}}, "PATCH")
        reject("/audio/modulation/settings", {"AssetPath": AUDIO, "Numeric": {"Channels": 3}}, "PATCH")
        edit(AUDIO, Numeric={"Channels": 2}, bSave=True)
        reject("/audio/modulation/generators/settings", {"AssetPath": FOLLOWER, "bSetAudioBus": True, "AudioBusPath": LFO}, "PATCH")
        gen(FOLLOWER, Numeric={"Gain": 2, "AttackTime": .05, "ReleaseTime": .2}, Flags={"bInvert": True}, bSetAudioBus=True, AudioBusPath=AUDIO, bSave=True)
        reject("/audio/modulation/sample", {"AssetPath": FOLLOWER})
        reject("/audio/modulation/sample", {"AssetPath": LFO, "Samples": 513})
        for path, generator in zip(BUSES, [LFO, AD, FOLLOWER]):
            create(path, "bus", ParameterPath=PARAMETER)
            reject("/audio/modulation/settings", {"AssetPath": path, "bSetGenerators": True, "GeneratorPaths": [generator,generator]}, "PATCH")
            edit(path, bSetGenerators=True, GeneratorPaths=[generator], bSave=True)
        create(PATCH, "patch", ParameterPath=PARAMETER)
        edit(PATCH, bSetBypass=True, bBypass=False, bSave=True)
        before = inspect(PATCH)
        assert inp(Curve="Custom", Keys=KEYS, bSampleAndHold=True, bDryRun=True)["would_change"] and inspect(PATCH) == before
        for extra in [{"Curve": "File"}, {"Curve": "Shared", "CurvePath": INVALID}, {"Curve": "Custom", "Keys": list(reversed(KEYS))}, {"Curve": "Custom", "Keys": [{"Time": 0, "Value": 2}, {"Time": 1, "Value": 1}]}, {"Scalar": 0}]:
            reject("/audio/modulation/inputs", {"AssetPath": PATCH, "BusPath": BUSES[0]} | extra)
        assert inspect(PATCH) == before
        # Built-in/native custom curve paths before saving the final fixture.
        for curve in ["Linear", "Exp", "Exp_Inverse", "Log", "Sin", "Sin_Full", "SCurve"]:
            inp(Curve=curve)
            assert all(math.isfinite(v) for v in sample(PATCH, BusPath=BUSES[0], Values=[0,.25,.5,.75,1])["values"])
        for mode in ["Constant", "Cubic"]:
            inp(Curve="Custom", Keys=[k | {"Interpolation": mode} for k in KEYS])
            assert all(math.isfinite(v) for v in sample(PATCH, BusPath=BUSES[0], Values=[0,.25,.5,.75,1])["values"])
        inp(Curve="Custom", Keys=KEYS, bSampleAndHold=True, bSave=True)
        inp(BUSES[1], Curve="Linear_Inv", bSave=True)
        inp(BUSES[2], Curve="Shared", CurvePath=SHARED, bSave=True)
        verify()
        MANIFEST.write_text(json.dumps({"paths": PATHS}), encoding="utf-8")
    except BaseException:
        for path in reversed(created):
            call("POST", "/assets/delete", {"AssetPath": path})
        raise
    print("Generator/patch creation, dry-run/invalid requests, transform methods, sampling and save: OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", required=True, choices=["create","verify"])
    args = parser.parse_args()
    run(args.base, args.phase)
