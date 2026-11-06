#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "StateTreeVerificationFixtures.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeEditorData.h"
#include "StateTreeState.h"
#include "StateTreeExecutionContext.h"
#include "StateTreeInstanceData.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "EdGraphSchema_K2.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeBlueprintInstanceTest,"UE5MCP.StateTree.BlueprintInstances",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeBlueprintInstanceTest::RunTest(const FString&)
{
 UStateTree* Tree=nullptr; UBlueprint* Blueprint=nullptr; TArray<UBlueprint*> ExtraBlueprints;
 ON_SCOPE_EXIT
 {
  for(UObject* Object:{static_cast<UObject*>(Tree),static_cast<UObject*>(Blueprint)}) if(Object) { FAssetRegistryModule::AssetDeleted(Object); Object->ClearFlags(RF_Public|RF_Standalone); Object->MarkAsGarbage(); Object->GetOutermost()->SetDirtyFlag(false); }
  for(auto* Extra:ExtraBlueprints) { FAssetRegistryModule::AssetDeleted(Extra); Extra->ClearFlags(RF_Public|RF_Standalone); Extra->MarkAsGarbage(); Extra->GetOutermost()->SetDirtyFlag(false); }
 };
 auto Parse=[](const FString& Text) { TSharedPtr<FJsonObject> Json; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json)) throw std::runtime_error("Invalid JSON"); return Json; };
 auto Control=[&](FStateTreeReq Request,const TCHAR* Operation) { if(Tree) Request.AssetPath=Tree->GetPathName(); return Parse(StateTreeUtils::Control(Request,Operation)); };
 try
 {
  const FString Name=TEXT("BP_VerificationTask_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
  Blueprint=FKismetEditorUtilities::CreateBlueprint(UMCPVerificationBlueprintTask::StaticClass(),CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+Name)),FName(*Name),BPTYPE_Normal,UBlueprint::StaticClass(),UBlueprintGeneratedClass::StaticClass());
  if(!TestNotNull(TEXT("Compiled Blueprint task fixture"),Blueprint)) return false;
  FKismetEditorUtilities::CompileBlueprint(Blueprint); FAssetRegistryModule::AssetCreated(Blueprint);
  FStateTreeReq Request; Request.AssetPath=TEXT("/Game/UE5MCP_Test/ST_Blueprint_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
  const auto Created=Control(Request,TEXT("create")); Tree=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path")));
  const auto Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id"));
  Request={}; Request.ParentId=Root; Request.Name=TEXT("Work"); const auto Work=Control(Request,TEXT("create_state"))->GetStringField(TEXT("selected_id"));
  Request={}; Request.StateId=Work; Control(Request,TEXT("create_transition"));
  auto Execute=[&](float Amount,float Extra=0)
  {
   UWorld::InitializationValues Values; Values.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
   auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values); ON_SCOPE_EXIT { World->DestroyWorld(false); };
   auto* Owner=World->SpawnActor<AActor>(); FStateTreeInstanceData Instance; FStateTreeExecutionContext Context(*Owner,*Tree,Instance); TestTrue(TEXT("Actor context"),Context.SetContextDataByName(TEXT("Actor"),FStateTreeDataView(Owner)));
   UMCPVerificationBlueprintTask::ObservedAmount=-1; UMCPVerificationBlueprintTask::ObservedExtra=-1; const auto Before=UMCPVerificationBlueprintTask::Executions;
   auto Status=Context.Start(); for(int32 Tick=0;Tick<128 && Status==EStateTreeRunStatus::Running;++Tick) Status=Context.Tick(.01f);
   TestTrue(TEXT("Blueprint wrapper executes task instance"),UMCPVerificationBlueprintTask::Executions>Before);
   TestEqual(TEXT("Instance scalar reaches runtime"),UMCPVerificationBlueprintTask::ObservedAmount,Amount);
   TestEqual(TEXT("Reinstanced Blueprint field reaches runtime"),UMCPVerificationBlueprintTask::ObservedExtra,Extra);
   TestTrue(TEXT("Wrapper task succeeds"),Status==EStateTreeRunStatus::Succeeded); Context.Stop();
  };
  Request={}; Request.StateId=Work; Request.NodeClassPath=UMCPVerificationBlueprintTask::StaticClass()->GetPathName(); Request.InstanceProperties={{TEXT("Amount"),TEXT("2")}};
  const auto Native=Control(Request,TEXT("create_node"))->GetStringField(TEXT("selected_id")); Execute(2);
  Request={}; Request.StateId=Work; Request.ItemId=Native; Request.bConfirm=true; Control(Request,TEXT("delete_node"));
  Request={}; Request.Name=TEXT("Amount"); Request.ParameterType=TEXT("Float"); Request.bSetValue=true; Request.Value=TEXT("3"); Control(Request,TEXT("create_parameter"));
  Request={}; Request.StateId=Work; Request.NodeClassPath=Blueprint->GeneratedClass->GetPathName(); Request.InstanceProperties={{TEXT("Label"),TEXT("Authored")},{TEXT("Offset"),TEXT("(X=1,Y=2,Z=3)")}};
  FStateTreeBindingReq Binding; Binding.SourceId=TEXT("root"); Binding.SourcePath=TEXT("Amount"); Binding.TargetId=TEXT("$new"); Binding.TargetPath=TEXT("Amount"); Request.Bindings.Add(Binding);
  const auto Task=Control(Request,TEXT("create_node"))->GetStringField(TEXT("selected_id")); Execute(3);
  auto CreateAuxiliary=[&](UClass* Parent,const TCHAR* Suffix)
  {
   const FString AuxiliaryName=Name+Suffix;
   auto* Auxiliary=FKismetEditorUtilities::CreateBlueprint(Parent,CreatePackage(*(TEXT("/Game/UE5MCP_Test/")+AuxiliaryName)),FName(*AuxiliaryName),BPTYPE_Normal,UBlueprint::StaticClass(),UBlueprintGeneratedClass::StaticClass());
   if(!Auxiliary) throw std::runtime_error("Could not create auxiliary Blueprint wrapper");
   ExtraBlueprints.Add(Auxiliary); FKismetEditorUtilities::CompileBlueprint(Auxiliary); FAssetRegistryModule::AssetCreated(Auxiliary); return Auxiliary->GeneratedClass;
  };
  Request={}; Request.StateId=Work; Request.Kind=TEXT("enter_condition"); Request.NodeClassPath=CreateAuxiliary(UMCPVerificationBlueprintCondition::StaticClass(),TEXT("Condition"))->GetPathName();
  Control(Request,TEXT("create_node"));
  Request={}; Request.StateId=Root; Request.Properties={{TEXT("SelectionBehavior"),TEXT("TrySelectChildrenWithHighestUtility")}}; Control(Request,TEXT("update_state"));
  Request={}; Request.StateId=Work; Request.Kind=TEXT("consideration"); Request.NodeClassPath=CreateAuxiliary(UMCPVerificationBlueprintConsideration::StaticClass(),TEXT("Consideration"))->GetPathName();
  Control(Request,TEXT("create_node"));
  Request={}; Request.Kind=TEXT("evaluator"); Request.NodeClassPath=CreateAuxiliary(UMCPVerificationBlueprintEvaluator::StaticClass(),TEXT("Evaluator"))->GetPathName();
  const auto Evaluator=Control(Request,TEXT("create_node"))->GetStringField(TEXT("selected_id"));
  Binding.SourceId=Evaluator; Binding.SourcePath=TEXT("OutputValue"); Binding.TargetId=Task; Request={}; Request.Binding=Binding; Request.bConfirm=true; Control(Request,TEXT("set_binding"));
  UMCPVerificationBlueprintCondition::Evaluations=0; UMCPVerificationBlueprintConsideration::Evaluations=0; UMCPVerificationBlueprintEvaluator::Starts=0; Execute(4);
  TestTrue(TEXT("Compiled Blueprint condition executes"),UMCPVerificationBlueprintCondition::Evaluations>0);
  TestTrue(TEXT("Compiled Blueprint consideration scores selection"),UMCPVerificationBlueprintConsideration::Evaluations>0);
  TestTrue(TEXT("Compiled Blueprint evaluator drives bound task input"),UMCPVerificationBlueprintEvaluator::Starts>0);
  Binding.SourceId=TEXT("root"); Binding.SourcePath=TEXT("Amount"); Request.Binding=Binding; Control(Request,TEXT("set_binding")); Execute(3);
  auto* Data=CastChecked<UStateTreeEditorData>(Tree->EditorData); auto* WorkState=Data->SubTrees[0]->Children[0].Get();
  TestTrue(TEXT("Blueprint instance owned by source tree"),WorkState->Tasks[0].InstanceObject->IsIn(Tree));
  TestTrue(TEXT("Blueprint generated class selected"),WorkState->Tasks[0].InstanceObject->GetClass()==Blueprint->GeneratedClass);
  const auto Discovered=Parse(StateTreeUtils::DiscoverClasses(Tree->GetPathName(),TEXT("task"),Name,100));
  TestEqual(TEXT("Loaded Blueprint class discovery"),Discovered->GetArrayField(TEXT("classes")).Num(),1);
  Request={}; Request.StateId=Work; Request.ItemId=Task; Request.InstanceProperties={{TEXT("Label"),TEXT("Updated")},{TEXT("Offset"),TEXT("(X=4,Y=5,Z=6)")}};
  Control(Request,TEXT("update_node")); Execute(3); TestTrue(TEXT("Undo Blueprint instance edit"),GEditor->UndoTransaction()); Execute(3); TestTrue(TEXT("Redo Blueprint instance edit"),GEditor->RedoTransaction()); Execute(3);
  FEdGraphPinType Type; Type.PinCategory=UEdGraphSchema_K2::PC_Real; Type.PinSubCategory=UEdGraphSchema_K2::PC_Float;
  TestTrue(TEXT("Add reflected Blueprint instance field"),FBlueprintEditorUtils::AddMemberVariable(Blueprint,TEXT("Extra"),Type,TEXT("0.0")));
  FKismetEditorUtilities::CompileBlueprint(Blueprint);
  TestTrue(TEXT("Reinstanced source class is current"),WorkState->Tasks[0].InstanceObject->GetClass()==Blueprint->GeneratedClass);
  Request={}; Request.StateId=Work; Request.ItemId=Task; Request.InstanceProperties={{TEXT("Extra"),TEXT("5")}}; Control(Request,TEXT("update_node")); Execute(3,5);
  TestTrue(TEXT("Undo reinstanced field edit"),GEditor->UndoTransaction()); Execute(3,0); TestTrue(TEXT("Redo reinstanced field edit"),GEditor->RedoTransaction()); Execute(3,5);
  const FString Before=StateTreeUtils::Inspect(Tree->GetPathName()); Request={}; Request.StateId=Work; Request.Kind=TEXT("enter_condition"); Request.NodeClassPath=Blueprint->GeneratedClass->GetPathName(); bool Rejected=false;
  try { Control(Request,TEXT("create_node")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Wrong Blueprint node family rejects"),Rejected); TestEqual(TEXT("Rejected wrapper preserves source"),StateTreeUtils::Inspect(Tree->GetPathName()),Before);
  Request={}; Request.StateId=Work; Request.ItemId=Task; Request.bConfirm=true; Control(Request,TEXT("delete_node")); TestEqual(TEXT("Deleting wrapper removes atomic bindings"),Data->EditorBindings.GetNumBindings(),0);
  TestTrue(TEXT("Undo wrapper deletion"),GEditor->UndoTransaction()); Execute(3,5);
  return true;
 }
 catch(const std::exception& Error) { AddError(UTF8_TO_TCHAR(Error.what())); return false; }
}
#endif
