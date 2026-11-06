"""Landscapes."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_world_landscapes() -> str:
    """Inspect up to128 loaded current-world landscape/streaming proxies, identity/topology/transform.
    Unloaded actors omitted; global iteration unbounded, GUID not revision proof.
    No landscape-info creation/load/edit/rebuild/save; native data validity unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/inspect", json={}, timeout=60).text


@mcp.tool()
def inspect_landscape_components(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect landscape proxy component-array page1..128, topology/combined heightmap/weightmaps.
    Up to32 weightmap paths/64 layer allocations per component; editing-layer data not evaluated.
    Indices/order can change between calls; no sampling/load/edit/rebuild/save, data validity unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/components/inspect", json={
        "ActorPath": actor_path, "Start": start, "Count": count
    }, timeout=60).text


@mcp.tool()
def inspect_landscape_heights(actor_path: str, x: int, y: int,
                              width: int = 1, height: int = 1) -> str:
    """Read native combined landscape source heights in grid rectangle dimensions1..64/origin+/-1e6.
    Explicit combined layer, independent of active edit layer; shared info includes other loaded proxies.
    Raw uint16 and local Z=(raw-32768)/128 rows Y then X; missing samples null.
    <=4096 requests, texture locking/decompression unbounded; source can be stale.
    No merge/GPU/collision sampling/load/edit/rebuild/save; native behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/heights/inspect", json={
        "ActorPath": actor_path, "X": x, "Y": y, "Width": width, "Height": height
    }, timeout=120).text


@mcp.tool()
def inspect_landscape_paint_layers(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Page1..128 existing shared landscape-info paint target layers/names/asset/owner paths.
    Includes placeholders; distinct from landscape edit-layer stack. No refresh/load/edit/save.
    Native metadata/material coverage/data validity unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/paint-layers/inspect", json={
        "ActorPath": actor_path, "Start": start, "Count": count
    }, timeout=60).text


@mcp.tool()
def inspect_landscape_weights(actor_path: str, layer_info_path: str, x: int, y: int,
                              width: int = 1, height: int = 1) -> str:
    """Read combined paint weight bytes0..255 for loaded registered layer-info asset.
    Grid origin+/-1e6/dimensions1..64; explicit combined source, shared info may include other proxies.
    Y rows/X columns, missing sparse samples null (not necessarily zero/absent geometry).
    Texture locking/decompression unbounded; no normalization/merge/GPU/load/edit/rebuild/save.
    Combined source freshness/native read behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/weights/inspect", json={
        "ActorPath": actor_path, "LayerInfoPath": layer_info_path,
        "X": x, "Y": y, "Width": width, "Height": height
    }, timeout=120).text


@mcp.tool()
def inspect_landscape_edit_layers(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect native UE5.7 edit-layer stack objects/GUID/name/flags/brush count/capabilities/alpha.
    Main landscape must be loaded, proxy path resolves existing info; page1..128.
    Distinct from paint targets, no legacy fields/merge/load/edit/save; native state unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/inspect", json={
        "ActorPath": actor_path, "Start": start, "Count": count
    }, timeout=60).text


@mcp.tool()
def set_landscape_edit_layer_bool(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                  field: str, expected_value: bool, value: bool,
                                  confirm: bool = False, dry_run: bool = False) -> str:
    """Set native edit-layer Visible/Locked with exact main actor/layer GUID/path/current flag guards.
    Visibility change requires unlocked layer. Actor/layer transaction/native setter/readback/no-op/dry-run.
    Native delegates may request deferred landscape merges; no synchronous merge/save.
    Native callbacks/renderer/collision/Nanite completion/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/bool", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "FieldName": field, "bExpectedValue": expected_value, "bValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_edit_layer_alpha(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                   target: str, expected_value: float, value: float,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set unlocked supported native Heightmap/Weightmap layer alpha within native inspected range.
    Exact main actor/layer GUID/path/current native-float alpha guards.
    Transaction/native ValueSet setter/readback/no-op/dry-run; may request deferred merges.
    No synchronous merge/build/save; source/collision/Nanite completion/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/alpha", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "FieldName": target, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_landscape_edit_layer_heights(actor_path: str, edit_layer_guid: str, edit_layer_path: str, x: int, y: int,
                              width: int = 1, height: int = 1) -> str:
    """Read bounded explicit edit-layer source with inspected native layer GUID/path/target support.
    Grid origin+/-1e6/dimensions1..64, shared info includes other loaded proxies.
    Reject touched components missing layer data to avoid native combined fallback; missing samples null.
    All-component traversal/source locking work unbounded; no merge/load/edit/rebuild/save.
    Native source may differ from rendered/merged state; data/side effects unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/heights/inspect", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path, "X": x, "Y": y, "Width": width, "Height": height
    }, timeout=120).text


@mcp.tool()
def inspect_landscape_edit_layer_weights(actor_path: str, edit_layer_guid: str, edit_layer_path: str, layer_info_path: str, x: int, y: int,
                              width: int = 1, height: int = 1) -> str:
    """Read bounded explicit edit-layer source with inspected native layer GUID/path/target support.
    Grid origin+/-1e6/dimensions1..64, shared info includes other loaded proxies.
    Reject touched components missing layer data to avoid native combined fallback; missing samples null.
    All-component traversal/source locking work unbounded; no merge/load/edit/rebuild/save.
    Native source may differ from rendered/merged state; data/side effects unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/weights/inspect", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path, "LayerInfoPath": layer_info_path,
        "X": x, "Y": y, "Width": width, "Height": height
    }, timeout=120).text


@mcp.tool()
def rename_landscape_edit_layer(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                expected_name: str, name: str,
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Rename unlocked native edit layer with inspected actor/GUID/path/exact display-name guard.
    Unique nonempty FName1..128/no control characters; case-only FName changes no-op.
    Object path/GUID retained; transaction/native setter/readback/dry-run/no build/save.
    Native rename can request deferred merge; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/rename", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "ExpectedName": expected_name, "Name": name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_landscape_edit_layer(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                 expected_layer_order: list[str], destination_index: int,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Move native edit layer to final zero-based destination index, full inspected GUID order<=256.
    Exact actor/moved-layer GUID/path guards; all layers whose indices change must be unlocked.
    Transaction/native reorder/full order readback/no-op/dry-run; forces deferred all-layer update.
    No synchronous merge/build/save; renderer/collision/Nanite completion/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/reorder", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "ExpectedLayerOrder": expected_layer_order, "DestinationIndex": destination_index,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_landscape(label: str, components_x: int = 1, components_y: int = 1, base_height: int = 32768,
                     x: int = 0, y: int = 0, layer_info_path: str = "", layer_name: str = "",
                     confirm: bool = False, dry_run: bool = True) -> str:
    """Create a flat native landscape in an ordinary (non-WorldPartition) editor map.
    One 31-quad section per component, 1..4 components per side, uniform base height 1..65535,
    100cm scale, no material. Optional new /Game layer-info asset imported as paint target layer_name.
    Unique letters/digits/underscore label. Transaction/native import/readback/dry-run; no map save.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/create", json={
        "Name": label, "Width": components_x, "Height": components_y, "Value": base_height,
        "X": x, "Y": y, "LayerInfoPath": layer_info_path, "FieldName": layer_name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=300).text


@mcp.tool()
def create_landscape_edit_layer(actor_path: str, name: str, expected_layer_order: list[str],
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Append standard native ULandscapeEditLayer with full inspected stack GUID guard<=256.
    Ordinary non-WorldPartition map/loaded main landscape, unique name1..128/native layer-count cap.
    Transaction/native create/readback/dry-run; native allocation affects loaded proxies/textures,
    requests initialization/spline updates/deferred merges, work unbounded. No synchronous build/save.
    Native allocation transaction coverage/callbacks/collision/Nanite/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/create", json={
        "ActorPath": actor_path, "Name": name, "ExpectedLayerOrder": expected_layer_order,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_landscape_edit_layer(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                expected_name: str, expected_layer_order: list[str],
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Delete unlocked standard native edit layer/no brushes in ordinary non-WorldPartition map.
    Full inspected GUID order2..256/main actor/layer GUID/path/name guards; preserve at least one layer.
    Transaction/native deletion/full remaining-order readback/dry-run/no save.
    Removes source layer data across loaded proxies; selection/texture usage/deferred merge may change.
    No synchronous merge/build; transaction content restoration/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/delete", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "ExpectedName": expected_name, "ExpectedLayerOrder": expected_layer_order,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_edit_layer_heights(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                     x: int, y: int, width: int, height: int,
                                     expected_heights: list[int], heights: list[int],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Patch raw uint16 heights0..65535, flattened row-major Y/X rectangle dimensions1..64.
    Exact inspected full source data/main actor/standard unlocked edit-layer GUID/path guards.
    Ordinary non-WorldPartition map, complete preexisting layer/component/texture coverage.
    Native transaction/write/mips/GPU upload/source readback; requests deferred all-layer update.
    No immediate normals/bounds/collision update; derived terrain completion/undo unverified.
    No synchronous build/save; native work unbounded, failure may leave partial undo transaction.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/heights", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "X": x, "Y": y, "Width": width, "Height": height,
        "ExpectedHeights": expected_heights, "Heights": heights,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_edit_layer_weights(actor_path: str, edit_layer_guid: str, edit_layer_path: str,
                                     layer_info_path: str, x: int, y: int, width: int, height: int,
                                     expected_weights: list[int], weights: list[int],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Patch selected paint-layer source weights0..255 flattened Y/X, dimensions1..64.
    Exact full expected data/main actor/unlocked standard edit layer GUID/path/registered layer-info.
    Ordinary non-WorldPartition map/complete preexisting loaded source coverage.
    Native SetAlphaData None restriction/transaction/Flush/readback/deferred all-layer update.
    Native allocation can repack channels/textures/references; normalization/render/undo unverified.
    No synchronous merge/build/save; native work unbounded, failure may leave partial transaction.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/edit-layers/weights", json={
        "ActorPath": actor_path, "EditLayerGuid": edit_layer_guid, "EditLayerPath": edit_layer_path,
        "LayerInfoPath": layer_info_path, "X": x, "Y": y, "Width": width, "Height": height,
        "ExpectedWeights": expected_weights, "Weights": weights,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_landscape_layer_info(layer_info_path: str) -> str:
    """Inspect loaded native layer-info blend/physical-material/hardness/collision/debug/spline settings.
    Blend0 None/1 FinalWeightBlending/2 PremultipliedAlphaBlending, group relevant to advanced blend.
    Shared asset; no load/reference search/merge/build/save, evaluator/collision validity unproven.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/layer-info/inspect", json={
        "LayerInfoPath": layer_info_path
    }, timeout=60).text


@mcp.tool()
def set_landscape_layer_info_blend(layer_info_path: str, expected_method: int,
                                   expected_group: str, method: int, group: str,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set shared native layer-info blend method0..2/group<=128 pair with inspected pair guard.
    Empty group None; case-insensitive FName, retained for methods that ignore group.
    Asset transaction/native setters/readback/no-op/dry-run; delegates can update all loaded references.
    Callbacks may observe intermediate pair, no synchronous merge/build/save; undo/render unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/layer-info/blend", json={
        "LayerInfoPath": layer_info_path, "ExpectedBlendMethod": expected_method,
        "ExpectedBlendGroup": expected_group, "BlendMethod": method, "BlendGroup": group,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_layer_info_scalar(layer_info_path: str, field: str,
                                    expected_value: float, value: float,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Set Hardness/MinimumCollisionRelevanceWeight0..1, SplineFalloffModulationTiling0.01..1e6,
    SplineFalloffModulationBias/Scale0..1e6 adapter cap. Exact inspected native float guard.
    Shared asset transaction/native ValueSet setter/readback/no-op/dry-run/no save.
    Hardness means erosion resistance; native referencing-landscape callbacks/deferred updates possible.
    No synchronous merge/collision rebuild/build; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/layer-info/scalar", json={
        "LayerInfoPath": layer_info_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_layer_info_asset(layer_info_path: str, field: str,
                                   expected_asset_path: str, asset_path: str,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set shared PhysicalMaterial/SplineFalloffModulationTexture to loaded compatible asset or empty clear.
    Exact inspected current path guard, asset transaction/native setter/readback/no-op/dry-run/no load/save.
    Landscape material physical-material node may override assigned physical material.
    Texture class does not prove sampling suitability; native shared callbacks/merge/collision/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/layer-info/asset", json={
        "LayerInfoPath": layer_info_path, "FieldName": field,
        "ExpectedAssetPath": expected_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_layer_info_debug_color(layer_info_path: str, expected_color: list[float],
                                         color: list[float], confirm: bool = False,
                                         dry_run: bool = False) -> str:
    """Set shared layer-info linear debug RGBA RGB0..1/alpha1, full inspected current RGBA guard.
    Native float/no sRGB conversion, asset transaction/native setter/readback/no-op/dry-run/no save.
    Native debug callback does not request landscape data update; display/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/layer-info/debug-color", json={
        "LayerInfoPath": layer_info_path, "ExpectedColor": expected_color, "Color": color,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_landscape_layer_info_spline_mask(layer_info_path: str, expected_mask: int, mask: int,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Set native spline-falloff texture channel0 Red/1 Green/2 Blue/3 Alpha, inspected ordinal guard.
    Shared asset transaction/native setter/readback/no-op/dry-run/no save; texture/scalars retained.
    No explicit spline reapply/merge/build; native callbacks/sampling/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/landscapes/layer-info/spline-mask", json={
        "LayerInfoPath": layer_info_path, "ExpectedValue": expected_mask, "Value": mask,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_foliage_type_landscape_layers(actor_path: str, type_path: str, expected_update_guid: str,
                                          field: str, expected_names: list[str], names: list[str],
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Replace LandscapeLayers/ExclusionLandscapeLayers with full inspected ordered-name guard.
    <=64 FNames1..128, empty array clears; order/duplicates retained, no landscape name resolution.
    Type GUID/membership guard/transaction/notification/readback/no-op/dry-run/no painting/reapply/build/save.
    Native hit-landscape/threshold eligibility/shared callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/landscape-layers", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "ExpectedNames": expected_names, "Names": names,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
