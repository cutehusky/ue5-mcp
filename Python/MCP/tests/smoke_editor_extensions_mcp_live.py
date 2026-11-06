"""MCP-level widget animations, consolidation with referencer fix-up, Smart Object slot formats, Game Features and Editor
Utilities discovery; prepare, restart, verify.

prepare: through the MCP wrappers, author two widget animations (create/range/rename/delete), compile and save; duplicate
three materials and two instances parented to the second and third, consolidate both sources into the first (instances
re-parented, multi-source); create a Smart Object definition and set slot Name/Offset/Rotation/Color/tags/bEnabled with
native ImportText formats; save everything and snapshot.
verify (fresh editor): reload and compare widget animations, instance parents and Smart Object slots, then delete.
"""
import json
import re
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
T = '/Game/UE5MCP_Test/'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'editor_extensions_mcp.json'
GRID = '/Game/LevelPrototyping/Materials/M_PrototypeGrid.M_PrototypeGrid'
GRAY = '/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray'
N = {}


def names(tag):
    p = lambda base: f'{T}{base}_{tag}.{base}_{tag}'
    N.update(tag=tag, wbp=p('WBP_MCPExt'), so=p('SO_MCPExt'), mx=p('M_MCPExtX'), my=p('M_MCPExtY'), mz=p('M_MCPExtZ'),
             iy=p('MI_MCPExtY'), iz=p('MI_MCPExtZ'))


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


def pkg(path):
    return path.split('.')[0]


def save(*paths):
    for p in paths:
        assert httpx.post(BASE + '/assets/save', json={'AssetPath': p}, timeout=600).is_success, p


# ---------------------------------------------------------------- widget animations
def anims():
    return json.loads(ok(m.widget_animations, N['wbp'])['snapshot'])['animations']


def widget_stage():
    assert httpx.post(BASE + '/widget-blueprints/create', json={'BpPath': pkg(N['wbp'])}, timeout=300).is_success
    snap = ok(m.widget_animations, N['wbp'])['snapshot']
    bad(m.widget_animations, N['wbp'], 'Create', name='FadeIn', start_seconds=2, end_seconds=1, expected_snapshot=snap, confirm=True, dry_run=False)
    bad(m.widget_animations, N['wbp'], 'Create', name='FadeIn', expected_snapshot='stale', confirm=True, dry_run=False)
    r = ok(m.widget_animations, N['wbp'], 'Create', name='FadeIn', end_seconds=1.5, expected_snapshot=snap, confirm=True, dry_run=True)
    assert anims() == [], r
    for name, lo, hi in (('FadeIn', 0, 1.5), ('Pulse', 0.25, 3)):
        snap = ok(m.widget_animations, N['wbp'])['snapshot']
        ok(m.widget_animations, N['wbp'], 'Create', name=name, start_seconds=lo, end_seconds=hi, expected_snapshot=snap, confirm=True, dry_run=False)
    a = {x['name']: x for x in anims()}
    assert set(a) == {'FadeIn', 'Pulse'}, a
    snap = ok(m.widget_animations, N['wbp'])['snapshot']
    ok(m.widget_animations, N['wbp'], 'SetRange', animation_path=a['Pulse']['path'], start_seconds=0.5, end_seconds=2, expected_snapshot=snap, confirm=True, dry_run=False)
    snap = ok(m.widget_animations, N['wbp'])['snapshot']
    ok(m.widget_animations, N['wbp'], 'Rename', animation_path=a['FadeIn']['path'], name='FadeOut', expected_snapshot=snap, confirm=True, dry_run=False)
    snap = ok(m.widget_animations, N['wbp'])['snapshot']
    bad(m.widget_animations, N['wbp'], 'Rename', animation_path=a['Pulse']['path'], name='FadeOut', expected_snapshot=snap, confirm=True, dry_run=False)  # duplicate
    assert sorted(x['name'] for x in anims()) == ['FadeOut', 'Pulse'], anims()
    assert httpx.post(BASE + '/blueprints/compile', json={'BpPath': pkg(N['wbp'])}, timeout=300).is_success
    save(N['wbp'])


# ---------------------------------------------------------------- consolidation with referencers
def parent(mi):
    return httpx.get(BASE + '/material-instances/parameters', params={'asset_path': mi}, timeout=120).json()['parent_path']


def consolidate_stage():
    for src, dst in ((GRID, N['mx']), (GRID, N['my']), (GRID, N['mz']), (GRAY, N['iy']), (GRAY, N['iz'])):
        assert httpx.post(BASE + '/assets/duplicate', json={'AssetPath': src, 'DestinationPath': pkg(dst)}, timeout=300).is_success, dst
    for mi, par in ((N['iy'], N['my']), (N['iz'], N['mz'])):
        assert httpx.patch(BASE + '/material-instances/parent', json={'AssetPath': mi, 'ParentPath': par}, timeout=300).is_success
    save(N['mx'], N['my'], N['mz'], N['iy'], N['iz'])
    assert parent(N['iy']) == N['my'] and parent(N['iz']) == N['mz'], (parent(N['iy']), parent(N['iz']))
    ins = ok(m.consolidate_assets, N['mx'], [N['my'], N['mz']])
    refs = json.dumps(ins)
    assert N['iy'].split('.')[0] in refs and N['iz'].split('.')[0] in refs, refs[:800]   # per-source referencers reported
    bad(m.consolidate_assets, N['mx'], [N['my'], N['mz']], 'Consolidate', ins['snapshot'], allow_irreversible=False, confirm=True, dry_run=False)
    bad(m.consolidate_assets, N['mx'], [N['my'], N['mz']], 'Consolidate', 'stale', allow_irreversible=True, confirm=True, dry_run=False)
    bad(m.consolidate_assets, N['mx'], [N['my'], N['iy']])   # mixed classes
    r = ok(m.consolidate_assets, N['mx'], [N['my'], N['mz']], 'Consolidate', ins['snapshot'], allow_irreversible=True, confirm=True, dry_run=True)
    assert not r.get('written'), r
    r = ok(m.consolidate_assets, N['mx'], [N['my'], N['mz']], 'Consolidate', ins['snapshot'], allow_irreversible=True, confirm=True, dry_run=False)
    assert r['written'] and not r['failed_objects'] and not r['invalid_objects'], r
    assert parent(N['iy']) == parent(N['iz']) == N['mx'], (parent(N['iy']), parent(N['iz']))
    save(N['iy'], N['iz'], N['mx'])


# ---------------------------------------------------------------- Smart Object slot formats
def slots():
    return json.loads(ok(m.smart_object_definition, N['so'])['snapshot'])['slots']


def enabled():
    return json.loads(ok(m.smart_object_definition, N['so'])['snapshot'])['slot_enabled']


def so_set(i, field, text):
    snap = ok(m.smart_object_definition, N['so'])['snapshot']
    return ok(m.smart_object_definition, N['so'], 'SetSlot', slot_index=i, field=field, value_text=text, expected_snapshot=snap, confirm=True, dry_run=False)


def smart_object_stage():
    bad(m.smart_object_definition, N['so'], 'Create', confirm=False, dry_run=False)
    ok(m.smart_object_definition, N['so'], 'Create', confirm=True, dry_run=False)
    snap = ok(m.smart_object_definition, N['so'])['snapshot']
    base = len(slots())
    ok(m.smart_object_definition, N['so'], 'AddSlot', slot_name='Seat', value_text='(X=10,Y=20,Z=0)', expected_snapshot=snap, confirm=True, dry_run=False)
    i = base
    so_set(i, 'Rotation', '(Pitch=0,Yaw=90,Roll=0)')
    so_set(i, 'Color', '(B=0,G=128,R=255,A=255)')
    so_set(i, 'Offset', '(X=50,Y=-25,Z=5)')
    so_set(i, 'ActivityTags', '(GameplayTags=)')
    so_set(i, 'bEnabled', 'False')
    s = slots()[i]
    assert 'Yaw=90' in s and 'DEBUG_DrawColor=(B=0,G=128,R=255,A=255)' in s and 'X=50' in s and 'Y=-25' in s, s
    assert enabled()[i] is False and all(enabled()[:i]), enabled()   # bEnabled is reported outside the slot text
    snap = ok(m.smart_object_definition, N['so'])['snapshot']
    bad(m.smart_object_definition, N['so'], 'SetSlot', slot_index=i, field='Rotation', value_text='not a rotator', expected_snapshot=snap, confirm=True, dry_run=False)
    bad(m.smart_object_definition, N['so'], 'SetSlot', slot_index=i + 5, field='Name', value_text='X', expected_snapshot=snap, confirm=True, dry_run=False)
    save(N['so'])


# ---------------------------------------------------------------- discovery-only families
def discovery_stage():
    gf = ok(m.game_feature_plugins)
    assert isinstance(gf['game_features'], list), gf
    bad(m.game_feature_plugins, 'Activate', 'NoSuchPlugin_MCP', 'Installed', confirm=True, dry_run=False)
    eu = ok(m.editor_utilities)
    assert eu['total'] >= 0 and isinstance(eu['utilities'], list), eu
    bad(m.editor_utilities, 'Run', '/Game', '/Game/Nope.Nope')
    # Legacy LOD actors: no route builds HLOD clusters, so the current ordinary map lists none; paging/path guards refuse.
    world = ok(m.inspect_editor_world_settings)['world_path']
    lod = ok(m.inspect_world_legacy_lod_actors, world, 0, 8)
    assert lod['loaded_lod_actor_count'] == 0 and lod['actors'] == [] and not lod['has_more'], lod
    bad(m.inspect_world_legacy_lod_actors, world, 0, 0)
    bad(m.inspect_world_legacy_lod_actors, world + '.Nope', 0, 8)
    return {'game_features': len(gf['game_features']), 'editor_utilities': eu['total'], 'lod_actors': lod['loaded_lod_actor_count']}


def snapshot():
    # The engine fills SelectionPreconditions.SchemaClass on load (empty before the first save), so it is left out.
    return {'anims': sorted((x['name'], x.get('start', x.get('start_seconds')), x.get('end', x.get('end_seconds'))) for x in anims()),
            'parents': [parent(N['iy']), parent(N['iz'])], 'slots': [re.sub(r',SelectionPreconditions=\(.*\)\)$', ')', x) for x in slots()], 'slot_enabled': enabled()}


def prepare():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    names(uuid.uuid4().hex[:6])
    STATE.write_text(json.dumps({'tag': N['tag']}), encoding='utf-8')
    widget_stage()
    consolidate_stage()
    smart_object_stage()
    found = discovery_stage()
    STATE.write_text(json.dumps({'tag': N['tag'], 'snapshot': snapshot()}, indent=1), encoding='utf-8')
    print('editor extensions prepared through MCP;', found)


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    names(st['tag'])
    try:
        for p in (N['wbp'], N['so'], N['iy'], N['iz'], N['mx']):
            httpx.get(BASE + '/assets/describe', params={'asset_path': p}, timeout=300)
        got = json.loads(json.dumps(snapshot()))
        diff = {k: (got.get(k), v) for k, v in st['snapshot'].items() if got.get(k) != v}
        assert not diff, diff
        print('widget animations, consolidated instance parents and Smart Object slots identical after cold reload')
    finally:
        cleanup()


def cleanup():
    if not N and STATE.exists():
        names(json.loads(STATE.read_text(encoding='utf-8')).get('tag', 'none'))
    for k in ('wbp', 'so', 'iy', 'iz', 'my', 'mz', 'mx'):
        if k in N:
            httpx.post(BASE + '/assets/delete', json={'AssetPath': pkg(N[k])}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
