#include "ModulationRuntimeUtils.h"
#include "ModulationUtils.h"
#include "UE5_MCP/API/DTO/ModulationRuntimeReq.h"
#include "AudioModulationDestination.h"
#include "AudioModulationStatics.h"
#include "Audio/AudioAddressPattern.h"
#include "SoundModulationParameter.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Serialization/JsonWriter.h"
#include "UObject/StrongObjectPtr.h"
#include <stdexcept>

namespace
{
	struct FState
	{
		TMap<FString, TStrongObjectPtr<UAudioModulationDestination>> Destinations;
		TMap<FString, TStrongObjectPtr<USoundControlBusMix>> Mixes;
		TMap<FString, TStrongObjectPtr<USoundControlBus>> Globals;
	};
	TMap<TWeakObjectPtr<UWorld>, FState> States;
	FDelegateHandle CleanupHandle;
	FString Path(const UObject* A) { return A ? A->GetPathName() : FString(); }
	UWorld* World(int32 Instance)
	{
		if (Instance < -1) throw std::runtime_error("PIEInstance must be -1 or nonnegative");
		UWorld* Result = nullptr;
		if (GEngine) for (const FWorldContext& C : GEngine->GetWorldContexts())
		{
			if (C.WorldType != EWorldType::PIE || !C.World() || (Instance >= 0 && C.PIEInstance != Instance)) continue;
			if (Result) throw std::runtime_error("Multiple PIE worlds; specify PIEInstance"); Result = C.World();
		}
		if (!Result) throw std::runtime_error("No matching PIE world; start a play session first"); return Result;
	}
	void Clear(UWorld* W, FState& S)
	{
		for (auto& Pair : S.Destinations) if (Pair.Value.IsValid()) Pair.Value->ClearModulator();
		if (W && UAudioModulationStatics::GetModulation(W))
		{
			for (auto& Pair : S.Mixes) if (Pair.Value.IsValid()) UAudioModulationStatics::DeactivateBusMix(W, Pair.Value.Get());
			for (auto& Pair : S.Globals) if (Pair.Value.IsValid()) UAudioModulationStatics::ClearGlobalBusMixValue(W, Pair.Value.Get(), 0.f);
		}
		S.Destinations.Reset(); S.Mixes.Reset(); S.Globals.Reset();
	}
	void OnCleanup(UWorld* W, bool, bool)
	{
		if (FState* S = States.Find(W)) { Clear(W, *S); States.Remove(W); }
	}
	FState& State(UWorld* W)
	{
		if (!CleanupHandle.IsValid()) CleanupHandle = FWorldDelegates::OnWorldCleanup.AddStatic(&OnCleanup);
		return States.FindOrAdd(W);
	}
	UObject* Asset(const FString& P)
	{
		UObject* A = P.IsEmpty() ? nullptr : StaticLoadObject(UObject::StaticClass(), nullptr, *P);
		if (!A) throw std::runtime_error("Asset not found");
		const auto Errors = ModulationUtils::ValidationErrors(A);
		if (!Errors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(Errors, TEXT("; ")))); return A;
	}
	void AddressPattern(const FString& Pattern)
	{
		if (Pattern.Len() > 256) throw std::runtime_error("AddressFilter is limited to 256 characters");
		for (TCHAR C : Pattern) if (FChar::IsControl(C)) throw std::runtime_error("AddressFilter cannot contain control characters");
		TArray<FString> Parts; Pattern.ParseIntoArray(Parts, TEXT("/"), false);
		for (const auto& Part : Parts)
		{
			if (!FAudioAddressPattern::IsValidPatternPart(Part)) throw std::runtime_error("Invalid native address pattern part");
			int32 Open = -1; TCHAR End = 0;
			for (int32 I = 0; I < Part.Len(); ++I)
			{
				const TCHAR C = Part[I];
				if (C == '[' || C == '{') { if (Open >= 0) throw std::runtime_error("Nested address groups are unsupported by the native matcher"); Open = I; End = C == '[' ? ']' : '}'; }
				else if (C == ']' || C == '}') { if (Open < 0 || C != End || I - Open <= 1) throw std::runtime_error("Address pattern groups must be paired and nonempty"); Open = -1; }
			}
			if (Open >= 0) throw std::runtime_error("Unterminated address pattern group");
		}
	}
	void Id(const FString& Value)
	{
		if (Value.IsEmpty() || Value.Len() > 64) throw std::runtime_error("DestinationId must contain 1-64 characters");
		for (TCHAR C : Value) if (!FChar::IsAlnum(C) && C != TEXT('_') && C != TEXT('-')) throw std::runtime_error("DestinationId allows letters, numbers, underscores and hyphens");
	}
}

void ModulationRuntimeUtils::Shutdown()
{
	if (CleanupHandle.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(CleanupHandle); CleanupHandle.Reset(); }
	for (auto& Pair : States) Clear(Pair.Key.Get(), Pair.Value); States.Reset();
}

UWorld* ModulationRuntimeUtils::ResolveAudioWorld(int32 PIEInstance)
{
	UWorld* W = World(PIEInstance);
	if (UAudioModulationStatics::GetAudioWorld(W) != W || !UAudioModulationStatics::GetModulation(W)) throw std::runtime_error("Audio Modulation is unavailable on this PIE audio device");
	return W;
}

FString ModulationRuntimeUtils::Inspect(const FString& AssetPath, int32 PIEInstance)
{
	UWorld* W = World(PIEInstance); const bool Available = UAudioModulationStatics::GetModulation(W) != nullptr;
	UObject* A = AssetPath.IsEmpty() ? nullptr : Asset(AssetPath);
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	const auto Device = W->GetAudioDevice();
	J->WriteValue(TEXT("world_path"), Path(W)); J->WriteValue(TEXT("audio_device_id"), Device.IsValid() ? static_cast<int64>(Device.GetDeviceID()) : -1);
	J->WriteValue(TEXT("modulation_available"), Available); J->WriteValue(TEXT("runtime_only"), true);
	J->WriteValue(TEXT("scope"), TEXT("selected_PIE_audio_device; destinations list contains only adapter-created handles"));
	J->WriteValue(TEXT("state_sampling"), TEXT("last_modulation_processing_tick; inactive modulators return native fallback value 1"));
	if (A)
	{
		J->WriteValue(TEXT("asset_path"), Path(A));
		if (Available) { if (auto* M = Cast<USoundControlBusMix>(A)) J->WriteValue(TEXT("mix_active"), UAudioModulationStatics::IsControlBusMixActive(W, M)); else if (auto* B = Cast<USoundModulatorBase>(A)) J->WriteValue(TEXT("value_normalized"), UAudioModulationStatics::GetModulatorValue(W, B)); else throw std::runtime_error("Runtime inspection supports mixes or modulators"); }
	}
	J->WriteArrayStart(TEXT("destinations"));
	if (FState* S = States.Find(W))
	{
		TArray<FString> Keys; S->Destinations.GetKeys(Keys); Keys.Sort();
		for (const FString& Key : Keys) { const auto& D = S->Destinations[Key]; J->WriteObjectStart(); J->WriteValue(TEXT("destination_id"), Key); J->WriteValue(TEXT("modulator_path"), Path(D->GetModulator())); J->WriteValue(TEXT("value_normalized"), D->GetValue()); J->WriteObjectEnd(); }
	}
	J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationRuntimeUtils::Control(const FModulationRuntimeReq& R)
{
	UWorld* W = ResolveAudioWorld(R.PIEInstance);
	const FString Op = R.Operation.ToLower();
	const bool Filter = Op == TEXT("update_mix_by_filter");
	const bool BatchMix = Op == TEXT("activate_mixes") || Op == TEXT("deactivate_mixes") || Op == TEXT("update_mixes_from_assets");
	const bool BatchModulators = Op == TEXT("update_modulators");
	const bool BatchGlobal = Op == TEXT("set_globals") || Op == TEXT("clear_globals");
	const bool DeviceWide = Op == TEXT("clear_all_globals") || Op == TEXT("deactivate_all_mixes");
	const bool DestinationOp = Op == TEXT("create_destination") || Op == TEXT("set_destination") || Op == TEXT("clear_destination") || Op == TEXT("release_destination");
	const bool MixOp = Filter || Op == TEXT("activate_mix") || Op == TEXT("deactivate_mix") || Op == TEXT("update_mix") || Op == TEXT("update_mix_from_asset");
	const bool GlobalOp = Op == TEXT("set_global") || Op == TEXT("clear_global");
	if (!DestinationOp && !MixOp && !GlobalOp && !BatchMix && !BatchModulators && !BatchGlobal && !DeviceWide && Op != TEXT("update_modulator")) throw std::runtime_error("Unsupported modulation runtime operation");
	FState* Current = States.Find(W); UAudioModulationDestination* Destination = nullptr;
	if (DestinationOp)
	{
		Id(R.DestinationId); if (Current) if (auto* D = Current->Destinations.Find(R.DestinationId)) Destination = D->Get();
		if (Op == TEXT("create_destination")) { if (Destination) throw std::runtime_error("DestinationId already exists in this world"); if (Current && Current->Destinations.Num() >= 64) throw std::runtime_error("Destinations are limited to 64 per world"); }
		else if (!Destination) throw std::runtime_error("DestinationId does not exist in this world");
	}
	const bool NeedsAsset = MixOp || GlobalOp || Op == TEXT("update_modulator") || Op == TEXT("create_destination") || Op == TEXT("set_destination");
	UObject* A = NeedsAsset ? Asset(R.AssetPath) : nullptr;
	USoundControlBusMix* Mix = Cast<USoundControlBusMix>(A); USoundControlBus* Bus = Cast<USoundControlBus>(A); USoundModulatorBase* Modulator = Cast<USoundModulatorBase>(A);
	if ((MixOp && !Mix) || (GlobalOp && !Bus) || ((Op == TEXT("update_modulator") || Op == TEXT("create_destination") || Op == TEXT("set_destination")) && !Modulator)) throw std::runtime_error("Asset class does not match the runtime operation");
	if (!FMath::IsFinite(R.FadeSeconds) || R.FadeSeconds < -1.f || R.FadeSeconds > 86400.f || !FMath::IsFinite(R.DurationSeconds) || R.DurationSeconds < -1.0 || R.DurationSeconds > 86400.0) throw std::runtime_error("FadeSeconds/DurationSeconds must be -1 or 0-86400 seconds");
	if ((Filter || Op == TEXT("update_mix") || Op == TEXT("update_mix_from_asset")) && !UAudioModulationStatics::IsControlBusMixActive(W, Mix)) throw std::runtime_error("Mix must be active before runtime updates");
	TSubclassOf<USoundModulationParameter> ParameterClass; USoundModulationParameter* Parameter = nullptr;
	if (Filter)
	{
		AddressPattern(R.AddressFilter);
		if (!R.ParameterClassFilter.IsEmpty()) { auto* C = LoadClass<USoundModulationParameter>(nullptr, *R.ParameterClassFilter); if (!C) throw std::runtime_error("ParameterClassFilter must identify a modulation parameter class"); ParameterClass = C; }
		if (!R.ParameterFilterPath.IsEmpty()) { Parameter = Cast<USoundModulationParameter>(Asset(R.ParameterFilterPath)); if (!Parameter) throw std::runtime_error("ParameterFilterPath must identify a modulation parameter asset"); }
	}
	else if (!R.AddressFilter.IsEmpty() || !R.ParameterClassFilter.IsEmpty() || !R.ParameterFilterPath.IsEmpty()) throw std::runtime_error("Filter fields apply only to update_mix_by_filter");
	TArray<UObject*> Batch; TSet<const UObject*> BatchSeen;
	if (BatchMix || BatchModulators || BatchGlobal)
	{
		if (!R.AssetPath.IsEmpty() || R.AssetPaths.IsEmpty() || R.AssetPaths.Num() > 128) throw std::runtime_error("Batch controls require 1-128 AssetPaths and no singular AssetPath");
		int32 Additional = 0;
		for (const auto& P : R.AssetPaths)
		{
			auto* Item = Asset(P);
			if (BatchSeen.Contains(Item) || (BatchMix && !Item->IsA<USoundControlBusMix>()) || (BatchGlobal && !Item->IsA<USoundControlBus>()) || (BatchModulators && !Item->IsA<USoundModulatorBase>())) throw std::runtime_error("Batch assets must be unique and match the operation's native class");
			if (Op == TEXT("update_mixes_from_assets") && !UAudioModulationStatics::IsControlBusMixActive(W, Cast<USoundControlBusMix>(Item))) throw std::runtime_error("All batch mixes must be active before runtime refresh");
			if (Op == TEXT("activate_mixes")) Additional += !Current || !Current->Mixes.Contains(Path(Item));
			if (Op == TEXT("set_globals")) Additional += !Current || !Current->Globals.Contains(Path(Item));
			BatchSeen.Add(Item); Batch.Add(Item);
		}
		const int32 Existing = !Current ? 0 : (BatchMix ? Current->Mixes.Num() : Current->Globals.Num());
		if (Additional + Existing > 128 && (Op == TEXT("activate_mixes") || Op == TEXT("set_globals"))) throw std::runtime_error("Combined owned runtime mixes/globals exceed the 128 per-world limit");
	}
	else if (!R.AssetPaths.IsEmpty()) throw std::runtime_error("AssetPaths apply only to batch controls");
	if (DeviceWide && !R.AssetPath.IsEmpty()) throw std::runtime_error("Device-wide controls do not take AssetPath");
	TArray<FSoundControlBusMixStage> Stages; TSet<const UObject*> Seen;
	if (Op == TEXT("update_mix"))
	{
		if (R.Stages.IsEmpty() || R.Stages.Num() > 128) throw std::runtime_error("Stages must contain 1-128 bus updates");
		for (const auto& Item : R.Stages)
		{
			auto* StageBus = Cast<USoundControlBus>(Asset(Item.BusPath));
			if (!StageBus || Seen.Contains(StageBus) || !Mix->MixStages.ContainsByPredicate([StageBus](const auto& S) { return S.Bus == StageBus; })) throw std::runtime_error("Stage buses must be unique members of the mix asset");
			if (!FMath::IsFinite(Item.TargetNormalized) || Item.TargetNormalized < 0.f || Item.TargetNormalized > 1.f) throw std::runtime_error("Stage targets must be normalized in [0,1]");
			Seen.Add(StageBus); Stages.Add(FSoundControlBusMixStage(StageBus, Item.TargetNormalized));
		}
	}
	else if (!R.Stages.IsEmpty()) throw std::runtime_error("Stages apply only to update_mix");
	if ((Filter || Op == TEXT("set_global") || Op == TEXT("set_globals")) && (!FMath::IsFinite(R.TargetNormalized) || R.TargetNormalized < 0.f || R.TargetNormalized > 1.f)) throw std::runtime_error("TargetNormalized must be in [0,1]");
	if (Current && ((Op == TEXT("activate_mix") && !Current->Mixes.Contains(Path(Mix)) && Current->Mixes.Num() >= 128) || (Op == TEXT("set_global") && !Current->Globals.Contains(Path(Bus)) && Current->Globals.Num() >= 128))) throw std::runtime_error("Adapter runtime mix/global controls are limited to 128 each per world");
	if (!R.bDryRun)
	{
		FState& S = State(W);
		if (Op == TEXT("create_destination")) { auto* D = UAudioModulationStatics::CreateModulationDestination(W, FName(*R.DestinationId), Modulator); if (!D || D->GetModulator() != Modulator) throw std::runtime_error("Native modulation destination creation failed"); S.Destinations.Add(R.DestinationId, TStrongObjectPtr<UAudioModulationDestination>(D)); }
		else if (Op == TEXT("set_destination")) Destination->SetModulator(Modulator);
		else if (Op == TEXT("clear_destination")) Destination->ClearModulator();
		else if (Op == TEXT("release_destination")) { Destination->ClearModulator(); S.Destinations.Remove(R.DestinationId); }
		else if (Op == TEXT("activate_mix")) { S.Mixes.Add(Path(Mix), TStrongObjectPtr<USoundControlBusMix>(Mix)); UAudioModulationStatics::ActivateBusMix(W, Mix); }
		else if (Op == TEXT("deactivate_mix")) UAudioModulationStatics::DeactivateBusMix(W, Mix);
		else if (Op == TEXT("update_mix")) UAudioModulationStatics::UpdateMix(W, Mix, Stages, R.FadeSeconds, R.DurationSeconds, R.bRetriggerOnActivation);
		else if (Op == TEXT("update_mix_from_asset")) UAudioModulationStatics::UpdateMixFromObject(W, Mix, R.FadeSeconds);
		else if (Op == TEXT("update_modulator")) UAudioModulationStatics::UpdateModulator(W, Modulator);
		else if (Op == TEXT("set_global")) { S.Globals.Add(Path(Bus), TStrongObjectPtr<USoundControlBus>(Bus)); UAudioModulationStatics::SetGlobalBusMixValue(W, Bus, R.TargetNormalized, R.FadeSeconds); }
		else if (Op == TEXT("clear_global")) { UAudioModulationStatics::ClearGlobalBusMixValue(W, Bus, R.FadeSeconds); S.Globals.Remove(Path(Bus)); }
		else if (Filter) UAudioModulationStatics::UpdateMixByFilter(W, Mix, R.AddressFilter, ParameterClass, Parameter, R.TargetNormalized, R.FadeSeconds);
		else if (Op == TEXT("clear_all_globals")) { UAudioModulationStatics::ClearAllGlobalBusMixValues(W, R.FadeSeconds); S.Globals.Reset(); }
		else if (Op == TEXT("deactivate_all_mixes")) { UAudioModulationStatics::DeactivateAllBusMixes(W); S.Mixes.Reset(); S.Globals.Reset(); }
		else for (auto* Item : Batch)
		{
			if (Op == TEXT("activate_mixes")) { auto* M = Cast<USoundControlBusMix>(Item); S.Mixes.Add(Path(M), TStrongObjectPtr<USoundControlBusMix>(M)); UAudioModulationStatics::ActivateBusMix(W, M); }
			else if (Op == TEXT("deactivate_mixes")) UAudioModulationStatics::DeactivateBusMix(W, Cast<USoundControlBusMix>(Item));
			else if (Op == TEXT("update_mixes_from_assets")) UAudioModulationStatics::UpdateMixFromObject(W, Cast<USoundControlBusMix>(Item), R.FadeSeconds);
			else if (Op == TEXT("update_modulators")) UAudioModulationStatics::UpdateModulator(W, Cast<USoundModulatorBase>(Item));
			else if (Op == TEXT("set_globals")) { auto* B = Cast<USoundControlBus>(Item); S.Globals.Add(Path(B), TStrongObjectPtr<USoundControlBus>(B)); UAudioModulationStatics::SetGlobalBusMixValue(W, B, R.TargetNormalized, R.FadeSeconds); }
			else if (Op == TEXT("clear_globals")) { auto* B = Cast<USoundControlBus>(Item); UAudioModulationStatics::ClearGlobalBusMixValue(W, B, R.FadeSeconds); S.Globals.Remove(Path(B)); }
		}
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	J->WriteValue(TEXT("operation"), Op); J->WriteValue(TEXT("world_path"), Path(W)); J->WriteValue(TEXT("runtime_only"), true);
	J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("command_submitted"), !R.bDryRun);
	J->WriteValue(TEXT("batch_count"), Batch.Num()); J->WriteValue(TEXT("device_wide"), DeviceWide);
	if (!Batch.IsEmpty()) J->WriteValue(TEXT("batch_semantics"), TEXT("all inputs validated before submission; native commands execute independently without rollback"));
	if (Filter) { J->WriteValue(TEXT("address_filter"), R.AddressFilter); J->WriteValue(TEXT("parameter_class_filter"), Path(ParameterClass.Get())); J->WriteValue(TEXT("parameter_filter_path"), Path(Parameter)); J->WriteValue(TEXT("filter_scope"), TEXT("native runtime proxy addresses and exact parameter class/asset IDs; no matched-count readback")); }
	J->WriteValue(TEXT("execution"), TEXT("asynchronous native audio/modulation processing; inspect to observe state")); J->WriteObjectEnd(); J->Close(); return Json;
}
