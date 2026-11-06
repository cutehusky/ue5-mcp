"""Level Sequence folders and binding tags: create, rename, color, sort, move, membership, removal, tag groups: prepare, restart, verify.

Usage: smoke_sequencer_folders_live.py prepare|verify|cleanup. Builds a saved Level Sequence with a CameraActor possessable and a
master event track, then a folder tree with track/binding membership and binding tag groups. Every edit is first sent with a
stale snapshot (rejected) and as a dry run (snapshot unchanged). The tree, memberships and tags must survive a cold restart and
pass structural validation.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
PKG = '/Game/UE5MCP_Test/LS_MCP_Folders'
SEQ = PKG + '.LS_MCP_Folders'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sequencer_folders.json'
TRACK = SEQ + ':MovieScene_0.MovieSceneEventTrack_0'
FOLDERS = '/level-sequences/folders'
TAGS = '/level-sequences/bindings/tags'
SNAP = {FOLDERS: 'folder_snapshot', TAGS: 'binding_tags_snapshot'}


class Tree:
    def __init__(self, api):
        self.api = api

    def inspect(self, route=FOLDERS):
        return self.api.call('POST', route, {'AssetPath': SEQ, 'FieldName': 'Inspect', 'BlockIndex': 0, 'Count': 128})

    def base(self, route, body):
        i = self.inspect(route)
        return i[SNAP[route]], {'AssetPath': SEQ, 'ExpectedClassPath': i['sequence_class_path'], 'ExpectedAssetSnapshot': i[SNAP[route]], 'bConfirm': True, **body}

    def edit(self, body, route=FOLDERS):
        snap, b = self.base(route, body)
        self.api.call('POST', route, {**b, 'ExpectedAssetSnapshot': snap + ' '}, ok=False)
        self.api.call('POST', route, {**b, 'ExpectedClassPath': '/Script/Engine.Blueprint'}, ok=False)
        self.api.call('POST', route, {**b, 'bDryRun': True})
        assert self.inspect(route)[SNAP[route]] == snap, (body, 'dry run changed state')
        done = self.api.call('POST', route, {**b, 'bDryRun': False})
        assert self.inspect(route)[SNAP[route]] != snap, (body, done)
        return done

    def bad(self, body, route=FOLDERS):
        snap, b = self.base(route, body)
        self.api.call('POST', route, {**b, 'bDryRun': False}, ok=False)
        assert self.inspect(route)[SNAP[route]] == snap, (body, 'rejected edit changed state')

    def folders(self):
        return {f['name']: f for f in self.inspect()['folders']}

    def path(self, name):
        return self.folders()[name]['path']

    def validate(self):
        return self.api.call('POST', FOLDERS + '/validate', {'AssetPath': SEQ, 'BlockIndex': 0, 'Count': 128})


def state(t):
    fs = t.folders()
    names = {f['path']: n for n, f in fs.items()}
    return {'folders': {n: {'parent': names.get(f['parent_path'], f['parent_path']), 'rgba': f['rgba_bytes'], 'sort': f['sorting_order'],
                            'tracks': len(f['tracks']), 'bindings': f['binding_guids']} for n, f in fs.items()},
            'tags': {g['name'] if 'name' in g else g['tag_name']: g for g in t.inspect(TAGS)['groups']}}


def track_signature(api):
    snap = api.call('POST', '/level-sequences/events/track-policy', {'AssetPath': SEQ, 'ExpressionPath': TRACK, 'FieldName': 'Inspect'})['track_snapshot']
    return json.loads(snap)['signature']


def prepare(api):
    t = Tree(api)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG}, timeout=180).text == PKG
    guid = api.call('POST', '/level-sequences/bindings', {'AssetPath': SEQ, 'Operation': 'add', 'Name': 'Cam', 'ClassPath': '/Script/Engine.CameraActor'})['binding_guid']
    guid2 = api.call('POST', '/level-sequences/bindings', {'AssetPath': SEQ, 'Operation': 'add', 'Name': 'Cam2', 'ClassPath': '/Script/Engine.CameraActor'})['binding_guid']
    api.call('POST', '/level-sequences/tracks', {'AssetPath': SEQ, 'Operation': 'add', 'TrackClass': 'event'})

    # Create roots and children; duplicate sibling names and path separators rejected.
    t.edit({'FieldName': 'Create', 'Name': 'Shots'})
    t.edit({'FieldName': 'Create', 'Name': 'Props'})
    t.bad({'FieldName': 'Create', 'Name': 'Shots'})
    t.bad({'FieldName': 'Create', 'Name': 'a/b'})
    t.edit({'FieldName': 'Create', 'Name': 'Cams', 'OwnerAssetPath': t.path('Shots')})
    t.edit({'FieldName': 'Create', 'Name': 'Temp', 'OwnerAssetPath': t.path('Shots')})
    assert t.folders()['Cams']['parent_path'] == t.path('Shots')

    # Rename, color, sort; wrong priors rejected.
    t.bad({'FieldName': 'Rename', 'ExpressionPath': t.path('Props'), 'Name': 'Shots', 'ExpectedLabel': 'Props'})
    t.bad({'FieldName': 'Rename', 'ExpressionPath': t.path('Props'), 'Name': 'Set', 'ExpectedLabel': 'Nope'})
    t.edit({'FieldName': 'Rename', 'ExpressionPath': t.path('Props'), 'Name': 'Set', 'ExpectedLabel': 'Props'})
    t.bad({'FieldName': 'Color', 'ExpressionPath': t.path('Set'), 'Color': [300, 0, 0, 255], 'ExpectedColor': [255, 255, 255, 255]})
    t.edit({'FieldName': 'Color', 'ExpressionPath': t.path('Set'), 'Color': [200, 40, 10, 255], 'ExpectedColor': [255, 255, 255, 255]})
    sort = t.folders()['Cams']['sorting_order']
    t.edit({'FieldName': 'Sort', 'ExpressionPath': t.path('Cams'), 'Value': 7, 'ExpectedValue': sort})

    # Membership: master track into Set, both bindings into Cams; then move one binding to root (unfiled).
    sig = track_signature(api)
    t.bad({'FieldName': 'AssignTrack', 'OwnerAssetPath': t.path('Set'), 'ExpectedTargetPath': 'None', 'SourceTexturePath': TRACK, 'ExpectedSourceId': '0' * 32})
    t.edit({'FieldName': 'AssignTrack', 'OwnerAssetPath': t.path('Set'), 'ExpectedTargetPath': 'None', 'SourceTexturePath': TRACK, 'ExpectedSourceId': sig})
    for g in (guid, guid2):
        t.edit({'FieldName': 'AssignBinding', 'OwnerAssetPath': t.path('Cams'), 'ExpectedTargetPath': 'None', 'ActorGuid': g})
    t.bad({'FieldName': 'AssignBinding', 'OwnerAssetPath': t.path('Set'), 'ExpectedTargetPath': 'None', 'ActorGuid': guid})
    t.bad({'FieldName': 'AssignBinding', 'OwnerAssetPath': t.path('Set'), 'ExpectedTargetPath': 'None', 'ActorGuid': '1' * 32})
    t.edit({'FieldName': 'AssignBinding', 'OwnerAssetPath': '', 'ExpectedTargetPath': t.path('Cams'), 'ActorGuid': guid2})
    f = t.folders()
    assert len(f['Set']['tracks']) == 1 and f['Cams']['binding_guids'] == [guid], f

    # Moves: Cams to root, cycle (Shots under its own child Temp) rejected, Temp under Set.
    t.bad({'FieldName': 'Move', 'ExpressionPath': t.path('Shots'), 'ExpectedTargetPath': 'None', 'OwnerAssetPath': t.path('Temp')})
    t.edit({'FieldName': 'Move', 'ExpressionPath': t.path('Cams'), 'ExpectedTargetPath': t.path('Shots'), 'OwnerAssetPath': ''})
    t.edit({'FieldName': 'Move', 'ExpressionPath': t.path('Temp'), 'ExpectedTargetPath': t.path('Shots'), 'OwnerAssetPath': t.path('Set')})
    f = t.folders()
    assert f['Cams']['parent_path'] == 'None' and f['Temp']['parent_path'] == f['Set']['path'] and f['Cams']['binding_guids'] == [guid], f

    # RemoveEmpty: non-empty Set rejected; empty Temp removed; undo/redo.
    t.bad({'FieldName': 'RemoveEmpty', 'ExpressionPath': t.path('Set'), 'ExpectedTargetPath': 'None'})
    t.edit({'FieldName': 'RemoveEmpty', 'ExpressionPath': t.path('Temp'), 'ExpectedTargetPath': t.path('Set')})
    assert 'Temp' not in t.folders()
    api.undo()
    assert 'Temp' in t.folders()
    api.redo()
    assert 'Temp' not in t.folders()

    # Binding tags: create, tag both bindings, untag, rename, remove (populated removal needs opt-in).
    t.edit({'FieldName': 'Create', 'Name': 'Heroes', 'bExpectedEnabled': False}, TAGS)
    t.bad({'FieldName': 'Create', 'Name': 'Heroes', 'bExpectedEnabled': True}, TAGS)
    for g in (guid, guid2):
        t.edit({'FieldName': 'TagRootBinding', 'Name': 'Heroes', 'ActorGuid': g, 'bExpectedEnabled': True}, TAGS)
    t.bad({'FieldName': 'TagRootBinding', 'Name': 'Heroes', 'ActorGuid': '1' * 32, 'bExpectedEnabled': True}, TAGS)
    t.edit({'FieldName': 'UntagRootBinding', 'Name': 'Heroes', 'ActorGuid': guid2, 'bExpectedEnabled': True}, TAGS)
    t.edit({'FieldName': 'Create', 'Name': 'Extras', 'bExpectedEnabled': False}, TAGS)
    t.edit({'FieldName': 'TagRootBinding', 'Name': 'Extras', 'ActorGuid': guid2, 'bExpectedEnabled': True}, TAGS)
    t.bad({'FieldName': 'RemoveTag', 'Name': 'Extras', 'bExpectedEnabled': True, 'bEnabled': False}, TAGS)
    t.edit({'FieldName': 'RemoveTag', 'Name': 'Extras', 'bExpectedEnabled': True, 'bEnabled': True}, TAGS)
    t.bad({'FieldName': 'RenameTag', 'Name': 'Heroes', 'OutputName': 'Leads', 'bExpectedEnabled': True, 'bEnabled': False}, TAGS)
    t.edit({'FieldName': 'RenameTag', 'Name': 'Heroes', 'OutputName': 'Leads', 'bExpectedEnabled': True, 'bEnabled': True}, TAGS)
    groups = t.inspect(TAGS)['groups']
    assert len(groups) == 1 and 'Leads' in json.dumps(groups) and guid in json.dumps(groups).upper() and guid2 not in json.dumps(groups).upper(), groups

    v = t.validate()
    assert v['reachable_folder_structure_valid'] and v['reachable_scan_complete'] and v['issue_count'] == 0 and v['visited_folder_count'] == 3, v
    api.call('POST', '/assets/save', {'AssetPath': PKG})
    s = state(t)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))
    print(json.dumps(s, indent=1))
    print('3 folders with track/binding membership and 1 binding tag prepared; saved')


def verify(api):
    t = Tree(api)
    got = json.loads(json.dumps(state(t)))
    want = json.loads(STATE.read_text())
    assert got == want, (got, want)
    v = t.validate()
    assert v['reachable_folder_structure_valid'] and v['issue_count'] == 0, v
    print('folders, memberships and binding tags identical after cold reload; validation clean')
    cleanup(api)


def cleanup(api):
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[sys.argv[1]](Api(BASE))
