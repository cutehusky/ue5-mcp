#pragma once

#include "CoreMinimal.h"

class ISourceControlProvider;
class ISourceControlRevision;

namespace GitReadUtils
{
	bool History(ISourceControlProvider& Provider, const FString& Filename,
		TArray<TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe>>& Revisions, TArray<FString>& Errors);
}
