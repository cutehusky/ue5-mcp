import httpx
from mcp.server.fastmcp import FastMCP
import dotenv
import os

dotenv.load_dotenv()

mcp = FastMCP("UE5BlueprintMCP", port=9000)

BASE_URL = os.getenv("UE5_REST_API_URL", "http://localhost:8080")

# System instruction for all tools
common_instruction = """
Valid Unreal Engine class name should be:
for Engine class like 'Actor', 'Pawn', 'Character', 'GameModeBase', etc.
for BP generated class should be /Game/YourFolder/YourBlueprint.YourBlueprint_C
for C++ class should be /Script/YourModule.YourClass

Valid variable, function or custom event signature is in c++ style:
for UObject type use valid Unreal Engine class name with * (e.g. Actor* ActorInput, StaticMeshComponent* MeshCompInput).
for array, set, map type use TArray<> TSet<> TMap<> (e.g. TArray<int32> IntArray, TSet<float> FloatSet, TMap<FString, int32> StringIntMap).
for struct type use valid Unreal Engine struct name (e.g. Vector Location, Rotator Rotation, Transform TransformInput).
for enum type use valid Unreal Engine enum name (e.g. EPhysicalSurface SurfaceType, ECollisionChannel CollisionChannel).
for basic type use int32, float, double, bool, FString, FName, FText,...
Variable use only single variable signature (e.g. 'float NewVar', 'Actor* TargetActor').
Function or custom event use multiple parameters separated by comma (e.g. `int32 Count, Actor* TargetActor, bool bIsActive').

Valid Blueprint path should start with /Game/ 

Valid value string to set default value of variable or pin:
for basic type should be in c++ style, can be deserialized to the variable type. 
for UObject type, use the full path of the asset (e.g. '/Game/StarterContent/Shapes/Shape_Cube.Shape_Cube' for StaticMesh etc.)
"""


@mcp.tool()
def create_blueprint(parent_class: str, bp_path: str) -> str:
    """Create a new Unreal Engine Blueprint.

    parent_class: Must be a valid Unreal Engine class name.
    bp_path: Must be a valid Blueprint path starting with /Game/
    """
    url = f"{BASE_URL}/create_bp"
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
    url = f"{BASE_URL}/create_function"
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
    url = f"{BASE_URL}/edit_function"
    body = {"BpPath": bp_path, "FunctionName": function_name, "FunctionInputSignature": input_signature,
            "FunctionOutputSignature": output_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def delete_function(bp_path: str, function_name: str) -> str:
    """Delete a function from the Blueprint.
    Caution: Deleting a function not remove existing function calls or references, may break the Blueprint.

    bp_path: Must be a valid Blueprint path
    function_name: Must be a valid existing function name.
    """
    url = f"{BASE_URL}/delete_function"
    body = {"BpPath": bp_path, "FunctionName": function_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_function_call_to_graph(bp_path: str, graph_name: str, function_name: str, class_to_call: str) -> str:
    """Add a function call node to the specified graph in the Blueprint.

    bp_path: Must be a valid Blueprint path
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    function_name: Must be a valid existing function name, you can use get_blueprint_functions to get the list of functions.
    class_to_call: Must be a valid Unreal Engine class name, leave empty to call function in the same Blueprint.
    """
    url = f"{BASE_URL}/add_function_call_to_graph"
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

    bp_path: Must be a valid Blueprint path
    """
    url = f"{BASE_URL}/get_blueprint_variables"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def get_blueprint_functions(bp_path: str) -> str:
    """Get the list of functions in the Blueprint.

    bp_path: Must be a valid Blueprint path
    """
    url = f"{BASE_URL}/get_blueprint_functions"
    params = {"bp_path": bp_path}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def get_graph(bp_path: str, graph_name: str) -> str:
    """Get the details of a specific graph structure (nodes and connections) in the Blueprint.

    bp_path: Must be a valid Blueprint path
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    """
    url = f"{BASE_URL}/get_graph"
    params = {"bp_path": bp_path, "graph_name": graph_name}
    response = httpx.get(url, params=params)
    return response.text


@mcp.tool()
def compile_blueprint(bp_path: str) -> str:
    """Compile the Blueprint.

    bp_path: Must be a valid Blueprint path
    """
    url = f"{BASE_URL}/compile_blueprint"
    params = {"bp_path": bp_path}
    response = httpx.post(url, params=params)
    return response.text


@mcp.tool()
def get_supported_nodes() -> str:
    """Get the list of supported nodes for the Blueprint system."""
    url = f"{BASE_URL}/get_supported_nodes"
    response = httpx.get(url)
    return response.text


@mcp.tool()
def add_variable_to_bp(bp_path: str, var_signature: str) -> str:
    """Add a new variable to the Blueprint.

    bp_path: Must be a valid Blueprint path.
    var_signature: Must be a valid single variable signature in c++ style (e.g., 'float NewVar').
    """
    url = f"{BASE_URL}/add_variable_to_bp"
    body = {"BpPath": bp_path, "VarSignature": var_signature}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def delete_variable_from_bp(bp_path: str, var_name: str) -> str:
    """Delete a variable from the Blueprint.

    bp_path: Must be a valid Blueprint path.
    var_name: Must be a valid existing variable name (e.g., 'NewVar').
    """
    url = f"{BASE_URL}/delete_variable_from_bp"
    body = {"BpPath": bp_path, "VarName": var_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def rename_variable_in_bp(bp_path: str, old_var_name: str, new_var_name: str) -> str:
    """Rename a variable in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    old_var_name: Must be a valid existing variable name (e.g., 'NewVar').
    new_var_name: Must be a valid new variable name (e.g., 'RenamedVar').
    """
    url = f"{BASE_URL}/rename_variable_in_bp"
    body = {"BpPath": bp_path, "OldVarName": old_var_name, "NewVarName": new_var_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def set_variable_default_value_in_bp(bp_path: str, var_name: str, default_value: str) -> str:
    """Set the default value for a variable in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    var_name: Must be a valid existing variable name (e.g., 'NewVar').
    default_value: Must be a valid default value string for the variable type.
    """
    url = f"{BASE_URL}/set_variable_default_value_in_bp"
    body = {"BpPath": bp_path, "VarName": var_name, "DefaultValue": default_value}
    response = httpx.post(url, json=body)
    return response.text


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
    url = f"{BASE_URL}/connect_pins"
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
    url = f"{BASE_URL}/break_pin_connection"
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
    url = f"{BASE_URL}/set_pin_default_value"
    body = {"BpPath": bp_path, "GraphName": graph_name, "NodeId": node_id, "PinName": pin_name,
            "DefaultValue": default_value}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_generic_node_to_graph(bp_path: str, graph_name: str, node_type_name: str) -> str:
    """Add a generic node to the specified graph.
    use this for nodes that do not require extra info and not covered by other specific node adding tools.
    if existing tool for specific node type, use that instead.

    bp_path: Must be a valid Blueprint path.
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    node_type_name: Must be a valid node type name (e.g., 'K2Node_PlayAnimation', 'K2Node_IfThenElse').
    node_type_name can be found in the supported nodes from tool: get_supported_nodes.
    """
    url = f"{BASE_URL}/add_generic_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "NodeTypeName": node_type_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_make_struct_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a make struct node to the specified graph.

    bp_path: Must be a valid Blueprint path.
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

    bp_path: Must be a valid Blueprint path.
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

    bp_path: Must be a valid Blueprint path.
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

    bp_path: Must be a valid Blueprint path.
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    extra_info: Must be a valid class name for casting (e.g., 'Actor').
    """
    url = f"{BASE_URL}/add_class_cast_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "ExtraInfo": extra_info}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def add_enum_cast_node_to_graph(bp_path: str, graph_name: str, extra_info: str) -> str:
    """Add a byte to enum cast node to the specified graph.

    bp_path: Must be a valid Blueprint path.
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

    bp_path: Must be a valid Blueprint path.
    graph_name: Must be a valid graph name (e.g., 'EventGraph').
    function_name: Must be a valid math function name in UKismetMathLibrary (e.g., 'Add_DoubleDouble').
    Common math function names in format Operation_OperandType1OperandType2 in camel style.
    """
    url = f"{BASE_URL}/add_math_node_to_graph"
    body = {"BpPath": bp_path, "GraphName": graph_name, "FunctionName": function_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def get_components_of_bp(bp_path: str) -> str:
    """Get the list of components in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    """
    url = f"{BASE_URL}/get_components_of_bp"
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
    url = f"{BASE_URL}/add_component_to_bp"
    body = {"BpPath": bp_path, "ComponentClass": component_class, "ComponentName": component_name,
            "AttachTo": attach_to}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def rename_component_in_bp(bp_path: str, component_name: str, new_component_name: str) -> str:
    """Rename a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    new_component_name: Must be a valid new component name. Must be unique within the Blueprint.
    """
    url = f"{BASE_URL}/rename_component_in_bp"
    body = {"BpPath": bp_path, "ComponentName": component_name, "NewComponentName": new_component_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def remove_component_from_bp(bp_path: str, component_name: str) -> str:
    """Remove a component from the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    """
    url = f"{BASE_URL}/remove_component_from_bp"
    body = {"BpPath": bp_path, "ComponentName": component_name}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def reattach_component_in_bp(bp_path: str, component_name: str, attach_to: str) -> str:
    """Reparent (reattach) a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    attach_to: Must be a valid new parent component name.
    """
    url = f"{BASE_URL}/reattach_component_in_bp"
    body = {"BpPath": bp_path, "ComponentName": component_name, "AttachTo": attach_to}
    response = httpx.post(url, json=body)
    return response.text


@mcp.tool()
def get_component_properties(bp_path: str, component_name: str) -> str:
    """Get the properties of a component in the Blueprint.

    bp_path: Must be a valid Blueprint path.
    component_name: Must be a valid existing component name.
    """
    url = f"{BASE_URL}/get_component_properties"
    params = {"bp_path": bp_path, "component_name": component_name}
    response = httpx.get(url, params=params)
    return response.text


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
    url = f"{BASE_URL}/set_component_property"
    body = {"BpPath": bp_path, "ComponentName": component_name, "Properties": properties}
    response = httpx.post(url, json=body)
    return response.text


async def main():
    await mcp.run_streamable_http_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
