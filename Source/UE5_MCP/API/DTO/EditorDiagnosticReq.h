#pragma once

#include "CoreMinimal.h"
#include "EditorDiagnosticReq.generated.h"

/** Request for bounded editor diagnostics, automation, and screenshots. */
USTRUCT()
struct FEditorDiagnosticReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString TestName;

	UPROPERTY()
	FString Filename;

	UPROPERTY()
	bool bShowUI = false;
};
