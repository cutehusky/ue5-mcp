#include "NavigationLinkUtils.h"
#include "NavigationWorldUtils.h"
#include "UE5_MCP/API/DTO/NavigationLinkReq.h"
#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Navigation/NavLinkProxy.h"
#include "NavigationSystem.h"
#include "NavLinkCustomComponent.h"
#include "NavAreas/NavArea.h"
#include "Components/SceneComponent.h"
#include "FileHelpers.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
	UWorld* World()
	{
		auto* W=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if(!W || W->WorldType!=EWorldType::Editor) throw std::runtime_error("An active editor world is required"); return W;
	}
	ANavLinkProxy* Proxy(UWorld* W,const FString& Path)
	{
		auto* P=FindObject<ANavLinkProxy>(nullptr,*Path);
		if(!IsValid(P) || P->GetWorld()!=W) throw std::runtime_error("ActorPath requires a native NavLinkProxy in the active editor world"); return P;
	}
	void Vector(TSharedRef<TJsonWriter<>> J,const FString& Name,const FVector& V)
	{
		J->WriteObjectStart(Name); J->WriteValue(TEXT("X"),V.X); J->WriteValue(TEXT("Y"),V.Y); J->WriteValue(TEXT("Z"),V.Z); J->WriteObjectEnd();
	}
	const TCHAR* Direction(ENavLinkDirection::Type D)
	{
		return D==ENavLinkDirection::LeftToRight ? TEXT("LeftToRight") : D==ENavLinkDirection::RightToLeft ? TEXT("RightToLeft") : TEXT("BothWays");
	}
	bool Equal(const TArray<FNavigationLink>& A,const TArray<FNavigationLink>& B)
	{
		if(A.Num()!=B.Num()) return false;
		for(int32 I=0;I<A.Num();++I)
		{
			const auto& X=A[I]; const auto& Y=B[I];
			if(X.Left!=Y.Left || X.Right!=Y.Right || X.Direction!=Y.Direction || X.GetAreaClass()!=Y.GetAreaClass() || X.SnapRadius!=Y.SnapRadius || X.SnapHeight!=Y.SnapHeight || X.bUseSnapHeight!=Y.bUseSnapHeight || X.bSnapToCheapestArea!=Y.bSnapToCheapestArea || X.LeftProjectHeight!=Y.LeftProjectHeight || X.MaxFallDownLength!=Y.MaxFallDownLength || !X.SupportedAgents.IsSame(Y.SupportedAgents)) return false;
		} return true;
	}
	void Row(TSharedRef<TJsonWriter<>> J,ANavLinkProxy* P)
	{
		J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),P->GetPathName()); J->WriteValue(TEXT("label"),P->GetActorLabel()); Vector(J,TEXT("location"),P->GetActorLocation());
		const auto Rotation=P->GetActorRotation(); J->WriteObjectStart(TEXT("rotation")); J->WriteValue(TEXT("Pitch"),Rotation.Pitch); J->WriteValue(TEXT("Yaw"),Rotation.Yaw); J->WriteValue(TEXT("Roll"),Rotation.Roll); J->WriteObjectEnd();
		J->WriteValue(TEXT("smart_link_relevant"),P->bSmartLinkIsRelevant); J->WriteValue(TEXT("segment_link_count"),P->SegmentLinks.Num()); J->WriteValue(TEXT("point_link_count"),P->PointLinks.Num());
		if(auto* C=P->GetSmartLinkComp())
		{
			FVector L,R; ENavLinkDirection::Type D; C->GetLinkData(L,R,D);
			J->WriteObjectStart(TEXT("smart_link")); J->WriteValue(TEXT("component_path"),C->GetPathName());
			Vector(J,TEXT("left"),L); Vector(J,TEXT("right"),R); Vector(J,TEXT("requested_left_world"),C->GetStartPoint()); Vector(J,TEXT("requested_right_world"),C->GetEndPoint());
			J->WriteValue(TEXT("direction"),Direction(D)); J->WriteValue(TEXT("enabled"),C->IsEnabled()); J->WriteValue(TEXT("has_moving_agents"),C->HasMovingAgents());
			J->WriteValue(TEXT("enabled_area_class"),C->GetEnabledArea() ? C->GetEnabledArea()->GetPathName() : TEXT("")); J->WriteValue(TEXT("disabled_area_class"),C->GetDisabledArea() ? C->GetDisabledArea()->GetPathName() : TEXT(""));
			J->WriteValue(TEXT("supported_agent_bits"),int64(C->GetSupportedAgents().GetAgentBits())); J->WriteValue(TEXT("native_link_id"),FString::Printf(TEXT("%llu"),C->GetId().GetId())); J->WriteObjectEnd();
		}
		J->WriteValue(TEXT("points_truncated"),P->PointLinks.Num()>64); J->WriteArrayStart(TEXT("point_links"));
		for(int32 I=0;I<FMath::Min(P->PointLinks.Num(),64);++I)
		{
			const auto& L=P->PointLinks[I]; J->WriteObjectStart(); J->WriteValue(TEXT("index"),I); Vector(J,TEXT("left"),L.Left); Vector(J,TEXT("right"),L.Right);
			Vector(J,TEXT("requested_left_world"),P->GetActorTransform().TransformPosition(L.Left)); Vector(J,TEXT("requested_right_world"),P->GetActorTransform().TransformPosition(L.Right));
			J->WriteValue(TEXT("direction"),Direction(L.Direction)); J->WriteValue(TEXT("area_class"),L.GetAreaClass() ? L.GetAreaClass()->GetPathName() : TEXT(""));
			J->WriteValue(TEXT("snap_radius"),L.SnapRadius); J->WriteValue(TEXT("snap_height"),L.SnapHeight); J->WriteValue(TEXT("use_snap_height"),bool(L.bUseSnapHeight)); J->WriteValue(TEXT("snap_to_cheapest_area"),bool(L.bSnapToCheapestArea));
			J->WriteValue(TEXT("left_project_height"),L.LeftProjectHeight); J->WriteValue(TEXT("right_project_height"),L.MaxFallDownLength); J->WriteValue(TEXT("supported_agent_bits"),int64(L.SupportedAgents.GetAgentBits())); J->WriteObjectEnd();
		}
		J->WriteArrayEnd(); J->WriteObjectEnd();
	}
	FString Json(UWorld* W,ANavLinkProxy* Only=nullptr,bool Changed=false,bool Dry=false,bool Saved=false)
	{
		FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetOutermost()->GetName()); J->WriteValue(TEXT("dirty"),W->GetOutermost()->IsDirty()); J->WriteValue(TEXT("changed"),Changed && !Dry); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved);
		J->WriteValue(TEXT("runtime_only"),W->WorldType==EWorldType::PIE);
		auto* S=Cast<UNavigationSystemV1>(W->GetNavigationSystem()); J->WriteValue(TEXT("running_build_tasks"),S ? S->GetNumRunningBuildTasks() : 0); J->WriteValue(TEXT("remaining_build_tasks"),S ? S->GetNumRemainingBuildTasks() : 0);
		J->WriteArrayStart(TEXT("proxies")); int32 Count=0; if(Only) { Row(J,Only); Count=1; } else for(TActorIterator<ANavLinkProxy> It(W);It;++It) if(++Count<=256) Row(J,*It); J->WriteArrayEnd(); J->WriteValue(TEXT("proxy_count"),Count); J->WriteValue(TEXT("proxies_truncated"),Count>256);
		J->WriteValue(TEXT("scope"),TEXT("Native proxy data in the selected editor/PIE world; local/requested endpoints precede native projection/snapping; configuration needs generation, enabled-area updates use native runtime control; traversal callbacks are separate")); J->WriteObjectEnd(); J->Close(); return Result;
	}
}

FString NavigationLinkUtils::Inspect(const FString& Path,const FString& Context,int32 PIEInstance)
{
	auto* W=NavigationWorldUtils::Resolve(Context,PIEInstance); return Json(W,Path.IsEmpty() ? nullptr : Proxy(W,Path));
}

FString NavigationLinkUtils::Control(const FNavigationLinkReq& R)
{
	if(R.WorldContext!=TEXT("editor") || R.PIEInstance!=-1) throw std::runtime_error("Simple-link authoring requires the editor world");
	auto* W=World();
	if(GEditor->PlayWorld || GEditor->bIsSimulatingInEditor || W->GetWorldPartition()) throw std::runtime_error("Simple-link mutations require an ordinary editor map with PIE/simulation stopped");
	if(!R.WorldPath.IsEmpty() && R.WorldPath!=W->GetOutermost()->GetName()) throw std::runtime_error("WorldPath does not match the active persistent map package");
	if(R.bSave && (!W->GetOutermost()->GetName().StartsWith(TEXT("/Game/")) || !FPackageName::DoesPackageExist(W->GetOutermost()->GetName()))) throw std::runtime_error("Save the map to an existing /Game package first");
	const FString Op=R.Operation.ToLower(); if(Op!=TEXT("create") && Op!=TEXT("update") && Op!=TEXT("delete")) throw std::runtime_error("Link operation must be create, update or delete");
	ANavLinkProxy* P=nullptr;
	if(Op==TEXT("create")) { if(!R.ActorPath.IsEmpty()) throw std::runtime_error("ActorPath must be empty when creating a link proxy"); }
	else { P=Proxy(W,R.ActorPath); if(P->GetClass()!=ANavLinkProxy::StaticClass() || P->GetLevel()!=W->PersistentLevel || P->bSmartLinkIsRelevant || !P->SegmentLinks.IsEmpty()) throw std::runtime_error("Only plain native persistent-level simple-link proxies without relevant smart links or segment links are supported"); }
	if(Op==TEXT("delete") && !R.bConfirm) throw std::runtime_error("Deleting a link proxy requires bConfirm=true");
	if(R.Location.ContainsNaN() || R.Location.GetAbsMax()>1.e9 || R.Rotation.ContainsNaN() || FMath::Max3(FMath::Abs(R.Rotation.Pitch),FMath::Abs(R.Rotation.Yaw),FMath::Abs(R.Rotation.Roll))>36000 || R.Label.Len()>128 || R.PointLinks.Num()>64) throw std::runtime_error("Invalid transform/label or more than 64 point links");
	TArray<FNavigationLink> Links;
	if(Op!=TEXT("delete")) for(const auto& L:R.PointLinks)
	{
		if(L.Left.ContainsNaN() || L.Right.ContainsNaN() || L.Left.GetAbsMax()>1.e6 || L.Right.GetAbsMax()>1.e6 || FVector::DistSquared(L.Left,L.Right)<.000001) throw std::runtime_error("Local link endpoints require distinct finite positions within +/-1e6 units");
		if(!FMath::IsFinite(L.SnapRadius) || L.SnapRadius<1 || L.SnapRadius>10000 || !FMath::IsFinite(L.SnapHeight) || L.SnapHeight<1 || L.SnapHeight>10000 || !FMath::IsFinite(L.LeftProjectHeight) || L.LeftProjectHeight<0 || L.LeftProjectHeight>10000 || !FMath::IsFinite(L.RightProjectHeight) || L.RightProjectHeight<0 || L.RightProjectHeight>10000) throw std::runtime_error("Snap radius/height requires [1,10000]; project heights require [0,10000]");
		auto* Area=LoadObject<UClass>(nullptr,*L.AreaClass);
		if(!Area || !Area->IsChildOf(UNavArea::StaticClass()) || Area->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("Link area requires a concrete compatible NavArea class");
		FNavigationLink V; V.Left=L.Left; V.Right=L.Right; V.SetAreaClass(Area);
		if(L.Direction==TEXT("BothWays")) V.Direction=ENavLinkDirection::BothWays; else if(L.Direction==TEXT("LeftToRight")) V.Direction=ENavLinkDirection::LeftToRight; else if(L.Direction==TEXT("RightToLeft")) V.Direction=ENavLinkDirection::RightToLeft; else throw std::runtime_error("Direction requires BothWays, LeftToRight or RightToLeft");
		V.SnapRadius=L.SnapRadius; V.SnapHeight=L.SnapHeight; V.bUseSnapHeight=L.bUseSnapHeight; V.bSnapToCheapestArea=L.bSnapToCheapestArea; V.LeftProjectHeight=L.LeftProjectHeight; V.MaxFallDownLength=L.RightProjectHeight;
		if(L.bSetSupportedAgents) { uint32 Bits=0; for(int32 I:L.SupportedAgentIndices) { if(I<0 || I>15 || (Bits & (1u<<I))) throw std::runtime_error("Agent indices require unique values in [0,15]"); Bits|=1u<<I; } V.SupportedAgents=FNavAgentSelector(Bits); V.SupportedAgents.MarkInitialized(); }
		else if(!L.SupportedAgentIndices.IsEmpty()) throw std::runtime_error("bSetSupportedAgents=true is required for an explicit agent selection");
		Links.Add(V);
	}
	const bool Changed=Op!=TEXT("update") || !Equal(P->PointLinks,Links) || !P->GetActorLocation().Equals(R.Location) || !P->GetActorRotation().Equals(R.Rotation.GetNormalized()) || !P->GetActorScale3D().Equals(FVector::OneVector) || (!R.Label.IsEmpty() && P->GetActorLabel()!=R.Label);
	if(!R.bDryRun && Changed)
	{
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","NavigationLinks","Edit Navigation Point Links"));
		if(Op==TEXT("delete")) { P->Modify(); if(!W->EditorDestroyActor(P,true)) throw std::runtime_error("Native proxy deletion failed"); P=nullptr; }
		else
		{
			if(!P) { W->PersistentLevel->Modify(); FActorSpawnParameters Params; Params.OverrideLevel=W->PersistentLevel; Params.ObjectFlags=RF_Transactional; P=W->SpawnActor<ANavLinkProxy>(ANavLinkProxy::StaticClass(),R.Location,R.Rotation.GetNormalized(),Params); if(!P) throw std::runtime_error("Native link proxy creation failed"); }
			P->Modify(); if(auto* C=P->GetRootComponent()) { C->SetFlags(RF_Transactional); C->Modify(); }
			P->PreEditChange(nullptr); P->PointLinks=MoveTemp(Links); P->SetActorLocation(R.Location); P->SetActorRotation(R.Rotation.GetNormalized()); P->SetActorScale3D(FVector::OneVector); if(!R.Label.IsEmpty()) P->SetActorLabel(R.Label);
			auto* Field=FindFProperty<FArrayProperty>(ANavLinkProxy::StaticClass(),TEXT("PointLinks")); FPropertyChangedEvent Event(Field,EPropertyChangeType::ValueSet); P->PostEditChangeProperty(Event); FNavigationSystem::UpdateActorData(*P); P->MarkPackageDirty();
		}
	}
	bool Saved=false; if(!R.bDryRun && R.bSave && W->GetOutermost()->IsDirty()) { if(!UEditorLoadingAndSavingUtils::SaveMap(W,W->GetOutermost()->GetName())) throw std::runtime_error("Links changed but map saving failed"); Saved=true; }
	return Json(W,P,Changed,R.bDryRun,Saved);
}

FString NavigationLinkUtils::Smart(const FNavigationLinkReq& R)
{
	auto* W=NavigationWorldUtils::Resolve(R.WorldContext,R.PIEInstance); const FString Op=R.Operation.ToLower();
	if(!R.WorldPath.IsEmpty() && R.WorldPath!=W->GetOutermost()->GetName()) throw std::runtime_error("WorldPath does not match the selected navigation world package");
	if(Op==TEXT("set_enabled"))
	{
		if(W->WorldType!=EWorldType::PIE || R.bSave) throw std::runtime_error("Runtime set_enabled requires a selected PIE world and cannot save assets");
		auto* P=Proxy(W,R.ActorPath); auto* C=P->GetSmartLinkComp();
		if(!C || !P->bSmartLinkIsRelevant) throw std::runtime_error("The selected PIE proxy must have a relevant native smart-link component");
		const bool Changed=C->IsEnabled()!=R.bEnabled;
		if(!R.bDryRun && Changed) P->SetSmartLinkEnabled(R.bEnabled);
		return Json(W,P,Changed,R.bDryRun,false);
	}
	if(R.WorldContext!=TEXT("editor") || GEditor->PlayWorld || GEditor->bIsSimulatingInEditor || W->GetWorldPartition()) throw std::runtime_error("Smart-link authoring requires an ordinary editor map with PIE/simulation stopped");
	if(Op!=TEXT("create") && Op!=TEXT("update") && Op!=TEXT("delete")) throw std::runtime_error("Smart-link operation must be create, update, delete or PIE set_enabled");
	if(R.bSave && (!W->GetOutermost()->GetName().StartsWith(TEXT("/Game/")) || !FPackageName::DoesPackageExist(W->GetOutermost()->GetName()))) throw std::runtime_error("Save the map to an existing /Game package first");
	ANavLinkProxy* P=nullptr;
	if(Op==TEXT("create")) { if(!R.ActorPath.IsEmpty()) throw std::runtime_error("ActorPath must be empty for creation"); }
	else { P=Proxy(W,R.ActorPath); if(P->GetClass()!=ANavLinkProxy::StaticClass() || P->GetLevel()!=W->PersistentLevel || !P->PointLinks.IsEmpty() || !P->SegmentLinks.IsEmpty()) throw std::runtime_error("Smart-only authoring requires a plain native persistent-level proxy without simple/segment links"); }
	if(Op==TEXT("delete") && !R.bConfirm) throw std::runtime_error("Deleting a smart-link proxy requires bConfirm=true");
	if(R.Location.ContainsNaN() || R.Location.GetAbsMax()>1.e9 || R.Rotation.ContainsNaN() || FMath::Max3(FMath::Abs(R.Rotation.Pitch),FMath::Abs(R.Rotation.Yaw),FMath::Abs(R.Rotation.Roll))>36000 || R.Label.Len()>128) throw std::runtime_error("Invalid actor transform or label");
	auto* C=P ? P->GetSmartLinkComp() : GetDefault<ANavLinkProxy>()->GetSmartLinkComp();
	if(!C) throw std::runtime_error("Native smart-link component is unavailable");
	FVector OldLeft,OldRight; ENavLinkDirection::Type OldDirection; C->GetLinkData(OldLeft,OldRight,OldDirection);
	ENavLinkDirection::Type D=ENavLinkDirection::BothWays; UClass* Enabled=nullptr; UClass* Disabled=nullptr; auto Agents=C->GetSupportedAgents();
	if(Op!=TEXT("delete"))
	{
		if(R.SmartLeft.ContainsNaN() || R.SmartRight.ContainsNaN() || R.SmartLeft.GetAbsMax()>1.e6 || R.SmartRight.GetAbsMax()>1.e6 || FVector::DistSquared(R.SmartLeft,R.SmartRight)<.000001) throw std::runtime_error("Smart endpoints must be distinct finite local positions within +/-1e6 units");
		if(R.SmartDirection==TEXT("LeftToRight")) D=ENavLinkDirection::LeftToRight; else if(R.SmartDirection==TEXT("RightToLeft")) D=ENavLinkDirection::RightToLeft; else if(R.SmartDirection!=TEXT("BothWays")) throw std::runtime_error("Invalid smart-link direction");
		auto Area=[](const FString& Path)->UClass* { auto* A=LoadObject<UClass>(nullptr,*Path); if(!A || !A->IsChildOf(UNavArea::StaticClass()) || A->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("Enabled/disabled areas require concrete compatible NavArea classes"); return A; };
		Enabled=Area(R.EnabledAreaClass); Disabled=Area(R.DisabledAreaClass);
		if(R.bSetSmartAgents) { uint32 Bits=0; for(int32 I:R.SmartAgentIndices) { if(I<0 || I>15 || (Bits & (1u<<I))) throw std::runtime_error("Smart agent indices must be unique values in [0,15]"); Bits|=1u<<I; } Agents=FNavAgentSelector(Bits); Agents.MarkInitialized(); }
		else if(!R.SmartAgentIndices.IsEmpty()) throw std::runtime_error("bSetSmartAgents=true is required for explicit agents");
	}
	const bool Changed=Op!=TEXT("update") || P->bSmartLinkIsRelevant!=R.bSmartLinkRelevant || C->IsEnabled()!=R.bEnabled || OldLeft!=R.SmartLeft || OldRight!=R.SmartRight || OldDirection!=D || C->GetEnabledArea()!=Enabled || C->GetDisabledArea()!=Disabled || !C->GetSupportedAgents().IsSame(Agents) || !P->GetActorLocation().Equals(R.Location) || !P->GetActorRotation().Equals(R.Rotation.GetNormalized()) || !P->GetActorScale3D().Equals(FVector::OneVector) || (!R.Label.IsEmpty() && P->GetActorLabel()!=R.Label);
	if(!R.bDryRun && Changed)
	{
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","SmartNavigationLink","Edit Smart Navigation Link"));
		if(Op==TEXT("delete")) { P->Modify(); if(!W->EditorDestroyActor(P,true)) throw std::runtime_error("Native proxy deletion failed"); P=nullptr; }
		else
		{
			if(!P) { W->PersistentLevel->Modify(); FActorSpawnParameters Params; Params.OverrideLevel=W->PersistentLevel; Params.ObjectFlags=RF_Transactional; P=W->SpawnActor<ANavLinkProxy>(ANavLinkProxy::StaticClass(),R.Location,R.Rotation.GetNormalized(),Params); if(!P) throw std::runtime_error("Native proxy creation failed"); P->PointLinks.Reset(); }
			C=P->GetSmartLinkComp(); P->Modify(); C->SetFlags(RF_Transactional); C->Modify(); if(auto* Root=P->GetRootComponent()) { Root->SetFlags(RF_Transactional); Root->Modify(); }
			P->PreEditChange(nullptr); P->SetActorLocation(R.Location); P->SetActorRotation(R.Rotation.GetNormalized()); P->SetActorScale3D(FVector::OneVector); if(!R.Label.IsEmpty()) P->SetActorLabel(R.Label);
			P->bSmartLinkIsRelevant=R.bSmartLinkRelevant; C->SetLinkData(R.SmartLeft,R.SmartRight,D); C->SetSupportedAgents(Agents); C->SetEnabledArea(Enabled); C->SetDisabledArea(Disabled); C->SetEnabled(R.bEnabled);
			auto* Field=FindFProperty<FBoolProperty>(ANavLinkProxy::StaticClass(),TEXT("bSmartLinkIsRelevant")); FPropertyChangedEvent Event(Field,EPropertyChangeType::ValueSet); P->PostEditChangeProperty(Event); C->RefreshNavigationModifiers(); FNavigationSystem::UpdateActorData(*P); P->MarkPackageDirty();
		}
	}
	bool Saved=false; if(!R.bDryRun && R.bSave && W->GetOutermost()->IsDirty()) { if(!UEditorLoadingAndSavingUtils::SaveMap(W,W->GetOutermost()->GetName())) throw std::runtime_error("Smart link changed but map saving failed"); Saved=true; }
	return Json(W,P,Changed,R.bDryRun,Saved);
}
