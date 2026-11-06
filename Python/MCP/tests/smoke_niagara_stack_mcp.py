"""Call every Niagara module-stack and rapid-iteration MCP tool through the registered FastMCP dispatcher.

Works on a duplicate of NS_JumpPad with the engine Drag and CompleteIfUnused modules inserted over REST.
Read-only tools run for real and mutating tools as confirmed dry runs; stacks, module inputs and rapid-iteration
stores must be unchanged. No available module has a vector/color pin or rapid-iteration parameter and
CompleteIfUnused has no scalar pin, so the three compound/system-pin tools are expected to reach a native type
guard (dispatcher wiring only).
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
SYS = '/Game/UE5MCP_Test/NS_MCP_StackMcp.NS_MCP_StackMcp'
DRAG = '/Niagara/Modules/Update/Forces/Drag.Drag'
SYSTEM_MODULE = '/Niagara/Modules/System/CompleteIfUnused.CompleteIfUnused'
READ_ONLY = ('inspect_',)
EXPECTED_GUARD = {'set_niagara_emitter_rapid_compound', 'set_niagara_emitter_module_pin_compound', 'edit_niagara_system_module_pin_default'}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': SYS}, timeout=180)
    api.call('POST', '/niagara/systems/duplicate', {'AssetPath': SYS, 'SourceAssetPath': SOURCE, 'bConfirm': True})
    try:
        e = api.call('GET', '/niagara/systems/definition', params={'asset_path': SYS})['emitters'][0]
        E = {'AssetPath': SYS, 'bConfirm': True, 'EmitterIndex': 0, 'EmitterId': e['id'], 'VersionId': e['version_id'], 'ValueKind': 'particle_update'}
        ver = lambda p: api.call('POST', '/niagara/scripts/inspect', {'AssetPath': p})['exposed_version_id']
        drag = api.call('POST', '/niagara/systems/emitters/modules', {**E, 'SourceAssetPath': DRAG, 'SourceVersionId': ver(DRAG), 'TargetIndex': 0})
        sysmod = api.call('POST', '/niagara/systems/modules', {'AssetPath': SYS, 'bConfirm': True, 'ValueKind': 'system_update',
                                                               'SourceAssetPath': SYSTEM_MODULE, 'SourceVersionId': ver(SYSTEM_MODULE), 'TargetIndex': -1})
        dpins = api.call('POST', '/niagara/systems/emitters/modules/inspect', {**E, 'NodeId': drag['node_id'], 'NodePath': drag['node_path']})['inputs']
        bool_pin = next(p for p in dpins if p['type'] == 'NiagaraBool')['pin_id']
        erapid = api.call('POST', '/niagara/systems/emitters/rapid-iteration/inspect', {**E, 'ValueKind': 'emitter_update'})['parameters']
        efloat = next(x['name'] for x in erapid if x['stored_input_value'].get('value_kind') == 'float')
        srapid = api.call('POST', '/niagara/systems/rapid-iteration/inspect', {'AssetPath': SYS, 'ValueKind': 'system_update'})['parameters']
        sfloat = next(x['name'] for x in srapid if x['stored_input_value'].get('value_kind') == 'float')
        smods = api.call('POST', '/niagara/systems/stack-inspect', {'AssetPath': SYS, 'ValueKind': 'system_update'})['modules']
        sm = next(m for m in smods if m['node_id'] == sysmod['node_id'])
        H = lambda stack='particle_update', **kw: dict(asset_path=SYS, emitter_index=0, emitter_id=e['id'], version_id=e['version_id'], stack=stack, **kw)
        D = lambda **kw: H(node_id=drag['node_id'], node_path=drag['node_path'], **kw)
        S = lambda **kw: dict(asset_path=SYS, stack='system_update', **kw)
        args = {
            'inspect_niagara_emitter_stack': H(),
            'inspect_niagara_emitter_module': D(),
            'inspect_niagara_emitter_rapid_iteration': H('emitter_update'),
            'inspect_niagara_emitter_stack_dependencies': H(),
            'inspect_niagara_system_stack': S(),
            'inspect_niagara_system_module': S(node_id=sm['node_id'], node_path=sm['node_path']),
            'inspect_niagara_system_rapid_iteration': S(),
            'inspect_niagara_system_stack_dependencies': S(),
            'append_niagara_emitter_module': H(module_path=DRAG, module_version_id=ver(DRAG)),
            'insert_niagara_emitter_module': H(module_path=DRAG, module_version_id=ver(DRAG), target_index=0),
            'set_niagara_emitter_module_enabled': D(enabled=False),
            'set_niagara_emitter_module_pin_default': D(pin_id=bool_pin, value=0),
            'reset_niagara_emitter_module_pin_default': D(pin_id=bool_pin),
            'set_niagara_emitter_module_pin_compound': D(pin_id=bool_pin, kind='vector', components=[1, 2, 3]),
            'set_niagara_emitter_rapid_scalar': H('emitter_update', parameter_name=efloat, kind='float', value=0.5),
            'set_niagara_emitter_rapid_compound': H('emitter_update', parameter_name=efloat, kind='vector', components=[1, 2, 3]),
            'remove_niagara_emitter_rapid_parameter': H('emitter_update', parameter_name=efloat, kind='float'),
            'edit_niagara_system_rapid_parameter': S(parameter_name=sfloat, kind='float', value=2),
            'insert_niagara_system_module': S(module_path=SYSTEM_MODULE, module_version_id=ver(SYSTEM_MODULE)),
            'set_niagara_system_module_enabled': S(node_id=sm['node_id'], node_path=sm['node_path'], enabled=False),
            'edit_niagara_system_module_pin_default': S(node_id=sm['node_id'], node_path=sm['node_path'], pin_id='00000000-0000-0000-0000-000000000001', action='reset'),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        props = lambda n: tools[n].inputSchema.get('properties', {})
        assert all(n.startswith(READ_ONLY) or 'dry_run' in props(n) for n in args)

        def state():
            Eb = {k: v for k, v in E.items() if k != 'ValueKind'}
            out = {s: api.call('POST', '/niagara/systems/emitters/stack-inspect', {**Eb, 'ValueKind': s})['modules'] for s in ('particle_update', 'emitter_update')}
            out['rapid'] = api.call('POST', '/niagara/systems/emitters/rapid-iteration/inspect', {**Eb, 'ValueKind': 'emitter_update'})['parameters']
            out['sys'] = api.call('POST', '/niagara/systems/stack-inspect', {'AssetPath': SYS, 'ValueKind': 'system_update'})['modules']
            out['srapid'] = api.call('POST', '/niagara/systems/rapid-iteration/inspect', {'AssetPath': SYS, 'ValueKind': 'system_update'})['parameters']
            out['drag'] = api.call('POST', '/niagara/systems/emitters/modules/inspect', {**E, 'NodeId': drag['node_id'], 'NodePath': drag['node_path']})['inputs']
            return out
        before = state()
        outcome = {}
        for name, a in args.items():
            a = dict(a)
            if 'dry_run' in props(name):
                a.update(dry_run=True, confirm=True)
            result = await mcp_server.mcp.call_tool(name, a)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:140]
            else:
                if 'dry_run' in props(name):
                    assert payload.get('dry_run') is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        assert state() == before, 'dry runs changed the stacks'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} Niagara stack MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); stacks unchanged')
        assert set(guarded) == EXPECTED_GUARD, guarded
    finally:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': SYS}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
