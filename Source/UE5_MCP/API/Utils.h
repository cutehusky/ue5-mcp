#pragma once
#include "JsonObjectConverter.h"

class Utils
{
public:
	template <typename T>
	static T BufferToJson(const TArray<uint8>& Buffer);

	static FString ToJsonString(const TArray<FString> array);
};

template <typename T>
T Utils::BufferToJson(const TArray<uint8>& Buffer)
{
	FUTF8ToTCHAR Converter(reinterpret_cast<const char*>(Buffer.GetData()), Buffer.Num());
	FString JsonStr(Converter.Length(), Converter.Get());
	T Obj; 
	if (FJsonObjectConverter::JsonObjectStringToUStruct(JsonStr, &Obj, 0, 0))
	{
		return Obj;
	}
	
	UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON: %s"), *JsonStr);
	throw std::runtime_error("Failed to parse JSON");
}