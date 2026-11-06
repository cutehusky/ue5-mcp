#pragma once
#include "CoreMinimal.h"
struct FModulationGeneratorReq;
struct FModulationSettingsReq;
struct FModulationInputReq;
struct FModulationSampleReq;
namespace ModulationAuthoringUtils
{
	bool Supports(const UObject* Asset);
	UClass* GeneratorClass(const FString& Type);
	TArray<FString> Errors(UObject* Asset);
	FString Inspect(UObject* Asset);
	FString Edit(UObject* Asset, const FModulationSettingsReq& Request);
	FString EditGenerator(UObject* Asset, const FModulationGeneratorReq& Request);
	FString Input(UObject* Asset, const FModulationInputReq& Request);
	FString Sample(UObject* Asset, const FModulationSampleReq& Request);
}
