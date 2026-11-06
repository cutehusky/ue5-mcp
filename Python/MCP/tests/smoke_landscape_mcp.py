"""Call every landscape MCP tool through the registered FastMCP dispatcher.

Builds a scratch map (before any asset) with a flat 2x2 landscape, a "Grass" paint layer and an extra edit layer
over REST. Read-only tools run for real, mutating tools (including create_landscape) as confirmed dry runs; the
landscape, edit layers, per-layer heights/weights and the layer info must be unchanged.
"""
import asyncio
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT, Api
import smoke_landscape_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server

BASE = 'http://127.0.0.1:8080'
LIVE = {'bConfirm': True, 'bDryRun': False}


async def run():
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    original = api.call('GET', '/worlds/inspect')['world_path']
    assert not original.startswith(live.MAP), 'scratch landscape map is open; run smoke_landscape_live.py cleanup'
    live.use_tag(uuid.uuid4().hex[:6])
    try:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        assert api.call('POST', '/worlds/create', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
        assert api.call('POST', '/worlds/load', {'WorldPath': live.MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
        assert api.call('GET', '/worlds/inspect')['world_path'].startswith(live.MAP)
        api.call('POST', '/landscapes/create', {'Name': 'MCP_Land', 'Width': 2, 'Height': 2, 'Value': 32768, 'LayerInfoPath': live.LI, 'FieldName': 'Grass', **LIVE})
        a = live.actor(api)
        api.call('POST', '/landscapes/edit-layers/create', {'ActorPath': a, 'Name': 'MCP_Edit', 'ExpectedLayerOrder': live.order(api), **LIVE})
        before = live.settled(api)
        l = live.layer(api, 'MCP_Edit')
        lr = dict(actor_path=a, edit_layer_guid=l['guid'], edit_layer_path=l['edit_layer_path'])
        rect = dict(x=10, y=12, width=2, height=2)
        li = api.call('POST', '/landscapes/layer-info/inspect', {'LayerInfoPath': live.LI})
        hz = [v for row in api.call('POST', '/landscapes/edit-layers/heights/inspect', {'ActorPath': a, 'EditLayerGuid': l['guid'], 'EditLayerPath': l['edit_layer_path'],
                                                                                         'X': 10, 'Y': 12, 'Width': 2, 'Height': 2})['raw_height_rows'] for v in row]
        wz = api.call('POST', '/landscapes/edit-layers/weights/inspect', {'ActorPath': a, 'EditLayerGuid': l['guid'], 'EditLayerPath': l['edit_layer_path'],
                                                                          'LayerInfoPath': live.LI, 'X': 10, 'Y': 12, 'Width': 2, 'Height': 2})
        wz = [v for row in wz.get('weight_rows', wz.get('raw_weight_rows')) for v in row]
        args = {
            'inspect_world_landscapes': {}, 'inspect_landscape_components': dict(actor_path=a), 'inspect_landscape_heights': dict(actor_path=a, **rect),
            'inspect_landscape_paint_layers': dict(actor_path=a), 'inspect_landscape_weights': dict(actor_path=a, layer_info_path=live.LI, **rect),
            'inspect_landscape_edit_layers': dict(actor_path=a), 'inspect_landscape_edit_layer_heights': dict(**lr, **rect),
            'inspect_landscape_edit_layer_weights': dict(**lr, layer_info_path=live.LI, **rect), 'inspect_landscape_layer_info': dict(layer_info_path=live.LI),
            'create_landscape': dict(label='MCP_Land2', components_x=1, components_y=1, x=50000),
            'create_landscape_edit_layer': dict(actor_path=a, name='MCP_New', expected_layer_order=live.order(api)),
            'delete_landscape_edit_layer': dict(**lr, expected_name='MCP_Edit', expected_layer_order=live.order(api)),
            'rename_landscape_edit_layer': dict(**lr, expected_name='MCP_Edit', name='MCP_Renamed'),
            'reorder_landscape_edit_layer': dict(**lr, expected_layer_order=live.order(api), destination_index=0),
            'set_landscape_edit_layer_bool': dict(**lr, field='Visible', expected_value=True, value=False),
            'set_landscape_edit_layer_alpha': dict(**lr, target='Heightmap', expected_value=1, value=0.5),
            'set_landscape_edit_layer_heights': dict(**lr, **rect, expected_heights=hz, heights=[33000] * 4),
            'set_landscape_edit_layer_weights': dict(**lr, layer_info_path=live.LI, **rect, expected_weights=wz, weights=[200] * 4),
            'set_landscape_layer_info_blend': dict(layer_info_path=live.LI, expected_method=li['blend_method'], expected_group=li['blend_group'], method=1, group='G'),
            'set_landscape_layer_info_scalar': dict(layer_info_path=live.LI, field='Hardness', expected_value=li['hardness'], value=0.75),
            'set_landscape_layer_info_asset': dict(layer_info_path=live.LI, field='PhysicalMaterial', expected_asset_path='', asset_path=live.PHYS),
            'set_landscape_layer_info_debug_color': dict(layer_info_path=live.LI, expected_color=li['debug_color_rgba'], color=[1, 0, 0, 1]),
            'set_landscape_layer_info_spline_mask': dict(layer_info_path=live.LI, expected_mask=li['spline_falloff_color_mask'], mask=1),
        }
        tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
        names = {t for t in tools if 'landscape' in t and 'foliage' not in t}
        assert names == set(args), sorted(names ^ set(args))
        assert len(args) == 23, len(args)
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
        after = live.settled(api)
        assert after == before, ('dry runs changed the landscape', [k for k in after if after[k] != before.get(k)])
        assert len(api.call('POST', '/landscapes/inspect', {})['landscape_proxies']) == 1, 'dry-run create added a landscape'
        guarded = {k: v for k, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} landscape MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); landscape unchanged')
        assert not guarded, guarded
    finally:
        httpx.post(BASE + '/worlds/load', json={'WorldPath': original, 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.MAP}, timeout=180)
        httpx.post(BASE + '/assets/delete', json={'AssetPath': live.LI}, timeout=180)


if __name__ == '__main__':
    asyncio.run(run())
