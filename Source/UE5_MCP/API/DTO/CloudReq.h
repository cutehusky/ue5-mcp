#pragma once
#include "CoreMinimal.h"
#include "CloudReq.generated.h"
USTRUCT()
struct FCloudReq { GENERATED_BODY()
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() FString Name;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString MaterialPath;
 UPROPERTY() FString ExpectedMaterialPath;
 UPROPERTY() FString ExpectedResolvedMaterialPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() bool bValue=false;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() TArray<double> Color;
 UPROPERTY() TArray<double> ExpectedColor;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
};
