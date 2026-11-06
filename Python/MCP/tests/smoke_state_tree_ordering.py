"""StateTree node/transition ordering, retained bindings, undo and cold reload."""
import argparse
import json
import uuid

import httpx
from smoke_navigation_mesh import PROJECT

STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'state_tree_ordering.json'


def run(base, phase):
    def call(method, route, body=None, **params):
        response = httpx.request(method, base + route, json=body, params=params, timeout=180)
        assert response.is_success, (response.status_code, response.text)
        return response.json()

    def inspect():
        return call('GET', '/state-trees/inspect', asset_path=path)

    def edit(method, route, **values):
        return call(method, '/state-trees/' + route, {'AssetPath': path} | values)

    def stable(snapshot):
        return {key: value for key, value in snapshot.items() if key not in
                ['affected_assets', 'selected_id', 'would_change', 'dry_run', 'saved',
                 'diagnostics', 'validation_compiled_copy']}

    def reject(route, **values):
        before = inspect()
        response = httpx.post(base + '/state-trees/' + route,
                              json={'AssetPath': path} | values, timeout=180)
        assert response.status_code >= 400, (response.status_code, response.text)
        assert inspect() == before, 'Rejected move changed source'

    def cleanup():
        call('POST', '/assets/delete', {'AssetPath': path})
        STATE.unlink(missing_ok=True)

    if phase in ['verify', 'cleanup']:
        saved = json.loads(STATE.read_text())
        path = saved['path']
        if phase == 'verify':
            snapshot = inspect()
            assert stable(snapshot) == saved['snapshot'], (snapshot, saved['snapshot'])
            assert snapshot['ready_to_run'] and not snapshot['dirty']
            assert snapshot['editor_hash'] == snapshot['compiled_hash']
            before = inspect()
            assert call('GET', '/state-trees/validate', asset_path=path)['diagnostics'].startswith('success')
            assert inspect() == before
            print('Cold node/transition order, GUIDs, bindings and compiled data: OK')
        cleanup()
        return

    assert not STATE.exists(), 'Verify or clean the prior ordering fixture'
    path = None
    keep = False
    try:
        created = call('POST', '/state-trees/create',
                       {'AssetPath': '/Game/UE5MCP_Test/ST_Ordering_' + uuid.uuid4().hex[:8]})
        path = created['asset_path']
        root = created['states'][0]['id']
        edit('PATCH', 'states', StateId=root, Properties={'SelectionBehavior': 'TrySelectChildrenWithHighestUtility'})
        child = edit('POST', 'states', ParentId=root, Name='Ordered')['selected_id']
        edit('POST', 'parameters', Name='Duration', ParameterType='Float', bSetValue=True, Value='0.02')
        tasks = []
        for duration in ['0.02', '0.03', '0.04']:
            tasks.append(edit('POST', 'nodes', StateId=child,
                              StructPath='/Script/StateTreeModule.StateTreeDelayTask',
                              InstanceProperties={'Duration': duration, 'RandomDeviation': '0'})['selected_id'])
        edit('POST', 'bindings', Binding={'SourceId': 'root', 'SourcePath': 'Duration',
                                         'TargetId': tasks[0], 'TargetPath': 'Duration'})
        transitions = []
        for _ in range(3):
            transition = edit('POST', 'transitions', StateId=child)['selected_id']
            transitions.append(transition)
            edit('POST', 'nodes', StateId=child, Kind='transition_condition', TransitionId=transition,
                 StructPath='/Script/StateTreeModule.StateTreeRandomCondition',
                 InstanceProperties={'Threshold': '1'})

        def state(snapshot):
            return next(row for row in snapshot['states'] if row['id'] == child)

        cases = [
            ('nodes/move', 'tasks', tasks, {'Kind': 'task'}),
            ('transitions/move', 'transitions', transitions, {}),
        ]
        for kind, collection, struct, properties, extra in [
            ('global_task', 'global_tasks', 'StateTreeDelayTask', {'Duration': '10', 'RandomDeviation': '0'}, {}),
            ('enter_condition', 'enter_conditions', 'StateTreeRandomCondition', {'Threshold': '1'}, {}),
            ('consideration', 'considerations', 'StateTreeConstantConsideration', {'Constant': '0.5'}, {}),
            ('transition_condition', 'conditions', 'StateTreeRandomCondition', {'Threshold': '1'},
             {'TransitionId': transitions[0]}),
        ]:
            identities = [edit('POST', 'nodes', StateId=child, Kind=kind,
                               StructPath='/Script/StateTreeModule.' + struct,
                               InstanceProperties=properties, **extra)['selected_id'] for _ in range(3)]
            if collection == 'conditions':
                # Include the condition that was already attached to this transition.
                identities = [row['id'] for row in state(inspect())['transitions'][0]['conditions']]
            cases.append(('nodes/move', collection, identities, {'Kind': kind} | extra))

        for route, collection, identities, extra in cases:
            def selected(snapshot):
                if collection == 'global_tasks':
                    return snapshot[collection]
                if collection == 'conditions':
                    return next(row for row in state(snapshot)['transitions']
                                if row['id'] == extra['TransitionId'])['conditions']
                return state(snapshot)[collection]

            before = inspect()
            rows = selected(before)
            by_id = {row['id']: row for row in rows}
            assert not edit('POST', route, StateId=child, ItemId=identities[0], Index=0, **extra)['would_change']
            edit('POST', route, StateId=child, ItemId=identities[0], Index=-1, bDryRun=True, **extra)
            assert inspect() == before
            for invalid in [-2, len(identities), 100]:
                reject(route, StateId=child, ItemId=identities[0], Index=invalid, **extra)
            if collection != 'global_tasks':
                reject(route, StateId=root, ItemId=identities[0], Index=0, **extra)
            reject(route, StateId=child, ItemId=str(uuid.uuid4()), Index=0, **extra)
            for index, expected in [(-1, identities[1:] + identities[:1]),
                                    (0, identities), (1, identities[1:2] + identities[:1] + identities[2:])]:
                previous = inspect()
                edit('POST', route, StateId=child, ItemId=identities[0], Index=index, **extra)
                after = inspect()
                moved = selected(after)
                assert [row['id'] for row in moved] == expected
                assert {row['id']: row for row in moved} == by_id
                assert after['bindings'] == before['bindings']
                call('POST', '/editor/transactions/undo')
                assert stable(inspect()) == stable(previous)
                call('POST', '/editor/transactions/redo')
                assert stable(inspect()) == stable(after)
            print(collection + ' ordering, GUID/content/binding retention, guards and undo/redo: OK')
        reject('nodes/move', StateId=child, Kind='single_task', ItemId=tasks[0], Index=0)
        edit('POST', 'compile', bSave=True)
        snapshot = inspect()
        assert snapshot['ready_to_run'] and not snapshot['dirty']
        assert snapshot['editor_hash'] == snapshot['compiled_hash']
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'path': path, 'snapshot': stable(snapshot)}, indent=2))
        keep = True
        print('Ordering fixture compiled and saved for fresh-editor verification: OK')
    finally:
        if path and not keep:
            cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    run(args.base, args.phase)
