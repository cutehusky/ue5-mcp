#pragma once
#include "CoreMinimal.h"
#include "LightingReq.generated.h"
USTRUCT()
struct FLightingReq { GENERATED_BODY()
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() FString ExpectedSettingsText;
 UPROPERTY() FString ActorGuid;
 UPROPERTY() FString ExpectedLabel;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString ExpectedClassPath;
 UPROPERTY() FString Name;
 UPROPERTY() FString LightType;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString SourceType;
 UPROPERTY() int32 ExpectedSourceType=-1;
 UPROPERTY() FString CubemapPath;
 UPROPERTY() FString ExpectedCubemapPath;
 UPROPERTY() FTransform Transform=FTransform::Identity;
 UPROPERTY() FTransform ExpectedTransform=FTransform::Identity;
 UPROPERTY() FString Mobility;
 UPROPERTY() int32 ExpectedMobility=-1;
 UPROPERTY() FString Units;
 UPROPERTY() int32 ExpectedUnits=-1;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString ExpectedAssetPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() double Value=0;
 UPROPERTY() bool bValue=false;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() TArray<double> LinearColor;
 UPROPERTY() TArray<double> ExpectedLinearColor;
 UPROPERTY() TArray<int32> Color;
 UPROPERTY() TArray<int32> ExpectedColor;
 UPROPERTY() TArray<int32> Channels;
 UPROPERTY() TArray<int32> ExpectedChannels;
 UPROPERTY() FVector Direction=FVector::ZeroVector;
 UPROPERTY() FVector ExpectedDirection=FVector::ZeroVector;
 UPROPERTY() FVector Scale=FVector::OneVector;
 UPROPERTY() FVector ExpectedScale=FVector::OneVector;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
};
