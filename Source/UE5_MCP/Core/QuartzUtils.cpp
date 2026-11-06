#include "QuartzUtils.h"
#include "UE5_MCP/API/DTO/QuartzReq.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Quartz/QuartzSubsystem.h"
#include "Quartz/AudioMixerClock.h"
#include "Serialization/JsonWriter.h"
#include <stdexcept>

namespace
{
	UWorld* World(int32 Instance)
	{
		if (Instance < -1) throw std::runtime_error("PIEInstance must be -1 for automatic selection or a nonnegative integer");
		UWorld* Result = nullptr;
		if (GEngine) for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType != EWorldType::PIE || !Context.World() || (Instance >= 0 && Context.PIEInstance != Instance)) continue;
			if (Result) throw std::runtime_error("Multiple PIE worlds are available; specify PIEInstance");
			Result = Context.World();
		}
		if (!Result) throw std::runtime_error("No matching PIE world; start a play session before using Quartz");
		return Result;
	}
	FName Name(const FString& Value)
	{
		if (Value.IsEmpty() || Value.Len() > 128 || Value != Value.TrimStartAndEnd()) throw std::runtime_error("ClockName must contain 1-128 characters without surrounding whitespace");
		for (TCHAR C : Value) if (!FChar::IsAlnum(C) && C != TEXT('_') && C != TEXT('-')) throw std::runtime_error("ClockName allows letters, numbers, underscores and hyphens");
		FName Result(*Value);
		if (Result.IsNone()) throw std::runtime_error("ClockName cannot be None");
		return Result;
	}
	UQuartzSubsystem* Subsystem(UWorld* W)
	{
		UQuartzSubsystem* S = W->GetSubsystem<UQuartzSubsystem>();
		if (!S) throw std::runtime_error("Quartz subsystem unavailable in the selected PIE world");
		return S;
	}
}

UWorld* QuartzUtils::ResolveWorld(int32 PIEInstance) { return World(PIEInstance); }
FName QuartzUtils::ClockName(const FString& Value) { return Name(Value); }

FString QuartzUtils::Inspect(const FString& ClockName, int32 PIEInstance)
{
	const FName N = Name(ClockName); UWorld* W = World(PIEInstance); UQuartzSubsystem* S = Subsystem(W);
	const Audio::FQuartzClockProxy P = S->GetProxyForClock(N);
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json);
	J->WriteObjectStart(); J->WriteValue(TEXT("clock_name"), N.ToString()); J->WriteValue(TEXT("world_path"), W->GetPathName());
	J->WriteValue(TEXT("runtime_only"), true); J->WriteValue(TEXT("exists"), P.DoesClockExist());
	J->WriteValue(TEXT("state_sampling"), TEXT("last_native_clock_tick"));
	if (P.DoesClockExist())
	{
		J->WriteValue(TEXT("running"), P.IsClockRunning()); J->WriteValue(TEXT("beats_per_minute"), P.GetTickRate().GetBeatsPerMinute());
		J->WriteValue(TEXT("estimated_runtime_seconds"), P.GetEstimatedClockRunTimeSeconds());
		const FQuartzTransportTimeStamp T = P.GetCurrentClockTimestamp();
		J->WriteObjectStart(TEXT("timestamp")); J->WriteValue(TEXT("bars"), T.Bars); J->WriteValue(TEXT("beat"), T.Beat);
		J->WriteValue(TEXT("beat_fraction"), T.BeatFraction); J->WriteValue(TEXT("seconds"), T.Seconds); J->WriteObjectEnd();
		J->WriteObjectStart(TEXT("duration_seconds"));
		// UE 5.7's public getter uses tick-rate constants for Bar/Beat, ignoring the
		// native metronome's time signature. Only publish fixed note durations.
		for (int32 I = static_cast<int32>(EQuartzCommandQuantization::ThirtySecondNote); I < static_cast<int32>(EQuartzCommandQuantization::Count); ++I)
			J->WriteValue(StaticEnum<EQuartzCommandQuantization>()->GetNameStringByValue(I), P.GetDurationOfQuantizationTypeInSeconds(static_cast<EQuartzCommandQuantization>(I), 1.f));
		J->WriteObjectEnd();
		J->WriteValue(TEXT("duration_scope"), TEXT("fixed_note_values; native Bar/Beat getter ignores time signature and is omitted"));
	}
	J->WriteObjectEnd(); J->Close(); return Json;
}

FString QuartzUtils::Control(const FQuartzReq& R)
{
	const FName N = Name(R.ClockName); UWorld* W = World(R.PIEInstance); UQuartzSubsystem* S = Subsystem(W);
	const FString Op = R.Operation.ToLower(); Audio::FQuartzClockProxy P = S->GetProxyForClock(N);
	if (Op != TEXT("create") && Op != TEXT("time_signature") && Op != TEXT("tempo") && Op != TEXT("start") && Op != TEXT("pause") && Op != TEXT("resume") && Op != TEXT("stop") && Op != TEXT("reset") && Op != TEXT("delete"))
		throw std::runtime_error("Operation must be create, time_signature, tempo, start, pause, resume, stop, reset or delete");
	if (Op == TEXT("create") && (P.DoesClockExist() || S->DoesClockExist(W, N))) throw std::runtime_error("Clock already exists; choose another name");
	if (Op != TEXT("create") && !P.DoesClockExist()) throw std::runtime_error("Clock does not exist in the selected PIE world");
	if ((Op == TEXT("create") || Op == TEXT("tempo")) && (!FMath::IsFinite(R.BeatsPerMinute) || R.BeatsPerMinute < 1.f || R.BeatsPerMinute > 1000.f))
		throw std::runtime_error("BeatsPerMinute must be finite and between 1 and 1000");
	FQuartzClockSettings Settings;
	if (Op == TEXT("create") || Op == TEXT("time_signature"))
	{
		if (R.BeatsPerBar < 1 || R.BeatsPerBar > 64) throw std::runtime_error("BeatsPerBar must be between 1 and 64");
		switch (R.BeatDenominator)
		{
		case 2: Settings.TimeSignature.BeatType = EQuartzTimeSignatureQuantization::HalfNote; break;
		case 4: Settings.TimeSignature.BeatType = EQuartzTimeSignatureQuantization::QuarterNote; break;
		case 8: Settings.TimeSignature.BeatType = EQuartzTimeSignatureQuantization::EighthNote; break;
		case 16: Settings.TimeSignature.BeatType = EQuartzTimeSignatureQuantization::SixteenthNote; break;
		case 32: Settings.TimeSignature.BeatType = EQuartzTimeSignatureQuantization::ThirtySecondNote; break;
		default: throw std::runtime_error("BeatDenominator must be 2, 4, 8, 16 or 32");
		}
		Settings.TimeSignature.NumBeats = R.BeatsPerBar; Settings.bIgnoreLevelChange = R.bIgnoreLevelChange;
		if (R.PulseOverrides.Num() > 32) throw std::runtime_error("PulseOverrides are limited to 32 groups");
		Audio::FQuartzClockTickRate Measure; Measure.SetSampleRate(96000); Measure.SetBeatsPerMinute(60);
		double Length = 0; int32 Pulses = 0;
		for (const auto& Group : R.PulseOverrides)
		{
			const int64 Value = StaticEnum<EQuartzCommandQuantization>()->GetValueByNameString(Group.PulseDuration);
			if (Value < static_cast<int64>(EQuartzCommandQuantization::ThirtySecondNote) || Value >= static_cast<int64>(EQuartzCommandQuantization::Count)) throw std::runtime_error("PulseDuration must be a fixed note quantization or Tick; Bar/Beat/None/Count are unsupported");
			if (Group.NumberOfPulses < 1 || Group.NumberOfPulses > 64 || Pulses + Group.NumberOfPulses > 128) throw std::runtime_error("Pulse groups require 1-64 pulses each and at most 128 total");
			FQuartzPulseOverrideStep Step; Step.NumberOfPulses = Group.NumberOfPulses; Step.PulseDuration = static_cast<EQuartzCommandQuantization>(Value);
			Settings.TimeSignature.OptionalPulseOverride.Add(Step); Pulses += Group.NumberOfPulses;
			Length += Group.NumberOfPulses * Measure.GetFramesPerDuration(Step.PulseDuration);
		}
		const double BarLength = R.BeatsPerBar * Measure.GetFramesPerDuration(Settings.TimeSignature.BeatType);
		if (!R.PulseOverrides.IsEmpty() && !FMath::IsNearlyEqual(Length, BarLength, .001)) throw std::runtime_error("PulseOverrides must span exactly one bar of the requested time signature");
	}
	else if (!R.PulseOverrides.IsEmpty()) throw std::runtime_error("PulseOverrides apply only to create or time_signature");
	if (Op == TEXT("delete") && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Deleting a clock requires bConfirm=true");
	bool Queued = false;
	if (!R.bDryRun)
	{
		if (Op == TEXT("create"))
		{
			if (!S->CreateNewClock(W, N, Settings, false, R.bUseAudioEngineClockManager)) throw std::runtime_error("Native Quartz clock creation failed");
			P = S->GetProxyForClock(N);
		}
		if (Op == TEXT("delete")) S->DeleteClockByName(W, N);
		else if (Op == TEXT("create") || Op == TEXT("tempo"))
		{
			const float BPM = R.BeatsPerMinute;
			Queued = P.SendCommandToClock([BPM](Audio::FQuartzClock* Clock) { auto Rate = Clock->GetTickRate(); Rate.SetBeatsPerMinute(BPM); Clock->ChangeTickRate(Rate); });
		}
		else if (Op == TEXT("time_signature"))
		{
			const FQuartzTimeSignature Signature = Settings.TimeSignature;
			// Changing pulse-array length with an old pulse cursor is unsafe in UE 5.7.
			// Reset transport before changing the signature on the owning clock thread.
			Queued = P.SendCommandToClock([Signature](Audio::FQuartzClock* Clock) { Clock->ResetTransport(); Clock->ChangeTimeSignature(Signature); });
		}
		else if (Op == TEXT("start") || Op == TEXT("resume")) Queued = P.SendCommandToClock([](Audio::FQuartzClock* Clock) { Clock->Resume(); });
		else if (Op == TEXT("pause")) Queued = P.SendCommandToClock([](Audio::FQuartzClock* Clock) { Clock->Pause(); });
		// Paused clocks return before refreshing their cached timestamp. Reapplying
		// the unchanged native tick rate refreshes that cache on the owning thread.
		else if (Op == TEXT("reset")) Queued = P.SendCommandToClock([](Audio::FQuartzClock* Clock) { Clock->ResetTransport(); Clock->ChangeTickRate(Clock->GetTickRate()); });
		else if (Op == TEXT("stop")) { const bool Cancel = R.bCancelPendingEvents; Queued = P.SendCommandToClock([Cancel](Audio::FQuartzClock* Clock) { Clock->Stop(Cancel); Clock->ChangeTickRate(Clock->GetTickRate()); }); }
		if (Op != TEXT("delete") && !Queued) throw std::runtime_error("Clock command could not be queued");
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	J->WriteValue(TEXT("clock_name"), N.ToString()); J->WriteValue(TEXT("operation"), Op); J->WriteValue(TEXT("dry_run"), R.bDryRun);
	J->WriteValue(TEXT("runtime_only"), true); J->WriteValue(TEXT("command_queued"), Queued);
	if (Op == TEXT("create") || Op == TEXT("time_signature"))
	{
		J->WriteObjectStart(TEXT("requested_time_signature")); J->WriteValue(TEXT("beats_per_bar"), R.BeatsPerBar); J->WriteValue(TEXT("beat_denominator"), R.BeatDenominator);
		J->WriteArrayStart(TEXT("pulse_overrides")); for (const auto& Step : Settings.TimeSignature.OptionalPulseOverride) { J->WriteObjectStart(); J->WriteValue(TEXT("number_of_pulses"), Step.NumberOfPulses); J->WriteValue(TEXT("pulse_duration"), StaticEnum<EQuartzCommandQuantization>()->GetNameStringByValue(static_cast<int64>(Step.PulseDuration))); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd();
		J->WriteValue(TEXT("transport_reset_submitted"), Op == TEXT("time_signature") && !R.bDryRun);
		J->WriteValue(TEXT("settings_scope"), TEXT("requested settings; native transport confirms effect; public API has no time-signature getter"));
	}
	J->WriteValue(TEXT("execution"), TEXT("next_native_clock_tick; inspect to observe completion")); J->WriteObjectEnd(); J->Close(); return Json;
}
