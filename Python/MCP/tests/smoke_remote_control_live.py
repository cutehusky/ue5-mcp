"""Remote Control Presets: create, expose/unexpose, value set; prepare, restart, verify.

prepare: on a blank map with a placed PointLight, create a preset, expose the light's Intensity and an actor function
(dry runs, stale guards and refusals), set the value with undo/redo, unexpose a field, save map and preset.
verify (fresh editor): reload the map; entities, binding and value match. Cleanup deletes the preset and map.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
MAP = '/Game/UE5MCP_Test/MCP_RemoteControl'
RC = '/Game/UE5MCP_Test/RCP_MCP'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'remote_control.json'
Y = dict(confirm=True)


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


def preset():
    return ok(m.inspect_remote_control_preset, RC)


def row(label):
    return next(e for e in preset()['entities'] if e['label'] == label)


def undo(redo=False):
    assert httpx.post(BASE + '/editor/transactions/' + ('redo' if redo else 'undo'), json={}, timeout=120).is_success


def prepare():
    cleanup()
    ok(m.create_editor_world, MAP, '', True, 'discard', True)
    load(MAP)
    actor = m.spawn_editor_actor(actor_class='/Script/Engine.PointLight').strip().strip('"')
    assert 'PersistentLevel' in actor, actor
    comp = actor + '.LightComponent0'
    bad(m.create_remote_control_preset, RC)
    bad(m.create_remote_control_preset, '/Engine/RCP_Bad', **Y)
    ok(m.create_remote_control_preset, RC, confirm=True, dry_run=True)
    bad(m.inspect_remote_control_preset, RC)
    ok(m.create_remote_control_preset, RC, confirm=True, save=True)
    bad(m.create_remote_control_preset, RC, **Y)
    assert any('RCP_MCP' in p for p in ok(m.list_remote_control_presets, 'RCP_MCP')['presets'])
    assert preset()['entity_count'] == 0
    bad(m.expose_remote_control_field, RC, comp, 'Intensity', 0)                                  # unconfirmed
    bad(m.expose_remote_control_field, RC, comp, 'Intensity', 5, **Y)                             # stale count
    bad(m.expose_remote_control_field, RC, comp, 'NoSuchField', 0, **Y)
    bad(m.expose_remote_control_field, RC, comp, 'Intensity', 0, kind='actor', **Y)
    bad(m.expose_remote_control_field, RC, '/Game/Nope.Nope', 'Intensity', 0, **Y)
    ok(m.expose_remote_control_field, RC, comp, 'Intensity', 0, label='Brightness', confirm=True, dry_run=True)
    assert preset()['entity_count'] == 0
    ok(m.expose_remote_control_field, RC, comp, 'Intensity', 0, label='Brightness', **Y)
    bad(m.expose_remote_control_field, RC, comp, 'AttenuationRadius', 1, label='Brightness', **Y)  # label in use
    bad(m.expose_remote_control_field, RC, actor, 'NotAFunction', 1, kind='function', **Y)
    ok(m.expose_remote_control_field, RC, actor, 'SetActorHiddenInGame', 1, kind='function', label='Hide', **Y)
    ok(m.expose_remote_control_field, RC, comp, 'AttenuationRadius', 2, label='Radius', **Y)
    b = row('Brightness')
    assert b['kind'] == 'property' and b['bound'] and b['bound_objects'] == [comp] and b['value_available'], b
    assert row('Hide')['kind'] == 'function' and row('Hide')['function'].endswith('SetActorHiddenInGame')
    # Value.
    old = b['value']
    args = (RC, b['id'], 'Brightness')
    bad(m.set_remote_control_value, *args, old, '1234')                                           # unconfirmed
    bad(m.set_remote_control_value, *args, '-1', '1234', **Y)                                     # stale value
    bad(m.set_remote_control_value, RC, b['id'], 'Wrong', old, '1234', **Y)                       # stale label
    bad(m.set_remote_control_value, *args, old, 'not a number', **Y)
    bad(m.set_remote_control_value, RC, row('Hide')['id'], 'Hide', old, '1', **Y)                 # function has no value
    assert ok(m.set_remote_control_value, *args, old, '1234', confirm=True, dry_run=True)['would_change']
    assert row('Brightness')['value'] == old
    ok(m.set_remote_control_value, *args, old, '1234', **Y)
    new = row('Brightness')['value']
    assert float(new) == 1234, new
    undo()
    assert row('Brightness')['value'] == old
    undo(redo=True)
    assert row('Brightness')['value'] == new
    assert not ok(m.set_remote_control_value, *args, new, new, **Y)['would_change']
    # Unexpose.
    r = row('Radius')
    bad(m.unexpose_remote_control_field, RC, r['id'], 'Wrong', **Y)
    bad(m.unexpose_remote_control_field, RC, r['id'], 'Radius')
    ok(m.unexpose_remote_control_field, RC, r['id'], 'Radius', confirm=True, dry_run=True)
    assert preset()['entity_count'] == 3
    ok(m.unexpose_remote_control_field, RC, r['id'], 'Radius', **Y)
    assert preset()['entity_count'] == 2
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/assets/save', json={'AssetPath': RC}, timeout=120).is_success
    snap = preset()
    snap.pop('dirty')
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(snap, indent=1), encoding='utf-8')
    print('Remote Control preset prepared and saved')


def verify():
    want = json.loads(STATE.read_text(encoding='utf-8'))
    load(MAP)
    got = preset()
    got.pop('dirty')
    assert got == want, json.dumps({'got': got, 'want': want})[:3000]
    print('Remote Control preset entities, binding and value identical after cold reload')
    cleanup()


def cleanup():
    load('/Game/ThirdPerson/Lvl_ThirdPerson')
    for p in (RC, MAP):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
