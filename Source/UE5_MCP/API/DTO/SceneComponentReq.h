#pragma once

#include "CoreMinimal.h"
#include "SceneComponentReq.generated.h"

/** Request for placed-actor component creation, attachment, property editing, or deletion. */
USTRUCT()
struct FSceneComponentReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString ActorPath;

	UPROPERTY()
	FString ComponentName;

	UPROPERTY()
	FString ComponentClass;

	UPROPERTY()
	FString AttachToComponent;

	UPROPERTY()
	FString AttachSocket;

	UPROPERTY()
	TMap<FString, FString> Properties;

	UPROPERTY()
	bool bSetAttachment = false;

	UPROPERTY()
	bool bConfirm = false;
};
