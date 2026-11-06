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
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeContainerParameterTest,"UE5MCP.StateTree.ContainerParameters",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeContainerParameterTest::RunTest(const FString&)
{
 TArray<UStateTree*> Trees;
 ON_SCOPE_EXIT { for(auto* Tree:Trees) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& Text) { TSharedPtr<FJsonObject> Json; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json)) throw std::runtime_error("Invalid JSON"); return Json; };
 auto Control=[&](UStateTree* Tree,FStateTreeReq Request,const TCHAR* Operation) { if(Tree) Request.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(Request,Operation)); };
 auto Create=[&]() { FStateTreeReq Request; Request.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Containers_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); const auto Json=Control(nullptr,Request,TEXT("create")); auto* Tree=LoadObject<UStateTree>(nullptr,*Json->GetStringField(TEXT("asset_path"))); Trees.Add(Tree); return Tree; };
 try
 {
  auto* Leaf=Create(); auto* Caller=Create();
  const auto Root=Parse(StateTreeUtils::Inspect(Leaf->GetPathName()))->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  FStateTreeReq Request; Request.Name=TEXT("Samples"); Request.ParameterType=TEXT("Float"); Request.ContainerType=TEXT("Array"); Request.bSetValue=true; Request.Value=TEXT("[\"1\",\"2\"]");
  const auto Samples=Control(Leaf,Request,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  Request.Name=TEXT("Codes"); Request.ParameterType=TEXT("Int32"); Request.ContainerType=TEXT("Set"); Request.Value=TEXT("[\"1\",\"2\",\"2\"]");
  const auto Codes=Control(Leaf,Request,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.ParentId=Root; Request.Name=TEXT("Observe"); const auto Work=Control(Leaf,Request,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.StateId=Work; Request.StructPath=FMCPVerificationContainerTask::StaticStruct()->GetPathName(); Request.InstanceProperties={{TEXT("Expected"),TEXT("6")}};
  for(const auto* Field:{TEXT("Samples"),TEXT("Codes")}) { FStateTreeBindingReq Binding; Binding.SourceId=TEXT("root"); Binding.SourcePath=Field; Binding.TargetId=TEXT("$new"); Binding.TargetPath=Field; Request.Bindings.Add(Binding); }
  Control(Leaf,Request,TEXT("create_node")); Request={}; Request.StateId=Work; Control(Leaf,Request,TEXT("create_transition"));
  const auto CallerRoot=Parse(StateTreeUtils::Inspect(Caller->GetPathName()))->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  Request={}; Request.ParentId=CallerRoot; Request.Name=TEXT("Call"); Request.StateType=TEXT("LinkedAsset"); Request.LinkedAssetPath=Leaf->GetPathName(); const auto Call=Control(Caller,Request,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.StateId=Call; Control(Caller,Request,TEXT("create_transition"));
  auto Execute=[&](UStateTree* Tree,float Expected)
  {
   UWorld::InitializationValues Values; Values.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values); ON_SCOPE_EXIT { World->DestroyWorld(false); };
   auto* Owner=World->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*Tree,Instance);
   TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner)));
   FMCPVerificationContainerTask::ObservedSum=-999; const int32 Before=FMCPVerificationContainerTask::Executions;
   auto Status=Context.Start(); for(int32 Tick=0;Tick<128 && Status==EStateTreeRunStatus::Running;++Tick) Status=Context.Tick(.01f);
   TestTrue(TEXT("Native container task executed"),FMCPVerificationContainerTask::Executions>Before);
   TestEqual(TEXT("Native bound array/set values and deduplication"),FMCPVerificationContainerTask::ObservedSum,Expected);
   Context.Stop();
  };
  Execute(Leaf,6); Execute(Caller,6);
  Request={}; Request.StateId=Call; Request.ItemId=Samples; Request.bSetValue=true; Request.Value=TEXT("[\"10\",\"20\"]"); Control(Caller,Request,TEXT("update_parameter")); Execute(Caller,33); Execute(Leaf,6);
  TestTrue(TEXT("Undo linked array override"),GEditor->UndoTransaction()); Execute(Caller,6);
  TestTrue(TEXT("Redo linked array override"),GEditor->RedoTransaction()); Execute(Caller,33);
  Request={}; Request.ItemId=Codes; Request.bSetValue=true; Request.Value=TEXT("[\"4\",\"5\",\"5\"]"); Control(Leaf,Request,TEXT("update_parameter")); Execute(Leaf,12); Execute(Caller,39);
  TestTrue(TEXT("Undo source set changes caller runtime"),GEditor->UndoTransaction()); Execute(Leaf,6); Execute(Caller,33);
  TestTrue(TEXT("Redo source set changes caller runtime"),GEditor->RedoTransaction()); Execute(Leaf,12); Execute(Caller,39);
  Request={}; Request.StateId=Call; Request.ItemId=Samples; Request.bConfirm=true; Control(Caller,Request,TEXT("reset_parameter")); Execute(Caller,12);
  return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
