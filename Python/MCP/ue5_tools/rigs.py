"""Control Rigs and Modular Rigs."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_control_rig(asset_path: str) -> str:
    """Inspect a Control Rig or Modular Rig asset."""
    return httpx.get(f"{app.BASE_URL}/control-rigs/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def list_modular_rig_modules(asset_path: str) -> str:
    """List Modular Rig module references, classes, and parents."""
    return httpx.get(f"{app.BASE_URL}/modular-rigs/modules", params={"asset_path": asset_path}).text


@mcp.tool()
def list_modular_rig_connections(asset_path: str) -> str:
    """List Modular Rig connector targets and unresolved connectors."""
    return httpx.get(f"{app.BASE_URL}/modular-rigs/connections", params={"asset_path": asset_path}).text


@mcp.tool()
def validate_modular_rig(asset_path: str) -> str:
    """Check module references and unresolved required connectors."""
    return httpx.get(f"{app.BASE_URL}/modular-rigs/validate", params={"asset_path": asset_path}).text


@mcp.tool()
def compile_modular_rig(asset_path: str, dry_run: bool = False,
                        save: bool = False) -> str:
    """Recompile a Modular Rig and report VM compiler counts."""
    return httpx.post(f"{app.BASE_URL}/modular-rigs/compile", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def list_modular_rig_variables(asset_path: str, module_name: str,
                                variable_name: str = "") -> str:
    """List a module's editable variables, config overrides, and bindings."""
    return httpx.get(f"{app.BASE_URL}/modular-rigs/variables", params={
        "asset_path": asset_path, "module_name": module_name,
        "variable_name": variable_name
    }).text


@mcp.tool()
def edit_modular_rig_variable(asset_path: str, module_name: str,
                              operation: str, variable_path: str,
                              value: str = "", source_path: str = "",
                              dry_run: bool = False, save: bool = False) -> str:
    """Set/reset a module config override or bind/unbind a top-level variable."""
    return httpx.post(f"{app.BASE_URL}/modular-rigs/variables", json={
        "AssetPath": asset_path, "ModuleName": module_name,
        "Operation": operation, "VariablePath": variable_path,
        "Value": value, "SourcePath": source_path,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def edit_modular_rig_module(asset_path: str, operation: str, module_name: str,
                            new_name: str = "", parent_name: str = "",
                            module_class_path: str = "", dry_run: bool = False,
                            confirm: bool = False, save: bool = False) -> str:
    """Add, rename, reparent, or confirm deletion of a Modular Rig module."""
    return httpx.post(f"{app.BASE_URL}/modular-rigs/modules", json={
        "AssetPath": asset_path, "Operation": operation,
        "ModuleName": module_name, "NewName": new_name,
        "ParentName": parent_name, "ModuleClassPath": module_class_path,
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def edit_modular_rig_connection(asset_path: str, operation: str,
                                connector_name: str, target_type: str = "",
                                target_name: str = "", dry_run: bool = False,
                                confirm: bool = False, save: bool = False,
                                targets: list[dict[str, str]] | None = None) -> str:
    """Connect, disconnect, or edit targets of a Modular Rig connector."""
    return httpx.post(f"{app.BASE_URL}/modular-rigs/connections", json={
        "AssetPath": asset_path, "Operation": operation,
        "ConnectorName": connector_name, "TargetType": target_type,
        "TargetName": target_name,
        "Targets": [{"Name": item["name"], "Type": item["type"]}
                    for item in (targets or [])], "bDryRun": dry_run,
        "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def list_control_rig_hierarchy(asset_path: str) -> str:
    """List Control Rig hierarchy elements with type, parent, and child count."""
    return httpx.get(f"{app.BASE_URL}/control-rigs/hierarchy", params={"asset_path": asset_path}).text


@mcp.tool()
def list_control_rig_graphs(asset_path: str) -> str:
    """List RigVM model graphs with node summaries and links."""
    return httpx.get(f"{app.BASE_URL}/control-rigs/graphs", params={"asset_path": asset_path}).text


@mcp.tool()
def list_control_rig_templates(search: str = "") -> str:
    """List registered RigVM template notations, optionally filtered by name."""
    return httpx.get(f"{app.BASE_URL}/control-rigs/templates", params={"search": search}).text


@mcp.tool()
def edit_control_rig_graph(asset_path: str, graph_path: str, operation: str,
                           node_name: str = "", unit_struct_path: str = "",
                           method_name: str = "Execute", pin_path: str = "",
                           default_value: str = "", source_pin_path: str = "",
                           target_pin_path: str = "", x: float = 0.0,
                           y: float = 0.0, dry_run: bool = False,
                           confirm: bool = False, save: bool = False,
                           comment_text: str = "", width: float = 400.0,
                           height: float = 300.0, cpp_type: str = "",
                           cpp_type_object_path: str = "",
                           array_operation: str = "", variable_name: str = "",
                           new_variable_name: str = "", is_getter: bool = True,
                           function_name: str = "", exposed_pin_name: str = "",
                           pin_direction: str = "", function_mutable: bool = False,
                           node_names: list[str] | None = None,
                           template_notation: str = "", entry_name: str = "",
                           injection_input_pin_name: str = "",
                           injection_output_pin_name: str = "",
                           injected_as_input: bool = True,
                           reroute_constant: bool = False,
                           custom_widget_name: str = "",
                           reroute_as_input: bool = True,
                           array_index: int = -1, array_size: int = -1,
                           pin_display_name: str = "", pin_expanded: bool = False,
                           pin_watched: bool = False) -> str:
    """Add/edit RigVM nodes, collapse or expand selected graph nodes, create constants/structs/reroutes on pins, resolve templates, edit dynamic array pins, and change pin display, expansion, or watch state. Expansion, array removal/shrinking, and replacing an occupied input pin require confirmation."""
    return httpx.post(f"{app.BASE_URL}/control-rigs/graphs", json={
        "AssetPath": asset_path, "GraphPath": graph_path,
        "Operation": operation, "NodeName": node_name,
        "UnitStructPath": unit_struct_path, "MethodName": method_name,
        "PinPath": pin_path, "DefaultValue": default_value,
        "SourcePinPath": source_pin_path, "TargetPinPath": target_pin_path,
        "Position": {"X": x, "Y": y},
        "CommentText": comment_text, "NodeSize": {"X": width, "Y": height},
        "CPPType": cpp_type, "CPPTypeObjectPath": cpp_type_object_path,
        "ArrayOperation": array_operation,
        "ArrayIndex": array_index, "ArraySize": array_size,
        "VariableName": variable_name, "NewVariableName": new_variable_name,
        "bIsGetter": is_getter, "FunctionName": function_name,
        "ExposedPinName": exposed_pin_name, "PinDirection": pin_direction,
        "bFunctionMutable": function_mutable,
        "NodeNames": node_names or [],
        "TemplateNotation": template_notation, "EntryName": entry_name,
        "InjectionInputPinName": injection_input_pin_name,
        "InjectionOutputPinName": injection_output_pin_name,
        "bInjectedAsInput": injected_as_input,
        "bRerouteConstant": reroute_constant, "CustomWidgetName": custom_widget_name,
        "bRerouteAsInput": reroute_as_input,
        "PinDisplayName": pin_display_name,
        "bPinExpanded": pin_expanded, "bPinWatched": pin_watched,
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def compile_control_rig(asset_path: str, dry_run: bool = False,
                        save: bool = False) -> str:
    """Recompile a Control Rig Blueprint VM and report compiler counts."""
    return httpx.post(f"{app.BASE_URL}/control-rigs/compile", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def validate_control_rig(asset_path: str, graph_path: str = "",
                         compile_vm: bool = False) -> str:
    """Validate RigVM graph nodes, pins, links, templates, and contained graphs, optionally compiling the Control Rig VM."""
    return httpx.post(f"{app.BASE_URL}/control-rigs/validate", json={
        "AssetPath": asset_path, "GraphPath": graph_path, "bCompile": compile_vm
    }).text


@mcp.tool()
def edit_control_rig_hierarchy(asset_path: str, operation: str, element_type: str,
                               name: str, new_name: str = "", parent_name: str = "",
                               parent_type: str = "", translation: tuple[float, float, float] = (0, 0, 0),
                               rotation: tuple[float, float, float] = (0, 0, 0),
                               scale: tuple[float, float, float] = (1, 1, 1),
                               curve_value: float = 0.0, dry_run: bool = False,
                               confirm: bool = False, save: bool = False,
                               control_type: str = "", control_value: str = "",
                               primary_axis: str = "x",
                               control_enum_path: str = "",
                               control_display_name: str = "",
                               control_animation_type: str = "",
                               shape_name: str = "", shape_color: str = "",
                               shape_visibility: str = "",
                               control_shape_transform: dict | None = None,
                               set_control_shape_transform: bool = False,
                               shape_visible: bool = True, set_shape_visible: bool = False,
                               draw_limits: bool = True, set_draw_limits: bool = False,
                               group_with_parent_control: bool = False,
                               set_group_with_parent_control: bool = False,
                               driven_control_names: list[str] | None = None,
                               set_driven_controls: bool = False,
                               preferred_rotation_order: str = "",
                               use_preferred_rotation_order: bool = False,
                               set_preferred_rotation_order: bool = False,
                               space_type: str = "", space_name: str = "",
                               space_label: str = "", space_index: int = -1,
                               maintain_global_transform: bool = True,
                               affect_children: bool = False,
                               set_restrict_space_switching: bool = False,
                               restrict_space_switching: bool = False,
                               initial: bool = False, minimum_value: str = "",
                               maximum_value: str = "", minimum_enabled: bool = True,
                               maximum_enabled: bool = True,
                               minimum_transform: dict | None = None,
                               maximum_transform: dict | None = None,
                               limit_dimensions: list[int] | None = None,
                               connector_type: str = "", optional: bool = False,
                               is_array: bool = False, description: str = "") -> str:
    """Add/edit Control Rig values, settings, available spaces, and channel hosts. switch_parent preserves the control's global transform by default; maintain_global_transform=false keeps its local value, while affect_children controls descendant propagation. Proxy controls require existing targets and are cycle-checked."""
    return httpx.post(f"{app.BASE_URL}/control-rigs/hierarchy", json={
        "AssetPath": asset_path, "Operation": operation,
        "ElementType": element_type, "Name": name, "NewName": new_name,
        "ParentName": parent_name, "ParentType": parent_type,
        "ControlType": control_type, "ControlValue": control_value,
        "PrimaryAxis": primary_axis,
        "ControlEnumPath": control_enum_path,
        "ControlDisplayName": control_display_name,
        "ControlAnimationType": control_animation_type,
        "ShapeName": shape_name, "ShapeColor": shape_color,
        "ShapeVisibility": shape_visibility,
        "ControlShapeTransform": control_shape_transform or {
            "Translation": {"X": 0.0, "Y": 0.0, "Z": 0.0},
            "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0, "W": 1.0},
            "Scale3D": {"X": 1.0, "Y": 1.0, "Z": 1.0}},
        "bSetControlShapeTransform": set_control_shape_transform,
        "bShapeVisible": shape_visible, "bSetShapeVisible": set_shape_visible,
        "bDrawLimits": draw_limits, "bSetDrawLimits": set_draw_limits,
        "bGroupWithParentControl": group_with_parent_control,
        "bSetGroupWithParentControl": set_group_with_parent_control,
        "DrivenControlNames": driven_control_names or [], "bSetDrivenControls": set_driven_controls,
        "PreferredRotationOrder": preferred_rotation_order,
        "bUsePreferredRotationOrder": use_preferred_rotation_order,
        "bSetPreferredRotationOrder": set_preferred_rotation_order,
        "SpaceType": space_type, "SpaceName": space_name,
        "SpaceLabel": space_label, "SpaceIndex": space_index,
        "bMaintainGlobalTransform": maintain_global_transform,
        "bAffectChildren": affect_children,
        "bSetRestrictSpaceSwitching": set_restrict_space_switching,
        "bRestrictSpaceSwitching": restrict_space_switching,
        "ConnectorType": connector_type, "bOptional": optional,
        "bIsArray": is_array, "Description": description,
        "MinimumValue": minimum_value, "MaximumValue": maximum_value,
        "MinimumTransform": minimum_transform or {
            "Translation": {"X": 0.0, "Y": 0.0, "Z": 0.0},
            "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0, "W": 1.0},
            "Scale3D": {"X": 1.0, "Y": 1.0, "Z": 1.0}},
        "MaximumTransform": maximum_transform or {
            "Translation": {"X": 0.0, "Y": 0.0, "Z": 0.0},
            "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0, "W": 1.0},
            "Scale3D": {"X": 1.0, "Y": 1.0, "Z": 1.0}},
        "LimitDimensions": limit_dimensions or [],
        "bMinimumEnabled": minimum_enabled, "bMaximumEnabled": maximum_enabled,
        "Translation": dict(zip(("X", "Y", "Z"), translation)),
        "Rotation": dict(zip(("Pitch", "Yaw", "Roll"), rotation)),
        "Scale": dict(zip(("X", "Y", "Z"), scale)),
        "CurveValue": curve_value, "bDryRun": dry_run,
        "bConfirm": confirm, "bSave": save, "bInitial": initial
    }).text
