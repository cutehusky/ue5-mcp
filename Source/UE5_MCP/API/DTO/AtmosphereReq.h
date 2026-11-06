#pragma once
#include "CoreMinimal.h"
#include "AtmosphereReq.generated.h"
USTRUCT()
struct FAtmosphereReq { GENERATED_BODY()
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() int32 ExpectedMode=-1;
 UPROPERTY() FString Name;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() bool bValue=false;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() TArray<double> Color;
 UPROPERTY() TArray<double> ExpectedColor;
 UPROPERTY() FVector Tent=FVector::ZeroVector;
 UPROPERTY() FVector ExpectedTent=FVector::ZeroVector;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
};
