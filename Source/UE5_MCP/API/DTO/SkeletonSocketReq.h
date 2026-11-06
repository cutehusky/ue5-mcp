#pragma once
#include "CoreMinimal.h"
#include "SkeletonSocketReq.generated.h"
USTRUCT()
struct FSkeletonSocketReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString PreviewAssetPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString Space=TEXT("world");
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() FString Operation=TEXT("create");
 UPROPERTY() FString SocketName;
 UPROPERTY() FString NewName;
 UPROPERTY() FString BoneName;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY() FVector Scale=FVector::OneVector;
 UPROPERTY() bool bForceAlwaysAnimated=true;
 UPROPERTY() bool bRemoveLocal=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
