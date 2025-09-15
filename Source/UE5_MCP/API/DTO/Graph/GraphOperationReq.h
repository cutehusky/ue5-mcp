#pragma once
#include "CoreMinimal.h"
#include "GraphOperationReq.generated.h"

USTRUCT()
struct FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;

	UPROPERTY()
	FString GraphName = "EventGraph";
};
