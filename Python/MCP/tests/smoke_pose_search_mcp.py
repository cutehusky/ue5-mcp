"""Call every Pose Search MCP tool through the registered FastMCP dispatcher.

Run after `smoke_pose_search_live.py prepare` and before `verify`. Inspect tools run for real;
mutating tools run as confirmed dry runs, so the saved fixtures and their snapshots stay unchanged.
Tools whose fixture the project lacks (composite, mirror table, vector field) must reach the server
and be rejected by its native guard.
"""
import asyncio
import json
import sys

import httpx
from smoke_pose_search_live import STATE, PROJECT, SKELETON, PREVIEW, JOG, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'


async def call(tool, args):
    result = await mcp_server.mcp.call_tool(tool, args)
    blocks = result[0] if isinstance(result, tuple) else result
    text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError((tool, 'non-JSON response', text[:400]))


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    state = json.loads(STATE.read_text(encoding='utf-8'))
    owned = state['owned']
    schema = next(p for p in owned if '/PSS_' in p)
    database = next(p for p in owned if '/PSD_' in p)
    norm = next(p for p in owned if '/PSN_' in p)
    interaction = next(p for p in owned if '/PSI_' in p)
    s = api.schema(schema)
    chans = s['channels']
    idx = lambda kind: next(c['index'] for c in chans if c['class_path'].endswith(kind))
    cpath = lambda i: chans[i]['object_path']
    pose, group, head = idx('_Pose'), idx('_Group'), idx('_Heading')
    tree = api.call('POST', '/pose-search/schemas/channels/inspect',
                    {'AssetPath': schema, 'ChannelIndex': group, 'ChannelPath': cpath(group)})['cached_channel_tree']
    kids = [n['object_path'] for n in tree if n['parent_path'] == cpath(group)]
    db = api.database(database)
    ents = db['animation_assets']
    eidx = lambda suffix: next(e['index'] for e in ents if e['asset_path'].endswith(suffix))
    seq, bs = eidx('MF_Pistol_Jog_Fwd'), eidx('AO_Pistol')
    epath = lambda i: ents[i]['asset_path']
    items = api.call('GET', '/pose-search/interactions/definition', params={'asset_path': interaction})['items']
    roles = [r['role'] for r in s['roles']]
    W = dict(confirm=True, dry_run=True)
    C = lambda i: dict(asset_path=schema, channel_index=i, expected_channel_path=cpath(i))
    E = lambda i: dict(asset_path=database, animation_index=i, expected_animation_path=epath(i))
    It = lambda i: dict(asset_path=interaction, item_index=i, expected_role=items[i]['role'], expected_animation_path=items[i]['animation_path'])
    G = dict(asset_path=schema, channel_index=group, expected_group_path=cpath(group))
    K = lambda c: dict(G, child_index=c, expected_child_path=kids[c])
    new = lambda name: schema.rsplit('/', 1)[0] + f'/{name}.{name}'

    inspect = {
        'inspect_pose_search_database': dict(asset_path=database),
        'inspect_pose_search_schema': dict(asset_path=schema),
        'list_pose_search_channel_types': dict(limit=8),
        'inspect_pose_search_channel': dict(C(head), field='Weight'),
        'inspect_pose_search_database_entry': E(seq),
        'inspect_pose_search_normalization_set': dict(asset_path=norm),
        'inspect_pose_search_interaction': dict(asset_path=interaction),
        'inspect_pose_search_entry_timing': E(seq),
        'inspect_pose_search_sampling_points': E(seq),
        'sample_pose_search_entry_root': dict(E(seq), role=roles[0], time=0.1),
        'inspect_pose_search_asset_setting': dict(asset_path=database, field='BaseCostBias'),
        'evaluate_pose_search_interaction_warp': dict(asset_path=interaction, expected_roles=[i['role'] for i in items],
                                                      actor_root_transforms=[{}, {'Translation': {'X': 150, 'Y': 0, 'Z': 0}}]),
    }
    dry = {
        'set_pose_search_schema_sample_rate': dict(asset_path=schema, sample_rate=45),
        'set_pose_search_database_schema': dict(asset_path=database, schema_path=schema),
        'add_pose_search_schema_channel': dict(asset_path=schema, channel_class='/Script/PoseSearch.PoseSearchFeatureChannel_Velocity'),
        'move_pose_search_schema_channel': dict(C(pose), target_index=0),
        'remove_pose_search_schema_channel': C(pose),
        'duplicate_pose_search_schema_channel': C(pose),
        'set_pose_search_channel_scalar': dict(C(head), field_name='Weight', value=7),
        'add_pose_search_schema_role': dict(asset_path=schema, role='Extra', skeleton_path=SKELETON),
        'add_pose_search_database_sequence': dict(asset_path=database, animation_path=JOG.format('Fwd_Left')),
        'set_pose_search_database_entry_flags': dict(E(seq), enabled=False),
        'remove_pose_search_database_entry': E(seq),
        'set_pose_search_entry_sampling_range': dict(E(seq), start=0.05, end=0.3),
        'set_pose_search_entry_mirror_policy': dict(E(seq), mirror_policy='original'),
        'duplicate_pose_search_database_entry': dict(E(seq), insertion_index=0),
        'move_pose_search_database_entry': dict(E(seq), final_index=1),
        'add_pose_search_database_blend_space': dict(asset_path=database, blend_space_path='/Game/Characters/Mannequins/Anims/Pistol/Aim/AO_Pistol.AO_Pistol'),
        'set_pose_search_blend_sampling': dict(E(bs), grid_sampling=True, horizontal_samples=4, vertical_samples=2),
        'add_pose_search_database_montage': dict(asset_path=database, animation_path='/Game/Characters/Mannequins/Anims/Pistol/MM_Pistol_Equip.MM_Pistol_Equip'),
        'set_pose_search_database_cost_bias': dict(asset_path=database, field='LoopingCostBias', value=0.1),
        'set_pose_search_database_search_mode': dict(asset_path=database, mode='BruteForce'),
        'set_pose_search_database_index_tuning': dict(asset_path=database, field='KDTreeMaxLeafSize', value=16),
        'set_pose_search_database_normalization_set': dict(asset_path=database, normalization_set_path=norm),
        'set_pose_search_normalization_databases': dict(asset_path=norm, database_paths=[database]),
        'set_pose_search_database_tags': dict(asset_path=database, tags=['A']),
        'create_pose_search_asset': dict(asset_path=new('PSS_McpDry'), kind='schema', skeleton_path=SKELETON),
        'duplicate_pose_search_asset': dict(asset_path=new('PSD_McpDry'), source_asset_path=database),
        'set_pose_search_channel_name': dict(C(head), field='NormalizationGroup', value='Hands'),
        'set_pose_search_channel_enum': dict(C(head), field='HeadingAxis', value='Z'),
        'reset_pose_search_channel_field': dict(C(head), field='HeadingAxis'),
        'set_pose_search_schema_preprocessor': dict(asset_path=schema, mode='None'),
        'set_pose_search_schema_permutation': dict(asset_path=schema, field='NumberOfPermutations', value=2),
        'set_pose_search_schema_flag': dict(asset_path=schema, field='bAddDataPadding', enabled=False),
        'request_pose_search_database_index': dict(asset_path=database, request='new'),
        'set_pose_search_role_skeleton': dict(asset_path=schema, role=roles[0], skeleton_path=SKELETON),
        'move_pose_search_schema_role': dict(asset_path=schema, role=roles[-1], final_index=0),
        'remove_pose_search_schema_role': dict(asset_path=schema, role=roles[-1]),
        'duplicate_pose_search_schema_role': dict(asset_path=schema, role=roles[-1], new_role='Copy'),
        'rename_pose_search_schema_role': dict(asset_path=schema, role=roles[-1], new_role='Renamed'),
        'add_pose_search_interaction_item': dict(asset_path=interaction, role='Third', animation_path=JOG.format('Right')),
        'remove_pose_search_interaction_item': It(1),
        'move_pose_search_interaction_item': dict(It(1), final_index=0),
        'set_pose_search_interaction_weight': dict(It(1), field='WarpingWeightRotation', value=0.25),
        'set_pose_search_interaction_banking': dict(asset_path=interaction, value=0.5),
        'set_pose_search_interaction_origin': dict(It(1), origin={'Translation': {'X': 50, 'Y': 0, 'Z': 0}}),
        'set_pose_search_interaction_animation': dict(It(1), animation_path=JOG.format('Bwd')),
        'set_pose_search_interaction_preview_mesh': dict(It(1), mesh_path=''),
        'rename_pose_search_interaction_role': dict(It(1), new_role='Other'),
        'duplicate_pose_search_interaction_item': dict(It(1), new_role='Other2'),
        'set_pose_search_blend_sampling_range': dict(E(bs), start=0, end=0.25),
        'set_pose_search_multi_animation_sampling': dict(E(bs), horizontal_samples=3, vertical_samples=2),
        'replace_pose_search_entry_animation': dict(E(seq), animation_path=JOG.format('Bwd_Left')),
        'set_pose_search_pose_bones': dict(C(pose), bones=[{'Bone': 'hand_l'}]),
        'set_pose_search_trajectory_samples': dict(C(idx('_Trajectory')), samples=[{'Offset': 0.25}]),
        'finalize_pose_search_schema': dict(asset_path=schema),
        'add_pose_search_group_child': dict(G, channel_class='/Script/PoseSearch.PoseSearchFeatureChannel_Velocity'),
        'remove_pose_search_group_child': K(0),
        'move_pose_search_group_child': dict(K(0), final_index=1),
        'duplicate_pose_search_group_child': K(0),
        'set_pose_search_channel_color': dict(C(head), field='DebugColor', r=0.1, g=0.2, b=0.3),
        'set_pose_search_database_preview_mesh': dict(asset_path=database, mesh_path=PREVIEW),
        'set_pose_search_database_interval': dict(asset_path=database, field='AdditionalExtrapolationTime', start_offset=-0.1, end_offset=0.1),
        'reset_pose_search_asset_setting': dict(asset_path=database, field='BaseCostBias'),
        'copy_pose_search_asset_setting': dict(asset_path=database, source_asset_path=next(p for p in owned if '/PSD2_' in p), field='BaseCostBias'),
        'add_pose_search_database_multi_animation': dict(asset_path=database, animation_path=interaction),
        'add_pose_search_default_channels': dict(asset_path=schema),
    }
    # No fixture exists for these in the project; the native guard must reject them.
    rejected = {
        'add_pose_search_database_composite': dict(asset_path=database, animation_path=JOG.format('Fwd')),
        'set_pose_search_role_mirror_table': dict(asset_path=schema, role=roles[0], mirror_table_path='/Game/Nope.Nope'),
        'set_pose_search_channel_vector': dict(C(head), field='HeadingAxis', x=1, y=0, z=0),
    }
    # Dry runs that the native guard still refuses because of fixture state.
    expected_refusal = {
        'add_pose_search_database_multi_animation': 'already exists',
        'add_pose_search_database_blend_space': 'already exists',
        'add_pose_search_default_channels': 'empty authored channel array',
        'add_pose_search_database_montage': None,
    }

    registered = {t.name for t in await mcp_server.mcp.list_tools() if 'pose_search' in t.name}
    covered = set(inspect) | set(dry) | set(rejected)
    assert registered == covered, ('uncovered', sorted(registered - covered), 'unknown', sorted(covered - registered))

    before = {p: api.call('GET', '/pose-search/databases/definition' if '/PSD' in p else '/pose-search/schemas/definition' if '/PSS' in p
                          else '/pose-search/normalization-sets/definition' if '/PSN_' in p else '/pose-search/interactions/definition',
                          params={'asset_path': p}) for p in owned}
    outcome = {}
    for tool, args in inspect.items():
        payload = await call(tool, args)
        assert 'errorMessage' not in payload, (tool, payload)
        outcome[tool] = 'inspect'
    for tool, args in dry.items():
        payload = await call(tool, {**args, **W})
        if 'errorMessage' in payload:
            hint = expected_refusal.get(tool, '__missing__')
            assert hint != '__missing__' and (hint is None or hint in payload['errorMessage']), (tool, payload)
            outcome[tool] = 'guard: ' + payload['errorMessage'][:80]
            continue
        assert payload.get('dry_run') is True, (tool, payload)
        outcome[tool] = 'dry-run'
    for tool, args in rejected.items():
        payload = await call(tool, {**args, **W})
        assert 'errorMessage' in payload, (tool, 'expected native rejection', payload)
        outcome[tool] = 'guard: ' + payload['errorMessage'][:80]
    after = {p: api.call('GET', '/pose-search/databases/definition' if '/PSD' in p else '/pose-search/schemas/definition' if '/PSS' in p
                         else '/pose-search/normalization-sets/definition' if '/PSN_' in p else '/pose-search/interactions/definition',
                         params={'asset_path': p}) for p in owned}
    for p in owned:
        a, b = dict(before[p]), dict(after[p])
        assert a == b, (p, 'dry runs changed the asset', sorted(k for k in a if a.get(k) != b.get(k)))
    print(json.dumps(outcome, indent=1))
    print(f'All {len(registered)} Pose Search MCP tools dispatched; dry runs left fixtures unchanged: OK')


if __name__ == '__main__':
    asyncio.run(run())
