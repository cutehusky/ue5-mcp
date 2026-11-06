#pragma once

#include "CoreMinimal.h"
#include "AssetPropertyReq.generated.h"

USTRUCT()
struct FAssetPropertyReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString AssetClass;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	TMap<FString, FString> Properties;
};
