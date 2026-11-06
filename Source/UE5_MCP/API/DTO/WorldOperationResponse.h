#pragma once

#include "CoreMinimal.h"
#include "WorldOperationResponse.generated.h"

/** Structured result for editor-world lifecycle mutations and preflight conflicts. */
USTRUCT()
struct FWorldOperationResponse
{
	GENERATED_BODY()

	UPROPERTY()
	bool Success = false;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString PreviousWorldPath;

	UPROPERTY()
	FString WorldPath;

	UPROPERTY()
	FString PackagePath;

	UPROPERTY()
	FString MapName;

	UPROPERTY()
	bool bDirty = false;

	UPROPERTY()
	bool bSaved = false;

	UPROPERTY()
	TArray<FString> DirtyMapPackages;

	UPROPERTY()
	TArray<FString> DirtyContentPackages;

	UPROPERTY()
	TArray<FString> ChangedPackages;

	UPROPERTY()
	TArray<FString> SavedPackages;

	UPROPERTY()
	TArray<FString> Warnings;

	UPROPERTY()
	TArray<FString> Errors;
};
