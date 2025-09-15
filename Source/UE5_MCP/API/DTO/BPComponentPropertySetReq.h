#pragma once
#include "CoreMinimal.h"
#include "BPComponentPropertySetReq.generated.h"

USTRUCT()
struct FBPComponentPropertySetReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;

	UPROPERTY()
	FString ComponentName;

	UPROPERTY()
	TMap<FString, FString> Properties; // key: property path, value: property value as string
};
