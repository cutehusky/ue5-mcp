#pragma once
#include "CoreMinimal.h"
#include "DecalReq.generated.h"
USTRUCT()
struct FDecalReq { GENERATED_BODY()
 UPROPERTY() FString WorldPath;
 UPROPERTY() FString Name;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString ActorGuid;
 UPROPERTY() FString ExpectedLabel;
 UPROPERTY() bool bFilterMaterial=false;
 UPROPERTY() FString MaterialPath;
 UPROPERTY() FString ExpectedMaterialPath;
 UPROPERTY() FVector Size=FVector::OneVector;
 UPROPERTY() FVector ExpectedSize=FVector::OneVector;
 UPROPERTY() TArray<double> Color;
 UPROPERTY() TArray<double> ExpectedColor;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() bool bReceivesDecals=true;
 UPROPERTY() bool bExpectedReceivesDecals=true;
 UPROPERTY() bool bVisible=true;
 UPROPERTY() bool bExpectedVisible=true;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() TArray<FString> ExpectedHierarchyPaths;
 UPROPERTY() TArray<FString> ExpectedHierarchyParents;
 UPROPERTY() TArray<int32> ExpectedHierarchyMobilities;
 UPROPERTY() bool bRequireHierarchySnapshot=false;
 UPROPERTY() int32 ExpectedChildCount=-1;
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=true;
};
