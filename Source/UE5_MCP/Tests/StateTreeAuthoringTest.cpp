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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeAuthoringTest,"UE5MCP.StateTree.Authoring",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeAuthoringTest::RunTest(const FString&)
{
 UStateTree* T=nullptr; ON_SCOPE_EXIT { if(T) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 auto Control=[&](FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto Created=Control(R,TEXT("create")); T=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path"))); if(!TestNotNull(TEXT("Native StateTree created"),T)) return false;
  const FString Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.ParentId=Root; R.Name=TEXT("A"); const FString A=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R.Name=TEXT("B"); const FString B=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=A; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("Duration"),TEXT("0.03")},{TEXT("RandomDeviation"),TEXT("0")}}; const FString Task=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id")); R.StateId=B; R.InstanceProperties[TEXT("Duration")]=TEXT("0.02"); Control(R,TEXT("create_node"));
  R={}; R.StateId=A; R.TargetType=TEXT("GotoState"); R.TargetStateId=B; Control(R,TEXT("create_transition")); R.StateId=B; R.TargetType=TEXT("Succeeded"); R.TargetStateId.Empty(); Control(R,TEXT("create_transition"));
  auto Execute=[&](bool ExpectA)
  {
   UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; auto* Owner=W->SpawnActor<AActor>();
   FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*T,Instance); TestTrue(TEXT("Native actor context set"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner)));
   bool SawA=false,SawB=false; auto Observe=[&]() { for(const auto Name:Context.GetActiveStateNames()) { SawA|=Name==TEXT("A"); SawB|=Name==TEXT("B"); } };
   auto Status=Context.Start(); Observe(); int32 Ticks=0; for(;Ticks<128 && Status==EStateTreeRunStatus::Running;++Ticks) { Status=Context.Tick(.01f); Observe(); }
   TestTrue(TEXT("Native state machine reaches success"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Enter condition controls A selection"),SawA,ExpectA); TestTrue(TEXT("Native transition reaches B"),SawB); Context.Stop(); return Ticks;
  };
  const int32 BeforeTicks=Execute(true);
  R={}; R.StateId=A; R.ItemId=Task; R.InstanceProperties.Add(TEXT("Duration"),TEXT("0.12")); Control(R,TEXT("update_node")); TestTrue(TEXT("Native edited duration changes execution"),Execute(true)>BeforeTicks);
  TestTrue(TEXT("Undo task edit"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores native duration behavior"),Execute(true),BeforeTicks); TestTrue(TEXT("Redo task edit"),GEditor->RedoTransaction()); TestTrue(TEXT("Redo restores edited runtime behavior"),Execute(true)>BeforeTicks); GEditor->UndoTransaction();
  R={}; R.Name=TEXT("Flag"); R.ParameterType=TEXT("Bool"); R.bSetValue=true; R.Value=TEXT("False"); const FString Flag=Control(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=A; R.Name=TEXT("Match"); R.ParameterType=TEXT("Bool"); R.bSetValue=true; R.Value=TEXT("False"); Control(R,TEXT("create_parameter"));
  auto* EditorData=CastChecked<UStateTreeEditorData>(T->EditorData); UStateTreeState* StateA=nullptr; for(UStateTreeState* Child:EditorData->SubTrees[0]->Children) if(Child->Name==TEXT("A")) StateA=Child; if(!TestNotNull(TEXT("State A"),StateA)) return false;
  R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeCompareBoolCondition"); R.InstanceProperties={{TEXT("bRight"),TEXT("False")}};
  FStateTreeBindingReq Left; Left.SourceId=TEXT("root"); Left.SourcePath=TEXT("Flag"); Left.TargetId=TEXT("$new"); Left.TargetPath=TEXT("bLeft"); R.Bindings.Add(Left);
  FStateTreeBindingReq Right; Right.SourceId=StateA->Parameters.ID.ToString(EGuidFormats::DigitsWithHyphens); Right.SourcePath=TEXT("Match"); Right.TargetId=TEXT("$new"); Right.TargetPath=TEXT("bRight"); R.Bindings.Add(Right);
  const FString Condition=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id")); Execute(true);
  R={}; R.ItemId=Flag; R.bSetValue=true; R.Value=TEXT("True"); Control(R,TEXT("update_parameter")); Execute(false); TestTrue(TEXT("Undo bound parameter edit"),GEditor->UndoTransaction()); Execute(true); TestTrue(TEXT("Redo bound parameter edit"),GEditor->RedoTransaction()); Execute(false); GEditor->UndoTransaction();
  R={}; R.ItemId=Flag; R.bSetName=true; R.Name=TEXT("RenamedFlag"); Control(R,TEXT("update_parameter")); Execute(true);
  TestEqual(TEXT("Rename preserves native parameter field ID"),EditorData->GetRootParametersPropertyBag().FindPropertyDescByName(TEXT("RenamedFlag"))->ID.ToString(EGuidFormats::DigitsWithHyphens),Flag);
  bool FoundRenamed=false; for(const auto& Binding:EditorData->EditorBindings.GetBindings()) FoundRenamed|=Binding.GetSourcePath().ToString()==TEXT("RenamedFlag"); TestTrue(TEXT("Native binding redirects follow parameter rename"),FoundRenamed);
  TestTrue(TEXT("Undo bound parameter rename"),GEditor->UndoTransaction()); Execute(true); TestTrue(TEXT("Redo bound parameter rename"),GEditor->RedoTransaction()); Execute(true);
  R={}; R.ItemId=Flag; R.bConfirm=true; bool BoundDeleteRejected=false; try { Control(R,TEXT("delete_parameter")); } catch(const std::exception&) { BoundDeleteRejected=true; } TestTrue(TEXT("Bound parameter deletion rejects"),BoundDeleteRejected);
  R={}; R.StateId=A; R.ItemId=Condition; R.Kind=TEXT("enter_condition"); R.bConfirm=true; Control(R,TEXT("delete_node")); TestEqual(TEXT("Deleting node removes its incoming bindings"),EditorData->EditorBindings.GetNumBindings(),0); TestTrue(TEXT("Undo bound node deletion"),GEditor->UndoTransaction()); TestEqual(TEXT("Undo restores incoming bindings"),EditorData->EditorBindings.GetNumBindings(),2); Execute(true);
  const FString Before=StateTreeUtils::Inspect(T->GetPathName()); auto Validated=Parse(StateTreeUtils::Inspect(T->GetPathName(),true)); TestTrue(TEXT("Validation compiles a transient copy"),Validated->GetBoolField(TEXT("validation_compiled_copy"))); TestEqual(TEXT("Validation preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  R={}; R.StateId=A; R.ItemId=Task; R.InstanceProperties.Add(TEXT("Duration"),TEXT("-1")); bool Rejected=false; try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Native clamp preflight rejects negative duration"),Rejected); TestEqual(TEXT("Rejected edit preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  R={}; R.StateId=Root; R.ParentId=A; Rejected=false; try { Control(R,TEXT("move_state")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Hierarchy cycle rejects"),Rejected);
  R={}; R.StateId=B; R.bConfirm=true; Rejected=false; try { Control(R,TEXT("delete_state")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Incoming transition prevents dangling deletion"),Rejected);
  TestTrue(TEXT("Compiled data remains native ready"),T->IsReadyToRun()); return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif

