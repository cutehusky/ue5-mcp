"""Native PIE Quartz clock lifecycle and musical timing smoke test; no saved assets."""
import argparse
import time
import httpx


def run(base):
    name = "MCP_QuartzSmoke"

    def call(method, route, body=None, **params):
        r = httpx.request(method, base + route, json=body, params=params, timeout=120)
        r.raise_for_status()
        return r.json()

    def control(op, **extra):
        return call("POST", "/audio/quartz/control", {"ClockName": name, "Operation": op} | extra)

    def inspect():
        return call("GET", "/audio/quartz/clock", clock_name=name)

    def reject(**extra):
        r = httpx.post(base + "/audio/quartz/control", json={"ClockName": name} | extra, timeout=120)
        assert r.status_code >= 400, r.text

    def until(predicate):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            state = inspect()
            if predicate(state):
                return state
            time.sleep(0.1)
        raise AssertionError(state)

    status = call("GET", "/editor/status")
    assert not status["is_playing"], "Test requires an idle editor so it can own and clean up its PIE session"
    reject()
    started = False
    try:
        call("POST", "/editor/play", {"Operation": "start"})
        started = True
        for _ in range(100):
            r = httpx.get(base + "/audio/quartz/clock", params={"clock_name": name}, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(0.1)
        else:
            raise AssertionError(r.text)
        assert not inspect()["exists"]
        reject(BeatsPerBar=0)
        reject(BeatDenominator=3)
        reject(BeatsPerMinute=0)
        reject(ClockName="None")
        reject(Operation="unknown")
        assert control("create", bDryRun=True)["dry_run"]
        assert not inspect()["exists"]
        # Native subsystem manager remains available in headless/null-audio PIE.
        result = control("create", BeatsPerMinute=120, BeatsPerBar=3, BeatDenominator=8,
                         bUseAudioEngineClockManager=False)
        assert result["command_queued"] and result["runtime_only"]
        state = until(lambda s: s["exists"] and abs(s["beats_per_minute"] - 120) < .01)
        assert abs(state["duration_seconds"]["QuarterNote"] - .5) < .001
        assert abs(state["duration_seconds"]["EighthNote"] - .25) < .001
        assert "Bar" not in state["duration_seconds"] and "Beat" not in state["duration_seconds"]
        assert not state["running"]
        reject()
        assert control("start", bDryRun=True)["dry_run"]
        assert not inspect()["running"]
        control("start")
        state = until(lambda s: s["running"] and s["timestamp"]["seconds"] > 1.5)
        assert 1 <= state["timestamp"]["beat"] <= 3 and state["timestamp"]["bars"] >= 2
        control("pause")
        before = until(lambda s: not s["running"])["timestamp"]["seconds"]
        time.sleep(.3)
        assert abs(inspect()["timestamp"]["seconds"] - before) < .001
        control("tempo", BeatsPerMinute=60, bDryRun=True)
        assert abs(inspect()["beats_per_minute"] - 120) < .01
        control("tempo", BeatsPerMinute=60)
        state = until(lambda s: abs(s["beats_per_minute"] - 60) < .01)
        assert abs(state["duration_seconds"]["QuarterNote"] - 1) < .001
        control("reset")
        state = until(lambda s: s["estimated_runtime_seconds"] < .001)
        assert state["timestamp"]["bars"] == 0 and state["timestamp"]["beat"] == 0
        control("resume")
        until(lambda s: s["running"] and s["timestamp"]["seconds"] > .2)
        control("stop")
        until(lambda s: not s["running"] and s["estimated_runtime_seconds"] < .001)
        reject(Operation="delete")
        assert control("delete", bDryRun=True)["dry_run"] and inspect()["exists"]
        control("delete", bConfirm=True)
        until(lambda s: not s["exists"])
        reject(Operation="start")
        # Exercise the production default manager as well as the subsystem manager.
        control("create", BeatsPerMinute=90)
        until(lambda s: s["exists"] and abs(s["beats_per_minute"] - 90) < .01)
        control("start")
        until(lambda s: s["running"] and s["timestamp"]["seconds"] > .2)
        control("stop")
        until(lambda s: not s["running"] and s["estimated_runtime_seconds"] < .001)
        control("delete", bConfirm=True)
        until(lambda s: not s["exists"])
        print("Quartz native PIE lifecycle, dry runs, tempo, 3/8 durations, pause/reset/stop and deletion: OK")
    finally:
        if started:
            try:
                if inspect()["exists"]:
                    control("delete", bConfirm=True)
            finally:
                call("POST", "/editor/play", {"Operation": "stop"})
                for _ in range(100):
                    if not call("GET", "/editor/status")["is_playing"]:
                        break
                    time.sleep(.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    run(parser.parse_args().base)
