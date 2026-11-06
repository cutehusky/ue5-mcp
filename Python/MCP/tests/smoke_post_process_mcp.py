"""Call every post-process volume MCP tool through the registered FastMCP dispatcher.

Builds a scratch map with a post-process volume holding one blendable and edited (non-default) bool/enum/float/int32/
vector/object settings over REST, so every reset tool has something to reset. Read-only tools run for real, mutating
tools as confirmed dry runs; the volume's controls, blendables and all settings fields must be unchanged.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_post_process_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}
P = '/volumes/post-process/'


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP), 'scratch post-process map is open; run smoke_post_process_live.py cleanup'
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        assert api.call('GET', '/worlds/inspect')['world_path'].startswith(live.MAP)
        live.ACTOR = A = api.call('POST', '/volumes/create-box', {'VolumeType': 'PostProcess', 'Name': 'MCP_PPV', 'Position': {'X': 0, 'Y': 0, 'Z': 0},
                                                                  'Extent': {'X': 200, 'Y': 200, 'Z': 200}, **LIVE})['actor_path']
        api.call('POST', P + 'blendable-add', {'ActorPath': A, 'ExpectedEntryCount': 0, 'ObjectPath': live.BLENDABLE, 'ScalarValue': 0.5, **LIVE})
        f = live.fields(api)
        api.call('POST', P + 'scalar', {'ActorPath': A, 'FieldName': 'WhiteTemp', 'ExpectedScalarValue': f['WhiteTemp']['scalar_value'], 'bExpectedBoolValue': False, 'ScalarValue': 5000, **LIVE})
        api.call('POST', P + 'integer', {'ActorPath': A, 'FieldName': 'LumenMaxReflectionBounces', 'ExpectedScalarValue': 1, 'bExpectedBoolValue': False, 'ScalarValue': 3, **LIVE})
        api.call('POST', P + 'bool', {'ActorPath': A, 'FieldName': 'bMobileHQGaussian', 'bExpectedBoolValue': False, 'bExpectedOverride': False, 'bBoolValue': True, **LIVE})
        api.call('POST', P + 'vector', {'ActorPath': A, 'FieldName': 'ColorSaturation', 'ExpectedChannels': [1, 1, 1, 1], 'bExpectedOverride': False, 'Channels': [0.5, 0.5, 0.5, 1], **LIVE})
        api.call('POST', P + 'enum', {'ActorPath': A, 'FieldName': 'BloomMethod', 'ExpectedEnumValue': 'BM_SOG', 'bExpectedOverride': False, 'EnumValue': 'BM_FFT', **LIVE})
        api.call('POST', P + 'object', {'ActorPath': A, 'FieldName': 'BloomDirtMask', 'ExpectedObjectPath': 'None', 'bExpectedOverride': False, 'ObjectPath': live.TEXTURE, **LIVE})
        v = live.inspect(api)
        args = {
            'inspect_post_process_volume': dict(actor_path=A), 'inspect_post_process_setting_fields': dict(actor_path=A, field_count=32),
            'set_post_process_volume_control': dict(actor_path=A, field='BlendWeight', expected_value=v['blend_weight'], scalar_value=0.5),
            'set_post_process_blendable_weight': dict(actor_path=A, expected_entry_count=1, entry_index=0, expected_object_path=live.BLENDABLE, expected_weight=0.5, weight=0.9),
            'remove_post_process_blendable': dict(actor_path=A, expected_entry_count=1, entry_index=0, expected_object_path=live.BLENDABLE, expected_weight=0.5),
            'add_post_process_blendable': dict(actor_path=A, expected_entry_count=1, object_path=live.BLENDABLE_B, weight=1),
            'set_post_process_setting_override': dict(actor_path=A, field='BloomIntensity', expected_enabled=False, enabled=True),
            'set_post_process_setting_scalar': dict(actor_path=A, field='WhiteTemp', expected_value=5000, expected_override=False, value=7000),
            'set_post_process_setting_bool': dict(actor_path=A, field='bMobileHQGaussian', expected_value=True, expected_override=False, value=False),
            'set_post_process_setting_enum': dict(actor_path=A, field='BloomMethod', expected_name='BM_FFT', expected_override=False, name='BM_SOG'),
            'set_post_process_setting_object': dict(actor_path=A, field='AutoExposureMeterMask', expected_object_path='None', expected_override=False, object_path=live.TEXTURE),
            'set_post_process_setting_vector': dict(actor_path=A, field='ColorSaturation', expected_channels=[0.5, 0.5, 0.5, 1], expected_override=False, channels=[1, 1, 1, 1]),
            'set_post_process_setting_integer': dict(actor_path=A, field='LumenMaxReflectionBounces', expected_value=3, expected_override=False, value=4),
            'reset_post_process_setting_scalar': dict(actor_path=A, field='WhiteTemp', expected_value=5000, expected_override=False),
            'reset_post_process_setting_integer': dict(actor_path=A, field='LumenMaxReflectionBounces', expected_value=3, expected_override=False),
            'reset_post_process_setting_bool': dict(actor_path=A, field='bMobileHQGaussian', expected_value=True, expected_override=False),
            'reset_post_process_setting_vector': dict(actor_path=A, field='ColorSaturation', expected_channels=[0.5, 0.5, 0.5, 1], expected_override=False),
            'reset_post_process_setting_enum': dict(actor_path=A, field='BloomMethod', expected_name='BM_FFT', expected_override=False),
            'reset_post_process_setting_object': dict(actor_path=A, field='BloomDirtMask', expected_object_path=live.TEXTURE, expected_override=False),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        names = {t for t in tools if 'post_process' in t}
        assert names == set(args), sorted(names ^ set(args))
        assert len(args) == 19, len(args)
        props = lambda name: tools[name].inputSchema.get('properties', {})
        before = live.state(api)
        outcome = {}
        for name, a in args.items():
            a = dict(a)
            if 'dry_run' in props(name):
                a.update(dry_run=True)
            if 'confirm' in props(name):
                a.update(confirm=True)
            result = await mcp_server.mcp.call_tool(name, a)
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
        assert live.close(live.state(api), before), 'dry runs changed the post-process volume'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} post-process MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); volume unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
