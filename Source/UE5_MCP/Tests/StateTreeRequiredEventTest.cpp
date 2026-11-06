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
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeRequiredEventTest,"UE5MCP.StateTree.RequiredEvents",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeRequiredEventTest::RunTest(const FString&)
{
 UStateTree* Tree=nullptr;
 ON_SCOPE_EXIT { if(Tree) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& Text) { TSharedPtr<FJsonObject> Json; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json)) throw std::runtime_error("Invalid JSON"); return Json; };
 auto Edit=[&](FStateTreeReq R,const TCHAR* Op) { if(Tree) R.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_EventNative_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
  auto Created=Edit(R,TEXT("create")); Tree=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path")));
  const auto Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.ParentId=Root; R.Name=TEXT("Waiting"); const auto Waiting=Edit(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Waiting; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("bRunForever"),TEXT("True")}}; Edit(R,TEXT("create_node"));
  R={}; R.ParentId=Root; R.Name=TEXT("Received"); R.bSetRequiredEvent=true; R.PayloadStructPath=TEXT("/Script/CoreUObject.Vector");
  const auto Received=Edit(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  const auto Snapshot=Parse(StateTreeUtils::Inspect(Tree->GetPathName())); FString Source;
  for(const auto& State:Snapshot->GetArrayField(TEXT("states"))) if(State->AsObject()->GetStringField(TEXT("id"))==Received) Source=State->AsObject()->GetStringField(TEXT("event_source_id"));
  R={}; R.StateId=Received; R.NodeClassPath=UMCPVerificationBlueprintTask::StaticClass()->GetPathName();
  FStateTreeBindingReq Binding; Binding.SourceId=Source; Binding.SourcePath=TEXT("Payload.X"); Binding.TargetId=TEXT("$new"); Binding.TargetPath=TEXT("Amount"); R.Bindings.Add(Binding); Edit(R,TEXT("create_node"));
  R={}; R.StateId=Received; Edit(R,TEXT("create_transition"));
  R={}; R.StateId=Waiting; R.Trigger=TEXT("OnEvent"); R.PayloadStructPath=TEXT("/Script/CoreUObject.Vector"); R.TargetType=TEXT("GotoState"); R.TargetStateId=Received; R.bConsumeEvent=false; const auto Transition=Edit(R,TEXT("create_transition"))->GetStringField(TEXT("selected_id"));
  for(bool Consume:{false,true})
  for(bool TransitionConsume:{false,true})
  {
   R={}; R.StateId=Waiting; R.ItemId=Transition; R.Trigger=TEXT("OnEvent"); R.PayloadStructPath=TEXT("/Script/CoreUObject.Vector"); R.TargetType=TEXT("GotoState"); R.TargetStateId=Received; R.bConsumeEvent=TransitionConsume; Edit(R,TEXT("update_transition"));
   R={}; R.StateId=Received; R.bSetRequiredEvent=true; R.PayloadStructPath=TEXT("/Script/CoreUObject.Vector"); R.bConsumeEvent=Consume; Edit(R,TEXT("update_state"));
   bool FoundCompiled=false;
   for(const auto& State:Tree->GetStates()) if(State.Name==TEXT("Received")) { FoundCompiled=true; TestEqual(TEXT("Native compiler retains state event consumption"),bool(State.bConsumeEventOnSelect),Consume); }
   TestTrue(TEXT("Required-event state compiled"),FoundCompiled);
   UWorld::InitializationValues Values; Values.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values); ON_SCOPE_EXIT { World->DestroyWorld(false); };
   auto* Owner=World->SpawnActor<AActor>(); FStateTreeInstanceData Instance;
   const auto SharedQueue=MakeShared<FStateTreeEventQueue>(); Instance.SetSharedEventQueue(SharedQueue);
   FStateTreeExecutionContext Context(*Owner,*Tree,Instance);
   TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner)));
   const auto Before=UMCPVerificationBlueprintTask::Executions; Context.Start();
   FInstancedStruct Wrong; Wrong.InitializeAs(TBaseStructure<FLinearColor>::Get()); Context.SendEvent(FGameplayTag(),FConstStructView(Wrong)); Context.Tick(.01f);
   TestEqual(TEXT("Wrong payload cannot select required-event state"),UMCPVerificationBlueprintTask::Executions,Before);
   SharedQueue->Reset();
   FInstancedStruct Payload; Payload.InitializeAs(TBaseStructure<FVector>::Get()); Payload.GetMutable<FVector>()=FVector(7,2,3);
   Context.SendEvent(FGameplayTag(),FConstStructView(Payload)); auto Status=Context.Tick(.01f);
   for(int32 Tick=0;Tick<16 && Status==EStateTreeRunStatus::Running;++Tick) Status=Context.Tick(.01f);
   TestTrue(TEXT("Matching native payload selects event state"),UMCPVerificationBlueprintTask::Executions>Before);
   TestEqual(TEXT("Required-event payload field reaches native task binding"),UMCPVerificationBlueprintTask::ObservedAmount,7.f);
   TestEqual(TEXT("Shared event retained only when state and transition both permit reuse"),SharedQueue->GetEventsView().Num(),(Consume || TransitionConsume) ? 0 : 1);
   TestTrue(TEXT("Event-driven state completes"),Status==EStateTreeRunStatus::Succeeded); Context.Stop();
  }
  return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
