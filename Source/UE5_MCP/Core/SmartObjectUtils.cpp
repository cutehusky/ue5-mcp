#include "SmartObjectUtils.h"
#include "UE5_MCP/API/DTO/EditorExtReq.h"
#include "SmartObjectDefinition.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"
#include "Editor.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace {
FArrayProperty* SlotsProperty(USmartObjectDefinition* D) { auto* P=FindFProperty<FArrayProperty>(USmartObjectDefinition::StaticClass(),TEXT("Slots")); if(!P || !CastField<FStructProperty>(P->Inner)) throw std::runtime_error("Native Smart Object Slots array unavailable"); return P; }
FString State(USmartObjectDefinition* D) {
 FArrayProperty* P=SlotsProperty(D); auto* Inner=CastField<FStructProperty>(P->Inner); FScriptArrayHelper Slots(P,P->ContainerPtrToValuePtr<void>(D));
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("definition"),D->GetPathName()); J->WriteValue(TEXT("slot_struct"),Inner->Struct->GetPathName()); J->WriteArrayStart(TEXT("slots"));
 for(int32 I=0;I<Slots.Num();++I) { FString Text; Inner->ExportTextItem_Direct(Text,Slots.GetRawPtr(I),nullptr,D,PPF_None); J->WriteValue(Text); }
 J->WriteArrayEnd();
 // Native slot text export omits bEnabled, so report it per slot to keep it under the snapshot guard.
 if(auto* Enabled=CastField<FBoolProperty>(Inner->Struct->FindPropertyByName(TEXT("bEnabled")))) { J->WriteArrayStart(TEXT("slot_enabled")); for(int32 I=0;I<Slots.Num();++I) J->WriteValue(Enabled->GetPropertyValue_InContainer(Slots.GetRawPtr(I))); J->WriteArrayEnd(); }
 TArray<FProperty*> Props; for(TFieldIterator<FProperty> It(USmartObjectDefinition::StaticClass());It;++It) if(It->GetFName()!=TEXT("Slots") && It->HasAnyPropertyFlags(CPF_Edit)) Props.Add(*It); Props.Sort([](const FProperty& A,const FProperty& B){ return A.GetName()<B.GetName(); });
 J->WriteObjectStart(TEXT("settings")); for(FProperty* Prop:Props) { FString Text; Prop->ExportTextItem_Direct(Text,Prop->ContainerPtrToValuePtr<void>(D),nullptr,D,PPF_None); J->WriteValue(Prop->GetName(),Text.Left(4096)); } J->WriteObjectEnd();
 J->WriteObjectEnd(); J->Close(); return Json;
}
USmartObjectDefinition* Resolve(const FString& Path) {
 if(Path.IsEmpty() || Path.Len()>1024) throw std::runtime_error("Bounded Smart Object definition path required");
 auto* D=LoadObject<USmartObjectDefinition>(nullptr,*Path); if(!IsValid(D) || !D->IsAsset() || D->HasAnyFlags(RF_Transient) || D->GetPathName()!=Path) throw std::runtime_error("Exact persistent Smart Object definition required"); return D;
}
void ImportField(UScriptStruct* Struct,void* Slot,const FString& Field,const FString& Text,UObject* Owner) {
 static const TSet<FString> Allowed={TEXT("Name"),TEXT("Offset"),TEXT("Rotation"),TEXT("bEnabled"),TEXT("ActivityTags"),TEXT("UserTagFilter"),TEXT("RuntimeTags"),TEXT("Color"),TEXT("SelectionPreconditions")};
 if(!Allowed.Contains(Field)) throw std::runtime_error("Slot field must be Name, Offset, Rotation, bEnabled, ActivityTags, UserTagFilter, RuntimeTags, Color or SelectionPreconditions");
 if(Text.Len()>16384) throw std::runtime_error("Slot field text<=16KiB required");
 FProperty* Prop=Struct->FindPropertyByName(FName(*Field)); if(!Prop && Field==TEXT("Color")) Prop=Struct->FindPropertyByName(TEXT("DEBUG_DrawColor")); /* 5.x editor-only slot colour */ if(!Prop) throw std::runtime_error("Slot field not present in this engine's slot struct");
 if(!Prop->ImportText_Direct(*Text,Prop->ContainerPtrToValuePtr<void>(Slot),Owner,PPF_None)) throw std::runtime_error("Native ImportText rejected slot field value");
}
void Notify(USmartObjectDefinition* D) { FPropertyChangedEvent Event(SlotsProperty(D),EPropertyChangeType::ValueSet); D->PostEditChangeProperty(Event); D->MarkPackageDirty(); }
}
FString SmartObjectUtils::Definition(const FEditorExtReq& R) {
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("Stopped editor on game thread required");
 const FString Op=R.Operation; bool Changed=false; USmartObjectDefinition* D=nullptr;
 if(Op==TEXT("Create")) {
  if(!R.bConfirm || R.AssetPath.Len()>1024 || !FPackageName::IsValidObjectPath(R.AssetPath)) throw std::runtime_error("Confirmation and valid new object path /Game/Path/Name.Name required");
  const FString Package=FPackageName::ObjectPathToPackageName(R.AssetPath),Name=FPackageName::ObjectPathToObjectName(R.AssetPath); if(Name!=FPackageName::GetShortName(Package) || !Package.StartsWith(TEXT("/Game/"))) throw std::runtime_error("Object name must match package short name under /Game");
  if(FindPackage(nullptr,*Package) || FPackageName::DoesPackageExist(Package)) throw std::runtime_error("Destination package already exists");
  Changed=true; if(!R.bDryRun) { UPackage* P=CreatePackage(*Package); D=NewObject<USmartObjectDefinition>(P,FName(*Name),RF_Public|RF_Standalone|RF_Transactional); FAssetRegistryModule::AssetCreated(D); D->MarkPackageDirty(); }
 } else {
  D=Resolve(R.AssetPath); const FString Before=State(D);
  if(Op!=TEXT("Inspect")) {
   if(!GEditor->Trans || !R.bConfirm || R.ExpectedSnapshot!=Before) throw std::runtime_error("Confirmation and exact full definition snapshot required");
   FArrayProperty* P=SlotsProperty(D); UScriptStruct* Struct=CastField<FStructProperty>(P->Inner)->Struct; FScriptArrayHelper Slots(P,P->ContainerPtrToValuePtr<void>(D));
   if(Op==TEXT("AddSlot")) { if(Slots.Num()>=255) throw std::runtime_error("Slot budget255 reached"); Changed=true;
    TArray<uint8> Scratch; Scratch.SetNumZeroed(Struct->GetStructureSize()); Struct->InitializeStruct(Scratch.GetData()); if(!R.Name.IsEmpty()) ImportField(Struct,Scratch.GetData(),TEXT("Name"),R.Name,D); if(!R.TextValue.IsEmpty()) ImportField(Struct,Scratch.GetData(),TEXT("Offset"),R.TextValue,D); Struct->DestroyStruct(Scratch.GetData());
    if(!R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Add Smart Object Slot"))); D->Modify(); const int32 I=Slots.AddValue(); void* Slot=Slots.GetRawPtr(I); if(FStructProperty* Id=CastField<FStructProperty>(Struct->FindPropertyByName(TEXT("ID")))) if(Id->Struct==TBaseStructure<FGuid>::Get()) *Id->ContainerPtrToValuePtr<FGuid>(Slot)=FGuid::NewGuid(); if(!R.Name.IsEmpty()) ImportField(Struct,Slot,TEXT("Name"),R.Name,D); if(!R.TextValue.IsEmpty()) ImportField(Struct,Slot,TEXT("Offset"),R.TextValue,D); Notify(D); } }
   else if(Op==TEXT("SetSlot") || Op==TEXT("RemoveSlot")) { if(R.Index<0 || R.Index>=Slots.Num()) throw std::runtime_error("Valid slot index required");
    if(Op==TEXT("RemoveSlot")) { if(!R.bAllow) throw std::runtime_error("Slot removal shifts indices and may break runtime claims/annotations; bAllow required"); Changed=true; if(!R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Remove Smart Object Slot"))); D->Modify(); Slots.RemoveValues(R.Index,1); Notify(D); } }
    else { TArray<uint8> Scratch; Scratch.SetNumZeroed(Struct->GetStructureSize()); Struct->InitializeStruct(Scratch.GetData()); Struct->CopyScriptStruct(Scratch.GetData(),Slots.GetRawPtr(R.Index)); ImportField(Struct,Scratch.GetData(),R.FieldName,R.TextValue,D); Changed=!Struct->CompareScriptStruct(Scratch.GetData(),Slots.GetRawPtr(R.Index),PPF_None);
     if(Changed && !R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Edit Smart Object Slot"))); D->Modify(); Struct->CopyScriptStruct(Slots.GetRawPtr(R.Index),Scratch.GetData()); Notify(D); } Struct->DestroyStruct(Scratch.GetData()); } }
   else throw std::runtime_error("Operation must be Inspect, Create, AddSlot, SetSlot or RemoveSlot");
  }
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("operation"),Op); J->WriteValue(TEXT("asset_path"),R.AssetPath); if(D) { J->WriteValue(TEXT("snapshot"),State(D)); J->WriteValue(TEXT("native_valid"),D->Validate()); } J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("written"),Changed && !R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun);
 J->WriteValue(TEXT("scope"),TEXT("Smart Object definition Inspect/Create/AddSlot/SetSlot/RemoveSlot. Snapshot exports native slot structs and editable definition settings (each<=4KiB). Create makes a new /Game package asset without saving. Slot edits use reflected Slots array, allowlisted slot fields through native ImportText, fresh editor slot GUIDs, transactions, PostEditChangeProperty and dirty marking; RemoveSlot requires bAllow. Behavior definitions, world conditions, annotations and placed components are not authored. native_valid is USmartObjectDefinition::Validate(). Unverified."));
 J->WriteObjectEnd(); J->Close(); return Json;
}
