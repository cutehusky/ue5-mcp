"""Class search, console commands, Blueprint and project errors, and log filters, against a live editor."""
import json
import sys
import time

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
J = json.loads
ROOT = '/Game/UE5MCP_Test/Diagnostics'
BROKEN, GOOD = f'{ROOT}/BP_MCP_Broken', f'{ROOT}/BP_MCP_Fine'


def failed(text):
    r = J(text)
    assert r['success'] is False and r['errorMessage'], r
    return r['errorMessage']


def names(**kw):
    r = J(m.list_ue_classes(limit=2000, **kw))
    return {c['name']: c for c in r['classes']}


# Classes: built in, custom C++, and Blueprints, filtered several ways.
actors = names(search='Character', category='character', can_be_parent=True)
assert actors['Character']['source'] == 'engine_cpp' and actors['Character']['can_be_blueprint_parent'], actors['Character']
assert 'DemoForPluginGameMode' in names(source='project_cpp', module='DemoForPlugin', include_abstract=True), 'custom C++ class missing'
assert all(c['source'] == 'project_cpp' for c in names(source='project_cpp').values())
modes = names(parent_class='GameModeBase', source='blueprint')
assert 'BP_ThirdPersonGameMode_C' in modes and all(c['category'] == 'game_mode' for c in modes.values()), modes
assert 'Actor' in names(search='Actor', module='Engine')
assert names(parent_class='AActor', search='StaticMeshActor'), 'C++ spelling of a parent should resolve'
assert not any(n.startswith(('SKEL_', 'REINST_')) for n in names(source='blueprint'))
assert 'list_ue_classes' in failed(m.list_ue_classes(parent_class='NoSuchClassAtAll'))
assert 'source must' in failed(m.list_ue_classes(source='nope'))
print('classes found', len(names()))

# Console.
assert 'confirm' in failed(m.execute_console_command('r.VSync'))
for blocked in ('quit', 'EXIT', 'debug crash', 'py print(1)'):
    assert 'not allowed' in failed(m.execute_console_command(blocked, confirm=True)), blocked
assert 'one command' in failed(m.execute_console_command('stat fps | quit', confirm=True))
assert 'did not recognise' in failed(m.execute_console_command('nosuchcommandatall', confirm=True))
r = J(m.execute_console_command('r.VSync', confirm=True))
assert r['success'] and 'r.VSync' in r['output'], r
print('console output', r['output'].strip()[:120])

# Blueprint errors: a broken one is reported, a good one is not, and neither is left dirty.
m.delete_asset(BROKEN)
m.delete_asset(GOOD)
try:
    for bp in (BROKEN, GOOD):
        m.create_blueprint(bp, '/Script/Engine.Actor')
    node = J(m.add_function_call_to_graph(BROKEN, 'EventGraph', 'SetVisibility', '/Script/Engine.SceneComponent'))['node_id']
    event = J(m.add_event_to_graph(BROKEN, 'EventGraph', 'ReceiveBeginPlay'))['node_id']
    m.connect_pins(BROKEN, 'EventGraph', event, 'then', node, 'execute')
    r = J(m.list_blueprint_errors(ROOT))
    assert r['clean'] is False and r['checked'] == 2 and r['errors'] > 0 and not r['truncated'], r
    assert [b['bp_path'].split('.')[-1] for b in r['blueprints']] == ['BP_MCP_Broken'], r
    assert r['blueprints'][0]['messages'][0]['node_id'] == node, r
    assert J(m.list_blueprint_errors(ROOT, search='BP_MCP_Fine'))['clean'] is True
    assert J(m.list_blueprint_errors(ROOT, limit=1))['truncated'] is True
    assert 'root must' in failed(m.list_blueprint_errors('/Engine'))
finally:
    m.delete_asset(BROKEN)
    m.delete_asset(GOOD)

# Project errors.
r = J(m.get_project_errors(5))
assert {'log', 'message_logs', 'cpp_build', 'clean'} <= set(r) and len(r['log']['error_lines']) <= 5, r
print('project errors: log', r['log']['errors'], 'build log', r['cpp_build']['available'])

# Logs: this session's file, exact filters, and reading only what is new.
r = J(m.get_editor_logs(limit=5))
assert r['returned'] == 5 and r['next_line'] > 5, r
start = r['next_line']
J(m.execute_console_command('r.VSync', confirm=True))
for _ in range(40):  # Log lines reach the file shortly after they are written.
    new = J(m.get_editor_logs(search='UE5_MCP console', since_line=start))
    if new['returned']:
        break
    time.sleep(.25)
assert new['returned'] >= 1 and all('UE5_MCP console' in line for line in new['lines']), new
assert all(': Error: ' in line for line in J(m.get_editor_logs(severity='Error', limit=20))['lines'])
assert all('LogTemp: ' in line for line in J(m.get_editor_logs(category='LogTemp', limit=20))['lines'])
assert 'severity must' in failed(m.get_editor_logs(severity='Loud'))
print('Project diagnostics verified')
