#pragma once
#include "CoreMinimal.h"
struct FNavigationFilterReq;
namespace NavigationFilterUtils
{
	FString Inspect(const FString& AssetPath);
	FString Control(const FNavigationFilterReq& R);
}
