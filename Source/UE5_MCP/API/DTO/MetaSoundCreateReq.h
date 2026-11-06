#pragma once

#include "CoreMinimal.h"
#include "MetaSoundCreateReq.generated.h"

USTRUCT()
struct FMetaSoundCreateReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString AssetType = TEXT("source");
	UPROPERTY() FString ParentAssetPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
