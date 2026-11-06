#include "AudioDiagnosticUtils.h"
#include "QuartzUtils.h"
#include "UE5_MCP/API/DTO/AudioDiagnosticReq.h"
#include "ActiveSound.h"
#include "AudioDevice.h"
#include "AudioDeviceManager.h"
#include "AudioMixerDevice.h"
#include "AudioThread.h"
#include "Components/AudioComponent.h"
#include "Containers/Ticker.h"
#include "Engine/World.h"
#include "Sound/SoundBase.h"
#include "Serialization/JsonWriter.h"
#include <atomic>
#include <stdexcept>

namespace
{
	struct FSoundRow
	{
		uint32 Instance = 0;
		uint64 Component = 0;
		TWeakObjectPtr<USoundBase> Sound;
		float Playback = 0, Unscaled = 0, Volume = 0, Pitch = 0;
		bool Paused = false, UI = false, HasVirtualized = false;
	};
	struct FPayload
	{
		std::atomic<bool> Ready{false};
		double Captured = 0;
		int32 DeviceCount = 0, WorldCount = 0;
		int32 Rate = 0, OutputChannels = 0, Frames = 0, Buffers = 0, MaxChannels = 0;
		bool Mixer = false;
		TArray<FSoundRow> Rows;
	};
	struct FEntry
	{
		// Owned/destroyed only on the game thread. Audio commands capture a raw device
		// pinned by this entry, and a separate thread-safe payload (never this handle).
		FAudioDeviceHandle Device;
		TSharedRef<FPayload, ESPMode::ThreadSafe> Data = MakeShared<FPayload, ESPMode::ThreadSafe>();
		FString WorldPath;
		double Requested = 0;
		int32 Limit = 0;
	};
	using FCaptures = TMap<FString, TUniquePtr<FEntry>>;
	TMap<TWeakObjectPtr<UWorld>, FCaptures> Worlds;
	TArray<TUniquePtr<FEntry>> Retired;
	FDelegateHandle Cleanup;
	FTSTicker::FDelegateHandle Ticker;
	void Id(const FString& Value)
	{
		if (Value.IsEmpty() || Value.Len() > 64) throw std::runtime_error("CaptureId requires 1-64 characters");
		for (TCHAR C : Value) if (!FChar::IsAlnum(C) && C != '_' && C != '-') throw std::runtime_error("CaptureId allows letters, numbers, underscores and hyphens");
	}
	void Retire(TUniquePtr<FEntry> Entry)
	{
		if (!Entry->Data->Ready.load(std::memory_order_acquire)) Retired.Add(MoveTemp(Entry));
	}
	bool Tick(float)
	{
		check(IsInGameThread());
		for (int32 I = Retired.Num() - 1; I >= 0; --I) if (Retired[I]->Data->Ready.load(std::memory_order_acquire)) Retired.RemoveAtSwap(I);
		return true;
	}
	void OnCleanup(UWorld* W, bool, bool)
	{
		if (auto* Map = Worlds.Find(W)) { for (auto& Pair : *Map) Retire(MoveTemp(Pair.Value)); Worlds.Remove(W); }
	}
	void Ensure()
	{
		if (!Cleanup.IsValid()) Cleanup = FWorldDelegates::OnWorldCleanup.AddStatic(&OnCleanup);
		if (!Ticker.IsValid()) Ticker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick));
	}
	void Number(TSharedRef<TJsonWriter<>>& J, const TCHAR* Key, float Value)
	{
		if (FMath::IsFinite(Value)) J->WriteValue(Key, Value); else J->WriteNull(Key);
	}
}

void AudioDiagnosticUtils::Shutdown()
{
	if (Ticker.IsValid()) { FTSTicker::RemoveTicker(Ticker); Ticker.Reset(); }
	if (Cleanup.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(Cleanup); Cleanup.Reset(); }
	// No callbacks are posted to the game thread. Drain native commands before
	// unloading their code and dropping the final game-thread device handles.
	FAudioCommandFence Fence; Fence.BeginFence(); Fence.Wait(); Worlds.Reset(); Retired.Reset();
}

FString AudioDiagnosticUtils::Control(const FAudioDiagnosticReq& R)
{
	Id(R.CaptureId); auto* W = QuartzUtils::ResolveWorld(R.PIEInstance); const FString Op = R.Operation.ToLower();
	auto* Map = Worlds.Find(W); auto* Existing = Map ? Map->Find(R.CaptureId) : nullptr;
	if (Op == TEXT("capture"))
	{
		int32 Total = Retired.Num(); for (const auto& World : Worlds) Total += World.Value.Num();
		if (Existing || (Map && Map->Num() >= 16) || Total >= 128) throw std::runtime_error("CaptureId exists, per-world limit 16, or global retained/pending limit 128 reached");
		if (R.Limit < 1 || R.Limit > 512) throw std::runtime_error("Limit must be in [1,512]");
		auto Device = W->GetAudioDevice(); if (!Device.IsValid()) throw std::runtime_error("Selected PIE world has no native audio device");
		if (!R.bDryRun)
		{
			auto Entry = MakeUnique<FEntry>(); Entry->Device = MoveTemp(Device); Entry->WorldPath = W->GetPathName(); Entry->Requested = FPlatformTime::Seconds(); Entry->Limit = R.Limit;
			auto* Mixer = FAudioDeviceManager::GetAudioMixerDeviceFromWorldContext(W);
			FAudioDevice* Raw = Entry->Device.GetAudioDevice(); const uint32 WorldId = W->GetUniqueID(); const TWeakObjectPtr<UWorld> WeakWorld(W); const int32 Limit = R.Limit; const auto Data = Entry->Data;
			Ensure(); Worlds.FindOrAdd(W).Add(R.CaptureId, MoveTemp(Entry));
			FAudioThread::RunCommandOnAudioThread([Raw, Mixer, Data, WorldId, WeakWorld, Limit]
			{
				check(IsInAudioThread()); Data->Captured = FPlatformTime::Seconds();
				Data->Rate = Raw->GetSampleRate(); Data->MaxChannels = Raw->GetMaxChannels();
				if (Mixer) { Data->Mixer = true; Data->OutputChannels = Mixer->GetDeviceOutputChannels(); Data->Frames = Mixer->GetNumOutputFrames(); Data->Buffers = Mixer->GetNumOutputBuffers(); }
				for (const FActiveSound* A : Raw->GetActiveSounds())
				{
					if (!A) continue; ++Data->DeviceCount;
					if (A->GetWorldID() != WorldId || A->GetWeakWorld() != WeakWorld) continue; ++Data->WorldCount;
					if (Data->Rows.Num() >= Limit) continue;
					FSoundRow S; S.Instance = A->GetInstanceID(); S.Component = A->GetAudioComponentID(); S.Sound = A->GetSound();
					S.Playback = A->PlaybackTime; S.Unscaled = A->PlaybackTimeUnscaled; S.Volume = A->VolumeMultiplier; S.Pitch = A->PitchMultiplier;
					S.Paused = A->bIsPaused; S.UI = A->bIsUISound; S.HasVirtualized = A->bHasVirtualized; Data->Rows.Add(MoveTemp(S));
				}
				// No device access follows publication; handles can now retire on the game thread.
				Data->Ready.store(true, std::memory_order_release);
			});
		}
	}
	else if (Op == TEXT("release"))
	{
		if (!Existing) throw std::runtime_error("CaptureId does not exist in this PIE world");
		if (!R.bDryRun) { Retire(MoveTemp(*Existing)); Map->Remove(R.CaptureId); }
	}
	else throw std::runtime_error("Diagnostic operation must be capture or release");
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("capture_id"), R.CaptureId); J->WriteValue(TEXT("operation"), Op); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("command_submitted"), !R.bDryRun && Op == TEXT("capture")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString AudioDiagnosticUtils::Inspect(const FString& Value, int32 Instance)
{
	Id(Value); auto* W = QuartzUtils::ResolveWorld(Instance); auto* Map = Worlds.Find(W); auto* Found = Map ? Map->Find(Value) : nullptr;
	if (!Found) throw std::runtime_error("CaptureId does not exist in this PIE world"); const auto& E = **Found;
	const bool Ready = E.Data->Ready.load(std::memory_order_acquire);
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("capture_id"), Value); J->WriteValue(TEXT("ready"), Ready);
	J->WriteValue(TEXT("world_path"), E.WorldPath); J->WriteValue(TEXT("audio_device_id"), static_cast<int64>(E.Device.GetDeviceID())); J->WriteValue(TEXT("requested_seconds"), E.Requested);
	J->WriteValue(TEXT("scope"), TEXT("audio-thread snapshot of native logical active sounds filtered by world ID; excludes separate virtual loops; not hardware voices or CPU profiling"));
	if (Ready)
	{
		const auto& D = *E.Data; J->WriteValue(TEXT("captured_seconds"), D.Captured); J->WriteValue(TEXT("device_active_sound_count"), D.DeviceCount); J->WriteValue(TEXT("world_active_sound_count"), D.WorldCount); J->WriteValue(TEXT("truncated"), D.WorldCount > D.Rows.Num());
		J->WriteObjectStart(TEXT("device_configuration_at_capture")); J->WriteValue(TEXT("mixer"), D.Mixer); J->WriteValue(TEXT("sample_rate"), D.Rate); J->WriteValue(TEXT("max_channels"), D.MaxChannels);
		if (D.Mixer) { J->WriteValue(TEXT("output_channels"), D.OutputChannels); J->WriteValue(TEXT("callback_frames"), D.Frames); J->WriteValue(TEXT("output_buffers"), D.Buffers); } J->WriteObjectEnd();
		J->WriteValue(TEXT("path_scope"), TEXT("weak sound/component paths resolved on game thread after capture; missing/deleted objects yield empty paths"));
		J->WriteArrayStart(TEXT("sounds"));
		for (const auto& S : D.Rows)
		{
			J->WriteObjectStart(); J->WriteValue(TEXT("instance_id"), S.Instance); J->WriteValue(TEXT("audio_component_id"), S.Component);
			auto* Sound = S.Sound.Get(); auto* Component = UAudioComponent::GetAudioComponentFromID(S.Component);
			if (!IsValid(Component) || Component->IsBeingDestroyed()) Component = nullptr;
			J->WriteValue(TEXT("sound_path"), Sound ? Sound->GetPathName() : FString()); J->WriteValue(TEXT("component_path"), Component ? Component->GetPathName() : FString());
			Number(J, TEXT("playback_seconds"), S.Playback); Number(J, TEXT("playback_unscaled_seconds"), S.Unscaled); Number(J, TEXT("volume_multiplier"), S.Volume); Number(J, TEXT("pitch_multiplier"), S.Pitch);
			J->WriteValue(TEXT("paused"), S.Paused); J->WriteValue(TEXT("ui_sound"), S.UI); J->WriteValue(TEXT("has_virtualized"), S.HasVirtualized); J->WriteObjectEnd();
		}
		J->WriteArrayEnd();
	}
	J->WriteObjectEnd(); J->Close(); return Json;
}
