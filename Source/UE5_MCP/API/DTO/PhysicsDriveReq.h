#pragma once

#include "CoreMinimal.h"
#include "PhysicsDriveReq.generated.h"

USTRUCT()
struct FPhysicsDriveReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString ConstraintName;

	/** linear or angular. */
	UPROPERTY()
	FString DriveType;

	/** slerp or twist_swing for angular drives. */
	UPROPERTY()
	FString AngularMode;

	UPROPERTY()
	bool bPositionX = false;

	UPROPERTY()
	bool bPositionY = false;

	UPROPERTY()
	bool bPositionZ = false;

	UPROPERTY()
	bool bVelocityX = false;

	UPROPERTY()
	bool bVelocityY = false;

	UPROPERTY()
	bool bVelocityZ = false;

	UPROPERTY()
	bool bOrientationTwist = false;

	UPROPERTY()
	bool bOrientationSwing = false;

	UPROPERTY()
	bool bAngularVelocityTwist = false;

	UPROPERTY()
	bool bAngularVelocitySwing = false;

	UPROPERTY()
	bool bSlerpPosition = false;

	UPROPERTY()
	bool bSlerpVelocity = false;

	UPROPERTY()
	bool bAccelerationMode = false;

	UPROPERTY()
	float Stiffness = 0.f;

	UPROPERTY()
	float Damping = 0.f;

	UPROPERTY()
	float ForceLimit = 0.f;

	UPROPERTY()
	FVector PositionTarget = FVector::ZeroVector;

	UPROPERTY()
	FVector VelocityTarget = FVector::ZeroVector;

	UPROPERTY()
	FRotator OrientationTarget = FRotator::ZeroRotator;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;
};
