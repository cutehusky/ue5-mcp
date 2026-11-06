#pragma once

#include "CoreMinimal.h"
#include "AnimationStateMachineReq.generated.h"

USTRUCT()
struct FAnimationStateMachineReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString StateMachineGraphPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString StateName;
	UPROPERTY() FString NodeId;
	UPROPERTY() FString FromStateId;
	UPROPERTY() FString ToStateId;
	UPROPERTY() bool bAlwaysResetOnEntry = false;
	UPROPERTY() int32 X = 0;
	UPROPERTY() int32 Y = 0;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
