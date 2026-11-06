"""Call every PCG world-component MCP tool (part 3) through the registered FastMCP dispatcher.

Builds a scratch map (before any asset) with a grid-points graph, a TargetPoint carrying a generated PCG component and
a second, cleaned spare component. Read-only tools run for real, mutating tools as confirmed dry runs; both
components' status and the generated points must be unchanged and no dry run may add or remove a component.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_pcg_world_live as live

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
    assert not original.startswith(live.MAP), 'scratch PCG map is open; run smoke_pcg_world_live.py cleanup'
    live.use_tag(uuid.uuid4().hex[:6])
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        assert api.call('GET', '/worlds/inspect')['world_path'].startswith(live.MAP)
        live.build_graph(api)
        actor = live.spawn(api, '/Script/Engine.TargetPoint', 0)
        ref = live.add_component(api, actor, 'MCP_PCG')
        spare = live.add_component(api, actor, 'MCP_PCG_Spare')
        for r in (ref, spare):
            api.call('PATCH', '/pcg/components/graph', {**r, 'SourceAssetPath': live.G, **LIVE})
        api.call('POST', '/pcg/components/operation', {**ref, 'Action': 'generate', 'bForce': True, **LIVE})
        live.wait_idle(api, ref, generated=True)
        entry = live.output(api, ref)['entries'][0]
        c = lambda r: dict(component_path=r['ComponentPath'], actor_path=r['ActorPath'])
        args = {
            'inspect_pcg_world_components': {},
            'inspect_pcg_component_status': c(ref), 'inspect_pcg_component_output': c(ref), 'inspect_pcg_component_resources': c(ref),
            'inspect_pcg_output_points': dict(**c(ref), output_index=entry['index'], data_path=entry['data_path'], start=10, count=5),
            'inspect_pcg_output_metadata': dict(**c(ref), output_index=entry['index'], data_path=entry['data_path']),
            'set_pcg_component_settings': dict(**c(ref), action='seed', seed=7),
            'set_pcg_component_generation_trigger': dict(**c(ref), trigger='GenerateOnDemand'),
            'set_pcg_component_partitioned': dict(**c(ref), enabled=True),
            'set_pcg_component_graph': dict(**c(ref), source_asset_path=''),
            'request_pcg_component_operation': dict(**c(ref), action='cleanup'),
            'add_pcg_actor_component': dict(actor_path=actor, component_name='MCP_PCG_New'),
            'remove_pcg_actor_component': c(spare),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        part3 = {t for t in tools if 'pcg' in t and ('component' in t or 'output' in t or 'world' in t)}
        assert part3 == set(args), sorted(part3 ^ set(args))
        props = lambda name: tools[name].inputSchema.get('properties', {})
        state = lambda: ([live.component(api, r) for r in (ref, spare)], [live.status(api, r) for r in (ref, spare)], live.all_points(api, ref),
                         sorted(x['path'] for x in api.call('POST', '/pcg/components/inspect', {})['components']))
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
        assert state() == before, 'dry runs changed the PCG components'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} PCG world MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); components unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.G}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
