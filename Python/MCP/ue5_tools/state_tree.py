"""StateTrees."""
import json
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_state_tree(asset_path: str, validate: bool = False) -> str:
    """Inspect native StateTree hierarchy/nodes/compiled states and hashes.

    validate compiles a transient duplicate and returns diagnostics without
    compiling or dirtying the source asset.
    """
    route="validate" if validate else "inspect"
    return httpx.get(f"{app.BASE_URL}/state-trees/{route}", params={"asset_path": asset_path}, timeout=180).text


@mcp.tool()
def list_state_tree_binding_sources(asset_path: str, target_id: str) -> str:
    """List native execution-scope binding source IDs, types and property names for a target."""
    return httpx.get(f"{app.BASE_URL}/state-trees/bindables",params={
        "asset_path":asset_path,"target_id":target_id
    }, timeout=180).text


@mcp.tool()
def list_state_tree_node_types(asset_path: str, kind: str = "task", search: str = "", limit: int = 100) -> str:
    """Discover loaded schema-approved native node structs and editable field metadata.

    Kind is task, global_task, condition, evaluator or consideration. Results
    include instance types, scalar/plain-struct support and native clamps.
    Input category fields may require bindings; the native compiler validates them.
    """
    return httpx.get(f"{app.BASE_URL}/state-trees/node-types",params={
        "asset_path":asset_path,"kind":kind,"search":search,"limit":limit
    },timeout=180).text


@mcp.tool()
def inspect_state_tree_runtime(component_path: str = "", search: str = "", limit: int = 100,
                               pie_instance: int = -1) -> str:
    """Inspect live native StateTree components in the selected PIE world.

    Empty component_path lists components. Reports native status, owner/schema,
    running/paused flags and debug active state names when supported by the build.
    Names are labels and may repeat across linked assets. Does not mutate assets
    or runtime components. Requires an active PIE session.
    """
    return httpx.get(f"{app.BASE_URL}/state-trees/runtime",params={
        "component_path":component_path,"search":search,"limit":limit,"pie_instance":pie_instance
    },timeout=180).text


def control_state_tree_runtime(component_path: str, operation: str, reason: str = "",
                               pie_instance: int = -1, dry_run: bool = False) -> str:
    """Start/restart/stop/pause/resume an explicit authoritative native PIE component.

    Native lifecycle calls affect runtime only. Start on running, repeated pause,
    repeated resume and stop on stopped logic are no-ops. Restart always requests
    a native restart. Pause/resume require running logic. Dry-run validates without
    calling the component. Starting/restarting requires a ready tree reference.
    """
    return httpx.post(f"{app.BASE_URL}/state-trees/runtime",json={
        "ComponentPath":component_path,"Operation":operation,"Reason":reason,
        "PIEInstance":pie_instance,"bDryRun":dry_run
    },timeout=180).text


def send_state_tree_event(component_path: str, event_tag: str, origin: str = "",
                          payload_struct: str = "", payload_properties: dict | None = None,
                          pie_instance: int = -1, dry_run: bool = False) -> str:
    """Submit a registered-tag event to a running unpaused authoritative PIE component.

    Optional payload uses a native plain struct <=64KiB and bounded editable UE
    text fields. Origin is a label <=128 characters. event_submitted means the
    native void API was invoked; event_queue_accepted reports an observed matching
    append to the native queue, not a transition or payload-field consumption. Inspect runtime status to observe execution. Dry-run sends nothing.
    """
    return httpx.post(f"{app.BASE_URL}/state-trees/runtime",json={
        "ComponentPath":component_path,"Operation":"event","EventTag":event_tag,
        "Name":origin,"StructPath":payload_struct,"Properties":payload_properties or {},
        "PIEInstance":pie_instance,"bDryRun":dry_run
    },timeout=180).text


def set_state_tree_runtime_parameters(component_path: str, values: dict | None = None,
                                      reset_parameter: str = "", pie_instance: int = -1,
                                      dry_run: bool = False) -> str:
    """Edit a stopped PIE component's native StateTree reference parameter overrides.

    values maps existing parameter names to UE text or supported persistent reference
    paths. reset_parameter removes one override and inherits the asset default;
    it cannot be combined with values. Stop explicitly first, then start to execute
    the new parameters. Container values use JSON arrays of typed strings encoded
    as the parameter value string. Uses a prepared reference copy; no asset edits or editor undo.
    Inspect runtime reference_parameters and reference_parameter_overrides for state.
    """
    if reset_parameter and values:
        raise ValueError("reset_parameter cannot be combined with values")
    return httpx.post(f"{app.BASE_URL}/state-trees/runtime",json={
        "ComponentPath":component_path,"Operation":"reset_parameter" if reset_parameter else "parameters",
        "Name":reset_parameter,"Properties":values or {},"PIEInstance":pie_instance,"bDryRun":dry_run
    },timeout=180).text


@mcp.tool()
def list_state_tree_node_classes(asset_path: str, kind: str = "task", search: str = "", limit: int = 100) -> str:
    """List loaded schema-approved concrete native/compiled Blueprint node classes and fields."""
    # Registry candidates are not schema approval; authoring validates loaded classes.
    return httpx.get(f"{app.BASE_URL}/state-trees/node-classes",params={
        "asset_path":asset_path,"kind":kind,"search":search,"limit":limit
    },timeout=180).text


@mcp.tool()
def edit_state_tree_schema(asset_path: str, properties: dict | None = None,
                           context_classes: dict | None = None, dry_run: bool = False,
                           save: bool = False, references: dict | None = None, containers: dict | None = None) -> str:
    """Edit owned schema scalar, reference, container and context-class fields.

    context_classes maps schema property names (e.g. ContextActorClass) to full
    compatible class paths. Native property-chain notifications refresh context
    descriptors before dependency preflight/compile. references uses persistent
    object/class paths. containers uses JSON arrays of typed strings or map
    Key/Value rows, with the same bounds as node instance containers. Does not replace schema class.
    """
    return httpx.patch(f"{app.BASE_URL}/state-trees/schema",json={
        "AssetPath":asset_path,"Properties":properties or {},"ContextClasses":context_classes or {},
        "SchemaReferences":references or {},"SchemaContainers":containers or {},
        "bDryRun":dry_run,"bSave":save
    },timeout=180).text


@mcp.tool()
def create_state_tree(asset_path: str,
                      schema_path: str = "/Script/GameplayStateTreeModule.StateTreeComponentSchema",
                      dry_run: bool = False, save: bool = False) -> str:
    """Create a native StateTree with its schema/editor data, root and compiled data."""
    return httpx.post(f"{app.BASE_URL}/state-trees/create", json={
        "AssetPath": asset_path, "SchemaPath": schema_path, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_state_tree_state(asset_path: str, operation: str = "create", state_id: str = "",
                           parent_id: str = "", name: str | None = None, state_type: str = "State",
                           target_state_id: str = "", linked_asset_path: str = "",
                           properties: dict | None = None, index: int = -1, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Create/update/move/delete a native StateTree state with compile preflight.

    Creation needs name, optional parent_id and type State/Group/Subtree/Linked/LinkedAsset.
    Linked needs target_state_id identifying an owned Subtree; LinkedAsset needs
    linked_asset_path with the same native schema. Move
    uses parent_id (empty means top level) and index (-1 appends). Update supports
    name plus scalar settings: Description, SelectionBehavior, TasksCompletion,
    CustomTickRate, bHasCustomTickRate, bEnabled and prerequisite checking.
    Delete requires confirm; incoming external transitions must be edited first.
    Linked dependencies and affected callers compile in one transaction. Incoming bindings from deleted
    nodes to surviving nodes must be removed first.
    """
    methods={"create":"POST","update":"PATCH","move":"POST","delete":"DELETE"}
    if operation not in methods:
        raise ValueError("operation requires create, update, move or delete")
    route="move" if operation=="move" else "states"
    return httpx.request(methods[operation],f"{app.BASE_URL}/state-trees/{route}",json={
        "AssetPath":asset_path,"StateId":state_id,"ParentId":parent_id,
        "Name":name or "","bSetName":name is not None,"StateType":state_type,"TargetStateId":target_state_id,"LinkedAssetPath":linked_asset_path,
        "Properties":properties or {},"Index":index,"bConfirm":confirm,
        "bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def retarget_state_tree_link(asset_path: str, state_id: str, target_state_id: str = "",
                             linked_asset_path: str = "",
                             confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Retarget Linked to an owned Subtree or LinkedAsset to linked_asset_path.

    Retarget requires confirm. Cycles, dangling references and invalid bindings
    fail transient preflight; state and node identities are preserved.
    """
    return httpx.post(f"{app.BASE_URL}/state-trees/links",json={
        "AssetPath":asset_path,"StateId":state_id,"TargetStateId":target_state_id,"LinkedAssetPath":linked_asset_path,
        "bConfirm":confirm,"bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def edit_state_tree_transition(asset_path: str, state_id: str, operation: str = "create",
                                item_id: str = "", trigger: str = "OnStateCompleted",
                                target_type: str = "Succeeded", target_state_id: str = "",
                                event_tag: str = "", payload_struct_path: str = "", consume_event: bool = True,
                                priority: str = "Normal", enabled: bool = True,
                                delay: float = 0, random_delay: float = 0, delayed: bool = False,
                                index: int = -1, confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete an ordered native transition, preserving its conditions.

    Updates replace transition settings. GotoState requires target_state_id;
    OnEvent requires a registered tag. Native success/failure/next-state targets
    and completion/tick/event triggers are supported. Delay/variance are 0..25.
    Delete requires confirm; delegate-based transitions require a binding adapter.
    """
    methods={"create":"POST","update":"PATCH","delete":"DELETE"}
    if operation not in methods:
        raise ValueError("operation requires create, update or delete")
    return httpx.request(methods[operation],f"{app.BASE_URL}/state-trees/transitions",json={
        "AssetPath":asset_path,"StateId":state_id,"ItemId":item_id,"Trigger":trigger,
        "TargetType":target_type,"TargetStateId":target_state_id,"EventTag":event_tag,
        "PayloadStructPath":payload_struct_path,"bConsumeEvent":consume_event,
        "Priority":priority,"bEnabled":enabled,"bDelay":delayed,"Delay":delay,
        "RandomDelay":random_delay,"Index":index,"bConfirm":confirm,
        "bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def edit_state_tree_node(asset_path: str, operation: str = "create", kind: str = "task",
                          state_id: str = "", transition_id: str = "", item_id: str = "",
                          struct_path: str = "", node_class_path: str = "", properties: dict | None = None,
                          instance_properties: dict | None = None, index: int = -1,
                          operand: str = "And", expression_indent: int = 0, set_expression: bool = False,
                          bindings: list[dict] | None = None, confirm: bool = False, dry_run: bool = False, save: bool = False,
                          functions: list[dict] | None = None, instance_references: dict | None = None, instance_containers: dict | None = None,
                          response_curve_keys: list[dict] | None = None, response_curve_asset: str | None = None,
                          enum_scores: dict | None = None, score_enum_path: str = "", name: str | None = None, task_enabled: bool | None = None,
                          considered_for_completion: bool | None = None,
                          condition_evaluation: str | None = None) -> str:
    """Create/update/delete schema-approved native struct nodes with compile preflight.

    name sets/clears the explicit native runtime/debug label. task_enabled controls
    the native task flag (task, single_task or global_task, including Blueprint wrappers).
    considered_for_completion changes editable task completion participation when
    allowed by the schema. condition_evaluation selects the native condition mode.
    Float Input considerations accept response_curve_keys (Time, Value, Interpolation,
    ArriveTangent, LeaveTangent) or response_curve_asset. Empty keys clears the curve.
    Enum Input considerations accept score_enum_path and enum_scores member-to-score
    map. Scores/time/value are normalized; curve keys must increase in time.
    Kind is task, single_task, global_task, evaluator, consideration, enter_condition
    or transition_condition. single_task targets the native slot on schemas that
    disallow multiple tasks.
    Native struct definitions use properties; editable instance data uses
    instance_properties, both scalar/plain-struct UE text. Creation accepts array
    index and condition expression operand/indent. Updates change operand/indent
    only when set_expression is true. Multiply is supported only for considerations;
    conditions require And/Or. Delete requires confirm.
    bindings applies direct property bindings atomically with creation/update.
    Each row uses SourceId, SourcePath, TargetId, TargetPath. Use root for the
    root parameter bag and $new for this node. Replacement requires confirm.
    instance_references maps scalar object/class instance fields to persistent asset
    or class paths; empty/None clears. Soft fields retain soft references.
    instance_containers maps array/set fields to JSON arrays of typed strings,
    including persistent reference paths (<=256 elements, <=64KiB per field).
    Map fields use JSON arrays of {"Key": "typed text", "Value": "typed text"};
    duplicate native keys reject. Nested containers are not supported.
    functions adds native property functions atomically. Rows use StructPath,
    OutputPath, TargetId, TargetPath, Properties, InstanceProperties and Inputs.
    TargetId $new selects this node; input TargetId $function selects the function.
    node_class_path chooses a concrete compiled StateTree Blueprint class instead
    of struct_path. Editable scalar/plain-struct instance fields are supported.
    """
    methods={"create":"POST","update":"PATCH","delete":"DELETE"}
    if operation not in methods:
        raise ValueError("operation requires create, update or delete")
    return httpx.request(methods[operation],f"{app.BASE_URL}/state-trees/nodes",json={
        "AssetPath":asset_path,"StateId":state_id,"TransitionId":transition_id,
        "bSetName":name is not None,"Name":name or "",
        "bSetTaskCompletion":considered_for_completion is not None,
        "bConsideredForCompletion":True if considered_for_completion is None else considered_for_completion,
        "bSetConditionEvaluation":condition_evaluation is not None,"ConditionEvaluation":condition_evaluation or "Evaluated",
        "bSetTaskEnabled":task_enabled is not None,"bEnabled":True if task_enabled is None else task_enabled,
        "ItemId":item_id,"Kind":kind,"StructPath":struct_path,"NodeClassPath":node_class_path,
        "Properties":properties or {},"InstanceProperties":instance_properties or {},"InstanceReferences":instance_references or {},"InstanceContainers":instance_containers or {},
        "bSetResponseCurve":response_curve_keys is not None or response_curve_asset is not None,
        "ResponseCurveKeys":response_curve_keys or [],"ResponseCurveAsset":response_curve_asset or "",
        "bSetEnumScores":enum_scores is not None,"ScoreEnumPath":score_enum_path,"EnumScores":enum_scores or {},
        "Index":index,"Operand":operand,"ExpressionIndent":expression_indent,"bSetExpression":set_expression,"Bindings":bindings or [],"Functions":functions or [],
        "bConfirm":confirm,"bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def edit_state_tree_parameter(asset_path: str, operation: str = "create", state_id: str = "",
                              item_id: str = "", name: str | None = None,
                              parameter_type: str = "Float", type_path: str = "", container_type: str = "",
                              value: str | list[str] | None = None, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete/reset a native root or state property-bag parameter.

    Empty state_id selects the root bag. Creation supports native scalar types,
    Enum (type_path), plain native Struct (type_path), Object/SoftObject and
    Class/SoftClass (type_path is the class constraint). Reference values use
    full persistent asset or native/generated class paths; empty/None clears.
    Other values use UE text. Soft paths stay soft after validation.
    Update changes name/value while preserving the field GUID and binding paths.
    Delete needs confirm and rejects parameters still used by bindings.
    Linked/LinkedAsset state bags inherit their layout; update value creates an override.
    Reset removes the override and its binding, restoring the inherited default;
    it requires confirm. Edit layout/name on the target subtree.
    container_type supports Array/Set; value accepts a list of typed element strings or its JSON text
    (max 256, <=64KiB), including persistent reference paths. Nested containers are
    not supported. Type replacement uses replace_state_tree_parameter_type.
    """
    methods={"create":"POST","update":"PATCH","delete":"DELETE","reset":"POST"}
    if operation not in methods:
        raise ValueError("operation requires create, update, delete or reset")
    route="parameters/reset" if operation=="reset" else "parameters"
    return httpx.request(methods[operation],f"{app.BASE_URL}/state-trees/{route}",json={
        "AssetPath":asset_path,"StateId":state_id,"ItemId":item_id,
        "Name":name or "","bSetName":name is not None,"ParameterType":parameter_type,
        "TypePath":type_path,"ContainerType":container_type,"Value":json.dumps(value) if isinstance(value,list) else value or "","bSetValue":value is not None,
        "bConfirm":confirm,"bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def edit_state_tree_binding(asset_path: str, target_id: str, target_path: str,
                            operation: str = "set", source_id: str = "", source_path: str = "",
                            confirm: bool = False, dry_run: bool = False, save: bool = False, output_binding: bool = False) -> str:
    """Set/delete a direct native property binding with compile preflight.

    IDs identify bindable structs (node IDs or parameter bag IDs); root aliases
    the root bag. Paths use native Foo.Bar[0] syntax. Native execution scope and
    compiler compatibility apply. Replacing/deleting bindings needs confirm.
    Required node inputs may be supplied atomically through edit_state_tree_node.
    output_binding uses native reverse direction: target copies into source.
    Property functions use edit_state_tree_function.
    """
    if operation not in {"set","delete"}:
        raise ValueError("operation requires set or delete")
    return httpx.request("POST" if operation=="set" else "DELETE",f"{app.BASE_URL}/state-trees/bindings",json={
        "AssetPath":asset_path,"Binding":{"SourceId":source_id,"SourcePath":source_path,
        "TargetId":target_id,"TargetPath":target_path,"bOutput":output_binding},"bConfirm":confirm,
        "bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def set_state_tree_required_event(asset_path: str, state_id: str, enabled: bool = True,
                                  event_tag: str = "", payload_struct_path: str = "",
                                  consume_event: bool = True, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Set/clear the native event required to enter a state.

    Enabled descriptors need a registered tag or native payload type. Inspection
    exposes event_source_id for native event/payload property bindings.
    """
    return httpx.patch(f"{app.BASE_URL}/state-trees/states",json={
        "AssetPath":asset_path,"StateId":state_id,"bSetRequiredEvent":True,"bEnabled":enabled,
        "EventTag":event_tag,"PayloadStructPath":payload_struct_path,"bConsumeEvent":consume_event,
        "bDryRun":dry_run,"bSave":save
    },timeout=180).text


@mcp.tool()
def move_state_tree_transition(asset_path: str, state_id: str, item_id: str, index: int = -1,
                               dry_run: bool = False, save: bool = False) -> str:
    """Reorder a native transition; index is final position, -1 appends; keeps conditions/IDs."""
    return httpx.post(f"{app.BASE_URL}/state-trees/transitions/move",json={
        "AssetPath":asset_path,"StateId":state_id,"ItemId":item_id,"Index":index,
        "bDryRun":dry_run,"bSave":save
    },timeout=180).text


@mcp.tool()
def move_state_tree_node(asset_path: str, item_id: str, kind: str = "task", state_id: str = "",
                         transition_id: str = "", index: int = -1, dry_run: bool = False,
                         save: bool = False) -> str:
    """Reorder a node within its current native collection while preserving GUID/bindings.

    Index is the final zero-based position; -1 appends. Native compile preflight
    checks binding execution scope and condition/consideration expression semantics.
    Single-task slots have no order. Moving between collections is not supported.
    """
    return httpx.post(f"{app.BASE_URL}/state-trees/nodes/move",json={
        "AssetPath":asset_path,"ItemId":item_id,"Kind":kind,"StateId":state_id,
        "TransitionId":transition_id,"Index":index,"bDryRun":dry_run,"bSave":save
    },timeout=180).text


@mcp.tool()
def move_state_tree_parameter(asset_path: str, item_id: str, state_id: str = "", index: int = -1,
                              dry_run: bool = False, save: bool = False) -> str:
    """Reorder a root/state property-bag field, preserving GUID/value; -1 appends.

    Linked layouts inherit ordering from their source and cannot be reordered here.
    """
    return httpx.post(f"{app.BASE_URL}/state-trees/parameters/move",json={
        "AssetPath":asset_path,"ItemId":item_id,"StateId":state_id,"Index":index,
        "bDryRun":dry_run,"bSave":save
    },timeout=180).text


@mcp.tool()
def replace_state_tree_parameter_type(asset_path: str, item_id: str, parameter_type: str,
                                      state_id: str = "", type_path: str = "", container_type: str = "", value: str | list[str] | None = None,
                                      confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Replace a root/state scalar parameter type while retaining its field GUID/name.

    Confirmation required. Native property-bag migration converts compatible values;
    provide value to explicitly initialize the new type. Existing binding/caller
    compatibility is checked through dependency preflight. Linked layouts must be
    edited at their source. container_type chooses None/Array/Set. Simultaneous rename is not supported.
    """
    return httpx.post(f"{app.BASE_URL}/state-trees/parameters/type",json={
        "AssetPath":asset_path,"ItemId":item_id,"StateId":state_id,"ParameterType":parameter_type,
        "TypePath":type_path,"ContainerType":container_type,"Value":json.dumps(value) if isinstance(value,list) else value or "","bSetValue":value is not None,
        "bConfirm":confirm,"bDryRun":dry_run,"bSave":save
    },timeout=180).text


@mcp.tool()
def compile_state_tree(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Compile through the native StateTree editor pipeline after transient preflight."""
    return httpx.post(f"{app.BASE_URL}/state-trees/compile",json={
        "AssetPath":asset_path,"bDryRun":dry_run,"bSave":save
    }, timeout=180).text


@mcp.tool()
def edit_state_tree_function(asset_path: str, operation: str = "create", item_id: str = "",
                             struct_path: str = "", target_id: str = "", target_path: str = "",
                             output_path: str = "", properties: dict | None = None,
                             instance_properties: dict | None = None, inputs: list[dict] | None = None,
                             confirm: bool = False, dry_run: bool = False, save: bool = False, instance_references: dict | None = None, instance_containers: dict | None = None) -> str:
    """Create/update/delete a native StateTree property function with compile preflight.

    Creation attaches the function output to target_id/target_path. Empty output_path
    selects the sole native Output property. Use discovery kind property_function.
    Inputs use SourceId/SourcePath/TargetId/TargetPath; $function selects this function
    as input target. Update edits settings/inputs by item_id. Delete requires confirm
    and removes owned nested input functions; external references must be removed first.
    Required function inputs should be supplied atomically on creation.
    """
    methods = {"create": "POST", "update": "PATCH", "delete": "DELETE"}
    if operation not in methods:
        raise ValueError("operation requires create, update or delete")
    return httpx.request(methods[operation], f"{app.BASE_URL}/state-trees/functions", json={
        "AssetPath": asset_path, "ItemId": item_id, "StructPath": struct_path,
        "Binding": {"TargetId": target_id, "TargetPath": target_path, "SourcePath": output_path},
        "Properties": properties or {}, "InstanceProperties": instance_properties or {},
        "InstanceReferences": instance_references or {}, "InstanceContainers": instance_containers or {}, "Bindings": inputs or [], "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_state_tree_schemas(search: str = "", limit: int = 100) -> str:
    """Discover loaded concrete native StateTree schemas and default capabilities.

    Reports supported state/selection types, task/condition/evaluator/utility flags,
    default context requirements and editable setting metadata. Optional unloaded
    modules are not enumerated. Actual asset settings may specialize the defaults.
    """
    return httpx.get(f"{app.BASE_URL}/state-trees/schemas", params={
        "search": search, "limit": limit
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
state_tree_runtime = merged_tool("state_tree_runtime", {
    "control_state_tree_runtime": control_state_tree_runtime,
    "send_state_tree_event": send_state_tree_event,
    "set_state_tree_runtime_parameters": set_state_tree_runtime_parameters,
})
