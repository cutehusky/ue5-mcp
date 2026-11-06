"""Loaded native StateTree schema discovery, context identities and query guards."""
import json
import uuid

import httpx

BASE = 'http://127.0.0.1:8080'


def call(**params):
    response = httpx.get(BASE + '/state-trees/schemas', params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def run():
    result = call(limit=256)
    schemas = result['schemas']
    paths = [schema['class_path'] for schema in schemas]
    assert paths == sorted(set(paths)), paths
    assert '/Script/GameplayStateTreeModule.StateTreeComponentSchema' in paths
    assert result['total'] == len(schemas) and not result['truncated']
    for schema in schemas:
        assert schema['class_path'].startswith('/Script/')
        assert schema['display_name'] and schema['state_types'] and schema['selection_behaviors']
        for flag in ['allow_multiple_tasks', 'allow_enter_conditions', 'allow_evaluators',
                     'allow_considerations', 'allow_global_parameters', 'allow_tasks_completion',
                     'allow_scheduled_tick']:
            assert isinstance(schema[flag], bool), (schema['class_path'], flag)
        context_ids = []
        for context in schema['contexts']:
            identity = uuid.UUID(context['id'])
            assert identity.int and context['name'] and context['type'].startswith('/Script/'), context
            context_ids.append(identity)
        assert len(context_ids) == len(set(context_ids))
        assert isinstance(schema['properties'], dict) and len(schema['settings']) <= 128
        for setting in schema['settings']:
            assert setting['name'] and setting['type'], setting
    limited = call(limit=1)
    assert limited['schemas'] == schemas[:1]
    assert limited['total'] == result['total']
    assert limited['truncated'] == (result['total'] > 1)
    for path in paths:
        filtered = call(search=path, limit=256)
        assert filtered['schemas'] == [schema for schema in schemas if path in schema['class_path']]
    empty = call(search='DefinitelyMissingSchemaFixture')
    assert empty['schemas'] == [] and empty['total'] == 0 and not empty['truncated']
    for params in [{'limit': 0}, {'limit': 257}, {'search': 'x' * 129}, {'limit': 'wrong'}]:
        response = httpx.get(BASE + '/state-trees/schemas', params=params, timeout=60)
        assert response.status_code >= 400, (params, response.status_code, response.text)
    assert call(limit=256) == result, 'Read-only discovery changed its output'
    print(f'Native schema discovery: {len(schemas)} loaded schemas, context GUIDs, capabilities, '
          'settings, sorting, filtering, limits and guards: OK')
    return result


if __name__ == '__main__':
    run()
