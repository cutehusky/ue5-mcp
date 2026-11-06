"""Behavior Trees, Blackboards, EQS, AI perception and Smart Objects."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp, _ext


@mcp.tool()
def list_environment_query_owners(pie_instance: int = -1, search: str = "", limit: int = 100) -> str:
    """Find live PIE actor paths and authority for explicit EQS request owners."""
    return httpx.get(f"{app.BASE_URL}/environment-queries/runtime/owners", params={
        "pie_instance": pie_instance, "search": search, "limit": limit
    }).text


def run_environment_query(asset_path: str, owner_path: str, request_id: str = "",
                           run_mode: str = "all_matching", parameters: list[dict] | None = None,
                           pie_instance: int = -1, max_items: int = 128,
                           timeout_seconds: float = 10, dry_run: bool = False) -> str:
    """Queue a native asynchronous EQS request for an authoritative live PIE actor.

    Parameter rows use Name, Type (float/int/bool), Value (scalar text), matching
    declared query-parameter bindings. Omitted parameters use native asset defaults.
    Modes: all_matching, single, random_best_5, random_best_25. Poll by request_id;
    an empty ID generates one. max_items caps retained output, not generator work.
    Timeout/abort cannot preempt a synchronous native generator mid-call. No asset
    edits or undo transaction. Dry-run validates without queueing a request.
    """
    return httpx.post(f"{app.BASE_URL}/environment-queries/runtime", json={
        "Operation": "run", "AssetPath": asset_path, "OwnerPath": owner_path,
        "RequestId": request_id, "RunMode": run_mode, "Parameters": parameters or [],
        "PIEInstance": pie_instance, "MaxItems": max_items,
        "TimeoutSeconds": timeout_seconds, "bDryRun": dry_run
    }).text


@mcp.tool()
def inspect_environment_query_requests(request_id: str = "", pie_instance: int = -1) -> str:
    """Read owned native EQS status/results, or list retained requests in one PIE world.

    Results include native status/ID, selected option, item type, scores, locations
    and actor paths where available. Storage holds at most 64 requests/16 running;
    completed snapshots expire after 120 seconds. World cleanup removes its records.
    """
    return httpx.get(f"{app.BASE_URL}/environment-queries/runtime", params={
        "request_id": request_id, "pie_instance": pie_instance
    }).text


def control_environment_query_request(request_id: str, operation: str = "cancel",
                                       pie_instance: int = -1, dry_run: bool = False) -> str:
    """Cancel an owned native request or forget its retained snapshot.

    operation requires cancel or forget. Forget also aborts running work. Repeated
    cancel of a terminal request is a no-op. Targets must belong to the selected
    PIE world. Dry-run does not change the record or invoke native abort.
    """
    if operation not in ["cancel", "forget"]:
        raise ValueError("operation requires cancel or forget")
    return httpx.post(f"{app.BASE_URL}/environment-queries/runtime", json={
        "Operation": operation, "RequestId": request_id,
        "PIEInstance": pie_instance, "bDryRun": dry_run
    }).text


@mcp.tool()
def inspect_environment_query(asset_path: str) -> str:
    """Inspect native EQS options, generators, tests, providers and compiled order."""
    return httpx.get(f"{app.BASE_URL}/environment-queries/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def create_environment_query(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Create an empty native EQS asset in a new /Game package."""
    return httpx.post(f"{app.BASE_URL}/environment-queries/create", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def initialize_environment_query_graph(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Initialize the native EQS editor graph, preserving existing runtime options."""
    return httpx.post(f"{app.BASE_URL}/environment-queries/graph", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def edit_environment_query_option(asset_path: str, operation: str = "create", node_guid: str = "",
                                   generator_class: str = "", x: int = 0, y: int = 200,
                                   properties: dict | None = None, classes: dict | None = None,
                                   provider_values: dict | None = None, named_parameters: dict | None = None,
                                   confirm: bool = False, dry_run: bool = False, save: bool = False,
                                   generator_tree: list[dict] | None = None) -> str:
    """Create/update/delete one native EQS option and its generator settings.

    Creation requires a concrete generator_class and unique X (fallback order).
    properties use native scalar/plain-struct UE text. classes maps class fields
    to compatible class paths. provider_values maps native Float/Int/Bool provider
    fields to scalar UE text. named_parameters binds those fields to query names;
    empty names clear bindings. Generator class changes require recreation.
    Delete requires confirm. Creation can use generator_tree prefix rows (see
    replace_environment_query_generators). Updates of a whole tree use that helper.
    Custom providers and forced mixed item layouts require separate adapters.
    """
    methods={"create": "POST", "update": "PATCH", "delete": "DELETE"}
    if operation not in methods:
        raise ValueError("operation requires create, update or delete")
    if generator_tree is not None and operation != "create":
        raise ValueError("generator_tree here requires create; use replace_environment_query_generators")
    return httpx.request(methods[operation], f"{app.BASE_URL}/environment-queries/options", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "ClassPath": generator_class,
        "X": x, "Y": y, "Properties": properties or {}, "Classes": classes or {},
        "ProviderValues": provider_values or {}, "NamedParameters": named_parameters or {},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save,
        "bSetGeneratorTree": generator_tree is not None, "GeneratorTree": generator_tree or []
    }).text


@mcp.tool()
def edit_environment_query_test(asset_path: str, operation: str = "create", node_guid: str = "",
                                 parent_guid: str = "", test_class: str = "", index: int = -1,
                                 enabled: bool | None = None, properties: dict | None = None,
                                 classes: dict | None = None, provider_values: dict | None = None,
                                 named_parameters: dict | None = None, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete a native EQS test compatible with its option item type.

    Creation uses parent_guid and test_class; index -1 appends. Updates can reorder
    by array index and change enabled/settings using the same typed maps as options.
    Native bAutoSortTests can change execution ordering independently of author order.
    Delete requires confirm. Edits are unavailable during PIE.
    """
    methods={"create": "POST", "update": "PATCH", "delete": "DELETE"}
    if operation not in methods:
        raise ValueError("operation requires create, update or delete")
    return httpx.request(methods[operation], f"{app.BASE_URL}/environment-queries/tests", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "ParentGuid": parent_guid,
        "ClassPath": test_class, "Index": index, "bSetEnabled": enabled is not None,
        "bEnabled": True if enabled is None else enabled, "Properties": properties or {},
        "Classes": classes or {}, "ProviderValues": provider_values or {},
        "NamedParameters": named_parameters or {}, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def replace_environment_query_generators(asset_path: str, node_guid: str, generator_tree: list[dict],
                                          dry_run: bool = False, save: bool = False) -> str:
    """Replace one option's native generator tree, preserving its GUID and tests.

    Prefix rows use ClassPath, Children and optional Properties/Classes/
    ProviderValues/NamedParameters maps. Composite rows require 1..16 children;
    leaves require zero. Example: Composite(2), CurrentLocation, CurrentLocation,
    using /Script/AIModule.EnvQueryGenerator_Composite and _CurrentLocation paths.
    Children must share exactly the same item type and be synchronous. Bounded to
    depth 8, 127 generators and 256 settings per expression. Replacement resets
    unspecified fields to class defaults. Existing tests must support the new
    item type. Dry-run/no-op, transactions and save apply; PIE edits reject.
    """
    return httpx.patch(f"{app.BASE_URL}/environment-queries/generators", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "GeneratorTree": generator_tree,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def layout_environment_query(asset_path: str, positions: list[dict], dry_run: bool = False, save: bool = False) -> str:
    """Set option NodeGuid/X/Y positions; unique X determines native fallback order."""
    return httpx.post(f"{app.BASE_URL}/environment-queries/layout", json={
        "AssetPath": asset_path, "Positions": positions, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def compile_environment_query(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Rebuild native EQS runtime option/test arrays from the editor graph."""
    return httpx.post(f"{app.BASE_URL}/environment-queries/compile", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def inspect_behavior_tree_runtime(component_path: str = "", pie_instance: int = -1) -> str:
    """Inspect registered live Behavior Tree components in one PIE world.

    An empty path lists up to 256 components. Reports authority, execution state,
    source/current trees and instantiated dynamic task defaults/current overrides.
    Choose an explicit pie_instance when multiple worlds exist.
    """
    return httpx.get(f"{app.BASE_URL}/behavior-trees/runtime", params={
        "component_path": component_path, "pie_instance": pie_instance
    }).text


@mcp.tool()
def replace_behavior_tree_runtime_subtree(component_path: str, injection_tag: str,
                                           asset_path: str = "", pie_instance: int = -1,
                                           dry_run: bool = False) -> str:
    """Replace currently instantiated dynamic tasks with an exact registered tag.

    Requires an authoritative running unpaused component in the selected PIE
    world. Empty asset_path clears/disables the subtree; active branch execution
    can fail. Preflights effective dependencies, Blackboard IDs and ignored root
    decorators. Active replacements request native restart asynchronously; inspect
    execution separately. New task instances start from authored defaults.
    Runtime changes do not edit assets or create undo transactions.
    """
    return httpx.post(f"{app.BASE_URL}/behavior-trees/runtime/dynamic-subtree", json={
        "ComponentPath": component_path, "InjectionTag": injection_tag,
        "AssetPath": asset_path, "PIEInstance": pie_instance, "bDryRun": dry_run
    }).text


@mcp.tool()
def inspect_behavior_tree(asset_path: str) -> str:
    """Inspect native graph/root, tasks/services/decorators, pins, properties and selector bindings."""
    return httpx.get(f"{app.BASE_URL}/behavior-trees/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def create_behavior_tree(asset_path: str) -> str:
    """Create an empty Behavior Tree asset."""
    return httpx.post(f"{app.BASE_URL}/behavior-trees/create", json={"AssetPath": asset_path}).text


@mcp.tool()
def validate_behavior_tree(asset_path: str) -> str:
    """Validate native graph topology, compiled execution data and direct Blackboard compatibility."""
    return httpx.post(f"{app.BASE_URL}/behavior-trees/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def initialize_behavior_tree_graph(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Explicitly create the native editor graph, preserving existing runtime nodes/Blackboard.

    Inspection does not create a graph. Editing is restricted to /Game assets with
    the native graph/schema and stopped PIE/simulation. Up to 512 nodes, depth 64.
    """
    return httpx.post(f"{app.BASE_URL}/behavior-trees/graph", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def create_behavior_tree_node(asset_path: str, class_path: str, parent_guid: str = "",
                              x: int = 0, y: int = 0, properties: dict | None = None,
                              blackboard_selectors: dict | None = None,
                              dry_run: bool = False, save: bool = False,
                              subtree_path: str | None = None, injection_tag: str | None = None) -> str:
    """Create a native graph node from a concrete composite/task/service/decorator class.

    Services/decorators require a composite/task parent_guid; composites/tasks use
    separate links. Properties are top-level editable scalar/plain-struct UE text
    values (e.g. WaitTime='(DefaultValue=0.1,Key=None)'). Blackboard selectors map
    a property name to a key name; native selector filters and ValueOrBBKey bindings
    are preflighted. SimpleParallel uses output 0 for one main task and output 1 for one background
    task/composite; pin roles are independent of X position. Its FinishMode accepts
    AbortBackground or WaitForBackground through properties. UObject/container
    properties and compound decorator logic need dedicated adapters.
    RunBehavior uses subtree_path for its static asset reference. None preserves it;
    empty clears it. References require compiled roots, native Blackboard/key-layout
    compatibility and acyclic dependencies (depth 32, at most 256 assets).
    Native root-decorator previews are injected read-only with scoped API GUIDs.
    Root decorators require the referenced editor graph; compound expressions are supported.
    RunBehaviorDynamic uses subtree_path for its optional default and injection_tag
    for a registered Gameplay Tag (None preserves; empty clears). Dynamic defaults
    cannot have root decorators, which native runtime execution would ignore.
    Editing asset defaults is rejected during PIE. Returns node_guid.
    """
    return httpx.post(f"{app.BASE_URL}/behavior-trees/nodes", json={
        "AssetPath": asset_path, "ClassPath": class_path, "ParentGuid": parent_guid,
        "X": x, "Y": y, "Properties": properties or {},
        "BlackboardSelectors": blackboard_selectors or {}, "bDryRun": dry_run, "bSave": save,
        "bSetSubtree": subtree_path is not None, "SubtreePath": subtree_path or "",
        "bSetInjectionTag": injection_tag is not None, "InjectionTag": injection_tag or ""
    }).text


@mcp.tool()
def update_behavior_tree_node(asset_path: str, node_guid: str, properties: dict | None = None,
                              blackboard_selectors: dict | None = None,
                              dry_run: bool = False, save: bool = False,
                              subtree_path: str | None = None, injection_tag: str | None = None) -> str:
    """Transactionally edit native node settings/selectors after transient preflight.

    See create_behavior_tree_node for value format and supported fields. Root,
    injected and read-only nodes cannot be edited here. X coordinates/layout are
    controlled separately and affect native child execution order.
    """
    return httpx.patch(f"{app.BASE_URL}/behavior-trees/nodes", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "Properties": properties or {},
        "BlackboardSelectors": blackboard_selectors or {}, "bDryRun": dry_run, "bSave": save,
        "bSetSubtree": subtree_path is not None, "SubtreePath": subtree_path or "",
        "bSetInjectionTag": injection_tag is not None, "InjectionTag": injection_tag or ""
    }).text


@mcp.tool()
def create_behavior_tree_decorator_logic(asset_path: str, parent_guid: str, logic: list[dict],
                                         name: str = "Logic", dry_run: bool = False, save: bool = False) -> str:
    """Attach a native compound decorator using prefix rows.

    Rows use Operation (and/or/not/test). AND/OR require Children 2..16;
    NOT requires Children 1. Tests use ClassPath, Properties and
    BlackboardSelectors like create_behavior_tree_node. Example:
    [{"Operation":"not","Children":1}, {"Operation":"test",
      "ClassPath":"/Script/AIModule.BTDecorator_Blackboard",
      "BlackboardSelectors":{"BlackboardKey":"Gate"}}].
    """
    return httpx.post(f"{app.BASE_URL}/behavior-trees/decorator-logic", json={
        "AssetPath": asset_path, "ParentGuid": parent_guid, "Logic": logic,
        "bSetCompoundName": True, "CompoundName": name, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def replace_behavior_tree_decorator_logic(asset_path: str, node_guid: str, logic: list[dict],
                                          name: str | None = None, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Replace a compound expression transactionally; omitted name preserves it.

    Uses the prefix row format of create_behavior_tree_decorator_logic.
    Leaf settings replace the full expression and start from class defaults.
    """
    return httpx.patch(f"{app.BASE_URL}/behavior-trees/decorator-logic", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "Logic": logic,
        "bSetCompoundName": name is not None, "CompoundName": name or "",
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def delete_behavior_tree_node(asset_path: str, node_guid: str, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Delete a node with its attached subnodes/links; preview affected_nodes via dry-run.

    Requires confirm for mutation. Linked children remain disconnected graph nodes;
    they are not recursively deleted. Root/read-only/injected nodes are protected.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/behavior-trees/nodes", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def set_behavior_tree_link(asset_path: str, node_guid: str, target_guid: str,
                           operation: str = "connect", pin_index: int = 0,
                           target_pin_index: int = 0, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Connect/disconnect a top-level output to input using the native graph schema.

    Pin indexes are per direction (0-8), as returned by inspection. Schema checks
    root/composite/task constraints and cycles. Replacing existing links requires
    confirm; dry-run reports affected_nodes. Subnodes use their parent attachment.
    """
    if operation not in {"connect", "disconnect"}:
        return "operation must be connect or disconnect"
    return httpx.request("POST" if operation == "connect" else "DELETE",
                         f"{app.BASE_URL}/behavior-trees/links", json={
        "AssetPath": asset_path, "NodeGuid": node_guid, "TargetGuid": target_guid,
        "PinIndex": pin_index, "TargetPinIndex": target_pin_index, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def layout_behavior_tree_nodes(asset_path: str, positions: list[dict],
                               dry_run: bool = False, save: bool = False) -> str:
    """Set unique top-level node positions: [{NodeGuid, X, Y}], each within +/-1e6.

    X positions determine native sibling execution order, so this recompiles the
    native tree. Inspection reports persisted compiled_children order and transient native
    execution_index values (these caches refresh on compilation/runtime load). Up to 512
    rows; subnodes and injected nodes are not positioned independently.
    """
    return httpx.post(f"{app.BASE_URL}/behavior-trees/layout", json={
        "AssetPath": asset_path, "Positions": positions, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def set_behavior_tree_blackboard(asset_path: str, blackboard_path: str = "",
                                 confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Set/clear the root and compiled-tree Blackboard together; changes require confirm.

    Existing selectors may need repair; inspect validation errors. Native key IDs
    are refreshed by graph compilation, without rewriting arbitrary Blueprint data.
    """
    return httpx.patch(f"{app.BASE_URL}/behavior-trees/settings", json={
        "AssetPath": asset_path, "BlackboardPath": blackboard_path, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def compile_behavior_tree(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Rebuild native runtime execution data from the graph and report validation.

    Compilation is an explicit mutation. Dry-run checks current bounded topology
    and reports that a rebuild would occur. Validation alone does not execute AI.
    """
    return httpx.post(f"{app.BASE_URL}/behavior-trees/compile", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def inspect_blackboard(asset_path: str) -> str:
    """Inspect Blackboard keys, types, and parent Blackboard."""
    return httpx.get(f"{app.BASE_URL}/blackboards/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def create_blackboard(asset_path: str) -> str:
    """Create an empty Blackboard asset."""
    return httpx.post(f"{app.BASE_URL}/blackboards/create", json={"AssetPath": asset_path}).text


@mcp.tool()
def add_blackboard_key(asset_path: str, key_name: str, key_type: str,
                       category: str | None = None, description: str | None = None,
                       instance_synced: bool | None = None,
                       dry_run: bool = False, save: bool = False,
                       type_settings: dict | None = None) -> str:
    """Add a local native Blackboard key; names use UE FName case-insensitive identity.

    Metadata is optional. instance_synced controls shared native Blackboard values;
    it is not an instance-editable flag. The native SelfActor key is reserved.
    Optional type_settings uses the typed fields documented by update_blackboard_key;
    this configures defaults atomically with creation without changing class defaults.
    """
    return httpx.post(f"{app.BASE_URL}/blackboards/keys", json={
        "AssetPath": asset_path, "KeyName": key_name, "KeyType": key_type,
        "bSetCategory": category is not None, "Category": category or "",
        "bSetDescription": description is not None, "Description": description or "",
        "bSetInstanceSynced": instance_synced is not None,
        "bInstanceSynced": instance_synced or False, "bDryRun": dry_run, "bSave": save,
        "bSetTypeSettings": type_settings is not None, "TypeSettings": type_settings or {}
    }).text


@mcp.tool()
def update_blackboard_key(asset_path: str, key_name: str, new_key_name: str = "",
                          key_type: str = "", category: str | None = None,
                          description: str | None = None, instance_synced: bool | None = None,
                          confirm: bool = False, dry_run: bool = False, save: bool = False,
                          type_settings: dict | None = None) -> str:
    """Edit a local Blackboard key with native transaction and descendant preflight.

    Empty type/name preserves them. Type replacement resets type-specific settings.
    Structural changes with referencers require confirm; dry-run lists packages.
    Rename updates direct FBlackboardKeySelector properties in related native
    Behavior Tree packages, including trees using descendant Blackboards.
    type_settings supports exact native Bool/Int/Float/Name/String/Vector/Rotator/
    Object/Class/Enum keys. Use bSetDefault plus BoolValue/IntValue/FloatValue/
    TextValue/VectorValue/RotationValue/ReferenceValue for the selected type.
    bSetUseDefault/bUseDefault controls Vector/Rotator initialization independently.
    bSetBaseClass/BaseClass constrains Object/Class; bSetEnumType/EnumTypePath
    configures Enum. bSetNativeEnumName/NativeEnumName sets a full /Script enum
    path override or clears it with an empty value. References use object paths;
    empty default ReferenceValue clears the reference. Enum values must fit a byte.
    Constraint changes with referencers require confirm. Settings are preflighted
    on a transient key; metadata and settings apply together in one transaction.
    Struct/custom/deprecated key settings and arbitrary Blueprint/string references
    remain separate adapters.
    Save also saves Behavior Trees whose selectors were renamed; inspect dry-run first.
    """
    return httpx.patch(f"{app.BASE_URL}/blackboards/keys", json={
        "AssetPath": asset_path, "KeyName": key_name, "NewKeyName": new_key_name,
        "KeyType": key_type, "bSetCategory": category is not None, "Category": category or "",
        "bSetDescription": description is not None, "Description": description or "",
        "bSetInstanceSynced": instance_synced is not None, "bInstanceSynced": instance_synced or False,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save,
        "bSetTypeSettings": type_settings is not None, "TypeSettings": type_settings or {}
    }).text


@mcp.tool()
def set_blackboard_parent(asset_path: str, parent_path: str = "", confirm: bool = False,
                          dry_run: bool = False, save: bool = False) -> str:
    """Set or clear the parent with cycle/key-conflict checks and native cache propagation.

    Structural edits with referencers require confirm; dry-run lists packages.
    Native AI configuration manages the persistent SelfActor key.
    """
    return httpx.patch(f"{app.BASE_URL}/blackboards/settings", json={
        "AssetPath": asset_path, "bSetParent": True, "ParentPath": parent_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def validate_blackboard(asset_path: str) -> str:
    """Validate bounded parent chains, effective key names/types and native ID capacity.

    This is structural validation; it does not execute a Behavior Tree or validate
    arbitrary Blueprint references, Struct/custom/deprecated key defaults. Exact
    native scalar/vector/rotation/Object/Class/Enum settings are checked.
    """
    return httpx.get(f"{app.BASE_URL}/blackboards/validate", params={"asset_path": asset_path}).text


@mcp.tool()
def remove_blackboard_key(asset_path: str, key_name: str, confirm: bool = False,
                          dry_run: bool = False, save: bool = False) -> str:
    """Delete a local key transactionally. Referencers require confirm; preview via dry_run.

    External selectors are not rewritten on deletion. SelfActor is reserved.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/blackboards/keys", json={
        "AssetPath": asset_path, "KeyName": key_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def inspect_ai_perception_runtime(component_path: str = "", search: str = "", limit: int = 100,
                                  pie_instance: int = -1) -> str:
    """Inspect native AI Perception components in the selected live PIE world.

    Reports owner/authority, dominant sense, configured sense classes, known targets
    and bounded stimulus snapshots (age, strength, sensed/active/expired, locations).
    Empty component_path lists components; explicit paths must belong to selected PIE.
    """
    return httpx.get(f"{app.BASE_URL}/ai-perception/runtime", params={
        "component_path": component_path, "search": search, "limit": limit,
        "pie_instance": pie_instance
    }, timeout=180).text


def control_ai_perception_runtime(component_path: str, operation: str, sense_class_path: str = "",
                                  actor_path: str = "", enabled: bool = True, confirm: bool = False,
                                  dry_run: bool = False, pie_instance: int = -1) -> str:
    """Control an explicit authoritative registered AI Perception PIE listener.

    Operations: sense enables/disables a configured loaded sense class; dominant
    selects a configured sense as native dominant sense; refresh
    requests a native listener update; forget_actor/forget_all clear native memory
    and require confirm. Actors/components must belong to selected PIE world.
    Refresh is asynchronous; forgetting does not prevent subsequent perception.
    """
    return httpx.post(f"{app.BASE_URL}/ai-perception/runtime", json={
        "ComponentPath": component_path, "Operation": operation, "SenseClassPath": sense_class_path,
        "ActorPath": actor_path, "bEnabled": enabled, "bConfirm": confirm,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def report_ai_perception_noise(actor_path: str, loudness: float = 1.0, max_range: float = 0.0,
                               tag: str = "", location: dict | None = None,
                               dry_run: bool = False, pie_instance: int = -1) -> str:
    """Submit a native asynchronous hearing event from an authoritative PIE actor.

    Defaults to actor location; optional location uses X/Y/Z. Zero max_range means
    native unlimited event range, while listener hearing radius still applies.
    Submission does not guarantee perception: sense config and affiliation apply.
    """
    return httpx.post(f"{app.BASE_URL}/ai-perception/runtime/noise", json={
        "ActorPath": actor_path, "Loudness": loudness, "MaxRange": max_range, "Tag": tag,
        "Location": location or {}, "bUseActorLocation": location is None,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def list_ai_perception_classes(search: str = "", limit: int = 100) -> str:
    """List loaded concrete AI Perception sense/config classes and editable defaults.

    Includes config-to-sense mapping, field types, clamps and read-only metadata.
    Optional unloaded modules and Blueprint assets are not enumerated.
    """
    return httpx.get(f"{app.BASE_URL}/ai-perception/classes", params={
        "search": search, "limit": limit
    }, timeout=180).text


def configure_ai_perception_runtime(component_path: str, config_class_path: str,
                                    properties: dict | None = None, confirm: bool = False,
                                    dry_run: bool = False, pie_instance: int = -1) -> str:
    """Configure a native sense on an authoritative registered PIE listener.

    Uses loaded concrete config class and editable numeric/bool/enum/plain-struct
    UE text settings. Existing exact-class config is copied for validation; adding
    a new sense requires confirm. Applies native ConfigureSense and requests refresh.
    Runtime only; does not persist editor/Blueprint defaults or alter enable state.
    """
    return httpx.post(f"{app.BASE_URL}/ai-perception/runtime", json={
        "ComponentPath": component_path, "Operation": "configure", "ConfigClassPath": config_class_path,
        "Properties": properties or {}, "bConfirm": confirm, "bDryRun": dry_run,
        "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def report_ai_perception_damage(damaged_actor_path: str, instigator_path: str, amount: float = 1.0,
                                tag: str = "", event_location: dict | None = None,
                                hit_location: dict | None = None, dry_run: bool = False,
                                pie_instance: int = -1) -> str:
    """Submit a native damage perception stimulus between authoritative PIE actors.

    Defaults to instigator/damaged actor locations; explicit event_location and
    hit_location must be supplied together as X/Y/Z objects. This reports perception
    only: it does not apply gameplay damage. Reception is native/asynchronous.
    """
    if (event_location is None) != (hit_location is None):
        raise ValueError("Supply both event_location and hit_location, or neither")
    return httpx.post(f"{app.BASE_URL}/ai-perception/runtime/damage", json={
        "ActorPath": damaged_actor_path, "InstigatorPath": instigator_path,
        "DamageAmount": amount, "Tag": tag, "Location": event_location or {},
        "HitLocation": hit_location or {}, "bUseActorLocation": event_location is None,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def control_ai_perception_source(actor_path: str, sense_class_path: str, operation: str = "register",
                                 confirm: bool = False, dry_run: bool = False,
                                 pie_instance: int = -1) -> str:
    """Request native PIE stimulus-source registration for one actor/sense.

    register/unregister use the native world perception system. Unregister requires
    confirm. Actor must be authoritative in selected PIE; sense class must be loaded.
    Response confirms submission, not final registration state. Auto-registration
    may register actors again; this does not persist a stimuli-source component.
    """
    return httpx.post(f"{app.BASE_URL}/ai-perception/runtime/sources", json={
        "ActorPath": actor_path, "SenseClassPath": sense_class_path, "Operation": operation,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def configure_ai_perception_component(component_path: str, operation: str = "configure",
                                      config_class_path: str = "", properties: dict | None = None,
                                      sense_class_path: str = "", confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Configure a placed editor AI Perception component with transaction/save support.

    Requires stopped PIE and a /Game actor package. configure validates a copied
    native config and editable numeric/bool/enum/plain-struct UE text fields; adding
    a sense requires confirm. dominant selects an already configured sense class.
    Does not edit Blueprint templates; component_path must identify placed component.
    """
    return httpx.patch(f"{app.BASE_URL}/ai-perception/configuration", json={
        "ComponentPath": component_path, "Operation": operation, "ConfigClassPath": config_class_path,
        "Properties": properties or {}, "SenseClassPath": sense_class_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ai_perception_components(component_path: str = "", search: str = "", limit: int = 100) -> str:
    """Inspect placed editor AI Perception components and stored sense configuration.

    Empty path lists current editor-world components. Reports owner/package/dirty
    state, dominant sense and bounded config fields. Runtime enablement and stimuli
    require inspect_ai_perception_runtime; editor defaults are not live perception.
    """
    return httpx.get(f"{app.BASE_URL}/ai-perception/configuration", params={
        "component_path": component_path, "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def inspect_ai_perception_sources(search: str = "", limit: int = 100) -> str:
    """Inspect placed editor stimuli-source components and stored registration senses."""
    return httpx.get(f"{app.BASE_URL}/ai-perception/sources", params={"search": search, "limit": limit}).text


@mcp.tool()
def configure_ai_perception_source(component_path: str, sense_classes: list[str], auto_register: bool = True,
                                   confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Replace placed source component auto-registration and sense list with transaction/save.

    Requires stopped PIE, a /Game placed component and confirm for changed settings.
    Sense classes must be unique, concrete and loaded; empty list clears senses.
    """
    return httpx.patch(f"{app.BASE_URL}/ai-perception/sources", json={
        "ComponentPath": component_path, "SenseClasses": sense_classes, "bEnabled": auto_register,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def smart_object_definition(asset_path: str, operation: str = "Inspect", slot_index: int = -1,
                            field: str = "", value_text: str = "", slot_name: str = "",
                            expected_snapshot: str = "", allow_remove: bool = False,
                            confirm: bool = False, dry_run: bool = True) -> str:
    """Smart Object definitions: Inspect/Create/AddSlot/SetSlot/RemoveSlot.
    Create takes a new /Game/Path/Name.Name object path. AddSlot takes optional slot_name and Offset text
    in value_text, e.g. "(X=0,Y=0,Z=0)". SetSlot field is one of Name/Offset/Rotation/bEnabled/ActivityTags/
    UserTagFilter/RuntimeTags/Color/SelectionPreconditions with UE ImportText value_text. Edits need confirm
    and exact snapshot; RemoveSlot needs allow_remove. No save. Unverified.
    """
    return _ext("/smart-objects/definition", {"Operation": operation, "AssetPath": asset_path, "Index": slot_index,
        "FieldName": field, "TextValue": value_text, "Name": slot_name, "ExpectedSnapshot": expected_snapshot,
        "bAllow": allow_remove, "bConfirm": confirm, "bDryRun": dry_run})


# Tools listed to clients. Each picks one of the functions above with its variant argument.
environment_query_runtime = merged_tool("environment_query_runtime", {
    "run_environment_query": run_environment_query,
    "control_environment_query_request": control_environment_query_request,
})
ai_perception_runtime = merged_tool("ai_perception_runtime", {
    "control_ai_perception_runtime": control_ai_perception_runtime,
    "configure_ai_perception_runtime": configure_ai_perception_runtime,
})
