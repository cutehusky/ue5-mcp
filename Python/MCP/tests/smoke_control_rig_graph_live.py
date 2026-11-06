"""Exercise RigVM graph mutations on a disposable Control Rig copy."""

from pathlib import Path
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/CR_Mannequin_FootIK.CR_Mannequin_FootIK"


def graph(asset, path):
    return next(g for g in request("GET", "/control-rigs/graphs",
                                   params={"asset_path": asset}) if g["path"] == path)


def main():
    name = "CR_MCP_Graph_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        path = "RigVMModel::"
        original = graph(asset, path)
        original_names = {node["name"] for node in original["nodes"]}

        constant_templates = request("GET", "/control-rigs/templates", params={"search": "Constant"})
        template_notation = next((item["notation"] for item in constant_templates["templates"]
                                  if "Constant" in item["notation"]), None)
        assert template_notation and constant_templates["count"] >= 1, constant_templates
        template_add = {"AssetPath": asset, "GraphPath": path,
                        "Operation": "add_template_node", "TemplateNotation": template_notation,
                        "NodeName": "MCP_Test_TemplateConstant", "Position": {"X": 5, "Y": 10}}
        request("POST", "/control-rigs/graphs", {**template_add,
            "TemplateNotation": "MCP_Missing_Template"}, expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**template_add, "bDryRun": True})["changed"]
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])
        template_result = request("POST", "/control-rigs/graphs", template_add)
        template_graph = graph(asset, path)
        template_node = next(node for node in template_graph["nodes"]
                             if node["name"] == template_result["node_name"])
        assert template_node["class"] == "RigVMDispatchNode", template_node
        assert template_node["template_notation"] == template_notation
        assert template_node["template_fully_unresolved"], template_node
        wildcard_pin = next(pin for pin in template_node["pins"] if pin["name"] == "Value")
        assert wildcard_pin["wildcard"], wildcard_pin
        unresolved_validation = request("POST", "/control-rigs/validate", {
            "AssetPath": asset, "GraphPath": path})
        assert unresolved_validation["valid"] and any(
            wildcard_pin["path"] in warning for warning in unresolved_validation["warnings"]), unresolved_validation
        resolve_wildcard = {"AssetPath": asset, "GraphPath": path,
                            "Operation": "resolve_wildcard_pin", "PinPath": wildcard_pin["path"],
                            "CPPType": "float"}
        request("POST", "/control-rigs/graphs", {**resolve_wildcard, "PinPath": "Missing.Pin"},
                expect_error=True)
        request("POST", "/control-rigs/graphs", {**resolve_wildcard, "CPPType": ""}, expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**resolve_wildcard, "bDryRun": True})["changed"]
        assert next(pin for node in graph(asset, path)["nodes"] for pin in node["pins"]
                    if pin["path"] == wildcard_pin["path"])["wildcard"]
        resolution_result = request("POST", "/control-rigs/graphs", resolve_wildcard)
        assert resolution_result["pin_path"] == wildcard_pin["path"]
        assert resolution_result["node_name"] == template_result["node_name"]
        assert resolution_result["cpp_type"] == "float"
        resolved_template = next(node for node in graph(asset, path)["nodes"]
                                 if node["name"] == template_result["node_name"])
        resolved_value = next(pin for pin in resolved_template["pins"] if pin["name"] == "Value")
        assert not resolved_template["template_fully_unresolved"], resolved_template
        assert not resolved_value["wildcard"] and resolved_value["type"] == "float", (resolved_template, resolved_value)
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": template_result["node_name"], "bConfirm": True})
        restored_graph = graph(asset, path)
        assert {node["name"] for node in restored_graph["nodes"]} == original_names, restored_graph
        assert restored_graph["links"] == original["links"], restored_graph

        injection_pin = next(pin for node in original["nodes"] for pin in node["pins"]
                             if pin["type"] == "float" and pin["direction"] == "input"
                             and pin["injected_node_count"] == 0)
        injection = {"AssetPath": asset, "GraphPath": path,
                     "Operation": "add_injected_node", "PinPath": injection_pin["path"],
                     "UnitStructPath": "/Script/ControlRig.RigUnit_Clamp_Float",
                     "InjectionInputPinName": "Value", "InjectionOutputPinName": "Result",
                     "bInjectedAsInput": True, "NodeName": "MCP_Test_InjectedClamp"}
        request("POST", "/control-rigs/graphs", {**injection,
            "InjectionOutputPinName": "MissingOutput"}, expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**injection, "bDryRun": True})["changed"]
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])
        injection_result = request("POST", "/control-rigs/graphs", injection)
        injected_graph = graph(asset, path)
        injected_node = next(node for node in injected_graph["nodes"]
                             if node["name"] == injection_result["node_name"])
        assert injected_node["injected"] and injected_node["class"] == "RigVMUnitNode", injected_node
        assert injected_node["injection_pin_path"] == injection_pin["path"]
        assert injected_node["injected_as_input"]
        updated_injection_pin = next(pin for node in injected_graph["nodes"]
                                     for pin in node["pins"] if pin["path"] == injection_pin["path"])
        assert updated_injection_pin["injected_node_count"] == 1, updated_injection_pin
        remove_injection = {"AssetPath": asset, "GraphPath": path,
                            "Operation": "remove_injected_node", "PinPath": injection_pin["path"],
                            "bInjectedAsInput": True}
        injection_preview = request("POST", "/control-rigs/graphs", {
            **remove_injection, "bDryRun": True})
        assert not injection_preview["changed"] and injection_preview["affected_injected_nodes"] == 1, injection_preview
        request("POST", "/control-rigs/graphs", remove_injection, expect_error=True)
        request("POST", "/control-rigs/graphs", {**remove_injection, "bConfirm": True})
        removed_injection_graph = graph(asset, path)
        assert len(removed_injection_graph["nodes"]) == len(original["nodes"]), removed_injection_graph
        assert removed_injection_graph["links"] == original["links"], removed_injection_graph
        restored_injection_pin = next(pin for node in removed_injection_graph["nodes"]
                                      for pin in node["pins"] if pin["path"] == injection_pin["path"])
        assert restored_injection_pin["injected_node_count"] == 0, restored_injection_pin

        assert original["event_names"], original
        invoke_entry = {"AssetPath": asset, "GraphPath": path,
                       "Operation": "add_invoke_entry", "EntryName": original["event_names"][0],
                       "NodeName": "MCP_Test_InvokeEntry", "Position": {"X": 10, "Y": 30}}
        request("POST", "/control-rigs/graphs", {**invoke_entry, "EntryName": "MCP_MissingEvent"},
                expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**invoke_entry, "bDryRun": True})["changed"]
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])
        invoke_entry_result = request("POST", "/control-rigs/graphs", invoke_entry)
        invoke_entry_node = next(node for node in graph(asset, path)["nodes"]
                                 if node["name"] == invoke_entry_result["node_name"])
        assert invoke_entry_node["class"] == "RigVMInvokeEntryNode", invoke_entry_node
        assert invoke_entry_node["entry_name"] == original["event_names"][0], invoke_entry_node
        assert any(pin["name"] == "Entry" and pin["default"] == original["event_names"][0]
                   for pin in invoke_entry_node["pins"]), invoke_entry_node
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": invoke_entry_result["node_name"], "bConfirm": True})
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])

        free_reroute = {"AssetPath": asset, "GraphPath": path,
                        "Operation": "add_free_reroute", "NodeName": "MCP_Test_FreeReroute",
                        "CPPType": "float", "DefaultValue": "2.5", "bRerouteConstant": True,
                        "CustomWidgetName": "Slider", "Position": {"X": 15, "Y": 35}}
        request("POST", "/control-rigs/graphs", {**free_reroute, "CPPType": ""}, expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**free_reroute, "bDryRun": True})["changed"]
        free_reroute_result = request("POST", "/control-rigs/graphs", free_reroute)
        free_reroute_node = next(node for node in graph(asset, path)["nodes"]
                                 if node["name"] == free_reroute_result["node_name"])
        assert free_reroute_node["class"] == "RigVMRerouteNode", free_reroute_node
        assert len(free_reroute_node["pins"]) == 1 and free_reroute_node["pins"][0]["type"] == "float", free_reroute_node
        assert free_reroute_node["pins"][0]["default"] == "2.5" and free_reroute_node["pins"][0]["constant"], free_reroute_node
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": free_reroute_result["node_name"], "bConfirm": True})
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])

        function_reference = {"AssetPath": asset, "GraphPath": path,
                              "Operation": "add_function_reference", "FunctionName": "FootTrace",
                              "NodeName": "MCP_Test_FootTraceReference",
                              "Position": {"X": 20, "Y": 40}}
        assert not request("POST", "/control-rigs/graphs", {**function_reference, "bDryRun": True})["changed"]
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])
        function_reference_result = request("POST", "/control-rigs/graphs", function_reference)
        function_reference_node = next(node for node in graph(asset, path)["nodes"]
                                       if node["name"] == function_reference_result["node_name"])
        assert function_reference_node["class"] == "RigVMFunctionReferenceNode"
        assert function_reference_node["function_name"] == "FootTrace", function_reference_node
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": function_reference_result["node_name"], "bConfirm": True})
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])

        branch_name = "MCP_Test_Branch"
        branch = {"AssetPath": asset, "GraphPath": path, "Operation": "add_branch",
                  "NodeName": branch_name, "Position": {"X": 40, "Y": 60}}
        assert branch_name not in original_names
        assert not request("POST", "/control-rigs/graphs", {**branch, "bDryRun": True})["changed"]
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])
        branch_result = request("POST", "/control-rigs/graphs", branch)
        branch_name = branch_result["node_name"]
        branch_node = next(node for node in graph(asset, path)["nodes"] if node["name"] == branch_name)
        branch_pins = {pin["name"] for pin in branch_node["pins"]}
        assert branch_node["title"] == "Branch" and {"Condition", "True", "False"} <= branch_pins, branch_node
        assert branch_node["x"] == 40 and branch_node["y"] == 60, branch_node

        comment_name = "MCP_Test_Comment"
        comment = {"AssetPath": asset, "GraphPath": path, "Operation": "add_comment",
                   "NodeName": comment_name, "CommentText": "MCP graph annotation",
                   "Position": {"X": 80, "Y": 120}, "NodeSize": {"X": 360, "Y": 180}}
        assert comment_name not in original_names
        request("POST", "/control-rigs/graphs", {**comment, "CommentText": ""}, expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**comment, "bDryRun": True})["changed"]
        comment_result = request("POST", "/control-rigs/graphs", comment)
        comment_name = comment_result["node_name"]
        comment_node = next(node for node in graph(asset, path)["nodes"] if node["name"] == comment_name)
        assert comment_node["class"] == "RigVMCommentNode" and comment_node["comment_text"] == "MCP graph annotation", comment_node

        constant = {"AssetPath": asset, "GraphPath": path, "Operation": "add_constant",
                    "NodeName": "MCP_Test_Constant", "CPPType": "float",
                    "DefaultValue": "1.25", "Position": {"X": 120, "Y": 160}}
        assert not request("POST", "/control-rigs/graphs", {**constant, "bDryRun": True})["changed"]
        constant_result = request("POST", "/control-rigs/graphs", constant)
        constant_node = next(node for node in graph(asset, path)["nodes"]
                             if node["name"] == constant_result["node_name"])
        assert constant_node["class"] == "RigVMDispatchNode" and constant_node["title"].startswith("Constant") and any(
            pin["default"] == "1.25" for pin in constant_node["pins"]), constant_node

        struct_nodes = []
        for operation, node_name in (("add_make_struct", "MCP_Test_MakeVector"),
                                     ("add_break_struct", "MCP_Test_BreakVector")):
            result = request("POST", "/control-rigs/graphs", {
                "AssetPath": asset, "GraphPath": path, "Operation": operation,
                "NodeName": node_name, "CPPType": "FVector",
                "CPPTypeObjectPath": "/Script/CoreUObject.Vector",
                "DefaultValue": "(X=1.0,Y=2.0,Z=3.0)",
                "Position": {"X": 160, "Y": 200}})
            struct_nodes.append(result["node_name"])
            struct_node = next(node for node in graph(asset, path)["nodes"]
                               if node["name"] == result["node_name"])
            assert struct_node["class"] == "RigVMDispatchNode" and "Vector" in struct_node["title"] and struct_node["pin_count"] >= 1, struct_node

        on_pin_nodes = []
        make_vector_node = next(node for node in graph(asset, path)["nodes"]
                                if node["name"] == struct_nodes[0])
        make_vector_output = next(pin for pin in make_vector_node["pins"]
                                  if pin["type"] == "FVector" and pin["direction"] in ("output", "io"))
        original_display_name = make_vector_output["display_name"]
        original_pin_watched = make_vector_output["watched"]
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_pin_display_name",
            "PinPath": make_vector_output["path"], "PinDisplayName": "MCP Vector Output"})
        pin_state = next(node for node in graph(asset, path)["nodes"]
                         if node["name"] == struct_nodes[0])
        assert next(pin for pin in pin_state["pins"]
                    if pin["path"] == make_vector_output["path"])["display_name"] == "MCP Vector Output"
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_pin_display_name",
            "PinPath": make_vector_output["path"], "PinDisplayName": ""})
        pin_state = next(node for node in graph(asset, path)["nodes"]
                         if node["name"] == struct_nodes[0])
        assert next(pin for pin in pin_state["pins"]
                    if pin["path"] == make_vector_output["path"])["display_name"] == original_display_name

        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_pin_watched",
            "PinPath": make_vector_output["path"], "bPinWatched": not original_pin_watched})
        pin_state = next(node for node in graph(asset, path)["nodes"]
                         if node["name"] == struct_nodes[0])
        assert next(pin for pin in pin_state["pins"]
                    if pin["path"] == make_vector_output["path"])["watched"] is not original_pin_watched
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_pin_watched",
            "PinPath": make_vector_output["path"], "bPinWatched": original_pin_watched})

        break_vector_node = next(node for node in graph(asset, path)["nodes"]
                                 if node["name"] == struct_nodes[1])
        break_vector_input = next(pin for pin in break_vector_node["pins"]
                                  if pin["type"] == "FVector" and pin["direction"] in ("input", "io"))
        break_on_pin = {"AssetPath": asset, "GraphPath": path,
                        "Operation": "add_break_struct_on_pin", "PinPath": make_vector_output["path"],
                        "NodeName": "MCP_Test_BreakOnPin"}
        break_preview = request("POST", "/control-rigs/graphs", {**break_on_pin, "bDryRun": True})
        assert not break_preview["changed"] and break_preview["would_change"]
        break_on_pin_result = request("POST", "/control-rigs/graphs", break_on_pin)
        on_pin_nodes.append(break_on_pin_result["node_name"])
        break_on_pin_node = next(node for node in graph(asset, path)["nodes"]
                                 if node["name"] == break_on_pin_result["node_name"])
        break_on_pin_struct = next(pin for pin in break_on_pin_node["pins"]
                                   if pin["type"] == "FVector" and pin["direction"] in ("input", "io"))
        assert any(link["source"] == make_vector_output["path"]
                   and link["target"] == break_on_pin_struct["path"]
                   for link in graph(asset, path)["links"])

        make_on_pin_result = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_make_struct_on_pin",
            "PinPath": break_vector_input["path"], "NodeName": "MCP_Test_MakeOnPin"})
        on_pin_nodes.append(make_on_pin_result["node_name"])
        make_on_pin_node = next(node for node in graph(asset, path)["nodes"]
                                if node["name"] == make_on_pin_result["node_name"])
        make_on_pin_struct = next(pin for pin in make_on_pin_node["pins"]
                                  if pin["type"] == "FVector" and pin["direction"] in ("output", "io"))
        assert any(link["source"] == make_on_pin_struct["path"]
                   and link["target"] == break_vector_input["path"]
                   for link in graph(asset, path)["links"])

        clamp_result = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_unit",
            "UnitStructPath": "/Script/ControlRig.RigUnit_Clamp_Float",
            "NodeName": "MCP_Test_OnPinClamp"})
        on_pin_parent_nodes = [clamp_result["node_name"]]
        clamp_node = next(node for node in graph(asset, path)["nodes"]
                          if node["name"] == clamp_result["node_name"])
        clamp_value_pin = next(pin for pin in clamp_node["pins"]
                               if pin["name"] == "Value" and pin["type"] == "float"
                               and pin["direction"] == "input")
        constant_on_pin = {"AssetPath": asset, "GraphPath": path,
                           "Operation": "add_constant_on_pin", "PinPath": clamp_value_pin["path"],
                           "NodeName": "MCP_Test_ConstantOnPin"}
        constant_preview = request("POST", "/control-rigs/graphs", {**constant_on_pin, "bDryRun": True})
        assert not constant_preview["changed"] and constant_preview["would_change"]
        constant_on_pin_result = request("POST", "/control-rigs/graphs", constant_on_pin)
        on_pin_nodes.append(constant_on_pin_result["node_name"])
        first_pin_constant = next(node for node in graph(asset, path)["nodes"]
                                  if node["name"] == constant_on_pin_result["node_name"])
        first_constant_value = next(pin for pin in first_pin_constant["pins"]
                                    if pin["type"] == "float" and pin["direction"] in ("io", "output"))
        assert any(link["source"] == first_constant_value["path"]
                   and link["target"] == clamp_value_pin["path"]
                   for link in graph(asset, path)["links"])
        replace_preview = request("POST", "/control-rigs/graphs", {
            **constant_on_pin, "NodeName": "MCP_Test_ReplacementConstant", "bDryRun": True})
        assert replace_preview["requires_confirmation"] and replace_preview["affected_pin_links"] == 1, replace_preview
        request("POST", "/control-rigs/graphs", {
            **constant_on_pin, "NodeName": "MCP_Test_ReplacementConstant"}, expect_error=True)
        replacement_constant = request("POST", "/control-rigs/graphs", {
            **constant_on_pin, "NodeName": "MCP_Test_ReplacementConstant", "bConfirm": True})
        on_pin_nodes.append(replacement_constant["node_name"])

        clamp_min_pin = next(pin for pin in clamp_node["pins"]
                             if pin["name"] == "Min" and pin["type"] == "float"
                             and pin["direction"] == "input")
        input_reroute = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_reroute_on_pin",
            "PinPath": clamp_min_pin["path"], "bRerouteAsInput": True,
            "NodeName": "MCP_Test_InputReroute"})
        on_pin_nodes.append(input_reroute["node_name"])
        input_reroute_node = next(node for node in graph(asset, path)["nodes"]
                                  if node["name"] == input_reroute["node_name"])
        assert input_reroute_node["class"] == "RigVMRerouteNode" and input_reroute["reroute_as_input"]
        assert any(link["target"] == clamp_min_pin["path"]
                   and input_reroute_node["path"] in link["source"]
                   for link in graph(asset, path)["links"])

        clamp_result_pin = next(pin for pin in clamp_node["pins"]
                                if pin["type"] == "float" and pin["direction"] == "output")
        output_reroute = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_reroute_on_pin",
            "PinPath": clamp_result_pin["path"], "bRerouteAsInput": False,
            "NodeName": "MCP_Test_OutputReroute"})
        on_pin_nodes.append(output_reroute["node_name"])
        assert not output_reroute["reroute_as_input"]

        before_collapse_links = graph(asset, path)["links"]
        replacement_link = next(link for link in before_collapse_links
                                if link["target"] == clamp_value_pin["path"]
                                and replacement_constant["node_name"] in link["source"])
        input_boundary_link = next(link for link in before_collapse_links
                                   if link["target"] == clamp_min_pin["path"])
        output_boundary_link = next(link for link in before_collapse_links
                                    if link["source"] == clamp_result_pin["path"])
        collapse_name = "MCP_Test_CollapsedFlow"
        collapse_request = {"AssetPath": asset, "GraphPath": path,
                            "Operation": "collapse_nodes",
                            "NodeNames": [replacement_constant["node_name"], clamp_result["node_name"]],
                            "NodeName": collapse_name}
        collapse_preview = request("POST", "/control-rigs/graphs", {
            **collapse_request, "bDryRun": True})
        assert not collapse_preview["changed"] and collapse_preview["would_change"], collapse_preview
        assert collapse_preview["selected_node_count"] == 2
        assert collapse_preview["internal_link_count"] == 1
        assert collapse_preview["boundary_link_count"] == 2, collapse_preview
        collapsed = request("POST", "/control-rigs/graphs", collapse_request)
        collapsed_outer_graph = graph(asset, path)
        collapse_node = next(node for node in collapsed_outer_graph["nodes"]
                             if node["name"] == collapsed["node_name"])
        assert collapse_node["class"] == "RigVMCollapseNode"
        assert collapse_node["contained_graph_path"] == collapsed["contained_graph_path"]
        assert collapse_node["contained_node_count"] >= 2, collapse_node
        contained_graph = graph(asset, collapsed["contained_graph_path"])
        assert {replacement_constant["node_name"], clamp_result["node_name"]} <= {
            node["name"] for node in contained_graph["nodes"]}, contained_graph
        assert any(input_reroute["node_name"] in link["source"]
                   and collapse_node["path"] in link["target"]
                   for link in collapsed_outer_graph["links"]), collapsed_outer_graph
        assert any(collapse_node["path"] in link["source"]
                   and output_reroute["node_name"] in link["target"]
                   for link in collapsed_outer_graph["links"]), collapsed_outer_graph

        expand_request = {"AssetPath": asset, "GraphPath": path,
                          "Operation": "expand_library_node", "NodeName": collapsed["node_name"]}
        expand_preview = request("POST", "/control-rigs/graphs", {**expand_request, "bDryRun": True})
        assert not expand_preview["changed"] and expand_preview["expanded_node_count"] == 2, expand_preview
        request("POST", "/control-rigs/graphs", expand_request, expect_error=True)
        expanded = request("POST", "/control-rigs/graphs", {**expand_request, "bConfirm": True})
        assert expanded["expanded_node_count"] == 2
        assert {replacement_constant["node_name"], clamp_result["node_name"]} <= set(
            expanded["expanded_node_names"]), expanded
        expanded_graph = graph(asset, path)
        assert collapse_node["name"] not in {node["name"] for node in expanded_graph["nodes"]}
        assert replacement_link in expanded_graph["links"], expanded_graph
        assert input_boundary_link in expanded_graph["links"] and output_boundary_link in expanded_graph["links"], expanded_graph

        typed_nodes = []
        for operation, node_name in (("add_if", "MCP_Test_IfFloat"),
                                     ("add_select", "MCP_Test_SelectFloat")):
            result = request("POST", "/control-rigs/graphs", {
                "AssetPath": asset, "GraphPath": path, "Operation": operation,
                "NodeName": node_name, "CPPType": "float",
                "Position": {"X": 200, "Y": 240}})
            typed_nodes.append(result["node_name"])
            typed_node = next(node for node in graph(asset, path)["nodes"]
                              if node["name"] == result["node_name"])
            expected_title = operation.removeprefix("add_").title()
            assert expected_title in typed_node["title"] and typed_node["pin_count"] >= 2, typed_node

        enum_add = {"AssetPath": asset, "GraphPath": path, "Operation": "add_enum",
                    "NodeName": "MCP_Test_Enum", "CPPTypeObjectPath": "/Script/Engine.EInputEvent",
                    "Position": {"X": 240, "Y": 280}}
        assert not request("POST", "/control-rigs/graphs", {**enum_add, "bDryRun": True})["changed"]
        enum_result = request("POST", "/control-rigs/graphs", enum_add)
        enum_node = next(node for node in graph(asset, path)["nodes"]
                         if node["name"] == enum_result["node_name"])
        assert enum_node["class"] == "RigVMEnumNode" and any(
            pin["type"] == "EInputEvent" and pin["default"] == "IE_Pressed"
            for pin in enum_node["pins"]), enum_node

        array_add = {"AssetPath": asset, "GraphPath": path, "Operation": "add_array",
                     "ArrayOperation": "add", "CPPType": "float",
                     "NodeName": "MCP_Test_ArrayAdd", "Position": {"X": 280, "Y": 320}}
        request("POST", "/control-rigs/graphs", {**array_add, "ArrayOperation": "unknown"}, expect_error=True)
        assert not request("POST", "/control-rigs/graphs", {**array_add, "bDryRun": True})["changed"]
        array_result = request("POST", "/control-rigs/graphs", array_add)
        array_node = next(node for node in graph(asset, path)["nodes"]
                          if node["name"] == array_result["node_name"])
        array_pins = {pin["name"]: pin for pin in array_node["pins"]}
        assert array_node["title"] == "Add" and {"Array", "Element", "Index"} <= array_pins.keys(), array_node
        assert array_pins["Array"]["type"] == "TArray<float>" and array_pins["Element"]["type"] == "float", array_node
        array_pin_path = array_pins["Array"]["path"]
        assert array_pins["Array"]["array"], array_pins["Array"]
        initial_array_elements = array_pins["Array"]["sub_pins"]
        initial_array_size = len(initial_array_elements)
        original_array_pin_expanded = array_pins["Array"]["expanded"]
        array_pin_add_preview = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_array_pin",
            "PinPath": array_pin_path, "bDryRun": True})
        assert not array_pin_add_preview["changed"] and array_pin_add_preview["would_change"]
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "insert_array_pin",
            "PinPath": array_pin_path, "ArrayIndex": initial_array_size + 1}, expect_error=True)
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_array_pin",
            "PinPath": "Missing.Array"}, expect_error=True)
        add_array_element = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_array_pin",
            "PinPath": array_pin_path, "DefaultValue": "1.25"})
        assert add_array_element["array_size_after"] == initial_array_size + 1, add_array_element
        first_array_element_path = add_array_element["array_element_path"]
        array_state = next(node for node in graph(asset, path)["nodes"]
                           if node["name"] == array_result["node_name"])
        current_array_pin = next(pin for pin in array_state["pins"] if pin["path"] == array_pin_path)
        assert len(current_array_pin["sub_pins"]) == initial_array_size + 1, current_array_pin
        assert first_array_element_path in {pin["path"] for pin in current_array_pin["sub_pins"]}
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_pin_expansion",
            "PinPath": array_pin_path, "bPinExpanded": not original_array_pin_expanded})
        array_state = next(node for node in graph(asset, path)["nodes"]
                           if node["name"] == array_result["node_name"])
        current_array_pin = next(pin for pin in array_state["pins"] if pin["path"] == array_pin_path)
        assert current_array_pin["expanded"] is not original_array_pin_expanded, current_array_pin
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_pin_expansion",
            "PinPath": array_pin_path, "bPinExpanded": original_array_pin_expanded})

        inserted_array_element = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "insert_array_pin",
            "PinPath": array_pin_path, "ArrayIndex": 0, "DefaultValue": "3.5"})
        assert inserted_array_element["array_size_after"] == initial_array_size + 2, inserted_array_element
        assert inserted_array_element["array_element_path"] in inserted_array_element["array_element_paths"]
        array_state = next(node for node in graph(asset, path)["nodes"]
                           if node["name"] == array_result["node_name"])
        current_array_pin = next(pin for pin in array_state["pins"] if pin["path"] == array_pin_path)
        inserted_element = current_array_pin["sub_pins"][0]
        assert inserted_element["path"] == inserted_array_element["array_element_path"]
        assert abs(float(inserted_element["default"]) - 3.5) < 1e-5, inserted_element

        duplicated_array_element = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "duplicate_array_pin",
            "PinPath": inserted_array_element["array_element_path"]})
        assert duplicated_array_element["array_size_after"] == initial_array_size + 3, duplicated_array_element
        remove_array_element = {"AssetPath": asset, "GraphPath": path,
                                "Operation": "remove_array_pin",
                                "PinPath": duplicated_array_element["array_element_path"]}
        removal_preview = request("POST", "/control-rigs/graphs", {
            **remove_array_element, "bDryRun": True})
        assert removal_preview["changed"] is False
        assert removal_preview["array_size_before"] == initial_array_size + 3
        assert removal_preview["array_size_after"] == initial_array_size + 2
        request("POST", "/control-rigs/graphs", remove_array_element, expect_error=True)
        request("POST", "/control-rigs/graphs", {**remove_array_element, "bConfirm": True})

        shrink_to_size = initial_array_size + 1
        resize_preview = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_array_pin_size",
            "PinPath": array_pin_path, "ArraySize": shrink_to_size, "bDryRun": True})
        assert resize_preview["changed"] is False and resize_preview["affected_array_elements"] == 1, resize_preview
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_array_pin_size",
            "PinPath": array_pin_path, "ArraySize": shrink_to_size}, expect_error=True)
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_array_pin_size",
            "PinPath": array_pin_path, "ArraySize": shrink_to_size, "bConfirm": True})
        resized_array = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "set_array_pin_size",
            "PinPath": array_pin_path, "ArraySize": initial_array_size + 2, "DefaultValue": "2.0"})
        assert resized_array["array_size_after"] == initial_array_size + 2, resized_array
        clear_preview = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "clear_array_pin",
            "PinPath": array_pin_path, "bDryRun": True})
        assert not clear_preview["changed"] and clear_preview["would_change"]
        assert clear_preview["array_size_after"] == 0, clear_preview
        request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "clear_array_pin",
            "PinPath": array_pin_path}, expect_error=True)
        cleared_array = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "clear_array_pin",
            "PinPath": array_pin_path, "bConfirm": True})
        assert cleared_array["array_size_after"] == 0, cleared_array

        for temporary_node_name in (branch_name, comment_name, constant_result["node_name"], *struct_nodes,
                                    *on_pin_nodes, *on_pin_parent_nodes, *typed_nodes,
                                    enum_result["node_name"], array_result["node_name"]):
            request("POST", "/control-rigs/graphs", {"AssetPath": asset,
                "GraphPath": path, "Operation": "remove_node", "NodeName": temporary_node_name,
                "bConfirm": True})
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])

        node_name = "MCP_Test_GetControlFloat"
        add = {"AssetPath": asset, "GraphPath": path, "Operation": "add_unit",
               "UnitStructPath": "/Script/ControlRig.RigUnit_GetControlFloat",
               "NodeName": node_name, "Position": {"X": 100, "Y": 100}}
        assert not request("POST", "/control-rigs/graphs", {**add, "bDryRun": True})["changed"]
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])
        added = request("POST", "/control-rigs/graphs", add)
        node_name = added["node_name"]
        current = graph(asset, path)
        node = next(n for n in current["nodes"] if n["name"] == node_name)
        assert node["x"] == 100 and node["y"] == 100, node

        request("POST", "/control-rigs/graphs", {"AssetPath": asset,
            "GraphPath": path, "Operation": "set_position", "NodeName": node_name,
            "Position": {"X": 240, "Y": 360}})
        node = next(n for n in graph(asset, path)["nodes"] if n["name"] == node_name)
        assert node["x"] == 240 and node["y"] == 360, node

        editable_pin = next(p for p in node["pins"] if p["type"] == "FName")
        request("POST", "/control-rigs/graphs", {"AssetPath": asset,
            "GraphPath": path, "Operation": "set_pin_default",
            "PinPath": editable_pin["path"], "DefaultValue": "MCP_Test_Control"})
        node = next(n for n in graph(asset, path)["nodes"] if n["name"] == node_name)
        assert any(p["path"] == editable_pin["path"] and p["default"] == "MCP_Test_Control"
                   for p in node["pins"]), node

        link = original["links"][0]
        break_link = {"AssetPath": asset, "GraphPath": path,
                      "Operation": "break_link", "SourcePinPath": link["source"],
                      "TargetPinPath": link["target"]}
        request("POST", "/control-rigs/graphs", break_link)
        assert link not in graph(asset, path)["links"]
        request("POST", "/control-rigs/graphs", {**break_link, "Operation": "add_link"})
        assert link in graph(asset, path)["links"]

        reroute = {"AssetPath": asset, "GraphPath": path, "Operation": "add_reroute",
                   "NodeName": "MCP_Test_Reroute", "SourcePinPath": link["source"],
                   "TargetPinPath": link["target"], "Position": {"X": 420, "Y": 320}}
        assert not request("POST", "/control-rigs/graphs", {**reroute, "bDryRun": True})["changed"]
        reroute_result = request("POST", "/control-rigs/graphs", reroute)
        reroute_node = next(node for node in graph(asset, path)["nodes"]
                            if node["name"] == reroute_result["node_name"])
        assert reroute_node["class"] == "RigVMRerouteNode" and reroute_node["pin_count"] >= 1, reroute_node
        assert link not in graph(asset, path)["links"]
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": reroute_result["node_name"], "bConfirm": True})
        if link not in graph(asset, path)["links"]:
            request("POST", "/control-rigs/graphs", {**break_link, "Operation": "add_link"})

        remove = {"AssetPath": asset, "GraphPath": path,
                  "Operation": "remove_node", "NodeName": node_name}
        assert not request("POST", "/control-rigs/graphs", {**remove, "bDryRun": True})["changed"]
        request("POST", "/control-rigs/graphs", remove, expect_error=True)
        request("POST", "/control-rigs/graphs", {**remove, "bConfirm": True})
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])

        function_path = "FunctionLibrary::|FootTrace"
        function_graph = graph(asset, function_path)
        original_function_node_count = len(function_graph["nodes"])
        original_local_variables = function_graph["local_variables"]
        original_input_arguments = function_graph["input_arguments"]
        original_output_arguments = function_graph["output_arguments"]
        variable_name = "MCP_Test_Local"
        renamed_variable = "MCP_Test_Local_Renamed"
        add_local = {"AssetPath": asset, "GraphPath": function_path,
                     "Operation": "add_local_variable", "VariableName": variable_name,
                     "CPPType": "float", "DefaultValue": "0.5"}
        assert not request("POST", "/control-rigs/graphs", {**add_local, "bDryRun": True})["changed"]
        assert graph(asset, function_path)["local_variables"] == original_local_variables
        request("POST", "/control-rigs/graphs", add_local)
        variable = next(item for item in graph(asset, function_path)["local_variables"]
                        if item["name"] == variable_name)
        assert variable["cpp_type"] == "float" and abs(float(variable["default"]) - 0.5) < 1e-5, variable

        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": function_path,
            "Operation": "set_local_variable_default", "VariableName": variable_name,
            "DefaultValue": "1.25"})
        for is_getter, variable_node_name in ((True, "MCP_Test_Local_Get"),
                                              (False, "MCP_Test_Local_Set")):
            request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": function_path,
                "Operation": "add_variable_node", "VariableName": variable_name,
                "bIsGetter": is_getter, "NodeName": variable_node_name,
                "Position": {"X": 300, "Y": 200}})
        variable_nodes = [node for node in graph(asset, function_path)["nodes"]
                          if node.get("variable_name") == variable_name]
        assert len(variable_nodes) == 2 and {node["variable_getter"] for node in variable_nodes} == {True, False}, variable_nodes
        assert all(node["variable_local"] and node["variable_cpp_type"] == "float"
                   and abs(float(node["variable_default"]) - 1.25) < 1e-5 for node in variable_nodes), variable_nodes

        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": function_path,
            "Operation": "rename_local_variable", "VariableName": variable_name,
            "NewVariableName": renamed_variable})
        function_graph = graph(asset, function_path)
        assert any(item["name"] == renamed_variable for item in function_graph["local_variables"]), function_graph
        assert {node.get("variable_name") for node in function_graph["nodes"]
                if node.get("variable_getter") is not None} == {renamed_variable}, function_graph["nodes"]

        remove_local = {"AssetPath": asset, "GraphPath": function_path,
                        "Operation": "remove_local_variable", "VariableName": renamed_variable}
        removal_preview = request("POST", "/control-rigs/graphs", {**remove_local, "bDryRun": True})
        assert not removal_preview["changed"] and removal_preview["affected_variable_nodes"] == 2, removal_preview
        request("POST", "/control-rigs/graphs", remove_local, expect_error=True)
        request("POST", "/control-rigs/graphs", {**remove_local, "bConfirm": True})
        function_graph = graph(asset, function_path)
        assert function_graph["local_variables"] == original_local_variables, function_graph
        assert len(function_graph["nodes"]) == original_function_node_count, function_graph

        argument_reference = {"AssetPath": asset, "GraphPath": path,
                              "Operation": "add_function_reference", "FunctionName": "FootTrace",
                              "NodeName": "MCP_Test_FootTraceArgumentReference",
                              "Position": {"X": 30, "Y": 80}}
        argument_reference_result = request("POST", "/control-rigs/graphs", argument_reference)
        exposed_input = {"AssetPath": asset, "GraphPath": function_path,
                         "Operation": "add_exposed_pin", "ExposedPinName": "MCP_Test_ExposedInput",
                         "PinDirection": "input", "CPPType": "float", "DefaultValue": "0.75"}
        assert not request("POST", "/control-rigs/graphs", {**exposed_input, "bDryRun": True})["changed"]
        request("POST", "/control-rigs/graphs", exposed_input)
        exposed_output = {**exposed_input, "ExposedPinName": "MCP_Test_ExposedOutput",
                          "PinDirection": "output", "DefaultValue": "0.0"}
        request("POST", "/control-rigs/graphs", exposed_output)
        function_graph = graph(asset, function_path)
        assert any(item["name"] == exposed_input["ExposedPinName"] and item["cpp_type"] == "float"
                   for item in function_graph["input_arguments"]), function_graph
        assert any(item["name"] == exposed_output["ExposedPinName"] and item["cpp_type"] == "float"
                   for item in function_graph["output_arguments"]), function_graph
        refreshed_reference = next(node for node in graph(asset, path)["nodes"]
                                   if node["name"] == argument_reference_result["node_name"])
        refreshed_pin_names = {pin["name"] for pin in refreshed_reference["pins"]}
        assert {exposed_input["ExposedPinName"], exposed_output["ExposedPinName"]} <= refreshed_pin_names, refreshed_reference

        remove_exposed_input = {"AssetPath": asset, "GraphPath": function_path,
                                "Operation": "remove_exposed_pin",
                                "ExposedPinName": exposed_input["ExposedPinName"]}
        removal_preview = request("POST", "/control-rigs/graphs", {**remove_exposed_input, "bDryRun": True})
        assert not removal_preview["changed"] and removal_preview["exposed_pin_name"] == exposed_input["ExposedPinName"], removal_preview
        request("POST", "/control-rigs/graphs", remove_exposed_input, expect_error=True)
        request("POST", "/control-rigs/graphs", {**remove_exposed_input, "bConfirm": True})
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": function_path,
            "Operation": "remove_exposed_pin", "ExposedPinName": exposed_output["ExposedPinName"],
            "bConfirm": True})
        function_graph = graph(asset, function_path)
        assert function_graph["input_arguments"] == original_input_arguments, function_graph
        assert function_graph["output_arguments"] == original_output_arguments, function_graph
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": argument_reference_result["node_name"],
            "bConfirm": True})
        assert len(graph(asset, path)["nodes"]) == len(original["nodes"])

        function_library_path = "FunctionLibrary::"
        original_function_library = graph(asset, function_library_path)
        original_function_names = {node["name"] for node in original_function_library["nodes"]}
        created_function_name = "MCP_Test_Function"
        add_function = {"AssetPath": asset, "GraphPath": function_library_path,
                        "Operation": "add_function", "FunctionName": created_function_name,
                        "bFunctionMutable": True, "Position": {"X": 500, "Y": 240}}
        assert created_function_name not in original_function_names
        assert not request("POST", "/control-rigs/graphs", {**add_function, "bDryRun": True})["changed"]
        assert {node["name"] for node in graph(asset, function_library_path)["nodes"]} == original_function_names
        function_result = request("POST", "/control-rigs/graphs", add_function)
        created_function_path = function_result["function_graph_path"]
        created_function_graph = graph(asset, created_function_path)
        assert {node["name"] for node in created_function_graph["nodes"]} >= {"Entry", "Return"}, created_function_graph

        created_reference = request("POST", "/control-rigs/graphs", {
            "AssetPath": asset, "GraphPath": path, "Operation": "add_function_reference",
            "FunctionName": created_function_name, "NodeName": "MCP_Test_FunctionReference",
            "Position": {"X": 540, "Y": 280}})
        remove_function = {"AssetPath": asset, "GraphPath": function_library_path,
                           "Operation": "remove_function", "FunctionName": created_function_name}
        reference_preview = request("POST", "/control-rigs/graphs", {**remove_function, "bDryRun": True})
        assert not reference_preview["changed"] and reference_preview["affected_function_references"] == 1, reference_preview
        request("POST", "/control-rigs/graphs", {**remove_function, "bConfirm": True}, expect_error=True)
        request("POST", "/control-rigs/graphs", {"AssetPath": asset, "GraphPath": path,
            "Operation": "remove_node", "NodeName": created_reference["node_name"], "bConfirm": True})
        no_reference_preview = request("POST", "/control-rigs/graphs", {**remove_function, "bDryRun": True})
        assert no_reference_preview["affected_function_references"] == 0, no_reference_preview
        request("POST", "/control-rigs/graphs", remove_function, expect_error=True)
        request("POST", "/control-rigs/graphs", {**remove_function, "bConfirm": True})
        assert created_function_path not in {item["path"] for item in request(
            "GET", "/control-rigs/graphs", params={"asset_path": asset})}
        assert {node["name"] for node in graph(asset, function_library_path)["nodes"]} == original_function_names

        graph_validation = request("POST", "/control-rigs/validate", {
            "AssetPath": asset, "GraphPath": path})
        assert graph_validation["valid"] and not graph_validation["errors"], graph_validation
        assert graph_validation["graph_count"] == 1 and graph_validation["node_count"] > 0, graph_validation
        assert graph_validation["pin_count"] > 0 and graph_validation["link_count"] > 0, graph_validation
        rig_validation = request("POST", "/control-rigs/validate", {
            "AssetPath": asset, "bCompile": True})
        assert rig_validation["valid"] and rig_validation["compile_checked"]
        assert rig_validation["compile_valid"] and rig_validation["compile_errors"] == 0, rig_validation
        assert rig_validation["graph_count"] >= graph_validation["graph_count"], rig_validation

        compiled = request("POST", "/control-rigs/compile", {"AssetPath": asset, "bSave": True})
        assert compiled["valid"] and compiled["errors"] == 0 and compiled["saved"], compiled
        assert asset_file.exists(), asset_file
        print("Control Rig graph live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Control Rig was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
