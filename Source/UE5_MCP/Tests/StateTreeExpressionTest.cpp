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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeExpressionTest,"UE5MCP.StateTree.Expressions",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeExpressionTest::RunTest(const FString&)
{
 UStateTree* T=nullptr; ON_SCOPE_EXIT { if(T) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 auto Control=[&](FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Expr_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto Created=Control(R,TEXT("create")); T=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path")));
  const FString Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.ParentId=Root; R.Name=TEXT("A"); const auto A=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R.Name=TEXT("B"); const auto B=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  for(const auto& State:{A,B}) { R={}; R.StateId=State; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("Duration"),TEXT("0.02")},{TEXT("RandomDeviation"),TEXT("0")}}; Control(R,TEXT("create_node")); R={}; R.StateId=State; Control(R,TEXT("create_transition")); }
  R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeRandomCondition"); R.InstanceProperties={{TEXT("Threshold"),TEXT("0")}}; const auto First=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id")); R.InstanceProperties[TEXT("Threshold")]=TEXT("1"); const auto Condition=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  auto Execute=[&](bool ExpectA) { UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*T,Instance); TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner))); bool SawA=false,SawB=false; auto Observe=[&]() { for(auto Name:Context.GetActiveStateNames()) { SawA|=Name==TEXT("A"); SawB|=Name==TEXT("B"); } }; auto Status=Context.Start(); Observe(); for(int32 I=0;I<128 && Status==EStateTreeRunStatus::Running;++I) { Status=Context.Tick(.01f); Observe(); } TestTrue(TEXT("Native reference condition tree succeeds"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Object/class binding controls A selection"),SawA,ExpectA); TestEqual(TEXT("Object/class binding controls B fallback"),SawB,!ExpectA); Context.Stop(); };
  Execute(false); R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.ItemId=Condition; R.bSetExpression=true; R.Operand=TEXT("Or"); Control(R,TEXT("update_node")); Execute(true); TestTrue(TEXT("Undo expression operand"),GEditor->UndoTransaction()); Execute(false); TestTrue(TEXT("Redo expression operand"),GEditor->RedoTransaction()); Execute(true);
  R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.ItemId=First; R.InstanceProperties={{TEXT("Threshold"),TEXT("1")}}; Control(R,TEXT("update_node")); R.ItemId=Condition; R.InstanceProperties[TEXT("Threshold")]=TEXT("0"); Control(R,TEXT("update_node"));
  R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeRandomCondition"); R.InstanceProperties={{TEXT("Threshold"),TEXT("0")}}; const auto Third=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id")); Execute(false);
  R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.ItemId=Third; R.bSetExpression=true; R.Operand=TEXT("And"); R.ExpressionIndent=1; Control(R,TEXT("update_node")); Execute(true); TestTrue(TEXT("Undo nested grouping"),GEditor->UndoTransaction()); Execute(false); TestTrue(TEXT("Redo nested grouping"),GEditor->RedoTransaction()); Execute(true);
  const FString Before=StateTreeUtils::Inspect(T->GetPathName()); R.ExpressionIndent=5; bool Rejected=false; try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Expression depth guard"),Rejected); TestEqual(TEXT("Invalid expression preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before); R.ExpressionIndent=0; R.Operand=TEXT("Copy"); Rejected=false; try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Hidden Copy operand rejected"),Rejected); R.Operand=TEXT("Multiply"); Rejected=false; try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Multiply condition update rejects before runtime"),Rejected); TestEqual(TEXT("Multiply update preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before); R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeRandomCondition"); R.Operand=TEXT("Multiply"); Rejected=false; try { Control(R,TEXT("create_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Multiply condition creation rejects"),Rejected); StateTreeUtils::Inspect(T->GetPathName(),true); TestEqual(TEXT("Expression validation preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  auto* Data=CastChecked<UStateTreeEditorData>(T->EditorData);
  auto* NativeState=Data->SubTrees[0]->Children[0].Get();
  auto& NativeCondition=NativeState->EnterConditions[0];
  const auto OriginalOperand=NativeCondition.ExpressionOperand;
  NativeCondition.ExpressionOperand=EStateTreeExpressionOperand::Multiply;
  ON_SCOPE_EXIT { NativeCondition.ExpressionOperand=OriginalOperand; };
  for(bool Validate:{false,true})
  {
   bool MetadataRejected=false;
   try { StateTreeUtils::Inspect(T->GetPathName(),Validate); }
   catch(const std::exception&) { MetadataRejected=true; }
   TestTrue(TEXT("Existing Multiply condition metadata rejects inspection/validation"),MetadataRejected);
  }
  return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
