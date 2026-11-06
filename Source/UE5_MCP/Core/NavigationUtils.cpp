#include "NavigationUtils.h"
#include "NavigationWorldUtils.h"
#include "UE5_MCP/API/DTO/NavigationReq.h"
#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "NavigationPath.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavMesh/NavMeshPath.h"
#include "NavModifierVolume.h"
#include "NavFilters/NavigationQueryFilter.h"
#include "ActorFactories/ActorFactory.h"
#include "Builders/CubeBuilder.h"
#include "Components/BrushComponent.h"
#include "ScopedTransaction.h"
#include "FileHelpers.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>

namespace
{
	using FWriter = TSharedRef<TJsonWriter<>>;
	void Vector(FWriter J,const FString& Key,const FVector& V)
	{
		J->WriteObjectStart(Key); J->WriteValue(TEXT("X"),V.X); J->WriteValue(TEXT("Y"),V.Y); J->WriteValue(TEXT("Z"),V.Z); J->WriteObjectEnd();
	}
	void Position(const FVector& V)
	{
		if(V.ContainsNaN() || V.GetAbsMax()>1.e9) throw std::runtime_error("Coordinates must be finite and within +/-1e9 units");
	}
	UWorld* World(const FNavigationReq* R=nullptr,bool Mutate=false)
	{
		if(Mutate && R && R->WorldContext!=TEXT("editor")) throw std::runtime_error("Navigation volume/build mutations require the editor world");
		auto* W=NavigationWorldUtils::Resolve(R ? R->WorldContext : TEXT("editor"),R ? R->PIEInstance : -1);
		if(R && !R->WorldPath.IsEmpty() && R->WorldPath!=W->GetOutermost()->GetName()) throw std::runtime_error("WorldPath does not match the active persistent editor map package");
		if(Mutate && (GEditor->PlayWorld || GEditor->bIsSimulatingInEditor)) throw std::runtime_error("Stop PIE or simulation before navigation mutations");
		if(Mutate && W->GetWorldPartition()) throw std::runtime_error("World Partition navigation volume/build authoring requires its dedicated external-actor and navigation-builder workflow; this route supports ordinary maps");
		if(R && R->bSave && (!W->GetOutermost()->GetName().StartsWith(TEXT("/Game/")) || !FPackageName::DoesPackageExist(W->GetOutermost()->GetName()))) throw std::runtime_error("Save the current map to an existing /Game package first");
		return W;
	}
	UNavigationSystemV1* System(UWorld* W)
	{
		auto* S=Cast<UNavigationSystemV1>(W->GetNavigationSystem());
		if(!S) throw std::runtime_error("The active editor world has no NavigationSystemV1; configure World Settings first");
		return S;
	}
	bool Save(UWorld* W,const FNavigationReq& R)
	{
		if(!R.bSave || R.bDryRun || !W->GetOutermost()->IsDirty()) return false;
		if(!UEditorLoadingAndSavingUtils::SaveMap(W,W->GetOutermost()->GetName())) throw std::runtime_error("Navigation operation changed the world but map saving failed");
		return true;
	}
	void BoundsRow(FWriter J,ANavMeshBoundsVolume* V)
	{
		J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),V->GetPathName()); J->WriteValue(TEXT("label"),V->GetActorLabel());
		const auto B=V->GetComponentsBoundingBox(true); Vector(J,TEXT("location"),V->GetActorLocation()); Vector(J,TEXT("bounds_center"),B.GetCenter()); Vector(J,TEXT("bounds_extent"),B.GetExtent());
		J->WriteValue(TEXT("supported_agent_bits"),int64(V->SupportedAgents.GetAgentBits())); J->WriteObjectEnd();
	}
	void State(FWriter J,UWorld* W)
	{
		auto* S=Cast<UNavigationSystemV1>(W->GetNavigationSystem());
		J->WriteValue(TEXT("world_path"),W->GetOutermost()->GetName()); J->WriteValue(TEXT("dirty"),W->GetOutermost()->IsDirty());
		J->WriteValue(TEXT("system_path"),S ? S->GetPathName() : TEXT("")); J->WriteValue(TEXT("partitioned"),W->GetWorldPartition()!=nullptr);
		J->WriteValue(TEXT("build_in_progress"),S && S->IsNavigationBuildInProgress()); J->WriteValue(TEXT("build_locked"),S && S->IsNavigationBuildingLocked());
		J->WriteValue(TEXT("remaining_build_tasks"),S ? S->GetNumRemainingBuildTasks() : 0); J->WriteValue(TEXT("running_build_tasks"),S ? S->GetNumRunningBuildTasks() : 0);
		J->WriteArrayStart(TEXT("bounds")); int32 Count=0; for(TActorIterator<ANavMeshBoundsVolume> It(W);It;++It) { if(Count++<256) BoundsRow(J,*It); } J->WriteArrayEnd(); J->WriteValue(TEXT("bounds_count"),Count); J->WriteValue(TEXT("bounds_truncated"),Count>256);
		J->WriteArrayStart(TEXT("modifiers")); int32 ModifierCount=0;
		for(TActorIterator<ANavModifierVolume> It(W);It;++It)
		{
			++ModifierCount; if(ModifierCount>256) continue; auto* M=*It; const auto Box=M->GetNavigationBounds();
			J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),M->GetPathName()); J->WriteValue(TEXT("label"),M->GetActorLabel());
			Vector(J,TEXT("location"),M->GetActorLocation()); Vector(J,TEXT("bounds_center"),Box.GetCenter()); Vector(J,TEXT("bounds_extent"),Box.GetExtent());
			J->WriteValue(TEXT("area_class"),M->GetAreaClass() ? M->GetAreaClass()->GetPathName() : TEXT(""));
			J->WriteValue(TEXT("area_class_to_replace"),M->GetAreaClassToReplace() ? M->GetAreaClassToReplace()->GetPathName() : TEXT("")); J->WriteObjectEnd();
		}
		J->WriteArrayEnd(); J->WriteValue(TEXT("modifier_count"),ModifierCount); J->WriteValue(TEXT("modifiers_truncated"),ModifierCount>256);
		J->WriteArrayStart(TEXT("nav_data")); int32 DataCount=0; if(S) for(ANavigationData* D:S->NavDataSet) if(IsValid(D))
		{
			++DataCount; if(DataCount>256) continue; J->WriteObjectStart(); J->WriteValue(TEXT("path"),D->GetPathName()); J->WriteValue(TEXT("class"),D->GetClass()->GetPathName());
			J->WriteValue(TEXT("agent_name"),D->GetConfig().Name.ToString()); J->WriteValue(TEXT("agent_radius"),D->GetConfig().AgentRadius); J->WriteValue(TEXT("agent_height"),D->GetConfig().AgentHeight);
			J->WriteValue(TEXT("needs_rebuild"),D->NeedsRebuild()); J->WriteObjectEnd();
		} J->WriteArrayEnd(); J->WriteValue(TEXT("nav_data_count"),DataCount); J->WriteValue(TEXT("nav_data_truncated"),DataCount>256);
	}
}

FString NavigationUtils::Inspect()
{
	FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); State(J,World()); J->WriteObjectEnd(); J->Close(); return Json;
}

namespace
{
FString EditVolume(const FNavigationReq& R,bool Modifier)
{
	auto* W=World(&R,true); const FString Op=R.Operation.ToLower();
	if(Op!=TEXT("create") && Op!=TEXT("update") && Op!=TEXT("delete")) throw std::runtime_error("Navigation volume operation must be create, update or delete");
	UClass* VolumeClass=Modifier ? ANavModifierVolume::StaticClass() : ANavMeshBoundsVolume::StaticClass();
	AVolume* V=nullptr;
	if(Op==TEXT("create")) { if(!R.ActorPath.IsEmpty()) throw std::runtime_error("ActorPath must be empty when creating bounds"); }
	else { V=FindObject<AVolume>(nullptr,*R.ActorPath); if(!IsValid(V) || !V->IsA(VolumeClass) || V->GetWorld()!=W || V->GetLevel()!=W->PersistentLevel) throw std::runtime_error("ActorPath must identify the requested navigation volume type in the active persistent level"); }
	if(Op==TEXT("delete") && !R.bConfirm) throw std::runtime_error("Deleting navigation volumes requires bConfirm=true");
	if(Op!=TEXT("delete")) { Position(R.Location); Position(R.Extent); if(R.Extent.GetMin()<1 || R.Extent.GetMax()>100000 || R.Label.Len()>128) throw std::runtime_error("Bounds half extents require [1,100000] units and label at most 128 characters"); }
	UClass* Area=nullptr; UClass* Replace=nullptr;
	if(Modifier && Op!=TEXT("delete"))
	{
		auto Resolve=[](const FString& Path)->UClass* { if(Path.IsEmpty()) return nullptr; auto* C=LoadObject<UClass>(nullptr,*Path); if(!C || !C->IsChildOf(UNavArea::StaticClass()) || C->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("Modifier area references require concrete compatible NavArea class paths"); return C; };
		Area=Resolve(R.AreaClass); Replace=Resolve(R.AreaClassToReplace);
	}
	bool Changed=Op!=TEXT("update") || !V->GetActorLocation().Equals(R.Location,.001) || !V->GetComponentsBoundingBox(true).GetExtent().Equals(R.Extent,.001) || !V->GetActorRotation().IsNearlyZero() || !V->GetActorScale3D().Equals(FVector::OneVector) || (!R.Label.IsEmpty() && R.Label!=V->GetActorLabel());
	if(Modifier && Op==TEXT("update")) { auto* M=CastChecked<ANavModifierVolume>(V); Changed|=M->GetAreaClass()!=Area || M->GetAreaClassToReplace()!=Replace; }
	FString Path=V ? V->GetPathName() : TEXT("");
	if(!R.bDryRun && Changed)
	{
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","NavVolume","Edit Navigation Volume"));
		if(Op==TEXT("delete")) { V->Modify(); if(!W->EditorDestroyActor(V,true)) throw std::runtime_error("Native navigation bounds deletion failed"); V=nullptr; }
		else
		{
			if(!V) { W->PersistentLevel->Modify(); FActorSpawnParameters Params; Params.OverrideLevel=W->PersistentLevel; Params.ObjectFlags=RF_Transactional; V=W->SpawnActor<AVolume>(VolumeClass,R.Location,FRotator::ZeroRotator,Params); if(!V) throw std::runtime_error("Native navigation volume spawn failed"); }
			V->Modify(); V->GetBrushComponent()->SetFlags(RF_Transactional); V->GetBrushComponent()->Modify(); V->SetActorLocation(R.Location); V->SetActorRotation(FRotator::ZeroRotator); V->SetActorScale3D(FVector::OneVector);
			auto* B=NewObject<UCubeBuilder>(); B->X=float(R.Extent.X*2); B->Y=float(R.Extent.Y*2); B->Z=float(R.Extent.Z*2); B->Hollow=false; B->Tessellated=false;
			UActorFactory::CreateBrushForVolumeActor(V,B);
			if(!R.Label.IsEmpty()) V->SetActorLabel(R.Label);
			if(Modifier) { auto* M=CastChecked<ANavModifierVolume>(V); M->SetAreaClass(Area); M->SetAreaClassToReplace(Replace); M->RebuildNavigationData(); }
			else if(auto* S=Cast<UNavigationSystemV1>(W->GetNavigationSystem())) S->OnNavigationBoundsUpdated(CastChecked<ANavMeshBoundsVolume>(V));
			V->MarkPackageDirty(); Path=V->GetPathName();
		}
	}
	const bool Saved=Save(W,R); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),Path); J->WriteValue(TEXT("changed"),Changed); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dry_run"),R.bDryRun); State(J,W); J->WriteObjectEnd(); J->Close(); return Json;
}
}

FString NavigationUtils::Bounds(const FNavigationReq& R) { return EditVolume(R,false); }
FString NavigationUtils::Modifiers(const FNavigationReq& R) { return EditVolume(R,true); }

FString NavigationUtils::Build(const FNavigationReq& R)
{
	auto* W=World(&R,true); auto* S=System(W);
	if(!R.bConfirm) throw std::runtime_error("Rebuilding current-world navigation requires bConfirm=true");
	if(S->GetNumRunningBuildTasks()>0) throw std::runtime_error("Native navigation generation tasks are running; wait for completion");
	// Match the native explicit-build policy: the automatic-editor-update lock
	// must not prevent a user-requested manual build.
	if(S->IsNavigationBuildingLocked(uint8(~ENavigationBuildLock::NoUpdateInEditor)) || !S->IsThereAnywhereToBuildNavigation()) throw std::runtime_error("Navigation building is locked or there are no eligible navigation bounds");
	const double Started=FPlatformTime::Seconds(); if(!R.bDryRun) S->Build(); const bool Saved=Save(W,R);
	FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("submitted"),!R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("elapsed_seconds"),FPlatformTime::Seconds()-Started);
	J->WriteValue(TEXT("scope"),TEXT("Blocking native build of eligible navigation data in the active ordinary editor world; completion does not prove navigability, use projection/path queries")); State(J,W); J->WriteObjectEnd(); J->Close(); return Json;
}

FString NavigationUtils::Query(const FNavigationReq& R)
{
	auto* W=World(&R); auto* S=System(W); const FString Op=R.Operation.ToLower();
	const bool Random=Op==TEXT("random_reachable") || Op==TEXT("random_navigable");
	if(Op!=TEXT("project") && Op!=TEXT("path") && Op!=TEXT("inspect_filter") && !Random) throw std::runtime_error("Query operation must be project, path, inspect_filter, random_reachable or random_navigable");
	if(Random && (!FMath::IsFinite(R.Radius) || R.Radius<=0 || R.Radius>100000 || R.SampleCount<1 || R.SampleCount>32)) throw std::runtime_error("Radius requires (0,100000] and SampleCount [1,32]");
	Position(R.Start); Position(R.End); Position(R.QueryExtent);
	if(R.QueryExtent.GetMin()<=0 || R.QueryExtent.GetMax()>10000 || R.MaxSearchNodes<16 || R.MaxSearchNodes>65536 || R.MaxPoints<1 || R.MaxPoints>1024 || !FMath::IsFinite(R.CostLimit) || R.CostLimit<=0 || R.CostLimit>1.e12) throw std::runtime_error("Invalid query extent, search-node limit [16,65536], point limit [1,1024] or cost limit (0,1e12]");
	auto* D=R.NavDataPath.IsEmpty() ? S->GetDefaultNavDataInstance(FNavigationSystem::DontCreate) : FindObject<ANavigationData>(nullptr,*R.NavDataPath);
	if(!IsValid(D) || D->GetWorld()!=W || !S->NavDataSet.Contains(D)) throw std::runtime_error("Select registered navigation data in the active world; build navigation first if none exists");
	UClass* FilterClass=R.FilterClass.IsEmpty() ? nullptr : LoadObject<UClass>(nullptr,*R.FilterClass);
	if(!R.FilterClass.IsEmpty() && (!FilterClass || !FilterClass->IsChildOf(UNavigationQueryFilter::StaticClass()) || FilterClass->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists))) throw std::runtime_error("FilterClass requires a concrete native navigation query filter class");
	auto BaseFilter=FilterClass ? UNavigationQueryFilter::GetQueryFilter(*D,W,FilterClass) : D->GetDefaultQueryFilter();
	if(!BaseFilter.IsValid()) throw std::runtime_error("Native navigation query filter is unavailable");
	if(Op==TEXT("inspect_filter"))
	{
		const int32 Capacity=D->GetMaxSupportedAreas();
		if(Capacity<1 || Capacity>256) throw std::runtime_error("Native navigation data does not expose a bounded area-cost table of at most 256 slots");
		TArray<float> Costs,Entries; Costs.Init(0,Capacity); Entries.Init(0,Capacity); BaseFilter->GetAllAreaCosts(Costs.GetData(),Entries.GetData(),Capacity);
		TArray<FSupportedAreaData> Areas; D->GetSupportedAreas(Areas);
		FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
		J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("world_context"),R.WorldContext); J->WriteValue(TEXT("nav_data_path"),D->GetPathName()); J->WriteValue(TEXT("filter_class"),R.FilterClass);
		J->WriteValue(TEXT("include_flags"),int32(BaseFilter->GetIncludeFlags())); J->WriteValue(TEXT("exclude_flags"),int32(BaseFilter->GetExcludeFlags())); J->WriteValue(TEXT("max_search_nodes"),int64(BaseFilter->GetMaxSearchNodes()));
		J->WriteValue(TEXT("area_capacity"),Capacity); J->WriteValue(TEXT("registered_area_count"),Areas.Num()); J->WriteValue(TEXT("truncated"),Areas.Num()>256);
		J->WriteArrayStart(TEXT("areas")); for(int32 I=0;I<FMath::Min(Areas.Num(),256);++I)
		{
			const auto& A=Areas[I]; const bool Valid=Costs.IsValidIndex(A.AreaID); J->WriteObjectStart(); J->WriteValue(TEXT("area_id"),A.AreaID); J->WriteValue(TEXT("area_class"),A.AreaClass ? A.AreaClass->GetPathName() : TEXT("")); J->WriteValue(TEXT("area_class_name"),A.AreaClassName); J->WriteValue(TEXT("cost_slot_valid"),Valid);
			if(Valid && FMath::IsFinite(Costs[A.AreaID])) J->WriteValue(TEXT("travel_cost"),Costs[A.AreaID]); else J->WriteNull(TEXT("travel_cost"));
			if(Valid && FMath::IsFinite(Entries[A.AreaID])) J->WriteValue(TEXT("entering_cost"),Entries[A.AreaID]); else J->WriteNull(TEXT("entering_cost")); J->WriteObjectEnd();
		} J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native registered area IDs and cached effective query-filter costs/flags before per-request search-node override; costs alone do not prove traversability; use actual path queries"));
		J->WriteObjectEnd(); J->Close(); return Json;
	}
	auto Filter=BaseFilter->GetCopy(); Filter->SetMaxSearchNodes(R.MaxSearchNodes);
	if(Random)
	{
		FNavLocation Origin; FVector Start=R.Start; bool Projected=false;
		if(R.bProjectEndpoints) { Projected=S->ProjectPointToNavigation(Start,Origin,R.QueryExtent,D,Filter); if(Projected) Start=Origin.Location; }
		const bool CanSample=!R.bProjectEndpoints || Projected;
		FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
		J->WriteValue(TEXT("operation"),Op); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("world_context"),R.WorldContext); J->WriteValue(TEXT("nav_data_path"),D->GetPathName()); Vector(J,TEXT("origin"),Start);
		J->WriteValue(TEXT("origin_projected"),Projected); J->WriteValue(TEXT("queried"),CanSample); J->WriteValue(TEXT("radius"),R.Radius); J->WriteValue(TEXT("sample_count"),R.SampleCount); J->WriteValue(TEXT("max_search_nodes"),R.MaxSearchNodes);
		int32 Successes=0; J->WriteArrayStart(TEXT("samples"));
		for(int32 I=0;I<R.SampleCount;++I)
		{
			FNavLocation Point; const bool Success=CanSample && (Op==TEXT("random_reachable") ? S->GetRandomReachablePointInRadius(Start,R.Radius,Point,D,Filter) : S->GetRandomPointInNavigableRadius(Start,R.Radius,Point,D,Filter));
			J->WriteObjectStart(); J->WriteValue(TEXT("index"),I); J->WriteValue(TEXT("success"),Success); if(Success) { ++Successes; Vector(J,TEXT("location"),Point.Location); } J->WriteObjectEnd();
		}
		J->WriteArrayEnd(); J->WriteValue(TEXT("successful_samples"),Successes);
		J->WriteValue(TEXT("scope"),TEXT("Native random navigation samples with copied filter/node bound; not deterministic or unique; navigable samples need not be connected to origin; native radius follows navigation query geometry, not an asserted 3D Euclidean bound"));
		J->WriteObjectEnd(); J->Close(); return Json;
	}
	FNavLocation ProjectedStart,ProjectedEnd; bool StartOk=false,EndOk=false; FVector Start=R.Start,End=R.End;
	if(Op==TEXT("project") || R.bProjectEndpoints)
	{
		StartOk=S->ProjectPointToNavigation(Start,ProjectedStart,R.QueryExtent,D,Filter); if(StartOk) Start=ProjectedStart.Location;
		if(Op==TEXT("path")) { EndOk=S->ProjectPointToNavigation(End,ProjectedEnd,R.QueryExtent,D,Filter); if(EndOk) End=ProjectedEnd.Location; }
	}
	FPathFindingResult Result(ENavigationQueryResult::Invalid);
	const bool CanQuery=Op==TEXT("path") && (!R.bProjectEndpoints || (StartOk && EndOk));
	if(CanQuery) { FPathFindingQuery Query(W,*D,Start,End,Filter,nullptr,R.CostLimit); Query.SetAllowPartialPaths(R.bAllowPartial); Result=S->FindPathSync(Query); }
	const bool HasPath=Result.Path.IsValid(); const bool Partial=HasPath && Result.Path->IsPartial();
	const bool MeshPath=HasPath && Result.Path->CastPath<FNavMeshPath>()!=nullptr;
	FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("operation"),Op); J->WriteValue(TEXT("nav_data_path"),D->GetPathName()); J->WriteValue(TEXT("start_projected"),StartOk); J->WriteValue(TEXT("end_projected"),EndOk); Vector(J,TEXT("start"),Start); Vector(J,TEXT("end"),End);
	J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("world_context"),R.WorldContext);
	J->WriteValue(TEXT("world_package_path"),W->GetOutermost()->GetName());
	J->WriteValue(TEXT("queried"),CanQuery); J->WriteValue(TEXT("success"),Op==TEXT("project") ? StartOk : Result.IsSuccessful()); J->WriteValue(TEXT("result"),int32(Result.Result)); J->WriteValue(TEXT("partial"),Partial); J->WriteValue(TEXT("max_search_nodes"),R.MaxSearchNodes);
	J->WriteValue(TEXT("path_length"),HasPath ? Result.Path->GetLength() : 0.); J->WriteValue(TEXT("path_cost"),HasPath ? Result.Path->GetCost() : 0.);
	J->WriteValue(TEXT("search_limit_reached"),HasPath && Result.Path->DidSearchReachedLimit());
	const int32 Count=HasPath ? Result.Path->GetPathPoints().Num() : 0; J->WriteValue(TEXT("point_count"),Count); J->WriteValue(TEXT("truncated"),Count>R.MaxPoints);
	J->WriteValue(TEXT("mesh_path_flags"),MeshPath);
	J->WriteArrayStart(TEXT("points")); if(HasPath) for(int32 I=0;I<FMath::Min(Count,R.MaxPoints);++I) { const auto& P=Result.Path->GetPathPoints()[I]; J->WriteObjectStart(); Vector(J,TEXT("location"),P.Location); J->WriteValue(TEXT("flags"),int64(P.Flags)); J->WriteValue(TEXT("off_mesh_connection"),MeshPath && FNavMeshNodeFlags(P.Flags).IsNavLink()); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}
