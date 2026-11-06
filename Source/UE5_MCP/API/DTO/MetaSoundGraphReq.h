#pragma once

#include "CoreMinimal.h"
#include "MetaSoundGraphReq.generated.h"

USTRUCT()
struct FMetaSoundGraphReq
{
	GENERATED_BODY()

	UPROPERTY() FString AssetPath;
	UPROPERTY() FString Operation;
	UPROPERTY() FString NodeId;
	UPROPERTY() FString NodeClass;
	UPROPERTY() int32 MajorVersion = 1;
	UPROPERTY() FString SourceNodeId;
	UPROPERTY() FString SourceOutput;
	UPROPERTY() FString TargetNodeId;
	UPROPERTY() FString TargetInput;
	UPROPERTY() FString InputName;
	UPROPERTY() FString InputValue;
	UPROPERTY() int32 PositionX = 0;
	UPROPERTY() int32 PositionY = 0;
	UPROPERTY() bool bReplaceExisting = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bSave = false;
};
