#pragma once
#include "CoreMinimal.h"
#include "PoseSearchReq.generated.h"
USTRUCT()
struct FPoseSearchTrajectorySampleReq
{
 GENERATED_BODY()
 UPROPERTY() float Offset=0;
 UPROPERTY() int32 Flags=2;
 UPROPERTY() float Weight=1;
 UPROPERTY() FString NormalizationGroup;
 UPROPERTY() FLinearColor DebugColor=FLinearColor::Blue;
};
USTRUCT()
struct FPoseSearchBoneReq
{
 GENERATED_BODY()
 UPROPERTY() FString Bone;
 UPROPERTY() int32 Flags=2;
 UPROPERTY() float Weight=1;
 UPROPERTY() FLinearColor DebugColor=FLinearColor::Green;
 UPROPERTY() FString NormalizationGroup;
};
USTRUCT()
struct FPoseSearchReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString AssetKind;
 UPROPERTY() FString IndexRequest;
 UPROPERTY() FString SourceAssetPath;
 UPROPERTY() FString SchemaPath;
 UPROPERTY() FString NormalizationSetPath;
 UPROPERTY() TArray<FString> DatabasePaths;
 UPROPERTY() TArray<FString> Tags;
 UPROPERTY() FString AnimationPath;
 UPROPERTY() int32 AnimationIndex=-1;
 UPROPERTY() FString SkeletonPath;
 UPROPERTY() FString MirrorTablePath;
 UPROPERTY() FString MirrorPolicy;
 UPROPERTY() FString Role;
 UPROPERTY() FString ChannelClass;
 UPROPERTY() FString ChannelPath;
 UPROPERTY() FString FieldName;
 UPROPERTY() FString NameValue;
 UPROPERTY() FString SearchMode;
 UPROPERTY() FString Preprocessor;
 UPROPERTY() double ScalarValue=0;
 UPROPERTY() TArray<float> SampleTimes;
 UPROPERTY() FVector VectorValue=FVector::ZeroVector;
 UPROPERTY() FLinearColor ColorValue=FLinearColor::White;
 UPROPERTY() TArray<FPoseSearchBoneReq> SampledBones;
 UPROPERTY() TArray<FPoseSearchTrajectorySampleReq> TrajectorySamples;
 UPROPERTY() FTransform Origin=FTransform::Identity;
 UPROPERTY() TArray<FTransform> ActorRootTransforms;
 UPROPERTY() TArray<FString> ExpectedRoles;
 UPROPERTY() TArray<FString> RelevantRoles;
 UPROPERTY() TArray<FString> MirrorTablePaths;
 UPROPERTY() int32 ChannelIndex=-1;
 UPROPERTY() TArray<int32> ChildIndices;
 UPROPERTY() int32 TargetIndex=-1;
 UPROPERTY() float RangeStart=0;
 UPROPERTY() float RangeEnd=0;
 UPROPERTY() bool bSingleSample=false;
 UPROPERTY() bool bGridSampling=false;
 UPROPERTY() int32 HorizontalSamples=9;
 UPROPERTY() int32 VerticalSamples=2;
 UPROPERTY() float BlendX=0;
 UPROPERTY() float BlendY=0;
 UPROPERTY() int32 SampleRate=30;
 UPROPERTY() bool bEnforceCompressedSampling=true;
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bDisableReselection=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
