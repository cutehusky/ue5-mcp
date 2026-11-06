#pragma once
#include "CoreMinimal.h"
struct FModulationRecordingReq;
namespace ModulationRecordingUtils
{
	FString Control(const FModulationRecordingReq& Request);
	FString Inspect(const FString& Id, int32 PIEInstance, uint64 AfterSequence, int32 Limit);
	void Shutdown();
}
