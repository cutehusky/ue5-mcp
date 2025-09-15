#pragma once
#include "CoreMinimal.h"

#include "BPComponentOperationReq.generated.h"

USTRUCT()
struct  FBPComponentOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;

	UPROPERTY()
	FString ComponentClass;

	UPROPERTY()
	FString ComponentName;

	UPROPERTY()
	FString AttachTo = FString();

	UPROPERTY()
	FString NewComponentName = FString(); // used for RenameComponentInBlueprint
};
