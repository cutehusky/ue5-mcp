#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/BehaviorTreeGraphUtils.h"
#include "UE5_MCP/Core/BlackboardUtils.h"
#include "UE5_MCP/API/DTO/BehaviorTreeGraphReq.h"
#include "UE5_MCP/API/DTO/BlackboardKeyReq.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BehaviorTree/Composites/BTComposite_SimpleParallel.h"
#include "BehaviorTreeGraphNode_SimpleParallel.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AIController.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBehaviorTreeParallelTest,"UE5MCP.BehaviorTree.SimpleParallel",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBehaviorTreeParallelTest::RunTest(const FString&)
{
 const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto* BP=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BB_ParallelAutomation_")+Id));
 auto* TP=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BT_ParallelAutomation_")+Id));
 auto* B=NewObject<UBlackboardData>(BP,*FString(TEXT("BB_ParallelAutomation_")+Id),RF_Public|RF_Standalone|RF_Transactional);
 auto* T=NewObject<UBehaviorTree>(TP,*FString(TEXT("BT_ParallelAutomation_")+Id),RF_Public|RF_Standalone|RF_Transactional);
 FAssetRegistryModule::AssetCreated(B); FAssetRegistryModule::AssetCreated(T);
 ON_SCOPE_EXIT { FAssetRegistryModule::AssetDeleted(T); FAssetRegistryModule::AssetDeleted(B); T->ClearFlags(RF_Public|RF_Standalone); B->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); B->MarkAsGarbage(); BP->SetDirtyFlag(false); TP->SetDirtyFlag(false); };
 auto Parse=[](const FString& Text) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J)) throw std::runtime_error("Invalid graph response JSON"); return J; };
 auto Control=[&](FBehaviorTreeGraphReq R,const TCHAR* Op) { R.AssetPath=T->GetPathName(); return Parse(BehaviorTreeGraphUtils::Control(R,Op)); };
 auto Create=[&](const TCHAR* Class,int32 X,const TMap<FString,FString>& Properties,const TMap<FString,FString>& Selectors)
 {
  FBehaviorTreeGraphReq R; R.ClassPath=FString(TEXT("/Script/AIModule."))+Class; R.X=X; R.Y=400; R.Properties=Properties; R.BlackboardSelectors=Selectors; return Control(R,TEXT("create_node"))->GetStringField(TEXT("node_guid"));
 };
 auto Connect=[&](const FString& From,const FString& To,int32 Slot=0) { FBehaviorTreeGraphReq R; R.NodeGuid=From; R.TargetGuid=To; R.PinIndex=Slot; Control(R,TEXT("connect")); };
 try
 {
  FBlackboardKeyReq K; K.AssetPath=B->GetPathName(); K.KeyName=TEXT("Done"); K.KeyType=TEXT("/Script/AIModule.BlackboardKeyType_Bool"); BlackboardUtils::Control(K,TEXT("add"));
  FBehaviorTreeGraphReq R; const FString Root=Control(R,TEXT("initialize"))->GetStringField(TEXT("root_guid"));
  R.BlackboardPath=B->GetPathName(); R.bConfirm=true; Control(R,TEXT("set_blackboard"));
  const FString Parallel=Create(TEXT("BTComposite_SimpleParallel"),0,{{TEXT("FinishMode"),TEXT("WaitForBackground")}},{ });
  Connect(Root,Parallel);
  TestFalse(TEXT("Incomplete parallel reports invalid"),Parse(BehaviorTreeGraphUtils::Inspect(T->GetPathName()))->GetBoolField(TEXT("valid")));
  const FString Main=Create(TEXT("BTTask_Wait"),900,{{TEXT("WaitTime"),TEXT("(DefaultValue=0.05,Key=None)")}},{ });
  const FString Background=Create(TEXT("BTComposite_Sequence"),-900,{ },{ });
  const FString LongWait=Create(TEXT("BTTask_Wait"),-1000,{{TEXT("WaitTime"),TEXT("(DefaultValue=0.30,Key=None)")}},{ });
  const FString Marker=Create(TEXT("BTTask_SetKeyValueBool"),-800,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("Done")}});
  const FString Before=BehaviorTreeGraphUtils::Inspect(T->GetPathName()); R={}; R.NodeGuid=Parallel; R.TargetGuid=Background;
  bool Rejected=false; try { Control(R,TEXT("connect")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Main pin rejects a composite"),Rejected); TestEqual(TEXT("Schema rejection preserves graph"),BehaviorTreeGraphUtils::Inspect(T->GetPathName()),Before);
  Connect(Parallel,Main,0); Connect(Parallel,Background,1); Connect(Background,LongWait); Connect(Background,Marker);
  auto* Native=Cast<UBTComposite_SimpleParallel>(T->RootNode);
  if(!TestNotNull(TEXT("Native parallel root"),Native)) return false;
  TestEqual(TEXT("Two compiled roles"),Native->Children.Num(),2);
  TestNotNull(TEXT("Main role is a task despite larger X"),Native->Children[0].ChildTask.Get());
  TestNotNull(TEXT("Background role is a composite despite smaller X"),Native->Children[1].ChildComposite.Get());
  TestTrue(TEXT("Complete parallel validates"),Parse(BehaviorTreeGraphUtils::Inspect(T->GetPathName()))->GetBoolField(TEXT("valid")));
  const FString Configured=BehaviorTreeGraphUtils::Inspect(T->GetPathName()); R={}; R.NodeGuid=Parallel; R.Properties.Add(TEXT("FinishMode"),TEXT("99")); Rejected=false;
  try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Invalid finish mode rejected"),Rejected); TestEqual(TEXT("Invalid finish mode preserves graph"),BehaviorTreeGraphUtils::Inspect(T->GetPathName()),Configured);
  auto Run=[&](const TCHAR* Mode,bool WantMarker)
  {
   FBehaviorTreeGraphReq Set; Set.NodeGuid=Parallel; Set.Properties.Add(TEXT("FinishMode"),Mode); Control(Set,TEXT("update_node"));
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { World->DestroyWorld(false); };
   World->CreateAISystem(); auto* C=World->SpawnActor<AAIController>(); UBlackboardComponent* Board=nullptr;
   if(!TestTrue(TEXT("Native Blackboard initialization"),C->UseBlackboard(B,Board))) return -1;
   if(!Board->HasBeenInitialized()) Board->InitializeComponent();
   auto* Runtime=NewObject<UBehaviorTreeComponent>(C); C->BrainComponent=Runtime; Runtime->RegisterComponent(); if(!Runtime->HasBeenInitialized()) Runtime->InitializeComponent();
   ON_SCOPE_EXIT { Runtime->StopTree(EBTStopMode::Forced); Runtime->Cleanup(); };
   Runtime->StartTree(*T,EBTExecutionMode::SingleRun); TestTrue(FString(Mode)+TEXT(" starts"),Runtime->IsRunning());
   TestFalse(TEXT("Marker is initially false"),Board->GetValueAsBool(TEXT("Done")));
   int32 Ticks=0; for(;Ticks<512 && Runtime->IsRunning();++Ticks) Runtime->TickComponent(.01f,LEVELTICK_All,nullptr);
   TestFalse(FString(Mode)+TEXT(" single-run terminates"),Runtime->IsRunning());
   TestEqual(FString(Mode)+TEXT(" native background marker"),Board->GetValueAsBool(TEXT("Done")),WantMarker); return Ticks;
  };
  const int32 Immediate=Run(TEXT("AbortBackground"),false);
  const int32 Delayed=Run(TEXT("WaitForBackground"),true);
  TestTrue(TEXT("Delayed mode waits beyond main task duration"),Immediate>0 && Delayed>Immediate+10);
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
