#pragma once

#include "CoreMinimal.h"
#include "Engine/AssetUserData.h"
#include "BlendSpaceSampleIdentityData.generated.h"

/** Persistent identities for Blend Space samples edited through UE5_MCP. */
UCLASS()
class UBlendSpaceSampleIdentityData : public UAssetUserData
{
	GENERATED_BODY()

public:
	UPROPERTY()
	TArray<FGuid> SampleIds;

	UPROPERTY()
	TArray<FString> SampleFingerprints;
};
