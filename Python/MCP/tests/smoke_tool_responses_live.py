"""Standard tool replies, add-node results, batch graph edits with rollback and property suggestions, against a live editor."""
import asyncio
import json
import sys

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
BP = '/Game/UE5MCP_Test/Responses/BP_MCP_Responses'
EG = 'EventGraph'
J = json.loads


def client(name, **arguments):
    """Call a tool as an MCP client does."""
    got = asyncio.run(m.mcp.call_tool(name, arguments))
    return J((got[0] if isinstance(got, tuple) else got)[0].text)


def failed(text):
    r = J(text)
    assert r['success'] is False and r['errorMessage'] and r['tool'], r
    assert not r['errorMessage'].startswith('Error') and r['errorKind'] and r['fix'], r
    return r['errorMessage']


m.delete_asset(BP)
try:
    assert J(m.create_blueprint(BP, '/Script/Engine.Actor'))['success']
    # Add-node tools say what they added.
    r = J(m.add_branch_node_to_graph(BP, EG))
    assert r['success'] and r['node_id'] and {'name': 'Condition', 'direction': 'input', 'type': 'bool'} in r['pins'], r
    assert r['node_id'] in {n['Id'] for n in J(m.get_graph(BP, EG))}
    # Failures have one shape, whichever route produced them.
    failed(m.connect_pins(BP, EG, r['node_id'], 'nope', r['node_id'], 'nope'))   # plain text route
    failed(m.inspect_blueprint_class_defaults('/Game/NoSuchBlueprint', '', 1))
    # Clients get one shape for every reply: object, list, or failure.
    r = client('get_ue_editor_status')
    assert r['success'] is True and r['tool'] == 'get_ue_editor_status' and 'engine_version' in r, r
    r = client('get_graph', bp_path=BP, graph_name=EG)
    assert r['success'] is True and isinstance(r['result'], list) and r['result'], r
    r = client('compile_blueprint', bp_path='/Game/NoSuchBlueprint')
    assert r['success'] is False and r['errorKind'] == 'not_found' and r['fix'] and r['arguments'], r
    # Create tools return the id of what they made.
    r = client('add_branch_node_to_graph', bp_path=BP, graph_name=EG)
    assert r['id'] == r['node_id'] and r['id_source'] == 'reply', r
    r = client('add_variable_to_bp', bp_path=BP, var_signature='int32 Lives')
    assert r['id'] == 'Lives' and r['id_source'] == 'arguments', r
    r = client('spawn_editor_actor', actor_class='/Script/Engine.Actor')
    assert r['success'] and 'Actor' in r['id'], r
    m.delete_editor_actor(r['id'])
    # Errors say what is wrong and how to fix it.
    node = J(m.add_branch_node_to_graph(BP, EG))['node_id']
    message = failed(m.connect_pins(BP, EG, node, 'nope', node, 'Condition'))
    assert "no pin 'nope'" in message and 'Condition (input bool)' in message, message
    message = failed(m.connect_pins(BP, EG, 'A' * 32, 'then', node, 'execute'))
    assert 'get_graph' in message, message
    assert 'list_assets' in failed(m.get_blueprint_variables('/Game/NoSuchBlueprint'))
    # Nested property names are suggested.
    m.add_component_to_bp(BP, 'StaticMeshComponent', 'Mesh', '')
    message = failed(m.set_component_property(BP, 'Mesh', {'CollisionProfileName': 'NoCollision'}))
    assert 'BodyInstance.CollisionProfileName' in message, message
    # Batch: everything in one call.
    count = len(J(m.get_graph(BP, EG)))
    good = [{'id': 'go', 'tool': 'add_event_to_graph', 'args': {'event_name': 'Go', 'is_custom': True, 'event_signature': ''}},
            {'id': 'say', 'tool': 'add_function_call_to_graph', 'args': {'function_name': 'PrintString', 'class_to_call': '/Script/Engine.KismetSystemLibrary'}}]
    r = J(m.edit_blueprint_graph(BP, good, [['go.then', 'say.execute']], [['say.InString', 'Hello']]))
    assert r['success'] and len(r['nodes']) == 2, r
    assert len(J(m.get_graph(BP, EG))) == count + 2
    say = next(n for n in J(m.get_graph(BP, EG)) if n['Id'] == r['nodes'][1]['node_id'])
    assert any(p['Name'] == 'InString' for p in say['Pins']), say
    # Batch: a bad link removes what the call added.
    count = len(J(m.get_graph(BP, EG)))
    bad = [{'id': 'other', 'tool': 'add_branch_node_to_graph', 'args': {}}]
    assert 'other.nope' in failed(m.edit_blueprint_graph(BP, bad, [['other.nope', 'other.Condition']]))
    assert len(J(m.get_graph(BP, EG))) == count
    failed(m.edit_blueprint_graph(BP, [{'id': 'x', 'tool': 'delete_asset', 'args': {}}]))
    assert J(m.compile_blueprint(BP))['success']
    # An unreachable editor is a result, not an exception.
    m.BASE_URL = 'http://127.0.0.1:9'
    assert 'not reachable' in failed(m.get_ue_editor_status())
finally:
    m.BASE_URL = 'http://127.0.0.1:8080'
    m.delete_asset(BP)
print('Tool responses verified')
