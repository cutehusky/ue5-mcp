"""Camera-cut metadata, camera-cut track policy and ranges, Take Recorder metadata; prepare, restart, verify.

prepare: on a new level sequence with two spawnable cameras and two cuts, author cut binding/lock/thumbnail, the
track's blend and auto-manage policies, rearrangement and a cut range (stale snapshot rejected, dry run unchanged,
real edit); create take metadata and author slate, take number, description, timing, timecodes, timestamp and level
origin, lock/unlock; create and remove metadata on a second sequence; save both.
verify (fresh editor): reload, compare the snapshot, then delete the sequences.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
PKG, PKG2 = '/Game/UE5MCP_Test/LS_MCP_Cuts', '/Game/UE5MCP_Test/LS_MCP_Takes2'
SEQ, SEQ2 = PKG + '.LS_MCP_Cuts', PKG2 + '.LS_MCP_Takes2'
TRACK = SEQ + ':MovieScene_0.MovieSceneCameraCutTrack_0'
CUT0, CUT1 = TRACK + '.MovieSceneCameraCutSection_0', TRACK + '.MovieSceneCameraCutSection_1'
LEVEL = '/Game/ThirdPerson/Lvl_ThirdPerson.Lvl_ThirdPerson'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'camera_cuts_takes.json'
SEC = 24000  # camera-cut frames are tick-resolution frames (24000 per second)


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:400])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:300])
    return r['errorMessage']


def strip(d):
    return {k: v for k, v in d.items() if k not in ('scope', 'dry_run', 'written', 'would_change', 'package_dirty', 'changed', 'created', 'removed')}


# ---------------------------------------------------------------- camera cuts
def cut(path):
    return ok(m.cinematic_camera_cut_metadata, SEQ, path)


def track():
    return ok(m.cinematic_camera_cut_track_policy, SEQ, TRACK)


def cuts():
    return J(m.list_level_sequence_camera_cuts(SEQ))['camera_cuts']


def cut_edit(path, op, **kw):
    i = cut(path)
    g = dict(expected_section_class_path=i['section_class_path'], expected_camera_cut_snapshot=i['camera_cut_snapshot'])
    bad(m.cinematic_camera_cut_metadata, SEQ, path, op, **kw, expected_section_class_path=i['section_class_path'],
        expected_camera_cut_snapshot=i['camera_cut_snapshot'] + ' ', confirm=True, dry_run=False)
    ok(m.cinematic_camera_cut_metadata, SEQ, path, op, **kw, **g, confirm=True, dry_run=True)
    assert cut(path) == i, (op, 'dry run changed it')
    ok(m.cinematic_camera_cut_metadata, SEQ, path, op, **kw, **g, confirm=True, dry_run=False)
    return cut(path)


def track_edit(op, **kw):
    t = track()
    g = dict(expected_track_class_path=t['track_class_path'], expected_camera_track_snapshot=t['camera_track_snapshot'])
    bad(m.cinematic_camera_cut_track_policy, SEQ, TRACK, op, **kw, expected_track_class_path=t['track_class_path'],
        expected_camera_track_snapshot=t['camera_track_snapshot'] + ' ', allow_layout_changes=True, confirm=True, dry_run=False)
    ok(m.cinematic_camera_cut_track_policy, SEQ, TRACK, op, **kw, **g, allow_layout_changes=True, confirm=True, dry_run=True)
    assert track() == t, (op, 'dry run changed it')
    return ok(m.cinematic_camera_cut_track_policy, SEQ, TRACK, op, **kw, **g, allow_layout_changes=True, confirm=True, dry_run=False)


def camera_stage():
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG}, timeout=180).text.strip('"') == PKG
    add = lambda n: httpx.post(BASE + '/level-sequences/bindings', json={'AssetPath': SEQ, 'Operation': 'add_spawnable',
                                                                        'ClassPath': '/Script/Engine.CameraActor', 'Name': n}, timeout=300).json()['binding_guid']
    g1, g2 = add('CamA'), add('CamB')
    for frame in (0, SEC):
        ok(m.edit_level_sequence_camera_cut, SEQ, 'add', g1, frame, SEC)
    i = cut(CUT0)
    assert i['section_class_path'].endswith('MovieSceneCameraCutSection'), i
    t = track()
    assert t['section_count'] == 2 and t['auto_manage'] and not t['can_blend'], t
    # Binding: replacing the current binding needs the opt-in; clearing and re-binding.
    cur = i['local_binding_guid'] if 'local_binding_guid' in i else g1
    bad(m.cinematic_camera_cut_metadata, SEQ, CUT0, 'Binding', local_binding_guid=g2, enabled=False,
        expected_section_class_path=i['section_class_path'], expected_camera_cut_snapshot=i['camera_cut_snapshot'], confirm=True, dry_run=False)
    bad(m.cinematic_camera_cut_metadata, SEQ, CUT0, 'Binding', local_binding_guid='0' * 31 + '1', enabled=True,
        expected_section_class_path=i['section_class_path'], expected_camera_cut_snapshot=i['camera_cut_snapshot'], confirm=True, dry_run=False)
    after = cut_edit(CUT0, 'Binding', local_binding_guid=g2, enabled=True)
    assert g2 in json.dumps(after) and cur in json.dumps(i), after
    assert [c['camera_binding_guid'] for c in cuts()] == [g2, g1], cuts()
    # Lock previous camera and thumbnail offset.
    after = cut_edit(CUT1, 'LockPrevious', enabled=True, expected_enabled=False)
    assert after['lock_previous_camera'] is True, after
    after = cut_edit(CUT1, 'Thumbnail', thumbnail_offset_seconds=0.5, expected_thumbnail_offset_seconds=0)
    assert abs(after['thumbnail_offset_seconds'] - 0.5) < 1e-6, after
    i = cut(CUT1)
    bad(m.cinematic_camera_cut_metadata, SEQ, CUT1, 'Thumbnail', thumbnail_offset_seconds=1.5, expected_thumbnail_offset_seconds=0.5,
        expected_section_class_path=i['section_class_path'], expected_camera_cut_snapshot=i['camera_cut_snapshot'], confirm=True, dry_run=False)  # beyond the cut
    # Track policy: blending on, auto-manage off, a range edit with gaps allowed, then auto-manage back on rearranges.
    track_edit('CanBlend', enabled=True, expected_enabled=False)
    assert track()['can_blend'] is True
    track_edit('AutoManage', enabled=False, expected_enabled=True)
    assert track()['auto_manage'] is False
    t = track()
    lo, hi = SEC, 2 * SEC
    bad(m.set_cinematic_camera_cut_range, SEQ, CUT1, 30000, 60000, lo, hi, cut(CUT1)['section_class_path'], t['camera_track_snapshot'],
        allow_layout_changes=False, confirm=True, dry_run=False)                       # opt-in missing
    bad(m.set_cinematic_camera_cut_range, SEQ, CUT1, 30000, 30000, lo, hi, cut(CUT1)['section_class_path'], t['camera_track_snapshot'],
        allow_layout_changes=True, confirm=True, dry_run=False)                        # empty range
    ok(m.set_cinematic_camera_cut_range, SEQ, CUT1, 30000, 60000, lo, hi, cut(CUT1)['section_class_path'], t['camera_track_snapshot'],
       allow_layout_changes=True, confirm=True, dry_run=True)
    assert cuts()[1]['lower'] == SEC, cuts()
    ok(m.set_cinematic_camera_cut_range, SEQ, CUT1, 30000, 60000, lo, hi, cut(CUT1)['section_class_path'], t['camera_track_snapshot'],
       allow_layout_changes=True, confirm=True, dry_run=False)
    assert [(c['lower'], c['upper']) for c in cuts()] == [(0, SEC), (30000, 60000)], cuts()
    # Re-enabling auto-management rearranges natively and closes the gap.
    track_edit('AutoManage', enabled=True, expected_enabled=False)
    c = cuts()
    assert track()['auto_manage'] and c[0]['upper'] == c[1]['lower'], c
    track_edit('Rearrange')
    assert len(cuts()) == 2
    httpx.post(BASE + '/assets/save', json={'AssetPath': SEQ}, timeout=300)


# ---------------------------------------------------------------- take metadata
def take(seq=SEQ):
    return ok(m.cinematic_take_metadata, seq)


def take_edit(op, seq=SEQ, **kw):
    t = take(seq)
    g = dict(metadata_path=t['metadata_path'], expected_metadata_exists=t['metadata_exists'],
             expected_sequence_class_path=t['sequence_class_path'], expected_take_metadata_snapshot=t['take_metadata_snapshot'])
    bad(m.cinematic_take_metadata, seq, op, **{**g, 'expected_take_metadata_snapshot': t['take_metadata_snapshot'] + ' '}, **kw, confirm=True, dry_run=False)
    ok(m.cinematic_take_metadata, seq, op, **g, **kw, confirm=True, dry_run=True)
    assert take(seq) == t, (op, 'dry run changed it')
    ok(m.cinematic_take_metadata, seq, op, **g, **kw, confirm=True, dry_run=False)
    return take(seq)


def timing_edit(op, **kw):
    t = take()
    g = (SEQ, t['metadata_path'], op, t['sequence_class_path'])
    bad(m.set_cinematic_take_timing_metadata, *g, t['take_metadata_snapshot'] + ' ', **kw, confirm=True, dry_run=False)
    ok(m.set_cinematic_take_timing_metadata, *g, t['take_metadata_snapshot'], **kw, confirm=True, dry_run=True)
    assert take() == t
    ok(m.set_cinematic_take_timing_metadata, *g, t['take_metadata_snapshot'], **kw, confirm=True, dry_run=False)
    return take()


def provenance_edit(op, **kw):
    t = take()
    g = (SEQ, t['metadata_path'], op, t['sequence_class_path'])
    bad(m.set_cinematic_take_provenance_metadata, *g, t['take_metadata_snapshot'] + ' ', **kw, confirm=True, dry_run=False)
    ok(m.set_cinematic_take_provenance_metadata, *g, t['take_metadata_snapshot'], **kw, confirm=True, dry_run=True)
    assert take() == t
    ok(m.set_cinematic_take_provenance_metadata, *g, t['take_metadata_snapshot'], **kw, confirm=True, dry_run=False)
    return take()


def take_stage():
    t = take()
    assert not t['metadata_exists'] and t['metadata_path'] == 'None', t
    bad(m.cinematic_take_metadata, SEQ, 'Slate', metadata_path='None', expected_metadata_exists=False, expected_sequence_class_path=t['sequence_class_path'],
        expected_take_metadata_snapshot=t['take_metadata_snapshot'], text='A', confirm=True, dry_run=False)   # no metadata yet
    t = take_edit('Create')
    assert t['metadata_exists'] and t['metadata_path'] != 'None', t
    bad(m.cinematic_take_metadata, SEQ, 'Create', metadata_path=t['metadata_path'], expected_metadata_exists=False,
        expected_sequence_class_path=t['sequence_class_path'], expected_take_metadata_snapshot=t['take_metadata_snapshot'], confirm=True, dry_run=False)
    t = take_edit('Slate', text='MCP_Slate_A')
    assert t['slate'] == 'MCP_Slate_A', t
    t = take_edit('TakeNumber', number=7)
    assert t['take_number'] == 7, t
    bad(m.cinematic_take_metadata, SEQ, 'TakeNumber', metadata_path=t['metadata_path'], expected_metadata_exists=True,
        expected_sequence_class_path=t['sequence_class_path'], expected_take_metadata_snapshot=t['take_metadata_snapshot'], number=0, confirm=True, dry_run=False)
    t = take_edit('Description', text='Take authored by MCP')
    assert t['description'] == 'Take authored by MCP', t
    # Manual rate and timecodes need from-timecode off first.
    if t['frame_rate_from_timecode']:
        bad(m.set_cinematic_take_timing_metadata, SEQ, t['metadata_path'], 'FrameRate', t['sequence_class_path'], t['take_metadata_snapshot'],
            rate_numerator=25, rate_denominator=1, confirm=True, dry_run=False)
        t = take_edit('FrameRateFromTimecode', enabled=False)
    assert t['frame_rate_from_timecode'] is False, t
    t = timing_edit('FrameRate', rate_numerator=25, rate_denominator=1)
    assert (t['authored_rate_numerator'], t['authored_rate_denominator']) == (25, 1), t
    t = timing_edit('Duration', duration_frames=250, subframe=0.5)
    assert t['duration_frames'] == 250 and t['duration_subframe'] == 0.5, t
    t = timing_edit('TimecodeIn', timecode_hmsf=[1, 2, 3, 4])
    assert [t['timecode_in'][k] for k in ('hours', 'minutes', 'seconds', 'frames')] == [1, 2, 3, 4], t['timecode_in']
    t = timing_edit('TimecodeOut', timecode_hmsf=[1, 2, 13, 4])
    assert t['timecode_out']['seconds'] == 13, t['timecode_out']
    tt = take()
    bad(m.set_cinematic_take_timing_metadata, SEQ, tt['metadata_path'], 'TimecodeIn', tt['sequence_class_path'], tt['take_metadata_snapshot'],
        timecode_hmsf=[24, 0, 0, 0], confirm=True, dry_run=False)
    bad(m.set_cinematic_take_timing_metadata, SEQ, tt['metadata_path'], 'Duration', tt['sequence_class_path'], tt['take_metadata_snapshot'],
        duration_frames=10, subframe=1.0, confirm=True, dry_run=False)
    # Provenance: timestamp presence change needs the opt-in.
    bad(m.set_cinematic_take_provenance_metadata, SEQ, tt['metadata_path'], 'Timestamp', tt['sequence_class_path'], tt['take_metadata_snapshot'],
        value='2026-11-02T10:00:00Z', allow_state_change=False, confirm=True, dry_run=False)
    t = provenance_edit('Timestamp', value='2026-11-02T12:30:00+02:00', allow_state_change=True)
    assert t['recorded_timestamp_present'] and t['timestamp_iso8601_utc'].startswith('2026-11-02T10:30:00'), t   # offset normalized to UTC
    t = provenance_edit('LevelOrigin', value=LEVEL, expected_prior_origin_path='')
    assert t['level_origin']['soft_path'].startswith('/Game/ThirdPerson/Lvl_ThirdPerson'), t['level_origin']
    bad(m.set_cinematic_take_provenance_metadata, SEQ, take()['metadata_path'], 'PresetOrigin', take()['sequence_class_path'], take()['take_metadata_snapshot'],
        value=LEVEL, expected_prior_origin_path='', confirm=True, dry_run=False)          # not a TakePreset
    # Lock: a locked take refuses edits; unlocking is the only allowed change.
    t = take_edit('Lock', enabled=True)
    assert t['locked'] is True, t
    bad(m.cinematic_take_metadata, SEQ, 'Slate', metadata_path=t['metadata_path'], expected_metadata_exists=True,
        expected_sequence_class_path=t['sequence_class_path'], expected_take_metadata_snapshot=t['take_metadata_snapshot'], text='X', confirm=True, dry_run=False)
    # Sources: no source list on a sequence that was never recorded.
    s = ok(m.inspect_cinematic_take_sources, SEQ)
    assert not s['sources_exist'] and s['total'] == 0, s
    httpx.post(BASE + '/assets/save', json={'AssetPath': SEQ}, timeout=300)


def removal_stage():
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG2}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG2}, timeout=180).text.strip('"') == PKG2
    t = take_edit('Create', seq=SEQ2)
    args = (SEQ2, t['metadata_path'], t['sequence_class_path'], t['take_metadata_snapshot'])
    bad(m.remove_cinematic_take_metadata, *args, allow_metadata_discard=False, confirm=True, dry_run=False)
    bad(m.remove_cinematic_take_metadata, SEQ2, t['metadata_path'], t['sequence_class_path'], t['take_metadata_snapshot'] + ' ', allow_metadata_discard=True, confirm=True, dry_run=False)
    ok(m.remove_cinematic_take_metadata, *args, allow_metadata_discard=True, confirm=True, dry_run=True)
    assert take(SEQ2)['metadata_exists']
    ok(m.remove_cinematic_take_metadata, *args, allow_metadata_discard=True, confirm=True, dry_run=False)
    assert not take(SEQ2)['metadata_exists'], take(SEQ2)
    httpx.post(BASE + '/assets/save', json={'AssetPath': SEQ2}, timeout=300)


def snapshot():
    return {'cuts': cuts(), 'cut0': strip(cut(CUT0)), 'cut1': strip(cut(CUT1)), 'track': strip(track()), 'take': strip(take()),
            'take2': strip(take(SEQ2))}


def prepare():
    cleanup()
    camera_stage()
    take_stage()
    removal_stage()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1))
    print('camera cuts and takes prepared; sequences saved')


def verify():
    st = json.loads(STATE.read_text())
    for p in (SEQ, SEQ2):
        httpx.get(BASE + '/assets/describe', params={'asset_path': p}, timeout=300)
    got, want = json.loads(json.dumps(snapshot())), st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('camera cuts and take metadata identical after cold reload')
    cleanup()


def cleanup():
    for p in (PKG, PKG2):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
