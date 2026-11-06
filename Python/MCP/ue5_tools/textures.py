"""Textures, render targets, virtual textures and scene captures."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp, _asset_request


@mcp.tool()
def inspect_texture(asset_path: str) -> str:
    """Inspect a Texture asset."""
    return httpx.get(f"{app.BASE_URL}/textures/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_texture_settings(asset_path: str, properties: dict, save: bool = False) -> str:
    """Edit reflected texture settings, for example SRGB, LODGroup, or MipGenSettings."""
    return _asset_request("textures/settings", asset_path, properties, save=save)


@mcp.tool()
def inspect_texture_source(asset_path: str) -> str:
    """Inspect source image dimensions, ID, files, and local file status."""
    return httpx.get(f"{app.BASE_URL}/textures/source", params={"asset_path": asset_path}).text


@mcp.tool()
def import_texture(source_file_path: str, destination_path: str, asset_name: str,
                   replace_existing: bool = False, confirm_replace: bool = False,
                   dry_run: bool = False, save: bool = False) -> str:
    """Import a local image (or .ies light profile) as a Texture asset; replacement requires confirmation."""
    return httpx.post(f"{app.BASE_URL}/textures/import", json={
        "SourceFilePath": source_file_path, "DestinationPath": destination_path,
        "AssetName": asset_name, "bReplaceExisting": replace_existing,
        "bConfirmReplace": confirm_replace, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def reimport_texture(asset_path: str, source_file_path: str = "",
                     confirm_reimport: bool = False,
                     confirm_source_change: bool = False,
                     dry_run: bool = False, save: bool = False) -> str:
    """Reimport a Texture from its recorded source or a confirmed new local file."""
    return httpx.post(f"{app.BASE_URL}/textures/reimport", json={
        "AssetPath": asset_path, "SourceFilePath": source_file_path,
        "bConfirmReimport": confirm_reimport,
        "bConfirmSourceChange": confirm_source_change,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def set_light_texture(actor_path: str, component_path: str, field: str, expected_asset_path: str,
                        asset_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded IESTexture/LightFunctionMaterial or rect SourceTexture; empty clears.
    LightFunctionMaterial requires native LightFunction domain.
    Exact inspected asset guard, native class check/transaction/editor notification/
    readback/dry-run/no-op/no load/build/save. Texture filter/render/undo behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/texture", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedAssetPath": expected_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_render_target_2d(asset_path: str) -> str:
    """Inspect loaded persistent 2D render-target authored settings/dimensions/clear color/native enums.
    No RHI resource dereference/read pixels/asset load/render evaluation/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_render_target_2d_setting(asset_path: str, expected_class_path: str, field_name: str,
                                   expected_value: float, value: float, confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set TargetGamma0..10, RenderTargetFormat/native mip sampler enums, shared/UAV/auto-mips flags0..1.
    Exact class/current guard, loaded standard-format dimensions1..2048 to avoid native modal callbacks.
    Native transaction/events/readback may recreate resources/refresh captures; derived gamma/sRGB may change.
    No hardware/read-pixels/capture outcome proof or explicit update/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/setting", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value, "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def resize_render_target_2d(asset_path: str, expected_class_path: str, expected_size_x: int, expected_size_y: int,
                              size_x: int, size_y: int, confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Edit paired standard-format target dimensions1..2048 with full previous pair/class guard.
    May reduce larger current targets; both values set before one native event to avoid modal callback.
    Resource recreation may discard old pixels; native callback queues matching scene captures globally.
    No explicit capture processing/read pixels/render evaluation/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/resize", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_size_x, "ExpectedSizeY": expected_size_y, "SizeX": size_x, "SizeY": size_y,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_render_target_2d_clear_color(asset_path: str, expected_class_path: str, expected_size_x: int,
                                      expected_size_y: int, expected_format: int, expected_rgba: list[float], rgba: list[float],
                                      confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Author linear clear RGBA-65504..65504 with full class/dimension/format/previous color guards.
    Standard-format dimensions1..2048/no custom override; preserves other settings, no sRGB conversion.
    Native callbacks can recreate resources/discard pixels; format may clamp/quantize/drop channels.
    Not clear-current-pixels: no explicit clear/capture/RHI update/read pixels/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/clear-color", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_size_x, "ExpectedSizeY": expected_size_y, "ExpectedFormat": expected_format,
        "ExpectedColor": expected_rgba, "Color": rgba, "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_loaded_render_targets_2d(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent 2D target assets1..128 with path substring, authored metadata only.
    No unloaded asset inventory/RHI access/read pixels/capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_render_target_2d_capture_consumers(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Page direct loaded scene-capture2D target references across all worlds/templates/transients1..128.
    Reports native resize noninteractive deferred-refresh predicate; no execution or capture/output proof.
    Not complete dependency graph, no RHI access/capture processing/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/consumers/inspect-page", json={
        "AssetPath": asset_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def create_render_target_2d(asset_path: str, size_x: int = 256, size_y: int = 256,
                              confirm: bool = False, dry_run: bool = True) -> str:
    """Create source-free native 2D render-target asset at new canonical /Game/Folder/Name.Name, dimensions1..2048.
    No overwrite; native factory format/clear/gamma/mip defaults retained, can initialize render resource.
    Registry/package/transaction/readback/dirty, asset-creation undo unverified; no capture/read pixels/render eval/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d/create", json={
        "AssetPath": asset_path, "SizeX": size_x, "SizeY": size_y, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_captures_2d_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded persistent current-world scene-capture2D metadata1..128, optional exact owner.
    No actual capture/capture processing/RHI access/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_target(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                  expected_target_path: str, target_path: str,
                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Assign loaded persistent render-target2D asset or empty clear with exact reference/GUID/label guard.
    Preserves transform/source/FOV/ortho/capture policies/visibility lists, target asset not edited.
    Native callbacks/normal renderer may capture; no explicit capture request/processing/RHI access/output proof/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/target", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedTargetPath": expected_target_path, "AssetPath": target_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_2d_settings(actor_path: str, component_path: str) -> str:
    """Inspect native projection/source/render-mode/scheduling/LOD/priority/ortho-plane settings and enum metadata.
    No capture/rendering eligibility evaluation or build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/settings/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                   expected_class_path: str, field_name: str, expected_value: float, value: float,
                                   confirm: bool = False, dry_run: bool = True, expected_setting_texts: list[str] | None = None) -> str:
    """Set inspected native capture setting within reported adapter bounds/native visible enum options.
    Optional full native_setting_texts from inspection guards all supported settings, in native list order.
    Exact class/current/GUID/label guards, full supported sibling/target/transform/visibility-list readback.
    Also supports bEnableOrthographicTiling/NumXTiles/NumYTiles1..64 and main-renderer/view-family/resolution/camera flags,
    UnlitViewmode, CompositeMode, PostProcessBlendWeight0..1, inherited main-camera postprocess,
    ignore-screen-percentage and fog-only-rendered-pixels flags. Tiling requires orthographic SceneColor; CVar overrides may apply.
    FOV degrees, ortho/view distances centimeters; inactive fields allowed, source can change derived show flags.
    Native callbacks/scheduling may capture, no explicit request/processing/output proof/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/settings/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_clip_plane(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      expected_class_path: str, expected_base: list[float], expected_normal: list[float],
                                      expected_enabled: bool, base: list[float], normal: list[float],
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Set world clip-plane base+/-1e9 and unit normal with full prior pair/enable/class/GUID/label guards.
    Does not change enable flag/project config; project global clip plane support required for effect.
    Native transaction/events/readback, no explicit capture/output evaluation/build/render sync/load/save.
    """
    if any(len(v) != 3 for v in (expected_base, expected_normal, base, normal)):
        raise ValueError("Plane base/normals require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/clip-plane", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedPlaneBase": dict(zip(("X", "Y", "Z"), expected_base)),
        "ExpectedPlaneNormal": dict(zip(("X", "Y", "Z"), expected_normal)), "bExpectedClipEnabled": expected_enabled,
        "PlaneBase": dict(zip(("X", "Y", "Z"), base)), "PlaneNormal": dict(zip(("X", "Y", "Z"), normal)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_projection_matrix(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                             expected_class_path: str, expected_matrix: list[float], matrix: list[float],
                                             expected_enabled: bool, enabled: bool,
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Set full16-entry row-major native custom projection matrix/use flag with exact prior pair/class/GUID/label guards.
    Finite entries+/-1e9/determinant abs>=1e-12; no convention conversion/valid Unreal frustum/output proof.
    Native custom projection does not currently affect culling; no explicit capture/evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/projection-matrix", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedMatrix": expected_matrix, "Matrix": matrix,
        "bExpectedUseCustomProjection": expected_enabled, "bUseCustomProjection": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_2d_actor_lists(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect authored hidden/show-only actor references in independent pages1..128, render-mode and component-list metadata.
    No actor loading/capture/render evaluation/build/render synchronization/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/actor-lists/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_actor_list(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      expected_class_path: str, field_name: str, expected_actor_paths: list[str],
                                      actor_paths: list[str], confirm: bool = False, dry_run: bool = True) -> str:
    """Replace HiddenActors/ShowOnlyActors<=64 with full ordered current-list/class/GUID/label guard.
    Unique loaded persistent current-world actors, empty clears; preserves opposite list/component lists/render mode.
    Overlap allowed, render mode/source/renderer gates effect; no ordinary visibility edits/explicit capture/evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/actor-lists/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedActorPaths": expected_actor_paths, "ActorPaths": actor_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_2d_component_lists(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect hidden/show-only weak primitive-component references in independent pages1..128.
    Stale/null references export None path; no loading/capture/render evaluation/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/component-lists/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_component_list(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          expected_class_path: str, field_name: str,
                                          expected_component_paths: list[str], component_paths: list[str],
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Replace HiddenComponents/ShowOnlyComponents<=64 with full prior-path/class/GUID/label guard.
    Unique loaded persistent current-world primitive targets, empty clears; preserves actor lists/opposite list/render mode.
    Stale/null paths are None and cannot distinguish expired handles; no target visibility edits/explicit capture/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/component-lists/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedComponentPaths": expected_component_paths, "ComponentPaths": component_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_2d_show_flags(actor_path: str, component_path: str, start: int = 0, count: int = 64,
                                          query_names: list[str] | None = None) -> str:
    """Page stored show-flag overrides1..128 and optionally query current native component bits<=128.
    Component flags are not final renderer output; no capture/flag update/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/show-flags/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count,
        "ShowFlagNames": query_names or []
    }, timeout=180).text


@mcp.tool()
def discover_scene_capture_2d_show_flags(actor_path: str, component_path: str, name_filter: str = "",
                                           start: int = 0, count: int = 64) -> str:
    """Discover native engine/custom show-flag registry in name-sorted pages1..128 with substring filter.
    Group/current bits/stored override counts, no mutability/renderer support proof or capture/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/show-flags/discover", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Name": name_filter,
        "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_show_flags(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      expected_class_path: str, expected_names: list[str], expected_enabled: list[bool],
                                      names: list[str], enabled: list[bool], confirm: bool = False, dry_run: bool = True) -> str:
    """Replace complete ordered show-flag overrides<=128 with full prior name/bool/class/GUID/label guards.
    Unique recognized native flag indices; empty clears stored overrides, native setter uses archetype defaults.
    Fixed/render-source/project flags may differ from stored values; no explicit capture/output proof/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/show-flags/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedShowFlagNames": expected_names, "ExpectedShowFlagValues": expected_enabled,
        "ShowFlagNames": names, "ShowFlagValues": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_resolution_divisor(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                              expected_class_path: str, expected_xy: list[int], xy: list[int],
                                              confirm: bool = False, dry_run: bool = True,
                                              expected_setting_texts: list[str] | None = None) -> str:
    """Set paired MainViewResolutionDivisor integer XY1..64 with full prior pair/class/GUID/label guards.
    Optional full native setting snapshot; preserves capture settings/target/transform/clip plane/visibility lists.
    Inactive accepted, no target resize/main-view edits/explicit capture/render eval/build/sync/load/save.
    """
    if len(expected_xy) != 2 or len(xy) != 2:
        raise ValueError("Divisors require XY pairs")
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/resolution-divisor", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedResolutionDivisor": dict(zip(("X", "Y"), expected_xy)),
        "ResolutionDivisor": dict(zip(("X", "Y"), xy)),
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_output_name(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                        expected_class_path: str, field_name: str, expected_name: str, name: str,
                                        confirm: bool = False, dry_run: bool = True,
                                        expected_setting_texts: list[str] | None = None) -> str:
    """Set UserSceneTextureBaseColor/Normal/SceneColor native FName with exact prior name/class/GUID/label guards.
    Empty/None clears, case-only changes no-op; duplicate names allowed, consumer/conflict behavior unverified.
    Can change effective main-view policy without changing authored flags; no explicit capture/evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/output-name", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "FieldName": field_name, "ExpectedOutputName": expected_name, "OutputName": name,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_transform_collection(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                                 expected_class_path: str, expected_collection_path: str, collection_path: str,
                                                 confirm: bool = False, dry_run: bool = True,
                                                 expected_setting_texts: list[str] | None = None) -> str:
    """Assign loaded material parameter collection or empty clear for native capture matrix outputs.
    Exact prior reference/class/GUID/label guards; retains parameter names/settings/target/transform.
    Vector layout/writer ownership not validated; normal rendering may write runtime collection instance values.
    No asset parameter edits/explicit capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/transform-collection", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedTargetPath": expected_collection_path, "AssetPath": collection_path,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_collection_parameter(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                                 expected_class_path: str, expected_collection_path: str,
                                                 field_name: str, expected_name: str, name: str,
                                                 confirm: bool = False, dry_run: bool = True,
                                                 expected_setting_texts: list[str] | None = None) -> str:
    """Set CollectionTransformWorldToLocal/CollectionTransformProjection first-vector name with exact prior/ref guards.
    Empty/None clears, native case-insensitive identity; preserves other parameter/settings/target/divisor.
    Needs5 contiguous vectors for world-to-local/4 projection; layout/overlap/writer ownership not validated.
    No collection asset edits/explicit parameter writes/capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/collection-parameter", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedTargetPath": expected_collection_path, "FieldName": field_name,
        "ExpectedOutputName": expected_name, "OutputName": name,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_2d_collection_layout(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect assigned collection authored vector order/defaults1..128 and configured5/4-vector output capacity/overlap.
    First matching names only; not native packing/runtime-instance/shader/other-writer conflict proof.
    No instance creation/parameter writes/capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/collection-layout/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_2d_view_channels(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          expected_class_path: str, expected_channels: list[int], channels: list[int],
                                          confirm: bool = False, dry_run: bool = True,
                                          expected_setting_texts: list[str] | None = None) -> str:
    """Set all five native view-lighting bits0..1 with full prior/class/GUID/label guards, zero allowed.
    Distinct from three object lighting channels; light-side masks/renderer path gate effects, lights unchanged.
    Native transaction/readback, no explicit capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/view-channels", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedChannels": expected_channels, "Channels": channels,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_2d_collection_writers(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Page loaded capture2D references to selected transform collection across worlds/templates/transients1..128.
    Includes selected capture, scheduling/world metadata and simple authored vector-range overlap.
    Not runtime write/conflict proof; worlds have separate collection instances, other/unloaded writers excluded.
    No instance creation/parameter writes/capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/2d/collection-writers/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_render_target_cube(asset_path: str) -> str:
    """Inspect loaded persistent cube target face size/HDR/override/gamma/mip/UAV/clear color/edit metadata.
    Cached mip count not GPU allocation/content freshness proof; no RHI access/read pixels/capture/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/cube/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_render_target_cube_setting(asset_path: str, expected_class_path: str, expected_face_size: int,
                                       field_name: str, expected_value: float, value: float,
                                       confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set cube SizeX1..2048/TargetGamma0..10/bHDR/bSupportsUAV/bAutoGenerateMips/native MipsSamplerFilter.
    Exact class/current face size/current field guards, standard format without custom override.
    Native callbacks may discard pixels/queue cube captures globally; no explicit processing/readback/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/cube/setting", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSizeX": expected_face_size,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_loaded_render_targets_cube(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent cube target assets1..128/path substring, authored face/HDR/override/mip metadata.
    No unloaded inventory/RHI access/read pixels/capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/cube/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_render_target_cube_capture_consumers(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Page direct loaded cube-capture references across worlds/templates/transients1..128.
    Native noninteractive resize/auto-mip deferred-refresh predicate, not actual capture execution/output proof.
    Excludes other/unloaded dependencies; no RHI access/capture processing/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/cube/consumers/inspect-page", json={
        "AssetPath": asset_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def create_render_target_cube(asset_path: str, face_size: int = 256, confirm: bool = False, dry_run: bool = True) -> str:
    """Create source-free exact native cube render-target asset at canonical new /Game/Folder/Name.Name.
    Face size1..2048, no overwrite, native HDR/clear/gamma/mip defaults, factory initializes six-face resource.
    Registry/transaction/readback/dirty, asset-creation undo unverified; no capture/read pixels/render eval/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/cube/create", json={
        "AssetPath": asset_path, "SizeX": face_size, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_captures_cube_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page native loaded persistent current-world cube captures1..128/path sorted/optional owner.
    Identity/target/rotation/scheduling/source metadata; no capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_cube_target(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      expected_target_path: str, target_path: str,
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Assign loaded persistent cube render target or empty clear with exact previous reference/GUID/label guards.
    Preserves capture rotation/postprocess blend/source/mode/scheduling/visibility lists/transform.
    Native callbacks/ordinary rendering may capture; no explicit request/processing/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/target", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedTargetPath": expected_target_path, "AssetPath": target_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_render_target_cube_clear_color(asset_path: str, expected_class_path: str, expected_face_size: int,
                                           expected_hdr: bool, expected_rgba: list[float], rgba: list[float],
                                           confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Author cube clear linear RGBA-65504..65504 with full class/face/HDR/previous color guards.
    Standard native format/face1..2048; preserves size/HDR/UAV/mip/filter/gamma, no color-space conversion.
    Resource recreation may discard pixels; not explicit clear-current-pixels/capture/readback/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/cube/clear-color", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSizeX": expected_face_size,
        "ExpectedFormat": int(expected_hdr), "ExpectedColor": expected_rgba, "Color": rgba,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_cube_settings(actor_path: str, component_path: str) -> str:
    """Inspect cube rotation/source/mode/scheduling/postprocess/LOD/distance/priority fields and native snapshots/enums."""
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/settings/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_cube_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                        expected_class_path: str, field_name: str, expected_value: float, value: float,
                                        confirm: bool = False, dry_run: bool = True,
                                        expected_setting_texts: list[str] | None = None) -> str:
    """Set inspected native cube capture field with class/GUID/label/current and optional full native snapshot guards.
    CaptureRotation selects actor-aligned versus world-axis cube; renderer/source/target eligibility unverified.
    No explicit capture/queue processing/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/settings/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_cube_actor_lists(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect authored hidden/show-only actor references in independent pages1..128, render-mode and component-list metadata.
    No actor loading/capture/render evaluation/build/render synchronization/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/actor-lists/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_cube_actor_list(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      expected_class_path: str, field_name: str, expected_actor_paths: list[str],
                                      actor_paths: list[str], confirm: bool = False, dry_run: bool = True) -> str:
    """Replace HiddenActors/ShowOnlyActors<=64 with full ordered current-list/class/GUID/label guard.
    Unique loaded persistent current-world actors, empty clears; preserves opposite list/component lists/render mode.
    Overlap allowed, render mode/source/renderer gates effect; no ordinary visibility edits/explicit capture/evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/actor-lists/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedActorPaths": expected_actor_paths, "ActorPaths": actor_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_cube_component_lists(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect hidden/show-only weak primitive-component references in independent pages1..128.
    Stale/null references export None path; no loading/capture/render evaluation/build/sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/component-lists/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_cube_component_list(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          expected_class_path: str, field_name: str,
                                          expected_component_paths: list[str], component_paths: list[str],
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Replace HiddenComponents/ShowOnlyComponents<=64 with full prior-path/class/GUID/label guard.
    Unique loaded persistent current-world primitive targets, empty clears; preserves actor lists/opposite list/render mode.
    Stale/null paths are None and cannot distinguish expired handles; no target visibility edits/explicit capture/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/component-lists/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedComponentPaths": expected_component_paths, "ComponentPaths": component_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_scene_capture_cube_show_flags(actor_path: str, component_path: str, start: int = 0, count: int = 64,
                                          query_names: list[str] | None = None) -> str:
    """Page stored show-flag overrides1..128 and optionally query current native component bits<=128.
    Component flags are not final renderer output; no capture/flag update/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/show-flags/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count,
        "ShowFlagNames": query_names or []
    }, timeout=180).text


@mcp.tool()
def discover_scene_capture_cube_show_flags(actor_path: str, component_path: str, name_filter: str = "",
                                           start: int = 0, count: int = 64) -> str:
    """Discover native engine/custom show-flag registry in name-sorted pages1..128 with substring filter.
    Group/current bits/stored override counts, no mutability/renderer support proof or capture/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/show-flags/discover", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Name": name_filter,
        "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_cube_show_flags(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      expected_class_path: str, expected_names: list[str], expected_enabled: list[bool],
                                      names: list[str], enabled: list[bool], confirm: bool = False, dry_run: bool = True) -> str:
    """Replace complete ordered show-flag overrides<=128 with full prior name/bool/class/GUID/label guards.
    Unique recognized native flag indices; empty clears stored overrides, native setter uses archetype defaults.
    Fixed/render-source/project flags may differ from stored values; no explicit capture/output proof/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/show-flags/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedShowFlagNames": expected_names, "ExpectedShowFlagValues": expected_enabled,
        "ShowFlagNames": names, "ShowFlagValues": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_scene_capture_cube_view_channels(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          expected_class_path: str, expected_channels: list[int], channels: list[int],
                                          confirm: bool = False, dry_run: bool = True,
                                          expected_setting_texts: list[str] | None = None) -> str:
    """Set all five native view-lighting bits0..1 with full prior/class/GUID/label guards, zero allowed.
    Distinct from three object lighting channels; light-side masks/renderer path gate effects, lights unchanged.
    Native transaction/readback, no explicit capture/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/scene-captures/cube/view-channels", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedClassPath": expected_class_path,
        "ExpectedChannels": expected_channels, "Channels": channels,
        "ExpectedSettingTexts": expected_setting_texts or [], "bRequireSettingSnapshot": expected_setting_texts is not None,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_render_target_volume(asset_path: str) -> str:
    """Inspect loaded persistent volume target XYZ/HDR/override/gamma/UAV/clear/native edit metadata.
    Native mip count1 is not GPU/pixel readiness proof; no RHI access/read pixels/capture/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/volume/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_loaded_render_targets_volume(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent volume targets1..128/path substring with native XYZ/HDR/override metadata.
    No unloaded inventory/RHI access/read pixels/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/volume/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def create_render_target_volume(asset_path: str, size_x: int = 64, size_y: int = 64, size_z: int = 64,
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Create source-free native volume target at new canonical /Game/Folder/Name.Name, no overwrite.
    XYZ1..2048/total voxels<=16777216 adapter budget, native format/clear/gamma defaults/resource initialization.
    No capture/read pixels/render evaluation/build/render sync/save; resource readiness/creation undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/volume/create", json={
        "AssetPath": asset_path, "SizeX": size_x, "SizeY": size_y, "SizeZ": size_z,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_render_target_volume_setting(asset_path: str, expected_class_path: str, expected_size_x: int,
                                         expected_size_y: int, expected_size_z: int, field_name: str,
                                         expected_value: float, value: float, confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set native volume TargetGamma0..10/bHDR/bSupportsUAV0..1 with exact class/XYZ/current scalar guards.
    Standard format/XYZ1..2048/voxels<=16777216; preserves dimensions/clear/other settings.
    Resource recreation may discard pixels; no resource update/readback/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/volume/setting", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_size_x, "ExpectedSizeY": expected_size_y, "ExpectedSizeZ": expected_size_z,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_render_target_volume_clear_color(asset_path: str, expected_class_path: str, expected_size_x: int,
                                             expected_size_y: int, expected_size_z: int, expected_hdr: bool,
                                             expected_rgba: list[float], rgba: list[float],
                                             confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Author native volume clear linear RGBA-65504..65504 with class/XYZ/HDR/full previous color guards.
    Standard format/dimensions1..2048/voxels<=16777216; no color-space conversion or explicit current-voxel clear.
    Resource recreation may discard contents; no resource update/readback/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/volume/clear-color", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_size_x, "ExpectedSizeY": expected_size_y, "ExpectedSizeZ": expected_size_z,
        "ExpectedFormat": int(expected_hdr), "ExpectedColor": expected_rgba, "Color": rgba,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def resize_render_target_volume(asset_path: str, expected_class_path: str, expected_xyz: list[int], xyz: list[int],
                                    confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Resize all volume target XYZ together with full current dimensions/class guards.
    Standard format/XYZ1..2048/voxels<=16777216; preserves HDR/UAV/gamma/clear/override settings.
    Resource recreation may discard voxel data; no explicit update/readback/capture/render eval/build/sync/load/save.
    """
    if len(expected_xyz) != 3 or len(xyz) != 3:
        raise ValueError("Dimensions require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/render-targets/volume/resize", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_xyz[0], "ExpectedSizeY": expected_xyz[1], "ExpectedSizeZ": expected_xyz[2],
        "SizeX": xyz[0], "SizeY": xyz[1], "SizeZ": xyz[2], "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_render_target_2d_array(asset_path: str) -> str:
    """Inspect loaded persistent array target width/height/slices/HDR/override/gamma/UAV/clear/edit metadata.
    Native one mip is not GPU readiness proof; no RHI access/read pixels/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d-array/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_loaded_render_targets_2d_array(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent array targets1..128/path substring with native width/height/slices metadata.
    No unloaded asset inventory/RHI access/read pixels/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d-array/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_render_target_2d_array_setting(asset_path: str, expected_class_path: str, expected_size_x: int,
                                         expected_size_y: int, expected_slices: int, field_name: str,
                                         expected_value: float, value: float, confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set native array TargetGamma0..10/bHDR/bSupportsUAV0..1 with exact class/width/height/slices/current scalar guards.
    Standard format/width/height/slices1..2048/texel-slices<=16777216; preserves dimensions/clear/other settings.
    Resource recreation may discard pixels; no resource update/readback/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d-array/setting", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_size_x, "ExpectedSizeY": expected_size_y, "ExpectedSizeZ": expected_slices,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_render_target_2d_array_clear_color(asset_path: str, expected_class_path: str, expected_size_x: int,
                                             expected_size_y: int, expected_slices: int, expected_hdr: bool,
                                             expected_rgba: list[float], rgba: list[float],
                                             confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Author native array clear linear RGBA-65504..65504 with class/width/height/slices/HDR/full previous color guards.
    Standard format/dimensions1..2048/texel-slices<=16777216; no color-space conversion or explicit current-texel-slice clear.
    Resource recreation may discard contents; no resource update/readback/render eval/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d-array/clear-color", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_size_x, "ExpectedSizeY": expected_size_y, "ExpectedSizeZ": expected_slices,
        "ExpectedFormat": int(expected_hdr), "ExpectedColor": expected_rgba, "Color": rgba,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def resize_render_target_2d_array(asset_path: str, expected_class_path: str, expected_xy_slices: list[int], xy_slices: list[int],
                                    confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Resize all array target width/height/slices together with full current dimensions/class guards.
    Standard format/width/height/slices1..2048/texel-slices<=16777216; preserves HDR/UAV/gamma/clear/override settings.
    Resource recreation may discard texel-slice data; no explicit update/readback/capture/render eval/build/sync/load/save.
    """
    if len(expected_xy_slices) != 3 or len(xy_slices) != 3:
        raise ValueError("Dimensions require width/height/slices triples")
    return httpx.post(f"{app.BASE_URL}/render-targets/2d-array/resize", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSizeX": expected_xy_slices[0], "ExpectedSizeY": expected_xy_slices[1], "ExpectedSizeZ": expected_xy_slices[2],
        "SizeX": xy_slices[0], "SizeY": xy_slices[1], "SizeZ": xy_slices[2], "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_render_target_2d_array(asset_path: str, width: int = 256, height: int = 256, slices: int = 4,
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Create source-free native array target at new canonical /Game/Folder/Name.Name, no overwrite.
    Width/height/slices1..2048/total texel-slices<=16777216; native format/HDR/clear/gamma defaults.
    Factory initializes resource; no capture/read pixels/render eval/build/sync/save, creation undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/2d-array/create", json={
        "AssetPath": asset_path, "SizeX": width, "SizeY": height, "SizeZ": slices,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_texture_2d_array(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect source-backed Texture2DArray address/source headers and authored source-texture refs1..128.
    Distinct from render targets; no bulk pixel locks/platform build waits/regeneration/compatibility execution/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/inspect", json={
        "AssetPath": asset_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_texture_2d_array_address(asset_path: str, expected_class_path: str, field_name: str,
                                    expected_value: int, value: int, confirm: bool = False, dry_run: bool = True) -> str:
    """Set source-backed Texture2DArray AddressX/Y/Z0 Wrap1 Clamp2 Mirror with exact class/current guards.
    Preserves other address modes/source refs/header dimensions; native callback updates resources/may schedule builds.
    No explicit build/source regeneration/bulk pixels/render evaluation/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/address", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_loaded_texture_2d_arrays(path_substring: str = "", source_texture_path: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent source-backed texture arrays1..128/path substring/optional direct source-texture filter.
    Reports matching source indices<=128/total count, excludes unloaded arrays/embedded imported slices/indirect dependencies.
    Source headers only, no regeneration/compatibility calls/build waits/bulk pixels/render eval/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/inspect-page", json={
        "PathFilter": path_substring, "AssetPath": source_texture_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_source_volume_texture(asset_path: str) -> str:
    """Inspect source-backed VolumeTexture source headers/tiling/address and optional2D source reference.
    Simple tile divisibility is not native conversion/freshness proof; no bulk pixels/build waits/regeneration/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volume-textures/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_source_volume_texture_address(asset_path: str, expected_class_path: str, expected_value: int, value: int,
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Set source VolumeTexture tiling0 Wrap1 Clamp2 Mirror on all axes with exact class/current guard.
    Preserves2D source/tile sizes/source header; native NotifyMaterials may recompile dependent samplers.
    No explicit source regeneration/build/bulk pixels/render eval/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volume-textures/address", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_loaded_source_volume_textures(path_substring: str = "", source_texture_path: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent source-backed volume textures1..128/path substring/optional direct2D source filter.
    Source headers/tiling/address metadata; excludes unloaded/indirect dependencies and no freshness proof.
    No regeneration/bulk pixels/platform build waits/render evaluation/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volume-textures/inspect-page", json={
        "PathFilter": path_substring, "AssetPath": source_texture_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_source_texture_cube(asset_path: str) -> str:
    """Inspect source-backed TextureCube headers and available authored compression/mip/LOD/filter/long-lat fields.
    Source layout may differ from final faces, no platform getter/mip data/build waits/conversion/render eval/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cubes/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_loaded_source_texture_cubes(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent source-backed cube textures1..128/path substring, excludes cube render targets.
    Source headers may describe long-lat layout; no platform getter/build waits/read pixels/render eval/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cubes/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def reorder_texture_2d_array_sources(asset_path: str, expected_class_path: str, expected_source_paths: list[str],
                                         source_index_order: list[int], confirm: bool = False, dry_run: bool = True) -> str:
    """Reorder complete source-texture list1..128 by unique index permutation/full current paths/class guards.
    List-generated arrays only, loaded single-slice sources matching dimensions/format/gamma, texels<=16777216.
    Native callback regenerates combined source/resources, changes slice-index meaning without consumer remap.
    Source assets unchanged, no explicit build/readback/render eval/sync/load/save; dry-run does not regenerate.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/sources/reorder", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSourcePaths": expected_source_paths, "SourceOrder": source_index_order,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_texture_2d_array_sources(asset_path: str, expected_class_path: str, expected_source_paths: list[str],
                                     source_paths: list[str], confirm: bool = False, dry_run: bool = True) -> dict:
    """Replace list-generated array slices with 1..128 unique loaded compatible sources; native regeneration, unverified.

    Full prior ordered paths required, including None for null references. Slice indices change for all consumers.
    Empty replacement is rejected. Dry run does not regenerate or verify pixels; no load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/sources/replace", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSourcePaths": expected_source_paths, "SourcePaths": source_paths,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=120.0).json()


@mcp.tool()
def set_source_volume_texture_tiles(asset_path: str, expected_class_path: str, expected_source_path: str,
                                    expected_tile_xy: list[int], tile_xy: list[int],
                                    expected_source_xy: list[int], expected_source_format: int,
                                    confirm: bool = False, dry_run: bool = True) -> dict:
    """Set paired volume source tile sizes; native source regeneration, unverified.

    Exact source reference/header and previous tile dimensions required. Complete layout depth1..512,
    total texels<=16777216; no remainder cropping/depth truncation. Source asset is unchanged.
    """
    if len(expected_tile_xy) != 2 or len(tile_xy) != 2 or len(expected_source_xy) != 2:
        raise ValueError("expected_tile_xy, tile_xy and expected_source_xy must each contain two integers")
    return httpx.post(f"{app.BASE_URL}/volume-textures/tiles", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedTargetPath": expected_source_path,
        "ExpectedSizeX": expected_tile_xy[0], "ExpectedSizeY": expected_tile_xy[1],
        "SizeX": tile_xy[0], "SizeY": tile_xy[1],
        "ExpectedSourceSizeX": expected_source_xy[0], "ExpectedSourceSizeY": expected_source_xy[1],
        "ExpectedFormat": expected_source_format, "bConfirm": confirm, "bDryRun": dry_run}, timeout=120.0).json()


@mcp.tool()
def set_source_volume_texture_source(asset_path: str, expected_class_path: str, expected_source_path: str, source_texture_path: str,
                                    expected_tile_xy: list[int], tile_xy: list[int],
                                    expected_source_xy: list[int], expected_source_format: int,
                                    confirm: bool = False, dry_run: bool = True) -> dict:
    """Replace volume source reference and explicit paired tile sizes; native source regeneration, unverified.

    Exact previous source path/tiles and replacement source header required; prior None allowed.
    Native tile callback regenerates with explicit tiles, bypassing default tile-size heuristic. Complete layout depth1..512,
    total texels<=16777216; no remainder cropping/depth truncation. Source asset is unchanged.
    """
    if len(expected_tile_xy) != 2 or len(tile_xy) != 2 or len(expected_source_xy) != 2:
        raise ValueError("expected_tile_xy, tile_xy and expected_source_xy must each contain two integers")
    return httpx.post(f"{app.BASE_URL}/volume-textures/source", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedTargetPath": expected_source_path, "SourceTexturePath": source_texture_path,
        "ExpectedSizeX": expected_tile_xy[0], "ExpectedSizeY": expected_tile_xy[1],
        "SizeX": tile_xy[0], "SizeY": tile_xy[1],
        "ExpectedSourceSizeX": expected_source_xy[0], "ExpectedSourceSizeY": expected_source_xy[1],
        "ExpectedFormat": expected_source_format, "bConfirm": confirm, "bDryRun": dry_run}, timeout=120.0).json()


@mcp.tool()
def create_source_texture_2d_array(asset_path: str, source_paths: list[str],
                                   confirm: bool = False, dry_run: bool = True) -> dict:
    """Create source-backed Texture2DArray through native factory, unverified.

    New canonical /Game/Folder/Name.Name only; no overwrite. 1..128 unique loaded compatible
    single-slice source textures; total texels<=16777216. Native creation CVar must already be1.
    Factory regenerates combined source; no source edits/save/pixel readiness verification.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/create", json={
        "AssetPath": asset_path, "SourcePaths": source_paths,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180.0).json()


@mcp.tool()
def create_source_volume_texture(asset_path: str, source_texture_path: str = "", tile_xy: list[int] | None = None,
                                 expected_source_xy: list[int] | None = None, expected_source_format: int = -1,
                                 confirm: bool = False, dry_run: bool = True) -> dict:
    """Create source-backed volume via native factory, unverified. New /Game path only, no overwrite.

    Empty source creates native single BGRA8 texel. Optional loaded single-slice source requires header guards
    and explicit divisible tiles, depth1..512/texels<=16777216. Native regeneration/resources, no save.
    """
    payload = {"AssetPath": asset_path, "SourceTexturePath": source_texture_path,
               "bConfirm": confirm, "bDryRun": dry_run}
    if source_texture_path:
        if tile_xy is None or len(tile_xy) != 2 or expected_source_xy is None or len(expected_source_xy) != 2:
            raise ValueError("A source requires tile_xy and expected_source_xy pairs")
        payload.update({"SizeX": tile_xy[0], "SizeY": tile_xy[1],
                        "ExpectedSourceSizeX": expected_source_xy[0], "ExpectedSourceSizeY": expected_source_xy[1],
                        "ExpectedFormat": expected_source_format})
    return httpx.post(f"{app.BASE_URL}/volume-textures/create", json=payload, timeout=180.0).json()


@mcp.tool()
def inspect_source_texture_cube_array(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect loaded source-backed cube array headers and source-cube reference pages1..128, unverified.

    Source headers may describe long-lat or six-face data; not final GPU cube count or freshness proof.
    No platform-data getters/bulk pixels/regeneration/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cube-arrays/inspect", json={
        "AssetPath": asset_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_loaded_source_texture_cube_arrays(path_substring: str = "", source_cube_path: str = "",
                                              start: int = 0, count: int = 64) -> str:
    """Page loaded persistent cube arrays with optional exact direct source-cube reference filter, unverified.

    Path-sorted pages1..128; loaded direct references only, not complete dependency graph.
    Source headers only; no platform getter/build wait/regeneration/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cube-arrays/inspect-page", json={
        "PathFilter": path_substring, "AssetPath": source_cube_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def replace_source_texture_cube_array_sources(asset_path: str, expected_class_path: str,
                                               expected_source_paths: list[str], source_paths: list[str],
                                               confirm: bool = False, dry_run: bool = True) -> str:
    """Replace cube-array sources1..128 with exact previous ordered paths0..128, unverified.

    Loaded unique cubes must match source dimensions/slices1or6/format/gamma; texels<=16777216.
    Native regeneration waits for source builds; one cube resets compression/mips/LOD/sRGB/streaming.
    Consumer indices change, no remapping. Empty replacement rejected, no save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cube-arrays/sources/replace", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSourcePaths": expected_source_paths, "SourcePaths": source_paths,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def reorder_source_texture_cube_array_sources(asset_path: str, expected_class_path: str,
                                               expected_source_paths: list[str], source_index_order: list[int],
                                               confirm: bool = False, dry_run: bool = True) -> str:
    """Reorder cube-array sources by complete unique index permutation1..128, unverified.

    Same compatibility/prior-list guards and regeneration effects as replacement. Native source-build waits;
    slice meanings change for consumers, no remapping/save/pixel proof. Dry-run does not regenerate.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cube-arrays/sources/reorder", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSourcePaths": expected_source_paths, "SourceOrder": source_index_order,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def create_source_texture_cube_array(asset_path: str, source_cube_paths: list[str],
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Create source-backed cube array via native factory, unverified. New canonical /Game path, no overwrite.

    1..128 unique loaded persistent source cubes with matching dimensions/source slices1or6/format/gamma,
    total source texels<=16777216. Native regeneration waits for source builds; initial settings derive
    from first cube with no-mips/never-stream defaults. No source edits/save/pixel readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cube-arrays/create", json={
        "AssetPath": asset_path, "SourcePaths": source_cube_paths,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_texture_array_source_compatibility(asset_path: str) -> str:
    """Diagnose complete2D/cube array source-header policy for up to128 refs, unverified.

    Reports invalid/duplicate refs, dimensions/slice layout/format/gamma mismatches and texel budget.
    Stricter adapter policy only, not native compatibility or GPU freshness proof. No build waits,
    native compatibility call, bulk pixels, regeneration, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/source-compatibility/inspect", json={
        "AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_texture_source_mips(asset_path: str, block_index: int = 0, layer_index: int = 0,
                                start: int = 0, count: int = 16) -> str:
    """Inspect selected source block/layer mip header pages1..32, unverified.

    UDIM coordinates, mip dimensions/slices/native uncompressed source byte sizes. Volume depth shrinks;
    source layout is distinct from generated/cooked/resident GPU mips. No pixel reads/build waits/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/inspect", json={
        "AssetPath": asset_path, "BlockIndex": block_index, "LayerIndex": layer_index,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_texture_source_layout(asset_path: str, page_kind: str = "blocks", start: int = 0, count: int = 64) -> str:
    """Discover texture source blocks or layers in independent pages1..128, unverified.

    page_kind blocks: coordinates/dimensions/slices/mip count; layers: source format/gamma.
    Returns indices for source mip inspection. Source headers only, no bulk availability/GPU proof.
    No pixel reads/platform getter/build waits/regeneration/load/save.
    """
    if page_kind not in ("blocks", "layers"):
        raise ValueError("page_kind must be blocks or layers")
    return httpx.post(f"{app.BASE_URL}/textures/source-layout/inspect-page", json={
        "AssetPath": asset_path, "FieldName": page_kind, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_texture_source_identity(asset_path: str) -> str:
    """Inspect native source identifiers/payload metadata/image compression, unverified.

    IDs are not freshly computed pixel hashes or generated-data cache keys. Payload metadata does not
    prove bytes can load; image compression differs from bulk/platform compression. No pixel reads,
    platform getters/build waits/regeneration/load/save. Source-less textures report native defaults.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-identity/inspect", json={
        "AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_texture_streaming_state(asset_path: str) -> str:
    """Inspect copied native cached texture residency/requested LOD counts and policy, unverified.

    Cached resource LODs differ from source mip counts. Async hints/state are not GPU readiness proof;
    virtual streaming support is not tile residency. No streaming requests/polling/waits/platform getters/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/streaming-state/inspect", json={
        "AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def duplicate_source_texture(source_texture_path: str, asset_path: str, expected_class_path: str,
                              expected_source_id: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Duplicate native source texture through AssetTools with exact class/source attribute ID, unverified.

    New canonical /Game path, no overwrite. Native2D/cube/volume/2D-array/cube-array only.
    Copies native source/import metadata, retains external references/source-file paths; no recursive
    clone/file copy/consumer remapping/derived-data proof. No save; native resource callbacks may run.
    """
    return httpx.post(f"{app.BASE_URL}/textures/duplicate", json={
        "SourceTexturePath": source_texture_path, "AssetPath": asset_path,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_texture_expression_references(asset_path: str, expression_path_substring: str = "",
                                            start: int = 0, count: int = 64) -> str:
    """Page loaded asset-owned texture-base expression direct defaults1..128, unverified.

    Reports expression/owner/GUID/authored sampler type. Exact native source texture types also receive
    authored sampler-policy diagnostics from native compression/sRGB/desired VT checks; no shader-platform
    adaptation or graph resolution. Includes unused nodes, not effective shader usage/parameter evaluation.
    No material compile/texture load/build waits/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/textures/expression-references/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": expression_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_texture_brush_assets(asset_path: str, brush_path_substring: str = "",
                                  start: int = 0, count: int = 64) -> str:
    """Page loaded persistent SlateBrushAsset direct texture resources1..128, unverified.

    Authored brush dimensions/draw/tiling/mirroring/image type/margins, not actual UI layout or usage.
    Excludes inline widget/style brushes, name-only resources, material indirection and unloaded assets.
    No Slate resource creation/widget evaluation/texture load/build waits/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/textures/brush-assets/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": brush_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def create_texture_2d_without_source_file(asset_path: str, width: int = 256, height: int = 256,
                                          confirm: bool = False, dry_run: bool = True, rgba: list[int] | None = None) -> str:
    """Create native Texture2D without an image file, unverified. New canonical /Game path, no overwrite.

    Power-of-two dimensions1..4096. Full BGRA8 source mip chain filled with optional RGBA bytes(default opaque white),
    all authored mips initialized, no linear conversion/alpha forcing. Native defaults/resource callbacks; no save/pixel proof.
    """
    return httpx.post(f"{app.BASE_URL}/textures/create-2d", json={
        "AssetPath": asset_path, "Color": rgba or [], "SizeX": width, "SizeY": height,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_texture_virtual_policy(asset_path: str) -> str:
    """Inspect authored VT streaming/priority/prefetch/related LOD policy and native metadata, unverified.

    Desired policy differs from cached virtual support, neither proves project/platform/material compatibility
    or page residency. Runtime virtual textures separate. No conversion/material rewrites/build waits/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/virtual-policy/inspect", json={
        "AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_texture_virtual_policy(asset_path: str, expected_class_path: str, expected_source_id: str,
                                field_name: str, expected_value: int, value: int,
                                confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set authored VT prefetch/priority policy on existing VT2D texture, unverified.

    Fields VirtualTexturePrefetchMips0..255, bUseVirtualTextureStreamingPriority0or1,
    VirtualTextureStreamingPriority visible native enum (override already enabled). Exact source attribute ID
    and previous field guard. No VT conversion/material remap/save; native resource callbacks may run.
    """
    return httpx.post(f"{app.BASE_URL}/textures/virtual-policy/set", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_address(asset_path: str, expected_class_path: str, expected_source_id: str,
                           field_name: str, expected_value: int, value: int,
                           confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set native Texture2D AddressX/Y0 Wrap1 Clamp2 Mirror, unverified.

    Exact loaded class/current value/source attribute ID required. Native callbacks/readback preserve
    other axis/source headers. No pixel comparison/hardware sampling proof/load/save; callbacks may build.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/address", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_texture_2d_settings(asset_path: str) -> str:
    """Inspect authored native Texture2D address/filter/mip/LOD/compression/color/padding/VT policy, unverified.

    Present reflected fields/native text/editability/raw conditions/enum options and source header/attribute ID.
    Hidden/sentinel enum values are inspection only. No platform allocation/pixel proof/build waits/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/settings/inspect", json={
        "AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_texture_2d_filter(asset_path: str, expected_class_path: str, expected_source_id: str,
                          expected_value: int, value: int, confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set native Texture2D Filter visible enum with exact current/source ID guards, unverified.

    Enum options from settings inspection; Default follows texture group. Authored policy not effective
    material/hardware sampling proof. Preserves addresses/source headers; callbacks may build, no save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/filter", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": "Filter", "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_mip_policy(asset_path: str, expected_class_path: str, expected_source_id: str,
                              expected_value: int, value: int, confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set Texture2D MipGenSettings visible native enum, unverified; enum options from settings inspection.

    Exact class/current policy/source attribute ID. Preserves filter/addresses/source header mip count.
    Native callbacks may generate mips/resources; no generated mip/pixel/residency proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/mip-policy", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": "MipGenSettings", "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_lod_limit(asset_path: str, expected_class_path: str, expected_source_id: str,
                             field_name: str, expected_value: int, value: int,
                             confirm: bool = False, dry_run: bool = True, expected_asset_snapshot: str = "") -> str:
    """Set Texture2D LODBias -32..32/NumCinematicMipLevels0..32/MaxTextureSize0 or power-of-two1..16384.

    Exact class/current/source attribute-ID guards, unverified. Native group/platform clamping determines
    effective result; callbacks may build. Preserves sibling limits/mip policy/filter/addresses, no save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/lod-limit", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_processing_flag(asset_path: str, expected_class_path: str, expected_source_id: str,
                                   field_name: str, expected_value: bool, value: bool,
                                   confirm: bool = False, dry_run: bool = True,
                                   expected_asset_snapshot: str = "") -> str:
    """Set Texture2D bPreserveBorder/bFlipGreenChannel/bPadWithBorderColor with exact current/source guards, unverified.

    Border-color padding requires existing padding mode and retains fixed color.
    Optional full authored snapshot from settings inspection. Native processing callbacks may build;
    generated pixel result/normal-map convention not proven. Preserves sibling flags/mip/filter/addresses, no save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/processing-flag", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": field_name, "ExpectedValue": int(expected_value), "Value": int(value),
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_adjustment(asset_path: str, expected_class_path: str, expected_source_id: str,
                              field_name: str, expected_value: float, value: float,
                              confirm: bool = False, dry_run: bool = True,
                              expected_asset_snapshot: str = "") -> str:
    """Set native Texture2D non-destructive color-adjustment policy, unverified.

    AdjustBrightness/AdjustBrightnessCurve/AdjustVibrance/AdjustSaturation/AdjustRGBCurve/AdjustHue/
    AdjustMinAlpha/AdjustMaxAlpha. Curves0..16/vibrance0..1/hue0..360/others+-65504; inverted alpha allowed.
    Exact previous native float/source-ID/optional snapshot, native callbacks may build; no preview/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/adjustment", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_mip_load_policy(asset_path: str, expected_class_path: str, expected_source_id: str,
                                   expected_value: int, value: int, confirm: bool = False, dry_run: bool = True,
                                   expected_asset_snapshot: str = "") -> str:
    """Set Texture2D MipLoadOptions visible native scoped enum, unverified.

    Exact current/source-ID/optional authored snapshot. Preserves generation/filter/address/source headers.
    Default follows group/platform; authored policy not actual residency/IO proof, no streaming request/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/mip-load-policy", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": "MipLoadOptions", "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_padding_policy(asset_path: str, expected_class_path: str, expected_source_id: str,
                                  expected_value: int, value: int, confirm: bool = False, dry_run: bool = True,
                                  expected_asset_snapshot: str = "") -> str:
    """Set Texture2D PowerOfTwoMode visible native enum with source/current/snapshot guards, unverified.

    Source and existing explicit resize bounds<=4096; explicit modes use existing resize dimensions.
    Preserves padding color/border flag/resize dimensions/addresses. Native callbacks may build, no preview/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/2d/padding-policy", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "FieldName": "PowerOfTwoMode", "ExpectedValue": expected_value, "Value": value,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_build_resize(asset_path: str, expected_class_path: str, expected_source_id: str,
                                expected_xy: list[int], xy: list[int], confirm: bool = False, dry_run: bool = True,
                                expected_asset_snapshot: str = "") -> str:
    """Set paired Texture2D ResizeDuringBuildX/Y0..4096, zero uses source dimension, unverified.

    Existing ResizeToSpecificResolution mode, exact prior pair/source ID/optional snapshot required.
    Both fields assigned before one callback; policy dimensions not final platform output proof, no save.
    """
    if len(expected_xy) != 2 or len(xy) != 2:
        raise ValueError("expected_xy and xy must each contain two integers")
    return httpx.post(f"{app.BASE_URL}/textures/2d/build-resize", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedSizeX": expected_xy[0], "ExpectedSizeY": expected_xy[1], "SizeX": xy[0], "SizeY": xy[1],
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_texture_2d_padding_color(asset_path: str, expected_class_path: str, expected_source_id: str,
                                 expected_rgba: list[int], rgba: list[int], confirm: bool = False, dry_run: bool = True,
                                 expected_asset_snapshot: str = "") -> str:
    """Set authored Texture2D PaddingColor full RGBA bytes, unverified; no linear conversion.

    Existing padding mode/border-color padding disabled, full previous color/source-ID/optional snapshot.
    Native callback may build padded mips; no generated pixel/color-space proof/save.
    """
    if len(expected_rgba) != 4 or len(rgba) != 4:
        raise ValueError("expected_rgba and rgba must each contain four bytes")
    return httpx.post(f"{app.BASE_URL}/textures/2d/padding-color", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedColor": expected_rgba, "Color": rgba,
        "ExpectedAssetSnapshot": expected_asset_snapshot or "", "bRequireAssetSnapshot": expected_asset_snapshot != "",
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture(asset_path: str) -> str:
    """Inspect runtime virtual-texture authored policy/native clamped dimensions, unverified.

    Encoded tile fields differ from pixel sizes. Not streaming UTexture/page residency or scene bounds proof.
    No producer/resource initialization/material evaluation/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_loaded_runtime_virtual_textures(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent runtime virtual textures1..128 with native policy dimensions, unverified.
    No producer/resource allocation/material evaluation/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def create_runtime_virtual_texture(asset_path: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Create native runtime virtual-texture asset with native defaults, unverified.

    New canonical /Game/Folder/Name.Name only, no overwrite. Native editor factory resolved at execution;
    dry-run does not load module/probe availability. No scene volume/material binding/project toggle/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/create", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_policy(asset_path: str, expected_class_path: str, expected_asset_snapshot: str,
                                        field_name: str, expected_value: int, value: int,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Set runtime VT clear/page-table/update/priority override flags or RemoveLowMips0..5, unverified.

    Flags bClearTextures/bSinglePhysicalSpace/bPrivateSpace/bContinuousUpdate/bUseCustomPriority/bAdaptive/
    bCompressTextures/bUseLowQualityCompression0or1. Low-quality enable requires compression and native
    BaseColor_Normal_Roughness layout; disabling compression can retain inactive low-quality flag.
    Adaptive changes require current tile count fit requested native maximum, rejecting implicit truncation.
    Mandatory full authored snapshot from inspection. Native callback notifies components/primitives,
    may recreate resources. No output/page residency proof/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/policy", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bRequireAssetSnapshot": True,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_size(asset_path: str, expected_class_path: str, expected_asset_snapshot: str,
                                      field_name: str, expected_value: int, value: int,
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Set encoded RVT TileCount exponent/TileSize code/TileBorderSize code, unverified.

    Tile count1<<code within native adaptive limit; tile pixels1<<(code+6), border pixels2*code, latter codes0..4.
    Exact current/full authored snapshot required. Native notifications may recreate resources; no residency proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/size", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bRequireAssetSnapshot": True,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_priority(asset_path: str, expected_class_path: str, expected_asset_snapshot: str,
                                          expected_value: int, value: int,
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Set runtime VT CustomPriority visible scoped enum, existing override required, unverified.

    Exact previous value/full authored snapshot. Native notifications may recreate resources;
    no scheduling/latency/page residency guarantee, no automatic override enable/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/priority", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bRequireAssetSnapshot": True,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_components(asset_path: str, component_path_substring: str = "",
                                                start: int = 0, count: int = 64) -> str:
    """Page loaded RVT component direct asset references across worlds/templates/transients1..128, unverified.

    Exposes identity/world/registered/visible/dirty flags, not active producer/page proof. Excludes primitive
    writer lists/materials/builders/unloaded refs. No resource/builder evaluation/build/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": component_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_writers(asset_path: str, component_path_substring: str = "",
                                             start: int = 0, count: int = 64) -> str:
    """Page loaded primitive authored RuntimeVirtualTextures direct refs1..128, unverified.

    Across worlds/templates/transients; matching indices/count/main-pass policy. Native array only,
    not custom virtual overrides/material writing/volume intersection/page coverage proof. No build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/writers/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": component_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_layout(asset_path: str, expected_class_path: str, expected_asset_snapshot: str,
                                        field_name: str, expected_value: int, value: int,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Set RVT MaterialType or LODGroup visible enum with exact current/full snapshot, unverified.

    MaterialType changes layer layout and can mismatch writers/samplers; no material migration/compatibility proof.
    Inactive low-quality compression flag retained. Native notifications/resources may run, no compile/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/layout", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bRequireAssetSnapshot": True,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_expressions(asset_path: str, expression_path_substring: str = "",
                                                 start: int = 0, count: int = 64) -> str:
    """Page loaded asset-owned RVT sample expression direct refs1..128 and authored flag comparisons, unverified.

    Includes derived parameter/unused nodes. Material-type/packed/adaptive matches are not full shader
    compatibility/effective override proof. No validation/init-dependent-settings/compile/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/expressions/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": expression_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_overrides(asset_path: str, material_path_substring: str = "",
                                               start: int = 0, count: int = 64) -> str:
    """Page loaded persistent material-instance authored direct RVT overrides1..128, unverified.

    Parameter association/layer index/GUID, not effective inherited values/shader usage or sample layout
    compatibility. Stale overrides may appear, dynamic/unloaded refs excluded. No evaluation/compile/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/material-overrides/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": material_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_virtual_texture_builder(asset_path: str) -> str:
    """Inspect loaded streaming runtime-VT builder flags/hash/desktop-mobile embedded refs, unverified.

    uint64 build hash decimal string, not recomputed freshness proof. Authored refs/source headers are
    not shading-path fallback/platform VT/page residency proof. No BuildTexture/platform getter/waits/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/virtual-texture-builders/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_loaded_virtual_texture_builders(path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Page loaded persistent VT builders1..128/hash/authored embedded refs, unverified.
    No freshness/platform fallback proof/BuildTexture/platform getter/streaming status/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/virtual-texture-builders/inspect-page", json={
        "PathFilter": path_substring, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_virtual_texture_builder_components(asset_path: str, component_path_substring: str = "",
                                                start: int = 0, count: int = 64) -> str:
    """Page loaded RVT component direct streaming-builder refs across worlds/templates/transients, unverified.
    Includes assigned runtime VT path, not builder/hash/layout/shading-path compatibility proof. No build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/virtual-texture-builders/components/inspect-page", json={
        "AssetPath": asset_path, "PathFilter": component_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_virtual_texture_builder_mobile_policy(asset_path: str, expected_class_path: str, expected_build_hash: str,
                                               expected_texture_paths: list[str], expected_value: bool, value: bool,
                                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set builder separate-mobile bool with exact hash/desktop-mobile refs/current guard, unverified.

    Native mobile VT setting already enabled, no project changes. Embedded textures retained, no build;
    enabling can select absent/stale mobile data; later BuildTexture may clear mobile ref when disabled.
    """
    if len(expected_texture_paths) != 2:
        raise ValueError("expected_texture_paths must contain desktop and mobile paths, None strings for absent")
    return httpx.post(f"{app.BASE_URL}/virtual-texture-builders/mobile-policy", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_build_hash,
        "ExpectedSourcePaths": expected_texture_paths, "ExpectedValue": int(expected_value), "Value": int(value),
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def create_virtual_texture_builder(asset_path: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Create native empty streaming runtime-VT builder container, unverified. New /Game path, no overwrite.

    Native editor factory resolved at execution; dry-run does not probe module. No embedded VT generation,
    component association/capture/BuildTexture/save; empty container is not built streaming texture data.
    """
    return httpx.post(f"{app.BASE_URL}/virtual-texture-builders/create", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_layers(asset_path: str) -> str:
    """Inspect native RVT layer count/policy pixel formats/sRGB/YCoCg sampling, unverified.

    Current native platform format selection, not arbitrary cook target/allocated producer readback.
    No material graph compatibility/page residency proof/render-thread resource getters/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/layers/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_component_settings(actor_path: str, component_path: str) -> str:
    """Inspect current-world RVT component authored bounds/scalability/streaming policies, unverified.

    Exact owner path, native text/editability/enum metadata and asset-builder refs. Soft actor refs not loaded.
    No bounds alignment/effective policy/status/build/Invalidate/producer init/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/settings/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_component_flag(actor_path: str, component_path: str, expected_class_path: str,
                                                actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                field_name: str, expected_value: bool, value: bool,
                                                confirm: bool = False, dry_run: bool = True) -> str:
    """Set current-world RVT component bool with actor identity/full snapshot guards, unverified.

    bSnapBoundsToLandscape/bEnableForNaniteOnly/bUseMinMaterialQuality/bEnableScalability/bHidePrimitives/
    bUseStreamingMipsFixedColor/bUseStreamingMipsOnly. Native callbacks may reconstruct resources/components;
    snap does not align bounds, fixed-color does not build. No asset edit/save/evaluation.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/flag", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": field_name, "ExpectedValue": int(expected_value), "Value": int(value),
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_runtime_virtual_texture_component_numeric(actor_path: str, component_path: str, expected_class_path: str,
                                                   actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                   field_name: str, expected_value: float, value: float,
                                                   confirm: bool = False, dry_run: bool = True) -> str:
    """Set RVT component ExpandBounds0..1000000/StreamLowMips0..12/ScalabilityGroup0..2, unverified.

    Group requires scalability enabled. Exact native previous value/actor identity/full snapshot.
    No bounds alignment/low-mip build/effective scalability proof; callbacks may reconstruct resources, no save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/numeric", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_runtime_virtual_texture_component_enum(actor_path: str, component_path: str, expected_class_path: str,
                                                actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                field_name: str, expected_value: int, value: int,
                                                confirm: bool = False, dry_run: bool = True) -> str:
    """Set RVT component MinInGameMaterialQuality/LossyCompressionAmount/UseStreamingMipsInEditorMode, unverified.

    Visible enum/exact prior/actor/full snapshot guards. Quality override already enabled; native editability
    gates streaming mode. Compression is later-build policy, no build/validity/effective policy proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/enum", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_component_fixed_color(actor_path: str, component_path: str, expected_class_path: str,
                                                       actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                       expected_rgba: list[float], rgba: list[float],
                                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Set RVT component fixed streaming-mip linear RGBA+-65504, enabled policy required, unverified.

    Exact full previous native floats/actor/full snapshot. Affects later BaseColor/Displacement build,
    red for displacement; alpha retained. No immediate texture edit/build/output proof/save.
    """
    if len(expected_rgba) != 4 or len(rgba) != 4:
        raise ValueError("expected_rgba and rgba must each contain four numbers")
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/fixed-color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "ExpectedColor": expected_rgba, "Color": rgba, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_component_reference(actor_path: str, component_path: str, expected_class_path: str,
                                                     actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                     field_name: str, expected_target_path: str, asset_path: str = "",
                                                     confirm: bool = False, dry_run: bool = True) -> str:
    """Assign RVT component VirtualTexture/StreamingTexture loaded asset or empty clear, unverified.

    Exact previous path (None absent)/actor/full snapshot. Native setters/callbacks preserve other ref/transform;
    other ref can become incompatible, no migration/build-hash validation/build/save or asset edits.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/reference", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": field_name, "ExpectedTargetPath": expected_target_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_bounds_actor(actor_path: str, component_path: str, expected_class_path: str,
                                              actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                              expected_bounds_actor_path: str, bounds_actor_path: str = "",
                                              confirm: bool = False, dry_run: bool = True) -> str:
    """Assign loaded same-world RVT bounds alignment actor soft ref or empty clear, unverified.

    Exact prior soft path (empty absent)/owner identity/full snapshot. Existing unresolved path not loaded.
    Target unchanged; no bounds calculation/snap/movement/attachment/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/bounds-actor", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "ExpectedTargetPath": expected_bounds_actor_path, "AssetPath": bounds_actor_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_component_platform(actor_path: str, component_path: str, expected_class_path: str,
                                                    actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                    operation: str, platform_key: str = "", expected_value: bool = False,
                                                    value: bool = False, confirm: bool = False, dry_run: bool = True) -> str:
    """Edit RVT component EnableInGamePerPlatform Default/Override/RemoveOverride, unverified.

    Default requires empty key; Override upserts named platform/group, RemoveOverride requires existing key.
    Exact actor/full snapshot/current selected value, map insertion cap128. Keys syntax only, not installed
    target or effective runtime precedence proof. No producer init/build/evaluation/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/platform-enable", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": operation, "Name": platform_key, "ExpectedValue": int(expected_value), "Value": int(value),
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_component_platforms(actor_path: str, component_path: str,
                                                         start: int = 0, count: int = 64) -> str:
    """Page current-world RVT component authored enable overrides1..128/key-sorted, unverified.

    Default bool/full component snapshot. Keys platform or group, not effective runtime precedence proof;
    complete map discoverable without generic text truncation. No build/resource evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/platform-enable/inspect-page", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_writer_settings(actor_path: str, component_path: str) -> str:
    """Inspect current-world primitive authored RVT writer list/LOD-culling/main-pass policy, unverified.

    Exact owner/native fields/metadata/full supported snapshot, list<=128 with None null refs.
    Custom overrides/material output/volume intersection/render culling not evaluated. No build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/writers/settings/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_writer_numeric(actor_path: str, component_path: str, expected_class_path: str,
                                                actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                field_name: str, expected_value: int, value: int,
                                                confirm: bool = False, dry_run: bool = True) -> str:
    """Set primitive RVT VirtualTextureLodBias -7..8/CullMips0..7/MinCoverage0..7, unverified.

    Exact prior signed-byte/actor/full writer snapshot, list<=128. Native callback may recreate render state;
    custom overrides/material output/culling effectiveness not evaluated. No asset edits/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/writers/numeric", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_writer_main_pass(actor_path: str, component_path: str, expected_class_path: str,
                                                  actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                  expected_value: int, value: int,
                                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Set primitive VirtualTextureRenderPassType visible enum with actor/writer snapshot guards, unverified.

    Preserves writer list/LOD-culling/transform. Main-pass visibility also depends on volume/material policy;
    native callback may reconstruct render state, no effective output/page proof/asset edits/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/writers/main-pass", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": "VirtualTextureRenderPassType", "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_writer_list(actor_path: str, component_path: str, expected_class_path: str,
                                             actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                             expected_paths: list[str], paths: list[str],
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Replace primitive authored RVT writer destinations0..128, empty clears, unverified.

    Exact ordered previous paths(None null)/actor/full writer snapshot. Unique loaded persistent new assets,
    native callback preserves LOD/culling/main-pass/transform. No material migration/volume binding/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/writers/list", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "ExpectedSourcePaths": expected_paths, "SourcePaths": paths, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def discover_runtime_virtual_texture_components(actor_path: str = "", runtime_texture_path: str = "",
                                                 component_path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Discover current-world persistent RVT components including unassigned ones1..128, unverified.

    Optional actor/asset exact filters, empty asset means all/None matches unassigned. References not loaded.
    Identity/GUID-label/asset-builder refs/flags, not producer/page proof. No build/evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/discover", json={
        "ActorPath": actor_path, "AssetPath": runtime_texture_path, "PathFilter": component_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def discover_runtime_virtual_texture_writers(actor_path: str = "", runtime_texture_path: str = "",
                                              component_path_substring: str = "", start: int = 0, count: int = 64) -> str:
    """Discover current-world primitive authored RVT writers including empty destination lists, unverified.

    Optional owner/direct asset filters, empty asset all/None only empty list (not null-filled).
    Native LOD/culling/main-pass/ref count, not custom override/material writing proof. No build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/writers/discover", json={
        "ActorPath": actor_path, "AssetPath": runtime_texture_path, "PathFilter": component_path_substring,
        "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def duplicate_runtime_virtual_texture(source_asset_path: str, asset_path: str, expected_class_path: str,
                                       expected_asset_snapshot: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Duplicate native RVT authored asset through AssetTools/full snapshot guard, unverified.

    New canonical /Game path/no overwrite. No scene/material reference remap, streaming builder/generated data
    cloning or producer-state guarantee. Source unchanged, no explicit producer init/build/evaluation/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/duplicate", json={
        "SourceTexturePath": source_asset_path, "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def create_runtime_virtual_texture_volume(world_path: str, name: str, location: list[float],
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Spawn native RVT volume/root component at location in ordinary unlocked persistent map, unverified.

    Unique name, zero rotation/unit scale/native defaults. Unit volume, no auto bounds alignment or asset/
    builder/material assignment. Registration may create resources; no page coverage proof/build/save.
    """
    if len(location) != 3:
        raise ValueError("location must contain three coordinates")
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/volumes/create", json={
        "WorldPath": world_path, "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def delete_runtime_virtual_texture_volume(world_path: str, actor_path: str, component_path: str,
                                           expected_class_path: str, actor_guid: str, expected_label: str,
                                           expected_asset_snapshot: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Delete exact native RVT volume/root in ordinary unlocked persistent map, unverified.

    Actor GUID-label/full component snapshot/no attached actors or nonnative components required.
    Native visualization removed, RVT/builder assets retained, external refs not repaired. No build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/volumes/delete", json={
        "WorldPath": world_path, "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedClassPath": expected_class_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_volume_transform(actor_path: str, component_path: str, expected_class_path: str,
                                                  actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                  expected_transform: dict, transform: dict,
                                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Set exact native unattached RVT volume world transform, full identity/settings/prior guards, unverified.

    Normalized quaternion/location+-1e9/positive scale0.001..1000000; unit volume local0..1 scales extent.
    Native no-sweep teleport/children follow, no landscape snap/bounds alignment/construction/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/volumes/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "ExpectedTransform": expected_transform, "Transform": transform,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_bounds_contributors(actor_path: str, component_path: str,
                                                         start: int = 0, count: int = 64) -> str:
    """Inspect primitive selection used by native RVT bounds alignment across loaded worlds, unverified.

    Alignment actor owner or virtual writer getter match, cached bounds/flags/cross-world count.
    Getter may run custom code. No native CalcBounds/landscape-complete bounds/final transform/snap calculation,
    SetBounds/PostEditMove/build/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/bounds-contributors/inspect-page", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def align_runtime_virtual_texture_bounds(actor_path: str, component_path: str, expected_class_path: str,
                                           actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                           expected_runtime_texture_snapshot: str, expected_transform: dict,
                                           expected_contributor_paths: list[str], confirm: bool = False, dry_run: bool = True) -> str:
    """Align native RVT volume with native SetBounds/landscape snap, unverified.

    Full component/asset snapshots/prior transform/complete sorted contributor list<=256. Cross-world/
    template/transient matches rejected. Dry-run CalcBounds preflight, no SetBounds/final snapped prediction.
    Native SetActorTransform/PostEditMove can reconstruct resources; no coverage/build/save proof.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/volumes/align-bounds", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "ExpectedRuntimeTextureSnapshot": expected_runtime_texture_snapshot, "ExpectedTransform": expected_transform,
        "ExpectedComponentPaths": expected_contributor_paths, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def build_runtime_virtual_texture_streaming_mips(actor_path: str, component_path: str, expected_class_path: str,
                                                  actor_guid: str, expected_label: str, expected_asset_snapshot: str,
                                                  expected_runtime_texture_snapshot: str, expected_transform: dict,
                                                  expected_build_hash: str, expected_texture_paths: list[str],
                                                  expected_builder_consumer_paths: list[str],
                                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Build one RVT component streaming mips for native supported paths, unverified; no explicit save.

    Full identity/component-asset snapshots/builder hash-refs/transform/sorted consumers required.
    Native operation flushes streaming/compilation, renders-reads tiles, replaces embedded data and may
    switch feature levels/show cancelable UI. Partial failure possible, not undoable guarantee. Dry-run no build.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/build-streaming-mips", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "ExpectedRuntimeTextureSnapshot": expected_runtime_texture_snapshot, "ExpectedTransform": expected_transform,
        "ExpectedSourceId": expected_build_hash, "ExpectedSourcePaths": expected_texture_paths,
        "ExpectedComponentPaths": expected_builder_consumer_paths, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_runtime_virtual_texture_streaming_status(actor_path: str, component_path: str, confirm: bool = False) -> str:
    """Explicit native RVT streaming settings/format status for deferred/mobile, unverified.

    Requires confirmation because native check may access platform data/wait for generated compilation.
    Flags distinguish missing refs/generated textures/settings-format mismatch, not scene pixel freshness/page
    residency/cook-platform proof. No build request/capture/BuildTexture/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/components/streaming-status", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bConfirm": confirm}, timeout=1800).text


@mcp.tool()
def synchronize_runtime_virtual_texture_sample(expression_path: str, owner_asset_path: str, expected_class_path: str,
                                                expression_guid: str, runtime_texture_path: str,
                                                expected_runtime_texture_snapshot: str, expected_type_packed_adaptive: list[int],
                                                confirm: bool = False, dry_run: bool = True) -> str:
    """Synchronize native RVT sample type/packed/adaptive flags from assigned asset, unverified.

    Exact expression GUID/class/current material-function collection membership/prior3/asset snapshot.
    Native expression-owner notifications may compile materials/resources, no success wait/proof/save.
    Does not migrate other nodes/instance overrides or rewire graph.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/expressions/synchronize", json={
        "ExpressionPath": expression_path, "OwnerAssetPath": owner_asset_path, "ExpectedClassPath": expected_class_path,
        "ExpressionGuid": expression_guid, "AssetPath": runtime_texture_path,
        "ExpectedRuntimeTextureSnapshot": expected_runtime_texture_snapshot, "ExpectedChannels": expected_type_packed_adaptive,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_sample_reference(expression_path: str, owner_asset_path: str, expected_class_path: str,
                                                  expression_guid: str, expected_target_path: str,
                                                  expected_type_packed_adaptive: list[int], runtime_texture_path: str = "",
                                                  expected_runtime_texture_snapshot: str = "",
                                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Assign RVT sample loaded asset/empty clear with exact prior ref/3flags/GUID/membership, unverified.

    Requested asset full snapshot required. Native callback synchronizes layout flags; clearing retains flags.
    Owner notifications may compile resources, no other node/override migration/compile proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/expressions/reference", json={
        "ExpressionPath": expression_path, "OwnerAssetPath": owner_asset_path, "ExpectedClassPath": expected_class_path,
        "ExpressionGuid": expression_guid, "ExpectedTargetPath": expected_target_path, "AssetPath": runtime_texture_path,
        "ExpectedRuntimeTextureSnapshot": expected_runtime_texture_snapshot, "ExpectedChannels": expected_type_packed_adaptive,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_sample(expression_path: str, owner_asset_path: str) -> str:
    """Inspect individual loaded RVT sample/parameter expression including unassigned refs, unverified.

    Node GUID/current collection membership/prior type-packed-adaptive/optional parameter GUID/settings/enum
    metadata. No graph input/instance override evaluation/shader validation/compile/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/expressions/inspect", json={
        "ExpressionPath": expression_path, "OwnerAssetPath": owner_asset_path}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_sample_policy(expression_path: str, owner_asset_path: str, expected_class_path: str,
                                               expression_guid: str, expected_asset_snapshot: str, field_name: str,
                                               expected_value: int, value: int, confirm: bool = False, dry_run: bool = True) -> str:
    """Set RVT sample position-origin/address/mip enums or bEnableFeedback0or1, unverified.

    Exact GUID/current member/value/full sample snapshot. Native origin/mip callbacks may reconstruct pins,
    owner notifications may compile resources; links/compile not verified. Disabling feedback can harm residency.
    No explicit compile/wait/build/render/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/expressions/policy", json={
        "ExpressionPath": expression_path, "OwnerAssetPath": owner_asset_path, "ExpectedClassPath": expected_class_path,
        "ExpressionGuid": expression_guid, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_instance_parameters(material_instance_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect instance authored RVT override pages1..128/list<=256/full ordered parent-override snapshot, unverified.

    Parameter association/layer index/parameter GUID/value refs, including stale/null entries. No inherited
    declarations/effective overrides/sample-layout compatibility resolution/compile/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/instance-parameters/inspect-page", json={
        "OwnerAssetPath": material_instance_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_runtime_virtual_texture_instance_parameter(material_instance_path: str, expected_class_path: str,
                                                    expected_override_snapshot: str, override_index: int,
                                                    parameter_guid: str, expected_target_path: str, runtime_texture_path: str,
                                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Set existing declared material-instance-constant RVT override through native setter, unverified.

    Exact full override snapshot/index/parameter GUID/prior ref/unique identity. Nonnull loaded VT only;
    native setter does not clear null. Sibling refs preserved, no sample layout migration/compile proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/instance-parameters/set", json={
        "OwnerAssetPath": material_instance_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_override_snapshot, "Start": override_index, "ExpressionGuid": parameter_guid,
        "ExpectedTargetPath": expected_target_path, "AssetPath": runtime_texture_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_parameter_declarations(material_instance_path: str, start: int = 0, count: int = 64) -> str:
    """Page native inherited RVT parameter declarations/name-association-layer-GUID and local override indices, unverified.

    Sorted pages1..128/declarations<=4096/local overrides<=256. No effective value/shader usage/static branch
    or sample layout proof; native hierarchy metadata traversal only, no explicit parent load/compile/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/instance-parameters/declarations/inspect-page", json={
        "OwnerAssetPath": material_instance_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def create_runtime_virtual_texture_instance_override(material_instance_path: str, expected_class_path: str,
                                                       expected_override_snapshot: str, native_declaration_index: int,
                                                       parameter_name: str, association: int, layer_index: int,
                                                       parameter_guid: str, runtime_texture_path: str,
                                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Create absent local material-instance RVT override through native setter, unverified.

    Exact native declaration index/GUID/name/association/layer and full override snapshot; nonnull loaded VT.
    Native setter/new GUID lifecycle preserved, existing siblings read back. No inherited value edit/compile proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/instance-parameters/create", json={
        "OwnerAssetPath": material_instance_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_override_snapshot, "Start": native_declaration_index,
        "Name": parameter_name, "ParameterAssociation": association, "ParameterIndex": layer_index,
        "ExpressionGuid": parameter_guid, "AssetPath": runtime_texture_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def remove_runtime_virtual_texture_instance_override(material_instance_path: str, expected_class_path: str,
                                                       expected_override_snapshot: str, override_index: int,
                                                       parameter_guid: str, expected_target_path: str,
                                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Remove one local material-instance RVT override via native array notifications, unverified.

    Exact snapshot/index/GUID/prior ref/unique identity. Stale declarations allowed for cleanup;
    parent fallback not evaluated, siblings/assets retained. Native recache/compile/VT flush may run, no save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/instance-parameters/remove", json={
        "OwnerAssetPath": material_instance_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_override_snapshot, "Start": override_index,
        "ExpressionGuid": parameter_guid, "ExpectedTargetPath": expected_target_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_runtime_virtual_texture_effective_parameters(material_instance_path: str, start: int = 0, count: int = 64) -> str:
    """Page declared RVT params/native inherited effective values/local override indices, unverified.

    Loaded acyclic parent hierarchy<=64, declarations<=4096/local overrides<=256. Found flag distinct from
    null value, no exact ancestor/shader-use/layout proof. No explicit asset loads/compile/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/runtime-virtual-textures/instance-parameters/effective/inspect-page", json={
        "OwnerAssetPath": material_instance_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def create_texture_cube_without_source_file(asset_path: str, face_size: int = 256,
                                            confirm: bool = False, dry_run: bool = True, rgba: list[int] | None = None) -> str:
    """Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create native source-backed TextureCube without image file, opaque-white six faces/all source mips, unverified.

    New canonical /Game path/no overwrite/power-of-two square face size1..1024. Native source mip locks,
    registry/editor callbacks/resources may run; no generated GPU output/creation undo proof/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cubes/create", json={
        "AssetPath": asset_path, "Color": rgba or [], "SizeX": face_size, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def create_volume_texture_without_source_file(asset_path: str, width: int = 32, height: int = 32, depth: int = 32,
                                              confirm: bool = False, dry_run: bool = True, rgba: list[int] | None = None) -> str:
    """Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create native opaque-white BGRA8 source-backed volume without image/atlas, unverified.

    New canonical /Game path/no overwrite/XYZ1..256/voxels<=16777216, one source mip.
    Native volume factory mip-streaming policy, source locks/registry/callbacks; no GPU proof/build wait/save.
    """
    return httpx.post(f"{app.BASE_URL}/volume-textures/create-solid", json={
        "AssetPath": asset_path, "Color": rgba or [], "SizeX": width, "SizeY": height, "SizeZ": depth,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def create_texture_2d_array_without_source_file(asset_path: str, width: int = 256, height: int = 256, slices: int = 4,
                                                confirm: bool = False, dry_run: bool = True, rgba: list[int] | None = None) -> str:
    """Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create opaque-white direct-source Texture2DArray without image/per-slice assets, unverified.

    New /Game path/no overwrite/XY1..2048/slices1..128/texels<=16777216, one BGRA8 source mip.
    SourceTextures empty/list authoring disabled; no per-slice assets created. Native locks/callbacks, no build wait/save.
    """
    return httpx.post(f"{app.BASE_URL}/texture-arrays/create-solid", json={
        "AssetPath": asset_path, "Color": rgba or [], "SizeX": width, "SizeY": height, "SizeZ": slices,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def create_texture_cube_array_without_source_file(asset_path: str, face_size: int = 128, cube_count: int = 4,
                                                  confirm: bool = False, dry_run: bool = True, rgba: list[int] | None = None) -> str:
    """Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create opaque-white direct-source TextureCubeArray without image/per-cube assets, unverified.

    New /Game path/no overwrite/power-of-two face1..1024/cubes1..128/face texels<=16777216.
    One BGRA8 source mip/six slices per cube/non-long-lat/list authoring disabled, no GPU/build wait/save proof.
    """
    return httpx.post(f"{app.BASE_URL}/texture-cube-arrays/create-solid", json={
        "AssetPath": asset_path, "Color": rgba or [], "SizeX": face_size, "SizeY": face_size, "SizeZ": cube_count,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_render_target_conversion(render_target_path: str) -> str:
    """Inspect native2D/cube/volume/array render-target conversion policy/class/formats, unverified.
    No pixel read/resource readiness/capture freshness proof/ConstructTexture/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/conversion/inspect", json={"SourceTexturePath": render_target_path}, timeout=180).text


@mcp.tool()
def convert_render_target_to_texture(render_target_path: str, asset_path: str, expected_class_path: str,
                                      expected_asset_snapshot: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Native target-to-new-texture conversion with GPU readback/possible render-thread waits, unverified.

    Exact2D/cube/volume/array target class/full snapshot/new /Game path/no overwrite/XY<=2048/texels<=16777216.
    Native default compression-sRGB/gamma, no alpha override/capture flush. Dry-run policy only, no save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/conversion/create-texture", json={
        "SourceTexturePath": render_target_path, "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def update_texture_from_render_target(render_target_path: str, texture_path: str, expected_class_path: str,
                                        expected_target_snapshot: str, expected_destination_snapshot: str,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Native render-target readback into existing texture source with full snapshots, unverified.

    Exact native counterparts/XY<=2048/texels<=16777216; linked array/atlas destinations rejected.
    Native pixel comparison/change delegate/transaction; compression-sRGB may change. External import file
    unchanged, later reimport may replace contents. Dry-run no pixels/change prediction; no explicit save.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/conversion/update-texture", json={
        "SourceTexturePath": render_target_path, "AssetPath": texture_path, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_target_snapshot, "ExpectedDestinationSnapshot": expected_destination_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def fill_texture_source_mip(asset_path: str, expected_class_path: str, expected_source_id: str,
                            expected_asset_snapshot: str, mip_index: int, rgba: list[int],
                            confirm: bool = False, dry_run: bool = True) -> str:
    """Overwrite selected authored BGRA8 source mip/all slices with RGBA bytes, unverified.

    Exact native subtype/source ID/full snapshot/single block-layer/texels<=16777216. Linked list/atlas textures
    rejected. Other mips not adapter-regenerated; native policy may ignore lower source mips. No pixel no-op
    comparison, source identity may change, external import file untouched. Native callbacks may build, no save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/fill", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "Start": mip_index, "Color": rgba,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_texture_source_pixels(asset_path: str, expected_source_id: str, mip_index: int = 0,
                                   block_index: int = 0, layer_index: int = 0, start: int = 0, count: int = 64,
                                   confirm: bool = False) -> str:
    """Explicit native BGRA8 source mip decode/pixel pages1..128, unverified; source-ID guard.

    Full selected mip<=16777216 texels decoded per request, payload may load/decompress from disk/cache.
    Reports RGBA bytes/X-Y-slice without gamma conversion, not generated/GPU pixels. No build/source edit/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/pixels/inspect-page", json={
        "AssetPath": asset_path, "ExpectedSourceId": expected_source_id, "MipIndex": mip_index,
        "BlockIndex": block_index, "LayerIndex": layer_index, "Start": start, "Count": count,
        "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def patch_texture_source_mip(asset_path: str, expected_class_path: str, expected_source_id: str,
                              expected_asset_snapshot: str, mip_index: int, start_pixel: int,
                              expected_rgba_bytes: list[int], rgba_bytes: list[int],
                              confirm: bool = False, dry_run: bool = True) -> str:
    """Patch contiguous authored BGRA8 source mip1..128 pixels with exact prior RGBA bytes, unverified.

    Full selected mip decoded even dry-run for prior/no-op guards, may load bulk disk-cache. Native class/source-ID/
    snapshot/single block-layer, linked atlas/list rejected. Outside range retained, no explicit build/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/pixels/patch", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "MipIndex": mip_index, "Start": start_pixel,
        "ExpectedPixelBytes": expected_rgba_bytes, "PixelBytes": rgba_bytes,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_texture_source_mip_statistics(asset_path: str, expected_source_id: str, mip_index: int = 0,
                                           block_index: int = 0, layer_index: int = 0, confirm: bool = False) -> str:
    """Decode selected BGRA8 source mip for byte-channel statistics/alpha coverage-histogram, unverified.

    Explicit confirmation/source ID/mip<=16777216 texels, full bulk decode/disk-cache load/CPU scan.
    Min-max/mean/population stddev without gamma conversion, not generated compression/GPU proof. No build/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/statistics", json={
        "AssetPath": asset_path, "ExpectedSourceId": expected_source_id, "MipIndex": mip_index,
        "BlockIndex": block_index, "LayerIndex": layer_index, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def compare_texture_source_mips(texture_a: str, texture_b: str, expected_source_id_a: str, expected_source_id_b: str,
                                 mip_index: int = 0, confirm: bool = False) -> str:
    """Compare native BGRA8 selected source mips/exact IDs/matching layout, unverified.

    Each mip<=16777216 texels, two full decoded buffers/disk-cache load/CPU scan. Exact differing pixels/first
    index/RGBA max-mean absolute/RMS byte errors. No gamma/perceptual/cube-face matching/generated GPU proof/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/compare", json={
        "AssetPath": texture_a, "SourceTexturePath": texture_b, "ExpectedSourceId": expected_source_id_a,
        "ExpectedOtherSourceId": expected_source_id_b, "MipIndex": mip_index, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def copy_texture_source_mip(source_texture_path: str, destination_texture_path: str,
                             expected_source_id: str, expected_destination_source_id: str,
                             expected_destination_class: str, expected_destination_snapshot: str,
                             source_mip_index: int = 0, destination_mip_index: int = 0,
                             confirm: bool = False, dry_run: bool = True) -> str:
    """Copy compatible authored BGRA8 source mip/all slices with exact identities/snapshot, unverified.

    Single block-layer/matching mip dimensions-slices/<=16777216 texels, linked atlas-list destination rejected.
    Full two-mip decode/no-op compare even dry-run; other mips retained, no resample/gamma conversion/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/copy", json={
        "SourceTexturePath": source_texture_path, "AssetPath": destination_texture_path,
        "ExpectedOtherSourceId": expected_source_id, "ExpectedSourceId": expected_destination_source_id,
        "ExpectedClassPath": expected_destination_class, "ExpectedAssetSnapshot": expected_destination_snapshot,
        "MipIndex": source_mip_index, "Start": destination_mip_index,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def validate_texture_source_mip_payloads(asset_path: str, expected_source_id: str, block_index: int = 0,
                                         layer_index: int = 0, confirm: bool = False) -> str:
    """Native decode/size validation for all source mips in selected block-layer, unverified.

    Exact source ID/mips1..32/cumulative returned decoded64MiB; any native source format. Bulk may load/decompress,
    internal payload allocation may exceed returned budget. Per-mip failures/SHA1 decoded-byte fingerprints
    (not security/authenticity proof, excludes dimensions-format-gamma), no pixel semantics/full-chain/
    external-file/generated GPU proof. No source edit/platform getter/build/render/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/validate-payloads", json={
        "AssetPath": asset_path, "ExpectedSourceId": expected_source_id, "BlockIndex": block_index,
        "LayerIndex": layer_index, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def inspect_texture_source_linear_pixels(asset_path: str, expected_source_id: str, mip_index: int = 0,
                                          block_index: int = 0, layer_index: int = 0, start: int = 0, count: int = 64,
                                          confirm: bool = False) -> str:
    """Native source grayscale/float/HDR image decode and gamma-to-linear pixel pages1..128, unverified.

    Exact source-ID/decoded64MiB, payload may load/decompress. Native ImageCore interpretation, no custom
    encoding/profile/normal semantics. Nonfinite channels null/finite flag, HDR unclamped. No GPU/build/save proof.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/linear-pixels/inspect-page", json={
        "AssetPath": asset_path, "ExpectedSourceId": expected_source_id, "MipIndex": mip_index,
        "BlockIndex": block_index, "LayerIndex": layer_index, "Start": start, "Count": count,
        "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def inspect_texture_source_linear_statistics(asset_path: str, expected_source_id: str, mip_index: int = 0,
                                              block_index: int = 0, layer_index: int = 0, confirm: bool = False) -> str:
    """Native grayscale/HDR linear-color source statistics, unverified; exact source-ID/decoded64MiB/pixels<=16777216.

    Finite/nonfinite/negative/above-one counts and finite-only min/max/mean/population stddev per channel,
    HDR unclamped. Native gamma interpretation, full bulk decode/CPU scan, no perceptual/GPU proof/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source-mips/linear-statistics", json={
        "AssetPath": asset_path, "ExpectedSourceId": expected_source_id, "MipIndex": mip_index,
        "BlockIndex": block_index, "LayerIndex": layer_index, "bConfirm": confirm}, timeout=180).text


@mcp.tool()
def export_render_target_image(render_target_path: str, filename_stem: str, image_format: str,
                               expected_class_path: str, expected_asset_snapshot: str,
                               confirm: bool = False, dry_run: bool = True, slice_index: int = 0) -> str:
    """Export native2D/cube/volume/2D-array DDS or selected slice PNG/EXR/HDR under Saved/UE5_MCP/Exports.
    Requires exact class/full authored snapshot from conversion inspect. No overwrite; stem letters/digits/_/-.
    Native GPU readback/encoding/waits, no capture freshness guarantee. Native gamma/quantization/alpha policy.
    Filesystem output has no editor undo; failed writes may leave partial files. Dry-run metadata/path only.
    PNG/EXR/HDR reads full target then exports selected native slice, no directional cube remap.
    DDS ignores slice_index and exports native mip0, dimensionality/faces/slices and native DXGI/gamma policy; no generated mip chain.
    Source implementation uncompiled and output unverified; decoded DDS layout/content not validated.
    """
    return httpx.post(f"{app.BASE_URL}/render-targets/export-image", json={
        "SourceTexturePath": render_target_path, "Name": filename_stem, "FieldName": image_format,
        "ExpectedClassPath": expected_class_path, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "SliceIndex": slice_index, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def export_texture_source_dds(asset_path: str, filename_stem: str, expected_class_path: str,
                              expected_source_id: str, expected_asset_snapshot: str,
                              block_index: int = 0, layer_index: int = 0,
                              confirm: bool = False, dry_run: bool = True) -> str:
    """Export native2D/2D-array/cube/cube-array/volume selected block/layer/all authored mips as DDS.
    Exact source-ID/class/full snapshot required.2D-array bridges missing engine exporter support
    with native ImageCore DDS container and per-mip image decode/shape-format-gamma guards.
    Long-lat remains2D/2D array; BGRE8 exports encoded BGRA bytes, not linear HDR conversion.
    No platform/GPU build; native source bulk decode/locks possible. Saved/UE5_MCP/Exports only,
    no overwrite/editor undo; partial file on error possible. Dry-run metadata only; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source/export-dds", json={
        "AssetPath": asset_path, "Name": filename_stem, "ExpectedClassPath": expected_class_path,
        "ExpectedSourceId": expected_source_id, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "BlockIndex": block_index, "LayerIndex": layer_index,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def export_texture_source_image(asset_path: str, filename_stem: str, image_format: str,
                                expected_class_path: str, expected_source_id: str,
                                expected_asset_snapshot: str, block_index: int = 0,
                                layer_index: int = 0, mip_index: int = 0, slice_index: int = 0,
                                confirm: bool = False, dry_run: bool = True) -> str:
    """Export authored source block/layer/mip/slice as PNG/EXR/HDR under Saved/UE5_MCP/Exports.
    Native2D/array/cube/cube-array/volume; source ordering, no directional face/long-lat conversion.
    Entire mip decoded, native gamma/encoding policy; PNG may quantize HDR and HDR may discard alpha.
    Source-ID/class/full snapshot guards, no overwrite/editor undo; partial file possible. Unverified.
    Dry-run metadata only; no GPU/platform build or source mutation.
    """
    return httpx.post(f"{app.BASE_URL}/textures/source/export-image", json={
        "AssetPath": asset_path, "Name": filename_stem, "FieldName": image_format,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "BlockIndex": block_index,
        "LayerIndex": layer_index, "MipIndex": mip_index, "SliceIndex": slice_index,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def set_texture_alpha_coverage(asset_path: str, enabled: bool, thresholds_rgba: list[float],
                               expected_enabled: bool, expected_thresholds_rgba: list[float],
                               expected_class_path: str, expected_source_id: str,
                               expected_asset_snapshot: str, confirm: bool = False,
                               dry_run: bool = True) -> str:
    """Set native2D/cube/volume/2D-array/cube-array mip coverage scaling and four RGBA thresholds0..1.
    Requires exact prior settings/class/source-ID/full authored snapshot. Disabled thresholds retained.
    Native callbacks may rebuild resources, no generated coverage proof/explicit save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/alpha-coverage", json={
        "AssetPath": asset_path, "bEnabled": enabled, "Color": thresholds_rgba,
        "bExpectedEnabled": expected_enabled, "ExpectedColor": expected_thresholds_rgba,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_texture_alpha_coverage(asset_path: str) -> str:
    """Inspect native2D/cube/volume/2D-array/cube-array mip-coverage flag, RGBA thresholds/editability.
    Includes source-ID/class/full snapshot for guarded edits, mip-generation/compression policy.
    Nonfinite thresholds null/validity false; no pixel decode/generated coverage/build/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/alpha-coverage/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def measure_texture_source_alpha_coverage(asset_path: str, expected_class_path: str,
                                         expected_source_id: str, expected_asset_snapshot: str,
                                         mip_index: int = 0, confirm: bool = False, start: int = 0, count: int = 64) -> str:
    """Measure selected native2D/cube/volume/array/cube-array source mip linear RGBA coverage.
    Single block/layer, native slice pages1..128,64MiB full mip decode/16M scanned pixels.
    Per-slice and aggregate selected-page counts, authored face/layer/depth order retained. Per-channel finite-only >= counts/fractions/nonfinite counts.
    Explicit decode confirmation and source-ID/class/full snapshot; no generated compression/GPU proof.
    No mutation/build/save. Native decode/threshold semantics unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/alpha-coverage/measure-source", json={
        "AssetPath": asset_path, "ExpectedClassPath": expected_class_path,
        "ExpectedSourceId": expected_source_id, "ExpectedAssetSnapshot": expected_asset_snapshot,
        "MipIndex": mip_index, "bConfirm": confirm, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_texture_compression_setting(asset_path: str, field_name: str, value: int,
                                    expected_value: int, expected_class_path: str,
                                    expected_source_id: str, expected_asset_snapshot: str,
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Set native source texture CompressionSettings/CompressionQuality/LossyCompressionAmount enum
    or CompressionNone/CompressionNoAlpha/CompressionForceAlpha boolean0or1. Five native source classes.
    Exact prior value/class/source-ID/full snapshot, native editability/enum/alpha conflict guards.
    Native callbacks may change dependent defaults/build resources; no output quality proof/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/compression/setting", json={
        "AssetPath": asset_path, "FieldName": field_name, "Value": value, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_texture_compression_settings(asset_path: str) -> str:
    """Inspect five native source texture classes' compression values/editability/visible enum choices.
    Supplies source-ID/class/full authored snapshot for guarded setter and alpha flag conflict.
    Native choices do not prove platform encoder support/effective quality. No build/decode/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/compression/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def inspect_texture_sampling_settings(asset_path: str) -> str:
    """Inspect native2D/cube/volume/array/cube-array LODGroup/Filter/MipGenSettings/MipLoadOptions/SRGB/NeverStream and LOD integer settings.
    Native available address/processing flags plus editability/enum choices/source-ID/class/full snapshot.
    Authored values do not prove effective sampler/gamma/residency. No build/decode/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/sampling/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def set_texture_sampling_setting(asset_path: str, field_name: str, value: int,
                                 expected_value: int, expected_class_path: str,
                                 expected_source_id: str, expected_asset_snapshot: str,
                                 confirm: bool = False, dry_run: bool = True) -> str:
    """Set five native source texture classes' LODGroup/Filter/MipGenSettings/MipLoadOptions enum or SRGB/NeverStream boolean0or1.
    Also native processing boolean flags bPreserveBorder/bFlipGreenChannel/bNormalizeNormals/
    bUseLegacyGamma/bUseNewMipFilter; normalization requires normal-map compression, legacy gamma sRGB.
    Also native available AddressX/AddressY/AddressZ/AddressMode enums; unavailable axes rejected.
    Volume uses unified AddressMode; cube types may expose no authored address fields.
    Also LODBias -32..32, MaxTextureSize0 or power-of-two1..16384, NumCinematicMipLevels0..32.
    Exact prior value/class/source-ID/full snapshot/native editability guards; callbacks may rebuild
    resources/change dependent defaults. SRGB reinterprets source, no explicit pixel conversion or
    material sampler rewrite/residency proof/save. Transactions/no-op/dry-run; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/sampling/setting", json={
        "AssetPath": asset_path, "FieldName": field_name, "Value": value, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def set_texture_downscale_override(asset_path: str, operation: str, platform_key: str,
                                   value: float, expected_value: float, expected_exists: bool,
                                   expected_class_path: str, expected_source_id: str,
                                   expected_asset_snapshot: str, confirm: bool = False,
                                   dry_run: bool = True) -> str:
    """NativeTexture2D downscale Default/Override/RemoveOverride; values0..8, Default empty key.
    Full snapshot/source-ID/class/prior entry-existence/value guards, native editability required.
    Key syntax only, no installed platform/effective precedence validation. No explicit build/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/downscale/override", json={
        "AssetPath": asset_path, "FieldName": operation, "Name": platform_key, "Value": value,
        "ExpectedValue": expected_value, "bExpectedEnabled": expected_exists,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def inspect_texture_downscale_overrides(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect nativeTexture2D authored downscale default/ordered platform pages1..128/options choices.
    Exact source-ID/class/full snapshot for edits; values<1 defer to group,1 no scale,>1 scale.
    Options editable via shared sampling setter field DownscaleOptions. No effective platform evaluation.
    No mutation/build/decode/save; nonfinite values null/range flag, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/downscale/inspect-page", json={
        "AssetPath": asset_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def set_texture_color_adjustment(asset_path: str, field_name: str, value: float,
                                 expected_value: float, expected_class_path: str,
                                 expected_source_id: str, expected_asset_snapshot: str,
                                 confirm: bool = False, dry_run: bool = True) -> str:
    """Set native2D/cube/volume/array/cube-array AdjustBrightness/BrightnessCurve/Vibrance/Saturation/
    RGBCurve/Hue/MinAlpha/MaxAlpha with full Adjust prefix. Curves0..16,vibrance0..1,hue0..360,
    others+/-65504; native float quantization, inverted alpha allowed. Inspect sampling supplies values.
    Exact previous native float/class/source-ID/full snapshot, transaction/callback/all-eight readback.
    No explicit pixel bake/build/save or output quality proof; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/color-adjustment", json={
        "AssetPath": asset_path, "FieldName": field_name, "Value": value, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def set_texture_build_resize(asset_path: str, width: int, height: int,
                             expected_width: int, expected_height: int,
                             expected_class_path: str, expected_source_id: str,
                             expected_asset_snapshot: str, confirm: bool = False,
                             dry_run: bool = True) -> str:
    """Pair native source texture ResizeDuringBuildX/Y0..4096,0 uses source dimension.
    Texture2D in practice: the engine keeps ResizeToSpecificResolution only on Texture2D. Existing mode/full snapshot/source-ID/class/
    prior pair required. One callback, source art not rewritten; no final platform dimensions proof/save.
    Set PowerOfTwoMode or bPadWithBorderColor through shared sampling setter. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/build-resize", json={
        "AssetPath": asset_path, "SizeX": width, "SizeY": height,
        "ExpectedSizeX": expected_width, "ExpectedSizeY": expected_height,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def set_texture_padding_color(asset_path: str, rgba_bytes: list[int], expected_rgba_bytes: list[int],
                              expected_class_path: str, expected_source_id: str,
                              expected_asset_snapshot: str, confirm: bool = False,
                              dry_run: bool = True) -> str:
    """Set native source texture PaddingColor RGBA bytes0..255, five native classes where editable.
    Existing pad-to-power-of-two/square mode with border-color policy disabled required; full prior
    color/class/source-ID/full snapshot. Sampling inspector provides typed color/resize fields.
    Native callback/all color-mode-resize guards, no gamma conversion/explicit build/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/textures/padding-color", json={
        "AssetPath": asset_path, "Color": rgba_bytes, "ExpectedColor": expected_rgba_bytes,
        "ExpectedClassPath": expected_class_path, "ExpectedSourceId": expected_source_id,
        "ExpectedAssetSnapshot": expected_asset_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
set_runtime_virtual_texture_component = merged_tool("set_runtime_virtual_texture_component", {
    "numeric": set_runtime_virtual_texture_component_numeric,
    "enum": set_runtime_virtual_texture_component_enum,
})
