#pragma once
#include "CoreMinimal.h"
#include "IKRigReq.generated.h"
USTRUCT()
struct FIKGoalOverrideReq
{
 GENERATED_BODY()
 UPROPERTY() FString Name;
 UPROPERTY() FString SourceBone;
 UPROPERTY() FString PositionSpace;
 UPROPERTY() FString RotationSpace;
 UPROPERTY() FVector Position=FVector::ZeroVector;
 UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY() float PositionAlpha=1;
 UPROPERTY() float RotationAlpha=1;
 UPROPERTY() bool bAdditive=false;
 UPROPERTY() bool bWorldSpace=false;
};
USTRUCT()
struct FIKRigReq
{
 GENERATED_BODY()
 UPROPERTY() TArray<FIKGoalOverrideReq> GoalOverrides;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString SourceAssetPath;
 UPROPERTY() TArray<FString> AnimationPaths;
 UPROPERTY() FString OutputFolder;
 UPROPERTY() bool bExportOnlyAnimatedBones=true;
 UPROPERTY() bool bRetainAdditiveFlags=true;
 UPROPERTY() FString OutputSearch;
 UPROPERTY() FString OutputReplace;
 UPROPERTY() FString OutputPrefix;
 UPROPERTY() FString OutputSuffix=TEXT("_Retargeted");
 UPROPERTY() TArray<FString> DisabledEvaluationOps;
 UPROPERTY() TArray<FString> SourceBones;
 UPROPERTY() TArray<FTransform> SourceLocalTransforms;
 UPROPERTY() FString SourcePoseOverride;
 UPROPERTY() FString TargetPoseOverride;
 UPROPERTY() bool bForceAllIKOff=false;
 UPROPERTY() bool bOverrideForceAllIKOff=false;
 UPROPERTY() int32 EvaluationLOD=-1;
 UPROPERTY() FTransform WorldToComponent=FTransform::Identity;
 UPROPERTY() bool bLocalOutput=false;
 UPROPERTY() int32 WarmupFrames=0;
 UPROPERTY() float DeltaTime=0;
 UPROPERTY() FString SourceMeshPath;
 UPROPERTY() FString TargetMeshPath;
 UPROPERTY() FString MeshPath;
 UPROPERTY() FString RigPath;
 UPROPERTY() FString PoseName;
 UPROPERTY() FString Side=TEXT("source");
 UPROPERTY() FString ChainName;
 UPROPERTY() FString SourceChain;
 UPROPERTY() FString NewName;
 UPROPERTY() FString Operation=TEXT("rename");
 UPROPERTY() FString StartBone;
 UPROPERTY() FString EndBone;
 UPROPERTY() FString GoalName;
 UPROPERTY() FString BoneName;
 UPROPERTY() TArray<FString> Bones;
 UPROPERTY() FString RootBone;
 UPROPERTY() FString SolverType;
 UPROPERTY() FString ExpectedName;
 UPROPERTY() FString SourceName;
 UPROPERTY() FString ParentName;
 UPROPERTY() int32 SolverIndex=-1;
 UPROPERTY() int32 TargetIndex=-1;
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bExcluded=true;
 UPROPERTY() bool bCascade=false;
 UPROPERTY() bool bForceRemap=false;
 UPROPERTY() FVector Translation=FVector::ZeroVector;
 UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY() FVector Scale=FVector::OneVector;
 UPROPERTY() FString FieldName;
 UPROPERTY() double ScalarValue=0;
 UPROPERTY() FString ValueKind=TEXT("scalar");
 UPROPERTY() FString TextValue;
 UPROPERTY() TArray<FString> NameValues;
 UPROPERTY() TArray<double> NumberValues;
 UPROPERTY() TArray<FString> SourceCurves;
 UPROPERTY() TArray<FString> TargetCurves;
 UPROPERTY() bool bCopyAllCurves=true;
 UPROPERTY() bool bRemapCurves=true;
 UPROPERTY() FVector VectorValue=FVector::ZeroVector;
 UPROPERTY() FRotator RotatorValue=FRotator::ZeroRotator;
 UPROPERTY() FQuat QuaternionValue=FQuat::Identity;
 UPROPERTY() FTransform TransformValue=FTransform::Identity;
 UPROPERTY() float PositionAlpha=1;
 UPROPERTY() float RotationAlpha=1;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
