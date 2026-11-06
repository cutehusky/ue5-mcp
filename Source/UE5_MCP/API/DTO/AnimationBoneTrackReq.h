#pragma once

#include "CoreMinimal.h"
#include "AnimationBoneTrackReq.generated.h"

USTRUCT()
struct FAnimationBoneTrackReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString BoneName;
	UPROPERTY() int32 FrameIndex = INDEX_NONE;
	UPROPERTY() FVector Translation = FVector::ZeroVector;
	UPROPERTY() FRotator Rotation = FRotator::ZeroRotator;
	UPROPERTY() FVector Scale = FVector::OneVector;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
