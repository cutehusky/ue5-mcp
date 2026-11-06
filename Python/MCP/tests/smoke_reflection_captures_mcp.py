"""Call every reflection-capture and planar-reflection MCP tool through the registered FastMCP dispatcher.

Builds a scratch map (sphere and box captures, a planar reflection, two static-mesh actors) over REST. Read-only tools
run for real, mutating tools as confirmed dry runs; all captures and the planar reflection must be unchanged and no
dry run may create or delete an actor.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_reflection_captures_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP), 'scratch reflection map is open; run smoke_reflection_captures_live.py cleanup'
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        assert api.call('GET', '/worlds/inspect')['world_path'].startswith(live.MAP)
        actors = sorted(live.spawn(api, x) for x in (0, 300))
        components = [a + '.StaticMeshComponent0' for a in actors]
        for shape, name, x in (('Sphere', 'MCP_Sphere', 0), ('Box', 'MCP_Box', 500)):
            api.call('POST', '/reflection-captures/create', {'Name': name, 'Shape': shape, 'Location': {'X': x, 'Y': 0, 'Z': 100}, **LIVE})
        api.call('POST', '/planar-reflections/create', {'Name': 'MCP_Planar', 'Location': {'X': 0, 'Y': 500, 'Z': 0}, **LIVE})
        s, b, p = live.captures(api)['MCP_Sphere'], live.captures(api)['MCP_Box'], live.planars(api)['MCP_Planar']
        ref = lambda e: dict(actor_path=e['actor_path'], component_path=e['component_path'])
        gl = lambda e: dict(**ref(e), actor_guid=e['actor_guid'], expected_label=e['label'])
        xf = lambda e: dict(expected_location=e['world_location'], expected_rotation=e['world_rotation_quaternion'], expected_scale=e['component_scale'])
        args = {
            'inspect_world_reflection_captures': {}, 'inspect_world_planar_reflections': {},
            'inspect_reflection_captures_page': dict(shape='Sphere'), 'inspect_planar_reflections_page': {},
            'set_reflection_capture_scalar': dict(**ref(s), field='Brightness', expected_value=s['brightness'], value=3),
            'set_reflection_capture_offset': dict(**ref(s), expected_offset=[0, 0, 0], offset=[5, 5, 5]),
            'set_reflection_capture_source': dict(**ref(b), expected_source_type=0, expected_cubemap_path='', source_type='SpecifiedCubemap', cubemap_path=live.CUBEMAP),
            'queue_reflection_capture_recapture': dict(**ref(s), expected_build_data_id=s['map_build_data_id']),
            'set_reflection_capture_visible': dict(**ref(b), expected_visible=True, visible=False),
            'create_reflection_capture': dict(shape='Box', name='MCP_BoxNew', location=[0, -900, 0]),
            'delete_reflection_capture': dict(**ref(b), expected_build_data_id=b['map_build_data_id']),
            'set_reflection_capture_transform': dict(**ref(s), **xf(s), location=[10, 10, 10], rotation=[0, 0, 0, 1], scale=[1, 1, 1]),
            'set_planar_reflection_scalar': dict(**ref(p), field='ExtraFOV', expected_value=p['extra_fov'], value=4),
            'set_planar_reflection_screen_percentage': dict(**ref(p), expected_value=p['screen_percentage'], value=80),
            'set_planar_reflection_bool': dict(**ref(p), field='bRenderSceneTwoSided', expected_value=False, value=True),
            'create_planar_reflection': dict(name='MCP_PlanarNew', location=[0, -900, 0]),
            'delete_planar_reflection': ref(p),
            'set_planar_reflection_visible': dict(**ref(p), expected_visible=True, visible=False),
            'set_planar_reflection_transform': dict(**ref(p), **xf(p), location=[0, 600, 10], rotation=[0, 0, 0, 1], scale=[2, 2, 1]),
            'inspect_planar_reflection_actor_lists': ref(p), 'inspect_planar_reflection_component_lists': ref(p),
            'inspect_planar_reflection_show_flags': dict(**ref(p), query_names=['Fog']),
            'discover_planar_reflection_show_flags': dict(**ref(p), name_filter='Fog'),
            'set_planar_reflection_actor_list': dict(**gl(p), field_name='HiddenActors', expected_actor_paths=[], actor_paths=actors),
            'set_planar_reflection_component_list': dict(**gl(p), field_name='HiddenComponents', expected_component_paths=[], component_paths=components),
            'set_planar_reflection_capture_policy': dict(**gl(p), field_name='bCaptureOnMovement', expected_value=1, value=0),
            'set_planar_reflection_capture_numeric': dict(**gl(p), field_name='LODDistanceFactor', expected_value=1, value=3),
            'set_planar_reflection_show_flags': dict(**gl(p), expected_names=[], expected_enabled=[], names=['Fog'], enabled=[False]),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        names = {t for t in tools if 'reflection' in t}
        assert names == set(args), sorted(names ^ set(args))
        assert len(args) == 28, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})
        ref_lists = lambda: (api.call('POST', '/reflection-captures/planar/actor-lists/inspect', {'ActorPath': p['actor_path'], 'ComponentPath': p['component_path'], 'Count': 64}),
                             api.call('POST', '/reflection-captures/planar/component-lists/inspect', {'ActorPath': p['actor_path'], 'ComponentPath': p['component_path'], 'Count': 64}),
                             api.call('POST', '/reflection-captures/planar/show-flags/inspect', {'ActorPath': p['actor_path'], 'ComponentPath': p['component_path'], 'Count': 64})['overrides'])
        state = lambda: (live.captures(api), live.planars(api), [{k: v for k, v in x.items() if k not in live.VOLATILE} if isinstance(x, dict) else x for x in ref_lists()])
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
            text = ''.join(b_.text for b_ in blocks if hasattr(b_, 'text'))
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
        assert live.close(state(), before), 'dry runs changed reflection state'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} reflection MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); captures unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
