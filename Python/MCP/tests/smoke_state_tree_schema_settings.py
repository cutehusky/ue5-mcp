"""Schema settings/context notifications, linked preflight and cold persistence."""
import argparse
from state_tree_verification import StateTreeVerification


def run(base, phase):
    test = StateTreeVerification('state_tree_schema_settings', base)
    if phase != 'prepare':
        if phase == 'verify':
            test.verify()
            print('Cold schema settings/context classes and linked assets: OK')
        test.cleanup()
        return
    assert not test.manifest.exists()
    keep = False
    try:
        leaf, _ = test.create('SchemaLeaf')
        caller, root = test.create('SchemaCaller')
        test.edit(caller, 'POST', 'states', ParentId=root, Name='Call',
                  StateType='LinkedAsset', LinkedAssetPath=leaf)
        before = test.snapshots()
        test.edit(leaf, 'PATCH', 'schema', Properties={'ScheduledTickPolicy': 'Denied'}, bDryRun=True)
        assert test.snapshots() == before
        changed = test.transaction_check(lambda: test.edit(
            leaf, 'PATCH', 'schema', Properties={'ScheduledTickPolicy': 'Denied'}))
        assert set(changed['affected_assets']) == set(test.paths)
        assert test.inspect(leaf)['schema_properties']['ScheduledTickPolicy'] == 'Denied'
        assert not test.inspect(leaf)['schema_capabilities']['scheduled_tick']
        assert not test.edit(leaf, 'PATCH', 'schema', Properties={'ScheduledTickPolicy': 'Denied'})['would_change']
        for values in [{'Properties': {'Missing': '1'}},
                       {'Properties': {'ScheduledTickPolicy': 'Invalid'}},
                       {'ContextClasses': {'ContextActorClass': '/Script/Engine.Material'}},
                       {'ContextClasses': {'Missing': '/Script/Engine.Actor'}},
                       {'ContextClasses': {'ContextActorClass': '/Script/Missing.Class'}},
                       {'Properties': {'ContextActorClass': '/Script/Engine.Pawn'}}]:
            test.reject(leaf, 'PATCH', 'schema', **values)
        # Broaden the leaf's owner requirement first, then the caller may narrow.
        test.transaction_check(lambda: test.edit(caller, 'PATCH', 'schema',
                                                 ContextClasses={'ContextActorClass': '/Script/Engine.Pawn'}))
        assert test.inspect(caller)['schema_context_classes']['ContextActorClass'] == '/Script/Engine.Pawn'
        assert not test.edit(caller, 'PATCH', 'schema',
                             ContextClasses={'ContextActorClass': '/Script/Engine.Pawn'})['would_change']
        test.save()
        keep = True
        print('Schema settings, context class constraints, notifications/capabilities, callers and transactions: OK')
    finally:
        if not keep:
            test.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'verify', 'cleanup'])
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    run(args.base, args.phase)
