"""Enhanced Input actions and mapping contexts."""
import httpx

from . import app
from .app import mcp, _asset_request


@mcp.tool()
def inspect_input_action(asset_path: str) -> str:
    """Inspect an Enhanced Input Action asset."""
    return httpx.get(f"{app.BASE_URL}/input-actions/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_input_action_settings(asset_path: str, properties: dict,
                               save: bool = False) -> str:
    """Edit reflected Enhanced Input Action settings such as ValueType or bConsumeInput."""
    return _asset_request("input-actions/settings", asset_path, properties, save=save)


@mcp.tool()
def inspect_input_mapping_context(asset_path: str) -> str:
    """Inspect Enhanced Input Action-to-key mappings."""
    return httpx.get(f"{app.BASE_URL}/input-mapping-contexts/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_input_mapping_context_settings(asset_path: str, properties: dict,
                                        save: bool = False) -> str:
    """Edit reflected Enhanced Input Mapping Context settings."""
    return _asset_request("input-mapping-contexts/settings", asset_path, properties, save=save)


@mcp.tool()
def map_input_action(mapping_context_path: str, action_path: str, key: str) -> str:
    """Map an Enhanced Input Action to a key name such as SpaceBar or W."""
    return httpx.post(f"{app.BASE_URL}/input-mapping-contexts/mappings", json={
        "AssetPath": mapping_context_path, "ActionPath": action_path, "Key": key
    }).text


@mcp.tool()
def replace_input_action_key(mapping_context_path: str, action_path: str,
                             key: str, new_key: str) -> str:
    """Replace one key mapping for an Enhanced Input Action."""
    return httpx.patch(f"{app.BASE_URL}/input-mapping-contexts/mappings", json={
        "AssetPath": mapping_context_path, "ActionPath": action_path,
        "Key": key, "NewKey": new_key
    }).text


@mcp.tool()
def unmap_input_action(mapping_context_path: str, action_path: str, key: str) -> str:
    """Remove an Enhanced Input Action key mapping."""
    return httpx.request("DELETE", f"{app.BASE_URL}/input-mapping-contexts/mappings", json={
        "AssetPath": mapping_context_path, "ActionPath": action_path, "Key": key
    }).text
