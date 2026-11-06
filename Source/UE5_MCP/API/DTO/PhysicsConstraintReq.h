#pragma once

#include "CoreMinimal.h"
#include "PhysicsConstraintReq.generated.h"

USTRUCT()
struct FPhysicsConstraintReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString ConstraintName;

	UPROPERTY()
	FString ChildBone;

	UPROPERTY()
	FString ParentBone;

	/** locked, limited, free, or empty to retain current motion. */
	UPROPERTY()
	FString LinearMotion;

	UPROPERTY()
	FString AngularMotion;

	UPROPERTY()
	float LinearLimit = -1.f;

	UPROPERTY()
	float Swing1Limit = -1.f;

	UPROPERTY()
	float Swing2Limit = -1.f;

	UPROPERTY()
	float TwistLimit = -1.f;

	/** enabled, disabled, or empty to retain current projection state. */
	UPROPERTY()
	FString Projection;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
