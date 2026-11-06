#pragma once

#include "CoreMinimal.h"
#include "CinematicCameraReq.generated.h"

USTRUCT()
struct FCinematicCameraReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString ActorPath;

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString BindingGuid;

	UPROPERTY()
	FString Label;

	UPROPERTY()
	FVector Location = FVector::ZeroVector;

	UPROPERTY()
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY()
	bool bSetTransform = false;

	UPROPERTY()
	float FocalLength = -1.f;

	UPROPERTY()
	float Aperture = -1.f;

	UPROPERTY()
	float MinFocalLength = -1.f;

	UPROPERTY()
	float MaxFocalLength = -1.f;

	UPROPERTY()
	float MinFStop = -1.f;

	UPROPERTY()
	float MaxFStop = -1.f;

	UPROPERTY()
	float SensorWidth = -1.f;

	UPROPERTY()
	float SensorHeight = -1.f;

	UPROPERTY()
	float ManualFocusDistance = -1.f;

	UPROPERTY()
	FString FocusMethod;

	UPROPERTY()
	FString FocusActorPath;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;
};
