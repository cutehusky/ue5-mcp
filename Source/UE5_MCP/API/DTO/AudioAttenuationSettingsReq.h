#pragma once

#include "CoreMinimal.h"
#include "AudioAttenuationSettingsReq.generated.h"

USTRUCT()
struct FAudioAttenuationSettingsReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() TMap<FString, double> NumericSettings;
	UPROPERTY() TMap<FString, bool> Flags;
	UPROPERTY() TMap<FString, FString> EnumSettings;
	UPROPERTY() bool bSetShapeExtents = false;
	UPROPERTY() FVector ShapeExtents = FVector::ZeroVector;
	UPROPERTY() bool bSetAudioLinkSettings = false;
	UPROPERTY() FString AudioLinkSettingsPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FAudioAttenuationCurveKey
{
	GENERATED_BODY()
	UPROPERTY() float Time = 0.0f;
	UPROPERTY() float Value = 0.0f;
	UPROPERTY() FString Interpolation = TEXT("Linear");
};

USTRUCT()
struct FAudioAttenuationCurveReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString CurveName;
	UPROPERTY() FString Operation;
	UPROPERTY() FString CurvePath;
	UPROPERTY() TArray<FAudioAttenuationCurveKey> Keys;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FAudioAttenuationEvaluateReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FVector Origin = FVector::ZeroVector;
	UPROPERTY() FRotator Rotation = FRotator::ZeroRotator;
	UPROPERTY() float DistanceScale = 1.0f;
	UPROPERTY() TArray<FVector> Locations;
};

USTRUCT()
struct FAudioAttenuationSubmixSendReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("upsert");
	UPROPERTY() FString SubmixPath;
	UPROPERTY() FString ControlMethod;
	UPROPERTY() bool bSetSendLevel = false;
	UPROPERTY() float SendLevel = 0.0f;
	UPROPERTY() bool bSetDisableManualSendClamp = false;
	UPROPERTY() bool bDisableManualSendClamp = false;
	UPROPERTY() bool bSetMinSendLevel = false;
	UPROPERTY() float MinSendLevel = 0.0f;
	UPROPERTY() bool bSetMaxSendLevel = false;
	UPROPERTY() float MaxSendLevel = 1.0f;
	UPROPERTY() bool bSetMinSendDistance = false;
	UPROPERTY() float MinSendDistance = 0.0f;
	UPROPERTY() bool bSetMaxSendDistance = false;
	UPROPERTY() float MaxSendDistance = 1000.0f;
	UPROPERTY() bool bSetExternalCurve = false;
	UPROPERTY() FString CurvePath;
	UPROPERTY() bool bSetCurveKeys = false;
	UPROPERTY() TArray<FAudioAttenuationCurveKey> Keys;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FAudioAttenuationPluginReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString PluginType;
	UPROPERTY() FString SettingsPath;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FAudioPluginSettingsCreateReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString SettingsClass;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
