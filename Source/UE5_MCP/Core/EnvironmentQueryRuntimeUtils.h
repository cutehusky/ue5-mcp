#pragma once
#include "CoreMinimal.h"
struct FEnvironmentQueryRuntimeReq;
class UWorld;
namespace EnvironmentQueryRuntimeUtils
{
 FString Control(const FEnvironmentQueryRuntimeReq& R);
 FString Inspect(const FString& Id,int32 PIEInstance);
 FString Owners(int32 PIEInstance,const FString& Search,int32 Limit);
 FString ControlInWorld(UWorld* World,const FEnvironmentQueryRuntimeReq& R);
 FString InspectInWorld(UWorld* World,const FString& Id);
 void Shutdown();
}
