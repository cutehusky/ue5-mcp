#pragma once

#include "CoreMinimal.h"
#include "StaticMeshSettingsReq.generated.h"

USTRUCT()
struct FStaticMeshSettingsReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Property;

	UPROPERTY()
	bool bValue = false;
};
