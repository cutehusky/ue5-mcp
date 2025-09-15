#include "Function.h"

#include "UE5_MCP/API/Utils.h"
#include "UE5_MCP/API/DTO/FunctionOperationReq.h"
#include "UE5_MCP/Core/BPUtils.h"

bool CreateFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FFunctionOperationReq body = Utils::BufferToJson<FFunctionOperationReq>(Req.Body);
		BPUtils::AddFunctionGraph(BPUtils::LoadBlueprint(body.BpPath), body.FunctionName, body.FunctionInputSignature, body.FunctionOutputSignature);
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

bool EditFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FFunctionOperationReq body = Utils::BufferToJson<FFunctionOperationReq>(Req.Body);
		BPUtils::EditFunctionGraph(BPUtils::LoadBlueprint(body.BpPath), body.FunctionName, body.FunctionInputSignature, body.FunctionOutputSignature);
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

bool DeleteFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete)
{
	try
	{
		FFunctionOperationReq body = Utils::BufferToJson<FFunctionOperationReq>(Req.Body);
		BPUtils::RemoveFunctionGraph(BPUtils::LoadBlueprint(body.BpPath), body.FunctionName);
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
