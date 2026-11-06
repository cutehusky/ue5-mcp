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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeReferenceTest,"UE5MCP.StateTree.ReferenceParameters",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeReferenceTest::RunTest(const FString&)
{
 UStateTree* T=nullptr; ON_SCOPE_EXIT { if(T) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 auto Control=[&](FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Refs_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto Created=Control(R,TEXT("create")); T=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path")));
  const FString Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  auto Parameter=[&](const TCHAR* Name,const TCHAR* Type,const TCHAR* Constraint,const TCHAR* Value) { R={}; R.Name=Name; R.ParameterType=Type; R.TypePath=Constraint; R.bSetValue=true; R.Value=Value; return Control(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id")); };
  const auto Resource=Parameter(TEXT("Resource"),TEXT("Object"),TEXT("/Script/Engine.Texture2D"),TEXT("/Engine/EngineResources/DefaultTexture.DefaultTexture"));
  const auto ResourceClass=Parameter(TEXT("ResourceClass"),TEXT("Class"),TEXT("/Script/CoreUObject.Object"),TEXT("/Script/Engine.Texture2D"));
  const auto Soft=Parameter(TEXT("SoftResource"),TEXT("SoftObject"),TEXT("/Script/Engine.Texture2D"),TEXT("/Engine/EngineResources/DefaultTexture.DefaultTexture")); Parameter(TEXT("SoftResourceClass"),TEXT("SoftClass"),TEXT("/Script/CoreUObject.Object"),TEXT("/Script/Engine.Texture2D"));
  auto* Data=CastChecked<UStateTreeEditorData>(T->EditorData); auto SoftPath=Data->GetRootParametersPropertyBag().GetValueSoftPath(TEXT("SoftResource")); TestTrue(TEXT("Soft object keeps native path"),SoftPath.HasValue() && SoftPath.GetValue().ToString()==TEXT("/Engine/EngineResources/DefaultTexture.DefaultTexture"));
  R={}; R.ParentId=Root; R.Name=TEXT("A"); const auto A=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id")); R.Name=TEXT("B"); const auto B=Control(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  for(const auto& State:{A,B}) { R={}; R.StateId=State; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("Duration"),TEXT("0.02")},{TEXT("RandomDeviation"),TEXT("0")}}; Control(R,TEXT("create_node")); R={}; R.StateId=State; Control(R,TEXT("create_transition")); }
  R={}; R.StateId=A; R.Kind=TEXT("enter_condition"); R.StructPath=TEXT("/Script/StateTreeModule.StateTreeObjectIsChildOfClassCondition"); FStateTreeBindingReq ObjectBinding; ObjectBinding.SourceId=TEXT("root"); ObjectBinding.SourcePath=TEXT("Resource"); ObjectBinding.TargetId=TEXT("$new"); ObjectBinding.TargetPath=TEXT("Object"); R.Bindings.Add(ObjectBinding); auto ClassBinding=ObjectBinding; ClassBinding.SourcePath=TEXT("ResourceClass"); ClassBinding.TargetPath=TEXT("Class"); R.Bindings.Add(ClassBinding); Control(R,TEXT("create_node"));
  auto Execute=[&](bool ExpectA) { UWorld::InitializationValues IV; IV.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false); auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&IV); ON_SCOPE_EXIT { W->DestroyWorld(false); }; auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*T,Instance); TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner))); bool SawA=false,SawB=false; auto Observe=[&]() { for(auto Name:Context.GetActiveStateNames()) { SawA|=Name==TEXT("A"); SawB|=Name==TEXT("B"); } }; auto Status=Context.Start(); Observe(); for(int32 I=0;I<128 && Status==EStateTreeRunStatus::Running;++I) { Status=Context.Tick(.01f); Observe(); } TestTrue(TEXT("Native reference condition tree succeeds"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Object/class binding controls A selection"),SawA,ExpectA); TestEqual(TEXT("Object/class binding controls B fallback"),SawB,!ExpectA); Context.Stop(); };
  Execute(true); R={}; R.ItemId=ResourceClass; R.bSetValue=true; R.Value=TEXT("/Script/Engine.Material"); Control(R,TEXT("update_parameter")); Execute(false); TestTrue(TEXT("Undo class reference edit"),GEditor->UndoTransaction()); Execute(true); TestTrue(TEXT("Redo class reference edit"),GEditor->RedoTransaction()); Execute(false); GEditor->UndoTransaction();
  R={}; R.ItemId=Resource; R.bSetValue=true; R.Value=TEXT("None"); Control(R,TEXT("update_parameter")); Execute(false); TestTrue(TEXT("Undo object clear"),GEditor->UndoTransaction()); Execute(true);
  const FString Before=StateTreeUtils::Inspect(T->GetPathName()); R={}; R.ItemId=Resource; R.bSetValue=true; R.Value=TEXT("/Script/Engine.Material"); bool Rejected=false; try { Control(R,TEXT("update_parameter")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Object constraint rejects wrong value"),Rejected); TestEqual(TEXT("Wrong reference preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  R={}; R.ItemId=Soft; R.bSetValue=true; R.Value=TEXT("/Game/UE5MCP_Test/Missing.Missing"); Rejected=false; try { Control(R,TEXT("update_parameter")); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Missing soft asset rejects"),Rejected); TestEqual(TEXT("Missing soft asset preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before);
  StateTreeUtils::Inspect(T->GetPathName(),true); TestEqual(TEXT("Reference validation preserves source"),StateTreeUtils::Inspect(T->GetPathName()),Before); return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
