#pragma once
#include "CoreMinimal.h"
#include "PCGReq.generated.h"
USTRUCT()
struct FPCGReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString ComponentPath;
 UPROPERTY() int32 OutputIndex=-1;
 UPROPERTY() FString DataPath;
 UPROPERTY() int32 PointStart=0;
 UPROPERTY() int32 PointCount=64;
 UPROPERTY() FString ActorPath;
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bForce=false;
 UPROPERTY() int32 Seed=42;
 UPROPERTY() FString SourceAssetPath;
 UPROPERTY() FString SettingsClass;
 UPROPERTY() FString SettingsPath;
 UPROPERTY() FString RecordHash;
 UPROPERTY() FString FieldName;
 UPROPERTY() FString ParameterName;
 UPROPERTY() FString ParameterId;
 UPROPERTY() int32 ElementStart=0;
 UPROPERTY() int32 ElementCount=64;
 UPROPERTY() double ScalarValue=0;
 UPROPERTY() FString EnumValue;
 UPROPERTY() FString TextValue;
 UPROPERTY() TArray<FString> StringValues;
 UPROPERTY() TArray<double> ScalarValues;
 UPROPERTY() TArray<FVector> VectorValues;
 UPROPERTY() FString ValueKind;
 UPROPERTY() FVector VectorValue=FVector::ZeroVector;
 UPROPERTY() FRotator RotatorValue=FRotator::ZeroRotator;
 UPROPERTY() FTransform TransformValue=FTransform::Identity;
 UPROPERTY() FLinearColor ColorValue=FLinearColor::White;
 UPROPERTY() int32 NodeIndex=-1;
 UPROPERTY() FString NodePath;
 UPROPERTY() int32 TargetNodeIndex=-1;
 UPROPERTY() FString TargetNodePath;
 UPROPERTY() FString FromPin;
 UPROPERTY() int32 PinIndex=-1;
 UPROPERTY() bool bAllowMultipleConnections=true;
 UPROPERTY() bool bAllowMultipleData=true;
 UPROPERTY() FString PinStatus=TEXT("Normal");
 UPROPERTY() int32 TargetPinIndex=-1;
 UPROPERTY() FString ToPin;
 UPROPERTY() FString Action;
 UPROPERTY() FString Title;
 UPROPERTY() bool bCommentVisible=false;
 UPROPERTY() bool bCommentPinned=false;
 UPROPERTY() int32 NodeX=0;
 UPROPERTY() int32 NodeY=0;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
