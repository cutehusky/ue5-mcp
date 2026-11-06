#pragma once

#include "CoreMinimal.h"
#include "AnimationBlueprintGraphReq.generated.h"

USTRUCT()
struct FAnimationBlueprintGraphReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString GraphPath;
	UPROPERTY() int32 ColumnSpacing = 420;
	UPROPERTY() int32 RowSpacing = 220;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
