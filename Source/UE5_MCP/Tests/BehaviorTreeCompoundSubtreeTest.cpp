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
#include "BehaviorTree/Tasks/BTTask_RunBehavior.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AIController.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBehaviorTreeCompoundSubtreeTest,"UE5MCP.BehaviorTree.CompoundSubtree",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBehaviorTreeCompoundSubtreeTest::RunTest(const FString&)
{
 const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 TArray<UObject*> Assets; TArray<UPackage*> Packages;
 auto New=[&](UClass* C,const TCHAR* Prefix) { const FString Name=FString(Prefix)+Id; auto* P=CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)); Packages.Add(P); auto* O=NewObject<UObject>(P,C,*Name,RF_Public|RF_Standalone|RF_Transactional); Assets.Add(O); FAssetRegistryModule::AssetCreated(O); return O; };
 auto* Board=CastChecked<UBlackboardData>(New(UBlackboardData::StaticClass(),TEXT("BB_Subtree_")));
 auto* Child=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Child_")));
 auto* Parent=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Parent_")));
 ON_SCOPE_EXIT { for(auto* O:Assets) { FAssetRegistryModule::AssetDeleted(O); O->ClearFlags(RF_Public|RF_Standalone); O->MarkAsGarbage(); } for(auto* P:Packages) P->SetDirtyFlag(false); };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid subtree response JSON"); return J; };
 auto Control=[&](UBehaviorTree* T,FBehaviorTreeGraphReq R,const TCHAR* Op) { R.AssetPath=T->GetPathName(); return Parse(BehaviorTreeGraphUtils::Control(R,Op)); };
 auto Create=[&](UBehaviorTree* T,const TCHAR* Class,int32 X,const TMap<FString,FString>& Props,const TMap<FString,FString>& Keys,const FString& ParentGuid=TEXT(""),UBehaviorTree* Subtree=nullptr)
 {
  FBehaviorTreeGraphReq R; R.ClassPath=FString(TEXT("/Script/AIModule."))+Class; R.X=X; R.Y=400; R.Properties=Props; R.BlackboardSelectors=Keys; R.ParentGuid=ParentGuid; R.bSetSubtree=Subtree!=nullptr; R.SubtreePath=Subtree ? Subtree->GetPathName() : FString(); return Control(T,R,TEXT("create_node"))->GetStringField(TEXT("node_guid"));
 };
 auto Connect=[&](UBehaviorTree* T,const FString& A,const FString& B) { FBehaviorTreeGraphReq R; R.NodeGuid=A; R.TargetGuid=B; Control(T,R,TEXT("connect")); };
 try
 {
  for(const TCHAR* Name:{TEXT("Gate"),TEXT("Done"),TEXT("After")}) { FBlackboardKeyReq K; K.AssetPath=Board->GetPathName(); K.KeyName=Name; K.KeyType=TEXT("/Script/AIModule.BlackboardKeyType_Bool"); BlackboardUtils::Control(K,TEXT("add")); }
  auto Setup=[&](UBehaviorTree* T) { FBehaviorTreeGraphReq R; auto Root=Control(T,R,TEXT("initialize"))->GetStringField(TEXT("root_guid")); R.BlackboardPath=Board->GetPathName(); R.bConfirm=true; Control(T,R,TEXT("set_blackboard")); auto Seq=Create(T,TEXT("BTComposite_Sequence"),0,{ },{ }); Connect(T,Root,Seq); return Seq; };
  const FString ChildRoot=Setup(Child);
  const FString ChildMarker=Create(Child,TEXT("BTTask_SetKeyValueBool"),0,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("Done")}}); Connect(Child,ChildRoot,ChildMarker);
  FBehaviorTreeGraphReq Logic; Logic.ParentGuid=ChildRoot;
  FBehaviorTreeLogicRow And; And.Operation=TEXT("and"); And.Children=2;
  FBehaviorTreeLogicRow Gate; Gate.Operation=TEXT("test"); Gate.ClassPath=TEXT("/Script/AIModule.BTDecorator_Blackboard"); Gate.BlackboardSelectors.Add(TEXT("BlackboardKey"),TEXT("Gate"));
  Logic.Logic={And,Gate,Gate}; Control(Child,Logic,TEXT("create_compound"));
  Child->GetOutermost()->SetDirtyFlag(false); const FString Source=BehaviorTreeGraphUtils::Inspect(Child->GetPathName());
  const FString ParentRoot=Setup(Parent);
  const FString Call=Create(Parent,TEXT("BTTask_RunBehavior"),-200,{ },{ },TEXT(""),Child);
  const FString Again=Create(Parent,TEXT("BTTask_RunBehavior"),0,{ },{ },TEXT(""),Child);
  const FString After=Create(Parent,TEXT("BTTask_SetKeyValueBool"),200,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("After")}});
  Connect(Parent,ParentRoot,Call); Connect(Parent,ParentRoot,Again); Connect(Parent,ParentRoot,After);
  auto Snapshot=Parse(BehaviorTreeGraphUtils::Inspect(Parent->GetPathName())); TestTrue(TEXT("Parent with root decorators validates"),Snapshot->GetBoolField(TEXT("valid")));
  TSet<FString> Guids; int32 Injected=0; for(const auto& V:Snapshot->GetArrayField(TEXT("nodes"))) { auto N=V->AsObject(); TestFalse(TEXT("API GUIDs are unique across repeated subtree calls"),Guids.Contains(N->GetStringField(TEXT("guid")))); Guids.Add(N->GetStringField(TEXT("guid"))); if(N->GetBoolField(TEXT("injected"))) { ++Injected; TestTrue(TEXT("Injected previews are read-only"),N->GetBoolField(TEXT("read_only"))); } }
  TSet<FString> InnerIds; for(const auto& V:Snapshot->GetArrayField(TEXT("nodes"))) if(V->AsObject()->GetBoolField(TEXT("injected"))) for(const auto& Inner:V->AsObject()->GetObjectField(TEXT("compound"))->GetArrayField(TEXT("inner_nodes"))) { const FString Guid=Inner->AsObject()->GetStringField(TEXT("guid")); TestFalse(TEXT("Repeated compound inner IDs are scoped"),InnerIds.Contains(Guid)); InnerIds.Add(Guid); }
  TestEqual(TEXT("Two native injected previews"),Injected,2); TestEqual(TEXT("Native source subtree remains unchanged"),BehaviorTreeGraphUtils::Inspect(Child->GetPathName()),Source);
  FBehaviorTreeGraphReq R; R.NodeGuid=Call; R.bSetSubtree=true; R.SubtreePath=Parent->GetPathName(); const FString Before=BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()); bool Rejected=false;
  try { Control(Parent,R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Self reference rejects"),Rejected); TestEqual(TEXT("Cycle rejection preserves parent"),BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()),Before);
  R.SubtreePath.Empty(); Control(Parent,R,TEXT("update_node")); TestTrue(TEXT("Undo reference clear"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores subtree asset"),CastChecked<UBTTask_RunBehavior>(Parent->RootNode->Children[0].ChildTask)->GetSubtreeAsset(),Child);
  TestTrue(TEXT("Redo reference clear"),GEditor->RedoTransaction());
  TestTrue(TEXT("Redo clear retains a readable graph"),Parse(BehaviorTreeGraphUtils::Inspect(Parent->GetPathName())).IsValid());
  TestTrue(TEXT("Restore reference after redo"),GEditor->UndoTransaction());
  TestTrue(TEXT("Restored parent validates after redo cycle"),Parse(BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()))->GetBoolField(TEXT("valid")));
  FBehaviorTreeGraphReq Compile; Control(Parent,Compile,TEXT("compile")); TestEqual(TEXT("Repeated native injection preserves source"),BehaviorTreeGraphUtils::Inspect(Child->GetPathName()),Source);
  auto Execute=[&](bool Gate)
  {
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; W->CreateAISystem(); auto* C=W->SpawnActor<AAIController>(); UBlackboardComponent* BB=nullptr;
   if(!TestTrue(TEXT("Native subtree Blackboard initializes"),C->UseBlackboard(Board,BB))) return;
   if(!BB->HasBeenInitialized()) BB->InitializeComponent(); BB->SetValueAsBool(TEXT("Gate"),Gate);
   auto* BT=NewObject<UBehaviorTreeComponent>(C); C->BrainComponent=BT; BT->RegisterComponent(); if(!BT->HasBeenInitialized()) BT->InitializeComponent(); ON_SCOPE_EXIT { BT->StopTree(EBTStopMode::Forced); BT->Cleanup(); };
   BT->StartTree(*Parent,EBTExecutionMode::SingleRun); for(int32 I=0;I<128 && BT->IsRunning();++I) BT->TickComponent(.01f,LEVELTICK_All,nullptr);
   TestFalse(TEXT("Native nested execution terminates"),BT->IsRunning()); TestEqual(TEXT("Child marker follows injected root gate"),BB->GetValueAsBool(TEXT("Done")),Gate); TestEqual(TEXT("Parent continuation follows child result"),BB->GetValueAsBool(TEXT("After")),Gate);
  };
  Execute(false); Execute(true); return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
