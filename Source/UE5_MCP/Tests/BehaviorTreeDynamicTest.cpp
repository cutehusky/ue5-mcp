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
#include "BehaviorTree/Tasks/BTTask_RunBehaviorDynamic.h"
#include "GameplayTagsManager.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AIController.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBehaviorTreeDynamicTest,"UE5MCP.BehaviorTree.Dynamic",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBehaviorTreeDynamicTest::RunTest(const FString&)
{
 const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 const FString TagName=TEXT("UE5MCP.Test.NativeDynamic.T")+Id;
 const FString TagDir=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("UE5MCP_Test")/(TEXT("Tags_")+Id));
 const FString TagFile=TagDir/TEXT("UE5MCP_NativeDynamic.ini"); IFileManager::Get().MakeDirectory(*TagDir,true);
 if(!FFileHelper::SaveStringToFile(TEXT("[/Script/GameplayTags.GameplayTagsList]\nGameplayTagList=(Tag=\"")+TagName+TEXT("\",DevComment=\"Temporary native test\")\n"),*TagFile)) { AddError(TEXT("Cannot create owned tag fixture")); return false; }
 UGameplayTagsManager::Get().AddTagIniSearchPath(TagDir);
 ON_SCOPE_EXIT { UGameplayTagsManager::Get().RemoveTagIniSearchPath(TagDir); IFileManager::Get().Delete(*TagFile); IFileManager::Get().DeleteDirectory(*TagDir); };
 const auto NativeTag=UGameplayTagsManager::Get().RequestGameplayTag(FName(*TagName),false);
 if(!TestTrue(TEXT("Owned test tag registered"),NativeTag.IsValid())) return false;
 TArray<UObject*> Assets; TArray<UPackage*> Packages;
 auto New=[&](UClass* C,const TCHAR* Prefix) { const FString Name=FString(Prefix)+Id; auto* P=CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)); Packages.Add(P); auto* O=NewObject<UObject>(P,C,*Name,RF_Public|RF_Standalone|RF_Transactional); Assets.Add(O); FAssetRegistryModule::AssetCreated(O); return O; };
 auto* Board=CastChecked<UBlackboardData>(New(UBlackboardData::StaticClass(),TEXT("BB_Subtree_")));
 auto* Child=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Child_")));
 auto* Alternative=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Alternative_")));
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
  const FString Wait=Create(Child,TEXT("BTTask_Wait"),-100,{{TEXT("WaitTime"),TEXT("(DefaultValue=0.5,Key=None)")},{TEXT("RandomDeviation"),TEXT("(DefaultValue=0,Key=None)")}},{ }); Connect(Child,ChildRoot,Wait);
  const FString Done=Create(Child,TEXT("BTTask_SetKeyValueBool"),100,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("Done")}}); Connect(Child,ChildRoot,Done);
  const FString AltRoot=Setup(Alternative);
  const FString After=Create(Alternative,TEXT("BTTask_SetKeyValueBool"),0,{{TEXT("Value"),TEXT("(DefaultValue=True,Key=None)")}},{{TEXT("BlackboardKey"),TEXT("After")}}); Connect(Alternative,AltRoot,After);
  const FString ParentRoot=Setup(Parent);
  FBehaviorTreeGraphReq R; R.ClassPath=TEXT("/Script/AIModule.BTTask_RunBehaviorDynamic"); R.bSetSubtree=true; R.SubtreePath=Child->GetPathName(); R.bSetInjectionTag=true; R.InjectionTag=TagName;
  const FString Call=Control(Parent,R,TEXT("create_node"))->GetStringField(TEXT("node_guid")); Connect(Parent,ParentRoot,Call);
  auto* Native=CastChecked<UBTTask_RunBehaviorDynamic>(Parent->RootNode->Children[0].ChildTask);
  TestEqual(TEXT("Native dynamic default reference"),Native->GetDefaultBehaviorAsset(),Child); TestTrue(TEXT("Native injection tag"),Native->GetInjectionTag()==NativeTag);
  R=FBehaviorTreeGraphReq(); R.NodeGuid=Call; R.bSetSubtree=true; R.SubtreePath=Alternative->GetPathName(); Control(Parent,R,TEXT("update_node"));
  TestEqual(TEXT("Alternative default assigned"),Native->GetDefaultBehaviorAsset(),Alternative);
  TestTrue(TEXT("Undo default replacement"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo default restored"),Native->GetDefaultBehaviorAsset(),Child);
  TestTrue(TEXT("Redo default replacement"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo default restored"),Native->GetDefaultBehaviorAsset(),Alternative); GEditor->UndoTransaction();
  const FString Before=BehaviorTreeGraphUtils::Inspect(Parent->GetPathName());
  R.SubtreePath=Parent->GetPathName(); bool Rejected=false; try { Control(Parent,R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Dynamic default self cycle rejects"),Rejected);
  R=FBehaviorTreeGraphReq(); R.NodeGuid=Call; R.bSetInjectionTag=true; R.InjectionTag=TEXT("UE5MCP.Unregistered.DoesNotExist"); Rejected=false; try { Control(Parent,R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Unregistered tag rejects"),Rejected);
  TestEqual(TEXT("Rejected changes preserve source"),BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()),Before);
  auto Execute=[&](int32 Mode)
  {
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; W->CreateAISystem(); auto* C=W->SpawnActor<AAIController>(); UBlackboardComponent* BB=nullptr;
   if(!TestTrue(TEXT("Native dynamic Blackboard initializes"),C->UseBlackboard(Board,BB))) return;
   if(!BB->HasBeenInitialized()) BB->InitializeComponent();
   auto* BT=NewObject<UBehaviorTreeComponent>(C); C->BrainComponent=BT; BT->RegisterComponent(); if(!BT->HasBeenInitialized()) BT->InitializeComponent(); ON_SCOPE_EXIT { BT->StopTree(EBTStopMode::Forced); BT->Cleanup(); };
   BT->StartTree(*Parent,EBTExecutionMode::SingleRun); for(int32 I=0;I<5 && BT->IsRunning();++I) BT->TickComponent(.01f,LEVELTICK_All,nullptr);
   TestTrue(TEXT("Default subtree is active before replacement"),BT->IsRunning());
   const auto Noop=Parse(BehaviorTreeGraphUtils::ReplaceDynamic(BT,TagName,Child->GetPathName())); TestFalse(TEXT("Live same-reference no-op"),Noop->GetBoolField(TEXT("applied")));
   const auto Dry=Parse(BehaviorTreeGraphUtils::ReplaceDynamic(BT,TagName,Alternative->GetPathName(),true)); TestFalse(TEXT("Live dry-run does not apply"),Dry->GetBoolField(TEXT("applied"))); TestEqual(TEXT("Dry-run finds one replacement"),int32(Dry->GetNumberField(TEXT("would_change_tasks"))),1);
   bool CycleRejected=false; try { BehaviorTreeGraphUtils::ReplaceDynamic(BT,TagName,Parent->GetPathName()); } catch(const std::exception&) { CycleRejected=true; } TestTrue(TEXT("Effective runtime cycle rejects"),CycleRejected);
   if(Mode==1) TestTrue(TEXT("Live replacement applies"),Parse(BehaviorTreeGraphUtils::ReplaceDynamic(BT,TagName,Alternative->GetPathName()))->GetBoolField(TEXT("applied")));
   if(Mode==2) TestTrue(TEXT("Live clear applies"),Parse(BehaviorTreeGraphUtils::ReplaceDynamic(BT,TagName,TEXT("")))->GetBoolField(TEXT("applied")));
   for(int32 I=0;I<128 && BT->IsRunning();++I) BT->TickComponent(.01f,LEVELTICK_All,nullptr);
   TestFalse(TEXT("Dynamic nested execution terminates"),BT->IsRunning()); TestEqual(TEXT("Default marker aborted by replacement"),BB->GetValueAsBool(TEXT("Done")),Mode==0); TestEqual(TEXT("Replacement marker executes"),BB->GetValueAsBool(TEXT("After")),Mode==1);
   TestEqual(TEXT("Runtime replacement preserves template default"),Native->GetDefaultBehaviorAsset(),Child);
  };
  Execute(0); Execute(1); Execute(2); return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
