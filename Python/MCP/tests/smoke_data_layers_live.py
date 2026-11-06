"""World Partition Data Layers: standalone assets, instances, hierarchy, states, actor membership and policies; prepare, restart, verify.

Usage: smoke_data_layers_live.py prepare|verify|cleanup. Copies the OpenWorld template to a scratch map and drives the
Data Layer MCP tools: standalone asset creation/type/load filter/actor filters/debug color/consumers, asset-backed and
private instance creation, inventory, hierarchy and impact discovery, parent, initial runtime state/visibility, short
name, streaming priority/slow-streaming override, local lock, filter inclusion, instance asset replacement, editor
visibility/loading, actor membership (single, whole set, name-dependent move), private embedded asset color/filters,
instance removal and partition server-streaming/logic policies. Each edit is rejected with a stale expected value,
dry-run checked, then applied. Authored state must survive a cold editor restart.
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
MAP = '/Game/UE5MCP_Test/MCP_DataLayers'
TEMPLATE = '/Engine/Maps/Templates/OpenWorld'
ASSETS = {n: f'/Game/UE5MCP_Test/DL_MCP_{n}' for n in 'ABCDE'}
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'data_layers.json'


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


def edit(fn, state, *a, changes=True, **kw):
    before = state()
    ok(fn, *a, confirm=True, dry_run=True, **kw)
    assert state() == before, (fn.__name__, 'dry run changed state')
    r = ok(fn, *a, confirm=True, dry_run=False, **kw)
    if changes:
        assert state() != before, (fn.__name__, 'edit left state unchanged', str(r)[:300])
    return r


def obj(name):
    return ASSETS[name] + '.DL_MCP_' + name


def save():
    assert httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600).json()['success']
    for p in ASSETS.values():
        httpx.post(BASE + '/assets/save', json={'AssetPath': p}, timeout=600)


def wp():
    return ok(m.inspect_world_partition)['partition_path']


def layers():
    return ok(m.inspect_partition_data_layers, wp(), 0, 128)['layers']


def layer(asset=None, private=False):
    """Registered instance for a standalone asset name, or the private editor layer."""
    return next(x for x in layers() if (x['private'] if private else x['asset_path'] == obj(asset)))


def asset(name):
    return ok(m.inspect_data_layer_asset, obj(name))


# ---------------------------------------------------------------- standalone assets
def asset_stage():
    for n in ASSETS:
        bad(m.create_data_layer_asset, ASSETS[n])                                  # confirmation required
        d = ok(m.create_data_layer_asset, ASSETS[n], confirm=True, dry_run=True)
        assert d['dry_run'] and 'errorMessage' in J(m.inspect_data_layer_asset(obj(n))), d
        r = ok(m.create_data_layer_asset, ASSETS[n], confirm=True)
        assert r['created'] and r['native_default_type'] == 0, r
    bad(m.create_data_layer_asset, ASSETS['A'], confirm=True)                     # no overwrite
    bad(m.create_data_layer_asset, '/Engine/DL_Nope', confirm=True)
    A = lambda: asset('A')
    bad(m.set_data_layer_asset_enum, obj('A'), 1, 'LoadFilter', 0, 1, confirm=True)       # stale type
    bad(m.set_data_layer_asset_enum, obj('A'), 0, 'LoadFilter', 0, 3, confirm=True)
    edit(m.set_data_layer_asset_enum, A, obj('A'), 0, 'LoadFilter', 0, 1)
    assert A()['client_only'] and A()['load_filter'] == 1, A()
    E = lambda: asset('E')
    edit(m.set_data_layer_asset_enum, E, obj('E'), 0, 'DataLayerType', 0, 1)
    assert E()['type'] == 1 and not E()['runtime'], E()
    bad(m.set_data_layer_asset_enum, obj('E'), 1, 'LoadFilter', 0, 1, confirm=True)       # load filter is runtime-only
    B = lambda: asset('B')
    sup = B()['supports_actor_filters']
    bad(m.set_data_layer_asset_actor_filters, obj('B'), 0, not sup, not sup, confirm=True)
    edit(m.set_data_layer_asset_actor_filters, B, obj('B'), 0, sup, not sup)
    col = A()['debug_color_bytes']
    bad(m.set_data_layer_asset_debug_color, obj('A'), 0, [1, 2, 3, 4], [10, 20, 30, 255], confirm=True)
    bad(m.set_data_layer_asset_debug_color, obj('A'), 0, col, [10, 20, 300, 255], confirm=True)
    edit(m.set_data_layer_asset_debug_color, A, obj('A'), 0, col, [10, 20, 30, 255])
    assert A()['debug_color_bytes'] == [10, 20, 30, 255]
    return {n: asset(n)['type'] for n in ASSETS}


# ---------------------------------------------------------------- instances and inventory
def instance_stage():
    W = wp()
    count = lambda: ok(m.inspect_partition_data_layers, W, 0, 128)['layer_count']
    for n in 'ABCE':
        c = count()
        bad(m.create_partition_data_layer_instance, W, obj(n), c + 1, confirm=True)
        d = ok(m.create_partition_data_layer_instance, W, obj(n), c, confirm=True, dry_run=True)
        assert count() == c, d
        ok(m.create_partition_data_layer_instance, W, obj(n), c, confirm=True)
        assert count() == c + 1
    bad(m.create_partition_data_layer_instance, W, obj('A'), count(), confirm=True)          # duplicate asset
    c = count()
    bad(m.create_partition_private_data_layer, W, c + 1, confirm=True)
    ok(m.create_partition_private_data_layer, W, c, confirm=True, dry_run=True)
    assert count() == c
    ok(m.create_partition_private_data_layer, W, c, confirm=True)
    assert count() == c + 1 and layer(private=True)['layer_type'] == 1, layer(private=True)
    page = ok(m.inspect_partition_data_layers, W, 1, 2)
    assert len(page['layers']) == 2 and page['has_more'], page
    bad(m.inspect_partition_data_layers, W, 0, 0)
    # Consumers: the standalone asset now lists its world instance.
    a = ok(m.inspect_data_layer_asset, obj('A'), 0, 8)
    assert a['loaded_instance_count'] == 1 and a['loaded_instances'][0]['path'] if a['loaded_instances'] and 'path' in a['loaded_instances'][0] else a['loaded_instance_paths'] == [layer('A')['path']], a
    return count()


# ---------------------------------------------------------------- hierarchy, states, naming, streaming, lock, filters
def authoring_stage():
    W = wp()
    A, B, C, E = (layer(n)['path'] for n in 'ABCE')
    L = lambda n: (lambda: layer(n))
    # Parent: B under A; an editor layer cannot be a child of a runtime layer (native type rule).
    bad(m.set_partition_data_layer_parent, W, B, A, A, confirm=True)
    bad(m.set_partition_data_layer_parent, W, E, '', A, confirm=True)
    bad(m.set_partition_data_layer_parent, W, A, '', A, confirm=True)                     # self parent
    edit(m.set_partition_data_layer_parent, L('B'), W, B, '', A)
    assert layer('B')['parent_path'] == A
    bad(m.set_partition_data_layer_parent, W, A, '', B, confirm=True)                     # cycle
    h = ok(m.inspect_partition_data_layer_hierarchy, W, A)
    assert B in json.dumps(h), h
    hb = ok(m.inspect_partition_data_layer_hierarchy, W, B)
    assert A in json.dumps(hb), hb
    imp = ok(m.inspect_partition_data_layer_impact, W, A)
    assert B in json.dumps(imp), imp
    # Initial runtime state and visibility on the runtime layer A.
    st = layer('A')['initial_runtime_state']
    bad(m.set_partition_data_layer_initial_runtime_state, W, A, st + 1, 2, confirm=True)
    bad(m.set_partition_data_layer_initial_runtime_state, W, A, st, 7, confirm=True)
    edit(m.set_partition_data_layer_initial_runtime_state, L('A'), W, A, st, 2)
    assert layer('A')['initial_runtime_state'] == 2
    bad(m.set_partition_data_layer_initial_runtime_state, W, E, layer('E')['initial_runtime_state'], 1, confirm=True)  # editor layer
    vis = layer('A')['initially_visible']
    bad(m.set_partition_data_layer_initial_visibility, W, A, not vis, vis, confirm=True)
    edit(m.set_partition_data_layer_initial_visibility, L('A'), W, A, vis, not vis)
    # Streaming priority and slow-streaming override on runtime layer C.
    c = layer('C')
    bad(m.set_partition_data_layer_streaming_setting, W, C, 1, 'StreamingPriority', c['streaming_priority'], 5, confirm=True)
    edit(m.set_partition_data_layer_streaming_setting, L('C'), W, C, 0, 'StreamingPriority', c['streaming_priority'], -3)
    edit(m.set_partition_data_layer_streaming_setting, L('C'), W, C, 0, 'OverrideBlockOnSlowStreaming', c['slow_streaming_override'], 2)
    bad(m.set_partition_data_layer_streaming_setting, W, C, 0, 'OverrideBlockOnSlowStreaming', 2, 3, confirm=True)
    assert layer('C')['streaming_priority'] == -3 and layer('C')['slow_streaming_override'] == 2, layer('C')
    # Short name: asset-backed names follow the asset, private layers are renameable.
    bad(m.set_partition_data_layer_short_name, W, A, layer('A')['short_name'], 'Renamed', confirm=True)
    P = layer(private=True)
    PL = lambda: layer(private=True)
    bad(m.set_partition_data_layer_short_name, W, P['path'], 'Wrong', 'MCP_Private', confirm=True)
    edit(m.set_partition_data_layer_short_name, PL, W, P['path'], P['short_name'], 'MCP_Private')
    assert PL()['short_name'] == 'MCP_Private', PL()
    # Local lock.
    edit(m.set_partition_data_layer_locked, L('C'), W, C, False, True)
    assert layer('C')['local_locked']
    bad(m.set_partition_data_layer_locked, W, C, False, False, confirm=True)
    edit(m.set_partition_data_layer_locked, L('C'), W, C, True, False)
    # Per-instance filter inclusion needs an asset that supports actor filters (B).
    b = layer('B')
    assert b['supports_actor_filters'], b
    bad(m.set_partition_data_layer_filter_included, W, A, 0, obj('A'), True, False, confirm=True)   # A has no filter support
    bad(m.set_partition_data_layer_filter_included, W, B, 0, obj('A'), b['filter_default_included'], False, confirm=True)
    edit(m.set_partition_data_layer_filter_included, L('B'), W, B, 0, obj('B'), b['filter_default_included'], not b['filter_default_included'])
    # Replace C's asset with D.
    n = len(layers())
    bad(m.set_partition_data_layer_instance_asset, W, C, 0, obj('C'), obj('A'), n, 0, confirm=True)  # A already has an instance
    bad(m.set_partition_data_layer_instance_asset, W, C, 0, obj('B'), obj('D'), n, 0, confirm=True)
    save()                                                                                        # changed execution needs clean packages
    edit(m.set_partition_data_layer_instance_asset, lambda: [x['asset_path'] for x in layers()], W, C, 0, obj('C'), obj('D'), n, 0)
    assert layer('D')['path'] == C
    return {n: layer(n) for n in 'ABDE'}


# ---------------------------------------------------------------- transient editor visibility and loading
def editor_state_stage():
    W = wp()
    E = layer('E')['path']
    L = lambda: {k: layer('E')[k] for k in ('visible', 'loaded_in_editor')}
    bad(m.set_partition_data_layer_visibility, W, E, False, False, confirm=True)
    edit(m.set_partition_data_layer_visibility, L, W, E, True, False)
    edit(m.set_partition_data_layer_visibility, L, W, E, False, True)
    save()
    bad(m.set_partition_data_layer_loading, W, E, False, False, confirm=True)
    edit(m.set_partition_data_layer_loading, L, W, E, True, False)
    save()
    edit(m.set_partition_data_layer_loading, L, W, E, False, True)
    return L()


# ---------------------------------------------------------------- actor membership
def spawn(location):
    path = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.StaticMeshActor',
                      'Location': dict(zip('XYZ', location))}, timeout=60).text
    assert path.startswith(MAP), path
    return path


def descriptor(path):
    start = 0
    while True:
        page = ok(m.inspect_world_partition_actor_descriptors, start, 128)
        for d in page['actor_descriptors']:
            if d['actor_soft_path'] == path:
                return d
        assert page['has_more'], ('descriptor not found', path)
        start = page['next_start']


def membership_stage():
    W = wp()
    paths = [spawn([500, 500, 100]), spawn([800, 500, 100])]
    save()
    out = {}
    A, B, E = (layer(n)['path'] for n in 'ABE')
    for path in paths:
        d = descriptor(path)
        args = (W, d['container_path'], d['guid'], path)
        cur = lambda: sorted(ok(m.inspect_loaded_partition_actor_data_layers, *args)['direct_member_paths'])
        assert cur() == [], cur()
        if path == paths[0]:
            bad(m.set_loaded_partition_actor_data_layer, *args, A, True, True, confirm=True)
            edit(m.set_loaded_partition_actor_data_layer, cur, *args, A, False, True)
            edit(m.set_loaded_partition_actor_data_layer, cur, *args, E, False, True)
            assert cur() == sorted([A, E]), cur()
            edit(m.set_loaded_partition_actor_data_layer, cur, *args, E, True, False)
            bad(m.replace_loaded_partition_actor_data_layers, *args, [], [A, B], confirm=True)
            bad(m.replace_loaded_partition_actor_data_layers, *args, [A], [A, A], confirm=True)
            edit(m.replace_loaded_partition_actor_data_layers, cur, *args, [A], [A, B, E])
            assert cur() == sorted([A, B, E]), cur()
        else:
            # The name-dependent move applies only to actors whose package depends on membership.
            info = ok(m.inspect_loaded_partition_actor_data_layers, *args)
            assert info['requires_partition_move'] is False, info
            bad(m.move_partition_actor_data_layers, *args, info['external_package'], [], [B], confirm=True, dry_run=True)
            edit(m.replace_loaded_partition_actor_data_layers, cur, *args, [], [B])
            assert cur() == [B], cur()
        out[path] = cur()
    save()
    return {'actors': paths, 'membership': out}


# ---------------------------------------------------------------- private embedded asset
def private_stage():
    W = wp()
    P = layer(private=True)
    I, Ap = P['path'], P['asset_path']
    S = lambda: ok(m.inspect_partition_private_data_layer_asset, W, I, Ap)
    s = S()
    assert s['private_embedded'] and s['type'] == 1, s
    bad(m.inspect_partition_private_data_layer_asset, W, layer('A')['path'], Ap)
    col = s['debug_color_bytes']
    bad(m.set_private_data_layer_asset_debug_color, W, I, Ap, 1, [1, 1, 1, 1], [0, 200, 100, 255], confirm=True)
    bad(m.set_private_data_layer_asset_debug_color, W, I, Ap, 0, col, [0, 200, 100, 255], confirm=True)
    edit(m.set_private_data_layer_asset_debug_color, S, W, I, Ap, 1, col, [0, 200, 100, 255])
    sup = S()['supports_actor_filters']
    bad(m.set_private_data_layer_asset_actor_filters, W, I, Ap, 1, not sup, not sup, confirm=True)
    edit(m.set_private_data_layer_asset_actor_filters, S, W, I, Ap, 1, sup, not sup)
    bad(m.set_data_layer_asset_debug_color, Ap, 1, col, [1, 2, 3, 255], confirm=True)          # standalone setters refuse private assets
    return {k: S()[k] for k in ('debug_color_bytes', 'supports_actor_filters', 'type')}


# ---------------------------------------------------------------- removal and partition policies
def removal_stage():
    W = wp()
    A, B = layer('A'), layer('B')
    n = len(layers())
    impact = ok(m.inspect_partition_data_layer_impact, W, A['path'])
    assert impact['direct_child_count'] == 1 and impact['loaded_member_count'] >= 1, impact
    bad(m.delete_partition_data_layer_instance, W, A['path'], A['short_name'], obj('A'), n, 0, impact['loaded_member_count'], confirm=True)
    # Remove the leaf instance D (formerly C): no children or actors.
    D = layer('D')
    di = ok(m.inspect_partition_data_layer_impact, W, D['path'])
    args = (W, D['path'], D['short_name'], obj('D'), n, di['direct_child_count'], di['loaded_member_count'])
    bad(m.delete_partition_data_layer_instance, W, D['path'], D['name'], obj('D'), n, 0, 0, confirm=True)   # name is the short name
    bad(m.delete_partition_data_layer_instance, *args[:3], obj('A'), *args[4:], confirm=True)
    save()
    edit(m.delete_partition_data_layer_instance, lambda: len(layers()), *args)
    assert len(layers()) == n - 1 and all(x['asset_path'] != obj('D') for x in layers())
    # Partition policies.
    pol = lambda: ok(m.inspect_partition_policies, W)
    p = pol()
    def cur(field):
        return next(x['value'] for x in pol()['policies'] if x['field_name'] == field)
    op = cur('DataLayersLogicOperator')
    bad(m.set_partition_policy, W, 'DataLayersLogicOperator', 1 - op, op, confirm=True)
    bad(m.set_partition_policy, W, 'DataLayersLogicOperator', op, 5, confirm=True)
    edit(m.set_partition_policy, pol, W, 'DataLayersLogicOperator', op, 1 - op)
    sm = cur('ServerStreamingMode')
    edit(m.set_partition_policy, pol, W, 'ServerStreamingMode', sm, 2 if sm != 2 else 1)
    p = pol()
    so = cur('ServerStreamingOutMode')
    edit(m.set_partition_policy, pol, W, 'ServerStreamingOutMode', so, 1 if so != 1 else 2)
    return pol()


STAGES = [asset_stage, instance_stage, authoring_stage, editor_state_stage, membership_stage, private_stage, removal_stage]


def snapshot(actors):
    W = wp()
    out = {'layers': [{k: v for k, v in x.items() if k not in ('package_dirty', 'visible', 'loaded_in_editor', 'effectively_visible', 'effectively_loaded')}
                      for x in layers()],
           'assets': {n: {k: v for k, v in asset(n).items() if k not in ('package_dirty', 'scope', 'loaded_instances', 'loaded_instance_paths')}
                      for n in 'ABE'},
           'policies': {k: v for k, v in ok(m.inspect_partition_policies, W).items() if k not in ('scope', 'package_dirty')}}
    out['members'] = {}
    for path in actors:
        d = descriptor(path)
        out['members'][path] = sorted(d.get('data_layers', []), key=json.dumps)
    return out


def prepare():
    cleanup()
    assert ok(m.create_editor_world, MAP, TEMPLATE, True, 'discard', True)['success']
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    out = {}
    for fn in STAGES:
        out[fn.__name__] = fn()
        save()
    actors = out['membership_stage']['actors']
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'actors': actors, 'snapshot': snapshot(actors)}, indent=1))
    print('data layers prepared; map saved')


def verify():
    st = json.loads(STATE.read_text())
    assert httpx.post(BASE + '/worlds/load', json={'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()['success']
    got = json.loads(json.dumps(snapshot(st['actors'])))
    want = st['snapshot']
    diff = [k for k in want if got.get(k) != want[k]]
    assert not diff, (diff, json.dumps({k: (got.get(k), want[k]) for k in diff})[:3000])
    print('data layers identical after cold reload')
    cleanup()


def cleanup():
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=300)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP + '_HLOD0_Instancing'}, timeout=300)   # created by the template copy
    for p in ASSETS.values():
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=120)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
