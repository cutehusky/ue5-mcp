#include "ModulationProfileUtils.h"
#include "ModulationRuntimeUtils.h"
#include "ModulationUtils.h"
#include "UE5_MCP/API/DTO/ModulationProfileReq.h"
#include "AudioModulationStatics.h"
#include "Editor.h"
#include "Engine/Engine.h"
#include "HAL/FileManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include <stdexcept>

namespace
{
	USoundControlBusMix* Mix(const FString& Path)
	{
		auto* A = Cast<USoundControlBusMix>(StaticLoadObject(USoundControlBusMix::StaticClass(), nullptr, *Path));
		if (!A || !A->IsAsset()) throw std::runtime_error("AssetPath must identify a saved Control Bus Mix asset"); return A;
	}
	FString NativePath(USoundControlBusMix* A, int32 Index)
	{
		if (Index < 0 || Index > 999) throw std::runtime_error("ProfileIndex must be in [0,999]");
		// UE 5.7 FProfileSerializer's native layout; keep this cache key spelling.
		const FString P = FPaths::GeneratedConfigDir() + TEXT("AudioModulation") + FPaths::GetPath(A->GetPathName()) / A->GetName() + (Index ? FString::FromInt(Index) : FString()) + TEXT(".ini");
		const FString Full = FPaths::ConvertRelativePathToFull(P);
		if (!FPaths::IsUnderDirectory(Full, FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()))) throw std::runtime_error("Native profile path must remain inside the project's Saved directory"); return P;
	}
	void Require(UObject* A) { const auto E = ModulationUtils::ValidationErrors(A); if (!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(E, TEXT("; ")))); }
	TArray<FSoundControlBusMixStage> Read(const FString& Path, FConfigFile& File)
	{
		const int64 Size = IFileManager::Get().FileSize(*Path);
		if (Size < 0 || Size > 1024 * 1024) throw std::runtime_error("Profile must exist and be at most 1 MiB"); File.Read(Path);
		if (File.Num() > 128) throw std::runtime_error("Profile stages are limited to 128");
		TArray<FSoundControlBusMixStage> Stages;
		for (const auto& Section : File)
		{
			auto* Bus = Cast<USoundControlBus>(StaticLoadObject(USoundControlBus::StaticClass(), nullptr, *Section.Key));
			if (!Bus) throw std::runtime_error("Profile section must identify a Control Bus asset"); Require(Bus);
			if (Section.Value.Num() != 3) throw std::runtime_error("Profile sections require AttackTime, ReleaseTime and TargetValue only");
			float Attack, Release, Target;
			auto Number = [&Section](const TCHAR* Key, float& V)
			{
				const FConfigValue* Raw = Section.Value.Find(FName(Key));
				if (!Raw || !LexTryParseString(V, *Raw->GetValue()) || !FMath::IsFinite(V)) throw std::runtime_error("Profile values must be finite numeric values");
			};
			Number(TEXT("AttackTime"), Attack); Number(TEXT("ReleaseTime"), Release); Number(TEXT("TargetValue"), Target);
			if (Attack < 0 || Attack > 86400 || Release < 0 || Release > 86400 || Target < 0 || Target > 1) throw std::runtime_error("Profile stage target/timing is outside supported ranges");
			FSoundControlBusMixStage Stage(Bus, Target); Stage.Value.AttackTime = Attack; Stage.Value.ReleaseTime = Release;
			Stage.Value.TargetUnitValue = Bus->Parameter ? Bus->Parameter->ConvertNormalizedToUnit(Target) : Target; Stages.Add(Stage);
		}
		return Stages;
	}
	bool Same(const TArray<FSoundControlBusMixStage>& A, const TArray<FSoundControlBusMixStage>& B)
	{
		if (A.Num() != B.Num()) return false;
		for (const auto& X : A) { const auto* Y = B.FindByPredicate([&X](const auto& S) { return S.Bus == X.Bus; }); if (!Y || X.Value.TargetValue != Y->Value.TargetValue || X.Value.AttackTime != Y->Value.AttackTime || X.Value.ReleaseTime != Y->Value.ReleaseTime) return false; } return true;
	}
}

FString ModulationProfileUtils::Inspect(const FString& AssetPath, int32 Index)
{
	auto* A = Mix(AssetPath); const FString P = NativePath(A, Index); const bool Exists = IFileManager::Get().FileExists(*P);
	FConfigFile File; TArray<FSoundControlBusMixStage> Stages; if (Exists) Stages = Read(P, File);
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), A->GetPathName()); J->WriteValue(TEXT("profile_index"), Index);
	J->WriteValue(TEXT("profile_path"), FPaths::ConvertRelativePathToFull(P)); J->WriteValue(TEXT("exists"), Exists);
	J->WriteValue(TEXT("scope"), TEXT("native profile stage targets/attack/release only; mix duration/retrigger settings are not serialized"));
	if (Exists) J->WriteValue(TEXT("modified_at"), IFileManager::Get().GetTimeStamp(*P).ToIso8601());
	J->WriteArrayStart(TEXT("stages")); for (const auto& S : Stages) { J->WriteObjectStart(); J->WriteValue(TEXT("bus_path"), S.Bus->GetPathName()); J->WriteValue(TEXT("target_normalized"), S.Value.TargetValue); J->WriteValue(TEXT("attack_seconds"), S.Value.AttackTime); J->WriteValue(TEXT("release_seconds"), S.Value.ReleaseTime); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationProfileUtils::Control(const FModulationProfileReq& R)
{
	auto* A = Mix(R.AssetPath); const FString P = NativePath(A, R.ProfileIndex); const bool Exists = IFileManager::Get().FileExists(*P);
	if (R.Operation != TEXT("save") && R.Operation != TEXT("load")) throw std::runtime_error("Operation must be save or load");
	if (R.PIEInstance < -1) throw std::runtime_error("PIEInstance must be -1 or nonnegative");
	bool HasPIE = false; if (GEngine) for (const auto& Context : GEngine->GetWorldContexts()) if (Context.WorldType == EWorldType::PIE && Context.World()) HasPIE = true;
	UObject* WorldContext = A;
	if (HasPIE || R.PIEInstance >= 0) WorldContext = ModulationRuntimeUtils::ResolveAudioWorld(R.PIEInstance);
	else if (!UAudioModulationStatics::GetModulation(nullptr)) throw std::runtime_error("Audio Modulation is unavailable on the editor's main audio device");
	bool Changed = false;
	if (R.Operation == TEXT("save"))
	{
		Require(A); if (Exists && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Overwriting a native profile requires bConfirm=true");
		if (!R.bDryRun) UAudioModulationStatics::SaveMixToProfile(WorldContext, A, R.ProfileIndex);
	}
	else
	{
		FConfigFile File; const auto Proposed = Read(P, File); Changed = !Same(A->MixStages, Proposed);
		if (Changed && R.bSave && HasPIE && !R.bDryRun) throw std::runtime_error("Stop PIE before saving an imported mix asset; load with bSave=false to keep the change dirty");
		if (Changed && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Loading a profile replaces asset mix stages and requires bConfirm=true");
		if (!R.bDryRun)
		{
			// Prime native cache with the validated on-disk snapshot, avoiding stale ini data.
			GConfig->Add(P, MoveTemp(File));
			TUniquePtr<FScopedTransaction> Transaction;
			if (Changed) { Transaction = MakeUnique<FScopedTransaction>(NSLOCTEXT("UE5MCP", "LoadModulationProfile", "Load Control Bus Mix profile")); A->Modify(); }
			const auto Previous = A->MixStages; const bool WasDirty = A->GetOutermost()->IsDirty();
			// UE's loader updates matching object stages. Its returned stage list is the
			// complete profile, so assign it to support adding/removing stage membership.
			const auto Loaded = UAudioModulationStatics::LoadMixFromProfile(WorldContext, A, false, R.ProfileIndex);
			if (!Same(Loaded, Proposed)) { A->MixStages = Previous; A->GetOutermost()->SetDirtyFlag(WasDirty); if (Transaction) Transaction->Cancel(); throw std::runtime_error("Native profile loader did not return the validated profile"); }
			if (Changed)
			{
				A->MixStages = Proposed; FPropertyChangedEvent Event(FindFProperty<FProperty>(A->GetClass(), TEXT("MixStages")), EPropertyChangeType::ValueSet); A->PostEditChangeProperty(Event); A->MarkPackageDirty();
				if (R.bSave) { auto* S = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr; if (!S || !S->SaveAsset(A->GetPathName(), true)) throw std::runtime_error("Profile loaded but asset saving failed"); }
			}
			else { A->MixStages = Previous; A->GetOutermost()->SetDirtyFlag(WasDirty); }
		}
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), A->GetPathName()); J->WriteValue(TEXT("profile_path"), FPaths::ConvertRelativePathToFull(P));
	J->WriteValue(TEXT("operation"), R.Operation); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("would_change_asset"), Changed); J->WriteValue(TEXT("changed_asset"), Changed && !R.bDryRun);
	J->WriteValue(TEXT("audio_context"), HasPIE ? TEXT("PIE") : TEXT("editor_main_device"));
	J->WriteValue(TEXT("saved_asset"), R.bSave && Changed && !R.bDryRun); J->WriteValue(TEXT("profile_save_submitted"), R.Operation == TEXT("save") && !R.bDryRun);
	J->WriteValue(TEXT("execution"), TEXT("profile save is asynchronous; inspect on-disk profile to verify completion")); J->WriteObjectEnd(); J->Close(); return Json;
}
