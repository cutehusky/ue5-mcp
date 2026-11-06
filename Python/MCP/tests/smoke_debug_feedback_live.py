"""Compile messages, Blueprint breakpoints during PIE, C++ class creation and Live Coding status, against a live editor.

The pause flow needs a windowed editor; a headless one must refuse breakpoints. Pass --create-class to write a real class.
"""
import json
import os
import sys
import time

import httpx

CREATE_CLASS = '--create-class' in sys.argv  # Also edits the .uproject and regenerates the .sln; restore them after.
sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
ROOT = '/Game/UE5MCP_Test/Debug'
GOOD, BROKEN = f'{ROOT}/BP_MCP_Debug', f'{ROOT}/BP_MCP_Broken'
KSL = '/Script/Engine.KismetSystemLibrary'


def J(text):
    return json.loads(text)


def nodes(bp):
    return J(m.get_graph(bp, 'EventGraph'))


def added(bp, fn, *args):
    before = {n['Id'] for n in nodes(bp)}
    fn(bp, 'EventGraph', *args)
    return next(n['Id'] for n in nodes(bp) if n['Id'] not in before)


def make(bp, function, owner):
    m.create_blueprint(bp, '/Script/Engine.Actor')
    tick = next((n['Id'] for n in nodes(bp) if 'Tick' in json.dumps(n)), None) or added(bp, m.add_event_to_graph, 'ReceiveTick')
    call = added(bp, m.add_function_call_to_graph, function, owner)
    m.connect_pins(bp, 'EventGraph', tick, 'then', call, 'execute')
    return call


def state():
    return J(m.inspect_blueprint_debug_state())


def wait_paused(seconds=60):
    end = time.time() + seconds
    while time.time() < end:
        s = state()
        if s['paused']:
            return s
        time.sleep(0.25)
    raise AssertionError('breakpoint never paused')


def wait_running(seconds=30):
    end = time.time() + seconds
    while time.time() < end and state()['paused']:
        time.sleep(0.1)
    assert not state()['paused'], 'still paused'


def compile_feedback():
    make(BROKEN, 'SetVisibility', '/Script/Engine.SceneComponent')
    r = J(m.compile_blueprint(BROKEN))
    assert r['success'] is False and r['compiled'] is False and r['errors'] > 0, r
    e = next(x for x in r['messages'] if x['severity'] == 'error')
    assert e['message'] and e.get('node_id'), r
    print('compile error reported:', e['message'][:120], e['node_id'])


def breakpoints():
    call = make(GOOD, 'PrintString', KSL)
    r = J(m.compile_blueprint(GOOD))
    assert r['success'] is True and r['errors'] == 0, r
    assert not state()['paused']
    assert 'errorMessage' in m.control_blueprint_debugger('resume')
    assert 'errorMessage' in m.edit_blueprint_breakpoint(GOOD, 'add', 'nope')
    assert 'errorMessage' in m.edit_blueprint_breakpoint(GOOD, 'add', call, 5)
    refused = m.edit_blueprint_breakpoint(GOOD, 'add', call)
    if 'headless' in refused:
        print('headless editor refused breakpoints, so the pause flow needs a windowed editor')
        return None
    assert J(refused)['breakpoints'][0]['node_id'] == call
    actor = m.spawn_editor_actor(asset_path=GOOD).strip().strip('"')
    m.control_ue_play_session('start')
    try:
        s = wait_paused()
        assert s['current']['node_id'] == call and s['call_stack'] and 'locals' in s and 'variables' in s, s
        print('paused at', s['current']['node_title'], [f['function'] for f in s['call_stack']])
        # Other routes are refused while paused, and logs still work.
        blocked = httpx.get(BASE + '/play-session', timeout=10)
        assert blocked.status_code == 409 and 'breakpoint' in blocked.text, blocked.text
        assert httpx.get(BASE + '/editor/logs', params={'limit': 1}, timeout=10).status_code == 200
        assert 'errorMessage' in m.control_blueprint_debugger('jump')
        assert J(m.control_blueprint_debugger('resume'))['success']
        s = wait_paused()  # Tick hits it again next frame.
        assert J(m.control_blueprint_debugger('step_over'))['success']
        s = wait_paused()
        print('stepped to', s['current']['node_title'])
        # Disable it, so the next resume keeps running.
        assert J(m.edit_blueprint_breakpoint(GOOD, 'disable', call))['breakpoints'][0]['enabled'] is False
        assert J(m.control_blueprint_debugger('resume'))['success']
        wait_running()
        time.sleep(1)
        assert not state()['paused']
        # A client that disappears can't leave the editor stuck.
        m.edit_blueprint_breakpoint(GOOD, 'add', call, 10)
        wait_paused()
        started = time.time()
        wait_running(40)
        waited = time.time() - started
        assert state()['auto_resumed'] and 5 < waited < 30, waited
        assert J(m.list_blueprint_breakpoints(GOOD))['breakpoints'][0]['enabled'] is False
        print(f'auto-resumed after {waited:.0f}s and disabled the breakpoint')
    finally:
        if state()['paused']:
            m.control_blueprint_debugger('resume')
        m.edit_blueprint_breakpoint(GOOD, 'clear_all')
        if state()['paused']:
            m.control_blueprint_debugger('resume')
        m.control_ue_play_session('stop')
    assert J(m.list_blueprint_breakpoints(GOOD))['breakpoints'] == []
    return actor


def cpp():
    print('live coding', m.get_live_coding_status())
    assert J(m.get_editor_build_status())['cxx_compile_status'] in ('unavailable', 'disabled', 'idle', 'compiling')
    name = 'MCPSmokeActor'
    assert 'errorMessage' in m.create_cpp_class('Bad Name', dry_run=True)
    assert 'errorMessage' in m.create_cpp_class(name, '/Script/Engine.NoSuchClass', dry_run=True)
    assert 'errorMessage' in m.create_cpp_class(name)  # needs confirm
    r = J(m.create_cpp_class(name, dry_run=True))
    assert r['dry_run'] and r['module'] == 'DemoForPlugin', r
    if not CREATE_CLASS:
        return
    r = J(m.create_cpp_class(name, confirm=True))
    try:
        assert r['success'] and os.path.isfile(r['header']) and os.path.isfile(r['source']), r
        assert f'class ' in open(r['header'], encoding='utf-8').read() and name in open(r['header'], encoding='utf-8').read()
        print('created', r['header'], 'loaded', r['class_loaded'], r['note'])
    finally:
        for key in ('header', 'source'):
            if r.get(key) and os.path.isfile(r[key]):
                os.remove(r[key])


def clean():
    for bp in (GOOD, BROKEN):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': bp}, timeout=180)


clean()
try:
    compile_feedback()
    actor = breakpoints()
    if actor:
        httpx.post(BASE + '/editor/actors/delete', json={'ActorPaths': [actor]}, timeout=30)
    cpp()
finally:
    clean()
print('Debug feedback verified')
