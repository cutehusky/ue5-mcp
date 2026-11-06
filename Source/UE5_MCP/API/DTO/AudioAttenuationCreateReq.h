#pragma once

#include "CoreMinimal.h"
#include "AudioAttenuationCreateReq.generated.h"

USTRUCT()
struct FAudioAttenuationCreateReq
{
	GENERATED_BODY()

	/** Long package name without an object suffix, for example /Game/Audio/Outdoor. */
	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;
};
