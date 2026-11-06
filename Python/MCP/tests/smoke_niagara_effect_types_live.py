"""Live Niagara effect-type, scalability, validation-rule and rule-set authoring on scratch assets.

prepare: create/duplicate effect types and rule sets, author culling settings, significance handler, scalability
rows/conditions and validation rules with guard/dry-run/undo checks, run system rule validation; save and snapshot.
verify (fresh editor): compare the cold-loaded effect types, rows, rules and rule sets, then delete them.
"""
import argparse
import json
from pathlib import Path

import httpx

from smoke_animation_curves_live import Api

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'niagara_effect_types.json'
ET = '/Game/UE5MCP_Test/ET_MCP_Rules.ET_MCP_Rules'
ET_COPY = '/Game/UE5MCP_Test/ET_MCP_RulesCopy.ET_MCP_RulesCopy'
RS = '/Game/UE5MCP_Test/VRS_MCP_Rules.VRS_MCP_Rules'
RS_COPY = '/Game/UE5MCP_Test/VRS_MCP_RulesCopy.VRS_MCP_RulesCopy'
SYS = '/Game/UE5MCP_Test/NS_MCP_Rules.NS_MCP_Rules'
SYS_SOURCE = '/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion.SimpleExplosion'
ASSETS = (SYS, ET, ET_COPY, RS, RS_COPY)
RULE = '/Script/NiagaraEditor.NiagaraValidationRule_'
C = {'AssetPath': ET, 'bConfirm': True}


def inspect(api, path=ET):
    return api.call('POST', '/niagara/effect-types/inspect', {'AssetPath': path})


def fields(d):
    return {f['name']: f.get('value') for f in d['editable_fields']}


def rows(api, kind, path=ET):
    return api.call('POST', '/niagara/effect-types/scalability/inspect', {'AssetPath': path, 'ValueKind': kind})['rows']


def row(api, kind, i=0):
    r = rows(api, kind)[i]
    return {**C, 'ValueKind': kind, 'ScalabilityIndex': i, 'RecordHash': r['record_hash']}, {f['field_path']: f.get('value') for f in r['fields']}


def rules(api, path=ET):
    if path.split('/')[-1].startswith('VRS_'):
        return api.call('POST', '/niagara/rule-sets/inspect', {'AssetPath': path})['rules']
    return inspect(api, path)['ValidationRules']['items']


def rule(api, cls, path=ET):
    r = next(x for x in rules(api, path) if x['class_path'] == RULE + cls)
    return {'AssetPath': path, 'bConfirm': True, 'RuleIndex': r['index'], 'RulePath': r['object_path']}


def rule_fields(api, R, base='/niagara/effect-types'):
    return {f['name']: f.get('value') for f in api.call('POST', base + '/rules/inspect', R)['fields']}


def creation_stage(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    api.call('POST', '/niagara/effect-types', {'AssetPath': ET}, ok=False)
    api.call('POST', '/niagara/effect-types', {**C, 'bDryRun': True})
    api.call('POST', '/niagara/effect-types/inspect', {'AssetPath': ET}, ok=False)
    api.call('POST', '/niagara/effect-types', C)
    api.call('POST', '/niagara/effect-types', C, ok=False)
    d = inspect(api)
    assert d['system_scalability_setting_count'] == 0 and d['ValidationRules']['count'] == 0, d


def policy_stage(api):
    api.call('PATCH', '/niagara/effect-types/bool', {**C, 'FieldName': 'bNope', 'bEnabled': True}, ok=False)
    api.call('PATCH', '/niagara/effect-types/bool', {**C, 'FieldName': 'bAllowCullingForLocalPlayers', 'bEnabled': True, 'bDryRun': True})
    assert fields(inspect(api))['bAllowCullingForLocalPlayers'] == 'False'
    api.call('PATCH', '/niagara/effect-types/bool', {**C, 'FieldName': 'bAllowCullingForLocalPlayers', 'bEnabled': True})
    api.call('PATCH', '/niagara/effect-types/enum', {**C, 'FieldName': 'CullReaction', 'NewName': 'Explode'}, ok=False)
    api.call('PATCH', '/niagara/effect-types/enum', {**C, 'FieldName': 'CullReaction', 'NewName': 'Deactivate'})
    api.call('PATCH', '/niagara/effect-types/enum', {**C, 'FieldName': 'UpdateFrequency', 'NewName': 'Continuous'})
    f = fields(inspect(api))
    assert f['bAllowCullingForLocalPlayers'] == 'True' and f['CullReaction'] == 'Deactivate' and f['UpdateFrequency'] == 'Continuous', f
    api.undo(); assert fields(inspect(api))['UpdateFrequency'] == 'SpawnOnly'
    api.redo(); assert fields(inspect(api))['UpdateFrequency'] == 'Continuous'
    handlers = [h['class_path'] for h in api.call('POST', '/niagara/significance-handlers', {})['classes']]
    assert '/Script/Niagara.NiagaraSignificanceHandlerDistance' in handlers, handlers
    api.call('PATCH', '/niagara/effect-types/significance-handler', {**C, 'HandlerClass': '/Script/Niagara.NiagaraSystem'}, ok=False)
    api.call('PATCH', '/niagara/effect-types/significance-handler', {**C, 'HandlerClass': '/Script/Niagara.NiagaraSignificanceHandlerDistance'})
    assert 'NiagaraSignificanceHandlerDistance' in fields(inspect(api))['SignificanceHandler']


def scalability_stage(api):
    profiles = api.call('POST', '/niagara/scalability/profiles', {})
    assert profiles['active_profile'] and any(p['name'] == 'Windows' for p in profiles['profiles'])
    R = {**C, 'ValueKind': 'system'}
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**R, 'ValueKind': 'particle', 'NewName': 'add'}, ok=False)
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**R, 'NewName': 'add', 'bDryRun': True})
    assert rows(api, 'system') == []
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**R, 'NewName': 'add'})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/scalar', {**H, 'RecordHash': '0' * 32, 'FieldName': 'MaxDistance', 'ScalarValue': 1}, ok=False)
    api.call('PATCH', '/niagara/effect-types/scalability/scalar', {**H, 'FieldName': 'MaxDistance', 'ScalarValue': 5000})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/scalar', {**H, 'FieldName': 'bCullByDistance', 'ScalarValue': 1})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/scalar', {**H, 'FieldName': 'MaxInstances', 'ScalarValue': 12})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/enum', {**H, 'FieldName': 'CullProxyMode', 'NewName': 'Bogus'}, ok=False)
    api.call('PATCH', '/niagara/effect-types/scalability/enum', {**H, 'FieldName': 'CullProxyMode', 'NewName': 'Instanced_Rendered'})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/quality', {**H, 'ScalarValue': 40, 'bEnabled': False}, ok=False)
    api.call('PATCH', '/niagara/effect-types/scalability/quality', {**H, 'ScalarValue': 2, 'bEnabled': False})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/profile', {**H, 'NewName': 'NoSuchProfile', 'TextValue': 'disabled', 'ScalarValue': 0}, ok=False)
    api.call('PATCH', '/niagara/effect-types/scalability/profile', {**H, 'NewName': 'Windows', 'TextValue': 'disabled', 'ScalarValue': 0})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/conditions', {**H, 'NewName': 'add', 'TextValue': 'not.a.cvar'}, ok=False)
    api.call('PATCH', '/niagara/effect-types/scalability/conditions', {**H, 'NewName': 'add', 'TextValue': 'fx.Niagara.QualityLevel'})
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/condition-settings', {**H, 'OutputIndex': 0, 'ConditionConfig': {'Name': 'fx.Niagara.QualityLevel', 'UseMinInt': True, 'MinInt': 1}})
    H, v = row(api, 'system')
    assert v['MaxDistance'] == '5000.000000' and v['bCullByDistance'] == 'True' and v['MaxInstances'] == '12' and v['CullProxyMode'] == 'Instanced_Rendered', v
    assert 'fx.Niagara.QualityLevel' in json.dumps(rows(api, 'system')[0]), 'condition missing'
    assert 'Windows' in json.dumps(rows(api, 'system')[0]), 'profile override missing'
    with_condition = rows(api, 'system')[0]['record_hash']
    api.undo(); assert rows(api, 'system')[0]['record_hash'] != with_condition
    api.redo(); assert rows(api, 'system')[0]['record_hash'] == with_condition
    # Field and whole-row reset, duplicate, reorder, removal.
    H, _ = row(api, 'system')
    api.call('PATCH', '/niagara/effect-types/scalability/reset-field', {**H, 'FieldName': 'MaxInstances'})
    H, v = row(api, 'system')
    assert v['MaxInstances'] == '0', v['MaxInstances']
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**H, 'NewName': 'duplicate'})
    assert len(rows(api, 'system')) == 2 and rows(api, 'system')[0]['record_hash'] == rows(api, 'system')[1]['record_hash']
    H1, _ = row(api, 'system', 1)
    api.call('PATCH', '/niagara/effect-types/scalability/reset-row', H1)
    _, v1 = row(api, 'system', 1)
    assert v1['MaxDistance'] == '0.000000' and v1['CullProxyMode'] == 'None', v1
    H1, _ = row(api, 'system', 1)
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**H1, 'NewName': 'move', 'TargetIndex': 0})
    assert row(api, 'system', 0)[1]['MaxDistance'] == '0.000000'
    # Active row, profile evaluation and overlap conflicts for two rows.
    act = api.call('POST', '/niagara/effect-types/scalability/active', {**C, 'ValueKind': 'system'})
    assert act['evaluated'] and act['selected_row_index'] in (0, 1), act
    ev = api.call('POST', '/niagara/effect-types/scalability/evaluate', {**C, 'ValueKind': 'system', 'NewName': 'Windows', 'ScalarValue': 3})
    assert ev['evaluated'] and len(ev['rows']) == 2, ev
    api.call('POST', '/niagara/effect-types/scalability/evaluate', {**C, 'ValueKind': 'system', 'NewName': 'NoSuchProfile', 'ScalarValue': 3}, ok=False)
    con = api.call('POST', '/niagara/effect-types/scalability/conflicts', {**C, 'ValueKind': 'system'})
    assert con['evaluated'] and con['conflict_pair_count'] >= 1, con
    H0, _ = row(api, 'system', 0)
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**H0, 'NewName': 'remove'})
    assert len(rows(api, 'system')) == 1 and row(api, 'system')[1]['MaxDistance'] == '5000.000000'
    # Emitter rows: add, edit, copy a system row across kinds is rejected, copy within kind works.
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**C, 'ValueKind': 'emitter', 'NewName': 'add'})
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**C, 'ValueKind': 'emitter', 'NewName': 'add'})
    E0, _ = row(api, 'emitter', 0)
    fields0 = [f['field_path'] for f in rows(api, 'emitter')[0]['fields']]
    scalar = 'SpawnCountScale' if 'SpawnCountScale' in fields0 else next(f['field_path'] for f in rows(api, 'emitter')[0]['fields'] if f['type'] == 'float')
    api.call('PATCH', '/niagara/effect-types/scalability/scalar', {**E0, 'FieldName': scalar, 'ScalarValue': 0.5})
    E1, _ = row(api, 'emitter', 1)
    S0, _ = row(api, 'system', 0)
    api.call('PATCH', '/niagara/effect-types/scalability/copy-row', {**E1, 'SourceAssetPath': ET, 'SourceScalabilityIndex': 0, 'SourceRecordHash': S0['RecordHash']}, ok=False)
    E0, _ = row(api, 'emitter', 0)
    api.call('PATCH', '/niagara/effect-types/scalability/copy-row', {**E1, 'SourceAssetPath': ET, 'SourceScalabilityIndex': 0, 'SourceRecordHash': E0['RecordHash']})
    assert rows(api, 'emitter')[0]['record_hash'] == rows(api, 'emitter')[1]['record_hash']
    assert row(api, 'emitter', 1)[1][scalar] == '0.500000', row(api, 'emitter', 1)[1][scalar]


def rule_stage(api):
    kinds = [c['class_path'] for c in api.call('POST', '/niagara/validation-rule-types', {})['classes']]
    assert RULE + 'SimulationStageBudget' in kinds and RULE + 'BannedRenderers' in kinds, kinds
    api.call('POST', '/niagara/effect-types/rules', {**C, 'RuleClass': '/Script/Niagara.NiagaraSystem'}, ok=False)
    api.call('POST', '/niagara/effect-types/rules', {**C, 'RuleClass': RULE + 'SimulationStageBudget', 'bDryRun': True})
    assert rules(api) == []
    for cls in ('SimulationStageBudget', 'BannedRenderers', 'NoWarmupTime', 'EmitterCount'):
        api.call('POST', '/niagara/effect-types/rules', {**C, 'RuleClass': RULE + cls})
    api.undo(); assert len(rules(api)) == 3
    api.redo(); assert len(rules(api)) == 4
    B = rule(api, 'SimulationStageBudget')
    api.call('PATCH', '/niagara/effect-types/rules/scalar', {**B, 'RulePath': B['RulePath'] + 'X', 'FieldName': 'MaxSimulationStages', 'ScalarValue': 4}, ok=False)
    api.call('PATCH', '/niagara/effect-types/rules/scalar', {**B, 'FieldName': 'MaxSimulationStages', 'ScalarValue': 1.5}, ok=False)
    api.call('PATCH', '/niagara/effect-types/rules/scalar', {**B, 'FieldName': 'MaxSimulationStages', 'ScalarValue': 4})
    api.call('PATCH', '/niagara/effect-types/rules/scalar', {**B, 'FieldName': 'bMaxSimulationStagesEnabled', 'ScalarValue': 1})
    api.call('PATCH', '/niagara/effect-types/rules/enum', {**B, 'FieldName': 'Severity', 'NewName': 'Fatal'}, ok=False)
    api.call('PATCH', '/niagara/effect-types/rules/enum', {**B, 'FieldName': 'Severity', 'NewName': 'Error'})
    f = rule_fields(api, B)
    assert f['MaxSimulationStages'] == '4' and f['bMaxSimulationStagesEnabled'] == 'True' and f['Severity'] == 'Error', f
    api.call('POST', '/niagara/effect-types/rules/reset-field', {**B, 'FieldName': 'Severity'})
    assert rule_fields(api, B)['Severity'] == 'Warning'
    BR = rule(api, 'BannedRenderers')
    api.call('PATCH', '/niagara/effect-types/rules/reference-array', {**BR, 'FieldName': 'BannedRenderers', 'StringValues': ['/Script/Niagara.NiagaraSystem']}, ok=False)
    api.call('PATCH', '/niagara/effect-types/rules/reference-array', {**BR, 'FieldName': 'BannedRenderers', 'StringValues': ['/Script/Niagara.NiagaraLightRendererProperties', '/Script/Niagara.NiagaraRibbonRendererProperties']})
    assert 'NiagaraLightRendererProperties' in rule_fields(api, BR)['BannedRenderers'], rule_fields(api, BR)
    # List edits: duplicate, move, remove.
    api.call('PATCH', '/niagara/effect-types/rules', {**BR, 'ValueKind': 'duplicate'})
    assert [r['class_path'].rsplit('_', 1)[1] for r in rules(api)] == ['SimulationStageBudget', 'BannedRenderers', 'NoWarmupTime', 'EmitterCount', 'BannedRenderers']
    dup = rules(api)[4]
    assert 'NiagaraRibbonRendererProperties' in rule_fields(api, {**C, 'RuleIndex': 4, 'RulePath': dup['object_path']})['BannedRenderers']
    api.call('PATCH', '/niagara/effect-types/rules', {**C, 'RuleIndex': 4, 'RulePath': dup['object_path'], 'ValueKind': 'move', 'TargetIndex': 0})
    assert rules(api)[0]['object_path'] == dup['object_path']
    EC = rule(api, 'EmitterCount')
    api.call('PATCH', '/niagara/effect-types/rules', {**EC, 'ValueKind': 'remove', 'bDryRun': True})
    assert len(rules(api)) == 5
    api.call('PATCH', '/niagara/effect-types/rules', {**EC, 'ValueKind': 'remove'})
    assert [r['class_path'].rsplit('_', 1)[1] for r in rules(api)] == ['BannedRenderers', 'SimulationStageBudget', 'BannedRenderers', 'NoWarmupTime']


def rule_set_stage(api):
    S = {'AssetPath': RS, 'bConfirm': True}
    api.call('POST', '/niagara/rule-sets', S)
    api.call('POST', '/niagara/rule-sets/rules', {**S, 'RuleClass': RULE + 'HasEffectType'})
    api.call('POST', '/niagara/rule-sets/rules', {**S, 'RuleClass': RULE + 'SimulationStageBudget'})
    SB = rule(api, 'SimulationStageBudget', RS)
    api.call('PATCH', '/niagara/rule-sets/rules/scalar', {**SB, 'FieldName': 'MaxTotalIterations', 'ScalarValue': 9})
    api.call('PATCH', '/niagara/rule-sets/rules/enum', {**SB, 'FieldName': 'Severity', 'NewName': 'Info'})
    f = rule_fields(api, SB, '/niagara/rule-sets')
    assert f['MaxTotalIterations'] == '9' and f['Severity'] == 'Info', f
    api.call('POST', '/niagara/rule-sets/duplicate', {'AssetPath': RS_COPY, 'SourceAssetPath': RS, 'bConfirm': True})
    assert [r['class_path'] for r in rules(api, RS_COPY)] == [r['class_path'] for r in rules(api, RS)]
    api.call('PATCH', '/niagara/effect-types/rule-sets', {**C, 'RuleSetPaths': [ET]}, ok=False)
    api.call('PATCH', '/niagara/effect-types/rule-sets', {**C, 'RuleSetPaths': [RS, RS_COPY]})
    sets = inspect(api)['ValidationRuleSets']
    assert sets['count'] == 2 and RS in json.dumps(sets) and RS_COPY in json.dumps(sets), sets
    api.call('POST', '/niagara/effect-types/duplicate', {'AssetPath': ET_COPY, 'SourceAssetPath': ET, 'bConfirm': True})
    assert [r['class_path'] for r in rules(api, ET_COPY)] == [r['class_path'] for r in rules(api)]
    assert len(rows(api, 'system', ET_COPY)) == 1


def validation_stage(api):
    api.call('POST', '/niagara/systems/duplicate', {'AssetPath': SYS, 'SourceAssetPath': SYS_SOURCE, 'bConfirm': True})
    api.call('POST', '/niagara/systems/validate-rules', {'AssetPath': SYS}, ok=False)
    r = api.call('POST', '/niagara/systems/validate-rules', {'AssetPath': SYS, 'bConfirm': True})
    assert not r['has_native_validation_rules'] and r['result_count'] == 0, r
    api.call('PATCH', '/niagara/systems/effect-type', {'AssetPath': SYS, 'bConfirm': True, 'SourceAssetPath': ET})
    api.call('PATCH', '/niagara/systems/warmup', {'AssetPath': SYS, 'bConfirm': True, 'WarmupTime': 1.0, 'WarmupDelta': 0.1})
    d = api.call('POST', '/niagara/systems/validate-rules', {'AssetPath': SYS, 'bConfirm': True, 'bDryRun': True})
    assert d['has_native_validation_rules'] and d['results'] == [], d
    r = api.call('POST', '/niagara/systems/validate-rules', {'AssetPath': SYS, 'bConfirm': True})
    assert r['has_native_validation_rules'] and r['result_count'] >= 1, r
    assert any('warm' in (x['summary'] + x['description']).lower() for x in r['results']), r['results']


def snapshot(api):
    out = {}
    for p in (ET, ET_COPY):
        d = inspect(api, p)
        d.pop('dirty', None); d.pop('scope', None)
        d['rows'] = {k: rows(api, k, p) for k in ('system', 'emitter')}
        d['rule_fields'] = [rule_fields(api, {'AssetPath': p, 'RuleIndex': r['index'], 'RulePath': r['object_path']}) for r in d['ValidationRules']['items']]
        out[p] = d
    for p in (RS, RS_COPY):
        d = api.call('POST', '/niagara/rule-sets/inspect', {'AssetPath': p})
        d.pop('dirty', None); d.pop('scope', None)
        d['rule_fields'] = [rule_fields(api, {'AssetPath': p, 'RuleIndex': r['index'], 'RulePath': r['object_path']}, '/niagara/rule-sets') for r in d['rules']]
        out[p] = d
    return out


def prepare(api):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text('{}', encoding='utf-8')
    creation_stage(api)
    policy_stage(api)
    scalability_stage(api)
    rule_stage(api)
    rule_set_stage(api)
    validation_stage(api)
    for p in ASSETS:
        api.call('POST', '/assets/save', {'AssetPath': p})
    STATE.write_text(json.dumps({'snapshot': snapshot(api)}), encoding='utf-8')
    print('prepared Niagara effect-type/rule authoring; restart the editor and run verify')


def verify(api):
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state.get('snapshot'), 'prepare did not finish; run cleanup'
    try:
        cold = snapshot(api)
        for k in state['snapshot']:
            assert state['snapshot'][k] == cold[k], (k, json.dumps(state['snapshot'][k])[:700], json.dumps(cold[k])[:700])
        print('Cold reload of Niagara effect types, scalability rows, validation rules and rule sets: OK')
    finally:
        cleanup(api)


def cleanup(api):
    for p in ASSETS:
        httpx.post(api.base + '/assets/delete', json={'AssetPath': p}, timeout=180)
    STATE.unlink(missing_ok=True)
    print('cleaned Niagara effect-type test assets')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    p.add_argument('--base', default='http://127.0.0.1:8080')
    a = p.parse_args()
    api = Api(a.base)
    assert not api.call('GET', '/editor/status')['is_playing']
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[a.phase](api)


if __name__ == '__main__':
    main()
