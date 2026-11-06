#pragma once

#include "CoreMinimal.h"
#include "InputMappingReq.generated.h"

USTRUCT()
struct FInputMappingReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString ActionPath;

	UPROPERTY()
	FString Key;

	UPROPERTY()
	FString NewKey;
};
