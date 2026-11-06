#pragma once
#include "CoreMinimal.h"
struct FNavigationAreaReq;
namespace NavigationAreaUtils
{
	FString Inspect(const FString& AssetPath);
	FString Control(const FNavigationAreaReq& R);
	void Shutdown();
}
