#pragma once

#include "CoreMinimal.h"

class USoundWave;
struct FSoundWaveImportReq;

namespace SoundWaveImportUtils
{
	FString FormatsJson();
	FString SourceJson(const USoundWave* Wave);
	FString Import(const FSoundWaveImportReq& Request);
	FString Reimport(USoundWave* Wave, const FSoundWaveImportReq& Request);
}
