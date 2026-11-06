#pragma once

#include "CoreMinimal.h"
#include "MaterialCoreSettingsReq.generated.h"

USTRUCT()
struct FMaterialCoreSettingsReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Domain;
	UPROPERTY() FString BlendMode;
	UPROPERTY() FString ShadingModel;
	UPROPERTY() bool bSetTwoSided = false;
	UPROPERTY() bool bTwoSided = false;
	UPROPERTY() TMap<FString, bool> UsageFlags;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
