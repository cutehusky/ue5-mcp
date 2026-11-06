#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/BlackboardUtils.h"
#include "UE5_MCP/API/DTO/BlackboardKeyReq.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/Tasks/BTTask_MoveTo.h"
#include "BehaviorTree/Composites/BTComposite_Sequence.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Vector.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Editor.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBlackboardAuthoringTest,"UE5MCP.Blackboard.SelectorRenameUndo",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBlackboardAuthoringTest::RunTest(const FString&)
{
 const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto* BP=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BB_Automation_")+Id));
 auto* TP=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BT_Automation_")+Id));
 auto* B=NewObject<UBlackboardData>(BP,*FString(TEXT("BB_Automation_")+Id),RF_Public|RF_Standalone|RF_Transactional);
 auto* T=NewObject<UBehaviorTree>(TP,*FString(TEXT("BT_Automation_")+Id),RF_Public|RF_Standalone|RF_Transactional);
 FAssetRegistryModule::AssetCreated(B); FAssetRegistryModule::AssetCreated(T);
 ON_SCOPE_EXIT
 {
  FAssetRegistryModule::AssetDeleted(T); FAssetRegistryModule::AssetDeleted(B);
  T->ClearFlags(RF_Public|RF_Standalone); B->ClearFlags(RF_Public|RF_Standalone);
  T->MarkAsGarbage(); B->MarkAsGarbage(); BP->SetDirtyFlag(false); TP->SetDirtyFlag(false);
 };
 try
 {
  FBlackboardKeyReq R; R.AssetPath=B->GetPathName(); R.KeyName=TEXT("Target"); R.KeyType=UBlackboardKeyType_Vector::StaticClass()->GetPathName();
  BlackboardUtils::Control(R,TEXT("add"));
  T->BlackboardAsset=B; T->RootNode=NewObject<UBTComposite_Sequence>(T,NAME_None,RF_Transactional);
  auto* Task=NewObject<UBTTask_MoveTo>(T,NAME_None,RF_Transactional);
  FBTCompositeChild Child; Child.ChildTask=Task; T->RootNode->Children.Add(Child);
  auto* Property=FindFProperty<FStructProperty>(Task->GetClass(),TEXT("BlackboardKey"));
  if(!TestNotNull(TEXT("Native MoveTo selector"),Property)) return false;
  auto* Selector=Property->ContainerPtrToValuePtr<FBlackboardKeySelector>(Task); Selector->SelectedKeyName=TEXT("Target"); Selector->ResolveSelectedKey(*B);
  R.KeyType.Empty(); R.NewKeyName=TEXT("Destination"); R.bDryRun=true;
  const FString Preview=BlackboardUtils::Control(R,TEXT("update"));
  TestTrue(TEXT("Preview reports selector object"),Preview.Contains(Task->GetPathName()));
  TestEqual(TEXT("Dry-run preserves selector"),Selector->SelectedKeyName,FName(TEXT("Target")));
  R.bDryRun=false; bool Rejected=false;
  try { BlackboardUtils::Control(R,TEXT("update")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Structural reference confirmation"),Rejected);
  R.bConfirm=true; BlackboardUtils::Control(R,TEXT("update"));
  TestEqual(TEXT("Renamed selector"),Selector->SelectedKeyName,FName(TEXT("Destination")));
  TestEqual(TEXT("Resolved native key ID"),Selector->GetSelectedKeyID(),B->GetKeyID(TEXT("Destination")));
  TestTrue(TEXT("Undo"),GEditor->UndoTransaction());
  TestEqual(TEXT("Undo selector"),Selector->SelectedKeyName,FName(TEXT("Target")));
  TestTrue(TEXT("Undo key"),B->GetKeyID(TEXT("Target"))!=FBlackboard::InvalidKey);
  TestTrue(TEXT("Redo"),GEditor->RedoTransaction());
  TestEqual(TEXT("Redo selector"),Selector->SelectedKeyName,FName(TEXT("Destination")));
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
