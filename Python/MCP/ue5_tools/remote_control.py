"""Remote Control Presets."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def list_remote_control_presets(search: str = "", limit: int = 100) -> str:
    """List Remote Control Preset assets from the asset registry."""
    return httpx.get(f"{app.BASE_URL}/remote-control/presets", params={"search": search, "limit": limit}, timeout=180).text


@mcp.tool()
def inspect_remote_control_preset(asset_path: str) -> str:
    """Inspect a preset's exposed properties and functions, bound objects and current property values.

    Bound objects resolve only while their world or asset is loaded. Exposed actors
    and protocol bindings are not listed.
    """
    return httpx.get(f"{app.BASE_URL}/remote-control/presets/inspect", params={"asset_path": asset_path}, timeout=180).text


@mcp.tool()
def create_remote_control_preset(asset_path: str, confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Create an empty Remote Control Preset in an unused /Game package."""
    return httpx.post(f"{app.BASE_URL}/remote-control/presets", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def expose_remote_control_field(asset_path: str, object_path: str, field_path: str, expected_entity_count: int,
                                kind: str = "property", label: str = "", confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Expose an editable property or BlueprintCallable function of a loaded editor object on a preset.

    kind is property or function; field_path is a property path or function name.
    expected_entity_count is the inspected entity_count. An empty label uses the native generated one;
    a label already in use is refused. Requires stopped PIE and confirmation.
    """
    return httpx.post(f"{app.BASE_URL}/remote-control/presets/expose", json={
        "AssetPath": asset_path, "ObjectPath": object_path, "FieldPath": field_path, "Kind": kind, "Label": label,
        "ExpectedEntityCount": expected_entity_count, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def unexpose_remote_control_field(asset_path: str, entity_id: str, expected_label: str, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Remove an exposed property or function from a preset, guarded by its inspected id and label."""
    return httpx.post(f"{app.BASE_URL}/remote-control/presets/unexpose", json={
        "AssetPath": asset_path, "EntityId": entity_id, "ExpectedLabel": expected_label,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_remote_control_value(asset_path: str, entity_id: str, expected_label: str, expected_value: str, value: str,
                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set an exposed property on its bound objects using UE text, guarded by the inspected label and value.

    Writes the bound objects in a transaction and marks them dirty; save them through
    their own map or asset. Array-element paths are not supported. Requires stopped PIE.
    """
    return httpx.patch(f"{app.BASE_URL}/remote-control/presets/value", json={
        "AssetPath": asset_path, "EntityId": entity_id, "ExpectedLabel": expected_label,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
