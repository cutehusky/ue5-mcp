#include "Function.h"

#include "UE5_MCP/API/DTO/FunctionOperationReq.h"
#include "UE5_MCP/Core/BPUtils.h"


void BuildBlueprintFunctionRouter(TSharedPtr<HttpApp> App)
{
	App->Post("/blueprints/functions",
[](const FHttpContext<FFunctionOperationReq, FString>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::AddFunctionGraph(
			Blueprint,
			body.FunctionName,
			body.FunctionInputSignature,
			body.FunctionOutputSignature
		);

		return C.TextResponse("OK");
	});

	App->Patch("/blueprints/functions",
	[](const FHttpContext<FFunctionOperationReq, FString>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::EditFunctionGraph(
			Blueprint,
			body.FunctionName,
			body.FunctionInputSignature,
			body.FunctionOutputSignature
		);

		return C.TextResponse("OK");
	});

	App->Delete("/blueprints/functions",
[](const FHttpContext<FFunctionOperationReq, FString>& C)
	{
		auto body = C.RequestBody();

		auto Blueprint = BPUtils::LoadBlueprint(body.BpPath);

		BPUtils::RemoveFunctionGraph(
			Blueprint,
			body.FunctionName
		);

		return C.TextResponse("OK");
	});
	
}
