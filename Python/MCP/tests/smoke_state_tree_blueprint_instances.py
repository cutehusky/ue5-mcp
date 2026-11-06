"""Blueprint instance authoring, reflected discovery and unloaded registry candidates."""
import argparse
import json
import uuid

import httpx
from state_tree_verification import StateTreeVerification


def run(base, phase):
    test = StateTreeVerification('state_tree_blueprint_instances', base)
    blueprints = []

    def cleanup():
        test.cleanup()
        for path in reversed(blueprints):
            test.call('POST', '/assets/delete', {'AssetPath': path})

    def discover(path, **values):
        return test.call('GET', '/state-trees/node-classes', asset_path=path, **values)

    def check_native_metadata(discovery):
        native = test.call('GET', '/state-trees/node-types', asset_path=discovery,
                           kind='task', search='MCPVerificationContainerTask')['nodes'][0]
        native_fields = {row['name']: row for row in native['instance_properties']}
        assert native_fields['Materials']['element']['reference_class'] == '/Script/Engine.MaterialInterface'
        assert native_fields['ActorClasses']['element']['reference_class'] == '/Script/Engine.Actor'
        assert native_fields['SoftMaterials']['value']['reference_class'] == '/Script/Engine.MaterialInterface'
        condition = test.call('GET', '/state-trees/node-types', asset_path=discovery,
                              kind='condition', search='StateTreeCompareFloatCondition')['nodes'][0]
        enums = [row for row in condition['properties'] + condition['instance_properties'] if 'enum_members' in row]
        assert enums, condition
        for row in enums:
            assert row['enum_path'].startswith('/Script/') and 0 < len(row['enum_members']) <= 256
            assert not any(name.endswith('_MAX') or name == 'MAX' for name in row['enum_members']), row

    if phase != 'prepare':
        saved = json.loads(test.manifest.read_text())
        blueprints.extend(saved['blueprints'])
        if phase == 'verify':
            # Use an empty tree before loading the tree that references the Blueprint.
            discovery = saved['paths'][0]
            candidate = discover(discovery, kind='task', search=saved['unloaded_class'])
            assert candidate['classes'] == [] and candidate['total'] == 0, candidate
            assert candidate['blueprint_candidate_total'] == 1, candidate
            row = candidate['blueprint_candidates'][0]
            assert row['class_path'] == saved['unloaded_class']
            assert not row['loaded'] and row['requires_authoring_validation'], row
            assert discover(discovery, kind='task', search=saved['unloaded_class']) == candidate
            test.verify()
            check_native_metadata(discovery)
            loaded = discover(discovery, kind='task', search=saved['author_class'])
            assert len(loaded['classes']) == 1
            assert loaded['classes'][0]['class_path'] == saved['author_class']
            assert any(field['name'] == 'Extra' for field in loaded['classes'][0]['instance_properties'])
            print('Cold Blueprint instance identity/settings/bindings and unloaded registry no-load candidates: OK')
        cleanup()
        return

    assert not test.manifest.exists(), 'Verify or clean the previous Blueprint fixture'
    keep = False
    try:
        discovery, _ = test.create('BlueprintDiscovery')
        author, root = test.create('BlueprintInstances')
        prefix = 'BP_MCPNodes_' + uuid.uuid4().hex[:8]

        def blueprint(name, parent):
            created = test.call('POST', '/blueprint', {'BpPath': '/Game/UE5MCP_Test/' + prefix + name,
                                                       'ParentClass': parent})
            path = created.get('bpPath') or created.get('BpPath') or created.get('bp_path')
            assert path, created
            if '.' not in path:
                path += '.' + path.rsplit('/', 1)[-1]
            blueprints.append(path)
            test.call('POST', '/blueprints/compile', {'BpPath': path})
            return path, path + '_C'

        bp, cls = blueprint('TaskA', '/Script/UE5_MCP.MCPVerificationBlueprintTask')
        unused, unused_cls = blueprint('TaskB', '/Script/UE5_MCP.MCPVerificationBlueprintTask')
        families = [('condition', 'enter_condition', '/Script/StateTreeModule.StateTreeConditionBlueprintBase'),
                    ('evaluator', 'evaluator', '/Script/StateTreeModule.StateTreeEvaluatorBlueprintBase'),
                    ('consideration', 'consideration', '/Script/StateTreeModule.StateTreeConsiderationBlueprintBase')]
        other_classes = []
        for family, kind, parent in families:
            _, family_class = blueprint(family, parent)
            other_classes.append((family, kind, family_class))
        test.call('POST', '/blueprints/variables', {'BpPath': bp, 'VarSignature': 'float Extra', 'DefaultValue': '0.0'})
        work = test.edit(author, 'POST', 'states', ParentId=root, Name='Work')['selected_id']
        test.edit(author, 'POST', 'transitions', StateId=work)
        test.edit(author, 'POST', 'parameters', Name='Amount', ParameterType='Float', bSetValue=True, Value='3')
        before = test.snapshots()
        bindings = [{'SourceId': 'root', 'SourcePath': 'Amount', 'TargetId': '$new', 'TargetPath': 'Amount'}]
        settings = {'Label': 'Authored', 'Offset': '(X=1,Y=2,Z=3)', 'Extra': '2'}
        test.edit(author, 'POST', 'nodes', StateId=work, NodeClassPath=cls,
                  InstanceProperties=settings, Bindings=bindings, bDryRun=True)
        assert test.snapshots() == before
        task = test.transaction_check(lambda: test.edit(author, 'POST', 'nodes', StateId=work,
                                                        NodeClassPath=cls, InstanceProperties=settings,
                                                        Bindings=bindings))['selected_id']

        def node():
            return next(row for row in test.state(author, work)['tasks'] if row['id'] == task)

        assert node()['instance_class'] == cls
        assert float(node()['instance_properties']['Extra']) == 2
        assert test.inspect(author)['binding_count'] == 1
        assert not test.edit(author, 'PATCH', 'nodes', StateId=work, ItemId=task,
                             InstanceProperties=settings)['would_change']
        changed = {'Label': 'Changed', 'Offset': '(X=4,Y=5,Z=6)', 'Extra': '5'}
        test.transaction_check(lambda: test.edit(author, 'PATCH', 'nodes', StateId=work,
                                                 ItemId=task, InstanceProperties=changed))
        test.reject(author, 'PATCH', 'nodes', StateId=work, ItemId=task,
                    InstanceProperties={'MissingField': '1'})
        test.reject(author, 'POST', 'nodes', StateId=work, Kind='enter_condition', NodeClassPath=cls)
        test.reject(author, 'POST', 'nodes', StateId=work,
                    NodeClassPath='/Script/StateTreeModule.StateTreeTaskBlueprintBase')
        # Structural Blueprint compilation must retain the authored instance and bindings.
        test.call('POST', '/blueprints/variables', {'BpPath': bp, 'VarSignature': 'bool Recompiled', 'DefaultValue': 'True'})
        assert node()['id'] == task and node()['instance_class'] == cls
        assert float(node()['instance_properties']['Extra']) == 5
        assert node()['instance_properties']['Recompiled'] == 'True'
        test.edit(author, 'POST', 'compile')
        for family, kind, family_class in other_classes:
            created = test.edit(author, 'POST', 'nodes', StateId=work, Kind=kind,
                                NodeClassPath=family_class)['selected_id']
            result = discover(discovery, kind=family, search=family_class)
            assert [row['class_path'] for row in result['classes']] == [family_class], result
            test.transaction_check(lambda: test.edit(author, 'DELETE', 'nodes', StateId=work,
                                                     Kind=kind, ItemId=created, bConfirm=True))
        result = discover(discovery, kind='task', search=prefix, limit=256)
        assert [row['class_path'] for row in result['classes']] == sorted([cls, unused_cls]), result
        assert result['blueprint_candidates'] == []
        limited = discover(discovery, kind='task', search=prefix, limit=1)
        assert len(limited['classes']) == 1 and limited['total'] == 2 and limited['truncated']
        metadata = {row['name']: row for row in next(row for row in result['classes']
                                                   if row['class_path'] == cls)['instance_properties']}
        for name in ['Amount', 'Offset', 'Label', 'Extra', 'Recompiled']:
            assert metadata[name]['editable'] and metadata[name]['plain_setting_supported'], metadata[name]
        for name in ['Material', 'SoftMaterial', 'ActorClass', 'SoftActorClass']:
            assert metadata[name]['reference_setting_supported'] and metadata[name]['reference_class'].startswith('/Script/'), metadata[name]
        for name, kind in [('Samples', 'Array'), ('Codes', 'Set'), ('Scores', 'Map')]:
            assert metadata[name]['container_setting_supported'] and metadata[name]['container_kind'] == kind, metadata[name]
        assert metadata['Samples']['element']['type'] == 'float'
        assert metadata['Scores']['key']['type'] == 'FName'
        assert metadata['Scores']['value']['type'] == 'float'
        check_native_metadata(discovery)
        for values in [{'kind': 'wrong'}, {'kind': 'task', 'limit': 0}, {'kind': 'task', 'limit': 257},
                       {'kind': 'task', 'search': 'x' * 129}]:
            response = httpx.get(base + '/state-trees/node-classes', params={'asset_path': discovery} | values, timeout=180)
            assert response.status_code >= 400, (values, response.text[:500])
        assert discover(discovery, kind='task', search='DefinitelyMissingFixture')['classes'] == []
        before = test.snapshots()
        test.edit(author, 'DELETE', 'nodes', StateId=work, ItemId=task, bConfirm=True)
        assert test.inspect(author)['binding_count'] == 0
        test.call('POST', '/editor/transactions/undo')
        assert test.snapshots(stable=True) == {path: test.stable(snapshot) for path, snapshot in before.items()}
        for blueprint_path in blueprints:
            test.call('POST', '/assets/save', {'AssetPath': blueprint_path})
        test.save()
        saved = json.loads(test.manifest.read_text())
        saved.update({'blueprints': blueprints, 'author_class': cls, 'unloaded_class': unused_cls})
        test.manifest.write_text(json.dumps(saved, indent=2))
        keep = True
        print('Blueprint REST instances, all wrapper families, recompile retention, discovery/settings metadata and guards: OK')
    finally:
        if not keep:
            cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    run(args.base, args.phase)
