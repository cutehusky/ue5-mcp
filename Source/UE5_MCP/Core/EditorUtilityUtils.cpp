#include "EditorUtilityUtils.h"
#include "UE5_MCP/API/DTO/EditorExtReq.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "EditorUtilityBlueprint.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Modules/ModuleManager.h"
#include "Editor.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
FString EditorUtilityUtils::Utilities(const FEditorExtReq& R) {
 if(!IsInGameThread() || !GEditor) throw std::runtime_error("Editor game thread required");
 const FString Filter=R.PathFilter.IsEmpty()?FString(TEXT("/Game")):R.PathFilter; if(Filter.Len()>512 || !Filter.StartsWith(TEXT("/"))) throw std::runtime_error("Bounded content path filter required");
 IAssetRegistry& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
 FARFilter AR; AR.PackagePaths.Add(FName(*Filter)); AR.bRecursivePaths=true; AR.ClassPaths.Add(UEditorUtilityWidgetBlueprint::StaticClass()->GetClassPathName()); AR.ClassPaths.Add(UEditorUtilityBlueprint::StaticClass()->GetClassPathName()); AR.bRecursiveClasses=true;
 TArray<FAssetData> Assets; Registry.GetAssets(AR,Assets); Assets.Sort([](const FAssetData& A,const FAssetData& B){ return A.GetObjectPathString()<B.GetObjectPathString(); });
 const int32 Start=FMath::Max(0,R.Start),Count=FMath::Clamp(R.Count,1,256);
 FString Action,TabId; bool Issued=false,Succeeded=false;
 if(R.Operation==TEXT("Run") || R.Operation==TEXT("SpawnTab")) {
  if(!R.bConfirm || !R.bAllow) throw std::runtime_error("Running editor utilities executes project code: bConfirm and bAllow required");
  if(GEditor->PlayWorld) throw std::runtime_error("Stopped editor required");
  const FAssetData* Data=Assets.FindByPredicate([&](const FAssetData& A){ return A.GetObjectPathString()==R.AssetPath; }); if(!Data) throw std::runtime_error("Exact registered editor utility asset path under PathFilter required");
  UEditorUtilitySubsystem* Sub=GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>(); if(!Sub) throw std::runtime_error("Editor Utility subsystem unavailable");
  UObject* Asset=Data->GetAsset(); if(!IsValid(Asset)) throw std::runtime_error("Editor utility asset failed to load");
  if(R.Operation==TEXT("SpawnTab")) { auto* Widget=Cast<UEditorUtilityWidgetBlueprint>(Asset); if(!Widget) throw std::runtime_error("SpawnTab requires an Editor Utility Widget Blueprint"); Action=TEXT("SpawnAndRegisterTab"); if(!R.bDryRun) { FName Id; Sub->SpawnAndRegisterTabAndGetID(Widget,Id); TabId=Id.ToString(); Succeeded=!Id.IsNone(); Issued=true; } }
  else { Action=TEXT("TryRun"); if(!R.bDryRun) { Succeeded=Sub->TryRun(Asset); Issued=true; } }
 } else if(R.Operation!=TEXT("Inspect")) throw std::runtime_error("Operation must be Inspect, Run or SpawnTab");
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("path_filter"),Filter); J->WriteValue(TEXT("total"),Assets.Num()); J->WriteArrayStart(TEXT("utilities"));
 for(int32 I=Start;I<Assets.Num() && I<Start+Count;++I) { J->WriteObjectStart(); J->WriteValue(TEXT("path"),Assets[I].GetObjectPathString()); J->WriteValue(TEXT("class"),Assets[I].AssetClassPath.ToString()); J->WriteValue(TEXT("loaded"),Assets[I].IsAssetLoaded()); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("action"),Action); J->WriteValue(TEXT("tab_id"),TabId); J->WriteValue(TEXT("issued"),Issued); J->WriteValue(TEXT("succeeded"),Succeeded); J->WriteValue(TEXT("dry_run"),R.bDryRun);
 J->WriteValue(TEXT("scope"),TEXT("Asset Registry discovery of Editor Utility Widget Blueprints and Editor Utility Blueprints under a path filter (paged<=256), plus native UEditorUtilitySubsystem SpawnAndRegisterTabAndGetID and TryRun. Execution runs arbitrary project editor code and requires bConfirm+bAllow in a stopped editor; side effects are not transactional or inspected. Unverified."));
 J->WriteObjectEnd(); J->Close(); return Json;
}
