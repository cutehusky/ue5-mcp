"""Blueprint assets, graphs, nodes, functions, variables and components."""
import json

import httpx

from . import app
from .app import merged_tool
from .app import mcp, _unsupported


@mcp.tool()
def create_blueprint(bp_path: str, parent_class: str) -> str:
    """Create a new Unreal Engine Blueprint.

    parent_class: Must be a valid Unreal Engine class name.
    bp_path: Must be a valid Blueprint path starting with /Game/
    """
    url = f"{app.BASE_URL}/blueprint"
    body = {"ParentClass": parent_class, "BpPath": bp_path}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def create_function(bp_path: str, function_name: str, input_signature: str, output_signature: str) -> str:
    """Create a new function in the Blueprint.

    bp_path: Must be a valid Blueprint path
    function_name: Must be a valid function name.
    input_signature: Must be a valid input signature string in c++ style.
    output_signature: Must be a valid output signature string in c++ style.
    """
    url = f"{app.BASE_URL}/blueprints/functions"
    body = {"BpPath": bp_path, "FunctionName": function_name, "FunctionInputSignature": input_signature,
            "FunctionOutputSignature": output_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def edit_function(bp_path: str, function_name: str, input_signature: str, output_signature: str) -> str:
    """Edit an existing function in the Blueprint.
    Caution: Changing function signatures not change existing function calls or references, may break the Blueprint.

    bp_path: Must be a valid Blueprint path
    function_name: Must be a valid existing function name
    input_signature: Must be a valid new input signature string
    output_signature: Must be a valid new output signature string
    """
    url = f"{app.BASE_URL}/blueprints/functions"
    body = {"BpPath": bp_path, "FunctionName": function_name, "FunctionInputSignature": input_signature,
            "FunctionOutputSignature": output_signature}
    response = httpx.patch(url, json=body)
    return response.text


@mcp.tool()
def delete_function(bp_path: str, function_name: str) -> str:
    """Delete a function from the Blueprint.
    Caution: Deleting a function not remove existing function calls or references, may break the Blueprint.

    bp_path: Must be a valid Blueprint path
    function_name: Must be a valid existing function name.
    """
    url = f"{app.BASE_URL}/blueprints/functions"
    body = {"BpPath": bp_path, "FunctionName": function_name}
    response = httpx.request("DELETE", url, json=body)
    return response.text


@mcp.tool()
def add_function_call_to_graph(bp_path: str, graph_name: str, function_name: str, class_to_call: str) -> str:
    """Add a function call node to the specified graph in the Blueprint.

    bp_path: Must be a valid Blueprint path
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    function_name: Must be a valid existing function name, you can use get_blueprint_functions to get the list of functions.
    class_to_call: Must be a valid Unreal Engine class name, leave empty to call function in the same Blueprint.
    """
    url = f"{app.BASE_URL}/add_function_call_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "FunctionName": function_name}
    if class_to_call:
        body["ClassToCall"] = class_to_call
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_event_to_graph(bp_path: str, graph_name: str, event_name: str, is_custom: bool = False,
                       event_signature: str = None) -> str:
    """Add an event (custom or built-in) to the specified graph in the Blueprint.
    Caution: it doesn't check duplicated event names, may cause compile errors

    bp_path: Must be a valid Blueprint path
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    event_name: Must be a valid event name
    for custom event, it can be any name you like but cannot conflict with existing function or event names.
    for built-in event, it must be a valid built-in event name, you can use get_blueprint_functions to get the list of functions, functions starting with 'Receive' are built-in events.
    is_custom: Set to True for custom events, False for built-in events.
    event_signature: Required only for custom events, must be a valid signature string in c++ style.
    """
    url = f"{app.BASE_URL}/add_event_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "EventName": event_name, "bIsCustomEvent": is_custom}
    if is_custom and event_signature:
        body["EventSignature"] = event_signature
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_variable_to_graph(bp_path: str, graph_name: str, var_name: str, is_setter: bool) -> str:
    """Add a variable node (setter or getter) to the specified graph in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    var_name: Must be a valid variable name (e.g., 'Test' or 'DefaultSceneRoot').
    is_setter: Set to True for a setter node, False for a getter node.
    """
    url = f"{app.BASE_URL}/add_variable_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "VarName": var_name, "bIsSetter": is_setter}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def get_blueprint_variables(bp_path: str) -> str:
    """Get the list of variables in the Blueprint.

    bp_path: Must be a valid Blueprint path
    """
    url = f"{app.BASE_URL}/blueprints/variables"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def get_blueprint_functions(bp_path: str) -> str:
    """Get the list of functions in the Blueprint.

    bp_path: Must be a valid Blueprint path
    """
    url = f"{app.BASE_URL}/blueprints/functions"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def get_graph(bp_path: str, graph_name: str) -> str:
    """Get the details of a specific graph structure (nodes and connections) in the Blueprint.

    bp_path: Must be a valid Blueprint path
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    """
    url = f"{app.BASE_URL}/blueprints/graphs"
    params = {"bp_path": bp_path, "graph_name": graph_name}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def compile_blueprint(bp_path: str) -> str:
    """Compile the Blueprint and return success, error and warning counts, and each message with its node.

    bp_path: Must be a valid Blueprint path
    """
    url = f"{app.BASE_URL}/blueprints/compile"
    response = httpx.post(url, json={"BpPath": bp_path})
    return response.text


@mcp.tool()
def get_supported_nodes() -> str:
    """Get the list of supported nodes for the Blueprint system."""
    url = f"{app.BASE_URL}/get_supported_nodes"
    response = httpx.get(url)
    return response.text


@mcp.tool()
def list_graph_node_types(graph_type: str = "blueprint") -> str:
    """List concrete node classes for blueprint, animation, material, or all graphs."""
    return httpx.post(f"{app.BASE_URL}/graphs/nodes/catalog", json={
        "NodeKind": graph_type
    }).text


@mcp.tool()
def add_variable_to_bp(bp_path: str, var_signature: str) -> str:
    """Add a new variable to the Blueprint.

    bp_path: Must be a valid Blueprint path.
    var_signature: Must be a valid single variable signature in c++ style (e.g., 'float NewVar').
    """
    url = f"{app.BASE_URL}/blueprints/variables"
    body = {"BpPath": bp_path, "VarSignature": var_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def delete_variable_from_bp(bp_path: str, var_name: str) -> str:
    """Delete a variable from the Blueprint.

    bp_path: Must be a valid Blueprint path.
    var_name: Must be a valid existing variable name (e.g., 'NewVar').
    """
    url = f"{app.BASE_URL}/blueprints/variables"
    body = {"BpPath": bp_path, "VarName": var_name}
    response = httpx.request("DELETE", url, json=body)
    return response.text


def rename_variable_in_bp(bp_path: str, old_var_name: str, new_var_name: str) -> str:
    """Rename a variable in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    old_var_name: Must be a valid existing variable name (e.g., 'NewVar').
    new_var_name: Must be a valid new variable name (e.g., 'RenamedVar').
    """
    return httpx.patch(f"{app.BASE_URL}/blueprints/variables", json={
        "BpPath": bp_path, "OldVarName": old_var_name, "NewVarName": new_var_name
    }).text


def set_variable_default_value_in_bp(bp_path: str, var_name: str, default_value: str) -> str:
    """Set the default value for a variable in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    var_name: Must be a valid existing variable name (e.g., 'NewVar').
    default_value: Must be a valid default value string for the variable type.
    """
    return httpx.patch(f"{app.BASE_URL}/blueprints/variables", json={
        "BpPath": bp_path, "VarName": var_name, "DefaultValue": default_value
    }).text


@mcp.tool()
def connect_pins(bp_path: str, graph_name: str, output_node_id: str, output_pin_name: str, input_node_id: str,
                 input_pin_name: str) -> str:
    """Connect pins between nodes in the specified graph.
    Node ids and pin name can be found in the graph structure from tool: get_graph.

    bp_path: Must be a valid Blueprint path
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    output_node_id: Must be a valid node ID.
    output_pin_name: Must be a valid pin name on the output node.
    input_node_id: Must be a valid node ID.
    input_pin_name: Must be a valid pin name on the input node.
    """
    url = f"{app.BASE_URL}/connect_pins"
    body = {"BpPath": bp_path, "GraphName": graph_name, "OutputNodeId": output_node_id,
            "OutputPinName": output_pin_name, "InputNodeId": input_node_id, "InputPinName": input_pin_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def break_pin_connection(bp_path: str, graph_name: str, output_node_id: str, output_pin_name: str, input_node_id: str,
                         input_pin_name: str) -> str:
    """Break the connection between pins in the specified graph.
    Node ids and pin name can be found in the graph structure from tool: get_graph.

    bp_path: Must be a valid Blueprint path.
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    output_node_id: Must be a valid node ID.
    output_pin_name: Must be a valid pin name on the output node.
    input_node_id: Must be a valid node ID.
    input_pin_name: Must be a valid pin name on the input node.
    """
    url = f"{app.BASE_URL}/break_pin_connection"
    body = {"BpPath": bp_path, "GraphName": graph_name, "OutputNodeId": output_node_id,
            "OutputPinName": output_pin_name, "InputNodeId": input_node_id, "InputPinName": input_pin_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def set_pin_default_value(bp_path: str, graph_name: str, node_id: str, pin_name: str, default_value: str) -> str:
    """Set the default value for a pin on a node in the specified graph.
    Node ids and pin name can be found in the graph structure from tool: get_graph.

    bp_path: Must be a valid Blueprint path.
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    node_id: Must be a valid node ID.
    pin_name: Must be a valid pin name.
    default_value: Must be a valid default value string for the pin type.
    """
    url = f"{app.BASE_URL}/set_pin_default_value"
    body = {"BpPath": bp_path, "GraphName": graph_name, "NodeId": node_id, "PinName": pin_name,
            "DefaultValue": default_value}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_generic_node_to_graph(bp_path: str, graph_name: str, node_type_name: str) -> str:
    """Add any concrete K2 node class returned by get_supported_nodes."""
    return httpx.post(f"{app.BASE_URL}/add_generic_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "NodeTypeName": node_type_name
    }).text


@mcp.tool()
def add_make_struct_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a Make Struct node."""
    return httpx.post(f"{app.BASE_URL}/add_make_struct_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info
    }).text


@mcp.tool()
def add_break_struct_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a Break Struct node."""
    return httpx.post(f"{app.BASE_URL}/add_break_struct_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info
    }).text


@mcp.tool()
def add_dynamic_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a Dynamic Cast node."""
    return httpx.post(f"{app.BASE_URL}/add_dynamic_cast_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info
    }).text


@mcp.tool()
def add_class_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a Class Cast node."""
    return httpx.post(f"{app.BASE_URL}/add_class_cast_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info
    }).text


@mcp.tool()
def add_enum_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a Byte-to-Enum Cast node."""
    return httpx.post(f"{app.BASE_URL}/add_enum_cast_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info
    }).text


@mcp.tool()
def add_math_node_to_graph(bp_path: str, graph_name: str, function_name: str) -> str:
    """Add a UKismetMathLibrary function node."""
    return httpx.post(f"{app.BASE_URL}/add_math_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "FunctionName": function_name
    }).text


@mcp.tool()
def add_comment_node_to_graph(bp_path: str, graph_name: str = "EventGraph",
                              comment: str = "") -> str:
    """Add a comment node."""
    return httpx.post(f"{app.BASE_URL}/add_comment_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": comment
    }).text


@mcp.tool()
def add_branch_node_to_graph(bp_path: str, graph_name: str = "EventGraph") -> str:
    """Add a Branch node."""
    return httpx.post(f"{app.BASE_URL}/add_branch_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name
    }).text


@mcp.tool()
def add_execution_sequence_node_to_graph(bp_path: str, graph_name: str = "EventGraph",
                                         output_count: int = 2) -> str:
    """Add an Execution Sequence node."""
    return httpx.post(f"{app.BASE_URL}/add_execution_sequence_node_to_graph", json={
        "BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": str(max(2, output_count))
    }).text


@mcp.tool()
def add_switch_node_to_graph(bp_path: str, graph_name: str = "EventGraph",
                             switch_type: str = "enum", extra_info: str = "") -> str:
    """Add one switch node using switch_type: enum, integer, string, or name.

    extra_info is the enum name for enum switches or the starting index for
    integer switches.
    """
    if switch_type.lower() not in {"enum", "integer", "int", "string", "name"}:
        return _unsupported("add_switch_node_to_graph", f"Unknown switch_type: {switch_type}")
    return httpx.post(f"{app.BASE_URL}/graphs/switch-nodes", json={
        "BpPath": bp_path, "GraphName": graph_name,
        "NodeKind": switch_type, "ExtraInfo": extra_info
    }).text


@mcp.tool()
def get_components_of_bp(bp_path: str) -> str:
    """Get the list of components in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    """
    url = f"{app.BASE_URL}/blueprints/components"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def add_component_to_bp(bp_path: str, component_class: str, component_name: str, attach_to: str) -> str:
    """Add a component to the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_class: Must be a valid component class name.
    component_name: Must be a valid component name. Must be unique within the Blueprint.
    attach_to: For SceneComponent only. Must be a valid parent component name (e.g., 'DefaultSceneRoot'). If left empty, attach to the first root component.
    """
    url = f"{app.BASE_URL}/blueprints/components"
    body = {"BpPath": bp_path, "ComponentClass": component_class, "ComponentName": component_name,
            "AttachTo": attach_to}
    response = httpx.post(url, json=body)
    return response.text


def rename_component_in_bp(bp_path: str, component_name: str, new_component_name: str) -> str:
    """Rename a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    new_component_name: Must be a valid new component name. Must be unique within the Blueprint.
    """
    return httpx.patch(f"{app.BASE_URL}/blueprints/components", json={
        "BpPath": bp_path, "ComponentName": component_name,
        "NewComponentName": new_component_name
    }).text


@mcp.tool()
def remove_component_from_bp(bp_path: str, component_name: str) -> str:
    """Remove a component from the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/blueprints/components", json={
        "BpPath": bp_path, "ComponentName": component_name
    }).text


def reattach_component_in_bp(bp_path: str, component_name: str, attach_to: str) -> str:
    """Reparent (reattach) a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    attach_to: Must be a valid new parent component name.
    """
    return httpx.patch(f"{app.BASE_URL}/blueprints/components", json={
        "BpPath": bp_path, "ComponentName": component_name, "AttachTo": attach_to
    }).text


@mcp.tool()
def get_component_properties(bp_path: str, component_name: str) -> str:
    """Get the properties of a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    """
    return httpx.get(f"{app.BASE_URL}/blueprints/components/properties", params={
        "bp_path": bp_path, "component_name": component_name
    }).text


@mcp.tool()
def set_component_property(bp_path: str, component_name: str, properties: dict) -> str:
    """Set properties for a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    properties: A dictionary of property paths to values:
    Property paths for multi-level properties are separated by dot (e.g., 'RelativeLocation.X', 'StaticMeshComponent.StaticMesh').
    For Array properties, use index as path (e.g., 'Tags.0', 'ChildrenComponents.1').
    Property values must be valid strings for the property type.
    For Struct properties, can set multiple fields at once using comma (e.g., 'RelativeLocation': 'X=0.5,Y=20,Z=100').
    For Object properties, use the full asset path (e.g., 'StaticMesh': '/Engine/BasicShapes/Cube.Cube').
    (e.g., {'RelativeLocation': 'X=0.5,Y=20,Z=100', 'StaticMesh': '/Engine/BasicShapes/Cube.Cube', 'Mobility': 'Movable'}).
    """
    url = f"{app.BASE_URL}/blueprints/components/properties"
    body = {"BpPath": bp_path, "ComponentName": component_name, "Properties": properties}
    response = httpx.patch(url, json=body)
    return response.text


@mcp.tool()
def get_blueprint_graph(bp_path: str, graph_name: str = "EventGraph") -> str:
    """Read nodes, pins, defaults and links from an event or function graph."""
    response = httpx.get(f"{app.BASE_URL}/blueprints/graphs", params={
        "bp_path": bp_path, "graph_name": graph_name
    })
    return response.text


@mcp.tool()
def organize_blueprint_graph(bp_path: str, graph_name: str = "EventGraph", column_spacing: int = 100, row_spacing: int = 48,
                             node_ids: list[str] | None = None, dry_run: bool = False) -> str:
    """Format a Blueprint graph so it reads left to right, with few crossings, no overlaps and straight execution lines.

    Works on event and function graphs, including those of Widget and Animation Blueprints. Handles cycles and separate
    groups of nodes, and resizes comments around their nodes. Undoable; use save_asset to keep the result.
    column_spacing, row_spacing: the gaps between nodes.
    node_ids: format only these nodes. Empty formats the whole graph.
    dry_run: report the positions and crossing counts without moving anything.
    """
    return httpx.post(f"{app.BASE_URL}/blueprints/graphs/layout", timeout=120, json={
        "BpPath": bp_path, "GraphName": graph_name, "ColumnSpacing": column_spacing, "RowSpacing": row_spacing,
        "NodeIds": node_ids or [], "bDryRun": dry_run
    }).text


@mcp.tool()
def list_blueprint_functions(class_path: str = "", search: str = "", limit: int = 200) -> str:
    """List Blueprint-callable/pure/event functions for a loaded UE class."""
    return httpx.get(f"{app.BASE_URL}/ue/blueprint-functions", params={
        "class_path": class_path, "search": search, "limit": limit
    }).text


@mcp.tool()
def inspect_blueprint_class_defaults(asset_path: str, search: str = "", limit: int = 200) -> str:
    """List a Blueprint's editable class defaults, including inherited ones and default subobjects.

    Paths look like DefaultPawnClass or CharacterMovement.MaxWalkSpeed; pass them to set_blueprint_class_default.
    """
    return httpx.get(f"{app.BASE_URL}/blueprints/class-defaults", params={"asset_path": asset_path, "search": search, "limit": limit}, timeout=180).text


@mcp.tool()
def set_blueprint_class_default(asset_path: str, property_path: str, expected_value: str, value: str,
                                confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Set one class default of a /Game Blueprint using UE text, then compile it.

    expected_value is the inspected value. Works for inherited fields (e.g. GameMode DefaultPawnClass) and native
    components (CharacterMovement.JumpZVelocity); components added in the Blueprint use set_component_property.
    Loaded child Blueprints are not updated until they next load. Requires stopped PIE.
    """
    return httpx.patch(f"{app.BASE_URL}/blueprints/class-defaults", json={
        "AssetPath": asset_path, "PropertyPath": property_path, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
edit_variable_in_bp = merged_tool("edit_variable_in_bp", {
    "rename_variable_in_bp": rename_variable_in_bp,
    "set_variable_default_value_in_bp": set_variable_default_value_in_bp,
})
edit_component_in_bp = merged_tool("edit_component_in_bp", {
    "rename_component_in_bp": rename_component_in_bp,
    "reattach_component_in_bp": reattach_component_in_bp,
})


@mcp.tool()
def edit_blueprint_graph(bp_path: str, nodes: list[dict], links: list[list[str]] | None = None,
                         defaults: list[list[str]] | None = None, graph_name: str = "EventGraph") -> str:
    """Add nodes, connect them and set pin values in one call. If a step fails, the nodes it added are removed.

    nodes: [{"id": "start", "tool": "add_event_to_graph", "args": {"event_name": "ReceiveBeginPlay"}}]. tool is any
    add_*_to_graph tool; args leave out bp_path and graph_name.
    links: [["start.then", "print.execute"]], from output to input. A reference is id.Pin, where id is a node id above
    or the id of a node already in the graph.
    defaults: [["print.InString", "Hello"]].
    Removing nodes after a failure does not restore links or values changed on nodes that were already in the graph.
    """
    created = {}
    done = []

    def pin(reference):
        node, _, name = reference.partition(".")
        if not name:
            raise ValueError(f"{reference} must be written as id.Pin")
        return created.get(node, node), name

    def checked(step, result):
        data = json.loads(result)
        if not data.get("success"):
            raise ValueError(f"{step}: {data.get('errorMessage')}")
        return data

    try:
        for node in nodes:
            tool = globals().get(str(node.get("tool")))
            if not str(node.get("tool")).startswith("add_") or not str(node.get("tool")).endswith("_to_graph") or tool is None:
                raise ValueError(f"{node.get('tool')} is not an add_*_to_graph tool")
            added = checked(f"node {node.get('id')}", tool(bp_path, graph_name, **node.get("args", {})))
            created[node["id"]] = added["node_id"]
            done.append({"id": node["id"], "node_id": added["node_id"], "pins": added["pins"]})
        for source, target in links or []:
            checked(f"link {source} to {target}", connect_pins(bp_path, graph_name, *pin(source), *pin(target)))
        for reference, value in defaults or []:
            checked(f"default {reference}", set_pin_default_value(bp_path, graph_name, *pin(reference), value))
    except (ValueError, TypeError, KeyError) as error:
        for node_id in created.values():
            httpx.post(f"{app.BASE_URL}/graphs/nodes/delete", json={"BpPath": bp_path, "GraphName": graph_name, "NodeId": node_id})
        return json.dumps({"errorMessage": str(error), "removed_nodes": len(created)})
    return json.dumps({"nodes": done})
