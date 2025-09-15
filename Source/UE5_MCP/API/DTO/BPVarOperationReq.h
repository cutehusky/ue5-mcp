#pragma once
#include "CoreMinimal.h"
#include "BPVarOperationReq.generated.h"

USTRUCT()
struct FBPVarOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString BpPath;

	UPROPERTY()
	FString VarSignature; // for AddVariable e.g. 'int32 MyVar'

	UPROPERTY()
	FString DefaultValue; // for AddVariable or SetVariableDefaultValue

	UPROPERTY()
	FString OldVarName; // for RenameVariable

	UPROPERTY()
	FString NewVarName; // for RenameVariable

	UPROPERTY()
	FString VarName; // for DeleteVariable or SetVariableDefaultValue
};
