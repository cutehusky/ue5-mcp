#pragma once
#include "CoreMinimal.h"
#include "ModulationReq.generated.h"

USTRUCT()
struct FModulationCreateReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString AssetType = TEXT("bus");
	UPROPERTY() FString ParameterType = TEXT("scalar");
	UPROPERTY() FString GeneratorType = TEXT("lfo");
	UPROPERTY() FString ParameterPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FModulationSettingsReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() TMap<FString, float> Numeric;
	UPROPERTY() bool bSetUnitDisplayName = false;
	UPROPERTY() FString UnitDisplayName;
	UPROPERTY() bool bSetParameter = false;
	UPROPERTY() FString ParameterPath;
	UPROPERTY() bool bSetBypass = false;
	UPROPERTY() bool bBypass = false;
	UPROPERTY() bool bSetAddress = false;
	UPROPERTY() bool bOverrideAddress = false;
	UPROPERTY() FString Address;
	UPROPERTY() bool bSetGenerators = false;
	UPROPERTY() TArray<FString> GeneratorPaths;
	UPROPERTY() bool bSetRetriggerOnActivation = false;
	UPROPERTY() bool bRetriggerOnActivation = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FModulationStageReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("upsert");
	UPROPERTY() FString BusPath;
	UPROPERTY() float TargetNormalized = 1.f;
	UPROPERTY() float AttackSeconds = .1f;
	UPROPERTY() float ReleaseSeconds = .1f;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FModulationConvertReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Direction = TEXT("normalized_to_unit");
	UPROPERTY() TArray<float> Values;
};
