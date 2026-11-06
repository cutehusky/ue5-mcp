#pragma once
#include "CoreMinimal.h"
#include "Sound/QuartzQuantizationUtilities.h"
#include "QuartzEventUtils.generated.h"

class UQuartzClockHandle;
class UWorld;
class UAudioComponent;
class UAudioBus;
struct FQuartzEventReq;

struct FQuartzApiEvent
{
	uint64 Sequence = 0;
	FString Kind, Value;
	FName Clock;
	FName CommandName;
	int32 Bars = 0, Beat = 0;
	float BeatFraction = 0;
	double ReceivedSeconds = 0;
};

UCLASS(Transient)
class UQuartzApiObserver : public UObject
{
	GENERATED_BODY()
public:
	UPROPERTY() TObjectPtr<UQuartzClockHandle> Handle;
	UPROPERTY() TObjectPtr<UAudioComponent> AudioComponent;
	UPROPERTY() TMap<FString, TObjectPtr<UAudioBus>> AudioBuses;
	TMap<FString, float> RequestedSendLevels;
	FName ClockName;
	FString Id, Operation;
	bool bSubscription = false, bClosed = false, bTerminal = false;
	uint64 Sequence = 0, Dropped = 0;
	TArray<FQuartzApiEvent> Events;
	TWeakPtr<Audio::IQuartzQuantizedCommand> Command;
	UFUNCTION() void OnCommand(EQuartzCommandDelegateSubType EventType, FName Name);
	UFUNCTION() void OnAudioFinished();
	UFUNCTION() void OnMetronome(FName Clock, EQuartzCommandQuantization Quantization, int32 Bars, int32 Beat, float BeatFraction);
	void Rejected(const FString& Reason);
	void Append(FQuartzApiEvent Event);
};

namespace QuartzEventUtils
{
	FString Control(const FQuartzEventReq& Request);
	FString Inspect(const FString& Id, int32 PIEInstance, uint64 AfterSequence, int32 Limit);
	void Shutdown();
}
