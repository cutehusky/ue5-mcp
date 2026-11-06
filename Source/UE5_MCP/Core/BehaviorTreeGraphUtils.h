#pragma once
#include "CoreMinimal.h"
struct FBehaviorTreeGraphReq;
struct FBehaviorTreeRuntimeReq;
class UBehaviorTreeComponent;
namespace BehaviorTreeGraphUtils
{
 FString Runtime(const FString& ComponentPath,int32 PIEInstance);
 FString RuntimeControl(const FBehaviorTreeRuntimeReq& R);
 // Component-level operation also supports isolated native Game-world tests.
 FString ReplaceDynamic(UBehaviorTreeComponent* Component,const FString& Tag,const FString& AssetPath,bool DryRun=false);
	FString Inspect(const FString& Path);
	FString Control(const FBehaviorTreeGraphReq& R,const FString& Operation);
}
