"""Live Pose Search authoring checks: schemas, channels, roles, databases, entries, normalization sets.

prepare: create owned assets under /Game/UE5MCP_Test/PoseSearch_<tag>, author them, check guards,
dry-run, undo/redo, save and record a manifest. verify (fresh editor): compare saved state, delete.
"""
import argparse
import json
import uuid
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'pose_search.json'
SKELETON = '/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin'
PREVIEW = '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple'
ANIMS = '/Game/Characters/Mannequins/Anims'


class Api:
    def __init__(self, base):
        self.base = base

    def call(self, method, route, body=None, params=None, ok=True):
        r = httpx.request(method, self.base + route, json=body, params=params, timeout=180)
        if ok:
            assert r.is_success, (method, route, r.status_code, r.text[:1500])
            return r.json()
        assert r.status_code >= 400, (method, route, 'expected rejection', r.text[:800])
        return r.text

    def undo(self):
        self.call('POST', '/editor/transactions/undo', {})

    def redo(self):
        self.call('POST', '/editor/transactions/redo', {})

    def schema(self, path):
        return self.call('GET', '/pose-search/schemas/definition', params={'asset_path': path})

    def database(self, path):
        return self.call('GET', '/pose-search/databases/definition', params={'asset_path': path})

    def normalization(self, path):
        return self.call('GET', '/pose-search/normalization-sets/definition', params={'asset_path': path})


def find_sequences(api, count):
    r = api.call('GET', '/assets/search', params={'path': ANIMS, 'class_name': 'AnimSequence', 'limit': 64}, ok=True)
    items = r.get('assets', r if isinstance(r, list) else [])
    paths = sorted(a['object_path'] if isinstance(a, dict) and 'object_path' in a else a.get('path', a) if isinstance(a, dict) else a for a in items)
    assert len(paths) >= count, paths
    return paths[:count]


def channel_classes(api):
    r = api.call('GET', '/pose-search/channel-types', params={'limit': 128})
    return {c['class_path'].rsplit('_', 1)[-1]: c['class_path'] for c in r['channel_types']}


def channels(api, schema):
    return [c['class_path'].rsplit('_', 1)[-1] for c in api.schema(schema)['channels']]


def schema_stage(api, schema):
    S = {'AssetPath': schema, 'bConfirm': True}
    # Sample rate: guards, dry-run, no-op, undo/redo.
    api.call('PATCH', '/pose-search/schemas/sample-rate', {**S, 'SampleRate': 0}, ok=False)
    api.call('PATCH', '/pose-search/schemas/sample-rate', {'AssetPath': schema, 'SampleRate': 60}, ok=False)
    before = api.schema(schema)['sample_rate']
    r = api.call('PATCH', '/pose-search/schemas/sample-rate', {**S, 'SampleRate': 60, 'bDryRun': True})
    assert r['would_change'] and api.schema(schema)['sample_rate'] == before
    api.call('PATCH', '/pose-search/schemas/sample-rate', {**S, 'SampleRate': 60})
    assert api.schema(schema)['sample_rate'] == 60
    api.undo(); assert api.schema(schema)['sample_rate'] == before
    api.redo(); assert api.schema(schema)['sample_rate'] == 60
    assert not api.call('PATCH', '/pose-search/schemas/sample-rate', {**S, 'SampleRate': 60})['would_change']

    # Roles: add, rename, duplicate, move, remove, skeleton; guards.
    roles = lambda: [x['role'] for x in api.schema(schema)['roles']]
    base_roles = roles()
    api.call('POST', '/pose-search/schemas/roles', {**S, 'Role': base_roles[0], 'SkeletonPath': SKELETON}, ok=False)
    api.call('POST', '/pose-search/schemas/roles', {**S, 'Role': 'Partner', 'SkeletonPath': '/Game/Nope.Nope'}, ok=False)
    api.call('POST', '/pose-search/schemas/roles', {**S, 'Role': 'Partner', 'SkeletonPath': SKELETON})
    assert roles() == base_roles + ['Partner']
    api.undo(); assert roles() == base_roles
    api.redo(); assert roles() == base_roles + ['Partner']
    api.call('PATCH', '/pose-search/schemas/roles/name', {**S, 'Role': 'Partner', 'NameValue': base_roles[0]}, ok=False)
    api.call('PATCH', '/pose-search/schemas/roles/name', {**S, 'Role': 'Partner', 'NameValue': 'Rival'})
    api.call('POST', '/pose-search/schemas/roles/duplicate', {**S, 'Role': 'Rival', 'NameValue': 'Rival2'})
    assert roles() == base_roles + ['Rival', 'Rival2']
    api.call('PATCH', '/pose-search/schemas/roles/order', {**S, 'Role': 'Rival2', 'TargetIndex': 0})
    assert roles() == ['Rival2'] + base_roles + ['Rival']
    api.call('PATCH', '/pose-search/schemas/roles/skeleton', {**S, 'Role': 'Rival', 'SkeletonPath': SKELETON})
    api.call('DELETE', '/pose-search/schemas/roles', {**S, 'Role': 'Missing'}, ok=False)
    for role in ('Rival2', 'Rival'):
        api.call('DELETE', '/pose-search/schemas/roles', {**S, 'Role': role})
    assert roles() == base_roles

    # Channels: discovery, add, fields, move/duplicate/remove, group children, finalize.
    cls = channel_classes(api)
    for needed in ('Pose', 'Trajectory', 'Group'):
        assert needed in cls, cls
    api.call('POST', '/pose-search/schemas/channels', {**S, 'ChannelClass': '/Script/Engine.Actor'}, ok=False)
    start = channels(api, schema)
    for name in ('Pose', 'Trajectory', 'Group'):
        r = api.call('POST', '/pose-search/schemas/channels', {**S, 'ChannelClass': cls[name]})
        assert r['inserted'] and r['created_channel_path'], r
    assert channels(api, schema) == start + ['Pose', 'Trajectory', 'Group']
    api.undo(); assert channels(api, schema) == start + ['Pose', 'Trajectory']
    api.redo(); assert channels(api, schema) == start + ['Pose', 'Trajectory', 'Group']
    pose, traj, group = len(start), len(start) + 1, len(start) + 2

    def ch(index, **kw):
        path = api.schema(schema)['channels'][index]['object_path']
        return {**S, 'ChannelIndex': index, 'ChannelPath': path, **kw}

    stale = ch(pose)
    stale['ChannelPath'] = api.schema(schema)['channels'][traj]['object_path']
    api.call('POST', '/pose-search/schemas/channels/inspect', stale, ok=False)

    info = api.call('POST', '/pose-search/schemas/channels/inspect', ch(pose))
    api.call('PATCH', '/pose-search/schemas/channels/scalar', ch(pose, FieldName='Weight', ScalarValue=2.5))
    assert '2.5' in json.dumps(api.call('POST', '/pose-search/schemas/channels/inspect', ch(pose, FieldName='Weight')))
    api.call('PATCH', '/pose-search/schemas/channels/scalar', ch(pose, FieldName='NoSuchField', ScalarValue=1), ok=False)
    api.call('PATCH', '/pose-search/schemas/channels/pose-bones', ch(pose, SampledBones=[{'Bone': 'foot_l'}, {'Bone': 'foot_r', 'Weight': 2}]))
    bones = json.dumps(api.call('POST', '/pose-search/schemas/channels/inspect', ch(pose)))
    assert 'foot_l' in bones and 'foot_r' in bones, bones[:600]
    api.call('PATCH', '/pose-search/schemas/channels/pose-bones', ch(pose, SampledBones=[{'Bone': 'no_such_bone'}]), ok=False)
    api.call('PATCH', '/pose-search/schemas/channels/trajectory-samples', ch(traj, TrajectorySamples=[{'Offset': -0.3}, {'Offset': 0}, {'Offset': 0.5}]))
    assert '0.5' in json.dumps(api.call('POST', '/pose-search/schemas/channels/inspect', ch(traj)))
    api.call('POST', '/pose-search/schemas/channels/group-children', ch(group, ChannelClass=cls['Pose']))
    api.call('POST', '/pose-search/schemas/channels/group-children', ch(group, ChannelClass=cls['Trajectory']))
    def kid(index, child, **kw):
        parent = ch(index)
        tree = api.call('POST', '/pose-search/schemas/channels/inspect', parent)['cached_channel_tree']
        kids = [n['object_path'] for n in tree if n['parent_path'] == parent['ChannelPath']]
        return {**parent, 'ChildIndices': [child], 'ChannelPath': kids[child], **kw}

    api.call('PATCH', '/pose-search/schemas/channels/scalar', kid(group, 0, FieldName='Weight', ScalarValue=3))
    assert '3' in json.dumps(api.call('POST', '/pose-search/schemas/channels/inspect', kid(group, 0, FieldName='Weight')))
    def child_op(index, child, **kw):
        return {**ch(index), 'AnimationIndex': child, 'SourceAssetPath': kid(index, child)['ChannelPath'], **kw}

    api.call('PATCH', '/pose-search/schemas/channels/group-children/order', {**child_op(group, 1, TargetIndex=0), 'SourceAssetPath': 'stale'}, ok=False)
    api.call('PATCH', '/pose-search/schemas/channels/group-children/order', child_op(group, 1, TargetIndex=0))
    first = kid(group, 0)['ChannelPath']
    assert 'Trajectory' in first, first
    api.undo(); assert 'Pose' in kid(group, 0)['ChannelPath']
    api.redo(); assert 'Trajectory' in kid(group, 0)['ChannelPath']
    api.call('POST', '/pose-search/schemas/channels/group-children/duplicate', child_op(group, 0))
    api.call('DELETE', '/pose-search/schemas/channels/group-children', child_op(group, 2))
    assert 'Trajectory' in kid(group, 0)['ChannelPath'] and 'Pose' in kid(group, 1)['ChannelPath']
    api.call('PATCH', '/pose-search/schemas/channels/order', ch(group, TargetIndex=pose))
    assert channels(api, schema)[pose] == 'Group'
    api.call('POST', '/pose-search/schemas/channels/duplicate', ch(pose))
    assert channels(api, schema).count('Group') == 2
    api.call('DELETE', '/pose-search/schemas/channels', ch(len(channels(api, schema)) - 1))
    assert channels(api, schema).count('Group') == 1
    # Typed field editors on a Heading channel.
    api.call('POST', '/pose-search/schemas/channels', {**S, 'ChannelClass': cls['Heading']})
    head = len(channels(api, schema)) - 1
    field = lambda name: json.dumps(api.call('POST', '/pose-search/schemas/channels/inspect', ch(head, FieldName=name)))
    api.call('PATCH', '/pose-search/schemas/channels/name', ch(head, FieldName='NormalizationGroup', NameValue='Feet'))
    assert 'Feet' in field('NormalizationGroup')
    api.call('PATCH', '/pose-search/schemas/channels/name', ch(head, FieldName='NormalizationGroup', NameValue='bad\nname'), ok=False)
    api.call('PATCH', '/pose-search/schemas/channels/enum', ch(head, FieldName='HeadingAxis', NameValue='Y'))
    assert '"Y"' in field('HeadingAxis') or 'Y' in field('HeadingAxis')
    api.call('PATCH', '/pose-search/schemas/channels/enum', ch(head, FieldName='HeadingAxis', NameValue='W'), ok=False)
    color = ch(head, FieldName='DebugColor', ColorValue={'R': 0.25, 'G': 0.5, 'B': 0.75, 'A': 1})
    r = api.call('PATCH', '/pose-search/schemas/channels/color', color)
    assert 'R=0.250000,G=0.500000,B=0.750000' in field('DebugColor'), field('DebugColor')
    assert not api.call('PATCH', '/pose-search/schemas/channels/color', ch(head, FieldName='DebugColor', ColorValue=color['ColorValue']))['would_change']
    weight = lambda: json.loads(field('Weight'))
    default_weight = json.dumps(weight())
    api.call('PATCH', '/pose-search/schemas/channels/scalar', ch(head, FieldName='Weight', ScalarValue=4))
    assert '4.0' in json.dumps(weight())
    api.call('POST', '/pose-search/schemas/channels/reset-field', ch(head, FieldName='Weight'))
    assert json.dumps(weight()) == default_weight
    api.undo(); assert '4.0' in json.dumps(weight())
    api.redo(); assert json.dumps(weight()) == default_weight

    # Schema-level settings.
    api.call('PATCH', '/pose-search/schemas/preprocessor', {**S, 'Preprocessor': 'Normalize'})
    api.call('PATCH', '/pose-search/schemas/preprocessor', {**S, 'Preprocessor': 'Bogus'}, ok=False)
    api.call('PATCH', '/pose-search/schemas/permutations', {**S, 'FieldName': 'NumberOfPermutations', 'ScalarValue': 3})
    api.call('PATCH', '/pose-search/schemas/permutations', {**S, 'FieldName': 'Nope', 'ScalarValue': 3}, ok=False)
    api.call('PATCH', '/pose-search/schemas/flags', {**S, 'FieldName': 'bAddDataPadding', 'bEnabled': True})
    api.call('PATCH', '/pose-search/schemas/flags', {**S, 'FieldName': 'bNope', 'bEnabled': True}, ok=False)
    settings = {x['name']: x for x in api.schema(schema)['scalar_settings']}
    assert settings['bAddDataPadding']['value'] is True, settings.get('bAddDataPadding')
    assert settings['NumberOfPermutations']['value_text'] == '3', settings.get('NumberOfPermutations')
    assert settings['DataPreprocessor']['enum_name'].endswith('Normalize'), settings.get('DataPreprocessor')

    r = api.call('POST', '/pose-search/schemas/finalize', S)
    s = api.schema(schema)
    assert s['finalized_channel_count'] >= 1 and s['cardinality'] > 0, (r, s['finalized_channel_count'], s['cardinality'])


JOG = ANIMS + '/Pistol/Jog/MF_Pistol_Jog_{0}.MF_Pistol_Jog_{0}'
MONTAGE = ANIMS + '/Pistol/MM_Pistol_Fire_Montage.MM_Pistol_Fire_Montage'
AIM_OFFSET = ANIMS + '/Pistol/Aim/AO_Pistol.AO_Pistol'


def database_stage(api, database, schema, norm, owned, root, tag):
    D = {'AssetPath': database, 'bConfirm': True}
    entries = lambda: [a['asset_path'] for a in api.database(database)['animation_assets']]
    fwd, bwd, left = JOG.format('Fwd'), JOG.format('Bwd'), JOG.format('Left')

    # Sequence/montage/blend-space insertion with guards, dry-run and undo/redo.
    api.call('POST', '/pose-search/databases/sequences', {**D, 'AnimationPath': '/Game/Nope.Nope'}, ok=False)
    api.call('POST', '/pose-search/databases/sequences', {**D, 'AnimationPath': fwd, 'bDryRun': True})
    assert entries() == []
    for seq in (fwd, bwd, left):
        api.call('POST', '/pose-search/databases/sequences', {**D, 'AnimationPath': seq})
    api.call('POST', '/pose-search/databases/sequences', {**D, 'AnimationPath': fwd}, ok=False)
    assert entries() == [fwd, bwd, left]
    api.undo(); assert entries() == [fwd, bwd]
    api.redo(); assert entries() == [fwd, bwd, left]
    api.call('POST', '/pose-search/databases/montages', {**D, 'AnimationPath': MONTAGE})
    api.call('POST', '/pose-search/databases/montages', {**D, 'AnimationPath': fwd}, ok=False)
    api.call('POST', '/pose-search/databases/blend-spaces', {**D, 'AnimationPath': AIM_OFFSET})
    assert entries() == [fwd, bwd, left, MONTAGE, AIM_OFFSET], entries()

    E = lambda i, **kw: {**D, 'AnimationIndex': i, 'AnimationPath': entries()[i], **kw}
    api.call('POST', '/pose-search/databases/entries/inspect', {**E(0), 'AnimationPath': bwd}, ok=False)
    entry = lambda i: api.call('POST', '/pose-search/databases/entries/inspect', E(i))
    # Flags, sampling range, mirror policy.
    api.call('PATCH', '/pose-search/databases/entries/flags', E(1, bEnabled=False, bDisableReselection=True))
    flags = json.dumps(entry(1))
    assert '"enabled": false' in flags.lower() or '"b_enabled": false' in flags.lower() or 'false' in flags, flags[:600]
    api.undo(); api.redo()
    api.call('PATCH', '/pose-search/databases/entries/sampling-range', E(0, RangeStart=0.1, RangeEnd=0.4))
    assert '0.4' in json.dumps(entry(0))
    api.call('PATCH', '/pose-search/databases/entries/sampling-range', E(0, RangeStart=0.5, RangeEnd=0.2), ok=False)
    api.call('PATCH', '/pose-search/databases/entries/mirror-policy', E(0, MirrorPolicy='sideways'), ok=False)
    # The project has no MirrorDataTable, so mirrored policies must be refused for every role.
    api.call('PATCH', '/pose-search/databases/entries/mirror-policy', E(0, MirrorPolicy='both'), ok=False)
    api.call('PATCH', '/pose-search/databases/entries/mirror-policy', E(0, MirrorPolicy='mirrored'), ok=False)
    assert not api.call('PATCH', '/pose-search/databases/entries/mirror-policy', E(0, MirrorPolicy='original'))['would_change']
    # Timing, sampling points, root sampling, blend-space sampling and range.
    assert entry(0) and api.call('POST', '/pose-search/databases/entries/timing', E(0))
    api.call('POST', '/pose-search/databases/entries/sampling-points', E(0))
    role = api.schema(schema)['roles'][0]['role']
    root_sample = api.call('POST', '/pose-search/databases/entries/sample-root', E(0, Role=role, ScalarValue=0.2, SampleTimes=[0.0, 0.2]))
    assert root_sample, root_sample
    api.call('POST', '/pose-search/databases/entries/sample-root', E(0, Role='NoRole', ScalarValue=0.2), ok=False)
    bs = entries().index(AIM_OFFSET)
    api.call('PATCH', '/pose-search/databases/entries/blend-sampling', E(bs, bGridSampling=True, HorizontalSamples=3, VerticalSamples=2))
    api.call('PATCH', '/pose-search/databases/entries/blend-sampling', E(bs, bGridSampling=True, HorizontalSamples=0, VerticalSamples=2), ok=False)
    api.call('PATCH', '/pose-search/databases/entries/blend-range', E(bs, RangeStart=0, RangeEnd=0.5))
    api.call('POST', '/pose-search/databases/entries/timing', E(bs, BlendX=0, BlendY=0))
    # Duplicate, move, replace, remove.
    api.call('POST', '/pose-search/databases/entries/duplicate', E(0, TargetIndex=len(entries()) + 1), ok=False)
    api.call('POST', '/pose-search/databases/entries/duplicate', E(0, TargetIndex=len(entries())))
    assert entries().count(fwd) == 2
    api.call('PATCH', '/pose-search/databases/entries/order', E(len(entries()) - 1, TargetIndex=0))
    api.call('PATCH', '/pose-search/databases/entries/animation', E(0, SourceAssetPath=JOG.format('Right')))
    assert entries()[0] == JOG.format('Right'), entries()
    api.call('DELETE', '/pose-search/databases/entries', E(0))
    assert entries() == [fwd, bwd, left, MONTAGE, AIM_OFFSET], entries()

    # Database-level settings.
    settings = lambda: {x['name']: x for x in api.database(database)['scalar_settings']}
    api.call('PATCH', '/pose-search/databases/cost-bias', {**D, 'FieldName': 'BaseCostBias', 'ScalarValue': 0.25})
    api.call('PATCH', '/pose-search/databases/cost-bias', {**D, 'FieldName': 'Nope', 'ScalarValue': 1}, ok=False)
    assert abs(settings()['BaseCostBias']['value'] - 0.25) < 1e-6
    api.call('PATCH', '/pose-search/databases/search-mode', {**D, 'SearchMode': 'VPTree'})
    api.call('PATCH', '/pose-search/databases/search-mode', {**D, 'SearchMode': 'Nope'}, ok=False)
    assert settings()['PoseSearchMode']['enum_name'].endswith('VPTree'), settings()['PoseSearchMode']
    api.call('PATCH', '/pose-search/databases/index-tuning', {**D, 'FieldName': 'KDTreeMaxLeafSize', 'ScalarValue': 12})
    api.call('PATCH', '/pose-search/databases/index-tuning', {**D, 'FieldName': 'KDTreeMaxLeafSize', 'ScalarValue': -5}, ok=False)
    api.call('PATCH', '/pose-search/databases/interval', {**D, 'FieldName': 'ExcludeFromDatabaseParameters', 'RangeStart': 0.1, 'RangeEnd': -0.1})
    assert api.database(database)['sampling_intervals']['ExcludeFromDatabaseParameters']['start_offset_seconds'] == 0.1
    api.call('PATCH', '/pose-search/databases/preview-mesh', {**D, 'SourceAssetPath': PREVIEW})
    assert api.database(database)['preview_mesh_path'] == PREVIEW
    api.call('PATCH', '/pose-search/databases/tags', {**D, 'Tags': ['Locomotion', 'Pistol']})
    assert api.database(database)['tags'] == ['Locomotion', 'Pistol']
    api.undo(); assert api.database(database)['tags'] == []
    api.redo()

    # Normalization set membership and database link.
    api.call('PATCH', '/pose-search/normalization-sets/databases', {'AssetPath': norm, 'bConfirm': True, 'DatabasePaths': [database]})
    assert database in json.dumps(api.normalization(norm))
    api.call('PATCH', '/pose-search/databases/normalization-set', {**D, 'NormalizationSetPath': norm})
    db = api.database(database)
    assert db['normalization_set_path'] == norm and db['normalization_membership_reference_matches'] == 1, db

    # Generic field tools and asset duplication.
    api.call('POST', '/pose-search/assets/inspect-field', {'AssetPath': database, 'FieldName': 'Tags'}, ok=False)
    assert '0.25' in json.dumps(api.call('POST', '/pose-search/assets/inspect-field', {'AssetPath': database, 'FieldName': 'BaseCostBias'}))
    copy = f'{root}/PSD2_{tag}.PSD2_{tag}'
    api.call('POST', '/pose-search/assets/duplicate', {'AssetPath': copy, 'SourceAssetPath': database, 'bConfirm': True})
    owned.append(copy)
    dup = api.database(copy)
    assert dup['animation_asset_count'] == 5 and dup['tags'] == ['Locomotion', 'Pistol'], dup['tags']
    bias = lambda path: {x['name']: x for x in api.database(path)['scalar_settings']}['BaseCostBias']['value']
    api.call('POST', '/pose-search/assets/reset-field', {'AssetPath': copy, 'FieldName': 'BaseCostBias', 'bConfirm': True})
    assert bias(copy) == 0, bias(copy)
    api.call('POST', '/pose-search/assets/copy-field', {'AssetPath': copy, 'FieldName': 'BaseCostBias', 'SourceAssetPath': database, 'bConfirm': True})
    assert abs(bias(copy) - 0.25) < 1e-6
    r = api.call('POST', '/pose-search/databases/index-request', {**D, 'IndexRequest': 'new'})
    api.call('POST', '/pose-search/databases/index-request', {**D, 'IndexRequest': 'bogus'}, ok=False)
    return r


def interaction_stage(api, interaction, schema, database):
    I = {'AssetPath': interaction, 'bConfirm': True}
    insp = lambda: api.call('GET', '/pose-search/interactions/definition', params={'asset_path': interaction})
    roles = lambda: [i['role'] for i in insp()['items']]
    fwd, bwd = JOG.format('Fwd'), JOG.format('Bwd')
    base_role = 'Lead'
    api.call('POST', '/pose-search/interactions/items', {**I, 'Role': 'None', 'AnimationPath': fwd}, ok=False)
    api.call('POST', '/pose-search/interactions/items', {**I, 'Role': base_role, 'AnimationPath': fwd})
    api.call('POST', '/pose-search/interactions/items', {**I, 'Role': base_role, 'AnimationPath': bwd}, ok=False)
    api.call('POST', '/pose-search/interactions/items', {**I, 'Role': 'Partner', 'AnimationPath': bwd})
    assert roles() == [base_role, 'Partner'], insp()
    api.undo(); assert roles() == [base_role]
    api.redo(); assert roles() == [base_role, 'Partner']
    it = lambda i, **kw: {**I, 'AnimationIndex': i, 'Role': roles()[i], 'AnimationPath': insp()['items'][i]['animation_path'], **kw}
    api.call('PATCH', '/pose-search/interactions/items/weight', {**it(1), 'Role': base_role, 'FieldName': 'WarpingWeightRotation', 'ScalarValue': 0.5}, ok=False)
    api.call('PATCH', '/pose-search/interactions/items/weight', it(1, FieldName='WarpingWeightRotation', ScalarValue=0.5))
    assert '0.5' in json.dumps(insp()['items'][1])
    api.call('PATCH', '/pose-search/interactions/banking-weight', {**I, 'ScalarValue': 0.75})
    assert insp()['banking_weight'] == 0.75
    api.call('PATCH', '/pose-search/interactions/items/origin', it(1, Origin={'Translation': {'X': 100, 'Y': 0, 'Z': 0}}))
    assert insp()['items'][1]['origin_text'].startswith('100.000000,0.000000,0.000000|'), insp()['items'][1]['origin_text']
    api.call('PATCH', '/pose-search/interactions/items/animation', it(1, SourceAssetPath=JOG.format('Left')))
    assert insp()['items'][1]['animation_path'] == JOG.format('Left')
    api.call('PATCH', '/pose-search/interactions/items/preview-mesh', it(1, SourceAssetPath=PREVIEW))
    api.call('PATCH', '/pose-search/interactions/items/role', it(1, NameValue=base_role), ok=False)
    api.call('PATCH', '/pose-search/interactions/items/role', it(1, NameValue='Rival'))
    api.call('POST', '/pose-search/interactions/items/duplicate', it(1, NameValue='Rival2'))
    assert roles() == [base_role, 'Rival', 'Rival2']
    api.call('PATCH', '/pose-search/interactions/items/order', it(2, TargetIndex=0))
    assert roles() == ['Rival2', base_role, 'Rival']
    api.call('DELETE', '/pose-search/interactions/items', it(0))
    api.call('PATCH', '/pose-search/interactions/items/role', it(1, NameValue='Partner'))
    assert roles() == [base_role, 'Partner']
    warp = api.call('POST', '/pose-search/interactions/evaluate-warp', {'AssetPath': interaction, 'ExpectedRoles': roles(), 'RelevantRoles': roles(),
                                                                     'ActorRootTransforms': [{}, {'Translation': {'X': 150, 'Y': 0, 'Z': 0}}], 'ScalarValue': 0})
    assert warp, warp
    api.call('POST', '/pose-search/interactions/evaluate-warp', {'AssetPath': interaction, 'ExpectedRoles': ['Wrong'], 'RelevantRoles': ['Wrong'],
                                                                'ActorRootTransforms': [{}]}, ok=False)
    # The interaction asset is a multi-animation asset; add it to the database (roles match the schema).
    for role in ('Lead', 'Partner'):
        if role not in [r['role'] for r in api.schema(schema)['roles']]:
            api.call('POST', '/pose-search/schemas/roles', {'AssetPath': schema, 'bConfirm': True, 'Role': role, 'SkeletonPath': SKELETON})
    api.call('POST', '/pose-search/databases/multi-animations', {'AssetPath': database, 'bConfirm': True, 'AnimationPath': interaction})
    assert interaction in [a['asset_path'] for a in api.database(database)['animation_assets']]


def prepare(api):
    assert not STATE.exists(), 'Run verify first'
    tag = uuid.uuid4().hex[:8]
    root = f'/Game/UE5MCP_Test/PoseSearch_{tag}'
    schema = f'{root}/PSS_{tag}.PSS_{tag}'
    database = f'{root}/PSD_{tag}.PSD_{tag}'
    norm = f'{root}/PSN_{tag}.PSN_{tag}'
    owned = []
    results = {}
    try:
        # Creation: guards, dry-run, real create.
        api.call('POST', '/pose-search/assets', {'AssetPath': schema, 'AssetKind': 'schema'}, ok=False)
        api.call('POST', '/pose-search/assets', {'AssetPath': schema, 'AssetKind': 'bogus', 'bConfirm': True}, ok=False)
        api.call('POST', '/pose-search/assets', {'AssetPath': '/Engine/X.X', 'AssetKind': 'schema', 'bConfirm': True}, ok=False)
        api.call('POST', '/pose-search/assets', {'AssetPath': schema, 'AssetKind': 'schema', 'bConfirm': True}, ok=False)
        dry = api.call('POST', '/pose-search/assets', {'AssetPath': schema, 'AssetKind': 'schema', 'SkeletonPath': SKELETON, 'bConfirm': True, 'bDryRun': True})
        assert not dry['created']
        for path, kind, extra in ((schema, 'schema', {'SkeletonPath': SKELETON}), (database, 'database', {'SchemaPath': schema}),
                                  (norm, 'normalization_set', {})):
            r = api.call('POST', '/pose-search/assets', {'AssetPath': path, 'AssetKind': kind, 'bConfirm': True, **extra})
            assert r['created'], r
            owned.append(path)
        api.call('POST', '/pose-search/assets', {'AssetPath': schema, 'AssetKind': 'schema', 'SkeletonPath': SKELETON, 'bConfirm': True}, ok=False)
        s = api.schema(schema)
        assert [r['role'] for r in s['roles']] and s['roles'][0]['skeleton'] == SKELETON, s['roles']
        assert api.database(database)['schema_path'] == schema
        results['create'] = 'schema/database/normalization set create, dry-run, duplicate and kind/path guards'

        schema_stage(api, schema)
        results['schema'] = 'ok'
        # Second schema: clear factory channels, re-initialize defaults, reassign the database schema.
        schema2 = f'{root}/PSS2_{tag}.PSS2_{tag}'
        api.call('POST', '/pose-search/assets', {'AssetPath': schema2, 'AssetKind': 'schema', 'SkeletonPath': SKELETON, 'bConfirm': True})
        owned.append(schema2)
        defaults = channels(api, schema2)
        api.call('POST', '/pose-search/schemas/channels/defaults', {'AssetPath': schema2, 'bConfirm': True}, ok=False)
        while api.schema(schema2)['channels']:
            c = api.schema(schema2)['channels'][0]
            api.call('DELETE', '/pose-search/schemas/channels', {'AssetPath': schema2, 'bConfirm': True, 'ChannelIndex': 0, 'ChannelPath': c['object_path']})
        api.call('POST', '/pose-search/schemas/channels/defaults', {'AssetPath': schema2, 'bConfirm': True})
        assert channels(api, schema2) == defaults, (channels(api, schema2), defaults)
        api.call('PATCH', '/pose-search/databases/schema', {'AssetPath': database, 'SchemaPath': schema2, 'bConfirm': True})
        assert api.database(database)['schema_path'] == schema2
        api.undo(); assert api.database(database)['schema_path'] == schema
        api.call('PATCH', '/pose-search/databases/schema', {'AssetPath': database, 'SchemaPath': '/Game/Nope.Nope', 'bConfirm': True}, ok=False)
        results['schema_defaults_and_reassign'] = 'ok'
        results['index_request'] = database_stage(api, database, schema, norm, owned, root, tag)
        results['database'] = 'ok'
        interaction = f'{root}/PSI_{tag}.PSI_{tag}'
        api.call('POST', '/pose-search/assets', {'AssetPath': interaction, 'AssetKind': 'interaction', 'bConfirm': True})
        owned.append(interaction)
        interaction_stage(api, interaction, schema, database)
        results['interaction'] = 'ok'
        results.pop('index_request')
        for path in owned:
            api.call('POST', '/assets/save', {'AssetPath': path})
        snapshots = snapshot(api, owned)
        assert not any(s.get('dirty') for s in snapshots.values()), 'saved assets still dirty'
        print(json.dumps(results, indent=1))
        print('Pose Search authoring OK; restart the editor and run verify')
    finally:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'tag': tag, 'root': root, 'owned': owned, 'snapshots': locals().get('snapshots')}), encoding='utf-8')
    return results


def snapshot(api, owned):
    out = {}
    for path in owned:
        name = path.rsplit('/', 1)[1]
        if name.startswith(('PSS_', 'PSS2_')):
            s = api.schema(path)
        elif name.startswith('PSN_'):
            s = api.normalization(path)
        elif name.startswith('PSI_'):
            s = api.call('GET', '/pose-search/interactions/definition', params={'asset_path': path})
        else:
            s = api.database(path)
        out[path] = s
    return out


def comparable(s):
    """Drop fields that legitimately differ between a live editor and a cold load."""
    s = json.loads(json.dumps(s))
    s.pop('dirty', None)
    s.pop('scope', None)
    return s


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshots'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api, state['owned'])
        for path, before in state['snapshots'].items():
            a, b = comparable(before), comparable(cold[path])
            diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            assert not diff, (path, diff, {k: (a.get(k), b.get(k)) for k in diff[:3]})
        print('Cold reload of schema roles/channels/settings, database entries/settings/tags/normalization link, '
              'normalization membership and interaction items: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    for path in reversed(state['owned']):
        httpx.post(api.base + '/assets/delete', json={'AssetPath': path}, timeout=180)
    STATE.unlink()
    print('cleaned', state['owned'])


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
