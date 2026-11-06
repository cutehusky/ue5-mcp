"""GAS Blueprint hard object references, Blueprint children of every family and enum/inheritance inspection.

prepare: HitImpact cue Blueprint (Sound reference, wrong-class/unregistered refused, None clear), Montage ability Blueprint
(MontageToPlay), a Blueprint child of a Blueprint parent for effect/execution/magnitude/cue_actor/cue_static (inherits an
edited parent field), enum option lists on ability policy fields; save and snapshot.
verify (fresh editor): every definition matches; cleanup deletes the Blueprints.
"""
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
ROOT = '/Game/UE5MCP_Test/GasExtras'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'gas_extras.json'
GA = '/Script/GameplayAbilities.'
SOUND = '/Engine/EditorSounds/Notifications/CompileSuccess_Cue.CompileSuccess_Cue'
MONTAGE = '/Game/Characters/Mannequins/Anims/Pistol/MM_Pistol_Fire_Montage.MM_Pistol_Fire_Montage'
Y = dict(confirm=True)
FAMILIES = ('effect', 'execution', 'magnitude', 'cue_actor', 'cue_static')
NAMES = ['GCS_Hit', 'GA_Montage'] + [f'{f}_Base' for f in FAMILIES] + [f'{f}_Child' for f in FAMILIES]


def C(name):
    return f'{ROOT}/{name}.{name}_C'


def A(name):
    return f'{ROOT}/{name}'


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


def fields(name):
    return {f['name']: f for f in ok(m.inspect_gameplay_definition_defaults, C(name))['fields']}


def edit(name, **kw):
    before = fields(name)
    ok(m.edit_gameplay_blueprint_defaults, A(name), kw.pop('properties', {}), confirm=True, dry_run=True, **kw)
    assert fields(name) == before, (name, 'dry run changed defaults')
    ok(m.edit_gameplay_blueprint_defaults, A(name), {}, confirm=True, save=True, **kw)


def references_stage():
    ok(m.create_gameplay_blueprint, A('GCS_Hit'), 'cue_static', GA + 'GameplayCueNotify_HitImpact', save=True)
    bad(m.edit_gameplay_blueprint_defaults, A('GCS_Hit'), {}, object_references={'Sound': MONTAGE}, **Y)          # wrong class
    bad(m.edit_gameplay_blueprint_defaults, A('GCS_Hit'), {}, object_references={'Sound': '/Game/Nope/S.S'}, **Y)
    bad(m.edit_gameplay_blueprint_defaults, A('GCS_Hit'), {}, object_references={'NotAField': SOUND}, **Y)
    bad(m.edit_gameplay_blueprint_defaults, A('GCS_Hit'), {}, object_references={'Sound': SOUND})               # unconfirmed
    edit('GCS_Hit', object_references={'Sound': SOUND})
    assert 'CompileSuccess_Cue' in fields('GCS_Hit')['Sound']['value'], fields('GCS_Hit')['Sound']
    edit('GCS_Hit', object_references={'Sound': 'None'})
    assert fields('GCS_Hit')['Sound']['value'] == 'None'
    edit('GCS_Hit', object_references={'Sound': SOUND})                                                         # kept for reload
    ok(m.create_gameplay_blueprint, A('GA_Montage'), 'ability', GA + 'GameplayAbility_Montage', save=True)
    edit('GA_Montage', object_references={'MontageToPlay': MONTAGE})
    assert 'MM_Pistol_Fire_Montage' in fields('GA_Montage')['MontageToPlay']['value']


def children_stage():
    for fam in FAMILIES:
        ok(m.create_gameplay_blueprint, A(f'{fam}_Base'), fam, save=True)
    bad(m.create_gameplay_blueprint, A('effect_Child'), 'effect', C('execution_Base'))                         # family mismatch
    bad(m.create_gameplay_blueprint, A('effect_Child'), 'effect', '/Game/Nope/X.X_C')
    # An edited parent field must be inherited by each child.
    edit('effect_Base', timing={'DurationPolicy': 'HasDuration', 'Duration': 7})
    ok(m.edit_gameplay_blueprint_defaults, A('execution_Base'), {'bRequiresPassedInTags': 'True'}, save=True, **Y)
    ok(m.edit_gameplay_blueprint_defaults, A('magnitude_Base'), {'bAllowNonNetAuthorityDependencyRegistration': 'True'}, save=True, **Y)
    ok(m.edit_gameplay_blueprint_defaults, A('cue_actor_Base'), {'bAutoDestroyOnRemove': 'True'}, save=True, **Y)
    ok(m.edit_gameplay_blueprint_defaults, A('cue_static_Base'), {'IsOverride': 'False'}, save=True, **Y)
    for fam in FAMILIES:
        r = ok(m.create_gameplay_blueprint, A(f'{fam}_Child'), fam, C(f'{fam}_Base'), save=True)
        assert r['parent_class'] == C(f'{fam}_Base'), r
        ok(m.load_ability_system_class, C(f'{fam}_Child'), fam)
    assert ok(m.evaluate_gameplay_effect_definition, C('effect_Child'))['duration_magnitude'] == 7
    for fam, field in (('execution', 'bRequiresPassedInTags'), ('magnitude', 'bAllowNonNetAuthorityDependencyRegistration'),
                       ('cue_actor', 'bAutoDestroyOnRemove')):
        f = fields(f'{fam}_Child')[field]
        assert f['value'] == 'True' and f['has_parent_value'] and not f['differs_from_parent'], (fam, f)


def enum_stage():
    f = fields('GA_Montage')['InstancingPolicy']
    print('enum field:', json.dumps(f)[:700])
    names = [e['name'] if isinstance(e, dict) else e for e in f['enum_values']]
    assert any('InstancedPerActor' in n for n in names) and any('InstancedPerExecution' in n for n in names), names
    assert f['enum_path'].endswith('EGameplayAbilityInstancingPolicy'), f


def snapshot():
    out = {}
    for n in NAMES:
        d = ok(m.inspect_gameplay_definition_defaults, C(n))
        out[n] = {k: v for k, v in d.items() if k not in ('dirty',)}
    return out


def prepare():
    cleanup()
    references_stage()
    children_stage()
    enum_stage()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'snapshot': snapshot()}, indent=1), encoding='utf-8')
    print('GAS references, children and enum inspection prepared')


def verify():
    want = json.loads(STATE.read_text(encoding='utf-8'))['snapshot']
    for n in NAMES:
        ok(m.load_ability_system_class, C(n), 'ability' if n.startswith('GA') else 'cue_static' if n == 'GCS_Hit' else n.rsplit('_', 1)[0])
    got = json.loads(json.dumps(snapshot()))
    for n in NAMES:
        assert got[n] == want[n], json.dumps({'name': n, 'got': got[n], 'want': want[n]})[:3000]
    print('GAS references, children and enum inspection identical after cold reload')
    cleanup()


def cleanup():
    for n in [x for x in NAMES if x.endswith('_Child')] + [x for x in NAMES if not x.endswith('_Child')]:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': A(n)}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
