#pragma once

#include "CoreMinimal.h"
#include "PhysicsBodySettingsReq.generated.h"

USTRUCT()
struct FPhysicsBodySettingsReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString BoneName;

	UPROPERTY()
	TMap<FString, FString> Settings;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;
};
