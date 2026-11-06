#pragma once

#include "CoreMinimal.h"
#include "AnimationAttributeReq.generated.h"

USTRUCT()
struct FAnimationAttributeReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString AttributeName;
	UPROPERTY() FString BoneName;
	UPROPERTY() FString AttributeType;
	UPROPERTY() float Time = 0.0f;
	UPROPERTY() FString Value;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
