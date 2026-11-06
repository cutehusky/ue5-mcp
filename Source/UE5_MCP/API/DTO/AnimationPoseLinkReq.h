#pragma once

#include "CoreMinimal.h"
#include "AnimationPoseLinkReq.generated.h"

USTRUCT()
struct FAnimationPoseLinkReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString GraphPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString OutputNodeId;
	UPROPERTY() FString OutputPinName;
	UPROPERTY() FString InputNodeId;
	UPROPERTY() FString InputPinName;
	UPROPERTY() bool bConfirmReplace = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
