"""Native single-task slot REST lifecycle and fresh-editor persistence."""
import argparse
import json
import uuid

import httpx
from smoke_navigation_mesh import PROJECT

STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'state_tree_single_task.json'
SCHEMA = '/Script/UE5_MCP.MCPVerificationSingleTaskSchema'


def run(base, phase):
    def call(method, route, body=None, **params):
        response = httpx.request(method, base + route, json=body, params=params, timeout=180)
        assert response.is_success, (response.status_code, response.text)
        return response.json()

    def inspect(path):
        return call('GET', '/state-trees/inspect', asset_path=path)

    def edit(path, method, route, **values):
        return call(method, '/state-trees/' + route, {'AssetPath': path} | values)

    def stable(snapshot):
        return {key: value for key, value in snapshot.items() if key not in
                ['affected_assets', 'selected_id', 'would_change', 'dry_run', 'saved',
                 'diagnostics', 'validation_compiled_copy']}

    def reject(path, method, route, **values):
        before = inspect(path)
        response = httpx.request(method, base + '/state-trees/' + route,
                                 json={'AssetPath': path} | values, timeout=180)
        assert response.status_code >= 400, (response.status_code, response.text)
        assert inspect(path) == before

    def cleanup(paths):
        for path in reversed(paths):
            call('POST', '/assets/delete', {'AssetPath': path})
        STATE.unlink(missing_ok=True)

    if phase in ['verify', 'cleanup']:
        saved = json.loads(STATE.read_text())
        if phase == 'verify':
            for path in saved['paths']:
                snapshot = inspect(path)
                assert stable(snapshot) == saved['snapshots'][path], path
                assert snapshot['ready_to_run'] and not snapshot['dirty']
                assert snapshot['editor_hash'] == snapshot['compiled_hash']
                assert call('GET', '/state-trees/validate', asset_path=path)['diagnostics'].startswith('success')
                assert inspect(path) == snapshot
            print('Cold single-task schemas, slot IDs/settings, bindings and compiled data: OK')
        cleanup(saved['paths'])
        return

    assert not STATE.exists(), 'Verify or clean the prior single-task fixture'
    paths = []
    keep = False
    try:
        def create(schema):
            result = call('POST', '/state-trees/create', {
                'AssetPath': '/Game/UE5MCP_Test/ST_SingleREST_' + uuid.uuid4().hex[:8],
                'SchemaPath': schema})
            paths.append(result['asset_path'])
            return result['asset_path'], result['states'][0]['id']

        path, root = create(SCHEMA)
        default, default_root = create('/Script/GameplayStateTreeModule.StateTreeComponentSchema')
        dependency, _ = create(SCHEMA)
        child = edit(path, 'POST', 'states', ParentId=root, Name='Work')['selected_id']

        def slot():
            row = next(state for state in inspect(path)['states'] if state['id'] == child)
            assert row['tasks'] == []
            return row['single_task']

        assert slot() == []
        edit(path, 'POST', 'parameters', Name='Duration', ParameterType='Float', bSetValue=True, Value='0.04')
        common = {'StateId': child, 'Kind': 'single_task'}
        struct = '/Script/StateTreeModule.StateTreeDelayTask'
        bindings = [{'SourceId': 'root', 'SourcePath': 'Duration', 'TargetId': '$new', 'TargetPath': 'Duration'}]
        before = inspect(path)
        edit(path, 'POST', 'nodes', **common, StructPath=struct, Bindings=bindings, bDryRun=True)
        assert inspect(path) == before
        task = edit(path, 'POST', 'nodes', **common, StructPath=struct, Bindings=bindings,
                    InstanceProperties={'RandomDeviation': '0'})['selected_id']
        assert len(slot()) == 1 and slot()[0]['id'] == task and inspect(path)['binding_count'] == 1
        created = inspect(path)
        call('POST', '/editor/transactions/undo')
        assert slot() == [] and inspect(path)['binding_count'] == 0
        call('POST', '/editor/transactions/redo')
        assert stable(inspect(path)) == stable(created)
        reject(path, 'POST', 'nodes', **common, StructPath=struct)
        reject(default, 'POST', 'nodes', StateId=default_root, Kind='single_task', StructPath=struct)
        reject(path, 'POST', 'nodes', StateId=child, Kind='task', StructPath=struct)
        for method in ['PATCH', 'DELETE']:
            for index in [-2, 1, 99]:
                reject(path, method, 'nodes', **common, ItemId=task, Index=index, bConfirm=True)
            reject(path, method, 'nodes', **common, ItemId=str(uuid.uuid4()), bConfirm=True)
        reject(path, 'POST', 'nodes/move', **common, ItemId=task, Index=0)
        for kind, extra in [('Group', {}), ('LinkedAsset', {'LinkedAssetPath': dependency})]:
            state = edit(path, 'POST', 'states', ParentId=root, Name=kind, StateType=kind, **extra)['selected_id']
            reject(path, 'POST', 'nodes', StateId=state, Kind='single_task', StructPath=struct)
        subtree = edit(path, 'POST', 'states', Name='Subtree', StateType='Subtree')['selected_id']
        linked = edit(path, 'POST', 'states', ParentId=root, Name='Linked', StateType='Linked',
                      TargetStateId=subtree)['selected_id']
        reject(path, 'POST', 'nodes', StateId=linked, Kind='single_task', StructPath=struct)
        before = inspect(path)
        values = {'RandomDeviation': '0.1'}
        edit(path, 'PATCH', 'nodes', **common, ItemId=task, InstanceProperties=values, bDryRun=True)
        assert inspect(path) == before
        edit(path, 'PATCH', 'nodes', **common, ItemId=task, InstanceProperties=values)
        after = inspect(path)
        assert slot()[0]['id'] == task and float(slot()[0]['instance_properties']['RandomDeviation']) == 0.1
        assert not edit(path, 'PATCH', 'nodes', **common, ItemId=task, InstanceProperties=values)['would_change']
        call('POST', '/editor/transactions/undo')
        assert stable(inspect(path)) == stable(before)
        call('POST', '/editor/transactions/redo')
        assert stable(inspect(path)) == stable(after)
        reject(path, 'DELETE', 'nodes', **common, ItemId=task)
        before = inspect(path)
        edit(path, 'DELETE', 'nodes', **common, ItemId=task, bConfirm=True, bDryRun=True)
        assert inspect(path) == before
        edit(path, 'DELETE', 'nodes', **common, ItemId=task, bConfirm=True)
        assert slot() == [] and inspect(path)['binding_count'] == 0
        call('POST', '/editor/transactions/undo')
        assert stable(inspect(path)) == stable(before)
        call('POST', '/editor/transactions/redo')
        assert slot() == [] and inspect(path)['binding_count'] == 0
        call('POST', '/editor/transactions/undo')
        for fixture in [dependency, default, path]:
            edit(fixture, 'POST', 'compile', bSave=True)
        snapshots = {fixture: stable(inspect(fixture)) for fixture in paths}
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'paths': paths, 'snapshots': snapshots}, indent=2))
        keep = True
        print('Single-task REST slots, atomic bindings, guard matrix, dry-run/no-op, undo/redo and save: OK')
    finally:
        if paths and not keep:
            cleanup(paths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    run(args.base, args.phase)
