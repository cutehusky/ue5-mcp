"""Level Sequence marked frames: add, move, delete, metadata, fences and list locking: prepare, restart, verify.

Usage: smoke_sequencer_markers_live.py prepare|verify|cleanup. Every edit is first sent with a stale snapshot (rejected) and as
a dry run (snapshot unchanged); duplicate labels, occupied frames and edits to a locked list are rejected. The final markers
and lock must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
PKG = '/Game/UE5MCP_Test/LS_MCP_Markers'
SEQ = PKG + '.LS_MCP_Markers'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sequencer_markers.json'
ROUTE = '/level-sequences/marked-frames'
FIELDS = ('tick_frame', 'label', 'comment', 'determinism_fence', 'inclusive_time', 'use_custom_color')


class Markers:
    def __init__(self, api):
        self.api = api

    def inspect(self):
        return self.api.call('POST', ROUTE, {'AssetPath': SEQ, 'FieldName': 'Inspect', 'BlockIndex': 0, 'Count': 128})

    def base(self, body):
        i = self.inspect()
        return i['marked_frames_snapshot'], {'AssetPath': SEQ, 'ExpectedClassPath': i['sequence_class_path'],
                                             'ExpectedAssetSnapshot': i['marked_frames_snapshot'], 'bConfirm': True, **body}

    def edit(self, body):
        snap, b = self.base(body)
        self.api.call('POST', ROUTE, {**b, 'ExpectedAssetSnapshot': snap + ' '}, ok=False)
        self.api.call('POST', ROUTE, {**b, 'ExpectedClassPath': '/Script/Engine.Blueprint'}, ok=False)
        self.api.call('POST', ROUTE, {**b, 'bDryRun': True})
        assert self.inspect()['marked_frames_snapshot'] == snap, (body, 'dry run changed markers')
        done = self.api.call('POST', ROUTE, {**b, 'bDryRun': False})
        assert self.inspect()['marked_frames_snapshot'] != snap, (body, done)
        return done

    def bad(self, body):
        snap, b = self.base(body)
        self.api.call('POST', ROUTE, {**b, 'bDryRun': False}, ok=False)
        assert self.inspect()['marked_frames_snapshot'] == snap, (body, 'rejected edit changed markers')

    def marks(self):
        return self.inspect()['marked_frames']


def state(m):
    i = m.inspect()
    return {'locked': i['marked_frames_locked'],
            'markers': [{k: x[k] for k in FIELDS} | {'rgba': [round(c, 3) for c in x['custom_linear_rgba']]} for x in i['marked_frames']]}


def meta(index, frame, prior, label, comment='', color=(0, 1, 1, 0.4), flags=(0, 0, 0)):
    return {'FieldName': 'Metadata', 'MipIndex': index, 'ExpectedSizeX': frame, 'ExpectedLabel': prior, 'Name': label,
            'OutputName': comment, 'Color': list(color), 'SourceOrder': list(flags)}


def prepare(api):
    m = Markers(api)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG}, timeout=180).text == PKG
    assert m.inspect()['total'] == 0

    # Add out of order (native sort), including a negative frame; duplicates rejected.
    for frame, label in ((5000, 'Mid'), (1000, 'Start'), (-2000, 'Pre'), (9000, 'End')):
        m.edit({'FieldName': 'Add', 'SizeX': frame, 'Name': label, 'OutputName': label.lower()})
    m.bad({'FieldName': 'Add', 'SizeX': 5000, 'Name': 'Other', 'OutputName': ''})
    m.bad({'FieldName': 'Add', 'SizeX': 7000, 'Name': 'Mid', 'OutputName': ''})
    m.bad({'FieldName': 'Add', 'SizeX': 7000, 'Name': '', 'OutputName': ''})
    assert [(x['tick_frame'], x['label']) for x in m.marks()] == [(-2000, 'Pre'), (1000, 'Start'), (5000, 'Mid'), (9000, 'End')]

    # Move keeps metadata and re-sorts; wrong source label and occupied destination rejected.
    m.bad({'FieldName': 'Move', 'MipIndex': 3, 'ExpectedSizeX': 9000, 'ExpectedLabel': 'Mid', 'SizeX': 3000})
    m.bad({'FieldName': 'Move', 'MipIndex': 3, 'ExpectedSizeX': 9000, 'ExpectedLabel': 'End', 'SizeX': 1000})
    m.edit({'FieldName': 'Move', 'MipIndex': 3, 'ExpectedSizeX': 9000, 'ExpectedLabel': 'End', 'SizeX': 3000})
    k = m.marks()
    assert [(x['tick_frame'], x['label'], x['comment']) for x in k] == [(-2000, 'Pre', 'pre'), (1000, 'Start', 'start'), (3000, 'End', 'end'), (5000, 'Mid', 'mid')], k

    # Delete.
    m.edit({'FieldName': 'Delete', 'MipIndex': 0, 'ExpectedSizeX': -2000, 'ExpectedLabel': 'Pre'})
    assert [x['label'] for x in m.marks()] == ['Start', 'End', 'Mid']

    # Metadata: custom color, fence and inclusive flags; duplicate label and out-of-range color rejected.
    m.bad(meta(2, 5000, 'Mid', 'Start'))
    m.bad(meta(2, 5000, 'Mid', 'Mid2', color=(1.5, 0, 0, 1)))
    m.edit(meta(2, 5000, 'Mid', 'Fence', 'determinism fence', color=(1, 0.5, 0, 1), flags=(1, 1, 1)))
    m.edit(meta(0, 1000, 'Start', 'Start', 'renamed comment'))
    x = m.marks()
    assert (x[2]['label'], x[2]['use_custom_color'], x[2]['determinism_fence'], x[2]['inclusive_time'], x[2]['tick_frame']) == ('Fence', True, True, True, 5000), x
    assert [round(c, 3) for c in x[2]['custom_linear_rgba']] == [1, 0.5, 0, 1] and x[0]['comment'] == 'renamed comment', x

    # Undo/redo the metadata edit.
    api.undo()
    assert m.marks()[0]['comment'] == 'start'
    api.redo()
    assert m.marks()[0]['comment'] == 'renamed comment'

    # Lock: edits refused while locked; unlock and lock again.
    m.bad({'FieldName': 'Lock', 'bEnabled': True, 'bExpectedEnabled': True})
    m.edit({'FieldName': 'Lock', 'bEnabled': True, 'bExpectedEnabled': False})
    m.bad({'FieldName': 'Add', 'SizeX': 7000, 'Name': 'Locked', 'OutputName': ''})
    m.bad(meta(0, 1000, 'Start', 'Nope'))
    m.edit({'FieldName': 'Lock', 'bEnabled': False, 'bExpectedEnabled': True})
    m.edit({'FieldName': 'Add', 'SizeX': 7000, 'Name': 'Late', 'OutputName': ''})
    m.edit({'FieldName': 'Lock', 'bEnabled': True, 'bExpectedEnabled': False})

    api.call('POST', '/assets/save', {'AssetPath': PKG})
    s = state(m)
    assert s['locked'] and [x['label'] for x in s['markers']] == ['Start', 'End', 'Fence', 'Late'], s
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))
    print(json.dumps(s, indent=1))
    print('4 markers with metadata and locked list prepared; saved')


def verify(api):
    got = state(Markers(api))
    want = json.loads(STATE.read_text())
    assert got == want, (got, want)
    print(f'{len(got["markers"])} markers, metadata and lock identical after cold reload')
    cleanup(api)


def cleanup(api):
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[sys.argv[1]](Api(BASE))
