"""Blueprint debugging, C++ class creation and Live Coding."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def list_blueprint_breakpoints(bp_path: str) -> str:
    """List a Blueprint's breakpoints with their node ids."""
    return httpx.get(f"{app.BASE_URL}/blueprints/breakpoints", params={"asset_path": bp_path}).text


@mcp.tool()
def edit_blueprint_breakpoint(bp_path: str, operation: str, node_id: str = "", timeout_seconds: int = 300) -> str:
    """Add, remove, enable or disable a breakpoint, or clear_all. Adding needs a windowed editor, not -nullrhi.

    node_id: the node's Id from get_graph. Not needed for clear_all. Event nodes do not pause; use the first node after one.
    timeout_seconds: if a hit stays paused this long (10-3600), the editor disables that breakpoint and resumes.
    While paused, other editor routes are refused, so use inspect_blueprint_debug_state and control_blueprint_debugger.
    """
    return httpx.post(f"{app.BASE_URL}/blueprints/breakpoints", json={
        "AssetPath": bp_path, "Operation": operation, "NodeId": node_id, "TimeoutSeconds": timeout_seconds}).text


@mcp.tool()
def inspect_blueprint_debug_state(search: str = "", limit: int = 200) -> str:
    """Report whether a breakpoint has paused the game and, if so, the node, call stack, locals and Blueprint variables."""
    return httpx.get(f"{app.BASE_URL}/blueprints/debug/state", params={"search": search, "limit": limit}).text


@mcp.tool()
def control_blueprint_debugger(operation: str) -> str:
    """Continue from a breakpoint. operation must be: resume, step_in, step_over, or step_out."""
    return httpx.post(f"{app.BASE_URL}/blueprints/debug/control", json={"Operation": operation}).text


@mcp.tool()
def create_cpp_class(class_name: str, parent_path: str = "/Script/Engine.Actor", module_name: str = "",
                     dry_run: bool = False, confirm: bool = False) -> str:
    """Add a C++ class to a project module, writing its .h and .cpp files. Requires confirm unless dry_run.

    class_name excludes the A or U prefix. The result says whether the class is loaded or the project must be rebuilt.
    Like the editor's New C++ Class, this regenerates project files and can add a module dependency to the .uproject.
    """
    return httpx.post(f"{app.BASE_URL}/project/cpp-classes", timeout=600, json={
        "ClassName": class_name, "ParentPath": parent_path, "ModuleName": module_name, "bDryRun": dry_run, "bConfirm": confirm}).text


@mcp.tool()
def get_live_coding_status() -> str:
    """Report whether Live Coding is available, enabled and compiling."""
    return httpx.get(f"{app.BASE_URL}/build/live-coding").text


@mcp.tool()
def compile_cpp_with_live_coding(wait: bool = True) -> str:
    """Compile changed C++ with Live Coding. Result is success, no_changes, in_progress or failure.

    Live Coding can't add classes or change class layouts; for those, close the editor and build the project.
    wait blocks the editor until the compile ends.
    """
    return httpx.post(f"{app.BASE_URL}/build/live-coding", timeout=1800, json={"bWait": wait}).text
