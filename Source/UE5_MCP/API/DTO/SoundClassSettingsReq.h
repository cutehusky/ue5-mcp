#pragma once

#include "CoreMinimal.h"
#include "SoundClassSettingsReq.generated.h"

USTRUCT()
struct FSoundClassSettingsReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;

	UPROPERTY() bool bSetParentClass = false;
	UPROPERTY() FString ParentClassPath;
	UPROPERTY() bool bSetDefaultSubmix = false;
	UPROPERTY() FString DefaultSubmixPath;
	UPROPERTY() bool bSetVolume = false;
	UPROPERTY() float Volume = 1.0f;
	UPROPERTY() bool bSetPitch = false;
	UPROPERTY() float Pitch = 1.0f;
	UPROPERTY() bool bSetLowPassFilterFrequency = false;
	UPROPERTY() float LowPassFilterFrequency = 20000.0f;
	UPROPERTY() bool bSetAttenuationDistanceScale = false;
	UPROPERTY() float AttenuationDistanceScale = 1.0f;
	UPROPERTY() bool bSetLFEBleed = false;
	UPROPERTY() float LFEBleed = 0.0f;
	UPROPERTY() bool bSetVoiceCenterChannelVolume = false;
	UPROPERTY() float VoiceCenterChannelVolume = 0.0f;
	UPROPERTY() bool bSetDefault2DReverbSendAmount = false;
	UPROPERTY() float Default2DReverbSendAmount = 0.0f;

	UPROPERTY() bool bSetAlwaysPlay = false;
	UPROPERTY() bool bAlwaysPlay = false;
	UPROPERTY() bool bSetIsUISound = false;
	UPROPERTY() bool bIsUISound = false;
	UPROPERTY() bool bSetIsMusic = false;
	UPROPERTY() bool bIsMusic = false;
	UPROPERTY() bool bSetCenterChannelOnly = false;
	UPROPERTY() bool bCenterChannelOnly = false;
	UPROPERTY() bool bSetApplyAmbientVolumes = false;
	UPROPERTY() bool bApplyAmbientVolumes = false;
	UPROPERTY() bool bSetReverb = false;
	UPROPERTY() bool bReverb = false;
	UPROPERTY() bool bSetApplyEffects = false;
	UPROPERTY() bool bApplyEffects = false;
	UPROPERTY() bool bSetOutputTarget = false;
	UPROPERTY() FString OutputTarget;
	UPROPERTY() bool bSetLoadingBehavior = false;
	UPROPERTY() FString LoadingBehavior;
};
