"""Build and playtest a small game using only the advertised core tools: run through a walled arena and collect 5 orbs.

Needs a live windowed editor. Tools outside CORE_TOOLS are refused, so a failure here means the core list has a gap.
Assets stay in /Game/OrbRun. Project settings are not changed; the map names its own GameMode.
"""
import json
import sys
import time

PLAY_ONLY = 'play' in sys.argv  # Replay the saved game, such as after restarting the editor.
sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402
from ue5_tools.catalog import CORE_TOOLS  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
ROOT = '/Game/OrbRun'
MAP, MODE, ORB, HUD = f'{ROOT}/Lvl_OrbRun', f'{ROOT}/BP_OrbMode', f'{ROOT}/BP_Orb', f'{ROOT}/WBP_OrbHud'
MODE_C, ORB_C, HUD_C = f'{MODE}.BP_OrbMode_C', f'{ORB}.BP_Orb_C', f'{HUD}.WBP_OrbHud_C'
GOAL = 5
GS, KSL = '/Script/Engine.GameplayStatics', '/Script/Engine.KismetSystemLibrary'
EG = 'EventGraph'


def T(name, *a, **kw):
    assert name in CORE_TOOLS, f'not in the core list: {name}'
    text = getattr(m, name)(*a, **kw)
    print(f'{name}: {str(text)[:200]}')
    assert 'errorMessage' not in str(text), (name, a, kw, text)
    return text


def nodes(bp):
    return json.loads(getattr(m, 'get_graph')(bp, EG))


def add(bp, name, *a, **kw):
    """Add a node and return its id."""
    return json.loads(T(name, bp, EG, *a, **kw))['node_id']


def pins(bp, node):
    return [p['Name'] for n in nodes(bp) if n['Id'] == node for p in n['Pins']]


def wire(bp, *links):
    for a, pa, b, pb in links:
        T('connect_pins', bp, EG, a, pa, b, pb)


def compiled(bp):
    r = json.loads(T('compile_blueprint', bp))
    assert r['success'], r
    T('save_asset', bp)


def hud():
    T('create_widget_blueprint', HUD)
    T('add_widget_to_blueprint', HUD, '/Script/UMG.CanvasPanel', 'Root')
    T('add_widget_to_blueprint', HUD, '/Script/UMG.TextBlock', 'Label', 'Root')
    T('add_widget_to_blueprint', HUD, '/Script/UMG.TextBlock', 'ScoreText', 'Root')
    T('set_widget_properties', HUD, 'Label', {'Text': 'Orbs collected', 'bIsVariable': 'true'})
    T('set_widget_properties', HUD, 'ScoreText', {'Text': '0', 'bIsVariable': 'true', 'Slot.LayoutData.Offsets.Top': '40'})
    compiled(HUD)
    show = add(HUD, 'add_event_to_graph', 'ShowScore', True, 'int32 Value')
    text = add(HUD, 'add_function_call_to_graph', 'Conv_IntToText', '/Script/Engine.KismetTextLibrary')
    score = add(HUD, 'add_variable_to_graph', 'ScoreText', False)
    put = add(HUD, 'add_function_call_to_graph', 'SetText', '/Script/UMG.TextBlock')
    print('pins', {x: pins(HUD, x) for x in (show, text, score, put)})
    wire(HUD, (show, 'then', put, 'execute'), (show, 'Value', text, 'Value'), (text, 'ReturnValue', put, 'InText'),
         (score, 'ScoreText', put, 'self'))
    win = add(HUD, 'add_event_to_graph', 'ShowWin', True, '')
    label = add(HUD, 'add_variable_to_graph', 'Label', False)
    say = add(HUD, 'add_function_call_to_graph', 'SetText', '/Script/UMG.TextBlock')
    T('set_pin_default_value', HUD, EG, say, 'InText', 'You win!')
    wire(HUD, (win, 'then', say, 'execute'), (label, 'Label', say, 'self'))
    compiled(HUD)


def mode():
    T('create_blueprint', MODE, '/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C')
    T('add_variable_to_bp', MODE, 'int32 Score')
    T('add_variable_to_bp', MODE, 'bool bWon')
    T('add_variable_to_bp', MODE, 'WBP_OrbHud_C* Hud')
    begin = add(MODE, 'add_event_to_graph', 'ReceiveBeginPlay')
    make = add(MODE, 'add_generic_node_to_graph', 'K2Node_CreateWidget')
    print('create widget pins', pins(MODE, make))
    T('set_pin_default_value', MODE, EG, make, 'Class', HUD_C)
    keep = add(MODE, 'add_variable_to_graph', 'Hud', True)
    show = add(MODE, 'add_function_call_to_graph', 'AddToViewport', '/Script/UMG.UserWidget')
    wire(MODE, (begin, 'then', make, 'execute'), (make, 'then', keep, 'execute'), (make, 'ReturnValue', keep, 'Hud'),
         (keep, 'then', show, 'execute'), (keep, 'Output_Get', show, 'self'))
    event = add(MODE, 'add_event_to_graph', 'AddOrb', True, '')
    get = add(MODE, 'add_variable_to_graph', 'Score', False)
    inc = add(MODE, 'add_math_node_to_graph', 'Add_IntInt')
    put = add(MODE, 'add_variable_to_graph', 'Score', True)
    gte = add(MODE, 'add_math_node_to_graph', 'GreaterEqual_IntInt')
    branch = add(MODE, 'add_branch_node_to_graph')
    won = add(MODE, 'add_variable_to_graph', 'bWon', True)
    print('pins', {x: pins(MODE, x) for x in (event, get, inc, put, gte, branch, won)})
    T('set_pin_default_value', MODE, EG, inc, 'B', '1')
    T('set_pin_default_value', MODE, EG, gte, 'B', str(GOAL))
    T('set_pin_default_value', MODE, EG, won, 'bWon', 'true')
    hud1, hud2 = add(MODE, 'add_variable_to_graph', 'Hud', False), add(MODE, 'add_variable_to_graph', 'Hud', False)
    update = add(MODE, 'add_function_call_to_graph', 'ShowScore', HUD_C)
    cheer = add(MODE, 'add_function_call_to_graph', 'ShowWin', HUD_C)
    wire(MODE, (put, 'then', update, 'execute'), (hud1, 'Hud', update, 'self'), (put, 'Output_Get', update, 'Value'),
         (update, 'then', branch, 'execute'), (won, 'then', cheer, 'execute'), (hud2, 'Hud', cheer, 'self'))
    wire(MODE, (event, 'then', put, 'execute'), (get, 'Score', inc, 'A'), (inc, 'ReturnValue', put, 'Score'),
         (put, 'Output_Get', gte, 'A'), (gte, 'ReturnValue', branch, 'Condition'),
         (branch, 'then', won, 'execute'))
    compiled(MODE)


def orb():
    T('create_blueprint', ORB, '/Script/Engine.Actor')
    T('add_component_to_bp', ORB, 'StaticMeshComponent', 'Mesh', '')
    T('set_component_property', ORB, 'Mesh', {
        'StaticMesh': "/Script/Engine.StaticMesh'/Engine/BasicShapes/Sphere.Sphere'",
        'RelativeScale3D': '(X=1,Y=1,Z=1)',
        'BodyInstance.CollisionProfileName': 'OverlapAllDynamic',
        'bGenerateOverlapEvents': 'true',
    })
    event = add(ORB, 'add_event_to_graph', 'ReceiveActorBeginOverlap')
    is_player = add(ORB, 'add_dynamic_cast_node_to_graph', 'Character')
    game_mode = add(ORB, 'add_function_call_to_graph', 'GetGameMode', GS)
    as_mode = add(ORB, 'add_dynamic_cast_node_to_graph', MODE_C)
    call = add(ORB, 'add_function_call_to_graph', 'AddOrb', MODE_C)
    destroy = add(ORB, 'add_function_call_to_graph', 'K2_DestroyActor', '/Script/Engine.Actor')
    print('pins', {x: pins(ORB, x) for x in (event, is_player, game_mode, as_mode, call, destroy)})
    wire(ORB, (event, 'then', is_player, 'execute'), (event, 'OtherActor', is_player, 'Object'),
         (is_player, 'then', as_mode, 'execute'), (game_mode, 'ReturnValue', as_mode, 'Object'),
         (as_mode, 'then', call, 'execute'), (as_mode, 'AsBP Orb Mode', call, 'self'), (call, 'then', destroy, 'execute'))
    compiled(ORB)


def level():
    T('create_editor_world', MAP, '/Game/ThirdPerson/Lvl_ThirdPerson', True, 'discard', True)
    T('load_editor_world', MAP, 'discard', True)
    T('set_editor_world_settings', class_settings={'DefaultGameMode': MODE_C}, confirm=True, world_path=MAP, save=True)
    T('save_editor_world', confirm=True)
    for x, y, z in probe():
        T('spawn_editor_actor', asset_path=ORB, location={'X': x, 'Y': y, 'Z': z})
    T('save_editor_world', confirm=True)


def orb_actors(session):
    return [a for a in session['actors'] if a['class'].endswith('BP_Orb_C')]


def orbs_left():
    return len(orb_actors(json.loads(T('inspect_play_session', 'BP_Orb'))))


def start_play():
    T('control_ue_play_session', 'start')
    for _ in range(60):
        if json.loads(T('get_ue_editor_status'))['is_playing']:
            break
        time.sleep(1)
    last = None
    for _ in range(30):  # Let the pawn land.
        time.sleep(1)
        z = json.loads(T('inspect_play_session', 'BP_Orb'))['player_location'][2]
        if z == last:
            return
        last = z
    raise AssertionError('the pawn never landed')


def probe():
    """Walk forward once and return points on that path, so every orb sits where the player will really go."""
    start_play()
    path = []
    try:
        T('send_play_input', 'W', 'press')
        for _ in range(GOAL):
            time.sleep(.4)
            path.append(json.loads(T('inspect_play_session', 'BP_Orb'))['player_location'])
        T('send_play_input', 'W', 'release')
    finally:
        T('control_ue_play_session', 'stop')
    while json.loads(T('get_ue_editor_status'))['is_playing']:
        time.sleep(1)
    print('walked', path)
    return path


def playtest():
    start_play()
    try:
        session = json.loads(T('inspect_play_session', 'BP_Orb'))
        assert 'BP_OrbMode' in session['game_mode'] and len(orb_actors(session)) == GOAL, session
        print('start', session['player_location'], [a['location'] for a in orb_actors(session)])
        T('request_editor_screenshot', 'OrbRun_start', True)
        T('send_play_input', 'W', 'press')
        time.sleep(5)
        T('send_play_input', 'W', 'release')
        print('player', json.loads(T('inspect_play_session', 'BP_Orb'))['player_location'])
        assert orbs_left() == 0, 'orbs were not all collected'
        values = {p['name']: p['value'] for p in json.loads(T('read_play_actor_properties', 'game_mode'))['properties']}
        assert values['Score'] == str(GOAL) and values['bWon'] == 'True', values
        time.sleep(1)
        T('request_editor_screenshot', 'OrbRun_win', True)
        time.sleep(3)
    finally:
        T('control_ue_play_session', 'stop')
    print('played: all orbs collected')


if __name__ == '__main__':
    if PLAY_ONLY:
        T('load_editor_world', MAP, 'discard', True)
        playtest()
        sys.exit()
    T('load_editor_world', '/Game/ThirdPerson/Lvl_ThirdPerson', 'discard', True)
    for path in (MAP, ORB, MODE, HUD):  # A rerun starts clean.
        getattr(m, 'delete_asset')(path)
    for step in (hud, mode, orb, level, playtest):
        print('==', step.__name__)
        step()
