"""Live reflection-capture and planar-reflection authoring on a scratch map.

prepare: create sphere/box reflection captures and a planar reflection (dry runs first), plus two spare actors to
delete and two static-mesh actors for visibility lists. Edit capture scalars, capture offset, source/cubemap,
visibility and world transform, queue a recapture; edit planar scalars, screen percentage, booleans, visibility and
transform, the inherited capture policy/numeric settings, actor/component lists and show-flag overrides; delete the
spare actors. Each edit with a dry run, stale guards, range refusals and (one per route) undo/redo; save and snapshot.
verify (fresh editor): reload the map, compare everything, then restore the original map and delete the scratch map.
"""
import argparse
import json
import math
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'reflection_captures.json'
MAP = '/Game/UE5MCP_Test/MCP_Reflection'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
CUBEMAP = '/Engine/EngineMaterials/DefaultCubemap.DefaultCubemap'
LIVE = {'bConfirm': True, 'bDryRun': False}
# render_state_created depends on the RHI/scene state, not on authored data.
VOLATILE = ('scope', 'package_dirty', 'render_state_created', 'index')


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-3)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return a == b


def strip(d):
    return {k: v for k, v in d.items() if k not in VOLATILE}


def captures(api):
    return {c['actor_path'].rsplit('.', 1)[1]: strip(c) for c in api.call('POST', '/reflection-captures/inspect-page', {'Count': 64})['captures']}


def planars(api):
    return {c['actor_path'].rsplit('.', 1)[1]: strip(c) for c in api.call('POST', '/reflection-captures/planar/inspect-page', {'Count': 64})['components']}


def ids(entry):
    return {'ActorPath': entry['actor_path'], 'ComponentPath': entry['component_path']}


def edit(api, route, get, name, body, check, undo=False, stale=None, extra_ids=None):
    """Dry run leaves state unchanged; optional stale body refused; real edit satisfies check(before, after)."""
    before = get(api)
    ref = {**ids(before[name]), **(extra_ids(before[name]) if extra_ids else {})}
    d = api.call('POST', route, {**ref, **body, 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, d)
    assert close(get(api), before), (route, body, 'dry run changed state')
    if stale:
        api.call('POST', route, {**ref, **body, **stale, **LIVE}, ok=False)
        assert close(get(api), before), (route, 'refused edit changed state')
    api.call('POST', route, {**ref, **body, **LIVE})
    after = get(api)
    assert check(before[name], after[name]), (route, body, json.dumps(after[name])[:1200])
    others = {k for k in before if k != name}
    assert all(close(before[k], after[k]) for k in others), (route, 'edit touched another capture')
    if undo:
        api.undo()
        assert close(get(api), before), (route, 'undo did not restore')
        api.redo()
        assert close(get(api), after), (route, 'redo did not reapply')
    return after[name]


def xf(loc, quat=(0, 0, 0, 1), scale=(1, 1, 1)):
    return {'Rotation': dict(zip('XYZW', quat)), 'Translation': dict(zip('XYZ', loc)), 'Scale3D': dict(zip('XYZ', scale))}


def create_stage(api):
    for shape, name, x in (('Sphere', 'MCP_Sphere', 0), ('Box', 'MCP_Box', 500), ('Sphere', 'MCP_SphereDel', 1500)):
        body = {'Name': name, 'Shape': shape, 'Location': {'X': x, 'Y': 0, 'Z': 100}}
        if name == 'MCP_Sphere':
            d = api.call('POST', '/reflection-captures/create', {**body, 'bConfirm': True, 'bDryRun': True})
            assert d['dry_run'] and not captures(api), d
            api.call('POST', '/reflection-captures/create', {**body, 'Shape': 'Cone', **LIVE}, ok=False)
        api.call('POST', '/reflection-captures/create', {**body, **LIVE})
    api.call('POST', '/reflection-captures/create', {'Name': 'MCP_Sphere', 'Shape': 'Sphere', 'Location': {'X': 0, 'Y': 0, 'Z': 0}, **LIVE}, ok=False)
    for name, y in (('MCP_Planar', 500), ('MCP_PlanarDel', 1500)):
        body = {'Name': name, 'Location': {'X': 0, 'Y': y, 'Z': 0}}
        if name == 'MCP_Planar':
            d = api.call('POST', '/planar-reflections/create', {**body, 'bConfirm': True, 'bDryRun': True})
            assert d['dry_run'] and not planars(api), d
        api.call('POST', '/planar-reflections/create', {**body, **LIVE})
    assert set(captures(api)) == {'MCP_Sphere', 'MCP_Box', 'MCP_SphereDel'} and set(planars(api)) == {'MCP_Planar', 'MCP_PlanarDel'}
    box = api.call('POST', '/reflection-captures/inspect-page', {'Count': 8, 'Shape': 'Box'})['captures']
    assert [c['shape'] for c in box] == ['Box'], box
    legacy = api.call('POST', '/reflection-captures/inspect', {})
    assert legacy['capture_count'] == 3, legacy


def capture_stage(api):
    scalar = '/reflection-captures/scalar'
    for i, (name, field, key, value) in enumerate((('MCP_Sphere', 'Brightness', 'brightness', 2.5), ('MCP_Sphere', 'SourceCubemapAngle', 'source_cubemap_angle', 90),
                                                   ('MCP_Sphere', 'InfluenceRadius', 'influence_radius', 1500), ('MCP_Box', 'BoxTransitionDistance', 'box_transition_distance', 40),
                                                   ('MCP_Box', 'Brightness', 'brightness', 0.5))):
        cur = captures(api)[name][key]
        edit(api, scalar, captures, name, {'FieldName': field, 'Value': value, 'ExpectedValue': cur},
             lambda b, a, key=key, value=value: close(a[key], value), undo=i == 0, stale={'ExpectedValue': cur + 1})
    # Shape-specific and range refusals.
    api.call('POST', scalar, {**ids(captures(api)['MCP_Box']), 'FieldName': 'InfluenceRadius', 'Value': 10, 'ExpectedValue': 0, **LIVE}, ok=False)
    api.call('POST', scalar, {**ids(captures(api)['MCP_Sphere']), 'FieldName': 'SourceCubemapAngle', 'Value': 400, 'ExpectedValue': 90, **LIVE}, ok=False)
    vec = lambda v: dict(zip('XYZ', v))
    edit(api, '/reflection-captures/offset', captures, 'MCP_Sphere', {'Offset': vec([10, 20, 30]), 'ExpectedOffset': vec([0, 0, 0])},
         lambda b, a: close(a['capture_offset'], [10, 20, 30]), undo=True, stale={'ExpectedOffset': vec([1, 1, 1])})
    edit(api, '/reflection-captures/source', captures, 'MCP_Box', {'SourceType': 'SpecifiedCubemap', 'CubemapPath': CUBEMAP, 'ExpectedSourceType': 0, 'ExpectedCubemapPath': ''},
         lambda b, a: a['source_type'] == 1 and a['cubemap_path'] == CUBEMAP, undo=True, stale={'ExpectedSourceType': 1})
    api.call('POST', '/reflection-captures/source', {**ids(captures(api)['MCP_Sphere']), 'SourceType': 'Sky', 'CubemapPath': '', 'ExpectedSourceType': 0,
                                                     'ExpectedCubemapPath': '', **LIVE}, ok=False)
    edit(api, '/reflection-captures/visible', captures, 'MCP_Box', {'bVisible': False, 'bExpectedVisible': True}, lambda b, a: a['visible'] is False,
         undo=True, stale={'bExpectedVisible': False})
    edit(api, '/reflection-captures/visible', captures, 'MCP_Box', {'bVisible': True, 'bExpectedVisible': False}, lambda b, a: a['visible'] is True)
    s = captures(api)['MCP_Sphere']
    q = [0, 0, math.sin(math.pi / 8), math.cos(math.pi / 8)]
    edit(api, '/reflection-captures/transform', captures, 'MCP_Sphere', {'Transform': xf([100, 50, 200], q), 'ExpectedTransform': xf(s['world_location'], s['world_rotation_quaternion'], s['component_scale'])},
         lambda b, a: close(a['world_location'], [100, 50, 200]) and close(a['world_rotation_quaternion'], q), undo=True,
         stale={'ExpectedTransform': xf([9, 9, 9])})
    s = captures(api)['MCP_Sphere']
    guid = s['map_build_data_id']
    d = api.call('POST', '/reflection-captures/queue-recapture', {**ids(s), 'ExpectedBuildDataId': guid, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and captures(api)['MCP_Sphere']['map_build_data_id'] == guid, d
    api.call('POST', '/reflection-captures/queue-recapture', {**ids(s), 'ExpectedBuildDataId': '00000000000000000000000000000000', **LIVE}, ok=False)
    d = api.call('POST', '/reflection-captures/queue-recapture', {**ids(s), 'ExpectedBuildDataId': guid, **LIVE})
    assert d['queue_requested'] and d['previous_build_data_id'] == guid and captures(api)['MCP_Sphere']['map_build_data_id'] == d['current_build_data_id'] != guid, d


def planar_stage(api):
    keys = {'NormalDistortionStrength': 'normal_distortion_strength', 'PrefilterRoughness': 'prefilter_roughness', 'PrefilterRoughnessDistance': 'prefilter_roughness_distance',
            'ExtraFOV': 'extra_fov', 'DistanceFromPlaneFadeoutStart': 'distance_fade_start', 'DistanceFromPlaneFadeoutEnd': 'distance_fade_end',
            'AngleFromPlaneFadeStart': 'angle_fade_start', 'AngleFromPlaneFadeEnd': 'angle_fade_end'}
    values = {'NormalDistortionStrength': 250, 'PrefilterRoughness': 0.05, 'PrefilterRoughnessDistance': 5000, 'ExtraFOV': 5,
              'DistanceFromPlaneFadeoutStart': 40, 'DistanceFromPlaneFadeoutEnd': 120, 'AngleFromPlaneFadeStart': 15, 'AngleFromPlaneFadeEnd': 35}
    for i, (field, key) in enumerate(keys.items()):
        cur = planars(api)['MCP_Planar'][key]
        edit(api, '/planar-reflections/scalar', planars, 'MCP_Planar', {'FieldName': field, 'Value': values[field], 'ExpectedValue': cur},
             lambda b, a, key=key, v=values[field]: close(a[key], v), undo=i == 0, stale={'ExpectedValue': cur + 1})
    edit(api, '/planar-reflections/screen-percentage', planars, 'MCP_Planar', {'Value': 75, 'ExpectedValue': 50}, lambda b, a: a['screen_percentage'] == 75,
         undo=True, stale={'ExpectedValue': 60})
    api.call('POST', '/planar-reflections/screen-percentage', {**ids(planars(api)['MCP_Planar']), 'Value': 20, 'ExpectedValue': 75, **LIVE}, ok=False)
    for field, key in (('bRenderSceneTwoSided', 'render_scene_two_sided'), ('bShowPreviewPlane', 'show_preview_plane')):
        cur = 1 if planars(api)['MCP_Planar'][key] else 0
        # The route carries any planar boolean in bVisible/bExpectedVisible (as the MCP wrapper does).
        edit(api, '/planar-reflections/bool', planars, 'MCP_Planar', {'FieldName': field, 'bVisible': not cur, 'bExpectedVisible': bool(cur)},
             lambda b, a, key=key, cur=cur: a[key] is (not cur), undo=field.startswith('bRender'), stale={'bExpectedVisible': not cur})
    edit(api, '/planar-reflections/visible', planars, 'MCP_Planar', {'bVisible': False, 'bExpectedVisible': True}, lambda b, a: a['visible'] is False, undo=True)
    edit(api, '/planar-reflections/visible', planars, 'MCP_Planar', {'bVisible': True, 'bExpectedVisible': False}, lambda b, a: a['visible'] is True)
    p = planars(api)['MCP_Planar']
    q = [math.sin(math.pi / 12), 0, 0, math.cos(math.pi / 12)]
    edit(api, '/planar-reflections/transform', planars, 'MCP_Planar', {'Transform': xf([0, 600, 25], q, [2, 2, 1]),
                                                                      'ExpectedTransform': xf(p['world_location'], p['world_rotation_quaternion'], p['component_scale'])},
         lambda b, a: close(a['world_location'], [0, 600, 25]) and close(a['component_scale'], [2, 2, 1]) and not close(a['world_plane_normal'], [0, 0, 1]),
         undo=True, stale={'ExpectedTransform': xf([1, 2, 3])})


def guid_label(api, name):
    entry = planars(api)[name]
    return {'ActorGuid': entry['actor_guid'], 'ExpectedLabel': entry['label']}


def planar_capture_stage(api, actors, components):
    g = lambda e: {'ActorGuid': e['actor_guid'], 'ExpectedLabel': e['label']}
    lists = lambda: api.call('POST', '/reflection-captures/planar/actor-lists/inspect', {**ids(planars(api)['MCP_Planar']), 'Count': 64})
    for i, (field, value) in enumerate((('bCaptureEveryFrame', None), ('bCaptureOnMovement', None), ('bAlwaysPersistRenderingState', None), ('bExcludeFromSceneTextureExtents', None))):
        key = {'bCaptureEveryFrame': 'capture_every_frame', 'bCaptureOnMovement': 'capture_on_movement', 'bAlwaysPersistRenderingState': 'always_persist_rendering_state',
               'bExcludeFromSceneTextureExtents': 'exclude_from_scene_texture_extents'}[field]
        cur = 1 if lists()[key] else 0
        before = lists()
        body = {**ids(planars(api)['MCP_Planar']), **g(planars(api)['MCP_Planar']), 'FieldName': field, 'Value': 1 - cur, 'ExpectedValue': cur}
        d = api.call('POST', '/reflection-captures/planar/capture-policy', {**body, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'] and lists() == before, d
        api.call('POST', '/reflection-captures/planar/capture-policy', {**body, 'ExpectedValue': 1 - cur, **LIVE}, ok=False)
        api.call('POST', '/reflection-captures/planar/capture-policy', {**body, **LIVE})
        assert lists()[key] is (not cur), (field, lists()[key])
        if i == 0:
            api.undo(); assert lists() == before, field
            api.redo(); assert lists()[key] is (not cur), field
    for field, key, value in (('CaptureSortPriority', 'capture_sort_priority', 3), ('LODDistanceFactor', 'lod_distance_factor', 2), ('MaxViewDistanceOverride', 'max_view_distance_override', 5000)):
        cur = lists()[key]
        body = {**ids(planars(api)['MCP_Planar']), **g(planars(api)['MCP_Planar']), 'FieldName': field, 'Value': value, 'ExpectedValue': cur}
        d = api.call('POST', '/reflection-captures/planar/capture-numeric', {**body, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'] and lists()[key] == cur, d
        api.call('POST', '/reflection-captures/planar/capture-numeric', {**body, 'ExpectedValue': cur + 1, **LIVE}, ok=False)
        api.call('POST', '/reflection-captures/planar/capture-numeric', {**body, **LIVE})
        assert close(lists()[key], value), (field, lists()[key])
    api.call('POST', '/reflection-captures/planar/capture-numeric', {**ids(planars(api)['MCP_Planar']), **g(planars(api)['MCP_Planar']), 'FieldName': 'LODDistanceFactor',
                                                                     'Value': 50, 'ExpectedValue': 2, **LIVE}, ok=False)
    # Hidden actors need render mode Legacy/RenderScenePrimitives, show-only actors PRM_UseShowOnlyList (native edit conditions).
    def set_list(route, field, key, paths, item_key, list_key):
        cur = api.call('POST', route.replace('/set', '/inspect'), {**ids(planars(api)['MCP_Planar']), 'Count': 64})
        prior = [x['path'] for x in cur[key][item_key]]
        body = {**ids(planars(api)['MCP_Planar']), **g(planars(api)['MCP_Planar']), 'FieldName': field, list_key: paths, 'Expected' + list_key: prior}
        d = api.call('POST', route, {**body, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'], d
        api.call('POST', route, {**body, 'Expected' + list_key: paths + paths[:0] + ['x'], **LIVE}, ok=False)
        api.call('POST', route, {**body, **LIVE})
        now = api.call('POST', route.replace('/set', '/inspect'), {**ids(planars(api)['MCP_Planar']), 'Count': 64})
        assert [x['path'] for x in now[key][item_key]] == paths, (field, now[key])
    policy = lambda v: api.call('POST', '/reflection-captures/planar/capture-policy', {**ids(planars(api)['MCP_Planar']), **g(planars(api)['MCP_Planar']), 'FieldName': 'PrimitiveRenderMode',
                                                                                        'Value': v, 'ExpectedValue': lists()['primitive_render_mode'], **LIVE})
    policy(1)
    set_list('/reflection-captures/planar/actor-lists/set', 'HiddenActors', 'hidden_actors', actors[:1], 'actors', 'ActorPaths')
    policy(2)
    set_list('/reflection-captures/planar/actor-lists/set', 'ShowOnlyActors', 'show_only_actors', actors, 'actors', 'ActorPaths')
    set_list('/reflection-captures/planar/component-lists/set', 'HiddenComponents', 'hidden_components', components[1:], 'components', 'ComponentPaths')
    set_list('/reflection-captures/planar/component-lists/set', 'ShowOnlyComponents', 'show_only_components', components, 'components', 'ComponentPaths')
    flags = api.call('POST', '/reflection-captures/planar/show-flags/discover', {**ids(planars(api)['MCP_Planar']), 'Name': 'Fog', 'Count': 8})['flags']
    assert any(f['name'] == 'Fog' for f in flags), flags
    sf = lambda: api.call('POST', '/reflection-captures/planar/show-flags/inspect', {**ids(planars(api)['MCP_Planar']), 'Count': 64})['overrides']
    prior = sf()
    body = {**ids(planars(api)['MCP_Planar']), **g(planars(api)['MCP_Planar']), 'ShowFlagNames': ['Fog', 'Bloom'], 'ShowFlagValues': [False, True],
            'ExpectedShowFlagNames': [o['name'] for o in prior], 'ExpectedShowFlagValues': [o['enabled'] for o in prior]}
    d = api.call('POST', '/reflection-captures/planar/show-flags/set', {**body, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and sf() == prior, d
    api.call('POST', '/reflection-captures/planar/show-flags/set', {**body, 'ExpectedShowFlagNames': ['Fog'], 'ExpectedShowFlagValues': [True], **LIVE}, ok=False)
    api.call('POST', '/reflection-captures/planar/show-flags/set', {**body, **LIVE})
    assert [(o['name'], o['enabled']) for o in sf()] == [('Fog', False), ('Bloom', True)], sf()
    api.undo(); assert sf() == prior, 'show-flag undo'
    api.redo()


def delete_stage(api):
    s = captures(api)['MCP_SphereDel']
    body = {**ids(s), 'ExpectedBuildDataId': s['map_build_data_id']}
    d = api.call('POST', '/reflection-captures/delete', {**body, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and 'MCP_SphereDel' in captures(api), d
    api.call('POST', '/reflection-captures/delete', {**body, 'ExpectedBuildDataId': '00000000000000000000000000000000', **LIVE}, ok=False)
    api.call('POST', '/reflection-captures/delete', {**body, **LIVE})
    assert 'MCP_SphereDel' not in captures(api)
    p = planars(api)['MCP_PlanarDel']
    d = api.call('POST', '/planar-reflections/delete', {**ids(p), 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and 'MCP_PlanarDel' in planars(api), d
    api.call('POST', '/planar-reflections/delete', {**ids(p), **LIVE})
    assert set(planars(api)) == {'MCP_Planar'} and set(captures(api)) == {'MCP_Sphere', 'MCP_Box'}


def snapshot(api):
    p = planars(api)['MCP_Planar']
    ref = {**ids(p), 'Count': 64}
    drop = lambda d: {k: v for k, v in d.items() if k not in VOLATILE}
    return {'captures': captures(api), 'planars': planars(api),
            'actor_lists': drop(api.call('POST', '/reflection-captures/planar/actor-lists/inspect', ref)),
            'component_lists': drop(api.call('POST', '/reflection-captures/planar/component-lists/inspect', ref)),
            'show_flags': api.call('POST', '/reflection-captures/planar/show-flags/inspect', ref)['overrides']}


def diff(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in set(a) | set(b) for d in diff(a.get(k), b.get(k), f'{path}.{k}')]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f'{path}[{i}]')]
    return [] if close(a, b) else [(path, a, b)]


def spawn(api, x):
    r = httpx.post(api.base + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.StaticMeshActor', 'Location': {'X': x, 'Y': -500, 'Z': 0}}, timeout=120)
    assert r.is_success, r.text[:400]
    return r.text.strip().strip('"')


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    original = api.call('GET', '/worlds/inspect')['world_path']
    if original.startswith(MAP):
        original = json.loads(STATE.read_text(encoding='utf-8')).get('original', FALLBACK) if STATE.exists() else FALLBACK
        original = FALLBACK if original.startswith(MAP) else original
        assert api.call('POST', '/worlds/load', {'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    STATE.write_text(json.dumps({'original': original}), encoding='utf-8')
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    # Everything below creates actors in the open world; never continue unless it is the scratch map.
    assert api.call('GET', '/worlds/inspect')['world_path'].startswith(MAP)
    actors = sorted(spawn(api, x) for x in (0, 300))
    components = [a + '.StaticMeshComponent0' for a in actors]
    create_stage(api)
    capture_stage(api)
    planar_stage(api)
    planar_capture_stage(api, actors, components)
    delete_stage(api)
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared reflection/planar capture authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        d = diff(state['snapshot'], snapshot(api))
        assert not d, d[:20]
        print('Cold reload of reflection captures, planar reflection, capture policies, lists and show flags: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned reflection test map')


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
