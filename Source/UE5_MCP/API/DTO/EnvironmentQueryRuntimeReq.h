#pragma once
#include "CoreMinimal.h"
#include "EnvironmentQueryRuntimeReq.generated.h"
USTRUCT()
struct FEnvironmentQueryParameter
{
 GENERATED_BODY()
 UPROPERTY() FString Name;
 UPROPERTY() FString Type;
 UPROPERTY() FString Value;
};
USTRUCT()
struct FEnvironmentQueryRuntimeReq
{
 GENERATED_BODY()
 UPROPERTY() FString Operation=TEXT("run");
 UPROPERTY() FString RequestId;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString OwnerPath;
 UPROPERTY() FString RunMode=TEXT("all_matching");
 UPROPERTY() TArray<FEnvironmentQueryParameter> Parameters;
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() int32 MaxItems=128;
 UPROPERTY() double TimeoutSeconds=10;
 UPROPERTY() bool bDryRun=false;
};
