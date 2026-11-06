"""Volumes."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_world_volumes() -> str:
    """Read up to128 loaded current-world volume actors/subclasses and coarse world bounds.
    Identities/class/label/level/brush component, total/truncation; nonfinite bounds null.
    Not brush topology or containment proof; no build/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/inspect", json={}, timeout=60).text


@mcp.tool()
def query_volume_point(actor_path: str, position: list[float], radius: float = 0) -> str:
    """Native world-space volume point/sphere overlap, radius0..1e6/world XYZ+/-1e9.
    Uses current brush collision; not whole-sphere containment or topology validation.
    Native distance semantics; read-only/no collision rebuild/load/save/mutation.
    """
    if len(position) != 3:
        raise ValueError("World position requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/volumes/query-point", json={
        "ActorPath": actor_path, "Position": dict(zip(("X", "Y", "Z"), position)), "Radius": radius
    }, timeout=60).text


@mcp.tool()
def inspect_pain_volume(actor_path: str) -> str:
    """Read native pain volume damage/interval/flags/type/instigator; no damage/timer calls."""
    return httpx.post(f"{app.BASE_URL}/volumes/pain/inspect", json={"ActorPath": actor_path}, timeout=60).text


@mcp.tool()
def set_pain_volume_setting(actor_path: str, field: str, expected_value: float,
                             scalar_value: float = 0, bool_value: bool = False,
                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set DamagePerSec(0..1e6), PainInterval(0.001..1e6), PainCausing/EntryPain(bool).
    Exact inspected field value guard (bool0/1), native float requests, transaction/
    editor notification/readback/dry-run/no-op. No damage/timer invocation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/pain/settings", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "ScalarValue": scalar_value, "bBoolValue": bool_value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_pain_volume_damage_type(actor_path: str, expected_class_path: str, class_path: str,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded UDamageType subclass with exact inspected current class guard.
    Empty expected class means null; requested class must be nonempty/current/persistent.
    Abstract data-holder classes allowed, no instantiation/damage/timers/load/save.
    Transaction/editor notification/dry-run/no-op; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/pain/damage-type", json={
        "ActorPath": actor_path, "ExpectedClassPath": expected_class_path, "ClassPath": class_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_box_volume(volume_type: str, name: str, position: list[float], extent: list[float],
                       label: str = "", confirm: bool = False, dry_run: bool = False, hollow: bool = False, wall_thickness: float = 0,
                            inner_radius: float = 0, tessellated: bool = False) -> str:
    """Optional native hollow Box/Cylinder; Box wall_thickness is full dimension reduction
    (per-face inset half), Cylinder inner_radius positive below outer. Cavity collision unverified.
    Location type also supports initialized World Partition, native unheld editor loader.
    Create native box volume in ordinary map: Physics/Pain/Blocking/Trigger/CameraBlocking/
    KillZ/CullDistance/LightmassImportance/PrecomputedVisibility/PostProcess/LevelStreaming/Location/HierarchicalLOD/Audio/
    LightmassCharacterIndirectDetail/PrecomputedVisibilityOverride/
    ProceduralFoliage/ProceduralFoliageBlocking (native defaults, no spawner/simulation).
    Unique name1..128 letters/digits/underscore, optional label<=128, world XYZ+/-1e9,
    half extents1..100000. Native type defaults, unit scale/no rotation.
    Transaction/dry-run/no save; brush/collision/undo/persistence unverified.
    """
    if len(position) != 3 or len(extent) != 3:
        raise ValueError("Position and half extents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/volumes/create-box", json={
        "VolumeType": volume_type, "Name": name, "Label": label,
        "Position": dict(zip(("X", "Y", "Z"), position)),
        "Extent": dict(zip(("X", "Y", "Z"), extent)), "bTessellated": tessellated, "bHollow": hollow, "WallThickness": wall_thickness, "InnerRadius": inner_radius,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_volume_collision(actor_path: str) -> str:
    """Read brush collision profile/enabled/overlap/physics-state and body aggregate counts.
    Not cooking freshness/contact/containment proof; no rebuild/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/inspect", json={"ActorPath": actor_path}, timeout=60).text


@mcp.tool()
def set_volume_overlap_events(actor_path: str, component_path: str, expected_enabled: bool,
                                enabled: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set inspected volume brush overlap-event flag with exact identity/current-value guards.
    Native setter may refresh overlaps and invoke callbacks; transaction/dry-run/no-op.
    Does not change collision profile/responses. No save; undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/overlap-events", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedBoolValue": expected_enabled,
        "bBoolValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volume_collision_enabled(actor_path: str, component_path: str, expected_mode: int,
                                   mode: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Set NoCollision/QueryOnly/PhysicsOnly/QueryAndPhysics/ProbeOnly/QueryAndProbe.
    Inspected current native ordinal0..5 and brush identity guards. Native physics/
    overlap refresh may invoke callbacks; transaction/dry-run/no-op/no save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/enabled", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedCollisionMode": expected_mode,
        "CollisionMode": mode, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volume_collision_response(actor_path: str, component_path: str, channel: int,
                                    expected_response: int, response: str,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Set one native channel0..31 to Ignore/Overlap/Block; expected ordinal0/1/2.
    Inspect channel_responses first; custom channel meanings depend on project config.
    Native setter may switch profile to Custom and refresh physics/overlaps.
    Transaction/dry-run/no-op/no save; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/response", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Channel": channel,
        "ExpectedResponse": expected_response, "Response": response, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volume_collision_object_type(actor_path: str, component_path: str, expected_object_type: int,
                                      channel: int, confirm: bool = False, dry_run: bool = False) -> str:
    """Set brush native object channel ordinal0..31 with inspected current type guard.
    Project channel meanings depend on configuration; no trace/object category inference.
    Native setter/transaction/dry-run/no-op/no save; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/object-type", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedObjectType": expected_object_type,
        "Channel": channel, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_volume_collision_profiles() -> str:
    """Read project collision presets(up to128),32 channel names/object-trace query mappings.
    MAX sentinels indicate unavailable query conversion; response arrays use channel indices.
    No config reload/write/component mutation; first singleton access may initialize config.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/profiles", json={}, timeout=60).text


@mcp.tool()
def set_volume_collision_profile(actor_path: str, component_path: str, expected_profile: str,
                                  profile: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Assign configured collision preset with inspected current name/brush identity guards.
    Native assignment replaces mode/type/responses and updates overlaps. Same name
    is no-op, not forced filter reset. Transaction/dry-run/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/collision/profile", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedProfileName": expected_profile,
        "ProfileName": profile, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_volume_cached_overlaps(actor_path: str, component_path: str) -> str:
    """Read up to128 current-world actors from inspected brush's existing overlap cache.
    Native collection work unbounded; cache may be empty/stale in editor. No refresh,
    collision rebuild/damage/timers/save/mutation; not containment/membership proof.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/overlaps/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=60).text


@mcp.tool()
def delete_volume(actor_path: str, component_path: str, expected_class_path: str,
                    confirm: bool = False, dry_run: bool = False) -> str:
    """Delete inspected persistent-level volume in ordinary map; no attached actors required.
    Exact actor/brush/class identities; native editor destruction with transaction/dry-run.
    External references/subsystem callbacks/undo/persistence unverified; no save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_cull_distance_volume(actor_path: str, entry_start: int = 0, entry_count: int = 64) -> str:
    """Read enabled state and size/cull-distance table pages1..128.
    Size is bounds sphere diameter, native nearest-size selection, zero distance=no culling.
    No affected-primitive scan/render refresh/save/mutation; nonfinite fields null.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/cull-distance/inspect", json={
        "ActorPath": actor_path, "EntryStart": entry_start, "EntryCount": entry_count
    }, timeout=60).text


@mcp.tool()
def set_cull_distance_volume_entry(actor_path: str, expected_entry_count: int, entry_index: int,
                                    expected_size: float, expected_distance: float,
                                    size: float, distance: float, confirm: bool = False,
                                    dry_run: bool = False) -> str:
    """Edit existing cull size/distance pair0..1e9 with inspected count/current pair guards.
    Native floats, zero distance=no culling; no sorting/deduplication. Transaction/
    property notification queues delayed world refresh, dry-run/no-op/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/cull-distance/entry", json={
        "ActorPath": actor_path, "ExpectedEntryCount": expected_entry_count, "EntryIndex": entry_index,
        "ExpectedPair": {"X": expected_size, "Y": expected_distance}, "Pair": {"X": size, "Y": distance},
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_cull_distance_volume_enabled(actor_path: str, expected_enabled: bool, enabled: bool,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set cull-volume enabled flag with inspected current-state guard.
    Transaction/editor notification queues delayed world update; table unchanged.
    Dry-run/no-op/no save; render effects/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/cull-distance/enabled", json={
        "ActorPath": actor_path, "bExpectedBoolValue": expected_enabled, "bBoolValue": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_cull_distance_volume_table(actor_path: str, expected_pairs: list[list[float]],
                                       pairs: list[list[float]], confirm: bool = False,
                                       dry_run: bool = False) -> str:
    """Replace entire ordered cull table with full inspected table guard; max4096 pairs.
    Each pair=[size,distance]0..1e9; empty clears, duplicates/order preserved.
    Native float/transaction/notification/delayed refresh/dry-run/no-op/no save; unverified.
    """
    if len(pairs) > 4096 or len(expected_pairs) > 4096 or any(len(p) != 2 for p in pairs + expected_pairs):
        raise ValueError("Tables require at most4096 size/distance pairs")
    return httpx.post(f"{app.BASE_URL}/volumes/cull-distance/table", json={
        "ActorPath": actor_path, "ExpectedPairs": [{"X": p[0], "Y": p[1]} for p in expected_pairs],
        "Pairs": [{"X": p[0], "Y": p[1]} for p in pairs], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_volume_unload_cooldown(level_path: str, expected_world_path: str,
                                              expected_streaming_path: str,
                                              expected_current_level_path: str,
                                              expected_seconds: float, seconds: float,
                                              confirm: bool = False, dry_run: bool = True) -> str:
    """Set authored native float volume-unload cooldown seconds0..1e6 with exact current guard.
    Native property events/transaction/dirty reporting; does not unload or evaluate streaming.
    Loaded locked targets rejected; unloaded ordinary entries supported, no explicit load/save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/volume-unload-cooldown", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedValue": expected_seconds, "Value": seconds,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_editor_sublevel_streaming_volumes(level_path: str, expected_world_path: str,
                                         expected_streaming_path: str, expected_current_level_path: str,
                                         expected_volume_paths: list[str], volume_paths: list[str],
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Replace full ordered sublevel streaming-volume assignments<=64; empty clears.
    Requested volumes already loaded/editable in persistent level; exact full-list/context guards.
    Native property events rebuild reverse references; transaction/readback/dirty reporting, no save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/sublevels/streaming-volumes", json={
        "LevelPath": level_path, "ExpectedWorldPath": expected_world_path,
        "ExpectedStreamingPath": expected_streaming_path,
        "ExpectedCurrentLevelPath": expected_current_level_path,
        "ExpectedVolumePaths": expected_volume_paths, "VolumePaths": volume_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_editor_streaming_volumes(expected_world_path: str, start: int = 0,
                                     count: int = 64) -> str:
    """Inspect loaded streaming volume identities/settings/assignments in current editor world.
    Sorted pages1..128, native reverse package names compared with attached streaming assignments.
    No cache repair, brush containment, streaming evaluation, actor load, mutation or save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/streaming-volumes/inspect", json={
        "ExpectedWorldPath": expected_world_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_editor_streaming_volume_setting(expected_world_path: str, actor_path: str,
                                        actor_guid: str, expected_label: str, field_name: str,
                                        expected_value: int, value: int,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Edit loaded persistent streaming volume bDisabled/bEditorPreVisOnly0..1 or StreamingUsage0..4.
    Inspect exact world/actor/GUID/label/current value first. Native events/transaction/readback.
    Reports immediate actor/dirty effects; no forced streaming evaluation, brush/assignment edit/save.
    """
    return httpx.post(f"{app.BASE_URL}/levels/streaming-volumes/setting", json={
        "ExpectedWorldPath": expected_world_path, "ActorPath": actor_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name,
        "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_cylinder_volume(volume_type: str, name: str, position: list[float],
                            radius: float, height: float, sides: int = 16,
                            label: str = "", confirm: bool = False, dry_run: bool = True, hollow: bool = False, wall_thickness: float = 0,
                            inner_radius: float = 0, align_to_side: bool = False) -> str:
    """Optional native hollow Box/Cylinder; Box wall_thickness is full dimension reduction
    (per-face inset half), Cylinder inner_radius positive below outer. Cavity collision unverified.
    Location type also supports initialized World Partition, native unheld editor loader.
    Create native solid polygonal cylinder volume in ordinary persistent editor map.
    Same types as create_box_volume, including LevelStreaming; radius1..100000, height2..200000,
    sides3..128, native defaults/identity rotation/unit scale. Transaction, no save or assignment.
    Polygonal brush approximation; native brush/collision/undo/persistence unverified.
    """
    if len(position) != 3:
        raise ValueError("Position requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/volumes/create-cylinder", json={
        "VolumeType": volume_type, "Name": name, "Label": label,
        "Position": dict(zip(("X", "Y", "Z"), position)),
        "Extent": {"X": radius, "Y": radius, "Z": height / 2}, "Sides": sides,
        "bAlignToSide": align_to_side, "bHollow": hollow, "WallThickness": wall_thickness, "InnerRadius": inner_radius,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_sphere_volume(volume_type: str, name: str, position: list[float], radius: float,
                         tessellation: int = 3, label: str = "", confirm: bool = False,
                         dry_run: bool = True) -> str:
    """Location type also supports initialized World Partition, native unheld editor loader.
    Create native polygonal sphere volume through UE Sphere brush tool in ordinary map.
    Same types as create_box_volume; radius1..100000, native tessellation1..5, unit scale/no rotation.
    Subdivided octahedral brush, not analytic sphere collision. Native transaction/defaults/no save.
    """
    if len(position) != 3:
        raise ValueError("Position requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/volumes/create-sphere", json={
        "VolumeType": volume_type, "Name": name, "Label": label,
        "Position": dict(zip(("X", "Y", "Z"), position)),
        "Extent": {"X": radius, "Y": radius, "Z": radius}, "Tessellation": tessellation,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_volume_brush_polygons(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect native authored brush polygons in local space, page1..128/first64 vertices each.
    Includes stored normals/UV vectors/material/flags/counts; nonfinite values null.
    Not compiled BSP/cooked collision/manifold proof; no load, rebuild, mutation or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/brush/polygons/inspect", json={
        "ActorPath": actor_path, "EntryStart": start, "EntryCount": count
    }, timeout=180).text


@mcp.tool()
def replace_volume_brush_shape(actor_path: str, actor_guid: str, expected_label: str,
                                expected_model_path: str, expected_polygon_count: int,
                                shape: str, extent: list[float], sides: int = 16,
                                tessellation: int = 3, confirm: bool = False,
                                dry_run: bool = True, partition_path: str = "", hollow: bool = False, wall_thickness: float = 0,
                            inner_radius: float = 0, tessellated: bool = False,
                                align_to_side: bool = False, inner_height: float = 0) -> str:
    """Optional native hollow Box/Cylinder; Box wall_thickness is full dimension reduction
    (per-face inset half), Cylinder inner_radius positive below outer. Cavity collision unverified.
    Replace entire volume brush with Box/Cylinder/Sphere/Cone; discards old surface authoring/materials.
    Inspect model/count first. Extent: Box half XYZ; Cylinder radius,radius,half-height;
    Sphere radius triple. Cone uses Cylinder extents and optional hollow inner_height. Dimensions1..100000, sides3..128, tessellation1..5.
    Native factory geometry/collision callbacks and transaction; transform retained, no save.
    Always replacement even same geometry; ordinary persistent volumes, or native unheld LocationVolume with exact partition_path.
    """
    if len(extent) != 3:
        raise ValueError("Extent requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/volumes/brush/replace-shape", json={
        "PartitionPath": partition_path, "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedObjectPath": expected_model_path, "ExpectedEntryCount": expected_polygon_count,
        "EnumValue": shape, "Extent": dict(zip(("X", "Y", "Z"), extent)),
        "Sides": sides, "Tessellation": tessellation, "bTessellated": tessellated, "bAlignToSide": align_to_side, "bHollow": hollow, "WallThickness": wall_thickness, "InnerRadius": inner_radius, "InnerHeight": inner_height,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volume_brush_color(actor_path: str, actor_guid: str, expected_label: str,
                            expected_color_bytes: list[int], color_bytes: list[int],
                            expected_enabled: bool, enabled: bool,
                            confirm: bool = False, dry_run: bool = True) -> str:
    """Set authored volume wireframe custom RGBA bytes and enable flag with full stale guards.
    Native brush color, not material/light color; disabled uses engine/category fallback.
    Transaction/editor callbacks/render-state dirty/readback, no render synchronization/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/brush/color", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedChannels": expected_color_bytes, "Channels": color_bytes,
        "bExpectedBoolValue": expected_enabled, "bBoolValue": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_volume_page(start: int = 0, count: int = 64,
                               class_path: str = "", level_path: str = "") -> str:
    """Inspect sorted loaded current-world volume pages1..128 with optional loaded class/level filters.
    Includes actor/GUID/color/bounds/package/editability; no actor load/build/mutation/save.
    Collection changes can shift offsets; native coarse bounds not containment proof.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/inspect-page", json={
        "EntryStart": start, "EntryCount": count, "ClassPath": class_path, "ObjectPath": level_path
    }, timeout=180).text


@mcp.tool()
def inspect_volume_brush_builder(actor_path: str) -> str:
    """Read stored Box/Cylinder/Sphere builder dimensions/flags and model identity/count guards.
    Reports absent/custom/foreign-owned recipe; stored recipe may differ from manually edited topology.
    No Build, default-object creation, package load, geometry validation, mutation or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/brush/builder/inspect", json={
        "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def create_cone_volume(volume_type: str, name: str, position: list[float], radius: float,
                       height: float, sides: int = 16, label: str = "", hollow: bool = False,
                       inner_radius: float = 0, inner_height: float = 0,
                       align_to_side: bool = False, confirm: bool = False,
                       dry_run: bool = True) -> str:
    """Create native polygonal cone volume, same types/map rules as box/cylinder.
    Radius1..100000,height2..200000,sides3..128. Hollow inner radius positive below outer,
    inner height positive<=outer. Native cone brush axis/origin, unit scale/no rotation.
    Location type supports initialized partition/unheld loader. Transaction/no save or assignment.
    """
    if len(position) != 3:
        raise ValueError("Position requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/volumes/create-cone", json={
        "VolumeType": volume_type, "Name": name, "Label": label,
        "Position": dict(zip(("X", "Y", "Z"), position)),
        "Extent": {"X": radius, "Y": radius, "Z": height / 2}, "Sides": sides,
        "bHollow": hollow, "InnerRadius": inner_radius, "InnerHeight": inner_height,
        "bAlignToSide": align_to_side, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
