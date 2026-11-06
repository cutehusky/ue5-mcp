"""Data Tables and Data Assets."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def get_data_table_rows(asset_path: str) -> str:
    """Read all rows from a DataTable as JSON, including the row struct path."""
    response = httpx.get(f"{app.BASE_URL}/data-tables/rows", params={"asset_path": asset_path})
    return response.text


@mcp.tool()
def upsert_data_table_row(asset_path: str, row_name: str, row_json: str) -> str:
    """Create or replace a DataTable row.

    row_json must be a JSON object matching the DataTable's row struct.
    """
    response = httpx.put(f"{app.BASE_URL}/data-tables/rows", json={
        "AssetPath": asset_path, "RowName": row_name, "RowJson": row_json
    })
    return response.text


@mcp.tool()
def delete_data_table_row(asset_path: str, row_name: str) -> str:
    """Delete a row from a DataTable."""
    response = httpx.request("DELETE", f"{app.BASE_URL}/data-tables/rows", json={
        "AssetPath": asset_path, "RowName": row_name
    })
    return response.text


@mcp.tool()
def inspect_data_asset(asset_path: str) -> str:
    """Inspect a UDataAsset or UPrimaryDataAsset."""
    return httpx.get(f"{app.BASE_URL}/data-assets/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def create_data_asset(asset_path: str, asset_class: str) -> str:
    """Create a Data Asset from a non-abstract UDataAsset-derived class."""
    return httpx.post(f"{app.BASE_URL}/data-assets/create", json={
        "AssetPath": asset_path, "AssetClass": asset_class
    }).text


@mcp.tool()
def validate_data_asset(asset_path: str, asset_class: str = "") -> str:
    """Validate a Data Asset and optional derived class compatibility."""
    return httpx.post(f"{app.BASE_URL}/data-assets/validate", json={
        "AssetPath": asset_path, "AssetClass": asset_class
    }).text
