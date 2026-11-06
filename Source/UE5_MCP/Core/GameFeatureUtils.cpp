#include "GameFeatureUtils.h"
#include "UE5_MCP/API/DTO/EditorExtReq.h"
#include "GameFeaturesSubsystem.h"
#include "GameFeatureTypes.h"
#include "Interfaces/IPluginManager.h"
#include "Editor.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace {
struct FFeature { FString Name; FString Url; FString Descriptor; };
TArray<FFeature> Discover() {
 TArray<FFeature> Out; UGameFeaturesSubsystem& Sub=UGameFeaturesSubsystem::Get();
 for(const TSharedRef<IPlugin>& Plugin:IPluginManager::Get().GetDiscoveredPlugins()) { FString Url; if(Sub.GetPluginURLByName(Plugin->GetName(),Url)) Out.Add({Plugin->GetName(),Url,Plugin->GetDescriptorFileName()}); }
 Out.Sort([](const FFeature& A,const FFeature& B){ return A.Name<B.Name; }); return Out;
}
FString StateName(const FString& Url) { return UE::GameFeatures::ToString(UGameFeaturesSubsystem::Get().GetPluginState(Url)); }
}
FString GameFeatureUtils::Plugins(const FEditorExtReq& R) {
 if(!IsInGameThread() || !GEditor) throw std::runtime_error("Editor game thread required");
 const TArray<FFeature> Features=Discover(); if(Features.Num()>512) throw std::runtime_error("Game feature discovery budget512 exceeded");
 UGameFeaturesSubsystem& Sub=UGameFeaturesSubsystem::Get(); FString Requested; bool Issued=false;
 if(R.Operation!=TEXT("Inspect")) {
  const FFeature* Feature=Features.FindByPredicate([&](const FFeature& F){ return F.Name==R.Name; }); if(!Feature) throw std::runtime_error("Exact discovered game feature plugin name required");
  const FString Prior=StateName(Feature->Url); if(!R.bConfirm || R.ExpectedSnapshot!=Prior) throw std::runtime_error("Confirmation and exact current plugin state name (ExpectedSnapshot) required");
  if(GEditor->PlayWorld && !R.bAllow) throw std::runtime_error("Changing game feature state during PIE requires bAllow");
  if(R.Operation==TEXT("Activate")) { Requested=TEXT("Active"); if(!R.bDryRun) Sub.LoadAndActivateGameFeaturePlugin(Feature->Url,FGameFeaturePluginLoadComplete()); }
  else if(R.Operation==TEXT("Deactivate")) { Requested=TEXT("Loaded"); if(!R.bDryRun) Sub.DeactivateGameFeaturePlugin(Feature->Url); }
  else if(R.Operation==TEXT("Unload")) { if(!R.bAllow) throw std::runtime_error("Unload releases plugin content; bAllow required"); Requested=TEXT("Unloaded/Registered"); if(!R.bDryRun) Sub.UnloadGameFeaturePlugin(Feature->Url,true); }
  else throw std::runtime_error("Operation must be Inspect, Activate, Deactivate or Unload");
  Issued=!R.bDryRun;
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("target"),R.Name); J->WriteValue(TEXT("requested_state"),Requested); J->WriteValue(TEXT("request_issued"),Issued); J->WriteValue(TEXT("dry_run"),R.bDryRun);
 J->WriteArrayStart(TEXT("game_features")); for(const FFeature& F:Features) { J->WriteObjectStart(); J->WriteValue(TEXT("name"),F.Name); J->WriteValue(TEXT("url"),F.Url); J->WriteValue(TEXT("descriptor"),F.Descriptor); J->WriteValue(TEXT("state"),StateName(F.Url)); J->WriteValue(TEXT("active"),Sub.IsGameFeaturePluginActive(F.Url)); J->WriteObjectEnd(); } J->WriteArrayEnd();
 J->WriteValue(TEXT("scope"),TEXT("UGameFeaturesSubsystem discovery (plugins resolvable by GetPluginURLByName) with native state names, plus Activate (LoadAndActivate), Deactivate and Unload (keep registered) requests guarded by confirmation and exact prior state name. State transitions are asynchronous; poll Inspect for the terminal state. Unload and PIE-time changes require bAllow. Does not edit .uplugin descriptors, initial state, actions or save. Unverified."));
 J->WriteObjectEnd(); J->Close(); return Json;
}
