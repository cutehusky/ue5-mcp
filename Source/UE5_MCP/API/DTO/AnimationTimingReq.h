#pragma once

#include "CoreMinimal.h"
#include "AnimationTimingReq.generated.h"

USTRUCT()
struct FAnimationTimingReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() int32 FrameRateNumerator = 30;
	UPROPERTY() int32 FrameRateDenominator = 1;
	UPROPERTY() int32 SourceFrames = INDEX_NONE;
	UPROPERTY() bool bConfirmTrim = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
