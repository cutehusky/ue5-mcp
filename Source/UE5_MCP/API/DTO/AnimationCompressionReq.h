#pragma once

#include "CoreMinimal.h"
#include "AnimationCompressionReq.generated.h"

USTRUCT()
struct FAnimationCompressionReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString BoneSettingsPath;
	UPROPERTY() FString CurveSettingsPath;
	UPROPERTY() FString VariableFrameStrippingPath;
	UPROPERTY() bool bSetAllowFrameStripping = false;
	UPROPERTY() bool bAllowFrameStripping = false;
	UPROPERTY() bool bSetErrorThresholdScale = false;
	UPROPERTY() float ErrorThresholdScale = 1.0f;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
