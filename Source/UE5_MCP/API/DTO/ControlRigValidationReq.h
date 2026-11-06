#pragma once

#include "CoreMinimal.h"
#include "ControlRigValidationReq.generated.h"

USTRUCT()
struct FControlRigValidationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString GraphPath;

	UPROPERTY()
	bool bCompile = false;
};
