"""Level Sequence typed channel defaults, extrapolation, keys, sampling, offsets and duplication: prepare, restart, verify.

Usage: smoke_sequencer_channels_live.py prepare|verify|cleanup. Builds a saved Level Sequence with a CameraActor
possessable carrying float-property, transform and visibility sections (Float, Double and Bool channels). Every edit is
first sent with a stale channel snapshot (rejected) and as a dry run (snapshot unchanged); the final native channel
snapshots must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
PKG = '/Game/UE5MCP_Test/LS_MCP_Channels'
SEQ = PKG + '.LS_MCP_Channels'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sequencer_channels.json'
MS = SEQ + ':MovieScene_0.'
FLOAT = MS + 'MovieSceneFloatTrack_0.MovieSceneFloatSection_0'
XFORM = MS + 'MovieScene3DTransformTrack_0.MovieScene3DTransformSection_0'
VIS = MS + 'MovieSceneVisibilityTrack_0.MovieSceneVisibilitySection_0'
BYTE = MS + 'MovieSceneByteTrack_0.MovieSceneByteSection_0'
INT = MS + 'MovieSceneIntegerTrack_0.MovieSceneIntegerSection_0'
OBJ = MS + 'MovieSceneObjectPropertyTrack_0.MovieSceneObjectPropertySection_0'
SECTIONS = {'float': (FLOAT, 'Float'), 'double': (XFORM, 'Double'), 'bool': (VIS, 'Bool'), 'byte': (BYTE, 'Byte'), 'integer': (INT, 'Integer'), 'object': (OBJ, 'Object')}
# CameraActor properties: AutoActivateForPlayer is a TEnumAsByte<EAutoReceiveInput>, InputPriority an int32, Owner an AActor reference.
PROPERTY_TRACKS = (('float_property', 'CustomTimeDilation'), ('byte_property', 'AutoActivateForPlayer'), ('integer_property', 'InputPriority'), ('object_property', 'Owner'))


def close(a, b):
    return abs(a - b) < 1e-4


class Channels:
    def __init__(self, api):
        self.api = api

    def info(self, section, kind, index=0):
        page = self.api.call('POST', '/level-sequences/channels/discover', {'AssetPath': SEQ, 'ExpressionPath': section, 'Start': 0, 'Count': 128})
        ch = next(c for c in page['channels'] if c['channel_type'] == kind and c['channel_index'] == index)
        return page['section_class_path'], ch

    def snap(self, section, kind, index=0):
        return self.info(section, kind, index)[1]['native_channel_snapshot']

    def keys(self, section, kind, index=0):
        route = '/level-sequences/channels/key-policy'
        return self.api.call('POST', route, {'AssetPath': SEQ, 'ExpressionPath': section, 'Name': kind, 'Start': index,
                                             'FieldName': 'Keys', 'BlockIndex': 0, 'Count': 128})['keys']

    def edit(self, route, section, kind, body, index=0, changes=True):
        """Stale snapshot rejected, dry run leaves the snapshot alone, then the real edit; returns the response."""
        cls, ch = self.info(section, kind, index)
        base = {'AssetPath': SEQ, 'ExpressionPath': section, 'Name': kind, 'Start': index, 'ExpectedClassPath': cls,
                'ExpectedAssetSnapshot': ch['native_channel_snapshot'], 'bConfirm': True, **body}
        self.api.call('POST', route, {**base, 'ExpectedAssetSnapshot': ch['native_channel_snapshot'] + ' '}, ok=False)
        self.api.call('POST', route, {**base, 'ExpectedClassPath': '/Script/MovieSceneTracks.MovieSceneEventTriggerSection'}, ok=False)
        dry = self.api.call('POST', route, {**base, 'bDryRun': True})
        assert self.snap(section, kind, index) == ch['native_channel_snapshot'], (route, body, 'dry run changed channel')
        done = self.api.call('POST', route, {**base, 'bDryRun': False})
        after = self.snap(section, kind, index)
        assert (after != ch['native_channel_snapshot']) == changes, (route, body, changes, done)
        return done

    def bad(self, route, section, kind, body, index=0):
        cls, ch = self.info(section, kind, index)
        self.api.call('POST', route, {'AssetPath': SEQ, 'ExpressionPath': section, 'Name': kind, 'Start': index, 'ExpectedClassPath': cls,
                                      'ExpectedAssetSnapshot': ch['native_channel_snapshot'], 'bConfirm': True, 'bDryRun': False, **body}, ok=False)
        assert self.snap(section, kind, index) == ch['native_channel_snapshot'], (route, body, 'rejected edit changed channel')

    def sample(self, section, kind, frames, index=0):
        cls, ch = self.info(section, kind, index)
        return self.api.call('POST', '/level-sequences/channels/sample', {'AssetPath': SEQ, 'ExpressionPath': section, 'Name': kind, 'Start': index,
                                                                           'ExpectedClassPath': cls, 'ExpectedAssetSnapshot': ch['native_channel_snapshot'],
                                                                           'SourceOrder': frames})['samples']


KP = '/level-sequences/channels/key-policy'
DEF = '/level-sequences/channels/default'
EXT = '/level-sequences/channels/extrapolation'


def numeric(c, section, kind):
    # Defaults: set, guarded re-set, clear, set again.
    _, ch = c.info(section, kind)
    had, old = ch['has_default'], ch.get('default_value', 0)
    c.bad(DEF, section, kind, {'FieldName': 'SetDefault', 'Value': 0.5, 'bExpectedEnabled': not had, 'ExpectedValue': old})
    c.edit(DEF, section, kind, {'FieldName': 'SetDefault', 'Value': 0.5, 'bExpectedEnabled': had, 'ExpectedValue': old})
    c.edit(DEF, section, kind, {'FieldName': 'SetDefault', 'Value': 0.5, 'bExpectedEnabled': True, 'ExpectedValue': 0.5}, changes=False)
    c.edit(DEF, section, kind, {'FieldName': 'ClearDefault', 'bExpectedEnabled': True, 'ExpectedValue': 0.5})
    assert not c.info(section, kind)[1]['has_default']
    c.edit(DEF, section, kind, {'FieldName': 'SetDefault', 'Value': 0.75, 'bExpectedEnabled': False, 'ExpectedValue': 0})
    assert close(c.info(section, kind)[1]['default_value'], 0.75)
    # Extrapolation policies.
    c.bad(EXT, section, kind, {'FieldName': 'PreInfinity', 'Value': 3, 'ExpectedValue': 0})
    c.bad(EXT, section, kind, {'FieldName': 'PreInfinity', 'Value': 99, 'ExpectedValue': 4})
    c.edit(EXT, section, kind, {'FieldName': 'PreInfinity', 'Value': 3, 'ExpectedValue': 4})
    c.edit(EXT, section, kind, {'FieldName': 'PostInfinity', 'Value': 0, 'ExpectedValue': 4})
    _, ch = c.info(section, kind)
    assert (ch['pre_infinity'], ch['post_infinity']) == (3, 0), ch
    # Keys: add three, reject occupied/outside frames.
    for frame, value in ((1000, 1.0), (5000, 2.0), (9000, 0.5)):
        c.edit(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': frame, 'Value': value})
    c.bad(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': 5000, 'Value': 3})
    c.bad(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': 999999, 'Value': 3})
    k = c.keys(section, kind)
    assert [x['frame'] for x in k] == [1000, 5000, 9000] and close(k[1]['value'], 2.0), k
    # Value, interpolation, tangent mode, manual tangents.
    c.bad(KP, section, kind, {'FieldName': 'KeyValue', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Value': 4, 'ExpectedValue': 3})
    c.edit(KP, section, kind, {'FieldName': 'KeyValue', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Value': 4, 'ExpectedValue': 2})
    assert close(c.keys(section, kind)[1]['value'], 4), c.keys(section, kind)
    k = c.keys(section, kind)[0]
    c.edit(KP, section, kind, {'FieldName': 'KeyInterpolation', 'MipIndex': 0, 'ExpectedSizeX': 1000, 'Value': 1, 'ExpectedFormat': k['interpolation']})
    assert c.keys(section, kind)[0]['interpolation'] == 1
    k = c.keys(section, kind)[1]
    c.edit(KP, section, kind, {'FieldName': 'KeyTangentMode', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Value': 1, 'ExpectedFormat': k['tangent_mode']})
    k = c.keys(section, kind)[1]
    assert k['tangent_mode'] == 1, k
    comps = k['tangent_components']
    c.bad(KP, section, kind, {'FieldName': 'KeyTangents', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Color': [0.1, 0.2, 0, 0], 'ExpectedColor': comps,
                              'Value': 0, 'ExpectedFormat': k['tangent_weight_mode']})
    c.edit(KP, section, kind, {'FieldName': 'KeyTangents', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Color': [0.25, 0.25, 0, 0], 'ExpectedColor': comps,
                               'Value': 0, 'ExpectedFormat': k['tangent_weight_mode']})
    k = c.keys(section, kind)[1]
    assert close(k['tangent_components'][0], 0.25) and close(k['tangent_components'][1], 0.25), k
    # Break mode: independent arrive/leave slopes; then weighted tangents (weight mode Both) with nonnegative weights.
    c.edit(KP, section, kind, {'FieldName': 'KeyTangentMode', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Value': 2, 'ExpectedFormat': 1})
    k = c.keys(section, kind)[1]
    c.edit(KP, section, kind, {'FieldName': 'KeyTangents', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Color': [0.25, -0.5, 0, 0],
                               'ExpectedColor': k['tangent_components'], 'Value': 0, 'ExpectedFormat': k['tangent_weight_mode']})
    k = c.keys(section, kind)[1]
    assert k['tangent_mode'] == 2 and close(k['tangent_components'][0], 0.25) and close(k['tangent_components'][1], -0.5), k
    c.bad(KP, section, kind, {'FieldName': 'KeyTangents', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Color': [0.25, -0.5, -1, 0.4],
                              'ExpectedColor': k['tangent_components'], 'Value': 3, 'ExpectedFormat': k['tangent_weight_mode']})
    c.bad(KP, section, kind, {'FieldName': 'KeyTangents', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Color': [0.25, -0.5, 0.3, 0.4],
                              'ExpectedColor': k['tangent_components'], 'Value': 9, 'ExpectedFormat': k['tangent_weight_mode']})
    c.edit(KP, section, kind, {'FieldName': 'KeyTangents', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Color': [0.25, -0.5, 0.3, 0.4],
                               'ExpectedColor': k['tangent_components'], 'Value': 3, 'ExpectedFormat': k['tangent_weight_mode']})
    k = c.keys(section, kind)[1]
    assert k['tangent_weight_mode'] == 3 and [round(x, 4) for x in k['tangent_components']] == [0.25, -0.5, 0.3, 0.4], k
    # Move, delete, duplicate, offset.
    c.bad(KP, section, kind, {'FieldName': 'KeyMove', 'MipIndex': 2, 'ExpectedSizeX': 9000, 'SizeX': 5000})
    c.edit(KP, section, kind, {'FieldName': 'KeyMove', 'MipIndex': 2, 'ExpectedSizeX': 9000, 'SizeX': 8000})
    c.edit(KP, section, kind, {'FieldName': 'KeyDelete', 'MipIndex': 0, 'ExpectedSizeX': 1000, 'ExpectedValue': 1.0})
    assert [x['frame'] for x in c.keys(section, kind)] == [5000, 8000]
    c.edit('/level-sequences/channels/duplicate-key', section, kind, {'MipIndex': 0, 'ExpectedSizeX': 5000, 'SizeX': 2000})
    k = c.keys(section, kind)
    assert [x['frame'] for x in k] == [2000, 5000, 8000] and close(k[0]['value'], 4) and close(k[0]['tangent_components'][0], 0.25), k
    c.bad('/level-sequences/channels/offset', section, kind, {'SizeX': 10 ** 7})
    c.edit('/level-sequences/channels/offset', section, kind, {'SizeX': 1000})
    k = c.keys(section, kind)
    assert [x['frame'] for x in k] == [3000, 6000, 9000], k
    # Sampling uses native interpolation, defaults and extrapolation.
    s = c.sample(section, kind, [3000, 6000, 6000, 9000])
    assert [x['has_value'] for x in s] == [True] * 4 and close(s[1]['value'], 4) and close(s[1]['value'], s[2]['value']) and close(s[3]['value'], 0.5), s
    return c.snap(section, kind)


def discrete(c, section, kind, a, b, invalid):
    _, ch = c.info(section, kind)
    had, old = ch['has_default'], ch.get('default_value', 0)
    c.bad(DEF, section, kind, {'FieldName': 'SetDefault', 'Value': invalid, 'bExpectedEnabled': had, 'ExpectedValue': old})
    new = b if old == a else a
    c.edit(DEF, section, kind, {'FieldName': 'SetDefault', 'Value': new, 'bExpectedEnabled': had, 'ExpectedValue': old})
    assert c.info(section, kind)[1]['default_value'] == new
    if kind != 'Bool':
        c.edit(DEF, section, kind, {'FieldName': 'ClearDefault', 'bExpectedEnabled': True, 'ExpectedValue': new})
        assert not c.info(section, kind)[1]['has_default']
    c.bad(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': 1000, 'Value': invalid})
    for frame, value in ((1000, a), (4000, b)):
        c.edit(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': frame, 'Value': value})
    c.bad(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': 4000, 'Value': a})
    c.bad(KP, section, kind, {'FieldName': 'KeyValue', 'MipIndex': 1, 'ExpectedSizeX': 4000, 'Value': a, 'ExpectedValue': a})
    c.edit(KP, section, kind, {'FieldName': 'KeyValue', 'MipIndex': 1, 'ExpectedSizeX': 4000, 'Value': a, 'ExpectedValue': b})
    c.edit(KP, section, kind, {'FieldName': 'KeyMove', 'MipIndex': 1, 'ExpectedSizeX': 4000, 'SizeX': 7000, 'ExpectedValue': a})
    c.edit('/level-sequences/channels/duplicate-key', section, kind, {'MipIndex': 0, 'ExpectedSizeX': 1000, 'SizeX': 2000})
    c.edit(KP, section, kind, {'FieldName': 'KeyDelete', 'MipIndex': 2, 'ExpectedSizeX': 7000, 'ExpectedValue': a})
    c.edit(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': 5000, 'Value': b})
    c.edit('/level-sequences/channels/offset', section, kind, {'SizeX': 500})
    k = c.keys(section, kind)
    assert [(x['frame'], x['value']) for x in k] == [(1500, a), (2500, a), (5500, b)], k
    s = c.sample(section, kind, [1500, 4000, 6000])
    got = [int(x['integer_decimal']) if kind == 'Integer' else x['value'] for x in s]
    assert got == ([bool(a), bool(a), bool(b)] if kind == 'Bool' else [a, a, b]), s
    if kind == 'Integer':
        assert all(x['value'] is None for x in s), s
        I = '/level-sequences/channels/integer-interpolation'
        cls, ch = c.info(section, kind)
        g = {'AssetPath': SEQ, 'ExpressionPath': section, 'Start': 0, 'ExpectedClassPath': cls}
        cur = c.api.call('POST', I, {**g, 'FieldName': 'IntegerInterpolationInspect'})['interpolate_linear_keys']
        c.api.call('POST', I, {**g, 'FieldName': 'IntegerInterpolationSet', 'bEnabled': not cur, 'bExpectedEnabled': not cur,
                               'ExpectedAssetSnapshot': ch['native_channel_snapshot'], 'bConfirm': True}, ok=False)
        c.api.call('POST', I, {**g, 'FieldName': 'IntegerInterpolationSet', 'bEnabled': True, 'bExpectedEnabled': cur,
                               'ExpectedAssetSnapshot': ch['native_channel_snapshot'], 'bConfirm': True, 'bDryRun': True})
        assert c.snap(section, kind) == ch['native_channel_snapshot']
        c.api.call('POST', I, {**g, 'FieldName': 'IntegerInterpolationSet', 'bEnabled': True, 'bExpectedEnabled': cur,
                               'ExpectedAssetSnapshot': ch['native_channel_snapshot'], 'bConfirm': True, 'bDryRun': False})
        mid = int(c.sample(section, kind, [4000])[0]['integer_decimal'])
        assert min(a, b) < mid < max(a, b), ('linear integer interpolation', mid)
    return c.snap(section, kind)


def objects(c, actor):
    section, kind = OBJ, 'Object'
    page = c.api.call('POST', DEF, {'AssetPath': SEQ, 'ExpressionPath': section, 'Name': kind, 'Start': 0, 'FieldName': 'Inspect'})
    assert page['property_class_path'] == '/Script/Engine.Actor', page
    old = page['default_soft_path']
    c.bad(DEF, section, kind, {'FieldName': 'SetDefault', 'SourceTexturePath': '/Engine/EngineSounds/ReverbSettings/Cave.Cave', 'ExpectedTargetPath': old})
    c.bad(DEF, section, kind, {'FieldName': 'SetDefault', 'SourceTexturePath': actor, 'ExpectedTargetPath': old + 'x'})
    c.edit(DEF, section, kind, {'FieldName': 'SetDefault', 'SourceTexturePath': actor, 'ExpectedTargetPath': old})
    c.edit(DEF, section, kind, {'FieldName': 'ClearDefault', 'ExpectedTargetPath': actor})
    c.edit(DEF, section, kind, {'FieldName': 'SetDefault', 'SourceTexturePath': actor, 'ExpectedTargetPath': ''})
    key = lambda body: c.edit(KP, section, kind, body)
    c.bad(KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': 1000, 'SourceTexturePath': '/Engine/EngineSounds/ReverbSettings/Cave.Cave'})
    key({'FieldName': 'KeyAdd', 'SizeX': 1000, 'SourceTexturePath': actor})
    key({'FieldName': 'KeyAdd', 'SizeX': 4000, 'SourceTexturePath': ''})
    c.bad(KP, section, kind, {'FieldName': 'KeyMove', 'MipIndex': 1, 'ExpectedSizeX': 4000, 'ExpectedTargetPath': '', 'SizeX': 1000})
    key({'FieldName': 'KeyValue', 'MipIndex': 1, 'ExpectedSizeX': 4000, 'ExpectedTargetPath': '', 'SourceTexturePath': actor})
    key({'FieldName': 'KeyMove', 'MipIndex': 1, 'ExpectedSizeX': 4000, 'ExpectedTargetPath': actor, 'SizeX': 6000})
    c.edit('/level-sequences/channels/duplicate-key', section, kind, {'MipIndex': 0, 'ExpectedSizeX': 1000, 'SizeX': 2000})
    key({'FieldName': 'KeyDelete', 'MipIndex': 2, 'ExpectedSizeX': 6000, 'ExpectedTargetPath': actor})
    key({'FieldName': 'KeyAdd', 'SizeX': 5000, 'SourceTexturePath': ''})
    c.edit('/level-sequences/channels/offset', section, kind, {'SizeX': 500})
    k = c.keys(section, kind)
    assert [(x['frame'], x['soft_path']) for x in k] == [(1500, actor), (2500, actor), (5500, '')], k
    cls, ch = c.info(section, kind)
    S = '/level-sequences/channels/sample'
    body = {'AssetPath': SEQ, 'ExpressionPath': section, 'Name': kind, 'Start': 0, 'ExpectedClassPath': cls,
            'ExpectedAssetSnapshot': ch['native_channel_snapshot'], 'SourceOrder': [1500, 6000]}
    c.api.call('POST', S, {**body, 'bConfirm': False}, ok=False)
    assert c.api.call('POST', S, {**body, 'bConfirm': True, 'bDryRun': True})['sampled'] is False
    s = c.api.call('POST', S, {**body, 'bConfirm': True, 'bDryRun': False})['samples']
    assert s[0]['resolved_object_valid'] and s[0]['object_path'] == actor and not s[1]['resolved_object_valid'], s
    return c.snap(section, kind)


def prepare(api):
    assert not STATE.exists(), 'run verify or cleanup first'
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text('{}')
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG}, timeout=180).text == PKG
    guid = api.call('POST', '/level-sequences/bindings', {'AssetPath': SEQ, 'Operation': 'add', 'Name': 'Cam', 'ClassPath': '/Script/Engine.CameraActor'})['binding_guid']
    for tc, prop in (('integer_property', 'CustomTimeDilation'), ('float_property', 'InputPriority'), ('byte_property', 'InputPriority'),
                     ('object_property', 'AutoActivateForPlayer'), ('float_property', 'NoSuchProperty')):
        api.call('POST', '/level-sequences/tracks', {'AssetPath': SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackClass': tc, 'PropertyName': prop, 'PropertyPath': prop}, ok=False)
    tracks = [(tc, {'PropertyName': prop, 'PropertyPath': prop}) for tc, prop in PROPERTY_TRACKS] + [('transform', {}), ('visibility', {})]
    for tc, extra in tracks:
        ti = api.call('POST', '/level-sequences/tracks', {'AssetPath': SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackClass': tc, **extra})['track_index']
        api.call('POST', '/level-sequences/sections', {'AssetPath': SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackIndex': ti, 'Frame': 0, 'EndFrame': 30000})
    c = Channels(api)
    page = api.call('POST', '/level-sequences/channels/discover', {'AssetPath': SEQ, 'ExpressionPath': XFORM, 'Start': 0, 'Count': 4})
    assert page['double_channel_count'] == 9 and page['has_more'] and page['next_start'] == 4, page
    rest = api.call('POST', '/level-sequences/channels/discover', {'AssetPath': SEQ, 'ExpressionPath': XFORM, 'Start': 4, 'Count': 128})
    assert len(page['channels']) + len(rest['channels']) == 10 and not rest['has_more'], rest
    page = api.call('POST', '/level-sequences/channels/discover', {'AssetPath': SEQ, 'ExpressionPath': BYTE, 'Start': 0, 'Count': 8})
    assert page['channels'][0]['enum_path'] == '/Script/Engine.EAutoReceiveInput', page['channels']
    actor = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.Actor'}, timeout=180).text.strip().strip('"')
    try:
        want = {'float': numeric(c, FLOAT, 'Float'), 'double': numeric(c, XFORM, 'Double'), 'bool': discrete(c, VIS, 'Bool', 1, 0, 2),
                'byte': discrete(c, BYTE, 'Byte', 1, 2, 200), 'integer': discrete(c, INT, 'Integer', 70, -30, 2 ** 31),
                'object': objects(c, actor)}
    finally:
        httpx.request('DELETE', BASE + '/editor/actors', json={'ActorPath': actor, 'bConfirm': True}, timeout=180)
    # Undo/redo of the last native channel transaction.
    before = c.snap(VIS, 'Bool')
    k = c.keys(VIS, 'Bool')
    c.edit(KP, VIS, 'Bool', {'FieldName': 'KeyDelete', 'MipIndex': 0, 'ExpectedSizeX': k[0]['frame'], 'ExpectedValue': 1})
    api.undo()
    assert c.snap(VIS, 'Bool') == before, 'undo did not restore channel'
    api.redo()
    assert c.snap(VIS, 'Bool') != before, 'redo did not reapply'
    api.undo()
    assert c.snap(VIS, 'Bool') == want['bool']
    api.call('POST', '/assets/save', {'AssetPath': SEQ})
    STATE.write_text(json.dumps({'want': want}))
    print('Sequencer Float/Double/Bool/Byte/Integer/Object channels: defaults, extrapolation, key add/value/mode/tangents/move/delete/duplicate/offset, sampling, guards, undo/redo OK; restart and verify')


def verify(api):
    state = json.loads(STATE.read_text())
    try:
        c = Channels(api)
        for name, (section, kind) in SECTIONS.items():
            assert c.snap(section, kind) == state['want'][name], (name, c.snap(section, kind), state['want'][name])
        print('Sequencer channel snapshots survived cold restart: OK')
    finally:
        cleanup(api)


def cleanup(api):
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    phase = sys.argv[1]
    api = Api(BASE)
    if phase == 'prepare':
        try:
            prepare(api)
        except BaseException:
            cleanup(api)
            raise
    else:
        {'verify': verify, 'cleanup': cleanup}[phase](api)
