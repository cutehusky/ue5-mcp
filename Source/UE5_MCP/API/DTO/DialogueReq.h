#pragma once

#include "CoreMinimal.h"
#include "DialogueReq.generated.h"

USTRUCT()
struct FDialogueCreateReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString AssetType = TEXT("wave");
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FDialogueVoiceSettingsReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Gender;
	UPROPERTY() FString Plurality;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FDialogueWaveSettingsReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() bool bSetSpokenText = false;
	UPROPERTY() FString SpokenText;
	UPROPERTY() bool bSetSubtitleOverride = false;
	UPROPERTY() FString SubtitleOverride;
	UPROPERTY() bool bSetOverrideSubtitle = false;
	UPROPERTY() bool bOverrideSubtitle = false;
	UPROPERTY() bool bSetVoiceActorDirection = false;
	UPROPERTY() FString VoiceActorDirection;
	UPROPERTY() bool bSetMature = false;
	UPROPERTY() bool bMature = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};

USTRUCT()
struct FDialogueContextReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("upsert");
	UPROPERTY() FString ContextId;
	UPROPERTY() bool bSetSpeaker = false;
	UPROPERTY() FString SpeakerPath;
	UPROPERTY() bool bSetTargets = false;
	UPROPERTY() TArray<FString> TargetPaths;
	UPROPERTY() bool bSetSoundWave = false;
	UPROPERTY() FString SoundWavePath;
	UPROPERTY() bool bSetLocalizationKeyFormat = false;
	UPROPERTY() FString LocalizationKeyFormat;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
