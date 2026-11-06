#pragma once

#include "CoreMinimal.h"
#include "DataAssetCreateReq.generated.h"

USTRUCT()
struct FDataAssetCreateReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString AssetClass;
};
