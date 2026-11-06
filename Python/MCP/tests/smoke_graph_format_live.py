"""organize_blueprint_graph on a real graph, a cycle, separate groups, a subset, comments, and bad input."""
import json
import sys

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
J = json.loads
BP = '/Game/UE5MCP_Test/Format/BP_MCP_Format'
EG = 'EventGraph'
KSL = '/Script/Engine.KismetSystemLibrary'


def failed(text):
    r = J(text)
    assert r['success'] is False and r['errorMessage'], r
    return r['errorMessage']


m.delete_asset(BP)
try:
    m.create_blueprint(BP, '/Script/Engine.Actor')
    # An execution chain whose nodes all start on top of each other, with pure inputs and a loop back to the start.
    add = lambda name, *a: J(getattr(m, name)(BP, EG, *a))['node_id']
    begin = add('add_event_to_graph', 'ReceiveBeginPlay')
    custom = add('add_event_to_graph', 'Again', True, '')
    first = add('add_branch_node_to_graph')
    say = [add('add_function_call_to_graph', 'PrintString', KSL) for _ in range(4)]
    random = add('add_function_call_to_graph', 'RandomBool', '/Script/Engine.KismetMathLibrary')
    m.compile_blueprint(BP)
    call = add('add_function_call_to_graph', 'Again', f'{BP}.BP_MCP_Format_C')
    links = [(begin, 'then', first, 'execute'), (custom, 'then', first, 'execute'), (random, 'ReturnValue', first, 'Condition'),
             (first, 'then', say[0], 'execute'), (first, 'else', say[1], 'execute'), (say[0], 'then', say[2], 'execute'),
             (say[2], 'then', call, 'execute'), (say[1], 'then', say[3], 'execute')]
    for a, pa, b, pb in links:
        assert J(m.connect_pins(BP, EG, a, pa, b, pb))['success']
    lonely = add('add_function_call_to_graph', 'PrintString', KSL)   # A separate group.
    m.add_comment_node_to_graph(BP, EG, 'Group')
    r = J(m.organize_blueprint_graph(BP, dry_run=True))
    assert r['dry_run'] and r['nodes'] == 13 and r['overlaps_before'] > 0 and r['overlaps_after'] == 0, r
    assert J(m.organize_blueprint_graph(BP, dry_run=True))['overlaps_before'] == r['overlaps_before'], 'dry run moved nodes'

    r = J(m.organize_blueprint_graph(BP))
    print({k: r[k] for k in ('nodes', 'wires', 'groups', 'width', 'height', 'crossings_before', 'crossings_after', 'overlaps_before', 'overlaps_after')})
    assert r['overlaps_after'] == 0 and r['crossings_after'] == 0 and r['groups'] == 5, r
    print('comments', r['comments_resized'], r['comments_left_in_place'])
    assert r['comments_resized'] + r['comments_left_in_place'] == 1, r
    placed = {p['node_id']: (p['x'], p['y']) for p in r['positions']}
    # Reads left to right, and the straight run after the branch keeps one row.
    assert placed[begin][0] < placed[first][0] < placed[say[0]][0] < placed[say[2]][0] < placed[call][0], placed
    assert placed[random][0] < placed[first][0], placed
    assert placed[say[0]][1] == placed[say[2]][1] == placed[call][1], placed
    assert all(v % 16 == 0 for xy in placed.values() for v in xy), placed
    assert J(m.compile_blueprint(BP))['success'], 'formatting broke the Blueprint'

    # Formatting again changes nothing.
    again = J(m.organize_blueprint_graph(BP))
    assert {p['node_id']: (p['x'], p['y']) for p in again['positions']} == placed, 'not stable'

    # A subset moves only those nodes.
    r = J(m.organize_blueprint_graph(BP, node_ids=[say[1], say[3]], column_spacing=300))
    assert r['nodes'] == 2 and r['wires'] == 1, r
    subset = {p['node_id']: (p['x'], p['y']) for p in r['positions']}
    assert subset[say[3]][0] > subset[say[1]][0], subset
    assert J(m.compile_blueprint(BP))['success']

    # Bad input.
    assert 'not a node id' in failed(m.organize_blueprint_graph(BP, node_ids=['nope']))
    assert 'get_graph' in failed(m.organize_blueprint_graph(BP, node_ids=['A' * 32]))
    assert 'Graph not found' in failed(m.organize_blueprint_graph(BP, 'NoGraph'))
    assert 'spacing' in failed(m.organize_blueprint_graph(BP, column_spacing=-1))
    assert 'list_assets' in failed(m.organize_blueprint_graph('/Game/NoSuchBlueprint'))
    # An empty graph is fine.
    m.delete_asset(BP)
    m.create_blueprint(BP, '/Script/Engine.Actor')
    m.create_function(BP, 'Empty', '', '')
    assert J(m.organize_blueprint_graph(BP, 'Empty'))['success']
finally:
    m.delete_asset(BP)

# Real graphs from the project and the RTS, without moving anything.
for bp in ('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', '/Game/RtsDemo/BP_RtsSoldier', '/Game/RtsDemo/BP_RtsController'):
    r = J(m.organize_blueprint_graph(bp, dry_run=True))
    print(bp.rsplit('/', 1)[1], {k: r[k] for k in ('nodes', 'wires', 'groups', 'crossings_before', 'crossings_after', 'overlaps_before', 'overlaps_after')})
    assert r['overlaps_after'] == 0, r
print('Graph format verified')
