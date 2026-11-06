#pragma once
#include "CoreMinimal.h"
struct FModulationCreateReq;
struct FModulationSettingsReq;
struct FModulationStageReq;
struct FModulationConvertReq;
namespace ModulationUtils
{
	bool Supports(const UObject* Asset);
	FString Create(const FModulationCreateReq& Request);
	FString Inspect(UObject* Asset);
	FString Edit(UObject* Asset, const FModulationSettingsReq& Request);
	FString Stage(UObject* Asset, const FModulationStageReq& Request);
	FString Convert(UObject* Asset, const FModulationConvertReq& Request);
	FString Validate(UObject* Asset);
	TArray<FString> ValidationErrors(UObject* Asset);
	UObject* TransientCopy(UObject* Asset);
}
