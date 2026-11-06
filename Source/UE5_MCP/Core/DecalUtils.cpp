#include "DecalUtils.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/DecalActor.h"
#include "Materials/Material.h"
#include "UE5_MCP/API/DTO/DecalReq.h"
#include "Components/DecalComponent.h"
#include "Materials/MaterialInterface.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "GameFramework/Actor.h"
#include "LevelUtils.h"
#include "ScopedTransaction.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectIterator.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace {
UWorld* DecalWorld() {
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("Stopped editor world required");
 auto* W=GEditor->GetEditorWorldContext().World();
 if(!IsValid(W) || W->WorldType!=EWorldType::Editor) throw std::runtime_error("Current editor world required");
 return W;
}
UDecalComponent* ResolveDecal(const FDecalReq& R) {
 auto* W=DecalWorld();
 if(R.ActorPath.IsEmpty() || R.ActorPath.Len()>2048 || R.ComponentPath.IsEmpty() || R.ComponentPath.Len()>2048) throw std::runtime_error("Bounded actor/component paths required");
 auto* C=FindObject<UDecalComponent>(nullptr,*R.ComponentPath);
 if(!IsValid(C) || C->IsTemplate() || C->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || C->GetPathName()!=R.ComponentPath || C->GetWorld()!=W || !IsValid(C->GetOwner()) || C->GetOwner()->IsTemplate() || C->GetOwner()->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || C->GetOwner()->GetPathName()!=R.ActorPath) throw std::runtime_error("Loaded persistent current-world decal identity required");
 return C;
}
const TArray<FString>& SettingNames() {
 static const TArray<FString> Names={TEXT("SortOrder"),TEXT("FadeScreenSize"),TEXT("FadeStartDelay"),TEXT("FadeDuration"),TEXT("FadeInStartDelay"),TEXT("FadeInDuration"),TEXT("bDestroyOwnerAfterFade")}; return Names;
}
double ReadSetting(const UDecalComponent* C,const FString& Name) {
 auto* P=FindFProperty<FProperty>(C->GetClass(),FName(*Name));
 if(auto* I=CastField<FIntProperty>(P)) return double(I->GetPropertyValue_InContainer(C));
 if(auto* F=CastField<FFloatProperty>(P)) return double(F->GetPropertyValue_InContainer(C));
 if(auto* B=CastField<FBoolProperty>(P)) return double(B->GetPropertyValue_InContainer(C));
 throw std::runtime_error("Native decal setting unavailable");
}
}
FString DecalUtils::InspectPage(const FDecalReq& R) {
 auto* W=DecalWorld();
 if(R.Start<0 || R.Count<1 || R.Count>128 || R.ActorPath.Len()>2048 || R.MaterialPath.Len()>2048) throw std::runtime_error("Offset/page1..128/optional bounded owner path required");
 TArray<UDecalComponent*> Entries;
 for(TObjectIterator<UDecalComponent> It;It;++It) {
  auto* C=*It; auto* A=C->GetOwner();
  if(!IsValid(C) || C->IsTemplate() || C->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || C->GetWorld()!=W || !IsValid(A) || A->IsTemplate() || A->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || (!R.ActorPath.IsEmpty() && A->GetPathName()!=R.ActorPath)) continue;
  if(R.bFilterMaterial && (C->GetDecalMaterial()?C->GetDecalMaterial()->GetPathName():FString())!=R.MaterialPath) continue;
  Entries.Add(C);
 }
 Entries.Sort([](const UDecalComponent& A,const UDecalComponent& B) { return A.GetPathName()<B.GetPathName(); });
 const int32 Start=FMath::Min(R.Start,Entries.Num()),End=Start+FMath::Min(R.Count,Entries.Num()-Start);
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
 J->WriteValue(TEXT("filter_material"),R.bFilterMaterial); J->WriteValue(TEXT("material_filter_path"),R.MaterialPath); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("component_count"),Entries.Num()); J->WriteValue(TEXT("next_start"),End); J->WriteValue(TEXT("has_more"),End<Entries.Num()); J->WriteArrayStart(TEXT("decals"));
 for(int32 I=Start;I<End;++I) {
  const auto* C=Entries[I]; const auto* A=C->GetOwner(); J->WriteObjectStart();
  J->WriteValue(TEXT("index"),I); J->WriteValue(TEXT("actor_path"),A->GetPathName()); J->WriteValue(TEXT("actor_guid"),A->GetActorGuid().ToString()); J->WriteValue(TEXT("label"),A->GetActorLabel()); J->WriteValue(TEXT("component_path"),C->GetPathName()); J->WriteValue(TEXT("class_path"),C->GetClass()->GetPathName()); J->WriteValue(TEXT("level_path"),GetPathNameSafe(A->GetLevel())); J->WriteValue(TEXT("mobility"),int32(C->Mobility.GetValue())); J->WriteValue(TEXT("direct_child_count"),C->GetAttachChildren().Num()); J->WriteValue(TEXT("registered"),C->IsRegistered()); J->WriteValue(TEXT("visible"),C->GetVisibleFlag()); J->WriteValue(TEXT("material_path"),C->GetDecalMaterial()?C->GetDecalMaterial()->GetPathName():FString()); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty());
  auto Number=[&](const TCHAR* Name,double Value) { if(FMath::IsFinite(Value)) J->WriteValue(Name,Value); else J->WriteNull(Name); };
  J->WriteObjectStart(TEXT("settings")); for(const auto& Name:SettingNames()) Number(*Name,ReadSetting(C,Name)); J->WriteObjectEnd();
  auto Vector=[&](const TCHAR* Name,const FVector& V) { J->WriteArrayStart(Name); for(double N:{V.X,V.Y,V.Z}) { if(FMath::IsFinite(N)) J->WriteValue(N); else J->WriteNull(); } J->WriteArrayEnd(); };
  Vector(TEXT("local_decal_size"),C->DecalSize); Vector(TEXT("world_location"),C->GetComponentLocation()); Vector(TEXT("component_scale"),C->GetComponentScale()); J->WriteValue(TEXT("attachment_parent_path"),GetPathNameSafe(C->GetAttachParent())); J->WriteArrayStart(TEXT("world_rotation_quaternion")); const auto Q=C->GetComponentQuat(); for(double N:{Q.X,Q.Y,Q.Z,Q.W}) { if(FMath::IsFinite(N)) J->WriteValue(N); else J->WriteNull(); } J->WriteArrayEnd(); J->WriteArrayStart(TEXT("linear_color")); for(float N:{C->DecalColor.R,C->DecalColor.G,C->DecalColor.B,C->DecalColor.A}) { if(FMath::IsFinite(N)) J->WriteValue(double(N)); else J->WriteNull(); } J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Loaded persistent current-world native decal component pages1..128/path sorted/optional owner. Authored material/size/color/render-fade settings, GUID/label/dirty; size excludes component scale. No material loading/domain or receiver/renderer eligibility/output evaluation, timer execution/capture/build/render synchronization/load/save/mutation. Global scan/sort unbounded; scene changes shift offsets. Compilation/native decal behavior unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}
FString DecalUtils::SetSetting(const FDecalReq& R) {
 auto* C=ResolveDecal(R); auto* A=C->GetOwner(); auto* W=C->GetWorld(); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A) || !FMath::IsFinite(R.Value) || !FMath::IsFinite(R.ExpectedValue) || !SettingNames().Contains(R.FieldName)) throw std::runtime_error("Confirmed editable decal/GUID/label/supported finite setting required");
 const bool Order=R.FieldName==TEXT("SortOrder"),Destroy=R.FieldName==TEXT("bDestroyOwnerAfterFade");
 if((Order && (R.Value<MIN_int32 || R.Value>MAX_int32 || R.Value!=FMath::FloorToDouble(R.Value))) || (Destroy && R.Value!=0 && R.Value!=1) || (!Order && !Destroy && (R.Value<0 || R.Value>(R.FieldName==TEXT("FadeScreenSize")?1.:100000.)))) throw std::runtime_error("Sort int32, destroy flag0..1, screen size0..1 or fade time0..100000 seconds required");
 auto* P=FindFProperty<FProperty>(C->GetClass(),FName(*R.FieldName)); auto* F=CastField<FFloatProperty>(P); auto* I=CastField<FIntProperty>(P); auto* B=CastField<FBoolProperty>(P);
 if(!P || (Order?!I:(Destroy?!B:!F)) || !C->CanEditChange(P)) throw std::runtime_error("Native editable typed decal property required");
 const double Before=ReadSetting(C,R.FieldName),Requested=(Order || Destroy)?R.Value:double(float(R.Value)); if(Before!=R.ExpectedValue) throw std::runtime_error("Exact decal current setting stale guard failed");
 TArray<double> Snapshot; for(const auto& Name:SettingNames()) Snapshot.Add(ReadSetting(C,Name)); const FVector Size=C->DecalSize; const FLinearColor Color=C->DecalColor; const auto* Material=C->GetDecalMaterial();
 auto Context=[&](bool Edited) { if(!IsValid(C) || !IsValid(A) || C->GetOwner()!=A || C->GetWorld()!=W || A->GetActorGuid()!=Guid || C->DecalSize!=Size || C->DecalColor!=Color || C->GetDecalMaterial()!=Material) return false; for(int32 K=0;K<SettingNames().Num();++K) if(ReadSetting(C,SettingNames()[K])!=((Edited && SettingNames()[K]==R.FieldName)?Requested:Snapshot[K])) return false; return true; };
 const bool Changed=Before!=Requested;
 if(Changed && !R.bDryRun) {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Decal Setting"))); A->Modify(); C->SetFlags(RF_Transactional); C->Modify(); C->PreEditChange(P); if(!Context(false)) throw std::runtime_error("Pre-edit changed decal context");
  if(Order) C->SetSortOrder(int32(Requested)); else if(R.FieldName==TEXT("FadeScreenSize")) C->SetFadeScreenSize(float(Requested)); else if(Destroy) B->SetPropertyValue_InContainer(C,Requested!=0); else F->SetPropertyValue_InContainer(C,float(Requested));
  FPropertyChangedEvent Event(P,EPropertyChangeType::ValueSet); C->PostEditChangeProperty(Event); if(!Context(true)) throw std::runtime_error("Native decal setting readback failed; inspect partial state"); C->MarkPackageDirty();
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("field_name"),R.FieldName); J->WriteValue(TEXT("previous_value"),Before); J->WriteValue(TEXT("requested_native_value"),Requested); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Native decal render/fade authored setting with exact actor/GUID/label/current value, full supported sibling/size/color/material pre-post readback, transaction/property events/dirty/no-op/dry-run. Sort/screen size use native setters; fade/destroy-after-fade values authored directly, does not invoke SetFadeIn/Out or schedule timers/start simulation. Destroy-after-fade can delete owning actor during later game/simulation fade, including actor with other components; no current deletion. Renderer/material/receiver eligibility/output unverified; no render evaluation/build/render synchronization/load/save, compilation/callback/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::SetMaterial(const FDecalReq& R) {
 auto* C=ResolveDecal(R); auto* A=C->GetOwner(); auto* W=C->GetWorld(); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A) || R.MaterialPath.Len()>2048 || R.ExpectedMaterialPath.Len()>2048) throw std::runtime_error("Confirmed editable decal/GUID/label/bounded material paths required");
 auto* Before=C->GetDecalMaterial(); const FString BeforePath=Before?Before->GetPathName():FString(); if(BeforePath!=R.ExpectedMaterialPath) throw std::runtime_error("Exact current decal material stale guard failed");
 UMaterialInterface* Requested=nullptr;
 if(!R.MaterialPath.IsEmpty()) {
  Requested=FindObject<UMaterialInterface>(nullptr,*R.MaterialPath);
  if(!IsValid(Requested) || Requested->IsTemplate() || Requested->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || Requested->GetOutermost()==GetTransientPackage() || Requested->GetPathName()!=R.MaterialPath) throw std::runtime_error("Loaded persistent material interface or empty clear required");
  const auto* Base=Requested->GetMaterial(); if(!IsValid(Base) || Base->MaterialDomain!=MD_DeferredDecal) throw std::runtime_error("Native DeferredDecal material domain required");
 }
 auto* P=FindFProperty<FObjectProperty>(C->GetClass(),TEXT("DecalMaterial")); if(!P || !C->CanEditChange(P) || (Requested && !Requested->IsA(P->PropertyClass)) || (!Requested && P->HasAnyPropertyFlags(CPF_NoClear))) throw std::runtime_error("Native editable compatible decal material reference required");
 TArray<double> Settings; for(const auto& Name:SettingNames()) Settings.Add(ReadSetting(C,Name)); const FVector Size=C->DecalSize; const FLinearColor Color=C->DecalColor; const FTransform Transform=C->GetComponentTransform(); const bool Visible=C->GetVisibleFlag(); const auto Mobility=C->Mobility;
 auto Context=[&]() { if(!IsValid(C) || !IsValid(A) || C->GetOwner()!=A || C->GetWorld()!=W || A->GetActorGuid()!=Guid || C->DecalSize!=Size || C->DecalColor!=Color || !C->GetComponentTransform().Equals(Transform,1.e-6) || C->GetVisibleFlag()!=Visible || C->Mobility!=Mobility) return false; for(int32 I=0;I<SettingNames().Num();++I) if(ReadSetting(C,SettingNames()[I])!=Settings[I]) return false; return true; };
 const bool Changed=Before!=Requested;
 if(Changed && !R.bDryRun) {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Decal Material"))); A->Modify(); C->SetFlags(RF_Transactional); C->Modify(); C->PreEditChange(P); if(!Context() || C->GetDecalMaterial()!=Before) throw std::runtime_error("Pre-edit changed decal material context");
  C->SetDecalMaterial(Requested); FPropertyChangedEvent Event(P,EPropertyChangeType::ValueSet); C->PostEditChangeProperty(Event); if(!Context() || C->GetDecalMaterial()!=Requested) throw std::runtime_error("Decal material readback failed; inspect partial state"); C->MarkPackageDirty();
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("previous_material_path"),BeforePath); J->WriteValue(TEXT("requested_material_path"),R.MaterialPath); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Loaded persistent DeferredDecal-domain material interface assignment or empty clear, exact actor/GUID/label/current reference guard. Native SetDecalMaterial/PrecachePSOs/render-state dirty/property notifications/transaction/full render-fade/size/color/transform/visibility/mobility preservation/readback/no-op/dry-run. Material asset not edited, domain alone not shader/receiver/platform/output readiness proof. Native PSO/custom material getter/callback work unbounded. No dynamic material creation/explicit asset load/render evaluation/build/render synchronization/save; compilation/callback/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::SetAppearance(const FDecalReq& R) {
 auto* C=ResolveDecal(R); auto* A=C->GetOwner(); auto* W=C->GetWorld(); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A)) throw std::runtime_error("Confirmed editable decal/GUID/label required");
 const bool SizeEdit=R.FieldName==TEXT("DecalSize"); if(!SizeEdit && R.FieldName!=TEXT("DecalColor")) throw std::runtime_error("DecalSize or DecalColor required");
 const FVector OldSize=C->DecalSize; const FLinearColor OldColor=C->DecalColor; FVector Size=OldSize; FLinearColor Color=OldColor;
 if(SizeEdit) {
  if(!FMath::IsFinite(R.Size.X) || !FMath::IsFinite(R.Size.Y) || !FMath::IsFinite(R.Size.Z) || R.Size.GetMin()<0.001 || R.Size.GetMax()>1.e6 || R.ExpectedSize!=OldSize) throw std::runtime_error("Exact current size and requested native local XYZ0.001..1e6 required"); Size=R.Size;
 } else {
  const TArray<double> Before={double(OldColor.R),double(OldColor.G),double(OldColor.B),double(OldColor.A)};
  if(R.ExpectedColor!=Before || R.Color.Num()!=4) throw std::runtime_error("Full exact inspected/requested linear RGBA required");
  for(double V:R.Color) if(!FMath::IsFinite(V) || V<0 || V>1000) throw std::runtime_error("Linear RGBA channels0..1000 required");
  Color=FLinearColor(float(R.Color[0]),float(R.Color[1]),float(R.Color[2]),float(R.Color[3]));
 }
 auto* P=FindFProperty<FStructProperty>(C->GetClass(),FName(*R.FieldName)); if(!P || P->Struct!=(SizeEdit?TBaseStructure<FVector>::Get():TBaseStructure<FLinearColor>::Get()) || !C->CanEditChange(P)) throw std::runtime_error("Native editable decal size/color struct required");
 TArray<double> Settings; for(const auto& Name:SettingNames()) Settings.Add(ReadSetting(C,Name)); const auto* Material=C->GetDecalMaterial(); const FTransform Transform=C->GetComponentTransform(); const auto Mobility=C->Mobility; const bool Visible=C->GetVisibleFlag();
 auto Context=[&](bool Edited) { if(!IsValid(C) || !IsValid(A) || C->GetOwner()!=A || C->GetWorld()!=W || A->GetActorGuid()!=Guid || C->GetDecalMaterial()!=Material || C->DecalSize!=(Edited?Size:OldSize) || C->DecalColor!=(Edited?Color:OldColor) || !C->GetComponentTransform().Equals(Transform,1.e-6) || C->Mobility!=Mobility || C->GetVisibleFlag()!=Visible) return false; for(int32 I=0;I<SettingNames().Num();++I) if(ReadSetting(C,SettingNames()[I])!=Settings[I]) return false; return true; };
 const bool Changed=Size!=OldSize || Color!=OldColor;
 if(Changed && !R.bDryRun) {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Decal Appearance"))); A->Modify(); C->SetFlags(RF_Transactional); C->Modify(); C->PreEditChange(P); if(!Context(false)) throw std::runtime_error("Pre-edit changed decal appearance context");
  if(SizeEdit) C->DecalSize=Size; else C->SetDecalColor(Color);
  FPropertyChangedEvent Event(P,EPropertyChangeType::ValueSet); C->PostEditChangeProperty(Event); if(!Context(true)) throw std::runtime_error("Native decal appearance readback failed; inspect partial state"); C->MarkRenderStateDirty(); C->MarkPackageDirty();
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("field_name"),R.FieldName); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty()); J->WriteArrayStart(TEXT("requested_local_size")); for(double V:{Size.X,Size.Y,Size.Z}) { if(FMath::IsFinite(V)) J->WriteValue(V); else J->WriteNull(); } J->WriteArrayEnd(); J->WriteArrayStart(TEXT("requested_linear_rgba")); for(float V:{Color.R,Color.G,Color.B,Color.A}) { if(FMath::IsFinite(V)) J->WriteValue(double(V)); else J->WriteNull(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native decal local size XYZ0.001..1e6 or linear RGBA0..1000 authoring with full exact previous value/actor/GUID/label guards. Size excludes component scale; no light/sRGB color conversion. Color is consumed by material Decal Color node, shader/receiver/project/platform gates visual effect. Native color setter/size property edit/transaction/events/render-state dirty/full material/render-fade/transform/mobility/visibility and sibling appearance readback/dirty/no-op/dry-run. No timers/actor resizing/transforms/material asset edits/render evaluation/build/render synchronization/load/save; compilation/callback/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::SetPlacement(const FDecalReq& R) {
 auto* C=ResolveDecal(R); auto* A=C->GetOwner(); auto* W=C->GetWorld(); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A)) throw std::runtime_error("Confirmed editable decal/GUID/label required");
 const bool TransformEdit=R.FieldName==TEXT("Transform"); if(!TransformEdit && R.FieldName!=TEXT("Visible")) throw std::runtime_error("Transform or Visible placement field required");
 const FTransform Before=C->GetComponentTransform(); const bool Visible=C->GetVisibleFlag(); const auto* Parent=C->GetAttachParent();
 if(TransformEdit) {
  const FVector P=R.Transform.GetLocation(),S=R.Transform.GetScale3D(); const FQuat Q=R.Transform.GetRotation();
  if(Parent || !Before.Equals(R.ExpectedTransform,1.e-6) || R.Transform.ContainsNaN() || !Q.IsNormalized() || !FMath::IsFinite(P.X) || !FMath::IsFinite(P.Y) || !FMath::IsFinite(P.Z) || P.GetAbsMax()>1.e9 || !FMath::IsFinite(S.X) || !FMath::IsFinite(S.Y) || !FMath::IsFinite(S.Z) || S.GetAbsMax()>1000 || FMath::Abs(S.X)<0.001 || FMath::Abs(S.Y)<0.001 || FMath::Abs(S.Z)<0.001) throw std::runtime_error("Unattached decal/full current transform/normalized rotation/location+/-1e9/nonzero scale abs0.001..1000 required");
 } else if(Visible!=R.bExpectedVisible) throw std::runtime_error("Exact current decal visibility stale guard failed");
 TArray<double> Settings; for(const auto& Name:SettingNames()) Settings.Add(ReadSetting(C,Name)); const FVector Size=C->DecalSize; const FLinearColor Color=C->DecalColor; const auto* Material=C->GetDecalMaterial(); const auto Mobility=C->Mobility;
 auto Context=[&](bool Edited) { if(!IsValid(C) || !IsValid(A) || C->GetOwner()!=A || C->GetWorld()!=W || A->GetActorGuid()!=Guid || C->GetAttachParent()!=Parent || C->Mobility!=Mobility || C->DecalSize!=Size || C->DecalColor!=Color || C->GetDecalMaterial()!=Material || C->GetVisibleFlag()!=((Edited && !TransformEdit)?R.bVisible:Visible) || !C->GetComponentTransform().Equals((Edited && TransformEdit)?R.Transform:Before,1.e-6)) return false; for(int32 I=0;I<SettingNames().Num();++I) if(ReadSetting(C,SettingNames()[I])!=Settings[I]) return false; return true; };
 const bool Changed=TransformEdit?!Before.Equals(R.Transform,1.e-6):Visible!=R.bVisible;
 if(Changed && !R.bDryRun) {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Decal Placement"))); A->Modify(); C->SetFlags(RF_Transactional); C->Modify(); if(!Context(false)) throw std::runtime_error("Decal placement changed before native setter");
  if(TransformEdit) C->SetWorldTransform(R.Transform,false,nullptr,ETeleportType::TeleportPhysics); else C->SetVisibility(R.bVisible,false);
  if(!Context(true)) throw std::runtime_error("Native decal placement readback failed; inspect partial state"); C->MarkPackageDirty();
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("field_name"),R.FieldName); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Native decal component visibility or unattached world transform, exact actor/GUID/label/current flag/full transform guard. Transaction/native setters/full render-fade/size/color/material/mobility/attachment and sibling placement readback/dirty/no-op/dry-run. Transform uses no-sweep teleport, native children follow and owner moves if component is root; local DecalSize retained. Visibility does not propagate to children or edit actor hidden flags. Negative nonzero scales allowed, projection/output/receivers not proven. No actor PostEditMove/construction-script invocation/timer scheduling/render evaluation/build/render synchronization/load/save; compilation/native movement/callback/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::Create(const FDecalReq& R) {
 auto* W=DecalWorld();
 if(!GEditor->Trans || !R.bConfirm || W->GetWorldPartition() || !IsValid(W->PersistentLevel) || W->GetPathName()!=R.WorldPath || FLevelUtils::IsLevelLocked(W->PersistentLevel)) throw std::runtime_error("Confirmed exact ordinary unlocked persistent editor world required");
 if(R.Name.IsEmpty() || R.Name.Len()>128 || FName(*R.Name).IsNone() || !FMath::IsFinite(R.Location.X) || !FMath::IsFinite(R.Location.Y) || !FMath::IsFinite(R.Location.Z) || R.Location.GetAbsMax()>1.e9) throw std::runtime_error("Bounded unique actor name/finite location+/-1e9 required");
 for(TCHAR Ch:R.Name) if(!FChar::IsAlnum(Ch) && Ch!=TEXT('_')) throw std::runtime_error("Actor name requires letters/digits/underscore");
 if(FindObject<UObject>(W->PersistentLevel,*R.Name)) throw std::runtime_error("Actor name already exists");
 ADecalActor* A=nullptr; UDecalComponent* C=nullptr;
 if(!R.bDryRun) {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Create Decal Actor"))); W->PersistentLevel->Modify(); FActorSpawnParameters Params; Params.Name=FName(*R.Name); Params.OverrideLevel=W->PersistentLevel; Params.ObjectFlags=RF_Transactional;
  A=W->SpawnActor<ADecalActor>(ADecalActor::StaticClass(),R.Location,FRotator::ZeroRotator,Params);
  if(!IsValid(A)) throw std::runtime_error("Native decal spawn failed; inspect partial state"); C=A->GetDecal();
  if(!IsValid(C) || !C->IsRegistered() || A->GetWorld()!=W || A->GetLevel()!=W->PersistentLevel || A->GetClass()!=ADecalActor::StaticClass() || A->GetRootComponent()!=C || C->GetOwner()!=A || A->GetFName()!=FName(*R.Name)) throw std::runtime_error("Native decal registration/identity readback failed; inspect partial state");
  A->Modify(); C->SetFlags(RF_Transactional); C->Modify(); A->MarkPackageDirty();
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),R.WorldPath); J->WriteValue(TEXT("name"),R.Name); J->WriteValue(TEXT("actor_path"),A?A->GetPathName():FString()); J->WriteValue(TEXT("component_path"),C?C->GetPathName():FString()); J->WriteValue(TEXT("actor_guid"),A?A->GetActorGuid().ToString():FString()); J->WriteValue(TEXT("label"),A?A->GetActorLabel():FString()); J->WriteValue(TEXT("material_path"),C && C->GetDecalMaterial()?C->GetDecalMaterial()->GetPathName():FString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),A && A->GetPackage()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Native exact ADecalActor/default root UDecalComponent spawn in confirmed exact ordinary unlocked persistent map, unique name/location+/-1e9, zero actor rotation/unit scale/native render-fade/material/size defaults. Native constructor/editor resources/registration/PSO work may run, no material autoassignment/readiness guarantee or image proof. Level/actor/component transaction/readback/dirty/dry-run; no actor selection/explicit material loading/timers/render evaluation/build/render synchronization/save. Compilation/default orientation/resource lifecycle/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}
FString DecalUtils::Delete(const FDecalReq& R) {
 auto* C=ResolveDecal(R); auto* W=C->GetWorld(); auto* A=Cast<ADecalActor>(C->GetOwner()); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || W->GetWorldPartition() || W->GetPathName()!=R.WorldPath || !IsValid(A) || A->GetClass()!=ADecalActor::StaticClass() || A->GetLevel()!=W->PersistentLevel || A->GetDecal()!=C || A->GetRootComponent()!=C || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A)) throw std::runtime_error("Confirmed exact ordinary native persistent decal actor/component/GUID/label required");
 const FString Material=C->GetDecalMaterial()?C->GetDecalMaterial()->GetPathName():FString(); if(Material!=R.ExpectedMaterialPath) throw std::runtime_error("Exact material reference deletion guard failed");
 TArray<AActor*> Attached; A->GetAttachedActors(Attached); if(!Attached.IsEmpty() || A->GetAttachParentActor()) throw std::runtime_error("Detach decal and all attached actors before deletion");
 TInlineComponentArray<UActorComponent*> Components(A); for(const auto* Component:Components) if(IsValid(Component) && Component->CreationMethod!=EComponentCreationMethod::Native) throw std::runtime_error("Remove extra nonnative actor components before native decal deletion");
 if(!R.bDryRun) {
  FScopedTransaction Transaction(FText::FromString(TEXT("MCP Delete Decal Actor"))); W->PersistentLevel->Modify(); A->Modify(); for(auto* Component:Components) if(IsValid(Component)) Component->Modify();
  if(!W->EditorDestroyActor(A,true)) throw std::runtime_error("Native decal destruction failed; inspect partial state");
  if(IsValid(A) && !A->IsActorBeingDestroyed()) throw std::runtime_error("Native decal actor still live after destruction; inspect partial state"); W->PersistentLevel->MarkPackageDirty();
 }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),R.ActorPath); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("actor_guid"),R.ActorGuid); J->WriteValue(TEXT("previous_material_path"),Material); J->WriteValue(TEXT("component_count"),Components.Num()); J->WriteValue(TEXT("deleted"),!R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),W->PersistentLevel->GetPackage()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Confirmed exact native ADecalActor/default root deletion in exact ordinary persistent map, GUID/label/material guards, no attached parent/children or nonnative components. Level/actor/all owned components transaction/native EditorDestroyActor/readback/dirty/dry-run. Native editor visualization components removed with actor, material asset retained; external references not fully discovered/repaired. Render resources/selection/reference callbacks may change; no render evaluation/build/render synchronization/save, compilation/lifecycle/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::InspectReceivers(const FDecalReq& R) {
 auto* W=DecalWorld(); if(R.Start<0 || R.Count<1 || R.Count>128 || R.ActorPath.Len()>2048 || R.ComponentPath.Len()>2048) throw std::runtime_error("Offset/page1..128/optional bounded owner-component filters required");
 TArray<UPrimitiveComponent*> Entries;
 for(TObjectIterator<UPrimitiveComponent> It;It;++It) {
  auto* C=*It; if(!IsValid(C) || C->IsTemplate() || C->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || C->GetWorld()!=W) continue; auto* A=C->GetOwner();
  if(!IsValid(A) || A->IsTemplate() || A->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || (!R.ActorPath.IsEmpty() && A->GetPathName()!=R.ActorPath) || (!R.ComponentPath.IsEmpty() && C->GetPathName()!=R.ComponentPath)) continue; Entries.Add(C);
 }
 Entries.Sort([](const UPrimitiveComponent& A,const UPrimitiveComponent& B) { return A.GetPathName()<B.GetPathName(); }); const int32 Start=FMath::Min(R.Start,Entries.Num()),End=Start+FMath::Min(R.Count,Entries.Num()-Start);
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("matched_count"),Entries.Num()); J->WriteValue(TEXT("next_start"),End); J->WriteValue(TEXT("has_more"),End<Entries.Num()); J->WriteArrayStart(TEXT("receivers"));
 for(int32 I=Start;I<End;++I) { const auto* C=Entries[I]; const auto* A=C->GetOwner(); J->WriteObjectStart(); J->WriteValue(TEXT("index"),I); J->WriteValue(TEXT("actor_path"),A->GetPathName()); J->WriteValue(TEXT("actor_guid"),A->GetActorGuid().ToString()); J->WriteValue(TEXT("label"),A->GetActorLabel()); J->WriteValue(TEXT("component_path"),C->GetPathName()); J->WriteValue(TEXT("class_path"),C->GetClass()->GetPathName()); J->WriteValue(TEXT("level_path"),GetPathNameSafe(A->GetLevel())); J->WriteValue(TEXT("receives_decals"),bool(C->bReceivesDecals)); J->WriteValue(TEXT("registered"),C->IsRegistered()); J->WriteValue(TEXT("visible"),C->GetVisibleFlag()); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty()); auto* P=FindFProperty<FBoolProperty>(C->GetClass(),TEXT("bReceivesDecals")); J->WriteValue(TEXT("native_can_edit"),P && C->CanEditChange(P)); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Loaded persistent current-world primitive component bReceivesDecals authoring inventory, not just mesh receivers. Path sorted/pages1..128/optional exact owner-component filters, no stable scene revision/global scan-sort unbounded. Flag not actual decal projection/material response/render-path support proof; does not inspect material assets or projected overlaps. No render evaluation/build/render synchronization/load/save/mutation; compilation/native receiver semantics unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}
FString DecalUtils::SetReceiver(const FDecalReq& R) {
 auto* W=DecalWorld(); if(R.ActorPath.IsEmpty() || R.ActorPath.Len()>2048 || R.ComponentPath.IsEmpty() || R.ComponentPath.Len()>2048) throw std::runtime_error("Bounded exact receiver owner/component paths required"); auto* C=FindObject<UPrimitiveComponent>(nullptr,*R.ComponentPath); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || !IsValid(C) || C->IsTemplate() || C->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || C->GetWorld()!=W || C->GetPathName()!=R.ComponentPath) throw std::runtime_error("Confirmed loaded persistent current-world primitive receiver required"); auto* A=C->GetOwner();
 if(!IsValid(A) || A->IsTemplate() || A->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || A->GetPathName()!=R.ActorPath || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A)) throw std::runtime_error("Exact editable receiver actor/GUID/label required");
 const bool Before=C->bReceivesDecals; if(Before!=R.bExpectedReceivesDecals) throw std::runtime_error("Exact current receiver flag stale guard failed"); auto* P=FindFProperty<FBoolProperty>(C->GetClass(),TEXT("bReceivesDecals")); if(!P || !C->CanEditChange(P)) throw std::runtime_error("Native editable receives-decals property required");
 const FTransform Transform=C->GetComponentTransform(); const bool Visible=C->GetVisibleFlag(),CastShadow=C->CastShadow; const auto Mobility=C->Mobility; const auto* Parent=C->GetAttachParent();
 auto Context=[&]() { return IsValid(C) && IsValid(A) && C->GetOwner()==A && C->GetWorld()==W && A->GetActorGuid()==Guid && C->GetVisibleFlag()==Visible && bool(C->CastShadow)==CastShadow && C->Mobility==Mobility && C->GetAttachParent()==Parent && C->GetComponentTransform().Equals(Transform,1.e-6); };
 const bool Changed=Before!=R.bReceivesDecals;
 if(Changed && !R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Decal Receiver"))); A->Modify(); C->SetFlags(RF_Transactional); C->Modify(); C->PreEditChange(P); if(!Context() || bool(C->bReceivesDecals)!=Before) throw std::runtime_error("Pre-edit changed decal receiver context"); C->SetReceivesDecals(R.bReceivesDecals); FPropertyChangedEvent Event(P,EPropertyChangeType::ValueSet); C->PostEditChangeProperty(Event); if(!Context() || bool(C->bReceivesDecals)!=R.bReceivesDecals) throw std::runtime_error("Native receiver readback failed; inspect partial state"); C->MarkPackageDirty(); }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("previous_receives_decals"),Before); J->WriteValue(TEXT("requested_receives_decals"),R.bReceivesDecals); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),C->GetPackage()->IsDirty()); J->WriteValue(TEXT("scope"),TEXT("Native primitive bReceivesDecals flag with exact actor/component/GUID/label/current flag guard. Native SetReceivesDecals/transaction/property notification/readback/dirty/no-op/dry-run; preserves transform/attachment/visibility/mobility/cast-shadow authoring. Does not edit projector/material assets or material decal response, receiver flag not rendering/overlap/material compatibility proof. Custom native callbacks/resource recreation may occur; no render evaluation/build/render synchronization/load/save, compilation/callback/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::SetMobility(const FDecalReq& R) {
 auto* C=ResolveDecal(R); auto* A=C->GetOwner(); auto* W=C->GetWorld(); FGuid Guid;
 if(!GEditor->Trans || !R.bConfirm || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || A->GetActorGuid()!=Guid || A->GetActorLabel()!=R.ExpectedLabel || !A->IsEditable() || FLevelUtils::IsLevelLocked(A) || !FMath::IsFinite(R.Value) || R.Value<0 || R.Value>2 || R.Value!=FMath::FloorToDouble(R.Value) || double(C->Mobility.GetValue())!=R.ExpectedValue || R.ExpectedChildCount!=C->GetAttachChildren().Num()) throw std::runtime_error("Confirmed editable decal/GUID/label/exact current mobility/direct child count and requested ordinal0..2 required");
 const auto Before=C->Mobility.GetValue(),Requested=EComponentMobility::Type(int32(R.Value)); auto* Parent=C->GetAttachParent(); if(Parent && int32(Parent->Mobility.GetValue())>int32(Requested)) throw std::runtime_error("Requested mobility incompatible with attached parent; change parent first"); auto* P=FindFProperty<FProperty>(C->GetClass(),TEXT("Mobility")); if(!P || !C->CanEditChange(P)) throw std::runtime_error("Native editable decal mobility required");
 TArray<USceneComponent*> Nodes; Nodes.Add(C); TSet<USceneComponent*> Seen; Seen.Add(C); TArray<int32> Mobilities; TArray<FString> Paths; TArray<USceneComponent*> Parents;
 for(int32 I=0;I<Nodes.Num();++I) { auto* N=Nodes[I]; auto* Owner=IsValid(N)?N->GetOwner():nullptr; if(Nodes.Num()>256 || !IsValid(N) || N->IsTemplate() || N->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || N->GetWorld()!=W || !IsValid(Owner) || !Owner->IsEditable() || FLevelUtils::IsLevelLocked(Owner)) throw std::runtime_error("At most256 loaded editable unlocked descendant components required"); Mobilities.Add(int32(N->Mobility.GetValue())); Paths.Add(N->GetPathName()); Parents.Add(N->GetAttachParent()); for(USceneComponent* Child:N->GetAttachChildren()) { if(!IsValid(Child) || Seen.Contains(Child)) throw std::runtime_error("Valid acyclic native attachment hierarchy required"); Seen.Add(Child); Nodes.Add(Child); } }
 const bool Guarded=R.bRequireHierarchySnapshot || !R.ExpectedHierarchyPaths.IsEmpty() || !R.ExpectedHierarchyParents.IsEmpty() || !R.ExpectedHierarchyMobilities.IsEmpty(); if(Guarded) { if(R.ExpectedHierarchyPaths.Num()!=Nodes.Num() || R.ExpectedHierarchyParents.Num()!=Nodes.Num() || R.ExpectedHierarchyMobilities.Num()!=Nodes.Num()) throw std::runtime_error("Full ordered mobility hierarchy path/parent/mobility snapshot required"); for(int32 I=0;I<Nodes.Num();++I) if(R.ExpectedHierarchyPaths[I]!=Paths[I] || R.ExpectedHierarchyParents[I]!=GetPathNameSafe(Parents[I]) || R.ExpectedHierarchyMobilities[I]!=Mobilities[I]) throw std::runtime_error("Full ordered mobility hierarchy snapshot stale guard failed"); }
 const FTransform Transform=C->GetComponentTransform(); const FVector Size=C->DecalSize; const FLinearColor Color=C->DecalColor; const auto* Material=C->GetDecalMaterial(); const bool Visible=C->GetVisibleFlag(); TArray<double> Settings; for(const auto& Name:SettingNames()) Settings.Add(ReadSetting(C,Name));
 const bool Changed=Before!=Requested;
 auto Context=[&](bool Edited) { if(!IsValid(C) || !IsValid(A) || C->GetOwner()!=A || A->GetActorGuid()!=Guid || C->GetWorld()!=W || C->GetAttachChildren().Num()!=R.ExpectedChildCount || C->DecalSize!=Size || C->DecalColor!=Color || C->GetDecalMaterial()!=Material || C->GetVisibleFlag()!=Visible || !C->GetComponentTransform().Equals(Transform,1.e-6)) return false; for(int32 I=0;I<Nodes.Num();++I) { auto* N=Nodes[I]; const int32 Expected=Edited && (Changed && (I==0 || Requested==EComponentMobility::Movable))?int32(Requested):Mobilities[I]; if(!IsValid(N) || N->GetWorld()!=W || N->GetPathName()!=Paths[I] || N->GetAttachParent()!=Parents[I] || int32(N->Mobility.GetValue())!=Expected) return false; } for(int32 I=0;I<SettingNames().Num();++I) if(ReadSetting(C,SettingNames()[I])!=Settings[I]) return false; return true; };
 if(Changed && !R.bDryRun) { FScopedTransaction Transaction(FText::FromString(TEXT("MCP Set Decal Mobility"))); TSet<AActor*> Owners; for(auto* N:Nodes) { if(!Owners.Contains(N->GetOwner())) { N->GetOwner()->Modify(); Owners.Add(N->GetOwner()); } N->SetFlags(RF_Transactional); N->Modify(); } C->PreEditChange(P); if(!Context(false)) throw std::runtime_error("Pre-edit changed decal mobility hierarchy"); C->SetMobility(Requested); FPropertyChangedEvent Event(P,EPropertyChangeType::ValueSet); C->PostEditChangeProperty(Event); if(!Context(true)) throw std::runtime_error("Native decal mobility hierarchy readback failed; inspect partial state"); for(int32 I=0;I<Nodes.Num();++I) if(int32(Nodes[I]->Mobility.GetValue())!=Mobilities[I]) Nodes[I]->MarkPackageDirty(); }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("hierarchy_snapshot_guarded"),Guarded); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteArrayStart(TEXT("hierarchy")); for(int32 I=0;I<Nodes.Num();++I) { J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),Paths[I]); J->WriteValue(TEXT("parent_path"),GetPathNameSafe(Parents[I])); J->WriteValue(TEXT("previous_mobility"),Mobilities[I]); J->WriteValue(TEXT("requested_mobility"),(Changed && (I==0 || Requested==EComponentMobility::Movable))?int32(Requested):Mobilities[I]); J->WriteValue(TEXT("current_mobility"),int32(Nodes[I]->Mobility.GetValue())); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native decal mobility0 Static/1 Stationary/2 Movable, exact actor/GUID/label/current ordinal/direct-child-count guard and compatible parent. Native SetMobility/reregistration propagates Movable to all descendants<=256, potentially other actors/editor visualization components; all snapshotted owners/components transacted/changed packages dirtied. Other requested mobilities preserve descendants. Full hierarchy path-parent-mobility and decal authoring readback/no-op/dry-run; direct child count is not unique subtree identity between calls. Native callbacks/resource recreation may run, no rendering/build/render synchronization/load/save; compilation/native hierarchy/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::InspectMobility(const FDecalReq& R) {
 const auto* C=ResolveDecal(R); TArray<const USceneComponent*> Nodes; Nodes.Add(C); TSet<const USceneComponent*> Seen; Seen.Add(C);
 for(int32 I=0;I<Nodes.Num();++I) { const auto* N=Nodes[I]; if(Nodes.Num()>256 || !IsValid(N) || N->IsTemplate() || N->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || N->GetWorld()!=C->GetWorld()) throw std::runtime_error("At most256 valid loaded current-world attachment components required"); for(const USceneComponent* Child:N->GetAttachChildren()) { if(!IsValid(Child) || Seen.Contains(Child)) throw std::runtime_error("Valid acyclic native attachment hierarchy required"); Seen.Add(Child); Nodes.Add(Child); } }
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),R.ActorPath); J->WriteValue(TEXT("component_path"),R.ComponentPath); J->WriteValue(TEXT("actor_guid"),C->GetOwner()->GetActorGuid().ToString()); J->WriteValue(TEXT("label"),C->GetOwner()->GetActorLabel()); J->WriteValue(TEXT("mobility"),int32(C->Mobility.GetValue())); J->WriteValue(TEXT("direct_child_count"),C->GetAttachChildren().Num()); J->WriteValue(TEXT("hierarchy_count"),Nodes.Num()); J->WriteArrayStart(TEXT("hierarchy"));
 for(int32 I=0;I<Nodes.Num();++I) { const auto* N=Nodes[I]; const auto* A=N->GetOwner(); J->WriteObjectStart(); J->WriteValue(TEXT("index"),I); J->WriteValue(TEXT("component_path"),N->GetPathName()); J->WriteValue(TEXT("parent_path"),GetPathNameSafe(N->GetAttachParent())); J->WriteValue(TEXT("mobility"),int32(N->Mobility.GetValue())); J->WriteValue(TEXT("owner_path"),GetPathNameSafe(A)); J->WriteValue(TEXT("owner_guid"),IsValid(A)?A->GetActorGuid().ToString():FString()); J->WriteValue(TEXT("owner_editable"),IsValid(A) && A->IsEditable()); J->WriteValue(TEXT("level_locked"),IsValid(A) && FLevelUtils::IsLevelLocked(const_cast<AActor*>(static_cast<const AActor*>(A)))); J->WriteValue(TEXT("package_dirty"),N->GetPackage()->IsDirty()); J->WriteValue(TEXT("registered"),N->IsRegistered()); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native breadth-first root-plus-descendant decal attachment mobility snapshot<=256, ordered path/parent/mobility records usable as full stale guard. Parent None path when unattached. Includes other actors/editor visualization components, owner editability/lock/dirty/registration metadata; not rendered-state proof. Scene changes invalidate snapshot, no traversal beyond loaded attachment graph or mutation/reregistration/rendering/build/load/save; compilation/native hierarchy serialization unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString DecalUtils::InspectMaterialUsers(const FDecalReq& R) {
 FDecalReq Filtered=R; Filtered.bFilterMaterial=true; return InspectPage(Filtered);
}
FString DecalUtils::InspectLoadedMaterials(const FDecalReq& R) {
 DecalWorld(); if(R.Start<0 || R.Count<1 || R.Count>128 || R.Name.Len()>256) throw std::runtime_error("Offset/page1..128/material path substring<=256 required");
 struct FEntry { UMaterialInterface* Material; UMaterial* Base; }; TArray<FEntry> Entries;
 for(TObjectIterator<UMaterialInterface> It;It;++It) { auto* M=*It; if(!IsValid(M) || M->IsTemplate() || M->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || M->GetOutermost()==GetTransientPackage() || (!R.Name.IsEmpty() && !M->GetPathName().Contains(R.Name,ESearchCase::IgnoreCase))) continue; auto* Base=M->GetMaterial(); if(!IsValid(Base) || Base->MaterialDomain!=MD_DeferredDecal) continue; Entries.Add({M,Base}); }
 Entries.Sort([](const FEntry& A,const FEntry& B) { return A.Material->GetPathName()<B.Material->GetPathName(); }); const int32 Start=FMath::Min(R.Start,Entries.Num()),End=Start+FMath::Min(R.Count,Entries.Num()-Start);
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("path_substring"),R.Name); J->WriteValue(TEXT("matched_count"),Entries.Num()); J->WriteValue(TEXT("next_start"),End); J->WriteValue(TEXT("has_more"),End<Entries.Num()); J->WriteArrayStart(TEXT("materials"));
 for(int32 I=Start;I<End;++I) { const auto& E=Entries[I]; J->WriteObjectStart(); J->WriteValue(TEXT("index"),I); J->WriteValue(TEXT("material_path"),E.Material->GetPathName()); J->WriteValue(TEXT("class_path"),E.Material->GetClass()->GetPathName()); J->WriteValue(TEXT("base_material_path"),E.Base->GetPathName()); J->WriteValue(TEXT("package_path"),E.Material->GetPackage()->GetName()); J->WriteValue(TEXT("package_dirty"),E.Material->GetPackage()->IsDirty()); J->WriteValue(TEXT("base_material_dirty"),E.Base->GetPackage()->IsDirty()); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Loaded persistent material interfaces whose native GetMaterial base reports DeferredDecal domain, path-substring filter/path-sorted pages1..128. Not complete asset-registry inventory/unloaded assets/inheritance validation/shader compile or receiver/platform/output readiness proof. Global object scan/custom base getters/sort unbounded; loaded set changes shift offsets. No explicit asset load/material edits/shader compilation/render evaluation/build/render synchronization/save; compilation/native material discovery semantics unverified.")); J->WriteObjectEnd(); J->Close(); return Json;
}
