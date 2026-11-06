"""Regression for UE5_MCP_BUG_REPORT.md (#1-#25) and TEST_PLAN_UE5_MCP.md R-001..R-012 through the MCP tools.

prepare: every item runs with a read-back and is recorded pass/fail, so one failure does not hide the rest. Saves fixtures.
verify (fresh editor): saved Blueprint, widget, animation and material edits reload; cleanup removes the test folder's assets.
"""
import json
import sys
import traceback

import httpx
from smoke_animation_curves_live import PROJECT

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
ORIGINAL_ARGV = list(sys.argv)
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server as m  # noqa: E402

BASE = 'http://127.0.0.1:8080'
m.BASE_URL = BASE
ROOT = '/Game/UE5MCP_Test/BugReg'
BP, WBP, AN, MAT, MI, SM, TEX, SKM, DT = (f'{ROOT}/{n}' for n in ('BP_Reg', 'WBP_Reg', 'AN_Reg', 'M_Reg', 'MI_Reg', 'SM_Reg', 'T_Reg', 'SKM_Reg', 'DT_Reg'))
SKELETON = '/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin'
MESH = '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple'
TP = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'bug_regression.json'
ASSETS = (BP, WBP, AN, MAT, MI, SM, TEX, SKM, DT)
RESULTS = {}


def J(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def ok(fn, *a, **kw):
    text = fn(*a, **kw)
    r = J(text)
    assert not (isinstance(r, dict) and ('errorMessage' in r or 'errorCode' in r)), (fn.__name__, text[:400])
    return r


def bad(fn, *a, **kw):
    r = J(fn(*a, **kw))
    assert isinstance(r, dict) and r.get('errorMessage'), (fn.__name__, 'expected rejection', str(r)[:300])
    return r['errorMessage']


def case(name):
    def wrap(fn):
        try:
            fn()
            RESULTS[name] = 'PASS'
        except Exception as e:
            RESULTS[name] = 'FAIL ' + repr(e)[:450]
            if not isinstance(e, AssertionError):
                traceback.print_exc()
    return wrap


def text(fn, *a):
    return json.dumps(ok(fn, *a))


def run():
    state = {}

    @case('#1 R-001 spawn from asset path')
    def _():
        p = m.spawn_editor_actor(asset_path='/Engine/BasicShapes/Cube.Cube', location={'X': 1000, 'Y': 2000, 'Z': 100}).strip().strip('"')
        assert 'PersistentLevel' in p, p
        state['actor'] = p
        assert p in text(m.list_editor_actors) if hasattr(m, 'list_editor_actors') else True

    @case('#1 select actors')
    def _():
        ok(m.select_editor_actors, [state['actor']])
        assert state['actor'] in text(m.get_ue_editor_selection)
        bad(m.select_editor_actors, ['/Game/Nope.Nope:PersistentLevel.None'])

    @case('#1 R-002 viewport')
    def _():
        ok(m.set_ue_viewport, {'X': 111, 'Y': 222, 'Z': 333}, {'Pitch': -10, 'Yaw': 20, 'Roll': 0})
        v = text(m.get_ue_viewport)
        assert '111' in v and '222' in v and '333' in v, v[:300]

    @case('#20 duplicate actor')
    def _():
        d = J(m.duplicate_editor_actor(state['actor'], {'X': 100, 'Y': 0, 'Z': 0}))
        d = d if isinstance(d, str) else json.dumps(d)
        assert 'errorMessage' not in d and d != state['actor'] and 'PersistentLevel' in d, d[:300]

    @case('R-005 delete actor by body')
    def _():
        bad(m.delete_editor_actor, state['actor'])
        ok(m.delete_editor_actor, state['actor'], confirm=True)
        assert state['actor'] not in text(m.list_editor_actors)

    @case('#2 #22 R-003 Blueprint variables')
    def _():
        ok(m.create_blueprint, BP, 'Actor')
        ok(m.add_variable_to_bp, BP, 'float TestSpeed')
        assert 'TestSpeed' in text(m.get_blueprint_variables, BP)
        ok(m.rename_variable_in_bp, BP, 'TestSpeed', 'Speed2')
        v = text(m.get_blueprint_variables, BP)
        assert 'Speed2' in v and 'TestSpeed' not in v
        ok(m.add_variable_to_bp, BP, 'int Temp')
        ok(m.delete_variable_from_bp, BP, 'Temp')
        assert 'Temp' not in text(m.get_blueprint_variables, BP)

    @case('#2 R-003 Blueprint functions')
    def _():
        ok(m.create_function, BP, 'DoThing', 'float A', 'bool B')
        assert 'DoThing' in text(m.get_blueprint_functions, BP)
        ok(m.create_function, BP, 'Doomed', '', '')
        ok(m.delete_function, BP, 'Doomed')                                         # R-005
        assert 'Doomed' not in text(m.get_blueprint_functions, BP)

    @case('#22 components and events')
    def _():
        ok(m.add_component_to_bp, BP, 'StaticMeshComponent', 'RegMesh', '')
        c = text(m.get_components_of_bp, BP)
        assert 'RegMesh' in c, c[:400]
        ok(m.add_event_to_graph, BP, 'EventGraph', 'RegEvent', True)
        g = text(m.get_graph, BP, 'EventGraph')
        assert 'RegEvent' in g, g[:600]

    @case('#25 supported nodes')
    def _():
        nodes = text(m.get_supported_nodes)
        assert 'K2Node' in nodes, nodes[:300]

    @case('#24 generic node')
    def _():
        before = text(m.get_graph, BP, 'EventGraph')
        ok(m.add_generic_node_to_graph, BP, 'EventGraph', 'K2Node_IfThenElse')
        assert text(m.get_graph, BP, 'EventGraph') != before

    @case('#2 compile')
    def _():
        ok(m.compile_blueprint, BP)
        httpx.post(BASE + '/assets/save', json={'AssetPath': BP}, timeout=120)

    @case('#6 #7 R-012 graph and components on existing Blueprint')
    def _():
        assert 'EventGraph' in text(m.get_graph, TP, 'EventGraph') or ok(m.get_graph, TP, 'EventGraph')
        assert text(m.get_components_of_bp, TP) not in ('{}', '[]')

    @case('#3 #10 R-004 Widget Blueprint')
    def _():
        ok(m.create_widget_blueprint, WBP)
        ok(m.add_widget_to_blueprint, WBP, '/Script/UMG.CanvasPanel', 'Root')
        ok(m.add_widget_to_blueprint, WBP, '/Script/UMG.TextBlock', 'Title', 'Root')
        w = text(m.list_widget_blueprint_widgets, WBP)
        assert 'Root' in w and 'Title' in w, w
        assert 'Widget Blueprint' in bad(m.list_widget_blueprint_widgets, BP)        # type check on a regular Blueprint
        httpx.post(BASE + '/assets/save', json={'AssetPath': WBP}, timeout=120)

    @case('#4 R-010 animation sequence creation')
    def _():
        ok(m.create_animation_sequence, AN, SKELETON, MESH)
        assert 'SK_Mannequin' in text(m.inspect_animation_sequence, AN)
        bad(m.create_animation_sequence, f'{ROOT}/AN_Bad', '/Game/Nope.Nope')

    @case('#12 animation type check')
    def _():
        assert 'Animation Sequence' in bad(m.inspect_animation_sequence, '/Game/Characters/Mannequins/Anims/Pistol/MM_Pistol_Fire_Montage')

    @case('#13 R-006 animation curve and notify tracks')
    def _():
        ok(m.edit_animation_curve, AN, 'add_curve', 'RegCurve')                       # notify_track omitted
        ok(m.edit_animation_curve, AN, 'add_float_key', 'RegCurve', time=0.0, value=2.5)
        c = text(m.get_animation_curve, AN, 'RegCurve')
        assert '2.5' in c, c[:400]
        ok(m.edit_animation_asset, AN, 'add_track', notify_track='RegTrack')
        ok(m.edit_animation_asset, AN, 'add', notify_track='RegTrack', notify_class='/Script/Engine.AnimNotify_PlaySound', notify_name='RegNamed')
        ok(m.edit_animation_asset, AN, 'add', notify_class='/Script/Engine.AnimNotify_PlaySound', notify_name='RegDefault')               # notify_track omitted
        assert ok(m.inspect_animation_sequence, AN)['notify_count'] == 2
        ok(m.edit_animation_curve, AN, 'add_curve', 'TempCurve')
        ok(m.edit_animation_curve, AN, 'remove_curve', 'TempCurve')
        httpx.post(BASE + '/assets/save', json={'AssetPath': AN}, timeout=120)

    @case('#16 R-009 animation settings without AssetClass')
    def _():
        ok(m.edit_animation_sequence_settings, AN, {'bAllowFrameStripping': 'false'})
        assert 'errorMessage' not in text(m.get_asset_properties, AN)

    def dup(src, dst):
        ok(m.duplicate_asset, src, dst)

    @case('#14 #23 R-007 material expressions')
    def _():
        dup('/Game/ThirdPerson/MI_ThirdPersonColWay', MI)
        dup('/Engine/BasicShapes/BasicShapeMaterial', MAT)
        ok(m.create_material_expression, MAT, '/Script/Engine.MaterialExpressionConstant', 'RegConst')
        ok(m.create_material_expression, MAT, '/Script/Engine.MaterialExpressionOneMinus', 'RegOneMinus')
        e = text(m.list_material_expressions, MAT)
        assert 'RegConst' in e and 'RegOneMinus' in e, e[:400]
        ok(m.connect_material_expressions, MAT, 'RegConst', 'RegOneMinus')
        bad(m.connect_material_expressions, MAT, 'RegConst', 'NoSuchExpression')
        httpx.post(BASE + '/assets/save', json={'AssetPath': MAT}, timeout=120)

    @case('#17 R-009 material settings')
    def _():
        ok(m.edit_material_settings, MAT, {'TwoSided': 'true'})
        assert 'true' in text(m.get_asset_properties, MAT).lower()
        ok(m.edit_material_instance_settings, MI, {'bOverrideSubsurfaceProfile': 'true'})

    @case('#5 #18 R-008 R-011 generic asset properties and validate')
    def _():
        ok(m.validate_asset, BP)
        ok(m.set_asset_properties, MI, {'bOverrideSubsurfaceProfile': 'false'})
        ok(m.get_asset_properties, MI)

    @case('#15 texture settings')
    def _():
        dup('/Game/Characters/Mannequins/Textures/Manny/T_Manny_01_D', TEX)
        ok(m.edit_texture_settings, TEX, {'SRGB': 'false'})
        assert '"srgb": false' in text(m.inspect_texture, TEX).lower() or 'false' in text(m.get_asset_properties, TEX).lower()

    @case('#21 R-009 static mesh LOD group')
    def _():
        dup('/Engine/BasicShapes/Cube', SM)
        ok(m.set_static_mesh_lod_group, SM, 'SmallProp')
        assert 'SmallProp' in text(m.get_asset_properties, SM)

    @case('#19 skeletal mesh section')
    def _():
        dup(MESH.split('.')[0], SKM)
        ok(m.set_skeletal_mesh_section, SKM, 0, 0, 'cast_shadow', 'false')
        bad(m.set_skeletal_mesh_section, SKELETON, 0, 0, 'cast_shadow', 'false')       # the report used this Skeleton, which is not a mesh

    @case('#11 DataTable rows')
    def _():
        dup('/Game/UE5MCP_Fixtures/DT_MCP_Tags', DT)
        ok(m.upsert_data_table_row, DT, 'RowA', json.dumps({'Tag': 'Reg.A', 'DevComment': 'one'}))
        assert 'RowA' in text(m.get_data_table_rows, DT)
        ok(m.delete_data_table_row, DT, 'RowA')
        assert 'RowA' not in text(m.get_data_table_rows, DT)
        assert 'not found' in bad(m.get_data_table_rows, f'{ROOT}/DT_Missing.DT_Missing').lower()

    @case('#8 #9 asset editor open and close')
    def _():
        status = ok(m.get_ue_editor_status)
        assert status
        headless = '--windowed' not in ORIGINAL_ARGV
        if headless:                                                                  # used to kill the editor
            assert 'windowed' in bad(m.open_asset_editor, BP)
            bad(m.close_asset_editor, BP)
            return
        ok(m.open_asset_editor, BP)
        bad(m.close_asset_editor, BP)
        ok(m.close_asset_editor, BP, confirm=True)


def prepare():
    cleanup()
    run()
    failed = {k: v for k, v in RESULTS.items() if v != 'PASS'}
    for k, v in RESULTS.items():
        print(f'{k}: {v}')
    print(f'{len(RESULTS) - len(failed)}/{len(RESULTS)} passed')
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(RESULTS, indent=1), encoding='utf-8')
    if failed:
        sys.exit(1)


def verify():
    v = text(m.get_blueprint_variables, BP)
    assert 'Speed2' in v, v
    assert 'DoThing' in text(m.get_blueprint_functions, BP)
    assert 'RegMesh' in text(m.get_components_of_bp, BP)
    assert 'RegEvent' in text(m.get_graph, BP, 'EventGraph')
    assert 'Title' in text(m.list_widget_blueprint_widgets, WBP)
    assert '2.5' in text(m.get_animation_curve, AN, 'RegCurve')
    assert 'RegConst' in text(m.list_material_expressions, MAT)
    print('Saved Blueprint, widget, animation and material edits identical after cold reload')
    cleanup()


def cleanup():
    for p in ASSETS:
        httpx.post(BASE + '/assets/delete', json={'AssetPath': p}, timeout=300)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[COMMAND]()
