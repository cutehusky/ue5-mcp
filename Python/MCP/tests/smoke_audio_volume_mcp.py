"""Call every AudioVolume MCP tool through the registered FastMCP dispatcher.

Builds a scratch map with an AudioVolume holding one submix override row and one listener send row with one destination
send whose inline curve has two keys, over REST. Read-only tools run for real, mutating tools as confirmed dry runs; the
volume, its routing rows and the inline curve must be unchanged.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_audio_volume_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP), 'scratch audio map is open; run smoke_audio_volume_live.py cleanup'
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        assert api.call('GET', '/worlds/inspect')['world_path'].startswith(live.MAP)
        api.call('POST', '/volumes/create-box', {'VolumeType': 'Audio', 'Name': 'MCP_Audio', 'Position': {'X': 0, 'Y': 0, 'Z': 0}, 'Extent': {'X': 500, 'Y': 500, 'Z': 200}, **LIVE})
        idr = live.ident(api)
        api.call('POST', '/volumes/audio/submix/override-add', {**idr, 'ExpectedEntryCount': 0, 'ObjectPath': live.SM, 'ExpectedRowTexts': [], **LIVE})
        api.call('POST', '/volumes/audio/submix/send-row-add', {**idr, 'ExpectedEntryCount': 0, 'ScalarValue': 0, 'ExpectedRowTexts': [], **LIVE})
        api.call('POST', '/volumes/audio/submix/send-add', {**idr, 'EntryIndex': 0, 'ExpectedEntryCount': 1, 'ExpectedScalarValue': 0, 'ExpectedNestedCount': 0,
                                                            'ObjectPath': live.SM, 'ExpectedRowTexts': live.texts(api), **LIVE})
        sctx = {**idr, 'EntryIndex': 0, 'ExpectedEntryCount': 1, 'ExpectedListenerState': 0, 'NestedIndex': 0, 'ExpectedNestedCount': 1, 'ExpectedObjectPath': live.SM}
        api.call('POST', '/volumes/audio/submix/send-inline-curve/linear-keys', {**sctx, 'ExpectedCurvePath': '', 'ExpectedPairs': [], 'Pairs': [{'X': 0, 'Y': 1}, {'X': 1, 'Y': 0}],
                                                                                 'ExpectedRowTexts': live.texts(api), **LIVE})
        before = live.settled(api)
        v, a = live.vol(api), live.actor(api)
        ov, sr, cv = live.rows(api, 'SubmixOverrideSettings')[0], live.rows(api)[0], live.curve(api)
        st, ot = live.texts(api), live.texts(api, 'SubmixOverrideSettings')
        i = dict(actor_path=a, actor_guid=v['actor_guid'], expected_label=v['label'])
        orow = dict(**i, row_index=0, expected_count=1, expected_submix_path=live.SM, expected_row_texts=ot)
        srow = dict(**i, row_index=0, expected_row_count=1, expected_listener_state=0, expected_row_texts=st)
        send = dict(**srow, send_index=0, expected_send_count=1, expected_submix_path=live.SM)
        inline = dict(**send, expected_external_curve_path='')
        s0 = sr['sends'][0]
        args = {
            'inspect_audio_volume': dict(actor_path=a), 'inspect_audio_volume_submix': dict(actor_path=a),
            'inspect_audio_volume_submix_row_items': dict(actor_path=a, collection='SubmixSendSettings', row_index=0),
            'inspect_audio_volume_send_inline_curve': dict(actor_path=a, row_index=0, send_index=0),
            'set_audio_volume_control': dict(**i, field_name='Priority', expected_value=v['priority'], priority=5),
            'set_audio_volume_interior': dict(**i, field_name='ExteriorVolume', expected_value=v['interior']['exterior_volume'], value=0.5),
            'set_audio_volume_reverb': dict(**i, field_name='Volume', expected_value=v['reverb']['volume'], value=0.75),
            'set_audio_volume_reverb_object': dict(**i, field_name='ReverbEffect', expected_object_path='', object_path=live.REVERB),
            'set_audio_volume_override_crossfade': dict(**orow, expected_seconds=ov['crossfade_time'], seconds=1.5),
            'set_audio_volume_override_effects': dict(**orow, expected_effect_paths=[], effect_paths=[live.PRESET]),
            'set_audio_volume_override_target': dict(**orow, submix_path=live.SM_EQ),
            'add_audio_volume_override': dict(**i, expected_count=1, submix_path=live.SM_EQ, expected_row_texts=ot),
            'remove_audio_volume_override': dict(**orow, expected_effect_paths=[]),
            'reorder_audio_volume_overrides': dict(**i, expected_submix_paths=[live.SM], source_index_order=[0], expected_row_texts=ot),
            'add_audio_volume_send_row': dict(**i, expected_count=1, listener_state=1, expected_row_texts=st),
            'add_audio_volume_submix_send': dict(**srow, expected_send_count=1, submix_path=live.SM_EQ),
            'set_audio_volume_send_numeric': dict(**send, field_name='SendLevel', expected_value=s0['send_level'], value=0.5),
            'set_audio_volume_send_control': dict(**send, field_name='SendStage', expected_value=int(s0['send_stage']), value=1),
            'set_audio_volume_send_curve': dict(**send, expected_curve_path='', curve_path=live.CURVE),
            'set_audio_volume_send_target': dict(**send, submix_path=live.SM_EQ),
            'remove_audio_volume_submix_send': dict(**send),
            'remove_audio_volume_send_row': dict(**i, row_index=0, expected_count=1, expected_listener_state=0, expected_destination_paths=[live.SM], expected_row_texts=st),
            'set_audio_volume_send_row_listener': dict(**i, row_index=0, expected_row_count=1, expected_send_count=1, expected_listener_state=0, listener_state=1, expected_row_texts=st),
            'replace_audio_volume_send_linear_keys': dict(**{k: v_ for k, v_ in send.items()}, expected_curve_path='', expected_keys=[[0, 1], [1, 0]], keys=[[0, 1], [0.5, 0.8], [1, 0]]),
            'reorder_audio_volume_submix_sends': dict(**srow, expected_destination_paths=[live.SM], source_index_order=[0]),
            'reorder_audio_volume_send_rows': dict(**i, expected_listener_states=[0], source_index_order=[0], expected_row_texts=st),
            'set_audio_volume_send_inline_key_setting': dict(**inline, key_index=0, expected_key_count=cv['key_count'], field_name='InterpMode',
                                                             expected_value=cv['keys'][0]['interpolation'], value=2),
            'set_audio_volume_send_inline_curve_setting': dict(**inline, field_name='DefaultValue', expected_value=cv['default_value'], value=0.5),
            'edit_audio_volume_send_inline_keys': dict(**inline, expected_key_count=cv['key_count'], operation='Add', time=0.25, value=0.9),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        names = {n for n in tools if n.startswith(('inspect_audio_volume', 'set_audio_volume', 'add_audio_volume', 'remove_audio_volume', 'reorder_audio_volume',
                                                    'replace_audio_volume', 'edit_audio_volume'))}
        assert names == set(args), sorted(names ^ set(args))
        props = lambda name: tools[name].inputSchema.get('properties', {})
        outcome = {}
        for name, aa in args.items():
            aa = dict(aa)
            if 'dry_run' in props(name):
                aa.update(dry_run=True)
            if 'confirm' in props(name):
                aa.update(confirm=True)
            result = await mcp_server.mcp.call_tool(name, aa)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:180]
            else:
                if 'dry_run' in props(name) and isinstance(payload, dict) and 'dry_run' in payload:
                    assert payload['dry_run'] is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        after = live.settled(api)
        assert live.close(after, before), ('dry runs changed the audio volume', [k for k in after if not live.close(after[k], before.get(k))])
        guarded = {k: v_ for k, v_ in outcome.items() if v_ != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} AudioVolume MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); volume unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
