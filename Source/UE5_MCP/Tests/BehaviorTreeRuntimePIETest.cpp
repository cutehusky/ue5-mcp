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
#include "Tests/AutomationEditorCommon.h"
#include "UE5_MCP/API/DTO/BehaviorTreeRuntimeReq.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

namespace
{
 struct FRuntimePIEFixture
 {
  TArray<UObject*> Assets; TArray<UPackage*> Packages; FString TagDir,TagFile;
  TWeakObjectPtr<UBehaviorTreeComponent> Component; TWeakObjectPtr<UBlackboardComponent> Blackboard;
  ~FRuntimePIEFixture()
  {
   if(!TagDir.IsEmpty()) UGameplayTagsManager::Get().RemoveTagIniSearchPath(TagDir);
   if(!TagFile.IsEmpty()) IFileManager::Get().Delete(*TagFile);
   if(!TagDir.IsEmpty()) IFileManager::Get().DeleteDirectory(*TagDir);
   for(auto* O:Assets) { FAssetRegistryModule::AssetDeleted(O); O->ClearFlags(RF_Public|RF_Standalone); O->MarkAsGarbage(); }
   for(auto* P:Packages) P->SetDirtyFlag(false);
  }
 };
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBehaviorTreeRuntimePIETest,"UE5MCP.BehaviorTree.RuntimePIE",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBehaviorTreeRuntimePIETest::RunTest(const FString&)
{
 if(!GEditor || GEditor->PlayWorld) { AddError(TEXT("Runtime PIE fixture requires an idle editor")); return false; }
 auto State=MakeShared<FRuntimePIEFixture>();
 const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 const FString TagName=TEXT("UE5MCP.Test.NativeDynamic.T")+Id;
 const FString TagDir=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("UE5MCP_Test")/(TEXT("Tags_")+Id));
 State->TagDir=TagDir;
 const FString TagFile=TagDir/TEXT("UE5MCP_NativeDynamic.ini"); State->TagFile=TagFile; IFileManager::Get().MakeDirectory(*TagDir,true);
 if(!FFileHelper::SaveStringToFile(TEXT("[/Script/GameplayTags.GameplayTagsList]\nGameplayTagList=(Tag=\"")+TagName+TEXT("\",DevComment=\"Temporary native test\")\n"),*TagFile)) { AddError(TEXT("Cannot create owned tag fixture")); return false; }
 UGameplayTagsManager::Get().AddTagIniSearchPath(TagDir);

 const auto NativeTag=UGameplayTagsManager::Get().RequestGameplayTag(FName(*TagName),false);
 if(!TestTrue(TEXT("Owned test tag registered"),NativeTag.IsValid())) return false;
 auto& Assets=State->Assets; auto& Packages=State->Packages;
 auto New=[&](UClass* C,const TCHAR* Prefix) { const FString Name=FString(Prefix)+Id; auto* P=CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)); Packages.Add(P); auto* O=NewObject<UObject>(P,C,*Name,RF_Public|RF_Standalone|RF_Transactional); Assets.Add(O); FAssetRegistryModule::AssetCreated(O); return O; };
 auto* Board=CastChecked<UBlackboardData>(New(UBlackboardData::StaticClass(),TEXT("BB_Subtree_")));
 auto* Child=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Child_")));
 auto* Alternative=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Alternative_")));
 auto* Parent=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Parent_")));

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
  auto* Decorated=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Decorated_"))); const FString DecoratedRoot=Setup(Decorated);
  auto DecoratedWait=Create(Decorated,TEXT("BTTask_Wait"),0,{ },{ }); Connect(Decorated,DecoratedRoot,DecoratedWait); Create(Decorated,TEXT("BTDecorator_Blackboard"),0,{ },{{TEXT("BlackboardKey"),TEXT("Gate")}},DecoratedRoot);
  auto* BadBoard=CastChecked<UBlackboardData>(New(UBlackboardData::StaticClass(),TEXT("BB_Bad_"))); FBlackboardKeyReq K; K.AssetPath=BadBoard->GetPathName(); K.KeyName=TEXT("Wrong"); K.KeyType=TEXT("/Script/AIModule.BlackboardKeyType_Bool"); BlackboardUtils::Control(K,TEXT("add"));
  auto* BadTree=CastChecked<UBehaviorTree>(New(UBehaviorTree::StaticClass(),TEXT("BT_Bad_"))); const FString BadRoot=Setup(BadTree); auto BadWait=Create(BadTree,TEXT("BTTask_Wait"),0,{ },{ }); Connect(BadTree,BadRoot,BadWait);
  FBehaviorTreeGraphReq BadSettings; BadSettings.BlackboardPath=BadBoard->GetPathName(); BadSettings.bConfirm=true; Control(BadTree,BadSettings,TEXT("set_blackboard"));
  bool NoPIERejected=false; try { BehaviorTreeGraphUtils::Runtime(TEXT(""),-1); } catch(const std::exception&) { NoPIERejected=true; } TestTrue(TEXT("Runtime inspect rejects editor-only context"),NoPIERejected);
  ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
  FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FFunctionLatentCommand>([this,State,Parent,Child,Alternative,Decorated,BadTree,Board,TagName,Before,Parse,Phase=0,Started=FPlatformTime::Seconds(),PhaseTime=0.0]() mutable
  {
   try
   {
    if(FPlatformTime::Seconds()-Started>30) { AddError(TEXT("Runtime PIE fixture timed out")); return true; }
    UWorld* W=GEditor ? GEditor->PlayWorld.Get() : nullptr; if(!W) return false;
    if(Phase==0)
    {
     auto* C=W->SpawnActor<AAIController>(); UBlackboardComponent* BB=nullptr;
     if(!C || !C->UseBlackboard(Board,BB)) { AddError(TEXT("PIE controller/Blackboard creation failed")); return true; }
     if(!BB->HasBeenInitialized()) BB->InitializeComponent();
     auto* BT=NewObject<UBehaviorTreeComponent>(C); C->BrainComponent=BT; BT->RegisterComponent(); if(!BT->HasBeenInitialized()) BT->InitializeComponent(); State->Component=BT; State->Blackboard=BB;
     BT->StartTree(*Parent,EBTExecutionMode::SingleRun); Phase=1; PhaseTime=FPlatformTime::Seconds(); return false;
    }
    auto* BT=State->Component.Get(); auto* BB=State->Blackboard.Get(); if(!BT || !BB) { AddError(TEXT("Owned PIE runtime components disappeared")); return true; }
    if(Phase==1)
    {
     if(BT->GetCurrentTree()!=Child || FPlatformTime::Seconds()-PhaseTime<0.05) return false;
     auto Snapshot=Parse(BehaviorTreeGraphUtils::Runtime(BT->GetPathName(),-1)); TestEqual(TEXT("Explicit PIE component inspection"),Snapshot->GetArrayField(TEXT("components")).Num(),1);
     auto C=Snapshot->GetArrayField(TEXT("components"))[0]->AsObject(); TestTrue(TEXT("PIE controller has authority"),C->GetBoolField(TEXT("authority"))); TestEqual(TEXT("One instantiated tagged task"),C->GetArrayField(TEXT("dynamic_tasks")).Num(),1);
     FBehaviorTreeRuntimeReq Request; Request.ComponentPath=BT->GetPathName(); Request.InjectionTag=TagName; Request.AssetPath=Alternative->GetPathName(); Request.bDryRun=true;
     auto Dry=Parse(BehaviorTreeGraphUtils::RuntimeControl(Request)); TestFalse(TEXT("PIE dry-run does not apply"),Dry->GetBoolField(TEXT("applied"))); TestEqual(TEXT("PIE dry-run finds replacement"),int32(Dry->GetNumberField(TEXT("would_change_tasks"))),1);
     auto Bad=Request; Bad.PIEInstance=999999; bool Rejected=false; try { BehaviorTreeGraphUtils::RuntimeControl(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Wrong PIE instance rejects"),Rejected);
     Bad=Request; Bad.ComponentPath=Parent->GetPathName(); Rejected=false; try { BehaviorTreeGraphUtils::RuntimeControl(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Asset paths cannot target runtime components"),Rejected);
     Bad=Request; Bad.AssetPath=Decorated->GetPathName(); Rejected=false; try { BehaviorTreeGraphUtils::RuntimeControl(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Ignored candidate root decorators reject"),Rejected);
     Bad=Request; Bad.AssetPath=BadTree->GetPathName(); Rejected=false; try { BehaviorTreeGraphUtils::RuntimeControl(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Live Blackboard mismatch rejects"),Rejected);
     Bad=Request; Bad.InjectionTag=TEXT("UE5MCP.Test.NativeDynamic"); Rejected=false; try { BehaviorTreeGraphUtils::RuntimeControl(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Registered parent tag does not match exact task tag"),Rejected);
     BT->PauseLogic(TEXT("Runtime guard test")); Rejected=false; try { BehaviorTreeGraphUtils::RuntimeControl(Request); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Paused runtime component rejects"),Rejected); BT->ResumeLogic(TEXT("Runtime guard test"));
     Request.bDryRun=false; TestTrue(TEXT("PIE native replacement submitted"),Parse(BehaviorTreeGraphUtils::RuntimeControl(Request))->GetBoolField(TEXT("applied"))); auto Noop=Parse(BehaviorTreeGraphUtils::RuntimeControl(Request)); TestFalse(TEXT("PIE repeated replacement is a no-op"),Noop->GetBoolField(TEXT("applied"))); Phase=2; return false;
    }
    if(Phase==2)
    {
     if(BT->IsRunning()) return false;
     TestFalse(TEXT("PIE replacement aborts default marker"),BB->GetValueAsBool(TEXT("Done"))); TestTrue(TEXT("PIE replacement executes new marker"),BB->GetValueAsBool(TEXT("After")));
     TestEqual(TEXT("PIE runtime mutation preserves authored source"),BehaviorTreeGraphUtils::Inspect(Parent->GetPathName()),Before);
     BB->SetValueAsBool(TEXT("Done"),false); BB->SetValueAsBool(TEXT("After"),false); BT->StartTree(*Parent,EBTExecutionMode::SingleRun); Phase=3; PhaseTime=FPlatformTime::Seconds(); return false;
    }
    if(Phase==3)
    {
     if(BT->GetCurrentTree()!=Child || FPlatformTime::Seconds()-PhaseTime<0.05) return false;
     FBehaviorTreeRuntimeReq Request; Request.ComponentPath=BT->GetPathName(); Request.InjectionTag=TagName;
     TestTrue(TEXT("PIE active subtree clear submitted"),Parse(BehaviorTreeGraphUtils::RuntimeControl(Request))->GetBoolField(TEXT("applied"))); Phase=4; return false;
    }
    if(BT->IsRunning()) return false;
    TestFalse(TEXT("Cleared branch does not execute default marker"),BB->GetValueAsBool(TEXT("Done"))); TestFalse(TEXT("Cleared branch does not execute replacement marker"),BB->GetValueAsBool(TEXT("After"))); return true;
   }
   catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return true; }
  }));
  ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
  FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FFunctionLatentCommand>([this,State,Started=FPlatformTime::Seconds()]() { if(GEditor && GEditor->PlayWorld) { if(FPlatformTime::Seconds()-Started<60) return false; AddError(TEXT("Owned PIE session did not stop")); } return true; }));
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
