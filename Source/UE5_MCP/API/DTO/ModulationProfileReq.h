#pragma once
#include "CoreMinimal.h"
#include "ModulationProfileReq.generated.h"
USTRUCT()
struct FModulationProfileReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() int32 ProfileIndex = 0;
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
