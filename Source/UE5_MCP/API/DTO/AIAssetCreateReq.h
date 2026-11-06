#pragma once

#include "CoreMinimal.h"
#include "AIAssetCreateReq.generated.h"

USTRUCT()
struct FAIAssetCreateReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;
};
