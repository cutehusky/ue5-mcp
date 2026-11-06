"""Call the Level Sequence folder and binding-tag MCP tools through the registered FastMCP dispatcher.

Builds the tree from smoke_sequencer_folders_live. Inspect and validation run for real; create, rename/color/sort, move,
remove, membership and tag edits run as confirmed dry runs. Folders and tags must be unchanged.
"""
import asyncio
import json
import sys

from smoke_animation_curves_live import PROJECT, Api
import smoke_sequencer_folders_live as live

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
    t = live.Tree(api)
    try:
        live.prepare(api)
        before = live.state(t)
        fi, ti = t.inspect(), t.inspect(live.TAGS)
        f = t.folders()
        guid = f['Cams']['binding_guids'][0]
        fg = dict(asset_path=live.SEQ, expected_sequence_class_path=fi['sequence_class_path'], expected_folder_snapshot=fi['folder_snapshot'], confirm=True, dry_run=True)
        tg = dict(asset_path=live.SEQ, expected_sequence_class_path=ti['sequence_class_path'], expected_binding_tags_snapshot=ti['binding_tags_snapshot'], confirm=True, dry_run=True)
        calls = [
            ('level_sequence_folders', dict(asset_path=live.SEQ), False),
            ('validate_level_sequence_folders', dict(asset_path=live.SEQ), False),
            ('level_sequence_folders', dict(**fg, operation='Create', parent_folder_path=f['Set']['path'], name='New'), True),
            ('edit_level_sequence_folder_settings', dict(**fg, folder_path=f['Set']['path'], operation='Rename', name='Stage', expected_name='Set'), True),
            ('edit_level_sequence_folder_settings', dict(**fg, folder_path=f['Set']['path'], operation='Color', rgba_bytes=[1, 2, 3, 255], expected_rgba_bytes=f['Set']['rgba_bytes']), True),
            ('edit_level_sequence_folder_settings', dict(**fg, folder_path=f['Cams']['path'], operation='Sort', sorting_order=1, expected_sorting_order=7), True),
            ('move_or_remove_level_sequence_folder', dict(**fg, folder_path=f['Cams']['path'], operation='Move', expected_parent_folder_path='None',
                                                          destination_parent_folder_path=f['Shots']['path']), True),
            ('move_or_remove_level_sequence_folder', dict(**fg, folder_path=f['Shots']['path'], operation='RemoveEmpty', expected_parent_folder_path='None'), True),
            ('assign_level_sequence_folder_content', dict(**fg, member_type='Binding', expected_source_folder_path=f['Cams']['path'], destination_folder_path=f['Shots']['path'],
                                                          binding_guid=guid), True),
            ('assign_level_sequence_folder_content', dict(**fg, member_type='Track', expected_source_folder_path=f['Set']['path'], destination_folder_path='',
                                                          master_track_path=live.TRACK, expected_track_signature=live.track_signature(api)), True),
            ('level_sequence_binding_tags', dict(asset_path=live.SEQ), False),
            ('level_sequence_binding_tags', dict(**tg, operation='UntagRootBinding', tag_name='Leads', binding_guid=guid, expected_tag_exists=True), True),
            ('rename_level_sequence_binding_tag', dict(**tg, tag_name='Leads', new_tag_name='Stars', allow_name_consumer_breakage=True), True),
        ]
        tools = {x.name for x in await mcp_server.mcp.list_tools()}
        assert {n for n, _, _ in calls} <= tools
        for name, args, mutating in calls:
            r = await call(name, args)
            if mutating:
                assert r['dry_run'] is True and not r['written'] and r['would_change'], (name, str(r)[:300])
        assert live.state(t) == before, 'dry runs changed folders or tags'
        print(f'{len({n for n, _, _ in calls})} Sequencer folder/tag MCP tools dispatched ({len(calls)} calls ok); folders and tags unchanged')
    finally:
        live.cleanup(api)


if __name__ == '__main__':
    asyncio.run(run())
