"""Level Sequence event tracks, trigger keys, director endpoints, parameter pins, payloads and repeaters: prepare, restart, verify.

Usage: smoke_sequencer_events_live.py prepare|verify|cleanup. Builds a saved Level Sequence with a master event track holding a
trigger section and a repeater section. Trigger keys are added, given a newly created director endpoint, bound to an existing
endpoint, given Int/String payloads, moved, duplicated, offset and deleted; the repeater gets its own endpoint and payload; the
track's firing policy is edited and an endpoint parameter is removed. Every mutation is first sent with a stale snapshot
(rejected) and as a dry run (state unchanged). Keys, payloads, endpoints, repeater and policy must survive a cold editor restart.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

BASE = 'http://127.0.0.1:8080'
PKG = '/Game/UE5MCP_Test/LS_MCP_Events'
SEQ = PKG + '.LS_MCP_Events'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'sequencer_events.json'
MS = SEQ + ':MovieScene_0.'
TRACK = MS + 'MovieSceneEventTrack_0'
TRIG = TRACK + '.MovieSceneEventTriggerSection_0'
REP = TRACK + '.MovieSceneEventRepeaterSection_0'
KP = '/level-sequences/channels/key-policy'
REPEATER = '/level-sequences/events/repeater'
POLICY = '/level-sequences/events/track-policy'
DISCOVER = '/level-sequences/events/endpoints/discover'
PIN_ADD = '/level-sequences/events/endpoints/pins/add'
PIN_REMOVE = '/level-sequences/events/endpoints/pins/remove'
TRIGGER_CLASS = '/Script/MovieSceneTracks.MovieSceneEventTriggerSection'
REPEATER_CLASS = '/Script/MovieSceneTracks.MovieSceneEventRepeaterSection'
# Fields that the director compiler regenerates; endpoint identity and payloads are what must persist.
STABLE = ('frame', 'endpoint_path', 'bound_object_pin_name', 'payload_variable_count')


class Events:
    def __init__(self, api):
        self.api = api

    def snap(self):
        page = self.api.call('POST', '/level-sequences/channels/discover', {'AssetPath': SEQ, 'ExpressionPath': TRIG, 'Start': 0, 'Count': 128})
        assert page['section_class_path'] == TRIGGER_CLASS and page['event_channel_count'] == 1, page
        ch = page['channels'][0]
        assert ch['channel_type'] == 'Event' and not ch['supports_default'], ch
        return ch['native_channel_snapshot']

    def keys(self):
        return self.api.call('POST', KP, {'AssetPath': SEQ, 'ExpressionPath': TRIG, 'Name': 'Event', 'Start': 0,
                                          'FieldName': 'Keys', 'BlockIndex': 0, 'Count': 128})['keys']

    def base(self, body):
        return {'AssetPath': SEQ, 'ExpressionPath': TRIG, 'Name': 'Event', 'Start': 0, 'ExpectedClassPath': TRIGGER_CLASS,
                'ExpectedAssetSnapshot': self.snap(), 'bConfirm': True, **body}

    def edit(self, body, route=KP, changes=True):
        """Stale snapshot and wrong class rejected, dry run leaves the channel alone, then the real edit."""
        base = self.base(body)
        self.api.call('POST', route, {**base, 'ExpectedAssetSnapshot': base['ExpectedAssetSnapshot'] + ' '}, ok=False)
        self.api.call('POST', route, {**base, 'ExpectedClassPath': REPEATER_CLASS}, ok=False)
        self.api.call('POST', route, {**base, 'bDryRun': True})
        assert self.snap() == base['ExpectedAssetSnapshot'], (body, 'dry run changed channel')
        done = self.api.call('POST', route, {**base, 'bDryRun': False})
        assert (self.snap() != base['ExpectedAssetSnapshot']) == changes, (body, changes, done)
        return done

    def bad(self, body, route=KP):
        before = self.snap()
        self.api.call('POST', route, {**self.base(body), 'bDryRun': False}, ok=False)
        assert self.snap() == before, (body, 'rejected edit changed channel')

    def endpoints(self):
        return self.api.call('POST', DISCOVER, {'AssetPath': SEQ, 'Start': 0, 'Count': 128})

    def endpoint(self, path):
        return next(e for e in self.endpoints()['endpoints'] if e['node_path'] == path)

    def director(self):
        d = self.endpoints()
        return {'OwnerAssetPath': d['director_blueprint_path'], 'ActorGuid': d['director_blueprint_guid']}

    def repeater(self):
        return self.api.call('POST', REPEATER, {'AssetPath': SEQ, 'ExpressionPath': REP, 'FieldName': 'Inspect', 'BlockIndex': 0, 'Count': 128})

    def rep_edit(self, body):
        r = self.repeater()
        base = {'AssetPath': SEQ, 'ExpressionPath': REP, 'ExpectedClassPath': REPEATER_CLASS, 'ExpectedAssetSnapshot': r['repeater_snapshot'], 'bConfirm': True, **body}
        self.api.call('POST', REPEATER, {**base, 'ExpectedAssetSnapshot': r['repeater_snapshot'] + ' '}, ok=False)
        self.api.call('POST', REPEATER, {**base, 'bDryRun': True})
        assert self.repeater()['repeater_snapshot'] == r['repeater_snapshot'], (body, 'dry run changed repeater')
        done = self.api.call('POST', REPEATER, {**base, 'bDryRun': False})
        assert self.repeater()['repeater_snapshot'] != r['repeater_snapshot'], (body, done)
        return done

    def add_pin(self, path, name, kind):
        e = self.endpoint(path)
        body = {'AssetPath': SEQ, **self.director(), 'SourceTexturePath': path, 'ExpectedSourceId': e['node_guid'],
                'ExpectedDestinationSnapshot': e['endpoint_snapshot'], 'OutputName': name, 'Name': kind, 'bConfirm': True}
        self.api.call('POST', PIN_ADD, {**body, 'ExpectedDestinationSnapshot': e['endpoint_snapshot'] + ' '}, ok=False)
        self.api.call('POST', PIN_ADD, {**body, 'Name': 'map'}, ok=False)
        self.api.call('POST', PIN_ADD, {**body, 'bDryRun': True})
        assert self.endpoint(path)['endpoint_snapshot'] == e['endpoint_snapshot'], 'pin dry run changed endpoint'
        self.api.call('POST', PIN_ADD, {**body, 'bDryRun': False})
        pin = next(p for p in self.endpoint(path)['pins'] if p['name'] == name)
        assert pin['direction'] == 1, pin
        return pin

    def pin_remove(self, path, name, dry_run, allow=False, expect=None):
        e = self.endpoint(path)
        pin = next(p for p in e['pins'] if p['name'] == name)
        body = {'AssetPath': SEQ, **self.director(), 'SourceTexturePath': path, 'ExpectedSourceId': e['node_guid'],
                'ExpectedDestinationSnapshot': e['endpoint_snapshot'], 'OutputName': name, 'ExpectedOtherSourceId': pin['guid'],
                'bEnabled': allow, 'bConfirm': True, 'bDryRun': dry_run, **(expect or {})}
        return self.api.call('POST', PIN_REMOVE, body)

    def payload(self, path, name, op, text='', exists=False, prior='', key=0, frame=1000):
        e = self.endpoint(path)
        pin = next((p for p in e['pins'] if p['name'] == name), {'guid': ''})
        return {'FieldName': op, 'MipIndex': key, 'ExpectedSizeX': frame, **self.director(), 'ExpectedSourceId': e['node_guid'],
                'ExpectedDestinationSnapshot': e['endpoint_snapshot'], 'ExpectedOtherSourceId': pin['guid'], 'ExpectedLabel': name,
                'OutputName': text, 'bExpectedEnabled': exists, 'ExpectedOutputName': prior}

    def policy(self):
        return self.api.call('POST', POLICY, {'AssetPath': SEQ, 'ExpressionPath': TRACK, 'FieldName': 'Inspect'})

    def set_policy(self, field, value, prior):
        p = self.policy()
        body = {'AssetPath': SEQ, 'ExpressionPath': TRACK, 'FieldName': field, 'Value': value, 'ExpectedValue': prior,
                'ExpectedClassPath': p['class_path'], 'ExpectedAssetSnapshot': p['track_snapshot'], 'bConfirm': True}
        self.api.call('POST', POLICY, {**body, 'ExpectedValue': 1 - prior if field != 'EventPosition' else prior + 1}, ok=False)
        self.api.call('POST', POLICY, {**body, 'bDryRun': True})
        assert self.policy()['track_snapshot'] == p['track_snapshot'], 'policy dry run changed track'
        self.api.call('POST', POLICY, {**body, 'bDryRun': False})


def state(e):
    keys = [{k: x[k] for k in STABLE} | {'payloads': sorted((v['name'], v['value_text']) for v in x['payload_variables'])} for x in e.keys()]
    r = e.repeater()
    pol = e.policy()
    eps = {x['node_path']: sorted(p['name'] for p in x['pins']) for x in e.endpoints()['endpoints']}
    return {'keys': keys, 'repeater_endpoint': r['endpoint_path'], 'repeater_payloads': sorted((v['name'], v['value_text']) for v in r['payload_variables']),
            'policy': [pol['fire_forwards'], pol['fire_backwards'], pol['event_position']], 'endpoints': eps}


def prepare(api):
    e = Events(api)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    assert httpx.post(BASE + '/level-sequences/create', json={'AssetPath': PKG}, timeout=180).text == PKG
    assert api.call('POST', '/level-sequences/tracks', {'AssetPath': SEQ, 'Operation': 'add', 'TrackClass': 'event'})['track_index'] == 0
    api.call('POST', '/level-sequences/sections', {'AssetPath': SEQ, 'Operation': 'add', 'TrackIndex': 0, 'Frame': 0, 'EndFrame': 30000, 'EventSectionType': 'bogus'}, ok=False)
    api.call('POST', '/level-sequences/sections', {'AssetPath': SEQ, 'Operation': 'add', 'TrackIndex': 0, 'Frame': 0, 'EndFrame': 30000})
    api.call('POST', '/level-sequences/sections', {'AssetPath': SEQ, 'Operation': 'add', 'TrackIndex': 0, 'Frame': 0, 'EndFrame': 30000, 'EventSectionType': 'repeater', 'RowIndex': 1})
    assert e.snap() == '()' and e.repeater()['endpoint_path'] == 'None'
    assert not e.endpoints()['director_blueprint_exists']

    # Empty keys, then reject occupied/outside frames.
    for frame in (1000, 5000):
        e.edit({'FieldName': 'KeyAdd', 'SizeX': frame})
    e.bad({'FieldName': 'KeyAdd', 'SizeX': 5000})
    e.bad({'FieldName': 'KeyAdd', 'SizeX': 999999})
    assert [(k['frame'], k['endpoint_path']) for k in e.keys()] == [(1000, 'None'), (5000, 'None')]

    # Create the director and a blank endpoint on key 0; a dry run must not create the director.
    e.bad({'FieldName': 'CreateEndpoint', 'MipIndex': 0, 'ExpectedSizeX': 1000, 'ExpectedTargetPath': 'None', 'bExpectedEnabled': True})
    created = e.edit({'FieldName': 'CreateEndpoint', 'MipIndex': 0, 'ExpectedSizeX': 1000, 'ExpectedTargetPath': 'None', 'bExpectedEnabled': False})
    assert created['director_compiled'] and created['endpoint_created'], created
    ep = created['endpoint_path']
    assert e.endpoints()['endpoint_count'] == 1
    k0 = e.keys()[0]
    assert k0['endpoint_path'] == ep and k0['compiled_function_path'] != 'None', k0
    # A second create without the replacement opt-in is refused.
    e.bad({'FieldName': 'CreateEndpoint', 'MipIndex': 0, 'ExpectedSizeX': 1000, 'ExpectedTargetPath': ep, 'bExpectedEnabled': True, **e.director()})

    # Parameter pins: Int and String for payloads, Extra to remove later.
    e.add_pin(ep, 'Count', 'int')
    e.add_pin(ep, 'Label', 'string')
    e.add_pin(ep, 'Extra', 'float')
    assert {'Count', 'Label', 'Extra'} <= {p['name'] for p in e.endpoint(ep)['pins']}

    # Bind key 1 to the existing endpoint, then clear and re-bind.
    def bind(key, frame, prior, path):
        x = e.endpoint(ep)
        return {'FieldName': 'BindEndpoint', 'MipIndex': key, 'ExpectedSizeX': frame, 'ExpectedTargetPath': prior, **e.director(),
                'SourceTexturePath': path, 'ExpectedSourceId': x['node_guid'] if path else '', 'ExpectedDestinationSnapshot': x['endpoint_snapshot'] if path else ''}
    e.bad({**bind(1, 5000, 'None', ep), 'ExpectedSourceId': '00000000000000000000000000000000'})
    e.edit(bind(1, 5000, 'None', ep))
    assert e.keys()[1]['endpoint_path'] == ep
    e.edit(bind(1, 5000, ep, ''))
    assert e.keys()[1]['endpoint_path'] == 'None'
    e.edit(bind(1, 5000, 'None', ep))

    # Payloads on key 0: invalid Int text rejected, set Int and String, overwrite, remove Label from key 1.
    e.bad(e.payload(ep, 'Count', 'PayloadSet', 'abc'))
    e.bad(e.payload(ep, 'Missing', 'PayloadSet', '1'))
    e.edit(e.payload(ep, 'Count', 'PayloadSet', '42'))
    e.edit(e.payload(ep, 'Label', 'PayloadSet', 'hello'))
    e.bad(e.payload(ep, 'Count', 'PayloadSet', '7', exists=True, prior='41'))
    e.edit(e.payload(ep, 'Count', 'PayloadSet', '7', exists=True, prior='42'))
    e.edit(e.payload(ep, 'Label', 'PayloadSet', 'tmp', key=1, frame=5000))
    e.edit(e.payload(ep, 'Label', 'PayloadRemove', exists=True, prior='tmp', key=1, frame=5000))
    k = e.keys()
    assert k[0]['payload_variable_count'] == 2 and k[1]['payload_variable_count'] == 0, k

    # Move, duplicate (payload copied, endpoint shared), offset, delete.
    e.bad({'FieldName': 'KeyMove', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'SizeX': 1000})
    e.edit({'FieldName': 'KeyMove', 'MipIndex': 1, 'ExpectedSizeX': 5000, 'SizeX': 6000})
    e.edit({'FieldName': 'KeyDuplicate', 'MipIndex': 0, 'ExpectedSizeX': 1000, 'SizeX': 3000})
    k = e.keys()
    assert [x['frame'] for x in k] == [1000, 3000, 6000] and k[1]['endpoint_path'] == ep and k[1]['payload_variables'] == k[0]['payload_variables'], k
    e.edit({'MipIndex': 0, 'ExpectedSizeX': 1000, 'SizeX': 8000}, route='/level-sequences/channels/duplicate-key')
    e.bad({'SizeX': 10 ** 7}, route='/level-sequences/channels/offset')
    e.edit({'SizeX': 500}, route='/level-sequences/channels/offset')
    k = e.keys()
    assert [x['frame'] for x in k] == [1500, 3500, 6500, 8500] and k[3]['payload_variables'] == k[0]['payload_variables'], k
    e.edit({'FieldName': 'KeyDelete', 'MipIndex': 3, 'ExpectedSizeX': 8500})
    assert [x['frame'] for x in e.keys()] == [1500, 3500, 6500]

    # Repeater: its own endpoint on the existing director, a String payload.
    rc = e.rep_edit({'FieldName': 'CreateEndpoint', 'ExpectedTargetPath': 'None', 'bExpectedEnabled': True, **e.director()})
    rep_ep = rc['endpoint_path'] if 'endpoint_path' in rc else e.repeater()['endpoint_path']
    assert rep_ep not in ('None', ep) and e.endpoints()['endpoint_count'] == 2, rc
    e.add_pin(rep_ep, 'Tag', 'string')
    x = e.endpoint(rep_ep)
    pin = next(p for p in x['pins'] if p['name'] == 'Tag')
    rp = {'FieldName': 'PayloadSet', **e.director(), 'ExpectedSourceId': x['node_guid'], 'ExpectedDestinationSnapshot': x['endpoint_snapshot'],
          'ExpectedOtherSourceId': pin['guid'], 'ExpectedLabel': 'Tag', 'OutputName': 'tick', 'bExpectedEnabled': False}
    e.rep_edit(rp)
    r = e.repeater()
    assert r['payload_count'] == 1 and r['payload_variables'][0]['name'] == 'Tag', r
    # Repeater BindEndpoint: clear, bind to the trigger endpoint, then replace with its own endpoint (opt-in) and restore the payload.
    def rbind(prior, path, **kw):
        x = e.endpoint(path) if path else None
        return {'FieldName': 'BindEndpoint', 'ExpectedTargetPath': prior, 'bExpectedEnabled': True, **e.director(), 'SourceTexturePath': path,
                'ExpectedSourceId': x['node_guid'] if x else '', 'ExpectedDestinationSnapshot': x['endpoint_snapshot'] if x else '', **kw}
    e.rep_edit(rbind(rep_ep, ''))
    assert e.repeater()['endpoint_path'] == 'None', e.repeater()
    e.rep_edit(rbind('None', ep))
    assert e.repeater()['endpoint_path'] == ep
    e.rep_edit(rbind(ep, rep_ep, bEnabled=True))
    assert e.repeater()['endpoint_path'] == rep_ep
    if e.repeater()['payload_count'] == 0:
        x = e.endpoint(rep_ep)
        e.rep_edit({**rp, 'ExpectedSourceId': x['node_guid'], 'ExpectedDestinationSnapshot': x['endpoint_snapshot']})
    assert e.repeater()['payload_variables'][0]['name'] == 'Tag', e.repeater()

    # Track firing policy.
    p = e.policy()
    assert (p['fire_forwards'], p['fire_backwards']) == (True, True), p
    e.set_policy('bFireEventsWhenBackwards', 0, 1)
    e.set_policy('EventPosition', 0, p['event_position'])
    p = e.policy()
    assert (p['fire_forwards'], p['fire_backwards'], p['event_position']) == (True, False, 0), p

    # Parameter removal: Count carries payloads, so the preflight reports the affected keys and apply needs the opt-in;
    # Extra has no uses and is removed outright.
    pre = e.pin_remove(ep, 'Count', True)
    assert pre['requires_breakage_opt_in'] and len(pre['affected_event_ids']) == 2, pre
    expect = {'ExpectedComponentPaths': pre['linked_pin_ids'], 'ExpectedSourcePaths': pre['affected_event_ids'], 'ExpectedSettingTexts': pre['affected_event_snapshots']}
    before = e.snap()
    api.call('POST', PIN_REMOVE, {'AssetPath': SEQ, **e.director(), 'SourceTexturePath': ep, 'ExpectedSourceId': e.endpoint(ep)['node_guid'],
                                  'ExpectedDestinationSnapshot': e.endpoint(ep)['endpoint_snapshot'], 'OutputName': 'Count',
                                  'ExpectedOtherSourceId': next(p for p in e.endpoint(ep)['pins'] if p['name'] == 'Count')['guid'],
                                  'bEnabled': False, 'bConfirm': True, 'bDryRun': False, **expect}, ok=False)
    assert e.snap() == before
    # Applied with the opt-in: the pin goes and its payloads are cleaned from the affected keys.
    pre = e.pin_remove(ep, 'Count', True)
    expect = {'ExpectedComponentPaths': pre['linked_pin_ids'], 'ExpectedSourcePaths': pre['affected_event_ids'], 'ExpectedSettingTexts': pre['affected_event_snapshots']}
    api.call('POST', PIN_REMOVE, {'AssetPath': SEQ, **e.director(), 'SourceTexturePath': ep, 'ExpectedSourceId': e.endpoint(ep)['node_guid'],
                                  'ExpectedDestinationSnapshot': e.endpoint(ep)['endpoint_snapshot'], 'OutputName': 'Count',
                                  'ExpectedOtherSourceId': next(p for p in e.endpoint(ep)['pins'] if p['name'] == 'Count')['guid'],
                                  'bEnabled': True, 'bConfirm': True, 'bDryRun': False, **expect})
    assert 'Count' not in {p['name'] for p in e.endpoint(ep)['pins']}
    assert all('Count' not in {v['name'] for v in k['payload_variables']} for k in e.keys()), e.keys()
    pre = e.pin_remove(ep, 'Extra', True)
    assert not pre['requires_breakage_opt_in'], pre
    assert e.pin_remove(ep, 'Extra', False)['removed']
    assert 'Extra' not in {p['name'] for p in e.endpoint(ep)['pins']}

    api.call('POST', '/assets/save', {'AssetPath': PKG})
    s = state(e)
    assert s['keys'][0]['payloads'] == s['keys'][1]['payloads'] == [('Label', 'hello')] and s['repeater_payloads'] == [('Tag', 'tick')], s
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))
    print(json.dumps(s, indent=1))
    print('event track, 3 trigger keys, 2 endpoints, payloads, repeater and policy prepared; saved')


def verify(api):
    e = Events(api)
    want = json.loads(STATE.read_text())
    got = json.loads(json.dumps(state(e)))
    assert got == want, (got, want)
    k = e.keys()
    assert all(x['compiled_function_path'] != 'None' for x in k), k
    print(f'event keys, endpoints, payloads, repeater and track policy identical after cold reload ({len(k)} keys)')
    cleanup(api)


def cleanup(api):
    httpx.post(BASE + '/assets/delete', json={'AssetPath': PKG}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[sys.argv[1]](Api(BASE))
