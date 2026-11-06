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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreePropertyFunctionTest,"UE5MCP.StateTree.PropertyFunctions",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreePropertyFunctionTest::RunTest(const FString&)
{
 UStateTree* Tree=nullptr;
 ON_SCOPE_EXIT { if(Tree) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid JSON"); return J; };
 auto Edit=[&](FStateTreeReq R,const TCHAR* Op) { if(Tree) R.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_FunctionNative_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto J=Edit(R,TEXT("create")); Tree=LoadObject<UStateTree>(nullptr,*J->GetStringField(TEXT("asset_path")));
  const auto Root=J->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.ParentId=Root; R.Name=TEXT("Work"); const auto Work=Edit(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Work; Edit(R,TEXT("create_transition"));
  R={}; R.Name=TEXT("Input"); R.ParameterType=TEXT("Float"); R.bSetValue=true; R.Value=TEXT("2"); const auto Input=Edit(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Work; R.NodeClassPath=UMCPVerificationBlueprintTask::StaticClass()->GetPathName();
  FStateTreeFunctionBindingReq Function; Function.StructPath=TEXT("/Script/StateTreeModule.StateTreeAddFloatPropertyFunction"); Function.TargetId=TEXT("$new"); Function.TargetPath=TEXT("Amount"); Function.InstanceProperties={{TEXT("Left"),TEXT("3")},{TEXT("Right"),TEXT("4")}}; R.Functions.Add(Function);
  const auto Task=Edit(R,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  auto Execute=[&](float Expected)
  {
   UWorld::InitializationValues V; V.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&V); ON_SCOPE_EXIT { W->DestroyWorld(false); };
   auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*Tree,Instance); Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner));
   UMCPVerificationBlueprintTask::ObservedAmount=-1; auto Status=Context.Start(); for(int32 I=0;I<16 && Status==EStateTreeRunStatus::Running;++I) Status=Context.Tick(.01f);
   TestTrue(TEXT("Function-bound native task succeeds"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Native property function result reaches task"),UMCPVerificationBlueprintTask::ObservedAmount,Expected); Context.Stop();
  };
  Execute(7);
  auto Snapshot=Parse(StateTreeUtils::Inspect(Tree->GetPathName())); const auto FunctionID=Snapshot->GetArrayField(TEXT("bindings"))[0]->AsObject()->GetStringField(TEXT("source_id"));
  R={}; R.StructPath=Function.StructPath; R.Binding.TargetId=FunctionID; R.Binding.TargetPath=TEXT("Left"); R.InstanceProperties={{TEXT("Right"),TEXT("5")}}; FStateTreeBindingReq B; B.SourceId=TEXT("root"); B.SourcePath=TEXT("Input"); B.TargetId=TEXT("$function"); B.TargetPath=TEXT("Left"); R.Bindings.Add(B);
  Edit(R,TEXT("create_function")); Execute(11);
  TestTrue(TEXT("Undo nested property function"),GEditor->UndoTransaction()); Execute(7); TestTrue(TEXT("Redo nested property function"),GEditor->RedoTransaction()); Execute(11);
  R={}; R.ItemId=Input; R.bSetValue=true; R.Value=TEXT("8"); Edit(R,TEXT("update_parameter")); Execute(17);
  R={}; R.ItemId=FunctionID; R.InstanceProperties={{TEXT("Right"),TEXT("10")}}; Edit(R,TEXT("update_function")); Execute(23);
  TestTrue(TEXT("Undo function settings"),GEditor->UndoTransaction()); Execute(17); TestTrue(TEXT("Redo function settings"),GEditor->RedoTransaction()); Execute(23);
  R={}; R.ItemId=FunctionID; R.bConfirm=true; Edit(R,TEXT("delete_function")); TestEqual(TEXT("Recursive cleanup removes owned functions/inputs"),Parse(StateTreeUtils::Inspect(Tree->GetPathName()))->GetIntegerField(TEXT("binding_count")),0);
  TestTrue(TEXT("Undo recursive function deletion"),GEditor->UndoTransaction()); Execute(23);
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
