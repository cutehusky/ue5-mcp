#pragma once
#include "CoreMinimal.h"
struct FNavigationReq;
namespace NavigationUtils
{
	FString Inspect();
	FString Bounds(const FNavigationReq& R);
	FString Modifiers(const FNavigationReq& R);
	FString Build(const FNavigationReq& R);
	FString Query(const FNavigationReq& R);
}
