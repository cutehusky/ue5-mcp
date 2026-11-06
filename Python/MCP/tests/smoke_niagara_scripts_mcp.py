"""Call every Niagara script and script-graph MCP tool through the registered FastMCP dispatcher.

Builds scratch function/module scripts with a few nodes over REST, then runs read-only tools for real and
mutating tools as confirmed dry runs. Script metadata and graphs must be unchanged before the scripts are deleted.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
FN = '/Game/UE5MCP_Test/NF_MCP_Mcp.NF_MCP_Mcp'
CALLEE = '/Game/UE5MCP_Test/NF_MCP_McpCallee.NF_MCP_McpCallee'
MODULE = '/Game/UE5MCP_Test/NM_MCP_Mcp.NM_MCP_Mcp'
REPLACEMENT = '/Game/UE5MCP_Test/NM_MCP_McpRepl.NM_MCP_McpRepl'
ASSETS = (FN, CALLEE, MODULE, REPLACEMENT)
READ_ONLY = ('inspect_', 'list_', 'validate_')


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    for p in ASSETS:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)
    for p, kind in ((FN, 'function'), (CALLEE, 'function'), (MODULE, 'module'), (REPLACEMENT, 'module')):
        api.call('POST', '/niagara/scripts', {'AssetPath': p, 'bConfirm': True, 'ValueKind': kind})
    version = lambda p: api.call('POST', '/niagara/scripts/inspect', {'AssetPath': p})['exposed_version_id']
    fv, mv, cv = version(FN), version(MODULE), version(CALLEE)
    V = {'AssetPath': FN, 'bConfirm': True, 'VersionId': fv}
    op = api.call('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': 'Integer::BitAnd'})
    cross = api.call('POST', '/niagara/scripts/graph/operations', {**V, 'NewName': 'Vector3::Cross', 'NodeY': 200})
    inp = api.call('POST', '/niagara/scripts/graph/scalar-inputs', {**V, 'ParameterName': 'Rate', 'ValueKind': 'int', 'ScalarValue': 3, 'NodeX': -400})
    rr = api.call('POST', '/niagara/scripts/graph/reroutes', {**V, 'NodeX': -200})
    cb = api.call('POST', '/niagara/scripts/graph/comment-boxes', {**V, 'TextValue': 'group'})
    try:
        g = api.call('POST', '/niagara/scripts/graph/inspect', V)
        by_id = {n['id']: n for n in g['nodes']}
        out = next(n for n in g['nodes'] if n['class_path'].endswith('NiagaraNodeOutput'))
        pin = lambda nid, name: next(p for p in by_id[nid]['pins'] if p['name'] == name)['id']
        in_out = next(p for p in by_id[inp['node_id']]['pins'] if p['direction'] == 1)['id']
        F = lambda **kw: dict(asset_path=FN, version_id=fv, **kw)
        M = lambda **kw: dict(asset_path=MODULE, version_id=mv, **kw)
        N = lambda r, **kw: F(node_id=r['node_id'], node_path=r['node_path'], **kw)
        O = F(node_id=out['id'], node_path=out['object_path'])
        args = {
            'inspect_niagara_script_asset': dict(asset_path=MODULE),
            'inspect_niagara_script_graph': F(),
            'list_niagara_script_operations': F(),
            'validate_niagara_script_graph': F(),
            'create_niagara_script_asset': dict(asset_path='/Game/UE5MCP_Test/NM_MCP_McpNew.NM_MCP_McpNew', kind='dynamic_input'),
            'duplicate_niagara_script_asset': dict(source_asset_path=MODULE, asset_path='/Game/UE5MCP_Test/NM_MCP_McpDup.NM_MCP_McpDup'),
            'set_niagara_script_text': M(field='Category', text='Dry'),
            'set_niagara_script_bool': M(field='bSuggested', enabled=True),
            'set_niagara_script_enum': M(field='LibraryVisibility', enum_name='Library'),
            'set_niagara_script_provided_dependencies': M(dependency_ids=['DryDep']),
            'set_niagara_module_usage_contexts': M(usage_names=['ParticleUpdateScript']),
            'set_niagara_script_deprecation_replacement': M(replacement_path=REPLACEMENT),
            'set_niagara_script_required_dependencies': M(dependencies=[{'Id': 'DryDep'}]),
            'move_niagara_script_node': N(op, x=10, y=20),
            'set_niagara_script_node_comment': N(op, text='dry'),
            'set_niagara_script_pin_scalar': N(op, pin_id=pin(op['node_id'], 'A'), value=4),
            'reset_niagara_script_pin_default': N(op, pin_id=pin(op['node_id'], 'B')),
            'set_niagara_script_pin_compound': N(cross, pin_id=pin(cross['node_id'], 'A'), kind='vector', components=[1, 2, 3]),
            'connect_niagara_script_pins': N(inp, pin_id=in_out, target_node_id=op['node_id'], target_node_path=op['node_path'], target_pin_id=pin(op['node_id'], 'A')),
            'disconnect_niagara_script_pins': N(inp, pin_id=in_out, target_node_id=op['node_id'], target_node_path=op['node_path'], target_pin_id=pin(op['node_id'], 'A')),
            'remove_niagara_script_node': N(rr),
            'add_niagara_script_reroute': F(x=5, y=5),
            'add_niagara_script_function_call': F(source_asset_path=CALLEE, source_version_id=cv),
            'add_niagara_script_operation': F(operation_name='Numeric::Add'),
            'add_niagara_script_comment_box': F(text='dry'),
            'resize_niagara_script_comment_box': N(cb, width=500, height=300),
            'duplicate_niagara_script_node': N(rr, x=1, y=1),
            'add_niagara_script_parameter_map': F(kind='get'),
            'add_niagara_script_scalar_input': F(name='DryF', kind='float', value=1),
            'add_niagara_script_compound_input': F(name='DryV', kind='vector', components=[1, 2, 3]),
            'add_niagara_script_constant_input': F(name='DryC', kind='float', scalar_value=2),
            'set_niagara_script_input_exposure': N(inp, field='bRequired', enabled=False),
            'set_niagara_script_input_priority': N(inp, priority=2),
            'set_niagara_script_input_value': N(inp, scalar_value=8),
            'rename_niagara_script_input': N(inp, new_name='DryRate'),
            'add_niagara_script_output': {**O, 'name': 'DryOut', 'kind': 'float'},
            'edit_niagara_script_output': {**O, 'output_index': 0, 'expected_name': out['outputs'][0]['name'], 'action': 'rename', 'new_name': 'DryOutput'},
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        script_tools = {n for n in tools if 'niagara_script' in n or n == 'set_niagara_module_usage_contexts'}
        assert script_tools == set(args), (sorted(script_tools - set(args)), sorted(set(args) - script_tools))
        props = lambda n: tools[n].inputSchema.get('properties', {})
        no_dry = sorted(n for n in args if not n.startswith(READ_ONLY) and 'dry_run' not in props(n))
        assert not no_dry, ('mutating tools without dry_run', no_dry)

        def state():
            s = {p: api.call('POST', '/niagara/scripts/inspect', {'AssetPath': p})['versions'] for p in (FN, MODULE)}
            s['graph'] = api.call('POST', '/niagara/scripts/graph/inspect', V)['nodes']
            return s
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
        assert state() == before, 'dry runs changed the scripts'
        for p in ('NM_MCP_McpNew', 'NM_MCP_McpDup'):
            api.call('POST', '/niagara/scripts/inspect', {'AssetPath': f'/Game/UE5MCP_Test/{p}.{p}'}, ok=False)
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} Niagara script MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); scripts unchanged')
        assert not guarded, guarded
    finally:
        for p in ASSETS:
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
