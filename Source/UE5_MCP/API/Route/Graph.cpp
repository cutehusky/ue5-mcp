#include "Graph.h"

#include "UE5_MCP/API/Interface/Utils.h"
#include "HttpServerRequest.h"
#include "HttpServerResponse.h"
#include "UE5_MCP/API/DTO/Graph/AddEventToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/AddFunctionCallToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/AddVariableToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/GenericAddNodeToGraphReq.h"
#include "UE5_MCP/API/DTO/Graph/PinOperationReq.h"
#include "UE5_MCP/API/DTO/Graph/SetPinDefaultValueReq.h"
#include "UE5_MCP/Core/BPUtils.h"
#include "UE5_MCP/Core/GraphUtils.h"
#include "Dom/JsonObject.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace Utils
{
	using ::BufferToJson;
	using ::ToJsonString;
}

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

bool GetGraphNodeCatalogHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		const FGenericAddNodeToGraphReq Body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		const FString Type = Body.NodeKind.IsEmpty() ? TEXT("blueprint") : Body.NodeKind;
		const FString Json = Utils::ToJsonString(GraphUtils::GetSupportedNodesForGraphType(Type));
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(Json, TEXT("application/json"));
		Resp->Code = EHttpServerResponseCodes::Ok;
		OnComplete(MoveTemp(Resp));
		return true;
	}
	catch (std::runtime_error& e)
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
		Resp->Code = EHttpServerResponseCodes::ServerError;
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

using FConfiguredGraphNodeOperation = TFunction<void(UBlueprint*, UEdGraph*, const FGenericAddNodeToGraphReq&)>;

bool AddConfiguredGraphNodeHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete,
	const FConfiguredGraphNodeOperation& Operation)
{
	try
	{
		const FGenericAddNodeToGraphReq Body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		UBlueprint* Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		UEdGraph* Graph = BPUtils::GetEventGraph(Blueprint, Body.GraphName);
		if (!Graph)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Graph not found: %s. Use EventGraph or a function name; get_blueprint_graph lists the graphs."), *Body.GraphName)));
		Operation(Blueprint, Graph, Body);
	}
	catch (std::runtime_error& e)
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

bool AddBranchNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	return AddConfiguredGraphNodeHandler(Req, OnComplete,
		[](UBlueprint* Blueprint, UEdGraph* Graph, const FGenericAddNodeToGraphReq&)
		{
			GraphUtils::AddBranchNodeToGraph(Blueprint, Graph);
		});
}

bool AddExecutionSequenceNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	return AddConfiguredGraphNodeHandler(Req, OnComplete,
		[](UBlueprint* Blueprint, UEdGraph* Graph, const FGenericAddNodeToGraphReq& Body)
		{
			int32 OutputCount = 2;
			LexTryParseString(OutputCount, *Body.ExtraInfo);
			GraphUtils::AddExecutionSequenceNodeToGraph(Blueprint, Graph, OutputCount);
		});
}

bool AddSwitchEnumNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	return AddConfiguredGraphNodeHandler(Req, OnComplete,
		[](UBlueprint* Blueprint, UEdGraph* Graph, const FGenericAddNodeToGraphReq& Body)
		{
			GraphUtils::AddSwitchEnumNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		});
}

bool AddSwitchIntegerNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	return AddConfiguredGraphNodeHandler(Req, OnComplete,
		[](UBlueprint* Blueprint, UEdGraph* Graph, const FGenericAddNodeToGraphReq& Body)
		{
			int32 StartIndex = 0;
			LexTryParseString(StartIndex, *Body.ExtraInfo);
			GraphUtils::AddSwitchIntegerNodeToGraph(Blueprint, Graph, StartIndex);
		});
}

bool AddSwitchStringNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	return AddConfiguredGraphNodeHandler(Req, OnComplete,
		[](UBlueprint* Blueprint, UEdGraph* Graph, const FGenericAddNodeToGraphReq&)
		{
			GraphUtils::AddSwitchStringNodeToGraph(Blueprint, Graph);
		});
}

bool AddSwitchNameNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	return AddConfiguredGraphNodeHandler(Req, OnComplete,
		[](UBlueprint* Blueprint, UEdGraph* Graph, const FGenericAddNodeToGraphReq&)
		{
			GraphUtils::AddSwitchNameNodeToGraph(Blueprint, Graph);
	});
}

bool AddGraphNodeHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		const FGenericAddNodeToGraphReq Body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		UBlueprint* Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		UEdGraph* Graph = BPUtils::GetEventGraph(Blueprint, Body.GraphName);
		if (!Graph)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Graph not found: %s. Use EventGraph or a function name; get_blueprint_graph lists the graphs."), *Body.GraphName)));

		const FString Kind = Body.NodeKind.ToLower();
		if (Kind == TEXT("generic"))
			GraphUtils::AddNodeByNameToGraph(Blueprint, Graph, Body.NodeTypeName);
		else if (Kind == TEXT("branch"))
			GraphUtils::AddBranchNodeToGraph(Blueprint, Graph);
		else if (Kind == TEXT("execution_sequence"))
		{
			int32 OutputCount = 2;
			LexTryParseString(OutputCount, *Body.ExtraInfo);
			GraphUtils::AddExecutionSequenceNodeToGraph(Blueprint, Graph, OutputCount);
		}
		else if (Kind == TEXT("switch_enum"))
			GraphUtils::AddSwitchEnumNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("switch_integer"))
		{
			int32 StartIndex = 0;
			LexTryParseString(StartIndex, *Body.ExtraInfo);
			GraphUtils::AddSwitchIntegerNodeToGraph(Blueprint, Graph, StartIndex);
		}
		else if (Kind == TEXT("switch_string"))
			GraphUtils::AddSwitchStringNodeToGraph(Blueprint, Graph);
		else if (Kind == TEXT("switch_name"))
			GraphUtils::AddSwitchNameNodeToGraph(Blueprint, Graph);
		else if (Kind == TEXT("make_struct"))
			GraphUtils::AddMakeStructNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("break_struct"))
			GraphUtils::AddBreakStructNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("dynamic_cast"))
			GraphUtils::AddDynamicCastNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("class_cast"))
			GraphUtils::AddClassCastNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("enum_cast"))
			GraphUtils::AddByteToEnumNodeCastToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("math"))
			GraphUtils::AddMathFunctionCallToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Kind == TEXT("comment"))
			GraphUtils::AddCommentNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Unsupported node_kind: %s"), *Body.NodeKind)));
	}
	catch (std::runtime_error& e)
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

bool AddSwitchNodeHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		const FGenericAddNodeToGraphReq Body = Utils::BufferToJson<FGenericAddNodeToGraphReq>(Req.Body);
		UBlueprint* Blueprint = BPUtils::LoadBlueprint(Body.BpPath);
		UEdGraph* Graph = BPUtils::GetEventGraph(Blueprint, Body.GraphName);
		if (!Graph)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Graph not found: %s. Use EventGraph or a function name; get_blueprint_graph lists the graphs."), *Body.GraphName)));

		const FString Type = Body.NodeKind.ToLower();
		if (Type == TEXT("enum"))
			GraphUtils::AddSwitchEnumNodeToGraph(Blueprint, Graph, Body.ExtraInfo);
		else if (Type == TEXT("integer") || Type == TEXT("int"))
		{
			int32 StartIndex = 0;
			LexTryParseString(StartIndex, *Body.ExtraInfo);
			GraphUtils::AddSwitchIntegerNodeToGraph(Blueprint, Graph, StartIndex);
		}
		else if (Type == TEXT("string"))
			GraphUtils::AddSwitchStringNodeToGraph(Blueprint, Graph);
		else if (Type == TEXT("name"))
			GraphUtils::AddSwitchNameNodeToGraph(Blueprint, Graph);
		else
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Unsupported switch_type: %s"), *Body.NodeKind)));
	}
	catch (std::runtime_error& e)
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

namespace
{
	TSharedPtr<FJsonObject> ParseBody(const FHttpServerRequest& Req)
	{
		const FUTF8ToTCHAR Text(reinterpret_cast<const ANSICHAR*>(Req.Body.GetData()), Req.Body.Num());
		const FString Json(Text.Length(), Text.Get());
		TSharedPtr<FJsonObject> Object;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
		FJsonSerializer::Deserialize(Reader, Object);
		return Object;
	}

	UEdGraph* GraphFromBody(const TSharedPtr<FJsonObject>& Body)
	{
		if (!Body) return nullptr;
		return BPUtils::GetEventGraph(BPUtils::LoadBlueprint(Body->GetStringField(TEXT("BpPath"))), Body->GetStringField(TEXT("GraphName")));
	}

	FString DescribeNode(const UEdGraphNode* Node)
	{
		FString Result;
		const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Result);
		J->WriteObjectStart();
		J->WriteValue(TEXT("success"), true);
		J->WriteValue(TEXT("node_id"), Node->NodeGuid.ToString());
		J->WriteValue(TEXT("node_title"), Node->GetNodeTitle(ENodeTitleType::ListView).ToString());
		J->WriteArrayStart(TEXT("pins"));
		for (const UEdGraphPin* Pin : Node->Pins)
		{
			J->WriteObjectStart();
			J->WriteValue(TEXT("name"), Pin->PinName.ToString());
			J->WriteValue(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
			J->WriteValue(TEXT("type"), Pin->PinType.PinCategory.ToString());
			J->WriteObjectEnd();
		}
		J->WriteArrayEnd();
		J->WriteObjectEnd();
		J->Close();
		return Result;
	}

	// Runs an add-node handler, then replies with the node it added.
	FHttpRequestHandler ReportingNewNode(bool (*Handler)(const FHttpServerRequest&, const FHttpResultCallback&))
	{
		return FHttpRequestHandler::CreateLambda([Handler](const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
		{
			UEdGraph* Graph = nullptr;
			TSet<FGuid> Before;
			try
			{
				Graph = GraphFromBody(ParseBody(Req));
				if (Graph) for (const UEdGraphNode* Node : Graph->Nodes) if (Node) Before.Add(Node->NodeGuid);
			}
			catch (std::runtime_error&) { Graph = nullptr; }  // The handler reports the bad path itself.
			return Handler(Req, [Graph, Before, OnComplete](TUniquePtr<FHttpServerResponse> Resp)
			{
				if (Resp->Code == EHttpServerResponseCodes::Ok && Graph)
					for (const UEdGraphNode* Node : Graph->Nodes)
						if (Node && !Before.Contains(Node->NodeGuid))
						{
							Resp = FHttpServerResponse::Create(DescribeNode(Node), TEXT("application/json"));
							Resp->Code = EHttpServerResponseCodes::Ok;
							break;
						}
				OnComplete(MoveTemp(Resp));
			});
		});
	}

	bool DeleteGraphNodeHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
	{
		TUniquePtr<FHttpServerResponse> Resp;
		try
		{
			const TSharedPtr<FJsonObject> Body = ParseBody(Req);
			UEdGraph* Graph = GraphFromBody(Body);
			FGuid Id;
			if (!Graph || !FGuid::Parse(Body->GetStringField(TEXT("NodeId")), Id)) throw std::runtime_error("A valid graph and NodeId are required");
			UEdGraphNode* Node = nullptr;
			for (UEdGraphNode* Candidate : Graph->Nodes) if (Candidate && Candidate->NodeGuid == Id) Node = Candidate;
			if (!Node) throw std::runtime_error("Node not found");
			FBlueprintEditorUtils::RemoveNode(BPUtils::LoadBlueprint(Body->GetStringField(TEXT("BpPath"))), Node, true);
			Resp = FHttpServerResponse::Create(TEXT("{\"success\":true}"), TEXT("application/json"));
			Resp->Code = EHttpServerResponseCodes::Ok;
		}
		catch (std::runtime_error& e)
		{
			Resp = FHttpServerResponse::Create(FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())), TEXT("text/plain"));
			Resp->Code = EHttpServerResponseCodes::ServerError;
		}
		OnComplete(MoveTemp(Resp));
		return true;
	}
}

void BuildGraphRouter(TSharedPtr<HttpApp> App)
{
	using V = EHttpServerRequestVerbs;
	App->Raw(V::VERB_POST, TEXT("/graphs/nodes/delete"), FHttpRequestHandler::CreateStatic(&DeleteGraphNodeHandler));
	App->Raw(V::VERB_POST, TEXT("/add_event_to_graph"), ReportingNewNode(&AddEventToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_variable_to_graph"), ReportingNewNode(&AddVariableToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_function_call_to_graph"), ReportingNewNode(&AddFunctionCallToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/connect_pins"), FHttpRequestHandler::CreateStatic(&ConnectPinsHandler));
	App->Raw(V::VERB_POST, TEXT("/break_pin_connection"), FHttpRequestHandler::CreateStatic(&BreakPinConnectionHandler));
	App->Raw(V::VERB_POST, TEXT("/set_pin_default_value"), FHttpRequestHandler::CreateStatic(&SetPinDefaultValueHandler));
	App->Raw(V::VERB_GET, TEXT("/get_supported_nodes"), FHttpRequestHandler::CreateStatic(&GetSupportedNodesHandler));
	App->Raw(V::VERB_POST, TEXT("/graphs/nodes/catalog"), FHttpRequestHandler::CreateStatic(&GetGraphNodeCatalogHandler));
	App->Raw(V::VERB_POST, TEXT("/add_generic_node_to_graph"), ReportingNewNode(&AddGenericNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_make_struct_node_to_graph"), ReportingNewNode(&AddMakeStructNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_break_struct_node_to_graph"), ReportingNewNode(&AddBreakStructNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_dynamic_cast_node_to_graph"), ReportingNewNode(&AddDynamicCastNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_class_cast_node_to_graph"), ReportingNewNode(&AddClassCastNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_enum_cast_node_to_graph"), ReportingNewNode(&AddEnumCastNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_math_node_to_graph"), ReportingNewNode(&AddMathNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_comment_node_to_graph"), ReportingNewNode(&AddCommentNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_branch_node_to_graph"), ReportingNewNode(&AddBranchNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/add_execution_sequence_node_to_graph"), ReportingNewNode(&AddExecutionSequenceNodeToGraphHandler));
	App->Raw(V::VERB_POST, TEXT("/graphs/switch-nodes"), FHttpRequestHandler::CreateStatic(&AddSwitchNodeHandler));
	App->Raw(V::VERB_POST, TEXT("/graphs/nodes"), FHttpRequestHandler::CreateStatic(&AddGraphNodeHandler));
}
