"""Native Quartz time signatures/pulse overrides, transport timing and meter changes."""
import argparse
import time
import httpx

GROUPS = [{"NumberOfPulses":2,"PulseDuration":"QuarterNote"},
          {"NumberOfPulses":1,"PulseDuration":"DottedQuarterNote"}]


def run(base):
    owned = []
    started = False

    def call(method, route, body=None, **params):
        r = httpx.request(method,base+route,json=body,params=params,timeout=120)
        r.raise_for_status()
        return r.json()

    def control(name, op, **extra):
        return call("POST","/audio/quartz/control",{"ClockName":name,"Operation":op}|extra)

    def inspect(name):
        return call("GET","/audio/quartz/clock",clock_name=name)

    def reject(name, **extra):
        r = httpx.post(base+"/audio/quartz/control",json={"ClockName":name}|extra,timeout=120)
        assert r.status_code >= 400, r.text

    def until(name, predicate):
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            s = inspect(name)
            if predicate(s):
                return s
            time.sleep(.1)
        raise AssertionError(s)

    def transport(name, durations, seconds=4):
        total = sum(durations)
        beats = set()
        deadline = time.monotonic()+seconds
        checks = 0
        while time.monotonic() < deadline:
            s = inspect(name)
            t = s["timestamp"]
            assert s["running"]
            phase = t["seconds"] % total
            boundaries = [0]
            for duration in durations:
                boundaries.append(boundaries[-1]+duration)
            if all(abs(phase-b)>.05 for b in boundaries):
                expected = next(i+1 for i in range(len(durations)) if phase < boundaries[i+1])
                assert t["beat"] == expected, (t,phase,expected,durations)
                assert t["bars"] == int(t["seconds"] / total)+1, (t,total)
                assert -.02 <= t["beat_fraction"] <= 1.02
                beats.add(expected)
                checks += 1
            time.sleep(.03)
        assert checks >= 4 and len(beats) >= 2, (checks,beats)

    assert not call("GET","/editor/status")["is_playing"], "Test requires an idle editor"
    try:
        call("POST","/editor/play",{"Operation":"start"})
        started = True
        for _ in range(100):
            r = httpx.get(base+"/audio/quartz/clock",params={"clock_name":"MCP_QuartzMeterProbe"},timeout=120)
            if r.status_code == 200:
                break
            time.sleep(.1)
        else:
            raise AssertionError(r.text)
        for mixer in [False,True]:
            name = "MCP_QuartzMeterSmoke_"+str(int(mixer))
            bad = [{"NumberOfPulses":0,"PulseDuration":"QuarterNote"},
                   {"NumberOfPulses":1,"PulseDuration":"None"},
                   {"NumberOfPulses":1,"PulseDuration":"Beat"},
                   {"NumberOfPulses":1,"PulseDuration":"Bar"},
                   {"NumberOfPulses":1,"PulseDuration":"Count"},
                   {"NumberOfPulses":129,"PulseDuration":"Tick"}]
            for group in bad:
                reject(name,BeatsPerBar=7,BeatDenominator=8,PulseOverrides=[group],bDryRun=True)
            reject(name,BeatsPerBar=7,BeatDenominator=8,PulseOverrides=[{"NumberOfPulses":1,"PulseDuration":"QuarterNote"}])
            reject(name,PulseOverrides=[{"NumberOfPulses":1,"PulseDuration":"QuarterNote"}]*33)
            result = control(name,"create",BeatsPerBar=7,BeatDenominator=8,PulseOverrides=GROUPS,bUseAudioEngineClockManager=mixer,bDryRun=True)
            assert result["requested_time_signature"]["beats_per_bar"] == 7 and not inspect(name)["exists"]
            result = control(name,"create",BeatsPerBar=7,BeatDenominator=8,PulseOverrides=GROUPS,bUseAudioEngineClockManager=mixer)
            owned.append(name)
            assert result["command_queued"] and result["requested_time_signature"]["pulse_overrides"][0]["number_of_pulses"] == 2
            until(name,lambda s:abs(s["beats_per_minute"]-120)<.01)
            control(name,"start")
            until(name,lambda s:s["running"])
            transport(name,[.5,.5,.75])
            until(name,lambda s:s["timestamp"]["beat"] == 3)
            control(name,"time_signature",BeatsPerBar=5,BeatDenominator=8,PulseOverrides=[{"NumberOfPulses":1,"PulseDuration":"QuarterNote"},{"NumberOfPulses":1,"PulseDuration":"DottedQuarterNote"}])
            until(name,lambda s:s["estimated_runtime_seconds"] < 1)
            transport(name,[.5,.75],seconds=3)
            control(name,"pause")
            before = until(name,lambda s:not s["running"])
            reject(name,Operation="time_signature",BeatsPerBar=0)
            reject(name,Operation="tempo",PulseOverrides=GROUPS)
            control(name,"time_signature",BeatsPerBar=5,BeatDenominator=4,bDryRun=True)
            assert abs(inspect(name)["estimated_runtime_seconds"]-before["estimated_runtime_seconds"])<.001
            result = control(name,"time_signature",BeatsPerBar=5,BeatDenominator=4)
            assert result["transport_reset_submitted"] and result["requested_time_signature"]["pulse_overrides"] == []
            s = until(name,lambda s:s["estimated_runtime_seconds"] < .001)
            assert not s["running"] and s["timestamp"]["bars"] == 0
            control(name,"resume")
            transport(name,[.5]*5)
            # Change pulse-array size while running: the adapter resets the native cursor safely.
            control(name,"time_signature",BeatsPerBar=3,BeatDenominator=4,PulseOverrides=[{"NumberOfPulses":3,"PulseDuration":"QuarterNote"}])
            until(name,lambda s:s["estimated_runtime_seconds"] < 1)
            transport(name,[.5]*3)
            control(name,"delete",bConfirm=True)
            until(name,lambda s:not s["exists"])
            owned.remove(name)
        print("Native Quartz 7/8 and 5/8 grouped pulses, live pulse-array shortening, 5/4 meter change, override clearing, dry-run and both managers: OK")
    finally:
        if started:
            for name in owned:
                control(name,"delete",bConfirm=True)
            call("POST","/editor/play",{"Operation":"stop"})
            for _ in range(100):
                if not call("GET","/editor/status")["is_playing"]:
                    break
                time.sleep(.1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base",default="http://127.0.0.1:8080")
    run(p.parse_args().base)
