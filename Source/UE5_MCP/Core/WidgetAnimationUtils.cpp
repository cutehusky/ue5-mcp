#include "WidgetAnimationUtils.h"
#include "UE5_MCP/API/DTO/EditorExtReq.h"
#include "WidgetBlueprint.h"
#include "Animation/WidgetAnimation.h"
#include "Blueprint/WidgetTree.h"
#include "MovieScene.h"
#include "MovieSceneTimeHelpers.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/Kismet2NameValidators.h"
#include "Editor.h"
#include "ScopedTransaction.h"
#include "UObject/Package.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace {
UWidgetBlueprint* ResolveBlueprint(const FString& Path) {
 if(Path.IsEmpty() || Path.Len()>2048) throw std::runtime_error("Bounded Widget Blueprint path required");
 auto* BP=FindObject<UWidgetBlueprint>(nullptr,*Path);
 if(!IsValid(BP) || !BP->IsAsset() || BP->IsTemplate() || BP->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || BP->GetOutermost()==GetTransientPackage() || BP->GetPathName()!=Path || !IsValid(BP->WidgetTree)) throw std::runtime_error("Exact loaded persistent Widget Blueprint with widget tree required");
 if(BP->Animations.Num()>256) throw std::runtime_error("Widget animation budget256 exceeded");
 return BP;
}
UWidgetAnimation* FindAnimation(UWidgetBlueprint* BP,const FString& Path) {
 for(UWidgetAnimation* A:BP->Animations) if(IsValid(A) && A->GetPathName()==Path) return A;
 throw std::runtime_error("Exact current widget animation path required");
}
FString State(UWidgetBlueprint* BP) {
 TArray<UWidgetAnimation*> Sorted; for(UWidgetAnimation* A:BP->Animations) Sorted.Add(A);
 FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("widget_blueprint"),BP->GetPathName()); J->WriteArrayStart(TEXT("animations"));
 for(UWidgetAnimation* A:Sorted) { J->WriteObjectStart(); J->WriteValue(TEXT("path"),GetPathNameSafe(A)); if(IsValid(A)) { J->WriteValue(TEXT("name"),A->GetName()); J->WriteValue(TEXT("display_label"),A->GetDisplayLabel()); J->WriteValue(TEXT("binding_count"),A->AnimationBindings.Num()); UMovieScene* S=A->GetMovieScene(); J->WriteValue(TEXT("movie_scene"),GetPathNameSafe(S)); if(IsValid(S)) { const FFrameRate Tick=S->GetTickResolution(),Display=S->GetDisplayRate(); J->WriteValue(TEXT("tick_resolution"),FString::Printf(TEXT("%d/%d"),Tick.Numerator,Tick.Denominator)); J->WriteValue(TEXT("display_rate"),FString::Printf(TEXT("%d/%d"),Display.Numerator,Display.Denominator)); const TRange<FFrameNumber> Range=S->GetPlaybackRange(); const bool Bounded=Range.HasLowerBound() && Range.HasUpperBound(); J->WriteValue(TEXT("playback_range_bounded"),Bounded); if(Bounded) { const FFrameNumber Lo=UE::MovieScene::DiscreteInclusiveLower(Range),Hi=UE::MovieScene::DiscreteExclusiveUpper(Range); J->WriteValue(TEXT("start_tick"),Lo.Value); J->WriteValue(TEXT("end_tick_exclusive"),Hi.Value); J->WriteValue(TEXT("start_seconds"),Tick.AsSeconds(Lo)); J->WriteValue(TEXT("end_seconds"),Tick.AsSeconds(Hi)); } J->WriteValue(TEXT("possessable_count"),S->GetPossessableCount()); J->WriteValue(TEXT("track_count"),S->GetTracks().Num()); J->WriteValue(TEXT("read_only"),S->IsReadOnly()); } } J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}
void ValidateNewName(UWidgetBlueprint* BP,const FString& Text,UWidgetAnimation* Self) {
 if(Text.IsEmpty() || Text.Len()>64) throw std::runtime_error("Animation name length1..64 required");
 FText Reason; if(!FName::IsValidXName(Text,INVALID_OBJECTNAME_CHARACTERS INVALID_LONGPACKAGE_CHARACTERS,&Reason)) throw std::runtime_error("Animation name contains invalid object characters");
 const FName Name(*Text);
 for(UWidgetAnimation* A:BP->Animations) if(IsValid(A) && A!=Self && A->GetFName()==Name) throw std::runtime_error("Animation name collides with existing animation");
 if(BP->WidgetTree->FindWidget(Name)) throw std::runtime_error("Animation name collides with a widget variable");
 FKismetNameValidator Validator(BP,Self?Self->GetFName():NAME_None); if(Validator.IsValid(Name)!=EValidatorResult::Ok) throw std::runtime_error("Animation name rejected by native Blueprint name validator");
 if(StaticFindObject(nullptr,BP,*Text)) throw std::runtime_error("Animation name collides with an existing Blueprint subobject");
}
void ValidateRange(const FEditorExtReq& R,double& Start,double& End) {
 if(R.Numbers.Num()!=2 || !FMath::IsFinite(R.Numbers[0]) || !FMath::IsFinite(R.Numbers[1]) || R.Numbers[0]<0 || R.Numbers[1]>3600 || R.Numbers[1]<=R.Numbers[0]) throw std::runtime_error("Numbers=[start_seconds,end_seconds] with 0<=start<end<=3600 required");
 Start=R.Numbers[0]; End=R.Numbers[1];
}
void ApplyRange(UMovieScene* S,double Start,double End) {
 const FFrameRate Tick=S->GetTickResolution(); const FFrameNumber Lo=(Start*Tick).RoundToFrame(),Hi=(End*Tick).RoundToFrame();
 if(Hi.Value<=Lo.Value) throw std::runtime_error("Range collapses at native tick resolution");
 S->SetPlaybackRange(Lo,Hi.Value-Lo.Value);
}
}
FString WidgetAnimationUtils::Animations(const FEditorExtReq& R) {
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld) throw std::runtime_error("Stopped editor on game thread required");
 UWidgetBlueprint* BP=ResolveBlueprint(R.AssetPath); const FString Before=State(BP); const FString Op=R.Operation; bool Changed=false; FString CreatedPath;
 if(Op!=TEXT("Inspect")) {
  if(!GEditor->Trans || !R.bConfirm || R.ExpectedSnapshot!=Before) throw std::runtime_error("Confirmation and exact full animation-list snapshot required");
  if(Op==TEXT("Create")) { ValidateNewName(BP,R.Name,nullptr); double Start=0,End=0; ValidateRange(R,Start,End); if(BP->Animations.Num()>=256) throw std::runtime_error("Animation budget256 reached"); Changed=true;
   if(!R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Create Widget Animation"))); BP->Modify(); const FName Name(*R.Name); auto* A=NewObject<UWidgetAnimation>(BP,Name,RF_Transactional); A->SetDisplayLabel(R.Name); A->MovieScene=NewObject<UMovieScene>(A,Name,RF_Transactional); A->MovieScene->SetDisplayRate(FFrameRate(20,1)); ApplyRange(A->MovieScene,Start,End); BP->Animations.Add(A); FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); CreatedPath=A->GetPathName(); } }
  else if(Op==TEXT("Rename")) { UWidgetAnimation* A=FindAnimation(BP,R.TargetPath); if(A->GetName()==R.Name) Changed=false; else { ValidateNewName(BP,R.Name,A); Changed=true; }
   if(Changed && !R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Rename Widget Animation"))); BP->Modify(); A->Modify(); const FName Old=A->GetFName(),New(*R.Name); A->SetDisplayLabel(R.Name); A->Rename(*R.Name,nullptr,REN_DontCreateRedirectors); if(IsValid(A->MovieScene)) { A->MovieScene->Modify(); A->MovieScene->Rename(*R.Name,nullptr,REN_DontCreateRedirectors); } FBlueprintEditorUtils::ReplaceVariableReferences(BP,Old,New); FBlueprintEditorUtils::ValidateBlueprintChildVariables(BP,New); FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); } }
  else if(Op==TEXT("Delete")) { UWidgetAnimation* A=FindAnimation(BP,R.TargetPath); if(FBlueprintEditorUtils::IsVariableUsed(BP,A->GetFName()) && !R.bAllow) throw std::runtime_error("Animation variable is referenced by Blueprint graphs; bAllow breakage opt-in required"); Changed=true;
   if(!R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Delete Widget Animation"))); BP->Modify(); A->Modify(); BP->Animations.Remove(A); A->Rename(*MakeUniqueObjectName(GetTransientPackage(),UWidgetAnimation::StaticClass()).ToString(),GetTransientPackage(),REN_DontCreateRedirectors); FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); } }
  else if(Op==TEXT("SetRange")) { UWidgetAnimation* A=FindAnimation(BP,R.TargetPath); UMovieScene* S=A->GetMovieScene(); if(!IsValid(S) || S->IsReadOnly()) throw std::runtime_error("Writable animation movie scene required"); double Start=0,End=0; ValidateRange(R,Start,End); const FFrameRate Tick=S->GetTickResolution(); const TRange<FFrameNumber> Old=S->GetPlaybackRange(); Changed=!(Old.HasLowerBound() && Old.HasUpperBound() && UE::MovieScene::DiscreteInclusiveLower(Old)==(Start*Tick).RoundToFrame() && UE::MovieScene::DiscreteExclusiveUpper(Old)==(End*Tick).RoundToFrame());
   if(Changed && !R.bDryRun) { FScopedTransaction T(FText::FromString(TEXT("MCP Set Widget Animation Range"))); S->Modify(); ApplyRange(S,Start,End); BP->MarkPackageDirty(); } }
  else throw std::runtime_error("Operation must be Inspect, Create, Rename, Delete or SetRange");
 }
 const FString After=State(BP); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("operation"),Op); J->WriteValue(TEXT("snapshot"),After); J->WriteValue(TEXT("created_path"),CreatedPath); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("written"),Changed && !R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun);
 J->WriteValue(TEXT("scope"),TEXT("UMG Widget Blueprint animations Inspect/Create/Rename/Delete/SetRange. Exact loaded Widget Blueprint/full animation-list snapshot/confirmation guards; names1..64 checked against animations, widgets, native Kismet validator and subobjects. Create mirrors editor defaults (20fps display, transactional movie scene) with playback range seconds; Rename replaces variable references; Delete requires bAllow when graphs reference the animation and moves the object to the transient package. Structural modification marks dirty without compile/save. Tracks/bindings/keys not authored. Unverified."));
 J->WriteObjectEnd(); J->Close(); return Json;
}
