"""Procedural Content Generation graphs."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_pcg_graph(asset_path: str) -> str:
    """Inspect persistent native PCG graph nodes/settings/pins/edge endpoints.
    Pins include capacity/required/advanced/override flags and bounded native
    property exports, including authored type identifiers.
    <=256 internal nodes plus input/output, <=64 pins/direction, <=4096 pins total,
    <=64 edges/pin. Graph instances not supported. No generation or world mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def create_pcg_graph(asset_path: str, confirm: bool = False,
                     dry_run: bool = False, save: bool = False) -> str:
    """Create empty PCG graph with native editor factory and no template dialog.
    Confirmed /Game matching package/object names, stopped PIE, destination absent.
    Transaction/native identity readback/optional save; dry run creates no asset.
    Does not generate PCG output or modify the world.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pcg_graph(source_asset_path: str, asset_path: str,
                        confirm: bool = False, dry_run: bool = False,
                        save: bool = False) -> str:
    """Duplicate persistent PCG graph through native AssetTools.
    Confirmed /Game destination/stopped PIE, absent destination package, native
    identity readback/transaction/optional save. Owned objects follow native copy
    behavior; external assets stay shared. No generation or world mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/duplicate", json={
        "SourceAssetPath": source_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def discover_pcg_node_classes() -> str:
    """List <=256 loaded concrete native PCG settings classes; palette suitability unverified."""
    return httpx.post(f"{app.BASE_URL}/pcg/node-classes", json={}, timeout=180).text


@mcp.tool()
def add_pcg_node(asset_path: str, settings_class: str, x: int = 0, y: int = 0,
                 confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Create native settings-class PCG node/default pins at bounded editor position.
    Confirmed /Game/stopped PIE; <=256 internal nodes, position +/-1e6. Transaction,
    native ownership/settings/count/position readback and optional save. No generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/nodes", json={
        "AssetPath": asset_path, "SettingsClass": settings_class, "NodeX": x, "NodeY": y,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def edit_pcg_node_presentation(asset_path: str, node_index: int, node_path: str,
                               action: str, x: int = 0, y: int = 0, title: str = "",
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Move node or set authored title (action=move/title; empty title clears).
    Node indices: graph input=-2, graph output=-1, internal>=0.
    Uses current inspected node index/path, native title sanitizers, +/-1e6 positions,
    transaction/readback/no-op/dry-run/save. Confirmed /Game/stopped PIE required.
    Open editor synchronization unverified; no PCG generation requested.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/presentation", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "Action": action, "NodeX": x, "NodeY": y, "Title": title,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pcg_node(asset_path: str, node_index: int, node_path: str,
                       x: int = 0, y: int = 0, confirm: bool = False,
                       dry_run: bool = False, save: bool = False) -> str:
    """Copy owned node settings into new unlinked PCG node at requested position.
    Native AddNodeCopy plus editor comment/bubble metadata transfer; requested position
    overrides copied position. Title/color use native creation defaults; external assets shared.
    Current index/path, <=256 nodes/64 pins per direction, confirmed /Game/stopped
    PIE, transaction/identity/unlinked readback/dry-run/save. No generation requested.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/nodes/duplicate", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "NodeX": x, "NodeY": y, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pcg_node(asset_path: str, node_index: int, node_path: str,
                    confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Remove inspected internal PCG node with native link cleanup.
    Current index/path, <=256 internal nodes/4096 pins/64 pins per direction and
    edges per pin; ownership/membership/symmetry preflight. Transaction/native
    remaining order/link readback/dry-run/save. Confirmed /Game/stopped PIE required.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/nodes/remove", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_pcg_edge(asset_path: str, action: str,
                  from_node_index: int, from_node_path: str, from_pin: str,
                  to_node_index: int, to_node_path: str, to_pin: str,
                  confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Connect/disconnect native labeled PCG edge without displacing other links.
    Inspected index/path identities: graph input=-2/output=-1/internal>=0. Native
    pin compatibility/capacity/symmetric-link checks, transaction/readback/no-op/save.
    Confirmed /Game/stopped PIE; cycles/subgraph validity not evaluated.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/edges", json={
        "AssetPath": asset_path, "Action": action, "NodeIndex": from_node_index,
        "NodePath": from_node_path, "FromPin": from_pin, "TargetNodeIndex": to_node_index,
        "TargetNodePath": to_node_path, "ToPin": to_pin,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_node_settings(asset_path: str, node_index: int, node_path: str) -> str:
    """Inspect authored internal-node settings, identity and native-export fingerprint.
    <=256 fields through eight inline struct levels, enum choices, clamps/edit
    conditions/PCG override metadata. Arrays/objects opaque; export allocation
    uncapped. Current inspected node index/path required. No mutation/generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/nodes/settings/inspect", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path
    }, timeout=180).text


def set_pcg_node_settings_scalar(asset_path: str, node_index: int, node_path: str,
                                 settings_path: str, record_hash: str, field: str,
                                 value: float, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Set owned PCG settings bool/numeric leaf using inspected identities/fingerprint.
    <=8 writable inline struct segments; finite +/-1e9, bool0/1, integer width and
    native clamps. Confirmed /Game/stopped PIE, transaction/native notification/
    readback/no-op/save/current hash. Callbacks may rebuild pins; no generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/scalar", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_node_settings_enum(asset_path: str, node_index: int, node_path: str,
                               settings_path: str, record_hash: str, field: str,
                               value: str, confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Set declared visible nonsentinel native enum on owned PCG settings leaf.
    Current inspected node/settings identities and fingerprint, <=8 writable struct
    segments; graph node/pin/edge transaction coverage and native callback/readback.
    Confirmed /Game/stopped PIE, no-op/dry-run/save/current hash; no generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/enum", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "FieldName": field, "EnumValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_node_settings_text(asset_path: str, node_index: int, node_path: str,
                               settings_path: str, record_hash: str, field: str,
                               value: str, confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Set name/string/text settings leaf; names<=128, string/text<=4096.
    Empty name becomes None. FText replacement uses plain text, replacing localization
    identity. Current inspected settings identity/hash; writable inline structs,
    graph transaction coverage, native callback/readback/save. No generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/text", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "FieldName": field, "TextValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pcg_node_settings_compound(asset_path: str, node_index: int, node_path: str,
                                   settings_path: str, record_hash: str, field: str,
                                   kind: str, value: dict, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Set exact FVector/FLinearColor settings leaf (kind=vector/color).
    value: vector {X,Y,Z}, color {R,G,B,A}. Finite vector +/-1e9/color +/-1e6.
    Current identities/hash, writable inline structs, graph transaction coverage,
    native notification/typed readback/save. Confirmed /Game/stopped PIE required.
    """
    if kind not in ("vector", "color"):
        raise ValueError("kind must be vector/color")
    required = {"X", "Y", "Z"} if kind == "vector" else {"R", "G", "B", "A"}
    if set(value) != required:
        raise ValueError(f"value keys must be {sorted(required)}")
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/compound", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "FieldName": field, "ValueKind": kind,
        "VectorValue" if kind == "vector" else "ColorValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_pcg_node_settings_field(asset_path: str, node_index: int, node_path: str,
                                  settings_path: str, record_hash: str, field: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Reset scalar/enum/name/string/text/vector/color leaf to native class default.
    Uses class defaults, not per-node seeded construction defaults. Current settings
    identity/hash, writable inline structs, bounded graph transaction coverage,
    native callbacks/typed readback/no-op/save. Confirmed /Game/stopped PIE required.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/reset-field", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash, "FieldName": field,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pcg_node_settings_asset(asset_path: str, node_index: int, node_path: str,
                                settings_path: str, record_hash: str, field: str,
                                source_asset_path: str = "", confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Set compatible persistent hard/soft asset leaf, or clear with empty source.
    Non-instanced references only; PCG graph/settings references require dedicated
    adapters. Current inspected identities/hash, graph transaction coverage,
    native notification/readback/save. Confirmed /Game/stopped PIE; no generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/asset", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "FieldName": field, "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_node_settings_string_array(asset_path: str, node_index: int, node_path: str,
                                       settings_path: str, record_hash: str, field: str,
                                       values: list[str], confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Replace ordered name/string array leaf, <=256 items; empty clears.
    Names<=128/string<=4096, duplicates preserved. Current identities/hash,
    writable inline structs, graph transaction coverage/native ordered readback/
    save. Confirmed /Game/stopped PIE; native callbacks may rebuild pins.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/settings/string-array", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "FieldName": field, "StringValues": values,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def validate_pcg_graph(asset_path: str) -> str:
    """Report local PCG node/pin/edge ownership, duplicate labels, symmetry/direction,
    and cycle/dependent residuals. <=256 internal nodes/4096 pins/16384 incidences,
    <=64 pins per direction/edges per pin; <=256 issues with total/truncation.
    No settings-specific validation, subgraph recursion, compilation or generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/validate", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_pcg_subgraph(asset_path: str, node_index: int, node_path: str,
                     settings_path: str, record_hash: str, source_asset_path: str = "",
                     confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Bind/clear native subgraph node to registered graph or graph instance.
    Current settings identity/hash, owned subgraph instance without active override.
    Authored recursion guards <=128 interfaces/4096 nodes/depth32. Native SetSubgraph
    and structural callback may reset pins/parameter overrides. Transaction/readback/
    save; confirmed /Game/stopped PIE. Dynamic runtime references not proven.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/subgraph", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_pcg_graph_instance(asset_path: str, parent_asset_path: str,
                              confirm: bool = False, dry_run: bool = False,
                              save: bool = False) -> str:
    """Create native PCG graph instance with registered graph/interface parent.
    Parent chain must resolve to native graph without cycles, depth<=32.
    Confirmed /Game destination/stopped PIE, package collision checks, native
    factory/parent identity readback/transaction/dry-run/save. No generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graph-instances", json={
        "AssetPath": asset_path, "SourceAssetPath": parent_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_graph_interface(asset_path: str) -> str:
    """Inspect native PCG graph/instance parent chain and <=256 parameter entries.
    Parent depth<=32/cycle guards. Returns resolved graph, parameter GUID/type/value,
    instance override/default flags and <=128 visible enum choices with setter support.
    Text<=4096; serialization work uncapped.
    No mutation, generation or world changes.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graph-interfaces/inspect", json={"AssetPath": asset_path}, timeout=180).text


def set_pcg_graph_parameter_scalar(asset_path: str, parameter_name: str,
                                   parameter_id: str, value: float,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Set existing exact bool/int32/float/double graph/interface parameter.
    Inspected name/GUID, <=256 parameters, parent-chain cycle/depth guards,
    confirmed /Game/stopped PIE. Native typed setters/notifications/readback/save.
    Same value does not force override; dependent-instance undo propagation unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/scalar", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_pcg_graph_parameter_override(asset_path: str, parameter_name: str,
                                      parameter_id: str, action: str,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Control instance parameter: enable_override/disable_override/reset_value.
    Disable restores parent and clears flag; reset restores parent retaining flag.
    Current name/GUID, bounded parent chain, native controls/readback/transaction/
    dry-run/save. Confirmed /Game/stopped PIE; dependent undo propagation unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-instances/parameters/override", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "Action": action,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_parameter_text(asset_path: str, parameter_name: str,
                                 parameter_id: str, value: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Set exact name/string/text graph parameter via native setters.
    Names<=128, string/text<=4096; changed FText replaces localization identity.
    Inspected name/GUID, parent-chain guards, confirmed /Game/stopped PIE,
    transaction/typed readback/no-op/save. Same value does not force override.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/text", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "TextValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_parameter_vector(asset_path: str, parameter_name: str,
                                   parameter_id: str, x: float, y: float, z: float,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Set exact FVector graph/instance parameter with finite components +/-1e9.
    Current name/GUID, <=256 parameters, parent-chain guards; native typed setter/
    pointer-getter copy readback/transaction/save. Same value does not force override.
    Confirmed /Game/stopped PIE; no generation requested.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/vector", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "VectorValue": {"X": x, "Y": y, "Z": z},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_parameter_enum(asset_path: str, parameter_name: str,
                                 parameter_id: str, value: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Set declared visible nonsentinel byte enum graph/interface parameter.
    Current parameter name/GUID, <=256 parameters, parent-chain guards; native
    enum-aware getter/setter/notification/readback/transaction/save. Same value
    does not force override. Confirmed /Game/stopped PIE; no generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/enum", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "EnumValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_pcg_graph_parameter(asset_path: str, parameter_name: str,
                                parameter_id: str, new_name: str,
                                confirm: bool = False, dry_run: bool = False,
                                save: bool = False) -> str:
    """Rename base graph parameter using native API, preserving GUID/value.
    Current name/GUID, unique non-None identifier<=128; instances rejected.
    Confirmed /Game/stopped PIE, transaction/native readback/dry-run/save.
    External dynamic name references are not explicitly migrated.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/parameters/name", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "TextValue": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def add_pcg_graph_parameter(asset_path: str, parameter_name: str, kind: str,
                             confirm: bool = False, dry_run: bool = False,
                             save: bool = False) -> str:
    """Add base graph parameter with native default and new GUID, <=256 entries.
    kind=bool/int/int64/float/double/name/string/text/vector/rotator/transform/name_array/string_array. Unique identifier<=128.
    Confirmed /Game/stopped PIE, transaction/native identity/type/count readback/save.
    Dry-run GUID provisional; assign values through typed parameter tools afterward.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name, "ValueKind": kind,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pcg_graph_parameter(asset_path: str, parameter_name: str,
                                parameter_id: str, confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Remove base graph parameter after native removal-policy check.
    Current name/GUID, <=256 parameters, native bag update/refresh, transaction,
    remaining GUID/name order readback/dry-run/save. External readers may need repair;
    dependent undo propagation unverified. Confirmed /Game/stopped PIE required.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/parameters/remove", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_world_components() -> str:
    """List <=256 loaded PCG components in current stopped editor world.
    Actor/component identities, registered/activated/seed/generation trigger,
    generation/cleanup/generated status and graph-instance identity. Excludes
    unloaded partition actors; global object iteration uncapped. No mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/inspect", json={}, timeout=180).text


def set_pcg_component_settings(component_path: str, actor_path: str, action: str,
                               seed: int = 42, enabled: bool = True,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Edit idle current-world PCG component seed or activation (action=seed/activated).
    Inspected component/actor identities, stopped PIE/confirmation, transaction and
    post-reconstruction readback. Native callbacks may regenerate/clean up world
    resources. No map save; generated-resource undo unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/components/settings", json={
        "ComponentPath": component_path, "ActorPath": actor_path, "Action": action,
        "Seed": seed, "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def request_pcg_component_operation(component_path: str, actor_path: str, action: str,
                                     force: bool = False, confirm: bool = False,
                                     dry_run: bool = False) -> str:
    """Request native local generate/cleanup/cancel; returns task ID/status, no wait.
    Confirmed stopped editor world/current identities. Generate requires activated
    non-runtime-scheduled idle component and bounded parent chain/base graph.
    Cleanup removes generated components. Execution can change world resources and
    run unbounded custom graph code; no completion/undo/save guarantee.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/operation", json={
        "ComponentPath": component_path, "ActorPath": actor_path, "Action": action,
        "bForce": force, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_component_status(component_path: str, actor_path: str) -> str:
    """Poll one current-world PCG component by inspected component/actor identity.
    Returns native generation task ID, generating/cleanup/idle/generated flags,
    registration/activation/seed/trigger and graph instance. Stopped PIE required.
    Idle is not success proof; generated flag is not output validation. No task wait.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/status", json={
        "ComponentPath": component_path, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_component_output(component_path: str, actor_path: str) -> str:
    """Inspect idle current-world component cached graph output, <=256 entries.
    Pin/data identities/classes, native point-data counts and <=64 tags per entry
    (1024 chars each).
    Cached output may be stale/empty and omit managed resources. No point conversion,
    spatial sampling, generation, mutation or output-correctness guarantee.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/output", json={
        "ComponentPath": component_path, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_component_resources(component_path: str, actor_path: str) -> str:
    """Inspect <=256 managed resources on idle current-world PCG component.
    Identity/class/unused/preview/transient flags, <=128 soft actor or component
    paths per native resource. References not loaded. Resource-array copy uncapped;
    custom resources identity/state only. No release, cleanup or generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/resources", json={
        "ComponentPath": component_path, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_output_points(component_path: str, actor_path: str, output_index: int,
                               data_path: str, start: int = 0, count: int = 64) -> str:
    """Read <=256 cached native points: transform, density, seed, bounds, color,
    steepness and metadata-entry identity (string, preserves int64 precision).
    Idle current-world component and inspected output index/data identity required.
    No spatial conversion/full point copy; virtual getter work not strictly bounded.
    Identity does not guarantee unchanged content across requests. No generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/output/points", json={
        "ComponentPath": component_path, "ActorPath": actor_path,
        "OutputIndex": output_index, "DataPath": data_path,
        "PointStart": start, "PointCount": count
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_output_metadata(component_path: str, actor_path: str,
                                  output_index: int, data_path: str) -> str:
    """Inspect cached output metadata names/type IDs: default and <=16 supported
    domains, <=256 attributes each, domain flags/custom IDs/default identity.
    Idle current-world component/owner and inspected output/data identity required.
    Native schema collection allocation uncapped; attribute values excluded.
    No point conversion, generation or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/output/metadata", json={
        "ComponentPath": component_path, "ActorPath": actor_path,
        "OutputIndex": output_index, "DataPath": data_path
    }, timeout=180).text


@mcp.tool()
def set_pcg_component_graph(component_path: str, actor_path: str,
                            source_asset_path: str = "", confirm: bool = False,
                            dry_run: bool = False) -> str:
    """Bind/clear idle current-world component graph using native local setter.
    Registered graph/interface source, parent cycle/depth guards, current actor/
    component identity, confirmed stopped PIE, transaction/native readback.
    Native refresh may reset overrides/regenerate resources; no map save or undo
    guarantee for generated resources. Subgraph recursion not evaluated here.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/components/graph", json={
        "ComponentPath": component_path, "ActorPath": actor_path,
        "SourceAssetPath": source_asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_pcg_component_generation_trigger(component_path: str, actor_path: str,
                                         trigger: str, confirm: bool = False,
                                         dry_run: bool = False) -> str:
    """Set native GenerateOnLoad/GenerateOnDemand/GenerateAtRuntime trigger.
    Idle persistent current-world component/actor identity, confirmed stopped PIE,
    transaction/native callback/reconstruction readback. Native scheduling may change
    generated world resources; no map save or generated-resource undo guarantee.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/components/settings", json={
        "ComponentPath": component_path, "ActorPath": actor_path,
        "Action": "generation_trigger", "EnumValue": trigger,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_pcg_component_partitioned(component_path: str, actor_path: str,
                                   enabled: bool, confirm: bool = False,
                                   dry_run: bool = False) -> str:
    """Set native PCG partition mode on idle registered current-world component.
    Confirmed stopped PIE/current owner identity/native CanPartition guard.
    Setter may immediately clean generated resources/change partition mappings.
    Actor/component transaction/readback; mapping/resource undo unverified, no save.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/components/partitioned", json={
        "ComponentPath": component_path, "ActorPath": actor_path,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_pcg_graph_parameter_int64(asset_path: str, parameter_name: str,
                                  parameter_id: str, value: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Set exact signed int64 parameter using lossless canonical decimal string.
    No leading plus/zeros/whitespace. Current name/GUID, parent-chain guards,
    native int64 setter/getter/readback/transaction/save. Response values strings.
    Confirmed /Game/stopped PIE; same value does not force override.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/int64", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "TextValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pcg_graph_parameter_rotator(asset_path: str, parameter_name: str,
                                    parameter_id: str, pitch: float, yaw: float, roll: float,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Set exact FRotator graph parameter; finite angles +/-1e6 degrees.
    Current name/GUID, bounded parent chain; native typed setter/getter readback,
    transaction/no-op/dry-run/save. Confirmed /Game/stopped PIE; no generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/rotator", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id,
        "RotatorValue": {"Pitch": pitch, "Yaw": yaw, "Roll": roll},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pcg_graph_parameter_transform(asset_path: str, parameter_name: str,
                                      parameter_id: str, transform: dict,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Set exact FTransform parameter: Translation XYZ, Rotation XYZW, Scale3D XYZ.
    Requires finite translation +/-1e9/scale +/-1e6 and normalized quaternion.
    Current name/GUID, parent-chain guards, native setter/readback/transaction/save.
    Confirmed /Game/stopped PIE; no generation requested.
    """
    if set(transform) != {"Translation", "Rotation", "Scale3D"}:
        raise ValueError("transform requires Translation, Rotation, Scale3D")
    for key, required in (("Translation", {"X", "Y", "Z"}),
                          ("Rotation", {"X", "Y", "Z", "W"}),
                          ("Scale3D", {"X", "Y", "Z"})):
        if set(transform[key]) != required:
            raise ValueError(f"{key} requires {sorted(required)}")
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/transform", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "TransformValue": transform,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def add_pcg_graph_enum_parameter(asset_path: str, parameter_name: str,
                                  enum_path: str, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Add enum graph parameter using loaded native /Script/ enum definition.
    Requires <=256 enum entries, visible zero default, visible values in byte range.
    Unique bounded name, <=256 parameters, confirmed /Game/stopped PIE,
    transaction/native GUID/type definition readback/dry-run/save. No generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name, "ValueKind": "enum",
        "SourceAssetPath": enum_path, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pcg_graph_instance(source_asset_path: str, asset_path: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Duplicate persistent PCG graph instance through native AssetTools.
    Parent-chain cycle/depth32 guards, <=256 parameters, destination collision checks.
    Native parent/parameter GUID/type/value/override readback, transaction/save.
    Parent and external assets shared. Confirmed /Game/stopped PIE; no generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graph-instances/duplicate", json={
        "SourceAssetPath": source_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pcg_graph_instance_parent(asset_path: str, source_asset_path: str,
                                   parent_hash: str, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Replace persistent graph-instance parent using inspected parent_hash.
    Registered parent, cycle/depth32 guards, confirmed /Game/stopped PIE,
    transaction/native parent readback/save. Native parameter override migration
    may discard old values; dependent undo propagation/subgraph recursion unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-instances/parent", json={
        "AssetPath": asset_path, "SourceAssetPath": source_asset_path,
        "RecordHash": parent_hash, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pcg_graph_pin(asset_path: str, node_index: int, node_path: str,
                       settings_path: str, record_hash: str, label: str,
                       confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Add native graph IO custom pin: input node=-2/output=-1, <=64 authored pins.
    Current node/settings identity/hash, native Any/multiple defaults/collision label
    fixup, graph transaction/notification/readback/save. Returns actual label;
    dry run does not predict label. Consumers may rebuild; no explicit generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/pins", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash, "FromPin": label,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_graph_pins(asset_path: str, node_index: int, node_path: str,
                            settings_path: str) -> str:
    """Inspect <=64 authored graph IO pins (input node=-2/output=-1).
    Returns array indices/labels/native properties and settings fingerprint.
    Authored indices differ from derived runtime pin arrays. No mutation/generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/pins/inspect", json={
        "AssetPath": asset_path, "NodeIndex": node_index,
        "NodePath": node_path, "SettingsPath": settings_path
    }, timeout=180).text


def edit_pcg_graph_pins(asset_path: str, node_index: int, node_path: str,
                         settings_path: str, record_hash: str, pin_index: int,
                         pin_label: str, action: str, target_index: int = -1,
                         confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Remove/move authored graph IO pin; target index is final array index.
    Current inspected node/settings hash and authored pin index/label, <=64 pins,
    graph transaction/native notification/ordered content readback/save. Removed
    links/consumer pins may change; consumer undo propagation unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/pins", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "PinIndex": pin_index, "FromPin": pin_label, "Action": action,
        "TargetPinIndex": target_index, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def rename_pcg_graph_pin(asset_path: str, node_index: int, node_path: str,
                          settings_path: str, record_hash: str, pin_index: int,
                          pin_label: str, new_label: str, confirm: bool = False,
                          dry_run: bool = False, save: bool = False) -> str:
    """Rename authored graph IO pin using current array index/label/settings hash.
    Unique non-None new label<=128, graph transaction/native fixup/ordered content
    readback/save. Native derived pins/consumer links may rebuild or be dropped;
    external label strings not migrated explicitly. Confirmed /Game/stopped PIE.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/pins", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "PinIndex": pin_index, "FromPin": pin_label,
        "Action": "rename", "TextValue": new_label,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def configure_pcg_graph_pin(asset_path: str, node_index: int, node_path: str,
                             settings_path: str, record_hash: str, pin_index: int,
                             pin_label: str, allow_multiple_connections: bool = True,
                             allow_multiple_data: bool = True, status: str = "Normal",
                             tooltip: str = "", confirm: bool = False,
                             dry_run: bool = False, save: bool = False) -> str:
    """Replace authored IO pin capacity/status/tooltip, preserving label/type/usage.
    Status Normal/Required/Advanced; multi-connections requires multi-data.
    Tooltip<=4096 uses plain FText. Current index/label/settings hash, graph
    transaction/native notification/ordered readback/save. Links/consumers may rebuild.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/pins", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "PinIndex": pin_index, "FromPin": pin_label, "Action": "configure",
        "bAllowMultipleConnections": allow_multiple_connections,
        "bAllowMultipleData": allow_multiple_data, "PinStatus": status,
        "TextValue": tooltip, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_pin_data_types(asset_path: str, node_index: int, node_path: str,
                                  settings_path: str, record_hash: str, pin_index: int,
                                  pin_label: str, data_classes: list[str],
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Set IO pin type composition from <=32 unique concrete loaded native PCG data classes.
    Empty list restores Any. Uses native UE5.7 FPCGDataTypeIdentifier composition,
    current index/label/settings hash, graph transaction/notification/readback/save.
    Type changes may drop links/rebuild consumers; no explicit generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/pins", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "SettingsPath": settings_path, "RecordHash": record_hash,
        "PinIndex": pin_index, "FromPin": pin_label, "Action": "data_types",
        "StringValues": data_classes, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def discover_pcg_data_classes() -> str:
    """List <=256 loaded concrete native PCG data classes/type identifiers.
    Exposes class paths and native type validity for IO pin composition. May construct
    class defaults; native/export work uncapped. No generation or world mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/data-classes", json={}, timeout=180).text


@mcp.tool()
def add_pcg_actor_component(actor_path: str, component_name: str,
                             confirm: bool = False, dry_run: bool = False) -> str:
    """Create/register native instance PCG component on existing editor-world actor.
    Persistent actor/current world, unique bounded name, <=64 PCG components,
    confirmed stopped PIE, transaction/registration readback/dry-run. Default settings,
    no graph assignment/map save/explicit generation; callback/undo lifecycle unverified.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components", json={
        "ActorPath": actor_path, "Title": component_name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_pcg_actor_component(component_path: str, actor_path: str,
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Remove clean nonpartitioned actor-instance PCG component, not native/BP defaults.
    Current identities, confirmed stopped editor world, idle/not-generated/no managed
    resources. Run cleanup and disable partitioning first. Actor/component transaction,
    native destroy/unregister readback; no map save, undo/reconstruction unverified.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/components/remove", json={
        "ComponentPath": component_path, "ActorPath": actor_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_pcg_graph_settings_scalar(asset_path: str, record_hash: str, field: str,
                                   value: float, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Set direct editable graph bool/numeric setting with current graph fingerprint.
    Native clamps/integer width/bool0/1/finite +/-1e9, graph transaction coverage,
    native property notification/typed readback/save. Confirmed /Game/stopped PIE.
    Edit conditions/callback scheduling/dependent undo unverified; no explicit generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/settings/scalar", json={
        "AssetPath": asset_path, "RecordHash": record_hash, "FieldName": field,
        "ScalarValue": value, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_settings_enum(asset_path: str, record_hash: str, field: str,
                                 value: str, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Set direct declared visible native graph enum using inspected graph hash.
    Native enum/byte checks, graph transaction coverage/root-member property event,
    typed readback/no-op/dry-run/save. Confirmed /Game/stopped PIE; no explicit generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/settings/enum", json={
        "AssetPath": asset_path, "RecordHash": record_hash, "FieldName": field,
        "EnumValue": value, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_settings_text(asset_path: str, record_hash: str, field: str,
                                 value: str, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Set direct editable graph name/string/text field with current graph hash.
    Name<=128/string-text<=4096; changed FText replaces localization identity.
    Confirmed /Game/stopped PIE, graph transaction/native notification/readback/save.
    Edit conditions/dependent callbacks unverified; no explicit generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/settings/text", json={
        "AssetPath": asset_path, "RecordHash": record_hash, "FieldName": field,
        "TextValue": value, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_pcg_graph_settings_field(asset_path: str, record_hash: str, field: str,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Reset direct scalar/enum/name/string/text/vector/color graph setting to native CDO.
    Current graph fingerprint, editable field checks, graph transaction coverage,
    root-member native notification/typed readback/no-op/save. Confirmed /Game/stopped
    PIE; native callbacks may rebuild dependent objects, no explicit generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/settings/reset-field", json={
        "AssetPath": asset_path, "RecordHash": record_hash, "FieldName": field,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_parameter_string_array(asset_path: str, parameter_name: str,
                                          parameter_id: str, values: list[str],
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Replace existing name/string array parameter, <=256 values; empty clears.
    Names<=128/strings<=4096, order/duplicates preserved. Inspected name/GUID,
    bounded parent chain, native UpdateArrayGraphParameter/typed readback/transaction/
    save. Confirmed /Game/stopped PIE. Creation kinds: name_array/string_array.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/string-array", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "StringValues": values,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_graph_parameter_scalar_array(asset_path: str, parameter_name: str,
                                          parameter_id: str, values: list[float],
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Replace exact bool/int32/float/double array parameter, <=256 values; empty clears.
    Bool0/1, int32 integral, float/double finite +/-1e9; ordered typed readback.
    Current name/GUID/parent-chain guards, native array update/transaction/save.
    Creation kinds: bool_array/int_array/float_array/double_array. No generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/scalar-array", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "ScalarValues": values,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_graph_parameter_array(asset_path: str, parameter_name: str,
                                       parameter_id: str, start: int = 0,
                                       count: int = 64) -> str:
    """Inspect <=256 array parameter elements as bounded native-export records.
    Current parameter name/GUID and parent-chain guards; returns element count/type/
    indices/text<=4096. Native export intermediate work uncapped; GUID does not
    guarantee stable values between requests. No mutation or generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/array/inspect", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "ElementStart": start, "ElementCount": count
    }, timeout=180).text


def set_pcg_graph_parameter_vector_array(asset_path: str, parameter_name: str,
                                          parameter_id: str, values: list[dict],
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Replace exact FVector array parameter, <=256 XYZ vectors; empty clears.
    Finite components +/-1e9, inspected name/GUID, bounded parent chain, native
    array-update callback/typed copy/ordered readback/transaction/save.
    Creation kind=vector_array. Confirmed /Game/stopped PIE; no generation.
    """
    if any(set(value) != {"X", "Y", "Z"} for value in values):
        raise ValueError("every vector requires X,Y,Z")
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/vector-array", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "VectorValues": values,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pcg_graph_dependencies(asset_path: str) -> str:
    """Inspect authored subgraph/instance-parent dependencies and cycle/missing diagnostics.
    <=128 interfaces/4096 nodes/depth32/512 reference records; truncated flag.
    Native virtual getter work uncapped; dynamic runtime references not proven.
    No compile, generation or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graph-interfaces/dependencies", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_pcg_graph_parameter_asset(asset_path: str, parameter_name: str,
                                   parameter_id: str, source_asset_path: str = "",
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Set compatible persistent hard/soft asset graph parameter, empty clears.
    Current name/GUID, registered class-compatible source, bounded parent chain,
    native typed setter/readback/transaction/save. Referenced asset unchanged;
    confirmed /Game/stopped PIE, no explicit generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/asset", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def add_pcg_graph_asset_parameter(asset_path: str, parameter_name: str,
                                   class_path: str, soft: bool = False,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Add class-constrained native hard/soft object graph parameter, default null.
    Loaded native /Script/ class, unique bounded name/<=256 parameters,
    confirmed /Game/stopped PIE, native GUID/type-class/count readback/transaction/save.
    Assign value with asset-parameter editor afterward. No generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ValueKind": "soft_object" if soft else "object", "SettingsClass": class_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def add_pcg_graph_class_parameter(asset_path: str, parameter_name: str,
                                   base_class_path: str, soft: bool = False,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Create constrained native hard/soft class parameter, default null.
    Loaded native base class, unique name, confirmed /Game/stopped PIE;
    native definition/GUID readback/transaction/save. No generation.
    """
    return httpx.post(f"{app.BASE_URL}/pcg/graphs/parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ValueKind": "soft_class" if soft else "class", "SettingsClass": base_class_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pcg_graph_parameter_class(asset_path: str, parameter_name: str,
                                   parameter_id: str, class_path: str = "",
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Set/clear compatible loaded native class graph parameter; abstract classes allowed.
    Current name/GUID, native metaclass constraint, bounded parent chain,
    confirmed /Game/stopped PIE; native hard/soft setter/readback/transaction/save.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graph-interfaces/parameters/class", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterId": parameter_id, "SourceAssetPath": class_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_node_comment(asset_path: str, node_index: int, node_path: str,
                          comment: str, confirm: bool = False,
                          dry_run: bool = False, save: bool = False) -> str:
    """Set editor-only PCG node comment<=4096, empty clears.
    Current node index/path (input=-2/output=-1/internal>=0), confirmation/stopped
    PIE, transaction/native field readback/no-op/save. Open editor sync unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/presentation", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "Action": "comment", "TextValue": comment,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pcg_node_comment_display(asset_path: str, node_index: int, node_path: str,
                                  visible: bool, pinned: bool,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Set PCG node editor comment-bubble visibility/pinning, preserving comment text.
    Current inspected index/path, confirmed /Game/stopped PIE, transaction/readback/
    no-op/save. Open graph editor synchronization unverified; no generation.
    """
    return httpx.patch(f"{app.BASE_URL}/pcg/graphs/nodes/presentation", json={
        "AssetPath": asset_path, "NodeIndex": node_index, "NodePath": node_path,
        "Action": "comment_display", "bCommentVisible": visible, "bCommentPinned": pinned,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
edit_pcg_node_display = merged_tool("edit_pcg_node_display", {
    "edit_pcg_node_presentation": edit_pcg_node_presentation,
    "set_pcg_node_comment": set_pcg_node_comment,
    "set_pcg_node_comment_display": set_pcg_node_comment_display,
})
add_pcg_graph_typed_parameter = merged_tool("add_pcg_graph_typed_parameter", {
    "add_pcg_graph_parameter": add_pcg_graph_parameter,
    "add_pcg_graph_enum_parameter": add_pcg_graph_enum_parameter,
    "add_pcg_graph_asset_parameter": add_pcg_graph_asset_parameter,
    "add_pcg_graph_class_parameter": add_pcg_graph_class_parameter,
})
edit_pcg_component_settings = merged_tool("edit_pcg_component_settings", {
    "set_pcg_component_settings": set_pcg_component_settings,
    "set_pcg_component_generation_trigger": set_pcg_component_generation_trigger,
})
edit_pcg_graph_pin = merged_tool("edit_pcg_graph_pin", {
    "edit_pcg_graph_pins": edit_pcg_graph_pins,
    "rename_pcg_graph_pin": rename_pcg_graph_pin,
    "configure_pcg_graph_pin": configure_pcg_graph_pin,
    "set_pcg_graph_pin_data_types": set_pcg_graph_pin_data_types,
})
set_pcg_node_settings = merged_tool("set_pcg_node_settings", {
    "scalar": set_pcg_node_settings_scalar,
    "enum": set_pcg_node_settings_enum,
    "text": set_pcg_node_settings_text,
    "string_array": set_pcg_node_settings_string_array,
})
set_pcg_graph_parameter = merged_tool("set_pcg_graph_parameter", {
    "scalar": set_pcg_graph_parameter_scalar,
    "text": set_pcg_graph_parameter_text,
    "vector": set_pcg_graph_parameter_vector,
    "enum": set_pcg_graph_parameter_enum,
    "int64": set_pcg_graph_parameter_int64,
    "string_array": set_pcg_graph_parameter_string_array,
    "scalar_array": set_pcg_graph_parameter_scalar_array,
    "vector_array": set_pcg_graph_parameter_vector_array,
})
set_pcg_graph_settings = merged_tool("set_pcg_graph_settings", {
    "scalar": set_pcg_graph_settings_scalar,
    "enum": set_pcg_graph_settings_enum,
    "text": set_pcg_graph_settings_text,
})
