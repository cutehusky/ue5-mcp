#pragma once
#include "CoreMinimal.h"
struct FDecalReq;
namespace DecalUtils { FString InspectMaterialUsers(const FDecalReq& R); FString InspectLoadedMaterials(const FDecalReq& R); FString InspectMobility(const FDecalReq& R); FString SetMobility(const FDecalReq& R); FString InspectReceivers(const FDecalReq& R); FString SetReceiver(const FDecalReq& R); FString Create(const FDecalReq& R); FString Delete(const FDecalReq& R); FString SetPlacement(const FDecalReq& R); FString SetAppearance(const FDecalReq& R); FString SetMaterial(const FDecalReq& R); FString InspectPage(const FDecalReq& R); FString SetSetting(const FDecalReq& R); }
