#include "BP.h"

#include "UE5_MCP/API/Utils.h"
#include "UE5_MCP/API/DTO/BPComponentOperationReq.h"
#include "UE5_MCP/API/DTO/BPComponentPropertySetReq.h"
#include "UE5_MCP/API/DTO/BPVarOperationReq.h"
#include "UE5_MCP/API/DTO/CreateBPReq.h"
#include "UE5_MCP/Core/BPUtils.h"
#include "UE5_MCP/Core/ClassUtils.h"

bool CreateBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FCreateBPReq body = Utils::BufferToJson<FCreateBPReq>(Req.Body);
		auto Result = ClassUtils::CreateBlueprintFromClass(body.ParentClass, body.BpPath);
		
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(FString::Printf(TEXT("Created BP: %s"), *Result), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

bool GetBPFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		auto BpPath = Req.QueryParams.Find("bp_path");
		if (!BpPath)
			throw std::runtime_error("Missing bp_path parameter");
		
		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);

		if (!Blueprint)
			throw std::runtime_error("Failed to load Blueprint from path");
		
		auto Funcs = BPUtils::GetBlueprintFunctions(Blueprint);

		FString Json = Utils::ToJsonString(Funcs);
		
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(Json, TEXT("application/json"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

bool GetBPVariablesHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		auto BpPath = Req.QueryParams.Find("bp_path");
		auto IncludeAll = Req.QueryParams.Find("include_all");
		bool bIncludeAll = IncludeAll && *IncludeAll == "true";
		
		if (!BpPath)
			throw std::runtime_error("Missing bp_path parameter");
		
		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);
		if (!Blueprint)
			throw std::runtime_error("Failed to load Blueprint from path");
		
		auto Vars = BPUtils::GetBlueprintVariables(Blueprint, bIncludeAll);

		FString Json = Utils::ToJsonString(Vars);
		
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(Json, TEXT("application/json"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

bool GetGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		auto bpPath = Req.QueryParams.Find("bp_path");
		auto graphName = Req.QueryParams.Find("graph_name");
		if (!bpPath || !graphName)
			throw std::runtime_error("Missing bp_path or graph_name parameter");
		auto Blueprint = BPUtils::LoadBlueprint(*bpPath);

		if (!Blueprint)
			throw std::runtime_error("Failed to load Blueprint from path");
		
		auto Graph = BPUtils::GetEventGraph(Blueprint, *graphName);
		
		if (!Graph)
			throw std::runtime_error("Graph not found");
		
		auto Json = BPUtils::GetBlueprintGraphJson(Graph);
		
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(Json, TEXT("application/json"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

bool CompileBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		auto BpPath = Req.QueryParams.Find("bp_path");
		if (!BpPath)
			throw std::runtime_error("Missing bp_path parameter");
		
		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);
		if (!Blueprint)
			throw std::runtime_error("Failed to load Blueprint from path");
		
		BPUtils::CompileBlueprint(Blueprint);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool AddVariableToBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPVarOperationReq body = Utils::BufferToJson<FBPVarOperationReq>(Req.Body);
		BPUtils::AddVariableToBlueprint(BPUtils::LoadBlueprint(body.BpPath), body.VarSignature, body.DefaultValue);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool DeleteVariableFromBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPVarOperationReq body = Utils::BufferToJson<FBPVarOperationReq>(Req.Body);
		BPUtils::DeleteVariableFromBlueprint(BPUtils::LoadBlueprint(body.BpPath), body.VarName);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool RenameVariableInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPVarOperationReq body = Utils::BufferToJson<FBPVarOperationReq>(Req.Body);
		BPUtils::RenameVariableInBlueprint(BPUtils::LoadBlueprint(body.BpPath), body.OldVarName, body.NewVarName);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool SetVariableDefaultValueInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPVarOperationReq body = Utils::BufferToJson<FBPVarOperationReq>(Req.Body);
		BPUtils::SetVariableDefaultValueInBlueprint(BPUtils::LoadBlueprint(body.BpPath), body.VarName, body.DefaultValue);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool AddComponentToBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPComponentOperationReq body = Utils::BufferToJson<FBPComponentOperationReq>(Req.Body);
		BPUtils::AddComponentToBlueprintByName(BPUtils::LoadBlueprint(body.BpPath),
		                                       body.ComponentClass,
		                                       body.ComponentName,
		                                       body.AttachTo);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool GetComponentsOfBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		auto BpPath = Req.QueryParams.Find("bp_path");
		if (!BpPath)
			throw std::runtime_error("Missing bp_path parameter");
		
		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);
		if (!Blueprint)
			throw std::runtime_error("Failed to load Blueprint from path");
		
		auto Json = BPUtils::GetBlueprintComponentsJson(Blueprint);
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(Json, TEXT("application/json"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

bool RemoveComponentFromBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPComponentOperationReq body = Utils::BufferToJson<FBPComponentOperationReq>(Req.Body);
		BPUtils::RemoveComponentFromBlueprint(BPUtils::LoadBlueprint(body.BpPath), body.ComponentName);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool RenameComponentInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPComponentOperationReq body = Utils::BufferToJson<FBPComponentOperationReq>(Req.Body);
		BPUtils::RenameComponentInBlueprint(BPUtils::LoadBlueprint(body.BpPath),
			body.ComponentName, body.NewComponentName);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool ReattachComponentInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPComponentOperationReq body = Utils::BufferToJson<FBPComponentOperationReq>(Req.Body);
		BPUtils::ChangeAttachToOfComponentInBlueprint(BPUtils::LoadBlueprint(body.BpPath),
			body.ComponentName,
			body.AttachTo);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}

bool GetComponentPropertiesHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		auto BpPath = Req.QueryParams.Find("bp_path");
		auto ComponentName = Req.QueryParams.Find("component_name");
		if (!BpPath || !ComponentName)
			throw std::runtime_error("Missing bp_path or component_name parameter");
		
		auto Blueprint = BPUtils::LoadBlueprint(*BpPath);
		if (!Blueprint)
			throw std::runtime_error("Failed to load Blueprint from path");
		
		auto Json = BPUtils::GetComponentsPropertiesJson(Blueprint, *ComponentName);
		
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(Json, TEXT("application/json"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

bool SetComponentPropertyHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FBPComponentPropertySetReq body = Utils::BufferToJson<FBPComponentPropertySetReq>(Req.Body);
		BPUtils::SetComponentPropertyInBlueprint(BPUtils::LoadBlueprint(body.BpPath),
		                                        body.ComponentName,
		                                        body.Properties);
	} catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create("OK", TEXT("text/plain"));
	Resp->Code = EHttpServerResponseCodes::Ok;
	OnComplete(MoveTemp(Resp));
	return true;
}




