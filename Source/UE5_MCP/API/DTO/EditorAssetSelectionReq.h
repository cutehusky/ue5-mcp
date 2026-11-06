#pragma once

#include "CoreMinimal.h"
#include "EditorAssetSelectionReq.generated.h"

/** Content Browser selection/reveal request. */
USTRUCT()
struct FEditorAssetSelectionReq
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<FString> AssetPaths;
};
