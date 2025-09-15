import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("UE5BlueprintMCP", port=9000)

BASE_URL = "http://localhost:8080"


@mcp.tool()
def create_blueprint(parent_class: str, bp_path: str) -> str:
    """Create a new Unreal Engine 5 Blueprint.

    parent_class: Must be a valid Unreal Engine class name (e.g., 'Actor').
    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    """
    url = f"{BASE_URL}/create_bp"
    body = {"ParentClass": parent_class, "BpPath": bp_path}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def create_function(bp_path: str, function_name: str, input_signature: str, output_signature: str) -> str:
    """Create a new function in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    function_name: Must be a valid function name (e.g., 'MyFunction').
    input_signature: Must be a valid input signature string (e.g., 'int32 Input1, float Input2').
    output_signature: Must be a valid output signature string (e.g., 'bool Output').
    """
    url = f"{BASE_URL}/create_function"
    body = {"BpPath": bp_path, "FunctionName": function_name, "FunctionInputSignature": input_signature,
            "FunctionOutputSignature": output_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def edit_function(bp_path: str, function_name: str, input_signature: str, output_signature: str) -> str:
    """Edit an existing function in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    function_name: Must be a valid existing function name (e.g., 'MyFunction').
    input_signature: Must be a valid new input signature string (e.g., 'int32 NewInput, float Input2, FString ExtraInput').
    output_signature: Must be a valid new output signature string (e.g., 'bool NewOutput, float ExtraOutput').
    """
    url = f"{BASE_URL}/edit_function"
    body = {"BpPath": bp_path, "FunctionName": function_name, "FunctionInputSignature": input_signature,
            "FunctionOutputSignature": output_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def delete_function(bp_path: str, function_name: str) -> str:
    """Delete a function from the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    function_name: Must be a valid existing function name (e.g., 'MyFunction').
    """
    url = f"{BASE_URL}/delete_function"
    body = {"BpPath": bp_path, "FunctionName": function_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_function_call_to_graph(bp_path: str, graph_name: str, function_name: str) -> str:
    """Add a function call node to the specified graph in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    function_name: Must be a valid existing function name (e.g., 'MyFunction').
    """
    url = f"{BASE_URL}/add_function_call_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "FunctionName": function_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_event_to_graph(bp_path: str, graph_name: str, event_name: str, is_custom: bool = False,
                       event_signature: str = None) -> str:
    """Add an event (custom or built-in) to the specified graph in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    event_name: Must be a valid event name (e.g., 'MyEvent' for custom, 'ReceiveHit' for built-in).
    is_custom: Set to True for custom events, False for built-in events.
    event_signature: Required only for custom events, must be a valid signature (e.g., 'int32 Param1, float Param2').
    """
    url = f"{BASE_URL}/add_event_to_graph"
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
    url = f"{BASE_URL}/add_variable_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "VarName": var_name, "bIsSetter": is_setter}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def get_blueprint_variables(bp_path: str) -> str:
    """Get the list of variables in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    """
    url = f"{BASE_URL}/get_blueprint_variables"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def get_blueprint_functions(bp_path: str) -> str:
    """Get the list of functions in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    """
    url = f"{BASE_URL}/get_blueprint_functions"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def get_graph(bp_path: str, graph_name: str) -> str:
    """Get the details of a specific graph in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    """
    url = f"{BASE_URL}/get_graph"
    params = {"bp_path": bp_path, "graph_name": graph_name}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def compile_blueprint(bp_path: str) -> str:
    """Compile the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    """
    url = f"{BASE_URL}/compile_blueprint"
    params = {"bp_path": bp_path}
    response = httpx.post(url, params=params)
    return response.text


@mcp.tool()
def get_supported_nodes() -> list:
    """Get the list of supported nodes for the Blueprint system."""
    url = f"{BASE_URL}/get_supported_nodes"
    response = httpx.get(url)
    return response.text


@mcp.tool()
def add_variable_to_bp(bp_path: str, var_signature: str) -> str:
    """Add a new variable to the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    var_signature: Must be a valid variable signature (e.g., 'float NewVar99').
    """
    url = f"{BASE_URL}/add_variable_to_bp"
    body = {"BpPath": bp_path, "VarSignature": var_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def delete_variable_from_bp(bp_path: str, var_name: str) -> str:
    """Delete a variable from the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    var_name: Must be a valid existing variable name (e.g., 'NewVar4').
    """
    url = f"{BASE_URL}/delete_variable_from_bp"
    body = {"BpPath": bp_path, "VarName": var_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def rename_variable_in_bp(bp_path: str, old_var_name: str, new_var_name: str) -> str:
    """Rename a variable in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    old_var_name: Must be a valid existing variable name (e.g., 'NewVar2').
    new_var_name: Must be a valid new variable name (e.g., 'RenamedVar').
    """
    url = f"{BASE_URL}/rename_variable_in_bp"
    body = {"BpPath": bp_path, "OldVarName": old_var_name, "NewVarName": new_var_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def set_variable_default_value_in_bp(bp_path: str, var_name: str, default_value: str) -> str:
    """Set the default value for a variable in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    var_name: Must be a valid existing variable name (e.g., 'NewVar').
    default_value: Must be a valid default value string for the variable type (e.g., '3.14159').
    """
    url = f"{BASE_URL}/set_variable_default_value_in_bp"
    body = {"BpPath": bp_path, "VarName": var_name, "DefaultValue": default_value}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def connect_pins(bp_path: str, graph_name: str, output_node_id: str, output_pin_name: str, input_node_id: str,
                 input_pin_name: str) -> str:
    """Connect pins between nodes in the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    output_node_id: Must be a valid node ID (e.g., '7C40B46046D4D873D5DF9C89D957426E').
    output_pin_name: Must be a valid pin name on the output node (e.g., 'NewVar5').
    input_node_id: Must be a valid node ID (e.g., '2AFEFE7B4F381FCD206A47903659176F').
    input_pin_name: Must be a valid pin name on the input node (e.g., 'TargetRelativeLocation').
    """
    url = f"{BASE_URL}/connect_pins"
    body = {"BpPath": bp_path, "GraphName": graph_name, "OutputNodeId": output_node_id,
            "OutputPinName": output_pin_name, "InputNodeId": input_node_id, "InputPinName": input_pin_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def break_pin_connection(bp_path: str, graph_name: str, output_node_id: str, output_pin_name: str, input_node_id: str,
                         input_pin_name: str) -> str:
    """Break the connection between pins in the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    output_node_id: Must be a valid node ID (e.g., '7C40B46046D4D873D5DF9C89D957426E').
    output_pin_name: Must be a valid pin name on the output node (e.g., 'NewVar5').
    input_node_id: Must be a valid node ID (e.g., '2AFEFE7B4F381FCD206A47903659176F').
    input_pin_name: Must be a valid pin name on the input node (e.g., 'TargetRelativeLocation').
    """
    url = f"{BASE_URL}/break_pin_connection"
    body = {"BpPath": bp_path, "GraphName": graph_name, "OutputNodeId": output_node_id,
            "OutputPinName": output_pin_name, "InputNodeId": input_node_id, "InputPinName": input_pin_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def set_pin_default_value(bp_path: str, graph_name: str, node_id: str, pin_name: str, default_value: str) -> str:
    """Set the default value for a pin on a node in the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    node_id: Must be a valid node ID (e.g., '2AFEFE7B4F381FCD206A47903659176F').
    pin_name: Must be a valid pin name (e.g., 'TargetRelativeLocation').
    default_value: Must be a valid default value string (e.g., '100, 200, 300').
    """
    url = f"{BASE_URL}/set_pin_default_value"
    body = {"BpPath": bp_path, "GraphName": graph_name, "NodeId": node_id, "PinName": pin_name,
            "DefaultValue": default_value}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_generic_node_to_graph(bp_path: str, graph_name: str, node_type_name: str) -> str:
    """Add a generic node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    node_type_name: Must be a valid node type name (e.g., 'K2Node_PlayAnimation').
    """
    url = f"{BASE_URL}/add_generic_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "NodeTypeName": node_type_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_make_struct_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a make struct node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    extra_info: Must be a valid struct type (e.g., 'Vector').
    """
    url = f"{BASE_URL}/add_make_struct_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_break_struct_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a break struct node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    extra_info: Must be a valid struct type (e.g., 'Vector').
    """
    url = f"{BASE_URL}/add_break_struct_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_dynamic_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a dynamic cast node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    extra_info: Must be a valid class name for casting (e.g., 'Actor').
    """
    url = f"{BASE_URL}/add_dynamic_cast_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_class_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a class cast node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    extra_info: Must be a valid class name for casting (e.g., 'Actor').
    """
    url = f"{BASE_URL}/add_class_cast_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_enum_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add an enum cast node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    extra_info: Must be a valid enum name for casting (e.g., 'EPhysicalSurface').
    """
    url = f"{BASE_URL}/add_enum_cast_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_math_node_to_graph(bp_path: str, graph_name: str, function_name: str) -> str:
    """Add a math node to the specified graph.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    function_name: Must be a valid math function name (e.g., 'Add_DoubleDouble').
    """
    url = f"{BASE_URL}/add_math_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "FunctionName": function_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def get_components_of_bp(bp_path: str) -> list:
    """Get the list of components in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    """
    url = f"{BASE_URL}/get_components_of_bp"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def add_component_to_bp(bp_path: str, component_class: str, component_name: str, attach_to: str) -> str:
    """Add a component to the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    component_class: Must be a valid component class name (e.g., 'StaticMeshComponent').
    component_name: Must be a valid component name (e.g., 'MyStaticMeshComp').
    attach_to: Must be a valid parent component name (e.g., 'DefaultSceneRoot').
    """
    url = f"{BASE_URL}/add_component_to_bp"
    body = {"BpPath": bp_path, "ComponentClass": component_class, "ComponentName": component_name,
            "AttachTo": attach_to}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def rename_component_in_bp(bp_path: str, component_name: str, new_component_name: str) -> str:
    """Rename a component in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    component_name: Must be a valid existing component name (e.g., 'MyStaticMeshComp2').
    new_component_name: Must be a valid new component name (e.g., 'RenamedComp').
    """
    url = f"{BASE_URL}/rename_component_in_bp"
    body = {"BpPath": bp_path, "ComponentName": component_name, "NewComponentName": new_component_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def remove_component_from_bp(bp_path: str, component_name: str) -> str:
    """Remove a component from the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    component_name: Must be a valid existing component name (e.g., 'RenamedComp').
    """
    url = f"{BASE_URL}/remove_component_from_bp"
    body = {"BpPath": bp_path, "ComponentName": component_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def reattach_component_in_bp(bp_path: str, component_name: str, attach_to: str) -> str:
    """Reparent (reattach) a component in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    component_name: Must be a valid existing component name (e.g., 'MyStaticMeshComp2').
    attach_to: Must be a valid new parent component name (e.g., 'MyStaticMeshComp').
    """
    url = f"{BASE_URL}/reattach_component_in_bp"
    body = {"BpPath": bp_path, "ComponentName": component_name, "AttachTo": attach_to}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def get_component_properties(bp_path: str, component_name: str) -> str:
    """Get the properties of a component in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    component_name: Must be a valid existing component name (e.g., 'MyStaticMeshComp').
    """
    url = f"{BASE_URL}/get_component_properties"
    params = {"bp_path": bp_path, "component_name": component_name}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def set_component_property(bp_path: str, component_name: str, properties: dict) -> str:
    """Set properties for a component in the Blueprint.

    bp_path: Must be a valid Blueprint path (e.g., '/Game/Test/MyBlueprint').
    component_name: Must be a valid existing component name (e.g., 'MyStaticMeshComp').
    properties: A dictionary of property names to values, where values are valid strings for the property type (e.g., {'RelativeLocation': 'X=0.5,Y=20,Z=100', 'StaticMesh': '/Engine/BasicShapes/Cube.Cube', 'Mobility': 'Movable'}).
    """
    url = f"{BASE_URL}/set_component_property"
    body = {"BpPath": bp_path, "ComponentName": component_name, "Properties": properties}
    response = httpx.post(url, json=body)
    return response.text


async def main():
    await mcp.run_streamable_http_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
