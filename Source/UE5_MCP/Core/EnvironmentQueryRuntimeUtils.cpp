#include "EnvironmentQueryRuntimeUtils.h"
#include "EnvironmentQueryUtils.h"
#include "NavigationWorldUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryRuntimeReq.h"
#include "EnvironmentQuery/EnvQuery.h"
#include "EnvironmentQuery/EnvQueryManager.h"
#include "EnvironmentQuery/Items/EnvQueryItemType_VectorBase.h"
#include "EnvironmentQuery/Items/EnvQueryItemType_ActorBase.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Containers/Ticker.h"
#include "Misc/DefaultValueHelper.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>
namespace
{
 struct FItem { float Score=0; FVector Location=FVector::ZeroVector; FString ActorPath; bool HasLocation=false; };
 struct FRecord
 {
  FString Id,State=TEXT("running"),Asset,OwnerPath,Mode,ItemType; TWeakObjectPtr<UWorld> World; TWeakObjectPtr<AActor> Owner; TWeakObjectPtr<UEnvQueryManager> Manager; TWeakPtr<FEnvQueryInstance> Instance;
  int32 NativeId=INDEX_NONE,NativeStatus=EEnvQueryStatus::Processing,Option=INDEX_NONE,Total=0,NativeTotal=0,Limit=128; double Started=0,Deadline=0,Finished=0; TArray<FItem> Items;
 };
 TMap<FString,TSharedPtr<FRecord>> Records; FTSTicker::FDelegateHandle Ticker; FDelegateHandle Cleanup;
 void World(UWorld* W) { if(!IsInGameThread() || !IsValid(W) || W->bIsTearingDown || (W->WorldType!=EWorldType::PIE && W->WorldType!=EWorldType::Game)) throw std::runtime_error("EQS runtime requires a live game/PIE world on the game thread"); }
 void Id(const FString& S) { if(S.IsEmpty() || S.Len()>64) throw std::runtime_error("RequestId requires 1-64 characters"); for(TCHAR C:S) if(!FChar::IsAlnum(C) && C!='_' && C!='-') throw std::runtime_error("RequestId allows letters, digits, underscore and hyphen"); }
 FString Status(int32 Value) { return StaticEnum<EEnvQueryStatus::Type>()->GetNameStringByValue(Value); }
 void Complete(TWeakPtr<FRecord> Weak,TSharedPtr<FEnvQueryResult> Result)
 {
  auto P=Weak.Pin(); if(!P || !Result.IsValid()) return;
  P->NativeStatus=Result->GetRawStatus(); P->Option=Result->OptionIndex; P->NativeTotal=Result->Items.Num(); P->Total=Result->IsSuccessful() ? (P->Mode==TEXT("all_matching") ? P->NativeTotal : FMath::Min(1,P->NativeTotal)) : 0; P->ItemType=Result->ItemType ? Result->ItemType->GetPathName() : FString(); P->Finished=FPlatformTime::Seconds();
  if(P->State==TEXT("running")) P->State=Result->IsSuccessful() ? TEXT("succeeded") : Result->IsAborted() ? TEXT("aborted") : Result->GetRawStatus()==EEnvQueryStatus::OwnerLost ? TEXT("owner_lost") : Result->GetRawStatus()==EEnvQueryStatus::MissingParam ? TEXT("missing_parameter") : TEXT("failed");
  const bool Locations=Result->ItemType && Result->ItemType->IsChildOf(UEnvQueryItemType_VectorBase::StaticClass()); const bool Actors=Result->ItemType && Result->ItemType->IsChildOf(UEnvQueryItemType_ActorBase::StaticClass());
  if(Result->IsSuccessful()) for(int32 I=0;I<FMath::Min(P->Limit,P->Total);++I) { FItem Item; Item.Score=Result->GetItemScore(I); if(Locations) { Item.Location=Result->GetItemAsLocation(I); Item.HasLocation=!Item.Location.ContainsNaN(); } if(Actors) { auto* A=Result->GetItemAsActor(I); if(IsValid(A) && !A->IsActorBeingDestroyed()) Item.ActorPath=A->GetPathName(); else Item.HasLocation=false; } P->Items.Add(MoveTemp(Item)); }
 }
 void Stop(FRecord& P,const FString& State)
 {
  if(P.State==TEXT("running")) { P.State=State; P.Finished=FPlatformTime::Seconds(); if(auto* M=P.Manager.Get()) M->AbortQuery(P.NativeId); }
  if(auto Instance=P.Instance.Pin()) Instance->FinishDelegate.Unbind();
 }
 bool Tick(float)
 {
  const double Now=FPlatformTime::Seconds();
  for(auto It=Records.CreateIterator();It;++It) { auto& P=*It.Value(); if(!P.World.IsValid()) { Stop(P,TEXT("world_destroyed")); It.RemoveCurrent(); continue; } if(P.State==TEXT("running")) { if(!P.Owner.IsValid() || P.Owner->IsActorBeingDestroyed()) Stop(P,TEXT("owner_lost")); else if(Now>=P.Deadline) Stop(P,TEXT("expired")); } if(P.Finished>0 && Now-P.Finished>120) { Stop(P,P.State); It.RemoveCurrent(); } } return true;
 }
 void OnCleanup(UWorld* W,bool,bool) { for(auto It=Records.CreateIterator();It;++It) if(It.Value()->World==W) { Stop(*It.Value(),TEXT("world_cleanup")); It.RemoveCurrent(); } }
 void Ensure() { if(!Ticker.IsValid()) Ticker=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick)); if(!Cleanup.IsValid()) Cleanup=FWorldDelegates::OnWorldCleanup.AddStatic(&OnCleanup); }
 TSharedPtr<FRecord> Find(UWorld* W,const FString& Key) { Id(Key); auto* P=Records.Find(Key); if(!P || (*P)->World!=W) throw std::runtime_error("RequestId does not belong to the selected world"); return *P; }
 void JsonRecord(TSharedRef<TJsonWriter<>> J,const FRecord& P)
 {
  J->WriteObjectStart(); J->WriteValue(TEXT("request_id"),P.Id); J->WriteValue(TEXT("native_query_id"),P.NativeId); J->WriteValue(TEXT("state"),P.State); J->WriteValue(TEXT("native_status"),Status(P.NativeStatus)); J->WriteValue(TEXT("asset_path"),P.Asset); J->WriteValue(TEXT("owner_path"),P.OwnerPath); J->WriteValue(TEXT("owner_alive"),P.Owner.IsValid()); J->WriteValue(TEXT("run_mode"),P.Mode); J->WriteValue(TEXT("option_index"),P.Option); J->WriteValue(TEXT("item_type"),P.ItemType); J->WriteValue(TEXT("total_items"),P.Total); J->WriteValue(TEXT("native_item_count"),P.NativeTotal); J->WriteValue(TEXT("returned_items"),P.Items.Num()); J->WriteValue(TEXT("truncated"),P.Total>P.Items.Num()); J->WriteValue(TEXT("elapsed_seconds"),(P.Finished>0 ? P.Finished : FPlatformTime::Seconds())-P.Started);
  J->WriteArrayStart(TEXT("items")); for(const auto& I:P.Items) { J->WriteObjectStart(); if(FMath::IsFinite(I.Score)) J->WriteValue(TEXT("score"),I.Score); else J->WriteNull(TEXT("score")); if(I.HasLocation) { J->WriteObjectStart(TEXT("location")); J->WriteValue(TEXT("X"),I.Location.X); J->WriteValue(TEXT("Y"),I.Location.Y); J->WriteValue(TEXT("Z"),I.Location.Z); J->WriteObjectEnd(); } if(!I.ActorPath.IsEmpty()) J->WriteValue(TEXT("actor_path"),I.ActorPath); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 FString Json(const FRecord& P,bool Dry=false,bool Change=false) { FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("would_change"),Change); J->WriteIdentifierPrefix(TEXT("request")); JsonRecord(J,P); J->WriteValue(TEXT("scope"),TEXT("Owned native asynchronous EQS request in the selected world. Scores/order are engine results; single/random modes expose the native selected first item, while native_item_count may include debugger candidates. Only retained output is capped. Timeout/abort are serviced between native manager ticks and cannot preempt a synchronous generator. No asset edits or undo transaction.")); J->WriteObjectEnd(); J->Close(); return S; }
 EEnvQueryRunMode::Type Mode(const FString& S) { if(S==TEXT("all_matching")) return EEnvQueryRunMode::AllMatching; if(S==TEXT("single")) return EEnvQueryRunMode::SingleResult; if(S==TEXT("random_best_5")) return EEnvQueryRunMode::RandomBest5Pct; if(S==TEXT("random_best_25")) return EEnvQueryRunMode::RandomBest25Pct; throw std::runtime_error("RunMode requires all_matching, single, random_best_5 or random_best_25"); }
 FEnvQueryRequest Request(UEnvQuery* Q,AActor* Owner,const FEnvironmentQueryRuntimeReq& R)
 {
  TArray<FAIDynamicParam> Defaults; Q->CollectQueryParams(*Owner,Defaults); TMap<FName,EAIParamType> Types; FEnvQueryRequest Result(Q,Owner);
  for(const auto& P:Defaults) { Types.Add(P.ParamName,P.ParamType); if(P.ParamType==EAIParamType::Float) Result.SetFloatParam(P.ParamName,P.Value); else if(P.ParamType==EAIParamType::Int) { int32 Value; FMemory::Memcpy(&Value,&P.Value,sizeof(Value)); Result.SetIntParam(P.ParamName,Value); } else if(P.ParamType==EAIParamType::Bool) Result.SetBoolParam(P.ParamName,P.Value>0); }
  if(R.Parameters.Num()>64) throw std::runtime_error("At most 64 runtime query parameters"); TSet<FName> Seen;
  for(const auto& P:R.Parameters)
  {
   const FName Name(*P.Name); const FString Type=P.Type.ToLower(),Text=P.Value.TrimStartAndEnd(); if(Name.IsNone() || P.Name.Len()>128 || Text.IsEmpty() || Text.Len()>64 || Seen.Contains(Name) || !Types.Contains(Name)) throw std::runtime_error("Parameters require unique declared query names and bounded scalar values"); Seen.Add(Name);
   if(Type==TEXT("float") && Types[Name]==EAIParamType::Float) { double Value=0; if(!FDefaultValueHelper::ParseDouble(Text,Value) || !FMath::IsFinite(Value) || FMath::Abs(Value)>1.e6) throw std::runtime_error("Float parameter must be finite and within +/-1e6"); Result.SetFloatParam(Name,float(Value)); }
   else if(Type==TEXT("int") && Types[Name]==EAIParamType::Int) { int32 Start=Text[0]=='-' || Text[0]=='+' ? 1 : 0; if(Start==Text.Len() || Text.Len()>10) throw std::runtime_error("Invalid integer parameter"); for(int32 I=Start;I<Text.Len();++I) if(!FChar::IsDigit(Text[I])) throw std::runtime_error("Integer parameter requires whole decimal digits"); const int64 Value=FCString::Atoi64(*Text); if(FMath::Abs(Value)>1000000) throw std::runtime_error("Integer parameter exceeds +/-1e6"); Result.SetIntParam(Name,int32(Value)); }
   else if(Type==TEXT("bool") && Types[Name]==EAIParamType::Bool) { if(!Text.Equals(TEXT("true"),ESearchCase::IgnoreCase) && !Text.Equals(TEXT("false"),ESearchCase::IgnoreCase)) throw std::runtime_error("Boolean parameter requires true or false"); Result.SetBoolParam(Name,Text.Equals(TEXT("true"),ESearchCase::IgnoreCase)); }
   else throw std::runtime_error("Parameter type does not match the native Float/Int/Bool declaration");
  } return Result;
 }
}
void EnvironmentQueryRuntimeUtils::Shutdown() { if(Ticker.IsValid()) { FTSTicker::RemoveTicker(Ticker); Ticker.Reset(); } if(Cleanup.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(Cleanup); Cleanup.Reset(); } for(auto& P:Records) Stop(*P.Value,TEXT("module_shutdown")); Records.Reset(); }
FString EnvironmentQueryRuntimeUtils::ControlInWorld(UWorld* W,const FEnvironmentQueryRuntimeReq& R)
{
 World(W); Tick(0); const FString Op=R.Operation.ToLower();
 if(Op==TEXT("cancel") || Op==TEXT("forget")) { auto P=Find(W,R.RequestId); const bool Change=Op==TEXT("forget") || P->State==TEXT("running"); if(!R.bDryRun) { Stop(*P,Op==TEXT("cancel") ? TEXT("cancelled") : TEXT("forgotten")); if(Op==TEXT("forget")) Records.Remove(P->Id); } return Json(*P,R.bDryRun,Change); }
 if(Op!=TEXT("run")) throw std::runtime_error("Operation requires run, cancel or forget");
 const FString Key=R.RequestId.IsEmpty() ? FGuid::NewGuid().ToString(EGuidFormats::Digits) : R.RequestId; Id(Key); if(Records.Contains(Key)) throw std::runtime_error("RequestId is already retained; forget it before reuse");
 if(Records.Num()>=64) throw std::runtime_error("At most 64 retained EQS requests; forget completed requests"); int32 Active=0; for(const auto& P:Records) if(P.Value->State==TEXT("running")) ++Active; if(Active>=16) throw std::runtime_error("At most 16 owned running EQS requests");
 if(R.MaxItems<1 || R.MaxItems>512 || !FMath::IsFinite(R.TimeoutSeconds) || R.TimeoutSeconds<0.1 || R.TimeoutSeconds>60) throw std::runtime_error("MaxItems requires 1-512; timeout requires 0.1-60 seconds");
 if(R.OwnerPath.IsEmpty() || R.OwnerPath.Len()>2048) throw std::runtime_error("An explicit PIE owner actor path is required"); auto* Owner=FindObject<AActor>(nullptr,*R.OwnerPath);
 if(!IsValid(Owner) || Owner->IsTemplate() || Owner->GetWorld()!=W || Owner->IsActorBeingDestroyed() || !Owner->HasAuthority()) throw std::runtime_error("OwnerPath requires an authoritative live actor in the selected world");
 auto* Q=EnvironmentQueryUtils::ValidateForRuntime(R.AssetPath); const auto RunMode=Mode(R.RunMode.ToLower()); auto Query=Request(Q,Owner,R); auto* Manager=UEnvQueryManager::GetCurrent(W); if(!Manager) throw std::runtime_error("Selected world has no native EQS manager");
 auto P=MakeShared<FRecord>(); P->Id=Key; P->World=W; P->Owner=Owner; P->OwnerPath=Owner->GetPathName(); P->Asset=Q->GetPathName(); P->Mode=R.RunMode.ToLower(); P->Limit=R.MaxItems; P->Started=FPlatformTime::Seconds(); P->Deadline=P->Started+R.TimeoutSeconds; P->Manager=Manager;
 if(R.bDryRun) { P->State=TEXT("preview"); return Json(*P,true,true); }
 auto Instance=Manager->PrepareQueryInstance(Query,RunMode); if(!Instance.IsValid()) throw std::runtime_error("Native EQS query preparation failed"); P->Instance=Instance; TWeakPtr<FRecord> Weak=P;
 Ensure(); Records.Add(Key,P); P->NativeId=Manager->RunQuery(Instance,FQueryFinishedSignature::CreateLambda([Weak](TSharedPtr<FEnvQueryResult> Result) { Complete(Weak,Result); })); if(P->NativeId==INDEX_NONE) { Records.Remove(Key); Instance->FinishDelegate.Unbind(); throw std::runtime_error("Native EQS request submission failed"); } return Json(*P,false,true);
}
FString EnvironmentQueryRuntimeUtils::Control(const FEnvironmentQueryRuntimeReq& R) { return ControlInWorld(NavigationWorldUtils::Resolve(TEXT("pie"),R.PIEInstance),R); }
FString EnvironmentQueryRuntimeUtils::InspectInWorld(UWorld* W,const FString& Key)
{
 World(W); Tick(0); if(!Key.IsEmpty()) return Json(*Find(W,Key)); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteArrayStart(TEXT("requests")); for(const auto& Pair:Records) if(Pair.Value->World==W) JsonRecord(J,*Pair.Value); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
FString EnvironmentQueryRuntimeUtils::Inspect(const FString& Key,int32 PIEInstance) { return InspectInWorld(NavigationWorldUtils::Resolve(TEXT("pie"),PIEInstance),Key); }
FString EnvironmentQueryRuntimeUtils::Owners(int32 PIEInstance,const FString& Search,int32 Limit)
{
 auto* W=NavigationWorldUtils::Resolve(TEXT("pie"),PIEInstance); World(W); if(Limit<1 || Limit>256 || Search.Len()>128) throw std::runtime_error("Owner listing requires limit 1-256 and search <=128 characters"); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteArrayStart(TEXT("owners")); int32 Count=0;
 for(TActorIterator<AActor> It(W);It;++It) if(IsValid(*It) && !It->IsActorBeingDestroyed() && (Search.IsEmpty() || It->GetName().Contains(Search))) { if(Count++>=Limit) break; J->WriteObjectStart(); J->WriteValue(TEXT("path"),It->GetPathName()); J->WriteValue(TEXT("class"),It->GetClass()->GetPathName()); J->WriteValue(TEXT("authority"),It->HasAuthority()); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("truncated"),Count>Limit); J->WriteObjectEnd(); J->Close(); return S;
}
