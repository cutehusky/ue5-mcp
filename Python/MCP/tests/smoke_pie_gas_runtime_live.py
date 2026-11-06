"""Gameplay Ability System and Gameplay Tag runtime routes against a live PIE session (/editor/pie/start).

Setup (editor): temporary tag ini; GA_MCP_Run (cost GE_MCP_RunCost, cooldown GE_MCP_RunCd, trigger on MCPRun.Event, asset tag
MCPRun.Ability), GE_MCP_RunBuff (infinite, Health AddBase SetByCaller MCPRun.Data + constant Mana, grants MCPRun.Buff);
BP_MCP_GasActor (Actor + AbilitySystemComponent) placed in a copy of the ThirdPerson map.
run (PIE): attribute sets and base values; grants with level/input/source tags/source object, level/input/source-tag
updates; activation checks with cost/cooldown diagnostics; activate/cancel/input; activation, cancellation and matching
by tags; gameplay events with targets/tags/optional objects; effect application with level, dynamic tags, causer and
SetByCaller; SetByCaller/level/inhibition updates; simple/compound/definition/attribute/source/exclusion effect queries;
stack removal; loose tags and aggregate counts; one-shot cues; component tag providers and provider query evaluation.
Runtime state is not persisted, so there is no cold-reload phase; cleanup removes the map, Blueprints and tag ini.
"""
import json
import sys
import time

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'run'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
MAP = '/Game/UE5MCP_Test/MCP_PIE_Gas'
ROOT = '/Game/UE5MCP_Test/GasRun'
ACTOR = f'{ROOT}/BP_MCP_GasActor'
SRC = 'MCPRun_Tags.ini'
INI = PROJECT / 'Config' / 'Tags' / SRC
ATTR = '/Script/GameplayAbilities.AbilitySystemTestAttributeSet:'
SET = '/Script/GameplayAbilities.AbilitySystemTestAttributeSet'
TAGS = ['MCPRun.Ability', 'MCPRun.Event', 'MCPRun.Data', 'MCPRun.Buff', 'MCPRun.Cooldown', 'MCPRun.Source', 'MCPRun.Dynamic',
        'MCPRun.Loose', 'MCPRun.Other', 'GameplayCue.MCPRun.Burst']
Y = dict(confirm=True)
MESH = '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple'
SPAWNED = {}


def C(name):
    return f'{ROOT}/{name}.{name}_C'


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


def load(path):
    r = httpx.post(BASE + '/worlds/load', json={'WorldPath': path, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600).json()
    assert r.get('success'), r


def pie(start):
    httpx.post(BASE + ('/editor/pie/start' if start else '/editor/pie/stop'), headers={'Content-Length': '0'}, timeout=60)
    for _ in range(60):
        if ok(m.get_ue_editor_status)['is_playing'] == start:
            time.sleep(1)
            return
        time.sleep(1)
    raise AssertionError('PIE did not ' + ('start' if start else 'stop'))


def setup():
    ok(m.create_gameplay_tag_source, SRC, **Y)
    for t in TAGS:
        ok(m.create_gameplay_tag, t, SRC, 'MCP runtime test', **Y)
    for name, kind in (('GA_MCP_Run', 'ability'), ('GE_MCP_RunCost', 'effect'), ('GE_MCP_RunCd', 'effect'), ('GE_MCP_RunBuff', 'effect'),
                       ('GE_MCP_RunTick', 'effect')):
        ok(m.create_gameplay_blueprint, f'{ROOT}/{name}', kind, save=True)
    edit = lambda name, **kw: ok(m.edit_gameplay_blueprint_defaults, f'{ROOT}/{name}', kw.pop('properties', {}), save=True, **Y, **kw)
    edit('GE_MCP_RunCost', timing={'DurationPolicy': 'Instant'},
         modifiers=[{'AttributePath': ATTR + 'Mana', 'Operation': 'AddBase', 'MagnitudeType': 'Constant', 'Magnitude': -30}])
    edit('GE_MCP_RunCd', timing={'DurationPolicy': 'HasDuration', 'Duration': 60}, effect_components=[
        {'ClassPath': '/Script/GameplayAbilities.TargetTagsGameplayEffectComponent',
         'InheritedTags': [{'PropertyName': 'InheritableGrantedTagsContainer', 'Added': ['MCPRun.Cooldown'], 'Removed': []}]}])
    edit('GE_MCP_RunBuff', timing={'DurationPolicy': 'Infinite'}, stacking={'StackingType': 'AggregateByTarget', 'StackLimitCount': '3'},
         modifiers=[{'AttributePath': ATTR + 'Health', 'Operation': 'AddBase', 'MagnitudeType': 'SetByCaller', 'DataTag': 'MCPRun.Data'},
                    {'AttributePath': ATTR + 'MaxMana', 'Operation': 'AddBase', 'MagnitudeType': 'Constant', 'Magnitude': 10}],
         effect_components=[{'ClassPath': '/Script/GameplayAbilities.TargetTagsGameplayEffectComponent',
                             'InheritedTags': [{'PropertyName': 'InheritableGrantedTagsContainer', 'Added': ['MCPRun.Buff'], 'Removed': []}]}])
    edit('GE_MCP_RunTick', timing={'DurationPolicy': 'HasDuration', 'Duration': 30, 'Period': 0.2},
         modifiers=[{'AttributePath': ATTR + 'Mana', 'Operation': 'AddBase', 'MagnitudeType': 'Constant', 'Magnitude': 1}])
    edit('GA_MCP_Run', tag_properties={'AbilityTags': '["MCPRun.Ability"]'},
         triggers=[{'Tag': 'MCPRun.Event', 'Source': 'GameplayEvent'}],
         class_references={'CostGameplayEffectClass': C('GE_MCP_RunCost'), 'CooldownGameplayEffectClass': C('GE_MCP_RunCd')})
    m.create_blueprint(ACTOR, 'Actor')
    m.add_component_to_bp(ACTOR, 'AbilitySystemComponent', 'ASC', '')
    m.compile_blueprint(ACTOR)
    httpx.post(BASE + '/assets/save', json={'AssetPath': ACTOR}, timeout=120)
    ok(m.create_editor_world, MAP, '/Game/ThirdPerson/Lvl_ThirdPerson', True, 'discard', True)
    load(MAP)
    SPAWNED['mesh'] = m.spawn_editor_actor(asset_path=MESH, location={'X': 0, 'Y': 400, 'Z': 100}).strip().strip('"')
    assert 'PersistentLevel' in SPAWNED['mesh'], SPAWNED['mesh']
    for x in (0, 400):                                                                           # source and target actors
        assert 'PersistentLevel' in m.spawn_editor_actor(actor_class=C('BP_MCP_GasActor'), location={'X': x, 'Y': 0, 'Z': 100})


def handles(r):
    """Every value stored under a *handle key anywhere in a response (handles are small integers, so no substring tests)."""
    out = set()
    if isinstance(r, dict):
        for k, v in r.items():
            if k.endswith('handle') and isinstance(v, (str, int)):
                out.add(str(v))
            else:
                out |= handles(v)
    elif isinstance(r, list):
        for v in r:
            out |= handles(v)
    return out


def components():
    return ok(m.inspect_ability_system_runtime, '', 'BP_MCP_GasActor')['components']


def comp(path):
    return ok(m.inspect_ability_system_runtime, path)['components'][0]


def attr(path, name):
    for s in comp(path)['attribute_sets']:
        for a in s.get('attributes', []):
            if a['name'] == name or a.get('field_path', '').endswith(':' + name):
                return a
    raise AssertionError((name, comp(path)['attribute_sets']))


def grant_row(path, handle):
    return next(g for g in comp(path)['abilities'] if g['handle'] == handle)


def runtime():
    cs = components()
    assert len(cs) == 2, cs
    asc, other = cs[0]['component_path'], cs[1]['component_path']
    owner, other_owner = cs[0]['owner_path'], cs[1]['owner_path']
    # Attribute sets and base values.
    bad(m.add_runtime_attribute_set, asc, SET)
    ok(m.add_runtime_attribute_set, asc, SET, confirm=True, dry_run=True)
    assert comp(asc)['attribute_sets'] == []
    ok(m.add_runtime_attribute_set, asc, SET, **Y)
    ok(m.add_runtime_attribute_set, other, SET, **Y)
    bad(m.add_runtime_attribute_set, asc, SET, **Y)                                            # related set exists
    print('attributes:', json.dumps(comp(asc)['attribute_sets'])[:600])
    bad(m.set_runtime_gameplay_attribute, asc, ATTR + 'Nope', 1, **Y)
    ok(m.set_runtime_gameplay_attribute, asc, ATTR + 'Mana', 50, **Y)
    print('mana:', attr(asc, 'Mana'))
    # Grants.
    bad(m.grant_runtime_gameplay_ability, asc, C('GE_MCP_RunCost'), **Y)                       # wrong family
    g = ok(m.grant_runtime_gameplay_ability, asc, C('GA_MCP_Run'), level=2, input_id=4, dynamic_source_tags=['MCPRun.Source'],
           source_object_path=other_owner, **Y)
    print('grant:', json.dumps(g)[:600])
    h = g.get('handle') or g.get('ability_handle')
    row = grant_row(asc, h)
    print('grant row:', json.dumps(row)[:900])
    ok(m.set_runtime_gameplay_ability_level, asc, h, 3, **Y)
    ok(m.set_runtime_ability_input_id, asc, h, 7, **Y)
    ok(m.set_runtime_ability_source_tags, asc, h, ['MCPRun.Dynamic'], **Y)
    row = grant_row(asc, h)
    assert row['level'] == 3 and row['input_id'] == 7 and 'MCPRun.Dynamic' in json.dumps(row), row
    # Activation checks: cost (Mana 50 >= 30) passes now.
    chk = ok(m.check_runtime_gameplay_ability, asc, h)
    print('check:', json.dumps(chk)[:900])
    # Activate (BP ability without a graph stays active), then cancel; input pressed/released.
    ok(m.control_ability_system_runtime, asc, h, 'activate', **Y)
    time.sleep(0.5)
    active = grant_row(asc, h)
    assert active['active'] and active['instance_count'] == 1 and active['instances'], active              # instance diagnostics
    # A Blueprint ability without a graph never commits, so drive the diagnostics directly: low Mana fails the cost,
    # an applied cooldown effect fails the cooldown and reports its tag and remaining time.
    ok(m.set_runtime_gameplay_attribute, asc, ATTR + 'Mana', 10, **Y)
    cd = ok(m.apply_runtime_gameplay_effect, asc, C('GE_MCP_RunCd'), **Y)
    chk2 = ok(m.check_runtime_gameplay_ability, asc, h)
    print('check blocked:', json.dumps(chk2)[:900])
    assert not chk2['can_activate'] and not chk2['cost_check_passed'] and not chk2['cooldown_check_passed'], chk2
    assert 'MCPRun.Cooldown' in chk2['cooldown_tags'] and 0 < chk2['cooldown_remaining'] <= 60, chk2
    ok(m.remove_runtime_gameplay_effect, asc, cd.get('active_handle') or cd.get('effect_handle') or cd.get('handle'), -1, **Y)
    ok(m.set_runtime_gameplay_attribute, asc, ATTR + 'Mana', 50, **Y)
    assert ok(m.check_runtime_gameplay_ability, asc, h)['can_activate']
    ctx = ok(m.check_runtime_gameplay_ability, asc, h, source_tags=['MCPRun.Source'], target_tags=['MCPRun.Other'])
    assert ctx['explicit_context_tags'] and ctx['source_tag_count'] == 1 and ctx['target_tag_count'] == 1, ctx
    bad(m.check_runtime_gameplay_ability, asc, h, source_tags=['MCPRun.Unregistered'])
    ok(m.control_ability_system_runtime, asc, h, 'cancel', **Y)
    ok(m.dispatch_runtime_ability_input, asc, h, 'press')
    ok(m.dispatch_runtime_ability_input, asc, h, 'release')
    # By tags.
    match = ok(m.match_runtime_abilities_by_tags, asc, ['MCPRun.Ability'])
    assert h in handles(match), match
    assert h not in handles(ok(m.match_runtime_abilities_by_tags, asc, ['MCPRun.Other']))
    ok(m.activate_runtime_abilities_by_tags, asc, ['MCPRun.Ability'], confirm=True, dry_run=True)
    ok(m.activate_runtime_abilities_by_tags, asc, ['MCPRun.Ability'], **Y)
    bad(m.cancel_runtime_abilities_by_tags, asc, ['MCPRun.Ability'], excluded_tags=['MCPRun.Ability'], **Y)   # overlap
    ok(m.cancel_runtime_abilities_by_tags, asc, ['MCPRun.Ability'], **Y)
    # Gameplay event triggers the ability; targets, tags and optional objects are accepted.
    ok(m.send_runtime_gameplay_event, asc, 'MCPRun.Event', 2.0, instigator_path=other_owner, target_path=owner,
       target_actor_paths=[other_owner], optional_object_path=other_owner, instigator_tags=['MCPRun.Source'], target_tags=['MCPRun.Other'])
    bad(m.send_runtime_gameplay_event, asc, 'MCPRun.Unregistered')
    # Effects.
    bad(m.apply_runtime_gameplay_effect, asc, C('GE_MCP_RunBuff'), set_by_caller={'MCPRun.Unregistered': 1}, **Y)
    bad(m.apply_runtime_gameplay_effect, asc, C('GE_MCP_RunBuff'), set_by_caller={'MCPRun.Data': 1})                 # unconfirmed
    e = ok(m.apply_runtime_gameplay_effect, asc, C('GE_MCP_RunBuff'), level=2, dynamic_asset_tags=['MCPRun.Dynamic'],
           effect_causer_path=other_owner, source_object_path=other_owner, set_by_caller={'MCPRun.Data': 25}, **Y)
    print('applied:', json.dumps(e)[:600])
    eh = e.get('active_handle') or e.get('effect_handle') or e.get('handle')
    hp = attr(asc, 'Health')
    print('health after buff:', hp)
    assert hp['base'] == 100 and hp['current'] == 125, hp                                          # SetByCaller 25
    ok(m.update_runtime_effect_magnitudes, asc, eh, {'MCPRun.Data': 40}, **Y)
    assert attr(asc, 'Health')['current'] == 140, attr(asc, 'Health')                               # re-aggregated
    ok(m.set_runtime_gameplay_effect_level, asc, eh, 4, **Y)
    effect = lambda: next(x for x in comp(asc)['effects'] if str(x['handle']) == str(eh))
    assert effect()['level'] == 4 and 'MCPRun.Dynamic' in effect()['asset_tags']['values'], effect()
    assert effect()['effect_causer'].endswith(other_owner.split('.')[-1]), effect()
    ok(m.inhibit_runtime_gameplay_effect, asc, eh, True, **Y)
    assert effect()['inhibited'] and attr(asc, 'Health')['current'] == 100, (effect(), attr(asc, 'Health'))
    ok(m.inhibit_runtime_gameplay_effect, asc, eh, False, **Y)
    assert not effect()['inhibited'] and attr(asc, 'Health')['current'] == 140
    q = ok(m.query_runtime_gameplay_effects, asc, ['MCPRun.Buff'], 'owning_any')                  # granted to the owner
    print('query:', json.dumps(q)[:900])
    assert eh in handles(q), q
    assert eh in handles(ok(m.query_runtime_gameplay_effects, asc, ['MCPRun.Dynamic'], 'effect_any'))   # dynamic asset tag
    assert eh not in handles(ok(m.query_runtime_gameplay_effects, asc, ['MCPRun.Other'], 'owning_any'))
    assert eh not in handles(ok(m.query_runtime_gameplay_effects, asc, ['MCPRun.Buff'], 'owning_no'))
    cq = [{'PropertyName': 'owning', 'QueryNodes': [{'Mode': 'AllTags', 'Tags': ['MCPRun.Buff'], 'Children': []}], 'RootIndex': 0},
          {'PropertyName': 'effect', 'QueryNodes': [{'Mode': 'AnyTags', 'Tags': ['MCPRun.Dynamic'], 'Children': []}], 'RootIndex': 0}]
    assert eh in handles(ok(m.query_runtime_gameplay_effects, asc, [], compound_queries=cq))
    bad(m.query_runtime_gameplay_effects, asc, [], compound_queries=[cq[0], cq[0]])                   # repeated family
    assert eh in handles(ok(m.query_runtime_gameplay_effects, asc, [], effect_class_path=C('GE_MCP_RunBuff')))
    assert eh in handles(ok(m.query_runtime_gameplay_effects, asc, [], attribute_path=ATTR + 'Health'))
    assert eh not in handles(ok(m.query_runtime_gameplay_effects, asc, ['MCPRun.Buff'], 'owning_any', ignored_handles=[eh]))
    assert eh in handles(ok(m.query_runtime_gameplay_effects, asc, [], source_object_path=other_owner))
    counts = ok(m.inspect_runtime_ability_tag_counts, asc, ['MCPRun.Buff', 'MCPRun.Loose'])
    print('tag counts:', json.dumps(counts)[:500])
    ok(m.add_runtime_loose_gameplay_tag, asc, 'MCPRun.Loose', 2, **Y)
    counts = ok(m.inspect_runtime_ability_tag_counts, asc, ['MCPRun.Loose'])
    assert '2' in json.dumps(counts), counts
    # Component tag providers: the ASC owns MCPRun.Buff and MCPRun.Loose.
    prov = ok(m.inspect_runtime_gameplay_tag_providers, 'BP_MCP_GasActor')['providers']
    mine = next(p for p in prov if p['provider_path'] == asc)
    assert {'MCPRun.Buff', 'MCPRun.Loose'} <= set(mine['tags']), mine
    qn = [{'Mode': 'AllTags', 'Tags': ['MCPRun.Buff', 'MCPRun.Loose'], 'Children': []}]
    assert ok(m.evaluate_provider_gameplay_tag_query, asc, qn)['matches']
    assert not ok(m.evaluate_provider_gameplay_tag_query, other, qn)['matches']
    # One-shot cue.
    bad(m.execute_runtime_gameplay_cue, asc, 'MCPRun.Buff')
    bad(m.execute_runtime_gameplay_cue, asc, 'GameplayCue.MCPRun.Burst', normalized_magnitude=2)
    ok(m.execute_runtime_gameplay_cue, asc, 'GameplayCue.MCPRun.Burst', 5, 0.5, location={'X': 1, 'Y': 2, 'Z': 3}, normal={'X': 0, 'Y': 0, 'Z': 1})
    # Periodic execution records ModifiedAttributes on the active spec (an infinite non-periodic effect records none).
    tick = ok(m.apply_runtime_gameplay_effect, asc, C('GE_MCP_RunTick'), **Y)['active_handle']
    time.sleep(1.5)
    rows = ok(m.query_runtime_gameplay_effects, asc, [], effect_class_path=C('GE_MCP_RunTick'))['effects']
    print('periodic:', json.dumps(rows)[:700])
    mods = rows[0]['modified_attributes']
    assert rows[0]['modified_attribute_count'] >= 1 and any(r.get('total_magnitude', r.get('magnitude', 0)) > 0 for r in mods), rows[0]
    ok(m.remove_runtime_gameplay_effect, asc, tick, -1, **Y)
    # Socket transform on the placed skeletal mesh (world, component and parent-bone spaces).
    world = owner.split(':')[0]
    sk = world + ':' + SPAWNED['mesh'].split(':', 1)[1] + '.SkeletalMeshComponent0'
    w = ok(m.inspect_runtime_skeletal_socket, sk, 'HandGrip_R', 'world')
    print('socket:', json.dumps(w)[:600])
    pb = ok(m.inspect_runtime_skeletal_socket, sk, 'HandGrip_R', 'parent_bone')
    assert w != pb and ok(m.inspect_runtime_skeletal_socket, sk, 'HandGrip_R', 'component'), (w, pb)
    bad(m.inspect_runtime_skeletal_socket, sk, 'NoSuchSocket', 'world')
    bad(m.inspect_runtime_skeletal_socket, sk, 'HandGrip_R', 'galaxy')
    bad(m.inspect_runtime_skeletal_socket, sk, 'weapon_r_muzzle', 'world')                       # parent bone not on this mesh
    # Remove effect stacks and the ability.
    ok(m.remove_runtime_gameplay_effect, asc, eh, -1, **Y)
    assert eh not in handles(comp(asc)['effects'])
    ok(m.remove_runtime_gameplay_ability, asc, h, 'clear', **Y)
    assert all(a['handle'] != h for a in comp(asc)['abilities'])


def run():
    cleanup()
    setup()
    pie(True)
    try:
        runtime()
    finally:
        pie(False)
    print('GAS and Gameplay Tag runtime routes verified in PIE')
    cleanup()
    INI.unlink(missing_ok=True)


def cleanup():
    if ok(m.get_ue_editor_status)['is_playing']:
        pie(False)
    load('/Game/ThirdPerson/Lvl_ThirdPerson')
    for p in (MAP, ACTOR, f'{ROOT}/GA_MCP_Run', f'{ROOT}/GE_MCP_RunCost', f'{ROOT}/GE_MCP_RunCd', f'{ROOT}/GE_MCP_RunBuff', f'{ROOT}/GE_MCP_RunTick'):
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)


if __name__ == '__main__':
    {'run': run, 'cleanup': cleanup}[COMMAND]()
