"""Exercise FastMCP argument decoding for typed-container authoring."""
import asyncio
import json
import sys

import httpx
from smoke_navigation_mesh import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server


async def run():
    saved = json.loads((PROJECT / 'Saved/UE5MCP_Test/state_tree_container_parameters.json').read_text())
    path = saved['paths'][0]
    fields = saved['snapshots'][path]['parameters']['fields']
    array = next(field for field in fields if field['name'] == 'ArrayFloat')
    replacement = next(field for field in fields if field['name'] == 'Replacement')
    base = 'http://127.0.0.1:8080'
    mcp_server.BASE_URL = base
    before = httpx.get(base + '/state-trees/inspect', params={'asset_path': path}, timeout=180).json()
    count = 0
    for value in ['["7","8"]', ['7', '8'], []]:
        for tool, arguments in [
            ('edit_state_tree_parameter', {'asset_path': path, 'operation': 'update',
                                          'item_id': array['id'], 'value': value, 'dry_run': True}),
            ('replace_state_tree_parameter_type', {'asset_path': path, 'item_id': replacement['id'],
                                                  'parameter_type': 'Float', 'container_type': 'Array',
                                                  'value': value, 'confirm': True, 'dry_run': True}),
        ]:
            result = await mcp_server.mcp.call_tool(tool, arguments)
            blocks = result[0] if isinstance(result, tuple) else result
            payload = json.loads(''.join(block.text for block in blocks if hasattr(block, 'text')))
            assert payload['dry_run']
            assert payload['would_change'] == (tool == 'replace_state_tree_parameter_type' or value != []), (tool, value)
            count += 1
    for invalid in [[1, 2], [['nested']], {'bad': 'value'}]:
        try:
            await mcp_server.mcp.call_tool('edit_state_tree_parameter', {
                'asset_path': path, 'operation': 'update', 'item_id': array['id'], 'value': invalid,
                'dry_run': True})
        except Exception as error:
            assert 'validation' in str(error).lower(), str(error)
        else:
            raise AssertionError('Invalid MCP typed-string container accepted')
    after = httpx.get(base + '/state-trees/inspect', params={'asset_path': path}, timeout=180).json()
    assert after == before
    evidence = {'passed': True, 'positive_cases': count, 'negative_cases': 3,
                'tools': ['edit_state_tree_parameter', 'replace_state_tree_parameter_type']}
    (PROJECT / 'Saved/Verification/2026-10-25/Container-MCP.json').write_text(json.dumps(evidence, indent=2))
    print('MCP typed containers: encoded JSON/direct lists/empty lists, both tools, invalid shapes and source preservation: OK')


if __name__ == '__main__':
    asyncio.run(run())
