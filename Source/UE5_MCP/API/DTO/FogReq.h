#pragma once
#include "CoreMinimal.h"
#include "FogReq.generated.h"
USTRUCT()
struct FFogReq { GENERATED_BODY()
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString Name;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString CubemapPath;
 UPROPERTY() FString ExpectedCubemapPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() bool bValue=false;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() FVector SecondLayer=FVector::ZeroVector;
 UPROPERTY() FVector ExpectedSecondLayer=FVector::ZeroVector;
 UPROPERTY() TArray<double> Color;
 UPROPERTY() TArray<double> ExpectedColor;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
};
