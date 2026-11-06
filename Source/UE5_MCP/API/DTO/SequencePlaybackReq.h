#pragma once

#include "CoreMinimal.h"
#include "SequencePlaybackReq.generated.h"

/** Request for bounded playback sampling on a sequence actor binding. */
USTRUCT()
struct FSequencePlaybackReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString BindingGuid;

	/** Optional placed actor that must already resolve from the sequence binding. */
	UPROPERTY()
	FString ActorPath;

	UPROPERTY()
	bool bPlayOnEditorActor = false;

	/** Frame in the Movie Scene tick resolution, matching the authoring routes. */
	UPROPERTY()
	int32 Frame = 0;
};
