"""Semantics of rich float keys and transform-curve duplication/resampling/range removal/offsets; prepare, restart, verify.

Works on a copy of AS_MCP_CurveFixture (create_anim_curve_fixture.py). The existing smoke_animation_curves_live.py calls
these routes; this test asserts what they do:
- a single rich float key keeps its supplied interpolation/tangents/weights and leaves near-coincident neighbours alone;
- float-curve duplication copies colour and comment;
- transform duplication copies all nine channels key for key;
- resampling reproduces the pre-resample evaluation at the new times and refuses bad times without partial mutation;
- the union timeline includes sparse disjoint channel times that the native densest-channel timeline omits;
- key-range removal and time offsets report per-channel impact, keep the other keys, and dry runs change nothing;
- diagnostics report a clean curve set as structurally valid.
verify (fresh editor): compare the cold-loaded curves, then delete the copy.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, FIXTURE

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
SEQ = '/Game/UE5MCP_Test/AS_MCP_CurvesDeep.AS_MCP_CurvesDeep'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'animation_curves_deep.json'
Y = dict(confirm=True)
CHANNELS = [(c, a) for c in ('translation', 'rotation', 'scale') for a in range(3)]


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


def rich(name):
    return ok(m.inspect_animation_rich_float_curve, SEQ, name)


def channel(name, ch, axis):
    return ok(m.inspect_animation_transform_curve_channel, SEQ, name, ch, axis, count=512)['keys']


def channels(name):
    return {f'{c}{a}': channel(name, c, a) for c, a in CHANNELS}


def times(name, ch='translation', axis=0):
    return [round(k['time'], 5) for k in channel(name, ch, axis)]


def float_stage():
    base = rich('MCP_Float')
    print('rich key fields:', sorted(base['keys'][0]))
    k = dict(base['keys'][1])
    # Set one rich key after a linear key: value, interpolation and the leave side are kept; native curve code normalises
    # the arrive side to the incoming linear slope (Break / WeightedLeave). Neighbours keep time, value and modes.
    key = {'Time': 0.3, 'Value': 2.0, 'Interpolation': 2, 'TangentMode': 1, 'ArriveTangent': 1.5, 'LeaveTangent': -2.0,
           'WeightMode': 3, 'ArriveWeight': 0.25, 'LeaveWeight': 0.75}
    stable = lambda x: {f: x[f] for f in ('time', 'value', 'interpolation', 'tangent_mode', 'weight_mode')}
    ok(m.edit_animation_rich_float_key, SEQ, 'MCP_Float', key, confirm=True, dry_run=True)
    assert rich('MCP_Float') == base
    ok(m.edit_animation_rich_float_key, SEQ, 'MCP_Float', key, **Y)
    keys = rich('MCP_Float')['keys']
    added = next(x for x in keys if abs(x['time'] - 0.3) < 1e-6)
    assert len(keys) == 4 and [stable(x) for x in keys if x is not added] == [stable(x) for x in base['keys']], keys
    assert added['value'] == 2 and added['interpolation'] == 2, added
    assert abs(added['leave_tangent'] + 2.0) < 1e-5 and abs(added['leave_weight'] - 0.75) < 1e-5, added
    assert (added['tangent_mode'], added['weight_mode']) == (2, 2) and abs(added['arrive_tangent'] - 10) < 1e-3, added
    bad(m.edit_animation_rich_float_key, SEQ, 'MCP_Float', {'Time': 0.3001}, operation='remove', **Y)      # exact float only
    # Removal used to report success while the 5.7 sequencer controller rebuilt the key from its control channel.
    ok(m.edit_animation_rich_float_key, SEQ, 'MCP_Float', {'Time': 0.3}, operation='remove', **Y)
    assert [x['time'] for x in rich('MCP_Float')['keys']] == [x['time'] for x in base['keys']]
    assert [x['time'] for x in rich('MCP_Float')['keys']] == [x['time'] for x in rich('MCP_Float')['keys']]
    ok(m.edit_animation_rich_float_key, SEQ, 'MCP_Float', key, **Y)                     # kept for the reload check
    # Duplication copies colour and comment.
    ok(m.set_animation_float_curve_color, SEQ, 'MCP_Float', {'R': 0.1, 'G': 0.6, 'B': 0.3, 'A': 1}, **Y)
    ok(m.set_animation_float_curve_comment, SEQ, 'MCP_Float', 'MCP deep comment', **Y)
    r = ok(m.duplicate_animation_float_curve, SEQ, 'MCP_Float', 'MCP_FloatCopy', **Y)
    print('float dup:', r)
    src, dup = rich('MCP_Float'), rich('MCP_FloatCopy')
    assert dup['keys'] == src['keys'], 'keys not copied'
    for f in ('color', 'comment'):
        assert dup.get(f) == src.get(f), (f, dup.get(f), src.get(f))


def transform_stage():
    key = lambda t, x, yaw: {'Time': t, 'Location': {'X': x, 'Y': x / 2, 'Z': 0}, 'Rotation': {'Pitch': 0, 'Yaw': yaw, 'Roll': 0},
                             'Scale': {'X': 1, 'Y': 1, 'Z': 1 + x / 100}}
    m.create_animation_transform_curve(SEQ, 'hand_r', **Y)
    ok(m.replace_animation_transform_curve_keys, SEQ, 'hand_r', [key(0.0, 0, 0), key(0.2, 10, 30), key(0.4, 20, 60), key(0.6, 30, 90)], **Y)
    # Sparse disjoint time on one axis: native timeline follows the densest channel, the union includes it.
    ok(m.replace_animation_transform_curve_channel, SEQ, 'hand_r', 'translation', 2,
       [{'Time': 0.0, 'Value': 0}, {'Time': 0.3, 'Value': 7}, {'Time': 0.6, 'Value': 0}], **Y)
    native = [round(k['time'], 5) for k in ok(m.inspect_animation_transform_curve_keys, SEQ, 'hand_r')['keys']]
    union = [round(k['time'], 5) for k in ok(m.inspect_animation_transform_curve_keys, SEQ, 'hand_r', union_timeline=True)['keys']]
    assert 0.3 not in native and 0.3 in union and set(native) <= set(union), (native, union)
    # Duplicate: all nine channels identical.
    bad(m.duplicate_animation_transform_curve, SEQ, 'hand_r', 'no_bone', **Y)
    bad(m.duplicate_animation_transform_curve, SEQ, 'hand_r', 'hand_r', **Y)
    ok(m.duplicate_animation_transform_curve, SEQ, 'hand_r', 'hand_l', confirm=True, dry_run=True)
    assert 'hand_l' not in json.dumps(ok(m.inspect_animation_curve_diagnostics, SEQ))
    ok(m.duplicate_animation_transform_curve, SEQ, 'hand_r', 'hand_l', **Y)
    assert channels('hand_l') == channels('hand_r')
    # Resample: new keys reproduce the pre-resample evaluation; bad times refused with no partial change.
    sample = [0.0, 0.1, 0.25, 0.5, 0.6]
    before = ok(m.evaluate_animation_transform_curve, SEQ, 'hand_l', sample)
    snap = channels('hand_l')
    bad(m.resample_animation_transform_curve, SEQ, 'hand_l', [0.0, 0.3, 0.2], **Y)
    bad(m.resample_animation_transform_curve, SEQ, 'hand_l', [0.0, 999.0], **Y)
    assert channels('hand_l') == snap
    ok(m.resample_animation_transform_curve, SEQ, 'hand_l', sample, confirm=True, dry_run=True)
    assert channels('hand_l') == snap
    ok(m.resample_animation_transform_curve, SEQ, 'hand_l', sample, **Y)
    assert times('hand_l') == sample and times('hand_l', 'rotation', 2) == sample, times('hand_l')
    after = ok(m.evaluate_animation_transform_curve, SEQ, 'hand_l', sample)
    tx = lambda e: [round(s['location'][0], 3) for s in e['samples']]
    assert tx(after) == tx(before), (tx(before), tx(after))
    # Key-range removal across all channels (inclusive), dry run first.
    snap = channels('hand_r')
    ok(m.remove_animation_transform_curve_key_range, SEQ, 'hand_r', 0.2, 0.4, confirm=True, dry_run=True)
    assert channels('hand_r') == snap
    r = ok(m.remove_animation_transform_curve_key_range, SEQ, 'hand_r', 0.2, 0.4, **Y)
    print('range removal:', json.dumps(r)[:400])
    assert times('hand_r') == [0.0, 0.6] and times('hand_r', 'translation', 2) == [0.0, 0.6], (times('hand_r'), times('hand_r', 'translation', 2))
    kept = channels('hand_r')
    tv = lambda k: (round(k['time'], 5), round(k['value'], 4))                       # auto tangents recompute natively
    assert [tv(k) for k in kept['translation0']] == [tv(snap['translation0'][0]), tv(snap['translation0'][-1])], kept['translation0']
    # Time offsets: every channel shifts; leaving the sequence duration is refused.
    bad(m.offset_animation_transform_curve_time, SEQ, 'hand_r', 999.0, **Y)
    ok(m.offset_animation_transform_curve_time, SEQ, 'hand_r', 0.1, confirm=True, dry_run=True)
    assert channels('hand_r') == kept
    ok(m.offset_animation_transform_curve_time, SEQ, 'hand_r', 0.1, **Y)
    assert times('hand_r') == [0.1, 0.7] and times('hand_r', 'scale', 2) == [0.1, 0.7], times('hand_r')
    shifted = channels('hand_r')
    assert [k['value'] for k in shifted['translation0']] == [k['value'] for k in kept['translation0']]


def diagnostics():
    d = ok(m.inspect_animation_curve_diagnostics, SEQ)
    return {k: d[k] for k in d if k not in ('scope',)}


def snapshot():
    return {'float': rich('MCP_Float'), 'float_copy': rich('MCP_FloatCopy'), 'hand_r': channels('hand_r'), 'hand_l': channels('hand_l'),
            'diagnostics': diagnostics()}


def prepare():
    cleanup()
    r = httpx.post(BASE + '/assets/duplicate', json={'AssetPath': FIXTURE, 'DestinationPath': SEQ.split('.')[0]}, timeout=300)
    assert r.is_success, r.text[:300]
    float_stage()
    transform_stage()
    d = diagnostics()
    print('diagnostics:', json.dumps(d)[:600])
    assert d['complete'] and d['structurally_valid'], d
    assert httpx.post(BASE + '/assets/save', json={'AssetPath': SEQ.split('.')[0]}, timeout=120).status_code == 200
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(snapshot(), indent=1), encoding='utf-8')
    print('Deep curve semantics prepared and saved')


def verify():
    want = json.loads(STATE.read_text(encoding='utf-8'))
    got = json.loads(json.dumps(snapshot()))
    for k in want:
        assert got[k] == want[k], json.dumps({'part': k, 'got': got[k], 'want': want[k]})[:3000]
    print('Deep curve state identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/assets/delete', json={'AssetPath': SEQ.split('.')[0]}, timeout=120)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
