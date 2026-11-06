"""Live float- and transform-curve authoring on the fixture sequence from create_anim_curve_fixture.py.

prepare: author float and transform curves with guard/dry-run/undo checks, save and snapshot.
verify (fresh editor): compare cold-loaded curve data, then delete the fixture sequence.
"""
import argparse
import json
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'animation_curves.json'
FIXTURE = '/Game/UE5MCP_Test/AS_MCP_CurveFixture.AS_MCP_CurveFixture'
SEQ = '/Game/UE5MCP_Test/AS_MCP_CurveWork.AS_MCP_CurveWork'
FILE = PROJECT / 'Content' / 'UE5MCP_Test' / 'AS_MCP_CurveFixture.uasset'


class Api:
    def __init__(self, base):
        self.base = base

    def call(self, method, route, body=None, params=None, ok=True):
        r = httpx.request(method, self.base + route, json=body, params=params, timeout=300)
        if ok:
            assert r.is_success, (method, route, r.status_code, r.text[:1500])
            return r.json()
        assert r.status_code >= 400, (method, route, 'expected rejection', r.text[:800])
        return r.text

    def undo(self):
        self.call('POST', '/editor/transactions/undo', {})

    def redo(self):
        self.call('POST', '/editor/transactions/redo', {})


def catalog(api):
    # FName display case depends on the first spelling registered in the editor process; compare case-insensitively.
    return {c['name'].lower(): c for c in api.call('GET', '/animations/curves/catalog', params={'asset_path': SEQ, 'count': 256})['curves']}


def rich(api, name):
    return api.call('GET', '/animations/curves/rich', params={'asset_path': SEQ, 'curve_name': name, 'count': 512})


def keys_of(api, name):
    return [(round(k['time'], 4), round(k['value'], 4)) for k in rich(api, name)['keys']]


def float_stage(api):
    C = {'AssetPath': SEQ, 'bConfirm': True}
    assert 'mcp_float' in catalog(api), catalog(api)
    assert keys_of(api, 'MCP_Float') == [(0.0, 0.0), (0.2, 1.0), (0.4, 0.5)], keys_of(api, 'MCP_Float')
    # Rich replacement with guards, dry-run, undo/redo.
    new = [{'Time': 0.0, 'Value': 1.0, 'Interpolation': 0}, {'Time': 0.3, 'Value': 2.0, 'Interpolation': 1}]
    api.call('PATCH', '/animations/curves/rich', {**C, 'CurveName': 'MCP_Float', 'Keys': list(reversed(new))}, ok=False)
    api.call('PATCH', '/animations/curves/rich', {**C, 'CurveName': 'Missing', 'Keys': new}, ok=False)
    api.call('PATCH', '/animations/curves/rich', {'AssetPath': SEQ, 'CurveName': 'MCP_Float', 'Keys': new}, ok=False)
    api.call('PATCH', '/animations/curves/rich', {**C, 'CurveName': 'MCP_Float', 'Keys': new, 'bDryRun': True})
    assert keys_of(api, 'MCP_Float') == [(0.0, 0.0), (0.2, 1.0), (0.4, 0.5)]
    api.call('PATCH', '/animations/curves/rich', {**C, 'CurveName': 'MCP_Float', 'Keys': new})
    assert keys_of(api, 'MCP_Float') == [(0.0, 1.0), (0.3, 2.0)]
    api.undo(); assert keys_of(api, 'MCP_Float') == [(0.0, 0.0), (0.2, 1.0), (0.4, 0.5)]
    api.redo(); assert keys_of(api, 'MCP_Float') == [(0.0, 1.0), (0.3, 2.0)]
    # Single keys: set, move, remove.
    api.call('POST', '/animations/curves/key', {**C, 'CurveName': 'MCP_Float', 'Operation': 'set', 'Key': {'Time': 0.5, 'Value': 3.0}})
    assert (0.5, 3.0) in keys_of(api, 'MCP_Float')
    api.call('POST', '/animations/curves/key', {**C, 'CurveName': 'MCP_Float', 'Operation': 'move', 'Key': {'Time': 0.5}, 'NewTime': 0.6})
    assert (0.6, 3.0) in keys_of(api, 'MCP_Float'), keys_of(api, 'MCP_Float')
    api.call('POST', '/animations/curves/key', {**C, 'CurveName': 'MCP_Float', 'Operation': 'move', 'Key': {'Time': 0.6}, 'NewTime': 0.3}, ok=False)
    api.call('POST', '/animations/curves/key', {**C, 'CurveName': 'MCP_Float', 'Operation': 'remove', 'Key': {'Time': 0.6}})
    assert keys_of(api, 'MCP_Float') == [(0.0, 1.0), (0.3, 2.0)]
    # Evaluation, resampling, range.
    ev = api.call('POST', '/animations/curves/evaluate', {**C, 'CurveName': 'MCP_Float', 'Times': [0.0, 0.3]})
    vals = [round(v, 3) for v in (ev.get('values') or [s['value'] for s in ev['samples']])]
    assert vals == [1.0, 2.0], ev
    rng = api.call('GET', '/animations/curves/range', params={'asset_path': SEQ, 'curve_name': 'MCP_Float'})
    assert '2' in json.dumps(rng), rng
    api.call('POST', '/animations/curves/resample', {**C, 'CurveName': 'MCP_Float', 'Times': [0.0, 0.1, 0.2, 0.3]})
    assert [t for t, _ in keys_of(api, 'MCP_Float')] == [0.0, 0.1, 0.2, 0.3], keys_of(api, 'MCP_Float')
    api.call('POST', '/animations/curves/resample', {**C, 'CurveName': 'MCP_Float', 'Times': [0.3, 0.1]}, ok=False)
    # Extrapolation, flags, color, comment.
    api.call('PATCH', '/animations/curves/extrapolation', {**C, 'CurveName': 'MCP_Float', 'PreExtrapolation': 0, 'PostExtrapolation': 3})
    meta = json.dumps(rich(api, 'MCP_Float'))
    assert 'Cycle' in meta or '"pre_extrapolation": 0' in meta, meta[:600]
    api.call('PATCH', '/animations/curves/extrapolation', {**C, 'CurveName': 'MCP_Float', 'PreExtrapolation': 99}, ok=False)
    api.call('PATCH', '/animations/curves/flag', {**C, 'CurveName': 'MCP_Float', 'Flag': 'Metadata', 'bFlagEnabled': True})
    api.call('PATCH', '/animations/curves/flag', {**C, 'CurveName': 'MCP_Float', 'Flag': 'DriveTrack', 'bFlagEnabled': True}, ok=False)
    api.call('PATCH', '/animations/curves/color', {**C, 'CurveName': 'MCP_Float', 'Color': {'R': 0.5, 'G': 0.25, 'B': 1, 'A': 1}})
    assert not api.call('PATCH', '/animations/curves/color', {**C, 'CurveName': 'MCP_Float', 'Color': {'R': 0.5, 'G': 0.25, 'B': 1, 'A': 1}})['would_change']
    api.call('PATCH', '/animations/curves/comment', {**C, 'CurveName': 'MCP_Float', 'Comment': 'authored by smoke test'})
    assert 'authored by smoke test' in json.dumps(rich(api, 'MCP_Float')) or 'authored by smoke test' in json.dumps(catalog(api)['mcp_float'])
    # Duplicate, rename, time offset/scale, key-range removal.
    api.call('POST', '/animations/curves/duplicate', {**C, 'CurveName': 'MCP_Float', 'NewName': 'MCP_Float'}, ok=False)
    api.call('POST', '/animations/curves/duplicate', {**C, 'CurveName': 'MCP_Float', 'NewName': 'MCP_Copy'})
    assert keys_of(api, 'MCP_Copy') == keys_of(api, 'MCP_Float')
    api.undo(); assert 'mcp_copy' not in catalog(api)
    api.redo()
    api.call('PATCH', '/animations/curves/name', {**C, 'CurveName': 'MCP_Copy', 'NewName': 'MCP_Float'}, ok=False)
    api.call('PATCH', '/animations/curves/name', {**C, 'CurveName': 'MCP_Copy', 'NewName': 'MCP_Shifted'})
    assert 'mcp_shifted' in catalog(api) and 'mcp_copy' not in catalog(api)
    api.call('PATCH', '/animations/curves/time-offset', {**C, 'CurveName': 'MCP_Shifted', 'TimeOffset': 0.1})
    assert [t for t, _ in keys_of(api, 'MCP_Shifted')] == [0.1, 0.2, 0.3, 0.4], keys_of(api, 'MCP_Shifted')
    api.call('PATCH', '/animations/curves/time-offset', {**C, 'CurveName': 'MCP_Shifted', 'TimeOffset': -5}, ok=False)
    api.call('PATCH', '/animations/curves/time-scale', {**C, 'CurveName': 'MCP_Shifted', 'TimeOrigin': 0.1, 'TimeFactor': 0.5})
    assert [t for t, _ in keys_of(api, 'MCP_Shifted')] == [0.1, 0.15, 0.2, 0.25], keys_of(api, 'MCP_Shifted')
    api.call('DELETE', '/animations/curves/key-range', {**C, 'CurveName': 'MCP_Shifted', 'RangeStart': 0.15, 'RangeEnd': 0.2})
    assert [t for t, _ in keys_of(api, 'MCP_Shifted')] == [0.1, 0.25], keys_of(api, 'MCP_Shifted')


def tkeys(api, name):
    r = api.call('GET', '/animations/curves/transform/keys', params={'asset_path': SEQ, 'curve_name': name, 'count': 256})
    return r


def transform_stage(api):
    C = {'AssetPath': SEQ, 'bConfirm': True}
    api.call('POST', '/animations/curves/transform', {**C, 'CurveName': 'no_bone'}, ok=False)
    api.call('POST', '/animations/curves/transform', {**C, 'CurveName': 'hand_r'})
    api.call('POST', '/animations/curves/transform', {**C, 'CurveName': 'hand_r'}, ok=False)
    assert 'hand_r' in catalog(api)
    api.undo(); assert 'hand_r' not in catalog(api)
    api.redo(); assert 'hand_r' in catalog(api)
    key = lambda t, x: {'Time': t, 'Location': {'X': x, 'Y': 0, 'Z': 0}, 'Rotation': {'Pitch': 0, 'Yaw': 0, 'Roll': 0}, 'Scale': {'X': 1, 'Y': 1, 'Z': 1}}
    api.call('PATCH', '/animations/curves/transform/keys', {**C, 'CurveName': 'hand_r', 'TransformKeys': [key(0.0, 0), key(0.2, 10), key(0.4, 20)]})
    tk = json.dumps(tkeys(api, 'hand_r'))
    assert '10' in tk and '20' in tk, tk[:600]
    k = key(0.3, 15); k.pop('Time')
    api.call('POST', '/animations/curves/transform/key', {**C, 'CurveName': 'hand_r', 'Key': {'Time': 0.3}, **k})
    assert '15' in json.dumps(tkeys(api, 'hand_r'))
    api.call('PATCH', '/animations/curves/transform/key/time', {**C, 'CurveName': 'hand_r', 'Key': {'Time': 0.3}, 'NewTime': 0.35})
    api.call('DELETE', '/animations/curves/transform/key', {**C, 'CurveName': 'hand_r', 'Key': {'Time': 0.35}})
    api.call('DELETE', '/animations/curves/transform/key', {**C, 'CurveName': 'hand_r', 'Key': {'Time': 0.33}}, ok=False)
    ch = api.call('GET', '/animations/curves/transform-channel', params={'asset_path': SEQ, 'curve_name': 'hand_r', 'channel': 'translation', 'axis': 0, 'count': 64})
    assert [round(k['value'], 3) for k in ch['keys']] == [0.0, 10.0, 20.0], ch['keys']
    api.call('PATCH', '/animations/curves/transform-channel', {**C, 'CurveName': 'hand_r', 'Channel': 'translation', 'Axis': 2,
                                                               'Keys': [{'Time': 0.0, 'Value': 5}, {'Time': 0.4, 'Value': 6}]})
    api.call('PATCH', '/animations/curves/transform-channel', {**C, 'CurveName': 'hand_r', 'Channel': 'bogus', 'Axis': 0, 'Keys': []}, ok=False)
    ev = api.call('POST', '/animations/curves/transform-channel/evaluate', {**C, 'CurveName': 'hand_r', 'Channel': 'translation', 'Axis': 2, 'Times': [0.0]})
    assert '5' in json.dumps(ev), ev
    # UE 5.7's sequencer controller only applies curve attributes to float curves; the route must refuse,
    # including dry runs, and report the engine limitation.
    msg = api.call('PATCH', '/animations/curves/transform-channel/extrapolation', {**C, 'CurveName': 'hand_r', 'Channel': 'translation', 'Axis': 0,
                                                                                  'PreExtrapolation': 3, 'PostExtrapolation': 3, 'bDryRun': True}, ok=False)
    assert 'not supported on UE 5.7' in msg, msg
    full = api.call('POST', '/animations/curves/transform/evaluate', {**C, 'CurveName': 'hand_r', 'Times': [0.2]})
    assert '10' in json.dumps(full), full
    api.call('POST', '/animations/curves/transform/resample', {**C, 'CurveName': 'hand_r', 'Times': [0.0, 0.1, 0.2, 0.3, 0.4]})
    api.call('PATCH', '/animations/curves/transform/flag', {**C, 'CurveName': 'hand_r', 'Flag': 'DriveTrack', 'bFlagEnabled': False})
    api.call('PATCH', '/animations/curves/transform/flag', {**C, 'CurveName': 'hand_r', 'Flag': 'Metadata', 'bFlagEnabled': True}, ok=False)
    api.call('POST', '/animations/curves/transform/duplicate', {**C, 'CurveName': 'hand_r', 'NewName': 'hand_l'})
    api.call('PATCH', '/animations/curves/transform/name', {**C, 'CurveName': 'hand_l', 'NewName': 'foot_l'})
    assert 'foot_l' in catalog(api) and 'hand_l' not in catalog(api)
    api.call('PATCH', '/animations/curves/transform/time-offset', {**C, 'CurveName': 'foot_l', 'TimeOffset': 0.05})
    api.call('DELETE', '/animations/curves/transform/key-range', {**C, 'CurveName': 'foot_l', 'RangeStart': 0.2, 'RangeEnd': 0.5})
    api.call('POST', '/animations/curves/transform', {**C, 'CurveName': 'head'})
    api.call('DELETE', '/animations/curves/transform', {**C, 'CurveName': 'head'})
    assert 'head' not in catalog(api)
    diag = api.call('GET', '/animations/curves/diagnostics', params={'asset_path': SEQ})
    assert diag, diag


def snapshot(api):
    out = {'catalog': catalog(api)}
    for name, c in out['catalog'].items():
        if c.get('type', c.get('kind', '')).lower().startswith('float') or name.startswith('MCP_'):
            out[name] = rich(api, name)
        else:
            out[name] = tkeys(api, name)
    return out


def prepare(api):
    assert FILE.exists(), 'Run create_anim_curve_fixture.py with -run=pythonscript first'
    assert not STATE.exists(), 'Run verify or cleanup first'
    r = httpx.post(api.base + '/assets/duplicate', json={'AssetPath': FIXTURE, 'DestinationPath': SEQ.split('.')[0]}, timeout=300)
    assert r.is_success, r.text[:300]
    try:
        float_stage(api)
        transform_stage(api)
        api.call('POST', '/assets/save', {'AssetPath': SEQ})
        snap = snapshot(api)
        print('Animation curve authoring OK; restart the editor and run verify')
    finally:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'snapshot': locals().get('snap')}), encoding='utf-8')


def strip(s):
    return json.loads(json.dumps(s).replace('"dirty": true', '"dirty": false'))


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api)
        a, b = strip(state['snapshot']), strip(cold)
        for k in set(a) | set(b):
            x = {kk: vv for kk, vv in (a.get(k) or {}).items() if kk != 'scope'}
            y = {kk: vv for kk, vv in (b.get(k) or {}).items() if kk != 'scope'}
            assert x == y, (k, json.dumps(x)[:400], json.dumps(y)[:400])
        print('Cold reload of float curve keys/flags/color/comment/extrapolation and transform curve keys/channels: OK')
    finally:
        cleanup(api)


def cleanup(api):
    """Delete the working copy; the fixture is kept for later runs (delete it with --remove-fixture)."""
    httpx.post(api.base + '/assets/delete', json={'AssetPath': SEQ}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned working copy')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    p.add_argument('--base', default='http://127.0.0.1:8080')
    p.add_argument('--remove-fixture', action='store_true')
    a = p.parse_args()
    api = Api(a.base)
    assert not api.call('GET', '/editor/status')['is_playing']
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[a.phase](api)
    if a.remove_fixture:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': FIXTURE}, timeout=180)


if __name__ == '__main__':
    main()
