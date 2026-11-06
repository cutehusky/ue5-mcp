#pragma once

#include "CoreMinimal.h"
#include "StaticMeshLodReq.generated.h"

USTRUCT()
struct FStaticMeshLodReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	TArray<float> ScreenSizes;

	UPROPERTY()
	FString LODGroup;
};
