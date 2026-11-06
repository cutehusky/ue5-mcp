#pragma once

#include "CoreMinimal.h"
#include "AudioWaveRebuildReq.generated.h"

USTRUCT()
struct FAudioWaveRebuildReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
