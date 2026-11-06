"""Call every animation-curve MCP tool through the registered FastMCP dispatcher.

Needs the fixture from create_anim_curve_fixture.py. Works on its own duplicate (float curve MCP_Float plus a
transform curve on hand_r); read-only tools run for real, mutating tools run as confirmed dry runs, and the
copy's curves must be unchanged before it is deleted.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import FIXTURE, PROJECT, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
SEQ = '/Game/UE5MCP_Test/AS_MCP_CurveMcp.AS_MCP_CurveMcp'
READ_ONLY = ('get_', 'inspect_', 'evaluate_', 'list_')


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    r = httpx.post(BASE + '/assets/duplicate', json={'AssetPath': FIXTURE, 'DestinationPath': SEQ.split('.')[0]}, timeout=300)
    assert r.is_success, r.text[:300]
    try:
        C = {'AssetPath': SEQ, 'bConfirm': True}
        api.call('POST', '/animations/curves/transform', {**C, 'CurveName': 'hand_r'})
        api.call('PATCH', '/animations/curves/transform/keys', {**C, 'CurveName': 'hand_r', 'TransformKeys': [
            {'Time': 0.0, 'Location': {'X': 0, 'Y': 0, 'Z': 0}}, {'Time': 0.2, 'Location': {'X': 10, 'Y': 0, 'Z': 0}}]})
        f, tr = 'MCP_Float', 'hand_r'
        A = lambda **kw: dict(asset_path=SEQ, **kw)
        args = {
            'get_animation_curve': A(curve_name=f),
            'inspect_animation_rich_float_curve': A(curve_name=f),
            'replace_animation_rich_float_curve': A(curve_name=f, keys=[{'Time': 0.0, 'Value': 2.0}]),
            'set_animation_float_curve_extrapolation': A(curve_name=f, pre=0, post=0),
            'evaluate_animation_float_curve': A(curve_name=f, times=[0.0, 0.2]),
            'duplicate_animation_float_curve': A(curve_name=f, new_name='McpDry'),
            'rename_animation_float_curve': A(curve_name=f, new_name='McpDry'),
            'set_animation_float_curve_flag': A(curve_name=f, flag='Metadata'),
            'set_animation_float_curve_color': A(curve_name=f, color={'R': 1, 'G': 0, 'B': 0, 'A': 1}),
            'edit_animation_rich_float_key': A(curve_name=f, key={'Time': 0.3, 'Value': 1.0}),
            'move_animation_rich_float_key': A(curve_name=f, time=0.2, new_time=0.3),
            'inspect_animation_transform_curve_channel': A(curve_name=tr),
            'replace_animation_transform_curve_channel': A(curve_name=tr, channel='translation', axis=1, keys=[{'Time': 0.0, 'Value': 1.0}]),
            'evaluate_animation_transform_curve_channel': A(curve_name=tr, channel='translation', axis=0, times=[0.2]),
            'set_animation_transform_channel_extrapolation': A(curve_name=tr, channel='translation', axis=0, pre=3, post=3),
            'evaluate_animation_transform_curve': A(curve_name=tr, times=[0.1]),
            'create_animation_transform_curve': A(bone_name='head'),
            'remove_animation_transform_curve': A(curve_name=tr),
            'duplicate_animation_transform_curve': A(curve_name=tr, destination_bone='hand_l'),
            'rename_animation_transform_curve': A(curve_name=tr, destination_bone='hand_l'),
            'set_animation_transform_curve_key': A(curve_name=tr, time=0.1, location={'X': 5, 'Y': 0, 'Z': 0}),
            'remove_animation_transform_curve_key': A(curve_name=tr, time=0.2),
            'set_animation_transform_curve_flag': A(curve_name=tr, flag='DriveTrack', enabled=False),
            'replace_animation_transform_curve_keys': A(curve_name=tr, keys=[{'Time': 0.0}]),
            'inspect_animation_transform_curve_keys': A(curve_name=tr, union_timeline=True),
            'move_animation_transform_curve_key': A(curve_name=tr, time=0.2, new_time=0.3),
            'resample_animation_transform_curve': A(curve_name=tr, times=[0.0, 0.1, 0.2]),
            'resample_animation_float_curve': A(curve_name=f, times=[0.0, 0.1]),
            'inspect_animation_curve_diagnostics': A(),
            'list_animation_source_curves': A(),
            'remove_animation_float_curve_key_range': A(curve_name=f, start_time=0.1, end_time=0.3),
            'remove_animation_transform_curve_key_range': A(curve_name=tr, start_time=0.1, end_time=0.3),
            'scale_animation_float_curve_time': A(curve_name=f, factor=0.5),
            'set_animation_float_curve_comment': A(curve_name=f, comment='dry'),
            'inspect_animation_float_curve_range': A(curve_name=f),
            'offset_animation_float_curve_time': A(curve_name=f, offset=0.05),
            'offset_animation_transform_curve_time': A(curve_name=tr, offset=0.05),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        # Every tool whose body calls an /animations/curves route (listed from mcp_server.py) must be covered.
        assert set(args) <= set(tools), sorted(set(args) - set(tools))
        assert len(args) == 37
        props = lambda n: tools[n].inputSchema.get('properties', {})
        no_dry = sorted(n for n in args if not n.startswith(READ_ONLY) and 'dry_run' not in props(n))
        assert not no_dry, ('mutating tools without dry_run', no_dry)

        state = lambda: (api.call('GET', '/animations/curves/rich', params={'asset_path': SEQ, 'curve_name': f, 'count': 64}),
                         api.call('GET', '/animations/curves/transform/keys', params={'asset_path': SEQ, 'curve_name': tr, 'count': 64}),
                         api.call('GET', '/animations/curves/catalog', params={'asset_path': SEQ}))
        before = state()
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
                outcome[name] = 'guard: ' + payload['errorMessage'][7:110]
            else:
                if 'dry_run' in props(name):
                    assert payload.get('dry_run') is True, (name, str(payload)[:300])
                outcome[name] = 'ok'
        assert state() == before, 'dry runs changed the curves'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} animation-curve MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} native guard); curves unchanged')
    finally:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': SEQ}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
