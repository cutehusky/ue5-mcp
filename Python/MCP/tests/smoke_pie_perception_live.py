"""AI Perception: placed editor configuration, persistent stimuli sources and PIE runtime controls; prepare, restart, verify.

Builds BP_MCP_AIController (AIController + AIPerceptionComponent) and BP_MCP_Target (Actor + AIPerceptionStimuliSource)
in a copy of the ThirdPerson map, then:
prepare: discover sense/config classes; configure the placed perception component (sight + hearing + damage, dominant
sense) and the placed stimuli source with dry runs and refusals; save the map; start PIE (/editor/pie/start) and drive the
runtime routes (inspection, configure, sense enable/disable, dominant, refresh, noise, damage, source register/unregister,
forget); stop PIE.
verify (fresh editor): the placed configuration and stimuli-source settings reload; cleanup deletes the map and Blueprints.
"""
import json
import sys
import time

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
MAP = '/Game/UE5MCP_Test/MCP_PIE_Perception'
AIC = '/Game/UE5MCP_Test/BP_MCP_AIController'
TGT = '/Game/UE5MCP_Test/BP_MCP_Target'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'pie_perception.json'
AI = '/Script/AIModule.'
Y = dict(confirm=True)
SPAWNED = {}


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:500])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:400])
    return r['errorMessage']


def load(path):
    r = httpx.post(BASE + '/worlds/load', json={'WorldPath': path, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()
    assert r.get('success'), r


def pie(start):
    httpx.post(BASE + ('/editor/pie/start' if start else '/editor/pie/stop'), headers={'Content-Length': '0'}, timeout=60)
    for _ in range(60):
        if ok(m.get_ue_editor_status)['is_playing'] == start:
            time.sleep(1)
            return
        time.sleep(1)
    raise AssertionError('PIE did not ' + ('start' if start else 'stop'))


def editor_component():
    comps = ok(m.inspect_ai_perception_components, '', 'BP_MCP_AIController')['components']
    assert len(comps) == 1, comps
    return comps[0]


def source_row():
    rows = [r for r in ok(m.inspect_ai_perception_sources, 'BP_MCP_Target')['sources']]
    assert len(rows) == 1, rows
    return rows[0]


def setup():
    ok(m.create_editor_world, MAP, '/Game/ThirdPerson/Lvl_ThirdPerson', True, 'discard', True)
    load(MAP)
    for bp, parent, comp, name in ((AIC, 'AIController', 'AIPerceptionComponent', 'Perception'),
                                   (TGT, 'Actor', 'AIPerceptionStimuliSourceComponent', 'Stimuli')):
        m.create_blueprint(bp, parent)
        m.add_component_to_bp(bp, comp, name, '')
        m.compile_blueprint(bp)
        assert httpx.post(BASE + '/assets/save', json={'AssetPath': bp}, timeout=120).status_code == 200   # keep the component after a restart
        short = bp.rsplit('/', 1)[1]
        SPAWNED[bp] = m.spawn_editor_actor(actor_class=f'{bp}.{short}_C', location={'X': 300, 'Y': 0, 'Z': 100} if bp == TGT else {'X': 0, 'Y': 0, 'Z': 100}).strip().strip('"')
        assert 'PersistentLevel' in SPAWNED[bp], SPAWNED[bp]


def editor_stage():
    classes = ok(m.list_ai_perception_classes)
    text = json.dumps(classes)
    for c in ('AISenseConfig_Sight', 'AISenseConfig_Hearing', 'AISenseConfig_Damage', 'AISense_Sight'):
        assert c in text, (c, text[:600])
    comp = editor_component()['component_path']
    bad(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISenseConfig_Sight', properties={'SightRadius': '3000'})   # unconfirmed new sense
    bad(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISenseConfig_Sight', properties={'SightRadius': 'abc'}, **Y)
    bad(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISense_Sight', **Y)                                         # not a config
    before = editor_component()
    ok(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISenseConfig_Sight',
       properties={'SightRadius': '3000', 'LoseSightRadius': '3500', 'PeripheralVisionAngleDegrees': '70'}, confirm=True, dry_run=True)
    assert editor_component() == before
    ok(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISenseConfig_Sight',
       properties={'SightRadius': '3000', 'LoseSightRadius': '3500', 'PeripheralVisionAngleDegrees': '70'}, **Y)
    ok(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISenseConfig_Hearing', properties={'HearingRange': '2500'}, **Y)
    ok(m.configure_ai_perception_component, comp, config_class_path=AI + 'AISenseConfig_Damage', **Y)
    bad(m.configure_ai_perception_component, comp, 'dominant', sense_class_path=AI + 'AISense_Team', **Y)                              # not configured
    ok(m.configure_ai_perception_component, comp, 'dominant', sense_class_path=AI + 'AISense_Sight', **Y)
    c = editor_component()
    print('editor component:', json.dumps(c)[:900])
    assert 'AISense_Sight' in c['dominant_sense'] and '3000' in json.dumps(c) and '2500' in json.dumps(c), c
    # Persistent stimuli source settings on the placed target.
    src = source_row()['component_path']
    bad(m.configure_ai_perception_source, src, [AI + 'AISenseConfig_Sight'], **Y)                                                     # config, not sense
    ok(m.configure_ai_perception_source, src, [AI + 'AISense_Sight', AI + 'AISense_Hearing'], confirm=True, dry_run=True)
    ok(m.configure_ai_perception_source, src, [AI + 'AISense_Sight', AI + 'AISense_Hearing'], **Y)
    row = source_row()
    print('source row:', json.dumps(row)[:600])
    assert 'AISense_Hearing' in json.dumps(row) and row.get('auto_register', row.get('auto_register_as_source')) in (True, None), row
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']


def runtime_stage():
    pie(True)
    try:
        comps = ok(m.inspect_ai_perception_runtime)['components']
        assert len(comps) == 1, comps
        rc = comps[0]
        cp, owner = rc['component_path'], rc['owner_path']
        print('runtime component:', json.dumps(rc)[:900])
        assert 'AISense_Sight' in rc['dominant_sense'] and len(rc['senses']) == 3, rc
        world = owner.split(':')[0]                                     # PIE copy: /Game/.../UEDPIE_0_<map>.<map>
        target = world + ':' + SPAWNED[TGT].split(':', 1)[1]
        print('target:', target)
        # Runtime configure (existing class copied) and new class needs confirm.
        ok(m.configure_ai_perception_runtime, cp, AI + 'AISenseConfig_Hearing', {'HearingRange': '4000'}, confirm=True, dry_run=True)
        # Neutral detection: the target has no team, so the default enemies-only affiliation filter would drop its noise.
        ok(m.configure_ai_perception_runtime, cp, AI + 'AISenseConfig_Hearing',
           {'HearingRange': '4000', 'DetectionByAffiliation': '(bDetectEnemies=True,bDetectNeutrals=True,bDetectFriendlies=True)'}, **Y)
        assert '4000' in json.dumps(ok(m.inspect_ai_perception_runtime, cp))
        bad(m.configure_ai_perception_runtime, cp, AI + 'AISenseConfig_Team')
        # Sense enable/disable, dominant, refresh.
        ok(m.control_ai_perception_runtime, cp, 'sense', AI + 'AISense_Damage', enabled=False)
        sense = lambda: {s['sense_class'].split('.')[-1]: s for s in ok(m.inspect_ai_perception_runtime, cp)['components'][0]['senses']}
        assert sense()['AISense_Damage']['enabled'] is False and sense()['AISense_Sight']['enabled'], sense()
        ok(m.control_ai_perception_runtime, cp, 'sense', AI + 'AISense_Damage', enabled=True)
        assert sense()['AISense_Damage']['enabled']
        ok(m.control_ai_perception_runtime, cp, 'dominant', AI + 'AISense_Hearing')
        assert 'AISense_Hearing' in ok(m.inspect_ai_perception_runtime, cp)['components'][0]['dominant_sense']
        bad(m.control_ai_perception_runtime, cp, 'dominant', AI + 'AISense_Team')
        ok(m.control_ai_perception_runtime, cp, 'refresh')
        # Hearing: a noise at the listener is perceived after a tick.
        bad(m.report_ai_perception_noise, target, loudness=-1)
        ok(m.report_ai_perception_noise, target, 1.0, 0.0, 'MCPNoise', dry_run=True)
        ok(m.report_ai_perception_noise, target, 1.0, 0.0, 'MCPNoise')
        ok(m.report_ai_perception_damage, target, owner, 5.0, 'MCPHit')
        known = []
        for _ in range(20):
            time.sleep(0.5)
            known = ok(m.inspect_ai_perception_runtime, cp)['components'][0]['actors']
            if known:
                break
        print('known actors:', json.dumps(known)[:900])
        assert any('BP_MCP_Target' in json.dumps(a) for a in known), known
        # Stimulus sources: register/unregister (unregister needs confirm).
        ok(m.control_ai_perception_source, target, AI + 'AISense_Sight', 'register')
        bad(m.control_ai_perception_source, target, AI + 'AISense_Sight', 'unregister')
        ok(m.control_ai_perception_source, target, AI + 'AISense_Sight', 'unregister', **Y)
        # Forget: confirm required.
        bad(m.control_ai_perception_runtime, cp, 'forget_all')
        ok(m.control_ai_perception_runtime, cp, 'forget_all', **Y)
        assert ok(m.inspect_ai_perception_runtime, cp)['components'][0]['known_actor_count'] == 0
        return {'known_before_forget': len(known)}
    finally:
        pie(False)


def snapshot():
    c, s = editor_component(), source_row()
    for d in (c, s):
        d.pop('dirty', None)
    return {'component': c, 'source': s}


def prepare():
    cleanup()
    setup()
    editor_stage()
    result = runtime_stage()
    load(MAP)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot(), 'runtime': result}, indent=1), encoding='utf-8')
    print('AI Perception editor configuration and PIE runtime prepared:', result)


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    load(MAP)
    got = json.loads(json.dumps(snapshot()))
    assert got == st['snapshot'], json.dumps({'got': got, 'want': st['snapshot']})[:3000]
    print('AI Perception placed configuration and stimuli source identical after cold reload')
    cleanup()


def cleanup():
    if ok(m.get_ue_editor_status)['is_playing']:
        pie(False)
    load('/Game/ThirdPerson/Lvl_ThirdPerson')
    for p in (MAP, AIC, TGT):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
