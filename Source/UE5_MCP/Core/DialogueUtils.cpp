#include "DialogueUtils.h"
#include "UE5_MCP/API/DTO/DialogueReq.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "Factories/DialogueVoiceFactory.h"
#include "Factories/DialogueWaveFactory.h"
#include "MetasoundSource.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Sound/DialogueVoice.h"
#include "Sound/DialogueWave.h"
#include "Sound/SoundWave.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include <stdexcept>

namespace
{
	const TCHAR* Genders[] = {TEXT("Neuter"), TEXT("Masculine"), TEXT("Feminine"), TEXT("Mixed")};
	const TCHAR* Numbers[] = {TEXT("Singular"), TEXT("Plural")};
	template<size_t N> int32 EnumIndex(const FString& Name, const TCHAR* const (&Names)[N])
	{
		for (int32 Index = 0; Index < N; ++Index) if (Name.Equals(Names[Index], ESearchCase::IgnoreCase)) return Index;
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Unsupported dialogue enum value: %s"), *Name)));
	}
	FString Path(const UObject* Object) { return Object ? Object->GetPathName() : FString(); }
	void Save(UObject* Asset, bool bSave)
	{
		if (!bSave) return;
		UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!Subsystem || !Subsystem->SaveAsset(Asset->GetPathName(), true)) throw std::runtime_error("Dialogue asset changed but saving failed");
	}
	FString Result(UObject* Asset, const FString& Operation, bool bWouldChange, bool bDryRun, bool bSave, const FString& ContextId = TEXT(""))
	{
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json);
		W->WriteObjectStart(); W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("operation"), Operation);
		W->WriteValue(TEXT("context_id"), ContextId); W->WriteValue(TEXT("would_change"), bWouldChange); W->WriteValue(TEXT("changed"), bWouldChange && !bDryRun);
		W->WriteValue(TEXT("dry_run"), bDryRun); W->WriteValue(TEXT("saved"), bWouldChange && !bDryRun && bSave);
		W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}
	bool ValidFormat(const FString& Format)
	{
		const FString Remainder = Format.Replace(TEXT("{ContextHash}"), TEXT(""));
		return !Format.TrimStartAndEnd().IsEmpty() && Format.Len() <= 256 && !Remainder.Contains(TEXT("{")) && !Remainder.Contains(TEXT("}"));
	}
	bool RecordedWave(const USoundWave* Wave)
	{
		return Wave && !Wave->bProcedural && !Wave->bIsSourceBus && !Wave->IsA<UMetaSoundSource>()
			&& FMath::IsFinite(Wave->Duration) && Wave->Duration > 0.0f;
	}
	UDialogueVoice* LoadVoice(const FString& VoicePath)
	{
		UDialogueVoice* Voice = VoicePath.IsEmpty() ? nullptr : Cast<UDialogueVoice>(StaticLoadObject(UDialogueVoice::StaticClass(), nullptr, *VoicePath));
		if (!Voice || !Voice->LocalizationGUID.IsValid()) throw std::runtime_error("speaker and target paths must identify Dialogue Voice assets with valid localization GUIDs");
		return Voice;
	}
	FDialogueContext Context(const FString& SpeakerPath, const TArray<FString>& TargetPaths)
	{
		if (TargetPaths.Num() > 64) throw std::runtime_error("Dialogue context targets are limited to 64 voices");
		FDialogueContext C; C.Speaker = LoadVoice(SpeakerPath); C.Targets.Reset(); TSet<UDialogueVoice*> Seen;
		for (const FString& TargetPath : TargetPaths)
		{
			UDialogueVoice* Voice = LoadVoice(TargetPath);
			if (Seen.Contains(Voice)) throw std::runtime_error("target_paths must not contain duplicate voices");
			Seen.Add(Voice); C.Targets.Add(Voice);
		}
		return C;
	}
	int32 Select(const TArray<FDialogueContextMapping>& Mappings, const FDialogueContextReq& R)
	{
		if (!R.ContextId.IsEmpty())
		{
			int32 Found = INDEX_NONE;
			for (int32 Index = 0; Index < Mappings.Num(); ++Index) if (Mappings[Index].Context.GetContextHash().Equals(R.ContextId, ESearchCase::IgnoreCase))
			{
				if (Found != INDEX_NONE) throw std::runtime_error("context_id is ambiguous; the asset contains duplicate context hashes");
				Found = Index;
			}
			return Found;
		}
		const FDialogueContext Requested = Context(R.SpeakerPath, R.TargetPaths);
		return Mappings.IndexOfByPredicate([&Requested](const FDialogueContextMapping& M) { return M.Context == Requested; });
	}
	void CheckVoice(const UDialogueVoice* Voice, TArray<FString>& Errors)
	{
		if (!Voice->LocalizationGUID.IsValid()) Errors.Add(TEXT("Dialogue Voice localization GUID is invalid"));
		if (static_cast<uint8>(Voice->Gender) >= UE_ARRAY_COUNT(Genders)) Errors.Add(TEXT("Dialogue Voice gender enum is invalid"));
		if (static_cast<uint8>(Voice->Plurality) >= UE_ARRAY_COUNT(Numbers)) Errors.Add(TEXT("Dialogue Voice plurality enum is invalid"));
	}
	bool CheckMappings(const UDialogueWave* Wave, const TArray<FDialogueContextMapping>& Mappings, TArray<FString>& Errors, TArray<FString>& Warnings)
	{
		bool bReady = !Mappings.IsEmpty(); TSet<FString> ContextIds, LocalizationKeys;
		if (!Wave->LocalizationGUID.IsValid()) Errors.Add(TEXT("Dialogue Wave localization GUID is invalid"));
		if (Mappings.Num() > 128) Errors.Add(TEXT("Dialogue context mappings exceed the adapter limit of 128"));
		if (Mappings.IsEmpty()) Warnings.Add(TEXT("Dialogue Wave has no context mappings"));
		for (int32 Index = 0; Index < Mappings.Num(); ++Index)
		{
			const FDialogueContextMapping& M = Mappings[Index];
			if (!M.Context.Speaker) { Warnings.Add(FString::Printf(TEXT("Context %d has no speaker"), Index)); bReady = false; }
			else CheckVoice(M.Context.Speaker, Errors);
			if (!M.SoundWave) { Warnings.Add(FString::Printf(TEXT("Context %d has no Sound Wave"), Index)); bReady = false; }
			else if (!RecordedWave(M.SoundWave)) Errors.Add(FString::Printf(TEXT("Context %d requires a recorded, non-procedural Sound Wave with positive duration"), Index));
			if (M.Context.Targets.Num() > 64) Errors.Add(FString::Printf(TEXT("Context %d exceeds 64 targets"), Index));
			TSet<UDialogueVoice*> Targets;
			for (UDialogueVoice* Target : M.Context.Targets)
			{
				if (!Target) { Warnings.Add(FString::Printf(TEXT("Context %d contains an unspecified target"), Index)); bReady = false; }
				else if (Targets.Contains(Target)) Errors.Add(FString::Printf(TEXT("Context %d contains duplicate target voices"), Index));
				else { Targets.Add(Target); CheckVoice(Target, Errors); }
			}
			const FString Id = M.Context.GetContextHash();
			if (ContextIds.Contains(Id)) Errors.Add(TEXT("Dialogue Wave contains duplicate native context hashes"));
			ContextIds.Add(Id);
			if (!ValidFormat(M.LocalizationKeyFormat)) Errors.Add(FString::Printf(TEXT("Context %d localization format must be nonempty and may use only {ContextHash}"), Index));
			else
			{
				const FString Key = M.GetLocalizationKey(Wave->LocalizationGUID.ToString());
				if (LocalizationKeys.Contains(Key)) Errors.Add(TEXT("Dialogue Wave contains duplicate localization keys"));
				LocalizationKeys.Add(Key);
			}
		}
		return bReady && Errors.IsEmpty();
	}
	void RequireMappings(const UDialogueWave* Wave, const TArray<FDialogueContextMapping>& Mappings)
	{
		TArray<FString> Errors, Warnings; CheckMappings(Wave, Mappings, Errors, Warnings);
		if (!Errors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(Errors, TEXT("; "))));
	}
	void Refresh(UDialogueWave* Wave)
	{
		for (FDialogueContextMapping& M : Wave->ContextMappings)
		{
			TArray<UDialogueVoice*> Targets; for (UDialogueVoice* Target : M.Context.Targets) Targets.Add(Target);
			Wave->UpdateContext(M, M.SoundWave, M.Context.Speaker, Targets);
		}
	}
	void Changed(UObject* Asset, bool bSave) { Asset->PostEditChange(); Asset->MarkPackageDirty(); Save(Asset, bSave); }
}

namespace DialogueUtils
{
	FString Create(const FDialogueCreateReq& R)
	{
		if (!R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(R.AssetPath)) throw std::runtime_error("asset_path must be a valid /Game package name without an object suffix");
		const FString Type = R.AssetType.TrimStartAndEnd().ToLower();
		if (Type != TEXT("voice") && Type != TEXT("wave")) throw std::runtime_error("asset_type must be voice or wave");
		FAssetToolsModule& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		FString Package, Name; Tools.Get().CreateUniqueAssetName(R.AssetPath, TEXT(""), Package, Name);
		UObject* Asset = nullptr;
		if (!R.bDryRun)
		{
			UFactory* Factory = Type == TEXT("voice") ? static_cast<UFactory*>(NewObject<UDialogueVoiceFactory>()) : static_cast<UFactory*>(NewObject<UDialogueWaveFactory>());
			UClass* Class = Type == TEXT("voice") ? UDialogueVoice::StaticClass() : UDialogueWave::StaticClass();
			Asset = Tools.Get().CreateAsset(Name, FPackageName::GetLongPackagePath(Package), Class, Factory);
			if (!Asset) throw std::runtime_error("Native dialogue factory failed to create an asset");
			Asset->MarkPackageDirty(); Save(Asset, R.bSave);
		}
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("asset_path"), Package + TEXT(".") + Name); W->WriteValue(TEXT("asset_type"), Type);
		W->WriteValue(TEXT("created"), !R.bDryRun); W->WriteValue(TEXT("would_create"), true); W->WriteValue(TEXT("dry_run"), R.bDryRun);
		W->WriteValue(TEXT("saved"), !R.bDryRun && R.bSave); W->WriteValue(TEXT("dirty"), Asset && Asset->GetOutermost()->IsDirty());
		if (UDialogueVoice* Voice = Cast<UDialogueVoice>(Asset)) W->WriteValue(TEXT("localization_guid"), Voice->LocalizationGUID.ToString());
		else if (UDialogueWave* Wave = Cast<UDialogueWave>(Asset)) W->WriteValue(TEXT("localization_guid"), Wave->LocalizationGUID.ToString());
		W->WriteObjectEnd(); W->Close(); return Json;
	}
	FString VoiceJson(UDialogueVoice* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Dialogue Voice");
		const uint8 Gender = Asset->Gender, Number = Asset->Plurality;
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("localization_guid"), Asset->LocalizationGUID.ToString());
		W->WriteValue(TEXT("gender"), Gender < UE_ARRAY_COUNT(Genders) ? Genders[Gender] : TEXT("Invalid"));
		W->WriteValue(TEXT("plurality"), Number < UE_ARRAY_COUNT(Numbers) ? Numbers[Number] : TEXT("Invalid"));
		W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}
	FString EditVoice(UDialogueVoice* Asset, const FDialogueVoiceSettingsReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Dialogue Voice");
		const int32 Gender = R.Gender.IsEmpty() ? static_cast<uint8>(Asset->Gender) : EnumIndex(R.Gender, Genders);
		const int32 Number = R.Plurality.IsEmpty() ? static_cast<uint8>(Asset->Plurality) : EnumIndex(R.Plurality, Numbers);
		if (Gender >= UE_ARRAY_COUNT(Genders) || Number >= UE_ARRAY_COUNT(Numbers)) throw std::runtime_error("Dialogue Voice enums are invalid");
		const bool bChange = Gender != static_cast<uint8>(Asset->Gender) || Number != static_cast<uint8>(Asset->Plurality);
		if (bChange && !R.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditDialogueVoice", "Edit Dialogue Voice")); Asset->Modify();
			Asset->Gender = static_cast<EGrammaticalGender::Type>(Gender); Asset->Plurality = static_cast<EGrammaticalNumber::Type>(Number); Changed(Asset, R.bSave);
		}
		return Result(Asset, TEXT("voice_settings"), bChange, R.bDryRun, R.bSave);
	}
	FString WaveJson(UDialogueWave* Asset)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Dialogue Wave");
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("localization_guid"), Asset->LocalizationGUID.ToString());
		W->WriteValue(TEXT("spoken_text"), Asset->SpokenText); W->WriteValue(TEXT("subtitle_override"), Asset->SubtitleOverride);
		W->WriteValue(TEXT("override_subtitle"), static_cast<bool>(Asset->bOverride_SubtitleOverride)); W->WriteValue(TEXT("mature"), static_cast<bool>(Asset->bMature));
		W->WriteValue(TEXT("voice_actor_direction"), Asset->VoiceActorDirection); W->WriteArrayStart(TEXT("contexts"));
		for (int32 Index = 0; Index < Asset->ContextMappings.Num(); ++Index)
		{
			const FDialogueContextMapping& M = Asset->ContextMappings[Index]; W->WriteObjectStart();
			W->WriteValue(TEXT("index"), Index); W->WriteValue(TEXT("context_id"), M.Context.GetContextHash()); W->WriteValue(TEXT("speaker_path"), Path(M.Context.Speaker));
			W->WriteArrayStart(TEXT("target_paths")); for (UDialogueVoice* Target : M.Context.Targets) W->WriteValue(Path(Target)); W->WriteArrayEnd();
			W->WriteValue(TEXT("sound_wave_path"), Path(M.SoundWave)); W->WriteValue(TEXT("localization_key_format"), M.LocalizationKeyFormat);
			const bool bFormat = ValidFormat(M.LocalizationKeyFormat);
			W->WriteValue(TEXT("localization_key"), bFormat ? Asset->GetContextLocalizationKey(M) : TEXT(""));
			W->WriteValue(TEXT("localized_spoken_text"), bFormat ? Asset->GetLocalizedSpokenText(M).ToString() : TEXT(""));
			W->WriteValue(TEXT("localized_subtitle"), bFormat ? Asset->GetLocalizedSubtitle(M).ToString() : TEXT(""));
			USoundBase* Proxy = M.Context.Speaker && M.SoundWave ? Asset->GetWaveFromContext(M) : nullptr;
			W->WriteValue(TEXT("proxy_available"), Proxy != nullptr); W->WriteObjectEnd();
		}
		W->WriteArrayEnd(); W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}
	FString EditWave(UDialogueWave* Asset, const FDialogueWaveSettingsReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Dialogue Wave");
		if (R.SpokenText.Len() > 65536 || R.SubtitleOverride.Len() > 65536 || R.VoiceActorDirection.Len() > 65536) throw std::runtime_error("Dialogue text fields are limited to 65536 characters per request");
		RequireMappings(Asset, Asset->ContextMappings);
		const bool bChange = (R.bSetSpokenText && Asset->SpokenText != R.SpokenText)
			|| (R.bSetSubtitleOverride && Asset->SubtitleOverride != R.SubtitleOverride)
			|| (R.bSetOverrideSubtitle && Asset->bOverride_SubtitleOverride != R.bOverrideSubtitle)
			|| (R.bSetVoiceActorDirection && Asset->VoiceActorDirection != R.VoiceActorDirection) || (R.bSetMature && Asset->bMature != R.bMature);
		if (bChange && !R.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditDialogueWave", "Edit Dialogue Wave")); Asset->Modify();
			if (R.bSetSpokenText) Asset->SpokenText = R.SpokenText;
			if (R.bSetSubtitleOverride) Asset->SubtitleOverride = R.SubtitleOverride;
			if (R.bSetOverrideSubtitle) Asset->bOverride_SubtitleOverride = R.bOverrideSubtitle;
			if (R.bSetVoiceActorDirection) Asset->VoiceActorDirection = R.VoiceActorDirection;
			if (R.bSetMature) Asset->bMature = R.bMature;
			Refresh(Asset); Changed(Asset, R.bSave);
		}
		return Result(Asset, TEXT("wave_settings"), bChange, R.bDryRun, R.bSave);
	}
	FString EditContext(UDialogueWave* Asset, const FDialogueContextReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Dialogue Wave");
		TArray<FDialogueContextMapping> Proposed = Asset->ContextMappings;
		const FString Operation = R.Operation.TrimStartAndEnd().ToLower(); FString ResultId = R.ContextId;
		if (Operation == TEXT("clear"))
		{
			if (!Proposed.IsEmpty() && !R.bDryRun && !R.bConfirm) throw std::runtime_error("clearing dialogue context mappings requires confirm=true"); Proposed.Reset();
		}
		else
		{
			int32 Index = Select(Proposed, R);
			if (Operation == TEXT("remove"))
			{
				if (Index == INDEX_NONE) throw std::runtime_error("Dialogue context mapping was not found");
				if (!R.bDryRun && !R.bConfirm) throw std::runtime_error("removing a dialogue context mapping requires confirm=true");
				ResultId = Proposed[Index].Context.GetContextHash(); Proposed.RemoveAt(Index);
			}
			else if (Operation == TEXT("upsert"))
			{
				if (!R.ContextId.IsEmpty() && Index == INDEX_NONE) throw std::runtime_error("context_id was not found");
				const bool bNew = Index == INDEX_NONE;
				FDialogueContextMapping Mapping = bNew ? FDialogueContextMapping() : Proposed[Index];
				if (bNew || R.bSetSpeaker) Mapping.Context.Speaker = LoadVoice(R.SpeakerPath);
				if (bNew || R.bSetTargets) Mapping.Context.Targets = Context(Path(Mapping.Context.Speaker), R.TargetPaths).Targets;
				if (R.bSetSoundWave)
				{
					Mapping.SoundWave = R.SoundWavePath.IsEmpty() ? nullptr : Cast<USoundWave>(StaticLoadObject(USoundWave::StaticClass(), nullptr, *R.SoundWavePath));
					if (!R.SoundWavePath.IsEmpty() && !RecordedWave(Mapping.SoundWave)) throw std::runtime_error("sound_wave_path must identify a recorded Sound Wave");
				}
				if (R.bSetLocalizationKeyFormat) Mapping.LocalizationKeyFormat = R.LocalizationKeyFormat;
				if (bNew && Proposed.Num() == 1 && !Proposed[0].Context.Speaker && !Proposed[0].SoundWave
					&& !Proposed[0].Context.Targets.ContainsByPredicate([](const TObjectPtr<UDialogueVoice>& Voice) { return Voice != nullptr; })) Index = 0;
				if (Index == INDEX_NONE)
				{
					if (Proposed.Num() >= 128) throw std::runtime_error("Dialogue mappings are limited to 128 contexts"); Proposed.Add(Mapping);
				}
				else Proposed[Index] = Mapping;
				ResultId = Mapping.Context.GetContextHash();
			}
			else throw std::runtime_error("operation must be upsert, remove, or clear");
		}
		RequireMappings(Asset, Proposed);
		bool bChange = Asset->ContextMappings.Num() != Proposed.Num();
		if (!bChange) for (int32 Index = 0; Index < Proposed.Num(); ++Index)
			if (Asset->ContextMappings[Index] != Proposed[Index] || Asset->ContextMappings[Index].LocalizationKeyFormat != Proposed[Index].LocalizationKeyFormat) { bChange = true; break; }
		if (bChange && !R.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditDialogueContext", "Edit Dialogue Context")); Asset->Modify();
			Asset->ContextMappings = Proposed; Refresh(Asset); Changed(Asset, R.bSave);
		}
		return Result(Asset, Operation, bChange, R.bDryRun, R.bSave, ResultId);
	}
	FString Resolve(UDialogueWave* Asset, const FDialogueContextReq& R)
	{
		if (!Asset) throw std::runtime_error("Asset is not a Dialogue Wave"); RequireMappings(Asset, Asset->ContextMappings);
		const int32 Index = Select(Asset->ContextMappings, R);
		const FDialogueContextMapping* M = Asset->ContextMappings.IsValidIndex(Index) ? &Asset->ContextMappings[Index] : nullptr;
		USoundBase* Proxy = M && M->Context.Speaker ? Asset->GetWaveFromContext(M->Context) : nullptr;
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("found"), M != nullptr);
		W->WriteValue(TEXT("context_id"), M ? M->Context.GetContextHash() : R.ContextId);
		W->WriteValue(TEXT("supports_context"), M && Asset->SupportsContext(M->Context)); W->WriteValue(TEXT("playable"), Proxy && M->SoundWave && RecordedWave(M->SoundWave) && Proxy->IsPlayable());
		W->WriteValue(TEXT("sound_wave_path"), M ? Path(M->SoundWave) : TEXT("")); W->WriteValue(TEXT("proxy_class"), Proxy ? Proxy->GetClass()->GetPathName() : TEXT(""));
		W->WriteValue(TEXT("localized_spoken_text"), M ? Asset->GetLocalizedSpokenText(*M).ToString() : TEXT(""));
		W->WriteValue(TEXT("localized_subtitle"), M ? Asset->GetLocalizedSubtitle(*M).ToString() : TEXT(""));
		W->WriteValue(TEXT("localization_key"), M ? Asset->GetContextLocalizationKey(*M) : TEXT(""));
		W->WriteValue(TEXT("recorded_audio_filename"), M ? Asset->GetContextRecordedAudioFilename(*M) : TEXT(""));
		W->WriteValue(TEXT("duration_seconds"), Proxy ? Proxy->GetDuration() : 0.0f); W->WriteObjectEnd(); W->Close(); return Json;
	}
	FString Validate(UObject* Asset)
	{
		TArray<FString> Errors, Warnings; bool bReady = false;
		if (UDialogueVoice* Voice = Cast<UDialogueVoice>(Asset)) CheckVoice(Voice, Errors);
		else if (UDialogueWave* Wave = Cast<UDialogueWave>(Asset)) bReady = CheckMappings(Wave, Wave->ContextMappings, Errors, Warnings);
		else throw std::runtime_error("Asset is not Dialogue Voice or Dialogue Wave");
		FString Json; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Json); W->WriteObjectStart();
		W->WriteValue(TEXT("asset_path"), Asset->GetPathName()); W->WriteValue(TEXT("valid"), Errors.IsEmpty()); W->WriteValue(TEXT("ready_for_playback"), bReady);
		W->WriteValue(TEXT("ready_for_context_use"), Asset->IsA<UDialogueVoice>() && Errors.IsEmpty());
		W->WriteValue(TEXT("validation_scope"), TEXT("dialogue_metadata_context_references_and_localization_keys"));
		W->WriteArrayStart(TEXT("errors")); for (const FString& E : Errors) W->WriteValue(E); W->WriteArrayEnd();
		W->WriteArrayStart(TEXT("warnings")); for (const FString& E : Warnings) W->WriteValue(E); W->WriteArrayEnd();
		W->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty()); W->WriteObjectEnd(); W->Close(); return Json;
	}
}
