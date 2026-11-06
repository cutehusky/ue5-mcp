#pragma once
#include "CoreMinimal.h"
#include "LandscapeReq.generated.h"
USTRUCT()
struct FLandscapeReq { GENERATED_BODY()
 UPROPERTY() FString ActorPath;
 UPROPERTY() TArray<double> Color;
 UPROPERTY() TArray<double> ExpectedColor;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString ExpectedAssetPath;
 UPROPERTY() int32 BlendMethod=-1;
 UPROPERTY() int32 ExpectedBlendMethod=-1;
 UPROPERTY() FString BlendGroup;
 UPROPERTY() FString ExpectedBlendGroup;
 UPROPERTY() TArray<int32> Weights;
 UPROPERTY() TArray<int32> ExpectedWeights;
 UPROPERTY() TArray<int32> Heights;
 UPROPERTY() TArray<int32> ExpectedHeights;
 UPROPERTY() TArray<FString> ExpectedLayerOrder;
 UPROPERTY() int32 DestinationIndex=-1;
 UPROPERTY() FString Name;
 UPROPERTY() FString ExpectedName;
 UPROPERTY() FString EditLayerGuid;
 UPROPERTY() FString EditLayerPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() bool bValue=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() FString LayerInfoPath;
 UPROPERTY() int32 X=0;
 UPROPERTY() int32 Y=0;
 UPROPERTY() int32 Width=1;
 UPROPERTY() int32 Height=1;
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
};
