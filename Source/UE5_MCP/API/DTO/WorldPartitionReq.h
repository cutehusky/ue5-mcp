#pragma once
#include "CoreMinimal.h"
#include "WorldPartition/WorldPartitionStreamingSource.h"
#include "WorldPartitionReq.generated.h"
USTRUCT()
struct FPartitionActorPinEntry { GENERATED_BODY()
 UPROPERTY() FString ContainerPath;
 UPROPERTY() FString ActorGuid;
 UPROPERTY() FString ActorPath;
 UPROPERTY() bool bExpectedPinned=false;
 UPROPERTY() bool bExpectedLoaded=false;
};
USTRUCT()
struct FWorldPartitionReq { GENERATED_BODY()
 UPROPERTY() double GridLoadingRange=25600;
 UPROPERTY() bool bProjectIn2D=false;
 UPROPERTY() TArray<FStreamingSourceShape> SourceShapes;
 UPROPERTY() TArray<FStreamingSourceShape> ExpectedSourceShapes;
 UPROPERTY() TArray<FPartitionActorPinEntry> PinEntries;
 UPROPERTY() TArray<FString> DefinitionPaths;
 UPROPERTY() TArray<FString> ExpectedDefinitionPaths;
 UPROPERTY() TArray<FString> GridNames;
 UPROPERTY() TArray<FString> ExpectedGridNames;
 UPROPERTY() TArray<int32> ExpectedSetupIndices;
 UPROPERTY() TArray<FString> SetupPaths;
 UPROPERTY() TArray<FString> ExpectedSetupPaths;
 UPROPERTY() TArray<FString> HLODLayerPaths;
 UPROPERTY() TArray<FString> ExpectedHLODLayerPaths;
 UPROPERTY() TArray<int32> ColorBytes;
 UPROPERTY() TArray<int32> ExpectedColorBytes;
 UPROPERTY() TArray<FString> DataLayerPaths;
 UPROPERTY() TArray<FString> ExpectedDataLayerPaths;
 UPROPERTY() int32 ItemIndex=-1;
 UPROPERTY() int32 ExpectedHLODIndex=-2;
 UPROPERTY() int32 ExpectedChildCount=-1;
 UPROPERTY() int32 ExpectedLoadedActorCount=-1;
 UPROPERTY() FString PartitionPath;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString ObjectPath;
 UPROPERTY() FString ExpectedObjectPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() double Value=0;
 UPROPERTY() double ExpectedValue=0;
 UPROPERTY() FString ClassPath;
 UPROPERTY() FString ExpectedClassPath;
 UPROPERTY() int32 LayerType=-1;
 UPROPERTY() int32 ExpectedLayerType=-1;
 UPROPERTY() FString ExpectedBuilderSettingsPath;
 UPROPERTY() FString ParentLayerPath;
 UPROPERTY() FString LinkedLayerPath;
 UPROPERTY() FString ExpectedAssetPath;
 UPROPERTY() FString Name;
 UPROPERTY() FString ExpectedName;
 UPROPERTY() bool bExpectedValue=false;
 UPROPERTY() bool bValue=false;
 UPROPERTY() FString ContainerPath;
 UPROPERTY() FString ActorGuid;
 UPROPERTY() bool bEditorOnlyReferences=false;
 UPROPERTY() FString AdapterPath;
 UPROPERTY() FString Label;
 UPROPERTY() FVector ExpectedExtent=FVector::ZeroVector;
 UPROPERTY() FVector ExpectedCenter=FVector::ZeroVector;
 UPROPERTY() TArray<double> ColorValues;
 UPROPERTY() TArray<double> ExpectedColorValues;
 UPROPERTY() FVector Center=FVector::ZeroVector;
 UPROPERTY() FVector Extent=FVector(1000);
 UPROPERTY() int32 ExpectedRegistryCount=-1;
 UPROPERTY() bool bExpectedLoaded=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bRecursive=false;
 UPROPERTY() int32 MaxDepth=4;
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
};
