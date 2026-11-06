#pragma once
#include "CoreMinimal.h"
struct FPerceptionReq;
namespace PerceptionUtils
{
 FString InspectEditor(const FString& ComponentPath,const FString& Search,int32 Limit);
 FString Discover(const FString& Search,int32 Limit);
 FString ConfigureSource(const FPerceptionReq& R);
 FString InspectSources(const FString& Search,int32 Limit);
 FString ControlSource(const FPerceptionReq& R);
 FString ReportDamage(const FPerceptionReq& R);
 FString ReportNoise(const FPerceptionReq& R);
 FString ControlEditor(const FPerceptionReq& R);
 FString ControlRuntime(const FPerceptionReq& R);
 FString InspectRuntime(const FString& ComponentPath,const FString& Search,int32 Limit,int32 PIEInstance);
}
