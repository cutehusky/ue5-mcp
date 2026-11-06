#pragma once
#include "CoreMinimal.h"
#include "ModulationRuntimeReq.generated.h"

USTRUCT()
struct FModulationRuntimeStage
{
	GENERATED_BODY()
	UPROPERTY() FString BusPath;
	UPROPERTY() float TargetNormalized = 1.f;
};

USTRUCT()
struct FModulationRuntimeReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() FString DestinationId;
	UPROPERTY() TArray<FString> AssetPaths;
	UPROPERTY() FString AddressFilter;
	UPROPERTY() FString ParameterClassFilter;
	UPROPERTY() FString ParameterFilterPath;
	UPROPERTY() TArray<FModulationRuntimeStage> Stages;
	UPROPERTY() float TargetNormalized = 1.f;
	UPROPERTY() float FadeSeconds = -1.f;
	UPROPERTY() double DurationSeconds = -1.0;
	UPROPERTY() bool bRetriggerOnActivation = false;
	UPROPERTY() bool bDryRun = false;
};
