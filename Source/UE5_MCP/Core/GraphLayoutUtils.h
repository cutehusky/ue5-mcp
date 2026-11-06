#pragma once
#include "CoreMinimal.h"

class UBlueprint;
class UEdGraph;

// Layered graph layout: break cycles, assign columns, reduce crossings, then align rows along the wires.
namespace GraphLayoutUtils
{
	// Empty NodeIds formats the whole graph. Returns a JSON report with crossings and overlaps before and after.
	FString Format(UBlueprint* Blueprint, UEdGraph* Graph, const TArray<FString>& NodeIds, int32 ColumnSpacing, int32 RowSpacing, bool bDryRun);
}
