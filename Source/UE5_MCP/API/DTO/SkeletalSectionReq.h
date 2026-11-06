#pragma once

#include "CoreMinimal.h"
#include "SkeletalSectionReq.generated.h"

USTRUCT()
struct FSkeletalSectionReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	int32 LODIndex = 0;

	UPROPERTY()
	int32 SectionIndex = 0;

	UPROPERTY()
	FString Property;

	UPROPERTY()
	bool bValue = false;
};
