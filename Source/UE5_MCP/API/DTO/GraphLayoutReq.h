#pragma once

#include "CoreMinimal.h"
#include "GraphLayoutReq.generated.h"

USTRUCT()
struct FGraphLayoutReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;

	UPROPERTY()
	FString GraphName;

	UPROPERTY()
	TArray<FString> NodeIds;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	int32 ColumnSpacing = 420;

	UPROPERTY()
	int32 RowSpacing = 220;
};
