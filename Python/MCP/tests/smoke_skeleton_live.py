"""Live Skeleton and skeletal-mesh socket authoring checks on duplicated Mannequin fixtures.

prepare: duplicate SK_Mannequin and SKM_Manny_Simple into /Game/UE5MCP_Test/Skel_<tag>, author sockets,
virtual bones, curve metadata, blend profiles, retarget sources, translation retargeting, compatibility,
preview attachments and mesh sockets with guard/dry-run/undo checks, save and snapshot.
verify (fresh editor): compare cold-loaded skeleton/mesh state, then delete the owned assets.
The original Mannequin assets are never edited; writes that would reach them run as dry runs only.
"""
import argparse
import json
import uuid
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'skeleton.json'
MESHES = '/Game/Characters/Mannequins/Meshes'
ORIG_SKELETON = f'{MESHES}/SK_Mannequin.SK_Mannequin'
ORIG_MESH = f'{MESHES}/SKM_Manny_Simple.SKM_Manny_Simple'
QUINN = f'{MESHES}/SKM_Quinn_Simple.SKM_Quinn_Simple'
PROP = '/Engine/BasicShapes/Cube.Cube'


class Api:
    def __init__(self, base):
        self.base = base

    def call(self, method, route, body=None, params=None, ok=True):
        r = httpx.request(method, self.base + route, json=body, params=params, timeout=300)
        if ok:
            assert r.is_success, (method, route, r.status_code, r.text[:1500])
            return r.json()
        assert r.status_code >= 400, (method, route, 'expected rejection', r.text[:800])
        return r.text

    def undo(self):
        self.call('POST', '/editor/transactions/undo', {})

    def redo(self):
        self.call('POST', '/editor/transactions/redo', {})

    def skel(self, path):
        return self.call('GET', '/skeletons/structure', params={'asset_path': path})

    def mesh_sockets(self, path):
        return self.call('GET', '/skeletal-meshes/sockets', params={'asset_path': path})


def names(items, key='name'):
    return [i[key] for i in items]


def skeleton_stage(api, sk):
    K = {'AssetPath': sk, 'bConfirm': True}
    sockets = lambda: names(api.skel(sk)['sockets'])
    base_sockets = sockets()
    # Sockets.
    api.call('POST', '/skeletons/sockets', {**K, 'SocketName': 'Prop', 'BoneName': 'no_bone'}, ok=False)
    api.call('POST', '/skeletons/sockets', {'AssetPath': sk, 'SocketName': 'Prop', 'BoneName': 'hand_r'}, ok=False)
    api.call('POST', '/skeletons/sockets', {**K, 'SocketName': 'Prop', 'BoneName': 'hand_r', 'bDryRun': True})
    assert sockets() == base_sockets
    api.call('POST', '/skeletons/sockets', {**K, 'SocketName': 'Prop', 'BoneName': 'hand_r', 'Location': {'X': 1, 'Y': 2, 'Z': 3}})
    assert 'Prop' in sockets()
    api.undo(); assert 'Prop' not in sockets()
    api.redo(); assert 'Prop' in sockets()
    api.call('POST', '/skeletons/sockets', {**K, 'SocketName': base_sockets[0], 'BoneName': 'hand_r'}, ok=False)
    api.call('POST', '/skeletons/sockets', {**K, 'Operation': 'update', 'SocketName': 'Prop', 'BoneName': 'hand_l', 'Location': {'X': 4, 'Y': 0, 'Z': 0}})
    prop = next(s for s in api.skel(sk)['sockets'] if s['name'] == 'Prop')
    assert 'hand_l' in json.dumps(prop) and '4' in json.dumps(prop), prop
    api.call('PATCH', '/skeletons/sockets/name', {**K, 'SocketName': 'Prop', 'NewName': base_sockets[0]}, ok=False)
    api.call('PATCH', '/skeletons/sockets/name', {**K, 'SocketName': 'Prop', 'NewName': 'Weapon'})
    assert 'Weapon' in sockets() and 'Prop' not in sockets()
    api.call('POST', '/skeletons/sockets', {**K, 'SocketName': 'Spare', 'BoneName': 'spine_03'})
    api.call('DELETE', '/skeletons/sockets', {**K, 'SocketName': 'Missing'}, ok=False)
    api.call('DELETE', '/skeletons/sockets', {**K, 'SocketName': 'Spare'})
    assert 'Spare' not in sockets()

    # Virtual bones.
    vbs = lambda: names(api.skel(sk)['virtual_bones'])
    api.call('POST', '/skeletons/virtual-bones', {**K, 'SourceBone': 'hand_l', 'TargetBone': 'no_bone'}, ok=False)
    api.call('POST', '/skeletons/virtual-bones', {**K, 'SourceBone': 'hand_l', 'TargetBone': 'hand_r'})
    api.call('POST', '/skeletons/virtual-bones', {**K, 'SourceBone': 'foot_l', 'TargetBone': 'foot_r'})
    created = vbs()
    assert len(created) == 2 and all(n.startswith('VB ') for n in created), created
    api.undo(); assert len(vbs()) == 1
    api.redo(); assert len(vbs()) == 2
    api.call('PATCH', '/skeletons/virtual-bones/name', {**K, 'Name': created[0], 'NewName': 'NoPrefix'}, ok=False)
    api.call('PATCH', '/skeletons/virtual-bones/name', {**K, 'Name': created[0], 'NewName': 'VB HandsSpan'})
    assert 'VB HandsSpan' in vbs()
    api.call('DELETE', '/skeletons/virtual-bones', {**K, 'Names': ['VB Missing']}, ok=False)
    api.call('DELETE', '/skeletons/virtual-bones', {**K, 'Names': [created[1]]})
    assert vbs() == ['VB HandsSpan'], vbs()

    # Curve metadata.
    curves = lambda: {c['name']: c for c in api.skel(sk)['curve_metadata']}
    api.call('POST', '/skeletons/curve-metadata', {**K, 'Name': 'MCP_Curve', 'LinkedBones': ['no_bone']}, ok=False)
    api.call('POST', '/skeletons/curve-metadata', {**K, 'Name': 'MCP_Curve', 'bMaterial': True, 'LinkedBones': ['head'], 'MaxLOD': 2})
    c = curves().get('MCP_Curve')
    assert c and 'head' in json.dumps(c), c
    api.call('POST', '/skeletons/curve-metadata', {**K, 'Operation': 'update', 'Name': 'MCP_Curve', 'bMorphTarget': True, 'LinkedBones': ['neck_01']})
    assert 'neck_01' in json.dumps(curves()['MCP_Curve'])
    api.call('POST', '/skeletons/curve-metadata/lifecycle', {**K, 'Name': 'MCP_Curve', 'NewName': 'MCP_Renamed', 'Operation': 'rename'})
    assert 'MCP_Renamed' in curves() and 'MCP_Curve' not in curves()
    api.call('POST', '/skeletons/curve-metadata', {**K, 'Name': 'MCP_Temp'})
    api.call('POST', '/skeletons/curve-metadata/lifecycle', {**K, 'Name': 'MCP_Temp', 'Operation': 'remove'})
    assert 'MCP_Temp' not in curves()

    # Blend profiles.
    profiles = lambda: {p['name']: p for p in api.skel(sk)['blend_profiles']}
    api.call('POST', '/skeletons/blend-profiles', {**K, 'ProfileName': 'MCP_Profile', 'Mode': 'Nope'}, ok=False)
    api.call('POST', '/skeletons/blend-profiles', {**K, 'ProfileName': 'MCP_Profile', 'Mode': 'WeightFactor'})
    assert 'MCP_Profile' in profiles()
    api.call('PATCH', '/skeletons/blend-profiles/scales', {**K, 'ProfileName': 'MCP_Profile', 'Bones': ['spine_01'], 'Scale': 0.5, 'bChildren': True})
    q = api.call('POST', '/skeletons/blend-profiles/scales/query', {**K, 'ProfileName': 'MCP_Profile', 'Bones': ['spine_01', 'spine_02']})
    assert '0.5' in json.dumps(q), q
    api.call('POST', '/skeletons/blend-profiles/reset', {**K, 'ProfileName': 'MCP_Profile', 'Bones': ['spine_02']})
    api.call('PATCH', '/skeletons/blend-profiles/scales', {**K, 'ProfileName': 'MCP_Profile', 'Bones': ['spine_03'], 'Scale': 5.0})
    api.call('PATCH', '/skeletons/blend-profiles/mode', {**K, 'ProfileName': 'MCP_Profile', 'Mode': 'BlendMask'}, ok=False)
    api.call('POST', '/skeletons/blend-profiles/reset', {**K, 'ProfileName': 'MCP_Profile', 'Bones': ['spine_03']})
    api.call('PATCH', '/skeletons/blend-profiles/mode', {**K, 'ProfileName': 'MCP_Profile', 'Mode': 'TimeFactor'})
    assert 'TimeFactor' in json.dumps(profiles()['MCP_Profile'])
    api.call('PATCH', '/skeletons/blend-profiles/name', {**K, 'ProfileName': 'MCP_Profile', 'NewName': 'MCP_Upper'})
    assert 'MCP_Upper' in profiles()
    api.call('POST', '/skeletons/blend-profiles', {**K, 'ProfileName': 'MCP_Copy', 'SourceProfileName': 'MCP_Upper', 'Mode': 'TimeFactor'})
    api.call('POST', '/skeletons/blend-profiles/references', {**K, 'ProfileName': 'MCP_Copy'})
    # Unreferenced: the undo buffer no longer counts as a referencer, so no override is needed.
    api.call('DELETE', '/skeletons/blend-profiles', {**K, 'ProfileName': 'MCP_Copy'})
    assert 'MCP_Copy' not in profiles() and 'MCP_Upper' in profiles()

    # Translation retargeting, compatibility, comparison, reference pose.
    api.call('PATCH', '/skeletons/translation-retargeting', {**K, 'Bones': ['spine_01'], 'Mode': 'Nope'}, ok=False)
    mode = lambda b: next(x for x in api.skel(sk)['bones'] if x['name'] == b)['translation_retargeting_mode']
    before = mode('spine_02')
    api.call('PATCH', '/skeletons/translation-retargeting', {**K, 'Bones': ['spine_01'], 'Mode': 'OrientAndScale', 'bChildren': True})
    assert mode('spine_01') == mode('spine_02') == 4 != before, (mode('spine_01'), mode('spine_02'), before)
    api.undo(); assert mode('spine_02') == before
    api.redo(); assert mode('spine_02') == 4
    api.call('POST', '/skeletons/compatibility', {**K, 'SourcePath': sk}, ok=False)
    api.call('POST', '/skeletons/compatibility', {**K, 'SourcePath': ORIG_SKELETON})
    assert ORIG_SKELETON in json.dumps(api.skel(sk)['compatible_skeletons'])
    api.call('PATCH', '/skeletons/compatibility/policy', {**K, 'bUseCompatibleRetargetModes': True})
    assert api.skel(sk)['use_compatible_retarget_modes'] is True
    cmp = api.call('POST', '/skeletons/compare', {'AssetPath': sk, 'SourcePath': ORIG_SKELETON})
    assert cmp, cmp

    # Preview attachments.
    api.call('POST', '/skeletons/preview-attachments', {**K, 'SocketName': 'Weapon', 'PreviewAssetPath': PROP, 'Operation': 'add'})
    assert PROP in json.dumps(api.skel(sk)['preview_attachments'])
    api.call('POST', '/skeletons/preview-attachments', {**K, 'SocketName': 'Weapon', 'NewName': 'VB HandsSpan', 'PreviewAssetPath': PROP, 'Operation': 'move'})
    assert 'VB HandsSpan' in json.dumps(api.skel(sk)['preview_attachments'])


def retarget_source_stage(api, sk, mesh):
    K = {'AssetPath': sk, 'bConfirm': True}
    sources = lambda: {s['pose_name']: s for s in api.skel(sk)['retarget_sources']}
    base = sorted(sources())
    # Creating or refreshing a source needs a mesh owned by this skeleton; the duplicated mesh still
    # belongs to SK_Mannequin, so the native ownership guard must refuse it.
    api.call('POST', '/skeletons/retarget-sources', {**K, 'PoseName': 'MCP_Pose', 'SourceMeshPath': mesh}, ok=False)
    pose = base[0]
    p = api.call('POST', '/skeletons/retarget-sources/pose', {**K, 'PoseName': pose, 'Bones': ['pelvis', 'spine_01']})
    assert 'pelvis' in json.dumps(p), json.dumps(p)[:400]
    api.call('POST', '/skeletons/retarget-sources/duplicate', {**K, 'PoseName': pose, 'NewName': pose}, ok=False)
    api.call('POST', '/skeletons/retarget-sources/duplicate', {**K, 'PoseName': pose, 'NewName': 'MCP_Pose2'})
    assert 'MCP_Pose2' in sources() and sources()['MCP_Pose2']['transform_count'] == sources()[pose]['transform_count']
    api.undo(); assert 'MCP_Pose2' not in sources()
    api.redo(); assert 'MCP_Pose2' in sources()
    api.call('PATCH', '/skeletons/retarget-sources/name', {**K, 'PoseName': 'MCP_Pose2', 'NewName': base[-1]}, ok=False)
    api.call('PATCH', '/skeletons/retarget-sources/name', {**K, 'PoseName': 'MCP_Pose2', 'NewName': 'MCP_Pose3'})
    assert 'MCP_Pose3' in sources() and 'MCP_Pose2' not in sources()
    before = json.dumps(api.call('POST', '/skeletons/retarget-sources/pose', {**K, 'PoseName': 'MCP_Pose3', 'Bones': ['spine_01']}))
    api.call('PATCH', '/skeletons/retarget-sources/pose', {**K, 'PoseName': 'MCP_Pose3',
                                                          'PoseEdits': [{'Bone': 'spine_01', 'Rotation': {'Pitch': 0, 'Yaw': 0, 'Roll': 15}}]})
    after = json.dumps(api.call('POST', '/skeletons/retarget-sources/pose', {**K, 'PoseName': 'MCP_Pose3', 'Bones': ['spine_01']}))
    assert after != before, after[:300]
    api.call('PATCH', '/skeletons/retarget-sources/pose', {**K, 'PoseName': 'MCP_Pose3', 'Bones': ['spine_01'], 'bResetReferencePose': True})
    api.call('PATCH', '/skeletons/retarget-sources/pose', {**K, 'PoseName': 'MCP_Pose3', 'PoseEdits': [{'Bone': 'no_bone'}]}, ok=False)
    r = httpx.request('DELETE', api.base + '/skeletons/retarget-sources', json={**K, 'PoseName': 'MCP_Pose3'}, timeout=120)
    if not r.is_success:
        api.call('DELETE', '/skeletons/retarget-sources', {**K, 'PoseName': 'MCP_Pose3', 'bAllowReferenced': True})
    assert sorted(sources()) == base, sorted(sources())
    return 'ok'


def mesh_stage(api, mesh):
    M = {'AssetPath': mesh, 'bConfirm': True}
    local = lambda: json.dumps(api.mesh_sockets(mesh))
    api.call('POST', '/skeletal-meshes/sockets', {**M, 'SocketName': 'MeshProp', 'BoneName': 'no_bone'}, ok=False)
    api.call('POST', '/skeletal-meshes/sockets', {**M, 'SocketName': 'MeshProp', 'BoneName': 'hand_r'})
    assert 'MeshProp' in local()
    api.undo(); assert 'MeshProp' not in local()
    api.redo()
    api.call('POST', '/skeletal-meshes/sockets', {**M, 'Operation': 'update', 'SocketName': 'MeshProp', 'BoneName': 'hand_l'})
    api.call('PATCH', '/skeletal-meshes/sockets/name', {**M, 'SocketName': 'MeshProp', 'NewName': 'MeshWeapon'})
    assert 'MeshWeapon' in local() and 'MeshProp' not in local()
    api.call('POST', '/skeletal-meshes/preview-attachments', {**M, 'SocketName': 'MeshWeapon', 'PreviewAssetPath': PROP, 'Operation': 'add'})
    # The duplicated mesh still uses the original SK_Mannequin, so customize/promote that touch shared
    # skeleton sockets run as dry runs only.
    dry = {}
    for s in api.skel(ORIG_SKELETON)['sockets']:
        r = httpx.post(api.base + '/skeletal-meshes/sockets/customize', json={**M, 'SocketName': s['name'], 'bDryRun': True}, timeout=120)
        dry[s['name']] = r.is_success or r.json().get('errorMessage', '')[:90]
    r = httpx.post(api.base + '/skeletal-meshes/sockets/promote', json={**M, 'SocketName': 'MeshWeapon', 'bDryRun': True}, timeout=120)
    dry['promote MeshWeapon'] = r.is_success or r.json().get('errorMessage', '')[:90]
    print('customize/promote dry runs:', json.dumps(dry, indent=1))
    api.call('POST', '/skeletal-meshes/sockets', {**M, 'SocketName': 'MeshTemp', 'BoneName': 'head'})
    api.call('DELETE', '/skeletal-meshes/sockets', {**M, 'SocketName': 'MeshTemp'})
    assert 'MeshTemp' not in local()


def prepare(api):
    assert not STATE.exists(), 'Run verify or cleanup first'
    tag = uuid.uuid4().hex[:8]
    root = f'/Game/UE5MCP_Test/Skel_{tag}'
    sk = f'{root}/SK_{tag}.SK_{tag}'
    mesh = f'{root}/SKM_{tag}.SKM_{tag}'
    owned = []
    results = {}
    original = api.skel(ORIG_SKELETON)
    try:
        for src, dst in ((ORIG_SKELETON, sk), (ORIG_MESH, mesh)):
            r = httpx.post(api.base + '/assets/duplicate', json={'AssetPath': src, 'DestinationPath': dst.split('.')[0]}, timeout=300)
            assert r.is_success, r.text[:400]
            owned.append(dst)
            assert r.text.strip().strip('"') == dst, (r.text, dst)
        skeleton_stage(api, sk)
        results['skeleton'] = 'ok'
        results['retarget_sources'] = retarget_source_stage(api, sk, mesh)
        mesh_stage(api, mesh)
        results['mesh_sockets'] = 'ok'
        assert api.skel(ORIG_SKELETON) == original, 'original SK_Mannequin changed'
        for path in owned:
            api.call('POST', '/assets/save', {'AssetPath': path})
        snapshots = {sk: api.skel(sk), mesh: api.mesh_sockets(mesh)}
        print(json.dumps(results, indent=1))
        print('Skeleton authoring OK; restart the editor and run verify')
    finally:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'owned': owned, 'snapshots': locals().get('snapshots')}), encoding='utf-8')


def comparable(s):
    return {k: v for k, v in s.items() if k not in ('dirty', 'scope')}


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshots'), 'prepare did not finish; run cleanup'
    try:
        sk, mesh = state['owned']
        cold = {sk: api.skel(sk), mesh: api.mesh_sockets(mesh)}
        for path, before in state['snapshots'].items():
            a, b = comparable(before), comparable(cold[path])
            diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            assert not diff, (path, diff, {k: (str(a.get(k))[:300], str(b.get(k))[:300]) for k in diff[:2]})
        print('Cold reload of skeleton sockets/virtual bones/curves/blend profiles/retargeting/compatibility/'
              'preview attachments and mesh sockets: OK')
    finally:
        cleanup(api)


def cleanup(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    for path in reversed(state['owned']):
        httpx.post(api.base + '/assets/delete', json={'AssetPath': path}, timeout=180)
    STATE.unlink()
    print('cleaned', len(state['owned']))


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
