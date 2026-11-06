#pragma once

#include "CoreMinimal.h"
#include "BlendSpaceReq.generated.h"

USTRUCT()
struct FBlendSpaceReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString AnimationPath;

	UPROPERTY()
	int32 SampleIndex = INDEX_NONE;

	UPROPERTY()
	FString SampleId;

	UPROPERTY()
	int32 AxisIndex = 0;

	UPROPERTY()
	FVector SampleValue = FVector::ZeroVector;

	UPROPERTY()
	TMap<FString, FString> Properties;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
