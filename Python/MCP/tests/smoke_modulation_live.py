"""Native modulation parameter/bus/mix authoring, conversions and saved-state regression."""
import argparse
import json
import math
from pathlib import Path
import httpx

PROJECT = Path(__file__).resolve().parents[5]
MANIFEST = PROJECT / "Saved" / "UE5MCP_ModulationSmoke.json"
TYPES = ["scalar", "scaled", "frequency", "filter_frequency", "volume", "bipolar", "additive"]
ROOT = "/Game/UE5MCP_Test/"
PARAMETERS = {kind: ROOT + "MP_MCP_Smoke_" + kind + ".MP_MCP_Smoke_" + kind for kind in TYPES}
BUS = ROOT + "CB_MCP_Smoke.CB_MCP_Smoke"
BUS_VOLUME = ROOT + "CB_MCP_VolumeSmoke.CB_MCP_VolumeSmoke"
MIX = ROOT + "CBM_MCP_Smoke.CBM_MCP_Smoke"
PATHS = list(PARAMETERS.values()) + [BUS, BUS_VOLUME, MIX]
INVALID = "/Engine/EngineSounds/1kSineTonePing.1kSineTonePing"


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

    def stage(bus=BUS, **extra):
        return call("POST", "/audio/modulation/stages", {"AssetPath": MIX, "BusPath": bus} | extra)

    def convert(path, values, direction="normalized_to_unit"):
        return call("POST", "/audio/modulation/convert", {"AssetPath": path, "Values": values, "Direction": direction})["values"]

    def near(values, expected):
        assert len(values) == len(expected)
        assert all(math.isclose(x, y, rel_tol=1e-4, abs_tol=1e-4) for x, y in zip(values, expected)), (values, expected)

    def cleanup():
        for path in reversed(PATHS):
            call("POST", "/assets/delete", {"AssetPath": path})
        MANIFEST.unlink(missing_ok=True)

    def verify():
        for path in PATHS:
            assert call("POST", "/audio/modulation/validate", {"AssetPath": path})["valid"]
            assert call("POST", "/audio/validate", {"AssetPath": path})["valid"]
            assert not inspect(path)["dirty"]
        p = PARAMETERS["scaled"]
        assert inspect(p)["default_normalized"] == .75 and inspect(p)["default_unit"] == 6
        assert inspect(p)["unit_display_name"] == "semitones"
        near(convert(p, [0, .25, .5, .75, 1]), [-12, -6, 0, 6, 12])
        near(convert(p, [-12, -6, 0, 6, 12], "unit_to_normalized"), [0, .25, .5, .75, 1])
        near(convert(PARAMETERS["frequency"], [0, .5, 1]), [20, math.sqrt(20 * 20000), 20000])
        near(convert(PARAMETERS["bipolar"], [0, .5, 1]), [-2, 0, 2])
        near(convert(PARAMETERS["volume"], [1]), [0])
        assert inspect(PARAMETERS["volume"])["numeric"]["MinVolume"] == -80
        assert inspect(BUS)["parameter_path"] == p and inspect(BUS)["address"] == "music.pitch"
        assert inspect(BUS)["override_address"] and inspect(BUS)["bypass"]
        state = inspect(MIX)
        assert state["duration_seconds"] == 5 and state["retrigger_on_activation"] and len(state["stages"]) == 2
        s = next(s for s in state["stages"] if s["bus_path"] == BUS)
        assert s["target_normalized"] == .25 and s["attack_seconds"] == .3 and s["release_seconds"] == .7
        assert s["target_unit"] == -6
        assert not edit(p, Numeric={"DefaultNormalized": .75})["changed"]
        assert not edit(BUS, bSetBypass=True, bBypass=True)["changed"]
        assert not edit(MIX, Numeric={"DurationSeconds": 5})["changed"]
        assert not stage(TargetNormalized=.25, AttackSeconds=.3, ReleaseSeconds=.7)["changed"]
        assert all(not inspect(path)["dirty"] for path in PATHS)
        print("Modulation native parameter classes, conversions, bus references and mix stages persisted: OK")

    if phase == "verify":
        assert MANIFEST.exists(), "Run create before restarting the editor"
        try:
            verify()
            reject("/audio/modulation/stages", {"AssetPath": MIX, "Operation": "remove", "BusPath": BUS})
            assert stage(Operation="remove", bDryRun=True)["would_change"]
            assert len(inspect(MIX)["stages"]) == 2
            assert stage(Operation="remove", bConfirm=True)["changed"]
            assert stage(Operation="clear", bConfirm=True)["changed"]
            assert not stage(Operation="clear", bConfirm=True)["changed"]
            edit(BUS, bSetParameter=True, ParameterPath="", bSetAddress=True, bOverrideAddress=False)
            assert inspect(BUS)["parameter_path"] == "" and inspect(BUS)["address"] == "CB_MCP_Smoke"
            assert not call("GET", "/assets/dirty-state", asset_path=INVALID)["dirty"]
        finally:
            cleanup()
        print("Modulation confirmed stage removal/clear, bus link clearing, source preservation and cleanup: OK")
        return

    created = []
    try:
        preflight = call("POST", "/audio/modulation/create", {"AssetPath": PARAMETERS["scaled"].split(".")[0], "AssetType": "parameter", "ParameterType": "scaled", "bDryRun": True})
        assert preflight["dry_run"] and not preflight["created"]
        reject("/audio/modulation/create", {"AssetPath": "/Engine/MP_Invalid", "AssetType": "parameter"})
        reject("/audio/modulation/create", {"AssetPath": "/Game/MP_Invalid", "AssetType": "parameter", "ParameterType": "invalid"})
        for kind, path in PARAMETERS.items():
            result = call("POST", "/audio/modulation/create", {"AssetPath": path.split(".")[0], "AssetType": "parameter", "ParameterType": kind, "bSave": True})
            assert result["asset_path"] == path, "Fixture already exists; clean it before testing"
            created.append(path)
        p = PARAMETERS["scaled"]
        before = inspect(p)
        assert edit(p, Numeric={"UnitMin": -12, "UnitMax": 12, "DefaultNormalized": .75}, bDryRun=True)["would_change"]
        assert inspect(p) == before
        for numeric in [{"UnitMin": 2, "UnitMax": 1}, {"DefaultNormalized": 2}, {"MinVolume": -50}, {"Bogus": 1}]:
            reject("/audio/modulation/settings", {"AssetPath": p, "Numeric": numeric}, "PATCH")
        assert inspect(p) == before
        edit(p, Numeric={"UnitMin": -12, "UnitMax": 12, "DefaultNormalized": .75}, bSetUnitDisplayName=True, UnitDisplayName="semitones", bSave=True)
        edit(PARAMETERS["frequency"], Numeric={"UnitMin": 20, "UnitMax": 20000}, bSave=True)
        edit(PARAMETERS["volume"], Numeric={"MinVolume": -80}, bSave=True)
        edit(PARAMETERS["bipolar"], Numeric={"UnitRange": 4}, bSave=True)
        reject("/audio/modulation/convert", {"AssetPath": p, "Values": [1.1]})
        reject("/audio/modulation/convert", {"AssetPath": p, "Values": [13], "Direction": "unit_to_normalized"})
        reject("/audio/modulation/create", {"AssetPath": BUS.split(".")[0], "ParameterPath": INVALID})
        for path, parameter in [(BUS, p), (BUS_VOLUME, PARAMETERS["volume"])]:
            r = call("POST", "/audio/modulation/create", {"AssetPath": path.split(".")[0], "ParameterPath": parameter, "bSave": True})
            assert r["asset_path"] == path
            created.append(path)
        before = inspect(BUS)
        assert edit(BUS, bSetBypass=True, bBypass=True, bSetAddress=True, bOverrideAddress=True, Address="music.pitch", bDryRun=True)["would_change"]
        assert inspect(BUS) == before
        reject("/audio/modulation/settings", {"AssetPath": BUS, "bSetParameter": True, "ParameterPath": INVALID}, "PATCH")
        reject("/audio/modulation/settings", {"AssetPath": BUS, "bSetGenerators": True, "GeneratorPaths": [p]}, "PATCH")
        reject("/audio/modulation/settings", {"AssetPath": BUS, "bSetAddress": True, "bOverrideAddress": True}, "PATCH")
        assert inspect(BUS) == before
        edit(BUS, bSetBypass=True, bBypass=True, bSetAddress=True, bOverrideAddress=True, Address="music.pitch", bSave=True)
        r = call("POST", "/audio/modulation/create", {"AssetPath": MIX.split(".")[0], "AssetType": "mix", "bSave": True})
        assert r["asset_path"] == MIX
        created.append(MIX)
        reject("/audio/modulation/settings", {"AssetPath": MIX, "Numeric": {"DurationSeconds": -2}}, "PATCH")
        edit(MIX, Numeric={"DurationSeconds": 5}, bSetRetriggerOnActivation=True, bRetriggerOnActivation=True, bSave=True)
        assert stage(TargetNormalized=.25, AttackSeconds=.3, ReleaseSeconds=.7, bDryRun=True)["would_change"]
        assert inspect(MIX)["stages"] == []
        reject("/audio/modulation/stages", {"AssetPath": MIX, "BusPath": BUS, "TargetNormalized": 2})
        reject("/audio/modulation/stages", {"AssetPath": MIX, "BusPath": INVALID})
        stage(TargetNormalized=.25, AttackSeconds=.3, ReleaseSeconds=.7, bSave=True)
        stage(BUS_VOLUME, TargetNormalized=.5, bSave=True)
        verify()
        MANIFEST.write_text(json.dumps({"paths": PATHS}), encoding="utf-8")
    except BaseException:
        for path in reversed(created):
            call("POST", "/assets/delete", {"AssetPath": path})
        raise
    print("Modulation creation, preflight/invalid requests, native settings/conversions, save and source preservation: OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", choices=["create", "verify"], required=True)
    args = parser.parse_args()
    run(args.base, args.phase)
