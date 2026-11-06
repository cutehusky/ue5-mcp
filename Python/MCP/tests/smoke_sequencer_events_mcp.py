"""Call the Level Sequence event MCP tools through the registered FastMCP dispatcher.

Builds the event sequence from smoke_sequencer_events_live (trigger keys, two endpoints, payloads, repeater, policy).
Inspection tools run for real, mutating tools as confirmed dry runs; keys, endpoints, payloads, repeater and policy must be unchanged.
"""
import asyncio
import json
import sys

from smoke_animation_curves_live import PROJECT, Api
import smoke_sequencer_events_live as live

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
import mcp_server
from merged_tool_names import use_old_names
use_old_names(mcp_server.mcp)


async def run():
    mcp_server.BASE_URL = live.BASE
    api = Api(live.BASE)
    e = live.Events(api)
    try:
        live.prepare(api)
        before, snap = live.state(e), e.snap()
        d = e.endpoints()
        director = dict(director_blueprint_path=d['director_blueprint_path'], director_blueprint_guid=d['director_blueprint_guid'])
        ep = before['keys'][0]['endpoint_path']
        rep_ep = before['repeater_endpoint']
        x, rx = e.endpoint(ep), e.endpoint(rep_ep)
        pin = {p['name']: p['guid'] for p in x['pins']}
        rep = e.repeater()
        k = dict(asset_path=live.SEQ, section_path=live.TRIG, channel_index=0, expected_section_class_path=live.TRIGGER_CLASS, expected_channel_snapshot=snap)
        rg = dict(asset_path=live.SEQ, section_path=live.REP, expected_section_class_path=live.REPEATER_CLASS, expected_repeater_snapshot=rep['repeater_snapshot'])
        node = dict(endpoint_guid=x['node_guid'], endpoint_snapshot=x['endpoint_snapshot'])
        pol = e.policy()
        args = {
            'discover_level_sequence_channels': dict(asset_path=live.SEQ, section_path=live.TRIG),
            'discover_level_sequence_event_endpoints': dict(asset_path=live.SEQ),
            'inspect_level_sequence_event_repeater': dict(asset_path=live.SEQ, section_path=live.REP),
            'level_sequence_event_keys': dict(**k, operation='KeyMove', key_index=2, expected_frame=6500, new_frame=7000),
            'create_level_sequence_event_endpoint': dict(**k, key_index=2, expected_frame=6500, expected_endpoint_path=ep, expected_director_exists=True,
                                                         **director, replace_existing_endpoint=True),
            'bind_level_sequence_event_endpoint': dict(**k, key_index=2, expected_frame=6500, expected_endpoint_path=ep, **director),
            'edit_level_sequence_event_payload': dict(**k, key_index=0, expected_frame=1500, payload_name='Label', operation='PayloadSet', **director, **node,
                                                      pin_guid=pin['Label'], value_text='bye', expected_exists=True, expected_text='hello'),
            'level_sequence_event_track_policy': dict(asset_path=live.SEQ, track_path=live.TRACK, field_name='bFireEventsWhenForwards', value=0, expected_value=1,
                                                      expected_class_path=pol['class_path'], expected_track_snapshot=pol['track_snapshot']),
            'level_sequence_event_repeater_endpoint': dict(**rg, operation='BindEndpoint', expected_endpoint_path=rep_ep, **director),
            'edit_level_sequence_repeater_payload': dict(**rg, payload_name='Tag', operation='PayloadRemove', **director, endpoint_guid=rx['node_guid'],
                                                         endpoint_snapshot=rx['endpoint_snapshot'], expected_exists=True, expected_text='tick'),
            'add_level_sequence_event_endpoint_pin': dict(asset_path=live.SEQ, **director, endpoint_path=ep, **node, pin_name='Speed', pin_type='double'),
            'remove_level_sequence_event_endpoint_pin': dict(asset_path=live.SEQ, **director, endpoint_path=ep, **node, pin_name='Label', pin_guid=pin['Label']),
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
            text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                raise AssertionError((name, 'non-JSON response', text[:300]))
            if isinstance(payload, dict) and 'errorMessage' in payload:
                outcome[name] = 'guard: ' + payload['errorMessage'][7:220]
                continue
            if 'dry_run' in props(name):
                assert payload.get('dry_run') is True and not payload.get('written') and not payload.get('removed'), (name, str(payload)[:300])
            outcome[name] = 'ok'
        assert live.state(e) == before and e.snap() == snap, 'dry runs changed events'
        guarded = {n: v for n, v in outcome.items() if v != 'ok'}
        print(json.dumps(guarded, indent=1))
        print(f'{len(args)} Sequencer event MCP tools dispatched ({len(args) - len(guarded)} ok, {len(guarded)} guard); events unchanged')
        assert not guarded, guarded
    finally:
        live.cleanup(api)


if __name__ == '__main__':
    asyncio.run(run())
