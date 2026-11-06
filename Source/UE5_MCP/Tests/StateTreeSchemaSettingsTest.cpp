#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeExecutionContext.h"
#include "StateTreeInstanceData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeSchemaSettingsTest,"UE5MCP.StateTree.SchemaSettings",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeSchemaSettingsTest::RunTest(const FString&)
{
 TArray<UStateTree*> Trees;
 ON_SCOPE_EXIT { for(auto* T:Trees) { FAssetRegistryModule::AssetDeleted(T); T->ClearFlags(RF_Public|RF_Standalone); T->MarkAsGarbage(); T->GetOutermost()->SetDirtyFlag(false); } };
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid JSON"); return J; };
 auto Edit=[&](UStateTree* T,FStateTreeReq R,const TCHAR* Op) { if(T) R.AssetPath=T->GetPathName(); return Parse(StateTreeUtils::Control(R,Op)); };
 try
 {
  auto Create=[&]() { FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Schema_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto J=Edit(nullptr,R,TEXT("create")); auto* T=LoadObject<UStateTree>(nullptr,*J->GetStringField(TEXT("asset_path"))); Trees.Add(T); return T; };
  auto* Leaf=Create(); auto* Caller=Create();
  auto Root=Parse(StateTreeUtils::Inspect(Caller->GetPathName()))->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  FStateTreeReq R; R.ParentId=Root; R.Name=TEXT("Call"); R.StateType=TEXT("LinkedAsset"); R.LinkedAssetPath=Leaf->GetPathName(); Edit(Caller,R,TEXT("create_state"));
  const FString Before=StateTreeUtils::Inspect(Leaf->GetPathName());
  R={}; R.ContextClasses={{TEXT("ContextActorClass"),TEXT("/Script/Engine.Pawn")}};
  bool Rejected=false; try { Edit(Leaf,R,TEXT("schema_settings")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Broad caller cannot satisfy narrowed linked context"),Rejected);
  TestEqual(TEXT("Incompatible linked context preserves source"),StateTreeUtils::Inspect(Leaf->GetPathName()),Before);
  Edit(Caller,R,TEXT("schema_settings")); Edit(Leaf,R,TEXT("schema_settings"));
  UWorld::InitializationValues V; V.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
  auto* W=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&V); ON_SCOPE_EXIT { W->DestroyWorld(false); };
  auto* Actor=W->SpawnActor<AActor>(); auto* Pawn=W->SpawnActor<APawn>();
  for(auto* T:{Leaf,Caller})
  {
   FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Pawn,*T,Instance);
   Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Actor));
   TestFalse(TEXT("Runtime rejects Actor for Pawn context"),Context.AreContextDataViewsValid());
   Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Pawn));
   TestTrue(TEXT("Runtime accepts Pawn context"),Context.AreContextDataViewsValid());
  }
  TestTrue(TEXT("Undo narrowed leaf schema"),GEditor->UndoTransaction());
  TestTrue(TEXT("Redo narrowed leaf schema"),GEditor->RedoTransaction());
  TestEqual(TEXT("Compiled context class follows schema notifications"),Leaf->GetContextDataDescs()[0].Struct.Get(),static_cast<const UStruct*>(APawn::StaticClass()));
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
