"""Live foliage and procedural-foliage authoring on a scratch map.

prepare: create the scratch map (before any asset), two static-mesh foliage types and a procedural spawner through the
fixture routes (dry runs, duplicate refusals first), an instanced foliage actor, a procedural foliage volume and a
blocking volume. Register types; append, move and delete manual instances; edit every type painting scalar/bool,
scale/cull/placement ranges, scaling mode, source mesh, override material slots/arrays and landscape layer filters;
edit every procedural species setting/flag/curve and scale range; edit spawner settings, its authored type list and
terrain materials; edit procedural component surface flags, spawner reference and tile overlap; edit the blocking
volume target, falloff enable/curve and its inline falloff keys/settings; unregister an empty type. Every edit has a dry
run and a stale-guard refusal; one edit per route also undo/redo. Save and snapshot.
verify (fresh editor): reload, compare everything, then restore the original map and delete the fixtures.
"""
import argparse
import json
import math
import time
import uuid
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'foliage.json'
MAP = '/Game/UE5MCP_Test/MCP_Foliage'
FALLBACK = '/Game/ThirdPerson/Lvl_ThirdPerson'
D = '/Game/UE5MCP_Test/'
LIVE = {'bConfirm': True, 'bDryRun': False}
CUBE, SPHERE = '/Engine/BasicShapes/Cube.Cube', '/Engine/BasicShapes/Sphere.Sphere'
MAT = '/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial'
CURVE = '/Engine/Tutorial/ContentIntroCurve.ContentIntroCurve'
FT = FT2 = SP = None
VOLATILE = ('scope', 'package_dirty', 'update_guid', 'procedural_guid', 'actor_guid', 'native_snapshot_text', 'cached_type_path', 'has_cached_type')


def use_tag(tag):
    global FT, FT2, SP
    n = lambda base: f'{D}{base}_{tag}.{base}_{tag}'
    FT, FT2, SP = n('FT_MCP_Cube'), n('FT_MCP_Sphere'), n('PFS_MCP_Spawner')


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-3)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return a == b


def strip(d):
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k not in VOLATILE}
    if isinstance(d, list):
        return [strip(v) for v in d]
    return d


def ifa(api):
    return api.call('POST', '/foliage/inspect', {})['foliage_actors'][0]['actor_path']


def ftype(api, path=None):
    return api.call('POST', '/foliage/types/asset/inspect', {'TypePath': path or FT})


def guid(api, path=None):
    return ftype(api, path)['update_guid']


def instances(api, path=None):
    return api.call('POST', '/foliage/instances/inspect', {'ActorPath': ifa(api), 'TypePath': path or FT, 'Count': 64})


def procedural(api):
    return api.call('POST', '/foliage/procedural/components/inspect', {})['procedural_components'][0]


def blocking(api):
    return api.call('POST', '/foliage/procedural/blocking/inspect', {})['blocking_volumes'][0]


def falloff(api):
    return api.call('POST', '/volumes/foliage-blocking/inline-falloff/inspect', {'ActorPath': blocking(api)['actor_path'], 'EntryStart': 0, 'EntryCount': 64})


def full(api):
    out = {'actors': api.call('POST', '/foliage/inspect', {})['foliage_actors'],
           'types': api.call('POST', '/foliage/types/inspect', {'ActorPath': ifa(api), 'Count': 16})['types'],
           'ft': ftype(api, FT), 'ft2': ftype(api, FT2), 'spawner': api.call('POST', '/foliage/procedural/spawner/inspect', {'AssetPath': SP}),
           'procedural': procedural(api), 'blocking': blocking(api), 'falloff': falloff(api)}
    for t in out['types']:
        out['inst_' + t['type_path']] = instances(api, t['type_path'])
    return strip(out)


def settled(api):
    prev = full(api)
    for _ in range(20):
        time.sleep(0.2)
        cur = full(api)
        if close(cur, prev):
            return cur
        prev = cur
    raise AssertionError('foliage state did not settle')


def edit(api, route, body, check, undo=False, stale=None):
    """body may be a callable returning fresh guards (update GUIDs change after every edit)."""
    make = body if callable(body) else (lambda: body)
    before = settled(api)
    d = api.call('POST', route, {**make(), 'bConfirm': True, 'bDryRun': True})
    assert d.get('dry_run') is True, (route, d)
    assert close(settled(api), before), (route, 'dry run changed state')
    if stale:
        api.call('POST', route, {**make(), **stale, **LIVE}, ok=False)
    api.call('POST', route, {**make(), **LIVE})
    after = settled(api)
    assert check(before, after), (route, make(), json.dumps({k: after[k] for k in after if not close(after[k], before.get(k))})[:1500])
    if undo:
        api.undo()
        u = settled(api)
        assert close(u, before), (route, 'undo did not restore', [k for k in u if not close(u[k], before.get(k))])
        api.redo()
        r = settled(api)
        assert close(r, after), (route, 'redo did not reapply', [k for k in r if not close(r[k], after.get(k))])
    return after


STALE_GUID = {'ExpectedUpdateGuid': '00000000000000000000000000000000'}


def fixtures(api):
    for path, mesh in ((FT, CUBE), (FT2, SPHERE)):
        d = api.call('POST', '/foliage/types/create', {'TypePath': path, 'AssetPath': mesh, 'bConfirm': True, 'bDryRun': True})
        assert d['dry_run'] and not d['created'], d
        api.call('POST', '/foliage/types/create', {'TypePath': path, 'AssetPath': mesh, **LIVE})
        api.call('POST', '/foliage/types/create', {'TypePath': path, 'AssetPath': mesh, **LIVE}, ok=False)
    api.call('POST', '/foliage/types/create', {'TypePath': f'{D}FT bad.FT bad', **LIVE}, ok=False)
    api.call('POST', '/foliage/types/create', {'TypePath': f'{D}FT_MCP_Bad.FT_MCP_Bad', 'AssetPath': MAT, **LIVE}, ok=False)
    assert ftype(api)['source_path'] == CUBE and ftype(api, FT2)['source_path'] == SPHERE
    d = api.call('POST', '/foliage/procedural/spawner/create', {'AssetPath': SP, 'bConfirm': True, 'bDryRun': True})
    assert d['dry_run'] and not d['created'], d
    api.call('POST', '/foliage/procedural/spawner/create', {'AssetPath': SP, **LIVE})
    api.call('POST', '/foliage/procedural/spawner/create', {'AssetPath': SP, **LIVE}, ok=False)
    r = httpx.post(api.base + '/editor/actors/spawn', json={'ActorClass': '/Script/Foliage.InstancedFoliageActor', 'Location': {'X': 0, 'Y': 0, 'Z': 0}}, timeout=120)
    assert r.is_success, r.text
    for vt in ('ProceduralFoliage', 'ProceduralFoliageBlocking'):
        api.call('POST', '/volumes/create-box', {'VolumeType': vt, 'Name': 'MCP_' + vt, 'Position': {'X': 0, 'Y': 0, 'Z': 0}, 'Extent': {'X': 500, 'Y': 500, 'Z': 200}, **LIVE})


def xf(x):
    return {'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Translation': {'X': x, 'Y': 0, 'Z': 0}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}


def instance_stage(api):
    count = lambda: len(api.call('POST', '/foliage/types/inspect', {'ActorPath': ifa(api), 'Count': 16})['types'])
    edit(api, '/foliage/types/register', lambda: {'ActorPath': ifa(api), 'TypePath': FT, 'ExpectedUpdateGuid': guid(api), 'ExpectedTypeCount': count()},
         lambda b, a: [t['type_path'] for t in a['types']] == [FT], undo=True, stale={'ExpectedTypeCount': 5})
    for i, x in enumerate((100, 200, 300)):
        edit(api, '/foliage/instances/add', lambda: {'ActorPath': ifa(api), 'TypePath': FT, 'ExpectedUpdateGuid': guid(api), 'ExpectedInstanceCount': instances(api)['instance_count'], 'Transform': xf(x)},
             lambda b, a, i=i: a['inst_' + FT]['instance_count'] == i + 1, undo=i == 0, stale={'ExpectedInstanceCount': 99})
    inst = lambda i: instances(api)['instances'][i]
    cur = lambda i: {'ActorPath': ifa(api), 'TypePath': FT, 'ExpectedUpdateGuid': guid(api), 'InstanceIndex': i, 'ExpectedInstanceCount': instances(api)['instance_count'],
                     'ExpectedBaseId': inst(i)['base_id'], 'ExpectedTransform': {'Rotation': dict(zip('XYZW', inst(i)['world_rotation_quaternion'])),
                                                                                 'Translation': dict(zip('XYZ', inst(i)['world_location'])), 'Scale3D': dict(zip('XYZ', inst(i)['world_scale']))}}
    moved = {'Rotation': {'X': 0, 'Y': 0, 'Z': math.sin(math.pi / 8), 'W': math.cos(math.pi / 8)}, 'Translation': {'X': 150, 'Y': 50, 'Z': 20}, 'Scale3D': {'X': 2, 'Y': 2, 'Z': 2}}
    edit(api, '/foliage/instances/transform', lambda: {**cur(1), 'Transform': moved},
         lambda b, a: close(a['inst_' + FT]['instances'][1]['world_location'], [150, 50, 20]) and close(a['inst_' + FT]['instances'][1]['world_scale'], [2, 2, 2]),
         undo=True, stale={'ExpectedTransform': xf(999)})
    edit(api, '/foliage/instances/delete', lambda: cur(2), lambda b, a: a['inst_' + FT]['instance_count'] == 2, undo=True, stale={'ExpectedInstanceCount': 7})


def rng(v):
    return {'X': v[0], 'Y': v[1]}


def type_stage(api):
    base = lambda: {'ActorPath': ifa(api), 'TypePath': FT, 'ExpectedUpdateGuid': guid(api)}
    keys = {'Density': 'density', 'DensityAdjustmentFactor': 'density_adjustment_factor', 'Radius': 'radius', 'MinimumLayerWeight': 'minimum_layer_weight',
            'MinimumExclusionLayerWeight': 'minimum_exclusion_layer_weight', 'SingleInstanceModeRadius': 'single_instance_mode_radius', 'AlignMaxAngle': 'align_max_angle',
            'RandomPitchAngle': 'random_pitch_angle'}
    vals = {'Density': 50, 'DensityAdjustmentFactor': 0.5, 'Radius': 25, 'MinimumLayerWeight': 0.25, 'MinimumExclusionLayerWeight': 0.75, 'SingleInstanceModeRadius': 30,
            'AlignMaxAngle': 15, 'RandomPitchAngle': 10}
    for i, (field, key) in enumerate(keys.items()):
        cur = ftype(api)[key]
        edit(api, '/foliage/types/scalar', lambda field=field, cur=cur: {**base(), 'FieldName': field, 'ExpectedValue': cur, 'Value': vals[field]},
             lambda b, a, key=key, field=field: close(a['ft'][key], vals[field]), undo=i == 0, stale=STALE_GUID)
    for i, (field, key) in enumerate((('AlignToNormal', 'align_to_normal'), ('RandomYaw', 'random_yaw'), ('CollisionWithWorld', 'collision_with_world'),
                                      ('bSingleInstanceModeOverrideRadius', 'single_instance_mode_override_radius'))):
        cur = ftype(api)[key]
        edit(api, '/foliage/types/bool', lambda field=field, cur=cur: {**base(), 'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur},
             lambda b, a, key=key, cur=cur: a['ft'][key] is (not cur), undo=i == 0, stale=STALE_GUID)
    for i, (field, key, v) in enumerate((('ScaleX', 'scale_x', [0.5, 1.5]), ('ScaleY', 'scale_y', [0.75, 1.25]), ('ScaleZ', 'scale_z', [1, 2]))):
        cur = ftype(api)[key]
        edit(api, '/foliage/types/scale-range', lambda field=field, cur=cur, v=v: {**base(), 'FieldName': field, 'ExpectedRange': rng(cur), 'Range': rng(v)},
             lambda b, a, key=key, v=v: close(a['ft'][key], v), undo=i == 0, stale=STALE_GUID)
    api.call('POST', '/foliage/types/scale-range', {**base(), 'FieldName': 'ScaleX', 'ExpectedRange': rng([0.5, 1.5]), 'Range': rng([2, 1]), **LIVE}, ok=False)
    edit(api, '/foliage/types/cull-range', lambda: {**base(), 'ExpectedRange': rng([ftype(api)['cull_distance_min'], ftype(api)['cull_distance_max']]), 'Range': rng([1000, 5000])},
         lambda b, a: (a['ft']['cull_distance_min'], a['ft']['cull_distance_max']) == (1000, 5000), undo=True, stale=STALE_GUID)
    edit(api, '/foliage/types/scaling', lambda: {**base(), 'ExpectedValue': ftype(api)['scaling'], 'Value': 1}, lambda b, a: a['ft']['scaling'] == 1, undo=True, stale=STALE_GUID)
    for i, (field, key, v) in enumerate((('GroundSlopeAngle', 'ground_slope_angle_range', [5, 30]), ('Height', 'height_range', [-1000, 5000]), ('ZOffset', 'z_offset_range', [-5, 5]))):
        cur = ftype(api)[key]
        edit(api, '/foliage/types/placement-range', lambda field=field, cur=cur, v=v: {**base(), 'FieldName': field, 'ExpectedRange': rng(cur), 'Range': rng(v)},
             lambda b, a, key=key, v=v: close(a['ft'][key], v), undo=i == 0, stale=STALE_GUID)
    edit(api, '/foliage/types/mesh', lambda: {**base(), 'ExpectedInstanceCount': instances(api)['instance_count'], 'ExpectedAssetPath': CUBE, 'AssetPath': SPHERE},
         lambda b, a: a['ft']['source_path'] == SPHERE, undo=True, stale={'ExpectedAssetPath': SPHERE})
    edit(api, '/foliage/types/mesh', lambda: {**base(), 'ExpectedInstanceCount': instances(api)['instance_count'], 'ExpectedAssetPath': SPHERE, 'AssetPath': CUBE},
         lambda b, a: a['ft']['source_path'] == CUBE)
    for field, key in (('OverrideMaterials', 'override_materials'), ('NaniteOverrideMaterials', 'nanite_override_materials')):
        edit(api, '/foliage/types/materials', lambda field=field: {**base(), 'FieldName': field, 'ExpectedAssetPaths': ftype(api)[key]['paths'], 'AssetPaths': [MAT, '']},
             lambda b, a, key=key: a['ft'][key]['count'] == 2 and a['ft'][key]['paths'][0] == MAT, undo=field == 'OverrideMaterials', stale={'ExpectedAssetPaths': [MAT]})
        edit(api, '/foliage/types/material-slot', lambda field=field: {**base(), 'FieldName': field, 'ExpectedSlotCount': 2, 'SlotIndex': 1, 'ExpectedAssetPath': '', 'AssetPath': MAT},
             lambda b, a, key=key: a['ft'][key]['paths'] == [MAT, MAT], undo=field == 'OverrideMaterials', stale={'ExpectedSlotCount': 3})
    for field, key in (('LandscapeLayers', 'landscape_layers'), ('ExclusionLandscapeLayers', 'exclusion_landscape_layers')):
        edit(api, '/foliage/types/landscape-layers', lambda field=field, key=key: {**base(), 'FieldName': field, 'ExpectedNames': ftype(api)[key]['names'], 'Names': ['Grass', 'Rock']},
             lambda b, a, key=key: a['ft'][key]['names'] == ['Grass', 'Rock'], undo=field == 'LandscapeLayers', stale={'ExpectedNames': ['Other']})


def procedural_type_stage(api):
    base = lambda: {'TypePath': FT, 'ExpectedUpdateGuid': guid(api)}
    ps = lambda a: a['ft']['procedural_settings']
    vals = {'CollisionRadius': 80, 'ShadeRadius': 60, 'InitialSeedDensity': 2, 'AverageSpreadDistance': 40, 'SpreadVariance': 100, 'MaxInitialSeedOffset': 5,
            'MaxInitialAge': 2, 'MaxAge': 8, 'OverlapPriority': 1, 'NumSteps': 4, 'SeedsPerStep': 5, 'DistributionSeed': 7}
    for i, (field, v) in enumerate(vals.items()):
        cur = ftype(api)['procedural_settings'][field]
        edit(api, '/foliage/types/procedural-setting', lambda field=field, cur=cur, v=v: {**base(), 'FieldName': field, 'ExpectedValue': cur, 'Value': v},
             lambda b, a, field=field, v=v: close(ps(a)[field], v), undo=i == 0, stale=STALE_GUID)
    for i, (field, key) in enumerate((('bCanGrowInShade', 'bCanGrowInShade'), ('bSpawnsInShade', 'bSpawnsInShade'), ('DensityFalloffEnabled', 'density_falloff_enabled'))):
        cur = ftype(api)['procedural_settings'][key]
        edit(api, '/foliage/types/procedural-bool', lambda field=field, cur=cur: {**base(), 'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur},
             lambda b, a, key=key, cur=cur: ps(a)[key] is (not cur), undo=i == 0, stale=STALE_GUID)
    for field, key in (('ScaleCurve', 'scale_curve_path'), ('DensityFalloffCurve', 'density_falloff_curve_path')):
        edit(api, '/foliage/types/procedural-curve', lambda field=field: {**base(), 'FieldName': field, 'ExpectedAssetPath': '', 'AssetPath': CURVE},
             lambda b, a, key=key: ps(a)[key] == CURVE, undo=field == 'ScaleCurve', stale={'ExpectedAssetPath': CURVE})
    edit(api, '/foliage/types/procedural-scale', lambda: {**base(), 'ExpectedRange': rng(ftype(api)['procedural_settings']['procedural_scale']), 'Range': rng([0.5, 2])},
         lambda b, a: close(ps(a)['procedural_scale'], [0.5, 2]), undo=True, stale=STALE_GUID)


def spawner_stage(api):
    sp = lambda: api.call('POST', '/foliage/procedural/spawner/inspect', {'AssetPath': SP})
    vals = {'RandomSeed': ('random_seed', 7), 'NumUniqueTiles': ('num_unique_tiles', 4), 'TileSize': ('tile_size', 5000), 'MinimumQuadTreeSize': ('minimum_quad_tree_size', 50)}
    for i, (field, (key, v)) in enumerate(vals.items()):
        cur = sp()[key]
        edit(api, '/foliage/procedural/spawner/setting', {'AssetPath': SP, 'FieldName': field, 'ExpectedValue': cur, 'Value': v},
             lambda b, a, key=key, v=v: close(a['spawner'][key], v), undo=i == 0, stale={'ExpectedValue': cur + 1})
    edit(api, '/foliage/procedural/spawner/types', {'AssetPath': SP, 'ExpectedAssetPaths': [], 'AssetPaths': [FT, FT2]},
         lambda b, a: a['spawner']['type_count'] == 2 and FT in json.dumps(a['spawner']['types']), undo=True, stale={'ExpectedAssetPaths': [FT]})
    edit(api, '/foliage/procedural/spawner/terrain-materials', {'AssetPath': SP, 'bExpectedValue': False, 'ExpectedAssetPaths': [], 'bValue': True, 'AssetPaths': [MAT]},
         lambda b, a: a['spawner']['use_override_terrain_materials'] and a['spawner']['terrain_material_count'] == 1, undo=True, stale={'bExpectedValue': True})


def component_stage(api):
    ref = lambda: {'ActorPath': procedural(api)['actor_path'], 'ComponentPath': procedural(api)['component_path'], 'ExpectedProceduralGuid': procedural(api)['procedural_guid']}
    stale = {'ExpectedProceduralGuid': '00000000000000000000000000000000'}
    for i, (field, key) in enumerate((('bAllowLandscape', 'allow_landscape'), ('bAllowBSP', 'allow_bsp'), ('bAllowStaticMesh', 'allow_static_mesh'),
                                      ('bAllowTranslucent', 'allow_translucent'), ('bAllowFoliage', 'allow_foliage'), ('bShowDebugTiles', 'show_debug_tiles'))):
        cur = procedural(api)[key]
        edit(api, '/foliage/procedural/components/bool', lambda field=field, cur=cur: {**ref(), 'FieldName': field, 'bExpectedValue': cur, 'bValue': not cur},
             lambda b, a, key=key, cur=cur: a['procedural'][key] is (not cur), undo=i == 0, stale=stale)
    edit(api, '/foliage/procedural/components/spawner', lambda: {**ref(), 'ExpectedAssetPath': '', 'AssetPath': SP},
         lambda b, a: a['procedural']['spawner_path'] == SP, undo=True, stale={'ExpectedAssetPath': SP})
    edit(api, '/foliage/procedural/components/overlap', lambda: {**ref(), 'ExpectedAssetPath': SP, 'ExpectedValue': procedural(api)['tile_overlap'], 'Value': 250},
         lambda b, a: close(a['procedural']['tile_overlap'], 250), undo=True, stale=stale)


def blocking_stage(api):
    bv = lambda: blocking(api)['actor_path']
    edit(api, '/foliage/procedural/blocking/target', lambda: {'ActorPath': bv(), 'ExpectedAssetPath': '', 'AssetPath': procedural(api)['actor_path']},
         lambda b, a: a['blocking']['procedural_volume_path'] == procedural(api)['actor_path'], undo=True, stale={'ExpectedAssetPath': procedural(api)['actor_path']})
    # Inline curve edits first (they guard on the current enable flag and external curve).
    fo = lambda: falloff(api)
    ident = lambda: {'ActorPath': bv(), 'ActorGuid': fo()['actor_guid'], 'ExpectedLabel': fo()['label'], 'bExpectedBoolValue': fo()['falloff_enabled'],
                     'ExpectedCurvePath': fo()['external_curve_path'], 'ExpectedCurveText': fo()['native_snapshot_text']}
    stale = {'ExpectedCurveText': 'stale'}
    keys = lambda: [(k['time'], k['value']) for k in fo()['keys']]
    edit(api, '/volumes/foliage-blocking/inline-falloff/linear-keys', lambda: {**ident(), 'ExpectedPairs': [{'X': t, 'Y': v} for t, v in keys()],
                                                                                 'Pairs': [{'X': 0, 'Y': 1}, {'X': 0.5, 'Y': 0.8}, {'X': 1, 'Y': 0}]},
         lambda b, a: close([[k['time'], k['value']] for k in a['falloff']['keys']], [[0, 1], [0.5, 0.8], [1, 0]]), undo=True, stale=stale)
    edit(api, '/volumes/foliage-blocking/inline-falloff/keys', lambda: {**ident(), 'ExpectedEntryCount': len(keys()), 'FieldName': 'Add', 'EntryIndex': -1, 'Pair': {'X': 0.25, 'Y': 0.9}},
         lambda b, a: a['falloff']['key_count'] == 4, undo=True, stale=stale)
    edit(api, '/volumes/foliage-blocking/inline-falloff/keys', lambda: {**ident(), 'ExpectedEntryCount': len(keys()), 'FieldName': 'Remove', 'EntryIndex': 1, 'Pair': {'X': 0, 'Y': 0}},
         lambda b, a: a['falloff']['key_count'] == 3, stale=stale)
    for i, (field, value) in enumerate((('DefaultValue', 0.5), ('PreInfinityExtrap', 1), ('PostInfinityExtrap', 2))):
        key = {'DefaultValue': 'default_value', 'PreInfinityExtrap': 'pre_extrapolation', 'PostInfinityExtrap': 'post_extrapolation'}[field]
        edit(api, '/volumes/foliage-blocking/inline-falloff/setting', lambda field=field, value=value, key=key: {**ident(), 'FieldName': field, 'ExpectedScalarValue': fo()[key], 'ScalarValue': value},
             lambda b, a, key=key, value=value: close(a['falloff'][key], value), undo=i == 0, stale=stale)
    for i, (field, value) in enumerate((('InterpMode', 2), ('TangentMode', 1), ('ArriveTangent', 0.5), ('LeaveTangent', -0.5))):
        key = {'InterpMode': 'interpolation', 'TangentMode': 'tangent_mode', 'ArriveTangent': 'arrive_tangent', 'LeaveTangent': 'leave_tangent'}[field]
        edit(api, '/volumes/foliage-blocking/inline-falloff/key-setting',
             lambda field=field, value=value, key=key: {**ident(), 'ExpectedEntryCount': len(keys()), 'EntryIndex': 1, 'FieldName': field, 'ExpectedScalarValue': fo()['keys'][1][key], 'ScalarValue': value},
             lambda b, a, key=key, value=value: close(a['falloff']['keys'][1][key], value), undo=i == 0, stale=stale)
    edit(api, '/foliage/procedural/blocking/falloff', lambda: {'ActorPath': bv(), 'bExpectedValue': False, 'ExpectedAssetPath': '', 'bValue': True, 'AssetPath': CURVE},
         lambda b, a: a['blocking']['use_falloff_curve'] and a['blocking']['external_falloff_curve_path'] == CURVE, undo=True, stale={'bExpectedValue': True})


def unregister_stage(api):
    count = lambda: len(api.call('POST', '/foliage/types/inspect', {'ActorPath': ifa(api), 'Count': 16})['types'])
    api.call('POST', '/foliage/types/register', {'ActorPath': ifa(api), 'TypePath': FT2, 'ExpectedUpdateGuid': guid(api, FT2), 'ExpectedTypeCount': count(), **LIVE})
    # A type with instances is refused; the empty one unregisters.
    api.call('POST', '/foliage/types/unregister-empty', {'ActorPath': ifa(api), 'TypePath': FT, 'ExpectedUpdateGuid': guid(api), 'ExpectedTypeCount': count(),
                                                         'ExpectedInstanceCount': instances(api)['instance_count'], **LIVE}, ok=False)
    edit(api, '/foliage/types/unregister-empty', lambda: {'ActorPath': ifa(api), 'TypePath': FT2, 'ExpectedUpdateGuid': guid(api, FT2), 'ExpectedTypeCount': count(), 'ExpectedInstanceCount': 0},
         lambda b, a: [t['type_path'] for t in a['types']] == [FT], undo=True, stale={'ExpectedTypeCount': 9})


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
    fixtures(api)
    instance_stage(api)
    type_stage(api)
    procedural_type_stage(api)
    spawner_stage(api)
    component_stage(api)
    blocking_stage(api)
    unregister_stage(api)
    for p in (FT, FT2, SP):
        api.call('POST', '/assets/save', {'AssetPath': p})
    assert api.call('POST', '/worlds/save', {'bConfirm': True}).get('success', True)
    STATE.write_text(json.dumps({'original': original, 'tag': tag, 'snapshot': settled(api)}), encoding='utf-8')
    print('prepared foliage authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    use_tag(state['tag'])
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        for p in (FT, FT2, SP):
            api.call('GET', '/assets/describe', params={'asset_path': p})
        assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        cold = settled(api)
        bad = [k for k in state['snapshot'] if not close(strip(state['snapshot'][k]), cold.get(k))]
        assert not bad, [(k, json.dumps(state['snapshot'][k])[:500], json.dumps(cold.get(k))[:500]) for k in bad[:3]]
        print('Cold reload of foliage types, instances, procedural species/spawner/component and blocking falloff: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('tag'):
        use_tag(state['tag'])
    httpx.post(api.base + '/worlds/load', json={'WorldPath': state.get('original') or FALLBACK, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(api.base + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    for p in (SP, FT, FT2):
        if p:
            httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned foliage test map and assets')


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
