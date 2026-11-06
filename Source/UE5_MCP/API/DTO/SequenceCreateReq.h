#pragma once

#include "CoreMinimal.h"
#include "SequenceCreateReq.generated.h"

USTRUCT()
struct FSequenceCreateReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;
};
