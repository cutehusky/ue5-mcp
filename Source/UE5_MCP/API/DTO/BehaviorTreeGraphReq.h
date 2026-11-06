#pragma once
#include "CoreMinimal.h"
#include "BehaviorTreeGraphReq.generated.h"
USTRUCT()
struct FBehaviorTreeLogicRow
{
	GENERATED_BODY()
	UPROPERTY() FString Operation;
	UPROPERTY() int32 Children=0;
	UPROPERTY() FString ClassPath;
	UPROPERTY() TMap<FString,FString> Properties;
	UPROPERTY() TMap<FString,FString> BlackboardSelectors;
};
USTRUCT()
struct FBehaviorTreeNodePosition
{
	GENERATED_BODY()
	UPROPERTY() FString NodeGuid;
	UPROPERTY() int32 X=0;
	UPROPERTY() int32 Y=0;
};
USTRUCT()
struct FBehaviorTreeGraphReq
{
	GENERATED_BODY()
	UPROPERTY() FString AssetPath;
	UPROPERTY() FString NodeGuid;
	UPROPERTY() FString ParentGuid;
	UPROPERTY() FString ClassPath;
	UPROPERTY() FString TargetGuid;
	UPROPERTY() int32 PinIndex=0;
	UPROPERTY() int32 TargetPinIndex=0;
	UPROPERTY() int32 X=0;
	UPROPERTY() int32 Y=0;
	UPROPERTY() TMap<FString,FString> Properties;
	UPROPERTY() TMap<FString,FString> BlackboardSelectors;
	UPROPERTY() TArray<FBehaviorTreeNodePosition> Positions;
	UPROPERTY() FString BlackboardPath;
	UPROPERTY() bool bSetSubtree=false;
	UPROPERTY() FString SubtreePath;
	UPROPERTY() bool bSetInjectionTag=false;
	UPROPERTY() FString InjectionTag;
	UPROPERTY() TArray<FBehaviorTreeLogicRow> Logic;
	UPROPERTY() bool bSetCompoundName=false;
	UPROPERTY() FString CompoundName;
	UPROPERTY() bool bConfirm=false;
	UPROPERTY() bool bDryRun=false;
	UPROPERTY() bool bSave=false;
};
