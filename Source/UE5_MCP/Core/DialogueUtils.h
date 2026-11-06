#pragma once

#include "CoreMinimal.h"

class UDialogueVoice;
class UDialogueWave;
struct FDialogueCreateReq;
struct FDialogueVoiceSettingsReq;
struct FDialogueWaveSettingsReq;
struct FDialogueContextReq;

namespace DialogueUtils
{
	FString Create(const FDialogueCreateReq& Request);
	FString VoiceJson(UDialogueVoice* Asset);
	FString EditVoice(UDialogueVoice* Asset, const FDialogueVoiceSettingsReq& Request);
	FString WaveJson(UDialogueWave* Asset);
	FString EditWave(UDialogueWave* Asset, const FDialogueWaveSettingsReq& Request);
	FString EditContext(UDialogueWave* Asset, const FDialogueContextReq& Request);
	FString Resolve(UDialogueWave* Asset, const FDialogueContextReq& Request);
	FString Validate(UObject* Asset);
}
