#pragma once

#include "CoreMinimal.h"
#include "MaterialInstanceReq.generated.h"

USTRUCT()
struct FMaterialInstanceReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString ParentPath;
	UPROPERTY() FString ParameterName;
	UPROPERTY() FString ParameterType;
	UPROPERTY() FString Association = TEXT("global");
	UPROPERTY() int32 Index = INDEX_NONE;
	UPROPERTY() FString Value;
	UPROPERTY() int32 FontPage = 0;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
