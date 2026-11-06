#pragma once
#include "CoreMinimal.h"
struct FAudioDiagnosticReq;
namespace AudioDiagnosticUtils
{
	FString Control(const FAudioDiagnosticReq& Request);
	FString Inspect(const FString& Id, int32 PIEInstance);
	void Shutdown();
}
