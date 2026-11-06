#pragma once
#include "CoreMinimal.h"
struct FModulationProfileReq;
namespace ModulationProfileUtils
{
	FString Inspect(const FString& AssetPath, int32 ProfileIndex);
	FString Control(const FModulationProfileReq& Request);
}
