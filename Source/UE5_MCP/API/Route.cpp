#include "Route.h"

#include "HttpServerRequest.h"
#include "IHttpRouter.h"
#include "Route/BP.h"
#include "Route/Function.h"
#include "Route/Graph.h"


void Router::Bind(TSharedPtr<IHttpRouter> Router)
{
	Router->BindRoute(FHttpPath("/create_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(CreateBPHandler));

	Router->BindRoute(FHttpPath("/create_function"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(CreateFunctionHandler));

	Router->BindRoute(FHttpPath("/edit_function"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(EditFunctionHandler));

	Router->BindRoute(FHttpPath("/delete_function"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(DeleteFunctionHandler));

	Router->BindRoute(FHttpPath("/add_function_call_to_graph"),
        EHttpServerRequestVerbs::VERB_POST,
        FHttpRequestHandler::CreateStatic(AddFunctionCallToGraphHandler));

	Router->BindRoute(FHttpPath("/add_event_to_graph"),
        EHttpServerRequestVerbs::VERB_POST,
        FHttpRequestHandler::CreateStatic(AddEventToGraphHandler));

	Router->BindRoute(FHttpPath("/add_variable_to_graph"),
        EHttpServerRequestVerbs::VERB_POST,
        FHttpRequestHandler::CreateStatic(AddVariableToGraphHandler));

	Router->BindRoute(FHttpPath("/get_blueprint_variables"),
        EHttpServerRequestVerbs::VERB_GET,
        FHttpRequestHandler::CreateStatic(GetBPVariablesHandler));

	Router->BindRoute(FHttpPath("/get_blueprint_functions"),
        EHttpServerRequestVerbs::VERB_GET,
        FHttpRequestHandler::CreateStatic(GetBPFunctionHandler));

	Router->BindRoute(FHttpPath("/get_graph"),
        EHttpServerRequestVerbs::VERB_GET,
        FHttpRequestHandler::CreateStatic(GetGraphHandler));

	Router->BindRoute(FHttpPath("/compile_blueprint"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(CompileBPHandler));

	Router->BindRoute(FHttpPath("/get_supported_nodes"),
		EHttpServerRequestVerbs::VERB_GET,
		FHttpRequestHandler::CreateStatic(GetSupportedNodesHandler));

	Router->BindRoute(FHttpPath("/add_variable_to_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddVariableToBPHandler));

	Router->BindRoute(FHttpPath("/rename_variable_in_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(RenameVariableInBPHandler));

	Router->BindRoute(FHttpPath("/delete_variable_from_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(DeleteVariableFromBPHandler));

	Router->BindRoute(FHttpPath("/set_variable_default_value_in_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(SetVariableDefaultValueInBPHandler));

	Router->BindRoute(FHttpPath("/connect_pins"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(ConnectPinsHandler));

	Router->BindRoute(FHttpPath("/break_pin_connection"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(BreakPinConnectionHandler));

	Router->BindRoute(FHttpPath("/set_pin_default_value"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(SetPinDefaultValueHandler));

	Router->BindRoute(FHttpPath("/add_generic_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddGenericNodeToGraphHandler));

	Router->BindRoute(FHttpPath("/add_make_struct_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddMakeStructNodeToGraphHandler));

	Router->BindRoute(FHttpPath("/add_break_struct_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddBreakStructNodeToGraphHandler));

	/*
	Router->BindRoute(FHttpPath("/add_switch_enum_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddSwitchEnumNodeToGraphHandler));
		*/

	Router->BindRoute(FHttpPath("/add_dynamic_cast_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddDynamicCastNodeToGraphHandler));

	Router->BindRoute(FHttpPath("/add_class_cast_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddClassCastNodeToGraphHandler));

	Router->BindRoute(FHttpPath("/add_enum_cast_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddEnumCastNodeToGraphHandler));

	
	Router->BindRoute(FHttpPath("/add_math_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddMathNodeToGraphHandler));

	/*
	Router->BindRoute(FHttpPath("/add_comment_node_to_graph"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddCommentNodeToGraphHandler));
		*/

	Router->BindRoute(FHttpPath("/add_component_to_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(AddComponentToBPHandler));

	Router->BindRoute(FHttpPath("/get_components_of_bp"),
		EHttpServerRequestVerbs::VERB_GET,
		FHttpRequestHandler::CreateStatic(GetComponentsOfBPHandler));

	Router->BindRoute(FHttpPath("/remove_component_from_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(RemoveComponentFromBPHandler));

	Router->BindRoute(FHttpPath("/rename_component_in_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(RenameComponentInBPHandler));

	Router->BindRoute(FHttpPath("/reattach_component_in_bp"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(ReattachComponentInBPHandler));

	Router->BindRoute(FHttpPath("/get_component_properties"),
		EHttpServerRequestVerbs::VERB_GET,
		FHttpRequestHandler::CreateStatic(GetComponentPropertiesHandler));

	Router->BindRoute(FHttpPath("/set_component_property"),
		EHttpServerRequestVerbs::VERB_POST,
		FHttpRequestHandler::CreateStatic(SetComponentPropertyHandler));

}
