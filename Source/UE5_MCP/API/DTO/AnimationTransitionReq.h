#pragma once

#include "CoreMinimal.h"
#include "AnimationTransitionReq.generated.h"

USTRUCT()
struct FAnimationTransitionReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString StateMachineGraphPath;
	UPROPERTY() FString TransitionId;
	UPROPERTY() bool bSetCrossfadeDuration = false;
	UPROPERTY() float CrossfadeDuration = 0.2f;
	UPROPERTY() bool bSetBlendMode = false;
	UPROPERTY() FString BlendMode;
	UPROPERTY() bool bSetPriorityOrder = false;
	UPROPERTY() int32 PriorityOrder = 1;
	UPROPERTY() bool bSetDisabled = false;
	UPROPERTY() bool bDisabled = false;
	UPROPERTY() bool bSetAutomaticRule = false;
	UPROPERTY() bool bAutomaticRule = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
