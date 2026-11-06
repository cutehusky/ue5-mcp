#include "QuartzEventUtils.h"
#include "QuartzUtils.h"
#include "UE5_MCP/API/DTO/QuartzEventReq.h"
#include "Async/Async.h"
#include "Components/AudioComponent.h"
#include "AudioMixerDevice.h"
#include "AudioDeviceManager.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundConcurrency.h"
#include "Sound/AudioBus.h"
#include "Engine/World.h"
#include "Quartz/AudioMixerClock.h"
#include "Quartz/AudioMixerClockHandle.h"
#include "Quartz/AudioMixerClockManager.h"
#include "Quartz/QuartzSubsystem.h"
#include "Serialization/JsonWriter.h"
#include "UObject/StrongObjectPtr.h"
#include <stdexcept>

void UQuartzApiObserver::Append(FQuartzApiEvent Event)
{
	check(IsInGameThread()); Event.Sequence = ++Sequence; Event.ReceivedSeconds = FPlatformTime::Seconds();
	if (Events.Num() >= 256) { Events.RemoveAt(0); ++Dropped; } Events.Add(MoveTemp(Event));
}

void UQuartzApiObserver::OnCommand(EQuartzCommandDelegateSubType Type, FName Name)
{
	FQuartzApiEvent E; E.Kind = TEXT("native_command"); E.Value = StaticEnum<EQuartzCommandDelegateSubType>()->GetNameStringByValue(static_cast<int64>(Type)); E.Clock = ClockName; E.CommandName = Name;
	Append(MoveTemp(E));
	if (Type == EQuartzCommandDelegateSubType::CommandOnStarted || Type == EQuartzCommandDelegateSubType::CommandOnCanceled || Type == EQuartzCommandDelegateSubType::CommandOnFailedToQueue) { bTerminal = true; Command.Reset(); }
}

void UQuartzApiObserver::OnMetronome(FName Clock, EQuartzCommandQuantization Quantization, int32 Bars, int32 Beat, float Fraction)
{
	if (bClosed) return;
	FQuartzApiEvent E; E.Kind = TEXT("native_metronome"); E.Value = StaticEnum<EQuartzCommandQuantization>()->GetNameStringByValue(static_cast<int64>(Quantization)); E.Clock = Clock; E.Bars = Bars; E.Beat = Beat; E.BeatFraction = Fraction; Append(MoveTemp(E));
}

void UQuartzApiObserver::Rejected(const FString& Reason)
{
	FQuartzApiEvent E; E.Kind = TEXT("adapter_rejected"); E.Value = Reason; E.Clock = ClockName; Append(MoveTemp(E)); bTerminal = true; Command.Reset();
}

void UQuartzApiObserver::OnAudioFinished()
{
	if (bClosed) return;
	FQuartzApiEvent E; E.Kind = TEXT("native_audio_finished"); E.Value = TEXT("OnAudioFinished"); E.Clock = ClockName; Append(MoveTemp(E));
}

namespace
{
	using FObservers = TMap<FString, TStrongObjectPtr<UQuartzApiObserver>>;
	struct FSend { UAudioBus* Bus; float Level; bool Post; FString Key; };
	TArray<FSend> Sends(const FQuartzEventReq& R, USoundBase* Sound, UQuartzApiObserver* O)
	{
		if (R.AudioBusSends.Num() > 16 || (O && R.AudioBusSends.IsEmpty())) throw std::runtime_error("Audio Bus sends require 1-16 entries for updates");
		if (!R.AudioBusSends.IsEmpty() && (!Sound || !Sound->bEnableBusSends)) throw std::runtime_error("Source sound must enable Audio Bus sends");
		TArray<FSend> Result; TSet<FString> Seen; int32 Additional = 0;
		for (const auto& S : R.AudioBusSends)
		{
			auto* B = LoadObject<UAudioBus>(nullptr, *S.BusPath);
			if (!B || !B->IsAsset() || !FMath::IsFinite(S.SendLevel) || S.SendLevel < 0 || S.SendLevel > 4) throw std::runtime_error("Audio Bus send requires a native Audio Bus asset and finite level [0,4]");
			const FString Key = (S.bPostEffect ? TEXT("post:") : TEXT("pre:")) + B->GetPathName();
			if (Seen.Contains(Key)) throw std::runtime_error("Audio Bus send stages must be unique per bus");
			Seen.Add(Key); Additional += !O || !O->AudioBuses.Contains(Key); Result.Add({B,S.SendLevel,S.bPostEffect,Key});
		}
		if (Additional + (O ? O->AudioBuses.Num() : 0) > 16) throw std::runtime_error("Owned sound components are limited to 16 Audio Bus send stages");
		return Result;
	}
	void ApplySends(UQuartzApiObserver* O, const TArray<FSend>& Values)
	{
		for (const auto& S : Values)
		{
			O->AudioBuses.Add(S.Key, S.Bus); O->RequestedSendLevels.Add(S.Key, S.Level);
			if (S.Post) O->AudioComponent->SetAudioBusSendPostEffect(S.Bus, S.Level);
			else O->AudioComponent->SetAudioBusSendPreEffect(S.Bus, S.Level);
		}
	}
	TMap<TWeakObjectPtr<UWorld>, FObservers> Worlds;
	FDelegateHandle Cleanup;
	void Id(const FString& Value)
	{
		if (Value.IsEmpty() || Value.Len() > 64) throw std::runtime_error("EventId must contain 1-64 characters");
		for (TCHAR C : Value) if (!FChar::IsAlnum(C) && C != TEXT('_') && C != TEXT('-')) throw std::runtime_error("EventId allows letters, numbers, underscores and hyphens");
	}
	void Transform(const FQuartzEventReq& R)
	{
		if (R.Location.ContainsNaN() || R.Rotation.ContainsNaN() || R.Location.GetAbsMax() > 1.e9 || FMath::Abs(R.Rotation.Pitch) > 360000 || FMath::Abs(R.Rotation.Yaw) > 360000 || FMath::Abs(R.Rotation.Roll) > 360000)
			throw std::runtime_error("Location/Rotation must be finite; position bounded to 1e9 cm and angles to 360000 degrees");
	}
	EQuartzCommandQuantization Quantization(const FString& Value)
	{
		const int64 V = StaticEnum<EQuartzCommandQuantization>()->GetValueByNameString(Value);
		if (V < 0 || V >= static_cast<int64>(EQuartzCommandQuantization::Count)) throw std::runtime_error("Quantization must identify a native musical division; None/Count are unsupported"); return static_cast<EQuartzCommandQuantization>(V);
	}
	Audio::FQuartzClockProxy Proxy(UWorld* W, FName Name)
	{
		auto* S = W->GetSubsystem<UQuartzSubsystem>(); if (!S) throw std::runtime_error("Quartz subsystem unavailable");
		auto P = S->GetProxyForClock(Name); if (!P.DoesClockExist()) throw std::runtime_error("Clock does not exist in this PIE world"); return P;
	}
	void Close(UWorld* W, UQuartzApiObserver* O)
	{
		O->bClosed = true;
		if (O->AudioComponent) { O->AudioComponent->Stop(); O->AudioComponent->DestroyComponent(); O->AudioComponent = nullptr; }
		O->AudioBuses.Reset(); O->RequestedSendLevels.Reset();
		if (!O->Handle) return;
		UQuartzClockHandle* H = O->Handle;
		if (H->DoesClockExist(W))
		{
			if (O->bSubscription) H->UnsubscribeFromAllTimeDivisions(W, H);
			else if (O->Command.IsValid()) { auto* S = W->GetSubsystem<UQuartzSubsystem>(); const auto WeakCommand = O->Command; if (S) S->GetProxyForClock(O->ClockName).SendCommandToClock([WeakCommand](Audio::FQuartzClock* C) { if (auto Command = WeakCommand.Pin()) C->CancelQuantizedCommand(Command); }); }
		}
	}
	void OnCleanup(UWorld* W, bool, bool)
	{
		if (auto* Map = Worlds.Find(W)) { for (auto& Pair : *Map) Close(W, Pair.Value.Get()); Worlds.Remove(W); }
	}
	FObservers& State(UWorld* W)
	{
		if (!Cleanup.IsValid()) Cleanup = FWorldDelegates::OnWorldCleanup.AddStatic(&OnCleanup); return Worlds.FindOrAdd(W);
	}
	UQuartzApiObserver* Observer(UWorld* W, FObservers& Map, const FString& IdValue, FName Name, const Audio::FQuartzClockProxy& P)
	{
		auto* O = NewObject<UQuartzApiObserver>(W); O->Id = IdValue; O->ClockName = Name;
		auto* H = NewObject<UQuartzClockHandle>(O); H->Init(W); H->SubscribeToClock(W, Name, &P); O->Handle = H;
		Map.Add(IdValue, TStrongObjectPtr<UQuartzApiObserver>(O)); return O;
	}
}

void QuartzEventUtils::Shutdown()
{
	if (Cleanup.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(Cleanup); Cleanup.Reset(); }
	for (auto& Pair : Worlds) if (auto* W = Pair.Key.Get()) for (auto& Item : Pair.Value) Close(W, Item.Value.Get()); Worlds.Reset();
}

FString QuartzEventUtils::Control(const FQuartzEventReq& R)
{
	Id(R.EventId); UWorld* W = QuartzUtils::ResolveWorld(R.PIEInstance); const FString Op = R.Operation.ToLower();
	const bool Play = Op == TEXT("play_sound");
	const bool Subscribe = Op == TEXT("subscribe"); const bool Schedule = Play || Op == TEXT("tempo") || Op == TEXT("reset") || Op == TEXT("notify") || Op == TEXT("start_other");
	const bool SendControl = Op == TEXT("set_audio_bus_sends");
	const bool AudioControl = SendControl || Op == TEXT("stop_sound") || Op == TEXT("pause_sound") || Op == TEXT("resume_sound") || Op == TEXT("move_sound");
	if (!Subscribe && !Schedule && !AudioControl && Op != TEXT("unsubscribe") && Op != TEXT("cancel") && Op != TEXT("release")) throw std::runtime_error("Unsupported Quartz event operation");
	FObservers* Map = Worlds.Find(W); UQuartzApiObserver* O = Map && Map->Contains(R.EventId) ? (*Map)[R.EventId].Get() : nullptr;
	bool Submitted = false;
	if (!Play && !SendControl && !R.AudioBusSends.IsEmpty()) throw std::runtime_error("AudioBusSends apply only to play_sound/set_audio_bus_sends");
	if (Subscribe || Schedule)
	{
		if (O) throw std::runtime_error("EventId already exists; release it or choose a new ID");
		if (Map && Map->Num() >= 128) throw std::runtime_error("Observers/requests are limited to 128 per PIE world");
		const FName Name = QuartzUtils::ClockName(R.ClockName); auto P = Proxy(W, Name); const auto Q = Quantization(R.Quantization);
		const int64 Reference = StaticEnum<EQuarztQuantizationReference>()->GetValueByNameString(R.ReferencePoint);
		if (Reference < 0 || Reference >= static_cast<int64>(EQuarztQuantizationReference::Count) || !FMath::IsFinite(R.Multiplier) || R.Multiplier < 1 || R.Multiplier > 64) throw std::runtime_error("ReferencePoint must be native BarRelative/TransportRelative/CurrentTimeRelative and Multiplier in [1,64]");
		if (Op == TEXT("tempo") && (!FMath::IsFinite(R.BeatsPerMinute) || R.BeatsPerMinute < 1 || R.BeatsPerMinute > 1000)) throw std::runtime_error("BeatsPerMinute must be finite and in [1,1000]");
		FName Other;
		USoundBase* Sound = nullptr;
		USoundAttenuation* Attenuation = nullptr;
		USoundConcurrency* Concurrency = nullptr;
		USceneComponent* Parent = nullptr;
		TArray<FSend> BusSends;
		if (Play)
		{
			Transform(R);
			auto* Mixer = FAudioDeviceManager::GetAudioMixerDeviceFromWorldContext(W);
			if (!Mixer || !Mixer->QuantizedEventClockManager.DoesClockExist(Name)) throw std::runtime_error("Quantized sound requires an audio engine clock in this PIE world");
			Sound = LoadObject<USoundBase>(nullptr, *R.SoundPath);
			if (!Sound) throw std::runtime_error("SoundPath must resolve to a native SoundBase asset");
			BusSends = Sends(R, Sound, nullptr);
			if (!R.AttenuationPath.IsEmpty()) { Attenuation = LoadObject<USoundAttenuation>(nullptr, *R.AttenuationPath); if (!Attenuation) throw std::runtime_error("AttenuationPath must resolve to a native Sound Attenuation asset"); }
			if (!R.ConcurrencyPath.IsEmpty()) { Concurrency = LoadObject<USoundConcurrency>(nullptr, *R.ConcurrencyPath); if (!Concurrency) throw std::runtime_error("ConcurrencyPath must resolve to a native Sound Concurrency asset"); }
			if (!R.AttachComponentPath.IsEmpty())
			{
				Parent = FindObject<USceneComponent>(nullptr, *R.AttachComponentPath);
				if (!IsValid(Parent) || Parent->GetWorld() != W || !Parent->IsRegistered()) throw std::runtime_error("AttachComponentPath must identify a registered scene component in the selected PIE world");
				if (!R.AttachSocket.IsEmpty() && !Parent->DoesSocketExist(FName(*R.AttachSocket))) throw std::runtime_error("AttachSocket does not exist on the selected component");
			}
			else if (!R.AttachSocket.IsEmpty()) throw std::runtime_error("AttachSocket requires AttachComponentPath");
			if (!FMath::IsFinite(R.StartTime) || R.StartTime < 0 || R.StartTime > 86400 || !FMath::IsFinite(R.FadeInDuration) || R.FadeInDuration < 0 || R.FadeInDuration > 3600 || !FMath::IsFinite(R.VolumeMultiplier) || R.VolumeMultiplier < 0 || R.VolumeMultiplier > 4 || !FMath::IsFinite(R.PitchMultiplier) || R.PitchMultiplier < .125f || R.PitchMultiplier > 4) throw std::runtime_error("Sound controls require start [0,86400], fade [0,3600], volume [0,4], pitch [0.125,4]");
		}
		if (Op == TEXT("start_other")) { Other = QuartzUtils::ClockName(R.OtherClockName); Proxy(W, Other); if (Other == Name) throw std::runtime_error("OtherClockName must identify another clock"); }
		if (!R.bDryRun)
		{
			O = Observer(W, State(W), R.EventId, Name, P); O->Operation = Op; O->bSubscription = Subscribe;
			UQuartzClockHandle* H = O->Handle;
			if (Subscribe) { FOnQuartzMetronomeEventBP Delegate; Delegate.BindDynamic(O, &UQuartzApiObserver::OnMetronome); H->SubscribeToQuantizationEvent(W, Q, Delegate, H); Submitted = true; }
			else
			{
				FQuartzQuantizationBoundary B(Q, R.Multiplier, static_cast<EQuarztQuantizationReference>(Reference), R.bFireOnClockStart); B.bCancelCommandIfClockIsNotRunning = R.bCancelIfNotRunning; B.bResumeClockOnQueued = R.bResumeOnQueued;
				FOnQuartzCommandEventBP Delegate; Delegate.BindDynamic(O, &UQuartzApiObserver::OnCommand); Audio::FQuartzQuantizedRequestData Data;
				if (Play)
				{
					auto* Component = NewObject<UAudioComponent>(W, NAME_None, RF_Transient); O->AudioComponent = Component;
					Component->bAutoActivate = false; Component->bAutoDestroy = false; Component->bIsUISound = !R.bSpatialized; Component->bAllowSpatialization = R.bSpatialized;
					Component->SetSound(Sound); Component->SetVolumeMultiplier(R.VolumeMultiplier); Component->SetPitchMultiplier(R.PitchMultiplier);
					if (Attenuation) Component->SetAttenuationSettings(Attenuation);
					if (Concurrency) Component->ConcurrencySet.Add(Concurrency);
					if (Parent) Component->SetupAttachment(Parent, FName(*R.AttachSocket));
					Component->OnAudioFinished.AddDynamic(O, &UQuartzApiObserver::OnAudioFinished); Component->RegisterComponentWithWorld(W);
					Component->SetWorldLocationAndRotation(R.Location, R.Rotation);
					ApplySends(O, BusSends);
					Component->PlayQuantized(W, H, B, Delegate, R.StartTime, R.FadeInDuration); Submitted = true;
				}
				else
				{
					if (Op == TEXT("tempo")) { Audio::FQuartzClockTickRate Rate; Rate.SetBeatsPerMinute(R.BeatsPerMinute); Data = UQuartzSubsystem::CreateRequestDataForTickRateChange(H, Delegate, Rate, B); }
					else if (Op == TEXT("reset")) Data = UQuartzSubsystem::CreateRequestDataForTransportReset(H, B, Delegate);
					else if (Op == TEXT("notify")) Data = UQuartzSubsystem::CreateRequestDataForQuantizedNotify(H, B, Delegate);
					else Data = UQuartzSubsystem::CreateRequestDataForStartOtherClock(H, Other, B, Delegate);
					O->Command = Data.QuantizedCommandPtr; const TWeakObjectPtr<UQuartzApiObserver> Weak(O);
					Submitted = P.SendCommandToClock([Data, Other, Weak](Audio::FQuartzClock* C) mutable
					{
						if (!Other.IsNone() && (!C->GetClockManager() || !C->GetClockManager()->DoesClockExist(Other))) { AsyncTask(ENamedThreads::GameThread, [Weak] { if (auto* Sink = Weak.Get()) Sink->Rejected(TEXT("Other clock is not managed by the source clock's manager")); }); return; }
						C->AddQuantizedCommand(Data);
					});
					if (!Submitted) { State(W).Remove(R.EventId); throw std::runtime_error("Native Quartz request could not be submitted"); }
				}
			}
		}
	}
	else
	{
		if (!O) throw std::runtime_error("EventId does not exist in this world");
		if (AudioControl && !O->AudioComponent) throw std::runtime_error("Operation requires an owned sound component");
		const TArray<FSend> BusSends = SendControl ? Sends(R, O->AudioComponent->Sound, O) : TArray<FSend>();
		if (Op == TEXT("move_sound")) Transform(R);
		if (Op == TEXT("cancel") && O->AudioComponent) throw std::runtime_error("Use stop_sound for quantized audio components");
		if (Op == TEXT("unsubscribe") && !O->bSubscription) throw std::runtime_error("EventId is not a metronome subscription");
		if (Op == TEXT("cancel") && (O->bSubscription || O->bTerminal)) throw std::runtime_error("Cancel requires a pending scheduled request");
		if (Op == TEXT("release") && !O->AudioComponent && !O->bSubscription && !O->bTerminal && O->Handle->DoesClockExist(W)) throw std::runtime_error("Cancel pending requests and wait for terminal events before release");
		if (!R.bDryRun)
		{
			if (Op == TEXT("cancel")) { const auto WeakCommand = O->Command; if (!WeakCommand.IsValid()) throw std::runtime_error("Request is no longer pending; poll its terminal events"); Submitted = Proxy(W, O->ClockName).SendCommandToClock([WeakCommand](Audio::FQuartzClock* C) { if (auto Command = WeakCommand.Pin()) C->CancelQuantizedCommand(Command); }); if (!Submitted) throw std::runtime_error("Cancellation could not be submitted"); }
			else if (AudioControl) { if (SendControl) ApplySends(O, BusSends); else if (Op == TEXT("stop_sound")) O->AudioComponent->Stop(); else if (Op == TEXT("move_sound")) O->AudioComponent->SetWorldLocationAndRotation(R.Location, R.Rotation); else O->AudioComponent->SetPaused(Op == TEXT("pause_sound")); Submitted = true; }
			else { Close(W, O); if (Op == TEXT("release")) Map->Remove(R.EventId); Submitted = true; }
		}
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("event_id"), R.EventId); J->WriteValue(TEXT("operation"), Op); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("submitted"), Submitted);
	J->WriteValue(TEXT("execution"), TEXT("native clock processing; poll events for native queue/start/cancel callbacks")); J->WriteObjectEnd(); J->Close(); return Json;
}

FString QuartzEventUtils::Inspect(const FString& Value, int32 PIEInstance, uint64 After, int32 Limit)
{
	Id(Value); if (Limit < 1 || Limit > 256) throw std::runtime_error("limit must be in [1,256]"); UWorld* W = QuartzUtils::ResolveWorld(PIEInstance);
	auto* Map = Worlds.Find(W); auto* Strong = Map ? Map->Find(Value) : nullptr; if (!Strong) throw std::runtime_error("EventId does not exist in this PIE world"); auto* O = Strong->Get();
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("event_id"), Value); J->WriteValue(TEXT("clock_name"), O->ClockName.ToString()); J->WriteValue(TEXT("operation"), O->Operation);
	J->WriteValue(TEXT("subscription"), O->bSubscription); J->WriteValue(TEXT("closed"), O->bClosed); J->WriteValue(TEXT("terminal"), O->bTerminal); J->WriteValue(TEXT("clock_exists"), O->Handle->DoesClockExist(W)); J->WriteValue(TEXT("dropped_events"), O->Dropped);
	J->WriteValue(TEXT("latest_sequence"), O->Sequence); J->WriteValue(TEXT("oldest_sequence"), O->Events.IsEmpty() ? uint64(0) : O->Events[0].Sequence);
	if (O->AudioComponent)
	{
		auto* A = O->AudioComponent.Get(); J->WriteObjectStart(TEXT("audio_component"));
		J->WriteValue(TEXT("component_path"), A->GetPathName());
		J->WriteValue(TEXT("sound_path"), A->Sound ? A->Sound->GetPathName() : FString());
		J->WriteValue(TEXT("registered"), A->IsRegistered()); J->WriteValue(TEXT("playing"), A->IsPlaying());
		J->WriteValue(TEXT("play_state"), StaticEnum<EAudioComponentPlayState>()->GetNameStringByValue(static_cast<int64>(A->GetPlayState())));
		J->WriteValue(TEXT("volume_multiplier"), A->VolumeMultiplier); J->WriteValue(TEXT("pitch_multiplier"), A->PitchMultiplier);
		J->WriteArrayStart(TEXT("requested_audio_bus_sends"));
		for (const auto& Pair : O->AudioBuses) { J->WriteObjectStart(); J->WriteValue(TEXT("bus_path"), Pair.Value->GetPathName()); J->WriteValue(TEXT("post_effect"), Pair.Key.StartsWith(TEXT("post:"))); J->WriteValue(TEXT("send_level"), O->RequestedSendLevels.FindRef(Pair.Key)); J->WriteObjectEnd(); }
		J->WriteArrayEnd(); J->WriteValue(TEXT("bus_send_scope"), TEXT("requested native component send settings; audio-thread routing is asynchronous"));
		J->WriteValue(TEXT("spatialization_allowed"), bool(A->bAllowSpatialization)); J->WriteValue(TEXT("ui_sound"), bool(A->bIsUISound));
		J->WriteValue(TEXT("attenuation_path"), A->AttenuationSettings ? A->AttenuationSettings->GetPathName() : FString());
		if (const auto* Settings = A->GetAttenuationSettingsToApply()) { J->WriteObjectStart(TEXT("effective_attenuation")); J->WriteValue(TEXT("attenuate"), bool(Settings->bAttenuate)); J->WriteValue(TEXT("spatialize"), bool(Settings->bSpatialize)); J->WriteValue(TEXT("falloff_distance"), Settings->FalloffDistance); J->WriteObjectEnd(); }
		J->WriteArrayStart(TEXT("concurrency_paths")); for (const auto& C : A->ConcurrencySet) if (C) J->WriteValue(C->GetPathName()); J->WriteArrayEnd();
		J->WriteValue(TEXT("attach_component_path"), A->GetAttachParent() ? A->GetAttachParent()->GetPathName() : FString()); J->WriteValue(TEXT("attach_socket"), A->GetAttachSocketName().ToString());
		const FVector L = A->GetComponentLocation(); const FRotator Rot = A->GetComponentRotation();
		J->WriteObjectStart(TEXT("location")); J->WriteValue(TEXT("x"), L.X); J->WriteValue(TEXT("y"), L.Y); J->WriteValue(TEXT("z"), L.Z); J->WriteObjectEnd();
		J->WriteObjectStart(TEXT("rotation")); J->WriteValue(TEXT("pitch"), Rot.Pitch); J->WriteValue(TEXT("yaw"), Rot.Yaw); J->WriteValue(TEXT("roll"), Rot.Roll); J->WriteObjectEnd();
		J->WriteValue(TEXT("scope"), TEXT("transient PIE component; world transform; native sound/attenuation determine effective spatialization; playing may include waiting for Quartz boundary")); J->WriteObjectEnd();
		J->WriteValue(TEXT("terminal_scope"), TEXT("Quartz command terminal callback, not sound completion; OnAudioFinished can also follow Stop"));
	}
	J->WriteValue(TEXT("timing_scope"), TEXT("native event payloads delivered to game thread; received_seconds is local monotonic receipt time")); J->WriteArrayStart(TEXT("events")); int32 Count = 0; uint64 Next = After;
	for (const auto& E : O->Events) if (E.Sequence > After && Count++ < Limit) { J->WriteObjectStart(); J->WriteValue(TEXT("sequence"), E.Sequence); J->WriteValue(TEXT("kind"), E.Kind); J->WriteValue(TEXT("value"), E.Value); J->WriteValue(TEXT("clock_name"), E.Clock.ToString()); J->WriteValue(TEXT("received_seconds"), E.ReceivedSeconds); if (E.Kind == TEXT("native_command")) J->WriteValue(TEXT("command_name"), E.CommandName.ToString()); if (E.Kind == TEXT("native_metronome")) { J->WriteValue(TEXT("bars"), E.Bars); J->WriteValue(TEXT("beat"), E.Beat); J->WriteValue(TEXT("beat_fraction"), E.BeatFraction); } J->WriteObjectEnd(); Next = E.Sequence; }
	J->WriteArrayEnd(); J->WriteValue(TEXT("next_sequence"), Next); J->WriteObjectEnd(); J->Close(); return Json;
}
