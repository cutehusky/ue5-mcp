"""Call the Level Sequence marker MCP tools through the registered FastMCP dispatcher.

Builds the markers from smoke_sequencer_markers_live, unlocks the list over REST, then runs Inspect for real and Add/Move/Delete,
metadata and lock as confirmed dry runs; the markers and lock must be unchanged.
"""
import asyncio
import json
import sys

from smoke_animation_curves_live import PROJECT, Api
import smoke_sequencer_markers_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)


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
    m = live.Markers(api)
    try:
        live.prepare(api)
        m.edit({'FieldName': 'Lock', 'bEnabled': False, 'bExpectedEnabled': True})
        before = live.state(m)
        i = m.inspect()
        g = dict(asset_path=live.SEQ, expected_sequence_class_path=i['sequence_class_path'], expected_marked_frames_snapshot=i['marked_frames_snapshot'],
                 confirm=True, dry_run=True)
        calls = [
            ('level_sequence_marked_frames', dict(asset_path=live.SEQ)),
            ('level_sequence_marked_frames', dict(**g, operation='Add', destination_tick_frame=8000, label='New', comment='x')),
            ('level_sequence_marked_frames', dict(**g, operation='Move', source_index=1, expected_source_tick_frame=3000, expected_source_label='End',
                                                  destination_tick_frame=4000)),
            ('level_sequence_marked_frames', dict(**g, operation='Delete', source_index=3, expected_source_tick_frame=7000, expected_source_label='Late')),
            ('set_level_sequence_marker_metadata', dict(**g, marker_index=0, expected_tick_frame=1000, expected_label='Start', label='S', comment='c',
                                                        use_custom_color=True, linear_rgba=[0.2, 0.4, 0.6, 1], determinism_fence=True, inclusive_time=False)),
            ('set_level_sequence_markers_locked', dict(**g, locked=True, expected_locked=False)),
        ]
        tools = {t.name for t in await mcp_server.mcp.list_tools()}
        assert {n for n, _ in calls} <= tools
        for name, args in calls:
            r = await call(name, args)
            assert r['dry_run'] is True and not r['written'], (name, r)
            if args.get('dry_run'):
                assert r['would_change'], (name, r)
        assert live.state(m) == before, 'dry runs changed markers'
        print(f'3 Sequencer marker MCP tools dispatched ({len(calls)} calls ok); markers unchanged')
    finally:
        live.cleanup(api)


if __name__ == '__main__':
    asyncio.run(run())
