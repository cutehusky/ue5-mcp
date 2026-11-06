"""Live scene-capture authoring on a scratch map with a SceneCapture2D and a SceneCaptureCube.

prepare: create the scratch map, capture actors, two static-mesh actors (visibility-list targets), 2D/cube render
targets and a material parameter collection with transform vectors. Assign targets (checked through the render-target
consumer pages), edit every editable typed setting, clip plane, custom projection, resolution divisor, user scene
texture outputs, transform collection and its parameter names, view-lighting channels, actor/component lists and
show-flag overrides, each with a dry run, stale guards and (for one edit per route) undo/redo; save and snapshot.
verify (fresh editor): reload the map, compare everything, then restore the original map and delete the fixtures.
"""
import argparse
import json
import math
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'scene_captures.json'
MAP = '/Game/UE5MCP_Test/MCP_SceneCapture'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
D = '/Game/UE5MCP_Test/'
E = '/Script/Engine.'
MPC_CLASS = E + 'MaterialParameterCollection'
# Deleted packages stay in memory until garbage collection, so assets use a per-run name tag.
RT2D = RTCUBE = MPC = None
# 5 world-to-local vectors and 4 projection vectors, contiguous, as the native capture writer expects.
W2L = ['W2L_0', 'W2L_1', 'W2L_2', 'W2L_3', 'W2L_4']
PROJ = ['Proj_0', 'Proj_1', 'Proj_2', 'Proj_3']
VOLATILE = ('scope', 'package_dirty', 'tile_index')
DRIVERS = ('ProjectionType', 'CaptureSource', 'bCaptureEveryFrame')


def use_tag(tag):
    global RT2D, RTCUBE, MPC
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    RT2D, RTCUBE, MPC = n('RT_MCP_Capture2D'), n('RT_MCP_CaptureCube'), n('MPC_MCP_Capture')


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-4)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return a == b


class Capture:
    def __init__(self, api, kind):
        self.api, self.kind = api, kind
        cap = api.call('POST', f'/scene-captures/{kind}/inspect-page', {'Count': 8})['captures']
        assert len(cap) == 1, cap
        self.actor, self.component = cap[0]['actor_path'], cap[0]['component_path']

    def route(self, tail):
        return f'/scene-captures/{self.kind}/{tail}'

    def ref(self):
        return {'ActorPath': self.actor, 'ComponentPath': self.component}

    def settings(self):
        return self.api.call('POST', self.route('settings/inspect'), self.ref())

    def ids(self):
        s = self.settings()
        return {**self.ref(), 'ExpectedClassPath': s['class_path'], 'ActorGuid': s['actor_guid'], 'ExpectedLabel': s['label'], 'bConfirm': True}

    def texts(self):
        return {'ExpectedSettingTexts': self.settings()['native_setting_texts'], 'bRequireSettingSnapshot': True}

    def page(self):
        return self.api.call('POST', self.route('inspect-page'), {'Count': 8})['captures'][0]

    def lists(self):
        a = self.api.call('POST', self.route('actor-lists/inspect'), {**self.ref(), 'Count': 64})
        c = self.api.call('POST', self.route('component-lists/inspect'), {**self.ref(), 'Count': 64})
        f = self.api.call('POST', self.route('show-flags/inspect'), {**self.ref(), 'Count': 128})
        return {'actors': {k: [x['path'] for x in a[k]['actors']] for k in ('hidden_actors', 'show_only_actors')},
                'components': {k: [x['path'] for x in c[k]['components']] for k in ('hidden_components', 'show_only_components')},
                'flags': f['overrides']}

    def state(self):
        s = {k: v for k, v in self.settings().items() if k not in VOLATILE}
        p = {k: v for k, v in self.page().items() if k not in VOLATILE}
        return {'settings': s, 'page': p, **self.lists()}

    def edit(self, tail, body, check, undo=False, stale=None):
        """Dry run leaves state unchanged; optional stale body is refused; the real edit satisfies check(before, after)."""
        before = self.state()
        d = self.api.call('POST', self.route(tail), {**self.ids(), **body, 'bDryRun': True})
        assert d.get('dry_run') is True, (tail, d)
        assert close(self.state(), before), (tail, 'dry run changed state')
        if stale:
            self.api.call('POST', self.route(tail), {**self.ids(), **body, **stale, 'bDryRun': False}, ok=False)
            assert close(self.state(), before), (tail, 'refused edit changed state')
        self.api.call('POST', self.route(tail), {**self.ids(), **body, 'bDryRun': False})
        after = self.state()
        assert check(before, after), (tail, body, json.dumps(after)[:1500])
        if undo:
            self.api.undo()
            assert close(self.state(), before), (tail, 'undo did not restore')
            self.api.redo()
            assert close(self.state(), after), (tail, 'redo did not reapply')
        return after


def field(state, name):
    return next(f for f in state['settings']['fields'] if f['name'] == name)


def next_value(f):
    v = f['value']
    if 'enum_options' in f:
        opts = [o['value'] for o in f['enum_options'] if not o['hidden'] and not o['name'].endswith('_MAX') and not o['name'].endswith('MAX')]
        return opts[(opts.index(v) + 1) % len(opts)] if v in opts else opts[0]
    lo, hi = f['adapter_min'], f['adapter_max']
    if lo == 0 and hi == 1 and f['name'].startswith('b'):
        return 1 - v
    if hi - v >= 1:
        return max(v + 1, lo) if not (lo <= 1 and hi <= 1) else (v + hi) / 2
    return (v + lo) / 2


def settings_stage(cap, known_uneditable):
    """Edit every typed field that is (or becomes) natively editable, in passes, since edits change edit conditions."""
    edited, first = set(), True
    for _ in range(3):
        progress = False
        # Fields that drive other fields' edit conditions go last in each pass.
        order = sorted((f['name'] for f in cap.settings()['fields']), key=lambda n: n in DRIVERS)
        for name in order:
            f = field({'settings': cap.settings()}, name)
            if name in edited or not f['native_can_edit']:
                continue
            value = next_value(f)
            texts = cap.texts()
            stale = {'ExpectedSettingTexts': texts['ExpectedSettingTexts'][:-1] + ['stale']} if first else {'ExpectedValue': f['value'] + 3}
            name = f['name']
            try:
                cap.edit('settings/set', {'FieldName': name, 'Value': value, 'ExpectedValue': f['value'], **texts},
                         lambda b, a, name=name, value=value: close(field(a, name)['value'], value), undo=first, stale=stale)
            except AssertionError as e:
                raise AssertionError((cap.kind, name, f['value'], value)) from e
            edited.add(name)
            first, progress = False, True
        if not progress:
            break
    remaining = {f['name'] for f in cap.settings()['fields']} - edited
    assert remaining == known_uneditable, (cap.kind, sorted(remaining))
    # Out-of-range values are refused.
    f = next(f for f in cap.settings()['fields'] if f['name'] == 'LODDistanceFactor')
    cap.api.call('POST', cap.route('settings/set'), {**cap.ids(), 'FieldName': 'LODDistanceFactor', 'Value': 99, 'ExpectedValue': f['value'], 'bDryRun': False}, ok=False)
    return edited


def target_stage(api, cap, target):
    kind = '2d' if cap.kind == '2d' else 'cube'
    consumers = lambda: api.call('POST', f'/render-targets/{kind}/consumers/inspect-page', {'AssetPath': target, 'Count': 8})
    assert consumers()['matched_count'] == 0
    cap.edit('target', {'AssetPath': target, 'ExpectedTargetPath': ''}, lambda b, a: a['page']['target_path'] == target,
             undo=True, stale={'ExpectedTargetPath': target})
    c = consumers()
    assert c['matched_count'] == 1 and json.dumps(c).count(cap.component) == 1, c
    # A wrong-kind target is refused (cube target on a 2D capture and vice versa).
    other = RTCUBE if cap.kind == '2d' else RT2D
    api.call('POST', cap.route('target'), {**cap.ids(), 'AssetPath': other, 'ExpectedTargetPath': target, 'bDryRun': False}, ok=False)


def set_setting(cap, name, value):
    f = field(cap.state(), name)
    cap.api.call('POST', cap.route('settings/set'), {**cap.ids(), 'FieldName': name, 'Value': value, 'ExpectedValue': f['value'], 'bDryRun': False})


def list_stage(api, cap, actors, components):
    # Native edit conditions: hidden actors need render mode Legacy/RenderScenePrimitives, show-only actors need
    # PRM_UseShowOnlyList; the route follows them.
    set_setting(cap, 'PrimitiveRenderMode', 1)
    msg = api.call('POST', cap.route('actor-lists/set'), {**cap.ids(), 'FieldName': 'ShowOnlyActors', 'ActorPaths': actors, 'ExpectedActorPaths': [], 'bDryRun': True}, ok=False)
    assert 'Native editable actor array required' in msg, msg
    cap.edit('actor-lists/set', {'FieldName': 'HiddenActors', 'ActorPaths': actors[:1], 'ExpectedActorPaths': []},
             lambda b, a: a['actors']['hidden_actors'] == actors[:1], undo=True, stale={'ExpectedActorPaths': actors})
    api.call('POST', cap.route('actor-lists/set'), {**cap.ids(), 'FieldName': 'HiddenActors', 'ActorPaths': [actors[0], actors[0]],
                                                    'ExpectedActorPaths': actors[:1], 'bDryRun': False}, ok=False)
    set_setting(cap, 'PrimitiveRenderMode', 2)
    cap.edit('actor-lists/set', {'FieldName': 'ShowOnlyActors', 'ActorPaths': actors, 'ExpectedActorPaths': []},
             lambda b, a: a['actors']['show_only_actors'] == actors and a['actors']['hidden_actors'] == actors[:1], stale={'ExpectedActorPaths': actors[:1]})
    for fld, key, paths in (('HiddenComponents', 'hidden_components', components[1:]), ('ShowOnlyComponents', 'show_only_components', components)):
        cap.edit('component-lists/set', {'FieldName': fld, 'ComponentPaths': paths, 'ExpectedComponentPaths': []},
                 lambda b, a, key=key, paths=paths: a['components'][key] == paths, undo=fld == 'HiddenComponents', stale={'ExpectedComponentPaths': components})
    flags = api.call('POST', cap.route('show-flags/discover'), {**cap.ref(), 'Name': 'Bloom', 'Count': 4})['flags']
    assert any(f['name'] == 'Bloom' for f in flags), flags
    cap.edit('show-flags/set', {'ShowFlagNames': ['Bloom', 'Fog'], 'ShowFlagValues': [False, True], 'ExpectedShowFlagNames': [], 'ExpectedShowFlagValues': []},
             lambda b, a: [(o['name'], o['enabled']) for o in a['flags']] == [('Bloom', False), ('Fog', True)], undo=True,
             stale={'ExpectedShowFlagNames': ['Bloom'], 'ExpectedShowFlagValues': [True]})
    api.call('POST', cap.route('show-flags/set'), {**cap.ids(), 'ShowFlagNames': ['NoSuchFlagMCP'], 'ShowFlagValues': [True],
                                                   'ExpectedShowFlagNames': ['Bloom', 'Fog'], 'ExpectedShowFlagValues': [False, True], 'bDryRun': False}, ok=False)
    q = api.call('POST', cap.route('show-flags/inspect'), {**cap.ref(), 'ShowFlagNames': ['Bloom'], 'Count': 8})
    assert q['queried_flags'] and q['queried_flags'][0]['name'] == 'Bloom', q


def channel_stage(cap):
    prior = cap.settings()['view_lighting_channels']
    cap.edit('view-channels', {'Channels': [1, 1, 0, 0, 1], 'ExpectedChannels': prior, **cap.texts()},
             lambda b, a: a['settings']['view_lighting_channels'] == [1, 1, 0, 0, 1] and a['settings']['view_lighting_channel_mask'] == 0b10011,
             undo=True, stale={'ExpectedChannels': [0, 0, 0, 0, 0]})
    cap.api.call('POST', cap.route('view-channels'), {**cap.ids(), 'Channels': [2, 0, 0, 0, 0], 'ExpectedChannels': [1, 1, 0, 0, 1], 'bDryRun': False}, ok=False)


def capture2d_stage(api, cap):
    s = cap.settings()
    vec = lambda v: {'X': v[0], 'Y': v[1], 'Z': v[2]}
    enabled = next(f for f in s['fields'] if f['name'] == 'bEnableClipPlane')['value'] == 1
    clip = {'PlaneBase': vec([0, 0, 50]), 'PlaneNormal': vec([0, 1, 0]), 'ExpectedPlaneBase': vec(s['clip_plane_base']),
            'ExpectedPlaneNormal': vec(s['clip_plane_normal']), 'bExpectedClipEnabled': enabled}
    # The clip-plane vectors are editable only with the read-only r.AllowGlobalClipPlane project setting (enabled in
    # DefaultEngine.ini for this verification).
    cap.edit('clip-plane', clip, lambda b, a: a['settings']['clip_plane_base'] == [0, 0, 50] and a['settings']['clip_plane_normal'] == [0, 1, 0],
             undo=True, stale={'ExpectedPlaneBase': vec([1, 2, 3])})
    api.call('POST', cap.route('clip-plane'), {**cap.ids(), **clip, 'ExpectedPlaneBase': vec([0, 0, 50]), 'ExpectedPlaneNormal': vec([0, 1, 0]),
                                               'PlaneNormal': vec([0, 2, 0]), 'bDryRun': False}, ok=False)   # normal must be unit length
    matrix = [2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1, 0, 0, 10, 0]
    cap.edit('projection-matrix', {'Matrix': matrix, 'ExpectedMatrix': s['custom_projection_matrix_row_major'], 'bUseCustomProjection': True,
                                   'bExpectedUseCustomProjection': s['use_custom_projection_matrix']},
             lambda b, a: a['settings']['custom_projection_matrix_row_major'] == matrix and a['settings']['use_custom_projection_matrix'] is True,
             undo=True, stale={'bExpectedUseCustomProjection': True})
    api.call('POST', cap.route('projection-matrix'), {**cap.ids(), 'Matrix': [0] * 16, 'ExpectedMatrix': matrix, 'bUseCustomProjection': True,
                                                      'bExpectedUseCustomProjection': True, 'bDryRun': False}, ok=False)
    cap.edit('resolution-divisor', {'ResolutionDivisor': {'X': 2, 'Y': 4}, 'ExpectedResolutionDivisor': {'X': 1, 'Y': 1}, **cap.texts()},
             lambda b, a: a['settings']['main_view_resolution_divisor'] == [2, 4], undo=True, stale={'ExpectedResolutionDivisor': {'X': 3, 'Y': 3}})
    api.call('POST', cap.route('resolution-divisor'), {**cap.ids(), 'ResolutionDivisor': {'X': 65, 'Y': 1}, 'ExpectedResolutionDivisor': {'X': 2, 'Y': 4}, 'bDryRun': False}, ok=False)
    for i, out in enumerate(('UserSceneTextureBaseColor', 'UserSceneTextureNormal', 'UserSceneTextureSceneColor')):
        cap.edit('output-name', {'FieldName': out, 'OutputName': f'MCP_{out[16:]}', 'ExpectedOutputName': 'None', **cap.texts()},
                 lambda b, a, out=out: a['settings']['user_scene_texture_outputs'][out] == f'MCP_{out[16:]}', undo=i == 0, stale={'ExpectedOutputName': 'Other'})
    # Transform collection: assign, name the first world-to-local and projection vectors, then inspect the layout.
    cap.edit('transform-collection', {'AssetPath': MPC, 'ExpectedTargetPath': '', **cap.texts()},
             lambda b, a: a['settings']['transform_collection_path'] == MPC, undo=True, stale={'ExpectedTargetPath': MPC})
    for fld, name, key in (('CollectionTransformWorldToLocal', W2L[0], 'transform_collection_world_to_local_parameter'),
                           ('CollectionTransformProjection', PROJ[0], 'transform_collection_projection_parameter')):
        cap.edit('collection-parameter', {'FieldName': fld, 'OutputName': name, 'ExpectedOutputName': 'None', 'ExpectedTargetPath': MPC, **cap.texts()},
                 lambda b, a, key=key, name=name: a['settings'][key] == name, undo=fld.endswith('Local'), stale={'ExpectedTargetPath': ''})
    layout = api.call('POST', cap.route('collection-layout/inspect'), {**cap.ref(), 'Count': 16})
    text = json.dumps(layout)
    assert all(n in text for n in W2L + PROJ), text[:1500]
    writers = api.call('POST', cap.route('collection-writers/inspect'), {**cap.ref(), 'Count': 8})
    assert cap.component in json.dumps(writers), json.dumps(writers)[:1500]
    return layout


def create_fixtures(api, tag):
    LIVE = {'bConfirm': True, 'bDryRun': False}
    api.call('POST', '/render-targets/2d/create', {'AssetPath': RT2D, 'SizeX': 64, 'SizeY': 64, **LIVE})
    api.call('POST', '/render-targets/cube/create', {'AssetPath': RTCUBE, 'SizeX': 32, **LIVE})
    snap = api.call('POST', '/materials/collections/create', {'AssetPath': MPC, **LIVE})['defaults_snapshot']
    for name in W2L + PROJ:
        snap = api.call('POST', '/materials/collections/parameters/add', {'AssetPath': MPC, 'FieldName': 'Vector', 'Name': name, 'Color': [0, 0, 0, 0],
                                                                          'ExpectedClassPath': MPC_CLASS, 'ExpectedAssetSnapshot': snap, **LIVE})['defaults_snapshot']
    def spawn(cls, x):
        # The spawn route answers with the bare actor path rather than JSON.
        r = httpx.post(api.base + '/editor/actors/spawn', json={'ActorClass': E + cls, 'Location': {'X': x, 'Y': 0, 'Z': 100}}, timeout=120)
        assert r.is_success, r.text[:500]
        return r.text.strip().strip('"')
    spawn('SceneCapture2D', 0)
    spawn('SceneCaptureCube', 200)
    actors = sorted(spawn('StaticMeshActor', x) for x in (400, 600))
    components = [a + '.StaticMeshComponent0' for a in actors]
    return actors, components


def snapshot(api):
    out = {}
    for kind in ('2d', 'cube'):
        out[kind] = Capture(api, kind).state()
    out['layout'] = {k: v for k, v in api.call('POST', '/scene-captures/2d/collection-layout/inspect', {**Capture(api, '2d').ref(), 'Count': 16}).items() if k not in VOLATILE}
    for kind, target in (('2d', RT2D), ('cube', RTCUBE)):
        out[f'consumers_{kind}'] = api.call('POST', f'/render-targets/{kind}/consumers/inspect-page', {'AssetPath': target, 'Count': 8})['matched_count']
    return out


def diff(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in set(a) | set(b) for d in diff(a.get(k), b.get(k), f'{path}.{k}')]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f'{path}[{i}]')]
    return [] if close(a, b) else [(path, a, b)]


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    original = api.call('GET', '/worlds/inspect')['world_path']
    if original.startswith(MAP):
        original = json.loads(STATE.read_text(encoding='utf-8')).get('original', FALLBACK) if STATE.exists() else FALLBACK
        original = FALLBACK if original.startswith(MAP) else original
        assert api.call('POST', '/worlds/load', {'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    tag = uuid.uuid4().hex[:6]
    use_tag(tag)
    STATE.write_text(json.dumps({'original': original, 'tag': tag}), encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    actors, components = create_fixtures(api, tag)
    c2, cc = Capture(api, '2d'), Capture(api, 'cube')
    target_stage(api, c2, RT2D)
    target_stage(api, cc, RTCUBE)
    settings_stage(c2, set())   # bEnableClipPlane is editable with r.AllowGlobalClipPlane on
    settings_stage(cc, set())
    capture2d_stage(api, c2)
    for cap in (c2, cc):
        channel_stage(cap)
        list_stage(api, cap, actors, components)
    for p in (RT2D, RTCUBE, MPC):
        api.call('POST', '/assets/save', {'AssetPath': p})
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'tag': tag, 'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared scene-capture authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in (RT2D, RTCUBE, MPC):
            api.call('GET', '/assets/describe', params={'asset_path': p})
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = snapshot(api)
        d = diff(state['snapshot'], cold)
        assert not d, d[:20]
        print('Cold reload of scene-capture2D/cube targets, settings, projection, outputs, transform collection, channels, lists and show flags: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    for p in (RT2D, RTCUBE, MPC):
        if p:
            httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned scene-capture test map and assets')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    p.add_argument('--base', default='http://127.0.0.1:8080')
    a = p.parse_args()
    api = Api(a.base)
    assert not api.call('GET', '/editor/status')['is_playing']
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[a.phase](api)


if __name__ == '__main__':
    main()
