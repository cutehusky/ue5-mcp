#pragma once

#include "CoreMinimal.h"
#include "TextureImportReq.generated.h"

USTRUCT()
struct FTextureImportReq
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
