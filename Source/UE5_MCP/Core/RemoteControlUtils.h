#pragma once
#include "CoreMinimal.h"
struct FRemoteControlReq;
namespace RemoteControlUtils
{
 FString List(const FString& Search,int32 Limit);
 FString Inspect(const FString& AssetPath);
 FString Create(const FRemoteControlReq& R);
 FString Expose(const FRemoteControlReq& R);
 FString Unexpose(const FRemoteControlReq& R);
 FString SetValue(const FRemoteControlReq& R);
}
