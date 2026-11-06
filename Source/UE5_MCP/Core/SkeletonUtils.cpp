#include "SkeletonUtils.h"
#include "UE5_MCP/API/DTO/SkeletonCurveReq.h"
#include "Animation/AnimCurveMetadata.h"
#include "Animation/AnimSequence.h"
#include "AnimationRuntime.h"
#include "UObject/ReferencerFinder.h"
#include "Animation/BlendProfile.h"
#include "UE5_MCP/API/DTO/CompatibleSkeletonReq.h"
#include "UE5_MCP/API/DTO/BoneRetargetReq.h"
#include "Engine/StaticMesh.h"
#include "NavigationWorldUtils.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "UObject/UObjectIterator.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/PreviewAssetAttachComponent.h"
#include "UObject/UnrealType.h"
#include "UE5_MCP/API/DTO/VirtualBoneReq.h"
#include "UE5_MCP/API/DTO/SkeletonSocketReq.h"
#include "Editor.h"
#include "ScopedTransaction.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/Package.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMeshSocket.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace
{
 void WriteCurveMetadata(TSharedRef<TJsonWriter<>> J,const USkeleton* Skeleton)
 {
  const int32 Count=Skeleton->GetNumCurveMetaData(); J->WriteValue(TEXT("curve_metadata_count"),Count); J->WriteValue(TEXT("curve_metadata_truncated"),Count>256); J->WriteArrayStart(TEXT("curve_metadata")); int32 Written=0;
  Skeleton->ForEachCurveMetaData([&](FName Name,const FCurveMetaData& Metadata)
  {
   if(Written++>=256) return; J->WriteObjectStart(); J->WriteValue(TEXT("name"),Name.ToString()); J->WriteValue(TEXT("material"),Metadata.Type.bMaterial); J->WriteValue(TEXT("morph_target"),Metadata.Type.bMorphtarget); J->WriteValue(TEXT("max_lod"),int32(Metadata.MaxLOD)); J->WriteValue(TEXT("linked_bone_count"),Metadata.LinkedBones.Num()); J->WriteValue(TEXT("linked_bones_truncated"),Metadata.LinkedBones.Num()>64); J->WriteArrayStart(TEXT("linked_bones"));
   for(int32 Index=0;Index<FMath::Min(Metadata.LinkedBones.Num(),64);++Index) { const auto& Bone=Metadata.LinkedBones[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("name"),Bone.BoneName.ToString()); J->WriteValue(TEXT("valid"),Skeleton->GetReferenceSkeleton().FindBoneIndex(Bone.BoneName)!=INDEX_NONE); J->WriteObjectEnd(); }
   J->WriteArrayEnd(); J->WriteObjectEnd();
  });
  J->WriteArrayEnd();
 }
 void WriteBlendProfiles(TSharedRef<TJsonWriter<>> J,const USkeleton* Skeleton)
 {
  J->WriteValue(TEXT("blend_profile_count"),Skeleton->BlendProfiles.Num()); J->WriteValue(TEXT("blend_profiles_truncated"),Skeleton->BlendProfiles.Num()>64); J->WriteArrayStart(TEXT("blend_profiles"));
  for(int32 Index=0;Index<FMath::Min(Skeleton->BlendProfiles.Num(),64);++Index)
  {
   const auto* Profile=Skeleton->BlendProfiles[Index].Get(); J->WriteObjectStart(); J->WriteValue(TEXT("valid"),IsValid(Profile));
   if(IsValid(Profile))
   {
    J->WriteValue(TEXT("name"),Profile->GetName()); J->WriteValue(TEXT("path"),Profile->GetPathName()); J->WriteValue(TEXT("mode"),StaticEnum<EBlendProfileMode>()->GetNameStringByValue(int64(Profile->GetMode()))); J->WriteValue(TEXT("owner_matches"),Profile->OwningSkeleton==Skeleton && Profile->GetOuter()==Skeleton); J->WriteValue(TEXT("entry_count"),Profile->ProfileEntries.Num()); J->WriteValue(TEXT("entries_truncated"),Profile->ProfileEntries.Num()>256); J->WriteArrayStart(TEXT("entries"));
    for(int32 EntryIndex=0;EntryIndex<FMath::Min(Profile->ProfileEntries.Num(),256);++EntryIndex) { const auto& Entry=Profile->ProfileEntries[EntryIndex]; J->WriteObjectStart(); J->WriteValue(TEXT("bone"),Entry.BoneReference.BoneName.ToString()); J->WriteValue(TEXT("bone_valid"),Skeleton->GetReferenceSkeleton().FindBoneIndex(Entry.BoneReference.BoneName)!=INDEX_NONE); if(FMath::IsFinite(Entry.BlendScale)) J->WriteValue(TEXT("scale"),Entry.BlendScale); else J->WriteNull(TEXT("scale")); J->WriteObjectEnd(); }
    J->WriteArrayEnd();
   }
   J->WriteObjectEnd();
  }
  J->WriteArrayEnd();
 }
 void WriteBoneTransform(TSharedRef<TJsonWriter<>> J,const TCHAR* Label,const FTransform& Transform)
 {
  J->WriteObjectStart(Label); J->WriteValue(TEXT("finite"),!Transform.ContainsNaN());
  auto Number=[&](double Value) { if(FMath::IsFinite(Value)) J->WriteValue(Value); else J->WriteNull(); };
  auto Vector=[&](const TCHAR* Name,const FVector& Value) { J->WriteArrayStart(Name); Number(Value.X); Number(Value.Y); Number(Value.Z); J->WriteArrayEnd(); };
  Vector(TEXT("location"),Transform.GetLocation()); Vector(TEXT("scale"),Transform.GetScale3D()); const auto Q=Transform.GetRotation(); J->WriteArrayStart(TEXT("quaternion_xyzw")); Number(Q.X); Number(Q.Y); Number(Q.Z); Number(Q.W); J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 void WritePreviewAttachments(TSharedRef<TJsonWriter<>> J,const TCHAR* Label,const FPreviewAssetAttachContainer& Container,const USkeleton* Skeleton,const USkeletalMesh* Mesh)
 {
  const auto* Property=FindFProperty<FSoftObjectProperty>(FPreviewAttachedObjectPair::StaticStruct(),TEXT("AttachedObject"));
  J->WriteObjectStart(Label); J->WriteValue(TEXT("count"),Container.Num()); J->WriteValue(TEXT("truncated"),Container.Num()>256); J->WriteValue(TEXT("asset_path_available"),Property!=nullptr); J->WriteArrayStart(TEXT("entries"));
  for(int32 Index=0;Index<FMath::Min(Container.Num(),256);++Index)
  {
   const auto& Pair=Container[Index]; bool TargetValid=false;
   if(Mesh) TargetValid=Mesh->GetRefSkeleton().FindBoneIndex(Pair.AttachedTo)!=INDEX_NONE || Mesh->FindSocket(Pair.AttachedTo)!=nullptr;
   else if(Skeleton) { TargetValid=Skeleton->GetReferenceSkeleton().FindBoneIndex(Pair.AttachedTo)!=INDEX_NONE; for(const auto& Socket:Skeleton->Sockets) if(Socket && Socket->SocketName==Pair.AttachedTo) TargetValid=true; }
   J->WriteObjectStart(); J->WriteValue(TEXT("index"),Index); J->WriteValue(TEXT("attach_name"),Pair.AttachedTo.ToString()); J->WriteValue(TEXT("target_valid"),TargetValid);
   if(Property) { const FSoftObjectPtr Reference=Property->GetPropertyValue_InContainer(&Pair); const auto Path=Reference.ToSoftObjectPath(); J->WriteValue(TEXT("asset_path"),Path.ToString()); J->WriteValue(TEXT("loaded"),Reference.IsValid()); J->WriteValue(TEXT("registered"),!Path.IsNull() && FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(Path).IsValid()); }
   J->WriteObjectEnd();
  }
  J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 void WriteSkeletonDiagnostics(TSharedRef<TJsonWriter<>> J,const USkeleton* Skeleton)
 {
  const auto& Reference=Skeleton->GetReferenceSkeleton(); const auto& Bones=Skeleton->GetVirtualBones();
  TArray<FString> Issues; int32 IssueCount=0; auto Issue=[&](const FString& Message) { ++IssueCount; if(Issues.Num()<128) Issues.Add(Message.Left(1024)); };
  const bool Complete=Skeleton->Sockets.Num()<=1024 && Bones.Num()<=256;
  TSet<FName> SocketNames; for(int32 Index=0;Index<FMath::Min(Skeleton->Sockets.Num(),1024);++Index)
  {
   const auto* Socket=Skeleton->Sockets[Index].Get(); if(!IsValid(Socket)) { Issue(TEXT("Null/invalid socket entry")); continue; }
   const FString Name=Socket->SocketName.ToString();
   if(Socket->SocketName.IsNone() || SocketNames.Contains(Socket->SocketName)) Issue(TEXT("Missing/duplicate socket name: ")+Name); SocketNames.Add(Socket->SocketName);
   if(Reference.FindBoneIndex(Socket->BoneName)==INDEX_NONE) Issue(TEXT("Socket parent bone missing: ")+Name);
   if(Reference.FindBoneIndex(Socket->SocketName)!=INDEX_NONE) Issue(TEXT("Socket name collides with bone: ")+Name);
   if(Socket->RelativeLocation.ContainsNaN() || Socket->RelativeRotation.ContainsNaN() || Socket->RelativeScale.ContainsNaN()) Issue(TEXT("Socket transform nonfinite: ")+Name);
   if(Socket->GetOuter()!=Skeleton) Issue(TEXT("Socket has unexpected owner: ")+Name);
  }
  TMap<FName,int32> Names; TSet<FString> Pairs;
  for(int32 Index=0;Index<FMath::Min(Bones.Num(),256);++Index)
  {
   const auto& Bone=Bones[Index]; const FString Name=Bone.VirtualBoneName.ToString();
   if(Bone.VirtualBoneName.IsNone() || Names.Contains(Bone.VirtualBoneName) || !VirtualBoneNameHelpers::CheckVirtualBonePrefix(Name)) Issue(TEXT("Invalid/duplicate virtual bone name: ")+Name); Names.Add(Bone.VirtualBoneName,Index);
   if(Bone.SourceBoneName==Bone.TargetBoneName || Reference.FindBoneIndex(Bone.SourceBoneName)==INDEX_NONE || Reference.FindBoneIndex(Bone.TargetBoneName)==INDEX_NONE) Issue(TEXT("Virtual bone endpoint invalid: ")+Name);
   const FString Pair=Bone.SourceBoneName.ToString()+TEXT("|")+Bone.TargetBoneName.ToString(); if(Pairs.Contains(Pair)) Issue(TEXT("Duplicate virtual bone endpoint pair: ")+Name); Pairs.Add(Pair);
  }
  TSet<int32> Visiting,Done; bool DepthLimited=false;
  TFunction<void(int32,int32)> Visit=[&](int32 Index,int32 Depth)
  {
   if(Done.Contains(Index)) return; if(Depth>32) { DepthLimited=true; Issue(TEXT("Virtual bone dependency depth exceeds 32")); return; }
   if(Visiting.Contains(Index)) { Issue(TEXT("Virtual bone dependency cycle: ")+Bones[Index].VirtualBoneName.ToString()); return; }
   Visiting.Add(Index); for(const FName Endpoint:{Bones[Index].SourceBoneName,Bones[Index].TargetBoneName}) if(const int32* Other=Names.Find(Endpoint)) Visit(*Other,Depth+1); Visiting.Remove(Index); Done.Add(Index);
  };
  for(int32 Index=0;Index<FMath::Min(Bones.Num(),256);++Index) Visit(Index,0);
  J->WriteObjectStart(TEXT("diagnostics")); J->WriteValue(TEXT("complete"),Complete && !DepthLimited); J->WriteValue(TEXT("structurally_valid"),Complete && !DepthLimited && IssueCount==0); J->WriteValue(TEXT("issue_count"),IssueCount); J->WriteValue(TEXT("issues_truncated"),IssueCount>Issues.Num()); J->WriteArrayStart(TEXT("issues")); for(const auto& Message:Issues) J->WriteValue(Message); J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Bounded Skeleton-owned socket/virtual-bone structural checks; no native animation compilation, mesh reference validation or runtime execution.")); J->WriteObjectEnd();
 }
 void RefreshSkeletonSocketMaps(USkeleton* Skeleton)
 {
  for(TObjectIterator<USkeletalMesh> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetSkeleton()==Skeleton) It->RebuildSocketMap();
 }
}
FString SkeletonUtils::Inspect(const FString& AssetPath)
{
 if(!IsInGameThread() || AssetPath.IsEmpty() || AssetPath.Len()>1024 || AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(AssetPath)) throw std::runtime_error("Skeleton inspection requires bounded full asset object path");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(AssetPath)).IsValid()) throw std::runtime_error("Skeleton asset must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent native Skeleton");
 const auto& Reference=Skeleton->GetReferenceSkeleton(); const auto& VirtualBones=Skeleton->GetVirtualBones();
 const auto& LocalPose=Reference.GetRefBonePose(); TArray<FTransform> ComponentPose; TArray<bool> ComponentValid;
 const int32 PoseCount=FMath::Min(Reference.GetNum(),1024); ComponentPose.SetNum(PoseCount); ComponentValid.Init(false,PoseCount);
 for(int32 Index=0;Index<PoseCount;++Index) if(LocalPose.IsValidIndex(Index)) { const int32 Parent=Reference.GetParentIndex(Index); if(Parent==INDEX_NONE) { ComponentPose[Index]=LocalPose[Index]; ComponentValid[Index]=true; } else if(Parent>=0 && Parent<Index && ComponentValid[Parent]) { ComponentPose[Index]=LocalPose[Index]*ComponentPose[Parent]; ComponentValid[Index]=true; } }

 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); WriteSkeletonDiagnostics(J,Skeleton); WriteBlendProfiles(J,Skeleton); WriteCurveMetadata(J,Skeleton); J->WriteValue(TEXT("retarget_source_count"),Skeleton->AnimRetargetSources.Num()); J->WriteValue(TEXT("retarget_sources_truncated"),Skeleton->AnimRetargetSources.Num()>64); J->WriteArrayStart(TEXT("retarget_sources")); int32 SourceCount=0; for(const auto& Pair:Skeleton->AnimRetargetSources) { if(SourceCount++>=64) break; J->WriteObjectStart(); J->WriteValue(TEXT("name"),Pair.Key.ToString()); J->WriteValue(TEXT("pose_name"),Pair.Value.PoseName.ToString()); J->WriteValue(TEXT("transform_count"),Pair.Value.ReferencePose.Num()); J->WriteValue(TEXT("source_mesh"),Pair.Value.SourceReferenceMesh.ToSoftObjectPath().ToString()); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("use_compatible_retarget_modes"),Skeleton->GetUseRetargetModesFromCompatibleSkeleton()); J->WriteValue(TEXT("compatible_skeleton_count"),Skeleton->GetCompatibleSkeletons().Num()); J->WriteValue(TEXT("compatible_skeletons_truncated"),Skeleton->GetCompatibleSkeletons().Num()>256); J->WriteArrayStart(TEXT("compatible_skeletons")); for(int32 Index=0;Index<FMath::Min(Skeleton->GetCompatibleSkeletons().Num(),256);++Index) J->WriteValue(Skeleton->GetCompatibleSkeletons()[Index].ToSoftObjectPath().ToString()); J->WriteArrayEnd(); WritePreviewAttachments(J,TEXT("preview_attachments"),Skeleton->PreviewAttachedAssetContainer,Skeleton,nullptr); J->WriteValue(TEXT("bone_count"),Reference.GetNum()); J->WriteValue(TEXT("bones_truncated"),Reference.GetNum()>1024); J->WriteArrayStart(TEXT("bones"));
 for(int32 Index=0;Index<FMath::Min(Reference.GetNum(),1024);++Index) { J->WriteObjectStart(); J->WriteValue(TEXT("index"),Index); J->WriteValue(TEXT("name"),Reference.GetBoneName(Index).ToString()); J->WriteValue(TEXT("parent_index"),Reference.GetParentIndex(Index)); J->WriteValue(TEXT("translation_retargeting_mode"),int32(Skeleton->GetBoneTranslationRetargetingMode(Index))); J->WriteValue(TEXT("raw_bone"),Index<Reference.GetRawBoneNum()); if(LocalPose.IsValidIndex(Index)) WriteBoneTransform(J,TEXT("reference_local"),LocalPose[Index]); J->WriteValue(TEXT("reference_component_available"),ComponentValid[Index]); if(ComponentValid[Index]) WriteBoneTransform(J,TEXT("reference_component"),ComponentPose[Index]); J->WriteObjectEnd(); } J->WriteArrayEnd();
 J->WriteValue(TEXT("socket_count"),Skeleton->Sockets.Num()); J->WriteValue(TEXT("sockets_truncated"),Skeleton->Sockets.Num()>256); J->WriteArrayStart(TEXT("sockets"));
 for(int32 Index=0;Index<FMath::Min(Skeleton->Sockets.Num(),256);++Index) if(const auto* Socket=Skeleton->Sockets[Index].Get())
 {
  J->WriteObjectStart(); J->WriteValue(TEXT("name"),Socket->SocketName.ToString()); J->WriteValue(TEXT("bone"),Socket->BoneName.ToString()); J->WriteValue(TEXT("bone_valid"),Reference.FindBoneIndex(Socket->BoneName)!=INDEX_NONE); J->WriteValue(TEXT("force_always_animated"),Socket->bForceAlwaysAnimated);
  auto Vector=[&](const TCHAR* Name,const FVector& Value) { J->WriteArrayStart(Name); for(double Number:{Value.X,Value.Y,Value.Z}) { if(FMath::IsFinite(Number)) J->WriteValue(Number); else J->WriteNull(); } J->WriteArrayEnd(); };
  Vector(TEXT("location"),Socket->RelativeLocation); Vector(TEXT("rotation_pitch_yaw_roll"),FVector(Socket->RelativeRotation.Pitch,Socket->RelativeRotation.Yaw,Socket->RelativeRotation.Roll)); Vector(TEXT("scale"),Socket->RelativeScale); J->WriteObjectEnd();
 } J->WriteArrayEnd();
 J->WriteValue(TEXT("virtual_bone_count"),VirtualBones.Num()); J->WriteValue(TEXT("virtual_bones_truncated"),VirtualBones.Num()>256); J->WriteArrayStart(TEXT("virtual_bones"));
 for(int32 Index=0;Index<FMath::Min(VirtualBones.Num(),256);++Index) { const auto& Bone=VirtualBones[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("name"),Bone.VirtualBoneName.ToString()); J->WriteValue(TEXT("source"),Bone.SourceBoneName.ToString()); J->WriteValue(TEXT("target"),Bone.TargetBoneName.ToString()); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Skeleton-owned sockets and virtual bones; mesh-only socket overrides are not included.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128 || R.BoneName.IsEmpty() || R.BoneName.Len()>128) throw std::runtime_error("Socket authoring requires stopped PIE, confirmed /Game Skeleton and bounded names");
 if(R.Operation!=TEXT("create") && R.Operation!=TEXT("update")) throw std::runtime_error("Socket operation requires create or update");
 auto Bounded=[](const FVector& V,double Limit) { return !V.ContainsNaN() && FMath::Abs(V.X)<=Limit && FMath::Abs(V.Y)<=Limit && FMath::Abs(V.Z)<=Limit; };
 if(!Bounded(R.Location,1.e8) || !Bounded(R.Scale,1.e4) || R.Rotation.ContainsNaN() || FMath::Abs(R.Rotation.Pitch)>360000 || FMath::Abs(R.Rotation.Yaw)>360000 || FMath::Abs(R.Rotation.Roll)>360000) throw std::runtime_error("Socket transform must be finite and bounded");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton");
 const FName Name(*R.SocketName),Bone(*R.BoneName); if(Name.IsNone() || Bone.IsNone() || Skeleton->GetReferenceSkeleton().FindBoneIndex(Bone)==INDEX_NONE) throw std::runtime_error("Socket name and existing bone required");
 USkeletalMeshSocket* Existing=nullptr; int32 Matches=0; for(const auto& SocketEntry:Skeleton->Sockets) if(auto* Socket=SocketEntry.Get()) if(Socket && Socket->SocketName==Name) { Existing=Socket; ++Matches; }
 if(Matches>1 || (R.Operation==TEXT("create") && Existing) || (R.Operation==TEXT("update") && !Existing)) throw std::runtime_error("Socket create requires unused name; update requires exactly one existing skeleton socket");
 if(R.Operation==TEXT("create") && (Skeleton->Sockets.Num()>=1024 || Skeleton->GetReferenceSkeleton().FindBoneIndex(Name)!=INDEX_NONE)) throw std::runtime_error("Socket count exceeds bound or name collides with bone");
 const bool Changed=!Existing || Existing->BoneName!=Bone || Existing->RelativeLocation!=R.Location || Existing->RelativeRotation!=R.Rotation || Existing->RelativeScale!=R.Scale || Existing->bForceAlwaysAnimated!=R.bForceAlwaysAnimated; bool Saved=false;
 if(!R.bDryRun && Changed)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Skeleton Socket"))); Skeleton->Modify();
  auto* Socket=Existing; if(!Socket) { Socket=NewObject<USkeletalMeshSocket>(Skeleton,NAME_None,RF_Transactional); Skeleton->Sockets.Add(Socket); } else { Socket->SetFlags(RF_Transactional); Socket->Modify(); }
  Socket->SocketName=Name; Socket->BoneName=Bone; Socket->RelativeLocation=R.Location; Socket->RelativeRotation=R.Rotation; Socket->RelativeScale=R.Scale; Socket->bForceAlwaysAnimated=R.bForceAlwaysAnimated; Socket->PostEditChange(); Skeleton->PostEditChange(); RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty();
 }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Socket edit completed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::DeleteSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128) throw std::runtime_error("Socket deletion requires stopped PIE, confirmed /Game Skeleton and bounded socket name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton");
 const FName Name(*R.SocketName); int32 Found=INDEX_NONE,Count=0;
 for(int32 Index=0;Index<Skeleton->Sockets.Num();++Index) if(Skeleton->Sockets[Index] && Skeleton->Sockets[Index]->SocketName==Name) { Found=Index; ++Count; }
 if(Name.IsNone() || Count!=1) throw std::runtime_error("Deletion requires exactly one existing skeleton-owned socket");
 int32 AttachmentCount=0; for(int32 Index=0;Index<Skeleton->PreviewAttachedAssetContainer.Num();++Index) if(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo==Name) ++AttachmentCount;
 bool Saved=false;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Delete Skeleton Socket"))); Skeleton->Modify(); auto* Socket=Skeleton->Sockets[Found].Get(); Socket->SetFlags(RF_Transactional); Socket->Modify(); Skeleton->Sockets.RemoveAt(Found); for(int32 Index=Skeleton->PreviewAttachedAssetContainer.Num()-1;Index>=0;--Index) if(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo==Name) Skeleton->PreviewAttachedAssetContainer.RemoveAtSwap(Index); Skeleton->PostEditChange(); RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty();
  if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Socket deleted but Skeleton save failed"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("deleted"),!R.bDryRun); J->WriteValue(TEXT("preview_attachment_removal_count"),AttachmentCount); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Removes skeleton-owned socket and matching Skeleton preview attachments; mesh overrides and external attachment names are not rewritten.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::CreateVirtualBone(const FVirtualBoneReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SourceBone.IsEmpty() || R.SourceBone.Len()>128 || R.TargetBone.IsEmpty() || R.TargetBone.Len()>128 || R.Name.Len()>128) throw std::runtime_error("Virtual bone creation requires stopped PIE, confirmed /Game Skeleton and bounded bone names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton");
 const FName Source(*R.SourceBone),Target(*R.TargetBone); const auto& Reference=Skeleton->GetReferenceSkeleton();
 if(Source.IsNone() || Target.IsNone() || Source==Target || Reference.FindBoneIndex(Source)==INDEX_NONE || Reference.FindBoneIndex(Target)==INDEX_NONE || Skeleton->GetVirtualBones().Num()>=256) throw std::runtime_error("Virtual bone requires distinct existing endpoints and <256 current virtual bones"); if(Reference.FindRawBoneIndex(Target)==INDEX_NONE) throw std::runtime_error("Virtual bone target must be a raw bone; native ref-skeleton rebuild indexes targets in raw-bone space and crashes on a virtual target");
 const FName Name=R.Name.IsEmpty() ? FVirtualBone(Source,Target).VirtualBoneName : FName(*R.Name);
 if(Name.IsNone() || Name.ToString().Len()>128 || !VirtualBoneNameHelpers::CheckVirtualBonePrefix(Name.ToString()) || Reference.FindBoneIndex(Name)!=INDEX_NONE) throw std::runtime_error("Virtual bone requires unused native VB-prefixed name");
 for(const auto& Bone:Skeleton->GetVirtualBones()) if(Bone.VirtualBoneName==Name || (Bone.SourceBoneName==Source && Bone.TargetBoneName==Target)) throw std::runtime_error("Virtual bone name or endpoint pair already exists");
 for(const auto& Socket:Skeleton->Sockets) if(Socket && Socket->SocketName==Name) throw std::runtime_error("Virtual bone name collides with skeleton socket");
 bool Saved=false;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Create Virtual Bone")));
  if(!Skeleton->AddNewNamedVirtualBone(Source,Target,Name)) { Transaction.Cancel(); throw std::runtime_error("Native virtual bone creation rejected request"); }
  RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty();
  if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Virtual bone created but Skeleton save failed"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("name"),Name.ToString()); J->WriteValue(TEXT("source"),Source.ToString()); J->WriteValue(TEXT("target"),Target.ToString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::DeleteVirtualBones(const FVirtualBoneReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.Names.IsEmpty() || R.Names.Num()>256) throw std::runtime_error("Virtual bone deletion requires stopped PIE, confirmed /Game Skeleton and 1..256 names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || Skeleton->GetVirtualBones().Num()>256) throw std::runtime_error("Asset must be persistent Skeleton with <=256 virtual bones");
 const auto& Bones=Skeleton->GetVirtualBones(); TSet<FName> Remove;
 for(const auto& Name:R.Names) { if(Name.IsEmpty() || Name.Len()>128 || Remove.Contains(FName(*Name))) throw std::runtime_error("Deletion names must be bounded and unique"); const FName Key(*Name); bool Found=false; for(const auto& Bone:Bones) if(Bone.VirtualBoneName==Key) Found=true; if(!Found) throw std::runtime_error("Requested virtual bone does not exist"); Remove.Add(Key); }
 bool Expanded=true; while(Expanded) { Expanded=false; for(const auto& Bone:Bones) if(!Remove.Contains(Bone.VirtualBoneName) && (Remove.Contains(Bone.SourceBoneName) || Remove.Contains(Bone.TargetBoneName))) { if(!R.bCascade) throw std::runtime_error("Dependent virtual bones require inclusion or explicit cascade"); Remove.Add(Bone.VirtualBoneName); Expanded=true; } }
 for(const auto& Socket:Skeleton->Sockets) if(Socket && Remove.Contains(Socket->BoneName)) throw std::runtime_error("Reparent or delete skeleton sockets attached to removed virtual bones first");
 TArray<FName> Ordered; TSet<FName> Pending=Remove;
 while(!Pending.IsEmpty())
 {
  bool Progress=false;
  for(const auto& Bone:Bones) if(Pending.Contains(Bone.VirtualBoneName)) { bool Dependent=false; for(const auto& Other:Bones) if(Pending.Contains(Other.VirtualBoneName) && Other.VirtualBoneName!=Bone.VirtualBoneName && (Other.SourceBoneName==Bone.VirtualBoneName || Other.TargetBoneName==Bone.VirtualBoneName)) { Dependent=true; break; } if(!Dependent) { Ordered.Add(Bone.VirtualBoneName); Pending.Remove(Bone.VirtualBoneName); Progress=true; } }
  if(!Progress) throw std::runtime_error("Virtual bone dependency cycle prevents ordered deletion");
 }
 int32 AttachmentCount=0; for(int32 Index=0;Index<Skeleton->PreviewAttachedAssetContainer.Num();++Index) if(Remove.Contains(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo)) ++AttachmentCount;
 bool Saved=false; if(!R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Delete Virtual Bones"))); Skeleton->Modify(); for(int32 Index=Skeleton->PreviewAttachedAssetContainer.Num()-1;Index>=0;--Index) if(Remove.Contains(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo)) Skeleton->PreviewAttachedAssetContainer.RemoveAtSwap(Index); Skeleton->RemoveVirtualBones(Ordered); RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Virtual bones deleted but Skeleton save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("deleted"),!R.bDryRun); J->WriteValue(TEXT("preview_attachment_removal_count"),AttachmentCount); J->WriteValue(TEXT("saved"),Saved); J->WriteArrayStart(TEXT("removal_order")); for(const auto Name:Ordered) J->WriteValue(Name.ToString()); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Native virtual bone removal/rebuild; external animation and mesh socket references are not rewritten or saved.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::RenameVirtualBone(const FVirtualBoneReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.Name.IsEmpty() || R.Name.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Virtual bone rename requires stopped PIE, confirmed /Game Skeleton and bounded names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton");
 const FName Old(*R.Name),New(*R.NewName); if(Old.IsNone() || New.IsNone() || !VirtualBoneNameHelpers::CheckVirtualBonePrefix(New.ToString())) throw std::runtime_error("Rename requires native VB-prefixed destination");
 int32 Found=0,DependentSources=0,DependentTargets=0; for(const auto& Bone:Skeleton->GetVirtualBones()) { if(Bone.VirtualBoneName==Old) ++Found; if(Bone.SourceBoneName==Old) ++DependentSources; if(Bone.TargetBoneName==Old) ++DependentTargets; }
 if(Found!=1) throw std::runtime_error("Rename requires exactly one existing virtual bone");
 auto* VirtualProperty=FindFProperty<FArrayProperty>(USkeleton::StaticClass(),TEXT("VirtualBones")); const auto* VirtualInner=VirtualProperty ? CastField<FStructProperty>(VirtualProperty->Inner) : nullptr;
 if(!VirtualInner || VirtualInner->Struct!=FVirtualBone::StaticStruct()) throw std::runtime_error("Native virtual bone array layout unavailable for target dependency rename");
 if(Old!=New && Skeleton->GetReferenceSkeleton().FindBoneIndex(New)!=INDEX_NONE) throw std::runtime_error("Destination collides with existing bone");
 int32 SocketCount=0; for(const auto& Socket:Skeleton->Sockets) if(Socket) { if(Old!=New && Socket->SocketName==New) throw std::runtime_error("Destination collides with skeleton socket name"); if(Socket->BoneName==Old) ++SocketCount; }
 bool Saved=false;
 if(!R.bDryRun && Old!=New)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Rename Virtual Bone"))); Skeleton->Modify();
  for(const auto& Socket:Skeleton->Sockets) if(Socket && Socket->BoneName==Old) { Socket->SetFlags(RF_Transactional); Socket->Modify(); Socket->BoneName=New; Socket->PostEditChange(); }
  FScriptArrayHelper VirtualRows(VirtualProperty,VirtualProperty->ContainerPtrToValuePtr<void>(Skeleton));
  for(int32 Index=0;Index<VirtualRows.Num();++Index) { auto* Bone=reinterpret_cast<FVirtualBone*>(VirtualRows.GetRawPtr(Index)); if(Bone->TargetBoneName==Old) Bone->TargetBoneName=New; }
  for(int32 Index=0;Index<Skeleton->PreviewAttachedAssetContainer.Num();++Index) if(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo==Old) Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo=New;
  Skeleton->RenameVirtualBone(Old,New); RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty();
 }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Virtual bone rename completed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("old_name"),Old.ToString()); J->WriteValue(TEXT("new_name"),New.ToString()); J->WriteValue(TEXT("would_change"),Old!=New); J->WriteValue(TEXT("socket_attachment_count"),SocketCount); J->WriteValue(TEXT("dependent_source_count"),DependentSources); J->WriteValue(TEXT("dependent_target_count"),DependentTargets); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Native virtual bone/source rename with typed target dependency updates and Skeleton socket reparenting; external animation and mesh-only references are not rewritten or saved.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::RenameSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Socket rename requires stopped PIE, confirmed /Game Skeleton and bounded names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton");
 const FName Old(*R.SocketName),New(*R.NewName); if(Old.IsNone() || New.IsNone()) throw std::runtime_error("Socket names cannot be None");
 USkeletalMeshSocket* Socket=nullptr; int32 Matches=0;
 for(const auto& Entry:Skeleton->Sockets) if(Entry) { if(Entry->SocketName==Old) { Socket=Entry.Get(); ++Matches; } else if(Entry->SocketName==New) throw std::runtime_error("Destination socket already exists"); }
 if(Matches!=1 || (Old!=New && Skeleton->GetReferenceSkeleton().FindBoneIndex(New)!=INDEX_NONE)) throw std::runtime_error("Rename requires exactly one source socket and unused non-bone destination");
 int32 Attachments=0; for(int32 Index=0;Index<Skeleton->PreviewAttachedAssetContainer.Num();++Index) if(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo==Old) ++Attachments;
 bool Saved=false;
 if(!R.bDryRun && Old!=New)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Rename Skeleton Socket"))); Skeleton->Modify(); Socket->SetFlags(RF_Transactional); Socket->Modify(); Socket->SocketName=New;
  for(int32 Index=0;Index<Skeleton->PreviewAttachedAssetContainer.Num();++Index) if(Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo==Old) Skeleton->PreviewAttachedAssetContainer[Index].AttachedTo=New;
  Socket->PostEditChange(); Skeleton->PostEditChange(); RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty();
 }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Socket rename completed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("old_name"),Old.ToString()); J->WriteValue(TEXT("new_name"),New.ToString()); J->WriteValue(TEXT("would_change"),Old!=New); J->WriteValue(TEXT("preview_attachment_count"),Attachments); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Skeleton socket and Skeleton preview attachment names only; external component/Blueprint/mesh-only references are not rewritten.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditMeshSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128 || R.BoneName.IsEmpty() || R.BoneName.Len()>128) throw std::runtime_error("Socket authoring requires stopped PIE, confirmed /Game SkeletalMesh and bounded names");
 if(R.Operation!=TEXT("create") && R.Operation!=TEXT("update")) throw std::runtime_error("Socket operation requires create or update");
 auto Bounded=[](const FVector& V,double Limit) { return !V.ContainsNaN() && FMath::Abs(V.X)<=Limit && FMath::Abs(V.Y)<=Limit && FMath::Abs(V.Z)<=Limit; };
 if(!Bounded(R.Location,1.e8) || !Bounded(R.Scale,1.e4) || R.Rotation.ContainsNaN() || FMath::Abs(R.Rotation.Pitch)>360000 || FMath::Abs(R.Rotation.Yaw)>360000 || FMath::Abs(R.Rotation.Roll)>360000) throw std::runtime_error("Socket transform must be finite and bounded");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("SkeletalMesh must exist in registry");
 auto* Skeleton=LoadObject<USkeletalMesh>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent SkeletalMesh");
 const FName Name(*R.SocketName),Bone(*R.BoneName); if(Name.IsNone() || Bone.IsNone() || Skeleton->GetRefSkeleton().FindBoneIndex(Bone)==INDEX_NONE) throw std::runtime_error("Socket name and existing bone required");
 USkeletalMeshSocket* Existing=nullptr; int32 Matches=0; for(const auto& SocketEntry:Skeleton->GetMeshOnlySocketList()) if(auto* Socket=SocketEntry.Get()) if(Socket && Socket->SocketName==Name) { Existing=Socket; ++Matches; }
 if(Matches>1 || (R.Operation==TEXT("create") && Existing) || (R.Operation==TEXT("update") && !Existing)) throw std::runtime_error("Socket create requires unused name; update requires exactly one existing mesh socket");
 if(R.Operation==TEXT("create") && (Skeleton->GetMeshOnlySocketList().Num()>=1024 || Skeleton->GetRefSkeleton().FindBoneIndex(Name)!=INDEX_NONE)) throw std::runtime_error("Socket count exceeds bound or name collides with bone");
 const bool Changed=!Existing || Existing->BoneName!=Bone || Existing->RelativeLocation!=R.Location || Existing->RelativeRotation!=R.Rotation || Existing->RelativeScale!=R.Scale || Existing->bForceAlwaysAnimated!=R.bForceAlwaysAnimated; bool Saved=false;
 if(!R.bDryRun && Changed)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Mesh Socket"))); Skeleton->Modify();
  auto* Socket=Existing; if(!Socket) { Socket=NewObject<USkeletalMeshSocket>(Skeleton,NAME_None,RF_Transactional); Skeleton->GetMeshOnlySocketList().Add(Socket); } else { Socket->SetFlags(RF_Transactional); Socket->Modify(); }
  Socket->SocketName=Name; Socket->BoneName=Bone; Socket->RelativeLocation=R.Location; Socket->RelativeRotation=R.Rotation; Socket->RelativeScale=R.Scale; Socket->bForceAlwaysAnimated=R.bForceAlwaysAnimated; Socket->PostEditChange(); Skeleton->RebuildSocketMap(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty();
 }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Socket edit completed but SkeletalMesh save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::DeleteMeshSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128) throw std::runtime_error("Socket deletion requires stopped PIE, confirmed /Game SkeletalMesh and bounded socket name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("SkeletalMesh must exist in registry");
 auto* Skeleton=LoadObject<USkeletalMesh>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent SkeletalMesh");
 const FName Name(*R.SocketName); int32 Found=INDEX_NONE,Count=0;
 for(int32 Index=0;Index<Skeleton->GetMeshOnlySocketList().Num();++Index) if(Skeleton->GetMeshOnlySocketList()[Index] && Skeleton->GetMeshOnlySocketList()[Index]->SocketName==Name) { Found=Index; ++Count; }
 if(Name.IsNone() || Count!=1) throw std::runtime_error("Deletion requires exactly one existing mesh-owned socket");
 int32 AttachmentCount=0; for(int32 Index=0;Index<Skeleton->GetPreviewAttachedAssetContainer().Num();++Index) if(Skeleton->GetPreviewAttachedAssetContainer()[Index].AttachedTo==Name) ++AttachmentCount;
 bool Saved=false;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Delete Mesh Socket"))); Skeleton->Modify(); auto* Socket=Skeleton->GetMeshOnlySocketList()[Found].Get(); Socket->SetFlags(RF_Transactional); Socket->Modify(); Skeleton->GetMeshOnlySocketList().RemoveAt(Found); for(int32 Index=Skeleton->GetPreviewAttachedAssetContainer().Num()-1;Index>=0;--Index) if(Skeleton->GetPreviewAttachedAssetContainer()[Index].AttachedTo==Name) Skeleton->GetPreviewAttachedAssetContainer().RemoveAtSwap(Index); Skeleton->RebuildSocketMap(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty();
  if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Socket deleted but SkeletalMesh save failed"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("deleted"),!R.bDryRun); J->WriteValue(TEXT("preview_attachment_removal_count"),AttachmentCount); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Removes mesh-owned socket and matching mesh preview attachments; shared Skeleton sockets and external attachment names are not rewritten.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::RenameMeshSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Socket rename requires stopped PIE, confirmed /Game SkeletalMesh and bounded names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("SkeletalMesh must exist in registry");
 auto* Skeleton=LoadObject<USkeletalMesh>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent SkeletalMesh");
 const FName Old(*R.SocketName),New(*R.NewName); if(Old.IsNone() || New.IsNone()) throw std::runtime_error("Socket names cannot be None");
 USkeletalMeshSocket* Socket=nullptr; int32 Matches=0;
 for(const auto& Entry:Skeleton->GetMeshOnlySocketList()) if(Entry) { if(Entry->SocketName==Old) { Socket=Entry.Get(); ++Matches; } else if(Entry->SocketName==New) throw std::runtime_error("Destination socket already exists"); }
 if(Matches!=1 || (Old!=New && Skeleton->GetRefSkeleton().FindBoneIndex(New)!=INDEX_NONE)) throw std::runtime_error("Rename requires exactly one source socket and unused non-bone destination");
 int32 Attachments=0; for(int32 Index=0;Index<Skeleton->GetPreviewAttachedAssetContainer().Num();++Index) if(Skeleton->GetPreviewAttachedAssetContainer()[Index].AttachedTo==Old) ++Attachments;
 bool Saved=false;
 if(!R.bDryRun && Old!=New)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Rename Mesh Socket"))); Skeleton->Modify(); Socket->SetFlags(RF_Transactional); Socket->Modify(); Socket->SocketName=New;
  for(int32 Index=0;Index<Skeleton->GetPreviewAttachedAssetContainer().Num();++Index) if(Skeleton->GetPreviewAttachedAssetContainer()[Index].AttachedTo==Old) Skeleton->GetPreviewAttachedAssetContainer()[Index].AttachedTo=New;
  Socket->PostEditChange(); Skeleton->RebuildSocketMap(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty();
 }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Socket rename completed but SkeletalMesh save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("old_name"),Old.ToString()); J->WriteValue(TEXT("new_name"),New.ToString()); J->WriteValue(TEXT("would_change"),Old!=New); J->WriteValue(TEXT("preview_attachment_count"),Attachments); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Mesh socket and mesh preview attachment names only; external component/Blueprint/shared Skeleton references are not rewritten.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::InspectMeshSockets(const FString& AssetPath)
{
 if(!IsInGameThread() || AssetPath.IsEmpty() || AssetPath.Len()>1024 || AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(AssetPath)) throw std::runtime_error("Mesh socket inspection requires bounded full asset object path");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(AssetPath)).IsValid()) throw std::runtime_error("SkeletalMesh must exist in registry");
 auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*AssetPath); if(!IsValid(Mesh) || Mesh->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent SkeletalMesh");
 auto* Skeleton=Mesh->GetSkeleton(); const auto& Local=Mesh->GetMeshOnlySocketList(); const int32 SharedCount=Skeleton ? Skeleton->Sockets.Num() : 0;
 TSet<FName> LocalNames; for(const auto& Socket:Local) if(Socket) LocalNames.Add(Socket->SocketName);
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Mesh->GetPathName()); J->WriteValue(TEXT("skeleton_path"),GetPathNameSafe(Skeleton)); J->WriteValue(TEXT("dirty"),Mesh->GetOutermost()->IsDirty()); WritePreviewAttachments(J,TEXT("mesh_preview_attachments"),Mesh->GetPreviewAttachedAssetContainer(),Skeleton,Mesh); if(Skeleton) WritePreviewAttachments(J,TEXT("skeleton_preview_attachments"),Skeleton->PreviewAttachedAssetContainer,Skeleton,Mesh); J->WriteValue(TEXT("mesh_socket_count"),Local.Num()); J->WriteValue(TEXT("skeleton_socket_count"),SharedCount); J->WriteValue(TEXT("truncated"),Local.Num()>256 || SharedCount>256); J->WriteArrayStart(TEXT("sockets"));
 auto Write=[&](const USkeletalMeshSocket* Socket,bool MeshOwned)
 {
  if(!IsValid(Socket)) return; const bool Overridden=!MeshOwned && LocalNames.Contains(Socket->SocketName);
  J->WriteObjectStart(); J->WriteValue(TEXT("name"),Socket->SocketName.ToString()); J->WriteValue(TEXT("owner"),MeshOwned ? TEXT("mesh") : TEXT("skeleton")); J->WriteValue(TEXT("overridden"),Overridden); J->WriteValue(TEXT("native_selected"),Mesh->FindSocket(Socket->SocketName)==Socket); J->WriteValue(TEXT("bone"),Socket->BoneName.ToString()); J->WriteValue(TEXT("bone_valid_on_mesh"),Mesh->GetRefSkeleton().FindBoneIndex(Socket->BoneName)!=INDEX_NONE); J->WriteValue(TEXT("force_always_animated"),Socket->bForceAlwaysAnimated);
  auto Vector=[&](const TCHAR* Name,const FVector& V) { J->WriteArrayStart(Name); for(double Number:{V.X,V.Y,V.Z}) { if(FMath::IsFinite(Number)) J->WriteValue(Number); else J->WriteNull(); } J->WriteArrayEnd(); };
  Vector(TEXT("location"),Socket->RelativeLocation); Vector(TEXT("rotation_pitch_yaw_roll"),FVector(Socket->RelativeRotation.Pitch,Socket->RelativeRotation.Yaw,Socket->RelativeRotation.Roll)); Vector(TEXT("scale"),Socket->RelativeScale); J->WriteObjectEnd();
 };
 for(int32 Index=0;Index<FMath::Min(Local.Num(),256);++Index) Write(Local[Index].Get(),true);
 if(Skeleton) for(int32 Index=0;Index<FMath::Min(SharedCount,256);++Index) Write(Skeleton->Sockets[Index].Get(),false);
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Mesh and shared Skeleton socket definitions with native FindSocket selection; no pose/world transform evaluation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::CustomizeMeshSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128) throw std::runtime_error("Socket customization requires stopped PIE, confirmed /Game SkeletalMesh and bounded socket name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("SkeletalMesh must exist in registry");
 auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*R.AssetPath); if(!IsValid(Mesh) || Mesh->HasAnyFlags(RF_Transient) || !IsValid(Mesh->GetSkeleton()) || Mesh->GetMeshOnlySocketList().Num()>=1024) throw std::runtime_error("Asset must be persistent SkeletalMesh with Skeleton and <1024 local sockets");
 const FName Name(*R.SocketName); if(Name.IsNone()) throw std::runtime_error("Socket name cannot be None");
 for(const auto& Socket:Mesh->GetMeshOnlySocketList()) if(Socket && Socket->SocketName==Name) throw std::runtime_error("Mesh override already exists");
 USkeletalMeshSocket* Source=nullptr; int32 Count=0; for(const auto& Socket:Mesh->GetSkeleton()->Sockets) if(Socket && Socket->SocketName==Name) { Source=Socket.Get(); ++Count; }
 if(Count!=1 || Mesh->GetRefSkeleton().FindBoneIndex(Source->BoneName)==INDEX_NONE) throw std::runtime_error("Customization requires exactly one shared Skeleton socket with valid mesh bone");
 if(Source->RelativeLocation.ContainsNaN() || Source->RelativeRotation.ContainsNaN() || Source->RelativeScale.ContainsNaN()) throw std::runtime_error("Source socket transform is nonfinite");
 bool Saved=false;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Customize Mesh Socket"))); Mesh->Modify();
  auto* Socket=DuplicateObject<USkeletalMeshSocket>(Source,Mesh); Socket->SetFlags(RF_Transactional); Mesh->GetMeshOnlySocketList().Add(Socket); Socket->PostEditChange(); Mesh->RebuildSocketMap(); Mesh->PostEditChange(); Mesh->MarkPackageDirty();
  if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Mesh,false); if(!Saved) throw std::runtime_error("Mesh socket customized but mesh save failed"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Mesh->GetPathName()); J->WriteValue(TEXT("skeleton_path"),Mesh->GetSkeleton()->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Mesh->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::PromoteMeshSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128) throw std::runtime_error("Socket promotion requires stopped PIE, confirmed /Game SkeletalMesh and bounded socket name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("SkeletalMesh must exist in registry");
 auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*R.AssetPath); auto* Skeleton=IsValid(Mesh) ? Mesh->GetSkeleton() : nullptr;
 if(!IsValid(Mesh) || Mesh->HasAnyFlags(RF_Transient) || !IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || !Skeleton->GetPathName().StartsWith(TEXT("/Game/")) || Skeleton->Sockets.Num()>=1024) throw std::runtime_error("Promotion requires persistent mesh and writable /Game Skeleton with <1024 sockets");
 const FName Name(*R.SocketName); USkeletalMeshSocket* Source=nullptr; int32 Count=0,SourceIndex=INDEX_NONE;
 for(int32 Index=0;Index<Mesh->GetMeshOnlySocketList().Num();++Index) if(const auto& Socket=Mesh->GetMeshOnlySocketList()[Index]) if(Socket->SocketName==Name) { Source=Socket.Get(); SourceIndex=Index; ++Count; }
 if(Name.IsNone() || Count!=1 || Skeleton->GetReferenceSkeleton().FindBoneIndex(Source->BoneName)==INDEX_NONE || Skeleton->GetReferenceSkeleton().FindBoneIndex(Name)!=INDEX_NONE) throw std::runtime_error("Promotion requires exactly one local socket, valid Skeleton parent bone and non-bone socket name");
 for(const auto& Socket:Skeleton->Sockets) if(Socket && Socket->SocketName==Name) throw std::runtime_error("Shared socket already exists; promotion does not overwrite it");
 if(Source->RelativeLocation.ContainsNaN() || Source->RelativeRotation.ContainsNaN() || Source->RelativeScale.ContainsNaN()) throw std::runtime_error("Source socket transform is nonfinite");
 bool SkeletonSaved=false,MeshSaved=false;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Promote Mesh Socket"))); Skeleton->Modify();
  auto* Socket=DuplicateObject<USkeletalMeshSocket>(Source,Skeleton); Socket->SetFlags(RF_Transactional); Skeleton->Sockets.Add(Socket); Socket->PostEditChange(); Skeleton->PostEditChange(); RefreshSkeletonSocketMaps(Skeleton); Skeleton->MarkPackageDirty();
  if(R.bRemoveLocal) { Mesh->Modify(); Source->SetFlags(RF_Transactional); Source->Modify(); Mesh->GetMeshOnlySocketList().RemoveAt(SourceIndex); Mesh->MarkPackageDirty(); }
  Mesh->RebuildSocketMap(); if(R.bRemoveLocal) Mesh->PostEditChange();
  if(R.bSave) { auto* Assets=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>(); SkeletonSaved=Assets->SaveLoadedAsset(Skeleton,false); if(R.bRemoveLocal) MeshSaved=Assets->SaveLoadedAsset(Mesh,false); if(!SkeletonSaved || (R.bRemoveLocal && !MeshSaved)) throw std::runtime_error("Socket promoted but one or more asset saves failed; inspect both dirty packages"); }
 }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Mesh->GetPathName()); J->WriteValue(TEXT("skeleton_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("promoted"),!R.bDryRun); J->WriteValue(TEXT("remove_local"),R.bRemoveLocal); J->WriteValue(TEXT("skeleton_saved"),SkeletonSaved); J->WriteValue(TEXT("mesh_saved"),MeshSaved); J->WriteValue(TEXT("skeleton_dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("mesh_dirty"),Mesh->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::InspectRuntimeSocket(const FSkeletonSocketReq& R)
{
 if(!IsInGameThread() || R.ComponentPath.IsEmpty() || R.ComponentPath.Len()>2048 || R.SocketName.IsEmpty() || R.SocketName.Len()>128) throw std::runtime_error("Runtime socket inspection requires bounded explicit component/socket names");
 auto* World=NavigationWorldUtils::Resolve(TEXT("pie"),R.PIEInstance); if(!IsValid(World) || World->WorldType!=EWorldType::PIE || World->bIsTearingDown) throw std::runtime_error("Runtime socket inspection requires selected live PIE");
 auto* Component=FindObject<USkeletalMeshComponent>(nullptr,*R.ComponentPath);
 if(!IsValid(Component) || Component->IsTemplate() || !Component->IsRegistered() || Component->GetWorld()!=World || !IsValid(Component->GetSkeletalMeshAsset())) throw std::runtime_error("Component must be registered SkeletalMeshComponent in selected PIE with mesh");
 const FName Name(*R.SocketName); auto* Mesh=Component->GetSkeletalMeshAsset(); const auto* Socket=Mesh->FindSocket(Name); if(Name.IsNone() || !IsValid(Socket) || Component->GetBoneIndex(Socket->BoneName)==INDEX_NONE) throw std::runtime_error("Named socket must resolve on mesh with valid runtime parent bone");
 ERelativeTransformSpace Space;
 if(R.Space==TEXT("world")) Space=RTS_World; else if(R.Space==TEXT("component")) Space=RTS_Component; else if(R.Space==TEXT("parent_bone")) Space=RTS_ParentBoneSpace; else throw std::runtime_error("Socket space requires world, component or parent_bone");
 const auto Transform=Component->GetSocketTransform(Name,Space); const auto Rotation=Transform.GetRotation(); const bool Finite=!Transform.ContainsNaN();
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),Component->GetPathName()); J->WriteValue(TEXT("mesh_path"),Mesh->GetPathName()); J->WriteValue(TEXT("socket_name"),Name.ToString()); J->WriteValue(TEXT("bone"),Socket->BoneName.ToString()); J->WriteValue(TEXT("socket_owner"),Socket->GetOuter()==Mesh ? TEXT("mesh") : TEXT("skeleton")); J->WriteValue(TEXT("space"),R.Space); J->WriteValue(TEXT("finite"),Finite);
 auto Number=[&](double Value) { if(FMath::IsFinite(Value)) J->WriteValue(Value); else J->WriteNull(); };
 auto Vector=[&](const TCHAR* Label,const FVector& Value) { J->WriteArrayStart(Label); Number(Value.X); Number(Value.Y); Number(Value.Z); J->WriteArrayEnd(); };
 Vector(TEXT("location"),Transform.GetLocation()); Vector(TEXT("scale"),Transform.GetScale3D()); J->WriteArrayStart(TEXT("rotation_quaternion_xyzw")); Number(Rotation.X); Number(Rotation.Y); Number(Rotation.Z); Number(Rotation.W); J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Current native evaluated pose snapshot; does not tick animation, force LOD bone evaluation, advance simulation or change attachments.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditPreviewAttachment(const FSkeletonSocketReq& R,bool MeshOwned)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PreviewAssetPath.IsEmpty() || R.PreviewAssetPath.Len()>1024 || R.PreviewAssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.PreviewAssetPath) || R.SocketName.IsEmpty() || R.SocketName.Len()>128) throw std::runtime_error("Preview attachment authoring requires stopped PIE, confirmed /Game owner, persistent preview asset and bounded attach name");
 if(R.Operation!=TEXT("add") && R.Operation!=TEXT("remove") && R.Operation!=TEXT("move")) throw std::runtime_error("Preview attachment operation requires add, remove or move");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid() || (R.Operation==TEXT("add") && !Registry.GetAssetByObjectPath(FSoftObjectPath(R.PreviewAssetPath)).IsValid())) throw std::runtime_error("Owner and preview asset must exist in registry");
 UObject* Owner=LoadObject<UObject>(nullptr,*R.AssetPath); auto* Mesh=Cast<USkeletalMesh>(Owner); auto* Skeleton=Cast<USkeleton>(Owner);
 if(!IsValid(Owner) || Owner->HasAnyFlags(RF_Transient) || (MeshOwned ? !Mesh : !Skeleton)) throw std::runtime_error("Preview owner has wrong asset type");
 UObject* Asset=nullptr;
 if(R.Operation==TEXT("add")) { Asset=LoadObject<UObject>(nullptr,*R.PreviewAssetPath); if(!IsValid(Asset) || Asset->HasAnyFlags(RF_Transient) || !Asset->IsAsset() || (!Asset->IsA<UStaticMesh>() && !Asset->IsA<USkeletalMesh>())) throw std::runtime_error("Preview attachment addition supports persistent StaticMesh or SkeletalMesh assets"); }
 const auto* PathProperty=FindFProperty<FSoftObjectProperty>(FPreviewAttachedObjectPair::StaticStruct(),TEXT("AttachedObject")); if(!PathProperty) throw std::runtime_error("Native preview soft asset layout unavailable");
 const FSoftObjectPath RequestedPath(R.PreviewAssetPath);
 auto Matches=[&](const FPreviewAttachedObjectPair& Pair) { const FSoftObjectPtr Stored=PathProperty->GetPropertyValue_InContainer(&Pair); return Stored.ToSoftObjectPath()==RequestedPath; };
 if(R.Operation==TEXT("move") && (R.NewName.IsEmpty() || R.NewName.Len()>128 || FName(*R.NewName).IsNone())) throw std::runtime_error("Preview move requires bounded destination attach name");
 const FName Destination=R.Operation==TEXT("move") ? FName(*R.NewName) : FName(*R.SocketName);
 const FName Attach(*R.SocketName); if(Attach.IsNone()) throw std::runtime_error("Attach name cannot be None");
 auto& Container=MeshOwned ? Mesh->GetPreviewAttachedAssetContainer() : Skeleton->PreviewAttachedAssetContainer;
 bool Exists=false; for(int32 Index=0;Index<Container.Num();++Index) if(Container[Index].AttachedTo==Attach && Matches(Container[Index])) Exists=true;
 if(R.Operation==TEXT("add") || R.Operation==TEXT("move"))
 {
  bool Valid=MeshOwned ? Mesh->GetRefSkeleton().FindBoneIndex(Destination)!=INDEX_NONE || Mesh->FindSocket(Destination)!=nullptr : Skeleton->GetReferenceSkeleton().FindBoneIndex(Destination)!=INDEX_NONE;
  if(!MeshOwned) for(const auto& Socket:Skeleton->Sockets) if(Socket && Socket->SocketName==Destination) Valid=true;
  if(!Valid || (R.Operation==TEXT("add") && !Exists && Container.Num()>=256)) throw std::runtime_error("Preview target must exist and attachment count remain <=256");
 }
 if(R.Operation==TEXT("move")) { if(!Exists) throw std::runtime_error("Preview move source pair does not exist"); if(Destination!=Attach) for(int32 Index=0;Index<Container.Num();++Index) if(Container[Index].AttachedTo==Destination && Matches(Container[Index])) throw std::runtime_error("Preview destination pair already exists"); }
 const bool Changed=R.Operation==TEXT("add") ? !Exists : R.Operation==TEXT("move") ? Destination!=Attach : Exists; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Edit Preview Attachment"))); Owner->Modify(); if(R.Operation==TEXT("add")) Container.AddUniqueAttachedObject(Asset,Attach); else if(R.Operation==TEXT("move")) { for(int32 Index=0;Index<Container.Num();++Index) if(Container[Index].AttachedTo==Attach && Matches(Container[Index])) Container[Index].AttachedTo=Destination; } else for(int32 Index=Container.Num()-1;Index>=0;--Index) if(Container[Index].AttachedTo==Attach && Matches(Container[Index])) Container.RemoveAtSwap(Index); Owner->PostEditChange(); Owner->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Owner,false); if(!Saved) throw std::runtime_error("Preview attachment edit completed but owner save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Owner->GetPathName()); J->WriteValue(TEXT("preview_asset"),R.PreviewAssetPath); J->WriteValue(TEXT("attach_name"),Attach.ToString()); J->WriteValue(TEXT("destination_attach_name"),Destination.ToString()); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("attachment_count"),Container.Num()); J->WriteValue(TEXT("scope"),TEXT("Persistent preview metadata only; no runtime attachment or explicit active Persona scene instantiation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::SetTranslationRetargeting(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.Bones.IsEmpty() || R.Bones.Num()>256) throw std::runtime_error("Retargeting edits require stopped PIE, confirmed /Game Skeleton and 1..256 bones");
 EBoneTranslationRetargetingMode::Type Mode;
 if(R.Mode==TEXT("Animation")) Mode=EBoneTranslationRetargetingMode::Animation; else if(R.Mode==TEXT("Skeleton")) Mode=EBoneTranslationRetargetingMode::Skeleton; else if(R.Mode==TEXT("AnimationScaled")) Mode=EBoneTranslationRetargetingMode::AnimationScaled; else if(R.Mode==TEXT("AnimationRelative")) Mode=EBoneTranslationRetargetingMode::AnimationRelative; else if(R.Mode==TEXT("OrientAndScale")) Mode=EBoneTranslationRetargetingMode::OrientAndScale; else throw std::runtime_error("Unsupported native translation retargeting mode");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton"); const auto& Reference=Skeleton->GetReferenceSkeleton();
 if(Reference.GetRawBoneNum()>4096) throw std::runtime_error("Retargeting bone count exceeds 4096");
 TSet<int32> Selected;
 for(const auto& Name:R.Bones) { if(Name.IsEmpty() || Name.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Name)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Selected.Contains(Index)) throw std::runtime_error("Bones must be unique existing raw Skeleton bones"); Selected.Add(Index); }
 TArray<int32> Affected;
 for(int32 Index=0;Index<Reference.GetRawBoneNum();++Index) { bool Include=Selected.Contains(Index); if(R.bChildren) for(int32 Parent=Reference.GetParentIndex(Index);!Include && Parent!=INDEX_NONE;Parent=Reference.GetParentIndex(Parent)) Include=Selected.Contains(Parent); if(Include) Affected.Add(Index); }
 int32 Changed=0; for(const int32 Index:Affected) if(Skeleton->GetBoneTranslationRetargetingMode(Index)!=Mode) ++Changed; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Bone Translation Retargeting"))); Skeleton->Modify(); for(const int32 Index:Affected) if(Skeleton->GetBoneTranslationRetargetingMode(Index)!=Mode) Skeleton->SetBoneTranslationRetargetingMode(Index,Mode,false); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Retargeting edit completed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("mode"),R.Mode); J->WriteValue(TEXT("affected_count"),Affected.Num()); J->WriteValue(TEXT("changed_count"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Skeleton translation retargeting settings only; no IK Retargeter graph or animation rebake.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditCompatibility(const FCompatibleSkeletonReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SourcePath.IsEmpty() || R.SourcePath.Len()>1024 || R.SourcePath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.SourcePath)) throw std::runtime_error("Compatibility edit requires stopped PIE, confirmed /Game Skeleton and bounded source object path");
 if(R.Operation!=TEXT("add") && R.Operation!=TEXT("remove")) throw std::runtime_error("Compatibility operation requires add or remove");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton owner must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 const TSoftObjectPtr<USkeleton> Source{FSoftObjectPath(R.SourcePath)}; if(Source.ToSoftObjectPath()==FSoftObjectPath(Skeleton)) throw std::runtime_error("Skeleton cannot declare itself compatible");
 const bool Exists=Skeleton->GetCompatibleSkeletons().Contains(Source);
 if(R.Operation==TEXT("add")) { if(!Registry.GetAssetByObjectPath(Source.ToSoftObjectPath()).IsValid()) throw std::runtime_error("Compatible source must exist in registry"); auto* Other=Source.LoadSynchronous(); if(!IsValid(Other) || Other->HasAnyFlags(RF_Transient) || (!Exists && Skeleton->GetCompatibleSkeletons().Num()>=256)) throw std::runtime_error("Compatible source must be persistent Skeleton and count <=256"); }
 const bool Changed=R.Operation==TEXT("add") ? !Exists : Exists; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Skeleton Compatibility"))); Skeleton->Modify(); if(R.Operation==TEXT("add")) Skeleton->AddCompatibleSkeletonSoft(Source); else Skeleton->RemoveCompatibleSkeleton(Source); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Compatibility edit completed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("source_path"),R.SourcePath); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("One-way native compatibility declaration only; does not prove bone hierarchy compatibility, retarget animations or change reciprocal source settings.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::SetCompatibilityPolicy(const FCompatibleSkeletonReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath)) throw std::runtime_error("Compatibility policy requires stopped PIE and confirmed /Game Skeleton");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton owner must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 const bool Before=Skeleton->GetUseRetargetModesFromCompatibleSkeleton(); const bool Changed=Before!=R.bUseCompatibleRetargetModes; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Compatible Skeleton Retarget Policy"))); Skeleton->Modify(); Skeleton->SetUseRetargetModesFromCompatibleSkeleton(R.bUseCompatibleRetargetModes); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Compatibility policy edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("before"),Before); J->WriteValue(TEXT("requested"),R.bUseCompatibleRetargetModes); J->WriteValue(TEXT("current"),Skeleton->GetUseRetargetModesFromCompatibleSkeleton()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),Skeleton->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::CompareHierarchy(const FCompatibleSkeletonReq& R)
{
 if(!IsInGameThread()) throw std::runtime_error("Skeleton comparison requires game thread");
 auto Load=[](const FString& Path) { if(Path.IsEmpty() || Path.Len()>1024 || Path.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(Path) || !FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(Path)).IsValid()) throw std::runtime_error("Comparison requires bounded registered Skeleton object paths"); auto* Asset=LoadObject<USkeleton>(nullptr,*Path); if(!IsValid(Asset) || Asset->HasAnyFlags(RF_Transient) || Asset->GetReferenceSkeleton().GetRawBoneNum()>4096) throw std::runtime_error("Comparison requires persistent Skeletons with <=4096 raw bones"); return Asset; };
 auto* Target=Load(R.AssetPath); auto* Source=Load(R.SourcePath); const auto& A=Target->GetReferenceSkeleton(); const auto& B=Source->GetReferenceSkeleton();
 TMap<FName,int32> TargetBones; for(int32 Index=0;Index<A.GetRawBoneNum();++Index) TargetBones.Add(A.GetBoneName(Index),Index);
 int32 Missing=0,ParentMismatch=0,PoseMismatch=0,Shared=0; TSet<FName> SourceNames;
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("target_path"),Target->GetPathName()); J->WriteValue(TEXT("source_path"),Source->GetPathName()); J->WriteValue(TEXT("target_raw_bone_count"),A.GetRawBoneNum()); J->WriteValue(TEXT("source_raw_bone_count"),B.GetRawBoneNum()); J->WriteArrayStart(TEXT("differences")); int32 Written=0,Total=0;
 auto Difference=[&](FName Bone,const TCHAR* Kind,FName SourceParent,FName TargetParent) { ++Total; if(Written++>=256) return; J->WriteObjectStart(); J->WriteValue(TEXT("bone"),Bone.ToString()); J->WriteValue(TEXT("kind"),Kind); J->WriteValue(TEXT("source_parent"),SourceParent.ToString()); J->WriteValue(TEXT("target_parent"),TargetParent.ToString()); J->WriteObjectEnd(); };
 for(int32 Index=0;Index<B.GetRawBoneNum();++Index)
 {
  const auto Name=B.GetBoneName(Index); SourceNames.Add(Name); const int32 BP=B.GetParentIndex(Index); const FName BParent=BP==INDEX_NONE ? NAME_None : B.GetBoneName(BP); const int32* Match=TargetBones.Find(Name);
  if(!Match) { ++Missing; Difference(Name,TEXT("missing_from_target"),BParent,NAME_None); continue; }
  ++Shared; const int32 AP=A.GetParentIndex(*Match); const FName AParent=AP==INDEX_NONE ? NAME_None : A.GetBoneName(AP);
  if(AParent!=BParent) { ++ParentMismatch; Difference(Name,TEXT("parent_mismatch"),BParent,AParent); }
  if(A.GetRefBonePose().IsValidIndex(*Match) && B.GetRefBonePose().IsValidIndex(Index) && !A.GetRefBonePose()[*Match].Equals(B.GetRefBonePose()[Index],1.e-4f)) { ++PoseMismatch; Difference(Name,TEXT("local_reference_pose_differs"),BParent,AParent); }
 }
 int32 TargetOnly=0; for(int32 Index=0;Index<A.GetRawBoneNum();++Index) if(!SourceNames.Contains(A.GetBoneName(Index))) ++TargetOnly;
 J->WriteArrayEnd(); J->WriteValue(TEXT("difference_count"),Total); J->WriteValue(TEXT("differences_truncated"),Total>256); J->WriteValue(TEXT("shared_bone_count"),Shared); J->WriteValue(TEXT("missing_from_target_count"),Missing); J->WriteValue(TEXT("target_only_count"),TargetOnly); J->WriteValue(TEXT("parent_mismatch_count"),ParentMismatch); J->WriteValue(TEXT("reference_pose_difference_count"),PoseMismatch); J->WriteValue(TEXT("source_hierarchy_covered"),Missing==0 && ParentMismatch==0); J->WriteValue(TEXT("scope"),TEXT("Directional raw-bone name/direct-parent and local reference-pose comparison at tolerance 0.0001; not a native animation compatibility verdict, skinning validation or retarget preview.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::SetBlendProfileScales(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128 || R.Bones.IsEmpty() || R.Bones.Num()>256 || !FMath::IsFinite(R.Scale) || R.Scale<0 || R.Scale>1000) throw std::runtime_error("Blend profile edit requires stopped PIE, confirmed /Game Skeleton, bounded profile/bones and finite scale [0,1000]");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 UBlendProfile* Profile=nullptr; int32 Matches=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.ProfileName)) { Profile=Entry.Get(); ++Matches; }
 if(Matches!=1 || Profile->OwningSkeleton!=Skeleton || Profile->GetOuter()!=Skeleton) throw std::runtime_error("Requires exactly one native owned blend profile");
 if((Profile->GetMode()==EBlendProfileMode::TimeFactor || Profile->GetMode()==EBlendProfileMode::BlendMask) && R.Scale>1.f) throw std::runtime_error("Time-factor/blend-mask scale requires [0,1]");
 const auto& Reference=Skeleton->GetReferenceSkeleton(); if(Reference.GetRawBoneNum()>4096) throw std::runtime_error("Bone count exceeds 4096"); TSet<int32> Selected;
 for(const auto& Name:R.Bones) { if(Name.IsEmpty() || Name.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Name)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Selected.Contains(Index)) throw std::runtime_error("Bones must be unique existing raw Skeleton bones"); Selected.Add(Index); }
 TArray<int32> Affected; for(int32 Index=0;Index<Reference.GetRawBoneNum();++Index) { bool Include=Selected.Contains(Index); if(R.bChildren) for(int32 Parent=Reference.GetParentIndex(Index);!Include && Parent!=INDEX_NONE;Parent=Reference.GetParentIndex(Parent)) Include=Selected.Contains(Parent); if(Include) Affected.Add(Index); }
 int32 Changed=0; for(const int32 Index:Affected) if(Profile->GetBoneBlendScale(Index)!=R.Scale) ++Changed; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Blend Profile Bone Scales"))); Skeleton->Modify(); Profile->SetFlags(RF_Transactional); Profile->Modify(); for(const int32 Index:Affected) if(Profile->GetBoneBlendScale(Index)!=R.Scale) Profile->SetBoneBlendScale(Index,R.Scale,false,true); Profile->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Blend profile edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("profile"),Profile->GetName()); J->WriteValue(TEXT("scale"),R.Scale); J->WriteValue(TEXT("affected_count"),Affected.Num()); J->WriteValue(TEXT("changed_count"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::CreateBlendProfile(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128 || R.SourceProfileName.Len()>128) throw std::runtime_error("Blend profile creation requires stopped PIE, confirmed /Game Skeleton and bounded profile name");
 EBlendProfileMode Mode; if(R.Mode==TEXT("TimeFactor")) Mode=EBlendProfileMode::TimeFactor; else if(R.Mode==TEXT("WeightFactor")) Mode=EBlendProfileMode::WeightFactor; else if(R.Mode==TEXT("BlendMask")) Mode=EBlendProfileMode::BlendMask; else throw std::runtime_error("Profile mode requires TimeFactor, WeightFactor or BlendMask");
 FText NameError; if(!FName::IsValidXName(R.ProfileName,INVALID_OBJECTNAME_CHARACTERS,&NameError) || FName(*R.ProfileName).IsNone()) throw std::runtime_error("Profile requires valid native object name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || Skeleton->BlendProfiles.Num()>=64) throw std::runtime_error("Owner must be persistent Skeleton with <64 profiles");
 if(StaticFindObjectFast(UObject::StaticClass(),Skeleton,FName(*R.ProfileName))) throw std::runtime_error("Profile destination object name already exists");
 UBlendProfile* Source=nullptr;
 if(!R.SourceProfileName.IsEmpty())
 {
  int32 Count=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.SourceProfileName)) { Source=Entry.Get(); ++Count; }
  if(Count!=1 || Source->OwningSkeleton!=Skeleton || Source->GetOuter()!=Skeleton || Source->ProfileEntries.Num()>4096) throw std::runtime_error("Duplication source must be unique native owned profile with <=4096 entries");
  Mode=Source->GetMode(); if(Mode!=EBlendProfileMode::TimeFactor && Mode!=EBlendProfileMode::WeightFactor && Mode!=EBlendProfileMode::BlendMask) throw std::runtime_error("Source has unsupported native mode");
  TSet<FName> Bones; for(const auto& Entry:Source->ProfileEntries) { if(Bones.Contains(Entry.BoneReference.BoneName) || Skeleton->GetReferenceSkeleton().FindBoneIndex(Entry.BoneReference.BoneName)==INDEX_NONE || !FMath::IsFinite(Entry.BlendScale) || Entry.BlendScale<0 || Entry.BlendScale>(Mode==EBlendProfileMode::WeightFactor ? 1000.f : 1.f)) throw std::runtime_error("Source profile contains duplicate/invalid bones or scales"); Bones.Add(Entry.BoneReference.BoneName); }
 }
 bool Saved=false; UBlendProfile* Profile=nullptr;
 if(!R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Create Blend Profile"))); Skeleton->Modify(); if(Source) { Profile=DuplicateObject<UBlendProfile>(Source,Skeleton,FName(*R.ProfileName)); Profile->SetFlags(RF_Public|RF_Transactional); Skeleton->BlendProfiles.Add(Profile); } else Profile=Skeleton->CreateNewBlendProfile(FName(*R.ProfileName)); if(!Profile) throw std::runtime_error("Native blend profile creation failed"); Profile->SetSkeleton(Skeleton); Profile->Mode=Mode; Profile->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Profile created but Skeleton save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("profile_name"),R.ProfileName); J->WriteValue(TEXT("profile_path"),GetPathNameSafe(Profile)); J->WriteValue(TEXT("mode"),StaticEnum<EBlendProfileMode>()->GetNameStringByValue(int64(Mode))); J->WriteValue(TEXT("source_profile"),R.SourceProfileName); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::RenameBlendProfile(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Blend profile rename requires stopped PIE, confirmed /Game Skeleton and bounded names");
 FText Error; if(!FName::IsValidXName(R.NewName,INVALID_OBJECTNAME_CHARACTERS,&Error) || FName(*R.NewName).IsNone()) throw std::runtime_error("Destination must be valid native object name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 const FName Old(*R.ProfileName),New(*R.NewName); UBlendProfile* Profile=nullptr; int32 Count=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==Old) { Profile=Entry.Get(); ++Count; }
 if(Count!=1 || Profile->OwningSkeleton!=Skeleton || Profile->GetOuter()!=Skeleton) throw std::runtime_error("Rename requires exactly one native owned profile");
 if(Old!=New && StaticFindObjectFast(UObject::StaticClass(),Skeleton,New)) throw std::runtime_error("Destination object name already exists"); const FString Before=Profile->GetPathName(); bool Saved=false;
 if(!R.bDryRun && Old!=New) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Rename Blend Profile"))); Skeleton->Modify(); Profile->SetFlags(RF_Transactional); Profile->Modify(); if(Skeleton->RenameBlendProfile(Old,New)!=Profile) { Transaction.Cancel(); throw std::runtime_error("Native profile rename failed"); } Profile->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Profile renamed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("before_path"),Before); J->WriteValue(TEXT("current_path"),Profile->GetPathName()); J->WriteValue(TEXT("requested_name"),R.NewName); J->WriteValue(TEXT("would_change"),Old!=New); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native owned profile object rename; no redirector or external soft-path/string-reference migration.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::ResetBlendProfileEntries(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128 || R.Bones.IsEmpty() || R.Bones.Num()>256) throw std::runtime_error("Blend profile edit requires stopped PIE, confirmed /Game Skeleton, bounded profile/bones");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 UBlendProfile* Profile=nullptr; int32 Matches=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.ProfileName)) { Profile=Entry.Get(); ++Matches; }
 if(Matches!=1 || Profile->OwningSkeleton!=Skeleton || Profile->GetOuter()!=Skeleton) throw std::runtime_error("Requires exactly one native owned blend profile");
 const auto& Reference=Skeleton->GetReferenceSkeleton(); if(Reference.GetRawBoneNum()>4096) throw std::runtime_error("Bone count exceeds 4096"); TSet<int32> Selected;
 for(const auto& Name:R.Bones) { if(Name.IsEmpty() || Name.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Name)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Selected.Contains(Index)) throw std::runtime_error("Bones must be unique existing raw Skeleton bones"); Selected.Add(Index); }
 TArray<int32> Affected; for(int32 Index=0;Index<Reference.GetRawBoneNum();++Index) { bool Include=Selected.Contains(Index); if(R.bChildren) for(int32 Parent=Reference.GetParentIndex(Index);!Include && Parent!=INDEX_NONE;Parent=Reference.GetParentIndex(Parent)) Include=Selected.Contains(Parent); if(Include) Affected.Add(Index); }
 int32 Changed=0; for(const int32 Index:Affected) if(Profile->GetEntryIndex(Reference.GetBoneName(Index))!=INDEX_NONE) ++Changed; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Reset Blend Profile Entries"))); Skeleton->Modify(); Profile->SetFlags(RF_Transactional); Profile->Modify(); for(const int32 Index:Affected) if(Profile->GetEntryIndex(Reference.GetBoneName(Index))!=INDEX_NONE) Profile->RemoveEntry(Index); Profile->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Blend profile edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("profile"),Profile->GetName()); J->WriteValue(TEXT("default_scale"),Profile->GetDefaultBlendScale()); J->WriteValue(TEXT("affected_count"),Affected.Num()); J->WriteValue(TEXT("changed_count"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteObjectEnd(); J->Close(); return Result;
}


FString SkeletonUtils::SetBlendProfileMode(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128) throw std::runtime_error("Profile mode editing requires stopped PIE, confirmed /Game Skeleton and bounded profile name");
 EBlendProfileMode Mode; if(R.Mode==TEXT("TimeFactor")) Mode=EBlendProfileMode::TimeFactor; else if(R.Mode==TEXT("WeightFactor")) Mode=EBlendProfileMode::WeightFactor; else if(R.Mode==TEXT("BlendMask")) Mode=EBlendProfileMode::BlendMask; else throw std::runtime_error("Mode requires TimeFactor, WeightFactor or BlendMask");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 UBlendProfile* Profile=nullptr; int32 Count=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.ProfileName)) { Profile=Entry.Get(); ++Count; }
 if(Count!=1 || Profile->OwningSkeleton!=Skeleton || Profile->GetOuter()!=Skeleton || Profile->ProfileEntries.Num()>4096) throw std::runtime_error("Requires unique native owned profile with <=4096 entries");
 for(const auto& Entry:Profile->ProfileEntries) if(!FMath::IsFinite(Entry.BlendScale) || Entry.BlendScale<0 || Entry.BlendScale>(Mode==EBlendProfileMode::WeightFactor ? 1000.f : 1.f)) throw std::runtime_error("Existing scale violates requested mode; edit scales before changing mode");
 const auto Before=Profile->GetMode(); const bool Changed=Before!=Mode; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Blend Profile Mode"))); Skeleton->Modify(); Profile->SetFlags(RF_Transactional); Profile->Modify(); Profile->Mode=Mode; Profile->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Profile mode edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("profile"),Profile->GetName()); J->WriteValue(TEXT("before_mode"),StaticEnum<EBlendProfileMode>()->GetNameStringByValue(int64(Before))); J->WriteValue(TEXT("requested_mode"),R.Mode); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("default_scale"),Profile->GetDefaultBlendScale()); J->WriteValue(TEXT("scope"),TEXT("Changes profile interpretation, including implicit default scale; existing consumer graph compatibility is not recompiled or proven.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::InspectBlendProfileReferences(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || R.AssetPath.IsEmpty() || R.AssetPath.Len()>1024 || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128) throw std::runtime_error("Profile reference inspection requires bounded Skeleton object path/profile name");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton)) throw std::runtime_error("Asset must be Skeleton"); UBlendProfile* Profile=nullptr; int32 Count=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.ProfileName)) { Profile=Entry.Get(); ++Count; } if(Count!=1) throw std::runtime_error("Requires exactly one named profile");
 TSet<UObject*> Ignore; Ignore.Add(Skeleton); Ignore.Add(Profile); const TArray<UObject*> Targets={Profile}; auto References=FReferencerFinder::GetAllReferencers(Targets,&Ignore,EReferencerFinderFlags::SkipWeakReferences); References.RemoveAll([](const UObject* Object){ return !Object || Object->GetOutermost()==GetTransientPackage() || Object->HasAnyFlags(RF_Transient); }); /* the undo buffer (TransBuffer) and other transient holders are not asset users */
 TArray<FName> Packages; Registry.GetReferencers(Skeleton->GetOutermost()->GetFName(),Packages); Packages.Sort(FNameLexicalLess());
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("profile_path"),Profile->GetPathName()); J->WriteValue(TEXT("loaded_referencer_count"),References.Num()); J->WriteValue(TEXT("loaded_referencers_truncated"),References.Num()>256); J->WriteArrayStart(TEXT("loaded_referencers")); for(int32 Index=0;Index<FMath::Min(References.Num(),256);++Index) if(IsValid(References[Index])) { J->WriteObjectStart(); J->WriteValue(TEXT("path"),References[Index]->GetPathName()); J->WriteValue(TEXT("class"),References[Index]->GetClass()->GetPathName()); J->WriteObjectEnd(); } J->WriteArrayEnd();
 J->WriteValue(TEXT("owner_package_referencer_count"),Packages.Num()); J->WriteValue(TEXT("package_referencers_truncated"),Packages.Num()>256); J->WriteArrayStart(TEXT("owner_package_referencers")); for(int32 Index=0;Index<FMath::Min(Packages.Num(),256);++Index) J->WriteValue(Packages[Index].ToString()); J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Loaded strong object referencers exclude owner/profile; package references are Skeleton-wide, not profile-specific. Missing unloaded or string/soft references cannot be ruled out; this is not deletion authorization.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::DeleteBlendProfile(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.IsEmpty() || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128) throw std::runtime_error("Profile deletion requires stopped PIE, confirmed /Game Skeleton and bounded profile name");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton");
 UBlendProfile* Profile=nullptr; int32 Count=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.ProfileName)) { Profile=Entry.Get(); ++Count; } if(Count!=1 || Profile->OwningSkeleton!=Skeleton || Profile->GetOuter()!=Skeleton) throw std::runtime_error("Deletion requires exactly one native owned profile");
 const FString Path=Profile->GetPathName(); TSet<UObject*> Ignore; Ignore.Add(Skeleton); Ignore.Add(Profile); const TArray<UObject*> Targets={Profile}; auto References=FReferencerFinder::GetAllReferencers(Targets,&Ignore,EReferencerFinderFlags::SkipWeakReferences); References.RemoveAll([](const UObject* Object){ return !Object || Object->GetOutermost()==GetTransientPackage() || Object->HasAnyFlags(RF_Transient); }); /* the undo buffer (TransBuffer) and other transient holders are not asset users */ TArray<FName> Packages; Registry.GetReferencers(Skeleton->GetOutermost()->GetFName(),Packages); Packages.Remove(Skeleton->GetOutermost()->GetFName());
 const bool Referenced=!References.IsEmpty() || !Packages.IsEmpty(); const bool Blocked=Referenced && !R.bAllowReferenced;
 bool Saved=false; if(!R.bDryRun) { if(Blocked) throw std::runtime_error("Loaded profile references or Skeleton-wide package dependencies found; inspect references and explicitly allow referenced deletion to proceed"); FScopedTransaction Transaction(FText::FromString(TEXT("MCP Delete Blend Profile"))); Skeleton->Modify(); Profile->SetFlags(RF_Transactional); Profile->Modify(); Skeleton->BlendProfiles.Remove(Profile); /* free the name: the garbage object otherwise stays under the Skeleton until GC, so re-creating a profile with that name failed */ Profile->Rename(nullptr,GetTransientPackage(),REN_DontCreateRedirectors); Profile->MarkAsGarbage(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Profile deleted but Skeleton save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("profile_path"),Path); J->WriteValue(TEXT("loaded_referencer_count"),References.Num()); J->WriteValue(TEXT("owner_package_referencer_count"),Packages.Num()); J->WriteValue(TEXT("blocked_by_references"),Blocked); J->WriteValue(TEXT("allow_referenced"),R.bAllowReferenced); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("deleted"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native editor-style removal and garbage marking; external references are not rewritten or saved. Registry dependencies are Skeleton-wide; soft/string/unloaded profile references may be absent. Undo/garbage collection behavior requires deferred verification.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::InspectBlendProfileScales(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || R.AssetPath.IsEmpty() || R.AssetPath.Len()>1024 || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.ProfileName.IsEmpty() || R.ProfileName.Len()>128 || R.Bones.Num()>256) throw std::runtime_error("Scale inspection requires bounded Skeleton path/profile and <=256 bone names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton)) throw std::runtime_error("Asset must be Skeleton"); UBlendProfile* Profile=nullptr; int32 Count=0; for(const auto& Entry:Skeleton->BlendProfiles) if(Entry && Entry->GetFName()==FName(*R.ProfileName)) { Profile=Entry.Get(); ++Count; }
 if(Count!=1 || Profile->OwningSkeleton!=Skeleton || Profile->GetOuter()!=Skeleton || Profile->ProfileEntries.Num()>4096) throw std::runtime_error("Requires unique native owned profile with <=4096 entries");
 const auto& Reference=Skeleton->GetReferenceSkeleton(); TArray<int32> Bones; TSet<int32> Seen;
 if(R.Bones.IsEmpty()) for(int32 Index=0;Index<FMath::Min(Reference.GetRawBoneNum(),256);++Index) Bones.Add(Index);
 else for(const auto& Name:R.Bones) { if(Name.IsEmpty() || Name.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Name)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Seen.Contains(Index)) throw std::runtime_error("Requested bones must be unique existing raw bones"); Seen.Add(Index); Bones.Add(Index); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("profile_path"),Profile->GetPathName()); J->WriteValue(TEXT("mode"),StaticEnum<EBlendProfileMode>()->GetNameStringByValue(int64(Profile->GetMode()))); J->WriteValue(TEXT("default_scale"),Profile->GetDefaultBlendScale()); J->WriteValue(TEXT("raw_bone_count"),Reference.GetRawBoneNum()); J->WriteValue(TEXT("truncated"),R.Bones.IsEmpty() && Reference.GetRawBoneNum()>256); J->WriteArrayStart(TEXT("bones"));
 for(const int32 Index:Bones) { const FName Name=Reference.GetBoneName(Index); const int32 EntryIndex=Profile->GetEntryIndex(Name); const float Scale=Profile->GetBoneBlendScale(Index); J->WriteObjectStart(); J->WriteValue(TEXT("name"),Name.ToString()); J->WriteValue(TEXT("index"),Index); J->WriteValue(TEXT("explicit_entry"),EntryIndex!=INDEX_NONE); J->WriteValue(TEXT("entry_index"),EntryIndex); if(FMath::IsFinite(Scale)) J->WriteValue(TEXT("effective_scale"),Scale); else J->WriteNull(TEXT("effective_scale")); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native profile lookup by current Skeleton bone indices; no blend evaluation or cache refresh is forced.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::InspectRetargetPose(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || R.AssetPath.IsEmpty() || R.AssetPath.Len()>1024 || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.IsEmpty() || R.PoseName.Len()>128 || R.Bones.Num()>256) throw std::runtime_error("Retarget pose inspection requires bounded registered Skeleton path/pose and <=256 bones");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton)) throw std::runtime_error("Asset must be Skeleton"); const auto* Pose=Skeleton->AnimRetargetSources.Find(FName(*R.PoseName)); if(!Pose) throw std::runtime_error("Named retarget source does not exist"); const auto& Reference=Skeleton->GetReferenceSkeleton();
 TArray<int32> Bones; TSet<int32> Seen; if(R.Bones.IsEmpty()) for(int32 Index=0;Index<FMath::Min(Reference.GetRawBoneNum(),256);++Index) Bones.Add(Index); else for(const auto& Name:R.Bones) { if(Name.IsEmpty() || Name.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Name)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Seen.Contains(Index)) throw std::runtime_error("Requested bones must be unique existing raw bones"); Seen.Add(Index); Bones.Add(Index); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("pose_name"),R.PoseName); J->WriteValue(TEXT("source_mesh"),Pose->SourceReferenceMesh.ToSoftObjectPath().ToString()); J->WriteValue(TEXT("transform_count"),Pose->ReferencePose.Num()); J->WriteValue(TEXT("raw_bone_count"),Reference.GetRawBoneNum()); J->WriteValue(TEXT("truncated"),R.Bones.IsEmpty() && Reference.GetRawBoneNum()>256); J->WriteArrayStart(TEXT("bones"));
 for(const int32 Index:Bones) { J->WriteObjectStart(); J->WriteValue(TEXT("name"),Reference.GetBoneName(Index).ToString()); J->WriteValue(TEXT("index"),Index); J->WriteValue(TEXT("available"),Pose->ReferencePose.IsValidIndex(Index)); if(Pose->ReferencePose.IsValidIndex(Index)) WriteBoneTransform(J,TEXT("local_transform"),Pose->ReferencePose[Index]); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Stored named retarget reference pose; no source mesh loading, pose rebuilding or animation evaluation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditRetargetSource(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.IsEmpty() || R.PoseName.Len()>128 || R.SourceMeshPath.IsEmpty() || R.SourceMeshPath.Len()>1024 || R.SourceMeshPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.SourceMeshPath)) throw std::runtime_error("Retarget source authoring requires stopped PIE, confirmed /Game Skeleton and bounded pose/mesh paths");
 if(R.Operation!=TEXT("create") && R.Operation!=TEXT("refresh")) throw std::runtime_error("Retarget source operation requires create or refresh");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid() || !Registry.GetAssetByObjectPath(FSoftObjectPath(R.SourceMeshPath)).IsValid()) throw std::runtime_error("Skeleton and mesh must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*R.SourceMeshPath);
 if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || !IsValid(Mesh) || Mesh->HasAnyFlags(RF_Transient) || Mesh->GetSkeleton()!=Skeleton || Skeleton->GetReferenceSkeleton().GetNum()>4096 || Mesh->GetRefSkeleton().GetNum()>4096) throw std::runtime_error("Source mesh must use exact persistent owner Skeleton with <=4096 bones");
 const FName Name(*R.PoseName); const auto* Existing=Skeleton->AnimRetargetSources.Find(Name);
 if(Name.IsNone() || (R.Operation==TEXT("create") && (Existing || Skeleton->AnimRetargetSources.Num()>=64)) || (R.Operation==TEXT("refresh") && !Existing)) throw std::runtime_error("Create requires unused pose and <64 sources; refresh requires existing pose");
 TArray<FTransform> Prepared; FAnimationRuntime::MakeSkeletonRefPoseFromMesh(Mesh,Skeleton,Prepared); if(Prepared.IsEmpty()) throw std::runtime_error("Native source pose rebuild produced no transforms"); for(const auto& Transform:Prepared) if(Transform.ContainsNaN()) throw std::runtime_error("Native source pose contains nonfinite transform");
 bool Changed=!Existing || Existing->SourceReferenceMesh.ToSoftObjectPath()!=FSoftObjectPath(Mesh) || Existing->ReferencePose.Num()!=Prepared.Num(); if(Existing && !Changed) for(int32 Index=0;Index<Prepared.Num();++Index) if(!Existing->ReferencePose[Index].Equals(Prepared[Index],0.f)) { Changed=true; break; }
 bool Saved=false; if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Retarget Source"))); Skeleton->Modify(); auto& Pose=Skeleton->AnimRetargetSources.FindOrAdd(Name); Pose.PoseName=Name; Pose.SourceReferenceMesh=Mesh; Skeleton->UpdateRetargetSource(Name); Skeleton->CallbackRetargetSourceChanged(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Retarget source edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("pose_name"),Name.ToString()); J->WriteValue(TEXT("source_mesh"),Mesh->GetPathName()); J->WriteValue(TEXT("transform_count"),Prepared.Num()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native stored retarget-source reference pose creation/refresh; does not rebake animation assets or edit IK Retargeters.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::SetAnimationRetargetSource(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.Len()>128) throw std::runtime_error("Animation retarget-source edit requires stopped PIE, confirmed /Game AnimSequence and bounded pose name");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Animation must exist in registry");
 auto* Sequence=LoadObject<UAnimSequence>(nullptr,*R.AssetPath); auto* Skeleton=IsValid(Sequence) ? Sequence->GetSkeleton() : nullptr; if(!IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !IsValid(Skeleton)) throw std::runtime_error("Asset must be persistent AnimSequence with Skeleton");
 const FName Name(*R.PoseName); if(!Name.IsNone() && !Skeleton->AnimRetargetSources.Contains(Name)) throw std::runtime_error("Named retarget source must exist on sequence Skeleton");
 const FName Before=Sequence->RetargetSource; const auto BeforeAsset=Sequence->GetRetargetSourceAsset().ToSoftObjectPath(); const bool Changed=Before!=Name || !BeforeAsset.IsNull(); bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Animation Retarget Source"))); Sequence->Modify(); Sequence->ClearRetargetSourceAsset(); Sequence->UpdateRetargetSourceAssetData(); Sequence->RetargetSource=Name; Sequence->PostEditChange(); Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Retarget source changed but animation save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("skeleton_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("before_name"),Before.ToString()); J->WriteValue(TEXT("before_source_mesh"),BeforeAsset.ToString()); J->WriteValue(TEXT("requested_name"),Name.ToString()); J->WriteValue(TEXT("current_name"),Sequence->RetargetSource.ToString()); J->WriteValue(TEXT("current_source_mesh"),Sequence->GetRetargetSourceAsset().ToSoftObjectPath().ToString()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Selects named Skeleton source or default None and clears per-animation source-mesh override; native property change may rebuild derived animation data. No IK Retargeter or cross-Skeleton rebake.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::SetAnimationRetargetMesh(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.SourceMeshPath.IsEmpty() || R.SourceMeshPath.Len()>1024 || R.SourceMeshPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.SourceMeshPath)) throw std::runtime_error("Animation source-mesh edit requires stopped PIE, confirmed /Game sequence and bounded mesh object path");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid() || !Registry.GetAssetByObjectPath(FSoftObjectPath(R.SourceMeshPath)).IsValid()) throw std::runtime_error("Animation and mesh must exist in registry");
 auto* Sequence=LoadObject<UAnimSequence>(nullptr,*R.AssetPath); auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*R.SourceMeshPath); auto* Skeleton=IsValid(Sequence) ? Sequence->GetSkeleton() : nullptr;
 if(!IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !IsValid(Mesh) || Mesh->HasAnyFlags(RF_Transient) || !IsValid(Skeleton) || Mesh->GetSkeleton()!=Skeleton || Skeleton->GetReferenceSkeleton().GetNum()>4096 || Mesh->GetRefSkeleton().GetNum()>4096) throw std::runtime_error("Persistent mesh must use exact sequence Skeleton with <=4096 bones");
 TArray<FTransform> Prepared; FAnimationRuntime::MakeSkeletonRefPoseFromMesh(Mesh,Skeleton,Prepared); if(Prepared.IsEmpty()) throw std::runtime_error("Native source pose rebuild produced no transforms"); for(const auto& Transform:Prepared) if(Transform.ContainsNaN()) throw std::runtime_error("Source reference pose is nonfinite");
 const auto BeforeAsset=Sequence->GetRetargetSourceAsset().ToSoftObjectPath(); const FName BeforeName=Sequence->RetargetSource; const bool SelectionChanged=BeforeAsset!=FSoftObjectPath(Mesh) || !BeforeName.IsNone(); bool Saved=false;
 if(!R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Animation Retarget Mesh"))); Sequence->Modify(); Sequence->RetargetSource=NAME_None; Sequence->SetRetargetSourceAsset(Mesh); Sequence->UpdateRetargetSourceAssetData(); Sequence->PostEditChange(); Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Retarget mesh refreshed but animation save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("before_name"),BeforeName.ToString()); J->WriteValue(TEXT("before_mesh"),BeforeAsset.ToString()); J->WriteValue(TEXT("requested_mesh"),Mesh->GetPathName()); J->WriteValue(TEXT("selection_would_change"),SelectionChanged); J->WriteValue(TEXT("pose_refresh_requested"),true); J->WriteValue(TEXT("transform_count"),Prepared.Num()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Selects/refreshed native per-sequence source-mesh pose and clears named source; repeats refresh when selection is unchanged. No animation rebake or IK retarget editing.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::InspectAnimationRetargetSource(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || R.AssetPath.IsEmpty() || R.AssetPath.Len()>1024 || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.Bones.Num()>256) throw std::runtime_error("Animation source inspection requires bounded registered sequence path and <=256 bones");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Animation must exist in registry");
 auto* Sequence=LoadObject<UAnimSequence>(nullptr,*R.AssetPath); auto* Skeleton=IsValid(Sequence) ? Sequence->GetSkeleton() : nullptr; if(!IsValid(Sequence) || !IsValid(Skeleton)) throw std::runtime_error("Asset must be AnimSequence with Skeleton");
 const auto& Reference=Skeleton->GetReferenceSkeleton(); const auto& Pose=Sequence->GetRetargetTransforms(); TArray<int32> Bones; TSet<int32> Seen;
 if(R.Bones.IsEmpty()) for(int32 Index=0;Index<FMath::Min(Reference.GetRawBoneNum(),256);++Index) Bones.Add(Index); else for(const auto& Name:R.Bones) { if(Name.IsEmpty() || Name.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Name)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Seen.Contains(Index)) throw std::runtime_error("Bone selection requires unique existing raw bones"); Seen.Add(Index); Bones.Add(Index); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("skeleton_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("named_source"),Sequence->RetargetSource.ToString()); J->WriteValue(TEXT("named_source_exists"),Sequence->RetargetSource.IsNone() || Skeleton->AnimRetargetSources.Contains(Sequence->RetargetSource)); J->WriteValue(TEXT("source_mesh"),Sequence->GetRetargetSourceAsset().ToSoftObjectPath().ToString()); J->WriteValue(TEXT("effective_source_name"),Sequence->GetRetargetTransformsSourceName().ToString()); J->WriteValue(TEXT("transform_count"),Pose.Num()); J->WriteValue(TEXT("dirty"),Sequence->GetOutermost()->IsDirty()); J->WriteValue(TEXT("truncated"),R.Bones.IsEmpty() && Reference.GetRawBoneNum()>256); J->WriteArrayStart(TEXT("bones"));
 for(const int32 Index:Bones) { J->WriteObjectStart(); J->WriteValue(TEXT("name"),Reference.GetBoneName(Index).ToString()); J->WriteValue(TEXT("index"),Index); J->WriteValue(TEXT("available"),Pose.IsValidIndex(Index)); if(Pose.IsValidIndex(Index)) WriteBoneTransform(J,TEXT("effective_reference_local"),Pose[Index]); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native GetRetargetTransforms/source-name readback, including stored mesh-pose precedence and fallback; no source mesh loading or pose refresh is forced.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::DeleteRetargetSource(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.IsEmpty() || R.PoseName.Len()>128) throw std::runtime_error("Retarget-source deletion requires stopped PIE, confirmed /Game Skeleton and bounded pose name");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); const FName Name(*R.PoseName); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || Name.IsNone() || !Skeleton->AnimRetargetSources.Contains(Name)) throw std::runtime_error("Requires persistent Skeleton and existing named retarget source");
 FARFilter Filter; Filter.ClassPaths.Add(UAnimSequence::StaticClass()->GetClassPathName()); Filter.bRecursiveClasses=true; Filter.TagsAndValues.Add(FName(TEXT("RetargetSource")),Name.ToString()); TArray<FAssetData> Candidates; Registry.GetAssets(Filter,Candidates); if(Candidates.Num()>256) throw std::runtime_error("Retarget-source candidate scan exceeds 256; narrow project references before deletion");
 TSet<FString> Consumers;
 for(const auto& Candidate:Candidates) { auto* Sequence=Cast<UAnimSequence>(Candidate.GetAsset()); if(!Sequence) throw std::runtime_error("Could not validate registry candidate animation"); if(Sequence->GetSkeleton()==Skeleton && Sequence->RetargetSource==Name) Consumers.Add(Sequence->GetPathName()); }
 for(TObjectIterator<UAnimSequence> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetSkeleton()==Skeleton && It->RetargetSource==Name) Consumers.Add(It->GetPathName());
 const bool Blocked=!Consumers.IsEmpty() && !R.bAllowReferenced; bool Saved=false;
 if(!R.bDryRun) { if(Blocked) throw std::runtime_error("Animation consumers still use this retarget source; reassign them or explicitly allow referenced deletion"); FScopedTransaction Transaction(FText::FromString(TEXT("MCP Delete Retarget Source"))); Skeleton->Modify(); Skeleton->AnimRetargetSources.Remove(Name); Skeleton->CallbackRetargetSourceChanged(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Retarget source deleted but Skeleton save failed"); } }
 TArray<FString> Sorted=Consumers.Array(); Sorted.Sort(); FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("pose_name"),Name.ToString()); J->WriteValue(TEXT("consumer_count"),Sorted.Num()); J->WriteValue(TEXT("consumers_truncated"),Sorted.Num()>256); J->WriteArrayStart(TEXT("consumers")); for(int32 Index=0;Index<FMath::Min(Sorted.Num(),256);++Index) J->WriteValue(Sorted[Index]); J->WriteArrayEnd(); J->WriteValue(TEXT("blocked_by_references"),Blocked); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("deleted"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Registry-tag candidates and currently loaded AnimSequences checked; stale/missing registry metadata or custom consumers may be absent. Referenced deletion does not rewrite animations and native missing-source fallback applies.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::RenameRetargetSource(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.IsEmpty() || R.PoseName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Retarget-source rename requires stopped PIE, confirmed /Game Skeleton and bounded pose name");
 auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); const FName Name(*R.PoseName); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || Name.IsNone() || !Skeleton->AnimRetargetSources.Contains(Name)) throw std::runtime_error("Requires persistent Skeleton and existing named retarget source");
 const FName Destination(*R.NewName); if(Destination.IsNone() || Destination==Name || Skeleton->AnimRetargetSources.Contains(Destination)) throw std::runtime_error("Rename requires distinct unused non-None destination pose name");
 FARFilter Filter; Filter.ClassPaths.Add(UAnimSequence::StaticClass()->GetClassPathName()); Filter.bRecursiveClasses=true; Filter.TagsAndValues.Add(FName(TEXT("RetargetSource")),Name.ToString()); TArray<FAssetData> Candidates; Registry.GetAssets(Filter,Candidates); if(Candidates.Num()>256) throw std::runtime_error("Retarget-source candidate scan exceeds 256; narrow project references before deletion");
 TSet<FString> Consumers;
 for(const auto& Candidate:Candidates) { auto* Sequence=Cast<UAnimSequence>(Candidate.GetAsset()); if(!Sequence) throw std::runtime_error("Could not validate registry candidate animation"); if(Sequence->GetSkeleton()==Skeleton && Sequence->RetargetSource==Name) Consumers.Add(Sequence->GetPathName()); }
 for(TObjectIterator<UAnimSequence> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetSkeleton()==Skeleton && It->RetargetSource==Name) Consumers.Add(It->GetPathName());
 TArray<UAnimSequence*> Sequences;
 if(Consumers.Num()>256) throw std::runtime_error("Consumer migration exceeds 256 sequences");
 for(const auto& Path:Consumers) { auto* Sequence=FindObject<UAnimSequence>(nullptr,*Path); if(!IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/"))) throw std::runtime_error("All migrated consumers must be persistent /Game sequences"); Sequences.Add(Sequence); }
 bool Saved=false; int32 SavedConsumers=0;
 if(!R.bDryRun)
 {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Rename Retarget Source"))); Skeleton->Modify(); FReferencePose Pose=Skeleton->AnimRetargetSources.FindChecked(Name); Pose.PoseName=Destination; Skeleton->AnimRetargetSources.Remove(Name); Skeleton->AnimRetargetSources.Add(Destination,MoveTemp(Pose));
  for(auto* Sequence:Sequences) { Sequence->Modify(); Sequence->RetargetSource=Destination; Sequence->PostEditChange(); Sequence->MarkPackageDirty(); }
  Skeleton->CallbackRetargetSourceChanged(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty();
  if(R.bSave) { auto* Assets=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>(); bool All=true; for(auto* Sequence:Sequences) { const bool Okay=Assets->SaveLoadedAsset(Sequence,false); if(Okay) ++SavedConsumers; All &= Okay; } Saved=Assets->SaveLoadedAsset(Skeleton,false); if(!Saved || !All) throw std::runtime_error("Retarget source renamed but one or more package saves failed; inspect Skeleton and consumer dirty state"); }
 }
 TArray<FString> Sorted=Consumers.Array(); Sorted.Sort(); FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("pose_name"),Name.ToString()); J->WriteValue(TEXT("consumer_count"),Sorted.Num()); J->WriteValue(TEXT("consumers_truncated"),Sorted.Num()>256); J->WriteArrayStart(TEXT("consumers")); for(int32 Index=0;Index<FMath::Min(Sorted.Num(),256);++Index) J->WriteValue(Sorted[Index]); J->WriteArrayEnd(); J->WriteValue(TEXT("new_name"),Destination.ToString()); J->WriteValue(TEXT("saved_consumer_count"),SavedConsumers); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("renamed"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Registry-tag candidates and currently loaded AnimSequences checked; stale/missing registry metadata or custom consumers may be absent. Discovered /Game sequence consumers migrate in one transaction; package saves are separate and can partially succeed.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::DuplicateRetargetSource(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.IsEmpty() || R.PoseName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Retarget-source duplication requires stopped PIE, confirmed /Game Skeleton and bounded names");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient) || Skeleton->AnimRetargetSources.Num()>=64) throw std::runtime_error("Requires persistent Skeleton with <64 retarget sources");
 const FName SourceName(*R.PoseName),Destination(*R.NewName); const auto* Source=Skeleton->AnimRetargetSources.Find(SourceName); if(!Source || Destination.IsNone() || Skeleton->AnimRetargetSources.Contains(Destination) || Source->ReferencePose.IsEmpty() || Source->ReferencePose.Num()>4096) throw std::runtime_error("Requires existing bounded source pose and unused destination");
 FReferencePose Prepared=*Source; Prepared.PoseName=Destination; for(const auto& Transform:Prepared.ReferencePose) if(Transform.ContainsNaN()) throw std::runtime_error("Source pose contains nonfinite transform"); const FString MeshPath=Prepared.SourceReferenceMesh.ToSoftObjectPath().ToString(); const int32 TransformCount=Prepared.ReferencePose.Num(); bool Saved=false;
 if(!R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Duplicate Retarget Source"))); Skeleton->Modify(); Skeleton->AnimRetargetSources.Add(Destination,MoveTemp(Prepared)); Skeleton->CallbackRetargetSourceChanged(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Retarget source duplicated but Skeleton save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("source_name"),SourceName.ToString()); J->WriteValue(TEXT("new_name"),Destination.ToString()); J->WriteValue(TEXT("source_mesh"),MeshPath); J->WriteValue(TEXT("transform_count"),TransformCount); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Copies stored named reference pose and soft source mesh link; no source mesh loading/rebuild or animation consumer migration.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditStoredRetargetPose(const FBoneRetargetReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.PoseName.IsEmpty() || R.PoseName.Len()>128 || R.PoseEdits.Num()>256 || (R.PoseEdits.IsEmpty() && !R.bClearSourceMesh && !R.bResetReferencePose)) throw std::runtime_error("Stored pose editing requires stopped PIE, confirmed /Game Skeleton, bounded pose and 1..256 edits or source-link clearing");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Owner must be persistent Skeleton"); const FName Name(*R.PoseName); auto* Existing=Skeleton->AnimRetargetSources.Find(Name); if(!Existing || Existing->ReferencePose.Num()>4096) throw std::runtime_error("Requires existing bounded stored pose");
 FReferencePose Prepared=*Existing; TSet<int32> Seen; int32 ChangedBones=0;
 if(R.bResetReferencePose)
 {
  if(!R.PoseEdits.IsEmpty() || R.Bones.IsEmpty() || R.Bones.Num()>256) throw std::runtime_error("Reference reset requires 1..256 bones and no simultaneous explicit pose edits");
  const auto& Reference=Skeleton->GetReferenceSkeleton(); const auto& Default=Reference.GetRefBonePose(); if(Reference.GetRawBoneNum()>4096) throw std::runtime_error("Reference reset bone count exceeds 4096"); TSet<int32> Selected;
  for(const auto& Bone:R.Bones) { if(Bone.IsEmpty() || Bone.Len()>128) throw std::runtime_error("Reset bone name exceeds bounds"); const int32 Index=Reference.FindBoneIndex(FName(*Bone)); if(Index<0 || Index>=Reference.GetRawBoneNum() || Selected.Contains(Index)) throw std::runtime_error("Reset requires unique existing raw bones"); Selected.Add(Index); }
  for(int32 Index=0;Index<Reference.GetRawBoneNum();++Index)
  {
   bool Include=Selected.Contains(Index); if(R.bChildren) for(int32 Parent=Reference.GetParentIndex(Index);!Include && Parent!=INDEX_NONE;Parent=Reference.GetParentIndex(Parent)) Include=Selected.Contains(Parent);
   if(!Include) continue; if(!Prepared.ReferencePose.IsValidIndex(Index) || !Default.IsValidIndex(Index) || Default[Index].ContainsNaN()) throw std::runtime_error("Reset bone must have finite default and existing stored transform");
   if(!Prepared.ReferencePose[Index].Equals(Default[Index],0.f)) { Prepared.ReferencePose[Index]=Default[Index]; ++ChangedBones; }
  }
 }
 for(const auto& Row:R.PoseEdits)
 {
  if(Row.Bone.IsEmpty() || Row.Bone.Len()>128) throw std::runtime_error("Bone name exceeds bounds"); const int32 Index=Skeleton->GetReferenceSkeleton().FindBoneIndex(FName(*Row.Bone));
  if(Index<0 || Index>=Skeleton->GetReferenceSkeleton().GetRawBoneNum() || !Prepared.ReferencePose.IsValidIndex(Index) || Seen.Contains(Index)) throw std::runtime_error("Edits require unique raw bone with stored transform"); Seen.Add(Index);
  auto Bounded=[](const FVector& V,double Max) { return !V.ContainsNaN() && FMath::Abs(V.X)<=Max && FMath::Abs(V.Y)<=Max && FMath::Abs(V.Z)<=Max; };
  if(!Bounded(Row.Location,1.e8) || !Bounded(Row.Scale,1.e4) || Row.Rotation.ContainsNaN() || FMath::Abs(Row.Rotation.Pitch)>360000 || FMath::Abs(Row.Rotation.Yaw)>360000 || FMath::Abs(Row.Rotation.Roll)>360000) throw std::runtime_error("Pose transforms must be finite and bounded");
  const FTransform Transform(Row.Rotation,Row.Location,Row.Scale); if(!Prepared.ReferencePose[Index].Equals(Transform,0.f)) { Prepared.ReferencePose[Index]=Transform; ++ChangedBones; }
 }
 const bool LinkChanged=R.bClearSourceMesh && !Prepared.SourceReferenceMesh.IsNull(); if(R.bClearSourceMesh) Prepared.SourceReferenceMesh.Reset(); const bool Changed=ChangedBones>0 || LinkChanged; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Edit Stored Retarget Pose"))); Skeleton->Modify(); Skeleton->AnimRetargetSources.FindChecked(Name)=MoveTemp(Prepared); Skeleton->CallbackRetargetSourceChanged(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Stored pose edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("pose_name"),Name.ToString()); J->WriteValue(TEXT("changed_bone_count"),ChangedBones); J->WriteValue(TEXT("reset_reference_pose"),R.bResetReferencePose); J->WriteValue(TEXT("source_link_would_clear"),LinkChanged); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Stored local reference transforms only; retained source mesh refresh may overwrite manual edits. No animation rebake or retarget quality evaluation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::EditCurveMetadata(const FSkeletonCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.Name.IsEmpty() || R.Name.Len()>128 || R.LinkedBones.Num()>64 || R.MaxLOD<0 || R.MaxLOD>255) throw std::runtime_error("Curve metadata edit requires stopped PIE, confirmed /Game Skeleton, bounded name/bones and MaxLOD [0,255]");
 if(R.Operation!=TEXT("create") && R.Operation!=TEXT("update")) throw std::runtime_error("Metadata operation requires create or update");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton"); const FName Name(*R.Name); const auto* Existing=static_cast<const USkeleton*>(Skeleton)->GetCurveMetaData(Name);
 if(Name.IsNone() || (R.Operation==TEXT("create") && (Existing || Skeleton->GetNumCurveMetaData()>=1024)) || (R.Operation==TEXT("update") && !Existing)) throw std::runtime_error("Create requires unused name/<1024 metadata; update requires existing name");
 TArray<FBoneReference> Links; TSet<FName> Seen; for(const auto& Bone:R.LinkedBones) { if(Bone.IsEmpty() || Bone.Len()>128) throw std::runtime_error("Linked bone name exceeds bounds"); const FName Key(*Bone); if(Seen.Contains(Key) || Skeleton->GetReferenceSkeleton().FindBoneIndex(Key)==INDEX_NONE) throw std::runtime_error("Linked bones must be unique existing Skeleton bones"); Seen.Add(Key); Links.Add(FBoneReference(Key)); }
 bool Changed=!Existing || Existing->Type.bMaterial!=R.bMaterial || Existing->Type.bMorphtarget!=R.bMorphTarget || Existing->MaxLOD!=R.MaxLOD || Existing->LinkedBones.Num()!=Links.Num(); if(Existing && !Changed) for(int32 Index=0;Index<Links.Num();++Index) if(Links[Index].BoneName!=Existing->LinkedBones[Index].BoneName) { Changed=true; break; }
 bool Saved=false; if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Skeleton Curve Metadata"))); Skeleton->Modify(); if(!Existing) Skeleton->AddCurveMetaData(Name,false); auto* Metadata=Cast<UAnimCurveMetaData>(Skeleton->GetAssetUserDataOfClass(UAnimCurveMetaData::StaticClass())); if(!Metadata) throw std::runtime_error("Native curve metadata storage unavailable"); Metadata->SetFlags(RF_Transactional); Metadata->Modify(); Metadata->SetCurveMetaDataMaterial(Name,R.bMaterial); Metadata->SetCurveMetaDataMorphTarget(Name,R.bMorphTarget); Metadata->SetCurveMetaDataBoneLinks(Name,Links,uint8(R.MaxLOD),Skeleton); Metadata->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Curve metadata edited but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("name"),Name.ToString()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Skeleton curve metadata only; no animation curve keys, material parameters or morph geometry are created.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString SkeletonUtils::CurveMetadataLifecycle(const FSkeletonCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || R.AssetPath.Len()>1024 || !R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(R.AssetPath) || R.Name.IsEmpty() || R.Name.Len()>128 || R.NewName.Len()>128) throw std::runtime_error("Metadata lifecycle requires stopped PIE, confirmed /Game Skeleton and bounded names");
 if(R.Operation!=TEXT("rename") && R.Operation!=TEXT("remove")) throw std::runtime_error("Metadata lifecycle operation requires rename or remove");
 if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(R.AssetPath)).IsValid()) throw std::runtime_error("Skeleton must exist in registry");
 auto* Skeleton=LoadObject<USkeleton>(nullptr,*R.AssetPath); if(!IsValid(Skeleton) || Skeleton->HasAnyFlags(RF_Transient)) throw std::runtime_error("Asset must be persistent Skeleton");
 const FName Name(*R.Name),Destination(*R.NewName); const auto* ReadOnly=static_cast<const USkeleton*>(Skeleton);
 if(Name.IsNone() || !ReadOnly->GetCurveMetaData(Name)) throw std::runtime_error("Metadata source must exist");
 if(R.Operation==TEXT("rename") && (R.NewName.IsEmpty() || Destination.IsNone() || (Destination!=Name && ReadOnly->GetCurveMetaData(Destination)))) throw std::runtime_error("Rename destination must be unused non-None name");
 const bool Changed=R.Operation==TEXT("remove") || Destination!=Name; bool Saved=false;
 if(!R.bDryRun && Changed) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Curve Metadata Lifecycle"))); Skeleton->Modify(); auto* Metadata=Cast<UAnimCurveMetaData>(Skeleton->GetAssetUserDataOfClass(UAnimCurveMetaData::StaticClass())); if(!Metadata) throw std::runtime_error("Native curve metadata storage unavailable"); Metadata->SetFlags(RF_Transactional); Metadata->Modify(); const bool Okay=R.Operation==TEXT("rename") ? Metadata->RenameCurveMetaData(Name,Destination) : Metadata->RemoveCurveMetaData(Name); if(!Okay) { Transaction.Cancel(); throw std::runtime_error("Native metadata lifecycle operation failed"); } Metadata->PostEditChange(); Skeleton->PostEditChange(); Skeleton->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Skeleton,false); if(!Saved) throw std::runtime_error("Metadata changed but Skeleton save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Skeleton->GetPathName()); J->WriteValue(TEXT("name"),Name.ToString()); J->WriteValue(TEXT("new_name"),Destination.ToString()); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Skeleton metadata only; existing animation curve names/keys and Blueprint/material/morph references are not migrated or removed. Native metadata may be recreated by later curve collection.")); J->WriteObjectEnd(); J->Close(); return Result;
}
