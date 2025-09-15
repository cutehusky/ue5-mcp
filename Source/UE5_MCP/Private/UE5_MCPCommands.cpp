// Copyright Epic Games, Inc. All Rights Reserved.

#include "UE5_MCPCommands.h"

#define LOCTEXT_NAMESPACE "FUE5_MCPModule"

void FUE5_MCPCommands::RegisterCommands()
{
	UI_COMMAND(OpenPluginWindow, "UE5_MCP", "Bring up UE5_MCP window", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
