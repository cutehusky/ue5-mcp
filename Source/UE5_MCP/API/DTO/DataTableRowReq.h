#pragma once

#include "CoreMinimal.h"
#include "DataTableRowReq.generated.h"

USTRUCT()
struct FDataTableRowReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString RowName;

	UPROPERTY()
	FString RowJson;
};
