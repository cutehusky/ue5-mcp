#include "NavigationSmartObserver.h"
void UNavigationSmartObserver::Reached(AActor* MovingActor, const FVector& DestinationPoint)
{
	if (Callback) Callback(MovingActor, DestinationPoint);
}
