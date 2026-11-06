"""Call every scene-capture MCP tool through the registered FastMCP dispatcher.

Builds the scratch capture map from smoke_scene_captures_live.py (2D and cube captures, two static-mesh actors,
render targets and a transform collection, assigned over REST). Read-only tools run for real, mutating tools as
confirmed dry runs; both captures' settings, lists, show flags and targets must be unchanged.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_scene_captures_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server

BASE = 'http://127.0.0.1:8080'
# The clip-plane vectors are editable only while the capture's bEnableClipPlane is on (and r.AllowGlobalClipPlane is set);
# these dispatches leave it off, so the native edit condition refuses. The live test enables it and edits the plane.
EXPECTED_GUARDS = {'set_scene_capture_2d_clip_plane'}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP), 'scratch capture map is open; run smoke_scene_captures_live.py cleanup'
    live.use_tag(uuid.uuid4().hex[:6])
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        actors, components = live.create_fixtures(api, None)
        c2, cc = live.Capture(api, '2d'), live.Capture(api, 'cube')
        api.call('POST', c2.route('target'), {**c2.ids(), 'AssetPath': live.RT2D, 'ExpectedTargetPath': '', 'bDryRun': False})
        api.call('POST', c2.route('transform-collection'), {**c2.ids(), 'AssetPath': live.MPC, 'ExpectedTargetPath': '', 'bDryRun': False})
        s2, sc = c2.settings(), cc.settings()
        ref = lambda c: dict(actor_path=c.actor, component_path=c.component)
        ids = lambda c, s: dict(**ref(c), actor_guid=s['actor_guid'], expected_label=s['label'])
        full = lambda c, s: dict(**ids(c, s), expected_class_path=s['class_path'])
        val = lambda s, name: next(f['value'] for f in s['fields'] if f['name'] == name)
        args = {
            'inspect_scene_captures_2d_page': dict(count=8), 'inspect_scene_captures_cube_page': dict(count=8),
            'inspect_scene_capture_2d_settings': ref(c2), 'inspect_scene_capture_cube_settings': ref(cc),
            'inspect_scene_capture_2d_actor_lists': ref(c2), 'inspect_scene_capture_cube_actor_lists': ref(cc),
            'inspect_scene_capture_2d_component_lists': ref(c2), 'inspect_scene_capture_cube_component_lists': ref(cc),
            'inspect_scene_capture_2d_show_flags': dict(**ref(c2), query_names=['Bloom']), 'inspect_scene_capture_cube_show_flags': dict(**ref(cc), query_names=['Fog']),
            'discover_scene_capture_2d_show_flags': dict(**ref(c2), name_filter='Bloom'), 'discover_scene_capture_cube_show_flags': dict(**ref(cc), name_filter='Fog'),
            'inspect_scene_capture_2d_collection_layout': ref(c2), 'inspect_scene_capture_2d_collection_writers': ref(c2),
            'set_scene_capture_2d_target': dict(**ids(c2, s2), expected_target_path=live.RT2D, target_path=''),
            'set_scene_capture_cube_target': dict(**ids(cc, sc), expected_target_path='', target_path=live.RTCUBE),
            'set_scene_capture_2d_setting': dict(**full(c2, s2), field_name='FOVAngle', expected_value=val(s2, 'FOVAngle'), value=60,
                                                 expected_setting_texts=s2['native_setting_texts']),
            'set_scene_capture_cube_setting': dict(**full(cc, sc), field_name='LODDistanceFactor', expected_value=val(sc, 'LODDistanceFactor'), value=2,
                                                   expected_setting_texts=sc['native_setting_texts']),
            'set_scene_capture_2d_clip_plane': dict(**full(c2, s2), expected_base=s2['clip_plane_base'], expected_normal=s2['clip_plane_normal'],
                                                    expected_enabled=False, base=[0, 0, 50], normal=[0, 1, 0]),
            'set_scene_capture_2d_projection_matrix': dict(**full(c2, s2), expected_matrix=s2['custom_projection_matrix_row_major'],
                                                           matrix=[2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1, 0, 0, 10, 0], expected_enabled=False, enabled=True),
            'set_scene_capture_2d_actor_list': dict(**full(c2, s2), field_name='HiddenActors', expected_actor_paths=[], actor_paths=actors),
            'set_scene_capture_cube_actor_list': dict(**full(cc, sc), field_name='HiddenActors', expected_actor_paths=[], actor_paths=actors[:1]),
            'set_scene_capture_2d_component_list': dict(**full(c2, s2), field_name='ShowOnlyComponents', expected_component_paths=[], component_paths=components),
            'set_scene_capture_cube_component_list': dict(**full(cc, sc), field_name='HiddenComponents', expected_component_paths=[], component_paths=components[:1]),
            'set_scene_capture_2d_show_flags': dict(**full(c2, s2), expected_names=[], expected_enabled=[], names=['Bloom'], enabled=[False]),
            'set_scene_capture_cube_show_flags': dict(**full(cc, sc), expected_names=[], expected_enabled=[], names=['Fog', 'Bloom'], enabled=[False, True]),
            'set_scene_capture_2d_resolution_divisor': dict(**full(c2, s2), expected_xy=[1, 1], xy=[2, 2], expected_setting_texts=s2['native_setting_texts']),
            'set_scene_capture_2d_output_name': dict(**full(c2, s2), field_name='UserSceneTextureNormal', expected_name='None', name='MCP_Normal',
                                                     expected_setting_texts=s2['native_setting_texts']),
            'set_scene_capture_2d_transform_collection': dict(**full(c2, s2), expected_collection_path=live.MPC, collection_path=''),
            'set_scene_capture_2d_collection_parameter': dict(**full(c2, s2), expected_collection_path=live.MPC, field_name='CollectionTransformProjection',
                                                              expected_name='None', name=live.PROJ[0]),
            'set_scene_capture_2d_view_channels': dict(**full(c2, s2), expected_channels=s2['view_lighting_channels'], channels=[0, 1, 1, 0, 0]),
            'set_scene_capture_cube_view_channels': dict(**full(cc, sc), expected_channels=sc['view_lighting_channels'], channels=[1, 0, 0, 0, 1],
                                                         expected_setting_texts=sc['native_setting_texts']),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        names = {t for t in tools if 'scene_capture' in t}
        assert names == set(args), sorted(names ^ set(args))
        assert len(args) == 32, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})
        state = lambda: (c2.state(), cc.state())
        before = state()
        outcome = {}
        for name, a in args.items():
            a = dict(a)
            if 'dry_run' in props(name):
                a.update(dry_run=True)
            if 'confirm' in props(name):
                a.update(confirm=True)
            result = await mcp_server.mcp.call_tool(name, a)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:180]
            else:
                if 'dry_run' in props(name) and isinstance(payload, dict) and 'dry_run' in payload:
                    assert payload['dry_run'] is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        assert live.close(state(), before), 'dry runs changed the captures'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} scene-capture MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); captures unchanged')
        assert set(guarded) == EXPECTED_GUARDS, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        for p in (live.RT2D, live.RTCUBE, live.MPC):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
