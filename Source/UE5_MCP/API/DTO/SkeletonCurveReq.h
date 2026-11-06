#pragma once
#include "CoreMinimal.h"
#include "SkeletonCurveReq.generated.h"
USTRUCT()
struct FSkeletonCurveReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString Name;
 UPROPERTY() FString NewName;
 UPROPERTY() FString Operation=TEXT("create");
 UPROPERTY() bool bMaterial=false;
 UPROPERTY() bool bMorphTarget=false;
 UPROPERTY() TArray<FString> LinkedBones;
 UPROPERTY() int32 MaxLOD=255;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
