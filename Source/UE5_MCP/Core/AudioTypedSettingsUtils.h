#pragma once

#include "CoreMinimal.h"

struct FSoundClassSettingsReq;
struct FSoundMixSettingsReq;
struct FSoundMixAdjusterReq;
struct FSoundSubmixSettingsReq;
struct FSoundSubmixEffectReq;
class USoundClass;
class USoundMix;
class USoundSubmix;

namespace AudioTypedSettingsUtils
{
	FString InspectSoundClass(USoundClass* Asset);
	FString EditSoundClass(USoundClass* Asset, const FSoundClassSettingsReq& Request);
	FString ValidateSoundClass(USoundClass* Asset);

	FString InspectSoundMix(USoundMix* Asset);
	FString EditSoundMix(USoundMix* Asset, const FSoundMixSettingsReq& Request);
	FString EditSoundMixAdjuster(USoundMix* Asset, const FSoundMixAdjusterReq& Request);
	FString ValidateSoundMix(USoundMix* Asset);

	FString InspectSoundSubmix(USoundSubmix* Asset);
	FString EditSoundSubmix(USoundSubmix* Asset, const FSoundSubmixSettingsReq& Request);
	FString EditSoundSubmixEffect(USoundSubmix* Asset, const FSoundSubmixEffectReq& Request);
	FString ValidateSoundSubmix(USoundSubmix* Asset);
}
