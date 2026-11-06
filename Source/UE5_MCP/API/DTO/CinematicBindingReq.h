#pragma once

#include "CoreMinimal.h"
#include "CinematicBindingReq.generated.h"

USTRUCT()
struct FCinematicBindingReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString Name;

	UPROPERTY()
	FString ClassPath;

	UPROPERTY()
	FString BindingGuid;

	/** Optional path of a placed actor to bind to the new possessable. */
	UPROPERTY()
	FString ActorPath;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;

	UPROPERTY()
	bool bConfirm = false;
};
