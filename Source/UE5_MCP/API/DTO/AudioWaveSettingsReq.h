#pragma once

#include "CoreMinimal.h"
#include "AudioWaveSettingsReq.generated.h"

USTRUCT()
struct FAudioWaveSettingsReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString CompressionType;
	UPROPERTY() bool bSetCompressionQuality = false;
	UPROPERTY() int32 CompressionQuality = 0;
	UPROPERTY() FString SampleRateQuality;
	UPROPERTY() bool bSetLooping = false;
	UPROPERTY() bool bLooping = false;
	UPROPERTY() FString LoadingBehavior;
	UPROPERTY() bool bSetCloudStreaming = false;
	UPROPERTY() bool bCloudStreaming = false;
	UPROPERTY() bool bSetSoundClass = false;
	UPROPERTY() FString SoundClassPath;
	UPROPERTY() bool bSetAttenuation = false;
	UPROPERTY() FString AttenuationPath;
	UPROPERTY() bool bSetConcurrencyPaths = false;
	UPROPERTY() TArray<FString> ConcurrencyPaths;
	UPROPERTY() bool bSetOverrideConcurrency = false;
	UPROPERTY() bool bOverrideConcurrency = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
