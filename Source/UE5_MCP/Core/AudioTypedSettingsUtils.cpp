#include "AudioTypedSettingsUtils.h"

#include "UE5_MCP/API/DTO/SoundClassSettingsReq.h"
#include "UE5_MCP/API/DTO/SoundMixSettingsReq.h"
#include "UE5_MCP/API/DTO/SoundSubmixSettingsReq.h"

#include "Editor.h"
#include "Logging/TokenizedMessage.h"
#include "ScopedTransaction.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundEffectSubmix.h"
#include "Sound/SoundMix.h"
#include "Sound/SoundSubmix.h"
#include "Subsystems/EditorAssetSubsystem.h"

#include "Serialization/JsonWriter.h"

#include <stdexcept>

namespace
{
	void SaveAssetsIfRequested(const TArray<UObject*>& Assets, bool bSave)
	{
		if (!bSave) return;
		UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!Subsystem) throw std::runtime_error("Editor Asset Subsystem is unavailable");
		for (UObject* Asset : Assets)
			if (Asset && !Subsystem->SaveAsset(Asset->GetPathName(), true))
				throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Failed to save audio asset %s"), *Asset->GetPathName())));
	}

	void MarkAssetsDirty(const TArray<UObject*>& Assets)
	{
		for (UObject* Asset : Assets)
			if (Asset) Asset->MarkPackageDirty();
	}

	FString ToPath(const UObject* Object)
	{
		return Object ? Object->GetPathName() : FString();
	}

	void WriteCommonMutation(TSharedRef<TJsonWriter<>>& Writer, UObject* Asset, const FString& Operation,
		bool bChanged, bool bWouldChange, bool bDryRun, bool bSaved)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("operation"), Operation);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("would_change"), bWouldChange);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd();
	}

	FString MutationJson(UObject* Asset, const FString& Operation, bool bChanged,
		bool bWouldChange, bool bDryRun, bool bSaved)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		WriteCommonMutation(Writer, Asset, Operation, bChanged, bWouldChange, bDryRun, bSaved);
		Writer->Close();
		return Json;
	}

	void WriteValidation(UObject* Asset, const TCHAR* Scope, const TArray<FString>& Errors,
		const TArray<FString>& Warnings, TSharedRef<TJsonWriter<>>& Writer)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("validation_scope"), Scope);
		Writer->WriteArrayStart(TEXT("errors"));
		for (const FString& Error : Errors) Writer->WriteValue(Error);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings"));
		for (const FString& Warning : Warnings) Writer->WriteValue(Warning);
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd();
	}

	FString OutputTargetName(EAudioOutputTarget::Type Value)
	{
		switch (Value)
		{
		case EAudioOutputTarget::Speaker: return TEXT("Speaker");
		case EAudioOutputTarget::Controller: return TEXT("Controller");
		case EAudioOutputTarget::ControllerFallbackToSpeaker: return TEXT("ControllerFallbackToSpeaker");
		default: return TEXT("Unknown");
		}
	}

	bool ParseOutputTarget(const FString& Text, EAudioOutputTarget::Type& OutValue)
	{
		if (Text.Equals(TEXT("Speaker"), ESearchCase::IgnoreCase)) OutValue = EAudioOutputTarget::Speaker;
		else if (Text.Equals(TEXT("Controller"), ESearchCase::IgnoreCase)) OutValue = EAudioOutputTarget::Controller;
		else if (Text.Equals(TEXT("ControllerFallbackToSpeaker"), ESearchCase::IgnoreCase)) OutValue = EAudioOutputTarget::ControllerFallbackToSpeaker;
		else return false;
		return true;
	}

	FString LoadingBehaviorName(ESoundWaveLoadingBehavior Value)
	{
		switch (Value)
		{
		case ESoundWaveLoadingBehavior::Inherited: return TEXT("Inherited");
		case ESoundWaveLoadingBehavior::RetainOnLoad: return TEXT("RetainOnLoad");
		case ESoundWaveLoadingBehavior::PrimeOnLoad: return TEXT("PrimeOnLoad");
		case ESoundWaveLoadingBehavior::LoadOnDemand: return TEXT("LoadOnDemand");
		case ESoundWaveLoadingBehavior::ForceInline: return TEXT("ForceInline");
		default: return TEXT("Uninitialized");
		}
	}

	bool ParseLoadingBehavior(const FString& Text, ESoundWaveLoadingBehavior& OutValue)
	{
		if (Text.Equals(TEXT("Inherited"), ESearchCase::IgnoreCase)) OutValue = ESoundWaveLoadingBehavior::Inherited;
		else if (Text.Equals(TEXT("RetainOnLoad"), ESearchCase::IgnoreCase)) OutValue = ESoundWaveLoadingBehavior::RetainOnLoad;
		else if (Text.Equals(TEXT("PrimeOnLoad"), ESearchCase::IgnoreCase)) OutValue = ESoundWaveLoadingBehavior::PrimeOnLoad;
		else if (Text.Equals(TEXT("LoadOnDemand"), ESearchCase::IgnoreCase)) OutValue = ESoundWaveLoadingBehavior::LoadOnDemand;
		else return false;
		return true;
	}

	bool SoundClassWouldCycle(USoundClass* Asset, USoundClass* ProposedParent)
	{
		TSet<USoundClass*> Visited;
		for (USoundClass* Current = ProposedParent; Current; Current = Current->ParentClass)
		{
			if (Current == Asset || Visited.Contains(Current)) return true;
			Visited.Add(Current);
		}
		return false;
	}

	float GetEQFrequency(const FAudioEQEffect& EQ, int32 Band)
	{
		switch (Band) { case 0: return EQ.FrequencyCenter0; case 1: return EQ.FrequencyCenter1; case 2: return EQ.FrequencyCenter2; default: return EQ.FrequencyCenter3; }
	}
	float GetEQGain(const FAudioEQEffect& EQ, int32 Band)
	{
		switch (Band) { case 0: return EQ.Gain0; case 1: return EQ.Gain1; case 2: return EQ.Gain2; default: return EQ.Gain3; }
	}
	float GetEQBandwidth(const FAudioEQEffect& EQ, int32 Band)
	{
		switch (Band) { case 0: return EQ.Bandwidth0; case 1: return EQ.Bandwidth1; case 2: return EQ.Bandwidth2; default: return EQ.Bandwidth3; }
	}
	void SetEQFrequency(FAudioEQEffect& EQ, int32 Band, float Value)
	{
		switch (Band) { case 0: EQ.FrequencyCenter0 = Value; break; case 1: EQ.FrequencyCenter1 = Value; break; case 2: EQ.FrequencyCenter2 = Value; break; default: EQ.FrequencyCenter3 = Value; break; }
	}
	void SetEQGain(FAudioEQEffect& EQ, int32 Band, float Value)
	{
		switch (Band) { case 0: EQ.Gain0 = Value; break; case 1: EQ.Gain1 = Value; break; case 2: EQ.Gain2 = Value; break; default: EQ.Gain3 = Value; break; }
	}
	void SetEQBandwidth(FAudioEQEffect& EQ, int32 Band, float Value)
	{
		switch (Band) { case 0: EQ.Bandwidth0 = Value; break; case 1: EQ.Bandwidth1 = Value; break; case 2: EQ.Bandwidth2 = Value; break; default: EQ.Bandwidth3 = Value; break; }
	}

	void CollectPassiveMixes(USoundClass* SoundClass, bool bIncludeChildren, TSet<USoundClass*>& SeenClasses,
		TSet<USoundMix*>& OutMixes)
	{
		if (!SoundClass || SeenClasses.Contains(SoundClass)) return;
		SeenClasses.Add(SoundClass);
		for (const FPassiveSoundMixModifier& Modifier : SoundClass->PassiveSoundMixModifiers)
			if (Modifier.SoundMix) OutMixes.Add(Modifier.SoundMix);
		if (bIncludeChildren)
			for (USoundClass* Child : SoundClass->ChildClasses) CollectPassiveMixes(Child, true, SeenClasses, OutMixes);
	}

	bool SoundMixDependencyPathReaches(USoundMix* Current, USoundMix* Target,
		TSet<USoundMix*>& Visiting, TSet<USoundMix*>& Visited)
	{
		if (Current == Target) return true;
		if (!Current || Visited.Contains(Current) || Visiting.Contains(Current)) return false;
		Visiting.Add(Current);
		for (const FSoundClassAdjuster& Adjuster : Current->SoundClassEffects)
		{
			TSet<USoundClass*> SeenClasses;
			TSet<USoundMix*> PassiveMixes;
			CollectPassiveMixes(Adjuster.SoundClassObject, Adjuster.bApplyToChildren, SeenClasses, PassiveMixes);
			for (USoundMix* PassiveMix : PassiveMixes)
				if (SoundMixDependencyPathReaches(PassiveMix, Target, Visiting, Visited)) return true;
		}
		Visiting.Remove(Current);
		Visited.Add(Current);
		return false;
	}

	bool SoundMixHasPassiveActivationLoop(USoundMix* Asset)
	{
		TSet<USoundMix*> Visiting, Visited;
		for (const FSoundClassAdjuster& Adjuster : Asset->SoundClassEffects)
		{
			TSet<USoundClass*> SeenClasses;
			TSet<USoundMix*> PassiveMixes;
			CollectPassiveMixes(Adjuster.SoundClassObject, Adjuster.bApplyToChildren, SeenClasses, PassiveMixes);
			for (USoundMix* PassiveMix : PassiveMixes)
				if (SoundMixDependencyPathReaches(PassiveMix, Asset, Visiting, Visited)) return true;
		}
		return false;
	}

	bool SubmixParentWouldCycle(USoundSubmix* Asset, USoundSubmixBase* ProposedParent)
	{
		TSet<USoundSubmixBase*> Visited;
		for (USoundSubmixBase* Current = ProposedParent; Current;)
		{
			if (Current == Asset || Visited.Contains(Current)) return true;
			Visited.Add(Current);
			USoundSubmixWithParentBase* WithParent = Cast<USoundSubmixWithParentBase>(Current);
			Current = WithParent ? WithParent->ParentSubmix : nullptr;
		}
		return false;
	}

	bool IsEngineAsset(const UObject* Asset)
	{
		return Asset && Asset->GetOutermost()->GetName().StartsWith(TEXT("/Engine/"));
	}
}

namespace AudioTypedSettingsUtils
{
	FString InspectSoundClass(USoundClass* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Class");
		const FSoundClassProperties& P = Asset->Properties;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("parent_class_path"), ToPath(Asset->ParentClass));
		Writer->WriteObjectStart(TEXT("settings"));
		Writer->WriteValue(TEXT("volume"), P.Volume);
		Writer->WriteValue(TEXT("pitch"), P.Pitch);
		Writer->WriteValue(TEXT("low_pass_filter_frequency"), P.LowPassFilterFrequency);
		Writer->WriteValue(TEXT("attenuation_distance_scale"), P.AttenuationDistanceScale);
		Writer->WriteValue(TEXT("lfe_bleed"), P.LFEBleed);
		Writer->WriteValue(TEXT("voice_center_channel_volume"), P.VoiceCenterChannelVolume);
		Writer->WriteValue(TEXT("default_2d_reverb_send_amount"), P.Default2DReverbSendAmount);
		Writer->WriteValue(TEXT("apply_effects"), static_cast<bool>(P.bApplyEffects));
		Writer->WriteValue(TEXT("always_play"), static_cast<bool>(P.bAlwaysPlay));
		Writer->WriteValue(TEXT("is_ui_sound"), static_cast<bool>(P.bIsUISound));
		Writer->WriteValue(TEXT("is_music"), static_cast<bool>(P.bIsMusic));
		Writer->WriteValue(TEXT("center_channel_only"), static_cast<bool>(P.bCenterChannelOnly));
		Writer->WriteValue(TEXT("apply_ambient_volumes"), static_cast<bool>(P.bApplyAmbientVolumes));
		Writer->WriteValue(TEXT("reverb"), static_cast<bool>(P.bReverb));
		Writer->WriteValue(TEXT("output_target"), OutputTargetName(P.OutputTarget.GetValue()));
		Writer->WriteValue(TEXT("loading_behavior"), LoadingBehaviorName(P.LoadingBehavior));
		Writer->WriteValue(TEXT("default_submix_path"), ToPath(P.DefaultSubmix));
		Writer->WriteObjectEnd();
		Writer->WriteArrayStart(TEXT("children"));
		for (const USoundClass* Child : Asset->ChildClasses) Writer->WriteValue(Child ? Child->GetPathName() : FString());
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("passive_sound_mixes"));
		for (const FPassiveSoundMixModifier& Modifier : Asset->PassiveSoundMixModifiers)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("sound_mix_path"), ToPath(Modifier.SoundMix));
			Writer->WriteValue(TEXT("min_volume_threshold"), Modifier.MinVolumeThreshold);
			Writer->WriteValue(TEXT("max_volume_threshold"), Modifier.MaxVolumeThreshold);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString EditSoundClass(USoundClass* Asset, const FSoundClassSettingsReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Class");
		FSoundClassProperties Proposed = Asset->Properties;
		if (R.bSetVolume) Proposed.Volume = R.Volume;
		if (R.bSetPitch) Proposed.Pitch = R.Pitch;
		if (R.bSetLowPassFilterFrequency) Proposed.LowPassFilterFrequency = R.LowPassFilterFrequency;
		if (R.bSetAttenuationDistanceScale) Proposed.AttenuationDistanceScale = R.AttenuationDistanceScale;
		if (R.bSetLFEBleed) Proposed.LFEBleed = R.LFEBleed;
		if (R.bSetVoiceCenterChannelVolume) Proposed.VoiceCenterChannelVolume = R.VoiceCenterChannelVolume;
		if (R.bSetDefault2DReverbSendAmount) Proposed.Default2DReverbSendAmount = R.Default2DReverbSendAmount;
		if (R.bSetAlwaysPlay) Proposed.bAlwaysPlay = R.bAlwaysPlay;
		if (R.bSetIsUISound) Proposed.bIsUISound = R.bIsUISound;
		if (R.bSetIsMusic) Proposed.bIsMusic = R.bIsMusic;
		if (R.bSetCenterChannelOnly) Proposed.bCenterChannelOnly = R.bCenterChannelOnly;
		if (R.bSetApplyAmbientVolumes) Proposed.bApplyAmbientVolumes = R.bApplyAmbientVolumes;
		if (R.bSetReverb) Proposed.bReverb = R.bReverb;
		if (R.bSetApplyEffects) Proposed.bApplyEffects = R.bApplyEffects;
		EAudioOutputTarget::Type OutputTarget = Asset->Properties.OutputTarget.GetValue();
		if (R.bSetOutputTarget && !ParseOutputTarget(R.OutputTarget, OutputTarget))
			throw std::runtime_error("output_target must be Speaker, Controller, or ControllerFallbackToSpeaker");
		if (R.bSetOutputTarget) Proposed.OutputTarget = OutputTarget;
		ESoundWaveLoadingBehavior LoadingBehavior = Asset->Properties.LoadingBehavior;
		if (R.bSetLoadingBehavior && !ParseLoadingBehavior(R.LoadingBehavior, LoadingBehavior))
			throw std::runtime_error("loading_behavior must be Inherited, RetainOnLoad, PrimeOnLoad, or LoadOnDemand for a Sound Class");
		if (R.bSetLoadingBehavior) Proposed.LoadingBehavior = LoadingBehavior;
		USoundSubmix* DefaultSubmix = Asset->Properties.DefaultSubmix;
		if (R.bSetDefaultSubmix)
		{
			DefaultSubmix = R.DefaultSubmixPath.IsEmpty() ? nullptr : Cast<USoundSubmix>(StaticLoadObject(USoundSubmix::StaticClass(), nullptr, *R.DefaultSubmixPath));
			if (!R.DefaultSubmixPath.IsEmpty() && !DefaultSubmix) throw std::runtime_error("default_submix_path must identify a Sound Submix");
			Proposed.DefaultSubmix = DefaultSubmix;
		}
		USoundClass* ParentClass = Asset->ParentClass;
		if (R.bSetParentClass)
		{
			ParentClass = R.ParentClassPath.IsEmpty() ? nullptr : Cast<USoundClass>(StaticLoadObject(USoundClass::StaticClass(), nullptr, *R.ParentClassPath));
			if (!R.ParentClassPath.IsEmpty() && !ParentClass) throw std::runtime_error("parent_class_path must identify a Sound Class");
			if (ParentClass && SoundClassWouldCycle(Asset, ParentClass)) throw std::runtime_error("parent_class_path would introduce a Sound Class hierarchy cycle");
			if (R.bSave && IsEngineAsset(ParentClass)) throw std::runtime_error("saving this parent assignment would modify an Engine Sound Class; duplicate it into /Game first");
		}

		const float NumericValues[] = { Proposed.Volume, Proposed.Pitch, Proposed.LowPassFilterFrequency,
			Proposed.AttenuationDistanceScale, Proposed.LFEBleed, Proposed.VoiceCenterChannelVolume,
			Proposed.Default2DReverbSendAmount };
		for (float Value : NumericValues) if (!FMath::IsFinite(Value)) throw std::runtime_error("Sound Class settings must be finite numbers");
		if (Proposed.Volume < 0.0f || Proposed.Pitch <= 0.0f || Proposed.LowPassFilterFrequency < 0.0f
			|| Proposed.LowPassFilterFrequency > 20000.0f || Proposed.AttenuationDistanceScale < 0.0f
			|| Proposed.LFEBleed < 0.0f || Proposed.VoiceCenterChannelVolume < 0.0f
			|| Proposed.Default2DReverbSendAmount < 0.0f)
			throw std::runtime_error("Sound Class numeric settings are outside their valid ranges");

		const FSoundClassProperties& Current = Asset->Properties;
		bool bWouldChange = Asset->ParentClass != ParentClass || Current.DefaultSubmix != Proposed.DefaultSubmix
			|| !FMath::IsNearlyEqual(Current.Volume, Proposed.Volume) || !FMath::IsNearlyEqual(Current.Pitch, Proposed.Pitch)
			|| !FMath::IsNearlyEqual(Current.LowPassFilterFrequency, Proposed.LowPassFilterFrequency)
			|| !FMath::IsNearlyEqual(Current.AttenuationDistanceScale, Proposed.AttenuationDistanceScale)
			|| !FMath::IsNearlyEqual(Current.LFEBleed, Proposed.LFEBleed)
			|| !FMath::IsNearlyEqual(Current.VoiceCenterChannelVolume, Proposed.VoiceCenterChannelVolume)
			|| !FMath::IsNearlyEqual(Current.Default2DReverbSendAmount, Proposed.Default2DReverbSendAmount)
			|| Current.bApplyEffects != Proposed.bApplyEffects || Current.bAlwaysPlay != Proposed.bAlwaysPlay
			|| Current.bIsUISound != Proposed.bIsUISound || Current.bIsMusic != Proposed.bIsMusic
			|| Current.bCenterChannelOnly != Proposed.bCenterChannelOnly || Current.bApplyAmbientVolumes != Proposed.bApplyAmbientVolumes
			|| Current.bReverb != Proposed.bReverb || Current.OutputTarget != Proposed.OutputTarget
			|| Current.LoadingBehavior != Proposed.LoadingBehavior;
		if (!bWouldChange) return MutationJson(Asset, TEXT("settings"), false, false, R.bDryRun, false);
		if (R.bDryRun) return MutationJson(Asset, TEXT("settings"), false, true, true, false);

		TArray<UObject*> ChangedAssets;
		ChangedAssets.Add(Asset);
		if (Asset->ParentClass && Asset->ParentClass != ParentClass) ChangedAssets.AddUnique(Asset->ParentClass);
		if (ParentClass && ParentClass != Asset->ParentClass) ChangedAssets.AddUnique(ParentClass);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditSoundClassSettings", "Edit Sound Class Settings"));
		for (UObject* ChangedAsset : ChangedAssets) ChangedAsset->Modify();
		Asset->Properties = Proposed;
		if (Asset->ParentClass != ParentClass)
		{
			Asset->SetParentClass(ParentClass);
			if (ParentClass) ParentClass->ChildClasses.AddUnique(Asset);
			Asset->RefreshAllGraphs(false);
		}
		for (UObject* ChangedAsset : ChangedAssets)
		{
#if WITH_EDITOR
			ChangedAsset->PostEditChange();
#endif
		}
		MarkAssetsDirty(ChangedAssets);
		SaveAssetsIfRequested(ChangedAssets, R.bSave);
		return MutationJson(Asset, TEXT("settings"), true, true, false, R.bSave);
	}

	FString ValidateSoundClass(USoundClass* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Class");
		TArray<FString> Errors, Warnings;
		const FSoundClassProperties& P = Asset->Properties;
		if (!FMath::IsFinite(P.Volume) || P.Volume < 0.0f) Errors.Add(TEXT("properties.volume must be finite and nonnegative"));
		if (!FMath::IsFinite(P.Pitch) || P.Pitch <= 0.0f) Errors.Add(TEXT("properties.pitch must be finite and positive"));
		if (!FMath::IsFinite(P.LowPassFilterFrequency) || P.LowPassFilterFrequency < 0.0f || P.LowPassFilterFrequency > 20000.0f) Errors.Add(TEXT("properties.low_pass_filter_frequency must be between 0 and 20000 Hz"));
		if (!FMath::IsFinite(P.AttenuationDistanceScale) || P.AttenuationDistanceScale < 0.0f) Errors.Add(TEXT("properties.attenuation_distance_scale must be finite and nonnegative"));
		if (!FMath::IsFinite(P.LFEBleed) || P.LFEBleed < 0.0f) Errors.Add(TEXT("properties.lfe_bleed must be finite and nonnegative"));
		if (!FMath::IsFinite(P.VoiceCenterChannelVolume) || P.VoiceCenterChannelVolume < 0.0f) Errors.Add(TEXT("properties.voice_center_channel_volume must be finite and nonnegative"));
		if (!FMath::IsFinite(P.Default2DReverbSendAmount) || P.Default2DReverbSendAmount < 0.0f) Errors.Add(TEXT("properties.default_2d_reverb_send_amount must be finite and nonnegative"));
		if (static_cast<uint8>(P.LoadingBehavior) > static_cast<uint8>(ESoundWaveLoadingBehavior::LoadOnDemand)) Errors.Add(TEXT("properties.loading_behavior must be Inherited, RetainOnLoad, PrimeOnLoad, or LoadOnDemand for a Sound Class"));
		TSet<USoundClass*> Parents;
		for (USoundClass* Current = Asset; Current; Current = Current->ParentClass)
		{
			if (Parents.Contains(Current)) { Errors.Add(TEXT("Sound Class parent hierarchy contains a cycle")); break; }
			Parents.Add(Current);
		}
		TSet<USoundClass*> Children;
		for (USoundClass* Child : Asset->ChildClasses)
		{
			if (!Child) Errors.Add(TEXT("Sound Class child list contains a null reference"));
			else if (Children.Contains(Child)) Errors.Add(TEXT("Sound Class child list contains a duplicate reference"));
			else
			{
				Children.Add(Child);
				if (Child->ParentClass != Asset) Warnings.Add(FString::Printf(TEXT("Child %s does not point back to this class as its parent"), *Child->GetPathName()));
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		WriteValidation(Asset, TEXT("sound_class_settings_and_hierarchy"), Errors, Warnings, Writer);
		Writer->Close();
		return Json;
	}

	FString InspectSoundMix(USoundMix* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Mix");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("initial_delay"), Asset->InitialDelay);
		Writer->WriteValue(TEXT("fade_in_time"), Asset->FadeInTime);
		Writer->WriteValue(TEXT("duration"), Asset->Duration);
		Writer->WriteValue(TEXT("fade_out_time"), Asset->FadeOutTime);
		Writer->WriteValue(TEXT("apply_eq"), static_cast<bool>(Asset->bApplyEQ));
		Writer->WriteValue(TEXT("eq_priority"), Asset->EQPriority);
		Writer->WriteArrayStart(TEXT("eq_bands"));
		for (int32 Band = 0; Band < 4; ++Band)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("band_index"), Band);
			Writer->WriteValue(TEXT("frequency_center"), GetEQFrequency(Asset->EQSettings, Band));
			Writer->WriteValue(TEXT("gain"), GetEQGain(Asset->EQSettings, Band));
			Writer->WriteValue(TEXT("bandwidth"), GetEQBandwidth(Asset->EQSettings, Band));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("class_adjusters"));
		for (const FSoundClassAdjuster& Adjuster : Asset->SoundClassEffects)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("sound_class_path"), ToPath(Adjuster.SoundClassObject));
			Writer->WriteValue(TEXT("volume_adjuster"), Adjuster.VolumeAdjuster);
			Writer->WriteValue(TEXT("pitch_adjuster"), Adjuster.PitchAdjuster);
			Writer->WriteValue(TEXT("low_pass_filter_frequency"), Adjuster.LowPassFilterFrequency);
			Writer->WriteValue(TEXT("voice_center_channel_volume_adjuster"), Adjuster.VoiceCenterChannelVolumeAdjuster);
			Writer->WriteValue(TEXT("apply_to_children"), static_cast<bool>(Adjuster.bApplyToChildren));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString EditSoundMix(USoundMix* Asset, const FSoundMixSettingsReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Mix");
		float InitialDelay = R.bSetInitialDelay ? R.InitialDelay : Asset->InitialDelay;
		float FadeInTime = R.bSetFadeInTime ? R.FadeInTime : Asset->FadeInTime;
		float Duration = R.bSetDuration ? R.Duration : Asset->Duration;
		float FadeOutTime = R.bSetFadeOutTime ? R.FadeOutTime : Asset->FadeOutTime;
		float EQPriority = R.bSetEQPriority ? R.EQPriority : Asset->EQPriority;
		bool bApplyEQ = R.bSetApplyEQ ? R.bApplyEQ : Asset->bApplyEQ;
		TSet<int32> EditedBands;
		for (const FSoundMixEQBandEditReq& Edit : R.EQBandEdits)
		{
			if (Edit.BandIndex < 0 || Edit.BandIndex > 3 || EditedBands.Contains(Edit.BandIndex)) throw std::runtime_error("eq_band_edits requires unique band_index values from 0 through 3");
			EditedBands.Add(Edit.BandIndex);
			const float Frequency = Edit.bSetFrequencyCenter ? Edit.FrequencyCenter : GetEQFrequency(Asset->EQSettings, Edit.BandIndex);
			const float Gain = Edit.bSetGain ? Edit.Gain : GetEQGain(Asset->EQSettings, Edit.BandIndex);
			const float Bandwidth = Edit.bSetBandwidth ? Edit.Bandwidth : GetEQBandwidth(Asset->EQSettings, Edit.BandIndex);
			if (!FMath::IsFinite(Frequency) || Frequency < 0.0f || Frequency > 20000.0f) throw std::runtime_error("EQ frequency_center must be between 0 and 20000 Hz");
			if (!FMath::IsFinite(Gain) || Gain < 0.0f || Gain > 10.0f) throw std::runtime_error("EQ gain must be between 0 and 10");
			if (!FMath::IsFinite(Bandwidth) || Bandwidth < 0.0f || Bandwidth > 2.0f) throw std::runtime_error("EQ bandwidth must be between 0 and 2");
		}
		if (!FMath::IsFinite(InitialDelay) || InitialDelay < 0.0f || !FMath::IsFinite(FadeInTime) || FadeInTime < 0.0f
			|| !FMath::IsFinite(Duration) || Duration < -1.0f || !FMath::IsFinite(FadeOutTime) || FadeOutTime < 0.0f
			|| !FMath::IsFinite(EQPriority)) throw std::runtime_error("Sound Mix time and EQ settings are outside their valid ranges");
		bool bWouldChange = !FMath::IsNearlyEqual(Asset->InitialDelay, InitialDelay) || !FMath::IsNearlyEqual(Asset->FadeInTime, FadeInTime)
			|| !FMath::IsNearlyEqual(Asset->Duration, Duration) || !FMath::IsNearlyEqual(Asset->FadeOutTime, FadeOutTime)
			|| !FMath::IsNearlyEqual(Asset->EQPriority, EQPriority) || Asset->bApplyEQ != bApplyEQ;
		for (const FSoundMixEQBandEditReq& Edit : R.EQBandEdits)
			bWouldChange |= (Edit.bSetFrequencyCenter && !FMath::IsNearlyEqual(GetEQFrequency(Asset->EQSettings, Edit.BandIndex), Edit.FrequencyCenter))
				|| (Edit.bSetGain && !FMath::IsNearlyEqual(GetEQGain(Asset->EQSettings, Edit.BandIndex), Edit.Gain))
				|| (Edit.bSetBandwidth && !FMath::IsNearlyEqual(GetEQBandwidth(Asset->EQSettings, Edit.BandIndex), Edit.Bandwidth));
		if (!bWouldChange) return MutationJson(Asset, TEXT("settings"), false, false, R.bDryRun, false);
		if (R.bDryRun) return MutationJson(Asset, TEXT("settings"), false, true, true, false);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditSoundMixSettings", "Edit Sound Mix Settings"));
		Asset->Modify();
		Asset->InitialDelay = InitialDelay;
		Asset->FadeInTime = FadeInTime;
		Asset->Duration = Duration;
		Asset->FadeOutTime = FadeOutTime;
		Asset->bApplyEQ = bApplyEQ;
		Asset->EQPriority = EQPriority;
		for (const FSoundMixEQBandEditReq& Edit : R.EQBandEdits)
		{
			if (Edit.bSetFrequencyCenter) SetEQFrequency(Asset->EQSettings, Edit.BandIndex, Edit.FrequencyCenter);
			if (Edit.bSetGain) SetEQGain(Asset->EQSettings, Edit.BandIndex, Edit.Gain);
			if (Edit.bSetBandwidth) SetEQBandwidth(Asset->EQSettings, Edit.BandIndex, Edit.Bandwidth);
		}
#if WITH_EDITOR
		Asset->PostEditChange();
#endif
		Asset->MarkPackageDirty();
		SaveAssetsIfRequested({ Asset }, R.bSave);
		return MutationJson(Asset, TEXT("settings"), true, true, false, R.bSave);
	}

	FString EditSoundMixAdjuster(USoundMix* Asset, const FSoundMixAdjusterReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Mix");
		const FString Operation = R.Operation.TrimStartAndEnd().ToLower();
		if (Operation != TEXT("upsert") && Operation != TEXT("remove")) throw std::runtime_error("operation must be upsert or remove");
		USoundClass* SoundClass = R.SoundClassPath.IsEmpty() ? nullptr : Cast<USoundClass>(StaticLoadObject(USoundClass::StaticClass(), nullptr, *R.SoundClassPath));
		if (!SoundClass) throw std::runtime_error("sound_class_path must identify a Sound Class");
		const int32 ExistingIndex = Asset->SoundClassEffects.IndexOfByPredicate([SoundClass](const FSoundClassAdjuster& Adjuster) { return Adjuster.SoundClassObject == SoundClass; });
		if (Operation == TEXT("remove"))
		{
			if (ExistingIndex == INDEX_NONE) throw std::runtime_error("No Sound Mix adjuster exists for sound_class_path");
			if (!R.bDryRun && !R.bConfirm) throw std::runtime_error("removing a Sound Mix adjuster requires confirm=true");
			if (R.bDryRun) return MutationJson(Asset, Operation, false, true, true, false);
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveSoundMixAdjuster", "Remove Sound Mix Class Adjuster"));
			Asset->Modify();
			Asset->SoundClassEffects.RemoveAt(ExistingIndex);
#if WITH_EDITOR
			Asset->PostEditChange();
#endif
			Asset->MarkPackageDirty();
			SaveAssetsIfRequested({ Asset }, R.bSave);
			return MutationJson(Asset, Operation, true, true, false, R.bSave);
		}

		if (R.bSetVolumeAdjuster && (!FMath::IsFinite(R.VolumeAdjuster) || R.VolumeAdjuster < 0.0f)) throw std::runtime_error("volume_adjuster must be finite and nonnegative");
		if (R.bSetPitchAdjuster && (!FMath::IsFinite(R.PitchAdjuster) || R.PitchAdjuster < 0.0f || R.PitchAdjuster > 8.0f)) throw std::runtime_error("pitch_adjuster must be between 0 and 8");
		if (R.bSetLowPassFilterFrequency && (!FMath::IsFinite(R.LowPassFilterFrequency) || R.LowPassFilterFrequency < 0.0f || R.LowPassFilterFrequency > 20000.0f)) throw std::runtime_error("low_pass_filter_frequency must be between 0 and 20000 Hz");
		if (R.bSetVoiceCenterChannelVolumeAdjuster && (!FMath::IsFinite(R.VoiceCenterChannelVolumeAdjuster) || R.VoiceCenterChannelVolumeAdjuster < 0.0f)) throw std::runtime_error("voice_center_channel_volume_adjuster must be finite and nonnegative");
		FSoundClassAdjuster Proposed = ExistingIndex == INDEX_NONE ? FSoundClassAdjuster() : Asset->SoundClassEffects[ExistingIndex];
		Proposed.SoundClassObject = SoundClass;
		if (R.bSetVolumeAdjuster) Proposed.VolumeAdjuster = R.VolumeAdjuster;
		if (R.bSetPitchAdjuster) Proposed.PitchAdjuster = R.PitchAdjuster;
		if (R.bSetLowPassFilterFrequency) Proposed.LowPassFilterFrequency = R.LowPassFilterFrequency;
		if (R.bSetVoiceCenterChannelVolumeAdjuster) Proposed.VoiceCenterChannelVolumeAdjuster = R.VoiceCenterChannelVolumeAdjuster;
		if (R.bSetApplyToChildren) Proposed.bApplyToChildren = R.bApplyToChildren;
		const bool bWouldChange = ExistingIndex == INDEX_NONE || Proposed.VolumeAdjuster != Asset->SoundClassEffects[ExistingIndex].VolumeAdjuster
			|| Proposed.PitchAdjuster != Asset->SoundClassEffects[ExistingIndex].PitchAdjuster
			|| Proposed.LowPassFilterFrequency != Asset->SoundClassEffects[ExistingIndex].LowPassFilterFrequency
			|| Proposed.VoiceCenterChannelVolumeAdjuster != Asset->SoundClassEffects[ExistingIndex].VoiceCenterChannelVolumeAdjuster
			|| Proposed.bApplyToChildren != Asset->SoundClassEffects[ExistingIndex].bApplyToChildren;
		if (!bWouldChange) return MutationJson(Asset, Operation, false, false, R.bDryRun, false);
		if (R.bDryRun) return MutationJson(Asset, Operation, false, true, true, false);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "UpsertSoundMixAdjuster", "Upsert Sound Mix Class Adjuster"));
		Asset->Modify();
		if (ExistingIndex == INDEX_NONE) Asset->SoundClassEffects.Add(Proposed);
		else Asset->SoundClassEffects[ExistingIndex] = Proposed;
#if WITH_EDITOR
		Asset->PostEditChange();
#endif
		Asset->MarkPackageDirty();
		SaveAssetsIfRequested({ Asset }, R.bSave);
		return MutationJson(Asset, Operation, true, true, false, R.bSave);
	}

	FString ValidateSoundMix(USoundMix* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Mix");
		TArray<FString> Errors, Warnings;
		if (!FMath::IsFinite(Asset->InitialDelay) || Asset->InitialDelay < 0.0f) Errors.Add(TEXT("initial_delay must be finite and nonnegative"));
		if (!FMath::IsFinite(Asset->FadeInTime) || Asset->FadeInTime < 0.0f) Errors.Add(TEXT("fade_in_time must be finite and nonnegative"));
		if (!FMath::IsFinite(Asset->Duration) || Asset->Duration < -1.0f) Errors.Add(TEXT("duration must be -1 or finite and nonnegative"));
		if (!FMath::IsFinite(Asset->FadeOutTime) || Asset->FadeOutTime < 0.0f) Errors.Add(TEXT("fade_out_time must be finite and nonnegative"));
		if (!FMath::IsFinite(Asset->EQPriority)) Errors.Add(TEXT("eq_priority must be finite"));
		for (int32 Band = 0; Band < 4; ++Band)
		{
			if (!FMath::IsFinite(GetEQFrequency(Asset->EQSettings, Band)) || GetEQFrequency(Asset->EQSettings, Band) < 0.0f || GetEQFrequency(Asset->EQSettings, Band) > 20000.0f) Errors.Add(FString::Printf(TEXT("EQ band %d frequency must be between 0 and 20000 Hz"), Band));
			if (!FMath::IsFinite(GetEQGain(Asset->EQSettings, Band)) || GetEQGain(Asset->EQSettings, Band) < 0.0f || GetEQGain(Asset->EQSettings, Band) > 10.0f) Errors.Add(FString::Printf(TEXT("EQ band %d gain must be between 0 and 10"), Band));
			if (!FMath::IsFinite(GetEQBandwidth(Asset->EQSettings, Band)) || GetEQBandwidth(Asset->EQSettings, Band) < 0.0f || GetEQBandwidth(Asset->EQSettings, Band) > 2.0f) Errors.Add(FString::Printf(TEXT("EQ band %d bandwidth must be between 0 and 2"), Band));
		}
		TSet<USoundClass*> AdjustedClasses;
		for (const FSoundClassAdjuster& Adjuster : Asset->SoundClassEffects)
		{
			if (!Adjuster.SoundClassObject) { Errors.Add(TEXT("Sound Mix contains an adjuster with no Sound Class")); continue; }
			if (AdjustedClasses.Contains(Adjuster.SoundClassObject)) Errors.Add(FString::Printf(TEXT("Sound Mix contains duplicate adjusters for %s"), *Adjuster.SoundClassObject->GetPathName()));
			AdjustedClasses.Add(Adjuster.SoundClassObject);
			if (!FMath::IsFinite(Adjuster.VolumeAdjuster) || Adjuster.VolumeAdjuster < 0.0f) Errors.Add(TEXT("Sound Mix volume adjusters must be finite and nonnegative"));
			if (!FMath::IsFinite(Adjuster.PitchAdjuster) || Adjuster.PitchAdjuster < 0.0f || Adjuster.PitchAdjuster > 8.0f) Errors.Add(TEXT("Sound Mix pitch adjusters must be between 0 and 8"));
			if (!FMath::IsFinite(Adjuster.LowPassFilterFrequency) || Adjuster.LowPassFilterFrequency < 0.0f || Adjuster.LowPassFilterFrequency > 20000.0f) Errors.Add(TEXT("Sound Mix low-pass frequencies must be between 0 and 20000 Hz"));
			if (!FMath::IsFinite(Adjuster.VoiceCenterChannelVolumeAdjuster) || Adjuster.VoiceCenterChannelVolumeAdjuster < 0.0f) Errors.Add(TEXT("Sound Mix center-channel adjusters must be finite and nonnegative"));
		}
		if (SoundMixHasPassiveActivationLoop(Asset)) Errors.Add(TEXT("Sound Mix has a passive activation dependency loop"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		WriteValidation(Asset, TEXT("sound_mix_timing_eq_and_class_adjusters"), Errors, Warnings, Writer);
		Writer->Close();
		return Json;
	}

	FString InspectSoundSubmix(USoundSubmix* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Submix");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("parent_submix_path"), ToPath(Asset->ParentSubmix));
		Writer->WriteValue(TEXT("auto_disable"), Asset->bAutoDisable);
		Writer->WriteValue(TEXT("auto_disable_time"), Asset->AutoDisableTime);
		Writer->WriteValue(TEXT("mute_when_backgrounded"), static_cast<bool>(Asset->bMuteWhenBackgrounded));
		Writer->WriteValue(TEXT("envelope_follower_attack_time"), Asset->EnvelopeFollowerAttackTime);
		Writer->WriteValue(TEXT("envelope_follower_release_time"), Asset->EnvelopeFollowerReleaseTime);
		Writer->WriteValue(TEXT("output_volume_db"), Asset->OutputVolumeModulation.Value);
		Writer->WriteValue(TEXT("wet_level_db"), Asset->WetLevelModulation.Value);
		Writer->WriteValue(TEXT("dry_level_db"), Asset->DryLevelModulation.Value);
		Writer->WriteValue(TEXT("is_dynamic"), Asset->IsDynamic(false));
		Writer->WriteArrayStart(TEXT("children"));
		for (const USoundSubmixBase* Child : Asset->ChildSubmixes) Writer->WriteValue(Child ? Child->GetPathName() : FString());
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("effects"));
		for (const USoundEffectSubmixPreset* Effect : Asset->SubmixEffectChain) Writer->WriteValue(Effect ? Effect->GetPathName() : FString());
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString EditSoundSubmix(USoundSubmix* Asset, const FSoundSubmixSettingsReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Submix");
		USoundSubmixBase* Parent = Asset->ParentSubmix;
		if (R.bSetParentSubmix)
		{
			Parent = R.ParentSubmixPath.IsEmpty() ? nullptr : Cast<USoundSubmixBase>(StaticLoadObject(USoundSubmixBase::StaticClass(), nullptr, *R.ParentSubmixPath));
			if (!R.ParentSubmixPath.IsEmpty() && !Parent) throw std::runtime_error("parent_submix_path must identify a Sound Submix asset");
			if (Parent && SubmixParentWouldCycle(Asset, Parent)) throw std::runtime_error("parent_submix_path would introduce a Sound Submix hierarchy cycle");
			if (R.bSave && IsEngineAsset(Parent)) throw std::runtime_error("saving this parent assignment would modify an Engine Sound Submix; duplicate it into /Game first");
		}
		const float AutoDisableTime = R.bSetAutoDisableTime ? R.AutoDisableTime : Asset->AutoDisableTime;
		const int32 Attack = R.bSetEnvelopeFollowerAttackTime ? R.EnvelopeFollowerAttackTime : Asset->EnvelopeFollowerAttackTime;
		const int32 Release = R.bSetEnvelopeFollowerReleaseTime ? R.EnvelopeFollowerReleaseTime : Asset->EnvelopeFollowerReleaseTime;
		const float OutputDb = R.bSetOutputVolumeDb ? R.OutputVolumeDb : Asset->OutputVolumeModulation.Value;
		const float WetDb = R.bSetWetLevelDb ? R.WetLevelDb : Asset->WetLevelModulation.Value;
		const float DryDb = R.bSetDryLevelDb ? R.DryLevelDb : Asset->DryLevelModulation.Value;
		if (!FMath::IsFinite(AutoDisableTime) || AutoDisableTime < 0.0f || Attack < 0 || Release < 0) throw std::runtime_error("Submix auto-disable and envelope-following settings must be nonnegative");
		for (float Value : {OutputDb, WetDb, DryDb}) if (!FMath::IsFinite(Value) || Value < -96.0f || Value > 0.0f) throw std::runtime_error("Submix output, wet, and dry levels must be between -96 and 0 dB");
		const bool bAutoDisable = R.bSetAutoDisable ? R.bAutoDisable : Asset->bAutoDisable;
		const bool bMute = R.bSetMuteWhenBackgrounded ? R.bMuteWhenBackgrounded : Asset->bMuteWhenBackgrounded;
		const bool bWouldChange = Parent != Asset->ParentSubmix || bAutoDisable != Asset->bAutoDisable
			|| !FMath::IsNearlyEqual(AutoDisableTime, Asset->AutoDisableTime) || bMute != Asset->bMuteWhenBackgrounded
			|| Attack != Asset->EnvelopeFollowerAttackTime || Release != Asset->EnvelopeFollowerReleaseTime
			|| !FMath::IsNearlyEqual(OutputDb, Asset->OutputVolumeModulation.Value)
			|| !FMath::IsNearlyEqual(WetDb, Asset->WetLevelModulation.Value)
			|| !FMath::IsNearlyEqual(DryDb, Asset->DryLevelModulation.Value);
		if (!bWouldChange) return MutationJson(Asset, TEXT("settings"), false, false, R.bDryRun, false);
		if (R.bDryRun) return MutationJson(Asset, TEXT("settings"), false, true, true, false);
		TArray<UObject*> ChangedAssets = { Asset };
		if (Asset->ParentSubmix && Asset->ParentSubmix != Parent) ChangedAssets.AddUnique(Asset->ParentSubmix);
		if (Parent && Parent != Asset->ParentSubmix) ChangedAssets.AddUnique(Parent);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditSoundSubmixSettings", "Edit Sound Submix Settings"));
		for (UObject* ChangedAsset : ChangedAssets) ChangedAsset->Modify();
		if (Parent != Asset->ParentSubmix) Asset->SetParentSubmix(Parent, true);
		Asset->bAutoDisable = bAutoDisable;
		Asset->AutoDisableTime = AutoDisableTime;
		Asset->bMuteWhenBackgrounded = bMute;
		Asset->EnvelopeFollowerAttackTime = Attack;
		Asset->EnvelopeFollowerReleaseTime = Release;
		Asset->OutputVolumeModulation.Value = OutputDb;
		Asset->WetLevelModulation.Value = WetDb;
		Asset->DryLevelModulation.Value = DryDb;
#if WITH_EDITOR
		Asset->PostEditChange();
#endif
		MarkAssetsDirty(ChangedAssets);
		SaveAssetsIfRequested(ChangedAssets, R.bSave);
		return MutationJson(Asset, TEXT("settings"), true, true, false, R.bSave);
	}

	FString EditSoundSubmixEffect(USoundSubmix* Asset, const FSoundSubmixEffectReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Submix");
		const FString Operation = R.Operation.TrimStartAndEnd().ToLower();
		if (Operation != TEXT("add") && Operation != TEXT("remove")) throw std::runtime_error("operation must be add or remove");
		USoundEffectSubmixPreset* Effect = R.EffectPath.IsEmpty() ? nullptr : Cast<USoundEffectSubmixPreset>(StaticLoadObject(USoundEffectSubmixPreset::StaticClass(), nullptr, *R.EffectPath));
		if (!Effect) throw std::runtime_error("effect_path must identify a Sound Effect Submix Preset");
		const int32 ExistingIndex = Asset->SubmixEffectChain.IndexOfByKey(Effect);
		if (Operation == TEXT("add") && ExistingIndex != INDEX_NONE) return MutationJson(Asset, Operation, false, false, R.bDryRun, false);
		if (Operation == TEXT("remove") && ExistingIndex == INDEX_NONE) throw std::runtime_error("effect_path is not present in this submix effect chain");
		if (Operation == TEXT("remove") && !R.bDryRun && !R.bConfirm) throw std::runtime_error("removing a submix effect requires confirm=true");
		if (R.bDryRun) return MutationJson(Asset, Operation, false, true, true, false);
		const FScopedTransaction Transaction(Operation == TEXT("add")
			? NSLOCTEXT("UE5_MCP", "AddSoundSubmixEffect", "Add Sound Submix Effect")
			: NSLOCTEXT("UE5_MCP", "RemoveSoundSubmixEffect", "Remove Sound Submix Effect"));
		Asset->Modify();
		if (Operation == TEXT("add")) Asset->SubmixEffectChain.Add(Effect);
		else Asset->SubmixEffectChain.RemoveAt(ExistingIndex);
#if WITH_EDITOR
		Asset->PostEditChange();
#endif
		Asset->MarkPackageDirty();
		SaveAssetsIfRequested({ Asset }, R.bSave);
		return MutationJson(Asset, Operation, true, true, false, R.bSave);
	}

	FString ValidateSoundSubmix(USoundSubmix* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Sound Submix");
		TArray<FString> Errors, Warnings;
		if (!FMath::IsFinite(Asset->AutoDisableTime) || Asset->AutoDisableTime < 0.0f) Errors.Add(TEXT("auto_disable_time must be finite and nonnegative"));
		if (Asset->EnvelopeFollowerAttackTime < 0) Errors.Add(TEXT("envelope_follower_attack_time must be nonnegative"));
		if (Asset->EnvelopeFollowerReleaseTime < 0) Errors.Add(TEXT("envelope_follower_release_time must be nonnegative"));
		for (const TPair<const TCHAR*, float>& Value : { TPair<const TCHAR*, float>(TEXT("output_volume_db"), Asset->OutputVolumeModulation.Value), TPair<const TCHAR*, float>(TEXT("wet_level_db"), Asset->WetLevelModulation.Value), TPair<const TCHAR*, float>(TEXT("dry_level_db"), Asset->DryLevelModulation.Value) })
			if (!FMath::IsFinite(Value.Value) || Value.Value < -96.0f || Value.Value > 0.0f) Errors.Add(FString::Printf(TEXT("%s must be between -96 and 0 dB"), Value.Key));
		if (SubmixParentWouldCycle(Asset, Asset->ParentSubmix)) Errors.Add(TEXT("Sound Submix parent hierarchy contains a cycle"));
		if (Asset->ParentSubmix && !Asset->ParentSubmix->ChildSubmixes.Contains(Asset)) Warnings.Add(TEXT("Parent Submix child list does not include this asset"));
		for (const USoundSubmixBase* Child : Asset->ChildSubmixes)
			if (!Child) Errors.Add(TEXT("Sound Submix child list contains a null reference"));
			else if (const USoundSubmixWithParentBase* ChildWithParent = Cast<USoundSubmixWithParentBase>(Child); ChildWithParent && ChildWithParent->ParentSubmix != Asset)
				Warnings.Add(FString::Printf(TEXT("Child Submix %s does not point back to this asset"), *Child->GetPathName()));
		TSet<const USoundEffectSubmixPreset*> Effects;
		for (const USoundEffectSubmixPreset* Effect : Asset->SubmixEffectChain)
		{
			if (!Effect) Errors.Add(TEXT("submix effect chain contains a null reference"));
			else if (Effects.Contains(Effect)) Errors.Add(TEXT("submix effect chain contains a duplicate preset"));
			else Effects.Add(Effect);
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		WriteValidation(Asset, TEXT("sound_submix_settings_parent_and_effect_chain"), Errors, Warnings, Writer);
		Writer->Close();
		return Json;
	}
}
