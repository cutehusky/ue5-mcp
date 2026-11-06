#include "RemoteControlUtils.h"
#include "UE5_MCP/API/DTO/RemoteControlReq.h"
#include "RemoteControlPreset.h"
#include "RemoteControlField.h"
#include "RemoteControlFieldPath.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Editor.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
 void RequireStoppedEditor()
 {
  if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("Remote Control edits require a stopped play session");
 }
 FString ObjectPathOf(const FString& Input)
 {
  const FString Package=FPackageName::ObjectPathToPackageName(Input);
  if(Input.Len()>1024 || !Package.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(Package)) throw std::runtime_error("Preset requires a bounded /Game asset path");
  return Input.Contains(TEXT(".")) ? Input : Package+TEXT(".")+FPackageName::GetLongPackageAssetName(Package);
 }
 URemoteControlPreset* LoadPreset(const FString& Input)
 {
  const FString Path=ObjectPathOf(Input);
  if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(Path)).IsValid()) throw std::runtime_error("Preset must exist in the asset registry");
  auto* Preset=LoadObject<URemoteControlPreset>(nullptr,*Path); if(!Preset) throw std::runtime_error("Asset is not a Remote Control Preset");
  return Preset;
 }
 bool SavePreset(URemoteControlPreset* Preset,const FRemoteControlReq& R)
 {
  if(!R.bSave || R.bDryRun) return false;
  if(!GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Preset,false)) throw std::runtime_error("Preset changed but its save failed");
  return true;
 }
 // Only plain field paths: resolved array-element addresses are not property containers.
 bool ResolveValue(UObject* Object,const FRCFieldPathInfo& Source,FProperty*& Property,void*& Address)
 {
  FRCFieldPathInfo Path=Source; if(!Object || Path.ToString().Contains(TEXT("[")) || !Path.Resolve(Object)) return false;
  const FRCFieldResolvedData Data=Path.GetResolvedData(); Property=CastField<FProperty>(Data.Field); if(!Property || !Data.ContainerAddress) return false;
  Address=Property->ContainerPtrToValuePtr<void>(Data.ContainerAddress); return true;
 }
 FString ValueText(FProperty* Property,const void* Address)
 {
  FString Text; Property->ExportTextItem_Direct(Text,Address,nullptr,nullptr,PPF_None); return Text;
 }
 TSharedPtr<FRemoteControlField> FindField(URemoteControlPreset* Preset,const FString& EntityId,const FString& ExpectedLabel)
 {
  FGuid Id; if(!FGuid::Parse(EntityId,Id)) throw std::runtime_error("EntityId requires a GUID");
  TSharedPtr<FRemoteControlField> Field=Preset->GetExposedEntity<FRemoteControlField>(Id).Pin();
  if(!Field) throw std::runtime_error("Entity is not an exposed property or function of this preset");
  if(Field->GetLabel().ToString()!=ExpectedLabel) throw std::runtime_error("ExpectedLabel stale guard failed");
  return Field;
 }
 void WriteResult(TSharedRef<TJsonWriter<>> J,const FRemoteControlReq& R,bool Changed,bool Saved)
 {
  J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved);
 }
}

FString RemoteControlUtils::List(const FString& Search,int32 Limit)
{
 if(!IsInGameThread() || Limit<1 || Limit>1000 || Search.Len()>128) throw std::runtime_error("Preset listing requires bounded search and limit 1-1000");
 TArray<FAssetData> Assets; FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetsByClass(URemoteControlPreset::StaticClass()->GetClassPathName(),Assets,true);
 Assets.RemoveAll([&](const FAssetData& A){ return !Search.IsEmpty() && !A.GetObjectPathString().Contains(Search); });
 Assets.Sort([](const FAssetData& A,const FAssetData& B){ return A.GetObjectPathString()<B.GetObjectPathString(); });
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("total"),Assets.Num()); J->WriteValue(TEXT("truncated"),Assets.Num()>Limit); J->WriteArrayStart(TEXT("presets"));
 for(int32 Index=0;Index<FMath::Min(Assets.Num(),Limit);++Index) J->WriteValue(Assets[Index].GetObjectPathString());
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Result;
}

FString RemoteControlUtils::Inspect(const FString& AssetPath)
{
 if(!IsInGameThread()) throw std::runtime_error("Preset inspection requires the game thread");
 auto* Preset=LoadPreset(AssetPath); const auto Fields=Preset->GetExposedEntities<FRemoteControlField>();
 TArray<TSharedPtr<const FRemoteControlField>> Rows; for(const auto& Weak:Fields) if(auto Field=Weak.Pin()) Rows.Add(Field);
 Rows.Sort([](const auto& A,const auto& B){ return A->GetLabel().LexicalLess(B->GetLabel()); });
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Preset->GetPathName()); J->WriteValue(TEXT("preset_id"),Preset->GetPresetId().ToString()); J->WriteValue(TEXT("dirty"),Preset->GetOutermost()->IsDirty()); J->WriteValue(TEXT("entity_count"),Rows.Num()); J->WriteArrayStart(TEXT("entities"));
 for(const auto& Field:Rows)
 {
  J->WriteObjectStart(); J->WriteValue(TEXT("id"),Field->GetId().ToString()); J->WriteValue(TEXT("label"),Field->GetLabel().ToString()); J->WriteValue(TEXT("field_name"),Field->FieldName.ToString()); J->WriteValue(TEXT("field_path"),Field->FieldPathInfo.ToString());
  const TArray<UObject*> Bound=Field->GetBoundObjects(); J->WriteValue(TEXT("bound"),!Bound.IsEmpty()); J->WriteArrayStart(TEXT("bound_objects")); for(const auto* Object:Bound) if(Object) J->WriteValue(Object->GetPathName()); J->WriteArrayEnd();
  if(Field->FieldType==EExposedFieldType::Function) { J->WriteValue(TEXT("kind"),TEXT("function")); const UFunction* Native=StaticCastSharedPtr<const FRemoteControlFunction>(Field)->GetFunction(); J->WriteValue(TEXT("function"),Native ? Native->GetPathName() : FString()); }
  else
  {
   J->WriteValue(TEXT("kind"),TEXT("property")); FProperty* Property=nullptr; void* Address=nullptr; const bool Readable=!Bound.IsEmpty() && ResolveValue(Bound[0],Field->FieldPathInfo,Property,Address);
   J->WriteValue(TEXT("value_available"),Readable); if(Readable) { J->WriteValue(TEXT("type"),Property->GetCPPType()); const FString Text=ValueText(Property,Address); J->WriteValue(TEXT("value_truncated"),Text.Len()>4096); J->WriteValue(TEXT("value"),Text.Left(4096)); }
  }
  J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Exposed properties and functions; bound objects resolve only while their world or asset is loaded. Exposed actors and protocol bindings are not listed.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString RemoteControlUtils::Create(const FRemoteControlReq& R)
{
 RequireStoppedEditor(); if(!R.bConfirm) throw std::runtime_error("Preset creation requires confirmation");
 const FString Path=ObjectPathOf(R.AssetPath); const FString PackageName=FPackageName::ObjectPathToPackageName(Path); const FString Name=FPackageName::GetLongPackageAssetName(PackageName);
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
 if(Registry.GetAssetByObjectPath(FSoftObjectPath(Path)).IsValid() || FindPackage(nullptr,*PackageName) || FPackageName::DoesPackageExist(PackageName)) throw std::runtime_error("Preset destination already exists");
 bool Saved=false;
 if(!R.bDryRun)
 {
  UPackage* Package=CreatePackage(*PackageName); auto* Preset=NewObject<URemoteControlPreset>(Package,*Name,RF_Public|RF_Standalone|RF_Transactional);
  FAssetRegistryModule::AssetCreated(Preset); Package->MarkPackageDirty(); Saved=SavePreset(Preset,R);
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Path); WriteResult(J,R,true,Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString RemoteControlUtils::Expose(const FRemoteControlReq& R)
{
 RequireStoppedEditor(); if(!R.bConfirm) throw std::runtime_error("Exposing requires confirmation");
 if(R.ObjectPath.IsEmpty() || R.ObjectPath.Len()>1024 || R.FieldPath.IsEmpty() || R.FieldPath.Len()>512 || R.Label.Len()>128) throw std::runtime_error("Exposing requires bounded object path, field path and label");
 auto* Preset=LoadPreset(R.AssetPath);
 if(R.ExpectedEntityCount!=Preset->GetExposedEntities<FRemoteControlField>().Num()) throw std::runtime_error("ExpectedEntityCount stale guard failed");
 UObject* Object=FindObject<UObject>(nullptr,*R.ObjectPath); if(!Object) Object=LoadObject<UObject>(nullptr,*R.ObjectPath);
 if(!IsValid(Object) || Object->HasAnyFlags(RF_Transient|RF_ClassDefaultObject) || Object->GetOutermost()==GetTransientPackage() || Object->GetOutermost()->HasAnyPackageFlags(PKG_PlayInEditor)) throw std::runtime_error("Exposed object must be a loaded persistent editor object");
 if(!R.Label.IsEmpty() && Preset->GetExposedEntityId(FName(*R.Label)).IsValid()) throw std::runtime_error("Label is already used by this preset");
 UFunction* Function=nullptr; FRCFieldPathInfo Path(R.FieldPath);
 if(R.Kind==TEXT("function")) { Function=Object->FindFunction(FName(*R.FieldPath)); if(!Function || !Function->HasAnyFunctionFlags(FUNC_BlueprintCallable)) throw std::runtime_error("Function must exist on the object and be BlueprintCallable"); }
 else if(R.Kind==TEXT("property")) { FProperty* Property=nullptr; void* Address=nullptr; if(!ResolveValue(Object,Path,Property,Address)) throw std::runtime_error("Field path does not resolve to a plain property of the object"); if(!Property->HasAnyPropertyFlags(CPF_Edit) || Property->HasAnyPropertyFlags(CPF_Transient)) throw std::runtime_error("Only editable non-transient properties can be exposed"); }
 else throw std::runtime_error("Kind requires property or function");
 FString Id,Label; bool Saved=false;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Expose Remote Control Field"))); Preset->Modify();
  FRemoteControlPresetExposeArgs Args; if(!R.Label.IsEmpty()) Args.Label=R.Label;
  TSharedPtr<FRemoteControlField> Field; if(Function) Field=Preset->ExposeFunction(Object,Function,Args).Pin(); else Field=Preset->ExposeProperty(Object,Path,Args).Pin();
  if(!Field) { Transaction.Cancel(); throw std::runtime_error("Native preset refused to expose the field"); }
  Id=Field->GetId().ToString(); Label=Field->GetLabel().ToString(); Preset->MarkPackageDirty(); Saved=SavePreset(Preset,R);
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Preset->GetPathName()); J->WriteValue(TEXT("id"),Id); J->WriteValue(TEXT("label"),Label); WriteResult(J,R,true,Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString RemoteControlUtils::Unexpose(const FRemoteControlReq& R)
{
 RequireStoppedEditor(); if(!R.bConfirm) throw std::runtime_error("Unexposing requires confirmation");
 auto* Preset=LoadPreset(R.AssetPath); const FGuid Id=FindField(Preset,R.EntityId,R.ExpectedLabel)->GetId(); bool Saved=false;
 if(!R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Unexpose Remote Control Field"))); Preset->Modify(); Preset->Unexpose(Id); Preset->MarkPackageDirty(); Saved=SavePreset(Preset,R); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Preset->GetPathName()); J->WriteValue(TEXT("id"),R.EntityId); WriteResult(J,R,true,Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString RemoteControlUtils::SetValue(const FRemoteControlReq& R)
{
 RequireStoppedEditor(); if(!R.bConfirm) throw std::runtime_error("Value edits require confirmation"); if(R.Value.Len()>65536) throw std::runtime_error("Value text is limited to 64KiB");
 auto* Preset=LoadPreset(R.AssetPath); const auto Field=FindField(Preset,R.EntityId,R.ExpectedLabel);
 if(Field->FieldType!=EExposedFieldType::Property) throw std::runtime_error("Only exposed properties have values");
 const TArray<UObject*> Bound=Field->GetBoundObjects(); if(Bound.IsEmpty()) throw std::runtime_error("Entity has no loaded bound object");
 // Validate every bound object against the stale guard and a scratch import before anything mutates.
 struct FTarget { UObject* Object; FProperty* Property; void* Address; }; TArray<FTarget> Targets; bool Changed=false; TArray<uint8> Scratch;
 for(UObject* Object:Bound)
 {
  FProperty* Property=nullptr; void* Address=nullptr; if(!ResolveValue(Object,Field->FieldPathInfo,Property,Address)) throw std::runtime_error("Bound object no longer resolves the field path");
  if(Property->HasAnyPropertyFlags(CPF_EditConst)) throw std::runtime_error("Property is read-only");
  if(ValueText(Property,Address)!=R.ExpectedValue) throw std::runtime_error("ExpectedValue stale guard failed");
  Scratch.SetNumZeroed(Property->GetElementSize()); Property->InitializeValue(Scratch.GetData()); const TCHAR* End=Property->ImportText_Direct(*R.Value,Scratch.GetData(),nullptr,PPF_None,GWarn);
  const bool Valid=End && !*End; if(Valid) Changed|=!Property->Identical(Scratch.GetData(),Address,PPF_None); Property->DestroyValue(Scratch.GetData()); if(!Valid) throw std::runtime_error("Value text does not import into the property");
  Targets.Add({Object,Property,Address});
 }
 if(Changed && !R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Remote Control Value")));
  for(const auto& T:Targets) { T.Object->Modify(); T.Object->PreEditChange(T.Property); T.Property->ImportText_Direct(*R.Value,T.Address,T.Object,PPF_None); FPropertyChangedEvent Event(T.Property,EPropertyChangeType::ValueSet); T.Object->PostEditChangeProperty(Event); T.Object->MarkPackageDirty(); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Preset->GetPathName()); J->WriteValue(TEXT("id"),R.EntityId); J->WriteValue(TEXT("bound_object_count"),Targets.Num()); WriteResult(J,R,Changed,false); J->WriteValue(TEXT("scope"),TEXT("Writes the bound objects, not the preset; they are marked dirty and saved through their own map or asset.")); J->WriteObjectEnd(); J->Close(); return Result;
}
