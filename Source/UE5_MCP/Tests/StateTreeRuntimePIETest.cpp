#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "GameplayTagsManager.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeInstanceData.h"
#include "StateTreeEvents.h"
#include "Components/StateTreeComponent.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Tests/AutomationEditorCommon.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include <stdexcept>
namespace
{
 struct FStateTreePIEFixture
 {
  UStateTree* Tree=nullptr; TWeakObjectPtr<UStateTreeComponent> Component; bool HttpDone=false; int32 HttpCode=0; FString HttpBody,TagDir,TagFile,EventTag;
  ~FStateTreePIEFixture() { if(!TagDir.IsEmpty()) UGameplayTagsManager::Get().RemoveTagIniSearchPath(TagDir); if(!TagFile.IsEmpty()) IFileManager::Get().Delete(*TagFile); if(!TagDir.IsEmpty()) IFileManager::Get().DeleteDirectory(*TagDir); if(Tree) { FAssetRegistryModule::AssetDeleted(Tree); Tree->ClearFlags(RF_Public|RF_Standalone); Tree->MarkAsGarbage(); Tree->GetOutermost()->SetDirtyFlag(false); } }
 };
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStateTreeRuntimePIETest,"UE5MCP.StateTree.RuntimePIE",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStateTreeRuntimePIETest::RunTest(const FString&)
{
 if(!GEditor || GEditor->PlayWorld) { AddError(TEXT("PIE fixture needs idle editor")); return false; }
 auto State=MakeShared<FStateTreePIEFixture>();
 auto Parse=[](const FString& S) { TSharedPtr<FJsonObject> J; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),J)) throw std::runtime_error("Invalid StateTree JSON"); return J; };
 try
 {
  const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits); State->EventTag=TEXT("UE5MCP.Test.StateTree.T")+Id; State->TagDir=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("UE5MCP_Test")/(TEXT("Tags_")+Id)); State->TagFile=State->TagDir/TEXT("StateTreeEvent.ini"); IFileManager::Get().MakeDirectory(*State->TagDir,true); if(!FFileHelper::SaveStringToFile(TEXT("[/Script/GameplayTags.GameplayTagsList]\nGameplayTagList=(Tag=\"")+State->EventTag+TEXT("\",DevComment=\"Owned test\")\n"),*State->TagFile)) throw std::runtime_error("Cannot create owned event tag fixture"); UGameplayTagsManager::Get().AddTagIniSearchPath(State->TagDir);
  FStateTreeReq R; R.AssetPath=TEXT("/Game/UE5MCP_Test/ST_PIE_")+FGuid::NewGuid().ToString(EGuidFormats::Digits); auto Created=Parse(StateTreeUtils::Control(R,TEXT("create"))); State->Tree=LoadObject<UStateTree>(nullptr,*Created->GetStringField(TEXT("asset_path"))); auto* T=State->Tree;
  const auto Root=Created->GetArrayField(TEXT("states"))[0]->AsObject()->GetStringField(TEXT("id")); R={}; R.AssetPath=T->GetPathName(); R.ParentId=Root; R.Name=TEXT("Waiting"); const auto Waiting=Parse(StateTreeUtils::Control(R,TEXT("create_state")))->GetStringField(TEXT("selected_id"));
  R={}; R.AssetPath=T->GetPathName(); R.Name=TEXT("WaitSeconds"); R.ParameterType=TEXT("Float"); R.bSetValue=true; R.Value=TEXT("10"); StateTreeUtils::Control(R,TEXT("create_parameter"));
  R={}; R.AssetPath=T->GetPathName(); R.Name=TEXT("Samples"); R.ParameterType=TEXT("Float"); R.ContainerType=TEXT("Array"); R.bSetValue=true; R.Value=TEXT("[\"1\",\"2\"]"); StateTreeUtils::Control(R,TEXT("create_parameter"));
  R.Name=TEXT("Codes"); R.ParameterType=TEXT("Int32"); R.ContainerType=TEXT("Set"); R.Value=TEXT("[\"1\",\"1\",\"2\"]"); StateTreeUtils::Control(R,TEXT("create_parameter"));
  R={}; R.AssetPath=T->GetPathName(); R.StateId=Waiting; R.StructPath=TEXT("/Script/StateTreeModule.StateTreeDelayTask"); R.InstanceProperties={{TEXT("Duration"),TEXT("10")},{TEXT("RandomDeviation"),TEXT("0")}}; FStateTreeBindingReq WaitBinding; WaitBinding.SourceId=TEXT("root"); WaitBinding.SourcePath=TEXT("WaitSeconds"); WaitBinding.TargetId=TEXT("$new"); WaitBinding.TargetPath=TEXT("Duration"); R.Bindings.Add(WaitBinding); StateTreeUtils::Control(R,TEXT("create_node")); R={}; R.AssetPath=T->GetPathName(); R.StateId=Waiting; R.Trigger=TEXT("OnStateCompleted"); R.TargetType=TEXT("Failed"); StateTreeUtils::Control(R,TEXT("create_transition")); R={}; R.AssetPath=T->GetPathName(); R.StateId=Waiting; R.Trigger=TEXT("OnEvent"); R.EventTag=State->EventTag; StateTreeUtils::Control(R,TEXT("create_transition")); const FString Before=StateTreeUtils::Inspect(T->GetPathName());
  ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
  FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FFunctionLatentCommand>([this,State,Before,Parse,Phase=0,Started=FPlatformTime::Seconds()]() mutable
  {
   try
   {
    if(FPlatformTime::Seconds()-Started>30) { AddError(TEXT("StateTree PIE fixture timed out")); return true; }
    auto* W=GEditor ? GEditor->PlayWorld.Get() : nullptr; if(!W) return false;
    if(Phase==0) { auto* Owner=W->SpawnActor<AActor>(); auto* C=NewObject<UStateTreeComponent>(Owner); C->SetStartLogicAutomatically(false); C->SetStateTree(State->Tree); C->RegisterComponent(); if(!C->HasBeenInitialized()) C->InitializeComponent(); State->Component=C; C->StartLogic(); Phase=1; return false; }
    auto* C=State->Component.Get(); if(!C) { AddError(TEXT("Owned runtime component lost")); return true; }
    if(Phase==4) { if(!State->HttpDone) return false; if(!TestEqual(TEXT("HTTP event response status"),State->HttpCode,200)) { AddError(State->HttpBody); return true; } const auto EventResponse=Parse(State->HttpBody); TestTrue(TEXT("HTTP payload event submitted"),EventResponse->GetBoolField(TEXT("event_submitted"))); TestTrue(TEXT("Native queue append acknowledged"),EventResponse->GetBoolField(TEXT("event_queue_accepted"))); TestEqual(TEXT("Native queued payload type"),EventResponse->GetStringField(TEXT("queued_payload_type")),FString(TEXT("/Script/StateTreeModule.StateTreeRandomConditionInstanceData"))); Phase=3; return false; }
    if(Phase==6)
    {
     if(!State->HttpDone) return false; if(!TestEqual(TEXT("HTTP parameter response status"),State->HttpCode,200)) { AddError(State->HttpBody); return true; } const auto Response=Parse(State->HttpBody); TestTrue(TEXT("HTTP runtime parameters applied"),Response->GetBoolField(TEXT("applied"))); TestTrue(TEXT("HTTP parameter operation decoded"),Response->GetBoolField(TEXT("parameter_operation")));
     const auto Snapshot=Parse(StateTreeUtils::InspectRuntime(C->GetPathName(),TEXT(""),100,-1))->GetArrayField(TEXT("components"))[0]->AsObject(); TestTrue(TEXT("HTTP updates native reference value"),Snapshot->GetObjectField(TEXT("reference_parameters"))->GetArrayField(TEXT("fields"))[0]->AsObject()->GetStringField(TEXT("value")).StartsWith(TEXT("0.03")));
     for(const auto& Field:Snapshot->GetObjectField(TEXT("reference_parameters"))->GetArrayField(TEXT("fields")))
     {
      const auto Item=Field->AsObject(); const auto Name=Item->GetStringField(TEXT("name"));
      if(Name==TEXT("Samples") || Name==TEXT("Codes"))
      {
       const auto& Values=Item->GetArrayField(TEXT("container_values"));
       TestEqual(TEXT("HTTP runtime container count/deduplication"),Values.Num(),2);
       float Sum=0; for(const auto& Value:Values) Sum+=FCString::Atof(*Value->AsString());
       TestEqual(TEXT("HTTP runtime container native values"),Sum,15.f);
      }
     }
     FStateTreeReq Parameter; Parameter.ComponentPath=C->GetPathName(); Parameter.Operation=TEXT("start"); StateTreeUtils::ControlRuntime(Parameter); Parameter.Operation=TEXT("parameters"); Parameter.Properties={{TEXT("WaitSeconds"),TEXT("0.01")}}; bool Rejected=false; try { StateTreeUtils::ControlRuntime(Parameter); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Running parameter edit rejects"),Rejected); Phase=5; return false;
    }
    if(Phase==3)
    {
     if(C->GetStateTreeRunStatus()!=EStateTreeRunStatus::Succeeded) return false; TestEqual(TEXT("Event transition preserves authored source"),StateTreeUtils::Inspect(State->Tree->GetPathName()),Before);
     FStateTreeReq Parameter; Parameter.ComponentPath=C->GetPathName(); Parameter.Operation=TEXT("stop"); StateTreeUtils::ControlRuntime(Parameter); Parameter.Operation=TEXT("parameters"); Parameter.Properties={{TEXT("WaitSeconds"),TEXT("0.02")},{TEXT("Samples"),TEXT("[\"3\",\"4\"]")},{TEXT("Codes"),TEXT("[\"4\",\"5\",\"5\"]")}}; Parameter.bDryRun=true; TestFalse(TEXT("Runtime parameter dry-run not applied"),Parse(StateTreeUtils::ControlRuntime(Parameter))->GetBoolField(TEXT("applied")));
     auto ReadParameter=[&]() { return Parse(StateTreeUtils::InspectRuntime(C->GetPathName(),TEXT(""),100,-1))->GetArrayField(TEXT("components"))[0]->AsObject()->GetObjectField(TEXT("reference_parameters"))->GetArrayField(TEXT("fields"))[0]->AsObject()->GetStringField(TEXT("value")); };
     TestTrue(TEXT("Parameter dry-run keeps inherited value"),ReadParameter().StartsWith(TEXT("10."))); Parameter.bDryRun=false; StateTreeUtils::ControlRuntime(Parameter); TestTrue(TEXT("Component reference override value applied"),ReadParameter().StartsWith(TEXT("0.02"))); TestFalse(TEXT("Repeated runtime parameter edit no-op"),Parse(StateTreeUtils::ControlRuntime(Parameter))->GetBoolField(TEXT("applied")));
     auto Bad=Parameter; Bad.Properties={{TEXT("Missing"),TEXT("1")}}; bool Rejected=false; try { StateTreeUtils::ControlRuntime(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Unknown runtime parameter rejects"),Rejected); Bad=Parameter; Bad.Properties={{TEXT("WaitSeconds"),TEXT("nan")}}; Rejected=false; try { StateTreeUtils::ControlRuntime(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Nonfinite runtime parameter rejects"),Rejected); TestTrue(TEXT("Invalid parameter preserves component override"),ReadParameter().StartsWith(TEXT("0.02")));
     Bad=Parameter; Bad.Properties={{TEXT("WaitSeconds"),TEXT("0.5")},{TEXT("Missing"),TEXT("1")}}; Rejected=false; try { StateTreeUtils::ControlRuntime(Bad); } catch(const std::exception&) { Rejected=true; } TestTrue(TEXT("Mixed valid/invalid parameter batch rejects"),Rejected); TestTrue(TEXT("Failed batch preserves prior override"),ReadParameter().StartsWith(TEXT("0.02")));
     int32 Port=8080; FParse::Value(FCommandLine::Get(),TEXT("UE5MCPApiPort="),Port); auto Http=FHttpModule::Get().CreateRequest(); Http->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/state-trees/runtime"),Port)); Http->SetVerb(TEXT("POST")); Http->SetHeader(TEXT("Content-Type"),TEXT("application/json")); auto Body=MakeShared<FJsonObject>(); Body->SetStringField(TEXT("ComponentPath"),C->GetPathName()); Body->SetStringField(TEXT("Operation"),TEXT("parameters")); auto Values=MakeShared<FJsonObject>(); Values->SetStringField(TEXT("WaitSeconds"),TEXT("0.03")); Values->SetStringField(TEXT("Samples"),TEXT("[\"7\",\"8\"]")); Values->SetStringField(TEXT("Codes"),TEXT("[\"6\",\"6\",\"9\"]")); Body->SetObjectField(TEXT("Properties"),Values); FString Json; FJsonSerializer::Serialize(Body,TJsonWriterFactory<>::Create(&Json)); Http->SetContentAsString(Json); Http->SetTimeout(10); State->HttpDone=false; Http->OnProcessRequestComplete().BindLambda([State](FHttpRequestPtr,FHttpResponsePtr Response,bool Success) { State->HttpCode=Success && Response.IsValid() ? Response->GetResponseCode() : 0; State->HttpBody=Response.IsValid() ? Response->GetContentAsString() : FString(); State->HttpDone=true; }); if(!Http->ProcessRequest()) { AddError(TEXT("HTTP parameter request could not start")); return true; } Phase=6; return false;
    }
    if(Phase==5)
    {
     if(C->GetStateTreeRunStatus()!=EStateTreeRunStatus::Failed) return false;
     TestEqual(TEXT("Short component override drives native completion"),C->GetStateTreeRunStatus(),EStateTreeRunStatus::Failed); FStateTreeReq Reset; Reset.ComponentPath=C->GetPathName(); Reset.Operation=TEXT("stop"); StateTreeUtils::ControlRuntime(Reset); Reset.Operation=TEXT("reset_parameter"); for(const auto* Name:{TEXT("WaitSeconds"),TEXT("Samples"),TEXT("Codes")}) { Reset.Name=Name; StateTreeUtils::ControlRuntime(Reset); }
     const auto Snapshot=Parse(StateTreeUtils::InspectRuntime(C->GetPathName(),TEXT(""),100,-1))->GetArrayField(TEXT("components"))[0]->AsObject(); TestEqual(TEXT("Reset removes runtime parameter override"),Snapshot->GetArrayField(TEXT("reference_parameter_overrides")).Num(),0); TestTrue(TEXT("Reset inherits asset default"),Snapshot->GetObjectField(TEXT("reference_parameters"))->GetArrayField(TEXT("fields"))[0]->AsObject()->GetStringField(TEXT("value")).StartsWith(TEXT("10."))); TestEqual(TEXT("Runtime parameter edits preserve asset"),StateTreeUtils::Inspect(State->Tree->GetPathName()),Before); C->DestroyComponent(); return true;
    }
    if(Phase==1)
    {
     int32 Port=8080; FParse::Value(FCommandLine::Get(),TEXT("UE5MCPApiPort="),Port);
     auto Request=FHttpModule::Get().CreateRequest(); Request->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/state-trees/runtime"),Port)); Request->SetVerb(TEXT("POST")); Request->SetHeader(TEXT("Content-Type"),TEXT("application/json")); auto Body=MakeShared<FJsonObject>(); Body->SetStringField(TEXT("ComponentPath"),C->GetPathName()); Body->SetStringField(TEXT("Operation"),TEXT("pause")); FString Json; FJsonSerializer::Serialize(Body,TJsonWriterFactory<>::Create(&Json)); Request->SetContentAsString(Json); Request->SetTimeout(10);
     Request->OnProcessRequestComplete().BindLambda([State](FHttpRequestPtr,FHttpResponsePtr Response,bool Success) { State->HttpCode=Success && Response.IsValid() ? Response->GetResponseCode() : 0; State->HttpBody=Response.IsValid() ? Response->GetContentAsString() : FString(); State->HttpDone=true; });
     if(!Request->ProcessRequest()) { AddError(TEXT("HTTP lifecycle request could not start")); return true; } Phase=2; return false;
    }
    if(!State->HttpDone) return false;
    if(!TestEqual(TEXT("Actual HTTP lifecycle status"),State->HttpCode,200)) { AddError(State->HttpBody); return true; }
    const auto Http=Parse(State->HttpBody); TestTrue(TEXT("HTTP pause applied"),Http->GetBoolField(TEXT("applied"))); TestTrue(TEXT("HTTP response reports paused"),Http->GetBoolField(TEXT("paused"))); TestTrue(TEXT("HTTP route paused native component"),C->IsPaused()); FStateTreeReq Resume; Resume.ComponentPath=C->GetPathName(); Resume.Operation=TEXT("resume"); StateTreeUtils::ControlRuntime(Resume);
    auto Read=[&]() { auto J=Parse(StateTreeUtils::InspectRuntime(C->GetPathName(),TEXT(""),100,-1)); TestEqual(TEXT("Exact component query"),J->GetArrayField(TEXT("components")).Num(),1); return J->GetArrayField(TEXT("components"))[0]->AsObject(); };
    auto J=Read(); TestTrue(TEXT("Native running status"),J->GetBoolField(TEXT("running"))); TestEqual(TEXT("Native run status enum"),J->GetStringField(TEXT("run_status")),FString(TEXT("Running"))); TestTrue(TEXT("Native authority"),J->GetBoolField(TEXT("authority"))); TestEqual(TEXT("Native owner path"),J->GetStringField(TEXT("owner_path")),C->GetOwner()->GetPathName());
#if WITH_GAMEPLAY_DEBUGGER
    bool SawWaiting=false; for(const auto& Name:J->GetArrayField(TEXT("active_state_names"))) SawWaiting|=Name->AsString()==TEXT("Waiting"); TestTrue(TEXT("Native active state reported"),SawWaiting);
#endif
    FStateTreeReq Request; Request.ComponentPath=C->GetPathName(); Request.Operation=TEXT("pause"); Request.bDryRun=true; TestFalse(TEXT("Runtime dry-run not applied"),Parse(StateTreeUtils::ControlRuntime(Request))->GetBoolField(TEXT("applied"))); TestFalse(TEXT("Dry-run preserves pause state"),C->IsPaused()); Request.bDryRun=false; StateTreeUtils::ControlRuntime(Request); TestFalse(TEXT("Repeated pause no-op"),Parse(StateTreeUtils::ControlRuntime(Request))->GetBoolField(TEXT("applied"))); TestTrue(TEXT("Native paused flag"),Read()->GetBoolField(TEXT("paused"))); Request.Operation=TEXT("resume"); StateTreeUtils::ControlRuntime(Request); TestFalse(TEXT("Native resumed flag"),Read()->GetBoolField(TEXT("paused"))); Request.Operation=TEXT("restart"); StateTreeUtils::ControlRuntime(Request); TestTrue(TEXT("Native restart keeps logic running"),C->IsRunning()); Request.Operation=TEXT("stop"); StateTreeUtils::ControlRuntime(Request); TestFalse(TEXT("Native stopped flag"),Read()->GetBoolField(TEXT("running")));
    TestFalse(TEXT("Repeated stop no-op"),Parse(StateTreeUtils::ControlRuntime(Request))->GetBoolField(TEXT("applied")));
    Request.Operation=TEXT("pause"); bool PauseRejected=false; try { StateTreeUtils::ControlRuntime(Request); } catch(const std::exception&) { PauseRejected=true; } TestTrue(TEXT("Pause stopped logic rejects"),PauseRejected);
    Request.Operation=TEXT("start"); Request.bDryRun=true; const auto StartPreview=Parse(StateTreeUtils::ControlRuntime(Request)); TestTrue(TEXT("Stopped start preview would change"),StartPreview->GetBoolField(TEXT("would_change"))); TestFalse(TEXT("Stopped start preview preserves runtime"),C->IsRunning()); Request.bDryRun=false; TestTrue(TEXT("Stopped component start applied"),Parse(StateTreeUtils::ControlRuntime(Request))->GetBoolField(TEXT("applied"))); TestTrue(TEXT("Start restores native running"),C->IsRunning()); TestFalse(TEXT("Repeated start no-op"),Parse(StateTreeUtils::ControlRuntime(Request))->GetBoolField(TEXT("applied")));
    auto Invalid=Request; Invalid.PIEInstance=999999; bool WorldRejected=false; try { StateTreeUtils::ControlRuntime(Invalid); } catch(const std::exception&) { WorldRejected=true; } TestTrue(TEXT("Wrong PIE control world rejected"),WorldRejected); Invalid=Request; Invalid.ComponentPath=State->Tree->GetPathName(); bool AssetRejected=false; try { StateTreeUtils::ControlRuntime(Invalid); } catch(const std::exception&) { AssetRejected=true; } TestTrue(TEXT("Asset path cannot control runtime"),AssetRejected); Invalid=Request; Invalid.Operation=TEXT("invalid"); bool OperationRejected=false; try { StateTreeUtils::ControlRuntime(Invalid); } catch(const std::exception&) { OperationRejected=true; } TestTrue(TEXT("Invalid runtime operation rejected"),OperationRejected); TestTrue(TEXT("Rejected control preserves running state"),C->IsRunning());
    TestEqual(TEXT("Runtime inspection preserves authored source"),StateTreeUtils::Inspect(State->Tree->GetPathName()),Before);
    Request.Operation=TEXT("event"); Request.EventTag=TEXT("UE5MCP.Test.UnregisteredFixture"); bool BadTag=false; try { StateTreeUtils::ControlRuntime(Request); } catch(const std::exception&) { BadTag=true; } TestTrue(TEXT("Unregistered runtime event rejects"),BadTag); Request.EventTag=State->EventTag; Request.bDryRun=true; TestFalse(TEXT("Event dry-run sends nothing"),Parse(StateTreeUtils::ControlRuntime(Request))->GetBoolField(TEXT("event_submitted"))); TestEqual(TEXT("Event preview preserves running state"),C->GetStateTreeRunStatus(),EStateTreeRunStatus::Running); Request.StructPath=TEXT("/Script/StateTreeModule.StateTreeRandomConditionInstanceData"); Request.Properties={{TEXT("Threshold"),TEXT("2")}}; bool BadPayload=false; try { StateTreeUtils::ControlRuntime(Request); } catch(const std::exception&) { BadPayload=true; } TestTrue(TEXT("Payload native clamp enforced"),BadPayload); Request.Properties[TEXT("Threshold")]=TEXT("0.5"); StateTreeUtils::ControlRuntime(Request); TestEqual(TEXT("Payload dry-run preserves native status"),C->GetStateTreeRunStatus(),EStateTreeRunStatus::Running);
    const auto* InstanceProperty=FindFProperty<FStructProperty>(C->GetClass(),TEXT("InstanceData")); auto* Instance=InstanceProperty->ContainerPtrToValuePtr<FStateTreeInstanceData>(C); auto& Queue=Instance->GetMutableEventQueue(); Queue.Reset(); const auto Tag=UGameplayTagsManager::Get().RequestGameplayTag(FName(*State->EventTag),false); for(int32 I=0;I<FStateTreeEventQueue::MaxActiveEvents;++I) TestTrue(TEXT("Fill owned native event queue"),Queue.SendEvent(C->GetOwner(),Tag)); Request.bDryRun=false; bool FullRejected=false; try { StateTreeUtils::ControlRuntime(Request); } catch(const std::exception&) { FullRejected=true; } TestTrue(TEXT("Full native queue rejected before submission"),FullRejected); TestEqual(TEXT("Rejected event preserves full queue"),Queue.GetEventsView().Num(),FStateTreeEventQueue::MaxActiveEvents); Queue.Reset();
    int32 Port=8080; FParse::Value(FCommandLine::Get(),TEXT("UE5MCPApiPort="),Port); auto EventRequest=FHttpModule::Get().CreateRequest(); EventRequest->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/state-trees/runtime"),Port)); EventRequest->SetVerb(TEXT("POST")); EventRequest->SetHeader(TEXT("Content-Type"),TEXT("application/json")); auto EventBody=MakeShared<FJsonObject>(); EventBody->SetStringField(TEXT("ComponentPath"),C->GetPathName()); EventBody->SetStringField(TEXT("Operation"),TEXT("event")); EventBody->SetStringField(TEXT("EventTag"),State->EventTag); EventBody->SetStringField(TEXT("StructPath"),Request.StructPath); auto Properties=MakeShared<FJsonObject>(); Properties->SetStringField(TEXT("Threshold"),TEXT("0.5")); EventBody->SetObjectField(TEXT("Properties"),Properties); FString Json; FJsonSerializer::Serialize(EventBody,TJsonWriterFactory<>::Create(&Json)); EventRequest->SetContentAsString(Json); EventRequest->SetTimeout(10); State->HttpDone=false;
    EventRequest->OnProcessRequestComplete().BindLambda([State](FHttpRequestPtr,FHttpResponsePtr Response,bool Success) { State->HttpCode=Success && Response.IsValid() ? Response->GetResponseCode() : 0; State->HttpBody=Response.IsValid() ? Response->GetContentAsString() : FString(); State->HttpDone=true; }); if(!EventRequest->ProcessRequest()) { AddError(TEXT("HTTP event request could not start")); return true; } Phase=4; return false;
   } catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return true; }
  }));
  ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand()); return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
