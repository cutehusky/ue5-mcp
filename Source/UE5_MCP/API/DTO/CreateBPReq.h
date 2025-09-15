#pragma once

#include "CoreMinimal.h"
#include "CreateBPReq.generated.h"

USTRUCT()
struct FCreateBPReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString ParentClass;

	UPROPERTY()
	FString BpPath;
};
