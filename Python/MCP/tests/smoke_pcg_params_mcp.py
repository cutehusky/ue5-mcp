"""Call every PCG graph-parameter and graph-instance MCP tool (part 2) through the registered FastMCP dispatcher.

Builds a base graph with one parameter of every kind, a second base graph and an instance with one override over
REST. Read-only tools run for real, mutating tools as confirmed dry runs; both interfaces (values, overrides, arrays)
must be unchanged and no dry run may create an asset.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_pcg_params_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    tag = uuid.uuid4().hex[:6]
    live.use_tag(tag)
    G, G2, I = live.G, live.G2, live.I
    n = lambda base: f'/Game/UE5MCP_Test/{base}_{tag}.{base}_{tag}'
    try:
        for p in (G, G2):
            api.call('POST', '/pcg/graphs', {'AssetPath': p, **LIVE})
        for kind, extra in live.KINDS.items():
            api.call('POST', '/pcg/graphs/parameters', {'AssetPath': G, 'ParameterName': f'P_{kind}', 'ValueKind': kind, **(extra or {}), **LIVE})
        api.call('POST', '/pcg/graphs/parameters', {'AssetPath': G2, 'ParameterName': 'P_float', 'ValueKind': 'float', **LIVE})
        api.call('POST', '/pcg/graph-instances', {'AssetPath': I, 'SourceAssetPath': G, **LIVE})
        api.call('PATCH', live.PI + 'scalar', {**live.pid(api, I, 'P_int'), 'ScalarValue': 4, **LIVE})
        before = live.settled(api)
        pr = lambda path, name: dict(asset_path=path, parameter_name=name, parameter_id=live.param(api, path, name)['id'])
        args = {
            'inspect_pcg_graph_interface': dict(asset_path=I),
            'create_pcg_graph_instance': dict(asset_path=n('PCGI_McpNew'), parent_asset_path=G),
            'duplicate_pcg_graph_instance': dict(source_asset_path=I, asset_path=n('PCGI_McpDup')),
            'set_pcg_graph_instance_parent': dict(asset_path=I, source_asset_path=G2, parent_hash=live.iface(api, I)['parent_hash']),
            'add_pcg_graph_parameter': dict(asset_path=G, parameter_name='P_new', kind='double'),
            'add_pcg_graph_enum_parameter': dict(asset_path=G, parameter_name='P_newenum', enum_path=live.ENUM),
            'add_pcg_graph_asset_parameter': dict(asset_path=G, parameter_name='P_newasset', class_path='/Script/Engine.StaticMesh', soft=True),
            'add_pcg_graph_class_parameter': dict(asset_path=G, parameter_name='P_newclass', base_class_path='/Script/Engine.Actor'),
            'rename_pcg_graph_parameter': dict(**pr(G, 'P_double'), new_name='P_double2'),
            'remove_pcg_graph_parameter': pr(G, 'P_double'),
            'edit_pcg_graph_parameter_override': dict(**pr(I, 'P_int'), action='disable_override'),
            'set_pcg_graph_parameter_scalar': dict(**pr(I, 'P_float'), value=3.5),
            'set_pcg_graph_parameter_text': dict(**pr(G, 'P_string'), value='mcp'),
            'set_pcg_graph_parameter_vector': dict(**pr(G, 'P_vector'), x=1, y=2, z=3),
            'set_pcg_graph_parameter_enum': dict(**pr(G, 'P_enum'), value='ECC_Camera'),
            'set_pcg_graph_parameter_int64': dict(**pr(G, 'P_int64'), value='123456789012'),
            'set_pcg_graph_parameter_rotator': dict(**pr(G, 'P_rotator'), pitch=1, yaw=2, roll=3),
            'set_pcg_graph_parameter_transform': dict(**pr(G, 'P_transform'), transform={'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Translation': {'X': 1, 'Y': 2, 'Z': 3},
                                                                                       'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}),
            'set_pcg_graph_parameter_string_array': dict(**pr(G, 'P_name_array'), values=['A']),
            'set_pcg_graph_parameter_scalar_array': dict(**pr(G, 'P_float_array'), values=[1.5]),
            'set_pcg_graph_parameter_vector_array': dict(**pr(G, 'P_vector_array'), values=[{'X': 1, 'Y': 2, 'Z': 3}]),
            'inspect_pcg_graph_parameter_array': pr(G, 'P_int_array'),
            'set_pcg_graph_parameter_asset': dict(**pr(G, 'P_object'), source_asset_path=live.MESH),
            'set_pcg_graph_parameter_class': dict(**pr(G, 'P_class'), class_path='/Script/Engine.StaticMeshActor'),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        part2 = {t for t in tools if t.startswith(('set_pcg_graph_parameter', 'add_pcg_graph_', 'rename_pcg_graph_parameter', 'remove_pcg_graph_parameter',
                                                  'edit_pcg_graph_parameter', 'inspect_pcg_graph_parameter', 'inspect_pcg_graph_interface'))
                 or 'graph_instance' in t}
        part2 -= {'add_pcg_graph_pin'}
        assert part2 == set(args), sorted(part2 ^ set(args))
        assert len(args) == 24, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})
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
        after = live.settled(api)
        assert after == before, ('dry runs changed parameters', live.diff(before, after)[:5])
        for created in ('PCGI_McpNew', 'PCGI_McpDup'):
            assert httpx.get(BASE + '/assets/describe', params={'asset_path': n(created)}, timeout=60).status_code >= 400, created
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} PCG parameter MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); interfaces unchanged')
        assert not guarded, guarded
    finally:
        for p in (I, G, G2):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
