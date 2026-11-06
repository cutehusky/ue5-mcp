#pragma once

#include "CoreMinimal.h"
#include "AnimationNotifyReq.generated.h"

USTRUCT()
struct FAnimationNotifyReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString NotifyTrack;

	UPROPERTY()
	FString NotifyClass;

	UPROPERTY()
	FString NotifyName;

	UPROPERTY()
	float Time = 0.0f;

	UPROPERTY()
	float Duration = 0.0f;

	UPROPERTY()
	float Value = 0.0f;

	UPROPERTY()
	FVector VectorValue = FVector::ZeroVector;
};
