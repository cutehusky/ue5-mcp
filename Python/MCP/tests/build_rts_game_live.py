"""Build a small top-down RTS in /Game/RtsDemo through MCP tools: left click ground to move the soldier, left click an enemy to attack.

Needs a live windowed editor. Project settings are not changed; the map names its own GameMode.
Pass play to replay the saved game with automated clicks. Playing moves the real system cursor.
"""
import json
import sys
import time

PLAY_ONLY = 'play' in sys.argv
sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
ROOT = '/Game/RtsDemo'
MAP, MODE, CTRL, CAM, SOLDIER, ENEMY = (f'{ROOT}/{n}' for n in ('Lvl_Rts', 'BP_RtsMode', 'BP_RtsController', 'BP_RtsCamera', 'BP_RtsSoldier', 'BP_RtsEnemy'))
BLUE, RED = f'{ROOT}/MI_RtsBlue', f'{ROOT}/MI_RtsRed'
ACTOR, PAWN, KSL, GS, PC = '/Script/Engine.Actor', '/Script/Engine.Pawn', '/Script/Engine.KismetSystemLibrary', '/Script/Engine.GameplayStatics', '/Script/Engine.PlayerController'
Y = dict(confirm=True)


def C(path):
    return f'{path}.{path.rsplit("/", 1)[1]}_C'


def T(name, *a, **kw):
    text = getattr(m, name)(*a, **kw)
    assert 'errorMessage' not in str(text), (name, a, kw, text)
    return text


def call(id_, function, owner):
    return {'id': id_, 'tool': 'add_function_call_to_graph', 'args': {'function_name': function, 'class_to_call': owner}}


def math(id_, function):
    return {'id': id_, 'tool': 'add_math_node_to_graph', 'args': {'function_name': function}}


def var(id_, name, setter=False):
    return {'id': id_, 'tool': 'add_variable_to_graph', 'args': {'var_name': name, 'is_setter': setter}}


def event(id_, name, signature=None):
    args = {'event_name': name}
    if signature is not None:
        args.update(is_custom=True, event_signature=signature)
    return {'id': id_, 'tool': 'add_event_to_graph', 'args': args}


def branch(id_):
    return {'id': id_, 'tool': 'add_branch_node_to_graph', 'args': {}}


def graph(bp, nodes, links, defaults=None):
    return json.loads(T('edit_blueprint_graph', bp, nodes, links, defaults or []))['nodes']


def done(bp):
    r = json.loads(T('compile_blueprint', bp))
    assert r['success'], r['messages']
    T('save_asset', bp)


def class_default(bp, path, value):
    rows = json.loads(T('inspect_blueprint_class_defaults', bp, path, 1000))['properties']
    old = next(r['value'] for r in rows if r['path'] == path)
    T('set_blueprint_class_default', bp, path, old, value, confirm=True)


def colours():
    parent = '/Game/LevelPrototyping/Materials/M_FlatCol'
    params = T('list_material_parameters', parent)
    print('flat colour parameters', params[:400])
    name = next(p['name'] for p in json.loads(params)['parameters'] if 'ector' in p['type'])
    for path, value in ((BLUE, 'R=0.05,G=0.2,B=1,A=1'), (RED, 'R=1,G=0.05,B=0.05,A=1')):
        T('create_asset', path, 'material_instance', parent_path=parent)
        T('set_material_parameter', path, name, 'vector', value)
        T('save_asset', path)


def body(bp, mesh, scale, material, profile='NoCollision', z=0):
    T('add_component_to_bp', bp, 'StaticMeshComponent', 'Body', '')
    T('set_component_property', bp, 'Body', {
        'StaticMesh': f"/Script/Engine.StaticMesh'/Engine/BasicShapes/{mesh}.{mesh}'",
        'RelativeScale3D': f'(X={scale[0]},Y={scale[1]},Z={scale[2]})', 'RelativeLocation': f'(X=0,Y=0,Z={z})',
        'BodyInstance.CollisionProfileName': profile,
        'OverrideMaterials': f"(\"/Script/Engine.MaterialInstanceConstant'{material}.{material.rsplit('/', 1)[1]}'\")",
    })


def enemy():
    T('create_blueprint', ENEMY, ACTOR)
    body(ENEMY, 'Cube', (1, 1, 1.6), RED, 'BlockAll')
    T('add_variable_to_bp', ENEMY, 'int32 Health')
    graph(ENEMY, [event('hit', 'TakeHit', ''), var('get', 'Health'), math('dec', 'Subtract_IntInt'), var('put', 'Health', True),
                  math('dead', 'GreaterEqual_IntInt'), branch('if'), call('die', 'K2_DestroyActor', ACTOR)],
          [['hit.then', 'put.execute'], ['get.Health', 'dec.A'], ['dec.ReturnValue', 'put.Health'], ['put.then', 'if.execute'],
           ['put.Output_Get', 'dead.A'], ['dead.ReturnValue', 'if.Condition'], ['if.then', 'die.execute']],
          [['dec.B', '1'], ['dead.B', '-3']])  # Health starts at 0: the third hit brings it to -3.
    done(ENEMY)


def soldier():
    T('create_blueprint', SOLDIER, '/Script/Engine.Character')
    body(SOLDIER, 'Cylinder', (0.7, 0.7, 1.76), BLUE)
    class_default(SOLDIER, 'AutoPossessAI', 'PlacedInWorldOrSpawned')
    for signature in ('Vector Destination', 'bool bHasDestination', f'{C(ENEMY).rsplit(".", 1)[1]}* Target', 'double NextAttack'):
        T('add_variable_to_bp', SOLDIER, signature)
    enemy_class = C(ENEMY)
    orders = graph(SOLDIER, [
        event('move', 'MoveToPoint', 'Vector Point'), var('dest', 'Destination', True), var('has', 'bHasDestination', True), var('clear', 'Target', True),
        event('attack', 'AttackEnemy', f'{enemy_class.rsplit(".", 1)[1]}* Enemy'), var('aim', 'Target', True), var('forget', 'bHasDestination', True),
    ], [['move.then', 'dest.execute'], ['move.Point', 'dest.Destination'], ['dest.then', 'has.execute'], ['has.then', 'clear.execute'],
        ['attack.then', 'aim.execute'], ['attack.Enemy', 'aim.Target'], ['aim.then', 'forget.execute']], [['has.bHasDestination', 'true']])
    graph(SOLDIER, [
        event('tick', 'ReceiveTick'), var('t1', 'Target'), call('valid', 'IsValid', KSL), branch('hasTarget'),
        call('me', 'K2_GetActorLocation', ACTOR), call('dist', 'GetDistanceTo', ACTOR), var('t2', 'Target'), math('near', 'Less_DoubleDouble'), branch('inRange'),
        call('now', 'GetGameTimeSinceCreation', ACTOR), var('next', 'NextAttack'), math('ready', 'GreaterEqual_DoubleDouble'), branch('canHit'),
        var('t3', 'Target'), call('hit', 'TakeHit', enemy_class), math('later', 'Add_DoubleDouble'), var('setNext', 'NextAttack', True),
        var('t4', 'Target'), call('there', 'K2_GetActorLocation', ACTOR), math('toEnemy', 'Subtract_VectorVector'), call('chase', 'AddMovementInput', PAWN),
        var('has', 'bHasDestination'), branch('going'), var('dest', 'Destination'), math('left', 'Vector_Distance2D'), math('far', 'Greater_DoubleDouble'), branch('notThere'),
        var('dest2', 'Destination'), math('toPoint', 'Subtract_VectorVector'), call('walk', 'AddMovementInput', PAWN),
    ], [
        ['tick.then', 'hasTarget.execute'], ['t1.Target', 'valid.Object'], ['valid.ReturnValue', 'hasTarget.Condition'],
        ['t2.Target', 'dist.OtherActor'], ['dist.ReturnValue', 'near.A'], ['hasTarget.then', 'inRange.execute'], ['near.ReturnValue', 'inRange.Condition'],
        ['inRange.then', 'canHit.execute'], ['now.ReturnValue', 'ready.A'], ['next.NextAttack', 'ready.B'], ['ready.ReturnValue', 'canHit.Condition'],
        ['canHit.then', 'hit.execute'], ['t3.Target', 'hit.self'], ['hit.then', 'setNext.execute'], ['now.ReturnValue', 'later.A'], ['later.ReturnValue', 'setNext.NextAttack'],
        ['inRange.else', 'chase.execute'], ['t4.Target', 'there.self'], ['there.ReturnValue', 'toEnemy.A'], ['me.ReturnValue', 'toEnemy.B'], ['toEnemy.ReturnValue', 'chase.WorldDirection'],
        ['hasTarget.else', 'going.execute'], ['has.bHasDestination', 'going.Condition'], ['going.then', 'notThere.execute'],
        ['me.ReturnValue', 'left.V1'], ['dest.Destination', 'left.V2'], ['left.ReturnValue', 'far.A'], ['far.ReturnValue', 'notThere.Condition'],
        ['notThere.then', 'walk.execute'], ['dest2.Destination', 'toPoint.A'], ['me.ReturnValue', 'toPoint.B'], ['toPoint.ReturnValue', 'walk.WorldDirection'],
    ], [['near.B', '230'], ['later.B', '1'], ['far.B', '60']])
    print('orders', [n['id'] for n in orders])
    done(SOLDIER)


def controller():
    T('create_blueprint', CTRL, PC)
    class_default(CTRL, 'bShowMouseCursor', 'True')
    nodes = graph(CTRL, [
        event('tick', 'ReceiveTick'), call('pressed', 'WasInputKeyJustPressed', PC), branch('clicked'),
        call('under', 'GetHitResultUnderCursorByChannel', PC), call('split', 'BreakHitResult', GS), branch('onSomething'),
        call('find', 'GetActorOfClass', GS), {'id': 'asEnemy', 'tool': 'add_dynamic_cast_node_to_graph', 'args': {'extra_info': C(ENEMY)}},
        {'id': 'asSoldier', 'tool': 'add_dynamic_cast_node_to_graph', 'args': {'extra_info': C(SOLDIER)}},
        call('attack', 'AttackEnemy', C(SOLDIER)), call('move', 'MoveToPoint', C(SOLDIER)),
    ], [], [['pressed.Key', 'LeftMouseButton'], ['find.ActorClass', C(SOLDIER)]])
    ids = {n['id']: n for n in nodes}
    print('pins', {k: [p['name'] for p in ids[k]['pins']] for k in ('under', 'find', 'asEnemy', 'asSoldier')})
    has_exec = lambda k: any(p['name'] == 'execute' for p in ids[k]['pins'])
    node_id = lambda k: ids[k]['node_id']
    links = [('tick', 'then', 'clicked', 'execute'), ('pressed', 'ReturnValue', 'clicked', 'Condition')]
    last = ('clicked', 'then')
    for k in ('under', 'find'):
        if has_exec(k):
            links.append((*last, k, 'execute'))
            last = (k, 'then')
    links += [(*last, 'onSomething', 'execute'), ('under', 'ReturnValue', 'onSomething', 'Condition'), ('under', 'HitResult', 'split', 'Hit'),
              ('onSomething', 'then', 'asSoldier', 'execute'), ('find', 'ReturnValue', 'asSoldier', 'Object'),
              ('asSoldier', 'then', 'asEnemy', 'execute'), ('split', 'HitActor', 'asEnemy', 'Object'),
              ('asEnemy', 'then', 'attack', 'execute'), ('asEnemy', 'AsBP Rts Enemy', 'attack', 'Enemy'), ('asSoldier', 'AsBP Rts Soldier', 'attack', 'self'),
              ('asEnemy', 'CastFailed', 'move', 'execute'), ('split', 'Location', 'move', 'Point'), ('asSoldier', 'AsBP Rts Soldier', 'move', 'self')]
    for a, pa, b, pb in links:
        T('connect_pins', CTRL, 'EventGraph', node_id(a), pa, node_id(b), pb)
    done(CTRL)


def camera():
    T('create_blueprint', CAM, PAWN)
    T('add_component_to_bp', CAM, 'CameraComponent', 'View', '')
    T('set_component_property', CAM, 'View', {'RelativeRotation': '(Pitch=-70,Yaw=0,Roll=0)', 'bUsePawnControlRotation': 'false'})
    done(CAM)


def mode():
    T('create_blueprint', MODE, '/Script/Engine.GameModeBase')
    class_default(MODE, 'DefaultPawnClass', C(CAM))
    class_default(MODE, 'PlayerControllerClass', C(CTRL))
    done(MODE)


def level():
    T('create_editor_world', MAP, '', True, 'discard', True)
    T('load_editor_world', MAP, 'discard', True)
    T('set_editor_world_settings', class_settings={'DefaultGameMode': C(MODE)}, confirm=True, world_path=MAP, save=True)
    place = lambda **kw: T('place_editor_asset', **kw)
    # The engine's Plane has no collision, so the cursor trace would miss it; a flat cube can be clicked.
    ground = place(asset_path='/Engine/BasicShapes/Cube.Cube', location={'X': 0, 'Y': 0, 'Z': -50}, scale={'X': 60, 'Y': 60, 'Z': 1}, label='Ground')
    print('ground', ground[:300])
    path = ground.strip().strip('"')
    grey = "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray"
    print(m.set_actor_component_properties(path, 'StaticMeshComponent0', {'OverrideMaterials': f"(\"/Script/Engine.MaterialInstanceConstant'{grey}'\")"})[:300])
    T('create_light_actor', 'Directional', 'Sun', [0, 0, 1000], confirm=True)
    T('create_light_actor', 'Sky', 'Sky', [0, 0, 1200], confirm=True)
    place(actor_class='/Script/Engine.PlayerStart', location={'X': -800, 'Y': 0, 'Z': 2200}, label='Start')
    place(asset_path=SOLDIER, location={'X': 0, 'Y': 0, 'Z': 100}, label='Soldier')
    place(asset_path=ENEMY, location={'X': 600, 'Y': 500, 'Z': 80}, label='EnemyA')
    place(asset_path=ENEMY, location={'X': 700, 'Y': -500, 'Z': 80}, label='EnemyB')
    T('save_editor_world', confirm=True)


def state():
    session = json.loads(T('inspect_play_session', 'BP_Rts'))
    enemies = [a for a in session['actors'] if a['class'].endswith('BP_RtsEnemy_C')]
    soldier_at = next(a['location'] for a in session['actors'] if a['class'].endswith('BP_RtsSoldier_C'))
    return enemies, soldier_at


def click(**aim):
    under = json.loads(T('move_play_mouse', **aim))
    assert under['hit'], under
    T('send_play_input', 'LeftMouseButton', 'press')
    time.sleep(.2)
    T('send_play_input', 'LeftMouseButton', 'release')
    return under


def until(check, seconds, what):
    end = time.time() + seconds
    while time.time() < end:
        if check():
            return
        time.sleep(.25)
    raise AssertionError(f'{what}; state {state()}')


def playtest():
    assert 'errorMessage' in m.move_play_mouse(actor='BP_RtsEnemy')  # No session yet.
    T('load_editor_world', MAP, 'discard', True)
    T('control_ue_play_session', 'start')
    until(lambda: json.loads(T('get_ue_editor_status'))['is_playing'], 60, 'play did not start')
    time.sleep(2)
    try:
        assert 'errorMessage' in m.move_play_mouse(actor='NoSuchActor')
        assert 'errorMessage' in m.move_play_mouse(screen_x=99999, screen_y=0)
        assert 'errorMessage' in m.move_play_mouse(world_location=[-5000, 0, 0])  # Behind the camera.
        # Click the ground: the soldier walks to that point.
        point = (-300, -500)
        under = click(world_location=[*point, 0])
        assert 'StaticMeshActor' in under['hit_actor'], under
        near_point = lambda: sum((a - b) ** 2 for a, b in zip(state()[1][:2], point)) ** .5 < 120
        until(near_point, 15, 'the soldier did not reach the clicked point')
        # Click an enemy: the soldier chases and destroys it, leaving the other, and stays where it fought.
        under = click(actor='BP_RtsEnemy')
        assert 'BP_RtsEnemy' in under['hit_actor'], under
        until(lambda: len(state()[0]) == 1, 25, 'the enemy was not destroyed')
        fought_at = state()[1]
        time.sleep(1.5)
        moved = sum((a - b) ** 2 for a, b in zip(state()[1][:2], fought_at[:2])) ** .5
        assert moved < 30, moved
        print('played: move and attack verified by mouse clicks')
    finally:
        T('send_play_input', 'LeftMouseButton', 'release')
        T('control_ue_play_session', 'stop')


if __name__ == '__main__' and PLAY_ONLY:
    playtest()
elif __name__ == '__main__':
    T('load_editor_world', '/Game/ThirdPerson/Lvl_ThirdPerson', 'discard', True)
    for path in (MAP, MODE, CTRL, CAM, SOLDIER, ENEMY, BLUE, RED):
        m.delete_asset(path)
    for step in (colours, enemy, soldier, controller, camera, mode, level):
        print('==', step.__name__)
        step()
    print('built')
