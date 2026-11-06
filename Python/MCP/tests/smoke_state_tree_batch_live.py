"""StateTree node containers, labels/enablement, completion/condition modes, utility inputs and schema references.

prepare: on an AI-component-schema StateTree, author MCPVerificationContainerTask array/set/map instance fields (scalars and
references, set deduplication, duplicate map key refused), explicit node names and task enablement, task completion
participation and condition evaluation mode, Float Input response-curve keys and Enum Input score tables, and schema
class references (AIControllerClass, ContextActorClass); dry runs and refusals throughout; compile and save.
verify (fresh editor): the inspected tree matches and is ready to run; cleanup deletes it.
"""
import json
import sys
import uuid

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'state_tree_batch.json'
SCHEMA = '/Script/GameplayStateTreeModule.StateTreeAIComponentSchema'
TASK = '/Script/UE5_MCP.MCPVerificationContainerTask'
MAT = '/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial'


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AssertionError(('non-JSON', text[:300]))


def ok(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert not (isinstance(r, dict) and 'errorMessage' in r), (fn.__name__, r.get('errorMessage', '')[:500])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and 'errorMessage' in r, (fn.__name__, 'expected rejection', str(r)[:400])
    return r['errorMessage']


def tree(path):
    return ok(m.inspect_state_tree, path)


def stable(t):
    return {k: v for k, v in t.items() if k not in ('dirty', 'selected_id', 'would_change', 'dry_run', 'saved', 'diagnostics')}


def state(path, sid):
    return next(s for s in tree(path)['states'] if s['id'] == sid)


def node(path, sid, kind, nid):
    s = state(path, sid)
    key = {'task': 'tasks', 'consideration': 'considerations', 'enter_condition': 'enter_conditions'}[kind]
    return next(n for n in s[key] if n['id'] == nid)


def same_after_dry(path, fn, *a, **kw):
    before = stable(tree(path))
    ok(fn, *a, dry_run=True, **kw)
    assert stable(tree(path)) == before, (fn.__name__, 'dry run changed the tree')


def container_stage(path, sid):
    t = ok(m.edit_state_tree_node, path, 'create', 'task', sid, struct_path=TASK)['selected_id']
    good = {'Samples': '["1.5","2.5","-3"]', 'Codes': '["4","2","4"]', 'Scores': json.dumps([{'Key': 'A', 'Value': '0.25'}, {'Key': 'B', 'Value': '0.75'}]),
            'Materials': json.dumps([MAT, MAT]), 'ActorClasses': '["/Script/Engine.Actor","/Script/Engine.Pawn"]',
            'SoftMaterials': json.dumps([{'Key': 'Main', 'Value': MAT}])}
    bad(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, instance_containers={'Scores': json.dumps([{'Key': 'A', 'Value': '1'}, {'Key': 'A', 'Value': '2'}])})
    bad(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, instance_containers={'Samples': '["abc"]'})
    bad(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, instance_containers={'Materials': '["/Game/Nope/M.M"]'})
    bad(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, instance_containers={'Expected': '["1"]'})       # not a container
    same_after_dry(path, m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, instance_containers=good)
    ok(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, instance_containers=good)
    n = node(path, sid, 'task', t)
    print('container node:', json.dumps(n)[:1500])
    text = json.dumps(n)
    assert '1.5' in text and '-3' in text and 'BasicShapeMaterial' in text and '/Script/Engine.Pawn' in text, text[:800]
    return t


def label_stage(path, sid, t):
    ok(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, name='MCP Containers', task_enabled=False)
    n = node(path, sid, 'task', t)
    assert n.get('explicit_name') == 'MCP Containers' and n.get('task_enabled') is False, n
    ok(m.edit_state_tree_node, path, 'update', 'task', sid, item_id=t, considered_for_completion=False)
    print('completion flags:', {k: v for k, v in node(path, sid, 'task', t).items() if 'complet' in k or 'enabled' in k})
    c = ok(m.edit_state_tree_node, path, 'create', 'enter_condition', sid, struct_path='/Script/StateTreeModule.StateTreeRandomCondition',
           condition_evaluation='ForcedTrue')['selected_id']
    bad(m.edit_state_tree_node, path, 'update', 'enter_condition', sid, item_id=c, condition_evaluation='Sometimes')
    bad(m.edit_state_tree_node, path, 'update', 'enter_condition', sid, item_id=c, task_enabled=False)           # not a task
    cn = node(path, sid, 'enter_condition', c)
    print('condition:', json.dumps(cn)[:500])
    assert 'ForcedTrue' in json.dumps(cn), cn


def utility_stage(path, root):
    ok(m.edit_state_tree_state, path, 'update', root, properties={'SelectionBehavior': 'TrySelectChildrenWithHighestUtility'})
    a = ok(m.edit_state_tree_state, path, 'create', name='UtilA', parent_id=root)['selected_id']
    b = ok(m.edit_state_tree_state, path, 'create', name='UtilB', parent_id=root)['selected_id']
    for s in (a, b):
        ok(m.edit_state_tree_node, path, 'create', 'task', s, struct_path='/Script/StateTreeModule.StateTreeDelayTask')
    keys = [{'Time': 0, 'Value': 0, 'Interpolation': 'Linear'}, {'Time': 0.5, 'Value': 1, 'Interpolation': 'Cubic', 'ArriveTangent': 0, 'LeaveTangent': 0},
            {'Time': 1, 'Value': 0.2, 'Interpolation': 'Constant'}]
    # Input properties must be bound (compile preflight): root parameters feed both considerations.
    ok(m.edit_state_tree_parameter, path, 'create', name='Urgency', parameter_type='Float', value='0.5')
    ok(m.edit_state_tree_parameter, path, 'create', name='Movement', parameter_type='Enum', type_path='/Script/Engine.EMovementMode', value='MOVE_Walking')
    bind = lambda src: [{'SourceId': 'root', 'SourcePath': src, 'TargetId': '$new', 'TargetPath': 'Input'}]
    fi = ok(m.edit_state_tree_node, path, 'create', 'consideration', a, struct_path='/Script/StateTreeModule.StateTreeFloatInputConsideration',
            bindings=bind('Urgency'))['selected_id']
    bad(m.edit_state_tree_node, path, 'update', 'consideration', a, item_id=fi, response_curve_keys=[keys[1], keys[0]])     # not increasing
    bad(m.edit_state_tree_node, path, 'update', 'consideration', a, item_id=fi, response_curve_keys=[{'Time': 0, 'Value': 2}])  # not normalized
    ok(m.edit_state_tree_node, path, 'update', 'consideration', a, item_id=fi, response_curve_keys=keys)
    print('float input:', json.dumps(node(path, a, 'consideration', fi))[:900])
    ei = ok(m.edit_state_tree_node, path, 'create', 'consideration', b, struct_path='/Script/StateTreeModule.StateTreeEnumInputConsideration',
            bindings=bind('Movement'))['selected_id']
    enum = '/Script/Engine.EMovementMode'
    # The Input is bound to an EMovementMode parameter; a different score enum used to crash native compile.
    bad(m.edit_state_tree_node, path, 'update', 'consideration', b, item_id=ei, score_enum_path='/Script/Engine.ECollisionChannel',
        enum_scores={'ECC_Visibility': 0.5})
    bad(m.edit_state_tree_node, path, 'update', 'consideration', b, item_id=ei, score_enum_path=enum, enum_scores={'MOVE_Bogus': 1})
    bad(m.edit_state_tree_node, path, 'update', 'consideration', b, item_id=ei, score_enum_path=enum, enum_scores={'MOVE_Walking': 2})
    ok(m.edit_state_tree_node, path, 'update', 'consideration', b, item_id=ei, score_enum_path=enum, enum_scores={'MOVE_Walking': 0.8, 'MOVE_Falling': 0.1})
    en = json.dumps(node(path, b, 'consideration', ei))
    print('enum input:', en[:900])
    assert 'MOVE_Walking' in en and '0.8' in en, en


def schema_stage(path):
    bad(m.edit_state_tree_schema, path, references={'AIControllerClass': '/Script/Engine.Actor'})                    # wrong base
    same_after_dry(path, m.edit_state_tree_schema, path, references={'AIControllerClass': '/Script/AIModule.DetourCrowdAIController'})
    ok(m.edit_state_tree_schema, path, references={'AIControllerClass': '/Script/AIModule.DetourCrowdAIController',
                                                   'ContextActorClass': '/Script/Engine.Pawn'})
    refs = tree(path)['schema_references']
    assert refs['AIControllerClass'].endswith('DetourCrowdAIController') and refs['ContextActorClass'].endswith('Pawn'), refs
    bad(m.edit_state_tree_schema, path, containers={'AIControllerClass': '["x"]'})                                  # no container field


def prepare():
    cleanup()
    path = ok(m.create_state_tree, '/Game/UE5MCP_Test/ST_Batch_' + uuid.uuid4().hex[:8], SCHEMA)['asset_path']
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'path': path}), encoding='utf-8')
    root = tree(path)['states'][0]['id']
    sid = ok(m.edit_state_tree_state, path, 'create', name='Containers', parent_id=root)['selected_id']
    t = container_stage(path, sid)
    label_stage(path, sid, t)
    utility_stage(path, root)
    schema_stage(path)
    ok(m.compile_state_tree, path, save=True)
    snap = stable(tree(path))
    assert snap.get('ready_to_run'), snap.get('diagnostics')
    STATE.write_text(json.dumps({'path': path, 'snapshot': snap}, indent=1), encoding='utf-8')
    print('StateTree batch prepared and saved:', path)


def verify():
    st = json.loads(STATE.read_text(encoding='utf-8'))
    got = json.loads(json.dumps(stable(tree(st['path']))))
    assert got == st['snapshot'], json.dumps({'got': got, 'want': st['snapshot']})[:3000]
    assert got['ready_to_run']
    print('StateTree containers, labels, modes, utility inputs and schema references identical after cold reload')
    cleanup()


def cleanup():
    if STATE.exists():
        p = json.loads(STATE.read_text(encoding='utf-8')).get('path', '')
        if p:
            httpx.post(BASE + '/assets/delete', json={'AssetPath': p.split('.')[0]}, timeout=120)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
