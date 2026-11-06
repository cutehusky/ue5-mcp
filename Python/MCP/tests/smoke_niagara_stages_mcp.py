"""Call every Niagara simulation-stage, event-handler and versioned emitter-setting MCP tool through the
registered FastMCP dispatcher, on a duplicate of the RenderTargetTexturePainter template.

Stage and emitter-setting tools run as confirmed dry runs and must succeed. No shipped asset has an event
handler and no route creates one, so the event-handler tools are dispatched against index 0 and must come back
with the native "event handler" guard; that checks the MCP wiring only. The copy must be unchanged.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
from smoke_niagara_stages_live import SOURCE

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
SYS = '/Game/UE5MCP_Test/NS_MCP_StagesMcp.NS_MCP_StagesMcp'


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': SYS}, timeout=180)
    api.call('POST', '/niagara/systems/duplicate', {'AssetPath': SYS, 'SourceAssetPath': SOURCE, 'bConfirm': True})
    api.call('POST', '/niagara/systems/user-parameters/scalar', {'AssetPath': SYS, 'bConfirm': True, 'ParameterName': 'User.McpIter', 'ValueKind': 'int', 'ScalarValue': 2})
    try:
        e = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})['emitters'][0]
        s = e['simulation_stages'][0]
        E = lambda **kw: dict(asset_path=SYS, emitter_index=0, emitter_id=e['id'], version_id=e['version_id'], **kw)
        S = lambda **kw: E(stage_index=s['index'], stage_path=s['object_path'], **kw)
        V = lambda **kw: E(event_index=0, script_path=s['script']['object_path'], **kw)
        args = {
            'set_niagara_emitter_scalar': E(field='RandomSeed', value=5),
            'set_niagara_emitter_enum': E(field='CalculateBoundsMode', enum_name='Fixed'),
            'set_niagara_emitter_fixed_bounds': E(min_x=-1, min_y=-1, min_z=-1, max_x=1, max_y=1, max_z=1),
            'set_niagara_simulation_stage_enabled': S(enabled=False),
            'rename_niagara_simulation_stage': S(new_name='McpDry'),
            'move_niagara_simulation_stage': S(target_index=2),
            'remove_niagara_simulation_stage': S(),
            'set_niagara_simulation_stage_enum': S(field='ExecuteBehavior', enum_name='OnSimulationReset'),
            'set_niagara_simulation_stage_bool': S(field='bDisablePartialParticleUpdate', enabled=True),
            'set_niagara_simulation_stage_state_range': S(state_min=1, state_max=2),
            'set_niagara_simulation_stage_integer_default': S(field='NumIterations', value=3),
            'reset_niagara_simulation_stage_binding': S(field='NumIterations'),
            'bind_niagara_simulation_stage_user_integer': S(field='NumIterations', parameter_name='User.McpIter'),
        }
        events = {
            'set_niagara_event_handler_count': V(field='SpawnNumber', value=2),
            'set_niagara_event_handler_bool': V(field='bRandomSpawnNumber', enabled=True),
            'set_niagara_event_handler_execution_mode': V(mode='SpawnedParticles'),
            'set_niagara_event_handler_source': V(event_name='CollisionEvent'),
            'remove_niagara_event_handler': V(),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) | set(events) <= set(tools), sorted((set(args) | set(events)) - set(tools))
        props = lambda n: tools[n].inputSchema.get('properties', {})
        assert all('dry_run' in props(n) for n in list(args) + list(events))

        def state():
            d = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})
            for k in ('dirty', 'compile_requests_pending', 'compile_or_gpu_requests_pending', 'native_ready_to_run', 'system_scripts', 'scope'):
                d.pop(k, None)
            return d['emitters']

        async def call(name, a):
            result = await mcp_server.mcp.call_tool(name, {**a, 'dry_run': True, 'confirm': True})
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))

        before = state()
        for name, a in args.items():
            payload = await call(name, a)
            assert 'errorMessage' not in payload and payload.get('dry_run') is True, (name, str(payload)[:300])
        for name, a in events.items():
            payload = await call(name, a)
            assert 'event' in payload.get('errorMessage', '').lower(), (name, str(payload)[:300])
        assert state() == before, 'dry runs changed the system'
        print(f'{len(args)} stage/emitter-setting MCP tools ok as dry runs; {len(events)} event-handler tools reached the native guard; system unchanged')
    finally:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': SYS}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
