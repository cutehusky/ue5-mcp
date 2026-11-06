#pragma once
#include "CoreMinimal.h"
#include "AnimationRichCurveReq.generated.h"
USTRUCT()
struct FAnimationRichKeyReq
{
 GENERATED_BODY()
 UPROPERTY() float Time=0;
 UPROPERTY() float Value=0;
 UPROPERTY() int32 Interpolation=0;
 UPROPERTY() int32 TangentMode=0;
 UPROPERTY() int32 WeightMode=0;
 UPROPERTY() float ArriveTangent=0;
 UPROPERTY() float LeaveTangent=0;
 UPROPERTY() float ArriveWeight=0;
 UPROPERTY() float LeaveWeight=0;
};
USTRUCT()
struct FAnimationTransformKeyReq
{
 GENERATED_BODY()
 UPROPERTY() float Time=0;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY() FVector Scale=FVector::OneVector;
};
USTRUCT()
struct FAnimationRichCurveReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString CurveName;
 UPROPERTY() FString Channel=TEXT("translation");
 UPROPERTY() int32 Axis=0;
 UPROPERTY() FString Operation=TEXT("set");
 UPROPERTY() FAnimationRichKeyReq Key;
 UPROPERTY() float NewTime=0;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY() FVector Scale=FVector::OneVector;
 UPROPERTY() FString NewName;
 UPROPERTY() FString Comment;
 UPROPERTY() FLinearColor Color=FLinearColor::White;
 UPROPERTY() FString Flag=TEXT("Editable");
 UPROPERTY() bool bFlagEnabled=true;
 UPROPERTY() int32 PreExtrapolation=4;
 UPROPERTY() int32 PostExtrapolation=4;
 UPROPERTY() TArray<FAnimationRichKeyReq> Keys;
 UPROPERTY() TArray<FAnimationTransformKeyReq> TransformKeys;
 UPROPERTY() TArray<float> Times;
 UPROPERTY() float DefaultValue=0;
 UPROPERTY() float BlendWeight=1;
 UPROPERTY() float TimeOffset=0;
 UPROPERTY() float TimeOrigin=0;
 UPROPERTY() float TimeFactor=1;
 UPROPERTY() float RangeStart=0;
 UPROPERTY() float RangeEnd=0;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
