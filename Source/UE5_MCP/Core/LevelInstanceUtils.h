#pragma once

#include "CoreMinimal.h"
class UWorld;
struct FLevelInstanceReq;

namespace LevelInstanceUtils
{
	FString Inspect(UWorld* World, const FString& ActorPath, bool bValidate = false);
	FString Operate(UWorld* World, const FLevelInstanceReq& Request);
}
