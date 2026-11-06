#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "StateTreeVerificationFixtures.h"
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
#include "UObject/GarbageCollection.h"
#include <stdexcept>
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeNodeReferenceTest,"UE5MCP.StateTree.NodeReferences",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeNodeReferenceTest::RunTest(const FString&)
{
 UStateTree* Tree=nullptr;
 ON_SCOPE_EXIT { if(Tree) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid JSON"); return J; };
 auto Edit=[&](FStateTreeReq R,const TCHAR* Op) { if(Tree) R.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_ReferenceNative_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto J=Edit(R,TEXT("create")); Tree=LoadObject<UStateTree>(nullptr,*J->GetStringField(TEXT("asset_path")));
  const auto Root=J->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  R={}; R.ParentId=Root; R.Name=TEXT("Work"); const auto Work=Edit(R,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Work; Edit(R,TEXT("create_transition"));
  R={}; R.Name=TEXT("Input"); R.ParameterType=TEXT("Float"); R.bSetValue=true; R.Value=TEXT("2"); const auto Input=Edit(R,TEXT("create_parameter"))->GetStringField(TEXT("selected_id"));
  R={}; R.StateId=Work; R.NodeClassPath=UMCPVerificationBlueprintTask::StaticClass()->GetPathName();
  const TMap<FString,FString> References={{TEXT("Material"),TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial")},{TEXT("SoftMaterial"),TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial")},{TEXT("ActorClass"),TEXT("/Script/Engine.Pawn")},{TEXT("SoftActorClass"),TEXT("/Script/Engine.Pawn")}};
  FStateTreeFunctionBindingReq Function; Function.StructPath=FMCPVerificationReferenceFunction::StaticStruct()->GetPathName(); Function.TargetId=TEXT("$new"); Function.TargetPath=TEXT("Amount"); Function.InstanceReferences=References; R.Functions.Add(Function);
  const auto Task=Edit(R,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  auto Execute=[&](float Expected)
  {
   UWorld::InitializationValues V; V.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&V); ON_SCOPE_EXIT { W->DestroyWorld(false); };
   auto* Owner=W->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*Tree,Instance); Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner));
   UMCPVerificationBlueprintTask::ObservedAmount=-1; auto Status=Context.Start(); for(int32 I=0;I<16 && Status==EStateTreeRunStatus::Running;++I) Status=Context.Tick(.01f);
   TestTrue(TEXT("Function-bound native task succeeds"),Status==EStateTreeRunStatus::Succeeded); TestEqual(TEXT("Native property function result reaches task"),UMCPVerificationBlueprintTask::ObservedAmount,Expected); Context.Stop();
  };
  Execute(15);
  auto Snapshot=Parse(StateTreeUtils::Inspect(Tree->GetPathName())); const auto FunctionID=Snapshot->GetArrayField(TEXT("bindings"))[0]->AsObject()->GetStringField(TEXT("source_id"));
  R={}; R.ItemId=FunctionID; R.InstanceReferences={{TEXT("Material"),TEXT("None")}}; Edit(R,TEXT("update_function")); Execute(14);
  TestTrue(TEXT("Undo function reference clearing"),GEditor->UndoTransaction()); Execute(15); TestTrue(TEXT("Redo function reference clearing"),GEditor->RedoTransaction()); Execute(14);
  for(const auto* Field:{TEXT("TransientMaterial"),TEXT("ReadOnlyMaterial"),TEXT("InstancedObject")})
  {
   const auto Before=StateTreeUtils::Inspect(Tree->GetPathName()); R={}; R.ItemId=FunctionID; R.InstanceReferences={{Field,References.FindChecked(TEXT("Material"))}}; bool Rejected=false;
   try { Edit(R,TEXT("update_function")); } catch(const std::exception&) { Rejected=true; }
   TestTrue(TEXT("Unsupported reference flags reject"),Rejected); TestEqual(TEXT("Rejected reference preserves source"),StateTreeUtils::Inspect(Tree->GetPathName()),Before);
  }
  R={}; R.StateId=Work; R.ItemId=Task; R.InstanceReferences=References; Edit(R,TEXT("update_node")); Execute(14);
  R={}; R.ItemId=FunctionID; R.InstanceReferences=References; Edit(R,TEXT("update_function")); Execute(15);
  const FString BeforeGC=StateTreeUtils::Inspect(Tree->GetPathName());
  TWeakObjectPtr<UMaterialInterface> Material=LoadObject<UMaterialInterface>(nullptr,*References.FindChecked(TEXT("Material")));
  CollectGarbage(RF_NoFlags);
  TestTrue(TEXT("Hard reference survives garbage collection"),Material.IsValid());
  TestEqual(TEXT("GC preserves hard/soft reference inspection"),StateTreeUtils::Inspect(Tree->GetPathName()),BeforeGC);
  Execute(15);
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
