// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Framework/Commands/Commands.h"
#include "UE5_MCPStyle.h"

class FUE5_MCPCommands : public TCommands<FUE5_MCPCommands>
{
public:

	FUE5_MCPCommands()
		: TCommands<FUE5_MCPCommands>(TEXT("UE5_MCP"), NSLOCTEXT("Contexts", "UE5_MCP", "UE5_MCP Plugin"), NAME_None, FUE5_MCPStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > OpenPluginWindow;
};