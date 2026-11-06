"""Widget Blueprints."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def create_widget_blueprint(bp_path: str, parent_class: str = "/Script/UMG.UserWidget") -> str:
    """Create a real UWidgetBlueprint, optionally derived from a UUserWidget class."""
    return httpx.post(f"{app.BASE_URL}/widget-blueprints/create", json={
        "BpPath": bp_path, "ParentClass": parent_class
    }).text


@mcp.tool()
def list_widget_blueprint_widgets(asset_path: str) -> str:
    """List Widget Blueprint widgets, classes, parents, and child indices."""
    response = httpx.get(f"{app.BASE_URL}/widget-blueprints/widgets", params={"asset_path": asset_path})
    return response.text


@mcp.tool()
def add_widget_to_blueprint(asset_path: str, widget_class: str,
                            widget_name: str, parent_name: str = "") -> str:
    """Add a UMG widget to the root or to an existing panel widget."""
    response = httpx.post(f"{app.BASE_URL}/widget-blueprints/widgets", json={
        "AssetPath": asset_path, "WidgetClass": widget_class,
        "WidgetName": widget_name, "ParentName": parent_name
    })
    return response.text


@mcp.tool()
def remove_widget_from_blueprint(asset_path: str, widget_name: str) -> str:
    """Remove a widget and its descendants from a Widget Blueprint."""
    response = httpx.request("DELETE", f"{app.BASE_URL}/widget-blueprints/widgets", json={
        "AssetPath": asset_path, "WidgetName": widget_name
    })
    return response.text


@mcp.tool()
def set_widget_properties(asset_path: str, widget_name: str, properties: dict) -> str:
    """Set reflected Widget properties such as text, visibility, anchors, or render transform."""
    response = httpx.patch(f"{app.BASE_URL}/widget-blueprints/widgets/properties", json={
        "AssetPath": asset_path, "WidgetName": widget_name, "Properties": properties
    })
    return response.text


@mcp.tool()
def reparent_widget(asset_path: str, widget_name: str, new_parent_name: str) -> str:
    """Move a Widget Blueprint widget under another panel widget."""
    response = httpx.patch(f"{app.BASE_URL}/widget-blueprints/widgets/reparent", json={
        "AssetPath": asset_path, "WidgetName": widget_name,
        "NewParentName": new_parent_name
    })
    return response.text
