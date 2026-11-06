#include "SoundAttenuationUtils.h"
#include "UE5_MCP/API/DTO/AudioAttenuationSettingsReq.h"
#include "Editor.h"
#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "IAudioExtensionPlugin.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "ScopedTransaction.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundSubmix.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectIterator.h"
#include "UObject/StructOnScope.h"
#include "Serialization/JsonWriter.h"

#include <stdexcept>

namespace
{
	struct FAttenuationField { const TCHAR* Name; const TCHAR* Property; };
	struct FNumber { const TCHAR* Name; const TCHAR* Property; double Min = 0.0; double Max = MAX_flt; };
	const FNumber Numbers[] = {
		{TEXT("falloff_distance"), TEXT("FalloffDistance")},
		{TEXT("cone_offset"), TEXT("ConeOffset")},
		{TEXT("cone_sphere_radius"), TEXT("ConeSphereRadius")},
		{TEXT("cone_sphere_falloff_distance"), TEXT("ConeSphereFalloffDistance")},
		{TEXT("attenuation_at_max_db"), TEXT("dBAttenuationAtMax"), -60.0, 0.0},
		{TEXT("binaural_radius"), TEXT("BinauralRadius")},
		{TEXT("non_spatialized_radius_start"), TEXT("NonSpatializedRadiusStart")},
		{TEXT("non_spatialized_radius_end"), TEXT("NonSpatializedRadiusEnd")},
		{TEXT("stereo_spread"), TEXT("StereoSpread")},
		{TEXT("air_absorption_distance_min"), TEXT("LPFRadiusMin")},
		{TEXT("air_absorption_distance_max"), TEXT("LPFRadiusMax")},
		{TEXT("lowpass_frequency_at_min"), TEXT("LPFFrequencyAtMin"), 0.0, 20000.0},
		{TEXT("lowpass_frequency_at_max"), TEXT("LPFFrequencyAtMax"), 0.0, 20000.0},
		{TEXT("highpass_frequency_at_min"), TEXT("HPFFrequencyAtMin"), 0.0, 20000.0},
		{TEXT("highpass_frequency_at_max"), TEXT("HPFFrequencyAtMax"), 0.0, 20000.0},
		{TEXT("focus_azimuth"), TEXT("FocusAzimuth"), 0.0, 180.0},
		{TEXT("non_focus_azimuth"), TEXT("NonFocusAzimuth"), 0.0, 180.0},
		{TEXT("focus_distance_scale"), TEXT("FocusDistanceScale")},
		{TEXT("non_focus_distance_scale"), TEXT("NonFocusDistanceScale")},
		{TEXT("focus_priority_scale"), TEXT("FocusPriorityScale")},
		{TEXT("non_focus_priority_scale"), TEXT("NonFocusPriorityScale")},
		{TEXT("focus_volume_attenuation"), TEXT("FocusVolumeAttenuation")},
		{TEXT("non_focus_volume_attenuation"), TEXT("NonFocusVolumeAttenuation")},
		{TEXT("focus_attack_interp_speed"), TEXT("FocusAttackInterpSpeed")},
		{TEXT("focus_release_interp_speed"), TEXT("FocusReleaseInterpSpeed")},
		{TEXT("occlusion_lowpass_frequency"), TEXT("OcclusionLowPassFilterFrequency"), 0.0, 20000.0},
		{TEXT("occlusion_volume_attenuation"), TEXT("OcclusionVolumeAttenuation")},
		{TEXT("occlusion_interpolation_time"), TEXT("OcclusionInterpolationTime")},
		{TEXT("reverb_wet_level_min"), TEXT("ReverbWetLevelMin"), 0.0, 1.0},
		{TEXT("reverb_wet_level_max"), TEXT("ReverbWetLevelMax"), 0.0, 1.0},
		{TEXT("reverb_distance_min"), TEXT("ReverbDistanceMin")},
		{TEXT("reverb_distance_max"), TEXT("ReverbDistanceMax")},
		{TEXT("manual_reverb_send_level"), TEXT("ManualReverbSendLevel"), 0.0, 1.0},
		{TEXT("priority_attenuation_min"), TEXT("PriorityAttenuationMin")},
		{TEXT("priority_attenuation_max"), TEXT("PriorityAttenuationMax")},
		{TEXT("priority_distance_min"), TEXT("PriorityAttenuationDistanceMin")},
		{TEXT("priority_distance_max"), TEXT("PriorityAttenuationDistanceMax")},
		{TEXT("manual_priority_attenuation"), TEXT("ManualPriorityAttenuation")}
	};
	const FAttenuationField Flags[] = {
		{TEXT("attenuate"), TEXT("bAttenuate")}, {TEXT("spatialize"), TEXT("bSpatialize")},
		{TEXT("air_absorption"), TEXT("bAttenuateWithLPF")},
		{TEXT("listener_focus"), TEXT("bEnableListenerFocus")},
		{TEXT("focus_interpolation"), TEXT("bEnableFocusInterpolation")},
		{TEXT("occlusion"), TEXT("bEnableOcclusion")},
		{TEXT("complex_occlusion_collision"), TEXT("bUseComplexCollisionForOcclusion")},
		{TEXT("reverb_send"), TEXT("bEnableReverbSend")},
		{TEXT("priority_attenuation"), TEXT("bEnablePriorityAttenuation")},
		{TEXT("normalize_stereo"), TEXT("bApplyNormalizationToStereoSounds")},
		{TEXT("log_frequency_scaling"), TEXT("bEnableLogFrequencyScaling")},
		{TEXT("submix_sends"), TEXT("bEnableSubmixSends")},
		{TEXT("source_data_override"), TEXT("bEnableSourceDataOverride")},
		{TEXT("send_to_audio_link"), TEXT("bEnableSendToAudioLink")}
	};
	const FAttenuationField Enums[] = {
		{TEXT("distance_algorithm"), TEXT("DistanceAlgorithm")},
		{TEXT("attenuation_shape"), TEXT("AttenuationShape")},
		{TEXT("falloff_mode"), TEXT("FalloffMode")},
		{TEXT("spatialization_algorithm"), TEXT("SpatializationAlgorithm")},
		{TEXT("absorption_method"), TEXT("AbsorptionMethod")},
		{TEXT("non_spatialized_radius_mode"), TEXT("NonSpatializedRadiusMode")},
		{TEXT("occlusion_trace_channel"), TEXT("OcclusionTraceChannel")},
		{TEXT("reverb_send_method"), TEXT("ReverbSendMethod")},
		{TEXT("priority_attenuation_method"), TEXT("PriorityAttenuationMethod")}
	};
	const TCHAR* CurveNames[] = {TEXT("attenuation"), TEXT("lowpass_absorption"), TEXT("highpass_absorption"), TEXT("reverb_send"), TEXT("priority")};
	const TCHAR* PluginTypes[] = {TEXT("spatialization"), TEXT("occlusion"), TEXT("reverb"), TEXT("source_data_override")};
	UClass* PluginBase(const FString& Type)
	{
		if (Type == TEXT("spatialization")) return USpatializationPluginSourceSettingsBase::StaticClass();
		if (Type == TEXT("occlusion")) return UOcclusionPluginSourceSettingsBase::StaticClass();
		if (Type == TEXT("reverb")) return UReverbPluginSourceSettingsBase::StaticClass();
		if (Type == TEXT("source_data_override")) return USourceDataOverridePluginSourceSettingsBase::StaticClass();
		throw std::runtime_error("plugin_type must be spatialization, occlusion, reverb, or source_data_override");
	}
	FArrayProperty* PluginArrayProperty(const FString& Type)
	{
		PluginBase(Type);
		const TCHAR* Name = Type == TEXT("spatialization") ? TEXT("SpatializationPluginSettingsArray")
			: Type == TEXT("occlusion") ? TEXT("OcclusionPluginSettingsArray")
			: Type == TEXT("reverb") ? TEXT("ReverbPluginSettingsArray") : TEXT("SourceDataOverridePluginSettingsArray");
		FArrayProperty* Result = FindFProperty<FArrayProperty>(FSoundAttenuationPluginSettings::StaticStruct(), FName(Name));
		if (!Result || !CastField<FObjectPropertyBase>(Result->Inner)) throw std::runtime_error("Native plugin settings array is unavailable");
		return Result;
	}
	TArray<UObject*> PluginObjects(const FSoundAttenuationSettings& S, const FString& Type)
	{
		FArrayProperty* P = PluginArrayProperty(Type);
		FScriptArrayHelper Helper(P, P->ContainerPtrToValuePtr<void>(const_cast<FSoundAttenuationPluginSettings*>(&S.PluginSettings)));
		FObjectPropertyBase* Inner = CastFieldChecked<FObjectPropertyBase>(P->Inner);
		TArray<UObject*> Result;
		for (int32 Index = 0; Index < Helper.Num(); ++Index) Result.Add(Inner->GetObjectPropertyValue(Helper.GetRawPtr(Index)));
		return Result;
	}

	FProperty* Property(const TCHAR* Name)
	{
		FProperty* Result = FindFProperty<FProperty>(FSoundAttenuationSettings::StaticStruct(), FName(Name));
		if (!Result) throw std::runtime_error("Required UE attenuation property is unavailable");
		return Result;
	}
	template<typename T, size_t N> const T* FindField(const T (&Fields)[N], const FString& Name)
	{
		for (const T& Field : Fields) if (Name.Equals(Field.Name, ESearchCase::IgnoreCase)) return &Field;
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Unknown attenuation setting: %s"), *Name)));
	}
	FNumericProperty* NumberProperty(const TCHAR* Name)
	{
		FNumericProperty* Result = CastField<FNumericProperty>(Property(Name));
		if (!Result || !Result->IsFloatingPoint()) throw std::runtime_error("UE attenuation numeric property type is incompatible");
		return Result;
	}
	double NumberValue(const FSoundAttenuationSettings& S, const TCHAR* Name)
	{
		FNumericProperty* P = NumberProperty(Name);
		return P->GetFloatingPointPropertyValue(P->ContainerPtrToValuePtr<void>(&S));
	}
	UEnum* EnumType(FProperty* P)
	{
		if (FEnumProperty* E = CastField<FEnumProperty>(P)) return E->GetEnum();
		if (FByteProperty* B = CastField<FByteProperty>(P)) return B->Enum;
		throw std::runtime_error("UE attenuation enum property type is incompatible");
	}
	FNumericProperty* EnumStorage(FProperty* P)
	{
		if (FEnumProperty* E = CastField<FEnumProperty>(P)) return E->GetUnderlyingProperty();
		return CastFieldChecked<FByteProperty>(P);
	}
	bool AllowedEnumIndex(UEnum* Enum, int32 Index)
	{
		if (Index == INDEX_NONE || Enum->HasMetaData(TEXT("Hidden"), Index)) return false;
		const FString Name = Enum->GetNameStringByIndex(Index);
		return !Name.EndsWith(TEXT("MAX")) && !Name.Contains(TEXT("Deprecated"));
	}
	int64 ParseEnum(FProperty* P, const FString& Value)
	{
		UEnum* Enum = EnumType(P);
		for (int32 Index = 0; Index < Enum->NumEnums(); ++Index)
			if (AllowedEnumIndex(Enum, Index) && (Enum->GetNameStringByIndex(Index).Equals(Value, ESearchCase::IgnoreCase)
				|| Enum->GetDisplayNameTextByIndex(Index).ToString().Equals(Value, ESearchCase::IgnoreCase))) return Enum->GetValueByIndex(Index);
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Invalid value %s for %s"), *Value, *P->GetName())));
	}
	FRuntimeFloatCurve* Curve(FSoundAttenuationSettings& S, const FString& Name)
	{
		if (Name == TEXT("attenuation")) return &S.CustomAttenuationCurve;
		if (Name == TEXT("lowpass_absorption")) return &S.CustomLowpassAirAbsorptionCurve;
		if (Name == TEXT("highpass_absorption")) return &S.CustomHighpassAirAbsorptionCurve;
		if (Name == TEXT("reverb_send")) return &S.CustomReverbSendCurve;
		if (Name == TEXT("priority")) return &S.CustomPriorityAttenuationCurve;
		throw std::runtime_error("curve_name must be attenuation, lowpass_absorption, highpass_absorption, reverb_send, or priority");
	}
	const FRuntimeFloatCurve* Curve(const FSoundAttenuationSettings& S, const FString& Name)
	{
		return Curve(const_cast<FSoundAttenuationSettings&>(S), Name);
	}
	void ValidateSettings(const FSoundAttenuationSettings& S, TArray<FString>& Errors, TArray<FString>& Warnings)
	{
		for (const FNumber& Field : Numbers)
		{
			const double Value = NumberValue(S, Field.Property);
			if (!FMath::IsFinite(Value) || Value < Field.Min || Value > Field.Max)
				Errors.Add(FString::Printf(TEXT("%s must be finite and between %g and %g"), Field.Name, Field.Min, Field.Max));
		}
		for (const FAttenuationField& Field : Enums)
		{
			FProperty* P = Property(Field.Property);
			const int64 Value = EnumStorage(P)->GetSignedIntPropertyValue(P->ContainerPtrToValuePtr<void>(&S));
			if (!AllowedEnumIndex(EnumType(P), EnumType(P)->GetIndexByValue(Value))) Errors.Add(FString::Printf(TEXT("%s contains an unsupported enum value"), Field.Name));
		}
		const FVector E = S.AttenuationShapeExtents;
		if (E.ContainsNaN() || E.X < 0.0 || E.Y < 0.0 || E.Z < 0.0) Errors.Add(TEXT("shape_extents must be finite and nonnegative"));
		if (S.AttenuationShape == EAttenuationShape::Capsule && E.X < E.Y) Errors.Add(TEXT("Capsule half-height (X) must be at least its radius (Y)"));
		if (S.AttenuationShape == EAttenuationShape::Cone && (E.Y > 180.0 || E.Z > 180.0)) Errors.Add(TEXT("Cone angle and falloff angle must be at most 180 degrees"));
		if (S.bSpatialize && S.NonSpatializedRadiusEnd > S.NonSpatializedRadiusStart) Errors.Add(TEXT("non_spatialized_radius_end must not exceed non_spatialized_radius_start"));
		if (S.bAttenuateWithLPF && S.LPFRadiusMin > S.LPFRadiusMax) Errors.Add(TEXT("air_absorption_distance_min must not exceed its maximum"));
		if (S.bEnableListenerFocus && S.FocusAzimuth > S.NonFocusAzimuth) Errors.Add(TEXT("focus_azimuth must not exceed non_focus_azimuth"));
		if (S.bEnableReverbSend && S.ReverbDistanceMin > S.ReverbDistanceMax) Errors.Add(TEXT("reverb_distance_min must not exceed its maximum"));
		if (S.bEnablePriorityAttenuation && S.PriorityAttenuationDistanceMin > S.PriorityAttenuationDistanceMax) Errors.Add(TEXT("priority_distance_min must not exceed its maximum"));
		for (const TCHAR* Name : CurveNames)
		{
			const FRichCurve* Rich = Curve(S, Name)->GetRichCurveConst();
			for (const FRichCurveKey& Key : Rich->GetConstRefOfKeys())
			{
				if (!FMath::IsFinite(Key.Time) || !FMath::IsFinite(Key.Value) || Key.Value < 0.0f || (FString(Name) != TEXT("priority") && Key.Value > 1.0f)) Errors.Add(FString::Printf(TEXT("%s curve contains a nonfinite or out-of-range key"), Name));
				if (Key.Time < 0.0f || Key.Time > 1.0f) Warnings.Add(FString::Printf(TEXT("%s curve contains keys outside its normalized 0-1 input range"), Name));
			}
		}
		if (S.bAttenuate && S.DistanceAlgorithm == EAttenuationDistanceModel::Custom && S.CustomAttenuationCurve.GetRichCurveConst()->GetNumKeys() == 0) Errors.Add(TEXT("Custom distance attenuation requires a curve with keys"));
		if (S.bEnableReverbSend && S.ReverbSendMethod == EReverbSendMethod::CustomCurve && S.CustomReverbSendCurve.GetRichCurveConst()->GetNumKeys() == 0) Errors.Add(TEXT("Custom reverb send requires a curve with keys"));
		if (S.bEnablePriorityAttenuation && S.PriorityAttenuationMethod == EPriorityAttenuationMethod::CustomCurve && S.CustomPriorityAttenuationCurve.GetRichCurveConst()->GetNumKeys() == 0) Errors.Add(TEXT("Custom priority attenuation requires a curve with keys"));
		TSet<USoundSubmixBase*> Submixes;
		if (S.SubmixSendSettings.Num() > 64) Errors.Add(TEXT("Attenuation supports at most 64 submix sends through this adapter"));
		for (const FAttenuationSubmixSendSettings& Send : S.SubmixSendSettings)
		{
			if (!Send.SoundSubmix) Errors.Add(TEXT("Submix send has no destination submix"));
			else if (Submixes.Contains(Send.SoundSubmix)) Errors.Add(TEXT("Submix sends contain a duplicate destination"));
			else Submixes.Add(Send.SoundSubmix);
			if (Send.SendLevelControlMethod != ESendLevelControlMethod::Manual && Send.SendLevelControlMethod != ESendLevelControlMethod::Linear && Send.SendLevelControlMethod != ESendLevelControlMethod::CustomCurve) Errors.Add(TEXT("Submix send control method is invalid"));
			const float Values[] = { Send.SendLevel, Send.MinSendLevel, Send.MaxSendLevel, Send.MinSendDistance, Send.MaxSendDistance };
			for (float Value : Values) if (!FMath::IsFinite(Value) || Value < 0.0f) Errors.Add(TEXT("Submix send levels and distances must be finite and nonnegative"));
			if (Send.SendLevelControlMethod == ESendLevelControlMethod::Manual && !Send.DisableManualSendClamp && Send.SendLevel > 1.0f) Errors.Add(TEXT("Manual send levels above 1 require disable_manual_send_clamp=true"));
			if (Send.MinSendLevel > 1.0f || Send.MaxSendLevel > 1.0f) Errors.Add(TEXT("Submix min/max send levels must be at most 1"));
			if (Send.SendLevelControlMethod != ESendLevelControlMethod::Manual && Send.MinSendDistance >= Send.MaxSendDistance) Errors.Add(TEXT("Distance-based submix sends require min_send_distance below max_send_distance"));
			const FRichCurve* Rich = Send.CustomSendLevelCurve.GetRichCurveConst();
			if (Send.SendLevelControlMethod == ESendLevelControlMethod::CustomCurve && Rich->GetNumKeys() == 0) Errors.Add(TEXT("Custom submix send requires a curve with keys"));
			for (const FRichCurveKey& Key : Rich->GetConstRefOfKeys())
			{
				if (!FMath::IsFinite(Key.Time) || !FMath::IsFinite(Key.Value)) Errors.Add(TEXT("Submix send curve keys must be finite"));
				else if (Key.Value < 0.0f || Key.Value > 1.0f)
				{
					if (Send.CustomSendLevelCurve.ExternalCurve) Warnings.Add(TEXT("External submix send curve values outside 0-1 are clamped by native send evaluation"));
					else Errors.Add(TEXT("Inline submix send curve values must be between 0 and 1"));
				}
			}
		}
		for (const TCHAR* Type : PluginTypes)
		{
			TSet<UObject*> Seen;
			const TArray<UObject*> Objects = PluginObjects(S, Type);
			if (Objects.Num() > 64) Errors.Add(FString::Printf(TEXT("%s plugin settings exceed 64 entries"), Type));
			for (UObject* Object : Objects)
			{
				if (!Object || !Object->IsA(PluginBase(Type))) Errors.Add(FString::Printf(TEXT("%s plugin settings contain a missing or incompatible object"), Type));
				else if (Seen.Contains(Object)) Errors.Add(FString::Printf(TEXT("%s plugin settings contain a duplicate reference"), Type));
				else Seen.Add(Object);
			}
		}
	}
	void RequireValid(const FSoundAttenuationSettings& S)
	{
		TArray<FString> Errors, Warnings;
		ValidateSettings(S, Errors, Warnings);
		if (!Errors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(Errors, TEXT("; "))));
	}
	void VectorJson(TSharedRef<TJsonWriter<>>& W, const TCHAR* Name, const FVector& Value)
	{
		W->WriteObjectStart(Name); W->WriteValue(TEXT("x"), Value.X); W->WriteValue(TEXT("y"), Value.Y); W->WriteValue(TEXT("z"), Value.Z); W->WriteObjectEnd();
	}
	FString Commit(USoundAttenuation* Asset, const FSoundAttenuationSettings& Proposed, const FString& Operation, bool bDryRun, bool bSave)
	{
		const bool bWouldChange = !FSoundAttenuationSettings::StaticStruct()->CompareScriptStruct(&Asset->Attenuation, &Proposed, PPF_None);
		if (bWouldChange && !bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditAttenuation", "Edit Sound Attenuation"));
			Asset->Modify(); Asset->Attenuation = Proposed; Asset->PostEditChange(); Asset->MarkPackageDirty();
			if (bSave)
			{
				UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
				if (!Subsystem || !Subsystem->SaveAsset(Asset->GetPathName(), true)) throw std::runtime_error("Sound Attenuation changed but saving failed");
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json);
		W->WriteObjectStart(); W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("operation"), Operation);
		W->WriteValue(TEXT("would_change"), bWouldChange); W->WriteValue(TEXT("changed"), bWouldChange && !bDryRun);
		W->WriteValue(TEXT("dry_run"), bDryRun); W->WriteValue(TEXT("saved"), bWouldChange && !bDryRun && bSave);
		W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}
	ERichCurveInterpMode Interpolation(const FString& Name)
	{
		if (Name.Equals(TEXT("Linear"), ESearchCase::IgnoreCase)) return RCIM_Linear;
		if (Name.Equals(TEXT("Constant"), ESearchCase::IgnoreCase)) return RCIM_Constant;
		if (Name.Equals(TEXT("Cubic"), ESearchCase::IgnoreCase)) return RCIM_Cubic;
		throw std::runtime_error("curve interpolation must be Linear, Constant, or Cubic");
	}
}

namespace SoundAttenuationUtils
{
	FString SettingsJson(USoundAttenuation* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		const FSoundAttenuationSettings& S = Asset->Attenuation;
		FString Json;
		TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json);
		W->WriteObjectStart(); W->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		W->WriteObjectStart(TEXT("numeric_settings"));
		for (const FNumber& Field : Numbers) W->WriteValue(Field.Name, NumberValue(S, Field.Property));
		W->WriteObjectEnd(); W->WriteObjectStart(TEXT("flags"));
		for (const FAttenuationField& Field : Flags) W->WriteValue(Field.Name, CastFieldChecked<FBoolProperty>(Property(Field.Property))->GetPropertyValue_InContainer(&S));
		W->WriteObjectEnd(); W->WriteObjectStart(TEXT("enum_settings"));
		for (const FAttenuationField& Field : Enums)
		{
			FProperty* P = Property(Field.Property);
			W->WriteValue(Field.Name, EnumType(P)->GetNameStringByValue(EnumStorage(P)->GetSignedIntPropertyValue(P->ContainerPtrToValuePtr<void>(&S))));
		}
		W->WriteObjectEnd(); VectorJson(W, TEXT("shape_extents"), S.AttenuationShapeExtents);
		W->WriteObjectStart(TEXT("allowed_enum_values"));
		for (const FAttenuationField& Field : Enums)
		{
			UEnum* Enum = EnumType(Property(Field.Property)); W->WriteArrayStart(Field.Name);
			for (int32 Index = 0; Index < Enum->NumEnums(); ++Index) if (AllowedEnumIndex(Enum, Index)) W->WriteValue(Enum->GetNameStringByIndex(Index));
			W->WriteArrayEnd();
		}
		W->WriteObjectEnd(); W->WriteObjectStart(TEXT("curves"));
		for (const TCHAR* Name : CurveNames)
		{
			const FRuntimeFloatCurve* C = Curve(S, Name); const FRichCurve* Rich = C->GetRichCurveConst();
			W->WriteObjectStart(Name); W->WriteValue(TEXT("external_curve_path"), C->ExternalCurve ? C->ExternalCurve->GetPathName() : TEXT(""));
			W->WriteValue(TEXT("key_count"), Rich->GetNumKeys()); W->WriteValue(TEXT("truncated"), Rich->GetNumKeys() > 256); W->WriteArrayStart(TEXT("keys"));
			int32 Count = 0;
			for (const FRichCurveKey& Key : Rich->GetConstRefOfKeys())
			{
				if (Count++ >= 256) break;
				W->WriteObjectStart(); W->WriteValue(TEXT("time"), Key.Time); W->WriteValue(TEXT("value"), Key.Value);
				W->WriteValue(TEXT("interpolation"), Key.InterpMode == RCIM_Constant ? TEXT("Constant") : Key.InterpMode == RCIM_Cubic ? TEXT("Cubic") : TEXT("Linear")); W->WriteObjectEnd();
			}
			W->WriteArrayEnd(); W->WriteObjectEnd();
		}
		W->WriteObjectEnd();
		W->WriteValue(TEXT("audio_link_settings_path"), S.AudioLinkSettingsOverride ? S.AudioLinkSettingsOverride->GetPathName() : TEXT(""));
		W->WriteObjectStart(TEXT("plugin_settings"));
		for (const TCHAR* Type : PluginTypes)
		{
			W->WriteArrayStart(Type);
			for (UObject* Object : PluginObjects(S, Type))
			{
				W->WriteObjectStart(); W->WriteValue(TEXT("settings_path"), Object ? Object->GetPathName() : TEXT(""));
				W->WriteValue(TEXT("class_path"), Object ? Object->GetClass()->GetPathName() : TEXT("")); W->WriteObjectEnd();
			}
			W->WriteArrayEnd();
		}
		W->WriteObjectEnd(); W->WriteArrayStart(TEXT("submix_sends"));
		for (const FAttenuationSubmixSendSettings& Send : S.SubmixSendSettings)
		{
			W->WriteObjectStart(); W->WriteValue(TEXT("submix_path"), Send.SoundSubmix ? Send.SoundSubmix->GetPathName() : TEXT(""));
			W->WriteValue(TEXT("control_method"), StaticEnum<ESendLevelControlMethod>()->GetNameStringByValue(static_cast<int64>(Send.SendLevelControlMethod)));
			W->WriteValue(TEXT("send_level"), Send.SendLevel); W->WriteValue(TEXT("disable_manual_send_clamp"), Send.DisableManualSendClamp);
			W->WriteValue(TEXT("min_send_level"), Send.MinSendLevel); W->WriteValue(TEXT("max_send_level"), Send.MaxSendLevel);
			W->WriteValue(TEXT("min_send_distance"), Send.MinSendDistance); W->WriteValue(TEXT("max_send_distance"), Send.MaxSendDistance);
			const FRuntimeFloatCurve& C = Send.CustomSendLevelCurve;
			W->WriteValue(TEXT("external_curve_path"), C.ExternalCurve ? C.ExternalCurve->GetPathName() : TEXT(""));
			W->WriteValue(TEXT("curve_key_count"), C.GetRichCurveConst()->GetNumKeys()); W->WriteArrayStart(TEXT("curve_keys"));
			int32 Count = 0;
			for (const FRichCurveKey& Key : C.GetRichCurveConst()->GetConstRefOfKeys())
			{
				if (Count++ >= 256) break;
				W->WriteObjectStart(); W->WriteValue(TEXT("time"), Key.Time); W->WriteValue(TEXT("value"), Key.Value);
				W->WriteValue(TEXT("interpolation"), Key.InterpMode == RCIM_Constant ? TEXT("Constant") : Key.InterpMode == RCIM_Cubic ? TEXT("Cubic") : TEXT("Linear")); W->WriteObjectEnd();
			}
			W->WriteArrayEnd(); W->WriteValue(TEXT("curve_keys_truncated"), C.GetRichCurveConst()->GetNumKeys() > 256); W->WriteObjectEnd();
		}
		W->WriteArrayEnd(); W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}

	FString EditSettings(USoundAttenuation* Asset, const FAudioAttenuationSettingsReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		FSoundAttenuationSettings Proposed(Asset->Attenuation);
		for (const auto& Entry : R.NumericSettings)
		{
			const FNumber* Field = FindField(Numbers, Entry.Key);
			if (!FMath::IsFinite(Entry.Value) || Entry.Value < Field->Min || Entry.Value > Field->Max) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("%s is outside its supported numeric range"), Field->Name)));
			FNumericProperty* P = NumberProperty(Field->Property); P->SetFloatingPointPropertyValue(P->ContainerPtrToValuePtr<void>(&Proposed), Entry.Value);
		}
		for (const auto& Entry : R.Flags)
		{
			const FAttenuationField* Field = FindField(Flags, Entry.Key); CastFieldChecked<FBoolProperty>(Property(Field->Property))->SetPropertyValue_InContainer(&Proposed, Entry.Value);
		}
		for (const auto& Entry : R.EnumSettings)
		{
			const FAttenuationField* Field = FindField(Enums, Entry.Key); FProperty* P = Property(Field->Property);
			const int64 Value = ParseEnum(P, Entry.Value); EnumStorage(P)->SetIntPropertyValue(P->ContainerPtrToValuePtr<void>(&Proposed), static_cast<uint64>(Value));
		}
		if (R.bSetShapeExtents) Proposed.AttenuationShapeExtents = R.ShapeExtents;
		if (R.bSetAudioLinkSettings)
		{
			Proposed.AudioLinkSettingsOverride = R.AudioLinkSettingsPath.IsEmpty() ? nullptr : Cast<UAudioLinkSettingsAbstract>(StaticLoadObject(UAudioLinkSettingsAbstract::StaticClass(), nullptr, *R.AudioLinkSettingsPath));
			if (!R.AudioLinkSettingsPath.IsEmpty() && !Proposed.AudioLinkSettingsOverride) throw std::runtime_error("audio_link_settings_path must identify an AudioLink Settings asset");
		}
		RequireValid(Proposed); return Commit(Asset, Proposed, TEXT("settings"), R.bDryRun, R.bSave);
	}

	FString EditCurve(USoundAttenuation* Asset, const FAudioAttenuationCurveReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		FSoundAttenuationSettings Proposed(Asset->Attenuation);
		const FString CurveName = R.CurveName.TrimStartAndEnd().ToLower();
		FRuntimeFloatCurve* C = Curve(Proposed, CurveName);
		const FString Operation = R.Operation.TrimStartAndEnd().ToLower();
		if (Operation == TEXT("set_external"))
		{
			UCurveFloat* External = Cast<UCurveFloat>(StaticLoadObject(UCurveFloat::StaticClass(), nullptr, *R.CurvePath));
			if (!External) throw std::runtime_error("curve_path must identify a Curve Float asset"); C->ExternalCurve = External;
		}
		else if (Operation == TEXT("replace_inline") || Operation == TEXT("clear"))
		{
			if ((C->ExternalCurve || C->EditorCurveData.GetNumKeys() > 0) && !R.bDryRun && !R.bConfirm) throw std::runtime_error("replacing or clearing existing attenuation curve data requires confirm=true");
			if (Operation == TEXT("replace_inline") && (R.Keys.IsEmpty() || R.Keys.Num() > 256)) throw std::runtime_error("replace_inline requires 1-256 normalized curve keys");
			C->ExternalCurve = nullptr; C->EditorCurveData.Reset();
			TSet<float> Times;
			if (Operation == TEXT("replace_inline")) for (const FAudioAttenuationCurveKey& Key : R.Keys)
			{
				if (!FMath::IsFinite(Key.Time) || Key.Time < 0.0f || Key.Time > 1.0f || Times.Contains(Key.Time)) throw std::runtime_error("curve key times must be unique and between 0 and 1");
				if (!FMath::IsFinite(Key.Value) || Key.Value < 0.0f || (CurveName != TEXT("priority") && Key.Value > 1.0f)) throw std::runtime_error("curve key values must be nonnegative; volume, filter, and reverb curves must be at most 1");
				Times.Add(Key.Time); const ERichCurveInterpMode Mode = Interpolation(Key.Interpolation);
				const FKeyHandle Handle = C->EditorCurveData.AddKey(Key.Time, Key.Value); C->EditorCurveData.SetKeyInterpMode(Handle, Mode);
			}
			C->EditorCurveData.AutoSetTangents();
		}
		else throw std::runtime_error("operation must be set_external, replace_inline, or clear");
		RequireValid(Proposed); return Commit(Asset, Proposed, Operation, R.bDryRun, R.bSave);
	}

	FString Validate(USoundAttenuation* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		TArray<FString> Errors, Warnings; ValidateSettings(Asset->Attenuation, Errors, Warnings);
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json);
		W->WriteObjectStart(); W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("valid"), Errors.IsEmpty());
		W->WriteValue(TEXT("validation_scope"), TEXT("attenuation_settings_shapes_curves_submix_sends_and_plugin_references"));
		W->WriteArrayStart(TEXT("errors")); for (const FString& E : Errors) W->WriteValue(E); W->WriteArrayEnd();
		W->WriteArrayStart(TEXT("warnings")); for (const FString& E : Warnings) W->WriteValue(E); W->WriteArrayEnd();
		W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}

	FString EditSubmixSend(USoundAttenuation* Asset, const FAudioAttenuationSubmixSendReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		FSoundAttenuationSettings Proposed(Asset->Attenuation);
		const FString Operation = R.Operation.TrimStartAndEnd().ToLower();
		if (Operation == TEXT("clear"))
		{
			if (!Proposed.SubmixSendSettings.IsEmpty() && !R.bDryRun && !R.bConfirm) throw std::runtime_error("clearing attenuation submix sends requires confirm=true");
			Proposed.SubmixSendSettings.Reset();
		}
		else
		{
			USoundSubmixBase* Submix = Cast<USoundSubmixBase>(StaticLoadObject(USoundSubmixBase::StaticClass(), nullptr, *R.SubmixPath));
			if (!Submix) throw std::runtime_error("submix_path must identify a Sound Submix asset");
			const int32 Index = Proposed.SubmixSendSettings.IndexOfByPredicate([Submix](const FAttenuationSubmixSendSettings& Send) { return Send.SoundSubmix == Submix; });
			if (Operation == TEXT("remove"))
			{
				if (Index == INDEX_NONE) throw std::runtime_error("submix_path is not present in this attenuation asset");
				if (!R.bDryRun && !R.bConfirm) throw std::runtime_error("removing an attenuation submix send requires confirm=true");
				Proposed.SubmixSendSettings.RemoveAll([Submix](const FAttenuationSubmixSendSettings& Send) { return Send.SoundSubmix == Submix; });
			}
			else if (Operation == TEXT("upsert"))
			{
				if (Index == INDEX_NONE && Proposed.SubmixSendSettings.Num() >= 64) throw std::runtime_error("attenuation submix sends are limited to 64 destinations");
				// This native struct's default constructor is not exported in UE 5.7.
				// Registered struct ops initialize the same native defaults across modules.
				FStructOnScope SendScope(FAttenuationSubmixSendSettings::StaticStruct());
				FAttenuationSubmixSendSettings& Send = *reinterpret_cast<FAttenuationSubmixSendSettings*>(SendScope.GetStructMemory());
				if (Index != INDEX_NONE) FAttenuationSubmixSendSettings::StaticStruct()->CopyScriptStruct(&Send, &Proposed.SubmixSendSettings[Index]);
				Send.SoundSubmix = Submix;
				if (!R.ControlMethod.IsEmpty())
				{
					if (R.ControlMethod.Equals(TEXT("Manual"), ESearchCase::IgnoreCase)) Send.SendLevelControlMethod = ESendLevelControlMethod::Manual;
					else if (R.ControlMethod.Equals(TEXT("Linear"), ESearchCase::IgnoreCase)) Send.SendLevelControlMethod = ESendLevelControlMethod::Linear;
					else if (R.ControlMethod.Equals(TEXT("CustomCurve"), ESearchCase::IgnoreCase)) Send.SendLevelControlMethod = ESendLevelControlMethod::CustomCurve;
					else throw std::runtime_error("control_method must be Manual, Linear, or CustomCurve");
				}
				if (R.bSetSendLevel) Send.SendLevel = R.SendLevel;
				if (R.bSetDisableManualSendClamp) Send.DisableManualSendClamp = R.bDisableManualSendClamp;
				if (R.bSetMinSendLevel) Send.MinSendLevel = R.MinSendLevel;
				if (R.bSetMaxSendLevel) Send.MaxSendLevel = R.MaxSendLevel;
				if (R.bSetMinSendDistance) Send.MinSendDistance = R.MinSendDistance;
				if (R.bSetMaxSendDistance) Send.MaxSendDistance = R.MaxSendDistance;
				if (R.bSetExternalCurve && R.bSetCurveKeys) throw std::runtime_error("set either an external send curve or inline curve keys in one request");
				if (R.bSetExternalCurve)
				{
					Send.CustomSendLevelCurve.ExternalCurve = R.CurvePath.IsEmpty() ? nullptr : Cast<UCurveFloat>(StaticLoadObject(UCurveFloat::StaticClass(), nullptr, *R.CurvePath));
					if (!R.CurvePath.IsEmpty() && !Send.CustomSendLevelCurve.ExternalCurve) throw std::runtime_error("curve_path must identify a Curve Float asset");
				}
				if (R.bSetCurveKeys)
				{
					if (R.Keys.IsEmpty() || R.Keys.Num() > 256) throw std::runtime_error("inline submix curves require 1-256 keys");
					if ((Send.CustomSendLevelCurve.ExternalCurve || Send.CustomSendLevelCurve.EditorCurveData.GetNumKeys() > 0) && !R.bDryRun && !R.bConfirm) throw std::runtime_error("replacing existing submix send curve data requires confirm=true");
					Send.CustomSendLevelCurve.ExternalCurve = nullptr; Send.CustomSendLevelCurve.EditorCurveData.Reset(); TSet<float> Times;
					for (const FAudioAttenuationCurveKey& Key : R.Keys)
					{
						if (!FMath::IsFinite(Key.Time) || Key.Time < 0.0f || Key.Time > 1.0f || Times.Contains(Key.Time) || !FMath::IsFinite(Key.Value) || Key.Value < 0.0f || Key.Value > 1.0f) throw std::runtime_error("submix curve keys require unique normalized times and values between 0 and 1");
						Times.Add(Key.Time); const FKeyHandle Handle = Send.CustomSendLevelCurve.EditorCurveData.AddKey(Key.Time, Key.Value);
						Send.CustomSendLevelCurve.EditorCurveData.SetKeyInterpMode(Handle, Interpolation(Key.Interpolation));
					}
					Send.CustomSendLevelCurve.EditorCurveData.AutoSetTangents();
				}
				if (Index == INDEX_NONE) Proposed.SubmixSendSettings.Add(Send); else Proposed.SubmixSendSettings[Index] = Send;
			}
			else throw std::runtime_error("submix send operation must be upsert, remove, or clear");
		}
		RequireValid(Proposed); return Commit(Asset, Proposed, TEXT("submix_send_") + Operation, R.bDryRun, R.bSave);
	}

	FString EditPlugin(USoundAttenuation* Asset, const FAudioAttenuationPluginReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		const FString Type = R.PluginType.TrimStartAndEnd().ToLower();
		UClass* Base = PluginBase(Type); FSoundAttenuationSettings Proposed(Asset->Attenuation);
		FArrayProperty* P = PluginArrayProperty(Type); FScriptArrayHelper Helper(P, P->ContainerPtrToValuePtr<void>(&Proposed.PluginSettings));
		FObjectPropertyBase* Inner = CastFieldChecked<FObjectPropertyBase>(P->Inner);
		const FString Operation = R.Operation.TrimStartAndEnd().ToLower();
		if (Operation == TEXT("clear"))
		{
			if (Helper.Num() > 0 && !R.bDryRun && !R.bConfirm) throw std::runtime_error("clearing plugin settings references requires confirm=true");
			Helper.EmptyValues();
		}
		else
		{
			UObject* Settings = StaticLoadObject(Base, nullptr, *R.SettingsPath);
			if (!Settings || !Settings->IsA(Base)) throw std::runtime_error("settings_path must identify a compatible plugin source settings asset");
			bool bFound = false;
			for (int32 Index = Helper.Num() - 1; Index >= 0; --Index)
				if (Inner->GetObjectPropertyValue(Helper.GetRawPtr(Index)) == Settings)
				{
					bFound = true;
					if (Operation == TEXT("remove"))
					{
						if (!R.bDryRun && !R.bConfirm) throw std::runtime_error("removing plugin settings references requires confirm=true");
						Helper.RemoveValues(Index);
					}
				}
			if (Operation == TEXT("add"))
			{
				if (!bFound)
				{
					if (Helper.Num() >= 64) throw std::runtime_error("plugin settings references are limited to 64 per family");
					const int32 Index = Helper.AddValue(); Inner->SetObjectPropertyValue(Helper.GetRawPtr(Index), Settings);
				}
			}
			else if (Operation == TEXT("remove")) { if (!bFound) throw std::runtime_error("settings_path is not linked in this plugin family"); }
			else throw std::runtime_error("plugin reference operation must be add, remove, or clear");
		}
		RequireValid(Proposed); return Commit(Asset, Proposed, TEXT("plugin_") + Operation, R.bDryRun, R.bSave);
	}

	FString PluginClassesJson()
	{
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("scope"), TEXT("loaded_concrete_plugin_source_settings_classes")); W->WriteArrayStart(TEXT("classes"));
		TArray<UClass*> Classes;
		for (TObjectIterator<UClass> It; It; ++It) if (!It->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists)) Classes.Add(*It);
		Classes.Sort([](const UClass& A, const UClass& B) { return A.GetPathName() < B.GetPathName(); });
		for (UClass* Class : Classes) for (const TCHAR* Type : PluginTypes) if (Class->IsChildOf(PluginBase(Type)))
		{
			W->WriteObjectStart(); W->WriteValue(TEXT("class_path"), Class->GetPathName()); W->WriteValue(TEXT("plugin_type"), Type); W->WriteValue(TEXT("display_name"), Class->GetDisplayNameText().ToString()); W->WriteObjectEnd(); break;
		}
		W->WriteArrayEnd(); W->WriteObjectEnd(); W->Close(); return Json;
	}

	FString CreatePluginSettings(const FAudioPluginSettingsCreateReq& R)
	{
		if (!R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(R.AssetPath)) throw std::runtime_error("asset_path must be a valid /Game package path without an object suffix");
		UClass* Class = LoadClass<UObject>(nullptr, *R.SettingsClass);
		if (!Class || Class->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists)) throw std::runtime_error("settings_class must identify a concrete plugin source settings class");
		FString Type;
		for (const TCHAR* Candidate : PluginTypes) if (Class->IsChildOf(PluginBase(Candidate))) { Type = Candidate; break; }
		if (Type.IsEmpty()) throw std::runtime_error("settings_class is not a supported plugin source settings class");
		FString Package, Name; FAssetToolsModule& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		Tools.Get().CreateUniqueAssetName(R.AssetPath, TEXT(""), Package, Name);
		const FString Path = Package + TEXT(".") + Name;
		if (!R.bDryRun)
		{
			UPackage* Outer = CreatePackage(*Package); UObject* Asset = NewObject<UObject>(Outer, Class, FName(*Name), RF_Public | RF_Standalone | RF_Transactional);
			if (!Asset) throw std::runtime_error("could not create plugin source settings asset");
			FAssetRegistryModule::AssetCreated(Asset); Asset->MarkPackageDirty();
			if (R.bSave)
			{
				UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
				if (!Subsystem || !Subsystem->SaveAsset(Path, true)) throw std::runtime_error("plugin settings asset created but saving failed");
			}
		}
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("asset_path"), Path); W->WriteValue(TEXT("class_path"), Class->GetPathName()); W->WriteValue(TEXT("plugin_type"), Type);
		W->WriteValue(TEXT("created"), !R.bDryRun); W->WriteValue(TEXT("would_create"), true); W->WriteValue(TEXT("dry_run"), R.bDryRun); W->WriteValue(TEXT("saved"), !R.bDryRun && R.bSave);
		W->WriteObjectEnd(); W->Close(); return Json;
	}

	FString Evaluate(USoundAttenuation* Asset, const FAudioAttenuationEvaluateReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		if (R.Locations.IsEmpty() || R.Locations.Num() > 256) throw std::runtime_error("locations must contain 1-256 world-space points");
		if (R.Origin.ContainsNaN() || R.Rotation.ContainsNaN() || !FMath::IsFinite(R.DistanceScale) || R.DistanceScale < 0.0f) throw std::runtime_error("origin, rotation, and nonnegative distance_scale must be finite");
		RequireValid(Asset->Attenuation);
		for (const FVector& Location : R.Locations) if (Location.ContainsNaN()) throw std::runtime_error("evaluation locations must be finite");
		const FTransform Origin(R.Rotation, R.Origin);
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json);
		W->WriteObjectStart(); W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("evaluation_scope"), TEXT("distance_volume_attenuation_only"));
		W->WriteArrayStart(TEXT("samples"));
		for (const FVector& Location : R.Locations)
		{
			const float Gain = Asset->Attenuation.bAttenuate ? Asset->Attenuation.Evaluate(Origin, Location, R.DistanceScale) : 1.0f;
			if (!FMath::IsFinite(Gain)) throw std::runtime_error("native distance attenuation evaluation returned a nonfinite result");
			W->WriteObjectStart(); VectorJson(W, TEXT("location"), Location); W->WriteValue(TEXT("linear_gain"), Gain); W->WriteObjectEnd();
		}
		W->WriteArrayEnd(); W->WriteObjectEnd(); W->Close(); return Json;
	}
}
