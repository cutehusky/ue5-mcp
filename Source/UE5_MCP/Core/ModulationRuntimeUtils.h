#pragma once
#include "CoreMinimal.h"
struct FModulationRuntimeReq;
class UWorld;
namespace ModulationRuntimeUtils
{
	FString Inspect(const FString& AssetPath, int32 PIEInstance);
	FString Control(const FModulationRuntimeReq& Request);
	void Shutdown();
	UWorld* ResolveAudioWorld(int32 PIEInstance);
}
