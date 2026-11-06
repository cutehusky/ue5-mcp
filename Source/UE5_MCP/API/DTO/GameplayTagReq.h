#pragma once
#include "CoreMinimal.h"
#include "GameplayTagReq.generated.h"
USTRUCT()
struct FGameplayTagQueryNodeReq
{
 GENERATED_BODY()
 UPROPERTY() FString Mode=TEXT("AllTags");
 UPROPERTY() TArray<FString> Tags;
 UPROPERTY() TArray<int32> Children;
};
USTRUCT()
struct FGameplayTagReq
{
 GENERATED_BODY()
 UPROPERTY() TArray<FString> Tags;
 UPROPERTY() TArray<FString> RequiredTags;
 UPROPERTY() FString Mode=TEXT("All");
 UPROPERTY() bool bExact=false;
 UPROPERTY() TArray<FGameplayTagQueryNodeReq> QueryNodes;
 UPROPERTY() int32 RootIndex=0;
 UPROPERTY() FString NewTagName;
 UPROPERTY() bool bRenameChildren=true;
 UPROPERTY() FString TagName;
 UPROPERTY() FString Comment;
 UPROPERTY() FString SourceName;
 UPROPERTY() FString ProviderPath;
 UPROPERTY() FString ActorPath;
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString PropertyName;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
