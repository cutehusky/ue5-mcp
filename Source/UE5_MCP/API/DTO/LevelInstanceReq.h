#pragma once

#include "CoreMinimal.h"
#include "LevelInstanceReq.generated.h"

USTRUCT()
struct FLevelInstanceReq
{
	GENERATED_BODY()
	UPROPERTY() FString ActorPath;
	UPROPERTY() FString WorldAssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString Label;
	UPROPERTY() FTransform Transform = FTransform::Identity;
	UPROPERTY() bool bLoad = true;
	UPROPERTY() bool bWait = true;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bSave = false;
	UPROPERTY() int32 BreakDepth = 1;
	UPROPERTY() bool bKeepFolders = true;
};
