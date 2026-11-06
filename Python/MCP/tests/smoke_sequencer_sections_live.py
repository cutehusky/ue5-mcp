"""Level Sequence section and track settings: blend, completion, easing, pre/post-roll, evaluation, priority, muting.

Usage: smoke_sequencer_sections_live.py prepare|verify|cleanup. Builds a saved Level Sequence with a CameraActor possessable
whose float-property track holds two overlapping sections. Every edit is first sent with a stale snapshot (rejected) and as a
dry run (snapshot unchanged); invalid values and wrong priors are rejected. The final settings must survive a cold restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
PKG = '/Game/UE5MCP_Test/LS_MCP_Sections'
SEQ = PKG + '.LS_MCP_Sections'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sequencer_sections.json'
TRACK = SEQ + ':MovieScene_0.MovieSceneFloatTrack_0'
S0 = TRACK + '.MovieSceneFloatSection_0'
S1 = TRACK + '.MovieSceneFloatSection_1'
CURVE = '/Engine/Tutorial/ContentIntroCurve.ContentIntroCurve'
SEC = '/level-sequences/sections/'
# route, inspect FieldName, snapshot key
ROUTES = {
    'blend': (SEC + 'blend-type', 'BlendInspect', 'blend_snapshot'),
    'completion': (SEC + 'completion-mode', 'CompletionInspect', 'completion_snapshot'),
    'easing': (SEC + 'easing', 'EasingInspect', 'easing_snapshot'),
    'builtin': (SEC + 'easing/built-in', 'BuiltInInspect', 'easing_snapshot'),
    'external': (SEC + 'easing/external-curve', 'ExternalInspect', 'easing_snapshot'),
    'auto': (SEC + 'easing/automatic', 'AutoEasingInspect', 'track_easing_snapshot'),
    'roll': (SEC + 'pre-post-roll', 'RollInspect', 'roll_snapshot'),
    'priority': (SEC + 'overlap-priority', 'PriorityInspect', 'priority_snapshot'),
    'evaluation': ('/level-sequences/tracks/evaluation-policy', 'Inspect', 'evaluation_snapshot'),
    'mute': ('/level-sequences/tracks/mute', 'Inspect', 'mute_snapshot'),
}


class Settings:
    def __init__(self, api):
        self.api = api

    def inspect(self, kind, path, extra=None):
        route, field, _ = ROUTES[kind]
        return self.api.call('POST', route, {'AssetPath': SEQ, 'ExpressionPath': path, 'FieldName': field, **(extra or {})})

    def base(self, kind, path, body, extra=None):
        route, _, key = ROUTES[kind]
        i = self.inspect(kind, path, extra)
        cls = i.get('section_class_path', i.get('track_class_path'))
        return route, key, i[key], {'AssetPath': SEQ, 'ExpressionPath': path, 'ExpectedClassPath': cls, 'ExpectedAssetSnapshot': i[key], 'bConfirm': True, **(extra or {}), **body}

    def edit(self, kind, path, body, extra=None):
        """Stale snapshot rejected, dry run leaves the snapshot alone, then the real edit must change it."""
        route, key, snap, b = self.base(kind, path, body, extra)
        self.api.call('POST', route, {**b, 'ExpectedAssetSnapshot': snap + ' '}, ok=False)
        self.api.call('POST', route, {**b, 'bDryRun': True})
        assert self.inspect(kind, path, extra)[key] == snap, (kind, body, 'dry run changed state')
        done = self.api.call('POST', route, {**b, 'bDryRun': False})
        assert self.inspect(kind, path, extra)[key] != snap, (kind, body, 'edit did not change state', done)
        return done

    def bad(self, kind, path, body, extra=None):
        route, key, snap, b = self.base(kind, path, body, extra)
        self.api.call('POST', route, {**b, 'bDryRun': False}, ok=False)
        assert self.inspect(kind, path, extra)[key] == snap, (kind, body, 'rejected edit changed state')


def state(s):
    e0, e1 = s.inspect('easing', S0), s.inspect('easing', S1)
    b0, x0 = s.inspect('builtin', S0), s.inspect('external', S0)
    r0, ev = s.inspect('roll', S0), s.inspect('evaluation', TRACK)
    m = s.inspect('mute', TRACK, {'Start': 3})
    pick = lambda d, ks: {k: d[k] for k in ks}
    ease = ('manual_in', 'manual_out', 'manual_in_tick_frames', 'manual_out_tick_frames', 'automatic_in_tick_frames', 'automatic_out_tick_frames', 'effective_in_tick_frames', 'effective_out_tick_frames')
    return {
        'blend': [s.inspect('blend', p)['blend_type'] for p in (S0, S1)],
        'completion': [s.inspect('completion', p)['completion_mode'] for p in (S0, S1)],
        'easing0': pick(e0, ease), 'easing1': pick(e1, ease),
        'ease_in_type': [b0['ease_in']['class_path'], b0['ease_in'].get('type_name')],
        'ease_out_class': x0['ease_out']['class_path'],
        'roll': [r0['pre_roll_tick_frames'], r0['post_roll_tick_frames']],
        'priority': [s.inspect('priority', p)['overlap_priority'] for p in (S0, S1)],
        'evaluation': pick(ev, ('evaluate_nearest_section', 'evaluate_in_preroll', 'evaluate_in_postroll')),
        'mute': pick(m, ('persistent_disabled', 'persistent_row_disabled', 'persistent_disabled_rows')),
    }


def prepare(api):
    s = Settings(api)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG}, timeout=180).text == PKG
    guid = api.call('POST', '/level-sequences/bindings', {'AssetPath': SEQ, 'Operation': 'add', 'Name': 'Cam', 'ClassPath': '/Script/Engine.CameraActor'})['binding_guid']
    api.call('POST', '/level-sequences/tracks', {'AssetPath': SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackClass': 'float_property',
                                                 'PropertyName': 'CustomTimeDilation', 'PropertyPath': 'CustomTimeDilation'})
    for lo, hi in ((0, 30000), (20000, 50000)):
        api.call('POST', '/level-sequences/sections', {'AssetPath': SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackIndex': 0, 'Frame': lo, 'EndFrame': hi})

    # Blend type: unsupported value and wrong prior rejected; Additive on S0.
    b = s.inspect('blend', S0)
    assert b['has_blend_type'] and b['blend_type'] == 1 and [x['value'] for x in b['supported_blend_types']] == [1, 2, 4, 8, 16], b
    s.bad('blend', S0, {'FieldName': 'BlendSet', 'Value': 3, 'bExpectedEnabled': True, 'ExpectedValue': 1})
    s.bad('blend', S0, {'FieldName': 'BlendSet', 'Value': 2, 'bExpectedEnabled': True, 'ExpectedValue': 4})
    s.edit('blend', S0, {'FieldName': 'BlendSet', 'Value': 2, 'bExpectedEnabled': True, 'ExpectedValue': 1})

    # Completion mode: ProjectDefault -> KeepState -> RestoreState; invalid mode rejected.
    assert s.inspect('completion', S0)['completion_mode'] == 2
    s.bad('completion', S0, {'FieldName': 'CompletionSet', 'Value': 9, 'ExpectedValue': 2})
    s.edit('completion', S0, {'FieldName': 'CompletionSet', 'Value': 0, 'ExpectedValue': 2})
    s.edit('completion', S0, {'FieldName': 'CompletionSet', 'Value': 1, 'ExpectedValue': 0})

    # Manual easing durations; longer than the section rejected.
    s.bad('easing', S0, {'FieldName': 'EasingIn', 'SizeX': 40000})
    s.bad('easing', S0, {'FieldName': 'EasingIn', 'SizeX': -1})
    s.edit('easing', S0, {'FieldName': 'EasingIn', 'SizeX': 1500})
    s.edit('easing', S0, {'FieldName': 'EasingOut', 'SizeX': 2000})
    e = s.inspect('easing', S0)
    assert (e['manual_in'], e['manual_in_tick_frames'], e['manual_out'], e['manual_out_tick_frames'], e['effective_in_tick_frames']) == (True, 1500, True, 2000, 1500), e

    # Built-in preset QuadIn on the in side; bad preset and wrong prior function rejected.
    fn = s.inspect('builtin', S0)['ease_in']['object_path']
    s.bad('builtin', S0, {'FieldName': 'BuiltInIn', 'Value': 99, 'ExpectedTargetPath': fn})
    s.bad('builtin', S0, {'FieldName': 'BuiltInIn', 'Value': 4, 'ExpectedTargetPath': fn + 'X'})
    s.edit('builtin', S0, {'FieldName': 'BuiltInIn', 'Value': 4, 'ExpectedTargetPath': fn})
    assert s.inspect('builtin', S0)['ease_in']['type_name'] == 'QuadIn'

    # External CurveFloat on the out side: wrong curve snapshot rejected; replacing the built-in needs the opt-in.
    x = s.inspect('external', S0, {'SourceTexturePath': CURVE})
    out = x['ease_out']['function_path']
    curve = {'SourceTexturePath': CURVE, 'ExpectedDestinationSnapshot': x['destination_curve_snapshot'], 'ExpectedTargetPath': out}
    s.bad('external', S0, {'FieldName': 'ExternalOut', **curve, 'ExpectedDestinationSnapshot': '()', 'bEnabled': True})
    s.bad('external', S0, {'FieldName': 'ExternalOut', **curve, 'bEnabled': False})
    s.edit('external', S0, {'FieldName': 'ExternalOut', **curve, 'bEnabled': True})
    assert s.inspect('external', S0)['ease_out']['class_path'] == '/Script/MovieScene.MovieSceneEasingExternalCurve'

    # Automatic easing: recompute the track; S1's in side overlaps S0 by 10000 ticks. Wrong prior rejected.
    s.bad('auto', S1, {'FieldName': 'AutoEasingIn', 'bEnabled': True, 'bExpectedEnabled': False})
    a = s.edit('auto', S1, {'FieldName': 'AutoEasingIn', 'bEnabled': True, 'bExpectedEnabled': True})
    e1 = s.inspect('easing', S1)
    assert a['recomputed'] and e1['automatic_in_tick_frames'] == 10000 and e1['effective_in_tick_frames'] == 10000, (a, e1)

    # Pre/post-roll: out-of-range and wrong priors rejected.
    s.bad('roll', S0, {'FieldName': 'RollSet', 'SizeX': 2000000, 'SizeY': 0, 'ExpectedSizeX': 0, 'ExpectedSizeY': 0})
    s.bad('roll', S0, {'FieldName': 'RollSet', 'SizeX': 500, 'SizeY': 700, 'ExpectedSizeX': 1, 'ExpectedSizeY': 0})
    s.edit('roll', S0, {'FieldName': 'RollSet', 'SizeX': 500, 'SizeY': 700, 'ExpectedSizeX': 0, 'ExpectedSizeY': 0})

    # Overlap priority on S1, with undo/redo; peers report the overlap.
    p = s.inspect('priority', S0)
    assert [x['range_overlaps'] for x in p['peers']] == [False, True], p
    s.bad('priority', S1, {'FieldName': 'PrioritySet', 'Value': 5, 'ExpectedValue': 1})
    s.edit('priority', S1, {'FieldName': 'PrioritySet', 'Value': 5, 'ExpectedValue': 0})
    api.undo()
    assert s.inspect('priority', S1)['overlap_priority'] == 0
    api.redo()
    assert s.inspect('priority', S1)['overlap_priority'] == 5

    # Track evaluation policy.
    s.bad('evaluation', TRACK, {'FieldName': 'bEvaluateInPreroll', 'bEnabled': True, 'bExpectedEnabled': True})
    s.bad('evaluation', TRACK, {'FieldName': 'bBogus', 'bEnabled': True, 'bExpectedEnabled': False})
    s.edit('evaluation', TRACK, {'FieldName': 'bEvalNearestSection', 'bEnabled': True, 'bExpectedEnabled': False})
    s.edit('evaluation', TRACK, {'FieldName': 'bEvaluateInPreroll', 'bEnabled': True, 'bExpectedEnabled': False})

    # Persistent muting: row 3 off, whole track off and back on.
    row = {'Start': 3}
    s.bad('mute', TRACK, {'FieldName': 'Row', 'bEnabled': True, 'bExpectedEnabled': True}, row)
    s.edit('mute', TRACK, {'FieldName': 'Row', 'bEnabled': True, 'bExpectedEnabled': False}, row)
    s.edit('mute', TRACK, {'FieldName': 'Track', 'bEnabled': True, 'bExpectedEnabled': False}, row)
    assert s.inspect('mute', TRACK, row)['effective_track_disabled']
    s.edit('mute', TRACK, {'FieldName': 'Track', 'bEnabled': False, 'bExpectedEnabled': True}, row)

    api.call('POST', '/assets/save', {'AssetPath': PKG})
    st = state(s)
    assert st['blend'] == [2, 1] and st['completion'] == [1, 2] and st['roll'] == [500, 700] and st['priority'] == [0, 5], st
    assert st['ease_in_type'][1] == 'QuadIn' and st['mute'] == {'persistent_disabled': False, 'persistent_row_disabled': True, 'persistent_disabled_rows': [3]}, st
    assert st['evaluation'] == {'evaluate_nearest_section': True, 'evaluate_in_preroll': True, 'evaluate_in_postroll': False}, st
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    print('blend, completion, manual/built-in/external/automatic easing, roll, priority, evaluation and mute prepared; saved')


def verify(api):
    got = json.loads(json.dumps(state(Settings(api))))
    want = json.loads(STATE.read_text())
    assert got == want, (got, want)
    print('section and track settings identical after cold reload')
    cleanup(api)


def cleanup(api):
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[sys.argv[1]](Api(BASE))
