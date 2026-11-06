#pragma once

#include "CoreMinimal.h"
#include "PhysicsBodyProfileReq.generated.h"

USTRUCT()
struct FPhysicsBodyProfileReq
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
	FString BoneName;

	UPROPERTY()
	bool bLocalSimulation = true;

	UPROPERTY()
	float OrientationStrength = 0.f;

	UPROPERTY()
	float AngularVelocityStrength = 0.f;

	UPROPERTY()
	float PositionStrength = 0.f;

	UPROPERTY()
	float VelocityStrength = 0.f;

	UPROPERTY()
	float MaxLinearForce = 0.f;

	UPROPERTY()
	float MaxAngularForce = 0.f;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
