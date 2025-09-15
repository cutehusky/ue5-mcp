#include "Graph.h"

#include "UE5_MCP/API/Utils.h"
#include "UE5_MCP/API/DTO/Graph/AddEventToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/AddFunctionCallToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/AddVariableToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/GenericAddNodeToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/PinOperationReq.h"
#include "UE5_MCP/API/DTO/Graph/SetPinDefaultValueReq.h"
#include "UE5_MCP/Core/BPUtils.h"
#include "UE5_MCP/Core/GraphUtils.h"


bool AddEventToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FAddEventToGraphReq body = Utils::BufferToJson<FAddEventToGraphReq>(Req.Body);
		if (body.bIsCustomEvent)
			GraphUtils::AddCustomEventToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath), body.GraphName),
				body.EventName,
				body.EventSignature);
		else
			GraphUtils::AddEventToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath), body.GraphName),
				body.EventName);
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

bool AddVariableToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FAddVariableToGraphReq body = Utils::BufferToJson<FAddVariableToGraphReq>(Req.Body);
		if (body.bIsSetter)
			GraphUtils::AddSetVariableNodeToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath), body.GraphName),
				body.VarName);
		else
			GraphUtils::AddGetVariableNodeToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),body.GraphName),
				body.VarName);
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

bool AddFunctionCallToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FAddFunctionCallToGraphReq body = Utils::BufferToJson<FAddFunctionCallToGraphReq>(Req.Body);
		if (body.ClassToCall.IsEmpty())
			GraphUtils::AddFunctionCallToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath), body.GraphName),
				body.FunctionName);
		else
			GraphUtils::AddFunctionCallToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath), body.GraphName),
				body.ClassToCall,
				body.FunctionName);
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

bool ConnectPinsHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FPinOperationReq body = Utils::BufferToJson<FPinOperationReq>(Req.Body);
		GraphUtils::ConnectPins(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.OutputNodeId,
			body.OutputPinName,
			body.InputNodeId,
			body.InputPinName);
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

bool BreakPinConnectionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FPinOperationReq body = Utils::BufferToJson<FPinOperationReq>(Req.Body);
		GraphUtils::BreakPinConnection(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.OutputNodeId,
			body.OutputPinName,
			body.InputNodeId,
			body.InputPinName);
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

bool SetPinDefaultValueHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FSetPinDefaultValueReq body = Utils::BufferToJson<FSetPinDefaultValueReq>(Req.Body);
		GraphUtils::SetPinDefaultValue(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.NodeId,
			body.PinName,
			body.DefaultValue);
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

bool GetSupportedNodesHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		TArray<FString> Nodes = GraphUtils::GetSupportedNode();
		FString Json = Utils::ToJsonString(Nodes);
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

bool AddGenericNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddNodeByNameToGraph(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.NodeTypeName);
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

bool AddMakeStructNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddMakeStructNodeToGraph(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.ExtraInfo);
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

bool AddBreakStructNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddBreakStructNodeToGraph(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.ExtraInfo);
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

/*
bool AddSwitchEnumNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddSwitchEnumNodeToGraph(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.ExtraInfo);
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
*/

bool AddDynamicCastNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddDynamicCastNodeToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
					body.GraphName),
				body.ExtraInfo);
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

bool AddClassCastNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddClassCastNodeToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
					body.GraphName),
				body.ExtraInfo);
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

bool AddEnumCastNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddByteToEnumNodeCastToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
					body.GraphName),
				body.ExtraInfo);
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

bool AddMathNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FAddFunctionCallToGraphReq body = Utils::BufferToJson<FAddFunctionCallToGraphReq>(Req.Body);
		GraphUtils::AddMathFunctionCallToGraph(
				BPUtils::LoadBlueprint(body.BpPath),
				BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath), body.GraphName),
				body.FunctionName);
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

bool AddCommentNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try {
		FGenericAddNodeToGraphReq body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		GraphUtils::AddCommentNodeToGraph(
			BPUtils::LoadBlueprint(body.BpPath),
			BPUtils::GetEventGraph(BPUtils::LoadBlueprint(body.BpPath),
				body.GraphName),
			body.ExtraInfo);
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
