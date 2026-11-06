#pragma once
#include "CoreMinimal.h"
struct FBlackboardKeyReq;
namespace BlackboardUtils
{
	void Shutdown();
	FString Inspect(const FString& Path);
	FString Control(const FBlackboardKeyReq& R,const FString& Operation);
}
