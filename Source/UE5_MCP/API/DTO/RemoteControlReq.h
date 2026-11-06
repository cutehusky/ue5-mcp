#pragma once
#include "CoreMinimal.h"
#include "RemoteControlReq.generated.h"
USTRUCT()
struct FRemoteControlReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString Kind=TEXT("property");
 UPROPERTY() FString ObjectPath;
 UPROPERTY() FString FieldPath;
 UPROPERTY() FString Label;
 UPROPERTY() FString EntityId;
 UPROPERTY() FString ExpectedLabel;
 UPROPERTY() FString Value;
 UPROPERTY() FString ExpectedValue;
 UPROPERTY() int32 ExpectedEntityCount=-1;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
