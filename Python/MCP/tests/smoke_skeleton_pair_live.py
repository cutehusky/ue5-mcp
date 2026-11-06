"""Skeleton tools that need a mesh owned by the edited Skeleton, plus virtual-bone/socket dependency edge cases.

Uses the SkelPair fixture (SK_MCP_Pair and SKM_MCP_Pair, whose Skeleton is SK_MCP_Pair; see create_fixtures.py) and an
owned AnimSequence created on it. The fixture itself is edited, so prepare snapshots its original structure and cleanup
removes everything this test adds, then asserts the fixture is back to that snapshot.
prepare: retarget sources from the mesh, stored-pose reset, animation retarget selection and consumer migration, mesh
socket customize/promote and shared-socket propagation, virtual-bone cascades and dependency renames, preview-attachment
lifecycle, compatibility add/remove, hierarchy comparison, reference-pose readback, blend-profile references; save.
verify (fresh editor): compare cold-loaded state, then clean up.
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
SK = '/Game/UE5MCP_Fixtures/SkelPair/SK_MCP_Pair.SK_MCP_Pair'
ME = '/Game/UE5MCP_Fixtures/SkelPair/SKM_MCP_Pair.SKM_MCP_Pair'
ORIG = '/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin'
AS = '/Game/UE5MCP_Test/AS_MCP_Pair.AS_MCP_Pair'
PROP = '/Engine/BasicShapes/Cube.Cube'
TEMP_PROP = '/Game/UE5MCP_Test/SM_MCP_TempProp'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'skeleton_pair.json'
ORIGINAL = PROJECT / 'Saved' / 'UE5MCP_Test' / 'skeleton_pair_original.json'
Y = dict(confirm=True)


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:500])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:400])
    return r['errorMessage']


def skel():
    return ok(m.inspect_skeleton_structure, SK)


def names(key, field='name'):
    return [x[field] for x in skel()[key]]


def mesh():
    return ok(m.inspect_mesh_sockets, ME)


def mesh_socket(name):
    return [s for s in mesh()['sockets'] if s['name'] == name]


def structural():
    d = skel()
    return {k: d[k] for k in ('sockets', 'virtual_bones', 'retarget_sources', 'compatible_skeletons', 'preview_attachments',
                              'blend_profiles', 'curve_metadata', 'use_compatible_retarget_modes')}


def retarget_stage():
    bad(m.edit_skeleton_retarget_source, SK, 'MCP_FromMesh', '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple', **Y)
    assert ok(m.edit_skeleton_retarget_source, SK, 'MCP_FromMesh', ME, confirm=True, dry_run=True)['dry_run']
    assert 'MCP_FromMesh' not in names('retarget_sources', 'pose_name')
    r = ok(m.edit_skeleton_retarget_source, SK, 'MCP_FromMesh', ME, **Y)
    assert r['transform_count'] == 161, r
    bad(m.edit_skeleton_retarget_source, SK, 'MCP_FromMesh', ME, **Y)                                      # create existing
    ok(m.edit_skeleton_retarget_source, SK, 'MCP_FromMesh', ME, operation='refresh', **Y)
    ref = {b['name']: b for b in ok(m.inspect_skeleton_retarget_pose, SK, 'MCP_FromMesh', ['spine_01', 'spine_02'])['bones']}
    ok(m.edit_skeleton_stored_retarget_pose, SK, 'MCP_FromMesh', [{'Bone': 'spine_01', 'Rotation': {'Pitch': 0, 'Yaw': 0, 'Roll': 20}},
                                                               {'Bone': 'spine_02', 'Location': {'X': 1, 'Y': 2, 'Z': 3}}], **Y)
    edited = {b['name']: b for b in ok(m.inspect_skeleton_retarget_pose, SK, 'MCP_FromMesh', ['spine_01', 'spine_02'])['bones']}
    assert edited != ref
    bad(m.reset_skeleton_stored_retarget_pose, SK, 'MCP_FromMesh', ['spine_01', 'spine_01'], **Y)
    ok(m.reset_skeleton_stored_retarget_pose, SK, 'MCP_FromMesh', ['spine_01'], children=True, confirm=True, dry_run=True)
    assert {b['name']: b for b in ok(m.inspect_skeleton_retarget_pose, SK, 'MCP_FromMesh', ['spine_01', 'spine_02'])['bones']} == edited
    ok(m.reset_skeleton_stored_retarget_pose, SK, 'MCP_FromMesh', ['spine_01'], children=True, **Y)          # spine_02 is a descendant
    # Reset restores the Skeleton reference pose (the FBX-imported mesh pose differs from it by float noise).
    ref_local = {b['name']: b['reference_local'] for b in skel()['bones'] if b['name'] in ('spine_01', 'spine_02')}
    reset = {b['name']: b['local_transform'] for b in ok(m.inspect_skeleton_retarget_pose, SK, 'MCP_FromMesh', ['spine_01', 'spine_02'])['bones']}
    assert reset == ref_local, (reset, ref_local)

    # Animation selection: named source, source mesh, effective inspection, consumer-aware rename/delete.
    m.create_animation_sequence(AS.split('.')[0], SK, ME)
    bad(m.set_animation_named_retarget_source, AS, 'NoSuchPose', **Y)
    ok(m.set_animation_named_retarget_source, AS, 'MCP_FromMesh', **Y)
    q = ok(m.inspect_animation_retarget_source, AS, ['spine_01'])
    assert q['named_source'] == 'MCP_FromMesh' and q['named_source_exists'] and q['source_mesh'] == '', q
    del_msg = bad(m.delete_skeleton_retarget_source, SK, 'MCP_FromMesh', **Y)                                # consumer blocks
    assert 'AS_MCP_Pair' in del_msg or 'consumer' in del_msg.lower() or 'referenc' in del_msg.lower(), del_msg
    plan = ok(m.rename_skeleton_retarget_source, SK, 'MCP_FromMesh', 'MCP_MeshPose', confirm=True, dry_run=True)
    assert 'AS_MCP_Pair' in json.dumps(plan), plan
    ok(m.rename_skeleton_retarget_source, SK, 'MCP_FromMesh', 'MCP_MeshPose', **Y)
    q = ok(m.inspect_animation_retarget_source, AS, ['spine_01'])
    assert q['named_source'] == 'MCP_MeshPose' and q['named_source_exists'], q                              # consumer migrated
    bad(m.set_animation_retarget_source_mesh, AS, '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple', **Y)
    ok(m.set_animation_retarget_source_mesh, AS, ME, **Y)
    q = ok(m.inspect_animation_retarget_source, AS, ['spine_01'])
    assert q['source_mesh'] == ME and q['named_source'] == 'None', q                                       # named source cleared
    ok(m.set_animation_named_retarget_source, AS, 'MCP_MeshPose', **Y)
    assert httpx.post(BASE + '/assets/save', json={'AssetPath': AS}, timeout=120).status_code == 200


def socket_stage():
    # Shared Skeleton sockets appear on the mesh immediately (propagation), customize copies one into a mesh override.
    ok(m.edit_skeleton_socket, SK, 'MCP_Shared', 'hand_r', location={'X': 1, 'Y': 2, 'Z': 3}, **Y)
    s = mesh_socket('MCP_Shared')
    assert s and s[0]['owner'] == 'skeleton' and not s[0]['overridden'], s
    bad(m.customize_mesh_socket, ME, 'NoSuchSocket', **Y)
    assert ok(m.customize_mesh_socket, ME, 'MCP_Shared', confirm=True, dry_run=True)['dry_run']
    assert not any(x['owner'] == 'mesh' for x in mesh_socket('MCP_Shared'))
    ok(m.customize_mesh_socket, ME, 'MCP_Shared', **Y)
    rows = mesh_socket('MCP_Shared')
    assert any(x['owner'] == 'mesh' for x in rows), rows
    bad(m.customize_mesh_socket, ME, 'MCP_Shared', **Y)                                                     # already overridden
    # Promote a mesh-only socket to the Skeleton, removing the local copy.
    ok(m.edit_mesh_socket, ME, 'MCP_Local', 'hand_l', **Y)
    bad(m.promote_mesh_socket, ME, 'MCP_Shared', **Y)                                                       # shared name exists
    assert ok(m.promote_mesh_socket, ME, 'MCP_Local', remove_local=True, confirm=True, dry_run=True)['dry_run']
    assert 'MCP_Local' not in names('sockets')
    ok(m.promote_mesh_socket, ME, 'MCP_Local', remove_local=True, **Y)
    assert 'MCP_Local' in names('sockets')
    rows = mesh_socket('MCP_Local')
    assert rows and all(x['owner'] == 'skeleton' for x in rows), rows


def virtual_bone_stage():
    vbs = lambda: {v['name']: v for v in skel()['virtual_bones']}
    ok(m.create_skeleton_virtual_bone, SK, 'hand_l', 'hand_r', **Y)
    a = next(iter(vbs()))
    ok(m.create_skeleton_virtual_bone, SK, a, 'foot_l', **Y)                                                 # depends on A
    b = next(n for n in vbs() if n != a)
    # A virtual target used to crash the editor (native rebuild indexes targets in raw-bone space); now refused.
    assert 'raw bone' in bad(m.create_skeleton_virtual_bone, SK, 'spine_01', a, **Y)
    ok(m.edit_skeleton_socket, SK, 'MCP_OnVB', a, **Y)                                                       # socket on A
    ok(m.edit_skeletal_preview_attachment, SK, PROP, b, **Y)                                                 # preview on B
    # Rename A: B's source and the socket's parent follow.
    bad(m.rename_skeleton_virtual_bone, SK, a, 'NoPrefix', **Y)
    ok(m.rename_skeleton_virtual_bone, SK, a, 'VB MCP_Root', **Y)
    v = vbs()
    assert 'VB MCP_Root' in v and a not in v, list(v)
    assert v[b]['source'] == 'VB MCP_Root', v[b]
    assert next(s for s in skel()['sockets'] if s['name'] == 'MCP_OnVB')['bone'] == 'VB MCP_Root'
    # Delete A without cascade: dependents block. Socket on A blocks even with cascade until moved.
    bad(m.delete_skeleton_virtual_bones, SK, ['VB MCP_Root'], **Y)
    ok(m.delete_skeleton_socket, SK, 'MCP_OnVB', **Y)
    plan = ok(m.delete_skeleton_virtual_bones, SK, ['VB MCP_Root'], cascade=True, confirm=True, dry_run=True)
    assert len(vbs()) == 2 and b in json.dumps(plan), plan                                               # cascade includes B
    ok(m.delete_skeleton_virtual_bones, SK, ['VB MCP_Root'], cascade=True, **Y)
    assert vbs() == {}, vbs()
    assert skel()['preview_attachments']['count'] == 0, skel()['preview_attachments']                      # B's preview removed
    assert skel()['diagnostics']['structurally_valid'] and skel()['diagnostics']['issue_count'] == 0


def misc_stage():
    # Preview attachment on a temporary asset that is then deleted: removal by stored path without loading.
    httpx.post(BASE + '/assets/duplicate', json={'AssetPath': PROP, 'DestinationPath': TEMP_PROP}, timeout=120)
    temp = TEMP_PROP + '.' + TEMP_PROP.rsplit('/', 1)[1]
    ok(m.edit_skeletal_preview_attachment, SK, temp, 'MCP_Shared', **Y)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': TEMP_PROP}, timeout=120)
    entries = skel()['preview_attachments']['entries']
    assert len(entries) == 1, entries
    ok(m.edit_skeletal_preview_attachment, SK, temp, 'MCP_Shared', operation='remove', **Y)
    assert skel()['preview_attachments']['count'] == 0
    ok(m.edit_skeletal_preview_attachment, SK, PROP, 'MCP_Shared', **Y)                                       # kept for reload
    # Compatibility add/remove; remove uses the stored soft path.
    ok(m.edit_skeleton_compatibility, SK, ORIG, **Y)
    assert not ok(m.edit_skeleton_compatibility, SK, ORIG, **Y)['would_change']                              # duplicate: no-op
    ok(m.edit_skeleton_compatibility, SK, ORIG, operation='remove', **Y)
    assert skel()['compatible_skeleton_count'] == 0
    ok(m.edit_skeleton_compatibility, SK, ORIG, **Y)
    # Hierarchy comparison both directions; an added virtual bone does not change raw-bone comparison.
    c = ok(m.compare_skeleton_hierarchies, SK, ORIG)
    assert c['shared_bone_count'] == 161 and c['difference_count'] == 0 and c['source_hierarchy_covered'], c
    bad(m.compare_skeleton_hierarchies, SK, '/Game/Nope/SK.SK')
    # Reference pose readback in the structure: composed component-space transforms are available and finite.
    bones = {b['name']: b for b in skel()['bones']}
    assert all(b['reference_component_available'] and b['reference_component']['finite'] for b in bones.values())
    pelvis, spine = bones['pelvis'], bones['spine_01']
    assert spine['parent_index'] == pelvis['index'] and spine['reference_component'] != spine['reference_local']
    assert abs(bones['root']['reference_component']['location'][2] - bones['root']['reference_local']['location'][2]) < 1e-6
    # Blend-profile references: a fresh profile has no referencers.
    ok(m.create_skeleton_blend_profile, SK, 'MCP_Profile', **Y)
    refs = ok(m.inspect_skeleton_blend_profile_references, SK, 'MCP_Profile')
    assert refs['loaded_referencer_count'] == 0, refs                         # the undo buffer is not an asset user
    ok(m.create_skeleton_blend_profile, SK, 'MCP_Temp', **Y)
    # Assets that depend on the Skeleton package (the pair mesh, the sequence) still require the explicit override.
    assert 'allow' in bad(m.delete_skeleton_blend_profile, SK, 'MCP_Temp', **Y)
    ok(m.delete_skeleton_blend_profile, SK, 'MCP_Temp', allow_referenced=True, **Y)
    assert 'MCP_Temp' not in names('blend_profiles')
    ok(m.create_skeleton_blend_profile, SK, 'MCP_Temp', **Y)                  # the deleted name is reusable at once
    ok(m.delete_skeleton_blend_profile, SK, 'MCP_Temp', allow_referenced=True, **Y)


def snapshot():
    return {'skeleton': structural(), 'mesh': mesh(), 'anim': ok(m.inspect_animation_retarget_source, AS, ['spine_01', 'spine_02'])}


def save_all():
    for p in (SK, ME, AS):
        assert httpx.post(BASE + '/assets/save', json={'AssetPath': p.split('.')[0]}, timeout=120).status_code == 200


def prepare():
    if not ORIGINAL.exists():
        ORIGINAL.parent.mkdir(parents=True, exist_ok=True)
        ORIGINAL.write_text(json.dumps(structural()), encoding='utf-8')
    cleanup(check=False)
    retarget_stage()
    socket_stage()
    virtual_bone_stage()
    misc_stage()
    save_all()
    snap = json.loads(json.dumps(snapshot()))
    for k in ('dirty',):
        snap['mesh'].pop(k, None); snap['anim'].pop(k, None)
    STATE.write_text(json.dumps(snap, indent=1), encoding='utf-8')
    print('Skeleton pair authoring prepared and saved')


def verify():
    want = json.loads(STATE.read_text(encoding='utf-8'))
    got = json.loads(json.dumps(snapshot()))
    for k in ('dirty',):
        got['mesh'].pop(k, None); got['anim'].pop(k, None)
    for part in want:
        assert got[part] == want[part], json.dumps({'part': part, 'got': got[part], 'want': want[part]})[:3000]
    print('Skeleton pair state identical after cold reload')
    cleanup(check=True)


def cleanup(check=True):
    """Remove everything this test adds to the fixture and delete the owned sequence."""
    original = json.loads(ORIGINAL.read_text(encoding='utf-8'))
    d = skel()
    keep = lambda key, field='name': {x[field] for x in original[key]}
    for e in d['preview_attachments']['entries']:
        m.edit_skeletal_preview_attachment(SK, e.get('asset_path', e.get('preview_asset_path', '')), e.get('attach_name', e.get('name', '')),
                                           operation='remove', **Y)
    for s in d['sockets']:
        if s['name'] not in keep('sockets'):
            m.delete_skeleton_socket(SK, s['name'], **Y)
    for s in mesh()['sockets']:
        if s['owner'] == 'mesh':
            m.delete_mesh_socket(ME, s['name'], **Y)
    if d['virtual_bones']:
        m.delete_skeleton_virtual_bones(SK, [v['name'] for v in d['virtual_bones']], cascade=True, **Y)
    for c in d['compatible_skeletons']:
        m.edit_skeleton_compatibility(SK, c if isinstance(c, str) else c.get('path', c.get('asset_path', '')), operation='remove', **Y)
    for p in d['blend_profiles']:
        if p['name'] not in keep('blend_profiles'):
            m.delete_skeleton_blend_profile(SK, p['name'], allow_referenced=True, **Y)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': AS.split('.')[0]}, timeout=120)
    for r in skel()['retarget_sources']:
        if r['pose_name'] not in keep('retarget_sources', 'pose_name'):
            m.delete_skeleton_retarget_source(SK, r['pose_name'], allow_referenced=True, **Y)
    for p in (SK, ME):
        httpx.post(BASE + '/assets/save', json={'AssetPath': p.split('.')[0]}, timeout=120)
    STATE.unlink(missing_ok=True)
    if check:
        now = structural()
        assert now == original, ('fixture not restored', [k for k in now if now[k] != original[k]])
        ORIGINAL.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
