"""Routes that need persistent fixtures (Verification/fixtures/create_fixtures.py): Slate brush references, Editor Utility
Run, Game Feature lifecycle and World Composition tiles; prepare, restart, verify.

prepare: page the fixture brush from its texture; run the fixture Editor Utility; walk MCPTestFeature through
Activate -> Deactivate -> Unload -> Activate; edit World Composition instance policy and both tiles' layer, display,
LOD-list and LOD-distance metadata (stale guard, dry run, real edit), inspect the hierarchy; save the persistent map and
tiles and snapshot.
verify (fresh editor): reload, compare the composition snapshot, then restore every fixture to its original state.
"""
import json
import sys
import time

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
F = '/Game/UE5MCP_Fixtures'
BRUSH = F + '/SB_MCP_Brush.SB_MCP_Brush'
UTILITY = F + '/EUB_MCP_Utility.EUB_MCP_Utility'
TEXTURE = '/Engine/EngineResources/DefaultTexture.DefaultTexture'
FEATURE = 'MCPTestFeature'
WC = F + '/WorldComposition/WC_Persistent'
TILES = [F + '/WorldComposition/Tiles/WC_TileA', F + '/WorldComposition/Tiles/WC_TileB']
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'fixtures.json'


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:400])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:300])
    return r['errorMessage']


def load(path):
    assert httpx.get(BASE + '/assets/describe', params={'asset_path': path}, timeout=300).is_success, path


# ---------------------------------------------------------------- brush, utility
def brush_stage():
    load(BRUSH)
    r = ok(m.inspect_texture_brush_assets, TEXTURE, 'UE5MCP_Fixtures', 0, 8)
    assert r['matching_brush_asset_count'] == 1 and r['brush_assets'][0]['asset_path'] == BRUSH, r
    b = r['brush_assets'][0]
    assert b['class_path'].endswith('SlateBrushAsset') and (b['image_width'], b['image_height']) == (32, 32), b
    assert ok(m.inspect_texture_brush_assets, TEXTURE, 'NoSuchBrush', 0, 8)['brush_assets'] == []


def utility_stage():
    u = ok(m.editor_utilities, 'Inspect', F)
    assert [x['path'] for x in u['utilities']] == [UTILITY] and u['total'] == 1, u
    bad(m.editor_utilities, 'Run', F, UTILITY, confirm=True, dry_run=False)                       # code-execution opt-in missing
    d = ok(m.editor_utilities, 'Run', F, UTILITY, allow_code_execution=True, confirm=True, dry_run=True)
    assert not d['issued'], d
    r = ok(m.editor_utilities, 'Run', F, UTILITY, allow_code_execution=True, confirm=True, dry_run=False)
    assert r['issued'] and r['succeeded'], r
    bad(m.editor_utilities, 'SpawnTab', F, UTILITY, allow_code_execution=True, confirm=True, dry_run=False)  # not a widget


# ---------------------------------------------------------------- Game Feature lifecycle
def feature_state():
    return next(g for g in ok(m.game_feature_plugins)['game_features'] if g['name'] == FEATURE)['state']


def transition(op, want, allow=False):
    cur = feature_state()
    bad(m.game_feature_plugins, op, FEATURE, 'NotTheState', allow=allow, confirm=True, dry_run=False)
    d = ok(m.game_feature_plugins, op, FEATURE, cur, allow=allow, confirm=True, dry_run=True)
    assert not d['request_issued'] and feature_state() == cur, d
    r = ok(m.game_feature_plugins, op, FEATURE, cur, allow=allow, confirm=True, dry_run=False)
    assert r['request_issued'], r
    for _ in range(120):
        if feature_state() == want:
            return
        time.sleep(0.5)
    raise AssertionError((op, 'stuck in', feature_state()))


def feature_stage():
    assert feature_state() in ('Registered', 'Loaded'), feature_state()   # Registered at startup, Loaded after a deactivation
    bad(m.game_feature_plugins, 'Activate', 'NoSuchFeature', 'Registered', confirm=True, dry_run=False)
    transition('Activate', 'Active')
    g = next(g for g in ok(m.game_feature_plugins)['game_features'] if g['name'] == FEATURE)
    assert g['active'], g
    transition('Deactivate', 'Loaded')     # native deactivation stops at Loaded
    bad(m.game_feature_plugins, 'Unload', FEATURE, 'Loaded', confirm=True, dry_run=False)   # unload needs allow
    transition('Unload', 'Registered', allow=True)   # unload drops content and stays registered
    transition('Activate', 'Active')
    transition('Deactivate', 'Loaded')


# ---------------------------------------------------------------- World Composition
def comp():
    o = ok(m.inspect_editor_world_settings)['world_origin']
    assert o['composition_policy_enabled'] and o['composition_object_present'], o
    return o['composition_path']


def tiles():
    return {t['package_path']: t for t in ok(m.inspect_world_composition_tiles, WC, comp(), 0, 16)['tiles']}


def settings():
    return ok(m.inspect_world_composition_tiles, WC, comp(), 0, 1)['settings']


def wc_load():
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': WC, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    for t in TILES:
        load(f'{t}.{t.rsplit("/", 1)[1]}')


def wc_edit(fn, state, *a, **kw):
    before = state()
    ok(fn, *a, **kw, confirm=True, dry_run=True)
    assert state() == before, (fn.__name__, 'dry run changed it')
    ok(fn, *a, **kw, confirm=True, dry_run=False)
    assert state() != before, (fn.__name__, 'no change')


def composition_stage(values):
    wc_load()
    C = comp()
    t = tiles()
    assert sorted(t) == TILES, sorted(t)
    for field, value in (('RebaseOriginDistance', values['rebase']), ('TilesStreamingTimeThreshold', values['threshold']),
                         ('bLoadAllTilesDuringCinematic', values['flag']), ('bLockTilesLocation', values['flag'])):
        cur = float(settings()[field])
        bad(m.set_world_composition_setting, WC, C, field, cur + 3, value, confirm=True, dry_run=False)
        wc_edit(m.set_world_composition_setting, settings, WC, C, field, cur, value)
    bad(m.set_world_composition_setting, WC, C, 'RebaseOriginDistance', values['rebase'], 0, confirm=True, dry_run=False)   # below 1
    a, b = TILES
    x = tiles()[a]
    bad(m.set_world_composition_tile_layer, WC, C, a, 2, 'Wrong', x['streaming_distance'], x['distance_streaming_enabled'],
        values['layer'], values['distance'], True, confirm=True, dry_run=False)
    wc_edit(m.set_world_composition_tile_layer, lambda: tiles()[a], WC, C, a, 2, x['layer_name'], x['streaming_distance'],
            x['distance_streaming_enabled'], values['layer'], values['distance'], True)
    assert tiles()[a]['layer_name'] == values['layer'] and tiles()[a]['streaming_distance'] == values['distance'], tiles()[a]
    assert tiles()[a]['package_has_tile_info'], tiles()[a]     # the edit writes native tile info into the package
    x = tiles()[b]
    bad(m.set_world_composition_tile_display, WC, C, b, 2, 'ZOrder', x['z_order'] + 1, values['zorder'], confirm=True, dry_run=False)
    wc_edit(m.set_world_composition_tile_display, lambda: tiles()[b], WC, C, b, 2, 'ZOrder', x['z_order'], values['zorder'])
    wc_edit(m.set_world_composition_tile_display, lambda: tiles()[b], WC, C, b, 2, 'bHideInTileView', int(tiles()[b]['hidden_in_tile_view']), values['flag'])
    bad(m.set_world_composition_tile_display, WC, C, b, 3, 'ZOrder', values['zorder'], 0, confirm=True, dry_run=False)   # stale tile count
    cur = [l['relative_streaming_distance'] for l in tiles()[b]['lod_settings']]
    bad(m.set_world_composition_tile_lod_list, WC, C, b, 2, cur, [1] * 5, confirm=True, dry_run=False)                   # more than 4
    wc_edit(m.set_world_composition_tile_lod_list, lambda: tiles()[b], WC, C, b, 2, cur, values['lods'])
    assert [l['relative_streaming_distance'] for l in tiles()[b]['lod_settings']] == values['lods'], tiles()[b]['lod_settings']
    if values['lods']:
        wc_edit(m.set_world_composition_tile_lod_distance, lambda: tiles()[b], WC, C, b, 2, len(values['lods']), 0, values['lods'][0], values['lods'][0] + 500)
        bad(m.set_world_composition_tile_lod_distance, WC, C, b, 2, len(values['lods']), 9, 0, 1, confirm=True, dry_run=False)   # index out of range
    h = ok(m.inspect_world_composition_tile_hierarchy, WC, C, a, 0, 8)
    assert 'ancestors' in json.dumps(h) or 'children' in json.dumps(h), h
    for p in [WC] + TILES:
        assert httpx.post(BASE + '/assets/save', json={'AssetPath': f'{p}.{p.rsplit("/", 1)[1]}'}, timeout=600).is_success, p
    return snapshot()


def snapshot():
    keep = ('layer_name', 'streaming_distance', 'distance_streaming_enabled', 'z_order', 'hidden_in_tile_view', 'lod_settings', 'package_has_tile_info')
    return {'settings': settings(), 'tiles': {p: {k: t[k] for k in keep} for p, t in tiles().items()}}


EDIT = {'rebase': 250000, 'threshold': 2.5, 'flag': 1, 'layer': 'MCPLayer', 'distance': 40000, 'zorder': 3, 'lods': [10000, 20000]}


def prepare():
    brush_stage()
    utility_stage()
    feature_stage()
    snap = composition_stage(EDIT)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snap}, indent=1), encoding='utf-8')
    print('fixture routes exercised; World Composition saved')


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    wc_load()
    got = json.loads(json.dumps(snapshot()))
    diff = {k: (got.get(k), v) for k, v in st['snapshot'].items() if got.get(k) != v}
    assert not diff, json.dumps(diff)[:3000]
    brush_stage()
    assert feature_state() == 'Registered', feature_state()
    print('World Composition policy and tile metadata identical after cold reload; brush and Game Feature fixtures intact')
    restore()


def restore():
    """Put the composition fixture back to native defaults so later runs start clean."""
    wc_load()
    C = comp()
    s = settings()
    for field, value in (('RebaseOriginDistance', 524287.5), ('TilesStreamingTimeThreshold', 1), ('bLoadAllTilesDuringCinematic', 0), ('bLockTilesLocation', 0)):
        if float(s[field]) != value:
            ok(m.set_world_composition_setting, WC, C, field, float(s[field]), value, confirm=True, dry_run=False)
    a, b = TILES
    x = tiles()[a]
    if x['layer_name'] != 'Uncategorized':
        ok(m.set_world_composition_tile_layer, WC, C, a, 2, x['layer_name'], x['streaming_distance'], x['distance_streaming_enabled'],
           'Uncategorized', 50000, True, confirm=True, dry_run=False)
    x = tiles()[b]
    for field, key, value in (('ZOrder', 'z_order', 0), ('bHideInTileView', 'hidden_in_tile_view', 0)):
        if int(x[key]) != value:
            ok(m.set_world_composition_tile_display, WC, C, b, 2, field, int(x[key]), value, confirm=True, dry_run=False)
    cur = [l['relative_streaming_distance'] for l in tiles()[b]['lod_settings']]
    if cur:
        ok(m.set_world_composition_tile_lod_list, WC, C, b, 2, cur, [], confirm=True, dry_run=False)
    for p in [WC] + TILES:
        httpx.post(BASE + '/assets/save', json={'AssetPath': f'{p}.{p.rsplit("/", 1)[1]}'}, timeout=600)
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    STATE.unlink(missing_ok=True)
    print('fixtures restored')


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': restore}[COMMAND]()
