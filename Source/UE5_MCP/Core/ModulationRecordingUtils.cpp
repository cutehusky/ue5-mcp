#include "ModulationRecordingUtils.h"
#include "ModulationRuntimeUtils.h"
#include "ModulationUtils.h"
#include "UE5_MCP/API/DTO/ModulationRecordingReq.h"
#include "AudioModulationDestination.h"
#include "AudioModulationStatics.h"
#include "Generators/SoundModulationEnvelopeFollower.h"
#include "Sound/AudioBus.h"
#include "IAudioModulation.h"
#include "Containers/Ticker.h"
#include "Engine/World.h"
#include "Serialization/JsonWriter.h"
#include "UObject/StrongObjectPtr.h"
#include <stdexcept>

namespace
{
	struct FSample { double Received = 0; float Value = 0; };
	struct FRecording
	{
		TStrongObjectPtr<UAudioModulationDestination> Destination;
		FString AssetPath, AudioBusPath, StopReason;
		double Started = 0, Next = 0, Duration = 0, Interval = 0;
		TArray<FSample> Samples;
	};
	using FRecordings = TMap<FString, TUniquePtr<FRecording>>;
	TMap<TWeakObjectPtr<UWorld>, FRecordings> Worlds;
	FDelegateHandle Cleanup;
	FTSTicker::FDelegateHandle Ticker;
	void Id(const FString& Value)
	{
		if (Value.IsEmpty() || Value.Len() > 64) throw std::runtime_error("RecordingId must contain 1-64 characters");
		for (TCHAR C : Value) if (!FChar::IsAlnum(C) && C != '_' && C != '-') throw std::runtime_error("RecordingId allows letters, numbers, underscores and hyphens");
	}
	void Close(FRecording& R, const FString& Reason)
	{
		if (R.Destination.IsValid()) { R.Destination->ClearModulator(); R.Destination.Reset(); }
		R.StopReason = Reason;
	}
	void Capture(FRecording& R, double Now)
	{
		const float V = R.Destination->GetValue();
		if (!FMath::IsFinite(V)) { Close(R, TEXT("nonfinite_native_value")); return; }
		R.Samples.Add({Now, V}); R.Next = Now + R.Interval;
		if (R.Samples.Num() >= 1024) Close(R, TEXT("sample_limit"));
	}
	bool Tick(float)
	{
		check(IsInGameThread()); const double Now = FPlatformTime::Seconds();
		for (auto& World : Worlds) for (auto& Pair : World.Value)
		{
			auto& R = *Pair.Value;
			if (!R.Destination.IsValid()) continue;
			if (Now - R.Started >= R.Duration) Close(R, TEXT("completed"));
			else if (Now >= R.Next) Capture(R, Now);
		}
		return true;
	}
	void OnCleanup(UWorld* W, bool, bool)
	{
		if (auto* Map = Worlds.Find(W)) { for (auto& Pair : *Map) Close(*Pair.Value, TEXT("world_cleanup")); Worlds.Remove(W); }
	}
	void Ensure()
	{
		if (!Cleanup.IsValid()) Cleanup = FWorldDelegates::OnWorldCleanup.AddStatic(&OnCleanup);
		if (!Ticker.IsValid()) Ticker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick));
	}
}

void ModulationRecordingUtils::Shutdown()
{
	if (Ticker.IsValid()) { FTSTicker::RemoveTicker(Ticker); Ticker.Reset(); }
	if (Cleanup.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(Cleanup); Cleanup.Reset(); }
	for (auto& World : Worlds) for (auto& Pair : World.Value) Close(*Pair.Value, TEXT("module_shutdown")); Worlds.Reset();
}

FString ModulationRecordingUtils::Control(const FModulationRecordingReq& R)
{
	Id(R.RecordingId); auto* W = ModulationRuntimeUtils::ResolveAudioWorld(R.PIEInstance); const FString Op = R.Operation.ToLower();
	bool Changed = !R.bDryRun;
	auto* Map = Worlds.Find(W); auto* Existing = Map ? Map->Find(R.RecordingId) : nullptr;
	if (Op == TEXT("start"))
	{
		if (Existing || (Map && Map->Num() >= 16)) throw std::runtime_error("RecordingId already exists or the 16-recording per-world limit was reached");
		if (!FMath::IsFinite(R.IntervalSeconds) || R.IntervalSeconds < .01f || R.IntervalSeconds > 1 || !FMath::IsFinite(R.DurationSeconds) || R.DurationSeconds < .02f || R.DurationSeconds > 60 || FMath::CeilToInt(R.DurationSeconds / R.IntervalSeconds) + 1 > 1024) throw std::runtime_error("Recording requires interval [0.01,1], duration [0.02,60] and at most 1024 requested samples");
		auto* A = LoadObject<USoundModulatorBase>(nullptr, *R.AssetPath);
		if (!A) throw std::runtime_error("AssetPath must identify a native sound modulator");
		const auto Errors = ModulationUtils::ValidationErrors(A); if (!Errors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(Errors, TEXT("; "))));
		FString BusPath;
		if (auto* F = Cast<USoundModulationGeneratorEnvelopeFollower>(A)) { if (!F->Params.AudioBus) throw std::runtime_error("Live envelope follower recording requires an assigned Audio Bus"); BusPath = F->Params.AudioBus->GetPathName(); }
		if (!R.bDryRun)
		{
			auto* D = UAudioModulationStatics::CreateModulationDestination(W, FName(*(TEXT("MCP_Recording_") + R.RecordingId)), A);
			if (!D || D->GetModulator() != A) throw std::runtime_error("Native recording destination could not be created");
			auto Recording = MakeUnique<FRecording>(); Recording->Destination = TStrongObjectPtr<UAudioModulationDestination>(D);
			Recording->AssetPath = A->GetPathName(); Recording->AudioBusPath = BusPath; Recording->Interval = R.IntervalSeconds; Recording->Duration = R.DurationSeconds;
			Recording->Started = FPlatformTime::Seconds(); Capture(*Recording, Recording->Started); Ensure(); Worlds.FindOrAdd(W).Add(R.RecordingId, MoveTemp(Recording));
		}
	}
	else if (Op == TEXT("stop") || Op == TEXT("release"))
	{
		if (!Existing) throw std::runtime_error("RecordingId does not exist in this PIE world");
		if (!R.bDryRun) { if ((*Existing)->Destination.IsValid()) Close(**Existing, TEXT("stopped")); else if (Op == TEXT("stop")) Changed = false; if (Op == TEXT("release")) Map->Remove(R.RecordingId); }
	}
	else throw std::runtime_error("Recording operation must be start, stop or release");
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("recording_id"), R.RecordingId); J->WriteValue(TEXT("operation"), Op); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("changed"), Changed); J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationRecordingUtils::Inspect(const FString& Value, int32 Instance, uint64 After, int32 Limit)
{
	Id(Value); if (Limit < 1 || Limit > 1024) throw std::runtime_error("limit must be in [1,1024]"); auto* W = ModulationRuntimeUtils::ResolveAudioWorld(Instance);
	auto* Map = Worlds.Find(W); auto* Found = Map ? Map->Find(Value) : nullptr; if (!Found) throw std::runtime_error("RecordingId does not exist in this PIE world"); const auto& R = **Found;
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("recording_id"), Value); J->WriteValue(TEXT("asset_path"), R.AssetPath); J->WriteValue(TEXT("audio_bus_path"), R.AudioBusPath);
	J->WriteValue(TEXT("running"), R.Destination.IsValid()); J->WriteValue(TEXT("stop_reason"), R.StopReason); J->WriteValue(TEXT("interval_seconds"), R.Interval); J->WriteValue(TEXT("duration_seconds"), R.Duration); J->WriteValue(TEXT("started_seconds"), R.Started); J->WriteValue(TEXT("sample_count"), R.Samples.Num());
	J->WriteValue(TEXT("sampling_scope"), TEXT("native destination GetValue from last modulation processing tick; initial/inactive native fallback may be 1; monotonic game-thread receipt times; skipped ticks are not synthesized; not sample-accurate PCM/envelope analysis"));
	J->WriteArrayStart(TEXT("samples")); uint64 Next = After; int32 Count = 0;
	for (int32 I = 0; I < R.Samples.Num(); ++I) if (static_cast<uint64>(I + 1) > After && Count++ < Limit) { const auto& S = R.Samples[I]; J->WriteObjectStart(); J->WriteValue(TEXT("sequence"), I + 1); J->WriteValue(TEXT("received_seconds"), S.Received); J->WriteValue(TEXT("value_normalized"), S.Value); J->WriteObjectEnd(); Next = I + 1; }
	J->WriteArrayEnd(); J->WriteValue(TEXT("next_sequence"), Next); J->WriteObjectEnd(); J->Close(); return Json;
}
