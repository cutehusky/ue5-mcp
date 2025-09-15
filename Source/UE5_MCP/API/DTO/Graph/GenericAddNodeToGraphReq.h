#pragma once
#include "CoreMinimal.h"
#include "GraphOperationReq.h"
#include "GenericAddNodeToGraphReq.generated.h"

USTRUCT()
struct FGenericAddNodeToGraphReq: public FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString NodeTypeName;

	UPROPERTY()
	FString ExtraInfo; // e.g. StructTypeName for Make/Break Struct nodes, PinTypeName for Switch Enum nodes, etc.
};
