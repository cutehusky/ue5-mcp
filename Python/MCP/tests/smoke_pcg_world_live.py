"""Live PCG world authoring (part 3: components, generation and cached output) on a scratch map.

prepare: create the scratch map (before any asset), a grid-points graph (CreatePointsGrid -> Output) and a TargetPoint
actor. Add a PCG component (dry run first, duplicate name refused), discover it, bind the graph, edit seed/activation/
generation trigger and partitioning, request generation and wait for it, read cached output entries, page through
generated points, inspect output metadata schemas and managed resources, request cleanup and regenerate; add a second
component and remove it (refused while generated, allowed once cleaned). Edits have dry runs, refusals and undo/redo.
Save and snapshot.
verify (fresh editor): reload the map, compare component settings/binding/status, regenerate and compare the output
(same seed, same points), then restore the original map and delete the fixtures.
"""
import argparse
import json
import time
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'pcg_world.json'
MAP = '/Game/UE5MCP_Test/MCP_PCGWorld'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
D = '/Game/UE5MCP_Test/'
LIVE = {'bConfirm': True, 'bDryRun': False}
G = None
VOLATILE = ('scope', 'generation_task_id', 'generation_task_valid')


def use_tag(tag):
    global G
    G = f'{D}PCG_MCP_World_{tag}.PCG_MCP_World_{tag}'


def status(api, ref):
    return {k: v for k, v in api.call('POST', '/pcg/components/status', ref).items() if k not in VOLATILE}


def component(api, ref):
    return next(c for c in api.call('POST', '/pcg/components/inspect', {})['components'] if c['path'] == ref['ComponentPath'])


def wait_idle(api, ref, generated=None):
    for _ in range(60):
        s = status(api, ref)
        if s['idle'] and (generated is None or s['generated'] is generated):
            return s
        time.sleep(0.5)
    raise AssertionError(('component did not become idle', s))


def output(api, ref):
    return {k: v for k, v in api.call('POST', '/pcg/components/output', ref).items() if k != 'scope'}


def points(api, ref, entry, start=0, count=256):
    return api.call('POST', '/pcg/components/output/points', {**ref, 'OutputIndex': entry['index'], 'DataPath': entry['data_path'], 'PointStart': start, 'PointCount': count})


def all_points(api, ref):
    out = output(api, ref)
    entry = out['entries'][0]
    got, start = [], 0
    while True:
        page = points(api, ref, entry, start, 64)
        assert page['start'] == start and page['returned_count'] == len(page['points']), page
        got += page['points']
        start += page['returned_count']
        if start >= page['point_count'] or not page['returned_count']:
            return entry['point_count'], got


def build_graph(api):
    api.call('POST', '/pcg/graphs', {'AssetPath': G, **LIVE})
    np = api.call('POST', '/pcg/graphs/nodes', {'AssetPath': G, 'SettingsClass': '/Script/PCG.PCGCreatePointsGridSettings', 'NodeX': 0, 'NodeY': 0, **LIVE})['node_path']
    g = api.call('POST', '/pcg/graphs/inspect', {'AssetPath': G})
    src = next(n for n in g['nodes'] if n['path'] == np)
    out = next(n for n in g['nodes'] if n['role'] == 'output')
    api.call('PATCH', '/pcg/graphs/edges', {'AssetPath': G, 'Action': 'connect', 'NodeIndex': src['index'], 'NodePath': src['path'], 'FromPin': src['output_pins'][0]['label'],
                                            'TargetNodeIndex': out['index'], 'TargetNodePath': out['path'], 'ToPin': out['input_pins'][0]['label'], **LIVE})
    api.call('POST', '/assets/save', {'AssetPath': G})


def spawn(api, cls, x):
    r = httpx.post(api.base + '/editor/actors/spawn', json={'ActorClass': cls, 'Location': {'X': x, 'Y': 0, 'Z': 0}}, timeout=120)
    assert r.is_success, r.text[:400]
    return r.text.strip().strip('"')


def add_component(api, actor, name, dry_first=False):
    body = {'ActorPath': actor, 'Title': name}
    if dry_first:
        d = api.call('POST', '/pcg/components', {**body, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'] and not api.call('POST', '/pcg/components/inspect', {})['components'], d
        api.call('POST', '/pcg/components', {**body, 'Title': 'bad name!', **LIVE}, ok=False)
    d = api.call('POST', '/pcg/components', {**body, **LIVE})
    api.call('POST', '/pcg/components', {**body, **LIVE}, ok=False)
    return {'ActorPath': actor, 'ComponentPath': d['component_path']}


def edit(api, ref, method, route, body, check, undo=False):
    before = status(api, ref)
    d = api.call(method, route, {**ref, **body, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, d)
    assert status(api, ref) == before, (route, body, 'dry run changed the component')
    api.call(method, route, {**ref, **body, **LIVE})
    after = wait_idle(api, ref)
    assert check(before, after), (route, body, after)
    if undo:
        api.undo()
        assert wait_idle(api, ref) == before, (route, body, 'undo did not restore')
        api.redo()
        assert wait_idle(api, ref) == after, (route, body, 'redo did not reapply')
    return after


def settings_stage(api, ref):
    # Status does not expose the bound graph or partition state; a same-value dry run reports would_change=false.
    same = lambda route, body: api.call('PATCH', route, {**ref, **body, 'bConfirm': True, 'bDryRun': True})['would_change'] is False
    edit(api, ref, 'PATCH', '/pcg/components/graph', {'SourceAssetPath': G}, lambda b, a: same('/pcg/components/graph', {'SourceAssetPath': G}), undo=True)
    api.call('PATCH', '/pcg/components/graph', {**ref, 'SourceAssetPath': '/Game/UE5MCP_Test/NoSuchGraph.NoSuchGraph', **LIVE}, ok=False)
    edit(api, ref, 'PATCH', '/pcg/components/settings', {'Action': 'seed', 'Seed': 1234}, lambda b, a: a['seed'] == 1234, undo=True)
    edit(api, ref, 'PATCH', '/pcg/components/settings', {'Action': 'generation_trigger', 'EnumValue': 'GenerateOnDemand'}, lambda b, a: a['generation_trigger'] == 'GenerateOnDemand', undo=True)
    api.call('PATCH', '/pcg/components/settings', {**ref, 'Action': 'generation_trigger', 'EnumValue': 'GenerateSometimes', **LIVE}, ok=False)
    edit(api, ref, 'PATCH', '/pcg/components/settings', {'Action': 'activated', 'bEnabled': False}, lambda b, a: a['activated'] is False, undo=True)
    # A deactivated component refuses generation.
    api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', **LIVE}, ok=False)
    edit(api, ref, 'PATCH', '/pcg/components/settings', {'Action': 'activated', 'bEnabled': True}, lambda b, a: a['activated'] is True)
    edit(api, ref, 'PATCH', '/pcg/components/partitioned', {'bEnabled': True}, lambda b, a: same('/pcg/components/partitioned', {'bEnabled': True}), undo=True)
    edit(api, ref, 'PATCH', '/pcg/components/partitioned', {'bEnabled': False}, lambda b, a: same('/pcg/components/partitioned', {'bEnabled': False}))
    api.call('PATCH', '/pcg/components/settings', {**ref, 'Action': 'speed', 'Seed': 1, **LIVE}, ok=False)


def generation_stage(api, ref):
    d = api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and not status(api, ref)['generated'], d
    d = api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', 'bForce': True, **LIVE})
    assert d['task_valid'], d
    s = wait_idle(api, ref, generated=True)
    out = output(api, ref)
    assert out['generated'] and out['entry_count'] == 1 and out['entries'][0]['is_native_point_data'], out
    count, pts = all_points(api, ref)
    assert count > 1 and len(pts) == count, (count, len(pts))
    first = points(api, ref, out['entries'][0], 0, 1)['points'][0]
    assert all(k in json.dumps(first) for k in ('ransform', 'ensity')), first
    api.call('POST', '/pcg/components/output/points', {**ref, 'OutputIndex': 0, 'DataPath': out['entries'][0]['data_path'], 'PointStart': count + 5, 'PointCount': 1}, ok=False)
    api.call('POST', '/pcg/components/output/points', {**ref, 'OutputIndex': 0, 'DataPath': out['entries'][0]['data_path'], 'PointStart': 0, 'PointCount': 999}, ok=False)
    meta = api.call('POST', '/pcg/components/output/metadata', {**ref, 'OutputIndex': 0, 'DataPath': out['entries'][0]['data_path']})
    assert 'domain' in json.dumps(meta).lower(), json.dumps(meta)[:600]
    res = api.call('POST', '/pcg/components/resources', ref)
    assert 'resource_count' in res, res
    # Cleanup empties the cached output; regenerating with the same seed reproduces the same points.
    d = api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'cleanup', 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and status(api, ref)['generated'], d
    api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'cleanup', **LIVE})
    wait_idle(api, ref, generated=False)
    assert output(api, ref)['entry_count'] == 0
    api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', 'bForce': True, **LIVE})
    wait_idle(api, ref, generated=True)
    assert all_points(api, ref) == (count, pts), 'regeneration differs'
    api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'explode', **LIVE}, ok=False)
    return count, pts


def removal_stage(api, actor):
    ref = add_component(api, actor, 'MCP_PCG_Spare')
    api.call('PATCH', '/pcg/components/graph', {**ref, 'SourceAssetPath': G, **LIVE})
    api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', 'bForce': True, **LIVE})
    wait_idle(api, ref, generated=True)
    assert 'cleanup' in api.call('POST', '/pcg/components/remove', {**ref, **LIVE}, ok=False).lower()
    api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'cleanup', **LIVE})
    wait_idle(api, ref, generated=False)
    d = api.call('POST', '/pcg/components/remove', {**ref, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and any(c['path'] == ref['ComponentPath'] for c in api.call('POST', '/pcg/components/inspect', {})['components']), d
    api.call('POST', '/pcg/components/remove', {**ref, **LIVE})
    assert not any(c['path'] == ref['ComponentPath'] for c in api.call('POST', '/pcg/components/inspect', {})['components'])


def snapshot(api, ref):
    c = {k: v for k, v in component(api, ref).items() if k not in VOLATILE}
    return {'component': c, 'status': status(api, ref)}


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
    # Everything below edits the open world; never continue unless it is the scratch map.
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    build_graph(api)
    actor = spawn(api, '/Script/Engine.TargetPoint', 0)
    ref = add_component(api, actor, 'MCP_PCG', dry_first=True)
    assert [c['path'] for c in api.call('POST', '/pcg/components/inspect', {})['components']] == [ref['ComponentPath']]
    settings_stage(api, ref)
    count, pts = generation_stage(api, ref)
    removal_stage(api, actor)
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'tag': tag, 'ref': ref, 'count': count, 'points': pts, 'snapshot': snapshot(api, ref)}), encoding='utf-8')
    print(f'prepared PCG component authoring ({count} generated points); restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    ref = state['ref']
    try:
        api.call('GET', '/assets/describe', params={'asset_path': G})
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        wait_idle(api, ref)
        cold = snapshot(api, ref)
        assert cold == state['snapshot'], (state['snapshot'], cold)
        api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', 'bForce': True, **LIVE})
        wait_idle(api, ref, generated=True)
        assert all_points(api, ref) == (state['count'], state['points']), 'cold regeneration differs'
        print(f"Cold reload of PCG component binding/seed/trigger/activation and regenerated output ({state['count']} points): OK")
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    if G:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': G}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned PCG world test map and graph')


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
