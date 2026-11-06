#pragma once
#include "CoreMinimal.h"
#include "GameplayTagReq.h"
#include "AbilitySystemReq.generated.h"
USTRUCT()
struct FGameplayCaptureReq
{
 GENERATED_BODY()
 UPROPERTY() FString AttributePath;
 UPROPERTY() FString Source=TEXT("Source");
 UPROPERTY() bool bSnapshot=false;
};
USTRUCT()
struct FEffectConditionalReq
{
 GENERATED_BODY()
 UPROPERTY() FString EffectClass;
 UPROPERTY() TArray<FString> RequiredSourceTags;
};
USTRUCT()
struct FEffectGrantedAbilityReq
{
 GENERATED_BODY()
 UPROPERTY() FString AbilityClass;
 UPROPERTY() float Level=1;
 UPROPERTY() FString LevelCurveTable;
 UPROPERTY() FString LevelCurveRow;
 UPROPERTY() int32 InputID=-1;
 UPROPERTY() FString RemovalPolicy=TEXT("CancelAbilityImmediately");
};

USTRUCT()
struct FEffectQueryReq
{
 GENERATED_BODY()
 UPROPERTY() FString PropertyName;
 UPROPERTY() TArray<FGameplayTagQueryNodeReq> QueryNodes;
 UPROPERTY() int32 RootIndex=0;
};
USTRUCT()
struct FEffectTagRequirementsReq
{
 GENERATED_BODY()
 UPROPERTY() FString PropertyName;
 UPROPERTY() TArray<FString> Required;
 UPROPERTY() TArray<FString> Ignored;
 UPROPERTY() TArray<FGameplayTagQueryNodeReq> QueryNodes;
 UPROPERTY() int32 RootIndex=0;
};
USTRUCT()
struct FEffectInheritedTagsReq
{
 GENERATED_BODY()
 UPROPERTY() FString PropertyName;
 UPROPERTY() TArray<FString> Added;
 UPROPERTY() TArray<FString> Removed;
};
USTRUCT()
struct FEffectComponentReq
{
 GENERATED_BODY()
 UPROPERTY() bool bSetAdditionalEffects=false;
 UPROPERTY() TArray<FEffectConditionalReq> OnApplication;
 UPROPERTY() TArray<FString> OnCompleteAlways;
 UPROPERTY() TArray<FString> OnCompleteNormal;
 UPROPERTY() TArray<FString> OnCompletePrematurely;
 UPROPERTY() bool bSetGrantedAbilities=false;
 UPROPERTY() TArray<FEffectGrantedAbilityReq> GrantedAbilities;
 UPROPERTY() TArray<FEffectQueryReq> Queries;
 UPROPERTY() TArray<FEffectTagRequirementsReq> Requirements;
 UPROPERTY() TArray<FEffectInheritedTagsReq> InheritedTags;
 UPROPERTY() TMap<FString,FString> TagProperties;
 UPROPERTY() TMap<FString,FString> ClassReferences;
 UPROPERTY() FString ClassPath;
 UPROPERTY() TMap<FString,FString> Properties;
};
USTRUCT()
struct FEffectCueReq
{
 GENERATED_BODY()
 UPROPERTY() TArray<FString> Tags;
 UPROPERTY() float MinLevel=0;
 UPROPERTY() float MaxLevel=1;
 UPROPERTY() FString AttributePath;
};
USTRUCT()
struct FEffectExecutionReq
{
 GENERATED_BODY()
 UPROPERTY() TArray<FEffectConditionalReq> ConditionalEffects;
 UPROPERTY() FString CalculationClass;
 UPROPERTY() TArray<FString> Tags;
};
USTRUCT()
struct FEffectModifierReq
{
 GENERATED_BODY()
 UPROPERTY() FString AttributePath;
 UPROPERTY() FString Operation=TEXT("AddBase");
 UPROPERTY() float Magnitude=0;
 UPROPERTY() FString MagnitudeType=TEXT("Constant");
 UPROPERTY() FString DataTag;
 UPROPERTY() FString CurveTablePath;
 UPROPERTY() FString CurveRow;
 UPROPERTY() FString CalculationClass;
 UPROPERTY() TArray<FGameplayTagQueryNodeReq> SourceQueryNodes;
 UPROPERTY() int32 SourceQueryRoot=0;
 UPROPERTY() TArray<FGameplayTagQueryNodeReq> TargetQueryNodes;
 UPROPERTY() int32 TargetQueryRoot=0;
 UPROPERTY() TArray<FString> SourceRequiredTags;
 UPROPERTY() TArray<FString> SourceIgnoredTags;
 UPROPERTY() TArray<FString> TargetRequiredTags;
 UPROPERTY() TArray<FString> TargetIgnoredTags;
 UPROPERTY() TArray<FString> SourceTagFilter;
 UPROPERTY() TArray<FString> TargetTagFilter;
 UPROPERTY() FString CaptureAttributePath;
 UPROPERTY() FString CaptureSource=TEXT("Source");
 UPROPERTY() bool bSnapshot=false;
 UPROPERTY() FString AttributeCalculation=TEXT("AttributeMagnitude");
 UPROPERTY() int32 EvaluationChannel=0;
 UPROPERTY() int32 FinalChannel=0;
 UPROPERTY() FString CoefficientCurveTable;
 UPROPERTY() FString CoefficientCurveRow;
 UPROPERTY() FString PreAddCurveTable;
 UPROPERTY() FString PreAddCurveRow;
 UPROPERTY() FString PostAddCurveTable;
 UPROPERTY() FString PostAddCurveRow;
 UPROPERTY() float Coefficient=1;
 UPROPERTY() float PreAdd=0;
 UPROPERTY() float PostAdd=0;
};
USTRUCT()
struct FAbilityTriggerReq
{
 GENERATED_BODY()
 UPROPERTY() FString Tag;
 UPROPERTY() FString Source=TEXT("GameplayEvent");
};
USTRUCT()
struct FAbilitySystemReq
{
 GENERATED_BODY()
 UPROPERTY() bool bSetEffectComponents=false;
 UPROPERTY() TArray<FEffectComponentReq> EffectComponents;
 UPROPERTY() TMap<FString,FString> Stacking;
 UPROPERTY() bool bSetTiming=false;
 UPROPERTY() FString DurationPolicy=TEXT("Instant");
 UPROPERTY() float Duration=1;
 UPROPERTY() float Period=0;
 UPROPERTY() FString DurationCurveTable;
 UPROPERTY() FString DurationCurveRow;
 UPROPERTY() FString PeriodCurveTable;
 UPROPERTY() FString PeriodCurveRow;
 UPROPERTY() bool bSetCues=false;
 UPROPERTY() TArray<FEffectCueReq> Cues;
 UPROPERTY() bool bSetExecutions=false;
 UPROPERTY() TArray<FEffectExecutionReq> Executions;
 UPROPERTY() bool bSetModifiers=false;
 UPROPERTY() TArray<FEffectModifierReq> Modifiers;
 UPROPERTY() bool bSetCaptures=false;
 UPROPERTY() TArray<FGameplayCaptureReq> Captures;
 UPROPERTY() bool bSetTriggers=false;
 UPROPERTY() TArray<FAbilityTriggerReq> Triggers;
 UPROPERTY() TMap<FString,FString> Properties;
 UPROPERTY() TArray<FString> ResetProperties;
 UPROPERTY() TMap<FString,FString> ObjectReferences;
 UPROPERTY() TMap<FString,FString> SoftObjectReferences;
 UPROPERTY() TMap<FString,FString> SoftClassReferences;
 UPROPERTY() TMap<FString,FString> ClassReferences;
 UPROPERTY() TMap<FString,FString> TagProperties;
 UPROPERTY() FString AssetPath;
 UPROPERTY() bool bSave=false;
 UPROPERTY() FString ClassPath;
 UPROPERTY() FString Kind=TEXT("ability");
 UPROPERTY() FString ComponentPath;
 UPROPERTY() TArray<FString> DynamicSourceTags;
 UPROPERTY() FString AbilityClassPath;
 UPROPERTY() int32 Level=1;
 UPROPERTY() int32 InputID=-1;
 UPROPERTY() FString AbilityHandle;
 UPROPERTY() FString EffectCauserPath;
 UPROPERTY() FString SourceObjectPath;
 UPROPERTY() TArray<FString> DynamicAssetTags;
 UPROPERTY() FString EffectClassPath;
 UPROPERTY() FString TargetComponentPath;
 UPROPERTY() float EffectLevel=1;
 UPROPERTY() TMap<FString,float> SetByCaller;
 UPROPERTY() bool bInhibit=true;
 UPROPERTY() bool bInvokeGameplayCues=true;
 UPROPERTY() FString EffectHandle;
 UPROPERTY() TArray<FString> IgnoredEffectHandles;
 UPROPERTY() int32 StacksToRemove=-1;
 UPROPERTY() FString AttributePath;
 UPROPERTY() float BaseValue=0;
 UPROPERTY() FString Operation;
 UPROPERTY() TArray<FString> Tags;
 UPROPERTY() TArray<FString> TargetActorPaths;
 UPROPERTY() FString OptionalObjectPath;
 UPROPERTY() FString OptionalObject2Path;
 UPROPERTY() FVector CueLocation=FVector::ZeroVector;
 UPROPERTY() FVector CueNormal=FVector::UpVector;
 UPROPERTY() bool bUseAvatarLocation=true;
 UPROPERTY() float NormalizedMagnitude=0;
 UPROPERTY() TArray<FEffectQueryReq> RuntimeQueries;
 UPROPERTY() TArray<FString> ExcludedTags;
 UPROPERTY() int32 TagCount=1;
 UPROPERTY() FString EventTag;
 UPROPERTY() FString InstigatorPath;
 UPROPERTY() FString TargetPath;
 UPROPERTY() TArray<FString> InstigatorTags;
 UPROPERTY() TArray<FString> TargetTags;
 UPROPERTY() bool bUseCheckTags=false;
 UPROPERTY() float EventMagnitude=0;
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
};
