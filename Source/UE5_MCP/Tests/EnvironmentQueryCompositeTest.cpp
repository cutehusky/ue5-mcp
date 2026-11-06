#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/EnvironmentQueryUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryReq.h"
#include "EnvironmentQuery/EnvQuery.h"
#include "EnvironmentQuery/EnvQueryOption.h"
#include "EnvironmentQuery/EnvQueryTest.h"
#include "EnvironmentQuery/EnvQueryManager.h"
#include "EnvironmentQuery/Generators/EnvQueryGenerator_Composite.h"
#include "EnvironmentQuery/Generators/EnvQueryGenerator_CurrentLocation.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Editor.h"
#include "UObject/Package.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include <stdexcept>
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnvironmentQueryCompositeTest,"UE5MCP.EnvironmentQuery.Composite",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEnvironmentQueryCompositeTest::RunTest(const FString&)
{
 const FString Name=TEXT("EQS_Composite_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto* Package=CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)); auto* Q=NewObject<UEnvQuery>(Package,*Name,RF_Public|RF_Standalone|RF_Transactional); FAssetRegistryModule::AssetCreated(Q);
 ON_SCOPE_EXIT { FAssetRegistryModule::AssetDeleted(Q); Q->ClearFlags(RF_Public|RF_Standalone); Q->MarkAsGarbage(); Package->SetDirtyFlag(false); };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid composite EQS JSON"); return J; };
 auto Control=[&](FEnvironmentQueryReq R,const TCHAR* Op) { R.AssetPath=Q->GetPathName(); return Parse(EnvironmentQueryUtils::Control(R,Op)); };
 auto Row=[](const TCHAR* Class,int32 Children=0) { FEnvironmentQueryGeneratorRow R; R.ClassPath=FString(TEXT("/Script/AIModule.EnvQueryGenerator_"))+Class; R.Children=Children; return R; };
 try
 {
  FEnvironmentQueryReq R; Control(R,TEXT("initialize"));
  R.bSetGeneratorTree=true; R.GeneratorTree={Row(TEXT("Composite"),2),Row(TEXT("CurrentLocation")),Row(TEXT("Composite"),1),Row(TEXT("CurrentLocation"))}; const auto OriginalRows=R.GeneratorTree;
  const FString Option=Control(R,TEXT("create_option"))->GetStringField(TEXT("node_guid")); auto* O=Q->GetOptions()[0]; auto* Root=CastChecked<UEnvQueryGenerator_Composite>(O->Generator); TestEqual(TEXT("Two native child generators"),Root->Generators.Num(),2); TestEqual(TEXT("Native nested child ownership"),Root->Generators[0]->GetOuter(),static_cast<UObject*>(Root));
  R={}; R.ParentGuid=Option; R.ClassPath=TEXT("/Script/AIModule.EnvQueryTest_Distance"); R.Properties.Add(TEXT("TestPurpose"),TEXT("Score")); Control(R,TEXT("create_test")); auto* ExistingTest=O->Tests[0].Get();
  auto Execute=[&](int32 Count)
  {
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; W->CreateAISystem(); auto* Owner=W->SpawnActor<AActor>(); auto* Manager=UEnvQueryManager::GetCurrent(W);
   if(!TestNotNull(TEXT("Composite query manager"),Manager)) return; auto Result=Manager->RunInstantQuery(FEnvQueryRequest(Q,Owner),EEnvQueryRunMode::AllMatching);
   if(!TestTrue(TEXT("Composite result exists"),Result.IsValid())) return; TestTrue(TEXT("Native composite executes"),Result->IsSuccessful()); TestEqual(TEXT("All native children contribute items"),Result->Items.Num(),Count);
   for(int32 I=0;I<Result->Items.Num();++I) TestTrue(TEXT("Native nested location item"),Result->GetItemAsLocation(I).Equals(Owner->GetActorLocation(),.01));
  };
  Execute(2); R={}; R.NodeGuid=Option; R.GeneratorTree=OriginalRows; TestFalse(TEXT("Equivalent generator tree is a no-op"),Control(R,TEXT("replace_generators"))->GetBoolField(TEXT("would_change")));
  R.GeneratorTree={Row(TEXT("CurrentLocation"))}; Control(R,TEXT("replace_generators")); TestTrue(TEXT("Replacement preserves option"),Q->GetOptions()[0]==O); TestEqual(TEXT("Replacement preserves test"),O->Tests[0].Get(),ExistingTest); Execute(1);
  TestTrue(TEXT("Undo replacement"),GEditor->UndoTransaction()); TestTrue(TEXT("Undo restores composite root"),O->Generator->IsA<UEnvQueryGenerator_Composite>()); Execute(2);
  TestTrue(TEXT("Undo generator tree validates"),Parse(EnvironmentQueryUtils::Inspect(Q->GetPathName()))->GetBoolField(TEXT("valid")));
  TestTrue(TEXT("Redo replacement"),GEditor->RedoTransaction()); Execute(1); GEditor->UndoTransaction();
  const FString Before=EnvironmentQueryUtils::Inspect(Q->GetPathName());
  auto Reject=[&](TArray<FEnvironmentQueryGeneratorRow> Rows) { FEnvironmentQueryReq Bad; Bad.NodeGuid=Option; Bad.GeneratorTree=Rows; bool Rejected=false; try { Control(Bad,TEXT("replace_generators")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Invalid tree rejects"),Rejected); TestEqual(TEXT("Rejected tree preserves source"),EnvironmentQueryUtils::Inspect(Q->GetPathName()),Before); };
  Reject({Row(TEXT("Composite"),2),Row(TEXT("CurrentLocation")),Row(TEXT("ActorsOfClass"))});
  auto Async=Row(TEXT("CurrentLocation")); Async.Properties.Add(TEXT("bCanRunAsync"),TEXT("True")); Reject({Row(TEXT("Composite"),1),Async});
  Reject({Row(TEXT("Composite"),0)}); Reject({Row(TEXT("CurrentLocation")),Row(TEXT("CurrentLocation"))});
  auto Forced=Row(TEXT("Composite"),1); Forced.Properties.Add(TEXT("bAllowDifferentItemTypes"),TEXT("True")); Reject({Forced,Row(TEXT("CurrentLocation"))});
  Root=CastChecked<UEnvQueryGenerator_Composite>(O->Generator); const auto Children=Root->Generators; Root->Generators.Add(Root); bool Rejected=false; try { EnvironmentQueryUtils::Inspect(Q->GetPathName()); } catch(const std::exception&) { Rejected=true; } Root->Generators=Children; TestTrue(TEXT("Read-only cycle guard precedes native recursion"),Rejected);
  TestEqual(TEXT("Cycle inspection preserves restored source"),EnvironmentQueryUtils::Inspect(Q->GetPathName()),Before); return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
