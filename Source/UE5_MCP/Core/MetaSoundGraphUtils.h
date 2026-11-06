#pragma once

#include "CoreMinimal.h"

struct FMetaSoundCreateReq;
struct FMetaSoundGraphReq;
class UObject;

namespace MetaSoundGraphUtils
{
	FString Create(const FMetaSoundCreateReq& Request);
	FString NodeClasses(const FString& Search, int32 Limit);
	FString Inspect(UObject* Asset);
	FString Mutate(UObject* Asset, const FMetaSoundGraphReq& Request);
	FString Validate(UObject* Asset);
	FString Compile(UObject* Asset, bool bDryRun, bool bSave);
}
