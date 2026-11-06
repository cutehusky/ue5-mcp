#pragma once

#include "CoreMinimal.h"

class USoundAttenuation;
struct FAudioAttenuationSettingsReq;
struct FAudioAttenuationCurveReq;
struct FAudioAttenuationEvaluateReq;
struct FAudioAttenuationSubmixSendReq;
struct FAudioAttenuationPluginReq;
struct FAudioPluginSettingsCreateReq;

namespace SoundAttenuationUtils
{
	FString SettingsJson(USoundAttenuation* Asset);
	FString EditSettings(USoundAttenuation* Asset, const FAudioAttenuationSettingsReq& Request);
	FString EditCurve(USoundAttenuation* Asset, const FAudioAttenuationCurveReq& Request);
	FString Validate(USoundAttenuation* Asset);
	FString Evaluate(USoundAttenuation* Asset, const FAudioAttenuationEvaluateReq& Request);
	FString EditSubmixSend(USoundAttenuation* Asset, const FAudioAttenuationSubmixSendReq& Request);
	FString EditPlugin(USoundAttenuation* Asset, const FAudioAttenuationPluginReq& Request);
	FString PluginClassesJson();
	FString CreatePluginSettings(const FAudioPluginSettingsCreateReq& Request);
}
