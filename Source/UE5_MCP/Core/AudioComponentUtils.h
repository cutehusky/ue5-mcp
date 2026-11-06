#pragma once
#include "CoreMinimal.h"
struct FAudioComponentSettingsReq;
namespace AudioComponentUtils
{
	FString Inspect(const FString& BlueprintPath, const FString& ComponentName, const FString& ActorPath = FString());
	FString Edit(const FAudioComponentSettingsReq& Request);
}
