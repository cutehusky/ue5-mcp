#pragma once
#include "CoreMinimal.h"
#include "GraphOperationReq.h"
#include "SetPinDefaultValueReq.generated.h"

USTRUCT()
struct FSetPinDefaultValueReq: public FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FGuid NodeId;

	UPROPERTY()
	FString PinName;

	UPROPERTY()
	FString DefaultValue;
};
