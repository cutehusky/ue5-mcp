"""Static and Skeletal Mesh import and settings."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def set_skeletal_mesh_section(asset_path: str, lod_index: int, section_index: int,
                              property: str, value: bool) -> str:
    """Edit skeletal mesh section flags: recompute_tangent, cast_shadow, or visible_in_ray_tracing."""
    response = httpx.patch(f"{app.BASE_URL}/skeletal-meshes/sections", json={
        "AssetPath": asset_path, "LODIndex": lod_index,
        "SectionIndex": section_index, "Property": property, "bValue": value
    })
    return response.text


@mcp.tool()
def inspect_static_mesh_source(asset_path: str) -> str:
    """Inspect Static Mesh LOD geometry and source file status."""
    return httpx.get(f"{app.BASE_URL}/static-meshes/source", params={"asset_path": asset_path}).text


@mcp.tool()
def import_static_mesh(source_file_path: str, destination_path: str, asset_name: str,
                       replace_existing: bool = False, confirm_replace: bool = False,
                       dry_run: bool = False, save: bool = False) -> str:
    """Import OBJ or glTF/GLB. OBJ replacement requires confirmation; glTF uses a new scene folder and returns actual asset paths."""
    return httpx.post(f"{app.BASE_URL}/static-meshes/import", json={
        "SourceFilePath": source_file_path, "DestinationPath": destination_path,
        "AssetName": asset_name, "bReplaceExisting": replace_existing,
        "bConfirmReplace": confirm_replace, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def reimport_static_mesh(asset_path: str, source_file_path: str = "",
                         confirm_reimport: bool = False,
                         confirm_source_change: bool = False,
                         dry_run: bool = False, save: bool = False) -> str:
    """Reimport a Static Mesh from its recorded source or a confirmed new source."""
    return httpx.post(f"{app.BASE_URL}/static-meshes/reimport", json={
        "AssetPath": asset_path, "SourceFilePath": source_file_path,
        "bConfirmReimport": confirm_reimport,
        "bConfirmSourceChange": confirm_source_change,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def set_static_mesh_lod_screen_sizes(asset_path: str, screen_sizes: list[float]) -> str:
    """Set static mesh LOD screen-size thresholds."""
    response = httpx.patch(f"{app.BASE_URL}/static-meshes/lod-screen-sizes", json={
        "AssetPath": asset_path, "ScreenSizes": screen_sizes
    })
    return response.text


@mcp.tool()
def set_static_mesh_lod_group(asset_path: str, lod_group: str) -> str:
    """Set a static mesh LOD group, such as SmallProp or LargeProp."""
    response = httpx.patch(f"{app.BASE_URL}/static-meshes/lod-group", json={
        "AssetPath": asset_path, "LODGroup": lod_group
    })
    return response.text


@mcp.tool()
def set_static_mesh_setting(asset_path: str, property: str, value: bool) -> str:
    """Edit static mesh settings: generate_lightmap_uvs or allow_cpu_access."""
    response = httpx.patch(f"{app.BASE_URL}/static-meshes/settings", json={
        "AssetPath": asset_path, "Property": property, "bValue": value
    })
    return response.text


@mcp.tool()
def edit_mesh_socket(asset_path: str, socket_name: str, bone_name: str,
                         operation: str = "create", location: dict | None = None,
                         rotation: dict | None = None, scale: dict | None = None,
                         force_always_animated: bool = True, confirm: bool = False,
                         dry_run: bool = False, save: bool = False) -> str:
    """Create/update a mesh-owned socket on a /Game SkeletalMesh with native transaction.

    Full object path and confirmation required; PIE must be stopped. Update replaces
    all socket transform/parent settings. Vectors use X/Y/Z; rotation Pitch/Yaw/Roll.
    Defaults are zero translation/rotation and unit scale. Shared Skeleton sockets can be overridden by matching name.
    """
    return httpx.post(f"{app.BASE_URL}/skeletal-meshes/sockets", json={
        "AssetPath": asset_path, "SocketName": socket_name, "BoneName": bone_name,
        "Operation": operation, "Location": location or {}, "Rotation": rotation or {},
        "Scale": scale if scale is not None else {"X": 1, "Y": 1, "Z": 1},
        "bForceAlwaysAnimated": force_always_animated, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def delete_mesh_socket(asset_path: str, socket_name: str, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Delete exactly one mesh-owned socket and its mesh preview attachments.

    Requires confirmed /Game SkeletalMesh full object path and stopped PIE. Dry-run
    validates only. Shared Skeleton sockets and external attachment names are not rewritten.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/skeletal-meshes/sockets", json={
        "AssetPath": asset_path, "SocketName": socket_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_mesh_socket(asset_path: str, socket_name: str, new_name: str,
                            confirm: bool = False, dry_run: bool = False,
                            save: bool = False) -> str:
    """Rename mesh-owned socket and mesh preview attachment names.

    Requires confirmed /Game SkeletalMesh and stopped PIE. Rejects socket/bone collisions;
    uses transaction, dry-run and optional save. External component/Blueprint/shared Skeleton
    references are not rewritten. Returns affected preview attachment count.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletal-meshes/sockets/name", json={
        "AssetPath": asset_path, "SocketName": socket_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_mesh_sockets(asset_path: str) -> str:
    """Inspect mesh-only and shared Skeleton socket definitions and override selection.

    Full registered SkeletalMesh object path required. Returns <=256 per owner with
    native FindSocket selection, local transforms, mesh bone validity and owner-separated
    preview entries (soft paths and target validity without loading preview assets). No pose or
    world transform evaluation; loads asset without authoring changes.
    """
    return httpx.get(f"{app.BASE_URL}/skeletal-meshes/sockets", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def customize_mesh_socket(asset_path: str, socket_name: str, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Copy shared Skeleton socket into a mesh-only override, preserving native settings.

    Requires confirmed /Game SkeletalMesh, stopped PIE, exactly one shared socket,
    valid mesh bone and no existing override. Uses native duplication/transaction,
    socket cache refresh and optional mesh save. Shared Skeleton remains unchanged.
    """
    return httpx.post(f"{app.BASE_URL}/skeletal-meshes/sockets/customize", json={
        "AssetPath": asset_path, "SocketName": socket_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def promote_mesh_socket(asset_path: str, socket_name: str, remove_local: bool = False,
                         confirm: bool = False, dry_run: bool = False,
                         save: bool = False) -> str:
    """Copy mesh-only socket to its /Game Skeleton, optionally removing local override.

    Requires confirmed /Game mesh, stopped PIE, valid Skeleton parent bone and no
    shared name collision. Preserves socket settings and mesh preview attachments.
    Native transaction spans both assets when remove_local; save writes Skeleton and
    changed mesh separately, so a partial save can occur. Dry-run validates only.
    """
    return httpx.post(f"{app.BASE_URL}/skeletal-meshes/sockets/promote", json={
        "AssetPath": asset_path, "SocketName": socket_name, "bRemoveLocal": remove_local,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_runtime_skeletal_socket(component_path: str, socket_name: str,
                                     space: str = "world", pie_instance: int = -1) -> str:
    """Read current evaluated socket transform on a registered selected-PIE mesh component.

    space: world/component/parent_bone. Requires actual socket with valid parent bone;
    returns selected mesh/Skeleton ownership, location, XYZW quaternion and scale.
    Does not tick animation, force LOD evaluation, advance simulation or mutate state.
    """
    return httpx.post(f"{app.BASE_URL}/skeletal-meshes/runtime/socket-transform", json={
        "ComponentPath": component_path, "SocketName": socket_name, "Space": space,
        "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def inspect_static_mesh_nanite(asset_path: str) -> str:
    """Read loaded Static Mesh Nanite settings/resource counters/fallback LOD counts.
    Compiling asset skips resource/settings access, no wait/build/load. Up to8
    conventional render LODs, input triangles/vertices/clusters/root pages. Native
    flags do not prove platform/material/GPU support or visible quality. Read-only.
    """
    return httpx.post(f"{app.BASE_URL}/static-mesh/nanite/inspect", json={
        "AssetPath": asset_path
    }, timeout=60).text


@mcp.tool()
def inspect_world_static_mesh_nanite_components() -> str:
    """Discover up to128 loaded current editor-world Static Mesh components/subclasses.
    Actor/component/asset identities, visibility/registration/disable flags, native
    Nanite flags/material count when asset not compiling. Counts/truncation explicit;
    no renderer/GPU proof/full material audit/load/build/mutation. Global iteration
    and custom getters unbounded. Provides identities for component material audit.
    """
    return httpx.post(f"{app.BASE_URL}/static-mesh/nanite/components/inspect", json={}, timeout=60).text


@mcp.tool()
def set_static_mesh_nanite_setting(asset_path: str, settings_hash: str, field: str,
                                    bool_value: bool = False, scalar_value: float = 0,
                                    save: bool = False, confirm: bool = False, dry_run: bool = False,
                                    enum_value: str = "") -> str:
    """Enums GenerateFallback(PlatformDefault/Enabled), FallbackTarget(Auto/PercentTriangles/RelativeError).
    Precision fields accept enum Auto or integer scalar within inspected native ranges.
    MinimumResidencyKB accepts uint32 (0 minimum,4294967295 whole mesh).
    Edit typed Nanite field with inspected full-settings hash on loaded /Game mesh.
    Bool fields Enabled/ExplicitTangents/LerpUVs. Scalars KeepPercentTriangles/
    FallbackPercentTriangles ratios0..1, TrimRelativeError/FallbackRelativeError/
    MaxEdgeLengthFactor0..1000. Native transaction/assignment check/rebuild notification,
    optional save/dry-run. Build may be asynchronous; no compiled output guarantee.
    """
    return httpx.post(f"{app.BASE_URL}/static-mesh/nanite/settings", json={
        "AssetPath": asset_path, "SettingsHash": settings_hash, "FieldName": field,
        "EnumValue": enum_value, "bBoolValue": bool_value, "ScalarValue": scalar_value, "bSave": save,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reset_static_mesh_nanite_setting(asset_path: str, settings_hash: str, field: str,
                                      save: bool = False, confirm: bool = False, dry_run: bool = False) -> str:
    """Reset one supported typed Nanite field to native FMeshNaniteSettings default.
    Same fields as set_static_mesh_nanite_setting, preserving other fields. Native
    struct defaults (not import/project/platform defaults). Full settings hash guard,
    transaction/notification/optional save/dry-run; rebuild may be asynchronous.
    """
    return httpx.post(f"{app.BASE_URL}/static-mesh/nanite/settings/reset", json={
        "AssetPath": asset_path, "SettingsHash": settings_hash, "FieldName": field,
        "bSave": save, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_static_mesh_component_force_disable_nanite(actor_path: str, component_path: str,
        asset_path: str, expected_force_disable: bool, force_disable: bool,
        confirm: bool = False, dry_run: bool = False) -> str:
    """Set native force-disable Nanite override on exact placed Static Mesh component.
    Inspected current flag/actor/asset guards, confirmed stopped editor/noncompiling
    mesh, component undo/readback/dry-run. Native setter may recreate render state.
    False does not guarantee Nanite use; asset/disallow settings unchanged. No save.
    """
    return httpx.post(f"{app.BASE_URL}/static-mesh/nanite/component-force-disable", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "bExpectedBoolValue": expected_force_disable, "bBoolValue": force_disable,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_composition_tile_lod_distance(world_path: str, composition_path: str,
                                             tile_package_path: str, expected_tile_count: int,
                                             expected_lod_count: int, lod_index: int,
                                             expected_distance: int, distance: int,
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Edit existing loaded tile LOD relative distance0..1e9 with cache/package/index/count guards.
    Effective distance=base layer+selected relative, checked signed32; no LOD map generation.
    Native header/cache dirty update, no undo record/load/streaming evaluation/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/tiles/lod-distance", json={
        "WorldPath": world_path, "CompositionPath": composition_path, "TilePackagePath": tile_package_path,
        "ExpectedTileCount": expected_tile_count, "ExpectedLODCount": expected_lod_count,
        "Start": lod_index, "ExpectedValue": expected_distance, "Value": distance,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_world_composition_tile_lod_list(world_path: str, composition_path: str,
                                        tile_package_path: str, expected_tile_count: int,
                                        expected_lod_distances: list[int], lod_distances: list[int],
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Replace tile LOD distance metadata<=4, empty clears, with full ordered stale guard.
    Existing slots preserve reserved metadata by index; appended slots native defaults.
    Does not create/delete/regenerate LOD maps or discovered package names. Loaded package required;
    native cache/header dirty update, no undo record, streaming evaluation or save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/composition/tiles/lod-list", json={
        "WorldPath": world_path, "CompositionPath": composition_path, "TilePackagePath": tile_package_path,
        "ExpectedTileCount": expected_tile_count, "ExpectedLODCount": len(expected_lod_distances),
        "ExpectedLODDistances": expected_lod_distances, "LODDistances": lod_distances,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_legacy_lod_actors(world_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect sorted loaded legacy LOD actor tiers/local setup indices/direct subactor refs.
    Pages1..128/subactors128, package/identity metadata; local-array diagnostic not effective override validity.
    No load, native build-validity helpers, cluster traversal, mutation/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/worlds/settings/hlod-actors/inspect", json={
        "WorldPath": world_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def import_fbx(source_file_path: str, asset_path: str, kind: str = "skeletal_mesh", skeleton_path: str = "",
               import_materials: bool = True, import_animations: bool = False, dry_run: bool = False,
               save: bool = False) -> str:
    """Import an FBX file to an unused /Game path. Existing assets are never overwritten. Requires stopped PIE.

    kind: skeletal_mesh, animation or static_mesh.
    skeleton_path: required for animation; for skeletal_mesh it reuses that Skeleton instead of creating a new one.
    import_animations: also import animation stored in the file, for skeletal_mesh only.
    Returns the main asset and created_assets, every asset added to the folder (Skeleton, Physics Asset, materials).
    A dry run validates the inputs but does not read the FBX, so it cannot catch a bad file or skeleton mismatch.
    """
    return httpx.post(f"{app.BASE_URL}/assets/import-fbx", json={
        "SourceFilePath": source_file_path, "AssetPath": asset_path, "Kind": kind, "SkeletonPath": skeleton_path,
        "bImportMaterials": import_materials, "bImportAnimations": import_animations, "bDryRun": dry_run, "bSave": save
    }, timeout=600).text
