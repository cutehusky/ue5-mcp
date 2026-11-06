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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBehaviorTreeCompoundTest,"UE5MCP.BehaviorTree.Compound",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBehaviorTreeCompoundTest::RunTest(const FString&)
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
  for(const TCHAR* Name:{TEXT("A"),TEXT("B"),TEXT("C"),TEXT("Done")}) { FBlackboardKeyReq K; K.AssetPath=Board->GetPathName(); K.KeyName=Name; K.KeyType=TEXT("/Script/AIModule.BlackboardKeyType_Bool"); BlackboardUtils::Control(K,TEXT("add")); }
  auto Setup=[&](UBehaviorTree* T) { FBehaviorTreeGraphReq R; auto Root=Control(T,R,TEXT("initialize"))->GetStringField(TEXT("root_guid")); R.BlackboardPath=Board->GetPathName(); R.bConfirm=true; Control(T,R,TEXT("set_blackboard")); auto Seq=Create(T,TEXT("BTComposite_Sequence"),0,{ },{ }); Connect(T,Root,Seq); return Seq; };
  const FString Seq=Setup(Parent);
  const FString Marker=Create(Parent,TEXT("BTTask_SetKeyValueBool"),0,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("Done")}}); Connect(Parent,Seq,Marker);
  auto TestRow=[](const TCHAR* Key) { FBehaviorTreeLogicRow V; V.Operation=TEXT("test"); V.ClassPath=TEXT("/Script/AIModule.BTDecorator_Blackboard"); V.BlackboardSelectors.Add(TEXT("BlackboardKey"),Key); return V; };
  auto LogicRow=[](const TCHAR* Op,int32 Count) { FBehaviorTreeLogicRow V; V.Operation=Op; V.Children=Count; return V; };
  FBehaviorTreeGraphReq R; R.ParentGuid=Marker; R.bSetCompoundName=true; R.CompoundName=TEXT("Truth table");
  R.Logic={LogicRow(TEXT("or"),2),LogicRow(TEXT("and"),2),TestRow(TEXT("A")),TestRow(TEXT("B")),LogicRow(TEXT("not"),1),TestRow(TEXT("C"))};
  const FString Group=Control(Parent,R,TEXT("create_compound"))->GetStringField(TEXT("node_guid"));
  TestEqual(TEXT("Three native decorators"),Parent->RootNode->Children[0].Decorators.Num(),3);
  TestEqual(TEXT("Six native prefix operations"),Parent->RootNode->Children[0].DecoratorOps.Num(),6);
  const FString Before=BehaviorTreeGraphUtils::Inspect(Parent->GetPathName());
  R.NodeGuid=Group;
  TestFalse(TEXT("Equivalent replacement is a no-op"),Control(Parent,R,TEXT("replace_compound"))->GetBoolField(TEXT("would_change")));
  R.Logic.Add(TestRow(TEXT("A"))); bool Rejected=false;
  try { Control(Parent,R,TEXT("replace_compound")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Trailing operands reject"),Rejected); TestEqual(TEXT("Invalid expression preserves graph"),BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()),Before); R.Logic.Pop();
  auto Execute=[&](int32 Bits)
  {
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; W->CreateAISystem(); auto* C=W->SpawnActor<AAIController>(); UBlackboardComponent* BB=nullptr;
   if(!TestTrue(TEXT("Native Blackboard initializes"),C->UseBlackboard(Board,BB))) return;
   if(!BB->HasBeenInitialized()) BB->InitializeComponent(); BB->SetValueAsBool(TEXT("A"),Bits&1); BB->SetValueAsBool(TEXT("B"),Bits&2); BB->SetValueAsBool(TEXT("C"),Bits&4);
   auto* BT=NewObject<UBehaviorTreeComponent>(C); C->BrainComponent=BT; BT->RegisterComponent(); if(!BT->HasBeenInitialized()) BT->InitializeComponent(); ON_SCOPE_EXIT { BT->StopTree(EBTStopMode::Forced); BT->Cleanup(); };
   BT->StartTree(*Parent,EBTExecutionMode::SingleRun); for(int32 I=0;I<128 && BT->IsRunning();++I) BT->TickComponent(.01f,LEVELTICK_All,nullptr);
   TestFalse(TEXT("Native compound execution terminates"),BT->IsRunning()); TestEqual(TEXT("OR(AND(A,B),NOT(C)) truth table"),BB->GetValueAsBool(TEXT("Done")),bool(((Bits&1)&&(Bits&2))||!(Bits&4)));
  };
  for(int32 Bits=0;Bits<8;++Bits) Execute(Bits);
  R.Logic={LogicRow(TEXT("and"),2),TestRow(TEXT("A")),TestRow(TEXT("B"))}; Control(Parent,R,TEXT("replace_compound"));
  TestEqual(TEXT("Replacement compiles two tests"),Parent->RootNode->Children[0].Decorators.Num(),2);
  TestTrue(TEXT("Undo replacement"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores three tests"),Parent->RootNode->Children[0].Decorators.Num(),3);
  TestTrue(TEXT("Undo graph validates"),Parse(BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()))->GetBoolField(TEXT("valid")));
  TestTrue(TEXT("Redo replacement"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo restores two tests"),Parent->RootNode->Children[0].Decorators.Num(),2);
  TestTrue(TEXT("Redo graph validates"),Parse(BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()))->GetBoolField(TEXT("valid")));
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
