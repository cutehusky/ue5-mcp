#pragma once
#include "CoreMinimal.h"
#include "NavigationAreaReq.generated.h"
USTRUCT()
struct FNavigationAreaReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation=TEXT("update");
	/** -1 preserves the existing value. */
	UPROPERTY() float DefaultCost=-1;
	UPROPERTY() float EnteringCost=-1;
	/** Empty preserves color; otherwise exactly four RGBA bytes. */
	UPROPERTY() TArray<int32> DrawColor;
	UPROPERTY() bool bSetSupportedAgents=false;
	UPROPERTY() TArray<int32> SupportedAgentIndices;
	UPROPERTY() bool bDryRun=false;
	UPROPERTY() bool bSave=false;
};
