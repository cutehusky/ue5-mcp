#include "BlackboardUtils.h"
#include "BlackboardKeySettingsUtils.h"
#include "UE5_MCP/API/DTO/BlackboardKeyReq.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Object.h"
#include "AISystem.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Editor.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/Package.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UObjectHash.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
 UBlackboardData* Load(const FString& Path)
 {
  const FString Package=FPackageName::ObjectPathToPackageName(Path);
  if(!FPackageName::IsValidLongPackageName(Package)) throw std::runtime_error("A valid Blackboard asset path is required");
  const FString Object=Path.Contains(TEXT(".")) ? Path : Package+TEXT(".")+FPackageName::GetLongPackageAssetName(Package);
  auto* B=FindObject<UBlackboardData>(nullptr,*Object);
  if(!B && FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(Object)).IsValid()) B=LoadObject<UBlackboardData>(nullptr,*Object);
  if(!IsValid(B)) throw std::runtime_error("Asset is not an existing Blackboard"); return B;
 }
 void Name(const FString& S)
 {
  if(S.IsEmpty() || S.Len()>128 || S.TrimStartAndEnd()!=S || FName(*S).IsNone()) throw std::runtime_error("Key names require 1-128 nonempty characters without outer whitespace or None");
  for(TCHAR C:S) if(C<32 || C==127) throw std::runtime_error("Key names cannot contain control characters");
 }
 bool Related(UBlackboardData* B,UBlackboardData* Target)
 {
  TSet<UBlackboardData*> Seen; for(;B && !Seen.Contains(B);B=B->Parent) { if(B==Target) return true; Seen.Add(B); } return false;
 }
 TArray<FString> Errors(UBlackboardData* B,const TArray<FBlackboardEntry>* Override=nullptr,UBlackboardData* Parent=nullptr,bool SetParent=false,UBlackboardData* Edited=nullptr)
 {
  auto* Target=Edited ? Edited : B;
  TArray<FString> E; TSet<UBlackboardData*> Seen; TSet<FName> Names; int32 Count=0;
  for(auto* It=B;It;It=It==Target && SetParent ? Parent : It->Parent.Get())
  {
   if(Seen.Contains(It) || Seen.Num()>=32) { E.Add(TEXT("Parent cycle or chain depth exceeds 32")); break; } Seen.Add(It);
   const auto& Keys=It==Target && Override ? *Override : It->Keys;
   for(const auto& K:Keys)
   {
    ++Count;
    if(K.EntryName.IsNone() || Names.Contains(K.EntryName)) E.Add(TEXT("Empty or duplicate local/inherited key: ")+K.EntryName.ToString()); Names.Add(K.EntryName);
    if(!IsValid(K.KeyType) || K.KeyType->GetClass()->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) E.Add(TEXT("Missing or incompatible key type: ")+K.EntryName.ToString());
   }
  }
  if(Count>=int32(FBlackboard::InvalidKey) || Count>1024) E.Add(TEXT("Effective key count exceeds native ID capacity or adapter limit 1024")); return E;
 }
 FString Signature(UBlackboardData* B)
 {
  FString S=GetPathNameSafe(B->Parent); for(const auto& K:B->Keys) S+=TEXT("|")+K.EntryName.ToString()+TEXT(":")+GetPathNameSafe(K.KeyType)+FString::FromInt(K.bInstanceSynced); return S;
 }
 TMap<TWeakObjectPtr<UBlackboardData>,FString> Tracked;
 FDelegateHandle Undo;
 void AfterUndo()
 {
  bool Changed=false;
  for(auto It=Tracked.CreateIterator();It;++It) if(auto* B=It.Key().Get()) Changed|=It.Value()!=Signature(B); else It.RemoveCurrent();
  if(!Changed) return;
  TSet<UBlackboardData*> Done;
  TFunction<void(UBlackboardData*)> Refresh=[&](UBlackboardData* B)
  {
   if(!B || Done.Contains(B) || !Errors(B).IsEmpty()) return;
   Done.Add(B); Refresh(B->Parent); B->UpdateParentKeys(); B->UpdateIfHasSynchronizedKeys();
  };
  for(auto& Pair:Tracked) if(auto* B=Pair.Key.Get()) Refresh(B);
  for(auto& Pair:Tracked) if(auto* B=Pair.Key.Get()) Pair.Value=Signature(B);
 }
 TArray<UBlackboardData*> Boards()
 {
  TArray<FAssetData> Assets; auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
  Registry.GetAssetsByClass(UBlackboardData::StaticClass()->GetClassPathName(),Assets,true);
  if(Assets.Num()>512) throw std::runtime_error("Blackboard dependency preflight exceeds 512 assets");
  TArray<UBlackboardData*> Result;
  for(const auto& A:Assets) if(auto* B=Cast<UBlackboardData>(A.GetAsset())) Result.AddUnique(B);
  for(TObjectIterator<UBlackboardData> It;It;++It) if(It->IsAsset()) Result.AddUnique(*It);
  if(Result.Num()>512) throw std::runtime_error("Blackboard dependency preflight exceeds 512 assets"); return Result;
 }
 FString Json(UBlackboardData* B,bool Change=false,bool Dry=false,bool Saved=false,const TArray<FString>& Dependencies={},const TArray<FString>& Updated={})
 {
  FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart();
  J->WriteValue(TEXT("asset_path"),B->GetPathName()); J->WriteValue(TEXT("parent_path"),B->Parent ? B->Parent->GetPathName() : TEXT(""));
  J->WriteValue(TEXT("changed"),Change && !Dry); J->WriteValue(TEXT("would_change"),Change); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),B->GetOutermost()->IsDirty());
  J->WriteValue(TEXT("has_synchronized_keys"),B->HasSynchronizedKeys());
  auto Rows=[&](const TCHAR* Field,bool Inherited)
  {
   J->WriteArrayStart(Field); TSet<UBlackboardData*> Seen; int32 Count=0;
   for(auto* It=Inherited ? B->Parent.Get() : B;It && !Seen.Contains(It) && Seen.Num()<32;It=Inherited ? It->Parent.Get() : nullptr)
   {
    Seen.Add(It); for(const auto& K:It->Keys) if(Count++<1024)
    {
     J->WriteObjectStart(); J->WriteValue(TEXT("name"),K.EntryName.ToString()); J->WriteValue(TEXT("type"),K.KeyType ? K.KeyType->GetClass()->GetPathName() : TEXT(""));
     J->WriteValue(TEXT("key_object_path"),K.KeyType ? K.KeyType->GetPathName() : TEXT("")); J->WriteValue(TEXT("owner_path"),It->GetPathName());
     J->WriteValue(TEXT("category"),K.EntryCategory.ToString()); J->WriteValue(TEXT("description"),K.EntryDescription); J->WriteValue(TEXT("instance_synced"),bool(K.bInstanceSynced));
     J->WriteRawJSONValue(TEXT("type_settings"),BlackboardKeySettingsUtils::Snapshot(K.KeyType));
     J->WriteValue(TEXT("key_id"),int32(It->GetFirstKeyID())+int32(&K-It->Keys.GetData())); J->WriteObjectEnd();
    }
   } J->WriteArrayEnd();
  }; Rows(TEXT("keys"),false); Rows(TEXT("inherited_keys"),true);
  J->WriteArrayStart(TEXT("referencer_packages")); for(const auto& D:Dependencies) J->WriteValue(D); J->WriteArrayEnd();
  J->WriteArrayStart(TEXT("updated_selector_objects")); for(const auto& D:Updated) J->WriteValue(D); J->WriteArrayEnd();
  auto E=Errors(B); const bool StructuralValid=E.IsEmpty(); TSet<UBlackboardData*> Seen;
  for(auto* It=B;It && !Seen.Contains(It) && Seen.Num()<32;It=It->Parent) { Seen.Add(It); for(const auto& K:It->Keys) for(const auto& V:BlackboardKeySettingsUtils::Validate(K.KeyType)) E.Add(K.EntryName.ToString()+TEXT(": ")+V); }
  J->WriteObjectStart(TEXT("validation")); J->WriteValue(TEXT("structurally_valid"),StructuralValid); J->WriteValue(TEXT("valid"),E.IsEmpty()); J->WriteArrayStart(TEXT("errors")); for(const auto& V:E) J->WriteValue(V); J->WriteArrayEnd();
  J->WriteValue(TEXT("scope"),TEXT("Bounded parent-chain, key names/types and native key capacity; instance_synced is native synchronization, not an instance-editable flag. Exact native scalar, vector/rotation, Object/Class and Enum settings are checked; Struct/custom/deprecated key settings and arbitrary Blueprint/string references require separate adapters."));
  J->WriteObjectEnd(); J->WriteObjectEnd(); J->Close(); return S;
 }
}

void BlackboardUtils::Shutdown()
{
 if(Undo.IsValid()) { FEditorDelegates::PostUndoRedo.Remove(Undo); Undo.Reset(); } Tracked.Reset();
}
FString BlackboardUtils::Inspect(const FString& Path) { return Json(Load(Path)); }
FString BlackboardUtils::Control(const FBlackboardKeyReq& R,const FString& Operation)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || GEditor->bIsSimulatingInEditor) throw std::runtime_error("Stop PIE/simulation before editing Blackboards");
 auto* B=Load(R.AssetPath); if(!B->GetOutermost()->GetName().StartsWith(TEXT("/Game/"))) throw std::runtime_error("Blackboard editing requires a /Game asset");
 const FString Op=Operation.ToLower(); if(Op!=TEXT("add") && Op!=TEXT("update") && Op!=TEXT("delete") && Op!=TEXT("settings")) throw std::runtime_error("Blackboard operation must be add, update, delete or settings");
 if(R.Category.Len()>128 || R.Description.Len()>4096) throw std::runtime_error("Category is limited to 128 and description to 4096 characters");
 const auto& Settings=R.TypeSettings;
 if(!R.bSetTypeSettings && (Settings.bSetDefault || Settings.bSetUseDefault || Settings.bSetBaseClass || Settings.bSetEnumType || Settings.bSetNativeEnumName)) throw std::runtime_error("bSetTypeSettings=true is required for typed key settings");
 if(R.bSetTypeSettings && (Op==TEXT("delete") || Op==TEXT("settings"))) throw std::runtime_error("Typed key settings apply only to key add/update");
 TStrongObjectPtr<UBlackboardKeyType> Prepared; bool SettingsChanged=false,CompatibilityChanged=false;
 auto Next=B->Keys; auto* Parent=B->Parent.Get(); int32 Index=INDEX_NONE; bool Rename=false,TypeChange=false,AddSelf=false;
 if(Op==TEXT("settings")) { if(!R.bSetParent) throw std::runtime_error("bSetParent=true is required; empty ParentPath clears the parent"); Parent=R.ParentPath.IsEmpty() ? nullptr : Load(R.ParentPath); }
 else
 {
  Name(R.KeyName); const FName Key(*R.KeyName); if(Key==FBlackboard::KeySelf) throw std::runtime_error("The native persistent SelfActor key is managed by the AI system");
  Index=Next.IndexOfByPredicate([&](const FBlackboardEntry& K){return K.EntryName==Key;});
  if(Op==TEXT("add")) { if(Index!=INDEX_NONE) throw std::runtime_error("A key with this name already exists"); FBlackboardEntry K; K.EntryName=Key; Index=Next.Add(K); }
  else if(Index==INDEX_NONE) throw std::runtime_error("A local key is required; inherited keys must be edited on their owner");
  if(Op==TEXT("delete")) Next.RemoveAt(Index);
  else
  {
   auto& K=Next[Index]; if(!R.NewKeyName.IsEmpty()) { Name(R.NewKeyName); if(FName(*R.NewKeyName)==FBlackboard::KeySelf) throw std::runtime_error("SelfActor is reserved"); Rename=K.EntryName!=FName(*R.NewKeyName); K.EntryName=FName(*R.NewKeyName); }
   if(Op==TEXT("add") || !R.KeyType.IsEmpty())
   {
    auto* Class=R.KeyType.IsEmpty() ? nullptr : LoadClass<UBlackboardKeyType>(nullptr,*R.KeyType);
    if(!Class || Class==UBlackboardKeyType::StaticClass() || Class->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("A concrete compatible Blackboard key type is required");
    TypeChange=!K.KeyType || K.KeyType->GetClass()!=Class;
    if(TypeChange) K.KeyType=Class->GetDefaultObject<UBlackboardKeyType>();
   }
   if(R.bSetCategory) K.EntryCategory=FName(*R.Category);
   if(R.bSetDescription) K.EntryDescription=R.Description;
   if(R.bSetInstanceSynced) K.bInstanceSynced=R.bInstanceSynced;
  }
 }
 if(R.bSetTypeSettings)
 {
  auto* Original=Next[Index].KeyType.Get();
  if(!IsValid(Original)) throw std::runtime_error("The local key has no valid type object; specify a compatible replacement KeyType");
  if(!TypeChange && Original->GetOuter()!=B) throw std::runtime_error("Key type settings require a key object owned by this Blackboard");
  Prepared=BlackboardKeySettingsUtils::Prepare(Original,R.TypeSettings);
  SettingsChanged=BlackboardKeySettingsUtils::Snapshot(Prepared.Get())!=BlackboardKeySettingsUtils::Snapshot(Original);
  CompatibilityChanged=BlackboardKeySettingsUtils::Compatibility(Prepared.Get())!=BlackboardKeySettingsUtils::Compatibility(Original);
 }
 const bool SetParent=Op==TEXT("settings");
 if(SetParent && Parent && GET_AI_CONFIG_VAR(bAddBlackboardSelfKey)) Next.RemoveAll([](const FBlackboardEntry& K){return K.EntryName==FBlackboard::KeySelf;});
 if(SetParent && !Parent && GET_AI_CONFIG_VAR(bAddBlackboardSelfKey) && !Next.ContainsByPredicate([](const FBlackboardEntry& K){return K.EntryName==FBlackboard::KeySelf;}))
 {
  FBlackboardEntry K; K.EntryName=FBlackboard::KeySelf; K.KeyType=GetMutableDefault<UBlackboardKeyType_Object>(); Next.Add(K); AddSelf=true;
 }
 auto ErrorsBefore=Errors(B,&Next,Parent,SetParent); if(!ErrorsBefore.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(ErrorsBefore,TEXT("; "))));
 bool Changed=SettingsChanged || Parent!=B->Parent || Next.Num()!=B->Keys.Num();
 if(!Changed) for(int32 I=0;I<Next.Num();++I) { const auto& A=Next[I]; const auto& V=B->Keys[I]; Changed|=!(A==V) || A.EntryCategory!=V.EntryCategory || A.EntryDescription!=V.EntryDescription || A.bInstanceSynced!=V.bInstanceSynced; }
 // Load before opening the transaction; Blueprint regeneration can otherwise pollute undo.
 auto All=Boards(); TArray<UBlackboardData*> Affected; for(auto* Child:All) if(Related(Child,B)) Affected.Add(Child);
 for(auto* Child:Affected) if(Child!=B)
 {
  const auto E=Errors(Child,&Next,Parent,SetParent,B);
  if(!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*(TEXT("Descendant Blackboard preflight: ")+FString::Join(E,TEXT("; ")))));
 }
 TArray<FName> References; for(auto* A:Affected) if(A!=B) References.AddUnique(A->GetOutermost()->GetFName());
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
 for(auto* A:Affected) { TArray<FName> Refs; Registry.GetReferencers(A->GetOutermost()->GetFName(),Refs,UE::AssetRegistry::EDependencyCategory::Package); for(FName V:Refs) References.AddUnique(V); }
 TArray<UBehaviorTree*> Trees; TArray<FAssetData> TreeAssets;
 Registry.GetAssetsByClass(UBehaviorTree::StaticClass()->GetClassPathName(),TreeAssets,true);
 if(TreeAssets.Num()>512) throw std::runtime_error("Behavior Tree dependency preflight exceeds 512 assets");
 for(const auto& A:TreeAssets) if(auto* T=Cast<UBehaviorTree>(A.GetAsset())) if(Related(T->GetBlackboardAsset(),B)) Trees.AddUnique(T);
 for(TObjectIterator<UBehaviorTree> It;It;++It) if(It->IsAsset() && Related(It->GetBlackboardAsset(),B)) Trees.AddUnique(*It);
 for(auto* T:Trees) References.AddUnique(T->GetOutermost()->GetFName());
 TArray<FString> Dependencies; for(FName V:References) Dependencies.Add(V.ToString()); Dependencies.Sort();
 const bool Structural=Rename || ((TypeChange || CompatibilityChanged) && Op!=TEXT("add")) || Op==TEXT("delete") || SetParent;
 if(Changed && Structural && !Dependencies.IsEmpty() && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Structural edits with referencers require bConfirm=true; dry-run reports referencer_packages");
 TArray<TPair<UObject*,FBlackboardKeySelector*>> Selectors; TMap<UObject*,UBlackboardData*> SelectorBoards;
 if(Rename) for(auto* T:Trees)
 {
  TArray<UObject*> Objects; GetObjectsWithOuter(T->GetOutermost(),Objects,true); Objects.AddUnique(T);
  for(auto* O:Objects) for(TFieldIterator<FStructProperty> It(O->GetClass());It;++It) if(It->Struct==FBlackboardKeySelector::StaticStruct())
  {
   auto* S=It->ContainerPtrToValuePtr<FBlackboardKeySelector>(O); if(S->SelectedKeyName==FName(*R.KeyName)) { Selectors.Add({O,S}); SelectorBoards.Add(O,T->GetBlackboardAsset()); }
  }
 }
 TArray<FString> Updated; for(const auto& Pair:Selectors) Updated.AddUnique(Pair.Key->GetPathName());
 if(Changed && !R.bDryRun)
 {
  FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","BlackboardEdit","Edit Blackboard"));
  B->SetFlags(RF_Transactional); B->Modify();
  B->PreEditChange(nullptr);
  if(Op!=TEXT("delete") && !SetParent && TypeChange) Next[Index].KeyType=NewObject<UBlackboardKeyType>(B,Next[Index].KeyType->GetClass(),NAME_None,RF_Transactional);
  if(Prepared.IsValid() && (SettingsChanged || TypeChange))
  {
   auto* K=Next[Index].KeyType.Get(); K->SetFlags(RF_Transactional); K->Modify(); K->PreEditChange(nullptr); BlackboardKeySettingsUtils::Copy(K,Prepared.Get());
  }
  if(AddSelf) Next.RemoveAll([](const FBlackboardEntry& K){return K.EntryName==FBlackboard::KeySelf;});
  B->Parent=Parent; B->Keys=Next;
  B->UpdateParentKeys(); B->UpdateIfHasSynchronizedKeys();
  auto* Property=FindFProperty<FProperty>(UBlackboardData::StaticClass(),SetParent ? TEXT("Parent") : TEXT("Keys"));
  FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); Event.MemberProperty=FindFProperty<FProperty>(UBlackboardData::StaticClass(),TEXT("Keys")); B->PostEditChangeProperty(Event);
  for(const auto& Pair:Selectors) { Pair.Key->SetFlags(RF_Transactional); Pair.Key->Modify(); Pair.Value->SelectedKeyName=FName(*R.NewKeyName); Pair.Value->ResolveSelectedKey(*SelectorBoards[Pair.Key]); Pair.Key->MarkPackageDirty(); }
  B->MarkPackageDirty();
  for(auto* A:Affected) Tracked.Add(A,Signature(A));
  if(!Undo.IsValid()) Undo=FEditorDelegates::PostUndoRedo.AddStatic(&AfterUndo);
 }
 bool Saved=false;
 if(R.bSave && !R.bDryRun)
 {
  auto* Assets=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>(); Saved=Assets->SaveLoadedAsset(B,false);
  if(!Saved) throw std::runtime_error("Blackboard changed but save failed");
  TSet<UPackage*> Renamed; for(const auto& Pair:Selectors) Renamed.Add(Pair.Key->GetOutermost());
  for(auto* T:Trees) if(Renamed.Contains(T->GetOutermost()) && !Assets->SaveLoadedAsset(T,false)) throw std::runtime_error("Blackboard saved but a renamed-selector Behavior Tree failed to save");
 }
 return Json(B,Changed,R.bDryRun,Saved,Dependencies,Updated);
}
