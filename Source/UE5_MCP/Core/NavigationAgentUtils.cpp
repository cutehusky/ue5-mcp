#include "NavigationAgentUtils.h"
#include "NavigationWorldUtils.h"
#include "NavigationSmartObserver.h"
#include "Navigation/NavLinkProxy.h"
#include "NavLinkCustomComponent.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UnrealType.h"
#include "UE5_MCP/API/DTO/NavigationAgentReq.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "NavFilters/NavigationQueryFilter.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "Containers/Ticker.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>

namespace
{
	struct FProbeEvent { uint64 Sequence=0; double Time=0; uint32 Request=0; FString Result; uint16 Flags=0; FString Kind=TEXT("move_completed"),LinkPath; FVector Destination=FVector::ZeroVector; };
	struct FProbe
	{
		FString Id,State=TEXT("active"),PawnPath,ControllerPath,LastSubmission;
		TWeakObjectPtr<UWorld> World; TWeakObjectPtr<ACharacter> Pawn; TWeakObjectPtr<AAIController> Controller;
		TWeakObjectPtr<UPathFollowingComponent> PathFollowing;
		TWeakObjectPtr<ANavLinkProxy> Watched; TStrongObjectPtr<UNavigationSmartObserver> Observer;
		FDelegateHandle Completion; double Started=0,Deadline=0; FVector Position=FVector::ZeroVector;
		TArray<FProbeEvent> Events; uint64 Sequence=0; uint32 LastRequest=0;
	};
	TMap<FString,TSharedPtr<FProbe>> Probes;
	FTSTicker::FDelegateHandle Ticker; FDelegateHandle Cleanup;
	void Id(const FString& Value)
	{
		if(Value.IsEmpty() || Value.Len()>64) throw std::runtime_error("ProbeId requires 1-64 characters");
		for(TCHAR C:Value) if(!FChar::IsAlnum(C) && C!='_' && C!='-') throw std::runtime_error("ProbeId allows letters, digits, underscore and hyphen");
	}
	void Position(const FVector& V) { if(V.ContainsNaN() || V.GetAbsMax()>1.e9) throw std::runtime_error("Positions must be finite and within +/-1e9 units"); }
	FMulticastDelegateProperty* LinkDelegate()
	{
		return FindFProperty<FMulticastDelegateProperty>(ANavLinkProxy::StaticClass(),TEXT("OnSmartLinkReached"));
	}
	void Unwatch(FProbe& P)
	{
		if(auto* O=P.Observer.Get())
		{
			O->Callback=nullptr;
			if(auto* Link=P.Watched.GetEvenIfUnreachable()) if(auto* Property=LinkDelegate())
			{
				FScriptDelegate Delegate; Delegate.BindUFunction(O,GET_FUNCTION_NAME_CHECKED(UNavigationSmartObserver,Reached));
				Property->RemoveDelegate(Delegate,Link,Property->ContainerPtrToValuePtr<void>(Link));
			}
		}
		P.Observer.Reset(); P.Watched.Reset();
	}
	void Close(FProbe& P,const FString& State,bool Destroy=true)
	{
		Unwatch(P);
		if(auto* Pawn=P.Pawn.Get()) P.Position=Pawn->GetActorLocation();
		// A controller may already be pending destruction. The weak component
		// serial still identifies its allocated delegate owner during teardown.
		if(auto* F=P.PathFollowing.GetEvenIfUnreachable()) F->OnRequestFinished.Remove(P.Completion);
		P.PathFollowing.Reset();
		auto* W=P.World.Get();
		if(Destroy && W && !W->bIsTearingDown)
		{
			if(auto* C=P.Controller.Get()) { C->StopMovement(); C->UnPossess(); W->DestroyActor(C); }
			if(auto* Pawn=P.Pawn.Get()) W->DestroyActor(Pawn);
		}
		P.Pawn.Reset(); P.Controller.Reset(); P.State=State;
	}
	bool Tick(float)
	{
		for(auto It=Probes.CreateIterator();It;++It)
		{
			auto& P=*It.Value(); if(!P.World.IsValid()) { Close(P,TEXT("world_destroyed"),false); It.RemoveCurrent(); continue; }
			if(auto* Pawn=P.Pawn.Get()) P.Position=Pawn->GetActorLocation();
			if(P.State==TEXT("active") && (FPlatformTime::Seconds()>=P.Deadline || !P.Pawn.IsValid() || !P.Controller.IsValid())) Close(P,FPlatformTime::Seconds()>=P.Deadline ? TEXT("expired") : TEXT("actor_destroyed"));
		} return true;
	}
	void OnCleanup(UWorld* W,bool,bool)
	{
		for(auto It=Probes.CreateIterator();It;++It) if(It.Value()->World==W) { Close(*It.Value(),TEXT("world_cleanup"),false); It.RemoveCurrent(); }
	}
	void Ensure()
	{
		if(!Ticker.IsValid()) Ticker=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick));
		if(!Cleanup.IsValid()) Cleanup=FWorldDelegates::OnWorldCleanup.AddStatic(&OnCleanup);
	}
	TSharedPtr<FProbe> Find(const FString& Value,UWorld* W)
	{
		Id(Value); auto* Found=Probes.Find(Value); if(!Found || (*Found)->World!=W) throw std::runtime_error("ProbeId does not belong to the selected PIE world"); return *Found;
	}
	void Vector(TSharedRef<TJsonWriter<>> J,const TCHAR* Name,const FVector& V)
	{
		J->WriteObjectStart(Name); J->WriteValue(TEXT("X"),V.X); J->WriteValue(TEXT("Y"),V.Y); J->WriteValue(TEXT("Z"),V.Z); J->WriteObjectEnd();
	}
	FString Json(const FProbe& P,uint64 After,int32 Limit)
	{
		auto* Pawn=P.Pawn.Get(); auto* C=P.Controller.Get(); auto* F=C ? C->GetPathFollowingComponent() : nullptr;
		FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart();
		J->WriteValue(TEXT("probe_id"),P.Id); J->WriteValue(TEXT("state"),P.State); J->WriteValue(TEXT("runtime_only"),true); J->WriteValue(TEXT("pawn_path"),P.PawnPath); J->WriteValue(TEXT("controller_path"),P.ControllerPath); J->WriteValue(TEXT("pawn_alive"),Pawn!=nullptr);
		Vector(J,TEXT("location"),Pawn ? Pawn->GetActorLocation() : P.Position); Vector(J,TEXT("velocity"),Pawn ? Pawn->GetVelocity() : FVector::ZeroVector);
		J->WriteValue(TEXT("path_status"),F ? StaticEnum<EPathFollowingStatus::Type>()->GetNameStringByValue(F->GetStatus()) : TEXT("unavailable"));
		J->WriteValue(TEXT("current_request_id"),F ? int64(F->GetCurrentRequestId().GetID()) : int64(0)); J->WriteValue(TEXT("last_submission"),P.LastSubmission); J->WriteValue(TEXT("last_submitted_request_id"),int64(P.LastRequest));
		J->WriteValue(TEXT("watched_smart_link"),P.Watched.IsValid() ? P.Watched->GetPathName() : FString());
		J->WriteValue(TEXT("using_custom_link"),F && F->GetCurrentCustomLinkOb()!=nullptr); J->WriteValue(TEXT("path_partial"),F && F->GetPath().IsValid() && F->GetPath()->IsPartial());
		J->WriteValue(TEXT("remaining_lifetime_seconds"),FMath::Max(0.,P.Deadline-FPlatformTime::Seconds())); J->WriteValue(TEXT("event_count"),P.Events.Num());
		J->WriteValue(TEXT("oldest_sequence"),P.Events.IsEmpty() ? int64(0) : int64(P.Events[0].Sequence));
		J->WriteArrayStart(TEXT("events")); int32 Count=0; uint64 Cursor=After;
		for(const auto& E:P.Events) if(E.Sequence>After && Count++<Limit) { J->WriteObjectStart(); J->WriteValue(TEXT("sequence"),int64(E.Sequence)); J->WriteValue(TEXT("elapsed_seconds"),E.Time); J->WriteValue(TEXT("request_id"),int64(E.Request)); J->WriteValue(TEXT("result"),E.Result); J->WriteValue(TEXT("flags"),int32(E.Flags)); J->WriteValue(TEXT("kind"),E.Kind); if(E.Kind==TEXT("smart_link_reached")) { J->WriteValue(TEXT("link_path"),E.LinkPath); Vector(J,TEXT("destination"),E.Destination); } J->WriteObjectEnd(); Cursor=E.Sequence; }
		J->WriteArrayEnd(); J->WriteValue(TEXT("next_sequence"),int64(Cursor)); J->WriteValue(TEXT("scope"),TEXT("Owned transient native character/controller in selected PIE; native movement/completion observations; capsule matches default nav-data agent; wall-clock lifetime; no teleportation or editor-asset changes")); J->WriteObjectEnd(); J->Close(); return Result;
	}
}

void NavigationAgentUtils::Shutdown()
{
	if(Ticker.IsValid()) { FTSTicker::RemoveTicker(Ticker); Ticker.Reset(); } if(Cleanup.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(Cleanup); Cleanup.Reset(); }
	for(auto& Pair:Probes) Close(*Pair.Value,TEXT("module_shutdown")); Probes.Reset();
}

FString NavigationAgentUtils::Inspect(const FString& Value,int32 PIEInstance,uint64 After,int32 Limit)
{
	if(Limit<1 || Limit>256) throw std::runtime_error("Limit requires [1,256]"); Tick(0); auto P=Find(Value,NavigationWorldUtils::Resolve(TEXT("pie"),PIEInstance)); return Json(*P,After,Limit);
}

FString NavigationAgentUtils::Control(const FNavigationAgentReq& R)
{
	Id(R.ProbeId); Tick(0); auto* W=NavigationWorldUtils::Resolve(TEXT("pie"),R.PIEInstance); const FString Op=R.Operation.ToLower();
	if(Op==TEXT("create"))
	{
		if(Probes.Contains(R.ProbeId) || Probes.Num()>=128) throw std::runtime_error("ProbeId exists or global retained-probe limit reached; release old probes");
		int32 Count=0; for(const auto& Pair:Probes) if(Pair.Value->World==W) ++Count; if(Count>=16) throw std::runtime_error("At most 16 retained probes per PIE world");
		Position(R.Location); if(!FMath::IsFinite(R.Speed) || R.Speed<10 || R.Speed>1200 || !FMath::IsFinite(R.DurationSeconds) || R.DurationSeconds<.2f || R.DurationSeconds>120) throw std::runtime_error("Speed requires [10,1200] and duration [0.2,120] seconds");
		auto* S=Cast<UNavigationSystemV1>(W->GetNavigationSystem()); auto* D=S ? S->GetDefaultNavDataInstance(FNavigationSystem::DontCreate) : nullptr; FNavLocation Feet;
		if(!D || !S->ProjectPointToNavigation(R.Location,Feet,FVector(100,100,500),D)) throw std::runtime_error("A default navmesh and projectable spawn feet location are required");
		const float Radius=D->GetConfig().AgentRadius,Half=D->GetConfig().AgentHeight*.5f;
		if(!FMath::IsFinite(Radius) || !FMath::IsFinite(Half) || Radius<=0 || Half<Radius || Half>1000) throw std::runtime_error("Default nav-data agent dimensions cannot form the probe capsule");
		if(!R.bDryRun)
		{
			auto P=MakeShared<FProbe>(); P->Id=R.ProbeId; P->World=W; P->Started=FPlatformTime::Seconds(); P->Deadline=P->Started+R.DurationSeconds;
			const FTransform Transform(FRotator::ZeroRotator,Feet.Location+FVector(0,0,Half+2));
			auto* Pawn=W->SpawnActorDeferred<ACharacter>(ACharacter::StaticClass(),Transform,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);
			if(!Pawn) throw std::runtime_error("Native probe character spawn failed");
			Pawn->SetFlags(RF_Transient); Pawn->AutoPossessAI=EAutoPossessAI::Disabled; Pawn->GetCapsuleComponent()->InitCapsuleSize(Radius,Half); Pawn->GetCharacterMovement()->MaxWalkSpeed=R.Speed; Pawn->FinishSpawning(Transform); P->Pawn=Pawn; P->PawnPath=Pawn->GetPathName();
			FActorSpawnParameters Params; Params.ObjectFlags=RF_Transient; auto* C=W->SpawnActor<AAIController>(AAIController::StaticClass(),Params);
			if(!C) { Close(*P,TEXT("create_failed")); throw std::runtime_error("Native probe controller spawn failed"); }
			P->Controller=C; P->ControllerPath=C->GetPathName(); C->Possess(Pawn); auto* F=C->GetPathFollowingComponent();
			if(!F || C->GetPawn()!=Pawn) { Close(*P,TEXT("create_failed")); throw std::runtime_error("Native possession/path following failed"); }
			P->PathFollowing=F;
			P->Completion=F->OnRequestFinished.AddLambda([Weak=TWeakPtr<FProbe>(P)](FAIRequestID Request,const FPathFollowingResult& Result)
			{
				if(auto Probe=Weak.Pin()) { if(Probe->Events.Num()>=256) Probe->Events.RemoveAt(0); Probe->Events.Add({++Probe->Sequence,FPlatformTime::Seconds()-Probe->Started,Request.GetID(),StaticEnum<EPathFollowingResult::Type>()->GetNameStringByValue(Result.Code),Result.Flags}); }
			});
			Ensure(); Probes.Add(R.ProbeId,P);
		}
	}
	else
	{
		auto P=Find(R.ProbeId,W);
		if(Op==TEXT("release")) { if(!R.bDryRun) { Close(*P,TEXT("released")); Probes.Remove(R.ProbeId); } }
		else
		{
			auto* C=P->Controller.Get(); auto* F=C ? C->GetPathFollowingComponent() : nullptr;
			if(P->State!=TEXT("active") || !C || !F) throw std::runtime_error("Probe actors are not active; release the retained record");
			if(Op==TEXT("move"))
			{
				Position(R.Destination); if(!FMath::IsFinite(R.AcceptanceRadius) || R.AcceptanceRadius<0 || R.AcceptanceRadius>2000) throw std::runtime_error("AcceptanceRadius requires [0,2000]");
				UClass* Filter=R.FilterClass.IsEmpty() ? nullptr : LoadObject<UClass>(nullptr,*R.FilterClass);
				if(!R.FilterClass.IsEmpty() && (!Filter || !Filter->IsChildOf(UNavigationQueryFilter::StaticClass()) || Filter->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists))) throw std::runtime_error("FilterClass requires a concrete compatible navigation query filter");
				if(!R.bDryRun) { FAIMoveRequest Move(R.Destination); Move.SetUsePathfinding(true).SetAllowPartialPath(R.bAllowPartial).SetProjectGoalLocation(R.bProjectGoal).SetAcceptanceRadius(R.AcceptanceRadius).SetReachTestIncludesAgentRadius(true).SetReachTestIncludesGoalRadius(false).SetNavigationFilter(Filter); const auto Result=C->MoveTo(Move); P->LastRequest=Result.MoveId.GetID(); P->LastSubmission=Result.Code==EPathFollowingRequestResult::RequestSuccessful ? TEXT("RequestSuccessful") : Result.Code==EPathFollowingRequestResult::AlreadyAtGoal ? TEXT("AlreadyAtGoal") : TEXT("Failed"); }
			}
			else if(Op==TEXT("watch_link") || Op==TEXT("unwatch_link"))
			{
				ANavLinkProxy* Link=nullptr;
				if(Op==TEXT("watch_link"))
				{
					Link=FindObject<ANavLinkProxy>(nullptr,*R.SmartLinkPath);
					if(R.SmartLinkPath.IsEmpty() || !Link || Link->GetWorld()!=W || !Link->bSmartLinkIsRelevant || !Link->GetSmartLinkComp() || !LinkDelegate()) throw std::runtime_error("SmartLinkPath requires a relevant native smart-link proxy in the selected PIE world");
				}
				if(Link!=P->Watched.Get())
				{
					if(P->Watched.IsValid() && F->GetCurrentCustomLinkOb()==P->Watched->GetSmartLinkComp()) throw std::runtime_error("Stop or resume the current smart link before changing its observer");
					if(!R.bDryRun)
					{
						Unwatch(*P);
						if(Link)
						{
							P->Watched=Link; P->Observer.Reset(NewObject<UNavigationSmartObserver>(GetTransientPackage()));
							P->Observer->Callback=[Weak=TWeakPtr<FProbe>(P)](AActor* Actor,const FVector& Destination)
							{
								if(auto Probe=Weak.Pin()) if(Actor==Probe->Pawn.Get() && Probe->Watched.IsValid())
								{
									if(Probe->Events.Num()>=256) Probe->Events.RemoveAt(0);
									FProbeEvent E; E.Sequence=++Probe->Sequence; E.Time=FPlatformTime::Seconds()-Probe->Started; E.Request=Probe->PathFollowing.IsValid() ? Probe->PathFollowing->GetCurrentRequestId().GetID() : 0; E.Kind=TEXT("smart_link_reached"); E.LinkPath=Probe->Watched->GetPathName(); E.Destination=Destination; Probe->Events.Add(MoveTemp(E));
								}
							};
							FScriptDelegate Delegate; Delegate.BindUFunction(P->Observer.Get(),GET_FUNCTION_NAME_CHECKED(UNavigationSmartObserver,Reached));
							auto* Property=LinkDelegate(); Property->AddDelegate(Delegate,Link,Property->ContainerPtrToValuePtr<void>(Link));
						}
					}
				}
			}
			else if(Op==TEXT("resume_link"))
			{
				auto* Link=P->Watched.Get(); if(!Link || !P->Pawn.IsValid() || F->GetCurrentCustomLinkOb()!=Link->GetSmartLinkComp()) throw std::runtime_error("The owned pawn must be using its watched smart link");
				if(!R.bDryRun) Link->ResumePathFollowing(P->Pawn.Get());
			}
			else if(Op==TEXT("stop")) { if(!R.bDryRun) C->StopMovement(); }
			else if(Op==TEXT("pause")) { if(F->GetStatus()!=EPathFollowingStatus::Moving) throw std::runtime_error("A moving request is required to pause"); if(!R.bDryRun) F->PauseMove(); }
			else if(Op==TEXT("resume")) { if(F->GetStatus()!=EPathFollowingStatus::Paused) throw std::runtime_error("A paused request is required to resume"); if(!R.bDryRun) F->ResumeMove(); }
			else throw std::runtime_error("Probe operation must be create, move, stop, pause, resume, watch_link, unwatch_link, resume_link or release");
		}
	}
	FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("probe_id"),R.ProbeId); J->WriteValue(TEXT("operation"),Op); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("submitted"),!R.bDryRun); J->WriteObjectEnd(); J->Close(); return Json;
}

