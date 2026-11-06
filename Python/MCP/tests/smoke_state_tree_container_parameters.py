"""Typed array/set parameters, replacement, linked overrides and persistence."""
import argparse
import json

from state_tree_verification import StateTreeVerification


def run(base, phase):
    test = StateTreeVerification('state_tree_container_parameters', base)
    if phase != 'prepare':
        if phase == 'verify':
            test.verify()
            print('Cold typed arrays/sets, replacement identities, references and caller overrides: OK')
        test.cleanup()
        return
    assert not test.manifest.exists(), 'Verify or clean the previous container fixture'
    keep = False
    try:
        leaf, _ = test.create('ContainerParameters')
        caller, root = test.create('ContainerCaller')

        def fields(path, state_id=''):
            return (test.state(path, state_id) if state_id else test.inspect(path))['parameters']['fields']

        def field(path, identity, state_id=''):
            return next(row for row in fields(path, state_id) if row['id'] == identity)

        material = '/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial'
        specs = [
            ('Float', ['1', '2.5'], ''),
            ('Int32', ['1', '2'], ''),
            ('Byte', ['0', '255'], ''),
            ('Int64', ['1', '1000000000000'], ''),
            ('UInt32', ['0', '4294967295'], ''),
            ('UInt64', ['0', '1000000000000'], ''),
            ('Double', ['1.25', '2.5'], ''),
            ('Bool', ['True', 'False'], ''),
            ('Name', ['Alpha', 'Beta'], ''),
            ('String', ['Alpha', 'Beta'], ''),
            ('Enum', ['ECC_Visibility', 'ECC_Camera'], '/Script/Engine.ECollisionChannel'),
            ('Struct', ['(X=1,Y=2,Z=3)', '(X=4,Y=5,Z=6)'], '/Script/CoreUObject.Vector'),
            ('Object', [material, 'None'], '/Script/Engine.MaterialInterface'),
            ('SoftObject', [material, 'None'], '/Script/Engine.MaterialInterface'),
            ('Class', ['/Script/Engine.Actor', '/Script/Engine.Pawn'], '/Script/Engine.Actor'),
            ('SoftClass', ['/Script/Engine.Actor', '/Script/Engine.Pawn'], '/Script/Engine.Actor'),
        ]
        identities = {}
        for container in ['Array', 'Set']:
            for kind, values, type_path in specs:
                created = test.edit(leaf, 'POST', 'parameters', Name=container + kind,
                                    ParameterType=kind, ContainerType=container, TypePath=type_path,
                                    bSetValue=True, Value=json.dumps(values + values[:1]))
                identity = created['selected_id']
                identities[container + kind] = identity
                row = field(leaf, identity)
                assert row['type'] == kind and row['container_type'] == container
                assert row['container_size'] == (3 if container == 'Array' else 2), row
                assert not row['container_values_truncated']
                if kind == 'Float':
                    assert [float(value) for value in row['container_values']] == ([1, 2.5, 1] if container == 'Array' else [1, 2.5])
                elif kind in ['Object', 'SoftObject']:
                    assert row['container_values'][0] == material
                elif kind in ['Class', 'SoftClass']:
                    assert '/Script/Engine.Actor' in row['container_values']
        link = test.edit(caller, 'POST', 'states', ParentId=root, Name='Call',
                         StateType='LinkedAsset', LinkedAssetPath=leaf)['selected_id']
        samples = identities['ArrayFloat']
        codes = identities['SetInt32']
        before = test.snapshots()
        test.edit(caller, 'PATCH', 'parameters', StateId=link, ItemId=samples,
                  bSetValue=True, Value='["4","5"]', bDryRun=True)
        assert test.snapshots() == before
        test.transaction_check(lambda: test.edit(caller, 'PATCH', 'parameters', StateId=link,
                                                 ItemId=samples, bSetValue=True, Value='["4","5"]'))
        assert [float(value) for value in field(caller, samples, link)['container_values']] == [4, 5]
        assert samples in test.state(caller, link)['parameter_overrides']
        assert [float(value) for value in field(leaf, samples)['container_values']] == [1, 2.5, 1]
        test.transaction_check(lambda: test.edit(leaf, 'PATCH', 'parameters', ItemId=codes,
                                                 bSetValue=True, Value='["8","8","9"]'))
        assert set(field(caller, codes, link)['container_values']) == {'8', '9'}
        test.transaction_check(lambda: test.edit(caller, 'POST', 'parameters/reset', StateId=link,
                                                 ItemId=samples, bConfirm=True))
        assert samples not in test.state(caller, link)['parameter_overrides']
        assert field(caller, samples, link)['container_values'] == field(leaf, samples)['container_values']
        for value in ['[1,2]', '[true]', '["nan"]', '["inf"]', '["1e20"]', '{"bad":1}',
                      json.dumps(['1'] * 257), '["' + '1' * 65537 + '"]']:
            test.reject(leaf, 'PATCH', 'parameters', ItemId=samples, bSetValue=True, Value=value)
        for value in ['2147483648', '-2147483649', '18446744073709551616', '1.5']:
            test.reject(leaf, 'PATCH', 'parameters', ItemId=codes, bSetValue=True, Value=json.dumps([value]))
        for name, value in [('ArrayByte', '256'), ('ArrayUInt32', '-1'), ('ArrayUInt32', '4294967296')]:
            test.reject(leaf, 'PATCH', 'parameters', ItemId=identities[name], bSetValue=True, Value=json.dumps([value]))
        test.transaction_check(lambda: test.edit(leaf, 'PATCH', 'parameters', ItemId=codes,
                                                 bSetValue=True, Value='["-2147483648","2147483647"]'))
        assert set(field(leaf, codes)['container_values']) == {'-2147483648', '2147483647'}
        for name, value in [('ArrayEnum', '["MissingEnumMember"]'),
                            ('ArrayObject', '["/Script/Engine.Actor"]'),
                            ('ArrayClass', '["/Script/Engine.Material"]'),
                            ('ArraySoftObject', '["/Game/DefinitelyMissing.Asset"]')]:
            test.reject(leaf, 'PATCH', 'parameters', ItemId=identities[name], bSetValue=True, Value=value)
        test.reject(leaf, 'POST', 'parameters', Name='Nested', ParameterType='Float', ContainerType='Map')
        test.reject(leaf, 'POST', 'parameters', Name='TextSet', ParameterType='Text', ContainerType='Set')
        test.transaction_check(lambda: test.edit(leaf, 'PATCH', 'parameters', ItemId=samples,
                                                 bSetValue=True, Value=json.dumps(['1'] * 256)))
        assert field(leaf, samples)['container_size'] == 256
        test.transaction_check(lambda: test.edit(leaf, 'PATCH', 'parameters', ItemId=samples,
                                                 bSetValue=True, Value='[]'))
        assert field(leaf, samples)['container_size'] == 0
        assert not test.edit(leaf, 'PATCH', 'parameters', ItemId=samples,
                             bSetValue=True, Value='[]')['would_change']
        print('Typed array/set values, hashing/deduplication, references, limits, caller overrides and guards: OK')

        # Exercise each supported replacement container layout with explicit values.
        count = test.edit(leaf, 'POST', 'parameters', Name='Replacement', ParameterType='Int32',
                          bSetValue=True, Value='7')['selected_id']
        for kind, container, values, expected in [
            ('Float', 'Array', ['1', '2'], [1, 2]),
            ('Double', 'Array', ['3', '4'], [3, 4]),
            ('Int32', 'Set', ['5', '5', '6'], [5, 6]),
            ('Float', 'None', None, None),
        ]:
            value = '11' if values is None else json.dumps(values)
            test.transaction_check(lambda: test.edit(leaf, 'POST', 'parameters/type', ItemId=count,
                                                     ParameterType=kind, ContainerType=container,
                                                     bConfirm=True, bSetValue=True, Value=value))
            row = field(leaf, count)
            assert row['id'] == count and row['name'] == 'Replacement' and row['type'] == kind
            assert row['container_type'] == container
            if expected is not None:
                assert sorted(float(value) for value in row['container_values']) == expected
            else:
                assert float(row['value']) == 11
            assert field(caller, count, link)['type'] == kind
        print('Scalar/array/set type replacement, explicit values, identity retention and caller layouts: OK')
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
