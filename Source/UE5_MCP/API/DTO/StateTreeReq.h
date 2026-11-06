#pragma once
#include "CoreMinimal.h"
#include "StateTreeReq.generated.h"
USTRUCT()
struct FStateTreeCurveKeyReq
{
 GENERATED_BODY()
 UPROPERTY() float Time=0;
 UPROPERTY() float Value=0;
 UPROPERTY() FString Interpolation=TEXT("Linear");
 UPROPERTY() float ArriveTangent=0;
 UPROPERTY() float LeaveTangent=0;
};
USTRUCT()
struct FStateTreeBindingReq
{
 GENERATED_BODY()
 UPROPERTY() FString SourceId;
 UPROPERTY() FString SourcePath;
 UPROPERTY() FString TargetId;
 UPROPERTY() FString TargetPath;
 UPROPERTY() bool bOutput=false;
};
USTRUCT()
struct FStateTreeFunctionBindingReq
{
 GENERATED_BODY()
 UPROPERTY() FString StructPath;
 UPROPERTY() FString OutputPath;
 UPROPERTY() FString TargetId;
 UPROPERTY() FString TargetPath;
 UPROPERTY() TMap<FString,FString> Properties;
 UPROPERTY() TMap<FString,FString> InstanceProperties;
 UPROPERTY() TMap<FString,FString> InstanceReferences;
 UPROPERTY() TMap<FString,FString> InstanceContainers;
 UPROPERTY() bool bSetResponseCurve=false;
 UPROPERTY() FString ResponseCurveAsset;
 UPROPERTY() TArray<FStateTreeCurveKeyReq> ResponseCurveKeys;
 UPROPERTY() bool bSetEnumScores=false;
 UPROPERTY() FString ScoreEnumPath;
 UPROPERTY() TMap<FString,float> EnumScores;
 UPROPERTY() TArray<FStateTreeBindingReq> Inputs;
};
USTRUCT()
struct FStateTreeReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString Operation;
 UPROPERTY() FString Reason;
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() FString SchemaPath=TEXT("/Script/GameplayStateTreeModule.StateTreeComponentSchema");
 UPROPERTY() FString StateId;
 UPROPERTY() FString ParentId;
 UPROPERTY() FString ItemId;
 UPROPERTY() FString TransitionId;
 UPROPERTY() FString Name;
 UPROPERTY() bool bSetName=false;
 UPROPERTY() bool bSetTaskEnabled=false;
 UPROPERTY() bool bSetTaskCompletion=false;
 UPROPERTY() bool bConsideredForCompletion=true;
 UPROPERTY() bool bSetConditionEvaluation=false;
 UPROPERTY() FString ConditionEvaluation=TEXT("Evaluated");
 UPROPERTY() FString StateType=TEXT("State");
 UPROPERTY() FString Kind=TEXT("task");
 UPROPERTY() FString StructPath;
 UPROPERTY() FString NodeClassPath;
 UPROPERTY() FString ParameterType=TEXT("Float");
 UPROPERTY() FString ContainerType;
 UPROPERTY() FString TypePath;
 UPROPERTY() FString Value;
 UPROPERTY() bool bSetValue=false;
 UPROPERTY() FStateTreeBindingReq Binding;
 UPROPERTY() TArray<FStateTreeBindingReq> Bindings;
 UPROPERTY() TArray<FStateTreeFunctionBindingReq> Functions;
 UPROPERTY() TMap<FString,FString> Properties;
 UPROPERTY() TMap<FString,FString> ContextClasses;
 UPROPERTY() TMap<FString,FString> SchemaReferences;
 UPROPERTY() TMap<FString,FString> SchemaContainers;
 UPROPERTY() TMap<FString,FString> InstanceProperties;
 UPROPERTY() TMap<FString,FString> InstanceReferences;
 UPROPERTY() TMap<FString,FString> InstanceContainers;
 UPROPERTY() bool bSetResponseCurve=false;
 UPROPERTY() FString ResponseCurveAsset;
 UPROPERTY() TArray<FStateTreeCurveKeyReq> ResponseCurveKeys;
 UPROPERTY() bool bSetEnumScores=false;
 UPROPERTY() FString ScoreEnumPath;
 UPROPERTY() TMap<FString,float> EnumScores;
 UPROPERTY() int32 Index=-1;
 UPROPERTY() FString Trigger=TEXT("OnStateCompleted");
 UPROPERTY() FString TargetType=TEXT("Succeeded");
 UPROPERTY() FString TargetStateId;
 UPROPERTY() FString LinkedAssetPath;
 UPROPERTY() FString EventTag;
 UPROPERTY() FString PayloadStructPath;
 UPROPERTY() bool bConsumeEvent=true;
 UPROPERTY() bool bSetRequiredEvent=false;
 UPROPERTY() FString Priority=TEXT("Normal");
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bDelay=false;
 UPROPERTY() float Delay=0;
 UPROPERTY() float RandomDelay=0;
 UPROPERTY() bool bSetExpression=false;
 UPROPERTY() int32 ExpressionIndent=0;
 UPROPERTY() FString Operand=TEXT("And");
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
