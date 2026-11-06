#pragma once
#include "CoreMinimal.h"
#include "ModulationFileReq.generated.h"

USTRUCT()
struct FModulationFileReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString BusPath;
	UPROPERTY() FString Operation = TEXT("import");
	UPROPERTY() FString SourceFilePath;
	UPROPERTY() int32 ChannelIndex = 0;
	UPROPERTY() int32 Resolution = 256;
	UPROPERTY() FString BitDepth = TEXT("IEEE_Float");
	UPROPERTY() float Phase = 0.f;
	UPROPERTY() float Top = 0.f;
	UPROPERTY() float Tail = 0.f;
	UPROPERTY() float FadeIn = 0.f;
	UPROPERTY() float FadeOut = 0.f;
	UPROPERTY() bool bNormalize = true;
	UPROPERTY() bool bRemoveOffset = true;
	UPROPERTY() bool bUseStoredSettings = true;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
