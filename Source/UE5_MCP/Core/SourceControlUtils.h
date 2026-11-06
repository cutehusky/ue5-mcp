#pragma once

#include "CoreMinimal.h"

struct FSourceControlReq;

namespace SourceControlUtils
{
	FString ProviderJson();
	FString AssetsJson(const FSourceControlReq& Request);
	FString HistoryJson(const FSourceControlReq& Request);
}
