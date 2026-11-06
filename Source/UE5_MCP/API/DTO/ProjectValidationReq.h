#pragma once

#include "CoreMinimal.h"
#include "ProjectValidationReq.generated.h"

/** Request for Blueprint compilation, asset audits, and redirector fix-up. */
USTRUCT()
struct FProjectValidationReq
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<FString> AssetPaths;

	UPROPERTY()
	FString DirectoryPath = TEXT("/Game");

	UPROPERTY()
	bool bRecursive = true;

	UPROPERTY()
	bool bSave = false;

	UPROPERTY()
	bool bConfirm = false;
};
