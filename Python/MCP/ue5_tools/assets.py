"""Generic asset operations, creation, source control and the Content Browser."""
from typing import Literal
import httpx

from . import app
from .app import mcp, _ext


@mcp.tool()
def describe_asset(asset_path: str) -> str:
    """Describe a UE asset. Includes Blueprint parent/type and the widget list for Widget Blueprints.

    asset_path: Unreal object path such as /Game/UI/WBP_Menu.WBP_Menu.
    """
    response = httpx.get(f"{app.BASE_URL}/assets/describe", params={"asset_path": asset_path})
    return response.text


@mcp.tool()
def get_asset_properties(asset_path: str) -> str:
    """Read reflected properties from a UE asset, including structs, arrays, enums and asset references."""
    response = httpx.get(f"{app.BASE_URL}/assets/properties", params={"asset_path": asset_path})
    return response.text


@mcp.tool()
def set_asset_properties(asset_path: str, properties: dict) -> str:
    """Set reflected asset properties using dot paths and UE text values.

    Supports nested struct fields, array indices, enum names and object asset paths.
    """
    response = httpx.patch(f"{app.BASE_URL}/assets/properties", json={
        "AssetPath": asset_path, "Properties": properties
    })
    return response.text


@mcp.tool()
def list_assets(directory_path: str = "/Game", recursive: bool = True) -> str:
    """List assets below a UE content directory."""
    response = httpx.get(f"{app.BASE_URL}/assets/list", params={
        "directory_path": directory_path, "recursive": str(recursive).lower()
    })
    return response.text


@mcp.tool()
def save_asset(asset_path: str) -> str:
    """Save a dirty UE asset package."""
    response = httpx.post(f"{app.BASE_URL}/assets/save", json={"AssetPath": asset_path})
    return response.text


@mcp.tool()
def duplicate_asset(asset_path: str, destination_path: str) -> str:
    """Duplicate an asset to a new content path."""
    response = httpx.post(f"{app.BASE_URL}/assets/duplicate", json={
        "AssetPath": asset_path, "DestinationPath": destination_path
    })
    return response.text


@mcp.tool()
def rename_asset(asset_path: str, destination_path: str) -> str:
    """Rename or move an asset to a new content path."""
    response = httpx.post(f"{app.BASE_URL}/assets/rename", json={
        "AssetPath": asset_path, "DestinationPath": destination_path
    })
    return response.text


@mcp.tool()
def get_asset_referencers(asset_path: str) -> str:
    """Find cached package referencers of an asset."""
    response = httpx.get(f"{app.BASE_URL}/assets/referencers", params={"asset_path": asset_path})
    return response.text


@mcp.tool()
def delete_asset(asset_path: str) -> str:
    """Force-delete an asset package. This can remove undo history and should be used deliberately."""
    response = httpx.post(f"{app.BASE_URL}/assets/delete", json={"AssetPath": asset_path})
    return response.text


@mcp.tool()
def get_asset_capabilities() -> str:
    """List legacy family names plus per-family generic, inspect, edit, create, rebuild, and validate flags."""
    return httpx.get(f"{app.BASE_URL}/assets/capabilities").text


@mcp.tool()
def batch_asset_operations(operations: list[dict], dry_run: bool = False,
                           save: bool = False, stop_on_error: bool = False) -> str:
    """Run ordered generic set_properties or save operations and return one result per entry. The batch is not atomic."""
    entries = []
    for item in operations:
        entries.append({
            "AssetPath": item.get("asset_path", item.get("AssetPath", "")),
            "AssetClass": item.get("asset_class", item.get("AssetClass", "")),
            "Operation": item.get("operation", item.get("Operation", "set_properties")),
            "Properties": item.get("properties", item.get("Properties", {})),
            "bDryRun": item.get("dry_run", item.get("bDryRun", False)),
            "bSave": item.get("save", item.get("bSave", False)),
        })
    return httpx.post(f"{app.BASE_URL}/assets/batch", json={
        "Operations": entries, "bDryRun": dry_run,
        "bSave": save, "bStopOnError": stop_on_error
    }).text


@mcp.tool()
def validate_asset(asset_path: str, asset_class: str = "",
                   properties: dict | None = None) -> str:
    """Check asset identity and preflight property paths and values without editing the asset."""
    return httpx.post(f"{app.BASE_URL}/assets/validate", json={
        "AssetPath": asset_path, "AssetClass": asset_class,
        "Properties": properties or {}
    }).text


@mcp.tool()
def preview_asset_operation(asset_path: str, operation: str = "set_properties",
                            asset_class: str = "",
                            properties: dict[str, str] | None = None) -> str:
    """Preview property changes or a save with validation and no asset mutation."""
    return httpx.post(f"{app.BASE_URL}/assets/preview-operation", json={
        "AssetPath": asset_path, "AssetClass": asset_class,
        "Operation": operation, "Properties": properties or {}
    }).text


@mcp.tool()
def get_editor_source_control_provider() -> str:
    """Inspect the editor's configured source-control provider and supported operations."""
    return httpx.get(f"{app.BASE_URL}/editor/source-control/provider").text


@mcp.tool()
def get_asset_source_control_status(asset_paths: list[str] | None = None, refresh: bool = True,
                                    file_paths: list[str] | None = None) -> str:
    """Read source-control state for /Game assets or selected project files, including missing files."""
    return httpx.post(f"{app.BASE_URL}/editor/source-control/status", json={
        "AssetPaths": asset_paths or [], "FilePaths": file_paths or [], "bRefresh": refresh,
    }, timeout=180).text


@mcp.tool()
def get_asset_source_control_history(asset_paths: list[str] | None = None, max_history: int = 20,
                                     history_offset: int = 0, refresh: bool = True,
                                     file_paths: list[str] | None = None) -> str:
    """Read bounded revision metadata for up to 16 /Game assets or selected project files."""
    return httpx.post(f"{app.BASE_URL}/editor/source-control/history", json={
        "AssetPaths": asset_paths or [], "FilePaths": file_paths or [], "MaxHistory": max_history,
        "HistoryOffset": history_offset, "bRefresh": refresh,
    }, timeout=180).text


@mcp.tool()
def operate_asset_source_control(asset_paths: list[str],
                                 operation: Literal["checkout", "add", "revert", "submit"],
                                 description: str = "", dry_run: bool = False,
                                 confirm: bool = False, confirm_delete_added: bool = False,
                                 file_paths: list[str] | None = None) -> str:
    """Run a provider operation on /Game assets or selected project files. Revert/submit require confirmation; submit requires a description and saved packages."""
    return httpx.post(f"{app.BASE_URL}/editor/source-control/operation", json={
        "AssetPaths": asset_paths, "FilePaths": file_paths or [], "Operation": operation, "Description": description,
        "bDryRun": dry_run, "bConfirm": confirm,
        "bConfirmDeleteAdded": confirm_delete_added,
    }, timeout=180).text


@mcp.tool()
def audit_editor_assets(asset_paths: list[str] | None = None,
                        directory_path: str = "/Game",
                        recursive: bool = True) -> str:
    """Audit dependencies, missing packages, referencers, and redirectors."""
    return httpx.post(f"{app.BASE_URL}/editor/asset-audit", json={
        "AssetPaths": asset_paths or [], "DirectoryPath": directory_path,
        "bRecursive": recursive
    }).text


@mcp.tool()
def fixup_editor_redirectors(asset_paths: list[str] | None = None,
                             directory_path: str = "/Game",
                             recursive: bool = True,
                             confirm: bool = False) -> str:
    """Fix referencers and delete resolved redirectors; requires confirmation."""
    return httpx.post(f"{app.BASE_URL}/editor/fixup-redirectors", json={
        "AssetPaths": asset_paths or [], "DirectoryPath": directory_path,
        "bRecursive": recursive, "bConfirm": confirm
    }).text


@mcp.tool()
def get_asset_editor_status(asset_path: str) -> str:
    """Report whether an asset editor is open and its editor name."""
    return httpx.get(f"{app.BASE_URL}/editor/assets/status", params={"asset_path": asset_path}).text


@mcp.tool()
def open_asset_editor(asset_path: str) -> str:
    """Open the appropriate UE editor for an asset."""
    return httpx.post(f"{app.BASE_URL}/editor/assets/open", json={"AssetPath": asset_path}).text


@mcp.tool()
def focus_asset_editor(asset_path: str) -> str:
    """Focus an already-open asset editor."""
    return httpx.post(f"{app.BASE_URL}/editor/assets/focus", json={"AssetPath": asset_path}).text


@mcp.tool()
def close_asset_editor(asset_path: str, confirm: bool = False) -> str:
    """Close all editors for an asset; requires confirm=True."""
    return httpx.request("DELETE", f"{app.BASE_URL}/editor/assets", json={
        "AssetPath": asset_path, "bConfirm": confirm
    }).text


@mcp.tool()
def get_content_browser_selection() -> str:
    """List assets selected in the primary UE Content Browser."""
    return httpx.get(f"{app.BASE_URL}/editor/assets/selected").text


@mcp.tool()
def select_content_browser_assets(asset_paths: list[str]) -> str:
    """Select assets in the Content Browser without forcing it to the foreground."""
    return httpx.post(f"{app.BASE_URL}/editor/assets/select", json={
        "AssetPaths": asset_paths
    }).text


@mcp.tool()
def reveal_content_browser_assets(asset_paths: list[str]) -> str:
    """Select assets and focus their location in the UE Content Browser."""
    return httpx.post(f"{app.BASE_URL}/editor/assets/reveal", json={
        "AssetPaths": asset_paths
    }).text


@mcp.tool()
def list_ue_classes(search: str = "", parent_class: str = "", category: str = "", source: str = "", module: str = "",
                    can_be_parent: bool = False, include_abstract: bool = False, limit: int = 200) -> str:
    """Find classes by name, parent, category or origin, including Blueprints that are not loaded and custom C++ classes.

    To choose a Blueprint's parent, pass can_be_parent=True. Native classes in modules that are not loaded are not listed.
    search: part of the class name.
    parent_class: a name such as Actor, or a path such as /Script/Engine.Actor or /Game/Folder/BP_Name.BP_Name_C.
    category: character, pawn, player_controller, game_mode, game_state, player_state, hud, actor, scene_component,
    actor_component, widget, anim_instance, data_asset, interface or object. Loaded classes also match their own
    Category or ClassGroupNames metadata, such as Rendering.
    source: engine_cpp, project_cpp (the project and its plugins) or blueprint.
    module: a C++ module name such as Engine or DemoForPlugin.
    """
    return httpx.get(f"{app.BASE_URL}/ue/classes", timeout=120, params={
        "search": search, "class_path": parent_class, "category": category, "source": source, "module": module,
        "can_be_parent": str(can_be_parent).lower(), "include_abstract": str(include_abstract).lower(), "limit": limit
    }).text


@mcp.tool()
def describe_ue_class(class_path: str) -> str:
    """Get UE class metadata, Blueprint-callable functions, properties, and parameter types."""
    return httpx.get(f"{app.BASE_URL}/ue/classes/describe", params={"class_path": class_path}).text


@mcp.tool()
def consolidate_assets(target_path: str, source_paths: list[str], operation: str = "Inspect",
                       expected_snapshot: str = "", allow_irreversible: bool = False,
                       confirm: bool = False, dry_run: bool = True) -> str:
    """Consolidate 1..64 same-class assets into target via native ObjectTools::ConsolidateObjects.
    Inspect returns per-source referencers as `snapshot`. Consolidate needs confirm, allow_irreversible and
    the exact snapshot; it is NOT undoable, dirties referencers and does not save. Unverified.
    """
    return _ext("/assets/consolidate", {"Operation": operation, "TargetPath": target_path, "Paths": source_paths,
        "ExpectedSnapshot": expected_snapshot, "bAllow": allow_irreversible, "bConfirm": confirm, "bDryRun": dry_run})


@mcp.tool()
def create_asset(asset_path: str, kind: str, parent_path: str = "", skeleton_path: str = "", struct_path: str = "",
                 animation_path: str = "", dry_run: bool = False, save: bool = False) -> str:
    """Create a new asset at an unused /Game path. Existing assets are never overwritten. Requires stopped PIE.

    kind and what it needs:
    material, physical_material, curve_float, curve_vector, curve_linear_color: nothing else
    material_instance: parent_path
    data_table: struct_path, a row struct such as /Script/GameplayTags.GameplayTagTableRow
    anim_blueprint, blend_space, blend_space_1d: skeleton_path
    montage: animation_path

    Other asset types have their own tools; find them with find_tools. Undo does not remove a created asset; use delete_asset.
    """
    return httpx.post(f"{app.BASE_URL}/assets/create", json={
        "AssetPath": asset_path, "Kind": kind, "ParentPath": parent_path, "SkeletonPath": skeleton_path,
        "StructPath": struct_path, "AnimationPath": animation_path, "bDryRun": dry_run, "bSave": save
    }).text
