#pragma once
#include "CoreMinimal.h"
#include "QuartzReq.generated.h"

USTRUCT()
struct FQuartzPulseReq
{
	GENERATED_BODY()
	UPROPERTY() int32 NumberOfPulses = 1;
	UPROPERTY() FString PulseDuration;
};

USTRUCT()
struct FQuartzReq
{
	GENERATED_BODY()
	UPROPERTY() FString ClockName;
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() FString Operation = TEXT("create");
	UPROPERTY() int32 BeatsPerBar = 4;
	UPROPERTY() int32 BeatDenominator = 4;
	UPROPERTY() TArray<FQuartzPulseReq> PulseOverrides;
	UPROPERTY() float BeatsPerMinute = 120.0f;
	UPROPERTY() bool bUseAudioEngineClockManager = true;
	UPROPERTY() bool bIgnoreLevelChange = false;
	UPROPERTY() bool bCancelPendingEvents = true;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
};
