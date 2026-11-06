"""Call every PCG graph-structure MCP tool (part 1: graphs, nodes, edges, node/graph settings, subgraphs, IO pins,
comments, diagnostics) through the registered FastMCP dispatcher.

Builds two scratch graphs over REST (sampler, transform, filter-by-tag, spawn-actor and subgraph nodes, one edge, an
extra input pin, the subgraph pointing at the second graph). Read-only tools run for real, mutating tools as confirmed
dry runs; the graph (nodes, settings, pins, dependencies) must be unchanged and no dry run may create an asset.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_pcg_graph_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}
S = live.S
PART1 = {'inspect_pcg_graph', 'create_pcg_graph', 'duplicate_pcg_graph', 'discover_pcg_node_classes', 'add_pcg_node', 'edit_pcg_node_presentation',
         'duplicate_pcg_node', 'remove_pcg_node', 'edit_pcg_edge', 'inspect_pcg_node_settings', 'set_pcg_node_settings_scalar', 'set_pcg_node_settings_enum',
         'set_pcg_node_settings_text', 'set_pcg_node_settings_compound', 'reset_pcg_node_settings_field', 'set_pcg_node_settings_asset',
         'set_pcg_node_settings_string_array', 'validate_pcg_graph', 'set_pcg_subgraph', 'add_pcg_graph_pin', 'inspect_pcg_graph_pins', 'edit_pcg_graph_pins',
         'rename_pcg_graph_pin', 'configure_pcg_graph_pin', 'set_pcg_graph_pin_data_types', 'discover_pcg_data_classes', 'set_pcg_graph_settings_scalar',
         'set_pcg_graph_settings_enum', 'set_pcg_graph_settings_text', 'reset_pcg_graph_settings_field', 'inspect_pcg_graph_dependencies',
         'set_pcg_node_comment', 'set_pcg_node_comment_display'}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    tag = uuid.uuid4().hex[:6]
    live.use_tag(tag)
    G, G2 = live.G, live.G2
    n = lambda base: f'/Game/UE5MCP_Test/{base}_{tag}.{base}_{tag}'
    try:
        for p in (G, G2):
            api.call('POST', '/pcg/graphs', {'AssetPath': p, **LIVE})
        add = lambda cls, x: api.call('POST', '/pcg/graphs/nodes', {'AssetPath': G, 'SettingsClass': S + cls, 'NodeX': x, 'NodeY': 0, **LIVE})['node_path'].rsplit(':', 1)[1]
        smp, tfm, flt, spn, sub = (add('PCGSurfaceSamplerSettings', 0), add('PCGTransformPointsSettings', 300), add('PCGFilterByTagSettings', 600),
                                   add('PCGSpawnActorSettings', 900), add('PCGSubgraphSettings', 1200))
        a, b = live.node(api, smp), live.node(api, tfm)
        api.call('PATCH', '/pcg/graphs/edges', {'AssetPath': G, 'Action': 'connect', 'NodeIndex': a['index'], 'NodePath': a['path'], 'FromPin': a['output_pins'][0]['label'],
                                                'TargetNodeIndex': b['index'], 'TargetNodePath': b['path'], 'ToPin': b['input_pins'][0]['label'], **LIVE})
        io = live.node(api, 'input')
        api.call('POST', '/pcg/graphs/pins', {**live.nref(io), 'SettingsPath': io['settings_path'], 'RecordHash': live.pins(api, 'input')['record_hash'], 'FromPin': 'MCP_A', **LIVE})
        s = live.settings(api, sub)
        api.call('PATCH', '/pcg/graphs/nodes/subgraph', {**live.nref(live.node(api, sub)), 'SettingsPath': s['settings_path'], 'RecordHash': s['record_hash'], 'SourceAssetPath': G2, **LIVE})
        before = live.settled(api)
        nd = lambda name: live.node(api, name)
        nr = lambda name: dict(asset_path=G, node_index=nd(name)['index'], node_path=nd(name)['path'])
        sh = lambda name: dict(**nr(name), settings_path=live.settings(api, name)['settings_path'], record_hash=live.settings(api, name)['record_hash'])
        io = nd('input')
        pin = dict(asset_path=G, node_index=io['index'], node_path=io['path'], settings_path=io['settings_path'], record_hash=live.pins(api, 'input')['record_hash'])
        gh = dict(asset_path=G, record_hash=live.graph(api)['record_hash'])
        point = next(c['path'] for c in api.call('POST', '/pcg/data-classes', {})['classes'] if c['name'] == 'PCGPointData')
        args = {
            'inspect_pcg_graph': dict(asset_path=G), 'create_pcg_graph': dict(asset_path=n('PCG_McpNew')),
            'duplicate_pcg_graph': dict(source_asset_path=G, asset_path=n('PCG_McpDup')), 'discover_pcg_node_classes': {}, 'discover_pcg_data_classes': {},
            'add_pcg_node': dict(asset_path=G, settings_class=S + 'PCGDensityFilterSettings', x=0, y=400),
            'edit_pcg_node_presentation': dict(**nr(smp), action='move', x=50, y=50),
            'duplicate_pcg_node': dict(**nr(smp), x=0, y=600), 'remove_pcg_node': nr(flt),
            'edit_pcg_edge': dict(asset_path=G, action='disconnect', from_node_index=nd(smp)['index'], from_node_path=nd(smp)['path'], from_pin=nd(smp)['output_pins'][0]['label'],
                                  to_node_index=nd(tfm)['index'], to_node_path=nd(tfm)['path'], to_pin=nd(tfm)['input_pins'][0]['label']),
            'inspect_pcg_node_settings': nr(smp),
            'set_pcg_node_settings_scalar': dict(**sh(smp), field='PointsPerSquaredMeter', value=0.75),
            'set_pcg_node_settings_enum': dict(**sh(flt), field='Operation', value=[c for c in live.field(live.settings(api, flt), 'Operation').get('enum_choices', [])
                                                                                          if c != live.field(live.settings(api, flt), 'Operation')['value']][0]),
            'set_pcg_node_settings_text': dict(**sh(flt), field='SelectedTags', value='MCP'),
            'set_pcg_node_settings_compound': dict(**sh(smp), field='PointExtents', kind='vector', value={'X': 5, 'Y': 5, 'Z': 5}),
            'reset_pcg_node_settings_field': dict(**sh(smp), field='Looseness'),
            'set_pcg_node_settings_asset': dict(**sh(smp), field='DebugSettings.PointMesh', source_asset_path=live.MESH),
            'set_pcg_node_settings_string_array': dict(**sh(spn), field='PostSpawnFunctionNames', values=['Fn']),
            'validate_pcg_graph': dict(asset_path=G), 'inspect_pcg_graph_dependencies': dict(asset_path=G),
            'set_pcg_subgraph': dict(**sh(sub), source_asset_path=''),
            'add_pcg_graph_pin': dict(**pin, label='MCP_B'),
            'inspect_pcg_graph_pins': dict(asset_path=G, node_index=io['index'], node_path=io['path'], settings_path=io['settings_path']),
            'edit_pcg_graph_pins': dict(**pin, pin_index=1, pin_label='MCP_A', action='remove'),
            'rename_pcg_graph_pin': dict(**pin, pin_index=1, pin_label='MCP_A', new_label='MCP_R'),
            'configure_pcg_graph_pin': dict(**pin, pin_index=1, pin_label='MCP_A', allow_multiple_connections=False, allow_multiple_data=False, status='Required', tooltip='t'),
            'set_pcg_graph_pin_data_types': dict(**pin, pin_index=1, pin_label='MCP_A', data_classes=[point]),
            'set_pcg_graph_settings_scalar': dict(**gh, field='bIsEditorOnly', value=1),
            'set_pcg_graph_settings_enum': dict(**gh, field='HiGenGridSize', value='Grid128'),
            'set_pcg_graph_settings_text': dict(**gh, field='Title', value='MCP'),
            'reset_pcg_graph_settings_field': dict(**gh, field='bUse2DGrid'),
            'set_pcg_node_comment': dict(**nr(smp), comment='MCP comment'),
            'set_pcg_node_comment_display': dict(**nr(smp), visible=True, pinned=True),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        assert set(args) == PART1, sorted(set(args) ^ PART1)
        assert PART1 <= set(tools), sorted(PART1 - set(tools))
        props = lambda name: tools[name].inputSchema.get('properties', {})
        outcome = {}
        for name, a in args.items():
            a = dict(a)
            if 'dry_run' in props(name):
                a.update(dry_run=True)
            if 'confirm' in props(name):
                a.update(confirm=True)
            result = await mcp_server.mcp.call_tool(name, a)
            blocks = result[0] if isinstance(result, tuple) else result
            text = ''.join(b_.text for b_ in blocks if hasattr(b_, 'text'))
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
        assert after == before, ('dry runs changed the graph', live.diff(before, after)[:5])
        for created in ('PCG_McpNew', 'PCG_McpDup'):
            assert httpx.get(BASE + '/assets/describe', params={'asset_path': n(created)}, timeout=60).status_code >= 400, created
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} PCG graph MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); graph unchanged')
        assert not guarded, guarded
    finally:
        for p in (G, G2):
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
