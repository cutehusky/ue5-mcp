"""Registered required-event MCP dispatch against a prepared REST fixture."""
import asyncio
import json
import sys
from smoke_navigation_mesh import PROJECT
from state_tree_verification import StateTreeVerification

sys.path.insert(0, str(PROJECT / 'Plugins/UE5_MCP/Python/MCP'))
import mcp_server


async def run():
    test = StateTreeVerification('state_tree_required_events', 'http://127.0.0.1:8080')
    saved = json.loads(test.manifest.read_text())
    path = saved['paths'][0]
    state = next(row for row in saved['snapshots'][path]['states'] if row['name'] == 'EventState')
    transition = state['transitions'][0]
    before = test.inspect(path)
    for name, arguments in [
        ('set_state_tree_required_event', {'asset_path': path, 'state_id': state['id'],
                                         'payload_struct_path': state['required_payload_struct'],
                                         'consume_event': False, 'dry_run': True}),
        ('edit_state_tree_transition', {'asset_path': path, 'state_id': state['id'],
                                       'item_id': transition['id'], 'operation': 'update',
                                       'trigger': 'OnEvent', 'payload_struct_path': transition['payload_struct'],
                                       'consume_event': True, 'dry_run': True}),
    ]:
        result = await mcp_server.mcp.call_tool(name, arguments)
        blocks = result[0] if isinstance(result, tuple) else result
        response = json.loads(''.join(block.text for block in blocks if hasattr(block, 'text')))
        assert response['dry_run'] and response['would_change'], (name, response)
    assert test.inspect(path) == before
    (PROJECT / 'Saved/Verification/2026-10-25/RequiredEvents-MCP.json').write_text(
        json.dumps({'passed': True, 'tools': ['set_state_tree_required_event', 'edit_state_tree_transition']}, indent=2))
    print('Required state/transition event MCP payload and consumption dispatch: OK')


if __name__ == '__main__':
    asyncio.run(run())
