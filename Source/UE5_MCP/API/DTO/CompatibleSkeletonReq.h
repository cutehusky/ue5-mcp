#pragma once
#include "CoreMinimal.h"
#include "CompatibleSkeletonReq.generated.h"
USTRUCT()
struct FCompatibleSkeletonReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString SourcePath;
 UPROPERTY() FString Operation=TEXT("add");
 UPROPERTY() bool bUseCompatibleRetargetModes=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
