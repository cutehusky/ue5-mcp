#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/EnvironmentQueryUtils.h"
#include "UE5_MCP/Core/EnvironmentQueryRuntimeUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryReq.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryRuntimeReq.h"
#include "EnvironmentQuery/EnvQuery.h"
#include "EnvironmentQuery/EnvQueryOption.h"
#include "EnvironmentQuery/EnvQueryManager.h"
#include "EnvironmentQuery/Generators/EnvQueryGenerator_OnCircle.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "HAL/PlatformProcess.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnvironmentQueryRuntimeTest,"UE5MCP.EnvironmentQuery.Runtime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEnvironmentQueryRuntimeTest::RunTest(const FString&)
{
 TArray<UEnvQuery*> Assets; TArray<UPackage*> Packages;
 ON_SCOPE_EXIT { for(auto* Q:Assets) { FAssetRegistryModule::AssetDeleted(Q); Q->ClearFlags(RF_Public|RF_Standalone); Q->MarkAsGarbage(); } for(auto* P:Packages) P->SetDirtyFlag(false); };
 auto New=[&]() { const FString Name=TEXT("EQS_Runtime_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto* P=CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)); Packages.Add(P); auto* Q=NewObject<UEnvQuery>(P,*Name,RF_Public|RF_Standalone|RF_Transactional); Assets.Add(Q); FAssetRegistryModule::AssetCreated(Q); return Q; };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid runtime EQS JSON"); return J; };
 auto Edit=[&](UEnvQuery* Q,FEnvironmentQueryReq R,const TCHAR* Op) { R.AssetPath=Q->GetPathName(); return Parse(EnvironmentQueryUtils::Control(R,Op)); };
 try
 {
  auto* Q=New(); FEnvironmentQueryReq E; Edit(Q,E,TEXT("initialize")); E.ClassPath=TEXT("/Script/AIModule.EnvQueryGenerator_CurrentLocation"); auto First=Edit(Q,E,TEXT("create_option"))->GetStringField(TEXT("node_guid")); E.X=300; Edit(Q,E,TEXT("create_option"));
  E={}; E.ParentGuid=First; E.ClassPath=TEXT("/Script/AIModule.EnvQueryTest_Distance"); E.Properties={{TEXT("TestPurpose"),TEXT("Filter")},{TEXT("FilterType"),TEXT("Minimum")}}; E.NamedParameters.Add(TEXT("FloatValueMin"),TEXT("MinimumDistance")); E.ProviderValues.Add(TEXT("FloatValueMin"),TEXT("0")); Edit(Q,E,TEXT("create_test"));
  E={}; E.ParentGuid=First; E.ClassPath=TEXT("/Script/AIModule.EnvQueryTest_Trace"); E.Properties.Add(TEXT("TestPurpose"),TEXT("Filter")); E.ProviderValues.Add(TEXT("BoolValue"),TEXT("False")); E.NamedParameters.Add(TEXT("BoolValue"),TEXT("RequireHit")); Edit(Q,E,TEXT("create_test"));
  auto* Circle=New(); E={}; Edit(Circle,E,TEXT("initialize")); E.ClassPath=TEXT("/Script/AIModule.EnvQueryGenerator_OnCircle"); E.Properties.Add(TEXT("PointOnCircleSpacingMethod"),TEXT("ByNumberOfPoints")); E.ProviderValues.Add(TEXT("NumberOfPoints"),TEXT("3")); E.NamedParameters.Add(TEXT("NumberOfPoints"),TEXT("PointCount")); Edit(Circle,E,TEXT("create_option")); CastChecked<UEnvQueryGenerator_OnCircle>(Circle->GetOptions()[0]->Generator)->TraceData.TraceMode=EEnvQueryTrace::None;
  const FString Before=EnvironmentQueryUtils::Inspect(Q->GetPathName()); const FString CircleBefore=EnvironmentQueryUtils::Inspect(Circle->GetPathName());
  auto NewWorld=[]() { UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(true).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); W->CreateAISystem(); return W; };
  UWorld* W=NewWorld(); ON_SCOPE_EXIT { if(W) W->DestroyWorld(false); };
  auto Actor=[](UWorld* World) { auto* A=World->SpawnActor<AActor>(); auto* Root=NewObject<USceneComponent>(A); A->SetRootComponent(Root); Root->RegisterComponent(); A->SetActorLocation(FVector(100,200,300)); return A; };
  auto* Owner=Actor(W); auto* Manager=UEnvQueryManager::GetCurrent(W);
  auto Call=[&](FEnvironmentQueryRuntimeReq R) { return Parse(EnvironmentQueryRuntimeUtils::ControlInWorld(W,R)); };
  auto Read=[&](const FString& Id) { return Parse(EnvironmentQueryRuntimeUtils::InspectInWorld(W,Id))->GetObjectField(TEXT("request")); };
  auto Run=[&](FEnvironmentQueryRuntimeReq R) { auto J=Call(R)->GetObjectField(TEXT("request")); auto Id=J->GetStringField(TEXT("request_id")); for(int32 I=0;I<128 && Read(Id)->GetStringField(TEXT("state"))==TEXT("running");++I) Manager->Tick(.01f); auto Done=Read(Id); FEnvironmentQueryRuntimeReq Forget; Forget.Operation=TEXT("forget"); Forget.RequestId=Id; Call(Forget); return Done; };
  FEnvironmentQueryRuntimeReq R; R.AssetPath=Q->GetPathName(); R.OwnerPath=Owner->GetPathName(); R.bDryRun=true; auto Preview=Call(R)->GetObjectField(TEXT("request")); bool Rejected=false; try { Read(Preview->GetStringField(TEXT("request_id"))); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Dry-run does not retain a request"),Rejected); R.bDryRun=false;
  auto Result=Run(R); TestEqual(TEXT("Asynchronous query succeeds"),Result->GetStringField(TEXT("state")),FString(TEXT("succeeded"))); TestEqual(TEXT("Omitted float/bool defaults select primary"),int32(Result->GetNumberField(TEXT("option_index"))),0);
  auto Location=Result->GetArrayField(TEXT("items"))[0]->AsObject()->GetObjectField(TEXT("location")); TestEqual(TEXT("Native result owner X"),Location->GetNumberField(TEXT("X")),100.0);
  R.Parameters={{TEXT("MinimumDistance"),TEXT("float"),TEXT("1")}}; Result=Run(R); TestEqual(TEXT("Float override changes native fallback"),int32(Result->GetNumberField(TEXT("option_index"))),1);
  R.Parameters={{TEXT("RequireHit"),TEXT("bool"),TEXT("true")}}; Result=Run(R); TestEqual(TEXT("Boolean override changes native trace filter"),int32(Result->GetNumberField(TEXT("option_index"))),1);
  R.Parameters.Reset(); R.AssetPath=Circle->GetPathName(); R.MaxItems=2; Result=Run(R); TestEqual(TEXT("Native integer default decoded exactly"),int32(Result->GetNumberField(TEXT("total_items"))),3); TestTrue(TEXT("Retained result cap reports truncation"),Result->GetBoolField(TEXT("truncated"))); TestEqual(TEXT("Retained result cap"),Result->GetArrayField(TEXT("items")).Num(),2);
  R.Parameters={{TEXT("PointCount"),TEXT("int"),TEXT("5")}}; Result=Run(R); TestEqual(TEXT("Integer override encoded exactly"),int32(Result->GetNumberField(TEXT("total_items"))),5);
  R.RunMode=TEXT("single"); Result=Run(R); TestEqual(TEXT("Native single-result mode"),int32(Result->GetNumberField(TEXT("total_items"))),1); R.RunMode=TEXT("all_matching");
  auto Reject=[&](const TArray<FEnvironmentQueryParameter>& Params) { R.Parameters=Params; bool Bad=false; try { Call(R); } catch(const std::exception&) { Bad=true; } TestTrue(TEXT("Invalid runtime parameter rejects"),Bad); };
  Reject({{TEXT("PointCount"),TEXT("float"),TEXT("5")}}); Reject({{TEXT("PointCount"),TEXT("int"),TEXT("2.5")}}); Reject({{TEXT("Missing"),TEXT("int"),TEXT("2")}}); Reject({{TEXT("PointCount"),TEXT("int"),TEXT("2")},{TEXT("pointcount"),TEXT("int"),TEXT("3")}});
  R.Parameters.Reset(); auto Pending=Call(R)->GetObjectField(TEXT("request"))->GetStringField(TEXT("request_id")); FEnvironmentQueryRuntimeReq C; C.RequestId=Pending; C.Operation=TEXT("cancel"); C.bDryRun=true; Call(C); TestEqual(TEXT("Cancel dry-run preserves running request"),Read(Pending)->GetStringField(TEXT("state")),FString(TEXT("running"))); C.bDryRun=false; Call(C); TestEqual(TEXT("Native cancellation observed"),Read(Pending)->GetStringField(TEXT("state")),FString(TEXT("cancelled"))); TestFalse(TEXT("Repeated cancel is a no-op"),Call(C)->GetBoolField(TEXT("would_change"))); C.Operation=TEXT("forget"); Call(C);
  R.TimeoutSeconds=.1; Pending=Call(R)->GetObjectField(TEXT("request"))->GetStringField(TEXT("request_id")); FPlatformProcess::Sleep(.12f); TestEqual(TEXT("Wall-clock expiry aborts pending native query"),Read(Pending)->GetStringField(TEXT("state")),FString(TEXT("expired"))); C.RequestId=Pending; Call(C); R.TimeoutSeconds=10;
  auto* Lost=Actor(W); R.OwnerPath=Lost->GetPathName(); Pending=Call(R)->GetObjectField(TEXT("request"))->GetStringField(TEXT("request_id")); W->DestroyActor(Lost); TestEqual(TEXT("Owner loss aborts owned query"),Read(Pending)->GetStringField(TEXT("state")),FString(TEXT("owner_lost"))); C.RequestId=Pending; Call(C);
  R.OwnerPath=Owner->GetPathName(); R.RequestId=FGuid::NewGuid().ToString(EGuidFormats::Digits); Call(R); W->DestroyWorld(false); W=nullptr; W=NewWorld(); Manager=UEnvQueryManager::GetCurrent(W); Owner=Actor(W); R.OwnerPath=Owner->GetPathName(); Call(R); C.RequestId=R.RequestId; Call(C); // same ID proves world cleanup removed the old record
  TestEqual(TEXT("Runtime requests preserve source graph/settings"),EnvironmentQueryUtils::Inspect(Q->GetPathName()),Before); TestEqual(TEXT("Runtime requests preserve circle source"),EnvironmentQueryUtils::Inspect(Circle->GetPathName()),CircleBefore); return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
