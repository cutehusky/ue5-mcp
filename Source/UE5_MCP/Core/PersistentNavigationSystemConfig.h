#pragma once
#include "CoreMinimal.h"
#include "NavigationSystem.h"
#include "PersistentNavigationSystemConfig.generated.h"

/** Native module-config behavior with complete per-map field serialization.
 * UE initializes module-config flags from project defaults in PostInitProperties;
 * delta-skipped false values could otherwise be replaced by those defaults on load.
 */
UCLASS(EditInlineNew, DisplayName="Persistent Navigation System Config")
class UE5_MCP_API UPersistentNavigationSystemConfig : public UNavigationSystemModuleConfig
{
	GENERATED_BODY()
public:
	virtual void Serialize(FArchive& Ar) override;
};
