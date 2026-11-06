#pragma once
#include "CoreMinimal.h"
struct FCloudReq;
namespace CloudUtils { FString InspectWorldPage(const FCloudReq& R); FString SetTransform(const FCloudReq& R); FString Create(const FCloudReq& R); FString Delete(const FCloudReq& R); FString SetMaterial(const FCloudReq& R); FString SetGroundAlbedo(const FCloudReq& R); FString SetVisible(const FCloudReq& R); FString SetTracingMode(const FCloudReq& R); FString InspectWorld(); FString SetScalar(const FCloudReq& R); FString SetBool(const FCloudReq& R); }
