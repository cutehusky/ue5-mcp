#pragma once

#include "CoreMinimal.h"
#include "SourceControlReq.generated.h"

USTRUCT()
struct FSourceControlReq
{
	GENERATED_BODY()

	UPROPERTY() TArray<FString> AssetPaths;
	UPROPERTY() TArray<FString> FilePaths;
	UPROPERTY() FString Operation = TEXT("status");
	UPROPERTY() FString Description;
	UPROPERTY() bool bRefresh = true;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bConfirmDeleteAdded = false;
	UPROPERTY() int32 MaxHistory = 20;
	UPROPERTY() int32 HistoryOffset = 0;
};
