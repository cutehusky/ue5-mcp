#include "GameCoreUtils.h"
#include "UE5_MCP/API/DTO/GameCoreReq.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetImportTask.h"
#include "AssetToolsModule.h"
#include "Engine/SkeletalMesh.h"
#include "Factories/FbxFactory.h"
#include "Factories/FbxImportUI.h"
#include "HAL/FileManager.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Engine/DataTable.h"
#include "StructUtils/UserDefinedStruct.h"
#include "Factories/AnimBlueprintFactory.h"
#include "Factories/AnimMontageFactory.h"
#include "Factories/BlendSpaceFactory1D.h"
#include "Factories/BlendSpaceFactoryNew.h"
#include "Factories/CurveFactory.h"
#include "Factories/DataTableFactory.h"
#include "Factories/MaterialFactoryNew.h"
#include "Factories/MaterialInstanceConstantFactoryNew.h"
#include "Factories/PhysicalMaterialFactoryNew.h"
#include "Materials/MaterialInterface.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameMapsSettings.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "HAL/PlatformProcess.h"
#include "InputKeyEventArgs.h"
#include "InputCoreTypes.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
 UBlueprint* LoadBlueprintAsset(const FString& Input)
 {
  const FString Package=FPackageName::ObjectPathToPackageName(Input);
  if(Input.Len()>1024 || !Package.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(Package)) throw std::runtime_error("Class defaults require a /Game Blueprint path");
  const FString Path=Input.Contains(TEXT(".")) ? Input : Package+TEXT(".")+FPackageName::GetLongPackageAssetName(Package);
  auto* Blueprint=LoadObject<UBlueprint>(nullptr,*Path); if(!Blueprint || !Blueprint->GeneratedClass) throw std::runtime_error("Asset must be a compiled Blueprint");
  return Blueprint;
 }
 FString ValueText(const FProperty* Property,const void* Address,UObject* Owner=nullptr)
 {
  FString Text; Property->ExportTextItem_Direct(Text,Address,nullptr,Owner,PPF_None); return Text;
 }
 bool IsLeafEditable(const FProperty* Property)
 {
  return Property->HasAnyPropertyFlags(CPF_Edit) && !Property->HasAnyPropertyFlags(CPF_EditConst|CPF_DisableEditOnTemplate|CPF_Transient|CPF_Deprecated);
 }
 struct FResolved { UObject* Owner=nullptr; FProperty* Property=nullptr; void* Address=nullptr; };
 // Walks "Field", "Struct.Field" and "DefaultSubobject.Field" from a class default object. Only default subobjects owned by
 // the CDO are entered, so edits never reach shared assets; components added in the Blueprint live in its SCS instead.
 FResolved ResolvePath(UObject* Defaults,const FString& Path)
 {
  TArray<FString> Parts; Path.ParseIntoArray(Parts,TEXT("."),true); if(Parts.IsEmpty() || Parts.Num()>16) throw std::runtime_error("PropertyPath requires 1-16 segments");
  UObject* Owner=Defaults; UStruct* Type=Defaults->GetClass(); void* Container=Defaults;
  for(int32 Index=0;Index<Parts.Num();++Index)
  {
   FProperty* Property=FindFProperty<FProperty>(Type,*Parts[Index]);
   if(!Property || Property->ArrayDim!=1) throw std::runtime_error("PropertyPath segment does not exist; components added in this Blueprint are edited with set_component_property");
   void* Address=Property->ContainerPtrToValuePtr<void>(Container);
   if(Index==Parts.Num()-1) { FResolved R; R.Owner=Owner; R.Property=Property; R.Address=Address; return R; }
   if(auto* Struct=CastField<FStructProperty>(Property)) { Type=Struct->Struct; Container=Address; continue; }
   auto* ObjectProperty=CastField<FObjectPropertyBase>(Property); UObject* Sub=ObjectProperty ? ObjectProperty->GetObjectPropertyValue(Address) : nullptr;
   if(!Sub || Sub->GetOuter()!=Owner || !Sub->IsDefaultSubobject()) throw std::runtime_error("PropertyPath may only enter structs and default subobjects");
   Owner=Sub; Type=Sub->GetClass(); Container=Sub;
  }
  throw std::runtime_error("PropertyPath is empty");
 }
 // Imports into scratch storage so a bad value never touches the target; returns whether it differs from Address.
 bool PreflightImport(const FProperty* Property,const FString& Value,const void* Address,UObject* Owner)
 {
  TArray<uint8> Scratch; Scratch.SetNumZeroed(Property->GetElementSize()); Property->InitializeValue(Scratch.GetData());
  const TCHAR* End=Property->ImportText_Direct(*Value,Scratch.GetData(),Owner,PPF_None,GWarn);
  const bool Valid=End && !*End; const bool Changed=Valid && !Property->Identical(Scratch.GetData(),Address,PPF_None); Property->DestroyValue(Scratch.GetData());
  if(!Valid) throw std::runtime_error("Value text does not import into the property");
  return Changed;
 }
 const TCHAR* const GGameSettings[]={TEXT("GameDefaultMap"),TEXT("EditorStartupMap"),TEXT("GlobalDefaultGameMode"),TEXT("GameInstanceClass")};
 UWorld* RequirePlayWorld()
 {
  if(!IsInGameThread() || !GEditor || !GEditor->PlayWorld) throw std::runtime_error("This requires a running play session; call start_play_in_editor first");
  return GEditor->PlayWorld;
 }
 void WriteVector(TSharedRef<TJsonWriter<>> J,const TCHAR* Name,const FVector& V)
 {
  J->WriteArrayStart(Name); J->WriteValue(V.X); J->WriteValue(V.Y); J->WriteValue(V.Z); J->WriteArrayEnd();
 }
 struct FPackageJob { FProcHandle Handle; FString LogFile,OutputDir,Platform,Configuration; bool bStarted=false,bCancelled=false; int32 ExitCode=-1; bool bExitKnown=false; };
 FPackageJob GPackage;
 bool RefreshPackage()
 {
  if(!GPackage.bStarted || GPackage.bExitKnown) return false;
  if(FPlatformProcess::IsProcRunning(GPackage.Handle)) return true;
  int32 Code=-1; FPlatformProcess::GetProcReturnCode(GPackage.Handle,&Code); GPackage.ExitCode=Code; GPackage.bExitKnown=true; FPlatformProcess::CloseProc(GPackage.Handle); return false;
 }
}

namespace
{
 template<typename T> T* LoadInput(const FString& Input,const char* Error)
 {
  const FString Path=Input.Contains(TEXT(".")) ? Input : Input+TEXT(".")+FPackageName::GetLongPackageAssetName(Input);
  T* Object=Input.Len()<=1024 && !Input.IsEmpty() ? LoadObject<T>(nullptr,*Path) : nullptr; if(!Object) throw std::runtime_error(Error);
  return Object;
 }
}

FString GameCoreUtils::CreateAsset(const FGameCoreReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("Asset creation requires stopped PIE");
 if(R.AssetPath.Len()>1024 || R.AssetPath.Contains(TEXT(".")) || !R.AssetPath.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(R.AssetPath)) throw std::runtime_error("asset_path must be an unused /Game package path such as /Game/Materials/M_Rock");
 const bool bAnimation=R.Kind==TEXT("montage"); const bool bSkeletal=R.Kind==TEXT("anim_blueprint") || R.Kind==TEXT("blend_space") || R.Kind==TEXT("blend_space_1d");
 if(!R.ParentPath.IsEmpty() && R.Kind!=TEXT("material_instance")) throw std::runtime_error("parent_path applies only to material_instance");
 if(!R.StructPath.IsEmpty() && R.Kind!=TEXT("data_table")) throw std::runtime_error("struct_path applies only to data_table");
 if(!R.SkeletonPath.IsEmpty() && !bSkeletal) throw std::runtime_error("skeleton_path applies only to anim_blueprint, blend_space and blend_space_1d");
 if(!R.AnimationPath.IsEmpty() && !bAnimation) throw std::runtime_error("animation_path applies only to montage");
 UFactory* Factory=nullptr; USkeleton* Skeleton=bSkeletal ? LoadInput<USkeleton>(R.SkeletonPath,"skeleton_path must name a Skeleton") : nullptr;
 if(R.Kind==TEXT("material")) Factory=NewObject<UMaterialFactoryNew>();
 else if(R.Kind==TEXT("material_instance")) { auto* F=NewObject<UMaterialInstanceConstantFactoryNew>(); F->InitialParent=LoadInput<UMaterialInterface>(R.ParentPath,"parent_path must name a Material or Material Instance"); Factory=F; }
 else if(R.Kind==TEXT("data_table"))
 {
  auto* Struct=LoadInput<UScriptStruct>(R.StructPath,"struct_path must name a row struct such as /Script/GameplayTags.GameplayTagTableRow");
  if(!Struct->IsChildOf(FTableRowBase::StaticStruct()) && !Cast<UUserDefinedStruct>(Struct)) throw std::runtime_error("struct_path must derive from FTableRowBase or be a User Defined Struct");
  auto* F=NewObject<UDataTableFactory>(); F->Struct=Struct; Factory=F;
 }
 else if(R.Kind==TEXT("curve_float")) Factory=NewObject<UCurveFloatFactory>();
 else if(R.Kind==TEXT("curve_vector")) Factory=NewObject<UCurveVectorFactory>();
 else if(R.Kind==TEXT("curve_linear_color")) Factory=NewObject<UCurveLinearColorFactory>();
 else if(R.Kind==TEXT("anim_blueprint")) { auto* F=NewObject<UAnimBlueprintFactory>(); F->TargetSkeleton=Skeleton; Factory=F; }
 else if(R.Kind==TEXT("blend_space")) { auto* F=NewObject<UBlendSpaceFactoryNew>(); F->TargetSkeleton=Skeleton; Factory=F; }
 else if(R.Kind==TEXT("blend_space_1d")) { auto* F=NewObject<UBlendSpaceFactory1D>(); F->TargetSkeleton=Skeleton; Factory=F; }
 else if(bAnimation) { auto* F=NewObject<UAnimMontageFactory>(); F->SourceAnimation=LoadInput<UAnimSequence>(R.AnimationPath,"animation_path must name an Animation Sequence"); F->TargetSkeleton=F->SourceAnimation->GetSkeleton(); Factory=F; }
 else if(R.Kind==TEXT("physical_material")) Factory=NewObject<UPhysicalMaterialFactoryNew>();
 else throw std::runtime_error("kind must be material, material_instance, data_table, curve_float, curve_vector, curve_linear_color, anim_blueprint, blend_space, blend_space_1d, montage or physical_material");
 TArray<FAssetData> Existing; FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get().GetAssetsByPackageName(*R.AssetPath,Existing);
 if(!Existing.IsEmpty() || FPackageName::DoesPackageExist(R.AssetPath)) throw std::runtime_error("asset_path already exists; existing assets are never overwritten");
 FString ClassPath=Factory->GetSupportedClass()->GetPathName(); FString Path=R.AssetPath; bool bSaved=false;
 if(!R.bDryRun)
 {
  UObject* Created=FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().CreateAsset(FPackageName::GetLongPackageAssetName(R.AssetPath),FPackageName::GetLongPackagePath(R.AssetPath),Factory->GetSupportedClass(),Factory);
  if(!Created) throw std::runtime_error("The engine factory did not create the asset");
  Created->MarkPackageDirty(); ClassPath=Created->GetClass()->GetPathName(); Path=Created->GetPathName();
  if(R.bSave) { bSaved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Created,false); if(!bSaved) throw std::runtime_error("The asset was created but saving failed; it remains unsaved"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Path); J->WriteValue(TEXT("class"),ClassPath); J->WriteValue(TEXT("kind"),R.Kind); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),bSaved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::ImportFbx(const FGameCoreReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("FBX import requires stopped PIE");
 if(R.AssetPath.Len()>1024 || R.AssetPath.Contains(TEXT(".")) || !R.AssetPath.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(R.AssetPath)) throw std::runtime_error("asset_path must be an unused /Game package path such as /Game/Characters/SK_Hero");
 const FString Source=FPaths::ConvertRelativePathToFull(R.SourceFilePath);
 if(FPaths::IsRelative(R.SourceFilePath) || !FPaths::GetExtension(Source).Equals(TEXT("fbx"),ESearchCase::IgnoreCase) || !IFileManager::Get().FileExists(*Source)) throw std::runtime_error("source_file_path must be an absolute path to an existing .fbx file");
 const bool bSkeletal=R.Kind==TEXT("skeletal_mesh"); const bool bAnimation=R.Kind==TEXT("animation");
 if(!bSkeletal && !bAnimation && R.Kind!=TEXT("static_mesh")) throw std::runtime_error("kind must be skeletal_mesh, animation or static_mesh");
 if(bAnimation && R.SkeletonPath.IsEmpty()) throw std::runtime_error("kind animation requires skeleton_path");
 if(R.Kind==TEXT("static_mesh") && !R.SkeletonPath.IsEmpty()) throw std::runtime_error("skeleton_path does not apply to static_mesh");
 if(R.bImportAnimations && !bSkeletal) throw std::runtime_error("import_animations applies only to skeletal_mesh");
 USkeleton* Skeleton=R.SkeletonPath.IsEmpty() ? nullptr : LoadInput<USkeleton>(R.SkeletonPath,"skeleton_path must name a Skeleton");
 IAssetRegistry& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
 TArray<FAssetData> Existing; Registry.GetAssetsByPackageName(*R.AssetPath,Existing);
 if(!Existing.IsEmpty() || FPackageName::DoesPackageExist(R.AssetPath)) throw std::runtime_error("asset_path already exists; existing assets are never overwritten");
 const FString Destination=FPackageName::GetLongPackagePath(R.AssetPath);
 const auto ListFolder=[&Registry,&Destination]() { TArray<FAssetData> Assets; Registry.GetAssetsByPath(*Destination,Assets,false); TSet<FString> Paths; for(const FAssetData& Asset:Assets) Paths.Add(Asset.GetObjectPathString()); return Paths; };
 TArray<FString> Created; FString MainPath,MainClass,SkeletonOut; bool bSaved=false;
 if(!R.bDryRun)
 {
  const TSet<FString> Before=ListFolder();
  auto* Options=NewObject<UFbxImportUI>();
  Options->bAutomatedImportShouldDetectType=false; Options->MeshTypeToImport=bSkeletal ? FBXIT_SkeletalMesh : bAnimation ? FBXIT_Animation : FBXIT_StaticMesh; Options->OriginalImportType=Options->MeshTypeToImport;
  Options->bImportAsSkeletal=bSkeletal; Options->bImportMesh=!bAnimation; Options->Skeleton=Skeleton; Options->bCreatePhysicsAsset=bSkeletal; Options->bImportAnimations=bAnimation || R.bImportAnimations;
  Options->bImportMaterials=!bAnimation && R.bImportMaterials; Options->bImportTextures=!bAnimation && R.bImportMaterials;
  TStrongObjectPtr<UAssetImportTask> Task(NewObject<UAssetImportTask>());
  Task->Filename=Source; Task->DestinationPath=Destination; Task->DestinationName=FPackageName::GetLongPackageAssetName(R.AssetPath); Task->bAutomated=true; Task->bAsync=false; Task->bSave=false; Task->bReplaceExisting=false; Task->Factory=NewObject<UFbxFactory>(); Task->Options=Options;
  TArray<UAssetImportTask*> Tasks={Task.Get()}; FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().ImportAssetTasks(Tasks);
  UClass* Wanted=bSkeletal ? USkeletalMesh::StaticClass() : bAnimation ? UAnimSequence::StaticClass() : UStaticMesh::StaticClass(); UObject* Main=nullptr;
  for(UObject* Object:Task->GetObjects()) if(Object && Object->IsA(Wanted)) { Main=Object; break; }
  if(!Main) throw std::runtime_error("The FBX import produced no asset of the requested kind; check the file contents, the skeleton match, and get_editor_logs");
  MainPath=Main->GetPathName(); MainClass=Main->GetClass()->GetPathName();
  if(auto* Mesh=Cast<USkeletalMesh>(Main)) SkeletonOut=Mesh->GetSkeleton() ? Mesh->GetSkeleton()->GetPathName() : FString();
  for(const FString& Path:ListFolder()) if(!Before.Contains(Path)) Created.Add(Path);
  Created.AddUnique(MainPath); Created.Sort();
  if(R.bSave) { auto* Assets=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>(); bSaved=true; for(const FString& Path:Created) bSaved&=Assets->SaveAsset(Path,false); if(!bSaved) throw std::runtime_error("The import succeeded but saving failed; assets remain unsaved"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),R.bDryRun ? R.AssetPath : MainPath); J->WriteValue(TEXT("class"),MainClass); J->WriteValue(TEXT("kind"),R.Kind); J->WriteValue(TEXT("skeleton"),SkeletonOut); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),bSaved); J->WriteArrayStart(TEXT("created_assets")); for(const FString& Path:Created) J->WriteValue(Path); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::InspectClassDefaults(const FString& AssetPath,const FString& Search,int32 Limit)
{
 if(!IsInGameThread() || Limit<1 || Limit>1000 || Search.Len()>128) throw std::runtime_error("Class defaults inspection requires a bounded search and limit 1-1000");
 auto* Blueprint=LoadBlueprintAsset(AssetPath); UObject* Defaults=Blueprint->GeneratedClass->GetDefaultObject();
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Blueprint->GetPathName()); J->WriteValue(TEXT("class"),Blueprint->GeneratedClass->GetPathName()); J->WriteValue(TEXT("parent_class"),Blueprint->ParentClass ? Blueprint->ParentClass->GetPathName() : FString());
 int32 Total=0; J->WriteArrayStart(TEXT("properties"));
 auto Emit=[&](UObject* Owner,const FString& Prefix) { for(TFieldIterator<FProperty> It(Owner->GetClass());It;++It) { if(It->ArrayDim!=1 || !IsLeafEditable(*It)) continue; const FString Path=Prefix+It->GetName(); if(!Search.IsEmpty() && !Path.Contains(Search)) continue; if(++Total>Limit) continue; const FString Text=ValueText(*It,It->ContainerPtrToValuePtr<void>(Owner),Owner); J->WriteObjectStart(); J->WriteValue(TEXT("path"),Path); J->WriteValue(TEXT("type"),It->GetCPPType()); J->WriteValue(TEXT("value_truncated"),Text.Len()>4096); J->WriteValue(TEXT("value"),Text.Left(4096)); J->WriteObjectEnd(); } };
 Emit(Defaults,FString());
 for(TFieldIterator<FObjectPropertyBase> It(Defaults->GetClass());It;++It) { if(It->ArrayDim!=1) continue; UObject* Sub=It->GetObjectPropertyValue_InContainer(Defaults); if(Sub && Sub->GetOuter()==Defaults && Sub->IsDefaultSubobject()) Emit(Sub,It->GetName()+TEXT(".")); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("total"),Total); J->WriteValue(TEXT("truncated"),Total>Limit); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::SetClassDefault(const FGameCoreReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.Value.Len()>65536) throw std::runtime_error("Class default edits require stopped PIE, confirmation and a bounded value");
 auto* Blueprint=LoadBlueprintAsset(R.AssetPath); FResolved T=ResolvePath(Blueprint->GeneratedClass->GetDefaultObject(),R.PropertyPath);
 if(!IsLeafEditable(T.Property)) throw std::runtime_error("Property is not editable on class defaults");
 const FString Before=ValueText(T.Property,T.Address,T.Owner); if(Before!=R.ExpectedValue) throw std::runtime_error("ExpectedValue stale guard failed");
 const bool Changed=PreflightImport(T.Property,R.Value,T.Address,T.Owner); bool Saved=false; FString After=Before;
 if(Changed && !R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Class Default"))); Blueprint->Modify(); T.Owner->SetFlags(RF_Transactional); T.Owner->Modify(); T.Owner->PreEditChange(T.Property);
  T.Property->ImportText_Direct(*R.Value,T.Address,T.Owner,PPF_None); FPropertyChangedEvent Event(T.Property,EPropertyChangeType::ValueSet); T.Owner->PostEditChangeProperty(Event);
  FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint); FKismetEditorUtilities::CompileBlueprint(Blueprint);
  if(Blueprint->Status==BS_Error) throw std::runtime_error("Default applied but the Blueprint failed to compile; use undo or inspect its diagnostics");
  const FResolved Fresh=ResolvePath(Blueprint->GeneratedClass->GetDefaultObject(),R.PropertyPath); After=ValueText(Fresh.Property,Fresh.Address,Fresh.Owner); Blueprint->MarkPackageDirty();
 }
 if(R.bSave && !R.bDryRun) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Blueprint,false); if(!Saved) throw std::runtime_error("Default applied but the save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Blueprint->GetPathName()); J->WriteValue(TEXT("path"),R.PropertyPath); J->WriteValue(TEXT("before"),Before); J->WriteValue(TEXT("after"),After); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::InspectGameSettings()
{
 auto* Settings=GetMutableDefault<UGameMapsSettings>(); FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart();
 for(const TCHAR* Name:GGameSettings) { auto* P=FindFProperty<FProperty>(Settings->GetClass(),Name); J->WriteValue(Name,P ? ValueText(P,P->ContainerPtrToValuePtr<void>(Settings),Settings) : FString()); }
 J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::SetGameSetting(const FGameCoreReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm) throw std::runtime_error("Game settings edits require stopped PIE and confirmation");
 bool Allowed=false; for(const TCHAR* Name:GGameSettings) Allowed|=R.PropertyPath==Name; if(!Allowed) throw std::runtime_error("PropertyPath must be GameDefaultMap, EditorStartupMap, GlobalDefaultGameMode or GameInstanceClass");
 auto* Settings=GetMutableDefault<UGameMapsSettings>(); auto* P=FindFProperty<FProperty>(Settings->GetClass(),*R.PropertyPath); if(!P) throw std::runtime_error("Native settings layout mismatch");
 void* Address=P->ContainerPtrToValuePtr<void>(Settings); const FString Before=ValueText(P,Address,Settings); if(Before!=R.ExpectedValue) throw std::runtime_error("ExpectedValue stale guard failed");
 // A wrong path here stops the packaged game from starting, so validate what the soft path would resolve to.
 if(CastField<FSoftClassProperty>(P)==nullptr && R.PropertyPath.EndsWith(TEXT("Map")))
 { if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.Value)).IsValid()) throw std::runtime_error("Map must exist in the asset registry"); }
 else
 { UClass* Class=LoadObject<UClass>(nullptr,*R.Value); UClass* Base=R.PropertyPath==TEXT("GlobalDefaultGameMode") ? AGameModeBase::StaticClass() : UGameInstance::StaticClass(); if(!Class || !Class->IsChildOf(Base)) throw std::runtime_error("Class must load and derive from the setting's base class"); }
 const bool Changed=PreflightImport(P,R.Value,Address,Settings);
 if(Changed && !R.bDryRun) { P->ImportText_Direct(*R.Value,Address,Settings,PPF_None); if(!Settings->TryUpdateDefaultConfigFile()) { P->ImportText_Direct(*Before,Address,Settings,PPF_None); throw std::runtime_error("Writing DefaultEngine.ini failed; the setting was restored"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("setting"),R.PropertyPath); J->WriteValue(TEXT("before"),Before); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("scope"),TEXT("Writes Config/DefaultEngine.ini immediately; not undoable.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::InspectPlaySession(const FString& Search,int32 Limit)
{
 UWorld* World=RequirePlayWorld(); if(Limit<1 || Limit>1000 || Search.Len()>128) throw std::runtime_error("Play session inspection requires a bounded search and limit 1-1000");
 APlayerController* Controller=World->GetFirstPlayerController(); APawn* Player=Controller ? Controller->GetPawn() : nullptr;
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("world"),World->GetPathName()); J->WriteValue(TEXT("time_seconds"),World->GetTimeSeconds()); J->WriteValue(TEXT("paused"),World->IsPaused());
 J->WriteValue(TEXT("game_mode"),World->GetAuthGameMode() ? World->GetAuthGameMode()->GetClass()->GetPathName() : FString()); J->WriteValue(TEXT("player_controller"),Controller ? Controller->GetPathName() : FString()); J->WriteValue(TEXT("player_pawn"),Player ? Player->GetPathName() : FString());
 if(Player) { WriteVector(J,TEXT("player_location"),Player->GetActorLocation()); WriteVector(J,TEXT("player_velocity"),Player->GetVelocity()); }
 int32 Total=0; J->WriteArrayStart(TEXT("actors"));
 for(TActorIterator<AActor> It(World);It;++It) { if(!Search.IsEmpty() && !It->GetPathName().Contains(Search) && !It->GetClass()->GetPathName().Contains(Search)) continue; if(++Total>Limit) continue; J->WriteObjectStart(); J->WriteValue(TEXT("path"),It->GetPathName()); J->WriteValue(TEXT("class"),It->GetClass()->GetPathName()); WriteVector(J,TEXT("location"),It->GetActorLocation()); J->WriteValue(TEXT("hidden"),It->IsHidden()); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("total"),Total); J->WriteValue(TEXT("truncated"),Total>Limit); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::ReadPlayActorProperties(const FString& Actor,const FString& Search,int32 Limit)
{
 UWorld* World=RequirePlayWorld(); if(Actor.IsEmpty() || Limit<1 || Limit>1000) throw std::runtime_error("actor is required, and limit must be 1-1000");
 AActor* Found=nullptr; if(Actor==TEXT("game_mode")) Found=World->GetAuthGameMode(); else if(Actor==TEXT("player_pawn")) { APlayerController* Controller=World->GetFirstPlayerController(); Found=Controller ? Controller->GetPawn() : nullptr; }
 else for(TActorIterator<AActor> It(World);It;++It) if(It->GetPathName().Contains(Actor) || It->GetClass()->GetName().Contains(Actor)) { Found=*It; break; }
 if(!Found) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("No actor in the play session matches %s. Use inspect_play_session to list them."),*Actor)));
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("actor"),Found->GetPathName()); J->WriteValue(TEXT("class"),Found->GetClass()->GetPathName()); int32 Total=0; J->WriteArrayStart(TEXT("properties"));
 for(TFieldIterator<FProperty> It(Found->GetClass());It;++It)
 {
  // With no search, list only variables declared in Blueprints; native actors have hundreds of properties.
  if(Search.IsEmpty() ? !Cast<UBlueprintGeneratedClass>(It->GetOwnerClass()) : !It->GetName().Contains(Search)) continue;
  if(++Total>Limit) continue;
  FString Value; It->ExportTextItem_Direct(Value,It->ContainerPtrToValuePtr<void>(Found),nullptr,Found,PPF_None);
  J->WriteObjectStart(); J->WriteValue(TEXT("name"),It->GetName()); J->WriteValue(TEXT("type"),It->GetCPPType()); J->WriteValue(TEXT("value"),Value); J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteValue(TEXT("total"),Total); J->WriteValue(TEXT("truncated"),Total>Limit); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::SendPlayInput(const FGameCoreReq& R)
{
 UWorld* World=RequirePlayWorld(); APlayerController* Controller=World->GetFirstPlayerController(); if(!Controller || !Controller->PlayerInput) throw std::runtime_error("The play session has no local player input");
 const FKey Key(*R.Key); if(!Key.IsValid()) throw std::runtime_error("Key must be a valid FKey name such as W, SpaceBar or LeftMouseButton");
 EInputEvent Event; if(R.Event==TEXT("press")) Event=IE_Pressed; else if(R.Event==TEXT("release")) Event=IE_Released; else if(R.Event==TEXT("axis")) Event=IE_Axis; else throw std::runtime_error("Event requires press, release or axis");
 if(!FMath::IsFinite(R.Amount) || FMath::Abs(R.Amount)>1000) throw std::runtime_error("Amount must be finite and bounded");
 FInputKeyEventArgs Args(nullptr,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),Key,Event); Args.AmountDepressed=Event==IE_Released ? 0.f : R.Amount;
 const bool Consumed=Controller->InputKey(Args);
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("key"),Key.ToString()); J->WriteValue(TEXT("event"),R.Event); J->WriteValue(TEXT("consumed"),Consumed); J->WriteValue(TEXT("key_down"),Controller->IsInputKeyDown(Key)); J->WriteValue(TEXT("scope"),TEXT("Input reaches the first local player's controller; a pressed key stays down until released.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::MovePlayMouse(const FGameCoreReq& R)
{
 UWorld* World=RequirePlayWorld(); APlayerController* Controller=World->GetFirstPlayerController(); if(!Controller || !Controller->GetLocalPlayer()) throw std::runtime_error("The play session has no local player. Start play in a windowed editor; -nullrhi has no game viewport.");
 int32 Width=0,Height=0; Controller->GetViewportSize(Width,Height); if(Width<=0 || Height<=0) throw std::runtime_error("The play session has no game viewport. Start play in a windowed editor; -nullrhi has none.");
 FVector2D Screen(R.ScreenX,R.ScreenY); FVector Target=FVector::ZeroVector; const bool bAimed=!R.Actor.IsEmpty() || R.bUseWorldLocation;
 if(!R.Actor.IsEmpty())
 {
  AActor* Found=nullptr; for(TActorIterator<AActor> It(World);It;++It) if(It->GetPathName().Contains(R.Actor) || It->GetClass()->GetName().Contains(R.Actor)) { Found=*It; break; }
  if(!Found) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("No actor in the play session matches %s. Use inspect_play_session to list them."),*R.Actor)));
  Target=Found->GetActorLocation();
 }
 else if(R.bUseWorldLocation) Target=FVector(R.WorldX,R.WorldY,R.WorldZ);
 if(bAimed && !Controller->ProjectWorldLocationToScreen(Target,Screen,false)) throw std::runtime_error("That location is behind the camera, so the mouse cannot point at it. Aim at something in view.");
 if(Screen.X<0 || Screen.Y<0 || Screen.X>=Width || Screen.Y>=Height) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Position (%.0f, %.0f) is outside the %d x %d game viewport. Aim at something in view."),Screen.X,Screen.Y,Width,Height)));
 Controller->SetMouseLocation(FMath::RoundToInt(Screen.X),FMath::RoundToInt(Screen.Y));
 FHitResult Hit; const bool bHit=Controller->GetHitResultAtScreenPosition(Screen,ECC_Visibility,false,Hit);
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("screen_x"),FMath::RoundToInt(Screen.X)); J->WriteValue(TEXT("screen_y"),FMath::RoundToInt(Screen.Y)); J->WriteValue(TEXT("viewport_width"),Width); J->WriteValue(TEXT("viewport_height"),Height);
 J->WriteValue(TEXT("hit"),bHit); J->WriteValue(TEXT("hit_actor"),bHit && Hit.GetActor() ? Hit.GetActor()->GetPathName() : FString()); if(bHit) WriteVector(J,TEXT("hit_location"),Hit.Location);
 J->WriteValue(TEXT("scope"),TEXT("hit uses the Visibility trace channel. This moves the real system cursor.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::StartPackage(const FGameCoreReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm) throw std::runtime_error("Packaging requires stopped PIE and confirmation");
 if(R.Platform!=TEXT("Win64")) throw std::runtime_error("Platform must be Win64; other platforms need SDKs this route does not check");
 if(R.Configuration!=TEXT("Development") && R.Configuration!=TEXT("Shipping") && R.Configuration!=TEXT("DebugGame")) throw std::runtime_error("Configuration requires Development, Shipping or DebugGame");
 if(RefreshPackage()) throw std::runtime_error("A package job is already running");
 // Cooking reads from disk, so unsaved edits would silently be missing from the build.
 TArray<UPackage*> Dirty; FEditorFileUtils::GetDirtyContentPackages(Dirty); FEditorFileUtils::GetDirtyWorldPackages(Dirty);
 if(!Dirty.IsEmpty() && !R.bAllowDirty) throw std::runtime_error("Unsaved packages would be missing from the build; save them or pass allow_dirty");
 const FString Stamp=FDateTime::Now().ToString(TEXT("%Y%m%d-%H%M%S")); const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("MCPBuilds")/Stamp);
 const FString Bat=FPaths::ConvertRelativePathToFull(FPaths::EngineDir()/TEXT("Build/BatchFiles/RunUAT.bat")); const FString Project=FPaths::ConvertRelativePathToFull(FPaths::GetProjectFilePath()); const FString Log=Root/TEXT("package.log");
 if(!FPaths::FileExists(Bat)) throw std::runtime_error("RunUAT.bat is not available in this engine install");
 if(!R.bDryRun)
 {
  IFileManager::Get().MakeDirectory(*Root,true);
  // Fixed argument list: only the validated platform and configuration vary. cmd redirects output so status can tail the log.
  const FString Inner=FString::Printf(TEXT("\"\"%s\" BuildCookRun -project=\"%s\" -noP4 -utf8output -unattended -platform=%s -clientconfig=%s -build -cook -stage -pak -archive -archivedirectory=\"%s\" > \"%s\" 2>&1\""),*Bat,*Project,*R.Platform,*R.Configuration,*(Root/TEXT("Archive")),*Log);
  FProcHandle Handle=FPlatformProcess::CreateProc(TEXT("cmd.exe"),*(TEXT("/c ")+Inner),true,true,true,nullptr,0,*Root,nullptr);
  if(!Handle.IsValid()) throw std::runtime_error("Failed to start RunUAT");
  GPackage=FPackageJob(); GPackage.Handle=Handle; GPackage.bStarted=true; GPackage.LogFile=Log; GPackage.OutputDir=Root/TEXT("Archive"); GPackage.Platform=R.Platform; GPackage.Configuration=R.Configuration;
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("platform"),R.Platform); J->WriteValue(TEXT("configuration"),R.Configuration); J->WriteValue(TEXT("dirty_package_count"),Dirty.Num()); J->WriteValue(TEXT("output_dir"),Root/TEXT("Archive")); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("started"),!R.bDryRun); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::PackageStatus(int32 LogLines)
{
 if(LogLines<0 || LogLines>1000) throw std::runtime_error("log_lines requires 0-1000");
 const bool Running=RefreshPackage(); TArray<FString> Tail;
 if(GPackage.bStarted && LogLines>0) { TArray<FString> Lines; FString Text; if(FFileHelper::LoadFileToString(Text,*GPackage.LogFile,FFileHelper::EHashOptions::None,FILEREAD_AllowWrite)) Text.ParseIntoArrayLines(Lines); for(int32 Index=FMath::Max(0,Lines.Num()-LogLines);Index<Lines.Num();++Index) Tail.Add(Lines[Index]); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("started"),GPackage.bStarted); J->WriteValue(TEXT("running"),Running); J->WriteValue(TEXT("cancelled"),GPackage.bCancelled); J->WriteValue(TEXT("finished"),GPackage.bExitKnown); if(GPackage.bExitKnown) { J->WriteValue(TEXT("exit_code"),GPackage.ExitCode); J->WriteValue(TEXT("succeeded"),GPackage.ExitCode==0 && !GPackage.bCancelled); }
 J->WriteValue(TEXT("platform"),GPackage.Platform); J->WriteValue(TEXT("configuration"),GPackage.Configuration); J->WriteValue(TEXT("output_dir"),GPackage.OutputDir); J->WriteValue(TEXT("log_file"),GPackage.LogFile); J->WriteArrayStart(TEXT("log_tail")); for(const auto& Line:Tail) J->WriteValue(Line); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Result;
}

FString GameCoreUtils::CancelPackage()
{
 if(!RefreshPackage()) throw std::runtime_error("No package job is running");
 FPlatformProcess::TerminateProc(GPackage.Handle,true); GPackage.bCancelled=true;
 return TEXT("{\"cancel_requested\":true}");
}
