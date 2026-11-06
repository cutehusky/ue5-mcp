#pragma once

#include "CoreMinimal.h"
#include "AssetPropertyReq.h"
#include "AssetBatchReq.generated.h"

/** Ordered generic-asset operations, with legacy single-operation fields retained. */
USTRUCT()
struct FAssetBatchReq
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<FAssetPropertyReq> Operations;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;

	UPROPERTY()
	bool bStopOnError = false;

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString AssetClass;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	TMap<FString, FString> Properties;
};
