"""Gameplay Tag catalog, evaluation, ini authoring, DataTable sources and Data Asset tag fields; prepare, restart, verify.

prepare: create two ini sources, tags, a comment update, a rename (redirect), a delete and a move; evaluate container and
compound queries; edit a Smart Object definition's ActivityTags container and UserTagFilter query (the Data Asset under
test) and evaluate the stored query; add a row to the DT_MCP_Tags fixture table and register it as a tag source.
verify (fresh editor): every ini/table/asset change is reloaded from disk, then cleanup removes the sources, the table
registration, the table row and the asset. The fixture table comes from Verification/fixtures/create_fixtures.py.
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
SRC, SRC2 = 'MCPTest_Tags.ini', 'MCPTest_Tags2.ini'
INI = [PROJECT / 'Config' / 'Tags' / SRC, PROJECT / 'Config' / 'Tags' / SRC2]
DEFAULT_INI = PROJECT / 'Config' / 'DefaultGameplayTags.ini'
ASSET = '/Game/UE5MCP_Test/GT_MCP_SmartObject'
TABLE = '/Game/UE5MCP_Fixtures/DT_MCP_Tags'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'gameplay_tags.json'


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


def tag(name):
    r = J(m.inspect_gameplay_tags(name, dictionary_only=False))
    if 'errorMessage' in r:
        assert 'not registered' in r['errorMessage'], r
        return None
    rows = [t for t in r['tags'] if t['name'] == name]
    return rows[0] if rows else None


def explicit():
    return sorted(t['name'] for t in ok(m.inspect_gameplay_tags, 'MCPTest', dictionary_only=True)['tags'] if t['explicit'])


def ini_stage():
    bad(m.create_gameplay_tag_source, 'bad name.ini', confirm=True)
    bad(m.create_gameplay_tag_source, SRC, confirm=False)
    assert ok(m.create_gameplay_tag_source, SRC, confirm=True, dry_run=True)['registered'] is False
    for s in (SRC, SRC2):
        assert ok(m.create_gameplay_tag_source, s, confirm=True)['registered']
    assert not ok(m.create_gameplay_tag_source, SRC, confirm=True)['would_change']                     # existing: no-op
    names = {s['name']: s for s in ok(m.inspect_gameplay_tag_sources, 'MCPTest')['sources']}
    assert names[SRC]['supports_tag_creation'] and names[SRC]['type'] == 'TagList', names
    # Tags: dry run, confirmation, invalid syntax, then real creation.
    bad(m.create_gameplay_tag, 'MCPTest.A', SRC, confirm=False)
    bad(m.create_gameplay_tag, 'MCPTest..Bad', SRC, confirm=True)
    bad(m.create_gameplay_tag, 'MCPTest.A', 'EnhancedInput', confirm=True)                          # native source
    assert ok(m.create_gameplay_tag, 'MCPTest.A.Child', SRC, 'child', confirm=True, dry_run=True)['registered'] is False
    assert tag('MCPTest.A.Child') is None
    for name, comment in (('MCPTest.A.Child', 'child'), ('MCPTest.B', 'bee'), ('MCPTest.Old', 'oldroot'), ('MCPTest.Old.Leaf', 'old'),
                          ('MCPTest.Doomed', 'doomed'), ('MCPTest.Mover', 'mover')):
        assert ok(m.create_gameplay_tag, name, SRC, comment, confirm=True)['registered'], name
    assert not ok(m.create_gameplay_tag, 'MCPTest.B', SRC, 'bee', confirm=True)['would_change']
    # Catalog: implicit parents, parent chain, source and comment.
    child = tag('MCPTest.A.Child')
    assert child['explicit'] and child['parents'] == ['MCPTest.A', 'MCPTest'] and child['source'] == SRC and child['comment'] == 'child', child
    assert tag('MCPTest.A')['explicit'] is False
    # Comment update (native UpdateTagInINI never writes comments; the route edits the source list itself).
    bad(m.update_gameplay_tag_comment, 'MCPTest.B', 'buzz', SRC2, confirm=True)                       # source guard
    bad(m.update_gameplay_tag_comment, 'MCPTest.B', 'buzz', SRC, confirm=False)
    ok(m.update_gameplay_tag_comment, 'MCPTest.B', 'buzz', SRC, confirm=True, dry_run=True)
    assert tag('MCPTest.B')['comment'] == 'bee'
    ok(m.update_gameplay_tag_comment, 'MCPTest.B', 'buzz', SRC, confirm=True)
    assert tag('MCPTest.B')['comment'] == 'buzz', tag('MCPTest.B')
    # Rename with children and a redirect.
    bad(m.rename_gameplay_tag, 'MCPTest.Old', 'MCPTest.B', confirm=True)                              # collision
    plan = ok(m.rename_gameplay_tag, 'MCPTest.Old', 'MCPTest.New', confirm=True, dry_run=True)
    assert sorted((r['from'], r['to']) for r in plan['renames']) == [('MCPTest.Old', 'MCPTest.New'), ('MCPTest.Old.Leaf', 'MCPTest.New.Leaf')], plan
    assert tag('MCPTest.Old.Leaf') is not None
    ok(m.rename_gameplay_tag, 'MCPTest.Old', 'MCPTest.New', confirm=True)
    # Native renames children first and then skips the now-implicit parent; the route restores its explicit row.
    assert tag('MCPTest.New')['explicit'] and tag('MCPTest.New')['comment'] == 'oldroot', tag('MCPTest.New')
    res = {r['input']: r for r in ok(m.resolve_gameplay_tags, ['MCPTest.Old.Leaf', 'MCPTest.New.Leaf', 'MCPTest.Nope'])['tags']}
    assert res['MCPTest.Old.Leaf']['redirected'] and res['MCPTest.Old.Leaf']['resolved'] == 'MCPTest.New.Leaf', res
    assert not res['MCPTest.New.Leaf']['redirected'] and not res['MCPTest.Nope']['valid'], res
    bad(m.resolve_gameplay_tags, ['bad tag,'])
    redirects = ok(m.inspect_gameplay_tag_settings, 'MCPTest')['redirects']
    assert len(redirects) == 2 and 'MCPTest.Old.Leaf' in json.dumps(redirects), redirects
    # Unused scan, delete and move.
    unused = {t['name'] for t in ok(m.inspect_unused_gameplay_tags, 'MCPTest')['tags']}
    assert 'MCPTest.Doomed' in unused, unused
    bad(m.delete_gameplay_tag, 'MCPTest.A', SRC, confirm=True)                                         # has children
    bad(m.delete_gameplay_tag, 'MCPTest.Doomed', SRC, confirm=False)
    assert ok(m.delete_gameplay_tag, 'MCPTest.Doomed', SRC, confirm=True, dry_run=True)['deleted'] is False
    ok(m.delete_gameplay_tag, 'MCPTest.Doomed', SRC, confirm=True)
    assert tag('MCPTest.Doomed') is None
    bad(m.move_gameplay_tags_to_source, ['MCPTest.Mover'], 'EnhancedInput', confirm=True)
    assert ok(m.move_gameplay_tags_to_source, ['MCPTest.Mover'], SRC2, confirm=True, dry_run=True)['planned'] == ['MCPTest.Mover']
    moved = ok(m.move_gameplay_tags_to_source, ['MCPTest.Mover'], SRC2, confirm=True)
    assert moved['moved'] == ['MCPTest.Mover'] and moved['native_success'], moved
    assert tag('MCPTest.Mover')['source'] == SRC2 and tag('MCPTest.Mover')['comment'] == 'mover', tag('MCPTest.Mover')


def evaluate_stage():
    def ev(tags, req, mode, exact=False):
        return ok(m.evaluate_gameplay_tags, tags, req, mode, exact)['matches']
    assert ev(['MCPTest.A.Child'], ['MCPTest.A'], 'All') and not ev(['MCPTest.A.Child'], ['MCPTest.A'], 'All', True)
    assert not ev(['MCPTest.A'], ['MCPTest.A.Child'], 'All')                                          # parent does not satisfy child
    assert ev(['MCPTest.B'], ['MCPTest.A', 'MCPTest.B'], 'Any') and not ev(['MCPTest.B'], ['MCPTest.A', 'MCPTest.B'], 'All')
    assert ev(['MCPTest.B'], ['MCPTest.A'], 'None') and not ev(['MCPTest.A.Child'], ['MCPTest.A'], 'None')
    assert ev([], [], 'All') and ev(['MCPTest.B', 'MCPTest.B'], ['MCPTest.B'], 'All')
    assert ok(m.evaluate_gameplay_tags, ['MCPTest.B', 'MCPTest.B'], ['MCPTest.B'], 'All')['unique_tag_count'] == 1
    bad(m.evaluate_gameplay_tags, ['MCPTest.Unregistered'], ['MCPTest.B'], 'All')
    bad(m.evaluate_gameplay_tags, ['MCPTest.B'], ['MCPTest.B'], 'Most')
    # Compound: (AnyTags A) and not (B) ; nested negation; exact; cycle and unreachable rejection.
    q = [{'Mode': 'AllExpressions', 'Tags': [], 'Children': [1, 2]},
         {'Mode': 'AnyTags', 'Tags': ['MCPTest.A'], 'Children': []},
         {'Mode': 'NoExpressions', 'Tags': [], 'Children': [3]},
         {'Mode': 'AnyTags', 'Tags': ['MCPTest.B'], 'Children': []}]
    cq = lambda tags, nodes=q: ok(m.evaluate_gameplay_tag_query, tags, nodes)['matches']
    assert cq(['MCPTest.A.Child']) and not cq(['MCPTest.A.Child', 'MCPTest.B']) and not cq(['MCPTest.B'])
    exact = [{'Mode': 'AnyTagsExact', 'Tags': ['MCPTest.A'], 'Children': []}]
    assert not cq(['MCPTest.A.Child'], exact) and cq(['MCPTest.A'], exact)
    bad(m.evaluate_gameplay_tag_query, ['MCPTest.B'], [{'Mode': 'AllExpressions', 'Tags': [], 'Children': [0]}])
    bad(m.evaluate_gameplay_tag_query, ['MCPTest.B'], q + [{'Mode': 'AnyTags', 'Tags': ['MCPTest.B'], 'Children': []}])
    bad(m.evaluate_gameplay_tag_query, ['MCPTest.B'], [{'Mode': 'AnyTags', 'Tags': [], 'Children': [1]}, q[1]])
    return q


QUERY = None


def fields():
    return {p['name']: p for p in ok(m.inspect_data_asset_gameplay_tags, ASSET)['properties']}


def asset_stage(q):
    m.create_data_asset(ASSET, '/Script/SmartObjectsModule.SmartObjectDefinition')
    f = fields()
    assert f['ActivityTags']['tags'] == [] and f['UserTagFilter']['empty'] and not f['ObjectTagFilter']['editable'], f
    bad(m.edit_data_asset_gameplay_tags, ASSET, 'ActivityTags', ['MCPTest.B'], confirm=False)
    bad(m.edit_data_asset_gameplay_tags, ASSET, 'ActivityTags', ['MCPTest.Unregistered'], confirm=True)
    bad(m.edit_data_asset_gameplay_tags, ASSET, 'ObjectTagFilter', ['MCPTest.B'], confirm=True)      # query / read-only
    bad(m.edit_data_asset_gameplay_tag_query, ASSET, 'ObjectTagFilter', q, confirm=True)
    ok(m.edit_data_asset_gameplay_tags, ASSET, 'ActivityTags', ['MCPTest.B', 'MCPTest.A.Child'], confirm=True, dry_run=True)
    assert fields()['ActivityTags']['tags'] == []
    ok(m.edit_data_asset_gameplay_tags, ASSET, 'ActivityTags', ['MCPTest.B', 'MCPTest.A.Child'], confirm=True)
    assert sorted(fields()['ActivityTags']['tags']) == ['MCPTest.A.Child', 'MCPTest.B'], fields()['ActivityTags']
    ok(m.edit_data_asset_gameplay_tag_query, ASSET, 'UserTagFilter', q, confirm=True, dry_run=True)
    assert fields()['UserTagFilter']['empty']
    ok(m.edit_data_asset_gameplay_tag_query, ASSET, 'UserTagFilter', q, confirm=True)
    uf = fields()['UserTagFilter']
    assert not uf['empty'] and not uf['query_nodes_truncated'] and sorted(uf['tags']) == ['MCPTest.A', 'MCPTest.B'], uf
    # Round trip: the read-back nodes evaluate like the authored ones.
    sq = lambda tags: ok(m.evaluate_data_asset_gameplay_tag_query, ASSET, 'UserTagFilter', tags)['matches']
    assert sq(['MCPTest.A.Child']) and not sq(['MCPTest.A.Child', 'MCPTest.B'])
    for tags in (['MCPTest.A.Child'], ['MCPTest.A.Child', 'MCPTest.B'], ['MCPTest.B']):
        assert ok(m.evaluate_gameplay_tag_query, tags, uf['query_nodes'], uf['root_index'])['matches'] == sq(tags), tags
    bad(m.evaluate_data_asset_gameplay_tag_query, ASSET, 'ActivityTags', ['MCPTest.B'])                 # not a query
    assert httpx.post(BASE + '/assets/save', json={'AssetPath': ASSET}, timeout=120).status_code == 200
    # The saved asset references MCPTest.B (the native scan reads asset-registry tag references, refreshed on save).
    assert 'MCPTest.B' not in {t['name'] for t in ok(m.inspect_unused_gameplay_tags, 'MCPTest')['tags']}


def table_stage():
    bad(m.edit_gameplay_tag_table_row, TABLE, 'Row1', 'MCPTable.Alpha', 'alpha', confirm=False)
    bad(m.edit_gameplay_tag_table_row, TABLE, 'Row1', 'MCPTable..Bad', confirm=True)
    ok(m.edit_gameplay_tag_table_row, TABLE, 'Row1', 'MCPTable.Alpha', 'alpha', confirm=True, dry_run=True)
    ok(m.edit_gameplay_tag_table_row, TABLE, 'Row1', 'MCPTable.Alpha', 'alpha', confirm=True, save=True)
    ok(m.edit_gameplay_tag_table_row, TABLE, 'Row2', 'MCPTable.Beta', 'beta', confirm=True, save=True)
    bad(m.edit_gameplay_tag_table_row, TABLE, 'Row3', 'MCPTable.Alpha', confirm=True)                  # duplicate tag
    bad(m.edit_gameplay_tag_table_row, TABLE, 'Row1', 'MCPTable.Gamma', confirm=True)                  # identity change
    ok(m.edit_gameplay_tag_table_row, TABLE, 'Row1', 'MCPTable.Alpha', 'alpha2', confirm=True, save=True)
    assert tag('MCPTable.Alpha') is None                                                               # not a source yet
    bad(m.register_gameplay_tag_table, TABLE, confirm=False)
    ok(m.register_gameplay_tag_table, TABLE, confirm=True, dry_run=True)
    assert not ok(m.inspect_gameplay_tag_settings)['tables']
    ok(m.register_gameplay_tag_table, TABLE, confirm=True)
    assert not ok(m.register_gameplay_tag_table, TABLE, confirm=True).get('would_change', False)
    assert tag('MCPTable.Alpha') and tag('MCPTable.Alpha')['comment'] == 'alpha2', tag('MCPTable.Alpha')
    assert any(TABLE in str(t) for t in ok(m.inspect_gameplay_tag_settings)['tables'])


def snapshot():
    f = fields()
    s = ok(m.inspect_gameplay_tag_settings, 'MCP')
    return {
        'tags': {n: {k: tag(n)[k] for k in ('explicit', 'source', 'comment', 'parents')} for n in
                 ('MCPTest.A.Child', 'MCPTest.B', 'MCPTest.New', 'MCPTest.New.Leaf', 'MCPTest.Mover', 'MCPTable.Alpha', 'MCPTable.Beta')},
        'gone': [n for n in ('MCPTest.Doomed', 'MCPTest.Old', 'MCPTest.Old.Leaf') if tag(n) is not None],
        'redirects': s['redirects'], 'tables': s['tables'],
        'activity': sorted(f['ActivityTags']['tags']),
        'query': {k: f['UserTagFilter'][k] for k in ('query_nodes', 'root_index', 'tags', 'description')},
        'stored': [ok(m.evaluate_data_asset_gameplay_tag_query, ASSET, 'UserTagFilter', t)['matches']
                   for t in (['MCPTest.A.Child'], ['MCPTest.A.Child', 'MCPTest.B'], ['MCPTest.B'])],
    }


def prepare():
    cleanup()
    ini_stage()
    asset_stage(evaluate_stage())
    table_stage()
    snap = snapshot()
    assert snap['redirects'], ('rename redirect not reported by settings', snap)
    assert snap['gone'] == [] and snap['stored'] == [True, False, False], snap
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snap}, indent=1), encoding='utf-8')
    print('Gameplay Tag sources, tags, table source and Data Asset fields prepared')


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    got = json.loads(json.dumps(snapshot()))
    assert got == st['snapshot'], json.dumps({'got': got, 'want': st['snapshot']})[:3000]
    assert sorted(explicit()) == ['MCPTest.A.Child', 'MCPTest.B', 'MCPTest.Mover', 'MCPTest.New', 'MCPTest.New.Leaf'], explicit()
    print('Gameplay Tag ini, table and Data Asset state identical after cold reload')
    cleanup()


def cleanup():
    """Remove the asset, the table rows and the ini sources. Registered tags stay in memory until the next restart."""
    m.inspect_data_asset_gameplay_tags(ASSET)   # load first: a delete right after startup can leave an unloaded asset
    httpx.post(BASE + '/assets/delete', json={'AssetPath': ASSET}, timeout=300)
    for row in ('Row1', 'Row2', 'Row3'):
        httpx.request('DELETE', BASE + '/data-tables/rows', json={'AssetPath': TABLE, 'RowName': row}, timeout=120)
    httpx.post(BASE + '/assets/save', json={'AssetPath': TABLE}, timeout=120)
    for p in INI:
        p.unlink(missing_ok=True)
    if DEFAULT_INI.exists() and 'DT_MCP_Tags' in DEFAULT_INI.read_text(encoding='utf-8'):
        DEFAULT_INI.unlink()   # the project had no DefaultGameplayTags.ini; registration created it
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
