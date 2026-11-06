#pragma once
#include "CoreMinimal.h"
struct FAbilitySystemReq;
namespace AbilitySystemUtils
{
 FString ValidateDefinition(const FString& ClassPath);
 FString EditBlueprintDefaults(const FAbilitySystemReq& R);
 FString InspectChannels();
 FString SetAbilityTags(const FAbilitySystemReq& R);
 FString CreateBlueprintAsset(const FAbilitySystemReq& R);
 FString ExecuteCue(const FAbilitySystemReq& R);
 FString EvaluateEffectDefinition(const FAbilitySystemReq& R);
 FString AddAttributeSet(const FAbilitySystemReq& R);
 FString InspectDefaults(const FString& ClassPath);
 FString InspectCalculation(const FString& ClassPath);
 FString InspectAttributeClass(const FString& ClassPath);
 FString LoadClassDefinition(const FAbilitySystemReq& R);
 FString InspectAbilityClass(const FString& ClassPath);
 FString InspectEffectClass(const FString& ClassPath);
 FString QueryEffects(const FAbilitySystemReq& R);
 FString MatchAbilitiesByTags(const FAbilitySystemReq& R);
 FString CancelByTags(const FAbilitySystemReq& R);
 FString ActivateByTags(const FAbilitySystemReq& R);
 FString AddLooseTag(const FAbilitySystemReq& R);
 FString InspectTagCounts(const FAbilitySystemReq& R);
 FString CheckAbility(const FAbilitySystemReq& R);
 FString SetAbilityInputID(const FAbilitySystemReq& R);
 FString SetAbilityLevel(const FAbilitySystemReq& R);
 FString AbilityInput(const FAbilitySystemReq& R);
 FString InhibitEffect(const FAbilitySystemReq& R);
 FString UpdateEffectMagnitudes(const FAbilitySystemReq& R);
 FString SetEffectLevel(const FAbilitySystemReq& R);
 FString ApplyEffect(const FAbilitySystemReq& R);
 FString RemoveAbility(const FAbilitySystemReq& R);
 FString GrantAbility(const FAbilitySystemReq& R);
 FString SetAttribute(const FAbilitySystemReq& R);
 FString SendEvent(const FAbilitySystemReq& R);
 FString Discover(const FString& Kind,const FString& Search,int32 Limit);
 FString RemoveEffect(const FAbilitySystemReq& R);
 FString ControlRuntime(const FAbilitySystemReq& R);
 FString InspectRuntime(const FString& ComponentPath,const FString& Search,int32 Limit,int32 PIEInstance);
}
