#pragma once
#include "CoreMinimal.h"
#include "EnvironmentQueryReq.generated.h"
USTRUCT()
struct FEnvironmentQueryGeneratorRow
{
 GENERATED_BODY()
 UPROPERTY() FString ClassPath;
 UPROPERTY() int32 Children=0;
 UPROPERTY() TMap<FString,FString> Properties;
 UPROPERTY() TMap<FString,FString> Classes;
 UPROPERTY() TMap<FString,FString> ProviderValues;
 UPROPERTY() TMap<FString,FString> NamedParameters;
};
USTRUCT()
struct FEnvironmentQueryPosition
{
 GENERATED_BODY()
 UPROPERTY() FString NodeGuid;
 UPROPERTY() int32 X=0;
 UPROPERTY() int32 Y=0;
};
USTRUCT()
struct FEnvironmentQueryReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString NodeGuid;
 UPROPERTY() FString ParentGuid;
 UPROPERTY() FString ClassPath;
 UPROPERTY() TMap<FString,FString> Properties;
 UPROPERTY() TMap<FString,FString> Classes;
 UPROPERTY() TMap<FString,FString> ProviderValues;
 UPROPERTY() TMap<FString,FString> NamedParameters;
 UPROPERTY() TArray<FEnvironmentQueryPosition> Positions;
 UPROPERTY() bool bSetGeneratorTree=false;
 UPROPERTY() TArray<FEnvironmentQueryGeneratorRow> GeneratorTree;
 UPROPERTY() int32 X=0;
 UPROPERTY() int32 Y=0;
 UPROPERTY() int32 Index=-1;
 UPROPERTY() bool bSetEnabled=false;
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
