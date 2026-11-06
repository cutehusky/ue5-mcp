#pragma once

#include "CoreMinimal.h"
#include "SoundSubmixSettingsReq.generated.h"

USTRUCT()
struct FSoundSubmixSettingsReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
	UPROPERTY() bool bSetParentSubmix = false;
	UPROPERTY() FString ParentSubmixPath;
	UPROPERTY() bool bSetAutoDisable = false;
	UPROPERTY() bool bAutoDisable = true;
	UPROPERTY() bool bSetAutoDisableTime = false;
	UPROPERTY() float AutoDisableTime = 0.01f;
	UPROPERTY() bool bSetMuteWhenBackgrounded = false;
	UPROPERTY() bool bMuteWhenBackgrounded = false;
	UPROPERTY() bool bSetEnvelopeFollowerAttackTime = false;
	UPROPERTY() int32 EnvelopeFollowerAttackTime = 10;
	UPROPERTY() bool bSetEnvelopeFollowerReleaseTime = false;
	UPROPERTY() int32 EnvelopeFollowerReleaseTime = 100;
	UPROPERTY() bool bSetOutputVolumeDb = false;
	UPROPERTY() float OutputVolumeDb = 0.0f;
	UPROPERTY() bool bSetWetLevelDb = false;
	UPROPERTY() float WetLevelDb = 0.0f;
	UPROPERTY() bool bSetDryLevelDb = false;
	UPROPERTY() float DryLevelDb = 0.0f;
};

USTRUCT()
struct FSoundSubmixEffectReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("add");
	UPROPERTY() FString EffectPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bSave = false;
};
