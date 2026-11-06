#pragma once
#include "CoreMinimal.h"
#include "AudioTraceReq.generated.h"
USTRUCT()
struct FAudioTraceReq
{
	GENERATED_BODY()
	UPROPERTY() FString CaptureId;
	UPROPERTY() FString Operation = TEXT("start");
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() TArray<FString> Channels;
	UPROPERTY() float DurationSeconds = 5.f;
	UPROPERTY() int32 MaxFileMB = 64;
	UPROPERTY() bool bDryRun = false;
};
