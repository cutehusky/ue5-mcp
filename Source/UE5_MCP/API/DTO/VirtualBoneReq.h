#pragma once
#include "CoreMinimal.h"
#include "VirtualBoneReq.generated.h"
USTRUCT()
struct FVirtualBoneReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString SourceBone;
 UPROPERTY() FString TargetBone;
 UPROPERTY() FString Name;
 UPROPERTY() FString NewName;
 UPROPERTY() TArray<FString> Names;
 UPROPERTY() bool bCascade=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
