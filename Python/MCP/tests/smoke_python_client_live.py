"""ue5_client: parsed replies, errors, variants, search, the map's accuracy and the skill's example, against a live editor."""
import inspect
import json
import re
import sys
from pathlib import Path

sys.argv = [sys.argv[0], '--port', 'not-a-number']  # A script's own arguments must not reach the server's parser.
from ue5_client import MAP_FILE, UE5Error, _server, ue  # noqa: E402

ROOT = MAP_FILE.parent
assert sys.argv[1:] == ['--port', 'not-a-number'], 'the script lost its arguments'
tools = json.loads(MAP_FILE.read_text(encoding='utf-8'))['tools']

# The map is accurate: every entry is callable, in the file and at the line it says.
for name, tool in tools.items():
    function = getattr(_server, name)
    assert callable(function) and inspect.signature(function), name
    lines = (ROOT / tool['file']).read_text(encoding='utf-8').splitlines()
    assert tool['line'] > 0 and re.match(rf'(async )?def {name}\(|{name} = ', lines[tool['line'] - 1]), (name, tool['line'])
print(len(tools), 'functions checked against their files')
for feature in {t['feature'] for t in tools.values()}:
    assert f'`{feature}.py`' in (ROOT / 'FEATURE_MAP.md').read_text(encoding='utf-8'), feature

# Search and help.
assert any('niagara' in row['name'] for row in ue.find('niagara renderer')), 'search'
assert all(row['feature'] == 'blueprints' for row in ue.find('graph', feature='blueprints'))
assert 'Python/MCP/ue5_tools/blueprints.py' in ue.describe('connect_pins') and 'bp_path' in ue.describe('connect_pins')
try:
    ue.conect_pins
    raise AssertionError('unknown tool allowed')
except AttributeError as error:
    assert 'connect_pins' in str(error), error
try:
    ue.httpx  # Module-level helpers are not tools.
    raise AssertionError('helper exposed')
except AttributeError:
    pass

# The example from the skill, run for real.
BP = '/Game/UE5MCP_Test/PyClient/BP_MCP_Client'
_server.delete_asset(BP)  # May not exist; this form doesn't raise.
try:
    assert ue.get_ue_editor_status()['project_name']
    ue.create_blueprint(BP, '/Script/Engine.Actor')
    r = ue.edit_blueprint_graph(BP, [
        {'id': 'start', 'tool': 'add_event_to_graph', 'args': {'event_name': 'Go', 'is_custom': True, 'event_signature': ''}},
        {'id': 'say', 'tool': 'add_function_call_to_graph', 'args': {'function_name': 'PrintString', 'class_to_call': '/Script/Engine.KismetSystemLibrary'}},
    ], [['start.then', 'say.execute']], [['say.InString', 'Hello']])
    assert len(r['nodes']) == 2 and r['nodes'][1]['node_id'], r
    assert ue.organize_blueprint_graph(BP)['overlaps_after'] == 0
    assert isinstance(ue.get_graph(BP, 'EventGraph'), list), 'lists stay plain'
    assert ue.compile_blueprint(BP)['success'] is True
    # Failures raise, whichever route produced them, and say what to do.
    try:
        ue.connect_pins(BP, 'EventGraph', r['nodes'][0]['node_id'], 'nope', r['nodes'][1]['node_id'], 'execute')
        raise AssertionError('no error')
    except UE5Error as error:
        assert "no pin 'nope'" in error.message and error.fix and error.tool == 'connect_pins', error
    try:
        ue.compile_blueprint('/Game/NoSuchBlueprint')
        raise AssertionError('no error')
    except UE5Error as error:
        assert error.kind == 'not_found', error
    # A variant of a merged tool is callable by its own name.
    variant = next(name for name, tool in tools.items() if tool['kind'] == 'variant')
    assert callable(getattr(ue, variant))
finally:
    _server.delete_asset(BP)

# An unreachable editor raises rather than crashing with a network error.
from ue5_client import Client  # noqa: E402
try:
    Client('http://127.0.0.1:9').get_ue_editor_status()
    raise AssertionError('no error')
except UE5Error as error:
    assert 'not reachable' in error.message, error
print('Python client verified')
