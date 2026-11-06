#pragma once
#include "CoreMinimal.h"
struct FQuartzReq;
class UWorld;
namespace QuartzUtils
{
	FString Inspect(const FString& ClockName, int32 PIEInstance);
	FString Control(const FQuartzReq& Request);
	UWorld* ResolveWorld(int32 PIEInstance);
	FName ClockName(const FString& Value);
}
