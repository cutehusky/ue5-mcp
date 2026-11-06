"""Live runtime-virtual-texture world authoring on a scratch map: RVT volumes, their components and primitive writers.

prepare: create the scratch map (before any asset, so no dirty package blocks it), an RVT, a builder, two RVT volumes
(dry run first) and a static-mesh writer. Edit the writer list/LOD/cull/coverage/main pass, the component's RVT and
builder references, every policy flag, numeric, enum, fixed colour, bounds-align actor and per-platform enable, move
the volume, inspect bounds contributors and align the bounds, check streaming status and the streaming-mip build
(dry run, then the headless refusal), delete the second volume; each edit with a dry run, stale guards and
undo/redo where it applies; save and snapshot.
verify (fresh editor): reload the map, compare component/writer/volume state, then restore the original map and delete.
"""
import argparse
import json
import math
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'rvt_world.json'
MAP = '/Game/UE5MCP_Test/MCP_RVT'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
D = '/Game/UE5MCP_Test/'
LIVE = {'bConfirm': True, 'bDryRun': False}
RVT = VTB = None
VOLATILE = ('scope', 'package_dirty')


def use_tag(tag):
    global RVT, VTB
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    RVT, VTB = n('RVT_MCP_World'), n('VTB_MCP_World')


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-3)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return a == b


def texts(d):
    return json.loads(d['native_authored_snapshot'])


def setting(d, name):
    return next(s for s in d['settings'] if s['name'] == name)


def enum_value(s):
    return next(e['value'] for e in s['enum_values'] if e['name'] == s['native_text'])


class Owner:
    """A component (RVT volume component or primitive writer) addressed by actor/component path."""

    def __init__(self, api, actor, component, route):
        self.api, self.actor, self.component, self.route = api, actor, component, route

    def ref(self):
        return {'ActorPath': self.actor, 'ComponentPath': self.component}

    def inspect(self):
        return self.api.call('POST', self.route, self.ref())

    def ids(self):
        d = self.inspect()
        return {**self.ref(), 'ExpectedClassPath': d['class_path'], 'ActorGuid': d['actor_guid'], 'ExpectedLabel': d['actor_label'],
                'ExpectedAssetSnapshot': d['native_authored_snapshot']}

    def state(self):
        return {k: v for k, v in self.inspect().items() if k not in VOLATILE}

    def edit(self, route, body, check, undo=False, stale=None):
        before = self.state()
        d = self.api.call('POST', route, {**self.ids(), **body, 'bConfirm': True, 'bDryRun': True})
        assert d.get('dry_run') is True, (route, d)
        assert close(self.state(), before), (route, body, 'dry run changed state')
        ids = self.ids()
        self.api.call('POST', route, {**ids, **body, 'ExpectedAssetSnapshot': ids['ExpectedAssetSnapshot'] + ' ', **LIVE}, ok=False)
        if stale:
            self.api.call('POST', route, {**ids, **body, **stale, **LIVE}, ok=False)
        assert close(self.state(), before), (route, 'refused edit changed state')
        self.api.call('POST', route, {**ids, **body, **LIVE})
        after = self.state()
        assert check(before, after), (route, body, json.dumps(after)[:1500])
        if undo:
            self.api.undo()
            assert close(self.state(), before), (route, 'undo did not restore')
            self.api.redo()
            assert close(self.state(), after), (route, 'redo did not reapply')
        return after


def spawn(api, cls, x):
    r = httpx.post(api.base + '/editor/actors/spawn', json={'ActorClass': cls, 'Location': {'X': x, 'Y': 0, 'Z': 0}}, timeout=120)
    assert r.is_success, r.text[:500]
    return r.text.strip().strip('"')


def volume(api, name, x, dry_first=False):
    w = api.call('GET', '/worlds/inspect')['world_path']
    assert w.startswith(MAP), w
    body = {'WorldPath': w, 'Name': name, 'Location': {'X': x, 'Y': 0, 'Z': 0}}
    if dry_first:
        d = api.call('POST', '/runtime-virtual-textures/volumes/create', {**body, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'] and not api.call('POST', '/runtime-virtual-textures/components/discover', {'Count': 8})['components'], d
    d = api.call('POST', '/runtime-virtual-textures/volumes/create', {**body, **LIVE})
    api.call('POST', '/runtime-virtual-textures/volumes/create', {**body, **LIVE}, ok=False)
    return d['actor_path'], d['component_path']


def writer_stage(api, writer):
    def flip_list(b, a):
        return a['runtime_virtual_texture_paths'] == [RVT]
    writer.edit('/runtime-virtual-textures/writers/list', {'SourcePaths': [RVT], 'ExpectedSourcePaths': []}, flip_list, undo=True, stale={'ExpectedSourcePaths': [RVT]})
    for name, value in (('VirtualTextureLodBias', 2), ('VirtualTextureCullMips', 1), ('VirtualTextureMinCoverage', 3)):
        cur = float(setting(writer.inspect(), name)['native_text'])
        writer.edit('/runtime-virtual-textures/writers/numeric', {'FieldName': name, 'Value': value, 'ExpectedValue': cur},
                    lambda b, a, name=name, value=value: float(setting(a, name)['native_text']) == value, undo=name == 'VirtualTextureLodBias',
                    stale={'ExpectedValue': cur + 1})
    api.call('POST', '/runtime-virtual-textures/writers/numeric', {**writer.ids(), 'FieldName': 'VirtualTextureLodBias', 'Value': 20, 'ExpectedValue': 2, **LIVE}, ok=False)
    s = setting(writer.inspect(), 'VirtualTextureRenderPassType')
    writer.edit('/runtime-virtual-textures/writers/main-pass', {'FieldName': 'VirtualTextureRenderPassType', 'Value': 2, 'ExpectedValue': enum_value(s)},
                lambda b, a: setting(a, 'VirtualTextureRenderPassType')['native_text'] == 'Always', undo=True)


def component_stage(api, comp, align_actor, writer):
    ref = '/runtime-virtual-textures/components/reference'
    comp.edit(ref, {'FieldName': 'VirtualTexture', 'AssetPath': RVT, 'ExpectedTargetPath': 'None'},
              lambda b, a: a['runtime_virtual_texture_path'] == RVT, undo=True, stale={'ExpectedTargetPath': RVT})
    comp.edit(ref, {'FieldName': 'StreamingTexture', 'AssetPath': VTB, 'ExpectedTargetPath': 'None'}, lambda b, a: a['streaming_builder_path'] == VTB)
    api.call('POST', ref, {**comp.ids(), 'FieldName': 'StreamingTexture', 'AssetPath': RVT, 'ExpectedTargetPath': VTB, **LIVE}, ok=False)
    flags = ('bSnapBoundsToLandscape', 'bEnableForNaniteOnly', 'bUseMinMaterialQuality', 'bEnableScalability', 'bHidePrimitives',
             'bUseStreamingMipsFixedColor', 'bUseStreamingMipsOnly')
    locked = []
    for i, name in enumerate(flags):
        s = setting(comp.inspect(), name)
        cur = 1 if s['native_text'] == 'True' else 0
        if not s['native_can_edit']:
            assert 'Native editable policy flag required' in api.call('POST', '/runtime-virtual-textures/components/flag',
                                                                     {**comp.ids(), 'FieldName': name, 'Value': 1 - cur, 'ExpectedValue': cur, **LIVE}, ok=False)
            locked.append(name)
            continue
        comp.edit('/runtime-virtual-textures/components/flag', {'FieldName': name, 'Value': 1 - cur, 'ExpectedValue': cur},
                  lambda b, a, name=name, cur=cur: setting(a, name)['native_text'] == ('False' if cur else 'True'), undo=i == 0, stale={'ExpectedValue': 1 - cur})
    for name, value in (('ExpandBounds', 50), ('StreamLowMips', 2), ('ScalabilityGroup', 1)):
        cur = float(setting(comp.inspect(), name)['native_text'])
        comp.edit('/runtime-virtual-textures/components/numeric', {'FieldName': name, 'Value': value, 'ExpectedValue': cur},
                  lambda b, a, name=name, value=value: float(setting(a, name)['native_text']) == value, undo=name == 'ExpandBounds', stale={'ExpectedValue': cur + 1})
    api.call('POST', '/runtime-virtual-textures/components/numeric', {**comp.ids(), 'FieldName': 'ScalabilityGroup', 'Value': 5, 'ExpectedValue': 1, **LIVE}, ok=False)
    for name in ('MinInGameMaterialQuality', 'LossyCompressionAmount', 'UseStreamingMipsInEditorMode'):
        s = setting(comp.inspect(), name)
        if not s['native_can_edit']:
            locked.append(name)
            continue
        opts = [e['value'] for e in s['enum_values'] if not e['hidden'] and not e['name'].endswith('MAX')]
        cur = enum_value(s)
        new = opts[(opts.index(cur) + 1) % len(opts)]
        comp.edit('/runtime-virtual-textures/components/enum', {'FieldName': name, 'Value': new, 'ExpectedValue': cur},
                  lambda b, a, name=name, new=new: enum_value(setting(a, name)) == new, undo=name == 'MinInGameMaterialQuality', stale={'ExpectedValue': new})
    comp.edit('/runtime-virtual-textures/components/fixed-color', {'Color': [0.5, 0.25, 1, 1], 'ExpectedColor': [0, 0, 0, 0]},
              lambda b, a: setting(a, 'StreamingMipsFixedColor')['native_text'] == '(R=0.500000,G=0.250000,B=1.000000,A=1.000000)', undo=True,
              stale={'ExpectedColor': [1, 1, 1, 1]})
    comp.edit('/runtime-virtual-textures/components/bounds-actor', {'AssetPath': align_actor, 'ExpectedTargetPath': ''},
              lambda b, a: setting(a, 'BoundsAlignActor')['native_text'].endswith(align_actor.rsplit('.', 1)[1]) or align_actor in setting(a, 'BoundsAlignActor')['native_text'],
              undo=True, stale={'ExpectedTargetPath': align_actor})
    plat = '/runtime-virtual-textures/components/platform-enable'
    page = lambda: api.call('POST', '/runtime-virtual-textures/components/platform-enable/inspect-page', {**comp.ref(), 'Count': 8})
    # Native text omits default values, so a false default exports as "()"; read the typed page instead.
    comp.edit(plat, {'FieldName': 'Default', 'Name': '', 'Value': 0, 'ExpectedValue': 1}, lambda b, a: page()['default_enabled'] is False, undo=True)
    comp.edit(plat, {'FieldName': 'Override', 'Name': 'Mobile', 'Value': 1, 'ExpectedValue': 0}, lambda b, a: 'Mobile' in setting(a, 'EnableInGamePerPlatform')['native_text'])
    comp.edit(plat, {'FieldName': 'Override', 'Name': 'Desktop', 'Value': 1, 'ExpectedValue': 0}, lambda b, a: 'Desktop' in setting(a, 'EnableInGamePerPlatform')['native_text'])
    comp.edit(plat, {'FieldName': 'RemoveOverride', 'Name': 'Desktop', 'Value': 0, 'ExpectedValue': 1}, lambda b, a: 'Desktop' not in setting(a, 'EnableInGamePerPlatform')['native_text'], undo=True)
    api.call('POST', plat, {**comp.ids(), 'FieldName': 'Override', 'Name': 'bad key!', 'Value': 1, 'ExpectedValue': 0, **LIVE}, ok=False)
    pages = api.call('POST', '/runtime-virtual-textures/components/platform-enable/inspect-page', {**comp.ref(), 'Count': 8})
    assert pages['default_enabled'] is False and pages['override_count'] == 1, pages
    return locked


def transform(loc, scale):
    return {'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Translation': {'X': loc[0], 'Y': loc[1], 'Z': loc[2]}, 'Scale3D': {'X': scale[0], 'Y': scale[1], 'Z': scale[2]}}


def placement_stage(api, comp, writer):
    rvt_snap = api.call('POST', '/runtime-virtual-textures/inspect', {'AssetPath': RVT})['native_authored_snapshot']
    t0 = transform([0, 0, 0], [1, 1, 1])
    comp.edit('/runtime-virtual-textures/volumes/transform', {'Transform': transform([100, 200, -50], [400, 300, 200]), 'ExpectedTransform': t0},
              lambda b, a: a['world_location'] == 'X=100.000 Y=200.000 Z=-50.000' and a['world_scale'] == 'X=400.000 Y=300.000 Z=200.000', undo=True,
              stale={'ExpectedTransform': transform([1, 1, 1], [1, 1, 1])})
    api.call('POST', '/runtime-virtual-textures/volumes/transform', {**comp.ids(), 'Transform': transform([0, 0, 0], [0, 1, 1]),
                                                                      'ExpectedTransform': transform([100, 200, -50], [400, 300, 200]), **LIVE}, ok=False)
    contrib = api.call('POST', '/runtime-virtual-textures/components/bounds-contributors/inspect-page', {**comp.ref(), 'Count': 16})
    paths = [c['component_path'] for c in contrib['primitives']]
    assert writer.component in paths, contrib
    t1 = transform([100, 200, -50], [400, 300, 200])
    align = {'ExpectedTransform': t1, 'ExpectedComponentPaths': paths, 'ExpectedRuntimeTextureSnapshot': rvt_snap}
    comp.edit('/runtime-virtual-textures/volumes/align-bounds', align, lambda b, a: a['world_location'] != b['world_location'] or a['world_scale'] != b['world_scale'],
              undo=True, stale={'ExpectedComponentPaths': []})
    status = api.call('POST', '/runtime-virtual-textures/components/streaming-status', {**comp.ref(), 'bConfirm': True})
    assert status['runtime_virtual_texture_path'] == RVT and status['builder_path'] == VTB, status
    b = api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})
    cur = comp.inspect()
    world = {'Rotation': cur['world_rotation_quaternion'], 'Location': cur['world_location'], 'Scale': cur['world_scale']}
    loc = [float(v.split('=')[1]) for v in world['Location'].split()]
    scale = [float(v.split('=')[1]) for v in world['Scale'].split()]
    build = {**comp.ids(), 'ExpectedRuntimeTextureSnapshot': rvt_snap, 'ExpectedSourceId': b['build_hash_decimal'], 'ExpectedSourcePaths': ['None', 'None'],
             'ExpectedTransform': transform(loc, scale), 'ExpectedComponentPaths': [comp.component]}
    d = api.call('POST', '/runtime-virtual-textures/components/build-streaming-mips', {**build, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, d
    # Refused under -nullrhi; with a rendering RHI the native build renders the streamed mips and updates the builder hash.
    r = httpx.post(api.base + '/runtime-virtual-textures/components/build-streaming-mips', json={**build, **LIVE}, timeout=1800)
    if 'Rendering-capable RHI' not in r.text:
        assert r.is_success, r.text[:500]
        after = api.call('POST', '/virtual-texture-builders/inspect', {'AssetPath': VTB})
        assert after['build_hash_decimal'] != b['build_hash_decimal'], (b['build_hash_decimal'], after['build_hash_decimal'])
        print('streaming mips built:', json.dumps(r.json())[:300])
    builders = api.call('POST', '/virtual-texture-builders/components/inspect-page', {'AssetPath': VTB, 'Count': 8})
    assert comp.component in json.dumps(builders), builders


def delete_stage(api):
    actor, component = volume(api, 'MCP_RVTVolume2', 2000)
    d = api.call('POST', '/runtime-virtual-textures/components/settings/inspect', {'ActorPath': actor, 'ComponentPath': component})
    w = api.call('GET', '/worlds/inspect')['world_path']
    body = {'ActorPath': actor, 'ComponentPath': component, 'WorldPath': w, 'ExpectedClassPath': d['class_path'], 'ActorGuid': d['actor_guid'],
            'ExpectedLabel': d['actor_label'], 'ExpectedAssetSnapshot': d['native_authored_snapshot']}
    r = api.call('POST', '/runtime-virtual-textures/volumes/delete', {**body, 'bConfirm': True, 'bDryRun': True})
    assert r['dry_run'], r
    api.call('POST', '/runtime-virtual-textures/volumes/delete', {**body, 'ExpectedLabel': 'Other', **LIVE}, ok=False)
    api.call('POST', '/runtime-virtual-textures/volumes/delete', {**body, **LIVE})
    left = [c['actor_path'] for c in api.call('POST', '/runtime-virtual-textures/components/discover', {'Count': 8})['components']]
    assert actor not in left and len(left) == 1, left


def snapshot(api, comp, writer):
    return {'component': comp.state(), 'writer': writer.state(),
            'platforms': {k: v for k, v in api.call('POST', '/runtime-virtual-textures/components/platform-enable/inspect-page', {**comp.ref(), 'Count': 8}).items() if k not in VOLATILE},
            'by_rvt': [c['component_path'] for c in api.call('POST', '/runtime-virtual-textures/components/inspect-page', {'AssetPath': RVT, 'Count': 8}).get('components', [])],
            'writers_by_rvt': [w['component_path'] for w in api.call('POST', '/runtime-virtual-textures/writers/inspect-page', {'AssetPath': RVT, 'Count': 8}).get('components', [])]}


def handles(api, state):
    comp = Owner(api, state['volume'][0], state['volume'][1], '/runtime-virtual-textures/components/settings/inspect')
    writer = Owner(api, state['writer'], state['writer'] + '.StaticMeshComponent0', '/runtime-virtual-textures/writers/settings/inspect')
    return comp, writer


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
    # Everything below spawns into the open world; never continue unless it is the scratch map.
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    api.call('POST', '/runtime-virtual-textures/create', {'AssetPath': RVT, **LIVE})
    api.call('POST', '/virtual-texture-builders/create', {'AssetPath': VTB, **LIVE})
    vol = volume(api, 'MCP_RVTVolume', 0, dry_first=True)
    writer_actor = spawn(api, '/Script/Engine.StaticMeshActor', 0)
    align_actor = spawn(api, '/Script/Engine.TargetPoint', 500)
    state = {'original': original, 'tag': tag, 'volume': vol, 'writer': writer_actor, 'align': align_actor}
    STATE.write_text(json.dumps(state), encoding='utf-8')
    comp, writer = handles(api, state)
    writer_stage(api, writer)
    locked = component_stage(api, comp, align_actor, writer)
    assert set(locked) <= {'bUseStreamingMipsOnly', 'UseStreamingMipsInEditorMode'}, locked
    placement_stage(api, comp, writer)
    delete_stage(api)
    for p in (RVT, VTB):
        api.call('POST', '/assets/save', {'AssetPath': p})
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({**state, 'locked': locked, 'snapshot': snapshot(api, comp, writer)}), encoding='utf-8')
    print(f'prepared runtime-VT world authoring (natively locked: {locked}); restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in (RVT, VTB):
            api.call('GET', '/assets/describe', params={'asset_path': p})
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = snapshot(api, *handles(api, state))
        for k in state['snapshot']:
            assert close(state['snapshot'][k], cold[k]), (k, json.dumps(state['snapshot'][k])[:1200], json.dumps(cold[k])[:1200])
        print('Cold reload of runtime-VT volume, component policies, references, platforms and primitive writer: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    for p in (RVT, VTB):
        if p:
            httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned runtime-VT world map and assets')


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
