#pragma once
#include "CoreMinimal.h"
#include "NavigationFilterReq.generated.h"

USTRUCT()
struct FNavigationAreaOverrideReq
{
	GENERATED_BODY()
	UPROPERTY() FString AreaClass;
	UPROPERTY() bool bExcluded = false;
	UPROPERTY() bool bOverrideTravelCost = false;
	UPROPERTY() float TravelCost = 1.f;
	UPROPERTY() bool bOverrideEnteringCost = false;
	UPROPERTY() float EnteringCost = 0.f;
};

USTRUCT()
struct FNavigationFilterReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation = TEXT("update");
	UPROPERTY() bool bSetAreas = false;
	UPROPERTY() TArray<FNavigationAreaOverrideReq> Areas;
	/** -1 preserves the current 16-bit flag mask. */
	UPROPERTY() int32 IncludeFlags = -1;
	UPROPERTY() int32 ExcludeFlags = -1;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
