#pragma once

#include "CoreMinimal.h"
#include "AnimationSectionReq.generated.h"

USTRUCT()
struct FAnimationSectionReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString SectionName;

	UPROPERTY()
	FString NextSectionName;

	UPROPERTY()
	float StartTime = 0.0f;

	UPROPERTY()
	bool bDelete = false;
};
