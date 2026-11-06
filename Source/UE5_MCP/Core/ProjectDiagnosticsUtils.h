#pragma once
#include "CoreMinimal.h"

// Class search, console commands, and project-wide errors and logs.
namespace ProjectDiagnosticsUtils
{
	struct FClassQuery
	{
		FString Search, Parent, Category, Source, Module;
		bool bCanBeParent = false;
		bool bIncludeAbstract = false;
		int32 Limit = 200;
	};
	FString ListClasses(const FClassQuery& Query);
	FString ExecuteConsole(const FString& Command, bool bConfirm);
	FString ListBlueprintErrors(const FString& Root, const FString& Search, bool bIncludeWarnings, int32 Limit);
	FString ProjectErrors(int32 Limit);
	FString ReadLogs(const FString& Search, const FString& Severity, const FString& Category, int32 SinceLine, int32 Limit);
}
