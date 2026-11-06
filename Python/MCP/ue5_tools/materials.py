"""Materials, instances and parameter collections."""
import httpx

from . import app
from .app import mcp, _asset_request


@mcp.tool()
def set_material_parameter(asset_path: str, parameter_name: str,
                           parameter_type: str, value: str) -> str:
    """Set a scalar, vector, or texture parameter on a Material Instance Constant.

    Vector values use R=,G=,B=,A= syntax. Texture values use a UE asset path.
    """
    response = httpx.patch(f"{app.BASE_URL}/materials/parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterType": parameter_type, "Value": value
    })
    return response.text


@mcp.tool()
def set_static_mesh_material(asset_path: str, slot_index: int, material_path: str) -> str:
    """Assign a material to a static mesh material slot."""
    response = httpx.patch(f"{app.BASE_URL}/static-meshes/materials", json={
        "AssetPath": asset_path, "SlotIndex": slot_index, "MaterialPath": material_path
    })
    return response.text


@mcp.tool()
def set_skeletal_mesh_material(asset_path: str, slot_index: int, material_path: str) -> str:
    """Assign a material to a skeletal mesh material slot."""
    response = httpx.patch(f"{app.BASE_URL}/skeletal-meshes/materials", json={
        "AssetPath": asset_path, "SlotIndex": slot_index, "MaterialPath": material_path
    })
    return response.text


@mcp.tool()
def list_material_expressions(asset_path: str) -> str:
    """List parent Material expression nodes and their editor positions."""
    response = httpx.get(f"{app.BASE_URL}/materials/expressions", params={"asset_path": asset_path})
    return response.text


@mcp.tool()
def create_material_expression(asset_path: str, expression_class: str,
                               expression_name: str = "", node_pos_x: int = 0,
                               node_pos_y: int = 0) -> str:
    """Create a Material expression node, using a class path such as /Script/Engine.MaterialExpressionScalarParameter."""
    response = httpx.post(f"{app.BASE_URL}/materials/expressions", json={
        "AssetPath": asset_path, "ExpressionClass": expression_class,
        "ExpressionName": expression_name,
        "NodePosX": node_pos_x, "NodePosY": node_pos_y
    })
    return response.text


@mcp.tool()
def connect_material_expressions(asset_path: str, from_expression: str,
                                 to_expression: str, from_output: str = "",
                                 to_input: str = "") -> str:
    """Connect two Material expression nodes by their UObject names."""
    response = httpx.post(f"{app.BASE_URL}/materials/expressions/connect", json={
        "AssetPath": asset_path, "FromExpression": from_expression,
        "ToExpression": to_expression, "FromOutput": from_output,
        "ToInput": to_input
    })
    return response.text


@mcp.tool()
def delete_material_expression(asset_path: str, expression_name: str) -> str:
    """Delete a Material expression node by UObject name."""
    response = httpx.request("DELETE", f"{app.BASE_URL}/materials/expressions", json={
        "AssetPath": asset_path, "ExpressionName": expression_name
    })
    return response.text


@mcp.tool()
def layout_material_expressions(asset_path: str) -> str:
    """Automatically arrange parent Material expression nodes."""
    response = httpx.post(f"{app.BASE_URL}/materials/layout", json={"AssetPath": asset_path})
    return response.text


@mcp.tool()
def inspect_material_asset(asset_path: str) -> str:
    """Inspect a parent Material or Material Instance."""
    return httpx.get(f"{app.BASE_URL}/materials/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def summarize_material(asset_path: str) -> str:
    """Read a parent Material's domain, blend mode, shading models, two-sided state, and usage flags."""
    return httpx.get(f"{app.BASE_URL}/materials/summary", params={"asset_path": asset_path}).text


@mcp.tool()
def list_material_parameters(asset_path: str) -> str:
    """List parent Material parameters with types, groups, descriptions, and defaults."""
    return httpx.get(f"{app.BASE_URL}/materials/parameters", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_material_core_settings(asset_path: str, domain: str = "", blend_mode: str = "",
                                shading_model: str = "", two_sided: bool | None = None,
                                usage_flags: dict[str, bool] | None = None,
                                dry_run: bool = False, save: bool = False) -> str:
    """Edit Material domain, blend mode, shading model, two-sided state, and usage flags.

    Enum values use UE names such as MD_Surface, BLEND_Masked, and MSM_Unlit.
    """
    return httpx.patch(f"{app.BASE_URL}/materials/core-settings", json={
        "AssetPath": asset_path, "Domain": domain, "BlendMode": blend_mode,
        "ShadingModel": shading_model, "bSetTwoSided": two_sided is not None,
        "bTwoSided": two_sided if two_sided is not None else False,
        "UsageFlags": usage_flags or {}, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def edit_material_settings(asset_path: str, properties: dict, save: bool = False) -> str:
    """Edit reflected parent Material settings."""
    return _asset_request("materials/settings", asset_path, properties, save=save)


@mcp.tool()
def validate_material(asset_path: str) -> str:
    """Report Material shader compilation status and available compile errors."""
    return httpx.post(f"{app.BASE_URL}/materials/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def edit_material_instance_settings(asset_path: str, properties: dict, save: bool = False) -> str:
    """Edit reflected Material Instance Constant settings."""
    return _asset_request("material-instances/settings", asset_path, properties, save=save)


@mcp.tool()
def list_material_instance_parameters(asset_path: str) -> str:
    """List effective Material Instance parameters, groups, values, and override flags."""
    return httpx.get(f"{app.BASE_URL}/material-instances/parameters", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_material_instance_parameter(asset_path: str, parameter_name: str,
                                     parameter_type: str, value: str,
                                     association: str = "global", index: int = -1,
                                     font_page: int = 0, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Set an existing scalar, vector, texture, static switch, runtime VT, or font override.

    Vector values use R=,G=,B=,A= syntax. Texture values use a UE asset path.
    Use association and index for layer or blend parameters.
    """
    return httpx.patch(f"{app.BASE_URL}/material-instances/parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ParameterType": parameter_type, "Value": value,
        "Association": association, "Index": index, "FontPage": font_page,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def set_material_instance_parent(asset_path: str, parent_path: str,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Assign a Material or Material Instance as parent; rejects inheritance cycles."""
    return httpx.patch(f"{app.BASE_URL}/material-instances/parent", json={
        "AssetPath": asset_path, "ParentPath": parent_path,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def reset_material_instance_parameters(asset_path: str,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Clear every local parameter override on a Material Instance Constant."""
    return httpx.post(f"{app.BASE_URL}/material-instances/reset", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def validate_material_instance(asset_path: str) -> str:
    """Report missing parent and local overrides absent from the parent parameter set."""
    return httpx.post(f"{app.BASE_URL}/material-instances/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def audit_static_mesh_component_nanite_materials(actor_path: str, component_path: str, asset_path: str) -> str:
    """Run native Nanite material audit including current component overrides.
    Exact current editor actor/component/asset, noncompiling mesh, <=64 slots.
    Material usage updates disabled; returns native errors/features/fallback and
    masked-allowed/disallowed policy validity. No platform/GPU/render-quality proof,
    asset build/save or simulation requested. Native inspection work uncapped.
    """
    return httpx.post(f"{app.BASE_URL}/static-mesh/nanite/component-audit", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path
    }, timeout=60).text


@mcp.tool()
def set_volumetric_cloud_material(actor_path: str, component_path: str,
                                  expected_material_path: str, expected_resolved_material_path: str,
                                  material_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded persistent Volume-domain cloud material or empty clear.
    Exact inspected authored soft-path and resolved lifetime-path guards, no explicit asset load.
    Native setter/notification may resolve reference/reregister/precache PSOs; shader readiness unproven.
    Transaction/readback/no-op/dry-run/no build/save; callbacks/undo of both references unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/material", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedMaterialPath": expected_material_path,
        "ExpectedResolvedMaterialPath": expected_resolved_material_path,
        "MaterialPath": material_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_decal_material(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                         expected_material_path: str, material_path: str,
                         confirm: bool = False, dry_run: bool = True) -> str:
    """Assign loaded persistent DeferredDecal-domain material interface or empty clear.
    Exact prior reference/GUID/label guard; preserves render/fade/size/color/transform/visibility/mobility.
    Native setter can precache PSOs/update render resources; domain is not output readiness proof.
    No material asset edits/dynamic instance creation/explicit load/render evaluation/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/material", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedMaterialPath": expected_material_path,
        "MaterialPath": material_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_decal_material_users(material_path: str, start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded current-world decals directly referencing exact material object path, empty selects unassigned.
    Optional exact owner; excludes unloaded worlds/components and indirect material dependencies.
    No asset loading/traversal/render evaluation/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/material-users/inspect-page", json={
        "MaterialPath": material_path, "ActorPath": actor_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_loaded_decal_materials(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Discover loaded persistent material interfaces with native DeferredDecal base domain, pages1..128.
    Path substring/path-sorted; no complete unloaded asset inventory/inheritance/shader/output proof.
    No explicit asset load/material edits/shader compile/render evaluation/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/materials/inspect-page", json={
        "Name": path_substring, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_texture_material_overrides(asset_path: str, material_path_substring: str = "",
                                        start: int = 0, count: int = 64) -> str:
    """Page loaded persistent material-instance direct authored texture overrides1..128, unverified.

    Includes native parameter association/layer index/GUID. Not effective shader usage/inherited consumers;
    excludes base-material defaults, dynamic instances, UI brushes, collections and unloaded refs.
    No material evaluation/compile/texture load/build waits/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/textures/material-overrides/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": material_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_material_data(asset_path: str, expected_class_path: str, expected_asset_snapshot: str,
                                               expected_float4: list[float], float4: list[float],
                                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set RVT CustomMaterialData native float4+-65504, full prior values/snapshot required, unverified.

    Arbitrary material data, no color conversion. Reports float quantization; native notifications may
    recreate resources, not proof materials consume channels/pages refresh. No graph edits/build/save.
    """
    if len(expected_float4) != 4 or len(float4) != 4:
        raise ValueError("expected_float4 and float4 must each contain four numbers")
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/material-data", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bRequireAssetSnapshot": True,
        "ExpectedColor": expected_float4, "Color": float4, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_material_parameter_groups(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect loaded native material editor-only authored group priorities/page1..128/full group snapshot.
    Not effective parameter membership/inheritance. No compile/load/save/mutation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/parameter-groups/inspect-page", json={
        "AssetPath": asset_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_material_parameter_group_priority(asset_path: str, group_index: int, group_name: str,
                                          priority: int, expected_priority: int,
                                          expected_class_path: str, expected_group_snapshot: str,
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Edit existing unique native material authored group priority+-1000000 with full group snapshot.
    Exact index/name/prior value/class; transaction/material editor data/full sibling readback.
    Metadata only, no shader notification/compile/save; editor panels may need refresh. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/parameter-groups/priority", json={
        "AssetPath": asset_path, "Start": group_index, "Name": group_name,
        "Value": priority, "ExpectedValue": expected_priority, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_group_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def edit_material_parameter_group_entry(asset_path: str, operation: str, group_name: str,
                                        expected_class_path: str, expected_group_snapshot: str,
                                        priority: int = 0, group_index: int = 0,
                                        expected_priority: int = 0, confirm: bool = False,
                                        dry_run: bool = True) -> str:
    """Add/Remove native material authored group-order metadata; no expression group reassignment.
    Add unique name/priority+-1000000, Remove exact unique index/name/prior priority, full snapshot/class.
    Transactions/editor data/full array readback; native refresh may recreate removed entries.
    No parameter deletion/shader notification/compile/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/parameter-groups/entry", json={
        "AssetPath": asset_path, "FieldName": operation, "Name": group_name,
        "Value": priority, "Start": group_index, "ExpectedValue": expected_priority,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_group_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_material_expression_metadata(asset_path: str, expression_path: str, node_guid: str) -> str:
    """Inspect material/function expression Group/SortPriority/Desc/ControlType/EnumerationIndex/editability/full snapshot.
    Exact current collection/node GUID; native field availability differs by type. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/metadata/inspect", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid}, timeout=180).text


@mcp.tool()
def set_material_expression_metadata(asset_path: str, expression_path: str, node_guid: str,
                                     field_name: str, expected_class_path: str, expected_metadata_snapshot: str,
                                     text: str = "", expected_text: str = "", value: int = 0,
                                     expected_value: int = 0, confirm: bool = False, dry_run: bool = True) -> str:
    """Edit material/function Group/Desc text, SortPriority+-1000000, or scalar ControlType enum.
    ControlType choices from inspect; also scalar EnumerationIndex byte0..255 when that control is active.
    Exact prior numeric value/full snapshot; no instance enumeration-array readiness proof.
    Group FName semantics, no parameter rename/value/GUID edit. Native callbacks may compile/cache groups.
    Transaction/readback/dry-run; no explicit shader wait/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/metadata/set", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": field_name, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_metadata_snapshot, "OutputName": text,
        "ExpectedOutputName": expected_text, "Value": value, "ExpectedValue": expected_value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def discover_material_expression_metadata(asset_path: str, path_filter: str = "", group_name: str = "",
                                           start: int = 0, count: int = 64) -> str:
    """Discover native material/function-owned expression metadata/path/GUID/class/snapshots/pages1..128.
    Optional path substring/exact native FName group; includes unconnected/nonparameter expressions.
    No function expansion/effective inherited parameter proof/compile/save/mutation. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/metadata/discover", json={
        "AssetPath": asset_path, "PathFilter": path_filter, "Name": group_name,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def material_scalar_slider_range(asset_path: str, expression_path: str, node_guid: str,
                                  operation: str = "Inspect", bounds: list[float] = [],
                                  expected_bounds: list[float] = [], expected_class_path: str = "",
                                  expected_metadata_snapshot: str = "", confirm: bool = False,
                                  dry_run: bool = True) -> str:
    """Inspect/Set native material/function scalar parameter paired slider min/max UI metadata.
    Set requires two finite bounds+/-65504/exact prior floats/class/full snapshot/node GUID/editability.
    Max<=Min disables native bounds; default value unchanged/unclamped. Callbacks may compile. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/scalar-slider-range", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "Color": bounds, "ExpectedColor": expected_bounds,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_scalar_enumeration_reference(asset_path: str, expression_path: str, node_guid: str,
                                          operation: str = "Inspect", enumeration_path: str = "",
                                          expected_reference_path: str = "", expected_class_path: str = "",
                                          expected_metadata_snapshot: str = "", confirm: bool = False,
                                          dry_run: bool = True) -> str:
    """Inspect/Set scalar parameter soft Enumeration reference for material/function owners.
    Set loaded UEnum/material enumeration provider or empty clear, existing Enumeration control,
    exact prior soft path/class/node GUID/full snapshot. Inspect does not load/evaluate provider.
    Native callbacks may compile; transactions/dry-run/no explicit load/save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/scalar-enumeration", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "SourceTexturePath": enumeration_path,
        "ExpectedTargetPath": expected_reference_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_metadata_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_instance_enumeration_slots(asset_path: str, operation: str = "Inspect", start: int = 0,
                                        count: int = 64, enumeration_path: str = "",
                                        expected_exists: bool = False, expected_reference_path: str = "",
                                        expected_class_path: str = "", expected_enumeration_snapshot: str = "",
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect paged native instance enumeration slots/effective parent fallback, or Set start slot0..255.
    Set existing or append next, loaded enum/provider or empty clear; no index-shifting removal.
    Exact local array snapshot/class/prior existence/path, transactions/callbacks/readback/dry-run.
    Null falls back to parent; effective lookup guards cycles/depth64, no soft loading/provider eval.
    Native callbacks may compile; no explicit save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/material-instances/enumeration-slots", json={
        "AssetPath": asset_path, "FieldName": operation, "Start": start, "Count": count,
        "SourceTexturePath": enumeration_path, "bExpectedEnabled": expected_exists,
        "ExpectedTargetPath": expected_reference_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_enumeration_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_material_enumeration_entries(object_path: str, expected_class_path: str,
                                         start: int = 0, count: int = 64, confirm: bool = False) -> str:
    """Observe native loaded UEnum/material enumeration provider entries/pages1..128/first4096 retained.
    Explicit confirmation: provider ForEachEntry executes native virtual code and may have custom side effects;
    entire callback iteration is unbounded despite retained cap. Enum hidden/sentinel entries retained.
    Native order/duplicate entries preserved, int64 values decimal strings. No load/compile/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/enumerations/entries", json={
        "SourceTexturePath": object_path, "ExpectedClassPath": expected_class_path,
        "Start": start, "Count": count, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def resolve_material_enumeration_value(object_path: str, expected_class_path: str,
                                       entry_name: str, fallback: int = 0, confirm: bool = False) -> str:
    """Resolve loaded enum/provider name with int32 fallback and separate found/result decimal strings.
    Explicit native provider callback confirmation; custom side effects/unbounded execution possible.
    Native name/case/scoped semantics, enum hidden/sentinel values not filtered. Provider miss result
    retained independently. No scalar assignment/load/compile/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/enumerations/resolve-value", json={
        "SourceTexturePath": object_path, "ExpectedClassPath": expected_class_path,
        "Name": entry_name, "Value": fallback, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def material_parameter_primitive_data_binding(asset_path: str, expression_path: str, node_guid: str,
                                              operation: str = "Inspect", enabled: bool = False,
                                              float_index: int = 0, expected_enabled: bool = False,
                                              expected_index: int = 0, expected_class_path: str = "",
                                              expected_metadata_snapshot: str = "", confirm: bool = False,
                                              dry_run: bool = True) -> str:
    """Inspect/Set native scalar/vector custom primitive-data enable/index (1/4 consecutive floats).
    Native capacity guard/full snapshot/class/node GUID/prior flag-index/native editability.
    No scene primitive data write/slot allocation/overlap prevention/default conversion; callbacks may compile.
    Transaction/paired notification/readback/dry-run/no explicit save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/primitive-data-binding", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "bEnabled": enabled, "Start": float_index,
        "bExpectedEnabled": expected_enabled, "ExpectedValue": expected_index,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_vector_channel_labels(asset_path: str, expression_path: str, node_guid: str,
                                    operation: str = "Inspect", labels_rgba: list[str] = [],
                                    expected_labels_rgba: list[str] = [], expected_class_path: str = "",
                                    expected_metadata_snapshot: str = "", confirm: bool = False,
                                    dry_run: bool = True) -> str:
    """Inspect/Set native vector parameter four RGBA channel labels for material/function owners.
    Exact prior4 displayed labels/class/node GUID/full snapshot/editability, strings<=256/no controls.
    New labels FText.FromString, no localization key authoring; identical display no-op preserves identities.
    One callback/default preservation/transaction/dry-run, may compile; no explicit save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/vector-channel-labels", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "SourcePaths": labels_rgba, "ExpectedSourcePaths": expected_labels_rgba,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_texture_channel_labels(asset_path: str, expression_path: str, node_guid: str,
                                     operation: str = "Inspect", labels_rgba: list[str] = [],
                                     expected_labels_rgba: list[str] = [], expected_class_path: str = "",
                                     expected_metadata_snapshot: str = "", confirm: bool = False,
                                     dry_run: bool = True) -> str:
    """Inspect/Set native engine texture-sample four RGBA channel labels in material/function.
    Includes native sample parameter subtypes, property editability/full snapshot/class/GUID/prior4 labels.
    Labels<=256/no controls, FText plain strings; same displayed strings no-op preserve identities.
    Transaction/callback/texture-sampler preservation/dry-run, may compile; no explicit save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/texture-channel-labels", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "SourcePaths": labels_rgba, "ExpectedSourcePaths": expected_labels_rgba,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_texture_sample_policy(asset_path: str, expression_path: str, node_guid: str,
                                    field_name: str = "Inspect", value: int = 0, expected_value: int = 0,
                                    expected_class_path: str = "", expected_metadata_snapshot: str = "",
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect native engine texture-sample policy or edit SamplerType/SamplerSource/MipValueMode/GatherMode enum
    or AutomaticViewMipBias bool0or1. ConstCoordinate0..7 requires unconnected coordinates;
    ConstMipValue level0..32/bias-32..32 requires corresponding mode/unconnected mip input.
    Enabled gather needs assigned nonvirtual2D/cube/no texture-object input.
    SynchronizeSamplerType invokes native assigned-texture policy,
    value must equal inspected expected sampler and no texture-object input connected.
    Full sample snapshot/native inputs/class/GUID/prior value guards.
    Assigned texture native authored-sampler diagnostic and input connectivity returned; texture-object input/
    instance override may differ. Native callbacks may reconstruct pins/compile; no automatic correction.
    No explicit load/shader wait/save; transactions/dry-run, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/texture-sample-policy", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": field_name, "Value": value, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def set_material_texture_sample_reference(asset_path: str, expression_path: str, node_guid: str,
                                           texture_path: str, expected_texture_path: str,
                                           expected_class_path: str, expected_metadata_snapshot: str,
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Assign loaded persistent texture or empty clear to native engine texture-sample/object default.
    Exact prior reference (None when null)/class/node GUID/full metadata snapshot;
    samples require no connected texture-object input, native Texture Object expressions also supported.
    Native parameter TextureIsValid subtype check where applicable; callbacks may synchronize sampler/compile.
    Plain samples lack subtype validator; clear may cause shader error. No instance override migration/save.
    Transaction/readback/dry-run; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/texture-reference", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "SourceTexturePath": texture_path, "ExpectedTargetPath": expected_texture_path,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_expression_parameter_default(asset_path: str, expression_path: str, node_guid: str,
                                          operation: str = "Inspect", value: float = 0,
                                          expected_value: float = 0, rgba: list[float] = [],
                                          expected_rgba: list[float] = [], expected_class_path: str = "",
                                          expected_metadata_snapshot: str = "", confirm: bool = False,
                                          dry_run: bool = True) -> str:
    """Inspect/Set exact native scalar or vector parameter default in material/function.
    Scalar value or full linear RGBA, finite+/-65504/exact prior native floats/class/GUID/full snapshot.
    No gamma conversion/slider clamp/instance override rewrite. Native callbacks may propagate defaults/compile.
    Transactions/readback/dry-run/no explicit load/shader wait/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/parameter-default", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "Value": value, "ExpectedValue": expected_value,
        "Color": rgba, "ExpectedColor": expected_rgba, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_metadata_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_static_parameter_default(asset_path: str, expression_path: str, node_guid: str,
                                       operation: str = "Inspect", boolean: bool = False,
                                       expected_boolean: bool = False, mask_rgba: list[int] = [],
                                       expected_mask_rgba: list[int] = [], expected_class_path: str = "",
                                       expected_metadata_snapshot: str = "", confirm: bool = False,
                                       dry_run: bool = True) -> str:
    """Inspect/Set native static bool/switch or component-mask parameter defaults in material/function.
    Exact prior bool/full4 mask bits0or1/class/nodeGUID/full snapshot/editability. All-zero mask allowed,
    may fail shader compile. No instance static override migration/DynamicBranch change. Callbacks may
    compile permutations; transactions/dry-run/no explicit load/shader wait/save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/static-parameter-default", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "bEnabled": boolean, "bExpectedEnabled": expected_boolean,
        "Channels": mask_rgba, "ExpectedChannels": expected_mask_rgba,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_font_sample_default(asset_path: str, expression_path: str, node_guid: str,
                                  operation: str = "Inspect", font_path: str = "", atlas_page: int = 0,
                                  expected_font_path: str = "None", expected_page: int = 0,
                                  expected_class_path: str = "", expected_metadata_snapshot: str = "",
                                  expected_font_snapshot: str = "", confirm: bool = False,
                                  dry_run: bool = True) -> str:
    """Inspect/Set native font-sample/parameter font+atlas page0..255 in material/function.
    Set loaded offline font/valid atlas/full font snapshot or empty clear/page0; exact prior font/page/
    expression snapshot/class/GUID. Font snapshot from inspect_material_font_atlas or existing assignment; no atlas build.
    Native callbacks may compile, no instance override migration/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/font-default", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "SourceTexturePath": font_path, "Start": atlas_page,
        "ExpectedTargetPath": expected_font_path, "ExpectedSizeX": expected_page,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "ExpectedDestinationSnapshot": expected_font_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_material_font_atlas(font_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect loaded font cache mode/atlas refs/source headers/pages1..128/destination font snapshot.
    Supplies font-default setter guard for fonts not currently assigned to an expression.
    No glyph rasterization/cache build/pixel decode/compile/load/save/mutation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/fonts/atlas-inspect-page", json={
        "AssetPath": font_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def material_collection_parameter_reference(asset_path: str, expression_path: str, node_guid: str,
                                             operation: str = "Inspect", collection_path: str = "",
                                             parameter_name: str = "", expected_collection_path: str = "None",
                                             expected_parameter_name: str = "None", expected_class_path: str = "",
                                             expected_metadata_snapshot: str = "", expected_collection_layout: str = "",
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Set native collection parameter expression collection/name/native parameter GUID.
    Inspect optional destination collection_path returns layout snapshot without assignment. Set unique
    scalar/vector parameter/exact destination layout/prior ref-name/class/nodeGUID/full expression snapshot.
    Empty clear requires None/empty name and may cause shader errors. Native callbacks may change pin types/
    compile; no collection value edits/runtime instance update/load/save. Transactions/dry-run, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/expressions/collection-parameter", json={
        "AssetPath": asset_path, "ExpressionPath": expression_path, "ExpressionGuid": node_guid,
        "FieldName": operation, "SourceTexturePath": collection_path, "Name": parameter_name,
        "ExpectedTargetPath": expected_collection_path, "ExpectedOutputName": expected_parameter_name,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_metadata_snapshot,
        "ExpectedDestinationSnapshot": expected_collection_layout, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def material_collection_defaults(asset_path: str, operation: str = "Inspect", start: int = 0, count: int = 64,
                                  parameter_name: str = "", parameter_guid: str = "", value: float = 0,
                                  expected_value: float = 0, rgba: list[float] = [], expected_rgba: list[float] = [],
                                  expected_class_path: str = "", expected_defaults_snapshot: str = "",
                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect native collection defaults/page1..128 or edit Scalar/Vector default at kind-local start index.
    Exact unique name/GUID/class/full defaults snapshot/prior native floats, finite+/-65504/linear RGBA.
    Native callbacks may update instances/resources/dependents, no runtime override reset/explicit save proof.
    Layout/sibling defaults readback/transactions/dry-run; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/defaults", json={
        "AssetPath": asset_path, "FieldName": operation, "Start": start, "Count": count,
        "Name": parameter_name, "ExpectedSourceId": parameter_guid, "Value": value,
        "ExpectedValue": expected_value, "Color": rgba, "ExpectedColor": expected_rgba,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_defaults_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def create_material_parameter_collection(asset_path: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Create native Material Parameter Collection via AssetTools/native factory defaults.
    Canonical new /Game/Folder/Name.Name/no overwrite, explicit confirmation/transaction/dirty/dry-run.
    Native resource initialization possible; creation undo/persistence unverified. No explicit compile/save.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/create", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def add_material_collection_parameter(asset_path: str, kind: str, parameter_name: str,
                                      expected_class_path: str, expected_defaults_snapshot: str,
                                      value: float = 0, rgba: list[float] = [],
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Append Scalar/Vector native collection parameter/new unique name/native GUID/per-kind1024 budget.
    Finite defaults+/-65504, linear vector, full snapshot/class/array editability/transaction/ArrayAdd callback.
    Native uniform-layout propagation may compile dependents; no explicit wait/save. Dry-run no promised GUID.
    Full sibling readback/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/parameters/add", json={
        "AssetPath": asset_path, "FieldName": kind, "Name": parameter_name, "Value": value,
        "Color": rgba, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_defaults_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def rename_material_collection_parameter(asset_path: str, kind: str, parameter_index: int,
                                         old_name: str, new_name: str, parameter_guid: str,
                                         expected_class_path: str, expected_defaults_snapshot: str,
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Rename native Scalar/Vector collection parameter preserving GUID/default/order.
    Exact full snapshot/class/index-old name-GUID/unused new FName. Loaded expression refs first256 reported,
    not complete unloaded/Blueprint/name-based dependency audit; name-based callers may require updates.
    Native callbacks may compile/refresh dependents; transaction/dry-run/no explicit load/save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/parameters/rename", json={
        "AssetPath": asset_path, "FieldName": kind, "Start": parameter_index,
        "Name": old_name, "OutputName": new_name, "ExpectedSourceId": parameter_guid,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_defaults_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def delete_material_collection_parameter(asset_path: str, kind: str, parameter_index: int,
                                         parameter_name: str, parameter_guid: str,
                                         expected_class_path: str, expected_defaults_snapshot: str,
                                         expected_loaded_expression_paths: list[str] = [],
                                         allow_breaking_loaded_references: bool = False,
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Delete native Scalar/Vector collection parameter, dry-run reports sorted loaded direct references.
    Exact snapshot/class/index-name-GUID and on mutation exact reference list/explicit break override when used.
    Unloaded/Blueprint/name-based dependencies not fully audited; expressions not remapped, may fail shaders.
    Native ArrayRemove/layout callbacks/remaining sibling readback/transaction/dry-run; no load/wait/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/parameters/delete", json={
        "AssetPath": asset_path, "FieldName": kind, "Start": parameter_index, "Name": parameter_name,
        "ExpectedSourceId": parameter_guid, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_defaults_snapshot, "ExpectedComponentPaths": expected_loaded_expression_paths,
        "bEnabled": allow_breaking_loaded_references, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def validate_material_collection_structure(asset_path: str) -> str:
    """Read-only native collection name/GUID uniqueness-validity/lookup roundtrip/default-finite/count checks.
    Separate loaded expression name-GUID mismatches, bounded returned diagnostics/full scans unbounded.
    Not shader/cook/uniform-resource/unloaded dependency/runtime readiness proof. No repair/build/load/save.
    Source implementation uncompiled and endpoint untested.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/validate-structure", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_material_collection_world_values(asset_path: str, world_path: str, world_kind: str = "Editor",
                                             start: int = 0, count: int = 64, confirm: bool = False) -> str:
    """Inspect native effective collection values in exact current Editor/active PIE world/page1..128.
    Explicit confirm: native world accessor can lazily create missing instance/update render state.
    No override writes/asset edits; getters fallback without exposing override presence, no GPU/frame proof.
    No explicit load/compile/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/world-values/inspect-page", json={
        "AssetPath": asset_path, "WorldPath": world_path, "Name": world_kind,
        "Start": start, "Count": count, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def set_material_collection_world_value(asset_path: str, world_path: str, instance_path: str,
                                         kind: str, parameter_name: str, parameter_guid: str,
                                         expected_defaults_snapshot: str, world_kind: str = "Editor",
                                         value: float = 0, expected_value: float = 0,
                                         rgba: list[float] = [], expected_rgba: list[float] = [],
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Set native Scalar/Vector world collection override/current Editor or active PIE world.
    Exact inspected instance/world paths/name-GUID-kind/full defaults snapshot/prior effective floats.
    Finite+/-65504/linear RGBA, native setters/render updates/delegates; no editor undo/asset save semantics.
    Accessor may lazily create instance even dry-run; no-op effective value preserves override presence.
    Native delegate side effects/partial writes possible; no GPU/frame proof, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/world-values/set", json={
        "AssetPath": asset_path, "WorldPath": world_path, "ComponentPath": instance_path,
        "Name": world_kind, "FieldName": kind, "OutputName": parameter_name,
        "ExpectedSourceId": parameter_guid, "ExpectedAssetSnapshot": expected_defaults_snapshot,
        "Value": value, "ExpectedValue": expected_value, "Color": rgba, "ExpectedColor": expected_rgba,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def reset_material_collection_world_values(asset_path: str, world_path: str, instance_path: str,
                                            expected_defaults_snapshot: str, expected_world_values_snapshot: str,
                                            world_kind: str = "Editor", confirm: bool = False,
                                            dry_run: bool = True) -> str:
    """Native reset clears all world instance scalar/vector override maps, exact current Editor/PIE identity.
    Full defaults/effective values snapshot from inspect, finite defaults/full default readback.
    Reset runs even values equal defaults (hidden overrides may exist); no editor undo/asset-save semantics.
    Accessor can lazily create even dry-run, no GPU/frame proof. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/world-values/reset", json={
        "AssetPath": asset_path, "WorldPath": world_path, "ComponentPath": instance_path,
        "Name": world_kind, "ExpectedAssetSnapshot": expected_defaults_snapshot,
        "ExpectedDestinationSnapshot": expected_world_values_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def discover_material_parameter_collections(path_filter: str = "", start: int = 0, count: int = 64) -> str:
    """Discover loaded native collection assets/pages1..128/counts/dirty/direct loaded expression counts.
    Optional path substring, global scans/sort unbounded, no unloaded referencer completeness.
    No world instance access/build/compile/load/save/mutation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/discover", json={
        "PathFilter": path_filter, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def reorder_material_collection_parameters(asset_path: str, kind: str, source_order: list[int],
                                            expected_class_path: str, expected_defaults_snapshot: str,
                                            confirm: bool = False, dry_run: bool = True) -> str:
    """Full Scalar/Vector kind-local permutation; preserves native GUID/name/default and other kind.
    Exact snapshot/class/native editability/unique names-GUIDs/per-kind1024 budget. Native ArrayMove
    callbacks may change uniform layout/recompile dependents. Transactions/readback/dry-run, no explicit save.
    Native propagation/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/parameters/reorder", json={
        "AssetPath": asset_path, "FieldName": kind, "SourceOrder": source_order,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_defaults_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_material_collection_references(asset_path: str, parameter_guid: str = "",
                                           start: int = 0, count: int = 64) -> str:
    """Inspect loaded direct collection-expression references/pages1..128/optional parameter GUID.
    Paths/nodeGUID/owner/full metadata and name-GUID resolution; transient/pending refs flagged.
    No complete unloaded/Blueprint/name-based/runtime dependency audit or owner collection membership proof.
    No mutation/repair/build/compile/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/materials/collections/references/inspect-page", json={
        "AssetPath": asset_path, "ExpectedSourceId": parameter_guid, "Start": start, "Count": count}, timeout=180).text
