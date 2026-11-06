#pragma once

#include "CoreMinimal.h"
#include "PhysicsProfileReq.generated.h"

USTRUCT()
struct FPhysicsProfileReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString ProfileName;

	UPROPERTY()
	FString SourceProfileName;

	UPROPERTY()
	FString NewName;

	UPROPERTY()
	FString ConstraintName;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
