#pragma once
#include "CoreMinimal.h"
#include "EditorExtReq.generated.h"
/** Shared request for feature-first editor extension families (widget animations, consolidation,
 *  game features, smart objects, editor utilities). Unverified. */
USTRUCT()
struct FEditorExtReq { GENERATED_BODY()
 UPROPERTY() FString Operation=TEXT("Inspect");
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString TargetPath;
 UPROPERTY() FString Name;
 UPROPERTY() FString FieldName;
 UPROPERTY() FString TextValue;
 UPROPERTY() FString PathFilter;
 UPROPERTY() TArray<FString> Paths;
 UPROPERTY() TArray<double> Numbers;
 UPROPERTY() int32 Index=-1;
 UPROPERTY() int32 Start=0;
 UPROPERTY() int32 Count=64;
 UPROPERTY() FString ExpectedSnapshot;
 UPROPERTY() bool bEnabled=false;
 UPROPERTY() bool bAllow=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=true;
};
