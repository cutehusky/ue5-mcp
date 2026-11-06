"""Call the Level Sequence section/track settings MCP tools through the registered FastMCP dispatcher.

Builds the sequence from smoke_sequencer_sections_live. Each tool runs once as Inspect and once as a confirmed dry-run edit;
every setting must be unchanged afterwards.
"""
import asyncio
import json
import sys

from smoke_animation_curves_live import PROJECT, Api
import smoke_sequencer_sections_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server


async def call(name, args):
    result = await mcp_server.mcp.call_tool(name, args)
    blocks = result[0] if isinstance(result, tuple) else result
    text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError((name, 'non-JSON response', text[:300]))
    assert 'errorMessage' not in payload, (name, payload['errorMessage'][:300])
    return payload


async def run():
    mcp_server.BASE_URL = live.BASE
    api = Api(live.BASE)
    s = live.Settings(api)
    try:
        live.prepare(api)
        before = live.state(s)
        cls = '/Script/MovieSceneTracks.MovieSceneFloatSection'
        tcls = '/Script/MovieSceneTracks.MovieSceneFloatTrack'
        snap = lambda kind, path, extra=None: s.inspect(kind, path, extra)[live.ROUTES[kind][2]]
        sec = lambda path=live.S0: dict(asset_path=live.SEQ, section_path=path)
        trk = dict(asset_path=live.SEQ, track_path=live.TRACK)
        x = s.inspect('external', live.S0, {'SourceTexturePath': live.CURVE})
        edits = {
            'level_sequence_section_blend_type': dict(**sec(), operation='Set', blend_type=16, expected_has_blend_type=True, expected_blend_type=2,
                                                      expected_section_class_path=cls, expected_blend_snapshot=snap('blend', live.S0)),
            'level_sequence_section_completion_mode': dict(**sec(), operation='Set', completion_mode=0, expected_completion_mode=1,
                                                           expected_section_class_path=cls, expected_completion_snapshot=snap('completion', live.S0)),
            'level_sequence_section_easing': dict(**sec(), operation='In', duration_tick_frames=900, expected_section_class_path=cls,
                                                  expected_easing_snapshot=snap('easing', live.S0)),
            'level_sequence_section_builtin_easing': dict(**sec(), operation='Out', preset=0, expected_function_path=x['ease_out']['function_path'],
                                                          expected_section_class_path=cls, expected_easing_snapshot=snap('builtin', live.S0),
                                                          allow_custom_replacement=True),
            'level_sequence_section_external_easing': dict(**sec(), operation='In', curve_path=live.CURVE, expected_curve_snapshot=x['destination_curve_snapshot'],
                                                           expected_function_path=x['ease_in']['function_path'], expected_section_class_path=cls,
                                                           expected_easing_snapshot=x['easing_snapshot'], allow_function_replacement=True),
            'level_sequence_section_automatic_easing': dict(**sec(live.S1), operation='Out', automatic=True, expected_automatic=True,
                                                            expected_section_class_path=cls, expected_track_easing_snapshot=snap('auto', live.S1)),
            'level_sequence_section_pre_post_roll': dict(**sec(), operation='Set', pre_roll_tick_frames=0, post_roll_tick_frames=0,
                                                         expected_pre_roll_tick_frames=500, expected_post_roll_tick_frames=700,
                                                         expected_section_class_path=cls, expected_roll_snapshot=snap('roll', live.S0)),
            'level_sequence_track_evaluation_policy': dict(**trk, field='bEvaluateInPostroll', enabled=True, expected_enabled=False,
                                                           expected_track_class_path=tcls, expected_evaluation_snapshot=snap('evaluation', live.TRACK)),
            'level_sequence_section_overlap_priority': dict(**sec(live.S1), operation='Set', priority=0, expected_priority=5,
                                                            expected_section_class_path=cls, expected_priority_snapshot=snap('priority', live.S1)),
            'level_sequence_track_mute': dict(**trk, operation='Row', row_index=3, disabled=False, expected_disabled=True,
                                              expected_track_class_path=tcls, expected_mute_snapshot=snap('mute', live.TRACK, {'Start': 3})),
        }
        tools = {t.name for t in await mcp_server.mcp.list_tools()}
        missing = sorted(set(edits) - tools)
        assert not missing, ('tools not registered', missing)
        for name, args in edits.items():
            inspect = {k: v for k, v in args.items() if k in ('asset_path', 'section_path', 'track_path', 'row_index')}
            await call(name, inspect)
            r = await call(name, dict(args, confirm=True, dry_run=True))
            assert r.get('dry_run') is True and not r.get('written') and not r.get('recomputed'), (name, str(r)[:300])
        assert live.state(s) == before, 'dry runs changed settings'
        print(f'{len(edits)} Sequencer section/track settings MCP tools dispatched (inspect + dry-run edit, {2 * len(edits)} ok); settings unchanged')
    finally:
        live.cleanup(api)


if __name__ == '__main__':
    asyncio.run(run())
