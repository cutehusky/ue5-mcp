#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeEditorData.h"
#include "StateTreeState.h"
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeLinkedTest,"UE5MCP.StateTree.LinkedSubtree",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeLinkedTest::RunTest(const FString&)
{
 UStateTree* T=nullptr; ON_SCOPE_EXIT { if(T) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 auto Control=[&](FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Link_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto Created=Control(R,TEXT("create")); T=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path"))); if(!TestNotNull(TEXT("Native StateTree"),T)) return false;
  const FString Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  auto Worker=[&](const TCHAR* Name,const TCHAR* Duration) { R={}; R.Name=Name; R.StateType=TEXT("Subtree"); const auto Subtree=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R={}; R.StateId=Subtree; R.Name=TEXT("Duration"); R.ParameterType=TEXT("Float"); R.bSetValue=true; R.Value=Duration; const auto Field=Control(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id")); R={}; R.ParentId=Subtree; R.Name=FString(Name)+TEXT(" task"); const auto Child=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); auto* D=CastChecked<UStateTreeEditorData>(T->EditorData); FGuid G; FGuid::Parse(Subtree,G); const auto Scope=D->GetStateByID(G)->Parameters.ID.ToString(EGuidFormats::DigitsWithHyphens); R={}; R.StateId=Child; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("RandomDeviation"),TEXT("0")}}; FStateTreeBindingReq B; B.SourceId=Scope; B.SourcePath=TEXT("Duration"); B.TargetId=TEXT("$new"); B.TargetPath=TEXT("Duration"); R.Bindings.Add(B); Control(R,TEXT("create_node")); R={}; R.StateId=Child; Control(R,TEXT("create_transition")); return TPair<FString,FString>(Subtree,Field); };
  const auto Fast=Worker(TEXT("Fast"),TEXT("0.03")); const auto Slow=Worker(TEXT("Slow"),TEXT("0.12"));
  R={}; R.ParentId=Root; R.Name=TEXT("Call"); R.StateType=TEXT("Linked"); R.TargetStateId=Fast.Key; const auto Call=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R={}; R.StateId=Call; Control(R,TEXT("create_transition"));
  auto Execute=[&](const TCHAR* WorkerName) { UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*T,Instance); TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner))); bool Saw=false; auto Observe=[&]() { for(const auto Name:Context.GetActiveStateNames()) Saw|=Name==FName(WorkerName); }; auto Status=Context.Start(); Observe(); int32 Ticks=0; for(;Ticks<128 && Status==EStateTreeRunStatus::Running;++Ticks) { Status=Context.Tick(.01f); Observe(); } TestTrue(TEXT("Native linked subtree executes"),Saw); TestTrue(TEXT("Native linked tree succeeds"),Status==EStateTreeRunStatus::Succeeded); Context.Stop(); return Ticks; };
  const int32 FastTicks=Execute(TEXT("Fast task"));
  R={}; R.StateId=Call; R.ItemId=Fast.Value; R.bSetValue=true; R.Value=TEXT("0.08"); Control(R,TEXT("update_parameter")); const int32 OverrideTicks=Execute(TEXT("Fast task")); TestTrue(TEXT("Linked parameter override changes runtime"),OverrideTicks>FastTicks); TestTrue(TEXT("Undo override"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores inherited runtime"),Execute(TEXT("Fast task")),FastTicks); TestTrue(TEXT("Redo override"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo restores override runtime"),Execute(TEXT("Fast task")),OverrideTicks);
  R={}; R.StateId=Fast.Key; R.Name=TEXT("Flag"); R.ParameterType=TEXT("Bool"); const auto Flag=Control(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  R.Name=TEXT("Count"); R.ParameterType=TEXT("Int32"); const auto Count=Control(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  for(int32 Index:{-1,0,1,0})
  {
   R={}; R.StateId=Fast.Key; R.ItemId=Fast.Value; R.Index=Index; Control(R,TEXT("move_parameter"));
   TestEqual(TEXT("Local linked binding offsets survive reorder"),Execute(TEXT("Fast task")),OverrideTicks);
   TestTrue(TEXT("Undo local parameter reorder"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo local caller execution"),Execute(TEXT("Fast task")),OverrideTicks);
   TestTrue(TEXT("Redo local parameter reorder"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo local caller execution"),Execute(TEXT("Fast task")),OverrideTicks);
  }
  for(const auto& Extra:{Count,Flag}) { R={}; R.StateId=Fast.Key; R.ItemId=Extra; R.bConfirm=true; Control(R,TEXT("delete_parameter")); }
  R={}; R.StateId=Call; R.ItemId=Fast.Value; R.bConfirm=true; Control(R,TEXT("reset_parameter")); TestEqual(TEXT("Native reset inherits default"),Execute(TEXT("Fast task")),FastTicks);
  R={}; R.StateId=Fast.Key; R.ItemId=Fast.Value; R.bSetValue=true; R.Value=TEXT("0.16"); Control(R,TEXT("update_parameter")); TestTrue(TEXT("Subtree default propagates to linked execution"),Execute(TEXT("Fast task"))>OverrideTicks); TestTrue(TEXT("Undo default"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo refreshes inherited runtime"),Execute(TEXT("Fast task")),FastTicks);
  R={}; R.StateId=Call; R.TargetStateId=Slow.Key; R.bConfirm=true; Control(R,TEXT("set_link")); const int32 SlowTicks=Execute(TEXT("Slow task")); TestTrue(TEXT("Retarget executes different native subtree"),SlowTicks>FastTicks); TestTrue(TEXT("Undo retarget"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores linked target runtime"),Execute(TEXT("Fast task")),FastTicks); TestTrue(TEXT("Redo retarget"),GEditor->RedoTransaction()); TestEqual(TEXT("Redo restores new target runtime"),Execute(TEXT("Slow task")),SlowTicks);
  R={}; R.ParentId=Slow.Key; R.Name=TEXT("Cross link"); R.StateType=TEXT("Linked"); R.TargetStateId=Fast.Key; const FString Cross=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  const FString BeforeCross=StateTreeUtils::Inspect(T->GetPathName()); bool CrossRejected=false; R={}; R.ParentId=Fast.Key; R.Name=TEXT("Cross cycle"); R.StateType=TEXT("Linked"); R.TargetStateId=Slow.Key; try { Control(R,TEXT("create_state")); } catch(const std::exception&) { CrossRejected=true; } TestTrue(TEXT("Mutually linked sibling subtrees reject"),CrossRejected); TestEqual(TEXT("Cross cycle preserves source"),StateTreeUtils::Inspect(T->GetPathName()),BeforeCross); R={}; R.StateId=Cross; R.bConfirm=true; Control(R,TEXT("delete_state"));
  const FString BeforeSelection=StateTreeUtils::Inspect(T->GetPathName()); R={}; R.StateId=Call; R.Properties={{TEXT("SelectionBehavior"),TEXT("TrySelectChildrenInOrder")}}; bool SelectionRejected=false; try { Control(R,TEXT("update_state")); } catch(const std::exception&) { SelectionRejected=true; } TestTrue(TEXT("Linked selection cannot be silently overridden by compiler"),SelectionRejected); TestEqual(TEXT("Rejected linked selection preserves source"),StateTreeUtils::Inspect(T->GetPathName()),BeforeSelection);
  const FString Before=StateTreeUtils::Inspect(T->GetPathName()); bool Rejected=false; R={}; R.ParentId=Slow.Key; R.Name=TEXT("Cycle"); R.StateType=TEXT("Linked"); R.TargetStateId=Slow.Key; try { Control(R,TEXT("create_state")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Native selection cycle guarded"),Rejected); TestEqual(TEXT("Cycle preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  R={}; R.StateId=Slow.Key; R.bConfirm=true; Rejected=false; try { Control(R,TEXT("delete_state")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Incoming linked reference protects subtree deletion"),Rejected); TestEqual(TEXT("Delete rejection preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  StateTreeUtils::Inspect(T->GetPathName(),true); TestEqual(TEXT("Linked validation preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before); return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
