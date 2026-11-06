#pragma once

#include "Components/StateTreeComponentSchema.h"
#include "StateTreeTaskBase.h"
#include "StateTreePropertyFunctionBase.h"
#include "Materials/MaterialInterface.h"
#include "Blueprint/StateTreeTaskBlueprintBase.h"
#include "Blueprint/StateTreeConditionBlueprintBase.h"
#include "Blueprint/StateTreeEvaluatorBlueprintBase.h"
#include "Blueprint/StateTreeConsiderationBlueprintBase.h"
#include "StateTreeVerificationFixtures.generated.h"

/** Concrete component schema used to verify the native single-task adapter. */
UCLASS()
class UMCPVerificationSingleTaskSchema : public UStateTreeComponentSchema
{
 GENERATED_BODY()
public:
 virtual bool AllowMultipleTasks() const override { return false; }
};

USTRUCT()
struct FMCPVerificationContainerTaskInstanceData
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, Category=Input, meta=(Optional)) TArray<float> Samples;
 UPROPERTY(EditAnywhere, Category=Input, meta=(Optional)) TSet<int32> Codes;
 UPROPERTY(EditAnywhere, Category=Input, meta=(Optional)) TMap<FName,float> Scores;
 UPROPERTY(EditAnywhere, Category=Parameter) float Expected=0;
 UPROPERTY(EditAnywhere, Category=Parameter) TObjectPtr<UMaterialInterface> Material;
 UPROPERTY(EditAnywhere, Category=Parameter) TSoftObjectPtr<UMaterialInterface> SoftMaterial;
 UPROPERTY(EditAnywhere, Category=Parameter) TSubclassOf<AActor> ActorClass;
 UPROPERTY(EditAnywhere, Category=Parameter) TSoftClassPtr<AActor> SoftActorClass;
 UPROPERTY(EditAnywhere, Category=Input, meta=(Optional)) TArray<TObjectPtr<UMaterialInterface>> Materials;
 UPROPERTY(EditAnywhere, Category=Input, meta=(Optional)) TSet<TSubclassOf<AActor>> ActorClasses;
 UPROPERTY(EditAnywhere, Category=Input, meta=(Optional)) TMap<FName,TSoftObjectPtr<UMaterialInterface>> SoftMaterials;
};

/** Observes native bound/container values during real execution. */
USTRUCT()
struct FMCPVerificationContainerTask : public FStateTreeTaskCommonBase
{
 GENERATED_BODY()
 using FInstanceDataType=FMCPVerificationContainerTaskInstanceData;
 inline static float ObservedSum=0;
 inline static int32 Executions=0;
 virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }
 virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context,const FStateTreeTransitionResult& Transition) const override;
};

/** Blueprintable deterministic task for wrapper ownership/reinstancing tests. */
UCLASS(Blueprintable)
class UMCPVerificationBlueprintTask : public UStateTreeTaskBlueprintBase
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, Category=Parameter) float Amount=1;
 UPROPERTY(EditAnywhere, Category=Output) float ProducedValue=0;
 UPROPERTY(EditAnywhere, Category=Parameter) bool bSucceed=true;
 UPROPERTY(EditAnywhere, Category=Parameter) FVector Offset=FVector::ZeroVector;
 UPROPERTY(EditAnywhere, Category=Parameter) FName Label;
 UPROPERTY(EditAnywhere, Category=Parameter) TObjectPtr<UMaterialInterface> Material;
 UPROPERTY(EditAnywhere, Category=Parameter) TSoftObjectPtr<UMaterialInterface> SoftMaterial;
 UPROPERTY(EditAnywhere, Category=Parameter) TSubclassOf<AActor> ActorClass;
 UPROPERTY(EditAnywhere, Category=Parameter) TSoftClassPtr<AActor> SoftActorClass;
 UPROPERTY(EditAnywhere, Category=Parameter) TArray<float> Samples;
 UPROPERTY(EditAnywhere, Category=Parameter) TSet<int32> Codes;
 UPROPERTY(EditAnywhere, Category=Parameter) TMap<FName,float> Scores;
 inline static float ObservedAmount=0;
 inline static int32 ObservedEventCount=0;
 inline static float ObservedExtra=0;
 inline static int32 Executions=0;
protected:
 virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context,const FStateTreeTransitionResult& Transition) override;
};

UCLASS(Blueprintable)
class UMCPVerificationBlueprintCondition : public UStateTreeConditionBlueprintBase
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, Category=Parameter) bool bAllow=true;
 inline static int32 Evaluations=0;
protected:
 virtual bool TestCondition(FStateTreeExecutionContext&) const override { ++Evaluations; return bAllow; }
};

UCLASS(Blueprintable)
class UMCPVerificationBlueprintEvaluator : public UStateTreeEvaluatorBlueprintBase
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, Category=Parameter) float Amount=4;
 UPROPERTY(EditAnywhere, Category=Output) float OutputValue=0;
 inline static int32 Starts=0;
protected:
 virtual void TreeStart(FStateTreeExecutionContext&) override { ++Starts; OutputValue=Amount; }
};

UCLASS(Blueprintable)
class UMCPVerificationBlueprintConsideration : public UStateTreeConsiderationBlueprintBase
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, Category=Parameter, meta=(ClampMin="0",ClampMax="1")) float Score=.8f;
 inline static int32 Evaluations=0;
protected:
 virtual float GetScore(FStateTreeExecutionContext&) const override { ++Evaluations; return Score; }
};

UCLASS(EditInlineNew, DefaultToInstanced)
class UMCPVerificationInstancedObject : public UObject
{
 GENERATED_BODY()
};

USTRUCT()
struct FMCPVerificationReferenceFunctionData
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, Category=Parameter) TObjectPtr<UMaterialInterface> Material;
 UPROPERTY(EditAnywhere, Category=Parameter) TSoftObjectPtr<UMaterialInterface> SoftMaterial;
 UPROPERTY(EditAnywhere, Category=Parameter) TSubclassOf<AActor> ActorClass;
 UPROPERTY(EditAnywhere, Category=Parameter) TSoftClassPtr<AActor> SoftActorClass;
 UPROPERTY(EditAnywhere, Transient, Category=Parameter) TObjectPtr<UMaterialInterface> TransientMaterial;
 UPROPERTY(VisibleAnywhere, Category=Parameter) TObjectPtr<UMaterialInterface> ReadOnlyMaterial;
 UPROPERTY(EditAnywhere, Instanced, Category=Parameter) TObjectPtr<UMCPVerificationInstancedObject> InstancedObject;
 UPROPERTY(EditAnywhere, Category=Output) float Result=0;
};
USTRUCT()
struct FMCPVerificationReferenceFunction : public FStateTreePropertyFunctionCommonBase
{
 GENERATED_BODY()
 using FInstanceDataType=FMCPVerificationReferenceFunctionData;
 virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }
 virtual void Execute(FStateTreeExecutionContext& Context) const override;
};
