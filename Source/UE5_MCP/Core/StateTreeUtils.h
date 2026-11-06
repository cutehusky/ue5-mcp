#pragma once
#include "CoreMinimal.h"
struct FStateTreeReq;
namespace StateTreeUtils
{
 void Shutdown();
 FString DiscoverSchemas(const FString& Search,int32 Limit);
 FString Inspect(const FString& Path,bool Validate=false);
 FString InspectBindables(const FString& Path,const FString& TargetId);
 FString DiscoverClasses(const FString& Path,const FString& Kind,const FString& Search,int32 Limit);
 FString Discover(const FString& Path,const FString& Kind,const FString& Search,int32 Limit);
 FString InspectRuntime(const FString& ComponentPath,const FString& Search,int32 Limit,int32 PIEInstance);
 FString ControlRuntime(const FStateTreeReq& R);
 FString Control(const FStateTreeReq& R,const FString& Op);
}
