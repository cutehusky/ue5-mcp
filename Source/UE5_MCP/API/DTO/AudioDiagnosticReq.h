#pragma once
#include "CoreMinimal.h"
#include "AudioDiagnosticReq.generated.h"
USTRUCT()
struct FAudioDiagnosticReq
{
	GENERATED_BODY()
	UPROPERTY() FString CaptureId;
	UPROPERTY() FString Operation = TEXT("capture");
	UPROPERTY() int32 PIEInstance = -1;
	UPROPERTY() int32 Limit = 128;
	UPROPERTY() bool bDryRun = false;
};
