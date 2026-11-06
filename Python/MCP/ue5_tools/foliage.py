"""Foliage types and procedural foliage."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_world_foliage() -> str:
    """Inspect up to128 loaded current-world native foliage partition actors/type counts.
    Unloaded cells/landscape grass/PCG/general ISMs omitted; no load/create/rebuild/save.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/inspect", json={}, timeout=60).text


@mcp.tool()
def inspect_foliage_types(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Page1..128 foliage actor type map/settings/source/editor and optional HISM counts.
    Map order unstable/traversal unbounded, actor foliage has no HISM; source getter custom work possible.
    No load/reapply/rebuild/save, placement/render state unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/inspect", json={
        "ActorPath": actor_path, "Start": start, "Count": count
    }, timeout=60).text


@mcp.tool()
def inspect_foliage_instances(actor_path: str, type_path: str, start: int = 0, count: int = 64) -> str:
    """Page1..128 native editor foliage placements/world transforms/base IDs/procedural GUID/flags.
    Indices unstable/not render IDs; Z offset separate. No base resolution/trace/edit/rebuild/save.
    Native editor/render agreement unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/instances/inspect", json={
        "ActorPath": actor_path, "TypePath": type_path, "Start": start, "Count": count
    }, timeout=60).text


def set_foliage_type_scalar(actor_path: str, type_path: str, expected_update_guid: str,
                            field: str, expected_value: float, value: float,
                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set Density0..10000/DensityAdjustmentFactor0..1000/Radius or SingleInstanceModeRadius0..100000.
    Also AlignMaxAngle/RandomPitchAngle0..359 degrees and MinimumLayerWeight/
    MinimumExclusionLayerWeight0..1.
    Inspected actor/type membership/update GUID/exact current float guards, native transaction/notification.
    Type can be shared; callback updates GUID/lightmap resolution and may notify/reallocate loaded actors.
    No painting/reapply/simulation/build/save; callbacks/render/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/scalar", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_foliage_type_bool(actor_path: str, type_path: str, expected_update_guid: str,
                          field: str, expected_value: bool, value: bool,
                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set AlignToNormal/RandomYaw/CollisionWithWorld/bSingleInstanceModeOverrideRadius.
    Inspected actor/type membership/update GUID/current flag guards, native bitfield notification.
    CollisionWithWorld is placement eligibility, not instance physics collision mode.
    Transaction/readback/no-op/dry-run/no reapply/painting/simulation/build/save; shared effects/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/bool", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "bExpectedValue": expected_value, "bValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_instance_transform(actor_path: str, type_path: str, expected_update_guid: str,
                                   instance_index: int, expected_instance_count: int, expected_base_id: int,
                                   expected_location: list[float], expected_rotation: list[float],
                                   expected_scale: list[float], location: list[float],
                                   rotation: list[float], scale: list[float],
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Move manual static-mesh foliage via native hash/implementation move notifications.
    Exact inspected actor/type GUID/count/index/base/world-transform guards, nonprocedural/not moving.
    XYZ+/-1e9/normalized XYZW/nonzero scale abs<=1000, native Rotator/float-scale conversion.
    Actor/HISM transaction/readback/no-op/dry-run; base/flags/Zoffset retained, no trace/snap/partition migration/save.
    Native render/collision/undo/persistence unverified; guards not unique instance revision.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/foliage/instances/transform", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "InstanceIndex": instance_index, "ExpectedInstanceCount": expected_instance_count,
        "ExpectedBaseId": expected_base_id,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_foliage_instance(actor_path: str, type_path: str, expected_update_guid: str,
                            instance_index: int, expected_instance_count: int, expected_base_id: int,
                            expected_location: list[float], expected_rotation: list[float],
                            expected_scale: list[float], confirm: bool = False,
                            dry_run: bool = False) -> str:
    """Delete manual static-mesh foliage with actor/type GUID/count/index/base/transform guards.
    Actor/HISM transaction/native remove/count/swap readback/dry-run. Native swaps last into deleted index.
    Reinspect cached indices; tree rebuild/native hash/selection/resource work may be unbounded.
    No type removal/procedural simulation/save; render/collision/undo/persistence unverified.
    """
    if len(expected_location) != 3 or len(expected_rotation) != 4 or len(expected_scale) != 3:
        raise ValueError("Expected transform requires XYZ position/scale and XYZW quaternion")
    return httpx.post(f"{app.BASE_URL}/foliage/instances/delete", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "InstanceIndex": instance_index, "ExpectedInstanceCount": expected_instance_count,
        "ExpectedBaseId": expected_base_id, "ExpectedTransform": {
            "Translation": dict(zip(("X", "Y", "Z"), expected_location)),
            "Rotation": dict(zip(("X", "Y", "Z", "W"), expected_rotation)),
            "Scale3D": dict(zip(("X", "Y", "Z"), expected_scale))},
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_foliage_instance(actor_path: str, type_path: str, expected_update_guid: str,
                         expected_instance_count: int, location: list[float],
                         rotation: list[float], scale: list[float],
                         confirm: bool = False, dry_run: bool = False) -> str:
    """Append manual unbased instance to existing initialized static-mesh foliage actor/type.
    Ordinary non-WorldPartition map/type GUID/current count<1e6 guards/no active move.
    XYZ+/-1e9/unit XYZW/nonzero scale abs<=1000, native Rotator/float-scale/default flags/Zoffset.
    Actor/HISM transaction/native append/async forced refresh/readback/dry-run/no save.
    No trace/snap/alignment/density/collision filtering/partition actor creation; undo/render unverified.
    """
    if len(location) != 3 or len(rotation) != 4 or len(scale) != 3:
        raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
    return httpx.post(f"{app.BASE_URL}/foliage/instances/add", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedInstanceCount": expected_instance_count, "Transform": {
            "Translation": dict(zip(("X", "Y", "Z"), location)),
            "Rotation": dict(zip(("X", "Y", "Z", "W"), rotation)),
            "Scale3D": dict(zip(("X", "Y", "Z"), scale))},
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def register_foliage_type(actor_path: str, type_path: str, expected_update_guid: str,
                           expected_type_count: int, confirm: bool = False,
                           dry_run: bool = False) -> str:
    """Register/initialize loaded shared static-mesh foliage asset on existing actor in ordinary map.
    Exact inspected type GUID/type-map count<=4096, loaded persistent source mesh required.
    Actor transaction/native add/initialize/HISM readback/no-op/dry-run/no save.
    No asset duplication/instance placement/partition actor creation; component allocation/render/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/register", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedTypeCount": expected_type_count, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_foliage_type(type_path: str, mesh_path: str = "", confirm: bool = False, dry_run: bool = True) -> str:
    """Create a static-mesh foliage type asset at a new canonical /Game/Folder/Name.Name path.
    Native defaults, optional static mesh, no overwrite. Not registered with any foliage actor.
    Transaction/dry-run; no save.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/create", json={
        "TypePath": type_path, "AssetPath": mesh_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_procedural_foliage_spawner(asset_path: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Create an empty procedural foliage spawner asset at a new canonical /Game/Folder/Name.Name path.
    Native defaults, no overwrite, no simulation. Transaction/dry-run; no save.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/spawner/create", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_foliage_type(type_path: str) -> str:
    """Inspect loaded foliage type independently of actor registration; update GUID/settings/source.
    Includes shared-asset status/outer/package dirty. No load/reference search/register/reapply/save.
    Native source getter may run custom work; placement/render readiness unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/asset/inspect", json={
        "TypePath": type_path
    }, timeout=60).text


@mcp.tool()
def set_foliage_type_scale_range(actor_path: str, type_path: str, expected_update_guid: str,
                                 field: str, expected_range: list[float], scale_range: list[float],
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set ScaleX/ScaleY/ScaleZ ordered min/max0.001..1000 adapter cap.
    Inspected actor/type membership/update GUID/full interval guards, native float transaction/notification.
    Effective axes depend on scaling mode; no painting/reapply/rescale existing instances/build/save.
    Shared callbacks/render/undo/persistence unverified.
    """
    if len(expected_range) != 2 or len(scale_range) != 2:
        raise ValueError("Expected/new scale interval requires min/max pairs")
    return httpx.post(f"{app.BASE_URL}/foliage/types/scale-range", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "ExpectedRange": dict(zip(("X", "Y"), expected_range)),
        "Range": dict(zip(("X", "Y"), scale_range)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_cull_range(actor_path: str, type_path: str, expected_update_guid: str,
                                expected_range: list[int], cull_range: list[int],
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Set ordered integer cull min/max0..1e9 world units with full inspected interval/type GUID guard.
    Native zero disables control; fade needs PerInstanceFadeAmount material support.
    Transaction/notification/readback/no-op/dry-run/no save; shared HISM/native callbacks/undo unverified.
    """
    if len(expected_range) != 2 or len(cull_range) != 2:
        raise ValueError("Expected/new cull interval requires min/max pairs")
    return httpx.post(f"{app.BASE_URL}/foliage/types/cull-range", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedRange": dict(zip(("X", "Y"), expected_range)),
        "Range": dict(zip(("X", "Y"), cull_range)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_scaling(actor_path: str, type_path: str, expected_update_guid: str,
                             expected_mode: int, mode: int,
                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set scaling0 Uniform/1 Free/2 LockXY/3 LockXZ/4 LockYZ, inspected mode/type GUID guard.
    Axis ranges retained, transaction/notification/readback/no-op/dry-run/no save.
    No existing-instance rescale/painting/reapply; shared native callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/scaling", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedValue": expected_mode, "Value": mode, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_mesh(actor_path: str, type_path: str, expected_update_guid: str,
                          expected_instance_count: int, expected_mesh_path: str, mesh_path: str,
                          confirm: bool = False, dry_run: bool = False) -> str:
    """Replace foliage type source mesh with loaded persistent UStaticMesh, no clear.
    Exact inspected actor/type membership/update GUID/actor count/current mesh guards.
    Type transaction/native source notifications/readback/no-op/dry-run/no save.
    Shared source callbacks may rebuild/reallocate all loaded referencing actors across worlds.
    Native work/transaction coverage/placement preservation/render/collision/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/mesh", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedInstanceCount": expected_instance_count, "ExpectedAssetPath": expected_mesh_path,
        "AssetPath": mesh_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_material_slot(actor_path: str, type_path: str, expected_update_guid: str,
                                   field: str, expected_slot_count: int, slot_index: int,
                                   expected_material_path: str, material_path: str,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set existing OverrideMaterials/NaniteOverrideMaterials slot to loaded material or empty null.
    Inspected actor/type GUID/full count1..64/index/current path guards, array size/order retained.
    Type transaction/native notification/readback/no-op/dry-run/no load/save.
    Mesh-slot/material usage/domain/shader/Nanite eligibility and shared callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/material-slot", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "ExpectedSlotCount": expected_slot_count, "SlotIndex": slot_index,
        "ExpectedAssetPath": expected_material_path, "AssetPath": material_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_foliage_type_materials(actor_path: str, type_path: str, expected_update_guid: str,
                                   field: str, expected_material_paths: list[str], material_paths: list[str],
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Replace OverrideMaterials/NaniteOverrideMaterials with full inspected ordered path-array guard.
    <=64 loaded materials/empty null slots; empty array clears, order/duplicates preserved.
    Actor/type GUID guards/type transaction/native notification/full readback/no-op/dry-run/no load/save.
    Native shared reallocation/material usage/mesh slots/shaders/Nanite/null fallback/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/materials", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "ExpectedAssetPaths": expected_material_paths, "AssetPaths": material_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def unregister_empty_foliage_type(actor_path: str, type_path: str, expected_update_guid: str,
                                  expected_type_count: int, confirm: bool = False,
                                  dry_run: bool = False) -> str:
    """Remove empty static-mesh foliage type registration from ordinary non-WorldPartition actor.
    Inspected type GUID/map count, zero editor/selection/render count and no actor moves required.
    Actor/all component transaction/native removal/readback/dry-run; native re-registers all actor components.
    Source asset retained; no instance/asset/actor deletion/save. Resource callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/unregister-empty", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedTypeCount": expected_type_count, "ExpectedInstanceCount": 0,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_placement_range(actor_path: str, type_path: str, expected_update_guid: str,
                                     field: str, expected_range: list[float], placement_range: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set ordered ZOffset/Height range+/-1e9 world units or GroundSlopeAngle0..359 degrees.
    Exact inspected actor/type GUID/full native-float interval guards, transaction/notification/readback.
    No-op/dry-run/no painting/trace/reapply/existing-instance move/build/save.
    Shared callbacks/native placement evaluation/undo/persistence unverified.
    """
    if len(expected_range) != 2 or len(placement_range) != 2:
        raise ValueError("Expected/new placement interval requires min/max pairs")
    return httpx.post(f"{app.BASE_URL}/foliage/types/placement-range", json={
        "ActorPath": actor_path, "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "FieldName": field, "ExpectedRange": dict(zip(("X", "Y"), expected_range)),
        "Range": dict(zip(("X", "Y"), placement_range)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_procedural_foliage() -> str:
    """Inspect up to128 loaded current-world procedural foliage components/spawner/GUID/surface flags.
    No bounds/region load/simulation/spawned-instance scan/edit/save; freshness unproven.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/components/inspect", json={}, timeout=60).text


@mcp.tool()
def inspect_procedural_foliage_spawner(spawner_path: str) -> str:
    """Inspect loaded spawner seed/tile/quad-tree configuration/cached types/material soft paths.
    Up to128 entries per array, const cached getter/no lazy refresh; absent cache not absent authored type.
    No simulation/random advance/tile generation/region load/edit/save; freshness/readiness unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/spawner/inspect", json={
        "AssetPath": spawner_path
    }, timeout=60).text


@mcp.tool()
def set_procedural_foliage_spawner_setting(spawner_path: str, field: str,
                                          expected_value: float, value: float,
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set RandomSeed int32/NumUniqueTiles1..64/TileSize1..1e6cm/MinimumQuadTreeSize0.01..1e6cm.
    Adapter limits/exact inspected current value guard/native type/transaction/notification/readback.
    No-op/dry-run/no simulation/cache clear/random advance/region load/resimulation/build/save.
    Cached tiles/placed instances may be stale; callbacks/cache coherence/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/spawner/setting", json={
        "AssetPath": spawner_path, "FieldName": field, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_procedural_foliage_component_bool(actor_path: str, component_path: str,
                                         expected_procedural_guid: str, field: str,
                                         expected_value: bool, value: bool,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Set bAllowLandscape/bAllowBSP/bAllowStaticMesh/bAllowTranslucent/bAllowFoliage/bShowDebugTiles.
    Inspected actor/component/procedural GUID/current flag guards, transaction/notification/readback.
    No-op/dry-run/no resimulation/placement/removal/region load/build/save; existing instances retained.
    Native/custom callbacks/display/eligibility/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/components/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedProceduralGuid": expected_procedural_guid, "FieldName": field,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_procedural_foliage_spawner(actor_path: str, component_path: str, expected_procedural_guid: str,
                                  expected_spawner_path: str, spawner_path: str,
                                  confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded persistent procedural spawner or empty clear, inspected component GUID/reference guard.
    Actor/component transaction/notification/readback/no-op/dry-run/no load/save.
    Existing procedural GUID/generated instances retained; no cache refresh/simulation/removal/build.
    Existing content may not match new spawner; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/components/spawner", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedProceduralGuid": expected_procedural_guid, "ExpectedAssetPath": expected_spawner_path,
        "AssetPath": spawner_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_procedural_foliage_tile_overlap(actor_path: str, component_path: str, expected_procedural_guid: str,
                                       expected_spawner_path: str, expected_overlap: float, overlap: float,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set authored tile overlap0..1e6cm adapter cap with inspected overlap/spawner/component GUID guards.
    Actor/component transaction/notification/readback/no-op/dry-run/no save.
    No simulation/resimulation/removal/region load/build; layout compatibility/cache/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/components/overlap", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedProceduralGuid": expected_procedural_guid, "ExpectedAssetPath": expected_spawner_path,
        "ExpectedValue": expected_overlap, "Value": overlap, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_procedural_foliage_spawner_types(spawner_path: str, expected_type_paths: list[str],
                                            type_paths: list[str], confirm: bool = False,
                                            dry_run: bool = False) -> str:
    """Replace spawner type wrappers with <=128 loaded persistent foliage type assets, empty clears.
    Full inspected ordered authored-reference guard, duplicates/order retained; Blueprint wrappers excluded.
    Checked reflected layout/native wrapper refresh/authored+cached readback/transaction/no-op/dry-run.
    No simulation/tile clear/random advance/region load/build/save; existing generated data retained.
    Unchanged authored array does not repair cache; reflection/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/spawner/types", json={
        "AssetPath": spawner_path, "ExpectedAssetPaths": expected_type_paths, "AssetPaths": type_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_procedural_foliage_terrain_materials(spawner_path: str, expected_enabled: bool,
                                            expected_material_paths: list[str], enabled: bool,
                                            material_paths: list[str], confirm: bool = False,
                                            dry_run: bool = False) -> str:
    """Set spawner terrain-material override flag/full soft-reference list with inspected pair guard.
    <=128 loaded material interfaces/empty null entries, empty array clears; order/duplicates retained.
    Override requires all eligible terrain materials; matching/inheritance semantics unverified.
    Checked reflection/asset transaction/notifications/readback/no-op/dry-run/no load/save.
    No simulation/cache clear/region load/build; existing generated content/cache/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/spawner/terrain-materials", json={
        "AssetPath": spawner_path, "bExpectedValue": expected_enabled,
        "ExpectedAssetPaths": expected_material_paths, "bValue": enabled, "AssetPaths": material_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_procedural_foliage_blocking_volumes() -> str:
    """Inspect up to128 loaded procedural blocking volumes/target/falloff flag/external curve/key count.
    Null target applies broadly; no curve evaluation/containment/trace/simulation/load/edit/save.
    Native placement/falloff outcome unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/blocking/inspect", json={}, timeout=60).text


@mcp.tool()
def set_procedural_foliage_blocking_target(actor_path: str, expected_volume_path: str, volume_path: str,
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set blocking volume target to loaded current-world procedural volume or empty all-procedural scope.
    Exact inspected reference guard/actor transaction/native notification/readback/no-op/dry-run/no save.
    Existing generated instances retained; no resimulation/removal/reapply/build. Eligibility/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/blocking/target", json={
        "ActorPath": actor_path, "ExpectedAssetPath": expected_volume_path, "AssetPath": volume_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_procedural_foliage_blocking_falloff(actor_path: str, expected_enabled: bool,
                                           expected_curve_path: str, enabled: bool, curve_path: str,
                                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set blocking-volume falloff flag/loaded external CurveFloat or empty embedded fallback.
    Full inspected pair guard/actor transaction/notification/readback/no-op/dry-run/no load/save.
    Embedded curve preserved; curve maps normalized XY distance to keep probability.
    Disabled falloff blocks applicable placement outright; no evaluation/validation/resimulation/removal/build.
    Native brush/target/filter semantics/callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/procedural/blocking/falloff", json={
        "ActorPath": actor_path, "bExpectedValue": expected_enabled, "ExpectedAssetPath": expected_curve_path,
        "bValue": enabled, "AssetPath": curve_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_procedural_setting(type_path: str, expected_update_guid: str,
                                       field: str, expected_value: float, value: float,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set native procedural type numeric setting independently of actor registration.
    NumSteps0..1000/SeedsPerStep0..1e6/DistributionSeed int32; CollisionRadius/ShadeRadius/
    InitialSeedDensity/AverageSpreadDistance/SpreadVariance/MaxInitialSeedOffset/MaxInitialAge/MaxAge0..1e6,
    OverlapPriority+/-1e6 adapter caps. Inspected GUID/current value guard, native transaction/notification.
    Initial seed density squared per10mx10m; future simulation cost can grow rapidly.
    No-op/dry-run/no simulation/cache clear/resimulation/build/save; native shared callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/procedural-setting", json={
        "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_procedural_bool(type_path: str, expected_update_guid: str,
                                     field: str, expected_value: bool, value: bool,
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set bCanGrowInShade/bSpawnsInShade/DensityFalloffEnabled, standalone GUID/current flag guards.
    Spawns-in-shade effective only when can-grow-in-shade; counterpart retained.
    Transaction/notification/readback/no-op/dry-run/no simulation/cache clear/build/save; undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/procedural-bool", json={
        "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid, "FieldName": field,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_procedural_curve(type_path: str, expected_update_guid: str,
                                      field: str, expected_curve_path: str, curve_path: str,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Assign ScaleCurve/DensityFalloffCurve loaded external CurveFloat or empty embedded fallback.
    Inspected type GUID/reference guard, embedded keys/density-enable retained, curve asset unchanged.
    Transaction/notification/readback/no-op/dry-run/no load/simulation/cache clear/build/save.
    Curve domain/range/probability/readiness/shared callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/foliage/types/procedural-curve", json={
        "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid, "FieldName": field,
        "ExpectedAssetPath": expected_curve_path, "AssetPath": curve_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_type_procedural_scale(type_path: str, expected_update_guid: str,
                                     expected_range: list[float], scale_range: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set procedural growth min/max scale0.001..1000 adapter cap, full inspected interval/type GUID guard.
    Independent of actor registration; native normalized-age ScaleCurve selects within range.
    Type transaction/notification/readback/no-op/dry-run/no simulation/cache clear/build/save.
    Native age/curve/scale evaluation/shared callbacks/undo unverified.
    """
    if len(expected_range) != 2 or len(scale_range) != 2:
        raise ValueError("Expected/new scale interval requires min/max pairs")
    return httpx.post(f"{app.BASE_URL}/foliage/types/procedural-scale", json={
        "TypePath": type_path, "ExpectedUpdateGuid": expected_update_guid,
        "ExpectedRange": dict(zip(("X", "Y"), expected_range)),
        "Range": dict(zip(("X", "Y"), scale_range)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_foliage_blocking_inline_falloff(actor_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect stored inline falloff keys/tangents in pages1..128, without curve evaluation or simulation."""
    return httpx.post(f"{app.BASE_URL}/volumes/foliage-blocking/inline-falloff/inspect", json={
        "ActorPath": actor_path, "EntryStart": start, "EntryCount": count
    }, timeout=180).text


@mcp.tool()
def replace_foliage_blocking_linear_falloff(actor_path: str, actor_guid: str, expected_label: str,
                                            expected_enabled: bool, expected_external_curve_path: str,
                                            expected_keys: list[list[float]], keys: list[list[float]],
                                            confirm: bool = False, dry_run: bool = True, expected_curve_text: str = "") -> str:
    """Replace full inline curve with linear time/value keys<=256, normalized0..1.
    Discards tangents/interpolation/handles; preserves enable/default/extrapolation/external reference.
    External curve can mask inline keys. Empty clears; no evaluation/resimulation/instance changes/save.
    """
    if any(len(pair) != 2 for pair in expected_keys + keys):
        raise ValueError("Keys require time/value pairs")
    return httpx.post(f"{app.BASE_URL}/volumes/foliage-blocking/inline-falloff/linear-keys", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "bExpectedBoolValue": expected_enabled, "ExpectedCurvePath": expected_external_curve_path,
        "ExpectedPairs": [{"X": p[0], "Y": p[1]} for p in expected_keys],
        "Pairs": [{"X": p[0], "Y": p[1]} for p in keys], "ExpectedCurveText": expected_curve_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_blocking_inline_curve_setting(actor_path: str, actor_guid: str, expected_label: str,
                                               expected_enabled: bool, expected_external_curve_path: str,
                                               field_name: str, expected_value: float, value: float,
                                               confirm: bool = False, dry_run: bool = True, expected_curve_text: str = "") -> str:
    """Set DefaultValue0..1, ClearDefaultValue(value1), PreInfinityExtrap or PostInfinityExtrap.
    Extrapolation:0 Cycle,1 CycleWithOffset,2 Oscillate,3 Linear,4 Constant,5 None.
    Guard expected default using inspected raw value, including native unset sentinel.
    Preserves keys/enable/external reference; no curve evaluation or foliage simulation/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/foliage-blocking/inline-falloff/setting", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "bExpectedBoolValue": expected_enabled, "ExpectedCurvePath": expected_external_curve_path,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "ExpectedCurveText": expected_curve_text, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_foliage_blocking_inline_key_setting(actor_path: str, actor_guid: str, expected_label: str,
                                            expected_enabled: bool, expected_external_curve_path: str,
                                            expected_curve_text: str, expected_key_count: int, key_index: int,
                                            field_name: str, expected_value: float, value: float,
                                            confirm: bool = False, dry_run: bool = True) -> str:
    """Edit one key with mandatory full untruncated native_snapshot_text from inspection.
    InterpMode0 Linear/1 Constant/2 Cubic; TangentMode0 Auto/1 User/2 Break/4 SmartAuto;
    TangentWeightMode0 None/1 Arrive/2 Leave/3 Both; ArriveTangent/LeaveTangent+/-1e6,
    ArriveTangentWeight/LeaveTangentWeight0..1e6. Retains key times/values, resets key handles;
    no automatic tangent calculation, curve evaluation, foliage simulation, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/foliage-blocking/inline-falloff/key-setting", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "bExpectedBoolValue": expected_enabled, "ExpectedCurvePath": expected_external_curve_path,
        "ExpectedCurveText": expected_curve_text, "ExpectedEntryCount": expected_key_count, "EntryIndex": key_index,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def edit_foliage_blocking_inline_keys(actor_path: str, actor_guid: str, expected_label: str,
                                       expected_enabled: bool, expected_external_curve_path: str,
                                       expected_curve_text: str, expected_key_count: int, operation: str,
                                       key_index: int = -1, time: float = 0, value: float = 0,
                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Add a linear key at unique normalized float time/value0..1 or Remove key_index.
    Requires full untruncated native falloff snapshot; preserves all surviving keys/tangents.
    At most256 keys, empty permitted; resets key handles, no tangent recalculation/evaluation/simulation/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/foliage-blocking/inline-falloff/keys", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "bExpectedBoolValue": expected_enabled, "ExpectedCurvePath": expected_external_curve_path,
        "ExpectedCurveText": expected_curve_text, "ExpectedEntryCount": expected_key_count,
        "FieldName": operation, "EntryIndex": key_index, "Pair": {"X": time, "Y": value},
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
set_foliage_type = merged_tool("set_foliage_type", {
    "scalar": set_foliage_type_scalar,
    "bool": set_foliage_type_bool,
})
