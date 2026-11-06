#pragma once
#include "CoreMinimal.h"
#include "AudioAttenuationSettingsReq.h"
#include "ModulationAuthoringReq.generated.h"

USTRUCT()
struct FModulationGeneratorReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() TMap<FString, float> Numeric;
	UPROPERTY() TMap<FString, bool> Flags;
	UPROPERTY() FString Shape;
	UPROPERTY() bool bSetAudioBus = false;
	UPROPERTY() FString AudioBusPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FModulationInputReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("upsert");
	UPROPERTY() FString BusPath;
	UPROPERTY() bool bSampleAndHold = false;
	UPROPERTY() FString Curve = TEXT("Linear");
	UPROPERTY() float Scalar = 2.5f;
	UPROPERTY() FString CurvePath;
	UPROPERTY() TArray<FAudioAttenuationCurveKey> Keys;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FModulationSampleReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString BusPath;
	UPROPERTY() TArray<float> Values;
	UPROPERTY() int32 Samples = 32;
	UPROPERTY() float StepSeconds = .01f;
};
