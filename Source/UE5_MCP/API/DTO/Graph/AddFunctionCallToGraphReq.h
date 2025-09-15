#pragma once

#include "CoreMinimal.h"
#include "GraphOperationReq.h"
#include "AddFunctionCallToGraphReq.generated.h"

USTRUCT()
struct FAddFunctionCallToGraphReq: public FGraphOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString FunctionName;

	UPROPERTY()
	FString ClassToCall = "";
};
