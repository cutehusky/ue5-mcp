#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeEditorData.h"
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeUtilityTest,"UE5MCP.StateTree.UtilityConsiderations",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeUtilityTest::RunTest(const FString&)
{
 UStateTree* T=nullptr; ON_SCOPE_EXIT { if(T) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 auto Control=[&](FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Utility_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto Created=Control(R,TEXT("create")); T=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path")));
  const FString Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.StateId=Root; R.Properties={{TEXT("SelectionBehavior"),TEXT("TrySelectChildrenWithHighestUtility")}}; Control(R,TEXT("update_state"));
  R={}; R.ParentId=Root; R.Name=TEXT("A"); const auto A=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R.Name=TEXT("B"); const auto B=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  for(const auto& State:{A,B}) { R={}; R.StateId=State; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("Duration"),TEXT("0.02")},{TEXT("RandomDeviation"),TEXT("0")}}; Control(R,TEXT("create_node")); R={}; R.StateId=State; Control(R,TEXT("create_transition")); }
  R={}; R.StateId=A; R.Kind=TEXT("consideration"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeConstantConsideration"); R.InstanceProperties={{TEXT("Constant"),TEXT("0.8")}}; const auto Score=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id")); R.StateId=B; R.InstanceProperties[TEXT("Constant")]=TEXT("0.4"); Control(R,TEXT("create_node"));
  auto Execute=[&](bool ExpectA) { UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*T,Instance); TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner))); bool SawA=false,SawB=false; auto Observe=[&]() { for(auto Name:Context.GetActiveStateNames()) { SawA|=Name==TEXT("A"); SawB|=Name==TEXT("B"); } }; auto Status=Context.Start(); Observe(); for(int32 I=0;I<128 && Status==EStateTreeRunStatus::Running;++I) { Status=Context.Tick(.01f); Observe(); } TestTrue(TEXT("Native reference condition tree succeeds"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Object/class binding controls A selection"),SawA,ExpectA); TestEqual(TEXT("Object/class binding controls B fallback"),SawB,!ExpectA); Context.Stop(); };
  Execute(true); R={}; R.StateId=A; R.Kind=TEXT("consideration"); R.ItemId=Score; R.InstanceProperties={{TEXT("Constant"),TEXT("0.1")}}; Control(R,TEXT("update_node")); Execute(false); TestTrue(TEXT("Undo native utility edit"),GEditor->UndoTransaction()); Execute(true); TestTrue(TEXT("Redo native utility edit"),GEditor->RedoTransaction()); Execute(false);
  GEditor->UndoTransaction(); Execute(true); R={}; R.StateId=A; R.Kind=TEXT("consideration"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeConstantConsideration"); R.InstanceProperties={{TEXT("Constant"),TEXT("0.25")}}; R.Operand=TEXT("Multiply"); const auto Multiplier=Control(R,TEXT("create_node"))->GetStringField(TEXT("selected_id")); Execute(false); TestTrue(TEXT("Undo utility multiplication"),GEditor->UndoTransaction()); Execute(true); TestTrue(TEXT("Redo utility multiplication"),GEditor->RedoTransaction()); Execute(false); GEditor->UndoTransaction(); R={}; R.StateId=A; R.Kind=TEXT("consideration"); R.ItemId=Score; R.InstanceProperties={{TEXT("Constant"),TEXT("0.1")}}; Control(R,TEXT("update_node"));
  const FString Before=StateTreeUtils::Inspect(T->GetPathName()); R.InstanceProperties[TEXT("Constant")]=TEXT("2"); bool Rejected=false; try { Control(R,TEXT("update_node")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Utility native clamp enforced"),Rejected); TestEqual(TEXT("Invalid utility preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  R={}; R.StateId=A; R.Kind=TEXT("consideration"); R.ItemId=Score; R.bConfirm=true; Control(R,TEXT("delete_node")); TestTrue(TEXT("Undo consideration deletion"),GEditor->UndoTransaction()); Execute(false); StateTreeUtils::Inspect(T->GetPathName(),true); TestEqual(TEXT("Utility validation preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before); return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
