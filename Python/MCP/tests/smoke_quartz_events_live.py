"""Native Quartz quantized commands, callbacks, metronome subscriptions and lifecycle."""
import argparse
import time
import httpx


def run(base):
    started = False
    owned = []

    def call(method, route, body=None, **params):
        r = httpx.request(method,base+route,json=body,params=params,timeout=120)
        r.raise_for_status()
        return r.json()

    def clock(name, operation, **extra):
        return call("POST","/audio/quartz/control",{"ClockName":name,"Operation":operation}|extra)

    def state(name):
        return call("GET","/audio/quartz/clock",clock_name=name)

    def event(id, op, name="", **extra):
        return call("POST","/audio/quartz/events",{"EventId":id,"Operation":op,"ClockName":name}|extra)

    def records(id, **extra):
        return call("GET","/audio/quartz/events",event_id=id,**extra)

    def reject(id, op, name="", **extra):
        r = httpx.post(base+"/audio/quartz/events",json={"EventId":id,"Operation":op,"ClockName":name}|extra,timeout=120)
        assert r.status_code >= 400, r.text

    def until(fetch, predicate):
        deadline = time.monotonic()+20
        while time.monotonic()<deadline:
            s = fetch()
            if predicate(s):
                return s
            time.sleep(.1)
        raise AssertionError(s)

    def terminal(id, expected="CommandOnStarted"):
        s = until(lambda:records(id),lambda s:s["terminal"])
        assert any(e["value"]==expected for e in s["events"]), s
        return s

    def start():
        call("POST","/editor/play",{"Operation":"start"})
        for _ in range(100):
            r = httpx.get(base+"/audio/quartz/clock",params={"clock_name":"MCP_QEventProbe"},timeout=120)
            if r.status_code == 200:
                return
            time.sleep(.1)
        raise AssertionError(r.text)

    def stop():
        call("POST","/editor/play",{"Operation":"stop"})
        until(lambda:call("GET","/editor/status"),lambda s:not s["is_playing"])

    assert not call("GET","/editor/status")["is_playing"], "Test requires an idle editor"
    try:
        start()
        started = True
        for mixer in [False,True]:
            name, other = "MCP_QEventSmoke_"+str(int(mixer)), "MCP_QEventOther_"+str(int(mixer))
            clock(name,"create",bUseAudioEngineClockManager=mixer)
            clock(other,"create",bUseAudioEngineClockManager=mixer)
            owned += [name,other]
            until(lambda:state(name),lambda s:abs(s["beats_per_minute"]-120)<.01)
            clock(name,"start")
            until(lambda:state(name),lambda s:s["running"])
            prefix = str(int(mixer))+"_"
            beat, tempo, notify, reset, cancel, sync = [prefix+x for x in ["beat","tempo","notify","reset","cancel","sync"]]
            reject("bad id","subscribe",name)
            reject("invalid","notify",name,Quantization="None")
            reject("invalid","notify",name,ReferencePoint="invalid")
            reject("invalid","notify",name,Multiplier=0)
            assert not event(beat,"subscribe",name,Quantization="Beat",bDryRun=True)["submitted"]
            absent = httpx.get(base+"/audio/quartz/events",params={"event_id":beat},timeout=120)
            assert absent.status_code >= 400
            event(beat,"subscribe",name,Quantization="Beat")
            reject(beat,"subscribe",name)
            b = until(lambda:records(beat),lambda s:len(s["events"])>=3)
            assert all(e["kind"]=="native_metronome" and e["value"]=="Beat" and e["beat"]>=1 for e in b["events"])
            page = records(beat,limit=1)
            assert len(page["events"])==1 and page["next_sequence"]==page["events"][0]["sequence"]
            next_page = records(beat,after_sequence=page["next_sequence"],limit=1)
            assert next_page["events"][0]["sequence"]>page["next_sequence"]
            event(tempo,"tempo",name,Quantization="QuarterNote",Multiplier=4,ReferencePoint="CurrentTimeRelative",BeatsPerMinute=60,bDryRun=True)
            assert abs(state(name)["beats_per_minute"]-120)<.01
            event(tempo,"tempo",name,Quantization="QuarterNote",Multiplier=4,ReferencePoint="CurrentTimeRelative",BeatsPerMinute=60)
            assert abs(state(name)["beats_per_minute"]-120)<.01
            t = terminal(tempo)
            queued = next(e for e in t["events"] if e["value"]=="CommandOnQueued")
            executed = next(e for e in t["events"] if e["value"]=="CommandOnStarted")
            assert executed["received_seconds"]-queued["received_seconds"]>1, t
            until(lambda:state(name),lambda s:abs(s["beats_per_minute"]-60)<.01)
            event(notify,"notify",name,Quantization="Beat",Multiplier=2,ReferencePoint="CurrentTimeRelative")
            terminal(notify)
            event(reset,"reset",name,Quantization="QuarterNote",Multiplier=2,ReferencePoint="CurrentTimeRelative")
            terminal(reset)
            assert state(name)["estimated_runtime_seconds"]<1
            event(cancel,"notify",name,Quantization="QuarterNote",Multiplier=20,ReferencePoint="CurrentTimeRelative")
            until(lambda:records(cancel),lambda s:any(e["value"]=="CommandOnQueued" for e in s["events"]))
            reject(cancel,"release")
            assert not event(cancel,"cancel",bDryRun=True)["submitted"] and not records(cancel)["terminal"]
            event(cancel,"cancel")
            terminal(cancel,"CommandOnCanceled")
            event(sync,"start_other",name,OtherClockName=other,Quantization="QuarterNote",Multiplier=2,ReferencePoint="CurrentTimeRelative")
            assert not state(other)["running"]
            terminal(sync)
            until(lambda:state(other),lambda s:s["running"])
            event(beat,"unsubscribe",bDryRun=True)
            assert not records(beat)["closed"]
            event(beat,"unsubscribe")
            last = records(beat)["latest_sequence"]
            time.sleep(.6)
            assert records(beat)["closed"] and records(beat)["latest_sequence"]==last
            if not mixer:
                tick = prefix+"tick"
                clock(name,"tempo",BeatsPerMinute=1000)
                until(lambda:state(name),lambda s:abs(s["beats_per_minute"]-1000)<.01)
                event(tick,"subscribe",name,Quantization="Tick")
                overflow = until(lambda:records(tick,limit=256),lambda s:s["dropped_events"]>0)
                assert overflow["oldest_sequence"]>1 and len(overflow["events"])==256
                event(tick,"release")
            for id in [beat,tempo,notify,reset,cancel,sync]:
                event(id,"release")
            clock(name,"delete",bConfirm=True)
            clock(other,"delete",bConfirm=True)
            owned.remove(name)
            owned.remove(other)
        # Subscriptions are owned by their PIE world, not retained after teardown.
        name = "MCP_QEventCleanup"
        clock(name,"create",bUseAudioEngineClockManager=False)
        owned.append(name)
        until(lambda:state(name),lambda s:abs(s["beats_per_minute"]-120)<.01)
        event("paused_cancel","notify",name,bCancelIfNotRunning=True)
        terminal("paused_cancel","CommandOnCanceled")
        event("paused_cancel","release")
        event("resume_notify","notify",name,Quantization="QuarterNote",Multiplier=3,ReferencePoint="CurrentTimeRelative",bFireOnClockStart=False,bResumeOnQueued=True)
        until(lambda:state(name),lambda s:s["running"])
        terminal("resume_notify")
        event("resume_notify","release")
        incompatible = "MCP_QEventCrossManager"
        clock(incompatible,"create",bUseAudioEngineClockManager=True)
        owned.append(incompatible)
        event("cross_manager","start_other",name,OtherClockName=incompatible)
        rejected = until(lambda:records("cross_manager"),lambda s:s["terminal"])
        assert rejected["events"][0]["kind"]=="adapter_rejected" and not state(incompatible)["running"]
        event("cross_manager","release")
        clock(incompatible,"delete",bConfirm=True)
        owned.remove(incompatible)
        event("cleanup","subscribe",name,Quantization="Beat")
        event("pending_cleanup","notify",name,Quantization="QuarterNote",Multiplier=64,ReferencePoint="CurrentTimeRelative")
        stop()
        started = False
        owned.clear()
        start()
        started = True
        absent = httpx.get(base+"/audio/quartz/events",params={"event_id":"cleanup"},timeout=120)
        assert absent.status_code >= 400
        print("Native Quartz command callbacks, tempo/reset/notify/start_other, cancellation, subscriptions, cursor/overflow, dry-run and PIE cleanup: OK")
    finally:
        if started:
            for name in owned:
                if state(name)["exists"]:
                    clock(name,"delete",bConfirm=True)
            stop()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base",default="http://127.0.0.1:8080")
    run(p.parse_args().base)
