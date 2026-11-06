#include "DebugFeedbackUtils.h"
#include "UE5_MCP/API/DTO/GameCoreReq.h"
#include "Containers/Ticker.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphToken.h"
#include "Editor.h"
#include "Editor/UnrealEdEngine.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Framework/Application/SlateApplication.h"
#include "GameProjectUtils.h"
#include "AddToProjectConfig.h"
#include "HttpServerRequest.h"
#include "HttpServerResponse.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/Breakpoint.h"
#include "Kismet2/CompilerResultsLog.h"
#include "Kismet2/KismetDebugUtilities.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Logging/TokenizedMessage.h"
#include "Misc/App.h"
#include "Misc/CoreMisc.h"
#include "Misc/Paths.h"
#include "Misc/UObjectToken.h"
#include "ModuleDescriptor.h"
#include "Modules/ModuleManager.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Stack.h"
#include "UObject/UnrealType.h"
#include <stdexcept>
#if PLATFORM_WINDOWS
#include "ILiveCodingModule.h"
#endif

namespace
{
 double PauseStartSeconds=0;
 double PauseTimeoutSeconds=300;
 bool bAutoResumed=false;

 UBlueprint* LoadBp(const FString& Path)
 {
  UBlueprint* B=Cast<UBlueprint>(StaticLoadObject(UBlueprint::StaticClass(),nullptr,*Path));
  if(!B) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Not a Blueprint: %s"),*Path)));
  return B;
 }
 UEdGraphNode* FindNode(UBlueprint* B,const FString& Guid)
 {
  TArray<UEdGraphNode*> Nodes; FBlueprintEditorUtils::GetAllNodesOfClass(B,Nodes);
  for(UEdGraphNode* N:Nodes) if(N && N->NodeGuid.ToString()==Guid) return N;
  throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Node not found: %s"),*Guid)));
 }
 void WriteNode(const TSharedRef<TJsonWriter<>>& J,const UEdGraphNode* N)
 {
  J->WriteValue(TEXT("node_id"),N->NodeGuid.ToString());
  J->WriteValue(TEXT("node_title"),N->GetNodeTitle(ENodeTitleType::ListView).ToString());
  J->WriteValue(TEXT("graph"),N->GetGraph() ? N->GetGraph()->GetName() : FString());
 }
 void ResumeExecution(bool bSingleStep)
 {
  GEditor->SetPIEWorldsPaused(false);
  if(bSingleStep) GEditor->PlaySessionSingleStepped(); else GEditor->PlaySessionResumed();
  FSlateApplication::Get().LeaveDebuggingMode(bSingleStep);
 }
 // Runs inside the engine's paused loop, which ticks only Slate.
 void PumpWhilePaused(float)
 {
  if(!GIntraFrameDebuggingGameThread) { PauseStartSeconds=0; return; }
  const double Now=FPlatformTime::Seconds();
  if(PauseStartSeconds==0) { PauseStartSeconds=Now; bAutoResumed=false; }
  FTSTicker::GetCoreTicker().Tick(FMath::Min((float)FApp::GetDeltaTime(),0.1f));
  FPlatformProcess::Sleep(0.005f);
  // The ticker can run a resume request, which clears the start time.
  if(GIntraFrameDebuggingGameThread && PauseStartSeconds>0 && Now-PauseStartSeconds>PauseTimeoutSeconds)
  {
   // Nobody resumed. Disable the breakpoint so it can't pause again every frame.
   if(UEdGraphNode* N=FKismetDebugUtilities::GetMostRecentBreakpointHit())
    if(UBlueprint* B=FBlueprintEditorUtils::FindBlueprintForNode(N)) FKismetDebugUtilities::SetBreakpointEnabled(N,B,false);
   UE_LOG(LogTemp,Warning,TEXT("UE5_MCP: resumed a Blueprint breakpoint after %.0f seconds with no client"),PauseTimeoutSeconds);
   bAutoResumed=true; PauseStartSeconds=0; ResumeExecution(false);
  }
 }
 bool AllowedWhilePaused(const FString& Path)
 {
  return Path.StartsWith(TEXT("/blueprints/debug")) || Path.StartsWith(TEXT("/blueprints/breakpoints")) || Path==TEXT("/editor/status") || Path==TEXT("/editor/logs");
 }
}

void DebugFeedbackUtils::Install(const TSharedPtr<IHttpRouter>& Router)
{
 static bool bPumpInstalled=false;
 if(!bPumpInstalled && FSlateApplication::IsInitialized()) { FSlateApplication::Get().OnPreTick().AddStatic(&PumpWhilePaused); bPumpInstalled=true; }
 Router->RegisterRequestPreprocessor(FHttpRequestHandler::CreateLambda([](const FHttpServerRequest& Request,const FHttpResultCallback& Done)
 {
  if(!GIntraFrameDebuggingGameThread || AllowedWhilePaused(Request.RelativePath.GetPath())) return false;
  TUniquePtr<FHttpServerResponse> Response=FHttpServerResponse::Create(TEXT("{\"errorMessage\":\"A Blueprint breakpoint has paused the editor. Use inspect_blueprint_debug_state, then control_blueprint_debugger to resume.\"}"),TEXT("application/json"));
  Response->Code=EHttpServerResponseCodes::Conflict; Done(MoveTemp(Response)); return true;
 }));
}

bool DebugFeedbackUtils::CompileAndWrite(UBlueprint* Blueprint,const TSharedRef<TJsonWriter<>>& J)
{
 FCompilerResultsLog Log; Log.SetSourcePath(Blueprint->GetPathName()); Log.bSilentMode=true;
 FKismetEditorUtilities::CompileBlueprint(Blueprint,EBlueprintCompileOptions::None,&Log);
 const bool bOk=Blueprint->Status!=BS_Error && Log.NumErrors==0;
 J->WriteValue(TEXT("compiled"),bOk);
 J->WriteValue(TEXT("up_to_date"),Blueprint->Status==BS_UpToDate || Blueprint->Status==BS_UpToDateWithWarnings);
 J->WriteValue(TEXT("errors"),Log.NumErrors); J->WriteValue(TEXT("warnings"),Log.NumWarnings);
 J->WriteArrayStart(TEXT("messages"));
 for(const TSharedRef<FTokenizedMessage>& M:Log.Messages)
 {
  const EMessageSeverity::Type S=M->GetSeverity(); if(S!=EMessageSeverity::Error && S!=EMessageSeverity::Warning && S!=EMessageSeverity::PerformanceWarning) continue;
  J->WriteObjectStart(); J->WriteValue(TEXT("severity"),S==EMessageSeverity::Error ? TEXT("error") : TEXT("warning")); J->WriteValue(TEXT("message"),M->ToText().ToString());
  for(const TSharedRef<IMessageToken>& T:M->GetMessageTokens())
  {
   const UEdGraphNode* N=nullptr;
   if(T->GetType()==EMessageToken::Object) N=Cast<UEdGraphNode>(StaticCastSharedRef<FUObjectToken>(T)->GetObject().Get());
   else if(T->GetType()==EMessageToken::EdGraph)
   {
    const TSharedRef<FEdGraphToken> G=StaticCastSharedRef<FEdGraphToken>(T);
    if(const UEdGraphPin* P=G->GetPin()) N=P->GetOwningNodeUnchecked();
    if(!N) N=Cast<UEdGraphNode>(G->GetGraphObject());
   }
   if(N) { WriteNode(J,N); break; }
  }
  J->WriteObjectEnd();
 }
 J->WriteArrayEnd();
 return bOk;
}

FString DebugFeedbackUtils::Compile(const FString& AssetPath)
{
 UBlueprint* B=LoadBp(AssetPath);
 FString Out; auto J=TJsonWriterFactory<>::Create(&Out); J->WriteObjectStart(); J->WriteValue(TEXT("bp_path"),B->GetPathName());
 const bool bOk=CompileAndWrite(B,J); J->WriteValue(TEXT("success"),bOk); J->WriteObjectEnd(); J->Close(); return Out;
}

FString DebugFeedbackUtils::ListBreakpoints(const FString& AssetPath)
{
 UBlueprint* B=LoadBp(AssetPath);
 FString Out; auto J=TJsonWriterFactory<>::Create(&Out); J->WriteObjectStart(); J->WriteValue(TEXT("bp_path"),B->GetPathName()); J->WriteArrayStart(TEXT("breakpoints"));
 FKismetDebugUtilities::ForeachBreakpoint(B,[&J](FBlueprintBreakpoint& P)
 {
  const UEdGraphNode* N=P.GetLocation(); if(!N) return;
  J->WriteObjectStart(); WriteNode(J,N); J->WriteValue(TEXT("enabled"),P.IsEnabledByUser()); J->WriteObjectEnd();
 });
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Out;
}

FString DebugFeedbackUtils::EditBreakpoint(const FGameCoreReq& R)
{
 UBlueprint* B=LoadBp(R.AssetPath);
 if(R.Operation==TEXT("clear_all")) FKismetDebugUtilities::ClearBreakpoints(B);
 else
 {
  UEdGraphNode* N=FindNode(B,R.NodeId);
  if(R.Operation==TEXT("add"))
  {
   // A hit opens the Blueprint editor window, which is a fatal error in an editor that can't render.
   if(!FSlateApplication::IsInitialized() || !FApp::CanEverRender()) throw std::runtime_error("Breakpoints need a windowed editor; this one is headless (-nullrhi)");
   if(R.TimeoutSeconds<10 || R.TimeoutSeconds>3600) throw std::runtime_error("timeout_seconds must be 10-3600");
   PauseTimeoutSeconds=R.TimeoutSeconds;
   if(FKismetDebugUtilities::FindBreakpointForNode(N,B)) FKismetDebugUtilities::SetBreakpointEnabled(N,B,true); else FKismetDebugUtilities::CreateBreakpoint(B,N,true);
  }
  else if(R.Operation==TEXT("remove")) FKismetDebugUtilities::RemoveBreakpointFromNode(N,B);
  else if(R.Operation==TEXT("enable") || R.Operation==TEXT("disable")) FKismetDebugUtilities::SetBreakpointEnabled(N,B,R.Operation==TEXT("enable"));
  else throw std::runtime_error("operation must be add, remove, enable, disable or clear_all");
 }
 return ListBreakpoints(R.AssetPath);
}

FString DebugFeedbackUtils::DebugState(const FString& Search,int32 Limit)
{
 if(Limit<1 || Limit>500 || Search.Len()>128) throw std::runtime_error("Debug state requires a bounded search and limit 1-500");
 FString Out; auto J=TJsonWriterFactory<>::Create(&Out); J->WriteObjectStart();
 const bool bPaused=GIntraFrameDebuggingGameThread; J->WriteValue(TEXT("paused"),bPaused); J->WriteValue(TEXT("auto_resumed"),bAutoResumed);
 if(bPaused)
 {
  J->WriteValue(TEXT("paused_seconds"),PauseStartSeconds>0 ? FPlatformTime::Seconds()-PauseStartSeconds : 0.0);
  J->WriteValue(TEXT("resume_after_seconds"),PauseTimeoutSeconds);
  if(const UEdGraphNode* N=FKismetDebugUtilities::GetCurrentInstruction()) { J->WriteObjectStart(TEXT("current")); WriteNode(J,N); if(const UBlueprint* B=FBlueprintEditorUtils::FindBlueprintForNode(N)) J->WriteValue(TEXT("bp_path"),B->GetPathName()); J->WriteObjectEnd(); }
  const TArrayView<const FFrame* const> Stack=FBlueprintContextTracker::Get().GetCurrentScriptStack();
  J->WriteArrayStart(TEXT("call_stack"));
  for(int32 I=Stack.Num()-1;I>=0;--I) { const FFrame* F=Stack[I]; J->WriteObjectStart(); J->WriteValue(TEXT("function"),F->Node ? F->Node->GetName() : FString()); J->WriteValue(TEXT("object"),F->Object ? F->Object->GetPathName() : FString()); J->WriteObjectEnd(); }
  J->WriteArrayEnd();
  if(Stack.Num()>0)
  {
   const FFrame* F=Stack.Last(); int32 Left=Limit;
   auto Matches=[&Search](const FProperty* P){ return Search.IsEmpty() || P->GetName().Contains(Search); };
   J->WriteObjectStart(TEXT("locals"));
   if(F->Node && F->Locals) for(TFieldIterator<FProperty> It(F->Node);It && Left>0;++It) if(Matches(*It))
   {
    FString V; It->ExportTextItem_Direct(V,It->ContainerPtrToValuePtr<void>(F->Locals),nullptr,nullptr,PPF_None); J->WriteValue(It->GetName(),V.Left(512)); --Left;
   }
   J->WriteObjectEnd();
   J->WriteObjectStart(TEXT("variables"));
   if(F->Object) for(TFieldIterator<FProperty> It(F->Object->GetClass());It && Left>0;++It)
    if(It->HasAnyPropertyFlags(CPF_BlueprintVisible) && Cast<UBlueprintGeneratedClass>(It->GetOwnerClass()) && Matches(*It))
    {
     FString V; It->ExportTextItem_InContainer(V,F->Object,nullptr,nullptr,PPF_None); J->WriteValue(It->GetName(),V.Left(512)); --Left;
    }
   J->WriteObjectEnd();
   J->WriteValue(TEXT("truncated"),Left==0);
  }
 }
 J->WriteObjectEnd(); J->Close(); return Out;
}

FString DebugFeedbackUtils::DebugControl(const FGameCoreReq& R)
{
 if(!GIntraFrameDebuggingGameThread) throw std::runtime_error("No Blueprint breakpoint is paused");
 bool bStep=true;
 if(R.Operation==TEXT("resume")) bStep=false;
 else if(R.Operation==TEXT("step_in")) FKismetDebugUtilities::RequestSingleStepIn();
 else if(R.Operation==TEXT("step_over")) FKismetDebugUtilities::RequestStepOver();
 else if(R.Operation==TEXT("step_out")) FKismetDebugUtilities::RequestStepOut();
 else throw std::runtime_error("operation must be resume, step_in, step_over or step_out");
 PauseStartSeconds=0; ResumeExecution(bStep);
 return FString::Printf(TEXT("{\"success\":true,\"operation\":\"%s\"}"),*R.Operation);
}

FString DebugFeedbackUtils::CreateCppClass(const FGameCoreReq& R)
{
 const TArray<FModuleContextInfo>& Modules=GameProjectUtils::GetCurrentProjectModules();
 // A copy: AddCodeToProject resets the engine's module list.
 FModuleContextInfo Module; bool bFound=false;
 for(const FModuleContextInfo& M:Modules) if(R.ModuleName.IsEmpty() ? M.ModuleType==EHostType::Runtime : M.ModuleName==R.ModuleName) { Module=M; bFound=true; break; }
 if(!bFound) throw std::runtime_error("Module not found in this project; it needs a C++ module");
 UClass* Parent=LoadObject<UClass>(nullptr,*R.ParentPath);
 if(!Parent || Parent->ClassGeneratedBy) throw std::runtime_error("parent_path must be a native class such as /Script/Engine.Actor");
 const TSet<FString> Disallowed; FText Fail;
 if(!GameProjectUtils::IsValidClassNameForCreation(R.ClassName,Module,Disallowed,Fail)) throw std::runtime_error(TCHAR_TO_UTF8(*Fail.ToString()));
 FString Out; auto J=TJsonWriterFactory<>::Create(&Out); J->WriteObjectStart(); J->WriteValue(TEXT("class_name"),R.ClassName); J->WriteValue(TEXT("module"),Module.ModuleName); J->WriteValue(TEXT("parent"),Parent->GetPathName()); J->WriteValue(TEXT("dry_run"),R.bDryRun);
 if(R.bDryRun) { J->WriteValue(TEXT("source_folder"),Module.ModuleSourcePath); J->WriteObjectEnd(); J->Close(); return Out; }
 if(!R.bConfirm) throw std::runtime_error("Creating a C++ class writes source files and requires confirm");
 if(GEditor->PlayWorld) throw std::runtime_error("Stop Play In Editor before creating a C++ class");
 FString Header,Cpp; GameProjectUtils::EReloadStatus Reload=GameProjectUtils::EReloadStatus::NotReloaded;
 const GameProjectUtils::EAddCodeToProjectResult Result=GameProjectUtils::AddCodeToProject(R.ClassName,Module.ModuleSourcePath,Module,FNewClassInfo(Parent),Disallowed,Header,Cpp,Fail,Reload);
 const bool bFilesWritten=FPaths::FileExists(Header) && FPaths::FileExists(Cpp);
 if(!bFilesWritten) throw std::runtime_error(TCHAR_TO_UTF8(*Fail.ToString()));
 J->WriteValue(TEXT("success"),true); J->WriteValue(TEXT("header"),Header); J->WriteValue(TEXT("source"),Cpp);
 const bool bLoaded=Result==GameProjectUtils::EAddCodeToProjectResult::Succeeded && FindObject<UClass>(nullptr,*FString::Printf(TEXT("/Script/%s.%s"),*Module.ModuleName,*R.ClassName))!=nullptr;
 J->WriteValue(TEXT("class_loaded"),bLoaded);
 J->WriteValue(TEXT("note"),bLoaded ? TEXT("The class is available in this editor session") : TEXT("Source files are written, but the class is not loaded. Close the editor, build the project and reopen it."));
 J->WriteObjectEnd(); J->Close(); return Out;
}

FString DebugFeedbackUtils::CxxCompileStatus()
{
#if PLATFORM_WINDOWS
 ILiveCodingModule* L=FModuleManager::LoadModulePtr<ILiveCodingModule>(LIVE_CODING_MODULE_NAME);
 if(!L) return TEXT("unavailable");
 if(L->IsCompiling()) return TEXT("compiling");
 return L->IsEnabledForSession() ? TEXT("idle") : TEXT("disabled");
#else
 return TEXT("unavailable");
#endif
}

FString DebugFeedbackUtils::LiveCodingStatus()
{
 FString Out; auto J=TJsonWriterFactory<>::Create(&Out); J->WriteObjectStart(); J->WriteValue(TEXT("status"),CxxCompileStatus());
#if PLATFORM_WINDOWS
 if(ILiveCodingModule* L=FModuleManager::LoadModulePtr<ILiveCodingModule>(LIVE_CODING_MODULE_NAME))
 {
  J->WriteValue(TEXT("enabled_by_default"),L->IsEnabledByDefault()); J->WriteValue(TEXT("enabled_for_session"),L->IsEnabledForSession()); J->WriteValue(TEXT("can_enable_for_session"),L->CanEnableForSession()); J->WriteValue(TEXT("has_started"),L->HasStarted());
  J->WriteValue(TEXT("enable_error"),L->GetEnableErrorText().ToString());
 }
#endif
 J->WriteObjectEnd(); J->Close(); return Out;
}

FString DebugFeedbackUtils::LiveCodingCompile(const FGameCoreReq& R)
{
#if PLATFORM_WINDOWS
 ILiveCodingModule* L=FModuleManager::LoadModulePtr<ILiveCodingModule>(LIVE_CODING_MODULE_NAME);
 if(!L) throw std::runtime_error("Live Coding is not available in this editor");
 if(!L->IsEnabledForSession())
 {
  if(!L->CanEnableForSession()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Live Coding can't be enabled: %s. Close the editor and build the project instead."),*L->GetEnableErrorText().ToString())));
  L->EnableForSession(true);
 }
 if(L->IsCompiling()) throw std::runtime_error("A Live Coding compile is already running");
 ELiveCodingCompileResult Result=ELiveCodingCompileResult::NotStarted;
 L->Compile(R.bWait ? ELiveCodingCompileFlags::WaitForCompletion : ELiveCodingCompileFlags::None,&Result);
 const TCHAR* Name=TEXT("not_started"); bool bOk=false;
 switch(Result)
 {
 case ELiveCodingCompileResult::Success: Name=TEXT("success"); bOk=true; break;
 case ELiveCodingCompileResult::NoChanges: Name=TEXT("no_changes"); bOk=true; break;
 case ELiveCodingCompileResult::InProgress: Name=TEXT("in_progress"); bOk=true; break;
 case ELiveCodingCompileResult::CompileStillActive: Name=TEXT("already_running"); break;
 case ELiveCodingCompileResult::Failure: Name=TEXT("failure"); break;
 case ELiveCodingCompileResult::Cancelled: Name=TEXT("cancelled"); break;
 default: break;
 }
 return FString::Printf(TEXT("{\"success\":%s,\"result\":\"%s\"}"),bOk ? TEXT("true") : TEXT("false"),Name);
#else
 throw std::runtime_error("Live Coding is only available on Windows");
#endif
}
