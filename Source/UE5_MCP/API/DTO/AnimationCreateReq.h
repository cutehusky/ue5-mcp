#pragma once

#include "CoreMinimal.h"
#include "AnimationCreateReq.generated.h"

USTRUCT()
struct FAnimationCreateReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString SkeletonPath;

	UPROPERTY()
	FString PreviewMeshPath;
};
