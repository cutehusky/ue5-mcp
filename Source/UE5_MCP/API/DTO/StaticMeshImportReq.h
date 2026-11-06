#pragma once

#include "CoreMinimal.h"
#include "StaticMeshImportReq.generated.h"

USTRUCT()
struct FStaticMeshImportReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString SourceFilePath;
	UPROPERTY() FString DestinationPath;
	UPROPERTY() FString AssetName;
	UPROPERTY() bool bReplaceExisting = false;
	UPROPERTY() bool bConfirmReplace = false;
	UPROPERTY() bool bConfirmReimport = false;
	UPROPERTY() bool bConfirmSourceChange = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
