#pragma once
#include "CoreMinimal.h"
struct FGameCoreReq;
// Core game-making loop: class defaults, project game settings, playtesting in PIE and packaging.
namespace GameCoreUtils
{
 FString CreateAsset(const FGameCoreReq& R);
 FString ImportFbx(const FGameCoreReq& R);
 FString InspectClassDefaults(const FString& AssetPath,const FString& Search,int32 Limit);
 FString SetClassDefault(const FGameCoreReq& R);
 FString InspectGameSettings();
 FString SetGameSetting(const FGameCoreReq& R);
 FString InspectPlaySession(const FString& Search,int32 Limit);
 FString ReadPlayActorProperties(const FString& Actor,const FString& Search,int32 Limit);
 FString SendPlayInput(const FGameCoreReq& R);
 FString MovePlayMouse(const FGameCoreReq& R);
 FString StartPackage(const FGameCoreReq& R);
 FString PackageStatus(int32 LogLines);
 FString CancelPackage();
}
