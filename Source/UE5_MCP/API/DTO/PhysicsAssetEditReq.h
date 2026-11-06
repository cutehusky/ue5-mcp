#pragma once

#include "CoreMinimal.h"
#include "PhysicsAssetEditReq.generated.h"

USTRUCT()
struct FPhysicsAssetEditReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString BoneName;

	UPROPERTY()
	FString OtherBoneName;

	UPROPERTY()
	FString SkeletalMeshPath;

	UPROPERTY()
	FString ShapeType = TEXT("sphere");

	UPROPERTY()
	int32 ShapeIndex = -1;

	UPROPERTY()
	FVector Center = FVector::ZeroVector;

	UPROPERTY()
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY()
	FVector Size = FVector(10.0, 10.0, 10.0);

	/** Local-space convex hull points; used only when ShapeType is convex. */
	UPROPERTY()
	TArray<FVector> Vertices;

	UPROPERTY()
	float Radius = 5.0f;

	UPROPERTY()
	float Length = 10.0f;

	UPROPERTY()
	bool bEnableCollision = true;

	UPROPERTY()
	bool bContributeToMass = true;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
