#pragma once
#include "CoreMinimal.h"
#include "NiagaraReq.generated.h"
USTRUCT()
struct FNiagaraDependencyReq
{
 GENERATED_BODY()
 UPROPERTY() FString Id;
 UPROPERTY() FString Order=TEXT("PreDependency");
 UPROPERTY() FString Constraint=TEXT("SameScript");
 UPROPERTY() FString RequiredVersion;
 UPROPERTY() int32 UsageMask=15;
 UPROPERTY() FString Description;
};
USTRUCT()
struct FNiagaraPreviewOverrideReq
{
 GENERATED_BODY()
 UPROPERTY() FString Name;
 UPROPERTY() FString Kind;
 UPROPERTY() double Scalar=0;
 UPROPERTY() FVector Vector=FVector::ZeroVector;
 UPROPERTY() FLinearColor Color=FLinearColor::White;
};
USTRUCT()
struct FNiagaraCVarConditionReq
{
 GENERATED_BODY()
 UPROPERTY() FString Name;
 UPROPERTY() FString PassResponse=TEXT("None");
 UPROPERTY() FString FailResponse=TEXT("Disable");
 UPROPERTY() bool BoolValue=true;
 UPROPERTY() bool UseMinInt=false;
 UPROPERTY() bool UseMaxInt=false;
 UPROPERTY() int32 MinInt=1;
 UPROPERTY() int32 MaxInt=1;
 UPROPERTY() bool UseMinFloat=false;
 UPROPERTY() bool UseMaxFloat=false;
 UPROPERTY() double MinFloat=1;
 UPROPERTY() double MaxFloat=1;
};
USTRUCT()
struct FNiagaraReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString HandlerClass;
 UPROPERTY() FNiagaraCVarConditionReq ConditionConfig;
 UPROPERTY() int32 ScalabilityIndex=-1;
 UPROPERTY() FString RecordHash;
 UPROPERTY() int32 SourceScalabilityIndex=-1;
 UPROPERTY() FString SourceRecordHash;
 UPROPERTY() FString RuleClass;
 UPROPERTY() int32 RuleIndex=-1;
 UPROPERTY() FString RulePath;
 UPROPERTY() TArray<FString> RuleSetPaths;
 UPROPERTY() TArray<FString> StringValues;
 UPROPERTY() FString SourceAssetPath;
 UPROPERTY() FString SourceVersionId;
 UPROPERTY() int32 EmitterIndex=-1;
 UPROPERTY() FString EmitterId;
 UPROPERTY() FString SourceEmitterId;
 UPROPERTY() FString VersionId;
 UPROPERTY() FString NodeId;
 UPROPERTY() FString PinId;
 UPROPERTY() FString TargetNodeId;
 UPROPERTY() FString TargetNodePath;
 UPROPERTY() FString TargetPinId;
 UPROPERTY() FString NodePath;
 UPROPERTY() int32 NodeX=0;
 UPROPERTY() int32 NodeY=0;
 UPROPERTY() int32 NodeWidth=400;
 UPROPERTY() int32 NodeHeight=200;
 UPROPERTY() int32 StateMin=0;
 UPROPERTY() int32 StateMax=0;
 UPROPERTY() int32 EventIndex=-1;
 UPROPERTY() FString ScriptPath;
 UPROPERTY() int32 StageIndex=-1;
 UPROPERTY() FString StagePath;
 UPROPERTY() int32 RendererIndex=-1;
 UPROPERTY() int32 TargetIndex=-1;
 UPROPERTY() int32 OutputIndex=-1;
 UPROPERTY() FString RendererPath;
 UPROPERTY() FString RendererClass;
 UPROPERTY() FString NewName;
 UPROPERTY() FString ParameterName;
 UPROPERTY() FString ValueKind;
 UPROPERTY() FString FieldName;
 UPROPERTY() FString TextValue;
 UPROPERTY() TArray<FString> DependencyIds;
 UPROPERTY() TArray<FNiagaraDependencyReq> RequiredDependencies;
 UPROPERTY() TArray<FString> UsageNames;
 UPROPERTY() double ScalarValue=0;
 UPROPERTY() FVector VectorValue=FVector::ZeroVector;
 UPROPERTY() FLinearColor ColorValue=FLinearColor::White;
 UPROPERTY() bool bExposeInput=true;
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bForce=false;
 UPROPERTY() int32 RandomSeed=0;
 UPROPERTY() FVector BoundsMin=FVector(-100);
 UPROPERTY() FVector BoundsMax=FVector(100);
 UPROPERTY() TArray<FNiagaraPreviewOverrideReq> PreviewOverrides;
 UPROPERTY() FTransform PreviewTransform=FTransform::Identity;
 UPROPERTY() int32 PreviewSeedOffset=0;
 UPROPERTY() int32 SimulationTicks=1;
 UPROPERTY() float WarmupTime=0;
 UPROPERTY() float WarmupDelta=1.f/15.f;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
