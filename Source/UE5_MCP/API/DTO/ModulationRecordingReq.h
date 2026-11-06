#pragma once
#include "CoreMinimal.h"
#include "ModulationRecordingReq.generated.h"
USTRUCT()
struct FModulationRecordingReq
{
	GENERATED_BODY()
	UPROPERTY() FString RecordingId;
	UPROPERTY() FString Operation = TEXT("start");
	UPROPERTY() FString AssetPath;
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() float IntervalSeconds = .05f;
	UPROPERTY() float DurationSeconds = 2.f;
	UPROPERTY() bool bDryRun = false;
};
