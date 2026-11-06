"""World Settings response metadata, guarded class/enum maps, Nanite masked policy, origin rebasing and partition
volumetric-lightmap loading; World Composition refusals; prepare, restart, verify.

prepare: on a scratch ordinary map, edit NaniteSettings.bAllowMaskedMaterials, KillZDamageType and
VisibilityAggressiveness with stale expected maps rejected and dry runs unchanged, checking transaction, planned
field change, dirty-package and directly-edited-actor metadata plus per-field capabilities; check origin-rebasing
policy; on an OpenWorld copy edit the partition-only volumetric-lightmap loading range and cell size; save both.
verify (fresh editor): reload both maps and compare the snapshot, then delete them.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
MAP, WP = '/Game/UE5MCP_Test/MCP_WSMeta', '/Game/UE5MCP_Test/MCP_WSMetaWP'
W, WPW = MAP, WP  # World Settings edits take the package path
TEMPLATE = '/Engine/Maps/Templates/OpenWorld'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'world_settings_meta.json'
MASKED = 'NaniteSettings.bAllowMaskedMaterials'
KILLZ = '/Script/Engine.DamageType'
RANGE, CELL = 'VolumetricLightmapLoadingRange', 'LightmassSettings.VolumetricLightmapLoadingCellSize'


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


def load(pkg):
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': pkg, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']


def ws():
    return ok(m.inspect_editor_world_settings)


def setw(world, **kw):
    return ok(m.set_editor_world_settings, world_path=world, confirm=True, **kw)


def check_metadata(r, field, before_text):
    t = r['transaction']
    assert t['supported'] and t['would_transact'] and t['primary_object_recorded'] and t['scope_body_completed'] and t['planned_change_count'] == 1, t
    pf = r['planned_field_changes']
    assert len(pf) == 1 and pf[0]['field'] == field and pf[0]['applied'] and pf[0]['before_native_text'] == before_text, pf
    assert pf[0]['current_native_text'] != before_text, pf
    d = r['dirty_package_impact']
    assert d['captured'] and MAP in json.dumps(d), d
    assert len(r['directly_edited_actor_paths']) == 1 and r['directly_edited_actor_paths'][0].endswith('.WorldSettings'), r['directly_edited_actor_paths']


# ---------------------------------------------------------------- ordinary map
def ordinary_stage():
    load(MAP)
    s = ws()
    caps = s['field_capabilities']
    c = caps[MASKED]
    assert c['kind'] == 'boolean' and c['nested'] and c['member_name'] == 'NaniteSettings' and c['native_leaf_editable'], c
    assert caps['VisibilityCellSize']['property_type'] == 'IntProperty' and not caps['VisibilityCellSize']['nested'], caps['VisibilityCellSize']
    assert s['transaction']['supported'] and not s['transaction']['would_transact'] and s['planned_field_changes'] == [], s['transaction']
    assert not s['dirty_package_impact']['captured'], s['dirty_package_impact']
    # Nanite masked-material policy with a stale bool guard, a dry run and the real edit.
    cur = s['bool_settings'][MASKED]
    bad(m.set_editor_world_settings, world_path=W, confirm=True, bool_settings={MASKED: not cur}, expected_bool_settings={MASKED: not cur})
    bad(m.set_editor_world_settings, world_path=W, confirm=True, bool_settings={MASKED: not cur}, expected_bool_settings={'bPrecomputeVisibility': False})  # guard key not requested
    r = setw(W, bool_settings={MASKED: not cur}, expected_bool_settings={MASKED: cur}, dry_run=True)
    assert not r['transaction']['scope_body_completed'] and r['planned_field_changes'][0]['applied'] is False, r['planned_field_changes']
    assert ws()['bool_settings'][MASKED] == cur
    r = setw(W, bool_settings={MASKED: not cur}, expected_bool_settings={MASKED: cur})
    assert ws()['bool_settings'][MASKED] is (not cur)
    check_metadata(r, MASKED, str(cur))
    # Class map with expected guard.
    killz = s['class_settings']['KillZDamageType']
    bad(m.set_editor_world_settings, world_path=W, confirm=True, class_settings={'KillZDamageType': KILLZ}, expected_class_settings={'KillZDamageType': KILLZ})
    setw(W, class_settings={'KillZDamageType': KILLZ}, expected_class_settings={'KillZDamageType': killz}, dry_run=True)
    assert ws()['class_settings']['KillZDamageType'] == killz
    r = setw(W, class_settings={'KillZDamageType': KILLZ}, expected_class_settings={'KillZDamageType': killz})
    assert ws()['class_settings']['KillZDamageType'] == KILLZ and r['planned_field_changes'][0]['field'] == 'KillZDamageType', r['planned_field_changes']
    # Enum map with expected guard.
    vis = s['enum_settings']['VisibilityAggressiveness']
    new = next(o for o in s['enum_options']['VisibilityAggressiveness'] if o != vis and not o.endswith('MAX')) \
        if isinstance(s['enum_options'].get('VisibilityAggressiveness'), list) else 'VIS_ModeratelyAggressive'
    new = new['name'] if isinstance(new, dict) else new
    bad(m.set_editor_world_settings, world_path=W, confirm=True, enum_settings={'VisibilityAggressiveness': new}, expected_enum_settings={'VisibilityAggressiveness': new})
    setw(W, enum_settings={'VisibilityAggressiveness': new}, expected_enum_settings={'VisibilityAggressiveness': vis})
    assert ws()['enum_settings']['VisibilityAggressiveness'] == new
    # A no-op leaves no planned changes and no transaction.
    r = setw(W, enum_settings={'VisibilityAggressiveness': new}, expected_enum_settings={'VisibilityAggressiveness': new})
    assert r['planned_field_changes'] == [] and not r['transaction']['would_transact'], r['transaction']
    # Origin rebasing: enabling needs native World Composition, which no route can switch on; disabling the stored flag is a no-op.
    o = ws()['world_origin']
    assert not o['composition_policy_enabled'] and not o['composition_object_present'] and not o['partitioned'] and o['current'] == [0, 0, 0], o
    bad(m.set_editor_world_settings, world_path=W, confirm=True, bool_settings={'bEnableWorldOriginRebasing': True})
    bad(m.set_editor_world_settings, world_path='', confirm=True, bool_settings={'bEnableWorldOriginRebasing': False})   # exact world required
    setw(W, bool_settings={'bEnableWorldOriginRebasing': False})
    assert ws()['bool_settings']['bEnableWorldOriginRebasing'] is False
    # Partition-only volumetric loading fields are refused on an ordinary map.
    bad(m.set_editor_world_settings, world_path=W, confirm=True, numeric_settings={RANGE: 3200})
    bad(m.set_editor_world_settings, world_path=W, confirm=True, numeric_settings={CELL: 6400})
    # World Composition tools refuse a map without a composition.
    bad(m.inspect_world_composition_tiles, W, 'None', 0, 8)
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']


# ---------------------------------------------------------------- World Partition map
def partition_stage():
    assert ok(m.create_editor_world, WP, TEMPLATE, True, 'discard', True)['success']
    load(WP)
    s = ws()
    assert s['world_origin']['partitioned'], s['world_origin']
    rng = s['numeric_settings'][RANGE]
    bad(m.set_editor_world_settings, world_path=WPW, confirm=True, numeric_settings={RANGE: 800})        # below 1600
    bad(m.set_editor_world_settings, world_path=WPW, confirm=True, numeric_settings={RANGE: 200000})     # above 102400
    bad(m.set_editor_world_settings, world_path=WPW, confirm=True, numeric_settings={RANGE: 3200}, expected_numeric_settings={RANGE: rng + 1})
    setw(WPW, numeric_settings={RANGE: 3200}, expected_numeric_settings={RANGE: rng}, dry_run=True)
    assert ws()['numeric_settings'][RANGE] == rng
    r = setw(WPW, numeric_settings={RANGE: 3200}, expected_numeric_settings={RANGE: rng})
    assert ws()['numeric_settings'][RANGE] == 3200 and r['planned_field_changes'][0]['field'] == RANGE, r['planned_field_changes']
    cell = s['numeric_settings'][CELL]
    want = 6400 if cell != 6400 else 12800
    bad(m.set_editor_world_settings, world_path=WPW, confirm=True, numeric_settings={CELL: 8})   # cell size in cm, 1600..102400
    setw(WPW, numeric_settings={CELL: want}, expected_numeric_settings={CELL: cell})
    assert ws()['numeric_settings'][CELL] == want
    bad(m.set_editor_world_settings, world_path=WPW, confirm=True, bool_settings={'bEnableWorldOriginRebasing': True})  # partition map
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': WP, 'bConfirm': True}, timeout=600).json()['success']


def snapshot():
    out = {}
    for pkg in (MAP, WP):
        load(pkg)
        s = ws()
        out[pkg] = {k: s[k] for k in ('bool_settings', 'class_settings', 'enum_settings')}
        out[pkg]['numeric'] = {k: s['numeric_settings'].get(k) for k in (RANGE, CELL, 'VisibilityCellSize')}
    return out


def prepare():
    cleanup()
    assert httpx.post(BASE + '/worlds/create', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True, 'bSave': True}, timeout=600).json()['success']
    ordinary_stage()
    partition_stage()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1))
    print('world settings metadata prepared; maps saved')


def verify():
    st = json.loads(STATE.read_text())
    got, want = json.loads(json.dumps(snapshot())), st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('world settings identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    for p in (MAP, WP, WP + '_HLOD0_Instancing'):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
