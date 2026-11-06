"""Call the Level Sequence Float/Double/Bool channel MCP tools through the registered FastMCP dispatcher.

Builds a Level Sequence with a float-property section (two keys) and a visibility section (one key) over REST.
Read-only and sampling tools run for real, mutating tools as confirmed dry runs; channel snapshots must be unchanged.
Covers Float/Double/Bool/Byte/Integer/Object tools; object sampling runs as a confirmed dry run (no loading).
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_sequencer_channels_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)


async def run():
    mcp_server.BASE_URL = live.BASE
    api = Api(live.BASE)
    c = live.Channels(api)
    httpx.post(live.BASE + '/assets/delete', json={'AssetPath': live.PKG}, timeout=180)
    try:
        assert httpx.post(live.BASE + '/level-sequences/create', json={'AssetPath': live.PKG}, timeout=180).text == live.PKG
        guid = api.call('POST', '/level-sequences/bindings', {'AssetPath': live.SEQ, 'Operation': 'add', 'Name': 'Cam', 'ClassPath': '/Script/Engine.CameraActor'})['binding_guid']
        for tc, extra in [(tc, {'PropertyName': p, 'PropertyPath': p}) for tc, p in live.PROPERTY_TRACKS] + [('visibility', {})]:
            ti = api.call('POST', '/level-sequences/tracks', {'AssetPath': live.SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackClass': tc, **extra})['track_index']
            api.call('POST', '/level-sequences/sections', {'AssetPath': live.SEQ, 'Operation': 'add', 'BindingGuid': guid, 'TrackIndex': ti, 'Frame': 0, 'EndFrame': 30000})
        for section, kind, keys in ((live.FLOAT, 'Float', ((1000, 1.0), (5000, 2.0))), (live.VIS, 'Bool', ((1000, 1),))):
            for frame, value in keys:
                c.edit(live.KP, section, kind, {'FieldName': 'KeyAdd', 'SizeX': frame, 'Value': value})
        mode = c.keys(live.FLOAT, 'Float')[1]['tangent_mode']
        c.edit(live.KP, live.FLOAT, 'Float', {'FieldName': 'KeyTangentMode', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'Value': 1, 'ExpectedFormat': mode})
        c.edit(live.KP, live.INT, 'Integer', {'FieldName': 'KeyAdd', 'SizeX': 1000, 'Value': 5})
        c.edit(live.KP, live.OBJ, 'Object', {'FieldName': 'KeyAdd', 'SizeX': 1000, 'SourceTexturePath': ''})
        fcls, fch = c.info(live.FLOAT, 'Float')
        before = {k: c.snap(s, kind) for k, (s, kind) in live.SECTIONS.items() if k != 'double'}
        icls, ich = c.info(live.INT, 'Integer')
        ocls, och = c.info(live.OBJ, 'Object')
        ig = dict(asset_path=live.SEQ, section_path=live.INT, channel_index=0, expected_section_class_path=icls, expected_channel_snapshot=ich['native_channel_snapshot'])
        og = dict(asset_path=live.SEQ, section_path=live.OBJ, channel_index=0, expected_section_class_path=ocls, expected_channel_snapshot=och['native_channel_snapshot'])
        ycls, ych = c.info(live.BYTE, 'Byte')
        bcls, bch = c.info(live.VIS, 'Bool')
        fk = c.keys(live.FLOAT, 'Float')
        f = dict(asset_path=live.SEQ, section_path=live.FLOAT, channel_type='Float', channel_index=0)
        fg = dict(**f, expected_section_class_path=fcls, expected_channel_snapshot=fch['native_channel_snapshot'])
        b = dict(asset_path=live.SEQ, section_path=live.VIS, channel_type='Bool', channel_index=0)
        bg = dict(**b, expected_section_class_path=bcls, expected_channel_snapshot=bch['native_channel_snapshot'])
        args = {
            'discover_level_sequence_numeric_channels': dict(asset_path=live.SEQ, section_path=live.FLOAT),
            'discover_level_sequence_channels': dict(asset_path=live.SEQ, section_path=live.VIS),
            'level_sequence_channel_extrapolation': dict(**fg, operation='PreInfinity', value=3, expected_value=4),
            'level_sequence_channel_default': dict(**fg, operation='SetDefault', value=0.5, expected_exists=False),
            'level_sequence_numeric_key_policy': dict(**fg, operation='KeyInterpolation', key_index=0, expected_frame=1000, value=1,
                                                      expected_mode=fk[0]['interpolation']),
            'set_level_sequence_key_tangents': dict(**fg, key_index=1, expected_frame=5000, components=[0.5, 0.5, 0, 0],
                                                    expected_components=fk[1]['tangent_components'], weight_mode=0,
                                                    expected_weight_mode=fk[1]['tangent_weight_mode']),
            'move_level_sequence_numeric_key': dict(**fg, key_index=1, expected_frame=5000, new_frame=6000),
            'set_level_sequence_numeric_key_value': dict(**fg, key_index=1, expected_frame=5000, value=3, expected_value=fk[1]['value']),
            'edit_level_sequence_numeric_key': dict(**fg, operation='KeyAdd', frame=9000, value=0.5),
            'level_sequence_discrete_keys': dict(**bg, operation='KeyAdd', frame=4000, value=0),
            'sample_level_sequence_numeric_channel': dict(**fg, tick_frames=[1000, 3000, 5000]),
            'sample_level_sequence_discrete_channel': dict(**bg, tick_frames=[0, 1000, 20000]),
            'offset_level_sequence_channel_keys': dict(**fg, offset_tick_frames=500),
            'duplicate_level_sequence_channel_key': dict(**bg, source_key_index=0, expected_source_frame=1000, destination_tick_frame=2000),
            'level_sequence_object_channel_default': dict(**og, operation='ClearDefault', object_path='', expected_soft_path=''),
            'level_sequence_object_keys': dict(**og, operation='KeyMove', key_index=0, expected_frame=1000, expected_soft_path='', frame=2000),
            'sample_level_sequence_object_channel': dict(**og, tick_frames=[1000]),
            'level_sequence_integer_interpolation': dict(**ig, operation='Set', enabled=True, expected_enabled=False),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        missing = sorted(set(args) - set(tools))
        assert not missing, ('tools not registered', missing)
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
            text = ''.join(x.text for x in blocks if hasattr(x, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:180]
                continue
            if 'dry_run' in props(name):
                assert payload.get('dry_run') is True and not payload.get('written'), (name, str(payload)[:300])
            outcome[name] = 'ok'
        assert {k: c.snap(s, kind) for k, (s, kind) in live.SECTIONS.items() if k != 'double'} == before, 'dry runs changed channels'
        byte = await mcp_server.mcp.call_tool('level_sequence_discrete_keys', dict(asset_path=live.SEQ, section_path=live.BYTE, channel_type='Byte', channel_index=0,
                                                operation='KeyAdd', frame=1000, value=2, expected_section_class_path=ycls,
                                                expected_channel_snapshot=ych['native_channel_snapshot'], confirm=True, dry_run=True))
        assert 'errorMessage' not in str(byte) and c.snap(live.BYTE, 'Byte') == ych['native_channel_snapshot'], byte
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} Sequencer channel MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); channels unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(live.BASE + '/assets/delete', json={'AssetPath': live.PKG}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
