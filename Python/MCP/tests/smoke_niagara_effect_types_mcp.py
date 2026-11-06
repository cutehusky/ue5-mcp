"""Call every Niagara effect-type, scalability, validation-rule and rule-set MCP tool through the registered
FastMCP dispatcher, on scratch assets built over REST.

Read-only tools run for real and mutating tools as confirmed dry runs; the assets must be unchanged. Tools whose
field kind no stock validation rule exposes (FName/asset/vector/color/text/string-array leaves) are expected to
reach a native guard. The CPU preview runs as a dry run only (a real run needs a compiled system).
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
ET = '/Game/UE5MCP_Test/ET_MCP_Mcp.ET_MCP_Mcp'
RS = '/Game/UE5MCP_Test/VRS_MCP_Mcp.VRS_MCP_Mcp'
NE = '/Game/UE5MCP_Test/NE_MCP_EtMcp.NE_MCP_EtMcp'
SYS = '/Game/UE5MCP_Test/NS_MCP_EtMcp.NS_MCP_EtMcp'
ASSETS = (SYS, ET, RS, NE)
RULE = '/Script/NiagaraEditor.NiagaraValidationRule_'
READ_ONLY = ('inspect_niagara_effect_type', 'inspect_niagara_effect_type_rule', 'inspect_niagara_validation_rule_set',
             'inspect_niagara_effect_type_scalability', 'list_', 'discover_')
EXPECTED_GUARD = {'set_niagara_effect_type_rule_reference', 'set_niagara_effect_type_rule_compound',
                  'set_niagara_validation_rule_text', 'set_niagara_validation_rule_string_array'}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    for p in ASSETS:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)
    C = {'AssetPath': ET, 'bConfirm': True}
    api.call('POST', '/niagara/effect-types', C)
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**C, 'ValueKind': 'system', 'NewName': 'add'})
    api.call('PATCH', '/niagara/effect-types/scalability/rows', {**C, 'ValueKind': 'system', 'NewName': 'add'})
    for cls in ('SimulationStageBudget', 'BannedRenderers'):
        api.call('POST', '/niagara/effect-types/rules', {**C, 'RuleClass': RULE + cls})
    api.call('PATCH', '/niagara/effect-types/scalability/conditions', {**C, 'ValueKind': 'system', 'ScalabilityIndex': 0, 'NewName': 'add', 'TextValue': 'fx.Niagara.QualityLevel',
                                                                       'RecordHash': api.call('POST', '/niagara/effect-types/scalability/inspect', {**C, 'ValueKind': 'system'})['rows'][0]['record_hash']})
    api.call('POST', '/niagara/rule-sets', {'AssetPath': RS, 'bConfirm': True})
    api.call('POST', '/niagara/rule-sets/rules', {'AssetPath': RS, 'bConfirm': True, 'RuleClass': RULE + 'SimulationStageBudget'})
    api.call('POST', '/niagara/emitters', {'AssetPath': NE, 'bConfirm': True})
    api.call('POST', '/niagara/systems', {'AssetPath': SYS, 'bConfirm': True})
    api.call('PATCH', '/niagara/systems/effect-type', {'AssetPath': SYS, 'bConfirm': True, 'SourceAssetPath': ET})
    try:
        rows = api.call('POST', '/niagara/effect-types/scalability/inspect', {**C, 'ValueKind': 'system'})['rows']
        h0, h1 = rows[0]['record_hash'], rows[1]['record_hash']
        rules = api.call('POST', '/niagara/effect-types/inspect', C)['ValidationRules']['items']
        sb, br = rules[0], rules[1]
        rsr = api.call('POST', '/niagara/rule-sets/inspect', {'AssetPath': RS})['rules'][0]
        E = lambda **kw: dict(asset_path=ET, **kw)
        SB = lambda **kw: E(rule_index=0, rule_path=sb['object_path'], **kw)
        BR = lambda **kw: E(rule_index=1, rule_path=br['object_path'], **kw)
        R0 = lambda **kw: E(kind='system', row_index=0, record_hash=h0, **kw)
        args = {
            'inspect_niagara_effect_type': E(),
            'list_niagara_significance_handlers': {},
            'list_niagara_validation_rule_types': {},
            'discover_niagara_scalability_profiles': {},
            'inspect_niagara_effect_type_rule': SB(),
            'inspect_niagara_validation_rule_set': dict(asset_path=RS),
            'inspect_niagara_effect_type_scalability': E(kind='system'),
            'inspect_niagara_effect_type_scalability_conflicts': E(kind='system'),
            'inspect_active_niagara_effect_type_scalability': E(kind='system'),
            'evaluate_niagara_effect_type_scalability': E(kind='system', profile='Windows', quality_level=3),
            'validate_niagara_system_rules': dict(asset_path=SYS),
            'create_niagara_effect_type': dict(asset_path='/Game/UE5MCP_Test/ET_MCP_McpNew.ET_MCP_McpNew'),
            'duplicate_niagara_effect_type': dict(source_asset_path=ET, asset_path='/Game/UE5MCP_Test/ET_MCP_McpDup.ET_MCP_McpDup'),
            'duplicate_niagara_emitter_asset': dict(source_asset_path=NE, asset_path='/Game/UE5MCP_Test/NE_MCP_McpDup.NE_MCP_McpDup'),
            'create_niagara_validation_rule_set': dict(asset_path='/Game/UE5MCP_Test/VRS_MCP_McpDup.VRS_MCP_McpDup', source_asset_path=RS),
            'set_niagara_effect_type_policy': E(field='CullReaction', enum_name='Deactivate'),
            'set_niagara_effect_type_significance': E(handler_class='/Script/Niagara.NiagaraSignificanceHandlerAge'),
            'add_niagara_effect_type_rule': E(rule_class=RULE + 'NoWarmupTime'),
            'edit_niagara_effect_type_rule': BR(action='move', target_index=0),
            'set_niagara_effect_type_rule_scalar': SB(field='MaxSimulationStages', value=3),
            'set_niagara_effect_type_rule_enum': SB(field='Severity', enum_name='Error'),
            'reset_niagara_effect_type_rule_field': SB(field='Severity'),
            'set_niagara_validation_rule_reference_array': BR(field='BannedRenderers', paths=['/Script/Niagara.NiagaraLightRendererProperties']),
            'set_niagara_effect_type_rule_reference': SB(field='Severity', kind='name', value='X'),
            'set_niagara_effect_type_rule_compound': SB(field='Severity', kind='vector', components=[1, 2, 3]),
            'set_niagara_validation_rule_text': SB(field='Severity', text='x'),
            'set_niagara_validation_rule_string_array': SB(field='Severity', values=['x']),
            'set_niagara_effect_type_rule_sets': E(rule_set_paths=[RS]),
            'edit_niagara_rule_set_rule': dict(asset_path=RS, action='scalar', rule_index=0, rule_path=rsr['object_path'], field='MaxTotalIterations', value=5),
            'edit_niagara_effect_type_scalability_rows': R0(action='duplicate'),
            'set_niagara_effect_type_scalability_scalar': R0(field='MaxDistance', value=100),
            'set_niagara_effect_type_scalability_enum': R0(field='CullProxyMode', value='Instanced_Rendered'),
            'reset_niagara_effect_type_scalability_field': R0(field='MaxDistance'),
            'set_niagara_effect_type_scalability_quality': R0(quality_level=1, enabled=False),
            'set_niagara_effect_type_scalability_profile': R0(profile='Windows', quality_level=0, state='disabled'),
            'edit_niagara_effect_type_scalability_conditions': R0(action='remove', condition_index=0),
            'set_niagara_effect_type_scalability_condition': R0(condition_index=0, cvar_name='fx.Niagara.QualityLevel', use_min_int=True, min_int=2),
            'copy_niagara_effect_type_scalability_row': E(kind='system', row_index=1, record_hash=h1, source_asset_path=ET, source_row_index=0, source_record_hash=h0),
            'reset_niagara_effect_type_scalability_row': R0(),
            'simulate_niagara_system_preview': dict(asset_path=SYS, ticks=2),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        props = lambda n: tools[n].inputSchema.get('properties', {})
        assert all(n.startswith(READ_ONLY) or 'dry_run' in props(n) for n in args), [n for n in args if not n.startswith(READ_ONLY) and 'dry_run' not in props(n)]

        def state():
            return {'et': api.call('POST', '/niagara/effect-types/inspect', C),
                    'rows': api.call('POST', '/niagara/effect-types/scalability/inspect', {**C, 'ValueKind': 'system'})['rows'],
                    'rule': api.call('POST', '/niagara/effect-types/rules/inspect', {**C, 'RuleIndex': 0, 'RulePath': sb['object_path']})['fields'],
                    'rs': api.call('POST', '/niagara/rule-sets/inspect', {'AssetPath': RS})['rules']}
        before = state()
        outcome = {}
        for name, a in args.items():
            a = dict(a)
            if 'dry_run' in props(name):
                a.update(dry_run=True, confirm=True)
            elif 'confirm' in props(name):
                a.update(confirm=True)
            result = await mcp_server.mcp.call_tool(name, a)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:140]
            else:
                if 'dry_run' in props(name) and 'dry_run' in payload:
                    assert payload['dry_run'] is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        assert state() == before, 'dry runs changed the assets'
        for p in ('ET_MCP_McpNew', 'ET_MCP_McpDup'):
            api.call('POST', '/niagara/effect-types/inspect', {'AssetPath': f'/Game/UE5MCP_Test/{p}.{p}'}, ok=False)
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} Niagara effect-type MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); assets unchanged')
        assert set(guarded) == EXPECTED_GUARD, guarded
    finally:
        for p in ASSETS:
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
