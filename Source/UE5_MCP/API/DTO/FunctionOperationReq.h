#pragma once
#include "CoreMinimal.h"
#include "FunctionOperationReq.generated.h"

USTRUCT()
struct FFunctionOperationReq
{
	GENERATED_BODY()
	
public:
	UPROPERTY()
	FString BpPath;

	UPROPERTY()
	FString FunctionName;

	UPROPERTY()
	FString FunctionInputSignature; // used for AddFunctionGraph and EditFunctionGraph

	UPROPERTY()
	FString FunctionOutputSignature; // used for AddFunctionGraph and EditFunctionGraph
};
