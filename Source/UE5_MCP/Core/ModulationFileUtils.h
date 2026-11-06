#pragma once
#include "CoreMinimal.h"
struct FModulationFileReq;
class USoundModulationPatch;
struct FWaveTableTransform;
namespace ModulationFileUtils
{
	FString Import(USoundModulationPatch* Asset, const FModulationFileReq& Request);
	TArray<FString> Errors(const FWaveTableTransform& Transform);
	FString SourceJson(const FWaveTableTransform& Transform);
	bool HasSource(const FWaveTableTransform& Transform);
	bool ReadSource(const FWaveTableTransform& Transform, FWaveTableTransform& FileTransform);
}
