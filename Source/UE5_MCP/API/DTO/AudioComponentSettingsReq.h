#pragma once
#include "CoreMinimal.h"
#include "AudioComponentSettingsReq.generated.h"
USTRUCT()
struct FAudioComponentSettingsReq
{
	GENERATED_BODY()
	UPROPERTY() FString BpPath;
	UPROPERTY() FString ActorPath;
	UPROPERTY() FString ComponentName;
	UPROPERTY() TMap<FString, float> NumericSettings;
	UPROPERTY() TMap<FString, bool> BoolSettings;
	UPROPERTY() TMap<FString, FString> References;
	UPROPERTY() bool bSetConcurrency = false;
	UPROPERTY() bool bResetInheritedOverride = false;
	UPROPERTY() TArray<FString> ConcurrencyPaths;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
