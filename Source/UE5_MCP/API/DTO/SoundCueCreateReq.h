#pragma once

#include "CoreMinimal.h"
#include "SoundCueCreateReq.generated.h"

USTRUCT()
struct FSoundCueCreateReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
