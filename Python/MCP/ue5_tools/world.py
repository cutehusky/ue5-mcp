"""Worlds, levels, sublevels, actors and the viewport."""
from typing import Literal
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def list_editor_worlds(directory_path: str = "/Game", recursive: bool = True,
                       search: str = "", limit: int = 200,
                       offset: int = 0) -> str:
    """List UE map assets deterministically without loading them."""
    return httpx.get(f"{app.BASE_URL}/worlds/list", params={
        "directory_path": directory_path, "recursive": str(recursive).lower(),
        "search": search, "limit": limit, "offset": offset
    }).text


@mcp.tool()
def inspect_editor_world(world_path: str = "") -> str:
    """Inspect the active world, or metadata for a specified UE map asset."""
    return httpx.get(f"{app.BASE_URL}/worlds/inspect", params={
        "world_path": world_path
    }).text


@mcp.tool()
def inspect_editor_world_settings() -> str:
    """Includes field_capabilities: native leaf/member editability, storage/config flags,
    raw edit conditions and clamps. Details-panel conditions are not fully evaluated.
    Inspect typed active World Settings, numeric bounds, enum choices and forced boolean values.

    World Partition forces bPrecomputeVisibility=false; attempts to enable it are
    rejected before any requested field changes.
    """
    return httpx.get(f"{app.BASE_URL}/worlds/settings").text


@mcp.tool()
def set_editor_world_settings(numeric_settings: dict | None = None,
                              bool_settings: dict | None = None,
                              class_settings: dict | None = None,
                              enum_settings: dict | None = None,
                              navigation: dict | None = None, confirm: bool = False,
                              world_path: str = "", dry_run: bool = False,
                              save: bool = False, object_settings: dict | None = None,
                              expected_object_settings: dict | None = None,
                              color_settings: dict | None = None,
                              expected_color_settings: dict | None = None,
                              expected_numeric_settings: dict | None = None,
                              expected_bool_settings: dict | None = None,
                              expected_class_settings: dict | None = None,
                              expected_enum_settings: dict | None = None,
                              transform_settings: dict | None = None,
                              expected_transform_settings: dict | None = None) -> str:
    """Ordinary-map HLOD policy: bGenerateSingleClusterForLevel and TransformSettings.HLODBakingTransform,
    native Translation/Rotation quaternion/Scale3D objects. Requires confirm/exact world, full expected
    transform map; no HLOD generation/rebuild or existing actor movement.
    Response dirty_package_impact captures global loaded package deltas through preflight/callbacks/save;
    directly_edited_actor_paths names World Settings actor, not exhaustive callback effects.
    BoolSettings bEnableWorldComposition requires confirm/exact saved ordinary world without manual sublevels;
    the native editor handler creates/removes the composition (it prompts, and unattended sessions decline,
    when tiles already exist in the map folder). BoolSettings bEnableWorldOriginRebasing requires
    confirm/exact ordinary world; enabling requires existing native World Composition. No coordinate shift.
    Partition volumetric loading policy includes LightmassSettings.VolumetricLightmapLoadingCellSize
    and VolumetricLightmapLoadingRange1600..102400; proposed VolumeLightingMethod must be volumetric.
    Response planned_field_changes names edited fields with bounded native before/current text;
    dry-run current remains unchanged and no callback effects are simulated.
    Response includes transaction scope observation, primary-object recording and planned change count;
    no durable transaction ID or verified undo guarantee. Map saving is outside transaction scope.
    NumericSettings includes VisibilityCellSize1..100000 and partition-only
    VolumetricLightmapLoadingRange1600..102400; BoolSettings includes bForceVolumetricLightmapsOnly.
    Authored build/loading policy only; no lightmap/visibility build or streaming evaluation.
    Optional expected_numeric/bool/class/enum_settings guard supplied keys before all edits;
    keys must also occur in requested map, exact world_path required. Native float numeric values
    must match inspection exactly; omitted guards preserve legacy behavior.
    ColorSettings supports LightmassSettings.EnvironmentColor as {R,G,B,A} integer bytes0..255,
    with matching expected_color_settings, exact world_path and confirm; separate lighting build required.
    NumericSettings also supports Min/MaxGlobalTimeDilation, Min/MaxCinematicTimeDilation,
    Min/MaxUndilatedFrameTime with proposed native-float min<=max checks; limits only,
    no current dilation change or world tick.
    ObjectSettings supports DefaultReverbSettings.ReverbEffect/ReverbPluginEffect and DefaultBaseSoundMix.
    Requires confirm, exact world_path and matching expected_object_settings map; compatible persistent assets
    only, empty clears. Base mix reference does not activate a mix on an existing device.
    NumericSettings supports DefaultReverbSettings.Volume/FadeTime and DefaultAmbientZoneSettings
    ExteriorVolume/InteriorVolume/ExteriorTime/InteriorTime/ExteriorLPF/InteriorLPF/
    ExteriorLPFTime/InteriorLPFTime. BoolSettings supports DefaultReverbSettings.bApplyReverb.
    Native callbacks update device defaults when available; audible behavior unverified.
    BoolSettings supports NaniteSettings.bAllowMaskedMaterials with native setter/chain notifications.
    This may recreate render state globally; no Nanite rebuild or rendering-readiness guarantee.
    Edit active persistent World Settings with whole-request preflight and native undo.

    Inspect first for supported exact property names, ranges and enum choices.
    Nested Lightmass fields use LightmassSettings.<field>. Classes use compatible
    concrete /Script or generated Blueprint class paths; empty clears where allowed.
    world_path optionally guards against switching maps. PIE/simulation must stop.
    Dry-run reports proposed changed state with current values and performs no edits.
    save requires an existing /Game map and saves the whole map, including prior edits.
    Lighting changes need a separate lighting build; class overrides apply at play start.
    navigation uses ConfigClass (empty keeps a supported stored class), bSetSystemClass/SystemClass,
    bSetSupportedAgents/SupportedAgentIndices (unique 0-15), bSetDefaultAgentName/
    DefaultAgentName and BoolSettings. Inspect supported native config classes/flags.
    Replacing a stored config or disabling navigation requires confirm=True. Native
    navigation-system recreation can queue nav-data work; it is not a build result.
    PersistentNavigationSystemConfig preserves native module flags on disk; maps
    using it depend on this plugin. Convert an existing native module config with
    an explicit inspected ConfigClass and confirm=True. Active overrides reject edits.
    """
    return httpx.patch(f"{app.BASE_URL}/worlds/settings", json={
        "TransformSettings": transform_settings or {},
        "ExpectedTransformSettings": expected_transform_settings or {},
        "ExpectedNumericSettings": expected_numeric_settings or {},
        "ExpectedBoolSettings": expected_bool_settings or {},
        "ExpectedClassSettings": expected_class_settings or {},
        "ExpectedEnumSettings": expected_enum_settings or {},
        "ColorSettings": color_settings or {},
        "ExpectedColorSettings": expected_color_settings or {},
        "ObjectSettings": object_settings or {},
        "ExpectedObjectSettings": expected_object_settings or {},
        "NumericSettings": numeric_settings or {}, "BoolSettings": bool_settings or {},
        "ClassSettings": class_settings or {}, "EnumSettings": enum_settings or {},
        "bSetNavigation": navigation is not None, "Navigation": navigation or {}, "bConfirm": confirm,
        "WorldPath": world_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def save_editor_world(world_path: str = "", save_as: bool = False,
                      confirm: bool = False) -> str:
    """Save the active map, optionally under a new /Game path.

    Set save_as=True when world_path differs from the active map. Replacing an
    existing target additionally requires confirm=True.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/save", json={
        "WorldPath": world_path, "bSaveAs": save_as, "bConfirm": confirm
    }).text


@mcp.tool()
def create_editor_world(
        world_path: str, template_path: str = "", save: bool = True,
        dirty_policy: Literal["fail", "save", "discard"] = "fail",
        confirm: bool = False) -> str:
    """Create a blank map or an independent map copied from a template.

    Existing targets and discard of dirty work require confirm=True.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/create", json={
        "WorldPath": world_path, "TemplatePath": template_path,
        "bSave": save, "DirtyPolicy": dirty_policy, "bConfirm": confirm
    }).text


@mcp.tool()
def validate_editor_world(world_path: str, load_dependencies: bool = True,
                          run_map_check: bool = False) -> str:
    """Validate a map and optionally its dependencies or active-world Map Check."""
    return httpx.post(f"{app.BASE_URL}/worlds/validate", json={
        "WorldPath": world_path,
        "bLoadDependencies": load_dependencies,
        "bRunMapCheck": run_map_check
    }).text


@mcp.tool()
def inspect_level_instances(actor_path: str = "", validate: bool = False) -> str:
    """Inspect Level Instances, loaded/editing actors, and source editing state; optionally validate map references and cycles."""
    route = "levels/instances/validate" if validate else "levels/instances"
    return httpx.get(f"{app.BASE_URL}/{route}", params={"actor_path": actor_path}, timeout=180).text


@mcp.tool()
def create_level_instance(world_asset_path: str, label: str = "", transform: dict | None = None,
                           load: bool = True, wait: bool = True,
                           dry_run: bool = False, save: bool = False) -> str:
    """Create a native standalone Level Instance from a saved /Game map in the active editor level."""
    body = {"WorldAssetPath": world_asset_path, "Label": label,
            "bLoad": load, "bWait": wait, "bDryRun": dry_run, "bSave": save}
    if transform is not None:
        body["Transform"] = transform
    return httpx.post(f"{app.BASE_URL}/levels/instances/create", json=body, timeout=180).text


def operate_level_instance(actor_path: str,
                            operation: Literal["load", "unload", "set_asset", "transform", "remove", "enter_edit", "commit", "discard", "break"],
                            world_asset_path: str = "", transform: dict | None = None,
                            load: bool = True, wait: bool = True, dry_run: bool = False,
                            confirm: bool = False, save: bool = False) -> str:
    """Manage Level Instance lifecycle and source editing. Dirty commit requires save=True; discard/unload/replacement/removal/break require confirmation. Break clears undo history; use break_level_instance for recursive/folder options."""
    body = {"ActorPath": actor_path, "Operation": operation, "WorldAssetPath": world_asset_path,
            "bLoad": load, "bWait": wait, "bDryRun": dry_run, "bConfirm": confirm, "bSave": save}
    if transform is not None:
        body["Transform"] = transform
    return httpx.post(f"{app.BASE_URL}/levels/instances/operation", json=body, timeout=180).text


def break_level_instance(actor_path: str, break_depth: int = 1, keep_folders: bool = True,
                          dry_run: bool = False, confirm: bool = False, save: bool = False) -> str:
    """Copy actors into the owning ordinary level and remove the instance. Depth is 1–8; dry runs preview actors/packages. Native break clears undo history and requires confirmation. World Partition/external-actor maps are unsupported."""
    return httpx.post(f"{app.BASE_URL}/levels/instances/operation", json={
        "ActorPath": actor_path, "Operation": "break", "BreakDepth": break_depth,
        "bKeepFolders": keep_folders, "bDryRun": dry_run, "bConfirm": confirm, "bSave": save,
    }, timeout=180).text


@mcp.tool()
def list_editor_sublevels() -> str:
    """List streaming sublevels attached to the active editor world."""
    return httpx.get(f"{app.BASE_URL}/levels/sublevels").text


@mcp.tool()
def add_editor_sublevel(level_path: str, streaming_class: str = "",
                        transform: dict | None = None) -> str:
    """Attach an existing map as a streaming sublevel with an optional transform."""
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/add", json={
        "LevelPath": level_path, "StreamingClass": streaming_class,
        "Transform": transform or {
            "Translation": {"X": 0.0, "Y": 0.0, "Z": 0.0},
            "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0, "W": 1.0},
            "Scale3D": {"X": 1.0, "Y": 1.0, "Z": 1.0}
        }
    }).text


@mcp.tool()
def remove_editor_sublevel(level_path: str, confirm: bool = False) -> str:
    """Detach a streaming sublevel; requires explicit confirmation."""
    return httpx.request("DELETE", f"{app.BASE_URL}/levels/sublevels/remove", json={
        "LevelPath": level_path, "bConfirm": confirm
    }).text


@mcp.tool()
def set_editor_sublevel_visibility(level_path: str, visible: bool) -> str:
    """Load as needed and set a streaming sublevel's editor visibility."""
    return httpx.patch(f"{app.BASE_URL}/levels/visibility", json={
        "LevelPath": level_path, "bVisible": visible
    }).text


@mcp.tool()
def load_editor_world(world_path: str,
                      dirty_policy: Literal["fail", "save", "discard"] = "fail",
                      confirm: bool = False) -> str:
    """Load a UE map into the editor using a /Game package or object path.

    dirty_policy must be fail, save, or discard. The default reports dirty map
    and content packages without changing editor state. Discarding dirty work
    additionally requires confirm=True. The route refuses to run during PIE.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/load", json={
        "WorldPath": world_path, "DirtyPolicy": dirty_policy,
        "bConfirm": confirm
    }).text


@mcp.tool()
def get_ue_viewport() -> str:
    """Get the active level viewport camera location and rotation."""
    return httpx.get(f"{app.BASE_URL}/editor/viewport").text


@mcp.tool()
def set_ue_viewport(location: dict, rotation: dict) -> str:
    """Set the active level viewport camera using X/Y/Z and Pitch/Yaw/Roll fields."""
    return httpx.patch(f"{app.BASE_URL}/editor/viewport", json={
        "Location": location, "Rotation": rotation
    }).text


@mcp.tool()
def list_editor_actors(search: str = "", class_path: str = "", limit: int = 200) -> str:
    """List actors in the current editor world, optionally filtered by label/name/class."""
    return httpx.get(f"{app.BASE_URL}/editor/actors", params={
        "search": search, "class_path": class_path, "limit": limit
    }).text


@mcp.tool()
def spawn_editor_actor(actor_class: str = "", asset_path: str = "",
                       location: dict | None = None,
                       rotation: dict | None = None) -> str:
    """Spawn an Actor class or placeable asset in the current editor world."""
    return httpx.post(f"{app.BASE_URL}/editor/actors/spawn", json={
        "ActorClass": actor_class, "AssetPath": asset_path,
        "Location": location or {"X": 0.0, "Y": 0.0, "Z": 0.0},
        "Rotation": rotation or {"Pitch": 0.0, "Yaw": 0.0, "Roll": 0.0}
    }).text


@mcp.tool()
def select_editor_actors(actor_paths: list[str]) -> str:
    """Replace the level-editor selection with actor object paths."""
    return httpx.post(f"{app.BASE_URL}/editor/actors/select", json={"ActorPaths": actor_paths}).text


@mcp.tool()
def duplicate_editor_actor(actor_path: str, offset: dict | None = None) -> str:
    """Duplicate an editor actor with an optional X/Y/Z offset."""
    return httpx.post(f"{app.BASE_URL}/editor/actors/duplicate", json={
        "ActorPath": actor_path, "Offset": offset or {"X": 0.0, "Y": 0.0, "Z": 0.0}
    }).text


@mcp.tool()
def edit_editor_actor_transform(actor_path: str, location: dict | None = None,
                                rotation: dict | None = None,
                                scale: dict | None = None,
                                label: str = "", folder_path: str = "",
                                attach_to: str = "", attach_socket: str = "") -> str:
    """Edit an actor transform, label, folder, or attachment in the current level."""
    body = {"ActorPath": actor_path}
    if location is not None:
        body.update({"Location": location, "bSetLocation": True})
    if rotation is not None:
        body.update({"Rotation": rotation, "bSetRotation": True})
    if scale is not None:
        body.update({"Scale": scale, "bSetScale": True})
    if label:
        body.update({"Label": label, "bSetLabel": True})
    if folder_path:
        body.update({"FolderPath": folder_path, "bSetFolderPath": True})
    if attach_to or attach_socket:
        body.update({"AttachTo": attach_to, "AttachSocket": attach_socket, "bSetAttachment": True})
    return httpx.patch(f"{app.BASE_URL}/editor/actors/transform", json=body).text


@mcp.tool()
def set_editor_actor_properties(actor_path: str, properties: dict) -> str:
    """Set reflected actor properties using UE property paths and string values."""
    return httpx.patch(f"{app.BASE_URL}/editor/actors/properties", json={
        "ActorPath": actor_path, "Properties": properties
    }).text


@mcp.tool()
def delete_editor_actor(actor_path: str, confirm: bool = False) -> str:
    """Delete an editor actor; requires confirm=True."""
    return httpx.request("DELETE", f"{app.BASE_URL}/editor/actors", json={
        "ActorPath": actor_path, "bConfirm": confirm
    }).text


@mcp.tool()
def select_all_editor_actors() -> str:
    """Select all actors in the current editor world."""
    return httpx.post(f"{app.BASE_URL}/editor/actors/select-all", json={}).text


@mcp.tool()
def query_scene_actors(search: str = "", class_path: str = "", tag: str = "",
                       folder: str = "", level: str = "",
                       minimum: dict | None = None, maximum: dict | None = None,
                       limit: int = 200) -> str:
    """Query placed actors deterministically by identity, class, tag, folder, level, or bounds."""
    params = {"search": search, "class_path": class_path, "tag": tag,
              "folder": folder, "level": level, "limit": limit}
    if minimum is not None and maximum is not None:
        params.update({"min_x": minimum.get("X", 0), "min_y": minimum.get("Y", 0),
                       "min_z": minimum.get("Z", 0), "max_x": maximum.get("X", 0),
                       "max_y": maximum.get("Y", 0), "max_z": maximum.get("Z", 0)})
    return httpx.get(f"{app.BASE_URL}/scene/actors/query", params=params).text


@mcp.tool()
def list_actor_components(actor_path: str) -> str:
    """List the deterministic component hierarchy of a placed editor actor."""
    return httpx.get(f"{app.BASE_URL}/scene/actors/components", params={"actor_path": actor_path}).text


@mcp.tool()
def get_actor_component_properties(actor_path: str, component_name: str) -> str:
    """Serialize reflected properties for one component on a placed actor."""
    return httpx.get(f"{app.BASE_URL}/scene/actors/components/properties", params={
        "actor_path": actor_path, "component_name": component_name
    }).text


@mcp.tool()
def add_actor_component(actor_path: str, component_class: str,
                        component_name: str, attach_to_component: str = "",
                        attach_socket: str = "", properties: dict | None = None) -> str:
    """Create and register a transactional instance component on a placed actor."""
    return httpx.post(f"{app.BASE_URL}/scene/actors/components", json={
        "ActorPath": actor_path, "ComponentClass": component_class,
        "ComponentName": component_name, "AttachToComponent": attach_to_component,
        "AttachSocket": attach_socket, "Properties": properties or {}
    }).text


@mcp.tool()
def attach_actor_component(actor_path: str, component_name: str,
                           attach_to_component: str = "", attach_socket: str = "") -> str:
    """Attach a scene component to another component, or detach when the parent is empty."""
    return httpx.patch(f"{app.BASE_URL}/scene/actors/components", json={
        "ActorPath": actor_path, "ComponentName": component_name,
        "AttachToComponent": attach_to_component, "AttachSocket": attach_socket,
        "bSetAttachment": True
    }).text


@mcp.tool()
def set_actor_component_properties(actor_path: str, component_name: str,
                                   properties: dict) -> str:
    """Set reflected properties on one placed-actor component transactionally."""
    return httpx.patch(f"{app.BASE_URL}/scene/actors/components/properties", json={
        "ActorPath": actor_path, "ComponentName": component_name,
        "Properties": properties
    }).text


@mcp.tool()
def delete_actor_component(actor_path: str, component_name: str,
                           confirm: bool = False) -> str:
    """Delete a non-root instance component; confirmation is always required."""
    return httpx.request("DELETE", f"{app.BASE_URL}/scene/actors/components", json={
        "ActorPath": actor_path, "ComponentName": component_name,
        "bConfirm": confirm
    }).text


@mcp.tool()
def place_editor_asset(actor_class: str = "", asset_path: str = "",
                       location: dict | None = None, rotation: dict | None = None,
                       scale: dict | None = None, label: str = "",
                       folder_path: str = "", select: bool = True) -> str:
    """Place an actor class or asset using UE's actor-factory workflow and an explicit transform."""
    return httpx.post(f"{app.BASE_URL}/editor/placement", json={
        "ActorClass": actor_class, "AssetPath": asset_path,
        "Location": location or {"X": 0.0, "Y": 0.0, "Z": 0.0},
        "Rotation": rotation or {"Pitch": 0.0, "Yaw": 0.0, "Roll": 0.0},
        "Scale": scale or {"X": 1.0, "Y": 1.0, "Z": 1.0},
        "Label": label, "FolderPath": folder_path, "bSelect": select
    }).text


@mcp.tool()
def make_editor_sublevel_current(level_path: str, expected_world_path: str,
                                 expected_streaming_path: str, expected_current_level_path: str,
                                 expected_visible: bool, confirm: bool = False,
                                 dry_run: bool = True) -> str:
    """Make an already-loaded unlocked ordinary sublevel current for editing and visible.
    Inspect guards with list_editor_sublevels; native current-level and visibility callbacks.
    Reports affected actors/dirty packages, no explicit load/save; not game activation.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/current", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "bExpectedVisible": expected_visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_locked(level_path: str, expected_world_path: str,
                               expected_streaming_path: str, expected_current_level_path: str,
                               expected_locked: bool, locked: bool,
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set authored edit lock of an already-loaded ordinary attached sublevel.
    Use authored_locked from listing as guard; effective locked also includes native read-only policy.
    Native transaction/dirty behavior, affected actor and dirty snapshots, no load or save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/locked", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "bExpectedLocked": expected_locked, "bLocked": locked,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_transform(level_path: str, expected_world_path: str,
                                  expected_streaming_path: str, expected_current_level_path: str,
                                  expected_transform: dict, transform: dict,
                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Set already-loaded ordinary sublevel offset through native editor transform handling.
    Transform objects use Unreal Translation{X,Y,Z}, Rotation{X,Y,Z,W}, Scale3D{X,Y,Z}.
    Convert listing arrays to those native fields; quaternion normalized, positive scale0.001..1000.
    Native transaction, actor PostEditMove/construction, possible BSP rebuild and redraw; no save.
    Full expected transform guard1e-6, native no-op tolerance; affected actor/dirty snapshots.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/transform", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedTransform": expected_transform, "Transform": transform,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_streaming_class(level_path: str, expected_world_path: str,
                                        expected_streaming_path: str,
                                        expected_current_level_path: str,
                                        expected_streaming_class: str, streaming_class: str,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Replace an already-loaded ordinary sublevel streaming class using native editor helper.
    Concrete requested class must already be loaded; changed execution requires clean loaded packages.
    Native replaces streaming object and may change visibility/current level; selected settings copied,
    custom class fields use native defaults. Reports new identity/actor/dirty state; no save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/streaming-class", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedStreamingClass": expected_streaming_class, "StreamingClass": streaming_class,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_folder(level_path: str, expected_world_path: str,
                               expected_streaming_path: str, expected_current_level_path: str,
                               expected_folder_path: str, folder_path: str,
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set native sublevel organization folder, including unloaded ordinary attached entries.
    Empty string is root; slash-separated segments, FName case-insensitive guards/no-op.
    Transaction/dirty reporting, no actor-folder edits, map rename, level load or save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/folder", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedFolderPath": expected_folder_path, "FolderPath": folder_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_editor_sublevel_color(level_path: str, expected_world_path: str,
                              expected_streaming_path: str, expected_current_level_path: str,
                              expected_color_rgba: list[float], color_rgba: list[float],
                              confirm: bool = False, dry_run: bool = True) -> str:
    """Set sublevel visualization linear RGBA0..1 with full native color/context guards.
    Native property callback marks loaded components render-state dirty; no display mode toggle.
    Transaction, affected actors/dirty reporting, unloaded entries supported; no load/save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/color", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedColorValues": expected_color_rgba, "ColorValues": color_rgba,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_priority(level_path: str, expected_world_path: str,
                                 expected_streaming_path: str, expected_current_level_path: str,
                                 expected_priority: int, priority: int,
                                 confirm: bool = False, dry_run: bool = True) -> str:
    """Set native signed32 sublevel streaming priority with current/context guards.
    Native SetPriority updates consideration order without interrupting current evaluation.
    Transaction/events/readback/dirty reporting; temporary override backup unchanged, no load/save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/priority", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedValue": expected_priority, "Value": priority,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_editor_sublevel_boolean(level_path: str, expected_world_path: str,
                                expected_streaming_path: str, expected_current_level_path: str,
                                field_name: str, expected_value: bool, value: bool,
                                confirm: bool = False, dry_run: bool = True) -> str:
    """Set bShouldBlockOnLoad/bShouldBlockOnUnload/bDrawOnLevelStatusMap with native bitfield guards.
    Authored future streaming/display configuration, no immediate load/unload or status-map toggle.
    Native events/transaction/readback/dirty reporting, unloaded ordinary entries supported; no save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/boolean", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "FieldName": field_name, "ExpectedValue": int(expected_value), "Value": int(value),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_composition_tiles(world_path: str, composition_path: str,
                                     start: int = 0, count: int = 64) -> str:
    """Read existing ordinary-world cached composition tiles, native-order pages1..128.
    Package/parent/positions/bounds/layer/distance/LOD metadata; identity from World Settings inspect.
    No package-header rescan, tile load, origin shift, streaming evaluation, mutation or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/tiles/inspect", json={
        "WorldPath": world_path, "CompositionPath": composition_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_world_composition_setting(world_path: str, composition_path: str, field_name: str,
                                   expected_value: float, value: float,
                                   confirm: bool = False, dry_run: bool = True) -> str:
    """Set existing composition instance policy with exact identities/current value guard.
    Fields: RebaseOriginDistance1..1e9, TilesStreamingTimeThreshold0..100000,
    bLoadAllTilesDuringCinematic/bRebaseOriginIn3DSpace/bLockTilesLocation0..1.
    Transaction/events/dirty; no config-file write/save, tile rescan/load or origin shift.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/setting", json={
        "WorldPath": world_path, "CompositionPath": composition_path, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_composition_tile_layer(world_path: str, composition_path: str, tile_package_path: str,
                                      expected_tile_count: int, expected_layer_name: str,
                                      expected_distance: int, expected_enabled: bool, layer_name: str,
                                      distance: int, enabled: bool, confirm: bool = False,
                                      dry_run: bool = True) -> str:
    """Edit existing loaded tile's embedded layer metadata with full native cache/package guards.
    Native cache/package header update and dirty, no undo record/automatic rollback/save.
    Same-name other tiles untouched; no reposition/load/streaming evaluation.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/tiles/layer", json={
        "WorldPath": world_path, "CompositionPath": composition_path, "TilePackagePath": tile_package_path,
        "ExpectedTileCount": expected_tile_count, "ExpectedLayerName": expected_layer_name,
        "ExpectedValue": expected_distance, "bExpectedDistanceStreamingEnabled": expected_enabled,
        "LayerName": layer_name, "Value": distance, "bDistanceStreamingEnabled": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_composition_tile_display(world_path: str, composition_path: str,
                                        tile_package_path: str, expected_tile_count: int,
                                        field_name: str, expected_value: int, value: int,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Set loaded tile browser ZOrder signed32 or bHideInTileView0..1 with native metadata guards.
    Browser display only, not actor visibility/streaming/world position. Cache/header update/dirty,
    no undo record, actor movement, tile load or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/tiles/display", json={
        "WorldPath": world_path, "CompositionPath": composition_path,
        "TilePackagePath": tile_package_path, "ExpectedTileCount": expected_tile_count,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_composition_tile_hierarchy(world_path: str, composition_path: str,
                                              tile_package_path: str, start: int = 0,
                                              count: int = 64) -> str:
    """Inspect cached tile ancestors<=128 and sorted direct-child pages1..128.
    Reports missing parents/cycles/truncation, not global validity; uncached persistent root may be missing.
    No absolute-position recalculation, header rescan, map load, reparent/move or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/tiles/hierarchy", json={
        "WorldPath": world_path, "CompositionPath": composition_path, "TilePackagePath": tile_package_path,
        "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_precomputed_visibility_override(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect authored visible/invisible actor and invisible-level refs, independent pages1..128.
    No build/containment/render visibility evaluation, actor load or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/visibility-override/inspect", json={
        "ActorPath": actor_path, "EntryStart": start, "EntryCount": count
    }, timeout=180).text


@mcp.tool()
def set_precomputed_visibility_override_actors(actor_path: str, actor_guid: str, expected_label: str,
                                                field_name: str, expected_paths: list[str], paths: list[str],
                                                confirm: bool = False, dry_run: bool = True) -> str:
    """Replace OverrideVisibleActors/OverrideInvisibleActors<=64 with full ordered stale guard.
    Unique loaded current-world refs, rejects opposite-list conflicts; empty clears.
    Native transaction/events/readback, no immediate hiding/render change/visibility build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/visibility-override/actors", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "FieldName": field_name, "ExpectedAssetPaths": expected_paths, "AssetPaths": paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_precomputed_visibility_override_levels(actor_path: str, actor_guid: str, expected_label: str,
                                                expected_names: list[str], names: list[str],
                                                confirm: bool = False, dry_run: bool = True) -> str:
    """Replace complete invisible-level name list<=64 with exact ordered previous-name guard.
    Native case-insensitive unique non-None names, empty clears; names may refer to unloaded levels.
    Transaction/events/readback, no visibility build, actor hiding, level load or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/visibility-override/levels", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedAssetPaths": expected_names, "AssetPaths": names,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
edit_level_instance = merged_tool("edit_level_instance", {
    "operate_level_instance": operate_level_instance,
    "break_level_instance": break_level_instance,
})
set_editor_sublevel = merged_tool("set_editor_sublevel", {
    "color": set_editor_sublevel_color,
    "boolean": set_editor_sublevel_boolean,
})
