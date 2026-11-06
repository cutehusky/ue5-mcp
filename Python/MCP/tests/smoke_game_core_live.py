"""Core game-making loop, end to end, using only MCP tools; prepare, restart, verify.

prepare: make a Character Blueprint child of the ThirdPerson character with a faster walk speed and a GameMode whose
DefaultPawnClass is that character; point the project's default GameMode at it (Config/DefaultEngine.ini is restored by
cleanup); start PIE, check the new pawn spawned, hold W and check it actually moves at the new speed, jump with SpaceBar.
verify (fresh editor): the class defaults and project setting reload. package: run after verify to build the game for real.
"""
import json
import shutil
import sys
import time

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
ROOT = '/Game/UE5MCP_Test/GameCore'
MAP = f'{ROOT}/MCP_GameCore'
PAWN, MODE = f'{ROOT}/BP_MCP_Hero', f'{ROOT}/BP_MCP_Mode'
PAWN_C = f'{PAWN}.BP_MCP_Hero_C'
MODE_C = f'{MODE}.BP_MCP_Mode_C'
PARENT = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C'
INI = PROJECT / 'Config' / 'DefaultEngine.ini'
BACKUP = PROJECT / 'Saved' / 'UE5MCP_Test' / 'DefaultEngine.game_core_backup.ini'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'game_core.json'
Y = dict(confirm=True)


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:500])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:400])
    return r['errorMessage']


def default(bp, path):
    rows = ok(m.inspect_blueprint_class_defaults, bp, path, 1000)['properties']
    return next(r['value'] for r in rows if r['path'] == path)


def load(path):
    r = httpx.post(BASE + '/worlds/load', json={'WorldPath': path, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()
    assert r.get('success'), r


def pie(start):
    (m.start_play_in_editor if start else m.stop_play_in_editor)()
    for _ in range(90):
        if ok(m.get_ue_editor_status)['is_playing'] == start:
            time.sleep(1)
            return
        time.sleep(1)
    raise AssertionError('PIE state did not change')


def authoring():
    m.create_blueprint(PAWN, PARENT)
    m.create_blueprint(MODE, '/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C')   # its controller adds the input mappings
    assert ok(m.inspect_blueprint_class_defaults, PAWN, 'MaxWalkSpeed')['total'] >= 1
    speed = default(PAWN, 'CharacterMovement.MaxWalkSpeed')
    a = (PAWN, 'CharacterMovement.MaxWalkSpeed')
    bad(m.set_blueprint_class_default, *a, speed, '1200')                                # unconfirmed
    bad(m.set_blueprint_class_default, *a, '-1', '1200', **Y)                            # stale
    bad(m.set_blueprint_class_default, *a, speed, 'fast', **Y)
    bad(m.set_blueprint_class_default, PAWN, 'CharacterMovement.NoSuchField', '', '1', **Y)
    bad(m.set_blueprint_class_default, PAWN, 'Mesh.SkeletalMeshAsset.RefSkeleton', '', '1', **Y)   # never enters shared assets
    ok(m.set_blueprint_class_default, *a, speed, '1200', confirm=True, dry_run=True)
    assert default(*a) == speed
    r = ok(m.set_blueprint_class_default, *a, speed, '1200', confirm=True, save=True)
    assert float(r['after']) == 1200, r
    b = (MODE, 'DefaultPawnClass')
    bad(m.set_blueprint_class_default, *b, default(*b), '/Script/Engine.Actor', **Y)     # not a Pawn
    ok(m.set_blueprint_class_default, *b, default(*b), PAWN_C, confirm=True, save=True)
    assert 'BP_MCP_Hero' in default(*b)


def settings():
    s = ok(m.inspect_project_game_settings)
    old = s['GlobalDefaultGameMode']
    bad(m.set_project_game_setting, 'GameUserSettingsClassName', '', 'x', **Y)           # not allowed
    bad(m.set_project_game_setting, 'GlobalDefaultGameMode', old, PAWN_C, **Y)           # not a GameMode
    bad(m.set_project_game_setting, 'GameDefaultMap', s['GameDefaultMap'], '/Game/Nope.Nope', **Y)
    bad(m.set_project_game_setting, 'GlobalDefaultGameMode', 'stale', MODE_C, **Y)
    before = INI.read_bytes()
    ok(m.set_project_game_setting, 'GlobalDefaultGameMode', old, MODE_C, confirm=True, dry_run=True)
    assert INI.read_bytes() == before
    ok(m.set_project_game_setting, 'GlobalDefaultGameMode', old, MODE_C, **Y)
    assert MODE_C in ok(m.inspect_project_game_settings)['GlobalDefaultGameMode'] and 'BP_MCP_Mode' in INI.read_text(encoding='utf-8')


def playtest():
    # The map's own GameMode override beats the project default, so point a copy of the map at the new mode.
    ok(m.create_editor_world, MAP, '/Game/ThirdPerson/Lvl_ThirdPerson', True, 'discard', True)
    load(MAP)
    ok(m.set_editor_world_settings, class_settings={'DefaultGameMode': MODE_C}, confirm=True, world_path=MAP, save=True)
    bad(m.send_play_input, 'W')                                                          # no session
    bad(m.inspect_play_session)
    pie(True)
    try:
        s = ok(m.inspect_play_session)
        assert 'BP_MCP_Mode' in s['game_mode'] and 'BP_MCP_Hero' in s['player_pawn'], (s['game_mode'], s['player_pawn'])
        assert s['total'] >= 1 and any('BP_MCP_Hero' in a['class'] for a in s['actors'])
        bad(m.send_play_input, 'NotARealKey')
        bad(m.send_play_input, 'W', 'tap')
        time.sleep(3)                                                                    # let the pawn land
        start = ok(m.inspect_play_session, 'BP_MCP_Hero')['player_location']
        ok(m.send_play_input, 'W', 'press')
        time.sleep(2)
        moving = ok(m.inspect_play_session, 'BP_MCP_Hero')
        ok(m.send_play_input, 'W', 'release')
        dist = sum((x - y) ** 2 for x, y in zip(moving['player_location'], start)) ** .5
        speed = sum(v ** 2 for v in moving['player_velocity'][:2]) ** .5
        print('moved', dist, 'speed', speed)
        assert dist > 1100, (dist, speed)                                 # above the 500 default: the edit took effect
        time.sleep(2)
        rest = ok(m.inspect_play_session, 'BP_MCP_Hero')
        assert sum(v ** 2 for v in rest['player_velocity'][:2]) ** .5 < 1, rest['player_velocity']   # release stopped it
        z = rest['player_location'][2]
        ok(m.send_play_input, 'SpaceBar', 'press')
        time.sleep(.3)
        up = ok(m.inspect_play_session, 'BP_MCP_Hero')['player_location'][2]
        ok(m.send_play_input, 'SpaceBar', 'release')
        assert up > z + 10, (z, up)
    finally:
        pie(False)


def snapshot():
    return {'speed': float(default(PAWN, 'CharacterMovement.MaxWalkSpeed')), 'pawn': default(MODE, 'DefaultPawnClass'),
            'mode': ok(m.inspect_project_game_settings)['GlobalDefaultGameMode']}


def prepare():
    cleanup()
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(INI, BACKUP)
    authoring()
    settings()
    playtest()
    STATE.write_text(json.dumps(snapshot()), encoding='utf-8')
    print('Game core loop prepared and playtested')


def verify():
    want = json.loads(STATE.read_text(encoding='utf-8'))
    assert snapshot() == want, (snapshot(), want)
    print('Class defaults and project game setting identical after cold reload')
    cleanup()


def package():
    bad(m.package_game)                                                                  # unconfirmed
    bad(m.package_game, 'Linux', **Y)
    bad(m.package_game, 'Win64', 'Fast', **Y)
    ok(m.package_game, allow_dirty=True, confirm=True, dry_run=True)
    ok(m.package_game, allow_dirty=True, **Y)
    bad(m.package_game, allow_dirty=True, **Y)                                           # one job at a time
    while True:
        s = ok(m.get_package_status, 5)
        if not s['running']:
            break
        time.sleep(30)
    print(json.dumps(s, indent=1)[:2500])
    assert s['succeeded'], s
    exes = list((PROJECT / 'Saved' / 'MCPBuilds').rglob('*.exe'))
    assert any(str(s['output_dir']).replace('\\', '/') in str(e).replace('\\', '/') for e in exes), exes[:5]
    print('Packaged game built:', s['output_dir'])


def cleanup():
    if ok(m.get_ue_editor_status)['is_playing']:
        pie(False)
    if BACKUP.exists():
        shutil.copyfile(BACKUP, INI)
        BACKUP.unlink()
    load('/Game/ThirdPerson/Lvl_ThirdPerson')
    for p in (MAP, MODE, PAWN):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'package': package, 'cleanup': cleanup}[COMMAND]()
