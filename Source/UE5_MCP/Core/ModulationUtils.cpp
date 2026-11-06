#include "ModulationUtils.h"
#include "ModulationAuthoringUtils.h"
#include "SoundModulationPatch.h"
#include "Sound/AudioBus.h"
#include "UE5_MCP/API/DTO/ModulationReq.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "AudioModulationSettings.h"
#include "Editor.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "SoundControlBus.h"
#include "SoundControlBusMix.h"
#include "SoundModulationParameter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectHash.h"
#include <stdexcept>

namespace
{
	FString Path(const UObject* A) { return A ? A->GetPathName() : FString(); }
	template<typename T> T* Reference(const FString& P)
	{
		T* A = P.IsEmpty() ? nullptr : Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, *P));
		if (!A) throw std::runtime_error("Reference does not identify an asset of the required modulation class");
		return A;
	}
	void Save(UObject* A, bool Requested)
	{
		if (!Requested) return;
		auto* S = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!S || !S->SaveAsset(A->GetPathName(), true)) throw std::runtime_error("Modulation asset changed but saving failed");
	}
	FString Result(UObject* A, const FString& Operation, bool Changed, bool Dry, bool Saved)
	{
		FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
		J->WriteValue(TEXT("asset_path"), Path(A)); J->WriteValue(TEXT("operation"), Operation);
		J->WriteValue(TEXT("would_change"), Changed); J->WriteValue(TEXT("changed"), Changed && !Dry);
		J->WriteValue(TEXT("dry_run"), Dry); J->WriteValue(TEXT("saved"), Saved && Changed && !Dry);
		J->WriteValue(TEXT("dirty"), A->GetOutermost()->IsDirty()); J->WriteObjectEnd(); J->Close(); return Json;
	}
	const TCHAR* ParameterFields[] = {TEXT("UnitMin"), TEXT("UnitMax"), TEXT("UnitRange"), TEXT("MinVolume")};
	FFloatProperty* Field(USoundModulationParameter* A, const FString& Key)
	{
		for (const TCHAR* Allowed : ParameterFields) if (Key == Allowed) return FindFProperty<FFloatProperty>(A->GetClass(), *Key);
		return nullptr;
	}
	TArray<FString> Errors(UObject* A)
	{
		TArray<FString> E;
		if (auto* P = Cast<USoundModulationParameter>(A))
		{
			if (!FMath::IsFinite(P->Settings.ValueNormalized) || P->Settings.ValueNormalized < 0.f || P->Settings.ValueNormalized > 1.f) E.Add(TEXT("DefaultNormalized must be in [0,1]"));
			const float Min = P->GetUnitMin(), Max = P->GetUnitMax();
			if (!FMath::IsFinite(Min) || !FMath::IsFinite(Max) || Min >= Max) E.Add(TEXT("Unit range must be finite and increasing"));
			if (P->IsA<USoundModulationParameterFrequencyBase>() && Min <= 0.f) E.Add(TEXT("Frequency minimum must be positive"));
			if (P->IsA<USoundModulationParameterAdditive>() && Min < 0.f) E.Add(TEXT("Additive minimum cannot be negative"));
			if (P->IsA<USoundModulationParameterVolume>() && Max != 0.f) E.Add(TEXT("Volume maximum must be zero dB"));
			if (E.IsEmpty() && !FMath::IsFinite(P->GetUnitDefault())) E.Add(TEXT("Native default conversion is nonfinite"));
		}
		else if (auto* B = Cast<USoundControlBus>(A))
		{
			if (B->bOverrideAddress && (B->Address.TrimStartAndEnd().IsEmpty() || B->Address.Len() > 256)) E.Add(TEXT("Override address must contain 1-256 characters"));
			if (B->Parameter) for (const FString& Error : Errors(B->Parameter)) E.Add(TEXT("Parameter: ") + Error);
			TSet<const UObject*> Seen;
			for (const auto& G : B->Generators) { if (!G || Seen.Contains(G)) E.Add(TEXT("Generators contain missing or duplicate references")); if (G && ModulationAuthoringUtils::Supports(G)) E.Append(ModulationAuthoringUtils::Errors(G)); Seen.Add(G); }
		}
		else if (auto* M = Cast<USoundControlBusMix>(A))
		{
			if (!FMath::IsFinite(M->Duration) || M->Duration < -1.0 || M->Duration > 86400.0) E.Add(TEXT("Duration must be -1 (manual) or 0-86400 seconds"));
			TSet<const UObject*> Seen;
			for (const auto& S : M->MixStages)
			{
				if (!S.Bus || Seen.Contains(S.Bus)) E.Add(TEXT("Mix stages contain missing or duplicate buses")); Seen.Add(S.Bus);
				if (S.Bus) for (const FString& Error : Errors(S.Bus)) E.Add(TEXT("Stage bus: ") + Error);
				if (!FMath::IsFinite(S.Value.TargetValue) || S.Value.TargetValue < 0.f || S.Value.TargetValue > 1.f) E.Add(TEXT("Stage target must be normalized in [0,1]"));
				if (!FMath::IsFinite(S.Value.AttackTime) || S.Value.AttackTime < 0.f || S.Value.AttackTime > 86400.f || !FMath::IsFinite(S.Value.ReleaseTime) || S.Value.ReleaseTime < 0.f || S.Value.ReleaseTime > 86400.f) E.Add(TEXT("Stage attack/release must be 0-86400 seconds"));
			}
		}
		else if (ModulationAuthoringUtils::Supports(A)) E.Append(ModulationAuthoringUtils::Errors(A));
		else E.Add(TEXT("Unsupported modulation asset"));
		return E;
	}
	void Require(UObject* A) { const auto E = Errors(A); if (!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(E, TEXT("; ")))); }
	UClass* ParameterClass(const FString& Type)
	{
		if (Type == TEXT("scalar")) return USoundModulationParameter::StaticClass();
		if (Type == TEXT("scaled")) return USoundModulationParameterScaled::StaticClass();
		if (Type == TEXT("frequency")) return USoundModulationParameterFrequency::StaticClass();
		if (Type == TEXT("filter_frequency")) return USoundModulationParameterFilterFrequency::StaticClass();
		if (Type == TEXT("volume")) return USoundModulationParameterVolume::StaticClass();
		if (Type == TEXT("bipolar")) return USoundModulationParameterBipolar::StaticClass();
		if (Type == TEXT("additive")) return USoundModulationParameterAdditive::StaticClass();
		throw std::runtime_error("ParameterType must be scalar, scaled, frequency, filter_frequency, volume, bipolar or additive");
	}
}

bool ModulationUtils::Supports(const UObject* A)
{
	return A && (A->IsA<USoundModulationParameter>() || A->IsA<USoundControlBus>() || A->IsA<USoundControlBusMix>() || ModulationAuthoringUtils::Supports(A));
}

FString ModulationUtils::Create(const FModulationCreateReq& R)
{
	if (!R.AssetPath.StartsWith(TEXT("/Game/")) || R.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(R.AssetPath)) throw std::runtime_error("AssetPath must be a valid /Game package path without object suffix");
	UClass* Class = nullptr; USoundModulationParameter* Parameter = nullptr;
	if (R.AssetType == TEXT("parameter")) Class = ParameterClass(R.ParameterType);
	else if (R.AssetType == TEXT("bus")) { Class = USoundControlBus::StaticClass(); Parameter = R.ParameterPath.IsEmpty() ? GetDefault<UAudioModulationSettings>()->GetModulationParameter(TEXT("Volume")).Get() : Reference<USoundModulationParameter>(R.ParameterPath); if (Parameter) Require(Parameter); }
	else if (R.AssetType == TEXT("mix")) Class = USoundControlBusMix::StaticClass();
	else if (R.AssetType == TEXT("patch")) { Class = USoundModulationPatch::StaticClass(); Parameter = R.ParameterPath.IsEmpty() ? nullptr : Reference<USoundModulationParameter>(R.ParameterPath); if (Parameter) Require(Parameter); }
	else if (R.AssetType == TEXT("generator")) Class = ModulationAuthoringUtils::GeneratorClass(R.GeneratorType);
	else if (R.AssetType == TEXT("audio_bus")) Class = UAudioBus::StaticClass();
	else throw std::runtime_error("AssetType must be parameter, bus, mix, patch, generator or audio_bus");
	if (R.AssetType != TEXT("bus") && R.AssetType != TEXT("patch") && !R.ParameterPath.IsEmpty()) throw std::runtime_error("ParameterPath is supported only when creating a bus or patch");
	FString Package, Name; FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get().CreateUniqueAssetName(R.AssetPath, TEXT(""), Package, Name);
	UObject* A = nullptr;
	if (!R.bDryRun)
	{
		A = NewObject<UObject>(CreatePackage(*Package), Class, FName(*Name), RF_Public | RF_Standalone | RF_Transactional);
		if (!A) throw std::runtime_error("Could not create modulation asset");
		if (auto* B = Cast<USoundControlBus>(A)) B->Parameter = Parameter;
		if (auto* Patch = Cast<USoundModulationPatch>(A)) Patch->PatchSettings.OutputParameter = Parameter;
		if (auto* P = Cast<USoundModulationParameter>(A)) P->RefreshUnitValue();
		FAssetRegistryModule::AssetCreated(A); A->MarkPackageDirty(); Save(A, R.bSave);
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	J->WriteValue(TEXT("asset_path"), Package + TEXT(".") + Name); J->WriteValue(TEXT("class_path"), Class->GetPathName());
	J->WriteValue(TEXT("created"), !R.bDryRun); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("saved"), !R.bDryRun && R.bSave);
	J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationUtils::Inspect(UObject* A)
{
	if (ModulationAuthoringUtils::Supports(A)) return ModulationAuthoringUtils::Inspect(A);
	if (!Supports(A)) throw std::runtime_error("Unsupported modulation asset");
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), Path(A)); J->WriteValue(TEXT("class_path"), A->GetClass()->GetPathName()); J->WriteValue(TEXT("dirty"), A->GetOutermost()->IsDirty());
	if (auto* P = Cast<USoundModulationParameter>(A))
	{
		J->WriteValue(TEXT("default_normalized"), P->Settings.ValueNormalized); J->WriteValue(TEXT("unit_display_name"), P->Settings.UnitDisplayName.ToString());
		const bool Valid = Errors(P).IsEmpty(); J->WriteValue(TEXT("conversion_valid"), Valid);
		if (Valid) { J->WriteValue(TEXT("default_unit"), P->GetUnitDefault()); J->WriteValue(TEXT("unit_min"), P->GetUnitMin()); J->WriteValue(TEXT("unit_max"), P->GetUnitMax()); J->WriteValue(TEXT("requires_conversion"), P->RequiresUnitConversion()); }
		J->WriteObjectStart(TEXT("numeric")); for (const TCHAR* Key : ParameterFields) if (auto* F = Field(P, Key)) J->WriteValue(Key, F->GetPropertyValue_InContainer(P)); J->WriteObjectEnd();
	}
	else if (auto* B = Cast<USoundControlBus>(A))
	{
		J->WriteValue(TEXT("parameter_path"), Path(B->Parameter)); J->WriteValue(TEXT("bypass"), B->bBypass); J->WriteValue(TEXT("override_address"), B->bOverrideAddress); J->WriteValue(TEXT("address"), B->Address);
		J->WriteValue(TEXT("default_normalized"), B->GetDefaultNormalizedValue()); J->WriteArrayStart(TEXT("generator_paths")); for (const auto& G : B->Generators) J->WriteValue(Path(G)); J->WriteArrayEnd();
	}
	else if (auto* M = Cast<USoundControlBusMix>(A))
	{
		J->WriteValue(TEXT("duration_seconds"), M->Duration); J->WriteValue(TEXT("retrigger_on_activation"), M->bRetriggerOnActivation); J->WriteArrayStart(TEXT("stages"));
		for (const auto& S : M->MixStages) { J->WriteObjectStart(); J->WriteValue(TEXT("bus_path"), Path(S.Bus)); J->WriteValue(TEXT("target_normalized"), S.Value.TargetValue); J->WriteValue(TEXT("attack_seconds"), S.Value.AttackTime); J->WriteValue(TEXT("release_seconds"), S.Value.ReleaseTime); if (S.Bus && Errors(S.Bus).IsEmpty()) J->WriteValue(TEXT("target_unit"), S.Bus->Parameter ? S.Bus->Parameter->ConvertNormalizedToUnit(S.Value.TargetValue) : S.Value.TargetValue); J->WriteObjectEnd(); } J->WriteArrayEnd();
	}
	J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationUtils::Edit(UObject* A, const FModulationSettingsReq& R)
{
	if (ModulationAuthoringUtils::Supports(A)) return ModulationAuthoringUtils::Edit(A, R);
	if (!Supports(A)) throw std::runtime_error("Unsupported modulation asset");
	// A transient preview validates complete proposed state without touching references.
	UObject* Preview = TransientCopy(A);
	if (auto* P = Cast<USoundModulationParameter>(Preview))
	{
		if (R.bSetParameter || R.bSetBypass || R.bSetAddress || R.bSetGenerators || R.bSetRetriggerOnActivation) throw std::runtime_error("Bus/mix fields cannot be applied to a parameter");
		for (const auto& Pair : R.Numeric)
		{
			if (!FMath::IsFinite(Pair.Value)) throw std::runtime_error("Numeric values must be finite");
			if (Pair.Key == TEXT("DefaultNormalized")) P->Settings.ValueNormalized = Pair.Value;
			else if (auto* F = Field(P, Pair.Key)) F->SetPropertyValue_InContainer(P, Pair.Value);
			else throw std::runtime_error("Unsupported numeric field for this parameter class");
		}
		if (R.bSetUnitDisplayName) { if (R.UnitDisplayName.Len() > 128) throw std::runtime_error("UnitDisplayName is limited to 128 characters"); P->Settings.UnitDisplayName = FText::FromString(R.UnitDisplayName); }
		Require(P); P->RefreshUnitValue();
	}
	else if (auto* B = Cast<USoundControlBus>(Preview))
	{
		if (!R.Numeric.IsEmpty() || R.bSetUnitDisplayName || R.bSetRetriggerOnActivation) throw std::runtime_error("Parameter/mix fields cannot be applied to a bus");
		// PostDuplicate adjusts the native default address to the preview's name.
		B->Address = CastChecked<USoundControlBus>(A)->Address;
		if (R.bSetParameter) B->Parameter = R.ParameterPath.IsEmpty() ? nullptr : Reference<USoundModulationParameter>(R.ParameterPath);
		if (R.bSetBypass) B->bBypass = R.bBypass;
		if (R.bSetAddress) { B->bOverrideAddress = R.bOverrideAddress; B->Address = R.bOverrideAddress ? R.Address : A->GetName(); }
		if (R.bSetGenerators)
		{
			if (R.GeneratorPaths.Num() > 64) throw std::runtime_error("Generators are limited to 64 references");
			TArray<TObjectPtr<USoundModulationGenerator>> Proposed;
			for (const FString& GeneratorPath : R.GeneratorPaths) Proposed.Add(Reference<USoundModulationGenerator>(GeneratorPath));
			for (const auto& G : B->Generators) if (!Proposed.Contains(G) && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Removing generators requires bConfirm=true");
			B->Generators = Proposed;
		}
	}
	else if (auto* M = Cast<USoundControlBusMix>(Preview))
	{
		if (R.bSetParameter || R.bSetBypass || R.bSetAddress || R.bSetGenerators || R.bSetUnitDisplayName) throw std::runtime_error("Parameter/bus fields cannot be applied to a mix");
		for (const auto& Pair : R.Numeric) { if (Pair.Key != TEXT("DurationSeconds")) throw std::runtime_error("Mix numeric fields support DurationSeconds only"); M->Duration = Pair.Value; }
		if (R.bSetRetriggerOnActivation) M->bRetriggerOnActivation = R.bRetriggerOnActivation;
	}
	Require(Preview);
	bool Changed = false;
	TArray<FProperty*> Properties;
	auto Identical = [A, Preview](FProperty* F)
	{
		if (auto* P = Cast<USoundModulationParameter>(A)) if (F->GetFName() == TEXT("Settings"))
		{
			const auto* Q = CastChecked<USoundModulationParameter>(Preview);
			return P->Settings.ValueNormalized == Q->Settings.ValueNormalized && P->Settings.UnitDisplayName.EqualTo(Q->Settings.UnitDisplayName);
		}
		return F->Identical_InContainer(A, Preview);
	};
	// Compare only fields owned by this operation. Duplicating MixStages resets
	// transient unit-display caches, which are not authored settings changes.
	TArray<FName> Names;
	if (A->IsA<USoundModulationParameter>()) { Names.Add(TEXT("Settings")); for (const TCHAR* Key : ParameterFields) Names.Add(Key); }
	else if (A->IsA<USoundControlBus>()) Names = {TEXT("Parameter"), TEXT("bBypass"), TEXT("bOverrideAddress"), TEXT("Address"), TEXT("Generators")};
	else Names = {TEXT("Duration"), TEXT("bRetriggerOnActivation")};
	for (const FName& Name : Names) if (FProperty* F = FindFProperty<FProperty>(A->GetClass(), Name)) { Properties.Add(F); if (!Identical(F)) Changed = true; }
	if (Changed && !R.bDryRun)
	{
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP", "ModulationSettings", "Edit modulation settings")); A->Modify();
		TArray<FProperty*> ChangedProperties;
		for (FProperty* F : Properties) if (!Identical(F)) { F->CopyCompleteValue_InContainer(A, Preview); ChangedProperties.Add(F); }
		for (FProperty* F : ChangedProperties) { FPropertyChangedEvent Event(F); A->PostEditChangeProperty(Event); }
		if (auto* P = Cast<USoundModulationParameter>(A)) P->RefreshUnitValue();
		A->MarkPackageDirty(); Save(A, R.bSave);
	}
	return Result(A, TEXT("settings"), Changed, R.bDryRun, R.bSave);
}

FString ModulationUtils::Stage(UObject* A, const FModulationStageReq& R)
{
	auto* M = Cast<USoundControlBusMix>(A); if (!M) throw std::runtime_error("Asset must be a Control Bus Mix");
	const FString Op = R.Operation.ToLower(); if (Op != TEXT("upsert") && Op != TEXT("remove") && Op != TEXT("clear")) throw std::runtime_error("Operation must be upsert, remove or clear");
	if (Op != TEXT("upsert") && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Removing mix stages requires bConfirm=true");
	USoundControlBus* B = Op == TEXT("clear") ? nullptr : Reference<USoundControlBus>(R.BusPath);
	auto Proposed = M->MixStages; int32 Index = Proposed.IndexOfByPredicate([B](const FSoundControlBusMixStage& S) { return S.Bus == B; });
	if (Op == TEXT("clear")) Proposed.Reset();
	else if (Op == TEXT("remove")) { if (Index == INDEX_NONE) throw std::runtime_error("Bus has no mix stage"); Proposed.RemoveAt(Index); }
	else
	{
		Require(B);
		if (!FMath::IsFinite(R.TargetNormalized) || R.TargetNormalized < 0.f || R.TargetNormalized > 1.f || !FMath::IsFinite(R.AttackSeconds) || R.AttackSeconds < 0.f || R.AttackSeconds > 86400.f || !FMath::IsFinite(R.ReleaseSeconds) || R.ReleaseSeconds < 0.f || R.ReleaseSeconds > 86400.f) throw std::runtime_error("Stage target must be in [0,1] and attack/release in [0,86400]");
		if (Index == INDEX_NONE) { if (Proposed.Num() >= 128) throw std::runtime_error("Mix stages are limited to 128"); Index = Proposed.Add(FSoundControlBusMixStage(B, R.TargetNormalized)); }
		auto& S = Proposed[Index]; S.Value.TargetValue = R.TargetNormalized; S.Value.AttackTime = R.AttackSeconds; S.Value.ReleaseTime = R.ReleaseSeconds;
		S.Value.TargetUnitValue = B->Parameter ? B->Parameter->ConvertNormalizedToUnit(R.TargetNormalized) : R.TargetNormalized;
	}
	auto* Preview = CastChecked<USoundControlBusMix>(TransientCopy(M)); Preview->MixStages = Proposed; Require(Preview);
	bool Changed = Proposed.Num() != M->MixStages.Num();
	if (!Changed) for (int32 I = 0; I < Proposed.Num(); ++I) { const auto& X = Proposed[I]; const auto& Y = M->MixStages[I]; if (X.Bus != Y.Bus || X.Value.TargetValue != Y.Value.TargetValue || X.Value.AttackTime != Y.Value.AttackTime || X.Value.ReleaseTime != Y.Value.ReleaseTime) Changed = true; }
	if (Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5MCP", "ModulationStages", "Edit Control Bus Mix stages")); M->Modify(); M->MixStages = Proposed; FPropertyChangedEvent Event(FindFProperty<FProperty>(M->GetClass(), TEXT("MixStages"))); M->PostEditChangeProperty(Event); M->MarkPackageDirty(); Save(M, R.bSave); }
	return Result(M, Op, Changed, R.bDryRun, R.bSave);
}

FString ModulationUtils::Convert(UObject* A, const FModulationConvertReq& R)
{
	auto* P = Cast<USoundModulationParameter>(A); if (!P) throw std::runtime_error("Asset must be a modulation parameter"); Require(P);
	const bool ToUnit = R.Direction == TEXT("normalized_to_unit"); if (!ToUnit && R.Direction != TEXT("unit_to_normalized")) throw std::runtime_error("Direction must be normalized_to_unit or unit_to_normalized");
	if (R.Values.IsEmpty() || R.Values.Num() > 256) throw std::runtime_error("Values must contain 1-256 numbers");
	TArray<float> Converted;
	for (float V : R.Values) { if (!FMath::IsFinite(V) || (ToUnit && (V < 0.f || V > 1.f)) || (!ToUnit && (V < P->GetUnitMin() || V > P->GetUnitMax()))) throw std::runtime_error("Conversion inputs must be finite and within the parameter domain"); const float C = ToUnit ? P->ConvertNormalizedToUnit(V) : P->ConvertUnitToNormalized(V); if (!FMath::IsFinite(C)) throw std::runtime_error("Native conversion returned a nonfinite value"); Converted.Add(C); }
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), Path(P)); J->WriteValue(TEXT("direction"), R.Direction); J->WriteArrayStart(TEXT("values")); for (float V : Converted) J->WriteValue(V); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationUtils::Validate(UObject* A)
{
	const auto E = Errors(A); FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), Path(A)); J->WriteValue(TEXT("valid"), E.IsEmpty()); J->WriteArrayStart(TEXT("errors")); for (const FString& Error : E) J->WriteValue(Error); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}

TArray<FString> ModulationUtils::ValidationErrors(UObject* A) { return Errors(A); }

UObject* ModulationUtils::TransientCopy(UObject* A)
{
	UObject* Preview = DuplicateObject(A, GetTransientPackage(), MakeUniqueObjectName(GetTransientPackage(), A->GetClass(), TEXT("MCP_ModulationPreview")));
	auto Flags = [](UObject* Object) { Object->ClearFlags(RF_Public | RF_Standalone); Object->SetFlags(RF_Transient); };
	Flags(Preview); ForEachObjectWithOuter(Preview, Flags); return Preview;
}
