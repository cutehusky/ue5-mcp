#pragma once
#include "CoreMinimal.h"
struct FWorldSettingsReq;
namespace WorldSettingsUtils
{
	FString InspectCompositionTiles(const FWorldSettingsReq& Request);
	FString SetCompositionSetting(const FWorldSettingsReq& Request);
	FString SetCompositionTileLayer(const FWorldSettingsReq& Request);
	FString SetCompositionTileDisplay(const FWorldSettingsReq& Request);
	FString SetCompositionTileLODDistance(const FWorldSettingsReq& Request);
	FString SetCompositionTileLODList(const FWorldSettingsReq& Request);
	FString InspectCompositionTileHierarchy(const FWorldSettingsReq& Request);
	FString InspectLegacyHLODLevels(const FWorldSettingsReq& Request);
	FString SetLegacyHLODLevelNumeric(const FWorldSettingsReq& Request);
	FString SetLegacyHLODLevelBool(const FWorldSettingsReq& Request);
	FString SetLegacyHLODLevelMethod(const FWorldSettingsReq& Request);
	FString InspectLegacyHLODFields(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedNumeric(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedBool(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedEnum(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedObject(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedName(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedString(const FWorldSettingsReq& Request);
	FString AddLegacyHLODLevel(const FWorldSettingsReq& Request);
	FString DuplicateLegacyHLODLevel(const FWorldSettingsReq& Request);
	FString RemoveLegacyHLODLevel(const FWorldSettingsReq& Request);
	FString InspectLegacyLODActors(const FWorldSettingsReq& Request);
	FString ReorderLegacyHLODLevels(const FWorldSettingsReq& Request);
	FString SetLegacyHLODSetupOverride(const FWorldSettingsReq& Request);
	FString InspectLegacyHLODSetupClasses(const FWorldSettingsReq& Request);
	FString SetLegacyHLODMaterialOverride(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedIntPoint(const FWorldSettingsReq& Request);
	FString SetLegacyHLODNestedColor(const FWorldSettingsReq& Request);
	FString ResetLegacyHLODLevel(const FWorldSettingsReq& Request);
	FString Inspect();
	FString Update(const FWorldSettingsReq& Request);
}
