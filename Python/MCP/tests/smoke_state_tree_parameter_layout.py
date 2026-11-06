"""Parameter ordering/type migration with local and transitive linked callers."""
import argparse
import uuid

from state_tree_verification import StateTreeVerification


def run(base, phase):
    test = StateTreeVerification('state_tree_parameter_layout', base)
    if phase != 'prepare':
        if phase == 'verify':
            test.verify()
            print('Cold parameter ordering/types, linked layouts/overrides, bindings and compiled data: OK')
        test.cleanup()
        return
    assert not test.manifest.exists(), 'Verify or clean the previous parameter-layout fixture'
    keep = False
    try:
        leaf, root = test.create('ParameterLeaf')
        caller, caller_root = test.create('ParameterCaller')
        outer, outer_root = test.create('ParameterOuter')

        def parameter(path, name, kind, value, **scope):
            return test.edit(path, 'POST', 'parameters', Name=name, ParameterType=kind,
                             bSetValue=True, Value=value, **scope)['selected_id']

        amount = parameter(leaf, 'Amount', 'Float', '0.03')
        flag = parameter(leaf, 'Flag', 'Bool', 'True')
        count = parameter(leaf, 'Count', 'Int32', '7')
        work = test.edit(leaf, 'POST', 'states', ParentId=root, Name='Work')['selected_id']
        test.edit(leaf, 'POST', 'nodes', StateId=work,
                  StructPath='/Script/StateTreeModule.StateTreeDelayTask',
                  InstanceProperties={'RandomDeviation': '0'},
                  Bindings=[{'SourceId': 'root', 'SourcePath': 'Amount', 'TargetId': '$new', 'TargetPath': 'Duration'}])
        test.edit(leaf, 'POST', 'transitions', StateId=work)
        link = test.edit(caller, 'POST', 'states', ParentId=caller_root, Name='Call',
                         StateType='LinkedAsset', LinkedAssetPath=leaf)['selected_id']
        test.edit(caller, 'POST', 'transitions', StateId=link)
        test.edit(outer, 'POST', 'states', ParentId=outer_root, Name='OuterCall',
                  StateType='LinkedAsset', LinkedAssetPath=caller)
        test.edit(caller, 'PATCH', 'parameters', StateId=link, ItemId=amount, bSetValue=True, Value='0.07')
        subtree = test.edit(leaf, 'POST', 'states', Name='Subtree', StateType='Subtree')['selected_id']
        local_amount = parameter(leaf, 'LocalAmount', 'Float', '0.05', StateId=subtree)
        local_flag = parameter(leaf, 'LocalFlag', 'Bool', 'True', StateId=subtree)
        local_count = parameter(leaf, 'LocalCount', 'Int32', '9', StateId=subtree)
        local_link = test.edit(leaf, 'POST', 'states', ParentId=root, Name='LocalCall',
                               StateType='Linked', TargetStateId=subtree)['selected_id']
        test.edit(leaf, 'PATCH', 'parameters', StateId=local_link, ItemId=local_amount,
                  bSetValue=True, Value='0.08')

        def fields(path, state_id=''):
            return (test.state(path, state_id) if state_id else test.inspect(path))['parameters']['fields']

        for selected, identities in [('', [amount, flag, count]), (subtree, [local_amount, local_flag, local_count])]:
            scope = {'StateId': selected} if selected else {}
            original = {row['id']: row for row in fields(leaf, selected)}
            before = test.snapshots()
            assert not test.edit(leaf, 'POST', 'parameters/move', ItemId=identities[0], Index=0, **scope)['would_change']
            test.edit(leaf, 'POST', 'parameters/move', ItemId=identities[0], Index=-1, bDryRun=True, **scope)
            assert test.snapshots() == before
            for invalid in [-2, 3, 99]:
                test.reject(leaf, 'POST', 'parameters/move', ItemId=identities[0], Index=invalid, **scope)
            test.reject(leaf, 'POST', 'parameters/move', ItemId=str(uuid.uuid4()), Index=0, **scope)
            for index, expected in [(-1, identities[1:] + identities[:1]), (0, identities),
                                    (1, identities[1:2] + identities[:1] + identities[2:]), (0, identities)]:
                moved = test.transaction_check(lambda: test.edit(
                    leaf, 'POST', 'parameters/move', ItemId=identities[0], Index=index, **scope))
                assert set(moved['affected_assets']) == set(test.paths)
                rows = fields(leaf, selected)
                assert [row['id'] for row in rows] == expected
                assert {row['id']: row for row in rows} == original
                inherited = fields(caller, link) if not selected else fields(leaf, local_link)
                assert [row['id'] for row in inherited] == expected
                assert identities[0] in test.state(caller, link)['parameter_overrides'] if not selected else identities[0] in test.state(leaf, local_link)['parameter_overrides']
                assert float(next(row for row in inherited if row['id'] == identities[0])['value']) == (0.07 if not selected else 0.08)
        for path, state_id, identity in [(caller, link, amount), (leaf, local_link, local_amount)]:
            test.reject(path, 'POST', 'parameters/move', StateId=state_id, ItemId=identity, Index=0)
            test.reject(path, 'POST', 'parameters/type', StateId=state_id, ItemId=identity,
                        ParameterType='Double', bConfirm=True)
        print('Root/local parameter moves preserve transitive layouts, GUIDs, values, overrides and undo/redo: OK')

        test.reject(leaf, 'POST', 'parameters/type', ItemId=amount, ParameterType='Double')
        test.reject(leaf, 'POST', 'parameters/type', ItemId=amount, ParameterType='Double',
                    bConfirm=True, bSetName=True, Name='Wrong')
        before = test.snapshots()
        test.edit(leaf, 'POST', 'parameters/type', ItemId=amount, ParameterType='Double', bConfirm=True, bDryRun=True)
        assert test.snapshots() == before
        test.transaction_check(lambda: test.edit(leaf, 'POST', 'parameters/type', ItemId=amount,
                                                 ParameterType='Double', bConfirm=True))
        for path, state_id, expected in [(leaf, '', 0.03), (caller, link, 0.07)]:
            row = next(row for row in fields(path, state_id) if row['id'] == amount)
            assert row['name'] == 'Amount' and row['type'] == 'Double' and abs(float(row['value']) - expected) < 1e-6, row
        assert not test.edit(leaf, 'POST', 'parameters/type', ItemId=amount,
                             ParameterType='Double', bConfirm=True)['would_change']
        test.reject(leaf, 'POST', 'parameters/type', ItemId=amount, ParameterType='String',
                    bConfirm=True, bSetValue=True, Value='incompatible')
        test.transaction_check(lambda: test.edit(leaf, 'POST', 'parameters/type', ItemId=count,
                                                 ParameterType='Double', bConfirm=True))
        row = next(row for row in fields(leaf) if row['id'] == count)
        assert row['name'] == 'Count' and row['type'] == 'Double' and float(row['value']) == 7
        test.transaction_check(lambda: test.edit(leaf, 'POST', 'parameters/type', ItemId=count,
                                                 ParameterType='Int32', bConfirm=True, bSetValue=True, Value='11'))
        assert next(row for row in fields(leaf) if row['id'] == count)['value'] == '11'
        print('Parameter numeric migration, GUID/name retention, caller overrides, binding preflight and explicit replacement: OK')
        test.save()
        keep = True
    finally:
        if not keep:
            test.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    run(args.base, args.phase)
