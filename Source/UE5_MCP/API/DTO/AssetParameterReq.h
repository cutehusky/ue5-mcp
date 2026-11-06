#pragma once

#include "CoreMinimal.h"
#include "AssetParameterReq.generated.h"

USTRUCT()
struct FAssetParameterReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString ParameterName;

	UPROPERTY()
	FString ParameterType;

	UPROPERTY()
	FString Value;
};
