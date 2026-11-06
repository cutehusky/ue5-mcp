#pragma once

#include "CoreMinimal.h"
#include "SoundMixSettingsReq.generated.h"

USTRUCT()
struct FSoundMixEQBandEditReq
{
	GENERATED_BODY()

	UPROPERTY() int32 BandIndex = -1;
	UPROPERTY() bool bSetFrequencyCenter = false;
	UPROPERTY() float FrequencyCenter = 0.0f;
	UPROPERTY() bool bSetGain = false;
	UPROPERTY() float Gain = 0.0f;
	UPROPERTY() bool bSetBandwidth = false;
	UPROPERTY() float Bandwidth = 0.0f;
};

USTRUCT()
struct FSoundMixSettingsReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
	UPROPERTY() bool bSetInitialDelay = false;
	UPROPERTY() float InitialDelay = 0.0f;
	UPROPERTY() bool bSetFadeInTime = false;
	UPROPERTY() float FadeInTime = 0.0f;
	UPROPERTY() bool bSetDuration = false;
	UPROPERTY() float Duration = -1.0f;
	UPROPERTY() bool bSetFadeOutTime = false;
	UPROPERTY() float FadeOutTime = 0.0f;
	UPROPERTY() bool bSetApplyEQ = false;
	UPROPERTY() bool bApplyEQ = false;
	UPROPERTY() bool bSetEQPriority = false;
	UPROPERTY() float EQPriority = 0.0f;
	UPROPERTY() TArray<FSoundMixEQBandEditReq> EQBandEdits;
};

USTRUCT()
struct FSoundMixAdjusterReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("upsert");
	UPROPERTY() FString SoundClassPath;
	UPROPERTY() bool bSetVolumeAdjuster = false;
	UPROPERTY() float VolumeAdjuster = 1.0f;
	UPROPERTY() bool bSetPitchAdjuster = false;
	UPROPERTY() float PitchAdjuster = 1.0f;
	UPROPERTY() bool bSetLowPassFilterFrequency = false;
	UPROPERTY() float LowPassFilterFrequency = 20000.0f;
	UPROPERTY() bool bSetVoiceCenterChannelVolumeAdjuster = false;
	UPROPERTY() float VoiceCenterChannelVolumeAdjuster = 1.0f;
	UPROPERTY() bool bSetApplyToChildren = false;
	UPROPERTY() bool bApplyToChildren = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bSave = false;
};
