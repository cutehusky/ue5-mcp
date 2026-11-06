#include "PersistentNavigationSystemConfig.h"

void UPersistentNavigationSystemConfig::Serialize(FArchive& Ar)
{
	const bool PreviousNoDelta=Ar.ArNoDelta;
	if(Ar.IsSaving() && Ar.IsPersistent()) Ar.ArNoDelta=true;
	Super::Serialize(Ar);
	Ar.ArNoDelta=PreviousNoDelta;
}
