#pragma once
#include "CoreMinimal.h"
#include "GraphOperationReq.h"
#include "PinOperationReq.generated.h"

USTRUCT()
struct FPinOperationReq: public FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FGuid OutputNodeId;

	UPROPERTY()
	FString OutputPinName;

	UPROPERTY()
	FGuid InputNodeId;

	UPROPERTY()
	FString InputPinName;
};
