"""Call the World Settings MCP tools with the audio fields through the registered FastMCP dispatcher.

On a scratch map, inspect runs for real and set_editor_world_settings runs as a confirmed dry run carrying every
default reverb/ambient numeric field, bApplyReverb and both asset references; the settings must be unchanged.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_world_audio_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server


async def call(name, args):
    result = await mcp_server.mcp.call_tool(name, args)
    blocks = result[0] if isinstance(result, tuple) else result
    payload = json.loads(''.join(b.text for b in blocks if hasattr(b, 'text')))
    assert 'errorMessage' not in payload, (name, payload['errorMessage'][:300])
    return payload


async def run():
    mcp_server.BASE_URL = live.BASE
    api = Api(live.BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP)
    try:
        httpx.post(live.BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        s = await call('inspect_editor_world_settings', {})
        before = live.audio(s)
        r = await call('set_editor_world_settings', dict(
            world_path=live.MAP, confirm=True, dry_run=True, numeric_settings=live.NUMERIC,
            bool_settings={'DefaultReverbSettings.bApplyReverb': not before['apply']},
            expected_numeric_settings=before['numeric'], expected_bool_settings={'DefaultReverbSettings.bApplyReverb': before['apply']},
            object_settings=live.OBJECTS, expected_object_settings={k: '' for k in live.OBJECTS}))
        assert r['changed'], r
        after = api.call('GET', '/worlds/settings')
        assert live.audio(after) == before and not after['dirty'], 'dry run changed settings'
        print('2 World Settings MCP tools dispatched with audio fields (2 ok); settings unchanged')
    finally:
        httpx.post(live.BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(live.BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
