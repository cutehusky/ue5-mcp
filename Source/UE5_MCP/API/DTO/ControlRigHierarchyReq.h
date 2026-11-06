#pragma once

#include "CoreMinimal.h"
#include "ControlRigHierarchyReq.generated.h"

USTRUCT()
struct FControlRigHierarchyReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString ElementType;

	UPROPERTY()
	FString Name;

	UPROPERTY()
	FString NewName;

	UPROPERTY()
	FString ParentType;

	UPROPERTY()
	FString ParentName;

	UPROPERTY()
	FString ControlType;

	UPROPERTY()
	FString ControlValue;

	/** Primary axis for scalar and Vector2D controls: x, y, or z. */
	UPROPERTY()
	FString PrimaryAxis = TEXT("x");

	/** Optional reflected UEnum object path for integer controls, for example /Script/Engine.EInputEvent. */
	UPROPERTY()
	FString ControlEnumPath;

	UPROPERTY()
	FString ControlDisplayName;

	UPROPERTY()
	FString ControlAnimationType;

	UPROPERTY()
	FString ShapeName;

	/** UE linear color text, for example R=1,G=0.2,B=0.1,A=1. */
	UPROPERTY()
	FString ShapeColor;

	UPROPERTY()
	FString ShapeVisibility;

	UPROPERTY()
	FString PreferredRotationOrder;

	UPROPERTY()
	FTransform ControlShapeTransform = FTransform::Identity;

	UPROPERTY()
	bool bSetControlShapeTransform = false;

	UPROPERTY()
	bool bSetShapeVisible = false;

	UPROPERTY()
	bool bShapeVisible = true;

	UPROPERTY()
	bool bSetDrawLimits = false;

	UPROPERTY()
	bool bDrawLimits = true;

	UPROPERTY()
	bool bSetGroupWithParentControl = false;

	UPROPERTY()
	bool bGroupWithParentControl = false;

	UPROPERTY()
	TArray<FString> DrivenControlNames;

	UPROPERTY()
	bool bSetDrivenControls = false;

	UPROPERTY()
	bool bSetPreferredRotationOrder = false;

	UPROPERTY()
	bool bUsePreferredRotationOrder = false;

	UPROPERTY()
	FString SpaceType;

	UPROPERTY()
	FString SpaceName;

	UPROPERTY()
	FString SpaceLabel;

	UPROPERTY()
	int32 SpaceIndex = -1;

	UPROPERTY()
	bool bAffectChildren = false;

	UPROPERTY()
	bool bMaintainGlobalTransform = true;

	UPROPERTY()
	bool bSetRestrictSpaceSwitching = false;

	UPROPERTY()
	bool bRestrictSpaceSwitching = false;

	UPROPERTY()
	FString ConnectorType;

	UPROPERTY()
	FString Description;

	UPROPERTY()
	bool bOptional = false;

	UPROPERTY()
	bool bIsArray = false;

	UPROPERTY()
	FString MinimumValue;

	UPROPERTY()
	FString MaximumValue;

	/** Composite-control limits use the same transform shape as Translation/Rotation/Scale. */
	UPROPERTY()
	FTransform MinimumTransform = FTransform::Identity;

	UPROPERTY()
	FTransform MaximumTransform = FTransform::Identity;

	/** Enabled limit dimensions: XYZ, then pitch/yaw/roll, then scale XYZ. Empty means all dimensions. */
	UPROPERTY()
	TArray<int32> LimitDimensions;

	UPROPERTY()
	bool bMinimumEnabled = true;

	UPROPERTY()
	bool bMaximumEnabled = true;

	UPROPERTY()
	FVector Translation = FVector::ZeroVector;

	UPROPERTY()
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY()
	FVector Scale = FVector::OneVector;

	UPROPERTY()
	float CurveValue = 0.f;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bInitial = false;

	UPROPERTY()
	bool bSave = false;
};
