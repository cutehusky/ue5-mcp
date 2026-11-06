"""Call every Niagara system-level MCP tool through the registered FastMCP dispatcher.

Works on a duplicate of NS_JumpPad plus a scratch emitter asset and effect type. Read-only tools run for real,
mutating tools run as confirmed dry runs, and the copy must be unchanged before the scratch assets are deleted.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
from smoke_niagara_system_live import SOURCE

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
SYS = '/Game/UE5MCP_Test/NS_MCP_Mcp.NS_MCP_Mcp'
EMITTER = '/Game/UE5MCP_Test/NE_MCP_Mcp.NE_MCP_Mcp'
EFFECT = '/Game/UE5MCP_Test/ET_MCP_Mcp.ET_MCP_Mcp'
READ_ONLY = ('inspect_', 'list_')


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    for p in (SYS, EMITTER, EFFECT):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)
    api.call('POST', '/niagara/systems/duplicate', {'AssetPath': SYS, 'SourceAssetPath': SOURCE, 'bConfirm': True})
    api.call('POST', '/niagara/emitters', {'AssetPath': EMITTER, 'bConfirm': True})
    api.call('POST', '/niagara/effect-types', {'AssetPath': EFFECT, 'bConfirm': True})
    # The scalar and vector setters edit existing defaults; NS_JumpPad only has a color one.
    api.call('POST', '/niagara/systems/user-parameters/scalar', {'AssetPath': SYS, 'bConfirm': True, 'ParameterName': 'User.McpOldF', 'ValueKind': 'float', 'ScalarValue': 1})
    api.call('POST', '/niagara/systems/user-parameters/vector', {'AssetPath': SYS, 'bConfirm': True, 'ParameterName': 'User.McpOldV', 'VectorValue': {'X': 1, 'Y': 1, 'Z': 1}})
    try:
        d = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})
        e = d['emitters'][0]
        sprite = next(r for r in e['renderers'] if r['class_path'].endswith('NiagaraSpriteRendererProperties'))
        mesh = next(r for r in e['renderers'] if r['class_path'].endswith('NiagaraMeshRendererProperties'))
        A = lambda **kw: dict(asset_path=SYS, **kw)
        H = lambda **kw: A(emitter_index=e['index'], expected_emitter_id=e['id'], **kw)
        RS = lambda **kw: H(renderer_index=sprite['index'], expected_renderer_path=sprite['object_path'], **kw)
        RM = lambda **kw: H(renderer_index=mesh['index'], expected_renderer_path=mesh['object_path'], **kw)
        args = {
            'inspect_niagara_system': A(),
            'inspect_niagara_emitter_asset': dict(asset_path=EMITTER),
            'list_niagara_renderer_types': dict(search='Sprite'),
            'inspect_niagara_renderer': RS(field='Alignment'),
            'create_niagara_system': dict(asset_path='/Game/UE5MCP_Test/NS_MCP_McpNew.NS_MCP_McpNew'),
            'duplicate_niagara_system': dict(asset_path='/Game/UE5MCP_Test/NS_MCP_McpDup.NS_MCP_McpDup', source_asset_path=SYS),
            'create_niagara_emitter_asset': dict(asset_path='/Game/UE5MCP_Test/NE_MCP_McpNew.NE_MCP_McpNew'),
            'create_niagara_effect_type': dict(asset_path='/Game/UE5MCP_Test/ET_MCP_McpNew.ET_MCP_McpNew'),
            'set_niagara_emitter_enabled': H(enabled=False),
            'rename_niagara_emitter': H(new_name='McpDry'),
            'duplicate_niagara_emitter': H(new_name='McpDryCopy'),
            'remove_niagara_emitter': H(),
            'add_niagara_emitter': A(emitter_path=EMITTER),
            'set_niagara_system_warmup': A(time=1.0, tick_delta=0.1),
            'set_niagara_user_scalar': A(parameter_name='User.McpOldF', kind='float', value=3),
            'set_niagara_user_vector': A(parameter_name='User.McpOldV', x=3, y=2, z=1),
            'set_niagara_user_color': A(parameter_name='User.Color', r=1, g=0, b=0, a=1),
            'add_niagara_user_scalar': A(parameter_name='User.McpF', kind='float', value=1.5),
            'add_niagara_user_vector': A(parameter_name='User.McpV', x=1, y=2, z=3),
            'add_niagara_user_color': A(parameter_name='User.McpC', r=1, g=1, b=1),
            'remove_niagara_user_parameter': A(parameter_name='User.Color', kind='color'),
            'set_niagara_system_fixed_bounds': A(minimum={'X': -1, 'Y': -1, 'Z': -1}, maximum={'X': 1, 'Y': 1, 'Z': 1}),
            'set_niagara_system_determinism': A(enabled=True, random_seed=7),
            'set_niagara_system_fixed_tick': A(enabled=True, delta_seconds=0.02),
            'set_niagara_system_effect_type': A(effect_type_path=EFFECT),
            'request_niagara_system_compile': A(force=True),
            'set_niagara_renderer_enabled': RS(enabled=not sprite['enabled']),
            'set_niagara_renderer_scalar': RS(field='SortOrderHint', value=2),
            'set_niagara_renderer_enum': RS(field='Alignment', value='VelocityAligned'),
            'set_niagara_renderer_asset': RS(field='Material', referenced_asset='/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial'),
            'reset_niagara_renderer_field': RS(field='MacroUVRadius'),
            'set_niagara_renderer_vector': RM(field='LockedAxis', x=0, y=1, z=0),
            'add_niagara_renderer': H(renderer_class='/Script/Niagara.NiagaraLightRendererProperties'),
            'remove_niagara_renderer': RS(),
            'move_niagara_renderer': RS(final_index=1),
            'duplicate_niagara_renderer': RS(),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        props = lambda n: tools[n].inputSchema.get('properties', {})
        no_dry = sorted(n for n in args if not n.startswith(READ_ONLY) and 'dry_run' not in props(n))
        assert not no_dry, ('mutating tools without dry_run', no_dry)

        def state():
            s = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})
            for k in ('dirty', 'compile_requests_pending', 'compile_or_gpu_requests_pending', 'native_ready_to_run', 'system_scripts', 'scope'):
                s.pop(k, None)
            for x in s['emitters']:
                x.pop('scripts', None)
            return s
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
                outcome[name] = 'guard: ' + payload['errorMessage'][7:110]
            else:
                if 'dry_run' in props(name):
                    assert payload.get('dry_run') is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        assert state() == before, 'dry runs changed the system'
        for p in ('NS_MCP_McpNew', 'NS_MCP_McpDup', 'NE_MCP_McpNew', 'ET_MCP_McpNew'):
            api.call('GET', '/niagara/systems/definition', params={'asset_path': f'/Game/UE5MCP_Test/{p}.{p}'}, ok=False)
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} Niagara system MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); system unchanged')
        assert not guarded, guarded
    finally:
        for p in (SYS, EMITTER, EFFECT):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
