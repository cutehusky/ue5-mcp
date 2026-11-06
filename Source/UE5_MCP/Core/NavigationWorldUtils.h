#pragma once
#include "CoreMinimal.h"
class UWorld;
namespace NavigationWorldUtils
{
	UWorld* Resolve(const FString& Context=TEXT("editor"),int32 PIEInstance=-1);
}
