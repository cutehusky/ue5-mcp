#pragma once
#include "CoreMinimal.h"
#include "QuartzEventReq.generated.h"

USTRUCT()
struct FQuartzAudioBusSend
{
	GENERATED_BODY()
	UPROPERTY() FString BusPath;
	UPROPERTY() float SendLevel = 1.f;
	UPROPERTY() bool bPostEffect = true;
};

USTRUCT()
struct FQuartzEventReq
{
	GENERATED_BODY()
	UPROPERTY() FString ClockName;
	UPROPERTY() FString EventId;
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() FString Operation;
	UPROPERTY() FString Quantization = TEXT("Bar");
	UPROPERTY() float Multiplier = 1.f;
	UPROPERTY() FString ReferencePoint = TEXT("TransportRelative");
	UPROPERTY() float BeatsPerMinute = 120.f;
	UPROPERTY() FString OtherClockName;
	UPROPERTY() FString SoundPath;
	UPROPERTY() float StartTime = 0.f;
	UPROPERTY() float VolumeMultiplier = 1.f;
	UPROPERTY() float PitchMultiplier = 1.f;
	UPROPERTY() float FadeInDuration = 0.f;
	UPROPERTY() bool bSpatialized = false;
	UPROPERTY() FVector Location = FVector::ZeroVector;
	UPROPERTY() FRotator Rotation = FRotator::ZeroRotator;
	UPROPERTY() FString AttachComponentPath;
	UPROPERTY() FString AttachSocket;
	UPROPERTY() FString AttenuationPath;
	UPROPERTY() FString ConcurrencyPath;
	UPROPERTY() TArray<FQuartzAudioBusSend> AudioBusSends;
	UPROPERTY() bool bFireOnClockStart = true;
	UPROPERTY() bool bCancelIfNotRunning = false;
	UPROPERTY() bool bResumeOnQueued = false;
	UPROPERTY() bool bDryRun = false;
};
