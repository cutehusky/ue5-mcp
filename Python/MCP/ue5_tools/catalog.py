"""Advertised core tool set and the find_tools, describe_tool and call_tool catalog."""
import json

from . import app
from .app import mcp, args


# Listing all tools costs about 430k tokens, more than most clients' context. Clients see this core game-making set plus
# three catalog tools; everything else stays callable and is found with find_tools. --all-tools restores the full list.
CORE_TOOLS = frozenset("""
get_ue_editor_status get_editor_logs execute_console_command list_blueprint_errors get_project_errors undo_ue_editor_transaction redo_ue_editor_transaction get_editor_build_status
list_assets describe_asset get_asset_properties set_asset_properties save_asset duplicate_asset rename_asset delete_asset
create_asset get_asset_referencers validate_asset list_ue_classes describe_ue_class
create_blueprint compile_blueprint compile_editor_blueprints get_blueprint_graph get_graph organize_blueprint_graph
    edit_blueprint_breakpoint inspect_blueprint_debug_state control_blueprint_debugger create_cpp_class
    get_live_coding_status compile_cpp_with_live_coding
get_supported_nodes edit_blueprint_graph add_generic_node_to_graph add_event_to_graph add_function_call_to_graph add_variable_to_graph
add_branch_node_to_graph add_math_node_to_graph add_dynamic_cast_node_to_graph connect_pins break_pin_connection set_pin_default_value
create_function edit_function delete_function get_blueprint_functions
add_variable_to_bp delete_variable_from_bp edit_variable_in_bp get_blueprint_variables
get_components_of_bp add_component_to_bp remove_component_from_bp edit_component_in_bp get_component_properties set_component_property
inspect_blueprint_class_defaults set_blueprint_class_default inspect_project_game_settings set_project_game_setting
create_editor_world load_editor_world save_editor_world inspect_editor_world_settings set_editor_world_settings
list_editor_actors spawn_editor_actor place_editor_asset query_scene_actors duplicate_editor_actor edit_editor_actor_transform
set_editor_actor_properties delete_editor_actor list_actor_components add_actor_component get_actor_component_properties
set_actor_component_properties select_editor_actors get_ue_viewport set_ue_viewport
create_light_actor set_light create_box_volume build_navigation
inspect_material_asset list_material_parameters list_material_expressions create_material_expression connect_material_expressions
layout_material_expressions edit_material_settings validate_material set_material_parameter set_material_instance_parent
list_material_instance_parameters edit_material_instance_parameter set_static_mesh_material
import_fbx import_static_mesh import_texture import_sound_wave create_data_asset inspect_data_asset get_data_table_rows upsert_data_table_row delete_data_table_row
inspect_input_action inspect_input_mapping_context map_input_action unmap_input_action
create_widget_blueprint list_widget_blueprint_widgets add_widget_to_blueprint remove_widget_from_blueprint set_widget_properties reparent_widget
create_behavior_tree create_blackboard create_state_tree create_gameplay_tag inspect_gameplay_tags
inspect_animation_blueprint create_level_sequence create_sound_cue create_niagara_system
control_ue_play_session inspect_play_session read_play_actor_properties move_play_mouse send_play_input request_editor_screenshot get_editor_screenshot_status
list_editor_automation_tests control_editor_automation_test get_editor_automation_status package_game get_package_status cancel_package
""".split())

TOOL_DOMAINS = {
    "niagara": "niagara", "geometry_script": "geometry_script", "partition": "world_partition", "hlod": "world_partition",
    "data_layer": "world_partition", "pcg": "pcg", "landscape": "landscape", "foliage": "foliage", "state_tree": "state_tree",
    "behavior_tree": "ai", "blackboard": "ai", "environment_query": "ai", "perception": "ai", "nav": "navigation",
    "ability": "gameplay_abilities", "gameplay": "gameplay_abilities", "ik_": "ik_retarget", "retarget": "ik_retarget",
    "pose_search": "pose_search", "rig": "rigs", "skeleton": "animation", "animation": "animation", "montage": "animation",
    "blend": "animation", "sequence": "cinematics", "cinematic": "cinematics", "take": "cinematics", "material": "materials",
    "texture": "textures", "render_target": "textures", "sound": "audio", "audio": "audio", "metasound": "audio",
    "modulation": "audio", "dialogue": "audio", "widget": "ui", "light": "lighting", "fog": "lighting", "sky": "lighting",
    "post_process": "lighting", "reflection": "lighting", "spline": "splines", "volume": "volumes", "physics": "physics",
    "actor": "world", "editor_world": "world", "sublevel": "world", "bp": "blueprint", "blueprint": "blueprint", "graph": "blueprint",
    "asset": "assets", "static_mesh": "assets",
}


def _tool_domain(name: str) -> str:
    return next((domain for key, domain in TOOL_DOMAINS.items() if key in name), "other")


def _summary(description: str | None) -> str:
    return " ".join((description or "").split("\n\n")[0].split())[:160]


@mcp.tool()
async def find_tools(query: str = "", domain: str = "", limit: int = 15) -> str:
    """Search every Unreal tool, including those not listed. Empty query and domain returns domains with tool counts.

    query is keywords such as "niagara renderer color". Then use describe_tool and call_tool on a result.
    """
    tools = [t for t in await mcp.list_tools() if t.name not in CATALOG_TOOLS]
    if domain:
        tools = [t for t in tools if _tool_domain(t.name) == domain]
    elif not query:
        counts = {}
        for t in tools:
            counts[_tool_domain(t.name)] = counts.get(_tool_domain(t.name), 0) + 1
        return json.dumps({"total": len(tools), "domains": dict(sorted(counts.items()))})
    words = [w for w in query.lower().replace("_", " ").split() if w]

    def score(t):
        name, text = t.name.lower().replace("_", " "), (t.description or "").lower()
        return sum(3 * (w in name) + (w in text) for w in words)
    ranked = sorted(((score(t), t) for t in tools), key=lambda p: (-p[0], p[1].name))
    rows = [{"name": t.name, "domain": _tool_domain(t.name), "summary": _summary(t.description)}
            for points, t in ranked if points or not words][:max(1, min(limit, 50))]
    return json.dumps({"matches": rows})


@mcp.tool()
async def describe_tool(name: str) -> str:
    """Return one tool's full description and input schema, for use with call_tool."""
    tool = next((t for t in await mcp.list_tools() if t.name == name), None)
    if tool is None:
        return json.dumps({"errorMessage": f"Unknown tool {name}; use find_tools"})
    return json.dumps({"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema})


@mcp.tool()
async def call_tool(name: str, arguments: dict | None = None) -> str:
    """Run any Unreal tool by name, including those not listed. Take arguments from describe_tool."""
    if name in CATALOG_TOOLS or name not in {t.name for t in await mcp.list_tools()}:
        return json.dumps({"errorMessage": f"Unknown tool {name}; use find_tools"})
    try:
        result = await mcp.call_tool(name, arguments or {})
    except Exception as error:  # bad arguments must reach the caller as a result it can correct
        return json.dumps({"errorMessage": str(error)})
    blocks = result[0] if isinstance(result, tuple) else result
    return "\n".join(getattr(block, "text", str(block)) for block in blocks)


CATALOG_TOOLS = frozenset({"find_tools", "describe_tool", "call_tool"})


async def _list_advertised_tools():
    tools = await mcp.list_tools()
    return tools if args.all_tools else [t for t in tools if t.name in CORE_TOOLS or t.name in CATALOG_TOOLS]


mcp._mcp_server.list_tools()(_list_advertised_tools)
