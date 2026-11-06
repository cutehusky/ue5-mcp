#pragma once

#include "CoreMinimal.h"
#include "AssetActionReq.generated.h"

USTRUCT()
struct FAssetActionReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString DestinationPath;

	UPROPERTY()
	FString DirectoryPath;

	UPROPERTY()
	bool bRecursive = true;
};
