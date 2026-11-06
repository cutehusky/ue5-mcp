#pragma once
#include "CoreMinimal.h"
struct FNavigationAgentReq;
namespace NavigationAgentUtils
{
	FString Control(const FNavigationAgentReq& R);
	FString Inspect(const FString& Id,int32 PIEInstance,uint64 After=0,int32 Limit=100);
	void Shutdown();
}
