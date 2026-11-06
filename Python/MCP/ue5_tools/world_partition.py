"""World Partition, HLOD and Data Layers."""
from typing import Literal
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_world_partition() -> str:
    """Inspect World Partition, external actors, streaming, and Data Layer counts."""
    return httpx.get(f"{app.BASE_URL}/worlds/partition").text


@mcp.tool()
def list_world_data_layers() -> str:
    """List current-world Data Layers and their effective editor states."""
    return httpx.get(f"{app.BASE_URL}/worlds/data-layers").text


@mcp.tool()
def set_world_data_layer_state(
        data_layer_name: str,
        operation: Literal["load", "unload", "show", "hide", "activate", "deactivate"]) -> str:
    """Change a named Data Layer's explicit editor loading or visibility state."""
    return httpx.post(f"{app.BASE_URL}/worlds/data-layers", json={
        "DataLayerName": data_layer_name, "Operation": operation
    }).text


@mcp.tool()
def inspect_world_partition_actor_descriptors(start: int = 0, count: int = 64) -> str:
    """Page registered WorldPartition actor descriptors without loading actors, offset0..1e6/count1..128.
    Metadata/loaded weak lookup/bounds/up to64 data layers and references per descriptor.
    Flat registered collection/order unstable/index not identity; descriptors may lag unsaved actor edits.
    No package/region load/cell generation/streaming activation/edit/build/save; loaded not visible proof.
    Native iterator/linkage/metadata behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actors/inspect", json={
        "Start": start, "Count": count
    }, timeout=120).text


@mcp.tool()
def inspect_world_partition_runtime_cells(start: int = 0, count: int = 64) -> str:
    """Page existing runtime-hash streaming cells0..1e6/count1..128 in stopped editor partition.
    Identity/GUID/package/state ordinal/always-loaded/data layers/native bounds, no cell generation/load.
    Editor hash can be empty before generation; order unstable/index not identity.
    No PIE/cook/streaming activation/edit/build/save, state not renderer/collision readiness proof.
    Native hash enumeration/getters/linkage unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/cells/inspect", json={
        "Start": start, "Count": count
    }, timeout=120).text


@mcp.tool()
def inspect_world_partition_editor_regions(start: int = 0, count: int = 64) -> str:
    """Page partition-owned editor loader adapters/path/world/loaded/user-created/label/bounds1..128.
    Registry order unstable; excludes actor-owned interfaces/runtime cells, loaded not exclusive residency proof.
    Native virtual getters unbounded; no creation/load/unload/release/streaming mutation/build/save.
    Native registry/getters/dirty neutrality unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/inspect", json={
        "Start": start, "Count": count
    }, timeout=120).text


@mcp.tool()
def create_world_partition_editor_region(partition_path: str, expected_registry_count: int,
                                          label: str, center: list[float], extent: list[float],
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Create unloaded native partition-owned box loader, inspected partition/registry count<1024.
    Center+/-1e9/half extents1..1e6/label1..128; user-created transient editor session state.
    No actor reference acquisition/load/streaming activation/undo transaction/build/save.
    Native partition owns lifetime; failure may leave registry entry, inspect adapters; lifecycle/UI unverified.
    """
    if len(center) != 3 or len(extent) != 3:
        raise ValueError("Center/half extents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/create", json={
        "PartitionPath": partition_path, "ExpectedRegistryCount": expected_registry_count, "Label": label,
        "Center": dict(zip(("X", "Y", "Z"), center)), "Extent": dict(zip(("X", "Y", "Z"), extent)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=120).text


@mcp.tool()
def release_unloaded_world_partition_editor_region(partition_path: str, adapter_path: str,
                                                    expected_registry_count: int, label: str,
                                                    center: list[float], extent: list[float],
                                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Release unloaded user-created native partition-owned editor region with inspected identity/count/shape guard.
    Must match label/center/half extents and current partition; loaded adapters rejected.
    Native release/delegate cleanup/readback/dry-run, no Load/Unload/undo transaction/build/save.
    Transient wrapper later GC, native lifecycle/custom callbacks unverified.
    """
    if len(center) != 3 or len(extent) != 3:
        raise ValueError("Inspected center/half extents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/release-unloaded", json={
        "PartitionPath": partition_path, "AdapterPath": adapter_path,
        "ExpectedRegistryCount": expected_registry_count, "Label": label,
        "Center": dict(zip(("X", "Y", "Z"), center)), "Extent": dict(zip(("X", "Y", "Z"), extent)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=120).text


@mcp.tool()
def load_world_partition_editor_region(partition_path: str, adapter_path: str,
                                       expected_registry_count: int, expected_loaded: bool,
                                       label: str, center: list[float], extent: list[float],
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Load user-created native region with inspected partition/adapter/count/state/label/bounds guards.
    Native dependency loads beyond box/actor construction/resource work unbounded, transient hold not undoable.
    Reports observed actor-path delta and dirty-package snapshots<=128, not complete dependency attribution.
    Native unload side effects can reset undo history/GC; no generation/runtime activation/build/save.
    Loaded hold not rendering/collision completion proof; native callbacks/lifecycle unverified.
    """
    if len(center) != 3 or len(extent) != 3:
        raise ValueError("Inspected center/half extents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/load", json={
        "PartitionPath": partition_path, "AdapterPath": adapter_path,
        "ExpectedRegistryCount": expected_registry_count, "bExpectedLoaded": expected_loaded, "Label": label,
        "Center": dict(zip(("X", "Y", "Z"), center)), "Extent": dict(zip(("X", "Y", "Z"), extent)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=300).text


@mcp.tool()
def unload_world_partition_editor_region(partition_path: str, adapter_path: str,
                                       expected_registry_count: int, expected_loaded: bool,
                                       label: str, center: list[float], extent: list[float],
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Unload user-created region with inspected partition/adapter/count/state/label/bounds guards.
    Changed-state execution requires no loaded dirty nontransient packages globally; dry-run reports blockers.
    No implicit save/discard; native unload may reset undo history/GC, transient and not undoable.
    Other loaders/pins can retain actors; reports observed actor-path delta/dirty snapshots<=128.
    No adapter release/generation/runtime activation/build/save; native callbacks/lifecycle unverified.
    """
    if len(center) != 3 or len(extent) != 3:
        raise ValueError("Inspected center/half extents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/unload", json={
        "PartitionPath": partition_path, "AdapterPath": adapter_path,
        "ExpectedRegistryCount": expected_registry_count, "bExpectedLoaded": expected_loaded, "Label": label,
        "Center": dict(zip(("X", "Y", "Z"), center)), "Extent": dict(zip(("X", "Y", "Z"), extent)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=300).text


@mcp.tool()
def inspect_world_partition_box_actors(partition_path: str, center: list[float], extent: list[float],
                                       start: int = 0, count: int = 64) -> str:
    """Query registered descriptor editor bounds intersecting box without loading actors.
    Inspected partition/center+/-1e9/half extents1..1e6; <=128 emitted matches.
    Start/next_start are raw descriptor offsets, not match indices; entire remaining registry may scan.
    Flat collection/no child recursion/dependency expansion/native loader filtering; invalid bounds omitted.
    Matches not exact load/unload set or residency proof; no loader/load/activation/build/save.
    """
    if len(center) != 3 or len(extent) != 3:
        raise ValueError("Center/half extents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/actors/inspect", json={
        "PartitionPath": partition_path, "Center": dict(zip(("X", "Y", "Z"), center)),
        "Extent": dict(zip(("X", "Y", "Z"), extent)), "Start": start, "Count": count
    }, timeout=120).text


@mcp.tool()
def inspect_world_partition_containers(start: int = 0, count: int = 64, recursive: bool = False) -> str:
    """Page native registered descriptor-container paths/IDs/packages/transform/child count/partition metadata.
    Optional recursion over already-cached child containers, <=128 emitted/offset<=1e6/order unstable.
    Container ID/path scopes actor GUIDs; cached inventory not all unloaded nested content proof.
    No initialization/registration/actor or package load/region load/generation/build/save.
    Native traversal depth/custom getters/dirty neutrality unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/containers/inspect", json={
        "Start": start, "Count": count, "bRecursive": recursive
    }, timeout=120).text


@mcp.tool()
def inspect_world_partition_actor_descriptor(partition_path: str, container_path: str, actor_guid: str) -> str:
    """Inspect single native descriptor by partition/container path/GUID without loading actor.
    Avoids inventory index ambiguity; metadata/weak loaded lookup/bounds/up to64 references/data layers.
    No refresh/reference acquisition/region load/edit/build/save; descriptor freshness/readiness unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/inspect", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid
    }, timeout=120).text


@mcp.tool()
def inspect_world_partition_actor_references(partition_path: str, container_path: str, actor_guid: str,
                                             start: int = 0, count: int = 64, editor_only: bool = False) -> str:
    """Page native direct actor references1..128, optional editor-only array, same-container metadata lookup.
    Partition/container/GUID addressing; no actor references/load/transitive traversal/cycle validation.
    Missing descriptor not proof of broken reference; metadata may change/lag unsaved edits.
    No refresh/region load/edit/build/save; native reference semantics unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/references/inspect", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "Start": start, "Count": count, "bEditorOnlyReferences": editor_only
    }, timeout=120).text


@mcp.tool()
def set_loaded_partition_actor_spatial(partition_path: str, container_path: str, actor_guid: str,
                                       actor_path: str, expected_value: bool, value: bool,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set already-loaded partition actor authored spatial-loading flag with full identity/current raw flag guard.
    Native component CanChange check, actor transaction/setter/notification/readback/no-op/dry-run.
    Reports dirty actor package, no load/generation/build/save; descriptor may lag/refresh through callbacks.
    Effective spatial state can be component-forced; native loader effects/external persistence/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/spatial", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "bExpectedValue": expected_value, "bValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_loaded_partition_actor_runtime_grid(partition_path: str, container_path: str, actor_guid: str,
                                            actor_path: str, expected_grid: str, grid: str,
                                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set loaded partition actor runtime grid, native CanEditChange/IsValidGrid for actor class.
    Inspected partition/container/GUID/actor/current FName guards, <=128 chars/empty or None default.
    Actor transaction/setter/notification/readback/no-op/dry-run/dirty actor package reporting/no save.
    Grid eligibility not cross-actor/data-layer/HLOD layout validation; no load/generation/build.
    Native callbacks/descriptor refresh/external persistence/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/runtime-grid", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "ExpectedName": expected_grid, "Name": grid,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_loaded_partition_actor_hlod_layer(partition_path: str, container_path: str, actor_guid: str,
                                          actor_path: str, expected_layer_path: str, expected_grid: str,
                                          layer_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded native HLOD layer or empty explicit clear, inspected actor/layer/grid identity guards.
    Native CanEditChange/runtime hash IsValidHLODLayer for changed nonnull layer; clear skips default resolution.
    Actor transaction/setter/notification/readback/no-op/dry-run/dirty package reporting/no load/build/save.
    No HLOD generation/asset edits; relevance/layer graph/descriptor refresh/external persistence/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/hlod-layer", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "ExpectedAssetPath": expected_layer_path, "ExpectedName": expected_grid,
        "AssetPath": layer_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_partition_hlod_layer(layer_path: str) -> str:
    """Inspect loaded HLOD asset generation type/builder settings/classes/parent/linked references.
    Bounded128 parent chain/cycle detection, no full linked/dependency graph validation.
    Native type0 Instancing/1 Merge/2 Simplify/3 Approximate/4 Custom/5 CustomHLODActor.
    Legacy layer grids omitted (UE5.7 partition settings own grids); no load/hash/generation/build/save.
    Native readiness/metadata/dirty neutrality unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/inspect", json={
        "AssetPath": layer_path
    }, timeout=120).text


@mcp.tool()
def set_world_partition_hlod_parent(layer_path: str, expected_parent_path: str, parent_path: str,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Set loaded HLOD layer parent/empty clear with inspected parent guard/prospective acyclic chain<=128.
    Native builder source-material reuse precheck/CanEditChange, asset transaction/setter/notification/readback.
    No-op/dry-run/no load/HLOD generation/hash/build/save; shared generated HLODs retained.
    Linked/full dependency graph not validated; callbacks/material eligibility/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/parent", json={
        "AssetPath": layer_path, "ExpectedAssetPath": expected_parent_path, "ParentLayerPath": parent_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_partition_hlod_layer_type(layer_path: str, expected_type: int,
                                        expected_builder_settings_path: str, layer_type: int,
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Set native generation type0..5 with inspected current type/settings-object identity guard.
    Native callback may load HLOD utilities/recreate settings and replace prior configuration.
    Custom requires configured concrete loaded builder class; asset/old-settings transaction/readback/dry-run.
    Reports resulting settings; readiness/parent-linked-material compatibility/undo unverified.
    No reference load/hash/HLOD generation/build/save; shared generated HLODs retained.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/type", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "LayerType": layer_type,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_partition_hlod_layer_class(layer_path: str, expected_type: int,
                                         expected_builder_settings_path: str, field: str,
                                         expected_class_path: str, class_path: str,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Set HLODBuilderClass/HLODActorClass/HLODModifierClass, inspected type/class/settings identity guards.
    Loaded concrete native meta-class compatible class/allowed empty default-disable; active Custom builder cannot clear.
    Inactive builder may be configured before Custom; native callback may recreate settings/load utilities.
    Transaction/notification/readback/no-op/dry-run/no HLOD generation/build/save.
    Builder/settings/Blueprint readiness/parent-material graph/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/class", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field,
        "ExpectedClassPath": expected_class_path, "ClassPath": class_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_hlod_builder_setting_fields(layer_path: str, expected_builder_settings_path: str,
                                        struct_path: str = "", start: int = 0, count: int = 64) -> str:
    """Inspect native HLOD builder settings root or nested struct path(up to8), page1..128.
    Exact settings identity guard, metadata/simple values/array counts/up to32 enum choices.
    No object/array element traversal; soft/composite values omitted, flags not full edit eligibility proof.
    No load/hash/HLOD generation/build/validation/edit/save; native reflection semantics unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/fields", json={
        "AssetPath": layer_path, "ExpectedBuilderSettingsPath": expected_builder_settings_path,
        "FieldName": struct_path, "Start": start, "Count": count
    }, timeout=120).text


def set_hlod_builder_numeric(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                              field_path: str, expected_value: float, value: float,
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Set native builder float/double/int32 leaf, up to8 nested structs/no object-array traversal.
    Inspected layer type/settings identity/path/current value guards, literal clamps/adapter+/-1e9.
    Native property-chain CanEditChange/pre/post notifications/layer-settings transaction/readback/no-op/dry-run.
    Cross-field/EditCondition/parent-material constraints not fully evaluated; callbacks may rewrite/replace.
    No load/hash/HLOD generation/build/save; failure may leave undo transaction, undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/numeric", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_hlod_builder_bool(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                           field_path: str, expected_value: bool, value: bool,
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set native HLOD builder bool/bitfield leaf, up to8 nested structs/no object-array traversal.
    Inspected type/settings identity/path/current flag guards, native chain editability/transaction/notifications/readback.
    No-op/dry-run; EditCondition/cross-field/parent-material constraints not fully evaluated.
    No load/hash/HLOD generation/build/save; custom callback rewrites/settings replacement/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/bool", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_hlod_builder_enum(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                           field_path: str, expected_name: str, name: str,
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set native HLOD builder enum/enum-byte leaf using inspected native current name/visible choice.
    Layer type/settings identity/path guards/up to8 structs/native chain editability/transaction/notifications.
    Hidden/MAX choices rejected; readback/no-op/dry-run/no load/hash/generation/build/save.
    EditCondition/cross-field/parent-material compatibility/callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/enum", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "ExpectedName": expected_name, "Name": name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_hlod_builder_asset_reference(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                                      field_path: str, expected_object_path: str, object_path: str,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set native hard asset-reference leaf, inspected settings/type/path/current reference guards.
    Loaded compatible persistent asset or empty null respecting NoClear; no class/soft/instanced refs.
    Empty expected path aliases native null name; up to8 structs/chain editability/transaction/notifications/readback.
    No-op/dry-run/no load/hash/HLOD generation/build/save; asset class not shader/material readiness proof.
    EditCondition/cross-field/parent-material/custom callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/object", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "ExpectedObjectPath": expected_object_path, "ObjectPath": object_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_partition_hlod_linked_layer(layer_path: str, expected_type: int,
                                          expected_linked_path: str, linked_path: str,
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set CustomHLODActor linked layer with inspected current type/link guard, loaded target/empty clear.
    Nonnull changed link requires CustomHLODActor, stale inactive link can clear; linked-only chain<=128/self-cycle checks.
    Asset transaction/reflected native field/editor notification/readback/no-op/dry-run.
    Parent/combined visibility dependency semantics not validated; no load/hash/generation/build/save, undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/linked", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedAssetPath": expected_linked_path, "LinkedLayerPath": linked_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_hlod_builder_string(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                            field_path: str, expected_value: str, value: str,
                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set native FString builder leaf with exact current string/settings/type guards.
    Up to8 nested editable structs, strings up to4096 code units including empty clear.
    Native property-chain transaction/notifications/readback; no-op/dry-run/no save.
    EditCondition/cross-field/custom callback behavior and undo remain unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/string", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "ExpectedName": expected_value, "Name": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_hlod_builder_name(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                            field_path: str, expected_value: str, value: str,
                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set native FName builder leaf with inspected current name spelling/settings/type guards.
    Up to8 nested editable structs, names shorter than native NAME_SIZE; empty clears to None.
    Case-only changes are no-ops. Native property-chain transaction/notifications/readback; no-op/dry-run/no save.
    EditCondition/cross-field/custom callback behavior and undo remain unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/name", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "ExpectedName": expected_value, "Name": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_hlod_builder_int64(layer_path: str, expected_type: int, expected_builder_settings_path: str,
                           field_path: str, expected_decimal: str, decimal: str,
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set signed int64 builder leaf using canonical decimal strings (full signed64 range).
    Exact current value/type/settings/path guards; rejects overflow, leading zeros and negative zero.
    Canonical integer ClampMin/Max metadata enforced, other clamp forms rejected.
    Native nested property-chain transactions/notifications/readback/no-op/dry-run/no save.
    EditCondition/cross-field/custom callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/settings/int64", json={
        "AssetPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedBuilderSettingsPath": expected_builder_settings_path, "FieldName": field_path,
        "ExpectedName": expected_decimal, "Name": decimal, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_loaded_partition_actor_data_layer(partition_path: str, container_path: str, actor_guid: str,
                                          actor_path: str, data_layer_path: str,
                                          expected_member: bool, member: bool,
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Add/remove already-loaded partition actor membership via native Data Layer editor subsystem.
    Exact partition/container/GUID/actor/layer paths and current membership guards.
    Name-dependent partition actors use whole-set native move; external migration and inherited removals rejected.
    Native read-only/type-context eligibility, transaction/readback/no-op/dry-run; no implicit load/save.
    Native visibility/selection callbacks and external-package persistence/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/data-layer", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "ObjectPath": data_layer_path,
        "bExpectedValue": expected_member, "bValue": member, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_loaded_partition_actor_data_layers(partition_path: str, container_path: str, actor_guid: str,
                                               actor_path: str, start: int = 0, count: int = 64) -> str:
    """Page registered current-world layers with loaded actor effective/direct membership and native eligibility.
    Exact partition/container/GUID/actor identity; paths sorted, pages up to128.
    No load/mutation/save; inherited/context membership differs from direct membership.
    Native eligibility is a current snapshot, callback/undo behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/data-layers/inspect", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_parent(partition_path: str, layer_path: str, expected_parent_path: str,
                                    parent_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Set registered Data Layer parent; empty parent clears to root, empty expected aliases None.
    Native hierarchy/read-only and bounded prospective chain checks, transaction/readback/no-op/dry-run.
    Native callbacks update visibility/loading and may unload/GC/reset undo; changed execution requires
    no loaded dirty nontransient packages globally. No implicit save; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/parent", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path,
        "ExpectedObjectPath": expected_parent_path, "ParentLayerPath": parent_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_data_layer_initial_runtime_state(partition_path: str, layer_path: str,
                                                   expected_state: int, state: int,
                                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set authored runtime layer initial state:0 Unloaded/1 Loaded/2 Activated.
    Current partition/layer/state guards, native editability/transaction/readback/no-op/dry-run.
    Does not activate live runtime or force editor loading; no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/initial-state", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "FieldName": "InitialRuntimeState",
        "ExpectedLayerType": expected_state, "LayerType": state, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_data_layer_initial_visibility(partition_path: str, layer_path: str,
                                                expected_visible: bool, visible: bool,
                                                confirm: bool = False, dry_run: bool = False) -> str:
    """Set authored initial editor visibility with current value/partition/layer guards.
    Native setter/transaction/editability/readback/dry-run; current visibility not forced.
    No implicit save; startup inheritance/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/initial-state", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "FieldName": "bIsInitiallyVisible",
        "bExpectedValue": expected_visible, "bValue": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_short_name(partition_path: str, layer_path: str, expected_name: str,
                                        name: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Rename editable Data Layer short name with inspected current spelling guard.
    Native sanitization/uniqueness may adjust requested name; assigned_short_name reports result/preview.
    Exact current name is no-op. Native transaction/rename broadcast/readback/dry-run/no save.
    Object/asset identity unchanged; native callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/short-name", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "ExpectedName": expected_name,
        "Name": name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_partition_data_layer_instance(partition_path: str, asset_path: str, expected_layer_count: int,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Create ordinary asset-backed Data Layer instance from already-loaded persistent asset.
    Inspected current partition/registry count, writable existing WorldDataLayers/native reference eligibility.
    Duplicate asset rejected; native transaction/add notifications/full registry readback/dry-run/no save.
    No actor membership assigned; private/deprecated/external injection separate; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/create", json={
        "PartitionPath": partition_path, "AssetPath": asset_path, "ExpectedRegistryCount": expected_layer_count,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_data_layer_impact(partition_path: str, layer_path: str,
                                        start: int = 0, count: int = 64) -> str:
    """Inspect direct children and paginated matching registered actor descriptors without loading.
    Reports full loaded-member/registry counts for removal guards and native child reparent preview.
    Compares authored asset/name, existing resolved-name cache and loaded actor membership.
    Raw descriptor cursor, up to128 matches; incomplete unloaded/inherited context coverage.
    Missing cache not resolved; not proof a layer is unreferenced or safe to delete.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/impact", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def delete_partition_data_layer_instance(partition_path: str, layer_path: str, expected_name: str,
                                         expected_asset_path: str, expected_layer_count: int,
                                         expected_child_count: int, expected_loaded_actor_count: int,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Remove ordinary layer instance via native editor subsystem; source asset retained.
    Guards current identity/name/asset/registry/child/loaded-member counts and native removal eligibility.
    Native removal reparents children/resolves descriptors; actor authored references can remain unresolved.
    Transaction/dry-run/registry readback, no save. Execution requires no loaded dirty packages.
    Known loaded actor impacts reported; unloaded package cleanup/undo/external persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/delete", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "ExpectedName": expected_name,
        "ExpectedAssetPath": expected_asset_path, "ExpectedRegistryCount": expected_layer_count,
        "ExpectedChildCount": expected_child_count, "ExpectedLoadedActorCount": expected_loaded_actor_count,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_partition_private_data_layer(partition_path: str, expected_layer_count: int,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Create native private editor Data Layer with constructor-owned embedded asset.
    Current partition/writable ordinary WorldDataLayers/registry count guards.
    Native unique default short name; rename separately, no standalone source asset required.
    Native transaction/add broadcasts/registry+owned-asset readback/dry-run/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/create-private", json={
        "PartitionPath": partition_path, "ExpectedRegistryCount": expected_layer_count,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_data_layers(partition_path: str, start: int = 0, count: int = 64) -> str:
    """Page current-world registered Data Layers without requiring an actor path.
    Reports registry count, class/private/asset/owner/package/current and initial states/native editability.
    Paths sorted/pages1..128; no load/reference acquisition/mutation/save. Snapshot unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_visibility(partition_path: str, layer_path: str,
                                        expected_visible: bool, visible: bool,
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Set current editor Data Layer visibility with inspected current flag/path guards.
    Native transaction/Modify(false)/visibility and selection refresh/readback/dry-run.
    Reports known loaded descendant-member potential impacts; parent visibility can still mask layer.
    No explicit dirty/save/load or initial-visibility change; native callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/visibility", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path,
        "bExpectedValue": expected_visible, "bValue": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_loading(partition_path: str, layer_path: str,
                                     expected_loaded: bool, loaded: bool,
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set current editor Data Layer load flag with exact current state/identity guards.
    Native user-change callbacks can load/unload actors, refresh selection, GC/reset undo.
    Changed execution requires no loaded dirty nontransient packages; dry-run reports precondition.
    Reports loaded actor deltas and dirty snapshots. Parent/other references can mask effect.
    No explicit transaction/save/build; per-user settings may update; behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/loading", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path,
        "bExpectedValue": expected_loaded, "bValue": loaded, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_loaded_partition_actor_data_layers(partition_path: str, container_path: str, actor_guid: str,
                                               actor_path: str, expected_layer_paths: list[str],
                                               layer_paths: list[str], confirm: bool = False,
                                               dry_run: bool = False) -> str:
    """Replace whole effective membership using public native remove/add deltas; exact set guards<=64.
    Registered ordinary layers/native eligibility; inherited memberships must remain.
    Name-dependent partition actors/external migration require separate native move workflow.
    Transaction/readback/dry-run/no save; callbacks can leave partial undo transaction on failure.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/data-layers/replace", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "ExpectedDataLayerPaths": expected_layer_paths, "DataLayerPaths": layer_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def move_partition_actor_data_layers(partition_path: str, container_path: str, actor_guid: str,
                                     actor_path: str, expected_external_package: str,
                                     expected_layer_paths: list[str], layer_paths: list[str],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Native ActorPartition move for name-dependent external actors, with whole current set/package guards.
    Native move renames actor/label, migrates external package/dependent objects and checks destination collision.
    Changed execution requires globally clean loaded packages. Dry-run checks adapter eligibility only.
    Native nontransactional rename/package migration is not fully undoable; partial failure needs inspection.
    Source actor path/package can change; no save/redirector migration; callbacks/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/data-layers/move-partition-actor", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "ExpectedObjectPath": expected_external_package,
        "ExpectedDataLayerPaths": expected_layer_paths, "DataLayerPaths": layer_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def inspect_data_layer_asset(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect loaded standalone Data Layer type/filter/debug color and loaded instance consumers.
    Sorted consumer detail pages1..128 include world/owner/parent/local flags/package state.
    No load/mutation/save; private embedded assets excluded, unloaded references not enumerated.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layer-assets/inspect", json={
        "AssetPath": asset_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_data_layer_asset_enum(asset_path: str, expected_type: int, field_name: str,
                              expected_value: int, value: int,
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Set DataLayerType (0 Runtime/1 Editor) or runtime-only LoadFilter (0 None/1 ClientOnly/2 ServerOnly).
    Shared ordinary standalone asset/current type+field guards/native editability/transaction/readback/dry-run.
    Reports loaded consumers; hierarchy/network/cook effects not validated. No save/build; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layer-assets/enum", json={
        "AssetPath": asset_path, "ExpectedLayerType": expected_type, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_data_layer_asset_actor_filters(asset_path: str, expected_type: int,
                                       expected_supported: bool, supported: bool,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set standalone ordinary Data Layer actor-filter support with inspected type/current flag guards.
    Native editability/transaction/property callbacks/readback/dry-run; existing filters not migrated.
    No explicit rebuild/save; native shared consumers/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layer-assets/actor-filters", json={
        "AssetPath": asset_path, "ExpectedLayerType": expected_type,
        "bExpectedValue": expected_supported, "bValue": supported, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_data_layer_asset_debug_color(asset_path: str, expected_type: int,
                                     expected_rgba_bytes: list[int], rgba_bytes: list[int],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set native Data Layer debug color using exactly4 RGBA byte channels0..255.
    Inspected type/full color guards/native setter/transaction/property notifications/readback/dry-run.
    Black can be replaced natively at PostLoad; no explicit render refresh/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layer-assets/debug-color", json={
        "AssetPath": asset_path, "ExpectedLayerType": expected_type,
        "ExpectedColorBytes": expected_rgba_bytes, "ColorBytes": rgba_bytes,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_data_layer_asset(asset_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Create standalone ordinary Data Layer asset using native factory/AssetTools, no overwrite.
    Valid /Game package or matching object path; native defaults Runtime and seeded debug color.
    Native transaction/registry readback/dry-run/no save; no world instance or membership created.
    Factory callbacks/undo/registry/cold persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layer-assets/create", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_world_partition_hlod_layer_asset(asset_path: str, confirm: bool = False,
                                            dry_run: bool = False) -> str:
    """Create native HLOD Layer using factory/AssetTools at new /Game path, no overwrite.
    Native factory may synchronously load engine default template and duplicate settings/linked ref;
    parent cleared. Dry-run skips factory/template load and cannot predict defaults.
    Transaction/readback/no save or world assignment/generation/build; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/create", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_default_hlod_layer(partition_path: str) -> str:
    """Inspect current initialized partition default HLOD reference/streaming/editability/package state.
    No actor traversal/load/generation/mutation/save; inheritance/grid readiness not evaluated.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-default/inspect", json={
        "PartitionPath": partition_path
    }, timeout=180).text


@mcp.tool()
def set_partition_default_hlod_layer(partition_path: str, expected_layer_path: str, layer_path: str,
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set native partition default HLOD reference; loaded persistent layer or empty clear.
    Current reference/partition/streaming/editability guards/transaction/notifications/readback/dry-run.
    Actors using inherited default may change selection; no eager assignment/grid validation/rebuild/save.
    Native callbacks/undo/map persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-default", json={
        "PartitionPath": partition_path, "ExpectedAssetPath": expected_layer_path, "AssetPath": layer_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_streaming_setting(partition_path: str, layer_path: str,
                                               expected_type: int, field_name: str,
                                               expected_value: int, value: int,
                                               confirm: bool = False, dry_run: bool = False) -> str:
    """Set StreamingPriority signed32 (lower=higher priority) or OverrideBlockOnSlowStreaming0..2.
    Override0 NoOverride/1 Blocking/2 NotBlocking; inspected layer type/current field guards.
    Native editability/transaction/property events/readback/dry-run/no save or runtime activation.
    Editor layers retain inactive values; combined grid/runtime policy/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/streaming-setting", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "ExpectedLayerType": expected_type,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_locked(partition_path: str, layer_path: str,
                                    expected_locked: bool, locked: bool,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Set local Data Layer lock with inspected current bitfield and writable ordinary owner guards.
    Native SetIsLocked/transaction/property events/readback/dry-run; self lock can be unlocked.
    Other runtime-owner/custom read-only restrictions remain; reports reason after change.
    No membership edit/save; native outliner notifications/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/locked", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path,
        "bExpectedValue": expected_locked, "bValue": locked, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_filter_included(partition_path: str, layer_path: str,
                                             expected_type: int, expected_asset_path: str,
                                             expected_included: bool, included: bool,
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set per-instance default actor-filter inclusion with current flag/type/asset guards.
    Native SupportsActorFilters/editability/read-only/transaction/property callbacks/readback/dry-run.
    Asset support unchanged; no explicit Level Instance filter rebuild/override migration/save.
    Native filter consumers/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/filter-included", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedAssetPath": expected_asset_path, "bExpectedValue": expected_included, "bValue": included,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_data_layer_instance_asset(partition_path: str, layer_path: str,
                                            expected_type: int, expected_asset_path: str, asset_path: str,
                                            expected_layer_count: int, expected_loaded_actor_count: int,
                                            confirm: bool = False, dry_run: bool = False) -> str:
    """Replace ordinary instance asset reference or empty clear, without migrating actor references.
    Native duplicate/reference/editability and current type/reference/registry/loaded impact guards.
    Transaction/property callback re-resolves descriptors; prior actors may become unresolved.
    Clear leaves invalid asset reference for repair; changed execution requires globally clean packages.
    No save; hierarchy/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/asset", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "ExpectedLayerType": expected_type,
        "ExpectedAssetPath": expected_asset_path, "AssetPath": asset_path,
        "ExpectedRegistryCount": expected_layer_count, "ExpectedLoadedActorCount": expected_loaded_actor_count,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_definitions(partition_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect authored native RuntimeHashSet main/HLOD partition definitions, page1..128.
    Existing object identities/ownership/priority/range/bounds/flags/LHGrid size and2D.
    Up to16 HLOD setups/16 refs each, full counts/truncation; no cell generation/actor load/mutation/save.
    SpatialHash adapter separate; indices unstable and grid/class eligibility not validated; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


def set_partition_runtime_definition_numeric(partition_path: str, runtime_hash_path: str,
                                             definition_path: str, expected_name: str,
                                             expected_hlod_index: int, expected_definition_count: int,
                                             field_name: str, expected_value: int, value: int,
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Edit LoadingRange0..1e9, LHGrid CellSize1600..1e9, or main Priority signed32.
    Exact current hash/owned unique definition/name/HLOD index/count/value guards.
    Native editability/transaction/property callbacks/reacquired readback/dry-run/no save.
    Grid preview can update; generated cells/HLOD derivative settings not rebuilt; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/numeric", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_runtime_definition_bool(partition_path: str, runtime_hash_path: str,
                                          definition_path: str, expected_name: str,
                                          expected_hlod_index: int, expected_definition_count: int,
                                          field_name: str, expected_value: bool, value: bool,
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set main bBlockOnSlowStreaming/bClientOnlyVisible or LHGrid bIs2D.
    Full inspected ownership/current flag guards/native main-only condition/transaction/readback/dry-run.
    Grid preview may reset/update; generated cells/HLOD not rebuilt, no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/bool", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "FieldName": field_name,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_runtime_definition_bounds_mode(partition_path: str, runtime_hash_path: str,
                                                 definition_path: str, expected_name: str,
                                                 expected_hlod_index: int, expected_definition_count: int,
                                                 expected_mode: int, mode: int,
                                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set main bounds mode0 UseContent/1 UseCellBounds/2 UseMinContentCellBounds.
    Full inspected ownership/current mode guards/native eligibility/transaction/readback/dry-run/no save.
    Generated cells/HLOD and actor bounds compatibility not rebuilt/validated; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/bounds-mode", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "ExpectedValue": expected_mode, "Value": mode,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_runtime_definition_origin(partition_path: str, runtime_hash_path: str,
                                            definition_path: str, expected_name: str,
                                            expected_hlod_index: int, expected_definition_count: int,
                                            expected_origin: list[float], origin: list[float],
                                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set main LHGrid origin XYZ within +/-1e9 with full inspected ownership/current vector guards.
    Native transaction/preview callbacks/readback/dry-run/no save; generated cells not rebuilt/migrated.
    """
    if len(expected_origin) != 3 or len(origin) != 3:
        raise ValueError("Origin vectors require exactly3 XYZ coordinates")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/origin", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count,
        "ExpectedCenter": dict(zip(("X", "Y", "Z"), expected_origin)), "Center": dict(zip(("X", "Y", "Z"), origin)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_runtime_definition_debug_color(partition_path: str, runtime_hash_path: str,
                                                 definition_path: str, expected_name: str,
                                                 expected_hlod_index: int, expected_definition_count: int,
                                                 expected_rgba: list[float], rgba: list[float],
                                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set main/HLOD runtime partition linear debug RGBA0..1, full inspected ownership/color guards.
    Native transaction/preview callbacks/readback/dry-run/no save or generated-cell refresh; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/debug-color", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "ExpectedColorValues": expected_rgba, "ColorValues": rgba,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_runtime_hlod_layer_reference(partition_path: str, runtime_hash_path: str,
                                              definition_path: str, expected_name: str,
                                              expected_hlod_index: int, expected_definition_count: int,
                                              item_index: int, expected_layer_path: str, layer_path: str,
                                              confirm: bool = False, dry_run: bool = False) -> str:
    """Replace existing runtime HLOD setup reference slot with loaded persistent HLOD layer.
    Full inspected ownership/current ref guards; duplicate target anywhere in sibling setups rejected.
    Native nested array index notifications/transaction/full target-array readback/dry-run/no save.
    No add/remove/clear/generation/build; chain callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-layer", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "ItemIndex": item_index,
        "ExpectedAssetPath": expected_layer_path, "AssetPath": layer_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_partition_runtime_hlod_layer_references(partition_path: str, runtime_hash_path: str,
                                                    definition_path: str, expected_name: str,
                                                    expected_hlod_index: int, expected_definition_count: int,
                                                    expected_layer_paths: list[str], layer_paths: list[str],
                                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Add/remove/reorder/clear HLOD setup refs through full ordered array replacement<=128.
    Full ownership/current ordered path guards; expected nulls use None spelling, requested refs nonnull/loaded.
    Duplicate requested/sibling assignments rejected; native nested chain/transaction/readback/dry-run/no save.
    No hierarchy/grid validation/generation/build; native events/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-layers", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count,
        "ExpectedHLODLayerPaths": expected_layer_paths, "HLODLayerPaths": layer_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_hlod_layer_references(partition_path: str, runtime_hash_path: str,
                                                    definition_path: str, expected_name: str,
                                                    expected_hlod_index: int, expected_definition_count: int,
                                                    start: int = 0, count: int = 64) -> str:
    """Page all existing HLOD setup reference slots1..128 with full inspected setup ownership guards.
    Reports native null spelling None and current layer types without loading/mutation/generation/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-layers/inspect", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def rename_partition_runtime_definition(partition_path: str, runtime_hash_path: str,
                                        definition_path: str, expected_name: str,
                                        expected_hlod_index: int, expected_definition_count: int,
                                        name: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Rename main runtime grid or HLOD setup with exact inspected ownership/current name guards.
    Unique token name, case-only no-op/native chain notifications/update object and row display/readback.
    Known descriptor grid refs reported but not migrated; old explicit actor grid names can become invalid.
    No generated asset rename/build/save; transaction/dry-run; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/name", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "Name": name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_partition_runtime_hlod_setup(partition_path: str, runtime_hash_path: str,
                                     main_definition_path: str, expected_name: str,
                                     expected_definition_count: int, expected_setup_paths: list[str],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Append spatial HLOD setup before trailing persistent setup via native ArrayAdd/fixup.
    Full main ownership/current ordered setup paths<64/native class-index/name/overflow guards.
    Native ancestor duplication/scaled defaults/transaction/readback/dry-run/no save.
    Fixup may recreate persistent setup/update derivatives; no generation/build; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-setups/add", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": main_definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": -1, "ExpectedRegistryCount": expected_definition_count,
        "ExpectedSetupPaths": expected_setup_paths, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_hlod_setups(partition_path: str, runtime_hash_path: str,
                                          main_definition_path: str, expected_name: str,
                                          expected_definition_count: int,
                                          start: int = 0, count: int = 64) -> str:
    """Page authored spatial/nonspatial HLOD setup identities1..128 with full main ownership guards.
    Reports definition class/name/HLOD index/range and refs16/count/truncation, no load/mutation/save.
    Nonspatial setup can use INDEX_NONE; structural role is not inferred from native index.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-setups/inspect", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": main_definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": -1,
        "ExpectedRegistryCount": expected_definition_count, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def remove_partition_runtime_hlod_setup(partition_path: str, runtime_hash_path: str,
                                        definition_path: str, expected_name: str, expected_hlod_index: int,
                                        expected_definition_count: int, expected_setup_paths: list[str],
                                        expected_layer_paths: list[str],
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Remove spatial HLOD setup with full ordered setup and removed reference guards.
    Native ArrayRemove/fixup preserves surviving object/order/names/refs; persistent setup may be recreated.
    Removed refs become unassigned, assets/generated HLODs untouched; native indices not renumbered.
    Later append guards can reject index gaps. Transaction/dry-run/no save; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-setups/remove", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "ExpectedSetupPaths": expected_setup_paths,
        "ExpectedHLODLayerPaths": expected_layer_paths, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def normalize_partition_runtime_hlod_indices(partition_path: str, runtime_hash_path: str,
                                             main_definition_path: str, expected_name: str,
                                             expected_definition_count: int, expected_setup_paths: list[str],
                                             expected_indices: list[int],
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Normalize spatial HLOD indices to array order after removal; persistent index unchanged.
    Full ordered setup path/index/ownership guards; transaction/derived property callbacks/readback/dry-run.
    Setup names/refs preserved. Indices affect future generated cell GUIDs; no rebuild/migration/save.
    Later append may require rename to avoid generated-name collision; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-setups/normalize-indices", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": main_definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": -1,
        "ExpectedRegistryCount": expected_definition_count, "ExpectedSetupPaths": expected_setup_paths,
        "ExpectedSetupIndices": expected_indices, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_partition_runtime_hlod_setups(partition_path: str, runtime_hash_path: str,
                                         main_definition_path: str, expected_name: str,
                                         expected_definition_count: int, expected_setup_paths: list[str],
                                         setup_paths: list[str], confirm: bool = False,
                                         dry_run: bool = False) -> str:
    """Permute spatial HLOD setups with full ordered path guards<=64; persistent setup remains last.
    Native ArrayMove/fixup/transactions preserve spatial objects/names/refs, may recreate persistent object.
    Native indices/ranges not recomputed; explicit normalization/settings edits separate.
    No generated rebuild/migration/save; dry-run/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/hlod-setups/reorder", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": main_definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": -1,
        "ExpectedRegistryCount": expected_definition_count, "ExpectedSetupPaths": expected_setup_paths,
        "SetupPaths": setup_paths, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_spatial_hash_grids(partition_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect authored RuntimeSpatialHash grid definitions/page1..128 without actor load/generation.
    Names/cell size/range/priority/block-client flags/XY origin/debug RGBA/HLOD references.
    Excludes generated StreamingGrids and grid-info actor contributions; no mutation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_partition_spatial_hash_grid_numeric(partition_path: str, runtime_hash_path: str,
                                            grid_index: int, expected_name: str, expected_grid_count: int,
                                            field_name: str, expected_value: float, value: float,
                                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set SpatialHash CellSize1600..1e9/Priority signed32/float LoadingRange0..1e9.
    Exact grid count/index/unique name/current value guards/native chain transaction/full sibling readback.
    Rejects invalid sibling values native callbacks would clamp; native float value reported.
    No generated-grid rebuild/load/save; native callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/numeric", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ItemIndex": grid_index,
        "ExpectedName": expected_name, "ExpectedRegistryCount": expected_grid_count, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_spatial_hash_grid_blocking(partition_path: str, runtime_hash_path: str,
                                             grid_index: int, expected_name: str, expected_grid_count: int,
                                             expected_blocking: bool, blocking: bool,
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set native editable slow-stream blocking flag with full identity/value guards/transaction/readback.
    Full sibling grid state preserved, dry-run/no save or generated cell rebuild; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/appearance", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ItemIndex": grid_index,
        "ExpectedName": expected_name, "ExpectedRegistryCount": expected_grid_count,
        "FieldName": "bBlockOnSlowStreaming", "bExpectedValue": expected_blocking, "bValue": blocking,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_spatial_hash_grid_origin(partition_path: str, runtime_hash_path: str,
                                           grid_index: int, expected_name: str, expected_grid_count: int,
                                           expected_xy: list[float], xy: list[float],
                                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set native grid XY origin within +/-1e9, full identity/vector guards/transaction/readback.
    No generated cell/actor package migration/rebuild/save; dry-run; unverified.
    """
    if len(expected_xy) != 2 or len(xy) != 2:
        raise ValueError("Origin requires exactly2 XY coordinates")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/appearance", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ItemIndex": grid_index,
        "ExpectedName": expected_name, "ExpectedRegistryCount": expected_grid_count, "FieldName": "Origin",
        "ExpectedCenter": {"X": expected_xy[0], "Y": expected_xy[1], "Z": 0},
        "Center": {"X": xy[0], "Y": xy[1], "Z": 0}, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_spatial_hash_grid_debug_color(partition_path: str, runtime_hash_path: str,
                                                grid_index: int, expected_name: str, expected_grid_count: int,
                                                expected_rgba: list[float], rgba: list[float],
                                                confirm: bool = False, dry_run: bool = False) -> str:
    """Set grid linear debug RGBA0..1 with full current color/identity guards/transaction/readback.
    No explicit renderer/generated grid sync/save; native float conversion/dry-run; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/appearance", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ItemIndex": grid_index,
        "ExpectedName": expected_name, "ExpectedRegistryCount": expected_grid_count, "FieldName": "DebugColor",
        "ExpectedColorValues": expected_rgba, "ColorValues": rgba, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def rename_partition_spatial_hash_grid(partition_path: str, runtime_hash_path: str,
                                       grid_index: int, expected_name: str, expected_grid_count: int,
                                       name: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Rename authored SpatialHash grid with exact current identity/name/count guards.
    Duplicate/native sibling auto-name effects rejected; transaction/nested event/full sibling readback.
    Known descriptor exact grid refs reported, not migrated; old explicit actor refs can become invalid.
    No generated grid/package rename/build/save; dry-run/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/name", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ItemIndex": grid_index,
        "ExpectedName": expected_name, "ExpectedRegistryCount": expected_grid_count, "Name": name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_partition_spatial_hash_grid(partition_path: str, runtime_hash_path: str,
                                    expected_grid_names: list[str], name: str,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Append authored SpatialHash grid with full ordered unique current names/count<128 guards.
    Native constructor defaults/random color/array transaction/Add event/full sibling readback.
    Dry-run skips constructor/random generation; no actor assignment/grid-info collision scan/build/save.
    Native initialization/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/add", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_grid_names), "ExpectedGridNames": expected_grid_names,
        "Name": name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_partition_spatial_hash_grid(partition_path: str, runtime_hash_path: str,
                                       expected_grid_names: list[str], grid_index: int, expected_name: str,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Remove authored grid with full ordered count/name/index guards and preserve at least one.
    Native array transaction/removal event/full survivor and default-grid readback/dry-run/no save.
    Explicit refs and None-default changes reported, not migrated; generated grids untouched/unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/remove", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_grid_names), "ExpectedGridNames": expected_grid_names,
        "ItemIndex": grid_index, "ExpectedName": expected_name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_partition_spatial_hash_grids(partition_path: str, runtime_hash_path: str,
                                         expected_grid_names: list[str], grid_names: list[str],
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Reorder authored grids by full unique name permutation; first grid becomes default.
    Full current order guard/native transaction/ArrayMove/full values and default readback/dry-run/no save.
    None-grid descriptor impacts reported; no actor reference/generated cell migration/build; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grids/reorder", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_grid_names), "ExpectedGridNames": expected_grid_names,
        "GridNames": grid_names, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_spatial_hash_settings(partition_path: str) -> str:
    """Inspect authored project overrides0..2/current native defaults/resolved flags/Z culling/cached settings.
    No CVar/config/cache writes or generation/load/save; cached generation values can be stale.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/settings/inspect", json={
        "PartitionPath": partition_path
    }, timeout=180).text


def set_partition_spatial_hash_override(partition_path: str, runtime_hash_path: str,
                                        field_name: str, expected_override: int, override: int,
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Set UseAlignedGridLevels/SnapNonAlignedGridLevelsToLowerLevels/PlaceSmallActorsUsingLocation/
    PlacePartitionActorsUsingLocation:0 ProjectDefault/1 Disabled/2 Enabled.
    Native guards/transaction/readback/dry-run; no global CVar/config/cache write/build/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/settings", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "FieldName": field_name,
        "ExpectedValue": expected_override, "Value": override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_spatial_hash_z_culling(partition_path: str, runtime_hash_path: str,
                                         expected_enabled: bool, enabled: bool,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Set authored SpatialHash Z culling with current flag/hash guards/native transaction/readback/dry-run.
    Existing generated cells not rebuilt; no config write/save; native behavior/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/settings", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "FieldName": "bEnableZCulling",
        "bExpectedValue": expected_enabled, "bValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_partition_runtime_main_definition(partition_path: str, runtime_hash_path: str,
                                          expected_definition_paths: list[str], name: str,
                                          class_path: str = "/Script/Engine.RuntimePartitionLHGrid",
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Append native HashSet main definition from loaded concrete runtime partition class.
    Full ordered current main path/name/count/new token guards; constructor+SetDefaultValues.
    Native ArrayAdd/MainLayer chain/fixup/readback; config may add persistent HLOD setup.
    Dry-run skips creation; no default HLOD hierarchy/actor assignment/generation/build/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/add", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_definition_paths), "ExpectedDefinitionPaths": expected_definition_paths,
        "Name": name, "ClassPath": class_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_partition_runtime_main_definition(partition_path: str, runtime_hash_path: str,
                                             expected_definition_paths: list[str], definition_index: int,
                                             expected_name: str, expected_setup_paths: list[str],
                                             expected_flat_hlod_layer_paths: list[str],
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Remove main HashSet definition preserving at least one, full ordered path/name/HLOD impact guards.
    Native ArrayRemove/transaction/full survivor and default readback/dry-run/no save.
    Source assets/generated content retained, refs unassigned; explicit/default descriptor impacts not migrated.
    Native events/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/remove", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_definition_paths), "ExpectedDefinitionPaths": expected_definition_paths,
        "ItemIndex": definition_index, "ExpectedName": expected_name, "ExpectedSetupPaths": expected_setup_paths,
        "ExpectedHLODLayerPaths": expected_flat_hlod_layer_paths, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_partition_runtime_main_definitions(partition_path: str, runtime_hash_path: str,
                                               expected_definition_paths: list[str], definition_paths: list[str],
                                               confirm: bool = False, dry_run: bool = False) -> str:
    """Permute authored main definitions with full ordered identity guards; first becomes default grid.
    Native ArrayMove/transaction/full descriptor-survivor/default readback/dry-run/no save.
    Known None-grid descriptor impacts reported, generated cells not rebuilt/migrated; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/reorder", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_definition_paths), "ExpectedDefinitionPaths": expected_definition_paths,
        "DefinitionPaths": definition_paths, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_partition_runtime_main_class(partition_path: str, runtime_hash_path: str,
                                         expected_definition_paths: list[str], definition_index: int,
                                         expected_name: str, expected_class_path: str, class_path: str,
                                         expected_setup_paths: list[str], expected_flat_hlod_layer_paths: list[str],
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Replace selected main with loaded concrete runtime class/native defaults; grid name retained.
    Full current main/class/HLOD identity-reference guards/transaction/native MainLayer fixup/readback.
    Main old settings not copied, HLOD objects may be recreated/scaled. No actor/generated rebuild/save.
    Dry-run skips constructors/overflow compatibility proof; custom effects/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/class", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path,
        "ExpectedRegistryCount": len(expected_definition_paths), "ExpectedDefinitionPaths": expected_definition_paths,
        "ItemIndex": definition_index, "ExpectedName": expected_name, "ExpectedClassPath": expected_class_path,
        "ClassPath": class_path, "ExpectedSetupPaths": expected_setup_paths,
        "ExpectedHLODLayerPaths": expected_flat_hlod_layer_paths, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_spatial_hash_grid_info_actors(partition_path: str,
                                                    start: int = 0, count: int = 64) -> str:
    """Inspect loaded native hidden/NotPlaceable grid-info actor contributions/page1..128.
    Native settings/identity/dirty state and same-name full-settings conflicts with authored/loaded info grids.
    Unloaded descriptor sources excluded; no load/reference acquisition/generation/mutation/save.
    Native internal actor creation/editing separate; not generation validation, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/spatial-hash/grid-info/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_streaming(partition_path: str) -> str:
    """Inspect authored/effective/editor partition streaming flags and registered/loaded descriptor counts.
    No actor reference acquisition/loading/generation/mutation/save; loaded flags not readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/streaming/inspect", json={
        "PartitionPath": partition_path
    }, timeout=180).text


@mcp.tool()
def set_partition_streaming(partition_path: str, expected_enabled: bool, enabled: bool,
                             confirm: bool = False, dry_run: bool = False) -> str:
    """Native main partition streaming setter with exact current flag/identity and clean-package guards.
    Owns native transaction/descriptor rehash/always-loaded loader replacement/editor reconstruction.
    Can load all actors/dependencies or unload/GC/reset undo; actor/dirty deltas reported128/full counts.
    Dry-run skips setter; no implicit save/generation/build, native loader/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/streaming", json={
        "PartitionPath": partition_path, "bExpectedValue": expected_enabled, "bValue": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_policies(partition_path: str) -> str:
    """Inspect authored native server streaming/stream-out/Data Layer logic enums/choices/editability.
    No runtime cache/project defaults/generation/load/mutation/save; network behavior not evaluated.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/policies/inspect", json={
        "PartitionPath": partition_path
    }, timeout=180).text


@mcp.tool()
def set_partition_policy(partition_path: str, field_name: str, expected_value: int, value: int,
                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set ServerStreamingMode0..3, ServerStreamingOutMode0..2 or DataLayersLogicOperator0 Or/1 And.
    Server modes:0 ProjectDefault/1 Disabled/2 Enabled/3 EnabledInPIE (streaming-mode only).
    Native editability/current enum/transaction/readback/dry-run; no runtime cache/CVar/config change/save.
    Native future network/multi-layer semantics/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/policies", json={
        "PartitionPath": partition_path, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_hlod_options(partition_path: str) -> str:
    """Inspect authored HLOD editor permission/standalone build flag/native experimental eligibility.
    Flag is not generated asset presence/readiness proof; no display refresh/load/build/mutation/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-options/inspect", json={
        "PartitionPath": partition_path
    }, timeout=180).text


@mcp.tool()
def set_partition_hlod_option(partition_path: str, field_name: str,
                               expected_value: bool, value: bool,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Set bAllowShowingHLODsInEditor or bHasStandaloneHLOD authored flag with native eligibility.
    Current value/main identity guards/transaction/notifications/readback/dry-run; no save/build.
    Native experimental setting unchanged; generated HLOD readiness/display refresh not guaranteed.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-options", json={
        "PartitionPath": partition_path, "FieldName": field_name, "bExpectedValue": expected_value,
        "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_actor_pin(partition_path: str, container_path: str, actor_guid: str) -> str:
    """Inspect native pin hold/weak loaded state and GUID-only API descriptor identity compatibility.
    No hard actor reference/load/pin mutation/save; child-container GUIDs may not be addressable.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/pin/inspect", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid
    }, timeout=180).text


@mcp.tool()
def set_partition_actor_pin(partition_path: str, container_path: str, actor_guid: str,
                             actor_soft_path: str, expected_pinned: bool, pinned: bool,
                             expected_loaded: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Native partition-owned actor pin/unpin with exact descriptor/current pin+loaded state guards.
    Changed execution requires globally clean packages; loaders may load dependencies/unload/GC/reset undo.
    Pin state not exclusive residency/readiness proof; reports actor/dirty deltas, no transaction/save.
    Dry-run/no-op/native lifetime/undo/session persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/pin", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_soft_path, "bExpectedValue": expected_pinned, "bValue": pinned,
        "bExpectedLoaded": expected_loaded, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_actor_pins(partition_path: str, entries: list[dict], pinned: bool,
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Batch1..64 native actor pin/unpin holds; entries use ContainerPath/ActorGuid/ActorPath/
    bExpectedPinned/bExpectedLoaded. All identities/states preflighted, duplicate GUIDs rejected.
    Changed GUIDs sent in one native refresh; clean-package guard/ordered readback/actor-dirty deltas.
    Native callbacks may leave partial state/load dependencies/unload/GC/reset undo; no transaction/save.
    Dry-run/native batch lifecycle/undo/session persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actors/pin", json={
        "PartitionPath": partition_path, "PinEntries": entries, "bValue": pinned,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_actor_pins(partition_path: str, pinned: bool = True,
                                  start: int = 0, count: int = 64) -> str:
    """Page native GUID-addressable descriptors matching pinned/unpinned state, up to128 matches.
    Raw descriptor cursor/native metadata/weak loaded state supplies batch guards; no hard actor load/mutation.
    Unaddressable child GUIDs skipped/count reported, no total pin count or residency/readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actors/pins/inspect", json={
        "PartitionPath": partition_path, "bValue": pinned, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_streaming_source_components(partition_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect loaded authored editor source components/owner identity/flags/enums/grids/color/shape count.
    Component registered state is not runtime provider registration; no source/completion evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


def set_partition_streaming_source_enabled(partition_path: str, component_path: str,
                                            actor_path: str, actor_guid: str,
                                            expected_enabled: bool, enabled: bool,
                                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set authored source enabled flag with exact component/owner/current guards/native enable-disable.
    Transaction/notifications/readback/dry-run/no save or runtime registration/activation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/setting", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "FieldName": "bStreamingSourceEnabled", "bExpectedValue": expected_enabled,
        "bValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_streaming_source_enum(partition_path: str, component_path: str,
                                         actor_path: str, actor_guid: str, field_name: str,
                                         expected_value: int, value: int,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Set Priority0/64/128/192/255, TargetBehavior0 Include/1 Exclude or TargetState0 Loaded/1 Activated.
    Exact authored component/owner/current field/native visible enum guards/transaction/readback/dry-run.
    No runtime provider registration/streaming activation/generation/save; callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/setting", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_partition_streaming_source_target_grids(partition_path: str, component_path: str,
                                                    actor_path: str, actor_guid: str,
                                                    expected_behavior: int, expected_grid_names: list[str],
                                                    grid_names: list[str], confirm: bool = False,
                                                    dry_run: bool = False) -> str:
    """Add/remove/reorder/clear source target grids through full ordered list<=64/current behavior guards.
    Unique native FNames, explicit None allowed; Include empty affects all, Exclude empty excludes none.
    Native transaction/array notifications/readback/dry-run/no save; target existence not validated.
    No runtime provider registration/activation/load/build; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/target-grids", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "ExpectedValue": expected_behavior,
        "ExpectedGridNames": expected_grid_names, "GridNames": grid_names,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_streaming_source_shapes(partition_path: str, component_path: str,
                                              actor_path: str, actor_guid: str,
                                              start: int = 0, count: int = 64) -> str:
    """Page authored source shapes1..128 as native DTO-compatible objects for exact array guards.
    Empty list uses grid-range sphere fallback; no geometry/source/streaming evaluation/load/mutation/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/shapes/inspect", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def replace_partition_streaming_source_shapes(partition_path: str, component_path: str,
                                              actor_path: str, actor_guid: str, expected_enabled: bool,
                                              expected_shapes: list[dict], shapes: list[dict],
                                              confirm: bool = False, dry_run: bool = False) -> str:
    """Add/remove/reorder/clear native shapes<=64 with exact ordered fields/current enabled guards.
    Shape keys:bUseGridLoadingRange,LoadingRangeScale,Radius,bIsSector,SectorAngle,
    Location{X,Y,Z},Rotation{Pitch,Yaw,Roll}; use inspection shape objects for expected values.
    Finite scale0..1000/radius0..1e9/angle0..360/local XYZ +/-1e9/rotation +/-360000 degrees.
    Native transaction/array events/readback/dry-run/no save; empty restores grid-range fallback.
    No source geometry/cell activation/load/build; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/shapes", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "bExpectedValue": expected_enabled,
        "ExpectedSourceShapes": expected_shapes, "SourceShapes": shapes,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_partition_streaming_source_component(partition_path: str, container_path: str,
                                                actor_guid: str, actor_path: str, name: str,
                                                expected_source_count: int = 0,
                                                confirm: bool = False, dry_run: bool = False) -> str:
    """Create native streaming-source instance on loaded editable descriptor actor/current source count<64.
    Unique object name/owner GUID-path guards/native transaction/instance creation+registration/readback.
    Native defaults/owner transform; editor registration does not register runtime provider or load cells.
    Dry-run/no save, Blueprint template/SCS separate; undo/external persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/create", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "ActorPath": actor_path, "Name": name, "ExpectedRegistryCount": expected_source_count,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_partition_streaming_source_component(partition_path: str, component_path: str,
                                                actor_path: str, actor_guid: str,
                                                expected_source_count: int, expected_enabled: bool,
                                                expected_shape_count: int, expected_target_grid_count: int,
                                                confirm: bool = False, dry_run: bool = False) -> str:
    """Remove actor-owned source instance, excluding native/SCS/default components.
    Exact owner/component/count/enabled/shape-target count guards/native transaction/destruction/readback.
    External references not migrated; dry-run/no save/runtime activation; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/remove", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "ExpectedRegistryCount": expected_source_count,
        "bExpectedValue": expected_enabled, "ExpectedChildCount": expected_shape_count,
        "ExpectedLoadedActorCount": expected_target_grid_count, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_streaming_source_debug_color(partition_path: str, component_path: str,
                                               actor_path: str, actor_guid: str,
                                               expected_rgba_bytes: list[int], rgba_bytes: list[int],
                                               confirm: bool = False, dry_run: bool = False) -> str:
    """Set source debug RGBA bytes0..255 with full color/owner-component guards/transaction/readback.
    No explicit render refresh/provider registration/cell activation/save; dry-run; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/visualization", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "FieldName": "DebugColor", "ExpectedColorBytes": expected_rgba_bytes,
        "ColorBytes": rgba_bytes, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_partition_streaming_source_visualizer_range(partition_path: str, component_path: str,
                                                    actor_path: str, actor_guid: str,
                                                    expected_range: float, loading_range: float,
                                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Set debug-only visualizer range0..1e9 with native float/current value/owner-component guards.
    Does not alter runtime grid loading range. Native transaction/readback/dry-run/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/visualization", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "FieldName": "DefaultVisualizerLoadingRange",
        "ExpectedValue": expected_range, "Value": loading_range, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_classes(partition_path: str, start: int = 0, count: int = 64) -> str:
    """Discover loaded runtime-partition classes/page1..128, creation flag eligibility and editable metadata32.
    Includes abstract/hidden classes for diagnosis; eligibility does not prove constructor/HLOD compatibility.
    No class defaults construction/asset load/mutation/generation/save; native reflection unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/classes/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_definition_fields(partition_path: str, runtime_hash_path: str,
                                                definition_path: str, expected_name: str,
                                                expected_hlod_index: int, expected_definition_count: int,
                                                start: int = 0, count: int = 64) -> str:
    """Inspect existing uniquely owned runtime definition native/custom fields/page1..128.
    Numeric integer decimals/bools/enums/names/hard refs/struct identities/array counts and edit metadata.
    No object traversal/composite export/load/CDO construction/mutation/save; metadata not editability proof.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-definitions/fields/inspect", json={
        "PartitionPath": partition_path, "ExpectedObjectPath": runtime_hash_path, "ObjectPath": definition_path,
        "ExpectedName": expected_name, "ExpectedHLODIndex": expected_hlod_index,
        "ExpectedRegistryCount": expected_definition_count, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def preview_partition_streaming_source_grid_filter(partition_path: str, component_path: str,
                                                   actor_path: str, actor_guid: str,
                                                   grid_names: list[str]) -> str:
    """Preview native source include/exclude matching against supplied grid names<=128.
    Reports filter match and enabled conjunction, duplicates retain input order; None compared literally.
    Does not resolve grid existence/defaults/geometry/provider registration/cell readiness.
    No load/activation/generation/mutation/save; native helper unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/target-grids/preview", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "GridNames": grid_names
    }, timeout=180).text


@mcp.tool()
def preview_partition_streaming_source_shapes(partition_path: str, component_path: str,
                                              actor_path: str, actor_guid: str,
                                              grid_loading_range: float = 25600,
                                              project_in_2d: bool = False) -> str:
    """Native authored shape transform preview with supplied grid range0..1e9/default fallback.
    Returns centers/axes/radii/angles/conservative sphere bounds, owner rotation/location (not actor scale).
    Disabled source still previewed, zero shapes may be omitted; output indices not authored slot mapping.
    No range resolution/provider registration/cell queries/loading/activation/mutation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/sources/shapes/preview", json={
        "PartitionPath": partition_path, "ObjectPath": component_path, "ActorPath": actor_path,
        "ActorGuid": actor_guid, "GridLoadingRange": grid_loading_range, "bProjectIn2D": project_in_2d
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_cell_detail(partition_path: str, cell_path: str, cell_guid: str) -> str:
    """Inspect exact hash-enumerated cell path/GUID:state/policy/HLOD/data-layer and native data bounds.
    No generation/source-cache evaluation/actor load/activation/save; editor may have no runtime cells.
    State ordinals are not rendering/collision/async readiness proof; native getters unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/cells/detail", json={
        "PartitionPath": partition_path, "ObjectPath": cell_path, "ActorGuid": cell_guid
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_cell_contents(partition_path: str, cell_path: str, cell_guid: str,
                                             actor_packages: bool = False,
                                             start: int = 0, count: int = 64) -> str:
    """Page native existing cell actor names or sorted unique package names1..128 without loading.
    Collections are independent, not parallel actor-package mappings; cook may clear editor metadata.
    Empty lists not content absence proof; native getters/full metadata costs unbounded; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/cells/contents/inspect", json={
        "PartitionPath": partition_path, "ObjectPath": cell_path, "ActorGuid": cell_guid,
        "bValue": actor_packages, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_cell_mappings(partition_path: str, cell_path: str, cell_guid: str,
                                             start: int = 0, count: int = 64) -> str:
    """Page existing native level-streaming cell actor/package/container mappings1..128.
    Includes transforms/class paths/editor flags/property override identities16/counts.
    LoadedPath is cached metadata, not live load proof; no package load/cook/mutation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/cells/mappings/inspect", json={
        "PartitionPath": partition_path, "ObjectPath": cell_path, "ActorGuid": cell_guid,
        "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_location_volumes(partition_path: str, start: int = 0, count: int = 64) -> str:
    """Page loaded native LocationVolume actor-owned editor loaders1..128 with identity/hold/bounds/color.
    Separate from partition-owned box region registry; no actor load/adapter creation/Load/Unload/save.
    Pending auto-load/hold flags not residency/readiness proof; native lifetime/getters unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/location-volumes/inspect", json={
        "PartitionPath": partition_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_partition_location_volume_loading(partition_path: str, actor_path: str, actor_guid: str,
                                           expected_label: str, expected_center: list[float],
                                           expected_extent: list[float], expected_loaded: bool,
                                           loaded: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Native existing LocationVolume Load/Unload with exact identity/label/bounds/hold guards.
    Changed execution globally clean packages; native filters/dependencies can load/unload/GC/reset undo.
    Reports actor and dirty deltas, no transaction/brush edit/save; hold not exclusive residency proof.
    """
    if len(expected_center) != 3 or len(expected_extent) != 3:
        raise ValueError("Expected center/extent require exactly3 XYZ values")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/location-volumes/loading", json={
        "PartitionPath": partition_path, "ActorPath": actor_path, "ActorGuid": actor_guid,
        "ExpectedName": expected_label, "Center": dict(zip(("X", "Y", "Z"), expected_center)),
        "Extent": dict(zip(("X", "Y", "Z"), expected_extent)), "bExpectedValue": expected_loaded,
        "bValue": loaded, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_partition_location_volume_debug_color(partition_path: str, actor_path: str, actor_guid: str,
                                               expected_label: str, expected_loaded: bool,
                                               expected_rgba_bytes: list[int], rgba_bytes: list[int],
                                               confirm: bool = False, dry_run: bool = False) -> str:
    """Set authored LocationVolume debug RGBA bytes with exact color/identity/current hold guards.
    Actor transaction/native property notifications/color+hold readback/dry-run/no save.
    No explicit loader reload/brush edit/render refresh; callbacks/undo/external persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/location-volumes/debug-color", json={
        "PartitionPath": partition_path, "ActorPath": actor_path, "ActorGuid": actor_guid,
        "ExpectedName": expected_label, "bExpectedLoaded": expected_loaded,
        "ExpectedColorBytes": expected_rgba_bytes, "ColorBytes": rgba_bytes,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_actor_referencers(partition_path: str, container_path: str, actor_guid: str,
                                         editor_only: bool = False, start: int = 0, count: int = 64) -> str:
    """Reverse one-hop descriptor references in exact target container/page1..128 matches.
    Raw descriptor cursor, optional editor-only list; excludes other-container/unregistered sources.
    Metadata may lag unsaved edits; no transitive/reference safety proof/load/mutation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/referencers/inspect", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "bEditorOnlyReferences": editor_only, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_actor_reference_graph(partition_path: str, container_path: str, actor_guid: str,
                                             editor_only: bool = False, max_depth: int = 4,
                                             node_limit: int = 64) -> str:
    """Bounded same-container BFS descriptor reference graph:<=128 nodes/depth16/1024 edges.
    Includes unresolved targets/frontier limits; repeated edges not cycle proof, missing metadata not broken refs.
    No actor hard references/load/cache refresh/mutation/save; native coverage unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/actor/references/graph", json={
        "PartitionPath": partition_path, "ContainerPath": container_path, "ActorGuid": actor_guid,
        "bEditorOnlyReferences": editor_only, "MaxDepth": max_depth, "Count": node_limit
    }, timeout=180).text


@mcp.tool()
def inspect_partition_editor_region(partition_path: str, adapter_path: str) -> str:
    """Inspect exact registered partition-owned loader wrapper/world/hold/optional label-color-bounds/count.
    Supplies guarded load/unload/release inputs without offset ambiguity; actor-owned loaders separate.
    No create/release/load/unload/mutation/save; native getters/lifetime unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/detail", json={
        "PartitionPath": partition_path, "AdapterPath": adapter_path
    }, timeout=180).text


@mcp.tool()
def replace_unloaded_partition_editor_region(partition_path: str, adapter_path: str, expected_count: int,
                                              expected_label: str, expected_center: list[float],
                                              expected_extent: list[float], label: str,
                                              center: list[float], extent: list[float],
                                              confirm: bool = False, dry_run: bool = False) -> str:
    """Replace unloaded user-created region with native box shape, new identity before old release.
    Exact old bounds/label/count guards/request bounds; new unloaded adapter readback first.
    No Load/Unload/transaction/save; partial failure may leave both adapters, inspect registry.
    Custom geometry becomes box; session lifetime/persistence unverified.
    """
    if any(len(v) != 3 for v in (expected_center, expected_extent, center, extent)):
        raise ValueError("All box vectors require exactly3 XYZ coordinates")
    return httpx.post(f"{app.BASE_URL}/worlds/partition/regions/replace-unloaded", json={
        "PartitionPath": partition_path, "AdapterPath": adapter_path, "ExpectedRegistryCount": expected_count,
        "ExpectedName": expected_label, "ExpectedCenter": dict(zip(("X", "Y", "Z"), expected_center)),
        "ExpectedExtent": dict(zip(("X", "Y", "Z"), expected_extent)), "Label": label,
        "Center": dict(zip(("X", "Y", "Z"), center)), "Extent": dict(zip(("X", "Y", "Z"), extent)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_grid_eligibility(partition_path: str, grid_name: str, actor_class_path: str) -> str:
    """Native current hash IsValidGrid for supplied token/loaded actor class plus default grid.
    HashSet includes native parsed tokens/main-selected definition resolution; empty means None/default.
    Eligibility not actor-specific editability/Data Layer compatibility/generated readiness proof.
    No class load/CDO construction/assignment/activation/save; custom native callbacks unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-grids/eligibility", json={
        "PartitionPath": partition_path, "Name": grid_name, "ClassPath": actor_class_path
    }, timeout=180).text


@mcp.tool()
def inspect_partition_runtime_hlod_eligibility(partition_path: str, grid_name: str, layer_path: str) -> str:
    """Native hash HLOD eligibility for loaded layer/grid plus explicit HashSet setup matches128/count.
    Native first-match/main-token semantics retained; base/custom hashes may lack eligibility support.
    Not full parent/material/build/default inheritance proof; no load/assignment/activation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/runtime-grids/hlod-eligibility", json={
        "PartitionPath": partition_path, "Name": grid_name, "AssetPath": layer_path
    }, timeout=180).text


@mcp.tool()
def inspect_world_partition_hlod_linked_chain(layer_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect loaded hard linked-HLOD chain bounded128 distinct nodes, paginated rows1..128.
    Reports cycles/invalid targets/traversal limit separately from page continuation, includes inactive links.
    Parent graph not traversed/combined; no asset load/generation/build/mutation/save; semantics unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/linked/inspect", json={
        "AssetPath": layer_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_world_partition_hlod_layer_referencers(layer_path: str, start: int = 0, count: int = 64) -> str:
    """Page loaded HLOD assets referencing target as parent/linked layer1..128, including inactive links.
    Excludes unloaded refs/actors/world defaults/runtime setups/transitive deps; not deletion safety proof.
    No package load/graph validation/generation/mutation/save; native coverage unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/hlod-layers/referencers/inspect", json={
        "AssetPath": layer_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_partition_data_layer_hierarchy(partition_path: str, layer_path: str,
                                            max_depth: int = 4, node_limit: int = 64) -> str:
    """Inspect registered layer ancestors<=128 and descendants<=128/depth16 with cycle/frontier flags.
    Reports local visibility/loading/authored runtime states; avoids potentially cyclic native effective getters.
    No actor load/reparent/streaming refresh/mutation/save; registry-only coverage unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/hierarchy/inspect", json={
        "PartitionPath": partition_path, "ObjectPath": layer_path, "MaxDepth": max_depth, "Count": node_limit
    }, timeout=180).text


def inspect_partition_private_data_layer_asset(partition_path: str, instance_path: str,
                                               asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect an already-loaded private embedded asset of a registered current-world Data Layer.
    Exact partition/owner/asset identities required; returns type/filter/color and loaded consumers.
    No load, mutation, streaming refresh or save; does not enable standalone asset setters.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layer-assets/inspect", json={
        "PartitionPath": partition_path, "ObjectPath": instance_path, "AssetPath": asset_path,
        "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_private_data_layer_asset_debug_color(partition_path: str, instance_path: str,
                                             asset_path: str, expected_type: int,
                                             expected_color_bytes: list[int], color_bytes: list[int],
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Set private embedded editor Data Layer debug RGBA bytes0..255 with full identity/color guards.
    Writable registered owner and confirmation required; owner/asset transaction, no save.
    Exact black can be replaced by native PostLoad; compilation/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/private-asset/debug-color", json={
        "PartitionPath": partition_path, "ObjectPath": instance_path, "AssetPath": asset_path,
        "ExpectedLayerType": expected_type, "ExpectedColorBytes": expected_color_bytes,
        "ColorBytes": color_bytes, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_private_data_layer_asset_actor_filters(partition_path: str, instance_path: str,
                                               asset_path: str, expected_type: int,
                                               expected_value: bool, value: bool,
                                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set private embedded Data Layer asset actor-filter support with exact owner/type/value guards.
    Owner/asset transaction and native events; no instance flag migration/filter rebuild/save.
    Requires current registered writable private editor layer; native behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/partition/data-layers/private-asset/actor-filters", json={
        "PartitionPath": partition_path, "ObjectPath": instance_path, "AssetPath": asset_path,
        "ExpectedLayerType": expected_type, "bExpectedValue": expected_value,
        "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_legacy_hlod_levels(world_path: str, start: int = 0, count: int = 64) -> str:
    """Read authored local legacy HLOD setup levels/common clustering settings, pages1..128.
    Does not resolve setup soft class/project override, create CDOs or load packages.
    Local data may be inactive under overrides/partition; no cluster generation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/inspect", json={
        "WorldPath": world_path, "Start": start, "Count": count
    }, timeout=180).text


def set_world_legacy_hlod_numeric(world_path: str, level_index: int, expected_level_count: int,
                                   field_name: str, expected_value: float, value: float,
                                   confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit local legacy HLOD TransitionScreenSize/OverrideDrawDistance/DesiredBoundRadius/
    DesiredFillingPercentage/MinNumberOfActorsToBuild. Rejects setup overrides/partition maps.
    Exact index/count/value guards, native indexed events/transaction; no generation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/numeric", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_world_legacy_hlod_boolean(world_path: str, level_index: int, expected_level_count: int,
                                   field_name: str, expected_value: bool, value: bool,
                                   confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit local HLOD bUseOverrideDrawDistance/bAllowSpecificExclusion/
    bOnlyGenerateClustersForVolumes/bReusePreviousLevelClusters with exact index/count/value guards.
    Rejects partition/setup overrides; native bitfield/events/transaction, no build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/boolean", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_name, "ExpectedValue": int(expected_value), "Value": int(value),
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_legacy_hlod_method(world_path: str, level_index: int, expected_level_count: int,
                                  expected_method: int, method: int,
                                  confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Set local HLOD method1 Merge/2 Simplify/3 Approximate with exact index/count/current guards.
    Preserves method-specific settings; backend availability not validated. Rejects partition/overrides.
    Native indexed events/transaction/readback; no generation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/method", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": "SimplificationMethod", "ExpectedValue": expected_method, "Value": method,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_legacy_hlod_fields(world_path: str, level_index: int, expected_level_count: int,
                                      struct_path: str = "", start: int = 0, count: int = 64) -> str:
    """Discover authored local HLOD nested structs<=8/page1..128, metadata and simple native text.
    Paths include MergeSetting, ProxySetting, ApproximateSettings; inactive values included.
    No object traversal/override loading/default construction/generation/mutation/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/fields", json={
        "WorldPath": world_path, "LevelIndex": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": struct_path, "Start": start, "Count": count
    }, timeout=180).text


def set_world_legacy_hlod_nested_numeric(world_path: str, level_index: int, expected_level_count: int,
                                          field_path: str, expected_value: float, value: float,
                                          confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected MergeSetting/ProxySetting/ApproximateSettings nested float/double/int32.
    Editable plain struct path<=8, native clamps/value+/-1e9; exact local count/index/current guards.
    UI conditions/backend availability not evaluated; native chain transaction, no build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-numeric", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedValue": expected_value, "Value": value,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_world_legacy_hlod_nested_boolean(world_path: str, level_index: int, expected_level_count: int,
                                          field_path: str, expected_value: bool, value: bool,
                                          confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested MergeSetting/ProxySetting/ApproximateSettings boolean/bitfield.
    Editable plain struct path<=8, exact local count/index/current value and setup override guards.
    UI conditions/backend availability not evaluated; native chain transaction, no build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-boolean", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedValue": int(expected_value), "Value": int(value),
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_world_legacy_hlod_nested_enum(world_path: str, level_index: int, expected_level_count: int,
                                       field_path: str, expected_value: int, value: int,
                                       confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested HLOD mesh enum using native integer values/options.
    Visible non-sentinel targets only, exact local count/index/current value/setup override guards.
    Native enum/byte storage and full indexed chain transaction; no backend validation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-enum", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedValue": expected_value, "Value": value,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_legacy_hlod_nested_object(world_path: str, level_index: int, expected_level_count: int,
                                         field_path: str, expected_object_path: str, object_path: str,
                                         confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested HLOD hard asset reference, loaded compatible assets or permitted clear.
    Empty current/target path means null; excludes classes, instanced objects and soft refs.
    Exact local index/count/current reference/override guards, native chain transaction; no load/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-object", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedObjectPath": expected_object_path, "ObjectPath": object_path,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_world_legacy_hlod_nested_name(world_path: str, level_index: int, expected_level_count: int,
                                       field_path: str, expected_name: str, name: str,
                                       confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested HLOD FName with native bounds/control-character checks.
    Empty maps to None; case-only differences are native FName no-ops. Exact local guards,
    indexed chain transaction/readback, no object rename, build or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-name", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedName": expected_name, "Name": name,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_world_legacy_hlod_nested_string(world_path: str, level_index: int, expected_level_count: int,
                                         field_path: str, expected_text: str, text: str,
                                         confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested HLOD FString<=4096, exact current text/index/count/override guards.
    Empty clears; no file import or command execution. Native indexed chain transaction/readback,
    no backend validation, generation/build or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-string", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedName": expected_text, "Name": text,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_world_legacy_hlod_level(world_path: str, expected_level_count: int,
                                 confirm: bool = False, dry_run: bool = True, expected_level_texts: list[str] | None = None) -> str:
    """Append native-default local legacy HLOD level, exact count<128/no override/ordinary map guards.
    Native array construction/chain transaction, prior settings readback; inspect new defaults afterward.
    No cluster generation, mesh build or save; dry-run does not construct level.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/add", json={
        "WorldPath": world_path, "ExpectedLODCount": expected_level_count,
        "ExpectedLevelTexts": expected_level_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def duplicate_world_legacy_hlod_level(world_path: str, source_level_index: int,
                                       expected_level_count: int, confirm: bool = False,
                                       dry_run: bool = True, expected_level_texts: list[str] | None = None) -> str:
    """Append full reflected copy of existing local legacy HLOD level, preserving prior levels.
    Exact ordinary map/count/source/override guards, native chain transaction/readback.
    Copies reference values, not referenced assets; no cluster generation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/duplicate", json={
        "WorldPath": world_path, "LevelIndex": source_level_index, "ExpectedLODCount": expected_level_count,
        "ExpectedLevelTexts": expected_level_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_world_legacy_hlod_level(world_path: str, level_index: int, expected_level_count: int,
                                    confirm: bool = False, dry_run: bool = True, expected_level_texts: list[str] | None = None) -> str:
    """Remove local legacy HLOD setup level with count/index/ordinary-map/override guards.
    Rejects loaded generated LOD actors at/above removed tier; unloaded references not discovered.
    Preserves surviving settings, no generated asset/actor cleanup or exclusion-flag migration.
    Native chain transaction/readback, empty allowed; no build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/remove", json={
        "WorldPath": world_path, "LevelIndex": level_index, "ExpectedLODCount": expected_level_count,
        "ExpectedLevelTexts": expected_level_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_world_legacy_hlod_levels(world_path: str, expected_level_count: int,
                                      source_index_order: list[int], confirm: bool = False,
                                      dry_run: bool = True, expected_level_texts: list[str] | None = None) -> str:
    """Reorder local HLOD levels using complete unique source-index permutation<=128.
    Rejects loaded LOD actors on changed tiers; unloaded refs/exclusion flags not migrated.
    Preserves settings, reuse-previous semantics change with order; native transaction/no build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/reorder", json={
        "WorldPath": world_path, "ExpectedLODCount": expected_level_count,
        "LevelOrder": source_index_order, "ExpectedLevelTexts": expected_level_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_legacy_hlod_setup_override(world_path: str, expected_class_path: str,
                                          class_path: str, confirm: bool = False,
                                          dry_run: bool = True) -> str:
    """Assign loaded concrete legacy HLOD setup class override or empty clear, preserving local setup.
    Rejects changed override with loaded generated LOD actors; unloaded refs not discovered.
    Native transaction/events/readback; callbacks may load indirectly, no explicit CDO/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-setup-override", json={
        "WorldPath": world_path, "ExpectedObjectPath": expected_class_path, "ObjectPath": class_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_legacy_hlod_setup_classes(world_path: str, start: int = 0, count: int = 64) -> str:
    """Discover loaded HLOD setup subclasses/selectability flags, sorted pages1..128.
    No unloaded Blueprint scan, package load, CDO creation or backend validity evaluation.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-setup-classes/inspect", json={
        "WorldPath": world_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_world_legacy_hlod_material_override(world_path: str, expected_material_path: str,
                                             material_path: str, confirm: bool = False,
                                             dry_run: bool = True) -> str:
    """Set ordinary-map legacy HLOD base-material override, loaded compatible material or empty clear.
    Native flatten-parameter preflight without popup; rejects map setup override/loaded generated LOD actors.
    Native transaction/events/readback; no material compile, cluster build or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-material-override", json={
        "WorldPath": world_path, "ExpectedObjectPath": expected_material_path, "ObjectPath": material_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_legacy_hlod_nested_int_point(world_path: str, level_index: int, expected_level_count: int,
                                            field_path: str, expected_xy: list[int], xy: list[int],
                                            confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested HLOD FIntPoint as complete XY pair0..1000000/native clamps.
    Exact current pair/index/count/override guards; no texture allocation/backend suitability proof.
    Native indexed chain transaction/readback; no generation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-int-point", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedPairValues": expected_xy, "PairValues": xy,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_world_legacy_hlod_nested_color(world_path: str, level_index: int, expected_level_count: int,
                                        field_path: str, expected_rgba: list[float], rgba: list[float],
                                        confirm: bool = False, dry_run: bool = True, expected_level_text: str = "") -> str:
    """Edit inspected nested HLOD FLinearColor with complete linear RGBA0..1/native clamps.
    Full current color/index/count/override guards, native indexed chain transaction/readback.
    No material compile, texture allocation, generation/build or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/nested-color", json={
        "WorldPath": world_path, "Start": level_index, "ExpectedLODCount": expected_level_count,
        "FieldName": field_path, "ExpectedColorValues": expected_rgba, "ColorValues": rgba,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reset_world_legacy_hlod_level(world_path: str, level_index: int, expected_level_count: int,
                                   expected_level_text: str, confirm: bool = False,
                                   dry_run: bool = True) -> str:
    """Reset entire local HLOD level to native constructor defaults, full snapshot required.
    Replaces nested settings/reference values, retains assets; rejects loaded generated actors on tier.
    Native defaults constructed even dry-run; transaction/full array readback, no build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-levels/reset", json={
        "WorldPath": world_path, "LevelIndex": level_index, "ExpectedLODCount": expected_level_count,
        "ExpectedLevelText": expected_level_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_hlod_cluster_volume(actor_path: str) -> str:
    """Inspect manual HLOD volume overlap policy/zero-based tier filter, empty=all.
    No inclusion queries, cluster generation, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/hlod/inspect", json={"ActorPath": actor_path}, timeout=180).text


@mcp.tool()
def set_hlod_cluster_volume_policy(actor_path: str, actor_guid: str, expected_label: str,
                                    expected_overlap: bool, overlap: bool,
                                    expected_levels: list[int], levels: list[int],
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Set manual HLOD volume overlap/full tier filter with exact current guards.
    Unique zero-based indices0..127, empty applies all; effective setup existence not validated.
    Native transaction/events/readback, no brush edit, inclusion query, cluster build or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/hlod/policy", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "bExpectedBoolValue": expected_overlap, "bBoolValue": overlap,
        "ExpectedHLODLevels": expected_levels, "HLODLevels": levels,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
set_partition_data_layer_initial = merged_tool("set_partition_data_layer_initial", {
    "set_partition_data_layer_initial_runtime_state": set_partition_data_layer_initial_runtime_state,
    "set_partition_data_layer_initial_visibility": set_partition_data_layer_initial_visibility,
})
inspect_data_layer_asset_info = merged_tool("inspect_data_layer_asset_info", {
    "inspect_data_layer_asset": inspect_data_layer_asset,
    "inspect_partition_private_data_layer_asset": inspect_partition_private_data_layer_asset,
})
set_partition_spatial_hash_grid_appearance = merged_tool("set_partition_spatial_hash_grid_appearance", {
    "set_partition_spatial_hash_grid_blocking": set_partition_spatial_hash_grid_blocking,
    "set_partition_spatial_hash_grid_origin": set_partition_spatial_hash_grid_origin,
    "set_partition_spatial_hash_grid_debug_color": set_partition_spatial_hash_grid_debug_color,
})
set_partition_spatial_hash_settings = merged_tool("set_partition_spatial_hash_settings", {
    "set_partition_spatial_hash_override": set_partition_spatial_hash_override,
    "set_partition_spatial_hash_z_culling": set_partition_spatial_hash_z_culling,
})
set_partition_streaming_source_setting = merged_tool("set_partition_streaming_source_setting", {
    "set_partition_streaming_source_enabled": set_partition_streaming_source_enabled,
    "set_partition_streaming_source_enum": set_partition_streaming_source_enum,
})
set_partition_streaming_source_visualization = merged_tool("set_partition_streaming_source_visualization", {
    "set_partition_streaming_source_debug_color": set_partition_streaming_source_debug_color,
    "set_partition_streaming_source_visualizer_range": set_partition_streaming_source_visualizer_range,
})
set_hlod_builder = merged_tool("set_hlod_builder", {
    "numeric": set_hlod_builder_numeric,
    "bool": set_hlod_builder_bool,
    "enum": set_hlod_builder_enum,
    "string": set_hlod_builder_string,
    "name": set_hlod_builder_name,
    "int64": set_hlod_builder_int64,
})
set_partition_runtime_definition = merged_tool("set_partition_runtime_definition", {
    "numeric": set_partition_runtime_definition_numeric,
    "bool": set_partition_runtime_definition_bool,
})
set_world_legacy_hlod = merged_tool("set_world_legacy_hlod", {
    "numeric": set_world_legacy_hlod_numeric,
    "boolean": set_world_legacy_hlod_boolean,
})
set_world_legacy_hlod_nested = merged_tool("set_world_legacy_hlod_nested", {
    "numeric": set_world_legacy_hlod_nested_numeric,
    "boolean": set_world_legacy_hlod_nested_boolean,
    "enum": set_world_legacy_hlod_nested_enum,
    "name": set_world_legacy_hlod_nested_name,
    "string": set_world_legacy_hlod_nested_string,
    "color": set_world_legacy_hlod_nested_color,
})
