#pragma once
#include "CoreMinimal.h"
struct FGameplayTagReq;
struct FGameplayTagQuery;
namespace GameplayTagUtils
{
 FGameplayTagQuery BuildQuery(const FGameplayTagReq& R);
 FString RegisterTable(const FGameplayTagReq& R);
 FString EditTableTag(const FGameplayTagReq& R);
 FString ResolveTags(const FGameplayTagReq& R);
 FString InspectSettings(const FString& Search,int32 Limit);
 FString InspectProviders(const FString& Search,int32 Limit,int32 PIEInstance);
 FString EvaluateRuntime(const FGameplayTagReq& R);
 FString InspectRuntime(const FString& ActorPath,const FString& Search,int32 Limit,int32 PIEInstance);
 FString InspectUnused(const FString& Search,int32 Limit);
 FString MoveTags(const FGameplayTagReq& R);
 FString DeleteTag(const FGameplayTagReq& R);
 FString RenameTag(const FGameplayTagReq& R);
 FString UpdateTag(const FGameplayTagReq& R);
 FString CreateSource(const FGameplayTagReq& R);
 FString InspectSources(const FString& Search,int32 Limit);
 FString CreateTag(const FGameplayTagReq& R);
 FString EvaluateAsset(const FGameplayTagReq& R);
 FString InspectAsset(const FString& Path);
 FString EditAsset(const FGameplayTagReq& R);
 FString Evaluate(const FGameplayTagReq& R);
 FString Inspect(const FString& Tag,const FString& Search,int32 Limit,bool DictionaryOnly);
}
