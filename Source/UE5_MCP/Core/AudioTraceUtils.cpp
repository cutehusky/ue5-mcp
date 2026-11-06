#include "AudioTraceUtils.h"
#include "QuartzUtils.h"
#include "UE5_MCP/API/DTO/AudioTraceReq.h"
#include "Containers/Ticker.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "Misc/ScopeLock.h"
#include "ProfilingDebugging/TraceAuxiliary.h"
#include "Serialization/JsonWriter.h"
#include "Trace/Trace.h"
#include <stdexcept>

namespace
{
	struct FChannel { FString Name; uint32 Id = 0; bool Enabled = false, ReadOnly = false; };
	struct FCapture
	{
		FString Id, Path, WorldPath, State = TEXT("connecting"), Reason;
		TWeakObjectPtr<UWorld> World;
		FGuid Guid;
		TArray<FChannel> Channels;
		TArray<uint32> Added;
		double Started = 0, Duration = 0;
		int64 SoftBytes = 0;
		uint64 Connections = 0, Stops = 0;
		bool StopSent = false;
	};
	struct FSignals { uint64 Connections = 0, Stops = 0; FGuid Guid; } Signals;
	FCriticalSection SignalLock;
	TMap<FString, TUniquePtr<FCapture>> Captures;
	FString Active;
	FTSTicker::FDelegateHandle Ticker;
	FDelegateHandle ConnectionHook, StopHook, CleanupHook;
	const TArray<FString> Allowed = {TEXT("audio"), TEXT("audiomixer"), TEXT("cpu"), TEXT("frame"), TEXT("bookmark")};
	FString Key(FString Name) { Name.RemoveFromEnd(TEXT("Channel")); return Name.ToLower(); }
	TMap<FString, FChannel> Channels()
	{
		TMap<FString,FChannel> Result;
		UE::Trace::EnumerateChannels([](const UE::Trace::FChannelInfo& Info, void* User)
		{
			const FString Name = UTF8_TO_TCHAR(Info.Name); const FString K = Key(Name);
			if (Allowed.Contains(K)) static_cast<TMap<FString,FChannel>*>(User)->Add(K, {Name,Info.Id,Info.bIsEnabled,Info.bIsReadOnly});
			return true;
		}, &Result);
		return Result;
	}
	FSignals ReadSignals() { FScopeLock Lock(&SignalLock); return Signals; }
	void Connected()
	{
		FGuid Session, Trace; if (!FTraceAuxiliary::IsConnected(Session, Trace)) return;
		FScopeLock Lock(&SignalLock); ++Signals.Connections; Signals.Guid = Trace;
	}
	void Stopped(FTraceAuxiliary::EConnectionType, const FString&) { FScopeLock Lock(&SignalLock); ++Signals.Stops; }
	void Finish(FCapture& C, const FString& State, bool Restore)
	{
		C.State = State;
		if (Restore && !C.Added.IsEmpty()) FTraceAuxiliary::DisableChannels(C.Added);
		Active.Reset();
	}
	bool Tick(float)
	{
		if (Active.IsEmpty()) return true;
		auto& C = *Captures[Active]; const auto S = ReadSignals(); FGuid Session, Current;
		if (!FTraceAuxiliary::IsConnected(Session, Current)) { if (C.Reason.IsEmpty()) C.Reason = TEXT("native_connection_ended"); Finish(C, TEXT("completed"), true); return true; }
		if (!C.Guid.IsValid())
		{
			if (S.Connections > C.Connections + 1 || S.Stops > C.Stops) { C.Reason = TEXT("connection_replaced_before_ownership_confirmation"); Finish(C, TEXT("ownership_lost"), false); return true; }
			if (S.Connections != C.Connections + 1) return true;
			C.Guid = S.Guid;
		}
		if (Current != C.Guid) { C.Reason = TEXT("native_connection_replaced"); Finish(C, TEXT("ownership_lost"), false); return true; }
		if (!C.StopSent && !FPaths::IsSamePath(FTraceAuxiliary::GetTraceDestinationString(), C.Path))
		{
			if (S.Stops > C.Stops) { C.StopSent = true; C.Reason = TEXT("external_stop"); }
			else { C.Reason = TEXT("native_destination_changed"); Finish(C, TEXT("ownership_lost"), false); return true; }
		}
		if (!C.StopSent)
		{
			C.State = TEXT("recording");
			if (C.Reason.IsEmpty() && FPlatformTime::Seconds() - C.Started >= C.Duration) C.Reason = TEXT("duration_limit");
			if (C.Reason.IsEmpty() && IFileManager::Get().FileSize(*C.Path) >= C.SoftBytes) C.Reason = TEXT("soft_size_limit");
			if (!C.Reason.IsEmpty()) C.StopSent = FTraceAuxiliary::Stop();
		}
		if (C.StopSent) C.State = TEXT("stopping");
		return true;
	}
	void Cleanup(UWorld* W, bool, bool)
	{
		if (!Active.IsEmpty()) { auto& C = *Captures[Active]; if (C.World == TWeakObjectPtr<UWorld>(W) && C.Reason.IsEmpty()) C.Reason = TEXT("world_cleanup"); }
	}
	void Ensure()
	{
		if (!ConnectionHook.IsValid()) ConnectionHook = FTraceAuxiliary::OnConnection.AddStatic(&Connected);
		if (!StopHook.IsValid()) StopHook = FTraceAuxiliary::OnTraceStopped.AddStatic(&Stopped);
		if (!CleanupHook.IsValid()) CleanupHook = FWorldDelegates::OnWorldCleanup.AddStatic(&Cleanup);
		if (!Ticker.IsValid()) Ticker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick));
	}
	void Id(const FString& V)
	{
		if (V.IsEmpty() || V.Len() > 64) throw std::runtime_error("CaptureId requires 1-64 characters");
		for (TCHAR C : V) if (!FChar::IsAlnum(C) && C != '_' && C != '-') throw std::runtime_error("CaptureId allows letters, numbers, underscores and hyphens");
	}
}

void AudioTraceUtils::Shutdown()
{
	Tick(0);
	if (!Active.IsEmpty())
	{
		auto& C = *Captures[Active]; FGuid Session, Current;
		if (C.Guid.IsValid() && FTraceAuxiliary::IsConnected(Session, Current) && Current == C.Guid)
		{
			if (!C.StopSent && FPaths::IsSamePath(FTraceAuxiliary::GetTraceDestinationString(), C.Path)) C.StopSent = FTraceAuxiliary::Stop();
			if (C.StopSent && !C.Added.IsEmpty()) FTraceAuxiliary::DisableChannels(C.Added);
		}
	}
	if (Ticker.IsValid()) { FTSTicker::RemoveTicker(Ticker); Ticker.Reset(); }
	if (ConnectionHook.IsValid()) { FTraceAuxiliary::OnConnection.Remove(ConnectionHook); ConnectionHook.Reset(); }
	if (StopHook.IsValid()) { FTraceAuxiliary::OnTraceStopped.Remove(StopHook); StopHook.Reset(); }
	if (CleanupHook.IsValid()) { FWorldDelegates::OnWorldCleanup.Remove(CleanupHook); CleanupHook.Reset(); }
	Captures.Reset(); Active.Reset();
}

FString AudioTraceUtils::Control(const FAudioTraceReq& R)
{
	Id(R.CaptureId); Tick(0); const FString Op = R.Operation.ToLower(); auto* Existing = Captures.Find(R.CaptureId);
	if (Op == TEXT("start"))
	{
		auto* W = QuartzUtils::ResolveWorld(R.PIEInstance);
		if (Existing || Captures.Num() >= 16) throw std::runtime_error("CaptureId exists or 16 retained trace records reached; release completed records");
		if (!Active.IsEmpty() || FTraceAuxiliary::IsConnected() || FTraceAuxiliary::IsPaused()) throw std::runtime_error("A native trace is already active or paused; existing sessions are not replaced");
		if (!FMath::IsFinite(R.DurationSeconds) || R.DurationSeconds < .1f || R.DurationSeconds > 60 || R.MaxFileMB < 1 || R.MaxFileMB > 256) throw std::runtime_error("DurationSeconds requires [0.1,60] and MaxFileMB [1,256]");
		const FString Root = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("Profiling/UE5MCP"));
		const FString Path = Root / (TEXT("Audio_") + R.CaptureId + TEXT(".utrace"));
		if (IFileManager::Get().FileExists(*Path)) throw std::runtime_error("Trace output already exists; choose a new CaptureId");
		auto Available = Channels(); TArray<FString> Wanted = R.Channels;
		if (Wanted.IsEmpty()) Wanted = {TEXT("audio"),TEXT("audiomixer"),TEXT("cpu"),TEXT("frame"),TEXT("bookmark")};
		if (Wanted.Num() > 5) throw std::runtime_error("At most five profiling channels are supported");
		auto C = MakeUnique<FCapture>(); TSet<FString> Seen;
		for (const auto& Name : Wanted)
		{
			const FString K = Key(Name); const auto* Channel = Available.Find(K);
			if (!Channel || Seen.Contains(K) || (Channel->ReadOnly && !Channel->Enabled)) throw std::runtime_error("Requested channel is unavailable, duplicate or read-only-disabled; inspect channel capabilities");
			Seen.Add(K); C->Channels.Add(*Channel); if (!Channel->Enabled) C->Added.Add(Channel->Id);
		}
		if (!R.bDryRun)
		{
			Ensure(); const auto S = ReadSignals(); C->Connections = S.Connections; C->Stops = S.Stops;
			if (!IFileManager::Get().MakeDirectory(*Root, true)) throw std::runtime_error("Could not create project trace directory");
			TMap<uint32,FString> Errors; FTraceAuxiliary::EnableChannels(C->Added, &Errors);
			if (!Errors.IsEmpty()) { FTraceAuxiliary::DisableChannels(C->Added); throw std::runtime_error("Native profiling channels could not be enabled"); }
			FTraceAuxiliary::FOptions Options; Options.bExcludeTail = true;
			if (!FTraceAuxiliary::Start(FTraceAuxiliary::EConnectionType::File, *Path, nullptr, &Options)) { FTraceAuxiliary::DisableChannels(C->Added); throw std::runtime_error("Native file trace could not start"); }
			C->Id = R.CaptureId; C->Path = Path; C->World = W; C->WorldPath = W->GetPathName(); C->Started = FPlatformTime::Seconds(); C->Duration = R.DurationSeconds; C->SoftBytes = int64(R.MaxFileMB) * 1024 * 1024;
			Captures.Add(R.CaptureId, MoveTemp(C)); Active = R.CaptureId;
		}
	}
	else if (Op == TEXT("stop") || Op == TEXT("release"))
	{
		if (!Existing) throw std::runtime_error("CaptureId is not owned by this adapter");
		if (Op == TEXT("release") && Active == R.CaptureId) throw std::runtime_error("Stop and await native trace completion before releasing its record");
		if (!R.bDryRun) { if (Op == TEXT("release")) Captures.Remove(R.CaptureId); else if (Active == R.CaptureId && (*Existing)->Reason.IsEmpty()) { (*Existing)->Reason = TEXT("manual_stop"); Tick(0); } }
	}
	else throw std::runtime_error("Trace operation must be start, stop or release");
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("capture_id"), R.CaptureId); J->WriteValue(TEXT("operation"), Op); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("submitted"), !R.bDryRun); J->WriteObjectEnd(); J->Close(); return Json;
}

FString AudioTraceUtils::Inspect(const FString& IdValue)
{
	Tick(0); const auto Available = Channels(); FGuid Session, Guid; const bool Connected = FTraceAuxiliary::IsConnected(Session, Guid);
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("native_connected"), Connected); J->WriteValue(TEXT("native_destination"), FTraceAuxiliary::GetTraceDestinationString()); J->WriteValue(TEXT("owned_active_id"), Active);
	J->WriteValue(TEXT("scope"), TEXT("process-wide native Unreal trace; audio/mixer channels plus optional CPU/frame/bookmark data; inspect .utrace in Unreal Insights"));
	J->WriteArrayStart(TEXT("available_channels")); for (const auto& Pair : Available) { const auto& C = Pair.Value; J->WriteObjectStart(); J->WriteValue(TEXT("name"), Key(C.Name)); J->WriteValue(TEXT("enabled"), C.Enabled); J->WriteValue(TEXT("read_only"), C.ReadOnly); J->WriteObjectEnd(); } J->WriteArrayEnd();
	if (!IdValue.IsEmpty())
	{
		Id(IdValue); const auto* Found = Captures.Find(IdValue); if (!Found) throw std::runtime_error("Trace record does not exist"); const auto& C = **Found;
		J->WriteValue(TEXT("capture_id"), C.Id); J->WriteValue(TEXT("state"), C.State); J->WriteValue(TEXT("stop_reason"), C.Reason); J->WriteValue(TEXT("path"), C.Path); J->WriteValue(TEXT("requested_world_path"), C.WorldPath);
		J->WriteValue(TEXT("trace_guid"), C.Guid.ToString(EGuidFormats::Digits)); J->WriteValue(TEXT("duration_seconds"), C.Duration); J->WriteValue(TEXT("soft_size_limit_bytes"), C.SoftBytes); J->WriteValue(TEXT("file_size_bytes"), IFileManager::Get().FileSize(*C.Path));
		J->WriteValue(TEXT("size_scope"), TEXT("soft stop threshold; native buffering and asynchronous close can overshoot"));
		J->WriteArrayStart(TEXT("requested_channels")); for (const auto& Cn : C.Channels) J->WriteValue(Key(Cn.Name)); J->WriteArrayEnd();
	}
	J->WriteObjectEnd(); J->Close(); return Json;
}
