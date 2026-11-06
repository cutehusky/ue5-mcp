#pragma once
#include "JsonObjectConverter.h"
#include "Exceptions/HttpException.h"

enum class EHttpServerRequestVerbs : uint16;

FString VerbToString(EHttpServerRequestVerbs Verb);

FString ToJsonString(const TArray<FString>& Array);

template <typename T>
T BufferToJson(const TArray<uint8>& Buffer)
{
	const FUTF8ToTCHAR Converter(reinterpret_cast<const char*>(Buffer.GetData()), Buffer.Num());
	FString JsonStr(Converter.Length(), Converter.Get());
	T Obj;

	FText FailReason;
	if (FJsonObjectConverter::JsonObjectStringToUStruct(
		// DTO fields are intentionally optional at the transport boundary. Route
		// handlers validate the fields required by each operation.
		JsonStr, &Obj, 0, 0, false, &FailReason))
	{
		return Obj;
	}
	
	UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON: %s"), *JsonStr);
	throw FValidationException(FailReason.ToString());
}
