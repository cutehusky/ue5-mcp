"""Required state/transition event descriptors and bound-payload removal guards."""
import argparse
import uuid
from state_tree_verification import StateTreeVerification

PAYLOAD = '/Script/StateTreeModule.StateTreeRandomConditionInstanceData'


def run(base, phase):
    test = StateTreeVerification('state_tree_required_events', base)
    if phase != 'prepare':
        if phase == 'verify':
            test.verify()
            print('Cold required event descriptors, native source IDs and payload bindings: OK')
        test.cleanup()
        return
    assert not test.manifest.exists()
    keep = False
    try:
        path, root = test.create('RequiredEvents')
        state = test.edit(path, 'POST', 'states', ParentId=root, Name='EventState')['selected_id']
        before = test.snapshots()
        args = dict(StateId=state, bSetRequiredEvent=True, bEnabled=True,
                    PayloadStructPath=PAYLOAD, bConsumeEvent=False)
        test.edit(path, 'PATCH', 'states', **args, bDryRun=True)
        assert test.snapshots() == before
        test.transaction_check(lambda: test.edit(path, 'PATCH', 'states', **args))
        row = test.state(path, state)
        source = row['event_source_id']
        assert uuid.UUID(source).int and row['requires_event']
        assert row['required_payload_struct'] == PAYLOAD and not row['consume_event']
        assert not test.edit(path, 'PATCH', 'states', **args)['would_change']
        task = test.edit(path, 'POST', 'nodes', StateId=state,
                         StructPath='/Script/StateTreeModule.StateTreeDelayTask',
                         InstanceProperties={'RandomDeviation': '0'},
                         Bindings=[{'SourceId': source, 'SourcePath': 'Payload.Threshold',
                                    'TargetId': '$new', 'TargetPath': 'Duration'}])['selected_id']
        test.reject(path, 'PATCH', 'states', StateId=state, bSetRequiredEvent=True, bEnabled=False)
        test.reject(path, 'PATCH', 'states', StateId=state, bSetRequiredEvent=True,
                    PayloadStructPath='/Script/CoreUObject.Vector')
        test.transaction_check(lambda: test.edit(path, 'PATCH', 'states', **(args | {'bConsumeEvent': True})))
        assert test.state(path, state)['event_source_id'] == source
        transition = test.edit(path, 'POST', 'transitions', StateId=state, Trigger='OnEvent',
                               PayloadStructPath=PAYLOAD, bConsumeEvent=False)['selected_id']
        tr = next(x for x in test.state(path, state)['transitions'] if x['id'] == transition)
        assert uuid.UUID(tr['event_source_id']).int and tr['payload_struct'] == PAYLOAD
        assert not tr['consume_event']
        condition = test.edit(path, 'POST', 'nodes', StateId=state, TransitionId=transition,
                              Kind='transition_condition',
                              StructPath='/Script/StateTreeModule.StateTreeRandomCondition',
                              Bindings=[{'SourceId': tr['event_source_id'], 'SourcePath': 'Payload.Threshold',
                                         'TargetId': '$new', 'TargetPath': 'Threshold'}])['selected_id']
        test.reject(path, 'PATCH', 'transitions', StateId=state, ItemId=transition,
                    Trigger='OnStateCompleted')
        for values in [{'PayloadStructPath': '/Script/Engine.Actor'},
                       {'PayloadStructPath': '/Script/Missing.Payload'},
                       {'EventTag': 'MCP.Definitely.Unregistered'}, {}]:
            test.reject(path, 'PATCH', 'states', StateId=state, bSetRequiredEvent=True,
                        bEnabled=True, **values)
        test.reject(path, 'POST', 'transitions', StateId=state, Trigger='OnStateCompleted',
                    PayloadStructPath=PAYLOAD)
        test.save()
        keep = True
        print('State/transition payload descriptors, consume flags, source GUIDs, bindings, removal/type guards and undo: OK')
    finally:
        if not keep:
            test.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    run(args.base, args.phase)
