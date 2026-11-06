#pragma once
#include "CoreMinimal.h"
#include "FoliageReq.generated.h"
USTRUCT()
struct FFoliageReq { GENERATED_BODY()
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString ExpectedProceduralGuid;
 UPROPERTY() TArray<FString> Names;
 UPROPERTY() TArray<FString> ExpectedNames;
 UPROPERTY() TArray<FString> AssetPaths;
 UPROPERTY() TArray<FString> ExpectedAssetPaths;
 UPROPERTY() int32 SlotIndex=-1;
 UPROPERTY() int32 ExpectedSlotCount=-1;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString ExpectedAssetPath;
 UPROPERTY() FVector2D Range=FVector2D::ZeroVector;
 UPROPERTY() FVector2D ExpectedRange=FVector2D::ZeroVector;
 UPROPERTY() int32 ExpectedTypeCount=-1;
 UPROPERTY() int32 InstanceIndex=-1;
 UPROPERTY() int32 ExpectedInstanceCount=-1;
 UPROPERTY() int32 ExpectedBaseId=-1;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() FString TypePath;
 UPROPERTY() FString ExpectedUpdateGuid;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() bool bValue=false;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
};
