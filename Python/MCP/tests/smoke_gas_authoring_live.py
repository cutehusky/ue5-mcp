"""Editor-side Gameplay Ability System authoring: discovery, Blueprint creation, typed defaults; prepare, restart, verify.

prepare: register test tags in a temporary ini source; create ability/effect/execution/magnitude/cue Blueprints (plus a
Blueprint child); author ability policies, tags, triggers and cost/cooldown refs; author effect timing, stacking, every
modifier magnitude type with requirements/filters/queries, executions with conditionals, cues and modern effect components;
author calculation captures and cue tags; reset an inherited field; inspect, evaluate and validate; save and snapshot.
verify (fresh editor): the Blueprints are unloaded registry candidates first, then load, and every definition matches.
cleanup deletes the Blueprints and the tag ini. CurveTable-backed rows use the CT_MCP_Gas fixture (create_fixtures.py).
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
ROOT = '/Game/UE5MCP_Test/GAS'
SRC = 'MCPGas_Tags.ini'
INI = PROJECT / 'Config' / 'Tags' / SRC
CURVES = '/Game/UE5MCP_Fixtures/CT_MCP_Gas.CT_MCP_Gas'   # rows (levels 1/2/5): Duration 4/8/20, Period 1/.5/.25, Scale 2/3/6, LevelRow 1/2/5
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'gas_authoring.json'
ATTR = '/Script/GameplayAbilities.AbilitySystemTestAttributeSet:'
TAGS = ['MCPGas.Asset', 'MCPGas.Event', 'MCPGas.Owned', 'MCPGas.Data', 'MCPGas.Req', 'MCPGas.Ign', 'MCPGas.Pass',
        'MCPGas.Granted', 'MCPGas.Block', 'GameplayCue.MCPGas.Hit', 'GameplayCue.MCPGas.Static']
BP = {'GA_MCP': 'ability', 'GA_MCP_Child': 'ability', 'GE_MCP': 'effect', 'GE_MCP_Cost': 'effect', 'GE_MCP_Extra': 'effect',
      'EX_MCP': 'execution', 'GE_MCP_Curve': 'effect', 'MM_MCP': 'magnitude', 'GCA_MCP': 'cue_actor', 'GCS_MCP': 'cue_static'}


def C(name):
    return f'{ROOT}/{name}.{name}_C'


def A(name):
    return f'{ROOT}/{name}'


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:600])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:400])
    return r['errorMessage']


def apply(name, properties=None, **kw):
    before = definition(name)
    ok(m.edit_gameplay_blueprint_defaults, A(name), properties or {}, confirm=True, dry_run=True, **kw)
    assert definition(name) == before, (name, 'dry run changed defaults', list(kw))
    r = ok(m.edit_gameplay_blueprint_defaults, A(name), properties or {}, confirm=True, save=True, **kw)
    assert definition(name) != before, (name, 'edit changed nothing', list(kw), r)
    return r


def definition(name):
    kind = BP[name]
    if kind == 'ability':
        return ok(m.inspect_gameplay_ability_definition, C(name))
    if kind == 'effect':
        return ok(m.inspect_gameplay_effect_definition, C(name))
    if kind in ('execution', 'magnitude'):
        return ok(m.inspect_gameplay_calculation_definition, C(name))
    return ok(m.inspect_gameplay_definition_defaults, C(name))


def tags_stage():
    ok(m.create_gameplay_tag_source, SRC, confirm=True)
    for t in TAGS:
        ok(m.create_gameplay_tag, t, SRC, 'MCP GAS test', confirm=True)


def discovery_stage():
    abilities = ok(m.list_ability_system_classes, 'ability')
    assert any(c['class_path'].endswith('GameplayAbility_Montage') for c in abilities['classes']), abilities
    sets = ok(m.list_ability_system_classes, 'attribute_set')
    assert any('AbilitySystemTestAttributeSet' in c['class_path'] for c in sets['classes'])
    comps = {c['class_path'].split('.')[-1] for c in ok(m.list_ability_system_classes, 'effect_component', limit=100)['classes']}
    assert {'AssetTagsGameplayEffectComponent', 'TargetTagRequirementsGameplayEffectComponent', 'AbilitiesGameplayEffectComponent',
            'AdditionalEffectsGameplayEffectComponent'} <= comps, comps
    assert ok(m.list_ability_system_classes, 'cue_static')['total'] >= 1
    bad(m.list_ability_system_classes, 'weapon')
    attrs = {a['name']: a for a in ok(m.inspect_gameplay_attribute_definition, '/Script/GameplayAbilities.AbilitySystemTestAttributeSet')['attributes']}
    assert attrs['Health']['base_default'] == 100 and attrs['Mana']['type'] == 'FGameplayAttributeData', attrs
    ch = ok(m.inspect_gameplay_evaluation_channels)
    assert ch['channels'][0]['valid'] and not ch['channels_enabled'], ch
    ok(m.load_ability_system_class, '/Script/GameplayAbilities.GameplayAbility_Montage', 'ability')
    bad(m.load_ability_system_class, '/Script/GameplayAbilities.GameplayAbility_Montage', 'effect')        # family
    bad(m.load_ability_system_class, '/Script/GameplayAbilities.GameplayAbility', 'attribute_set')
    bad(m.load_ability_system_class, '/Game/Nope/GA_Nope.GA_Nope_C', 'ability')


def create_stage():
    bad(m.create_gameplay_blueprint, '/Engine/GA_Bad', 'ability')
    bad(m.create_gameplay_blueprint, A('GA_Bad'), 'weapon')
    bad(m.create_gameplay_blueprint, A('GA_Bad'), 'ability', '/Script/GameplayAbilities.GameplayEffect')    # family mismatch
    r = ok(m.create_gameplay_blueprint, A('GA_MCP'), 'ability', dry_run=True)
    assert r['dry_run']
    bad(m.load_ability_system_class, C('GA_MCP'), 'ability')                                                # nothing created
    for name, kind in BP.items():
        if name == 'GA_MCP_Child':
            continue
        r = ok(m.create_gameplay_blueprint, A(name), kind, save=True)
        assert r['saved'] and r['generated_class'] == C(name), r
    bad(m.create_gameplay_blueprint, A('GA_MCP'), 'ability')                                                  # exists
    r = ok(m.create_gameplay_blueprint, A('GA_MCP_Child'), 'ability', C('GA_MCP'), save=True)
    assert r['parent_class'] == C('GA_MCP'), r
    for name, kind in BP.items():
        ok(m.load_ability_system_class, C(name), kind)
    ex = ok(m.list_ability_system_classes, 'execution')
    assert any(c['class_path'] == C('EX_MCP') for c in ex['classes']), ex


def ability_stage():
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {'bRetriggerInstancedAbility': 'True'}, confirm=False)
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {'NoSuchField': '1'}, confirm=True)
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {'InstancingPolicy': 'Bogus'}, confirm=True)
    apply('GA_MCP', {'bRetriggerInstancedAbility': 'True', 'InstancingPolicy': 'InstancedPerActor'})
    d = definition('GA_MCP')
    assert d['instancing_policy'] == 1, d['instancing_policy']
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {}, confirm=True, tag_properties={'AbilityTags': '["MCPGas.Unregistered"]'})
    apply('GA_MCP', tag_properties={'AbilityTags': '["MCPGas.Asset"]', 'ActivationOwnedTags': '["MCPGas.Owned"]',
                                    'ActivationBlockedTags': '["MCPGas.Block"]'})
    d = definition('GA_MCP')
    assert d['asset_tags']['values'] == ['MCPGas.Asset'], d['asset_tags']
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {}, confirm=True,
        triggers=[{'Tag': 'MCPGas.Event', 'Source': 'GameplayEvent'}, {'Tag': 'MCPGas.Event', 'Source': 'GameplayEvent'}])
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {}, confirm=True, triggers=[{'Tag': 'MCPGas.Event', 'Source': 'Telepathy'}])
    apply('GA_MCP', triggers=[{'Tag': 'MCPGas.Event', 'Source': 'GameplayEvent'}, {'Tag': 'MCPGas.Owned', 'Source': 'OwnedTagAdded'}])
    rows = definition('GA_MCP')['trigger_rows']
    assert [(t['tag'], t['source']) for t in rows] == [('MCPGas.Event', 0), ('MCPGas.Owned', 1)], rows   # native EGameplayAbilityTriggerSource values
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {}, confirm=True, class_references={'CostGameplayEffectClass': C('GA_MCP_Child')})
    # Native IsDataValid preflight: a cooldown effect must grant tags.
    assert 'grants no tags' in bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP'), {}, confirm=True,
                                   class_references={'CooldownGameplayEffectClass': C('GE_MCP_Extra')})
    apply('GA_MCP', class_references={'CostGameplayEffectClass': C('GE_MCP_Cost')})
    assert definition('GA_MCP')['cost_effect_class'] == C('GE_MCP_Cost')
    # The child existed before the parent edits: inheriting fields follow the parent; then override and reset.
    child = ok(m.inspect_gameplay_definition_defaults, C('GA_MCP_Child'))
    retrig = next(f for f in child['fields'] if f['name'] == 'bRetriggerInstancedAbility')
    assert retrig['value'] == 'True' and not retrig['differs_from_parent'], retrig
    apply('GA_MCP_Child', {'bRetriggerInstancedAbility': 'False'})
    retrig = next(f for f in ok(m.inspect_gameplay_definition_defaults, C('GA_MCP_Child'))['fields'] if f['name'] == 'bRetriggerInstancedAbility')
    assert retrig['differs_from_parent'], retrig
    bad(m.edit_gameplay_blueprint_defaults, A('GA_MCP_Child'), {'bRetriggerInstancedAbility': 'True'}, confirm=True,
        reset_properties=['bRetriggerInstancedAbility'])                                                     # overlap
    apply('GA_MCP_Child', reset_properties=['bRetriggerInstancedAbility'])
    retrig = next(f for f in ok(m.inspect_gameplay_definition_defaults, C('GA_MCP_Child'))['fields'] if f['name'] == 'bRetriggerInstancedAbility')
    assert retrig['value'] == 'True' and not retrig['differs_from_parent'], retrig


Q = [{'Mode': 'AnyTags', 'Tags': ['MCPGas.Req'], 'Children': []}]


def effect_stage():
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, timing={'DurationPolicy': 'HasDuration', 'Duration': -1})
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, timing={'DurationPolicy': 'Instant', 'Period': 2})
    apply('GE_MCP', timing={'DurationPolicy': 'HasDuration', 'Duration': 5, 'Period': 1})
    ev = ok(m.evaluate_gameplay_effect_definition, C('GE_MCP'), 1)
    assert ev['duration_static'] and ev['duration_magnitude'] == 5 and ev['period'] == 1, ev
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, stacking={'StackingType': 'Bogus'})
    apply('GE_MCP', stacking={'StackingType': 'AggregateBySource', 'StackLimitCount': '3', 'StackDurationRefreshPolicy': 'NeverRefresh'})
    d = definition('GE_MCP')
    assert d['stacking_type'] == 'AggregateBySource' and d['stack_limit'] == 3, (d['stacking_type'], d['stack_limit'])
    mods = [
        {'AttributePath': ATTR + 'Health', 'Operation': 'AddBase', 'MagnitudeType': 'Constant', 'Magnitude': -10,
         'SourceRequiredTags': ['MCPGas.Req'], 'TargetIgnoredTags': ['MCPGas.Ign'], 'EvaluationChannel': 0},
        {'AttributePath': ATTR + 'Mana', 'Operation': 'MultiplyAdditive', 'MagnitudeType': 'SetByCaller', 'DataTag': 'MCPGas.Data',
         'SourceQueryNodes': Q},
        {'AttributePath': ATTR + 'MaxHealth', 'Operation': 'AddBase', 'MagnitudeType': 'AttributeBased', 'CaptureAttributePath': ATTR + 'Health',
         'CaptureSource': 'Target', 'bSnapshot': True, 'Coefficient': 0.5, 'PreAdd': 1, 'PostAdd': 2,
         'SourceTagFilter': ['MCPGas.Req'], 'TargetTagFilter': ['MCPGas.Pass']},
        {'AttributePath': ATTR + 'MaxMana', 'Operation': 'AddBase', 'MagnitudeType': 'CustomCalculation', 'CalculationClass': C('MM_MCP'),
         'Coefficient': 2},
    ]
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True,
        modifiers=[dict(mods[0], Operation='Division', Magnitude=0)])                                       # zero divisor
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, modifiers=[dict(mods[0], AttributePath=ATTR + 'Nope')])
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True,
        modifiers=[dict(mods[0], SourceRequiredTags=['MCPGas.Req'], SourceIgnoredTags=['MCPGas.Req'])])     # contradiction
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, modifiers=[dict(mods[0], EvaluationChannel=3)])
    apply('GE_MCP', modifiers=mods)
    rows = definition('GE_MCP')['modifiers']
    assert len(rows) == 4, rows
    ev = ok(m.evaluate_gameplay_effect_definition, C('GE_MCP'), 1)
    assert ev['modifiers'][0]['static'] and ev['modifiers'][0]['magnitude'] == -10, ev['modifiers']
    assert not ev['modifiers'][1]['static'] and ev['modifiers'][1]['magnitude'] is None, ev['modifiers']
    # Executions with passed-in tags and conditional effects; self reference rejected.
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True,
        executions=[{'CalculationClass': C('EX_MCP'), 'Tags': [], 'ConditionalEffects': [{'EffectClass': C('GE_MCP'), 'RequiredSourceTags': []}]}])
    apply('GE_MCP', executions=[{'CalculationClass': C('EX_MCP'), 'Tags': ['MCPGas.Pass'],
                                 'ConditionalEffects': [{'EffectClass': C('GE_MCP_Extra'), 'RequiredSourceTags': ['MCPGas.Req']}]}])
    ex = definition('GE_MCP')['executions']
    assert len(ex) == 1 and C('EX_MCP') in json.dumps(ex) and 'MCPGas.Pass' in json.dumps(ex), ex
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, cues=[{'Tags': ['MCPGas.Asset'], 'MinLevel': 0, 'MaxLevel': 1}])
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, cues=[{'Tags': ['GameplayCue.MCPGas.Hit'], 'MinLevel': 2, 'MaxLevel': 1}])
    apply('GE_MCP', cues=[{'Tags': ['GameplayCue.MCPGas.Hit'], 'MinLevel': 0, 'MaxLevel': 5, 'AttributePath': ATTR + 'Health'}])
    cues = definition('GE_MCP')['cues']
    assert cues and cues[0]['tags']['values'] == ['GameplayCue.MCPGas.Hit'] and cues[0]['max_level'] == 5, cues
    # Modern components: asset tags, target requirements (lists + compound query), inherited target tags,
    # granted abilities and additional effects.
    comps = [
        {'ClassPath': '/Script/GameplayAbilities.AssetTagsGameplayEffectComponent',
         'InheritedTags': [{'PropertyName': 'InheritableAssetTags', 'Added': ['MCPGas.Asset'], 'Removed': []}]},
        {'ClassPath': '/Script/GameplayAbilities.TargetTagRequirementsGameplayEffectComponent',
         'Requirements': [{'PropertyName': 'ApplicationTagRequirements', 'Required': ['MCPGas.Req'], 'Ignored': ['MCPGas.Ign'], 'QueryNodes': Q}]},
        {'ClassPath': '/Script/GameplayAbilities.TargetTagsGameplayEffectComponent',
         'InheritedTags': [{'PropertyName': 'InheritableGrantedTagsContainer', 'Added': ['MCPGas.Granted'], 'Removed': []}]},
        {'ClassPath': '/Script/GameplayAbilities.AbilitiesGameplayEffectComponent', 'bSetGrantedAbilities': True,
         'GrantedAbilities': [{'AbilityClass': C('GA_MCP'), 'Level': 2, 'InputID': 3, 'RemovalPolicy': 'RemoveAbilityOnEnd'}]},
        {'ClassPath': '/Script/GameplayAbilities.AdditionalEffectsGameplayEffectComponent', 'bSetAdditionalEffects': True,
         'OnApplication': [{'EffectClass': C('GE_MCP_Extra'), 'RequiredSourceTags': ['MCPGas.Req']}], 'OnCompleteAlways': [C('GE_MCP_Cost')]},
    ]
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True, effect_components=[comps[0], comps[0]])     # duplicate class
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True,
        effect_components=[dict(comps[4], OnApplication=[{'EffectClass': C('GE_MCP'), 'RequiredSourceTags': []}])])  # self reference
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP'), {}, confirm=True,
        effect_components=[dict(comps[1], Requirements=[{'PropertyName': 'ApplicationTagRequirements', 'Required': ['MCPGas.Req'], 'Ignored': ['MCPGas.Req']}])])
    apply('GE_MCP', effect_components=comps)
    got = definition('GE_MCP')['components']
    assert len(got) == 5 and 'MCPGas.Granted' in json.dumps(got) and C('GA_MCP') in json.dumps(got), got
    # Cross-asset conditional cycle: Extra -> GE_MCP while GE_MCP -> Extra.
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP_Extra'), {}, confirm=True,
        executions=[{'CalculationClass': C('EX_MCP'), 'Tags': [], 'ConditionalEffects': [{'EffectClass': C('GE_MCP'), 'RequiredSourceTags': []}]}])
    v = ok(m.validate_gameplay_definition, C('GE_MCP'))
    assert v['valid'] or v.get('native_result') in ('Valid', 'NotValidated'), v
    apply('GE_MCP_Extra', timing={'DurationPolicy': 'HasDuration', 'Duration': 2}, effect_components=[
        {'ClassPath': '/Script/GameplayAbilities.TargetTagsGameplayEffectComponent',
         'InheritedTags': [{'PropertyName': 'InheritableGrantedTagsContainer', 'Added': ['MCPGas.Block'], 'Removed': []}]}])
    apply('GA_MCP', class_references={'CooldownGameplayEffectClass': C('GE_MCP_Extra')})
    assert definition('GA_MCP')['cooldown_effect_class'] == C('GE_MCP_Extra')
    assert definition('GA_MCP_Child')['cooldown_effect_class'] == C('GE_MCP_Extra')                         # propagated
    apply('GE_MCP_Cost', timing={'DurationPolicy': 'Instant'}, modifiers=[{'AttributePath': ATTR + 'Mana', 'Operation': 'AddBase', 'MagnitudeType': 'Constant', 'Magnitude': -5}])


def curve_stage():
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP_Curve'), {}, confirm=True,
        timing={'DurationPolicy': 'HasDuration', 'DurationCurveTable': CURVES, 'DurationCurveRow': 'Missing'})
    apply('GE_MCP_Curve', timing={'DurationPolicy': 'HasDuration', 'Duration': 1, 'DurationCurveTable': CURVES, 'DurationCurveRow': 'Duration',
                                  'Period': 1, 'PeriodCurveTable': CURVES, 'PeriodCurveRow': 'Period'})
    for level, dur, per in ((1, 4, 1), (2, 8, 0.5), (5, 20, 0.25), (3.5, 14, 0.375)):
        ev = ok(m.evaluate_gameplay_effect_definition, C('GE_MCP_Curve'), level)
        assert abs(ev['duration_magnitude'] - dur) < 1e-4 and abs(ev['period'] - per) < 1e-4, (level, ev)
    lookup = {'CurveTablePath': CURVES, 'CurveRow': 'Scale'}
    mods = [
        dict({'AttributePath': ATTR + 'Health', 'Operation': 'AddBase', 'MagnitudeType': 'CurveTable', 'Magnitude': 10}, **lookup),
        {'AttributePath': ATTR + 'Mana', 'Operation': 'AddBase', 'MagnitudeType': 'AttributeBased', 'CaptureAttributePath': ATTR + 'Health',
         'CaptureSource': 'Source', 'CoefficientCurveTable': CURVES, 'CoefficientCurveRow': 'Scale', 'Coefficient': 1,
         'PreAddCurveTable': CURVES, 'PreAddCurveRow': 'LevelRow', 'PreAdd': 1, 'CurveTablePath': CURVES, 'CurveRow': 'Scale'},
        {'AttributePath': ATTR + 'MaxMana', 'Operation': 'AddBase', 'MagnitudeType': 'CustomCalculation', 'CalculationClass': C('MM_MCP'),
         'PostAddCurveTable': CURVES, 'PostAddCurveRow': 'Scale', 'PostAdd': 1, 'CurveTablePath': CURVES, 'CurveRow': 'LevelRow'},
    ]
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP_Curve'), {}, confirm=True, modifiers=[dict(mods[0], CurveRow='Missing')])
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP_Curve'), {}, confirm=True, modifiers=[dict(mods[0], CurveTablePath='/Game/Nope/CT.CT')])
    apply('GE_MCP_Curve', modifiers=mods)
    for level, want in ((1, 20), (2, 30), (5, 60)):
        ev = ok(m.evaluate_gameplay_effect_definition, C('GE_MCP_Curve'), level)
        assert ev['modifiers'][0]['static'] and abs(ev['modifiers'][0]['magnitude'] - want) < 1e-4, (level, ev['modifiers'])
    text = json.dumps(definition('GE_MCP_Curve'))
    assert text.count('CT_MCP_Gas') >= 5, text[:2000]
    # Granted ability level from a curve row (level-one value must be finite in [1, 1e6]).
    grant = {'ClassPath': '/Script/GameplayAbilities.AbilitiesGameplayEffectComponent', 'bSetGrantedAbilities': True,
             'GrantedAbilities': [{'AbilityClass': C('GA_MCP'), 'Level': 1, 'LevelCurveTable': CURVES, 'LevelCurveRow': 'LevelRow'}]}
    bad(m.edit_gameplay_blueprint_defaults, A('GE_MCP_Curve'), {}, confirm=True,
        effect_components=[dict(grant, GrantedAbilities=[dict(grant['GrantedAbilities'][0], LevelCurveRow='Missing')])])
    apply('GE_MCP_Curve', effect_components=[grant])
    assert 'LevelRow' in json.dumps(definition('GE_MCP_Curve')['components'])


def calc_cue_stage():
    caps = [{'AttributePath': ATTR + 'Health', 'Source': 'Target', 'bSnapshot': False},
            {'AttributePath': ATTR + 'Mana', 'Source': 'Source', 'bSnapshot': True}]
    bad(m.edit_gameplay_blueprint_defaults, A('EX_MCP'), {}, confirm=True, captures=[caps[0], caps[0]])
    apply('EX_MCP', captures=caps)
    rows = definition('EX_MCP')['captures']
    assert [(r['attribute'].split(':')[-1], r['source'], r['snapshot']) for r in rows] == [('Health', 'Target', False), ('Mana', 'Source', True)], rows
    apply('MM_MCP', captures=caps[:1])
    bad(m.edit_gameplay_blueprint_defaults, A('GCS_MCP'), {}, confirm=True, tag_properties={'GameplayCueTag': '["MCPGas.Asset"]'})
    apply('GCS_MCP', tag_properties={'GameplayCueTag': '["GameplayCue.MCPGas.Static"]'})
    apply('GCA_MCP', {'bAutoDestroyOnRemove': 'True'}, tag_properties={'GameplayCueTag': '["GameplayCue.MCPGas.Hit"]'})
    cues = ok(m.list_ability_system_classes, 'cue_static', 'GCS_MCP')['classes']
    assert cues and cues[0].get('cue_tag') == 'GameplayCue.MCPGas.Static', cues


def snapshot():
    return {n: definition(n) for n in BP}


def prepare():
    cleanup(keep_tags=True)   # deleting the ini while its tags stay registered would turn re-creation into a no-op
    tags_stage()
    discovery_stage()
    create_stage()
    ability_stage()
    effect_stage()
    curve_stage()
    calc_cue_stage()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1), encoding='utf-8')
    print('GAS Blueprints and typed defaults prepared and saved')


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    cands = ok(m.list_ability_system_classes, 'ability', 'GA_MCP')
    assert any('GA_MCP' in json.dumps(c) for c in cands.get('blueprint_candidates', [])), cands      # unloaded registry discovery
    for name, kind in BP.items():
        ok(m.load_ability_system_class, C(name), kind)
    got = json.loads(json.dumps(snapshot()))
    for name in BP:
        assert got[name] == st['snapshot'][name], json.dumps({'name': name, 'got': got[name], 'want': st['snapshot'][name]})[:3000]
    print('GAS Blueprint defaults identical after cold reload')
    cleanup()


def cleanup(keep_tags=False):
    for name in sorted(BP, key=lambda n: n != 'GA_MCP_Child'):    # child before parent
        httpx.post(BASE + '/assets/delete', json={'AssetPath': A(name)}, timeout=300)
    if not keep_tags:
        INI.unlink(missing_ok=True)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
