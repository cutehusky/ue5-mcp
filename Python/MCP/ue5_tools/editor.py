"""Editor status, logs, undo, selection and utilities."""
import httpx

from . import app
from .app import mcp, _ext


@mcp.tool()
def get_ue_editor_status() -> str:
    """Get current UE editor, world, map, play-state, engine, and selection status."""
    return httpx.get(f"{app.BASE_URL}/editor/status").text


@mcp.tool()
def get_editor_logs(search: str = "", severity: str = "", category: str = "", since_line: int = 0, limit: int = 200) -> str:
    """Read the newest lines of this editor session's Output Log, with filters.

    search: text in the line. severity: Fatal, Error, Warning, Display, Log or Verbose. category: such as LogBlueprint.
    since_line: pass the previous reply's next_line to read only what is new.
    """
    return httpx.get(f"{app.BASE_URL}/editor/logs", params={
        "search": search, "severity": severity, "category": category, "since_line": since_line, "limit": limit
    }).text


@mcp.tool()
def execute_console_command(command: str, confirm: bool = False) -> str:
    """Run one Unreal console command or console variable, in the play session if one is running. Requires confirm=True.

    Examples: stat fps, r.ScreenPercentage 100, showdebug collision. Most commands cannot be undone.
    Refuses quit, exit, crash and debug commands, and py and python.
    """
    return httpx.post(f"{app.BASE_URL}/editor/console", timeout=120, json={"Value": command, "bConfirm": confirm}).text


@mcp.tool()
def list_blueprint_errors(root: str = "/Game", search: str = "", include_warnings: bool = False, limit: int = 200) -> str:
    """Compile the Blueprints under a /Game folder and return those with errors, with each message and node.

    Assets are not saved or left marked as edited. Loading and compiling a large folder is slow, so narrow root or search.
    limit caps how many are checked; truncated says if some were not. Requires stopped play.
    """
    return httpx.post(f"{app.BASE_URL}/blueprints/errors", timeout=1800, json={
        "AssetPath": root, "Key": search, "bWait": include_warnings, "TimeoutSeconds": limit}).text


@mcp.tool()
def get_project_errors(limit: int = 100) -> str:
    """Summarise current problems: this session's log errors, editor Message Log pages and the last C++ build's errors.

    Read-only. Blueprints are not compiled; use list_blueprint_errors for them.
    """
    return httpx.get(f"{app.BASE_URL}/project/errors", params={"limit": limit}, timeout=60).text


@mcp.tool()
def run_editor_map_check() -> str:
    """Run UE Map Check for the active editor world without opening result dialogs."""
    return httpx.post(f"{app.BASE_URL}/editor/map-check", json={}).text


@mcp.tool()
def undo_ue_editor_transaction() -> str:
    """Undo the latest UE editor transaction, such as an actor or asset edit."""
    return httpx.post(f"{app.BASE_URL}/editor/transactions/undo", json={}).text


@mcp.tool()
def redo_ue_editor_transaction() -> str:
    """Redo the latest undone UE editor transaction."""
    return httpx.post(f"{app.BASE_URL}/editor/transactions/redo", json={}).text


@mcp.tool()
def get_ue_editor_selection() -> str:
    """List actors currently selected in the UE level editor."""
    return httpx.get(f"{app.BASE_URL}/editor/selection").text


@mcp.tool()
def clear_editor_selection() -> str:
    """Clear the level-editor actor selection."""
    return httpx.post(f"{app.BASE_URL}/editor/actors/clear-selection", json={}).text


@mcp.tool()
def game_feature_plugins(operation: str = "Inspect", plugin_name: str = "", expected_state: str = "",
                         allow: bool = False, confirm: bool = False, dry_run: bool = True) -> str:
    """Game Feature plugins: Inspect (names/URLs/native states) and Activate/Deactivate/Unload requests.
    Mutations need confirm and expected_state equal to the current native state name. Unload and PIE-time
    changes need allow. Transitions are asynchronous: poll Inspect. Unverified.
    """
    return _ext("/game-features", {"Operation": operation, "Name": plugin_name, "ExpectedSnapshot": expected_state,
        "bAllow": allow, "bConfirm": confirm, "bDryRun": dry_run})


@mcp.tool()
def editor_utilities(operation: str = "Inspect", path_filter: str = "/Game", asset_path: str = "",
                     start: int = 0, count: int = 64, allow_code_execution: bool = False,
                     confirm: bool = False, dry_run: bool = True) -> str:
    """Editor Utility Widgets/Blueprints: Inspect (paged discovery), SpawnTab (widget) or Run (TryRun).
    Running executes project editor code: needs confirm and allow_code_execution in a stopped editor.
    Side effects are not transactional. Unverified.
    """
    return _ext("/editor-utilities", {"Operation": operation, "PathFilter": path_filter, "AssetPath": asset_path,
        "Start": start, "Count": count, "bAllow": allow_code_execution, "bConfirm": confirm, "bDryRun": dry_run})
