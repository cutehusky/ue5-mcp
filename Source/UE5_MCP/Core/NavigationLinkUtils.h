#pragma once
#include "CoreMinimal.h"
struct FNavigationLinkReq;
namespace NavigationLinkUtils
{
	FString Inspect(const FString& ActorPath,const FString& WorldContext=TEXT("editor"),int32 PIEInstance=-1);
	FString Control(const FNavigationLinkReq& R);
	FString Smart(const FNavigationLinkReq& R);
}
