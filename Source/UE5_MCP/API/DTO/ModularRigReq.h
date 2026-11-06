#pragma once

#include "CoreMinimal.h"
#include "ModularRigReq.generated.h"

USTRUCT()
struct FModularRigTargetReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString Name;

	UPROPERTY()
	FString Type;
};

USTRUCT()
struct FModularRigReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString ModuleName;

	UPROPERTY()
	FString NewName;

	UPROPERTY()
	FString ParentName;

	UPROPERTY()
	FString ModuleClassPath;

	UPROPERTY()
	FString ConnectorName;

	UPROPERTY()
	FString TargetType;

	UPROPERTY()
	FString TargetName;

	UPROPERTY()
	TArray<FModularRigTargetReq> Targets;

	UPROPERTY()
	FString VariablePath;

	UPROPERTY()
	FString Value;

	UPROPERTY()
	FString SourcePath;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
