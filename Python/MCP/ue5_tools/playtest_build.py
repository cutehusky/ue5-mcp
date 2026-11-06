"""Play-In-Editor, screenshots, automation tests, project game settings and packaging."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def start_play_in_editor() -> str:
    """Queue an in-process Play-In-Editor session on the current editor map.

    The engine starts it on its next tick; poll get_ue_editor_status for is_playing.
    Refused while a session is running or queued.
    """
    return httpx.post(f"{app.BASE_URL}/editor/pie/start", timeout=60).text


@mcp.tool()
def stop_play_in_editor() -> str:
    """Request the end of the running Play-In-Editor session (ends on the next tick)."""
    return httpx.post(f"{app.BASE_URL}/editor/pie/stop", timeout=60).text


@mcp.tool()
def control_ue_play_session(operation: str) -> str:
    """Control the UE play session. operation must be: start, start_here, pause, resume, or stop.

    start plays from the PlayerStart, like a real game; poll get_ue_editor_status for is_playing.
    start_here plays from the active viewport camera, and no pawn spawns if the camera is inside geometry.
    """
    return httpx.post(f"{app.BASE_URL}/editor/play", json={"Operation": operation}).text


@mcp.tool()
def list_editor_automation_tests(search: str = "", limit: int = 200) -> str:
    """Discover local UE automation tests valid for the current editor environment."""
    return httpx.get(f"{app.BASE_URL}/editor/automation", params={
        "search": search, "limit": limit
    }).text


def run_editor_automation_test(test_name: str) -> str:
    """Start one exact discovered, single-participant UE automation test."""
    return httpx.post(f"{app.BASE_URL}/editor/automation", json={
        "Operation": "run", "TestName": test_name
    }).text


@mcp.tool()
def get_editor_automation_status() -> str:
    """Get completion, success, duration, warnings, errors, and entries for the current test."""
    return httpx.get(f"{app.BASE_URL}/editor/automation/status").text


def stop_editor_automation_test() -> str:
    """Stop the currently running local UE automation test."""
    return httpx.post(f"{app.BASE_URL}/editor/automation", json={
        "Operation": "stop"
    }).text


@mcp.tool()
def request_editor_screenshot(filename: str = "UE5MCP_Screenshot",
                              show_ui: bool = False) -> str:
    """Request a deterministic PNG screenshot under Saved/Screenshots/UE5MCP."""
    return httpx.post(f"{app.BASE_URL}/editor/screenshots", json={
        "Filename": filename, "bShowUI": show_ui
    }).text


@mcp.tool()
def get_editor_screenshot_status() -> str:
    """Report whether the latest requested editor screenshot has been written."""
    return httpx.get(f"{app.BASE_URL}/editor/screenshots").text


@mcp.tool()
def compile_editor_blueprints(asset_paths: list[str] | None = None,
                              save: bool = False) -> str:
    """Compile specified Blueprints, or selected Content Browser Blueprints.

    This tool intentionally does not claim or initiate C++ hot reload.
    """
    return httpx.post(f"{app.BASE_URL}/editor/compile", json={
        "AssetPaths": asset_paths or [], "bSave": save
    }).text


@mcp.tool()
def get_editor_build_status() -> str:
    """Report asset/shader compilation, redirector fix-up, automation, and PIE activity."""
    return httpx.get(f"{app.BASE_URL}/editor/build-status").text


@mcp.tool()
def inspect_project_game_settings() -> str:
    """Read the project's default game map, editor startup map, default GameMode and GameInstance class."""
    return httpx.get(f"{app.BASE_URL}/project/game-settings", timeout=60).text


@mcp.tool()
def set_project_game_setting(setting: str, expected_value: str, value: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Set GameDefaultMap, EditorStartupMap, GlobalDefaultGameMode or GameInstanceClass.

    The map or class must exist and fit the setting. Writes Config/DefaultEngine.ini immediately; not undoable.
    """
    return httpx.patch(f"{app.BASE_URL}/project/game-settings", json={
        "PropertyPath": setting, "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=60).text


@mcp.tool()
def inspect_play_session(search: str = "", limit: int = 200) -> str:
    """Observe the running PIE game: time, GameMode, player pawn location/velocity and live actors."""
    return httpx.get(f"{app.BASE_URL}/play-session", params={"search": search, "limit": limit}, timeout=60).text


@mcp.tool()
def read_play_actor_properties(actor: str, search: str = "", limit: int = 200) -> str:
    """Read live values from an actor in the running game, such as a score.

    actor: game_mode, player_pawn, or part of an actor's path or class name.
    search: part of a property name. Empty lists only variables declared in Blueprints.
    """
    return httpx.get(f"{app.BASE_URL}/play-session/properties", params={"actor": actor, "search": search, "limit": limit}, timeout=60).text


@mcp.tool()
def move_play_mouse(actor: str = "", world_location: list[float] | None = None, screen_x: float = 0, screen_y: float = 0) -> str:
    """Point the mouse in the running game and report what is under it. Then click with send_play_input.

    Aim with one of: actor (part of a path or class name), world_location [x, y, z], or screen_x and screen_y in viewport pixels.
    Needs a windowed editor, and moves the real system cursor, so a person using the mouse can move it away.
    """
    if world_location is not None and len(world_location) != 3:
        raise ValueError("world_location must be [x, y, z]")
    x, y, z = world_location or (0, 0, 0)
    return httpx.post(f"{app.BASE_URL}/play-session/mouse", timeout=60, json={
        "Actor": actor, "bUseWorldLocation": world_location is not None, "WorldX": x, "WorldY": y, "WorldZ": z,
        "ScreenX": screen_x, "ScreenY": screen_y}).text


@mcp.tool()
def send_play_input(key: str, event: str = "press", amount: float = 1.0) -> str:
    """Send a key to the running PIE game's first player, to playtest it.

    key is an FKey name (W, SpaceBar, LeftMouseButton, Gamepad_LeftX). event is press, release or axis.
    A pressed key stays down until released.
    """
    return httpx.post(f"{app.BASE_URL}/play-session/input", json={"Key": key, "Event": event, "Amount": amount}, timeout=60).text


@mcp.tool()
def package_game(platform: str = "Win64", configuration: str = "Development", allow_dirty: bool = False,
                 confirm: bool = False, dry_run: bool = False) -> str:
    """Start packaging the project in the background with RunUAT BuildCookRun; poll get_package_status.

    Output goes to Saved/MCPBuilds. Refused while packages are unsaved unless allow_dirty, since cooking reads disk.
    """
    return httpx.post(f"{app.BASE_URL}/build/package", json={
        "Platform": platform, "Configuration": configuration, "bAllowDirty": allow_dirty, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=120).text


@mcp.tool()
def get_package_status(log_lines: int = 40) -> str:
    """Report the current package job: running, exit code, output folder and the end of its log."""
    return httpx.get(f"{app.BASE_URL}/build/package", params={"log_lines": log_lines}, timeout=60).text


@mcp.tool()
def cancel_package() -> str:
    """Stop the running package job and its child processes."""
    return httpx.post(f"{app.BASE_URL}/build/package/cancel", json={}, timeout=60).text


@mcp.tool()
def inspect_gameplay_calculation_definition(class_path: str) -> str:
    """Inspect native effect calculation attribute captures: field, source/target, snapshot.

    Reads loaded calculation defaults and native capture definitions without executing
    a calculation. Includes bounded capture rows and invalid attribute markers.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/calculation-definition", params={
        "class_path": class_path
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_evaluation_channels() -> str:
    """Inspect native GAS evaluation-channel enablement, IDs, aliases and validity."""
    return httpx.get(f"{app.BASE_URL}/ability-system/evaluation-channels", timeout=180).text


@mcp.tool()
def validate_gameplay_definition(class_path: str) -> str:
    """Validate loaded native or current compiled GAS ability/effect/calculation/cue defaults on a temporary duplicate.

    Returns native Valid/Invalid/NotValidated diagnostics and effect dependency graph
    errors. valid is true only for native Valid without errors. Does not compile
    Blueprints or execute runtime abilities/effects.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/validate", params={
        "class_path": class_path
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_definition_defaults(class_path: str) -> str:
    """Read GAS defaults, parent differences, enum options and reference constraints.

    Requires loaded native or current compiled Blueprint class. Returns <=128 fields
    with <=4096 characters of native text each and explicit truncation. Field discovery
    does not imply every type is supported by defaults editing. Does not load or compile.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/defaults", params={
        "class_path": class_path
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
control_editor_automation_test = merged_tool("control_editor_automation_test", {
    "run_editor_automation_test": run_editor_automation_test,
    "stop_editor_automation_test": stop_editor_automation_test,
})
