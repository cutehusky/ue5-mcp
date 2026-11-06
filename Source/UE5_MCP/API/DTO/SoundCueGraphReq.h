#pragma once

#include "CoreMinimal.h"
#include "SoundCueGraphReq.generated.h"

USTRUCT()
struct FSoundCueGraphReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString NodeId;
	UPROPERTY() FString NodeClass;
	UPROPERTY() FString WavePath;
	UPROPERTY() FString SourceNodeId;
	UPROPERTY() FString TargetNodeId;
	UPROPERTY() int32 InputIndex = 0;
	UPROPERTY() int32 PositionX = 0;
	UPROPERTY() int32 PositionY = 0;
	UPROPERTY() bool bSetWave = false;
	UPROPERTY() bool bSetLooping = false;
	UPROPERTY() bool bLooping = false;
	UPROPERTY() TMap<FString, FString> Properties;
	UPROPERTY() bool bReplaceExisting = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bSave = false;
};
