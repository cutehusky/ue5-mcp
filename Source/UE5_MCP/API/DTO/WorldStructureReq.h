#pragma once

#include "CoreMinimal.h"
#include "WorldStructureReq.generated.h"

/** Request for sublevel and Data Layer editor operations. */
USTRUCT()
struct FWorldStructureReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString ActorPath;

	UPROPERTY()
	FString ActorGuid;

	UPROPERTY()
	FString ExpectedLabel;

	UPROPERTY()
	FString FieldName;

	UPROPERTY()
	int32 Start = 0;

	UPROPERTY()
	int32 Count = 64;

	UPROPERTY()
	FString ExpectedWorldPath;

	UPROPERTY()
	FString ExpectedStreamingPath;

	UPROPERTY()
	FString ExpectedCurrentLevelPath;

	UPROPERTY()
	bool bLocked = false;

	UPROPERTY()
	bool bExpectedLocked = false;

	UPROPERTY()
	bool bExpectedVisible = false;

	UPROPERTY()
	bool bDryRun = true;

	UPROPERTY()
	TArray<FString> VolumePaths;

	UPROPERTY()
	TArray<FString> ExpectedVolumePaths;

	UPROPERTY()
	TArray<double> ColorValues;

	UPROPERTY()
	TArray<double> ExpectedColorValues;

	UPROPERTY()
	double Value = 0;

	UPROPERTY()
	double ExpectedValue = 0;

	UPROPERTY()
	FString FolderPath;

	UPROPERTY()
	FString ExpectedFolderPath;

	UPROPERTY()
	FString LevelPath;

	UPROPERTY()
	FString ExpectedStreamingClass;

	UPROPERTY()
	FString StreamingClass;

	UPROPERTY()
	FString DataLayerName;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FTransform ExpectedTransform = FTransform::Identity;

	UPROPERTY()
	FTransform Transform = FTransform::Identity;

	UPROPERTY()
	bool bVisible = true;

	UPROPERTY()
	bool bConfirm = false;
};
