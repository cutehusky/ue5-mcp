"""Call the Level Sequence subsection/shot MCP tools through the registered FastMCP dispatcher.

Builds the hierarchy from smoke_sequencer_subsections_live. Each tool runs once as Inspect and once as a confirmed dry-run edit;
parameters, origin, references and shot metadata must be unchanged.
"""
import asyncio
import json
import sys

from smoke_animation_curves_live import PROJECT, Api
import smoke_sequencer_subsections_live as live

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
    s = live.Subs(api)
    try:
        live.prepare(api)
        before = live.state(s)
        shot, sub = s.inspect('params', live.SHOT), s.inspect('params', live.SUB)
        o, m = s.inspect('origin', live.SUB), s.inspect('shot', live.SHOT)
        ref = s.inspect('reference', live.SUB, {'SourceTexturePath': live.B})
        g = lambda i: dict(asset_path=live.PARENT, expected_section_class_path=i['section_class_path'])
        edits = {
            'level_sequence_subsection_parameters': dict(section_path=live.SHOT, **g(shot), operation='Bias', value=10, expected_value=50,
                                                         expected_nested_sequence_path=live.A, expected_subsection_snapshot=shot['subsection_snapshot']),
            'level_sequence_subsection_origin': dict(section_path=live.SUB, **g(o), operation='DefaultSet', axis=1, value=5, expected_has_default=False,
                                                     expected_nested_sequence_path=live.C, expected_origin_snapshot=o['origin_snapshot']),
            'level_sequence_subsection_reference': dict(section_path=live.SUB, **g(sub), operation='Set', candidate_sequence_path=live.B,
                                                        expected_nested_sequence_path=live.C, expected_subsection_snapshot=sub['subsection_snapshot'],
                                                        expected_destination_graph_snapshot=ref['destination_graph_snapshot'], allow_replacement=True),
            'cinematic_shot_metadata': dict(section_path=live.SHOT, **g(m), operation='Thumbnail', thumbnail_offset_seconds=1.0,
                                            expected_thumbnail_offset_seconds=0.5, expected_shot_metadata_snapshot=m['shot_metadata_snapshot']),
        }
        tools = {t.name for t in await mcp_server.mcp.list_tools()}
        assert set(edits) | {'list_cinematic_shots'} <= tools
        shots = await call('list_cinematic_shots', dict(asset_path=live.PARENT))
        assert [x['shot_name'] for x in shots['shots']] == ['Opening'], shots
        for name, args in edits.items():
            await call(name, dict(asset_path=live.PARENT, section_path=args['section_path']))
            r = await call(name, dict(args, confirm=True, dry_run=True))
            assert r['dry_run'] is True and not r['written'] and r['would_change'], (name, str(r)[:300])
        assert live.state(s) == before, 'dry runs changed subsections'
        print(f'{len(edits) + 1} Sequencer subsection/shot MCP tools dispatched ({2 * len(edits) + 1} calls ok); hierarchy unchanged')
    finally:
        live.cleanup(api)


if __name__ == '__main__':
    asyncio.run(run())
