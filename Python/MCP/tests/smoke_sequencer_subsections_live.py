"""Level Sequence subsections and shots: timing/hierarchy parameters, time warp, transform origin, reference replacement, shot metadata.

Usage: smoke_sequencer_subsections_live.py prepare|verify|cleanup. Builds a parent Level Sequence with a cinematic shot (child A)
and a plain subsequence (child B) on their own tracks. Every edit is first sent with a stale snapshot (rejected) and as a dry
run (snapshot unchanged); invalid values, wrong priors, missing opt-ins and hierarchy cycles are rejected. Final parameters,
origin, references and shot metadata must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
DIR = '/Game/UE5MCP_Test/'
NAMES = ('LS_MCP_SubParent', 'LS_MCP_SubA', 'LS_MCP_SubB', 'LS_MCP_SubC')
PARENT, A, B, C = (DIR + n + '.' + n for n in NAMES)
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sequencer_subsections.json'
SHOT = PARENT + ':MovieScene_0.MovieSceneCinematicShotTrack_0.MovieSceneCinematicShotSection_0'
SUB = PARENT + ':MovieScene_0.MovieSceneSubTrack_0.MovieSceneSubSection_0'
ROUTES = {
    'params': ('/level-sequences/subsections/parameters', 'SubInspect', 'subsection_snapshot'),
    'origin': ('/level-sequences/subsections/origin', 'OriginInspect', 'origin_snapshot'),
    'reference': ('/level-sequences/subsections/reference', 'ReferenceInspect', 'subsection_snapshot'),
    'shot': ('/cinematic/shots/metadata', 'ShotInspect', 'shot_metadata_snapshot'),
}
PARAMS = ('hierarchical_bias', 'flags_mask', 'can_loop', 'start_offset_inner_ticks', 'end_offset_inner_ticks', 'first_loop_offset_inner_ticks',
          'time_warp_type', 'fixed_time_warp_tick_frame', 'fixed_play_rate')


class Subs:
    def __init__(self, api):
        self.api = api

    def inspect(self, kind, path, extra=None):
        route, field, _ = ROUTES[kind]
        return self.api.call('POST', route, {'AssetPath': PARENT, 'ExpressionPath': path, 'FieldName': field, **(extra or {})})

    def base(self, kind, path, body):
        route, _, key = ROUTES[kind]
        i = self.inspect(kind, path)
        return route, key, i[key], {'AssetPath': PARENT, 'ExpressionPath': path, 'ExpectedClassPath': i['section_class_path'],
                                    'ExpectedTargetPath': i.get('nested_sequence_path', 'None'), 'ExpectedAssetSnapshot': i[key], 'bConfirm': True, **body}

    def edit(self, kind, path, body):
        route, key, snap, b = self.base(kind, path, body)
        self.api.call('POST', route, {**b, 'ExpectedAssetSnapshot': snap + ' '}, ok=False)
        self.api.call('POST', route, {**b, 'bDryRun': True})
        assert self.inspect(kind, path)[key] == snap, (kind, body, 'dry run changed state')
        done = self.api.call('POST', route, {**b, 'bDryRun': False})
        assert self.inspect(kind, path)[key] != snap, (kind, body, done)
        return done

    def bad(self, kind, path, body):
        route, key, snap, b = self.base(kind, path, body)
        self.api.call('POST', route, {**b, 'bDryRun': False}, ok=False)
        assert self.inspect(kind, path)[key] == snap, (kind, body, 'rejected edit changed state')

    def p(self, path, field):
        return self.inspect('params', path)[field]


def state(s):
    shot, sub = s.inspect('params', SHOT), s.inspect('params', SUB)
    o = s.inspect('origin', SUB)
    m = s.inspect('shot', SHOT)
    return {'shot': {k: shot[k] for k in PARAMS} | {'nested': shot['nested_sequence_path']},
            'sub': {k: sub[k] for k in PARAMS} | {'nested': sub['nested_sequence_path']},
            'origin': {'mask': o['origin_mask'], 'defaults': [(a['has_default'], a['default_value']) for a in o['axes']]},
            'shot_meta': {k: m[k] for k in ('authored_display_name', 'effective_display_name', 'uses_sequence_name_fallback', 'thumbnail_offset_seconds')}}


def prepare(api):
    s = Subs(api)
    for n in NAMES:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': DIR + n}, timeout=180)
        assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': DIR + n}, timeout=180).text == DIR + n
    # Children need a playback range for clip offsets. UE's FMovieSceneFrameRange text import applies the value but does not
    # advance the parse buffer, so the generic setter reports trailing input; the range itself is checked instead.
    for child in (A, B, C):
        api.call('PATCH', '/level-sequences/settings', {'AssetPath': child, 'Properties': {'PlaybackRange': 'Inclusive:0:Exclusive:48000'}}, ok=False)
        info = api.call('GET', '/level-sequences/inspect', params={'asset_path': child})
        assert (info['playback_lower'], info['playback_upper']) == (0, 48000), info
    api.call('POST', '/cinematic/shots', {'AssetPath': PARENT, 'Operation': 'add', 'SequencePath': A, 'ShotName': 'Shot01', 'Frame': 0, 'Duration': 48000})
    api.call('POST', '/level-sequences/subsequences', {'AssetPath': PARENT, 'Operation': 'add', 'SequencePath': B, 'Frame': 0, 'Duration': 24000})
    # The plain subsequence lands on its own track, not on the shot track.
    subs = api.call('GET', '/level-sequences/subsequences', params={'asset_path': PARENT})['subsequences']
    assert [x['track_class'] for x in subs] == ['/Script/MovieScene.MovieSceneSubTrack'] and subs[0]['sequence_path'] == B, subs
    assert s.inspect('params', SUB)['section_class_path'] == '/Script/MovieScene.MovieSceneSubSection'

    # Parameters on the shot: bias, flags, loop, offsets, play rate.
    assert s.p(SHOT, 'hierarchical_bias') == 100
    s.bad('params', SHOT, {'FieldName': 'SubBias', 'Value': 50, 'ExpectedValue': 99})
    s.edit('params', SHOT, {'FieldName': 'SubBias', 'Value': 50, 'ExpectedValue': 100})
    s.bad('params', SHOT, {'FieldName': 'SubFlags', 'Value': 3, 'ExpectedValue': 0})
    s.bad('params', SHOT, {'FieldName': 'SubFlags', 'Value': 16, 'ExpectedValue': 0})
    s.edit('params', SHOT, {'FieldName': 'SubFlags', 'Value': 5, 'ExpectedValue': 0})
    s.bad('params', SHOT, {'FieldName': 'SubEndOffset', 'Value': 500, 'ExpectedValue': 0})
    s.edit('params', SHOT, {'FieldName': 'SubStartOffset', 'Value': 1000, 'ExpectedValue': 0})
    s.edit('params', SHOT, {'FieldName': 'SubLoop', 'bEnabled': True, 'bExpectedEnabled': False})
    s.edit('params', SHOT, {'FieldName': 'SubEndOffset', 'Value': 500, 'ExpectedValue': 0})
    s.edit('params', SHOT, {'FieldName': 'SubFirstLoopOffset', 'Value': 200, 'ExpectedValue': 0})
    s.bad('params', SHOT, {'FieldName': 'SubStartOffset', 'Value': 2000000, 'ExpectedValue': 1000})
    s.bad('params', SHOT, {'FieldName': 'SubFixedPlayRate', 'Value': 5000, 'ExpectedValue': 1})
    s.edit('params', SHOT, {'FieldName': 'SubFixedPlayRate', 'Value': 2, 'ExpectedValue': 1})

    # Fixed-time warp on the subsequence replaces the play-rate mode only with the opt-in.
    s.bad('params', SUB, {'FieldName': 'SubFixedTime', 'Value': 300, 'bEnabled': False})
    s.edit('params', SUB, {'FieldName': 'SubFixedTime', 'Value': 300, 'bEnabled': True})
    s.edit('params', SUB, {'FieldName': 'SubFixedTime', 'Value': 450, 'ExpectedValue': 300})
    assert s.p(SUB, 'fixed_time_warp_tick_frame') == 450, s.inspect('params', SUB)

    # Transform origin on the subsequence: mask, defaults; invalid bits rejected.
    s.bad('origin', SUB, {'FieldName': 'OriginMask', 'Value': 64, 'ExpectedValue': 0})
    s.edit('origin', SUB, {'FieldName': 'OriginMask', 'Value': 1 | 2 | 32, 'ExpectedValue': 0})
    s.bad('origin', SUB, {'FieldName': 'OriginDefaultSet', 'MipIndex': 0, 'Value': 2e9, 'bExpectedEnabled': False})
    s.edit('origin', SUB, {'FieldName': 'OriginDefaultSet', 'MipIndex': 0, 'Value': 150, 'bExpectedEnabled': False})
    s.edit('origin', SUB, {'FieldName': 'OriginDefaultSet', 'MipIndex': 5, 'Value': 45, 'bExpectedEnabled': False})
    s.edit('origin', SUB, {'FieldName': 'OriginDefaultSet', 'MipIndex': 4, 'Value': 10, 'bExpectedEnabled': False})
    s.edit('origin', SUB, {'FieldName': 'OriginDefaultClear', 'MipIndex': 4, 'ExpectedValue': 10, 'bExpectedEnabled': True})

    # Reference: the parent itself (cycle) rejected; B -> C needs the replacement opt-in and keeps parameters.
    for cand, opt in ((PARENT, True), (C, False)):
        r = s.inspect('reference', SUB, {'SourceTexturePath': cand}) if cand != PARENT else {}
        s.bad('reference', SUB, {'FieldName': 'ReferenceSet', 'SourceTexturePath': cand, 'ExpectedDestinationSnapshot': r.get('destination_graph_snapshot', '{}'), 'bEnabled': opt})
    before = s.p(SUB, 'fixed_time_warp_tick_frame')
    r = s.inspect('reference', SUB, {'SourceTexturePath': C})
    s.edit('reference', SUB, {'FieldName': 'ReferenceSet', 'SourceTexturePath': C, 'ExpectedDestinationSnapshot': r['destination_graph_snapshot'], 'bEnabled': True})
    assert s.inspect('params', SUB)['nested_sequence_path'] == C and s.p(SUB, 'fixed_time_warp_tick_frame') == before

    # Shot metadata: name, fallback, thumbnail offset; undo/redo.
    s.bad('shot', SHOT, {'FieldName': 'ShotName', 'Name': 'Opening', 'ExpectedLabel': 'Wrong'})
    s.edit('shot', SHOT, {'FieldName': 'ShotName', 'Name': '', 'ExpectedLabel': 'Shot01'})
    m = s.inspect('shot', SHOT)
    assert m['uses_sequence_name_fallback'] and m['effective_display_name'] == 'LS_MCP_SubA', m
    s.edit('shot', SHOT, {'FieldName': 'ShotName', 'Name': 'Opening', 'ExpectedLabel': ''})
    s.bad('shot', SHOT, {'FieldName': 'ShotThumbnail', 'Value': 50, 'ExpectedValue': 0})
    s.edit('shot', SHOT, {'FieldName': 'ShotThumbnail', 'Value': 0.5, 'ExpectedValue': 0})
    api.undo()
    assert s.inspect('shot', SHOT)['thumbnail_offset_seconds'] == 0
    api.redo()
    assert abs(s.inspect('shot', SHOT)['thumbnail_offset_seconds'] - 0.5) < 1e-6

    for n in NAMES:
        api.call('POST', '/assets/save', {'AssetPath': DIR + n})
    st = state(s)
    assert (st['shot']['hierarchical_bias'], st['shot']['flags_mask'], st['shot']['can_loop'], st['shot']['start_offset_inner_ticks'],
            st['shot']['end_offset_inner_ticks'], st['shot']['first_loop_offset_inner_ticks'], st['shot']['fixed_play_rate']) == (50, 5, True, 1000, 500, 200, 2), st
    assert st['origin'] == {'mask': 35, 'defaults': [(True, 150), (False, None), (False, None), (False, None), (False, None), (True, 45)]}, st
    assert st['shot_meta']['authored_display_name'] == 'Opening' and st['sub']['nested'] == C, st
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    print('shot parameters, fixed-time warp, origin, reference and shot metadata prepared; saved')


def verify(api):
    got = json.loads(json.dumps(state(Subs(api))))
    want = json.loads(STATE.read_text())
    assert got == want, (got, want)
    print('subsection/shot parameters, origin, reference and shot metadata identical after cold reload')
    cleanup(api)


def cleanup(api):
    for n in NAMES:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': DIR + n}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[sys.argv[1]](Api(BASE))
