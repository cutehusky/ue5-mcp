#pragma once

#include "CoreMinimal.h"
#include "AudioConcurrencyCreateReq.generated.h"

USTRUCT()
struct FAudioConcurrencyCreateReq
{
	GENERATED_BODY()

	/** Long package name without an object suffix, for example /Game/Audio/Footsteps. */
	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;
};
