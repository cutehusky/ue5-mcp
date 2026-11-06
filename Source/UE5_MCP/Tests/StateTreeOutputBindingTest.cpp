#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "StateTreeVerificationFixtures.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeExecutionContext.h"
#include "StateTreeInstanceData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeOutputBindingTest,"UE5MCP.StateTree.OutputBindings",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeOutputBindingTest::RunTest(const FString&)
{
 UStateTree* Tree=nullptr;
 ON_SCOPE_EXIT { if(Tree) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid JSON"); return J; };
 auto Edit=[&](FStateTreeReq R,const TCHAR* Op) { if(Tree) R.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_OutputNative_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto J=Edit(R,TEXT("create")); Tree=LoadObject<UStateTree>(nullptr,*J->GetStringField(TEXT("asset_path")));
  const auto Root=J->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.Kind=TEXT("evaluator"); R.NodeClassPath=UMCPVerificationBlueprintEvaluator::StaticClass()->GetPathName(); const auto Evaluator=Edit(R,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  R={}; R.ParentId=Root; R.Name=TEXT("Producer"); const auto Producer=Edit(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  R.Name=TEXT("Consumer"); const auto Consumer=Edit(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Producer; R.NodeClassPath=UMCPVerificationBlueprintTask::StaticClass()->GetPathName(); R.InstanceProperties={{TEXT("Amount"),TEXT("7")}};
  FStateTreeBindingReq B; B.SourceId=Evaluator; B.SourcePath=TEXT("Amount"); B.TargetId=TEXT("$new"); B.TargetPath=TEXT("ProducedValue"); B.bOutput=true; R.Bindings.Add(B); const auto Task=Edit(R,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Consumer; R.NodeClassPath=UMCPVerificationBlueprintTask::StaticClass()->GetPathName(); B.SourcePath=TEXT("Amount"); B.TargetPath=TEXT("Amount"); B.bOutput=false; R.Bindings.Add(B); Edit(R,TEXT("create_node"));
  R={}; R.StateId=Producer; R.TargetType=TEXT("GotoState"); R.TargetStateId=Consumer; Edit(R,TEXT("create_transition")); R={}; R.StateId=Consumer; Edit(R,TEXT("create_transition"));
  auto Execute=[&](float Expected)
  {
   UWorld::InitializationValues V; V.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&V); ON_SCOPE_EXIT { W->DestroyWorld(false); };
   auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*Tree,Instance); Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner));
   UMCPVerificationBlueprintTask::ObservedAmount=-1; auto Status=Context.Start(); for(int32 I=0;I<16 && Status==EStateTreeRunStatus::Running;++I) Status=Context.Tick(.01f);
   TestTrue(TEXT("Producer and consumer complete"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Output reverse copy reaches later consumer through evaluator source"),UMCPVerificationBlueprintTask::ObservedAmount,Expected); Context.Stop();
  };
  Execute(14);
  R={}; R.StateId=Producer; R.ItemId=Task; R.InstanceProperties={{TEXT("Amount"),TEXT("9")}}; Edit(R,TEXT("update_node")); Execute(18);
  TestTrue(TEXT("Undo output producer edit"),GEditor->UndoTransaction()); Execute(14); TestTrue(TEXT("Redo output producer edit"),GEditor->RedoTransaction()); Execute(18);
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
