#pragma once
#include "CoreMinimal.h"
#include "GraphOperationReq.h"
#include "AddEventToGraphReq.generated.h"

USTRUCT()
struct FAddEventToGraphReq: public FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString EventName;

	UPROPERTY()
	FString EventSignature;

	UPROPERTY()
	bool bIsCustomEvent = false;
};
