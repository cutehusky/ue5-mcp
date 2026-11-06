#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "StateTreeVerificationFixtures.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeEditorData.h"
#include "StateTreeState.h"
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeSingleTaskTest,"UE5MCP.StateTree.SingleTask",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeSingleTaskTest::RunTest(const FString&)
{
 UStateTree* Tree=nullptr;
 ON_SCOPE_EXIT { if(Tree) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& Text) { TSharedPtr<FJsonObject> Json; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json)) throw std::runtime_error("Invalid StateTree JSON"); return Json; };
 auto Control=[&](FStateTreeReq Request,const TCHAR* Operation) { if(Tree) Request.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(Request,Operation)); };
 auto Reject=[&](FStateTreeReq Request,const TCHAR* Operation)
 {
  const FString Before=StateTreeUtils::Inspect(Tree->GetPathName()); bool Rejected=false;
  try { Control(Request,Operation); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Invalid single-task request rejects"),Rejected);
  TestEqual(TEXT("Rejected single-task request preserves source"),StateTreeUtils::Inspect(Tree->GetPathName()),Before);
 };
 try
 {
  FStateTreeReq Request;
  Request.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Single_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
  Request.SchemaPath=UMCPVerificationSingleTaskSchema::StaticClass()->GetPathName();
  const auto Created=Control(Request,TEXT("create"));
  Tree=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path")));
  if(!TestNotNull(TEXT("Single-task tree created"),Tree)) return false;
  const FString Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  Request={}; Request.ParentId=Root; Request.Name=TEXT("Work");
  const FString Work=Control(Request,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.StateId=Work; Control(Request,TEXT("create_transition"));
  Request={}; Request.Name=TEXT("Duration"); Request.ParameterType=TEXT("Float"); Request.bSetValue=true; Request.Value=TEXT("0.04");
  const FString Parameter=Control(Request,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.StateId=Work; Request.Kind=TEXT("single_task"); Request.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask");
  Request.InstanceProperties={{TEXT("Duration"),TEXT("0.02")},{TEXT("RandomDeviation"),TEXT("0")}};
  const FString Task=Control(Request,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  auto* Data=CastChecked<UStateTreeEditorData>(Tree->EditorData);
  auto* NativeState=Data->SubTrees[0]->Children[0].Get();
  TestTrue(TEXT("Native SingleTask populated"),NativeState->SingleTask.Node.IsValid());
  TestTrue(TEXT("Multiple-task array remains empty"),NativeState->Tasks.IsEmpty());
  auto Execute=[&]()
  {
   UWorld::InitializationValues Values; Values.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values);
   ON_SCOPE_EXIT { World->DestroyWorld(false); };
   auto* Owner=World->SpawnActor<AActor>(); FStateTreeInstanceData Instance;
   FStateTreeExecutionContext Context(*Owner,*Tree,Instance);
   TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner)));
   auto Status=Context.Start(); int32 Ticks=0;
   for(;Ticks<128 && Status==EStateTreeRunStatus::Running;++Ticks) Status=Context.Tick(.01f);
   TestTrue(TEXT("Native single-task execution succeeds"),Status==EStateTreeRunStatus::Succeeded);
   Context.Stop(); return Ticks;
  };
  const int32 InitialTicks=Execute();
  Reject(Request,TEXT("create_node"));
  Request.ItemId=Task; Request.Index=1; Reject(Request,TEXT("update_node"));
  Request.Index=-2; Reject(Request,TEXT("update_node"));
  Request.Index=-1; Request.ItemId=FGuid::NewGuid().ToString(); Reject(Request,TEXT("update_node"));
  Request.ItemId=Task; Request.Kind=TEXT("task"); Reject(Request,TEXT("update_node"));
  Request.Kind=TEXT("single_task"); Request.InstanceProperties[TEXT("Duration")]=TEXT("0.12");
  Control(Request,TEXT("update_node")); TestTrue(TEXT("Single-task update changes execution"),Execute()>InitialTicks);
  TestTrue(TEXT("Undo single-task update"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores single-task execution"),Execute(),InitialTicks);
  TestTrue(TEXT("Redo single-task update"),GEditor->RedoTransaction()); TestTrue(TEXT("Redo restores single-task execution"),Execute()>InitialTicks);
  Request.InstanceProperties.Empty(); FStateTreeBindingReq Binding; Binding.SourceId=TEXT("root"); Binding.SourcePath=TEXT("Duration"); Binding.TargetId=Task; Binding.TargetPath=TEXT("Duration"); Request.Bindings.Add(Binding);
  Control(Request,TEXT("update_node")); const int32 BoundTicks=Execute();
  TestEqual(TEXT("Single-task binding stored"),Data->EditorBindings.GetNumBindings(),1);
  Request={}; Request.ItemId=Parameter; Request.bSetValue=true; Request.Value=TEXT("0.16"); Control(Request,TEXT("update_parameter"));
  TestTrue(TEXT("Native binding drives single task"),Execute()>BoundTicks);
  Request={}; Request.StateId=Work; Request.Kind=TEXT("single_task"); Request.ItemId=Task;
  Reject(Request,TEXT("delete_node")); Request.bConfirm=true;
  Control(Request,TEXT("delete_node")); TestFalse(TEXT("Native slot cleared"),NativeState->SingleTask.Node.IsValid());
  TestEqual(TEXT("Single-task binding removed"),Data->EditorBindings.GetNumBindings(),0);
  TestTrue(TEXT("Undo single-task deletion"),GEditor->UndoTransaction());
  TestTrue(TEXT("Undo restores native slot"),NativeState->SingleTask.Node.IsValid());
  TestEqual(TEXT("Undo restores binding"),Data->EditorBindings.GetNumBindings(),1); Execute();
  TestTrue(TEXT("Redo single-task deletion"),GEditor->RedoTransaction());
  TestFalse(TEXT("Redo clears native slot"),NativeState->SingleTask.Node.IsValid());
  Request={}; Request.ParentId=Root; Request.Name=TEXT("Group"); Request.StateType=TEXT("Group");
  const FString Group=Control(Request,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.StateId=Group; Request.Kind=TEXT("single_task"); Request.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); Reject(Request,TEXT("create_node"));
  return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
