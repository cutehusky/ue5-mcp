// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"
#include "HAL/PlatformProcess.h"

class FToolBarBuilder;
class FMenuBuilder;

class FUE5_MCPModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	
	/** This function will be bound to Command (by default it will bring up plugin window) */
	void PluginButtonClicked();

	TSharedPtr<class HttpApp> GetApp();

private:

	void RegisterMenus();

	TSharedRef<class SDockTab> OnSpawnPluginTab(const class FSpawnTabArgs& SpawnTabArgs);

private:
	TSharedPtr<class FUICommandList> PluginCommands;
	TSharedPtr<class HttpApp> App;
	FProcHandle PythonServerProcess;
	int32 UnrealApiPort = 0;

	bool StartUnrealApiServer(bool bAutoAllocatePort, int32 RequestedPort, const TSharedPtr<class STextBlock>& StatusText);
	void StopUnrealApiServer(const TSharedPtr<class STextBlock>& StatusText);
	bool IsPortAvailable(int32 Port) const;
	int32 FindAvailablePort() const;
	void StartPythonServer(const FString& PythonExecutable, const FString& ScriptPath, int32 McpPort, const TSharedPtr<class STextBlock>& StatusText);
	void StopPythonServer(const TSharedPtr<class STextBlock>& StatusText);
	bool IsPythonServerRunning();
};
