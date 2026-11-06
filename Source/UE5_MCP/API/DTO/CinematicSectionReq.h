#pragma once

#include "CoreMinimal.h"
#include "CinematicSectionReq.generated.h"

USTRUCT()
struct FCinematicSectionReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString CameraBindingGuid;

	UPROPERTY()
	FString SequencePath;

	UPROPERTY()
	FString ShotName;

	UPROPERTY()
	int32 Frame = 0;

	UPROPERTY()
	int32 Duration = 1;

	UPROPERTY()
	int32 RowIndex = 0;

	UPROPERTY()
	int32 SectionIndex = -1;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;

	UPROPERTY()
	bool bConfirm = false;
};
