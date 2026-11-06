#pragma once
#include "CoreMinimal.h"
#include "BehaviorTreeRuntimeReq.generated.h"
USTRUCT()
struct FBehaviorTreeRuntimeReq
{
 GENERATED_BODY()
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString InjectionTag;
 UPROPERTY() FString AssetPath;
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() bool bDryRun=false;
};
