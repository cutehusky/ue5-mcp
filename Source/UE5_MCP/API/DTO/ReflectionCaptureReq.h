#pragma once
#include "CoreMinimal.h"
#include "ReflectionCaptureReq.generated.h"
USTRUCT()
struct FReflectionCaptureReq { GENERATED_BODY()
 UPROPERTY() TArray<FString> ShowFlagNames;
 UPROPERTY() TArray<bool> ShowFlagValues;
 UPROPERTY() TArray<FString> ExpectedShowFlagNames;
 UPROPERTY() TArray<bool> ExpectedShowFlagValues;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString ActorGuid;
 UPROPERTY() FString ExpectedLabel;
 UPROPERTY() TArray<FString> ComponentPaths;
 UPROPERTY() TArray<FString> ExpectedComponentPaths;
 UPROPERTY() TArray<FString> ActorPaths;
 UPROPERTY() TArray<FString> ExpectedActorPaths;
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() FString Name;
 UPROPERTY() FString Shape;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FVector Offset=FVector::ZeroVector;
 UPROPERTY() FVector ExpectedOffset=FVector::ZeroVector;
 UPROPERTY() FString SourceType;
 UPROPERTY() int32 ExpectedSourceType=-1;
 UPROPERTY() FString CubemapPath;
 UPROPERTY() FString ExpectedCubemapPath;
 UPROPERTY() FString ExpectedBuildDataId;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() FString FieldName;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() double Value=0;
 UPROPERTY() bool bVisible=true;
 UPROPERTY() bool bExpectedVisible=true;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
};
