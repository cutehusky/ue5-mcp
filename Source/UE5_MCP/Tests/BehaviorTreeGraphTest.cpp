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
#include "BehaviorTree/BTCompositeNode.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BehaviorTree/Composites/BTComposite_Sequence.h"
#include "BehaviorTree/Tasks/BTTask_Wait.h"
#include "BehaviorTree/Services/BTService_DefaultFocus.h"
#include "BehaviorTree/Decorators/BTDecorator_ForceSuccess.h"
#include "BehaviorTree/BTService.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Bool.h"
#include "BehaviorTreeGraph.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AIController.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBehaviorTreeGraphTest,"UE5MCP.BehaviorTree.GraphRuntime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBehaviorTreeGraphTest::RunTest(const FString&)
{
 const FString Suffix=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto* BP=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BB_GraphAutomation_")+Suffix));
 auto* TP=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BT_GraphAutomation_")+Suffix));
 auto* B=NewObject<UBlackboardData>(BP,*FString(TEXT("BB_GraphAutomation_")+Suffix),RF_Public|RF_Standalone|RF_Transactional);
 auto* T=NewObject<UBehaviorTree>(TP,*FString(TEXT("BT_GraphAutomation_")+Suffix),RF_Public|RF_Standalone|RF_Transactional);
 FAssetRegistryModule::AssetCreated(B); FAssetRegistryModule::AssetCreated(T);
 ON_SCOPE_EXIT
 {
  FAssetRegistryModule::AssetDeleted(T); FAssetRegistryModule::AssetDeleted(B);
  T->ClearFlags(RF_Public|RF_Standalone); B->ClearFlags(RF_Public|RF_Standalone);
  T->MarkAsGarbage(); B->MarkAsGarbage(); BP->SetDirtyFlag(false); TP->SetDirtyFlag(false);
 };
 auto Parse=[&](const FString& Text)
 {
  TSharedPtr<FJsonObject> Json;
  if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json)) throw std::runtime_error("Native graph response is invalid JSON");
  return Json;
 };
 auto Control=[&](FBehaviorTreeGraphReq R,const TCHAR* Op) { R.AssetPath=T->GetPathName(); return Parse(BehaviorTreeGraphUtils::Control(R,Op)); };
 auto Create=[&](const TCHAR* Class,int32 X,const TMap<FString,FString>& Props,const TMap<FString,FString>& Selectors,const FString& Parent=TEXT(""))
 {
  FBehaviorTreeGraphReq R; R.ClassPath=FString(TEXT("/Script/AIModule."))+Class; R.X=X; R.Y=400; R.Properties=Props; R.BlackboardSelectors=Selectors; R.ParentGuid=Parent;
  return Control(R,TEXT("create_node"))->GetStringField(TEXT("node_guid"));
 };
 auto Connect=[&](const FString& A,const FString& Target)
 {
  FBehaviorTreeGraphReq R; R.NodeGuid=A; R.TargetGuid=Target; Control(R,TEXT("connect"));
 };
 try
 {
  FBlackboardKeyReq K; K.AssetPath=B->GetPathName(); K.KeyName=TEXT("Done"); K.KeyType=TEXT("/Script/AIModule.BlackboardKeyType_Bool"); BlackboardUtils::Control(K,TEXT("add"));
  K.KeyName=TEXT("Delay"); K.KeyType=TEXT("/Script/AIModule.BlackboardKeyType_Float"); K.bSetTypeSettings=true; K.TypeSettings.bSetDefault=true; K.TypeSettings.FloatValue=.02; BlackboardUtils::Control(K,TEXT("add"));
  // Explicit graph initialization must preserve an existing compiled runtime tree.
  TStrongObjectPtr<UBehaviorTree> Legacy(NewObject<UBehaviorTree>(TP,NAME_None,RF_Transient)); Legacy->BlackboardAsset=B;
  auto* LegacyRoot=NewObject<UBTComposite_Sequence>(Legacy.Get()); auto* LegacyTask=NewObject<UBTTask_Wait>(Legacy.Get());
  Legacy->RootNode=LegacyRoot; FBTCompositeChild LegacyChild; LegacyChild.ChildTask=LegacyTask; LegacyRoot->Children.Add(LegacyChild);
  auto* LegacyService=NewObject<UBTService_DefaultFocus>(Legacy.Get()); LegacyRoot->Services.Add(LegacyService);
  auto* LegacyDecorator=NewObject<UBTDecorator_ForceSuccess>(Legacy.Get()); Legacy->RootDecorators.Add(LegacyDecorator);
  FBehaviorTreeGraphReq LegacyRequest; LegacyRequest.AssetPath=Legacy->GetPathName(); LegacyRequest.bDryRun=true;
  BehaviorTreeGraphUtils::Control(LegacyRequest,TEXT("initialize")); TestTrue(TEXT("Initialize dry-run preserves runtime-only tree"),Legacy->BTGraph==nullptr && Legacy->RootNode==LegacyRoot);
  LegacyRequest.bDryRun=false; BehaviorTreeGraphUtils::Control(LegacyRequest,TEXT("initialize"));
  TestTrue(TEXT("Existing runtime root preserved"),Legacy->RootNode==LegacyRoot);
  TestTrue(TEXT("Existing runtime child preserved"),LegacyRoot->Children.Num()==1 && LegacyRoot->Children[0].ChildTask==LegacyTask);
  TestTrue(TEXT("Existing Blackboard preserved"),Legacy->GetBlackboardAsset()==B);
  TestTrue(TEXT("Existing service preserved"),LegacyRoot->Services.Num()==1 && LegacyRoot->Services[0]==LegacyService);
  TestTrue(TEXT("Existing root decorator preserved"),Legacy->RootDecorators.Num()==1 && Legacy->RootDecorators[0]==LegacyDecorator);
  TestTrue(TEXT("Undo graph initialization"),GEditor->UndoTransaction()); TestTrue(TEXT("Undo restores runtime-only tree"),Legacy->BTGraph==nullptr && Legacy->RootNode==LegacyRoot && LegacyRoot->Children.Num()==1 && LegacyRoot->Children[0].ChildTask==LegacyTask);
  TestTrue(TEXT("Undo preserves native runtime ownership"),LegacyRoot->GetOuter()==Legacy.Get() && LegacyTask->GetOuter()==Legacy.Get());
  TestTrue(TEXT("Undo preserves native service/decorator data"),LegacyRoot->Services.Num()==1 && LegacyRoot->Services[0]==LegacyService && Legacy->RootDecorators.Num()==1 && Legacy->RootDecorators[0]==LegacyDecorator);
  TestTrue(TEXT("Redo graph initialization"),GEditor->RedoTransaction()); TestTrue(TEXT("Redo restored native editor graph"),Legacy->BTGraph!=nullptr);
  FBehaviorTreeGraphReq R; const FString Root=Control(R,TEXT("initialize"))->GetStringField(TEXT("root_guid"));
  TestTrue(TEXT("Initialize preserves null Blackboard instead of adopting a random loaded asset"),T->GetBlackboardAsset()==nullptr);
  R.BlackboardPath=B->GetPathName(); R.bConfirm=true; Control(R,TEXT("set_blackboard"));
  const FString Sequence=Create(TEXT("BTComposite_Sequence"),0,{},{});
  const FString Wait=Create(TEXT("BTTask_Wait"),-200,{{TEXT("WaitTime"),TEXT("(DefaultValue=0.02,Key=None)")}},{{TEXT("WaitTime"),TEXT("Delay")}});
  const FString Marker=Create(TEXT("BTTask_SetKeyValueBool"),200,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("Done")}});
  Connect(Root,Sequence); Connect(Sequence,Wait); Connect(Sequence,Marker);
  Create(TEXT("BTService_DefaultFocus"),0,{},{{TEXT("BlackboardKey"),TEXT("SelfActor")}},Sequence);
  const FString Decorator=Create(TEXT("BTDecorator_ForceSuccess"),0,{},{},Wait);
  TestEqual(TEXT("Native compiled task count"),T->RootNode->Children.Num(),2);
  TestEqual(TEXT("Native compiled service count"),T->RootNode->Services.Num(),1);
  TestEqual(TEXT("Native compiled child decorator count"),T->RootNode->Children[0].Decorators.Num(),1);
  TestTrue(TEXT("Compiled graph validates"),Parse(BehaviorTreeGraphUtils::Inspect(T->GetPathName()))->GetBoolField(TEXT("valid")));
  const FString Before=BehaviorTreeGraphUtils::Inspect(T->GetPathName());
  R={}; R.NodeGuid=Wait; R.BlackboardSelectors.Add(TEXT("WaitTime"),TEXT("Done")); bool Rejected=false;
  try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Reject incompatible native value binding"),Rejected);
  TestEqual(TEXT("Preflight preserves graph/runtime state"),BehaviorTreeGraphUtils::Inspect(T->GetPathName()),Before);
  R={}; R.NodeGuid=Wait; R.bDryRun=true; auto Preview=Control(R,TEXT("delete_node"));
  bool ReportsDecorator=false; for(const auto& V:Preview->GetArrayField(TEXT("affected_nodes"))) ReportsDecorator|=V->AsString()==Decorator;
  TestTrue(TEXT("Delete preview reports decorator"),ReportsDecorator);
  R.bDryRun=false; R.bConfirm=true; Control(R,TEXT("delete_node"));
  TestEqual(TEXT("Deleted native branch"),T->RootNode->Children.Num(),1);
  TestTrue(TEXT("Undo branch deletion"),GEditor->UndoTransaction());
  TestEqual(TEXT("Restored native branch"),T->RootNode->Children.Num(),2);
  TestEqual(TEXT("Restored decorator"),T->RootNode->Children[0].Decorators.Num(),1);
  TestTrue(TEXT("Redo branch deletion"),GEditor->RedoTransaction());
  TestEqual(TEXT("Redo native branch"),T->RootNode->Children.Num(),1);
  TestTrue(TEXT("Restore final tree"),GEditor->UndoTransaction());
  R={}; R.Positions.Add({Wait,400,400}); R.Positions.Add({Marker,-400,400}); Control(R,TEXT("set_positions"));
  TestTrue(TEXT("X coordinates reorder compiled children"),T->RootNode->Children[0].ChildTask->GetClass()->GetName()==TEXT("BTTask_SetKeyValueBool"));
  TestTrue(TEXT("Undo execution order"),GEditor->UndoTransaction());
  TestTrue(TEXT("Wait task restored first"),T->RootNode->Children[0].ChildTask->GetClass()->GetName()==TEXT("BTTask_Wait"));

  UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
  auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV);
  if(!TestNotNull(TEXT("Owned runtime world"),World)) return false;
  ON_SCOPE_EXIT { World->DestroyWorld(false); };
  World->CreateAISystem(); auto* C=World->SpawnActor<AAIController>();
  if(!TestNotNull(TEXT("Owned native controller"),C)) return false;
  UBlackboardComponent* RuntimeBB=nullptr;
  if(!TestTrue(TEXT("Native UseBlackboard"),C->UseBlackboard(B,RuntimeBB))) return false;
  if(!RuntimeBB->HasBeenInitialized()) RuntimeBB->InitializeComponent();
  auto* Runtime=NewObject<UBehaviorTreeComponent>(C); C->BrainComponent=Runtime; Runtime->RegisterComponent();
  if(!Runtime->HasBeenInitialized()) Runtime->InitializeComponent();
  ON_SCOPE_EXIT { Runtime->StopTree(EBTStopMode::Forced); Runtime->Cleanup(); };
  Runtime->StartTree(*T,EBTExecutionMode::SingleRun);
  TestTrue(TEXT("Native tree started"),Runtime->IsRunning());
  TestFalse(TEXT("Marker initially false before Wait finishes"),RuntimeBB->GetValueAsBool(TEXT("Done")));
  for(int32 I=0;I<128 && Runtime->IsRunning();++I) Runtime->TickComponent(.05f,LEVELTICK_All,nullptr);
  TestFalse(TEXT("Native single-run tree finishes"),Runtime->IsRunning());
  TestTrue(TEXT("Native task after Wait wrote the Blackboard marker"),RuntimeBB->GetValueAsBool(TEXT("Done")));
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif

