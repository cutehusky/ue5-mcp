// Copyright Epic Games, Inc. All Rights Reserved.

#include "UE5_MCP.h"

#include "HttpServerModule.h"
#include "UE5_MCP/Core/DebugFeedbackUtils.h"
#include "UE5_MCPStyle.h"
#include "UE5_MCPCommands.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"
#include "UE5_MCP/API/Route.h"
#include "UE5_MCP/API/Interface/HttpApp.h"
#include "UE5_MCP/Core/ModulationRuntimeUtils.h"
#include "UE5_MCP/Core/ModulationRecordingUtils.h"
#include "UE5_MCP/Core/AudioDiagnosticUtils.h"
#include "UE5_MCP/Core/AudioTraceUtils.h"
#include "UE5_MCP/Core/NavigationAreaUtils.h"
#include "UE5_MCP/Core/BlackboardUtils.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/Core/NavigationAgentUtils.h"
#include "UE5_MCP/Core/EnvironmentQueryRuntimeUtils.h"
#include "UE5_MCP/Core/QuartzEventUtils.h"
#include "Widgets/Input/SSpinBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SCheckBox.h"
#include "HAL/PlatformProcess.h"
#include "Misc/Paths.h"
#include "Interfaces/IPluginManager.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

class IHttpRouter;
static const FName UE5_MCPTabName("UE5_MCP");

#define LOCTEXT_NAMESPACE "FUE5_MCPModule"

void FUE5_MCPModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	
	FUE5_MCPStyle::Initialize();
	FUE5_MCPStyle::ReloadTextures();

	FUE5_MCPCommands::Register();
	
	PluginCommands = MakeShareable(new FUICommandList);

	PluginCommands->MapAction(
		FUE5_MCPCommands::Get().OpenPluginWindow,
		FExecuteAction::CreateRaw(this, &FUE5_MCPModule::PluginButtonClicked),
		FCanExecuteAction());

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FUE5_MCPModule::RegisterMenus));
	
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(UE5_MCPTabName, FOnSpawnTab::CreateRaw(this, &FUE5_MCPModule::OnSpawnPluginTab))
		.SetDisplayName(LOCTEXT("FUE5_MCPTabTitle", "UE5_MCP"))
		.SetMenuType(ETabSpawnerMenuType::Hidden);

	App = MakeShared<HttpApp>();
	BuildRouter(App);

	int32 CommandLineApiPort = 0;
	if (FParse::Value(FCommandLine::Get(), TEXT("UE5MCPApiPort="), CommandLineApiPort))
	{
		if (StartUnrealApiServer(false, CommandLineApiPort, nullptr))
		{
			UE_LOG(LogTemp, Display, TEXT("UE5_MCP API started from command line on port %d"), CommandLineApiPort);
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("UE5_MCP could not start command-line API on port %d"), CommandLineApiPort);
		}
	}
}

void FUE5_MCPModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	StopPythonServer(nullptr);
	StopUnrealApiServer(nullptr);

	ModulationRuntimeUtils::Shutdown();
	ModulationRecordingUtils::Shutdown();
	AudioDiagnosticUtils::Shutdown();
	AudioTraceUtils::Shutdown();
	NavigationAreaUtils::Shutdown();
	BlackboardUtils::Shutdown();
	StateTreeUtils::Shutdown();
	NavigationAgentUtils::Shutdown();
	EnvironmentQueryRuntimeUtils::Shutdown();
	QuartzEventUtils::Shutdown();

	FUE5_MCPStyle::Shutdown();

	FUE5_MCPCommands::Unregister();

	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(UE5_MCPTabName);
}

TSharedRef<SDockTab> FUE5_MCPModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
	const FString PluginBaseDir = IPluginManager::Get().FindPlugin(TEXT("UE5_MCP"))->GetBaseDir();
	const FString DefaultScriptPath = FPaths::Combine(PluginBaseDir, TEXT("Python/MCP/mcp_server.py"));
	TSharedPtr<SEditableTextBox> PythonExecutableBox;
	TSharedPtr<SEditableTextBox> ScriptPathBox;
	TSharedPtr<SSpinBox<int32>> ApiPortSpinBox;
	TSharedPtr<SSpinBox<int32>> McpPortSpinBox;
	TSharedPtr<SCheckBox> AutoAllocatePortCheckBox;
	TSharedPtr<STextBlock> ApiStatusText;
	TSharedPtr<STextBlock> StatusText;
	
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			SNew(SBox)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			[
				SNew(SVerticalBox)
	
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("ApiServerHeading", "Unreal API server"))
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("ApiPortLabel", "Unreal API port"))
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5)
				[
					SAssignNew(ApiPortSpinBox, SSpinBox<int32>)
					.MinValue(1)
					.MaxValue(65535)
					.Value(8080)
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5)
				[
					SAssignNew(AutoAllocatePortCheckBox, SCheckBox)
					.IsChecked(ECheckBoxState::Checked)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("AutoAllocatePort", "Use automatic port allocation"))
					]
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5)
				[
					SAssignNew(ApiStatusText, STextBlock)
					.Text(LOCTEXT("ApiStopped", "Unreal API server: stopped"))
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5)
				[
					SNew(SButton)
					.Text(LOCTEXT("StartApiServer", "Start Unreal API server"))
					.OnClicked_Lambda([ApiPortSpinBox, AutoAllocatePortCheckBox, ApiStatusText, this]() -> FReply
					{
						StartUnrealApiServer(AutoAllocatePortCheckBox->IsChecked(), ApiPortSpinBox->GetValue(), ApiStatusText);
						return FReply::Handled();
					})
				]
	
				+ SVerticalBox::Slot()
				.Padding(5)
				[
					SNew(SButton)
					.Text(LOCTEXT("StopApiServer", "Stop Unreal API server"))
					.OnClicked_Lambda([ApiStatusText, this]() -> FReply
					{
						StopUnrealApiServer(ApiStatusText);
						return FReply::Handled();
					})
				]

				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 16, 5, 5)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("PythonServerHeading", "Python MCP server"))
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SAssignNew(PythonExecutableBox, SEditableTextBox)
					.Text(FText::FromString(TEXT("python")))
					.HintText(LOCTEXT("PythonExecutableHint", "Python executable (python, py, or full path)"))
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SAssignNew(ScriptPathBox, SEditableTextBox)
					.Text(FText::FromString(DefaultScriptPath))
					.HintText(LOCTEXT("ScriptPathHint", "Path to mcp_server.py"))
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("McpPortLabel", "MCP server port"))
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SAssignNew(McpPortSpinBox, SSpinBox<int32>)
					.MinValue(1)
					.MaxValue(65535)
					.Value(9000)
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SAssignNew(StatusText, STextBlock)
					.Text(LOCTEXT("PythonStopped", "Python MCP server: stopped"))
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SNew(SButton)
					.Text(LOCTEXT("StartPythonServer", "Run Python MCP server"))
					.OnClicked_Lambda([PythonExecutableBox, ScriptPathBox, ApiPortSpinBox, AutoAllocatePortCheckBox, McpPortSpinBox, ApiStatusText, StatusText, this]() -> FReply
					{
						if (UnrealApiPort == 0 && !StartUnrealApiServer(AutoAllocatePortCheckBox->IsChecked(), ApiPortSpinBox->GetValue(), ApiStatusText)) return FReply::Handled();
						StartPythonServer(PythonExecutableBox->GetText().ToString(), ScriptPathBox->GetText().ToString(), McpPortSpinBox->GetValue(), StatusText);
						return FReply::Handled();
					})
				]

				+ SVerticalBox::Slot().AutoHeight().Padding(5)
				[
					SNew(SButton)
					.Text(LOCTEXT("StopPythonServer", "Stop Python MCP server"))
					.OnClicked_Lambda([StatusText, this]() -> FReply
					{
						StopPythonServer(StatusText);
						return FReply::Handled();
					})
				]
			]
		];
	
}

int32 FUE5_MCPModule::FindAvailablePort() const
{
	for (int32 Port = 8080; Port <= 65535; ++Port)
	{
		if (IsPortAvailable(Port)) return Port;
	}

	return 0;
}

bool FUE5_MCPModule::IsPortAvailable(int32 Port) const
{
	if (Port < 1 || Port > 65535) return false;

	ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!SocketSubsystem) return false;

	FSocket* ProbeSocket = SocketSubsystem->CreateSocket(NAME_Stream, TEXT("UE5_MCP_PortProbe"), false);
	if (!ProbeSocket) return false;

	TSharedRef<FInternetAddr> Address = SocketSubsystem->CreateInternetAddr();
	Address->SetAnyAddress();
	Address->SetPort(Port);
	const bool bAvailable = ProbeSocket->Bind(*Address);
	SocketSubsystem->DestroySocket(ProbeSocket);
	return bAvailable;
}

bool FUE5_MCPModule::StartUnrealApiServer(bool bAutoAllocatePort, int32 RequestedPort, const TSharedPtr<STextBlock>& StatusText)
{
	if (UnrealApiPort > 0)
	{
		if (StatusText.IsValid()) StatusText->SetText(FText::Format(LOCTEXT("ApiAlreadyRunning", "Unreal API server: running on port {0}"), FText::AsNumber(UnrealApiPort)));
		return true;
	}

	UnrealApiPort = bAutoAllocatePort ? FindAvailablePort() : RequestedPort;
	if (UnrealApiPort == 0)
	{
		if (StatusText.IsValid()) StatusText->SetText(LOCTEXT("ApiStartFailed", "Unreal API server: no free port found"));
		return false;
	}
	if (!bAutoAllocatePort && !IsPortAvailable(UnrealApiPort))
	{
		if (StatusText.IsValid()) StatusText->SetText(FText::Format(LOCTEXT("ApiPortUnavailable", "Unreal API server: port {0} is unavailable"), FText::AsNumber(UnrealApiPort)));
		UnrealApiPort = 0;
		return false;
	}

	const auto Router = FHttpServerModule::Get().GetHttpRouter(UnrealApiPort);
	App->Bind(Router);
	DebugFeedbackUtils::Install(Router);
	FHttpServerModule::Get().StartAllListeners();
	if (StatusText.IsValid()) StatusText->SetText(FText::Format(LOCTEXT("ApiRunning", "Unreal API server: running on port {0}"), FText::AsNumber(UnrealApiPort)));
	return true;
}

void FUE5_MCPModule::StopUnrealApiServer(const TSharedPtr<STextBlock>& StatusText)
{
	if (UnrealApiPort > 0 && FModuleManager::Get().IsModuleLoaded(TEXT("HTTPServer")))
		FHttpServerModule::Get().StopAllListeners();
	UnrealApiPort = 0;
	if (StatusText.IsValid()) StatusText->SetText(LOCTEXT("ApiStoppedAfterStop", "Unreal API server: stopped"));
}

bool FUE5_MCPModule::IsPythonServerRunning()
{
	return PythonServerProcess.IsValid() && FPlatformProcess::IsProcRunning(PythonServerProcess);
}

void FUE5_MCPModule::StartPythonServer(const FString& PythonExecutable, const FString& ScriptPath, int32 McpPort, const TSharedPtr<STextBlock>& StatusText)
{
	if (IsPythonServerRunning())
	{
		if (StatusText.IsValid()) StatusText->SetText(LOCTEXT("PythonAlreadyRunning", "Python MCP server: already running"));
		return;
	}

	if (PythonExecutable.IsEmpty() || ScriptPath.IsEmpty() || McpPort < 1 || McpPort > 65535 || UnrealApiPort < 1 || UnrealApiPort > 65535)
	{
		if (StatusText.IsValid()) StatusText->SetText(LOCTEXT("PythonInvalidSettings", "Python MCP server: invalid settings"));
		return;
	}

	const FString FullScriptPath = FPaths::ConvertRelativePathToFull(ScriptPath);
	const FString Arguments = FString::Printf(TEXT("\"%s\" --port %d --ue-api-url http://localhost:%d"), *FullScriptPath, McpPort, UnrealApiPort);
	uint32 ProcessId = 0;
	PythonServerProcess = FPlatformProcess::CreateProc(*PythonExecutable, *Arguments, true, false, false, &ProcessId, 0, *FPaths::GetPath(FullScriptPath), nullptr, nullptr);

	if (PythonServerProcess.IsValid())
	{
		if (StatusText.IsValid()) StatusText->SetText(FText::Format(LOCTEXT("PythonRunning", "Python MCP server: running (PID {0})"), FText::AsNumber(ProcessId)));
	}
	else if (StatusText.IsValid())
	{
		StatusText->SetText(LOCTEXT("PythonStartFailed", "Python MCP server: failed to start"));
	}
}

void FUE5_MCPModule::StopPythonServer(const TSharedPtr<STextBlock>& StatusText)
{
	if (PythonServerProcess.IsValid())
	{
		if (FPlatformProcess::IsProcRunning(PythonServerProcess)) FPlatformProcess::TerminateProc(PythonServerProcess, true);
		FPlatformProcess::CloseProc(PythonServerProcess);
		PythonServerProcess.Reset();
	}

	if (StatusText.IsValid()) StatusText->SetText(LOCTEXT("PythonStoppedAfterStop", "Python MCP server: stopped"));
}

void FUE5_MCPModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(UE5_MCPTabName);
}

TSharedPtr<class HttpApp> FUE5_MCPModule::GetApp()
{
	return App;
}

void FUE5_MCPModule::RegisterMenus()
{
	// Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
	FToolMenuOwnerScoped OwnerScoped(this);

	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
		{
			FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
			Section.AddMenuEntryWithCommandList(FUE5_MCPCommands::Get().OpenPluginWindow, PluginCommands);
		}
	}

	{
		UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
		{
			FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("Settings");
			{
				FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FUE5_MCPCommands::Get().OpenPluginWindow));
				Entry.SetCommandList(PluginCommands);
			}
		}
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FUE5_MCPModule, UE5_MCP)
