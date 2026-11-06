#pragma once
#include "CoreMinimal.h"
#include "BpDTO.generated.h"


USTRUCT()
struct FBPOperationRequest
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;
};

USTRUCT()
struct FCreateBPRequest: public FBPOperationRequest
{
	GENERATED_BODY()

	UPROPERTY()
	FString ParentClass;
};

USTRUCT()
struct FCreateBPResponse
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;
};
