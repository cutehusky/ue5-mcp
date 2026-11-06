#pragma once
#include "CoreMinimal.h"
struct FAudioTraceReq;
namespace AudioTraceUtils
{
	FString Control(const FAudioTraceReq& Request);
	FString Inspect(const FString& Id);
	void Shutdown();
}
