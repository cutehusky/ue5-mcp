"""Sublevel authoring and level-streaming volumes; prepare, restart, verify.

prepare: in a scratch persistent map, create two LevelStreaming box volumes, add two sublevels, then edit each
sublevel field through its guarded route (stale guard rejected, dry run unchanged, real edit): current editing level,
lock, transform, streaming class, folder, volume-unload cooldown, colour, streaming volumes, priority and the three
booleans; edit streaming-volume settings and check the reverse references; save every map.
verify (fresh editor): reload the persistent map and compare the snapshot, then delete the maps.
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
T = '/Game/UE5MCP_Test/'
P, A, B = T + 'MCP_SubP', T + 'MCP_SubA', T + 'MCP_SubB'
WORLD = P + '.MCP_SubP'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sublevels.json'
KEYS = {'bDisabled': 'disabled', 'bEditorPreVisOnly': 'editor_previs_only', 'StreamingUsage': 'streaming_usage'}
ALWAYS = '/Script/Engine.LevelStreamingAlwaysLoaded'
DYNAMIC = '/Script/Engine.LevelStreamingDynamic'


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:400])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:300])
    return r['errorMessage']


def listing():
    return ok(m.list_editor_sublevels)


def sub(pkg):
    return next(s for s in listing()['sublevels'] if s['package_path'] == pkg)


def guards(pkg):
    """(level_path, world, streaming object, current editing level) for a sublevel."""
    li = listing()
    s = next(x for x in li['sublevels'] if x['package_path'] == pkg)
    return pkg, li['world_path'], s['streaming_path'], li['current_level_path']


def edit(fn, pkg, expected, value, key, want=None, stale=None, **kw):
    """Stale expected value refused, dry run unchanged, then the edit lands."""
    before = sub(pkg)
    bad(fn, *guards(pkg), stale, value, confirm=True, dry_run=False, **kw)
    ok(fn, *guards(pkg), expected, value, confirm=True, dry_run=True, **kw)
    assert sub(pkg) == before, (fn.__name__, 'dry run changed it')
    ok(fn, *guards(pkg), expected, value, confirm=True, dry_run=False, **kw)
    got = sub(pkg)[key]
    assert got == (value if want is None else want), (fn.__name__, got, value)


def volumes():
    return ok(m.inspect_editor_streaming_volumes, WORLD, 0, 64)


def vol(label):
    return next(v for v in volumes()['volumes'] if v['label'] == label)


def save():
    # Saving the persistent map also saves its loaded sublevel packages.
    r = httpx.post(BASE + '/worlds/save', json={'WorldPath': P, 'bConfirm': True}, timeout=600).json()
    assert r['success'] and not r['dirtyMapPackages'], r


# ---------------------------------------------------------------- stages
def setup():
    for pkg in (A, B, P):
        assert httpx.post(BASE + '/worlds/create', json={'WorldPath': pkg, 'DirtyPolicy': 'discard', 'bSave': True}, timeout=600).json()['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': P, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    # Streaming volumes belong to the persistent level, so they are created before a sublevel becomes current.
    ok(m.create_box_volume, 'LevelStreaming', 'MCP_StreamVolA', [0, 0, 0], [200, 200, 200], label='MCP_StreamVolA', confirm=True, dry_run=True)
    assert not volumes()['volumes']
    for name, x in (('MCP_StreamVolA', 0), ('MCP_StreamVolB', 1000)):
        r = ok(m.create_box_volume, 'LevelStreaming', name, [x, 0, 0], [200, 200, 200], label=name, confirm=True)
        assert 'LevelStreamingVolume' in json.dumps(r), r
    for pkg, cls in ((A, ''), (B, ALWAYS)):
        assert m.add_editor_sublevel(pkg, cls).strip().strip('"') == pkg
    li = listing()
    assert [s['class'] for s in li['sublevels']] == [DYNAMIC, ALWAYS], li
    assert [s['package_path'] for s in li['sublevels']] == [A, B] and all(s['loaded'] for s in li['sublevels']), li
    save()


def current_stage():
    li = listing()
    assert li['current_level_path'] == B + '.MCP_SubB:PersistentLevel', li['current_level_path']  # the last added
    lvl, w, s, cur = guards(A)
    bad(m.make_editor_sublevel_current, lvl, w, s, A + '.MCP_SubA:PersistentLevel', True, confirm=True, dry_run=False)  # stale current
    bad(m.make_editor_sublevel_current, lvl, w, s, cur, False, confirm=True, dry_run=False)                             # stale visibility
    ok(m.make_editor_sublevel_current, lvl, w, s, cur, True, confirm=True, dry_run=True)
    assert listing()['current_level_path'] == cur
    ok(m.make_editor_sublevel_current, lvl, w, s, cur, True, confirm=True, dry_run=False)
    assert listing()['current_level_path'] == A + '.MCP_SubA:PersistentLevel' and sub(A)['is_current_level'], listing()


def class_stage():
    # Streaming-class replacement needs clean packages: refused while anything is dirty, allowed after a save.
    bad(m.set_editor_sublevel_streaming_class, *guards(B), ALWAYS, DYNAMIC, confirm=True, dry_run=False)
    save()
    edit(m.set_editor_sublevel_streaming_class, B, ALWAYS, DYNAMIC, 'class', stale=DYNAMIC)
    bad(m.set_editor_sublevel_streaming_class, *guards(B), DYNAMIC, '/Script/Engine.Actor', confirm=True, dry_run=False)
    assert sub(B)['streaming_path'].split(':')[-1].startswith('LevelStreamingDynamic'), sub(B)
    save()


def field_stage():
    t0 = {'Translation': {'X': 0, 'Y': 0, 'Z': 0}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}
    t1 = {'Translation': {'X': 500, 'Y': -250, 'Z': 100}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0.7071067811865476, 'W': 0.7071067811865476},
          'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}
    bad(m.set_editor_sublevel_transform, *guards(B), t0, {**t1, 'Rotation': {'X': 0, 'Y': 0, 'Z': 1, 'W': 1}}, confirm=True, dry_run=False)
    bad(m.set_editor_sublevel_transform, *guards(B), t0, {**t1, 'Scale3D': {'X': 0, 'Y': 1, 'Z': 1}}, confirm=True, dry_run=False)
    edit(m.set_editor_sublevel_transform, B, t0, t1, 'level_transform',
         want={'translation': [500, -250, 100], 'rotation_quaternion_xyzw': [0, 0, 0.7071067811865476, 0.7071067811865476], 'scale': [1, 1, 1]},
         stale=t1)
    edit(m.set_editor_sublevel_folder, B, '', 'MCP/Streaming', 'folder_path', stale='Other')
    bad(m.set_editor_sublevel_folder, *guards(B), 'MCP/Streaming', 'bad//path', confirm=True, dry_run=False)
    edit(m.set_editor_sublevel_volume_unload_cooldown, B, 2, 7.5, 'volume_unload_cooldown', stale=3)
    bad(m.set_editor_sublevel_volume_unload_cooldown, *guards(B), 7.5, -1, confirm=True, dry_run=False)
    color = sub(B)['level_color_rgba']
    edit(m.set_editor_sublevel_color, B, color, [0.25, 0.5, 0.75, 1], 'level_color_rgba', stale=[0, 0, 0, 0])
    bad(m.set_editor_sublevel_color, *guards(B), [0.25, 0.5, 0.75, 1], [2, 0, 0, 1], confirm=True, dry_run=False)
    edit(m.set_editor_sublevel_priority, B, 0, -12, 'streaming_priority', stale=5)
    for field, key, cur in (('bShouldBlockOnLoad', 'block_on_load', False), ('bShouldBlockOnUnload', 'block_on_unload', False),
                            ('bDrawOnLevelStatusMap', 'draw_on_level_status_map', True)):
        before = sub(B)
        bad(m.set_editor_sublevel_boolean, *guards(B), field, not cur, not cur, confirm=True, dry_run=False)
        ok(m.set_editor_sublevel_boolean, *guards(B), field, cur, not cur, confirm=True, dry_run=True)
        assert sub(B) == before
        ok(m.set_editor_sublevel_boolean, *guards(B), field, cur, not cur, confirm=True, dry_run=False)
        assert sub(B)[key] is (not cur), (field, sub(B))
    bad(m.set_editor_sublevel_boolean, *guards(B), 'bIsStatic', False, True, confirm=True, dry_run=False)


def volume_stage():
    va, vb = vol('MCP_StreamVolA'), vol('MCP_StreamVolB')
    for v in (va, vb):
        assert v['level_path'].endswith('MCP_SubP:PersistentLevel') and v['assigned_streaming_count'] == 0, v
    pa, pb = va['actor_path'], vb['actor_path']
    bad(m.set_editor_sublevel_streaming_volumes, *guards(B), [pa], [pa, pb], confirm=True, dry_run=False)   # stale
    bad(m.set_editor_sublevel_streaming_volumes, *guards(B), [], [pa, pa], confirm=True, dry_run=False)    # duplicate
    ok(m.set_editor_sublevel_streaming_volumes, *guards(B), [], [pb, pa], confirm=True, dry_run=True)
    assert sub(B)['streaming_volume_paths'] == []
    ok(m.set_editor_sublevel_streaming_volumes, *guards(B), [], [pb, pa], confirm=True, dry_run=False)
    assert sub(B)['streaming_volume_paths'] == [pb, pa] and sub(B)['streaming_volume_count'] == 2, sub(B)
    ok(m.set_editor_sublevel_streaming_volumes, *guards(A), [], [pa], confirm=True, dry_run=False)
    # Reverse references rebuilt natively on every volume.
    va, vb = vol('MCP_StreamVolA'), vol('MCP_StreamVolB')
    assert va['assigned_streaming_count'] == 2 and vb['assigned_streaming_count'] == 1, (va, vb)
    assert va['reverse_references_match'] and vb['reverse_references_match'], (va, vb)
    assert va['reverse_level_package_names'] == [A, B] and vb['reverse_level_package_names'] == [B], (va, vb)
    # Clearing one sublevel's list.
    ok(m.set_editor_sublevel_streaming_volumes, *guards(A), [pa], [], confirm=True, dry_run=False)
    assert sub(A)['streaming_volume_paths'] == [] and vol('MCP_StreamVolA')['assigned_streaming_count'] == 1
    # Streaming-volume settings.
    for field, value in (('bDisabled', 1), ('bEditorPreVisOnly', 1), ('StreamingUsage', 2)):
        v = vol('MCP_StreamVolB')
        key = KEYS[field]
        cur = int(v[key])
        ids = (WORLD, v['actor_path'], v['actor_guid'], v['label'])
        bad(m.set_editor_streaming_volume_setting, *ids, field, cur + 3, value, confirm=True, dry_run=False)
        ok(m.set_editor_streaming_volume_setting, *ids, field, cur, value, confirm=True, dry_run=True)
        assert int(vol('MCP_StreamVolB')[key]) == cur
        ok(m.set_editor_streaming_volume_setting, *ids, field, cur, value, confirm=True, dry_run=False)
        assert int(vol('MCP_StreamVolB')[key]) == value, (field, vol('MCP_StreamVolB'))
        assert vol('MCP_StreamVolB')['assigned_streaming_count'] == 1  # reverse names kept
    v = vol('MCP_StreamVolB')
    bad(m.set_editor_streaming_volume_setting, WORLD, v['actor_path'], v['actor_guid'], v['label'], 'StreamingUsage', 2, 9, confirm=True, dry_run=False)


def lock_stage():
    # Lock last: a locked level refuses the other edits.
    edit(m.set_editor_sublevel_locked, B, False, True, 'authored_locked', stale=True)
    assert sub(B)['locked'], sub(B)
    bad(m.set_editor_sublevel_priority, *guards(B), -12, 3, confirm=True, dry_run=False)   # locked
    edit(m.set_editor_sublevel_locked, A, False, True, 'authored_locked', stale=True)
    edit(m.set_editor_sublevel_locked, A, True, False, 'authored_locked', stale=False)


def snapshot():
    out = {}
    for s in listing()['sublevels']:
        s = {k: v for k, v in s.items() if k not in ('is_current_level', 'should_be_loaded', 'should_be_visible', 'visible', 'editor_visible', 'loaded')}
        s['level_color_rgba'] = [round(c, 5) for c in s['level_color_rgba']]
        s['level_transform'] = {k: [round(x, 5) for x in v] for k, v in s['level_transform'].items()}
        out[s['package_path']] = s
    for label in ('MCP_StreamVolA', 'MCP_StreamVolB'):
        v = vol(label)
        out[label] = {k: v[k] for k in ('disabled', 'editor_previs_only', 'streaming_usage', 'reverse_level_package_names', 'assigned_streaming_count', 'reverse_references_match')}
    return out


def prepare():
    cleanup()
    setup()
    current_stage()
    class_stage()
    field_stage()
    volume_stage()
    lock_stage()
    save()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1))
    print('sublevels prepared; maps saved')


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': P, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got, want = json.loads(json.dumps(snapshot())), st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('sublevels and streaming volumes identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    for pkg in (P, A, B):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': pkg}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
