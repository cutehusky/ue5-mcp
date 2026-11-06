#pragma once

#include "CoreMinimal.h"
#include "MaterialExpressionReq.generated.h"

USTRUCT()
struct FMaterialExpressionReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString ExpressionClass;

	UPROPERTY()
	FString ExpressionName;

	UPROPERTY()
	FString FromExpression;

	UPROPERTY()
	FString ToExpression;

	UPROPERTY()
	FString FromOutput;

	UPROPERTY()
	FString ToInput;

	UPROPERTY()
	int32 NodePosX = 0;

	UPROPERTY()
	int32 NodePosY = 0;
};
