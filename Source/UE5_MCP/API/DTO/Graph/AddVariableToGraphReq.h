#pragma once
#include "CoreMinimal.h"
#include "GraphOperationReq.h"
#include "AddVariableToGraphReq.generated.h"

USTRUCT()
struct FAddVariableToGraphReq: public FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString VarName;

	UPROPERTY()
	bool bIsSetter = false;
};
