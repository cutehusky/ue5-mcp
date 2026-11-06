#pragma once
#include "CoreMinimal.h"
struct FAtmosphereReq;
namespace AtmosphereUtils { FString InspectWorldPage(const FAtmosphereReq& R); FString SetTransform(const FAtmosphereReq& R); FString Create(const FAtmosphereReq& R); FString Delete(const FAtmosphereReq& R); FString SetTransformMode(const FAtmosphereReq& R); FString SetAbsorptionTent(const FAtmosphereReq& R); FString SetVisible(const FAtmosphereReq& R); FString SetColor(const FAtmosphereReq& R); FString SetGroundAlbedo(const FAtmosphereReq& R); FString InspectWorld(); FString SetScalar(const FAtmosphereReq& R); FString SetBool(const FAtmosphereReq& R); }
