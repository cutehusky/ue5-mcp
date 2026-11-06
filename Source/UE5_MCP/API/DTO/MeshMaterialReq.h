#pragma once

#include "CoreMinimal.h"
#include "MeshMaterialReq.generated.h"

USTRUCT()
struct FMeshMaterialReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	int32 SlotIndex = 0;

	UPROPERTY()
	FString MaterialPath;
};
