#include "AssetConsolidationUtils.h"
#include "UE5_MCP/API/DTO/EditorExtReq.h"
#include "ObjectTools.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Modules/ModuleManager.h"
#include "Misc/PackageName.h"
#include "Editor.h"
#include "UObject/Package.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace {
UObject* ResolveAsset(const FString& Path) {
 if(Path.IsEmpty() || Path.Len()>1024 || !FPackageName::IsValidObjectPath(Path)) throw std::runtime_error("Bounded valid asset object path required");
 IAssetRegistry& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
 const FAssetData Data=Registry.GetAssetByObjectPath(FSoftObjectPath(Path)); if(!Data.IsValid() || Data.IsRedirector()) throw std::runtime_error("Registered non-redirector asset required");
 UObject* Object=Data.GetAsset(); if(!IsValid(Object) || !Object->IsAsset() || Object->HasAnyFlags(RF_Transient) || Object->GetOutermost()==GetTransientPackage() || Object->GetPathName()!=Path) throw std::runtime_error("Exact persistent asset required");
 return Object;
}
void WriteReferencers(TSharedRef<TJsonWriter<>> J,UObject* Object) {
 IAssetRegistry& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
 TArray<FName> Referencers; Registry.GetReferencers(Object->GetOutermost()->GetFName(),Referencers); Referencers.Sort(FNameLexicalLess());
 J->WriteValue(TEXT("referencer_count"),Referencers.Num()); J->WriteArrayStart(TEXT("referencers")); for(int32 I=0;I<Referencers.Num() && I<256;++I) J->WriteValue(Referencers[I].ToString()); J->WriteArrayEnd(); J->WriteValue(TEXT("referencers_truncated"),Referencers.Num()>256);
}
}
FString AssetConsolidationUtils::Consolidate(const FEditorExtReq& R) {
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("Stopped editor on game thread required");
 if(R.Paths.Num()<1 || R.Paths.Num()>64) throw std::runtime_error("Paths must list 1..64 assets to consolidate into TargetPath");
 UObject* Target=ResolveAsset(R.TargetPath); TArray<UObject*> Sources; TSet<FString> Seen;
 for(const FString& Path:R.Paths) { if(Seen.Contains(Path) || Path==R.TargetPath) throw std::runtime_error("Distinct sources different from target required"); Seen.Add(Path); UObject* Source=ResolveAsset(Path); if(Source->GetClass()!=Target->GetClass()) throw std::runtime_error("All sources must have the target's exact class"); if(Source->GetOutermost()==Target->GetOutermost()) throw std::runtime_error("Sources must live in packages other than the target's"); Sources.Add(Source); }
 FString Snapshot; { auto J=TJsonWriterFactory<>::Create(&Snapshot); J->WriteObjectStart(); J->WriteValue(TEXT("target"),Target->GetPathName()); J->WriteValue(TEXT("class"),Target->GetClass()->GetPathName()); J->WriteArrayStart(TEXT("sources")); for(UObject* S:Sources) { J->WriteObjectStart(); J->WriteValue(TEXT("path"),S->GetPathName()); J->WriteValue(TEXT("package_dirty"),S->GetOutermost()->IsDirty()); WriteReferencers(J,S); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); }
 bool Written=false; TArray<FString> Dirtied,Invalid,Failed;
 if(R.Operation==TEXT("Consolidate")) {
  if(!R.bConfirm || !R.bAllow || R.ExpectedSnapshot!=Snapshot) throw std::runtime_error("Consolidation is destructive and not undoable: bConfirm, bAllow and exact source/referencer snapshot required");
  if(!R.bDryRun) { TArray<UObject*> Mutable=Sources; const ObjectTools::FConsolidationResults Results=ObjectTools::ConsolidateObjects(Target,Mutable,false); for(UPackage* P:Results.DirtiedPackages) Dirtied.Add(GetPathNameSafe(P)); for(UObject* O:Results.InvalidConsolidationObjs) Invalid.Add(GetPathNameSafe(O)); for(UObject* O:Results.FailedConsolidationObjs) Failed.Add(GetPathNameSafe(O)); Written=true; }
 } else if(R.Operation!=TEXT("Inspect")) throw std::runtime_error("Operation must be Inspect or Consolidate");
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("snapshot"),Snapshot); J->WriteValue(TEXT("written"),Written); J->WriteValue(TEXT("dry_run"),R.bDryRun);
 auto Arr=[&](const TCHAR* K,const TArray<FString>& V){ J->WriteArrayStart(K); for(const FString& S:V) J->WriteValue(S); J->WriteArrayEnd(); }; Arr(TEXT("dirtied_packages"),Dirtied); Arr(TEXT("invalid_objects"),Invalid); Arr(TEXT("failed_objects"),Failed);
 J->WriteValue(TEXT("scope"),TEXT("Native ObjectTools::ConsolidateObjects of 1..64 same-class registered sources into one target without confirmation dialogs. Inspect reports per-source registry referencers (first256) and package dirty state as the guard snapshot. Consolidate requires bConfirm+bAllow+exact snapshot; it replaces references, removes sources and dirties referencer packages; it is not an editor transaction and cannot be undone. Does not save, fix up redirectors or check source control. Unverified."));
 J->WriteObjectEnd(); J->Close(); return Json;
}
