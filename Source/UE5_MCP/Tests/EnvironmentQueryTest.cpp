#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/EnvironmentQueryUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryReq.h"
#include "EnvironmentQuery/EnvQuery.h"
#include "EnvironmentQuery/EnvQueryOption.h"
#include "EnvironmentQuery/EnvQueryTest.h"
#include "EnvironmentQuery/EnvQueryManager.h"
#include "EnvironmentQuery/Generators/EnvQueryGenerator_CurrentLocation.h"
#include "EnvironmentQuery/Tests/EnvQueryTest_Distance.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Editor.h"
#include "UObject/Package.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include <stdexcept>
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnvironmentQueryAuthoringTest,"UE5MCP.EnvironmentQuery.Authoring",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEnvironmentQueryAuthoringTest::RunTest(const FString&)
{
 const FString Name=TEXT("EQS_Native_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto* Package=CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)); auto* Q=NewObject<UEnvQuery>(Package,*Name,RF_Public|RF_Standalone|RF_Transactional); FAssetRegistryModule::AssetCreated(Q);
 ON_SCOPE_EXIT { FAssetRegistryModule::AssetDeleted(Q); Q->ClearFlags(RF_Public|RF_Standalone); Q->MarkAsGarbage(); Package->SetDirtyFlag(false); };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid EQS JSON"); return J; };
 auto Control=[&](FEnvironmentQueryReq R,const TCHAR* Op) { R.AssetPath=Q->GetPathName(); return Parse(EnvironmentQueryUtils::Control(R,Op)); };
 try
 {
  // Preserve an existing runtime-only query through native graph initialization.
  auto* Original=NewObject<UEnvQueryOption>(Q); Original->Generator=NewObject<UEnvQueryGenerator_CurrentLocation>(Q); Q->GetOptionsMutable().Add(Original);
  FEnvironmentQueryReq R; Control(R,TEXT("initialize")); TestEqual(TEXT("Native initialization preserves option"),Q->GetOptions()[0],Original);
  TestTrue(TEXT("Undo graph initialization"),GEditor->UndoTransaction()); TestNull(TEXT("Undo restores runtime-only query"),Q->EdGraph.Get()); TestEqual(TEXT("Undo preserves compiled option"),Q->GetOptions()[0],Original);
  TestTrue(TEXT("Redo graph initialization"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo preserves compiled option"),Q->GetOptions()[0],Original);
  auto Snapshot=Parse(EnvironmentQueryUtils::Inspect(Q->GetPathName())); const FString First=Snapshot->GetArrayField(TEXT("options"))[0]->AsObject()->GetStringField(TEXT("guid"));
  R={}; R.ClassPath=TEXT("/Script/AIModule.EnvQueryGenerator_CurrentLocation"); R.X=300; const FString Second=Control(R,TEXT("create_option"))->GetStringField(TEXT("node_guid"));
  R={}; R.ParentGuid=First; R.ClassPath=TEXT("/Script/AIModule.EnvQueryTest_Distance"); R.Properties={{TEXT("TestPurpose"),TEXT("Filter")},{TEXT("FilterType"),TEXT("Minimum")}}; R.ProviderValues.Add(TEXT("FloatValueMin"),TEXT("0")); R.NamedParameters.Add(TEXT("FloatValueMin"),TEXT("MinimumDistance"));
  const FString Distance=Control(R,TEXT("create_test"))->GetStringField(TEXT("node_guid")); TestEqual(TEXT("Native test array compiled"),Q->GetOptions()[0]->Tests.Num(),1);
  auto Execute=[&](float Minimum,int32 ExpectedOption)
  {
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; W->CreateAISystem(); auto* Owner=W->SpawnActor<AActor>(); Owner->SetActorLocation(FVector(100,200,300));
   auto* Manager=UEnvQueryManager::GetCurrent(W); if(!TestNotNull(TEXT("Native query manager"),Manager)) return;
   FEnvQueryRequest Request(Q,Owner); Request.SetFloatParam(TEXT("MinimumDistance"),Minimum); auto Result=Manager->RunInstantQuery(Request,EEnvQueryRunMode::AllMatching);
   if(!TestTrue(TEXT("Native query returns a result"),Result.IsValid())) return;
   TestTrue(TEXT("Native EQS execution succeeds"),Result->IsSuccessful()); TestEqual(TEXT("Native EQS produces one location"),Result->Items.Num(),1); TestEqual(TEXT("Native option fallback follows provider value"),Result->OptionIndex,ExpectedOption);
   if(Result->Items.Num()) TestTrue(TEXT("Native item is querier location"),Result->GetItemAsLocation(0).Equals(Owner->GetActorLocation(),.01));
  };
  Execute(0,0); Execute(1,1);
  R={}; R.NodeGuid=Distance; R.bSetEnabled=true; R.bEnabled=false; Control(R,TEXT("update_test")); TestEqual(TEXT("Disabled test omitted from compiled array"),Q->GetOptions()[0]->Tests.Num(),0); Execute(1,0);
  TestTrue(TEXT("Undo disabled test"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores native test"),Q->GetOptions()[0]->Tests.Num(),1); Execute(1,1);
  TestTrue(TEXT("Redo disabled test"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo restores disabled test"),Q->GetOptions()[0]->Tests.Num(),0); GEditor->UndoTransaction();
  const FString Before=EnvironmentQueryUtils::Inspect(Q->GetPathName()); R={}; R.NodeGuid=Distance; R.ProviderValues.Add(TEXT("ScoringFactor"),TEXT("nan")); bool Rejected=false; try { Control(R,TEXT("update_test")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Non-finite provider rejects"),Rejected); TestEqual(TEXT("Rejected request preserves query"),EnvironmentQueryUtils::Inspect(Q->GetPathName()),Before);
  R={}; R.Positions={{First,500,200},{Second,-100,200}}; Control(R,TEXT("layout")); TestEqual(TEXT("Native X layout changes fallback order"),Q->GetOptions()[1],Original); Execute(1,0);
  TestTrue(TEXT("Undo option order"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores fallback order"),Q->GetOptions()[0],Original);
  TestTrue(TEXT("Compiled graph validates"),Parse(EnvironmentQueryUtils::Inspect(Q->GetPathName()))->GetBoolField(TEXT("valid"))); return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
