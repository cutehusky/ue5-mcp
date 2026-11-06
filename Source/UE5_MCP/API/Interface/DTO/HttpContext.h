#pragma once
#include "ErrorResponse.h"
#include "HttpServerRequest.h"
#include "HttpServerResponse.h"


template <typename TResponse>
struct IResponse
{
	static TUniquePtr<FHttpServerResponse> JsonResponse(
		TResponse&& ResponseData,
		EHttpServerResponseCodes StatusCode = EHttpServerResponseCodes::Ok)
	{
		const FJsonResponse<TResponse> JsonRes(Forward<TResponse>(ResponseData), StatusCode);
		return JsonRes.ToHttpResponse();
	}
};

template<>
struct IResponse<FString>
{
	static TUniquePtr<FHttpServerResponse> TextResponse(
		const FString& ResponseData,
		const FString& ContentType = TEXT("text/plain"))
	{
		return FHttpServerResponse::Create(ResponseData, ContentType);
	}
};

template<>
struct IResponse<TArray<uint8>>
{
	static TUniquePtr<FHttpServerResponse> BinaryResponse(
		TArray<uint8>&& ResponseData,
		const FString& ContentType = TEXT("application/octet-stream"))
	{
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			Forward<TArray<uint8>>(ResponseData),
			ContentType);
		Resp->Code = EHttpServerResponseCodes::Ok;
		return Resp;
	}
};

struct FHttpContextBase
{
	const FHttpServerRequest &RawRequest;

	FHttpContextBase(const FHttpServerRequest& InRequest): RawRequest(InRequest)
	{
	}
	
	FString Query(
		const FString& Key,
		const FString& DefaultValue = TEXT("")) const
	{
		const FString* ValuePtr = RawRequest.QueryParams.Find(Key);
		return ValuePtr ? *ValuePtr : DefaultValue;
	}

	FString Header(
		const FString& Key,
		const FString& DefaultValue = TEXT("")) const
	{
		const TArray<FString>* ValuesPtr = RawRequest.Headers.Find(Key);
		return (ValuesPtr && ValuesPtr->Num() > 0) ? (*ValuesPtr)[0] : DefaultValue;
	}

	FString Param(
		const FString& Key,
		const FString& DefaultValue = TEXT("")) const
	{
		const FString* ValuePtr = RawRequest.PathParams.Find(Key);
		return ValuePtr ? *ValuePtr : DefaultValue;
	}
	
	static TUniquePtr<FHttpServerResponse> ErrorResponse(
		const FString& ErrorType,
		const FString& ErrorMessage,
		const FString& ErrorDetails = TEXT(""),
		const EHttpServerResponseCodes StatusCode = EHttpServerResponseCodes::ServerError)
	{
		const FJsonErrorResponse JsonResp(ErrorType, ErrorMessage, ErrorDetails, StatusCode);
		return JsonResp.ToHttpResponse();
	}
};


template<typename TRequest, typename TResponse>
struct FHttpContext: FHttpContextBase, IResponse<TResponse>
{
	using TRequestType = TRequest;
	using TResponseType = TResponse;

	TRequest RequestBody() const
	{
		return BufferToJson<TRequest>(this->RawRequest.Body);
	}

	FHttpContext(const FHttpServerRequest& InRequest): FHttpContextBase(InRequest)
	{
	}
};

template<typename TResponse>
struct FHttpContext<void, TResponse> : FHttpContextBase, IResponse<TResponse>
{
	using TRequestType = void;
	using TResponseType = TResponse;
	
	FHttpContext(const FHttpServerRequest& InRequest): FHttpContextBase(InRequest)
	{
	}
};

