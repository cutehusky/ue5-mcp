"""Native PIE modulation mix/global/destination state; asset settings remain unchanged."""
import argparse
import math
import time
import httpx


def path(name):
    return f"/Game/UE5MCP_Test/{name}.{name}"


PARAMETER, BUS, MIX, LFO, PATCH = [path("MRT_MCP_Smoke_" + k) for k in ["Parameter","Bus","Mix","LFO","Patch"]]
PATHS = [PARAMETER, BUS, MIX, LFO, PATCH]


def run(base):
    def call(method, route, body=None, **params):
        r = httpx.request(method, base + route, json=body, params=params, timeout=180)
        r.raise_for_status()
        return r.json()

    def control(op, asset="", **extra):
        return call("POST", "/audio/modulation/runtime", {"Operation": op, "AssetPath": asset} | extra)

    def reject(**body):
        r = httpx.post(base + "/audio/modulation/runtime", json=body, timeout=180)
        assert r.status_code >= 400, r.text

    def inspect(asset=""):
        return call("GET", "/audio/modulation/runtime", asset_path=asset)

    def settings(asset):
        return call("GET", "/audio/modulation/settings", asset_path=asset)

    def until(predicate, asset=""):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            state = inspect(asset)
            if predicate(state):
                return state
            time.sleep(.1)
        raise AssertionError(state)

    def destination(state, key):
        return next(d for d in state["destinations"] if d["destination_id"] == key)

    created = []
    started = False
    before = {}
    assert not call("GET", "/editor/status")["is_playing"], "Test requires an idle editor to own its PIE session"
    reject(Operation="activate_mix", AssetPath=MIX)
    try:
        for asset, kind, extra in [(PARAMETER,"parameter",{}), (BUS,"bus",{"ParameterPath":PARAMETER}), (MIX,"mix",{}), (LFO,"generator",{}), (PATCH,"patch",{"ParameterPath":PARAMETER})]:
            r = call("POST", "/audio/modulation/create", {"AssetPath":asset.split(".")[0], "AssetType":kind, "bSave":True} | extra)
            assert r["asset_path"] == asset, "Fixture exists; clean it before testing"
            created.append(asset)
        call("POST", "/audio/modulation/stages", {"AssetPath":MIX, "BusPath":BUS, "TargetNormalized":.8, "AttackSeconds":0, "ReleaseSeconds":0, "bSave":True})
        call("PATCH", "/audio/modulation/generators/settings", {"AssetPath":LFO, "Numeric":{"Frequency":.5}, "bSave":True})
        call("POST", "/audio/modulation/inputs", {"AssetPath":PATCH, "BusPath":BUS, "bSave":True})
        call("PATCH", "/audio/modulation/settings", {"AssetPath":PATCH, "bSetBypass":True, "bBypass":False, "bSave":True})
        before = {asset:settings(asset) for asset in PATHS}
        call("POST", "/editor/play", {"Operation":"start"})
        started = True
        for _ in range(100):
            r = httpx.get(base + "/audio/modulation/runtime", timeout=180)
            if r.status_code == 200:
                break
            time.sleep(.1)
        else:
            raise AssertionError(r.text)
        assert inspect()["modulation_available"]
        reject(Operation="unknown")
        reject(Operation="activate_mix", AssetPath=BUS)
        reject(Operation="create_destination", AssetPath=BUS, DestinationId="bad id")
        reject(Operation="update_mix", AssetPath=MIX, Stages=[{"BusPath":BUS, "TargetNormalized":.2}])
        assert not control("create_destination", BUS, DestinationId="bus", bDryRun=True)["command_submitted"]
        assert inspect()["destinations"] == []
        control("create_destination", BUS, DestinationId="bus")
        reject(Operation="create_destination", AssetPath=BUS, DestinationId="bus")
        control("create_destination", PATCH, DestinationId="patch")
        control("activate_mix", MIX, bDryRun=True)
        assert not inspect(MIX)["mix_active"]
        control("activate_mix", MIX)
        until(lambda s:s["mix_active"], MIX)
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-.8)<.005)
        until(lambda s:abs(destination(s,"patch")["value_normalized"]-.8)<.005)
        reject(Operation="update_mix", AssetPath=MIX, Stages=[{"BusPath":BUS,"TargetNormalized":2}])
        reject(Operation="update_mix", AssetPath=MIX, Stages=[{"BusPath":BUS},{"BusPath":BUS}])
        control("update_mix", MIX, Stages=[{"BusPath":BUS,"TargetNormalized":.2}], FadeSeconds=0, bDryRun=True)
        assert abs(destination(inspect(),"bus")["value_normalized"]-.8)<.005
        control("update_mix", MIX, Stages=[{"BusPath":BUS,"TargetNormalized":.2}], FadeSeconds=0)
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-.2)<.005)
        assert settings(MIX) == before[MIX]
        control("update_mix_from_asset", MIX, FadeSeconds=0)
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-.8)<.005)
        control("set_global", BUS, TargetNormalized=.5, FadeSeconds=0)
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-.4)<.005)
        control("clear_global", BUS, FadeSeconds=0)
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-.8)<.005)
        control("update_modulator", BUS)
        control("deactivate_mix", MIX)
        until(lambda s:not s["mix_active"], MIX)
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-1)<.005)
        control("set_destination", LFO, DestinationId="bus")
        observed = [destination(inspect(),"bus")["value_normalized"] for _ in range(8)]
        assert all(math.isfinite(v) for v in observed) and max(observed)-min(observed)>.1, observed
        control("clear_destination", DestinationId="bus", bDryRun=True)
        assert destination(inspect(),"bus")["modulator_path"] == LFO
        control("clear_destination", DestinationId="bus")
        assert destination(inspect(),"bus")["modulator_path"] == ""
        control("release_destination", DestinationId="bus")
        reject(Operation="release_destination", DestinationId="bus")
        # Leave one watcher and global value for teardown cleanup; next PIE must start empty.
        control("set_global", BUS, TargetNormalized=.3, FadeSeconds=0)
        assert all(settings(asset) == before[asset] for asset in PATHS)
        call("POST", "/editor/play", {"Operation":"stop"})
        started = False
        for _ in range(100):
            if not call("GET", "/editor/status")["is_playing"]:
                break
            time.sleep(.1)
        call("POST", "/editor/play", {"Operation":"start"})
        started = True
        for _ in range(100):
            r = httpx.get(base + "/audio/modulation/runtime", timeout=180)
            if r.status_code == 200:
                break
            time.sleep(.1)
        assert inspect()["destinations"] == [] and not inspect(MIX)["mix_active"]
        control("create_destination", BUS, DestinationId="bus")
        until(lambda s:abs(destination(s,"bus")["value_normalized"]-1)<.005)
        assert all(settings(asset) == before[asset] for asset in PATHS)
        print("Native PIE destinations, mix activation/runtime updates, global values, live generator/patch values, dry runs, asset preservation and teardown cleanup: OK")
    finally:
        if started:
            call("POST", "/editor/play", {"Operation":"stop"})
            for _ in range(100):
                if not call("GET", "/editor/status")["is_playing"]:
                    break
                time.sleep(.1)
        for asset in reversed(created):
            call("POST", "/assets/delete", {"AssetPath":asset})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    run(parser.parse_args().base)
