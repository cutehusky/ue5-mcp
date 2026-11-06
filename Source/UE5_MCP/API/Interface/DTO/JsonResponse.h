#pragma once
#include "HttpServerResponse.h"
#include "JsonObjectConverter.h"

template<typename T>
struct FJsonResponse
{
	TUniquePtr<FHttpServerResponse> ToHttpResponse() const
	{
		
		FString ResString;
		FJsonObjectConverter::UStructToJsonObjectString(*Body,ResString);
		TUniquePtr<FHttpServerResponse> Resp = FHttpServerResponse::Create(
			ResString,
			TEXT("application/json")
		);
		
		Resp->Code = Code;
		Resp->HttpVersion = HttpVersion;
		Resp->Headers = Headers;
		return Resp;
	}
	
	FJsonResponse(
		EHttpServerResponseCodes InCode = EHttpServerResponseCodes::Ok,
		TMap<FString, TArray<FString>> InHeaders = TMap<FString, TArray<FString>>(),
		HttpVersion::EHttpServerHttpVersion InHttpVersion = HttpVersion::EHttpServerHttpVersion::HTTP_VERSION_1_1
	): HttpVersion(InHttpVersion), Code(InCode), Headers(MoveTemp(InHeaders)), Body(nullptr)
	{
	}
	
	FJsonResponse(
		T&& InBody,
		EHttpServerResponseCodes InCode = EHttpServerResponseCodes::Ok,
		TMap<FString, TArray<FString>> InHeaders = TMap<FString, TArray<FString>>(),
		HttpVersion::EHttpServerHttpVersion InHttpVersion = HttpVersion::EHttpServerHttpVersion::HTTP_VERSION_1_1
	): HttpVersion(InHttpVersion), Code(InCode), Headers(
		MoveTemp(InHeaders)
	), Body(MakeUnique<T>(MoveTemp(InBody)))
	{
	}
	
	HttpVersion::EHttpServerHttpVersion HttpVersion;

	EHttpServerResponseCodes Code;

	TMap<FString, TArray<FString>> Headers;

	TUniquePtr<T> Body;

	FJsonResponse& SetCode(EHttpServerResponseCodes InCode) { Code = InCode; return *this; }

	FJsonResponse& SetHeader(FString Key, FString Value) {
		Headers.FindOrAdd(Key).Add(Value);
		return *this;
	}
};
