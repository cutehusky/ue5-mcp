#pragma once
#include "CoreMinimal.h"
#include "NavigationSmartObserver.generated.h"

/** Transient multicast listener; leaves the proxy's native movement delegate intact. */
UCLASS(Transient)
class UNavigationSmartObserver : public UObject
{
	GENERATED_BODY()
public:
	TFunction<void(AActor*, const FVector&)> Callback;
	UFUNCTION() void Reached(AActor* MovingActor, const FVector& DestinationPoint);
};
