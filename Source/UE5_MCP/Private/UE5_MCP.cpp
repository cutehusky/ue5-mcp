// Copyright Epic Games, Inc. All Rights Reserved.

#include "UE5_MCP.h"

#include "HttpServerModule.h"
#include "UE5_MCPStyle.h"
#include "UE5_MCPCommands.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"
#include "UE5_MCP/API/Route.h"
#include "Widgets/Input/SSpinBox.h"

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
}

void FUE5_MCPModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FUE5_MCPStyle::Shutdown();

	FUE5_MCPCommands::Unregister();

	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(UE5_MCPTabName);
}

TSharedRef<SDockTab> FUE5_MCPModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
	TSharedPtr<SSpinBox<int32>> PortSpinBox;
	
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			SNew(SBox)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			[
				SNew(SVerticalBox)
	
				+ SVerticalBox::Slot()
				.Padding(5)
				[
					SNew(STextBlock)
					.Text(FText::FromString("Port:"))
				]
	
				// Number box
				+ SVerticalBox::Slot()
				.Padding(5)
				[
					SAssignNew(PortSpinBox, SSpinBox<int32>)
					.MinValue(1)          // valid port range
					.MaxValue(65535)
					.Value(8080)          // default value
				]
	
				// Button
				+ SVerticalBox::Slot()
				.Padding(5)
				[
					SNew(SButton)
					.Text(FText::FromString("Run Server"))
					.OnClicked_Lambda([PortSpinBox]() -> FReply
					{
						if (PortSpinBox.IsValid())
						{
							int32 Port = PortSpinBox->GetValue();
						
							if (Port <= 0 || Port > 65535)
							{
								UE_LOG(LogTemp, Error, TEXT("Invalid port number: %d"), Port);
							}
							else
							{
								auto Router = FHttpServerModule::Get().GetHttpRouter(Port);
								Router::Bind(Router);
								FHttpServerModule::Get().StartAllListeners();
							}
						}
						return FReply::Handled();
					})
				]
	
				+ SVerticalBox::Slot()
				.Padding(5)
				[
					SNew(SButton)
					.Text(FText::FromString("Stop Server"))
					.OnClicked_Lambda([PortSpinBox]() -> FReply
					{
						FHttpServerModule::Get().StopAllListeners();
						return FReply::Handled();
					})
				]
			]
		];
	
}

void FUE5_MCPModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(UE5_MCPTabName);
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