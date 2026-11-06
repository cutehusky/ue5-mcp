"""Native inactive/active mix profile capture, guarded loading and editor restart persistence."""
import argparse
import json
import time
from pathlib import Path
import httpx

PROJECT = Path(__file__).resolve().parents[5]
MANIFEST = PROJECT / "Saved" / "UE5MCP_ModulationProfilesSmoke.json"
BUS = "/Game/UE5MCP_Test/MProfile_MCP_BusSmoke.MProfile_MCP_BusSmoke"
MIX = "/Game/UE5MCP_Test/MProfile_MCP_MixSmoke.MProfile_MCP_MixSmoke"
PATHS = [BUS, MIX]


def run(base, phase):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base + route, json=body, params=params, timeout=180)
        r.raise_for_status()
        return r.json()

    def profile(index):
        return call("GET", "/audio/modulation/profiles", asset_path=MIX, profile_index=index)

    def control(operation, index, **extra):
        return call("POST", "/audio/modulation/profiles", {"AssetPath": MIX, "Operation": operation, "ProfileIndex": index} | extra)

    def runtime(op, **extra):
        return call("POST", "/audio/modulation/runtime", {"AssetPath": MIX, "Operation": op} | extra)

    def settings():
        return call("GET", "/audio/modulation/settings", asset_path=MIX)

    def reject(index, op="load", **extra):
        r = httpx.post(base + "/audio/modulation/profiles", json={"AssetPath": MIX, "Operation": op, "ProfileIndex": index} | extra, timeout=180)
        assert r.status_code >= 400, r.text

    def wait_profile(index, target):
        for _ in range(100):
            p = profile(index)
            if p["exists"] and len(p["stages"]) == 1 and abs(p["stages"][0]["target_normalized"] - target) < .001:
                return p
            time.sleep(.1)
        raise AssertionError(p)

    def start():
        call("POST", "/editor/play", {"Operation": "start"})
        for _ in range(100):
            r = httpx.get(base + "/audio/modulation/runtime", timeout=180)
            if r.status_code == 200:
                assert r.json()["modulation_available"]
                return
            time.sleep(.1)
        raise AssertionError(r.text)

    def stop():
        call("POST", "/editor/play", {"Operation":"stop"})
        for _ in range(100):
            if not call("GET", "/editor/status")["is_playing"]:
                return
            time.sleep(.1)

    def file_path(info):
        p = Path(info["profile_path"]).resolve()
        assert p.is_relative_to((PROJECT / "Saved").resolve()) and p.name in ["MProfile_MCP_MixSmoke.ini", "MProfile_MCP_MixSmoke1.ini"]
        return p

    def cleanup(files):
        for asset in reversed(PATHS):
            call("POST", "/assets/delete", {"AssetPath":asset})
        for p in files:
            validated = file_path({"profile_path":str(p)})
            validated.unlink(missing_ok=True)
        MANIFEST.unlink(missing_ok=True)

    assert not call("GET", "/editor/status")["is_playing"], "Test requires an idle editor"
    if phase == "verify":
        files = [Path(p) for p in json.loads(MANIFEST.read_text())["profiles"]]
        started = False
        try:
            assert not settings()["dirty"] and settings()["stages"][0]["target_normalized"] == .2
            assert profile(0)["stages"][0]["target_normalized"] == .7
            assert profile(1)["stages"][0]["target_normalized"] == .2
            start()
            started = True
            runtime("activate_mix")
            for _ in range(100):
                if call("GET", "/audio/modulation/runtime", asset_path=MIX)["mix_active"]:
                    break
                time.sleep(.1)
            runtime("update_mix", Stages=[{"BusPath":BUS,"TargetNormalized":.4}], FadeSeconds=0)
            for _ in range(100):
                if abs(call("GET", "/audio/modulation/runtime", asset_path=BUS)["value_normalized"]-.4)<.001:
                    break
                time.sleep(.1)
            assert not control("load", 1, bSave=True)["changed_asset"] and not settings()["dirty"]
            for _ in range(100):
                value = call("GET", "/audio/modulation/runtime", asset_path=BUS)["value_normalized"]
                if abs(value-.2)<.001:
                    break
                time.sleep(.1)
            else:
                raise AssertionError(value)
            before = settings()
            assert control("load", 0, bDryRun=True)["would_change_asset"] and settings() == before
            reject(0)
            reject(0, bConfirm=True, bSave=True)
            assert settings() == before
            stop()
            started = False
            assert control("load", 0, bConfirm=True, bSave=True)["saved_asset"]
            assert settings()["stages"][0]["target_normalized"] == .7
            print("Native profile files and asset stages survived restart; no-op load and confirmed replacement: OK")
        finally:
            if started:
                stop()
            cleanup(files)
        return

    created = []
    files = []
    started = False
    try:
        for asset, kind in [(BUS,"bus"),(MIX,"mix")]:
            r = call("POST", "/audio/modulation/create", {"AssetPath":asset.split(".")[0], "AssetType":kind, "bSave":True})
            assert r["asset_path"] == asset, "Fixture exists; clean it before testing"
            created.append(asset)
        call("POST", "/audio/modulation/stages", {"AssetPath":MIX, "BusPath":BUS, "TargetNormalized":.7, "AttackSeconds":.2, "ReleaseSeconds":.4, "bSave":True})
        for index in [0,1]:
            info = profile(index)
            assert not info["exists"], "Profile fixture exists; clean it before testing"
            files.append(file_path(info))
        start()
        started = True
        assert control("save", 0, bDryRun=True)["dry_run"] and not profile(0)["exists"]
        reject(-1, "save")
        reject(1000, "save")
        reject(4)
        control("save", 0)
        info = wait_profile(0, .7)
        assert abs(info["stages"][0]["attack_seconds"]-.2)<.001 and abs(info["stages"][0]["release_seconds"]-.4)<.001
        reject(0, "save")
        original = files[0].read_bytes()
        assert control("save", 0, bDryRun=True)["dry_run"] and files[0].read_bytes() == original
        control("save", 0, bConfirm=True)
        wait_profile(0, .7)
        before = settings()
        runtime("activate_mix")
        for _ in range(100):
            s = call("GET", "/audio/modulation/runtime", asset_path=MIX)
            if s["mix_active"]:
                break
            time.sleep(.1)
        runtime("update_mix", Stages=[{"BusPath":BUS, "TargetNormalized":.2}], FadeSeconds=0)
        for _ in range(100):
            s = call("GET", "/audio/modulation/runtime", asset_path=BUS)
            if abs(s["value_normalized"]-.2)<.001:
                break
            time.sleep(.1)
        else:
            raise AssertionError(s)
        control("save", 1)
        wait_profile(1, .2)
        assert settings() == before
        runtime("deactivate_mix")
        stop()
        started = False
        call("POST", "/audio/modulation/stages", {"AssetPath":MIX, "Operation":"clear", "bConfirm":True, "bSave":True})
        assert settings()["stages"] == []
        assert control("load", 1, bDryRun=True)["would_change_asset"] and settings()["stages"] == []
        reject(1)
        # Malformed files and invalid reference sections must be rejected before asset changes.
        good = files[1].read_bytes()
        files[1].write_text(f"[{BUS}]\nAttackTime=-1\nReleaseTime=0\nTargetValue=2\n")
        reject(1, bConfirm=True)
        assert settings()["stages"] == []
        files[1].write_bytes(good)
        assert control("load", 1, bConfirm=True, bSave=True)["changed_asset"]
        assert settings()["stages"][0]["target_normalized"] == .2 and not settings()["dirty"]
        MANIFEST.write_text(json.dumps({"profiles":[str(p) for p in files]}))
        print("Native inactive/active profile saves, overwrite guards, disk preflight, added stage loading and save: OK")
    except BaseException:
        if started:
            stop()
        for asset in reversed(created):
            call("POST", "/assets/delete", {"AssetPath":asset})
        for p in files:
            p.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", required=True, choices=["create","verify"])
    args = parser.parse_args()
    run(args.base, args.phase)
