#include "BpRoute.h"
#include "UE5_MCP/API/DTO/BpDTO.h"

#include "UE5_MCP/API/DTO/BPComponentOperationReq.h"
#include "UE5_MCP/API/DTO/BPComponentPropertySetReq.h"
#include "UE5_MCP/API/DTO/BPVarOperationReq.h"
#include "UE5_MCP/API/DTO/GraphLayoutReq.h"
#include "UE5_MCP/API/Interface/DTO/ActionResponse.h"
#include "UE5_MCP/Core/BPUtils.h"
#include "UE5_MCP/Core/ClassUtils.h"
#include "UE5_MCP/Core/DebugFeedbackUtils.h"
#include "UE5_MCP/Core/GraphLayoutUtils.h"

void BuildBlueprintRouter(
	TSharedPtr<HttpApp> App)
{
	App->Post("/blueprint",
[] (const FHttpContext<FCreateBPRequest, FCreateBPResponse>& C)
	{
		auto body = C.RequestBody();
		auto ResultPath = ClassUtils::CreateBlueprintFromClass(
			body.ParentClass, body.BpPath);
	
		return C.JsonResponse(FCreateBPResponse {
			.BpPath = ResultPath
		});
	});

	App->Get("/blueprints/functions",
	[](const FHttpContext<void, FString>& C)
	{
		auto BpPath = C.Query("bp_path");
	
		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);
		auto Funcs = BPUtils::GetBlueprintFunctions(Blueprint);
	
		return C.TextResponse(ToJsonString(Funcs), TEXT("application/json"));
	});

	App->Post("/widget-blueprints/create",
	[](const FHttpContext<FCreateBPRequest, FCreateBPResponse>& C)
	{
		auto Body = C.RequestBody();
		const FString ParentClass = Body.ParentClass.IsEmpty() ? TEXT("/Script/UMG.UserWidget") : Body.ParentClass;
		return C.JsonResponse(FCreateBPResponse{
			.BpPath = ClassUtils::CreateWidgetBlueprint(ParentClass, Body.BpPath)
		});
	});

	App->Get("/blueprints/graphs",
	[](const FHttpContext<void, FString>& C)
	{
		auto Blueprint = BPUtils::LoadBlueprint(C.Query("bp_path"));
		const FString GraphName = C.Query("graph_name", TEXT("EventGraph"));
		UEdGraph* Graph = BPUtils::GetEventGraph(Blueprint, GraphName);
		if (!Graph)
			Graph = BPUtils::GetFunctionGraph(Blueprint, GraphName);
		if (!Graph)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Graph not found: %s. Use EventGraph or a function name; get_blueprint_graph lists the graphs."), *GraphName)));
		return C.TextResponse(BPUtils::GetBlueprintGraphJson(Graph), TEXT("application/json"));
	});

	App->Post("/blueprints/graphs/layout",
	[](const FHttpContext<FGraphLayoutReq, FString>& C)
	{
		auto Body = C.RequestBody();
		auto Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		UEdGraph* Graph = BPUtils::GetEventGraph(Blueprint, Body.GraphName);
		if (!Graph)
			Graph = BPUtils::GetFunctionGraph(Blueprint, Body.GraphName);
		if (!Graph)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Graph not found: %s. Use EventGraph or a function name; get_blueprint_graph lists the graphs."), *Body.GraphName)));
		return C.TextResponse(GraphLayoutUtils::Format(Blueprint, Graph, Body.NodeIds, Body.ColumnSpacing, Body.RowSpacing, Body.bDryRun), TEXT("application/json"));
	});
	
	App->Get("/blueprints/variables",
	[](const FHttpContext<void, FString>& C)
	{
		auto BpPath = C.Query("bp_path");
		bool bIncludeAll = C.Query("include_all") == "true";
	
		auto Blueprint = BPUtils::LoadBlueprint(BpPath);
		auto Vars = BPUtils::GetBlueprintVariables(Blueprint, bIncludeAll);
	
		return C.TextResponse(ToJsonString(Vars), TEXT("application/json"));
	});

	App->Post("/blueprints/compile",
	[](const FHttpContext<FBPOperationRequest, FString>& C)
	{
		return C.TextResponse(DebugFeedbackUtils::Compile(C.RequestBody().BpPath), TEXT("application/json"));
	});

	App->Post("/blueprints/variables",
	[](const FHttpContext<FBPVarOperationReq, FActionResponse>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::AddVariableToBlueprint(
			Blueprint,
			body.VarSignature,
			body.DefaultValue
		);

		return C.JsonResponse(FActionResponse {});
	});

	App->Delete("/blueprints/variables",
	[](const FHttpContext<FBPVarOperationReq, FActionResponse>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::DeleteVariableFromBlueprint(
			Blueprint,
			body.VarName
		);

		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/blueprints/variables",
	[](const FHttpContext<FBPVarOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		auto Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		if (!Body.OldVarName.IsEmpty() || !Body.NewVarName.IsEmpty())
			BPUtils::RenameVariableInBlueprint(Blueprint, Body.OldVarName, Body.NewVarName);
		else
			BPUtils::SetVariableDefaultValueInBlueprint(Blueprint, Body.VarName, Body.DefaultValue);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/blueprints/components",
	[](const FHttpContext<FBPComponentOperationReq, FActionResponse>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::AddComponentToBlueprintByName(
			Blueprint,
			body.ComponentClass,
			body.ComponentName,
			body.AttachTo
		);

		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/blueprints/components",
	[](const FHttpContext<void, FString>& C)
	{
		auto BpPath = C.Query("bp_path");

		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);
		auto JsonStr = BPUtils::GetBlueprintComponentsJsonString(Blueprint);

		return C.TextResponse(JsonStr, TEXT("application/json"));
	});

	App->Patch("/blueprints/components/properties",
	[](const FHttpContext<FBPComponentPropertySetReq, FActionResponse>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::SetComponentPropertyInBlueprint(
			Blueprint,
			body.ComponentName,
			body.Properties
		);

		return C.JsonResponse(FActionResponse {});
	});

	App->Delete("/blueprints/components",
	[](const FHttpContext<FBPComponentOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		auto Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		BPUtils::RemoveComponentFromBlueprint(Blueprint, Body.ComponentName);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/blueprints/components",
	[](const FHttpContext<FBPComponentOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		auto Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		if (!Body.NewComponentName.IsEmpty())
			BPUtils::RenameComponentInBlueprint(Blueprint, Body.ComponentName, Body.NewComponentName);
		else
			BPUtils::ChangeAttachToOfComponentInBlueprint(Blueprint, Body.ComponentName, Body.AttachTo);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/blueprints/components/properties",
	[](const FHttpContext<void, FString>& C)
	{
		auto Blueprint = BPUtils::LoadBlueprint(C.Query("bp_path"));
		return C.TextResponse(
			BPUtils::GetComponentsPropertiesJson(Blueprint, C.Query("component_name")),
			TEXT("application/json"));
	});
}
