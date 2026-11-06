#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeAssetLinkTest,"UE5MCP.StateTree.LinkedAssets",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeAssetLinkTest::RunTest(const FString&)
{
 TArray<UStateTree*> Trees; ON_SCOPE_EXIT { for(auto* T:Trees) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 auto Control=[&](UStateTree* T,FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 auto Create=[&](const TCHAR* Name) { FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Assets_")+FString(Name)+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto J=Control(nullptr,R,TEXT("create")); auto* T=LoadObject<UStateTree>(nullptr,*J->GetStringField(TEXT("asset_path"))); Trees.Add(T); return T; };
 auto Root=[&](UStateTree* T) { return Parse(StateTreeUtils::Inspect(T->GetPathName()))->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id")); };
 try
 {
  auto* C=Create(TEXT("Leaf")); auto* B=Create(TEXT("Middle")); auto* A=Create(TEXT("Caller"));
  FStateTreeReq R; R.Name=TEXT("Duration"); R.ParameterType=TEXT("Float"); R.bSetValue=true; R.Value=TEXT("0.03"); const auto Field=Control(C,R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  R={}; R.ParentId=Root(C); R.Name=TEXT("Leaf task"); const auto Work=Control(C,R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R={}; R.StateId=Work; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("RandomDeviation"),TEXT("0")}}; FStateTreeBindingReq Binding; Binding.SourceId=TEXT("root"); Binding.SourcePath=TEXT("Duration"); Binding.TargetId=TEXT("$new"); Binding.TargetPath=TEXT("Duration"); R.Bindings.Add(Binding); Control(C,R,TEXT("create_node")); R={}; R.StateId=Work; Control(C,R,TEXT("create_transition"));
  auto Link=[&](UStateTree* Parent,UStateTree* Child) { R={}; R.ParentId=Root(Parent); R.Name=TEXT("Call"); R.StateType=TEXT("LinkedAsset"); R.LinkedAssetPath=Child->GetPathName(); const auto ID=Control(Parent,R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R={}; R.StateId=ID; Control(Parent,R,TEXT("create_transition")); return ID; };
  const auto MiddleCall=Link(B,C); Link(A,B);
  auto Execute=[&](const TCHAR* Expected=TEXT("Leaf task")) { UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*A,Instance); TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner))); bool Saw=false; auto Observe=[&]() { for(auto Name:Context.GetActiveStateNames()) Saw|=Name==FName(Expected); }; auto Status=Context.Start(); Observe(); int32 Ticks=0; for(;Ticks<128 && Status==EStateTreeRunStatus::Running;++Ticks) { Status=Context.Tick(.01f); Observe(); } TestTrue(TEXT("Cross-asset leaf executes"),Saw); TestTrue(TEXT("Three native frames complete"),Status==EStateTreeRunStatus::Succeeded); Context.Stop(); return Ticks; };
  const int32 BeforeTicks=Execute();
  auto Snapshot=[&]() { TArray<FString> S; for(auto* T:Trees) S.Add(StateTreeUtils::Inspect(T->GetPathName())); return S; };
  auto Before=Snapshot(); R={}; R.ItemId=Field; R.bSetValue=true; R.Value=TEXT("0.16"); R.bDryRun=true; Control(C,R,TEXT("update_parameter")); TestTrue(TEXT("Dry run preserves all three sources"),Snapshot()==Before); StateTreeUtils::Inspect(C->GetPathName(),true); TestTrue(TEXT("Read-only dependency validation preserves sources"),Snapshot()==Before);
  R.bDryRun=false; const auto Changed=Control(C,R,TEXT("update_parameter")); TestEqual(TEXT("Source edit captures transitive callers"),Changed->GetArrayField(TEXT("affected_assets")).Num(),3); const int32 LongTicks=Execute(); TestTrue(TEXT("Default propagates through native frames"),LongTicks>BeforeTicks); TestTrue(TEXT("Undo source and callers"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores cross-asset runtime"),Execute(),BeforeTicks); TestTrue(TEXT("Redo source and callers"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo restores cross-asset runtime"),Execute(),LongTicks);
  R={}; R.StateId=MiddleCall; R.ItemId=Field; R.bSetValue=true; R.Value=TEXT("0.06"); const auto LeafBefore=StateTreeUtils::Inspect(C->GetPathName()); Control(B,R,TEXT("update_parameter")); const int32 OverrideTicks=Execute(); TestTrue(TEXT("Linked asset override drives leaf"),OverrideTicks<LongTicks && OverrideTicks>BeforeTicks); TestEqual(TEXT("Caller override preserves leaf source"),StateTreeUtils::Inspect(C->GetPathName()),LeafBefore);
  R={}; R.Name=TEXT("Flag"); R.ParameterType=TEXT("Bool"); R.bSetValue=true; R.Value=TEXT("True"); const auto Flag=Control(C,R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  R.Name=TEXT("Count"); R.ParameterType=TEXT("Int32"); R.Value=TEXT("7"); const auto Count=Control(C,R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  for(int32 Index:{-1,0,1,0})
  {
   R={}; R.ItemId=Field; R.Index=Index; const auto Moved=Control(C,R,TEXT("move_parameter"));
   const auto& Fields=Moved->GetObjectField(TEXT("parameters"))->GetArrayField(TEXT("fields"));
   TestEqual(TEXT("Native root parameter final position"),Fields[Index==-1 ? 2 : Index]->AsObject()->GetStringField(TEXT("id")),Field);
   TestEqual(TEXT("Reordered source retains cross-asset binding/override execution"),Execute(),OverrideTicks);
   TestTrue(TEXT("Undo cross-asset parameter reorder"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo reordered caller execution"),Execute(),OverrideTicks);
   TestTrue(TEXT("Redo cross-asset parameter reorder"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo reordered caller execution"),Execute(),OverrideTicks);
  }
  for(const auto& Extra:{Count,Flag}) { R={}; R.ItemId=Extra; R.bConfirm=true; Control(C,R,TEXT("delete_parameter")); }
  R={}; R.ItemId=Field; R.ParameterType=TEXT("Double"); R.bConfirm=true; Control(C,R,TEXT("replace_parameter"));
  TestEqual(TEXT("Numeric type migration preserves cross-asset runtime and override"),Execute(),OverrideTicks);
  TestTrue(TEXT("Undo numeric parameter replacement"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo type replacement runtime"),Execute(),OverrideTicks);
  TestTrue(TEXT("Redo numeric parameter replacement"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo type replacement runtime"),Execute(),OverrideTicks);
  const auto BeforeIncompatibleType=StateTreeUtils::Inspect(C->GetPathName()); R.ParameterType=TEXT("String"); R.bSetValue=true; R.Value=TEXT("incompatible"); bool IncompatibleTypeRejected=false;
  try { Control(C,R,TEXT("replace_parameter")); } catch(const std::exception&) { IncompatibleTypeRejected=true; }
  TestTrue(TEXT("Incompatible bound parameter replacement rejects"),IncompatibleTypeRejected);
  TestEqual(TEXT("Incompatible replacement preserves native source"),StateTreeUtils::Inspect(C->GetPathName()),BeforeIncompatibleType);
  TestEqual(TEXT("Rejected replacement preserves caller runtime"),Execute(),OverrideTicks);
  R={}; R.ItemId=Field; R.bSetName=true; R.Name=TEXT("WaitSeconds"); Control(C,R,TEXT("update_parameter")); TestEqual(TEXT("Rename keeps overridden native runtime"),Execute(),OverrideTicks);
  R={}; R.StateId=MiddleCall; R.ItemId=Field; R.bConfirm=true; Control(B,R,TEXT("reset_parameter")); TestEqual(TEXT("Reset linked asset override inherits source"),Execute(),LongTicks); TestTrue(TEXT("Undo reset"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores linked asset override"),Execute(),OverrideTicks);
  auto* Alternate=Create(TEXT("Alternate")); R={}; R.ParentId=Root(Alternate); R.Name=TEXT("Alternate task"); const auto AlternateWork=Control(Alternate,R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R={}; R.StateId=AlternateWork; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("Duration"),TEXT("0.28")},{TEXT("RandomDeviation"),TEXT("0")}}; Control(Alternate,R,TEXT("create_node")); R={}; R.StateId=AlternateWork; Control(Alternate,R,TEXT("create_transition"));
  R={}; R.StateId=MiddleCall; R.LinkedAssetPath=Alternate->GetPathName(); R.bConfirm=true; Control(B,R,TEXT("set_link")); const int32 AlternateTicks=Execute(TEXT("Alternate task")); TestTrue(TEXT("External retarget runs a different native task"),AlternateTicks>LongTicks); TestTrue(TEXT("Undo external retarget"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores external target and override runtime"),Execute(),OverrideTicks); TestTrue(TEXT("Redo external retarget"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo executes alternate external target"),Execute(TEXT("Alternate task")),AlternateTicks); GEditor->UndoTransaction();
  Before=Snapshot(); R={}; R.ParentId=Root(C); R.Name=TEXT("Cycle"); R.StateType=TEXT("LinkedAsset"); R.LinkedAssetPath=A->GetPathName(); bool Rejected=false; try { Control(C,R,TEXT("create_state")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Transitive asset cycle rejects"),Rejected); TestTrue(TEXT("Cycle preserves every source"),Snapshot()==Before);
  R.LinkedAssetPath=C->GetPathName(); Rejected=false; try { Control(C,R,TEXT("create_state")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Self-linked asset rejects"),Rejected); TestTrue(TEXT("Self-cycle preserves sources"),Snapshot()==Before);
  return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
