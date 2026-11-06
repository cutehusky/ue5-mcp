#include "GitReadUtils.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformTime.h"
#include "ISourceControlProvider.h"
#include "ISourceControlRevision.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "SourceControlHelpers.h"

namespace
{
	FString Text(const TArray<uint8>& Bytes)
	{
		FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Bytes.GetData()), Bytes.Num());
		return FString(Converted.Length(), Converted.Get());
	}

	FString Arg(const FString& Value)
	{
		return TEXT("\"") + Value.Replace(TEXT("\\"), TEXT("/")).Replace(TEXT("\""), TEXT("\\\"")) + TEXT("\"");
	}
	bool Hash(const FString& Value)
	{
		if (Value.Len() != 40 && Value.Len() != 64) return false;
		for (const TCHAR Character : Value) if (!FChar::IsHexDigit(Character)) return false;
		return true;
	}

	bool Run(const FString& Binary, const FString& Repository, const FString& Arguments,
		TArray<uint8>& Output, TArray<FString>& Errors, const FString& Input = TEXT(""), int64 Limit = 16 * 1024 * 1024)
	{
		void *ReadOut = nullptr, *WriteOut = nullptr, *ReadErr = nullptr, *WriteErr = nullptr;
		void *ReadIn = nullptr, *WriteIn = nullptr;
		if (!FPlatformProcess::CreatePipe(ReadOut, WriteOut) || !FPlatformProcess::CreatePipe(ReadErr, WriteErr)
			|| (!Input.IsEmpty() && !FPlatformProcess::CreatePipe(ReadIn, WriteIn, true)))
		{
			FPlatformProcess::ClosePipe(ReadOut, WriteOut); FPlatformProcess::ClosePipe(ReadErr, WriteErr);
			FPlatformProcess::ClosePipe(ReadIn, WriteIn);
			Errors.Add(TEXT("Could not create Git metadata pipes")); return false;
		}
		FProcHandle Process = FPlatformProcess::CreateProc(*Binary, *Arguments, false, true, true,
			nullptr, 0, *Repository, WriteOut, ReadIn, WriteErr);
		if (Process.IsValid() && WriteIn)
		{
			FPlatformProcess::WritePipe(WriteIn, Input);
			FPlatformProcess::ClosePipe(nullptr, WriteIn); WriteIn = nullptr;
		}
		TArray<uint8> ErrorBytes;
		bool bBoundExceeded = false;
		const double Started = FPlatformTime::Seconds();
		auto Drain = [&]()
		{
			TArray<uint8> Chunk;
			while (FPlatformProcess::ReadPipeToArray(ReadOut, Chunk))
			{
				Output.Append(Chunk); Chunk.Reset();
				if (Output.Num() > Limit) { bBoundExceeded = true; break; }
			}
			while (FPlatformProcess::ReadPipeToArray(ReadErr, Chunk))
			{
				ErrorBytes.Append(Chunk); Chunk.Reset();
				if (ErrorBytes.Num() > 1024 * 1024) { bBoundExceeded = true; break; }
			}
		};
		if (Process.IsValid())
		{
			while (FPlatformProcess::IsProcRunning(Process))
			{
				Drain();
				if (bBoundExceeded || FPlatformTime::Seconds() - Started > 30.0)
				{
					bBoundExceeded = true; FPlatformProcess::TerminateProc(Process, true); break;
				}
				FPlatformProcess::Sleep(0.002f);
			}
			FPlatformProcess::WaitForProc(Process); Drain();
		}
		int32 Code = -1;
		if (Process.IsValid()) { FPlatformProcess::GetProcReturnCode(Process, &Code); FPlatformProcess::CloseProc(Process); }
		FPlatformProcess::ClosePipe(ReadOut, WriteOut); FPlatformProcess::ClosePipe(ReadErr, WriteErr);
		FPlatformProcess::ClosePipe(ReadIn, WriteIn);
		if (bBoundExceeded) Errors.Add(TEXT("Git read exceeded its time or output bound"));
		else if (Code != 0) Errors.Add(ErrorBytes.IsEmpty() ? TEXT("Git read failed") : Text(ErrorBytes).Left(8192));
		return Code == 0 && !bBoundExceeded;
	}

	class FReadRevision final : public ISourceControlRevision
	{
	public:
		FString Binary, Repository, Commit, Blob, Filename, Description, User, Action;
		FDateTime Date;
		int32 Number = 0, Size = 0;
		virtual bool Get(FString& Output, EConcurrency::Type) const override
		{
			if (Action == TEXT("delete")) return false;
			TArray<uint8> Bytes; TArray<FString> Errors;
			if (!Run(Binary, Repository, TEXT("--no-pager -C ") + Arg(Repository) + TEXT(" cat-file blob ") + Arg(Blob), Bytes, Errors,
				TEXT(""), 256LL * 1024 * 1024)) return false;
			if (Output.IsEmpty()) Output = FPaths::CreateTempFilename(*FPaths::ProjectSavedDir(), TEXT("UE5MCP_Git_"));
			return FFileHelper::SaveArrayToFile(Bytes, *Output);
		}
		virtual bool GetAnnotated(TArray<FAnnotationLine>&) const override { return false; }
		virtual bool GetAnnotated(FString&) const override { return false; }
		virtual const FString& GetFilename() const override { return Filename; }
		virtual int32 GetRevisionNumber() const override { return Number; }
		virtual const FString& GetRevision() const override { return Commit; }
		virtual const FString& GetDescription() const override { return Description; }
		virtual const FString& GetUserName() const override { return User; }
		virtual const FString& GetClientSpec() const override { static FString Empty; return Empty; }
		virtual const FString& GetAction() const override { return Action; }
		virtual TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe> GetBranchSource() const override { return nullptr; }
		virtual const FDateTime& GetDate() const override { return Date; }
		virtual int32 GetCheckInIdentifier() const override { return 0; }
		virtual int32 GetFileSize() const override { return Size; }
	};
}

bool GitReadUtils::History(ISourceControlProvider& Provider, const FString& Filename,
	TArray<TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe>>& Revisions, TArray<FString>& Errors)
{
	const TMap<ISourceControlProvider::EStatus, FString> Status = Provider.GetStatus();
	const FString* RepositoryValue = Status.Find(ISourceControlProvider::EStatus::Repository);
	FString Binary;
	GConfig->GetString(TEXT("GitSourceControl.GitSourceControlSettings"), TEXT("BinaryPath"), Binary, USourceControlHelpers::GetSettingsIni());
	if (Binary.IsEmpty() || !IFileManager::Get().FileExists(*Binary) || !RepositoryValue || RepositoryValue->IsEmpty())
	{
		Errors.Add(TEXT("Missing-file Git reads require a configured Git binary and repository")); return false;
	}
	FString Repository = FPaths::ConvertRelativePathToFull(*RepositoryValue);
	FPaths::NormalizeDirectoryName(Repository);
	FString Relative = Filename;
	if (!FPaths::MakePathRelativeTo(Relative, *(Repository + TEXT("/"))) || Relative.StartsWith(TEXT("../")))
	{
		Errors.Add(TEXT("Selected file is outside the configured Git repository")); return false;
	}
	TArray<uint8> Bytes;
	if (!Run(Binary, Repository, TEXT("--no-pager -C ") + Arg(Repository) +
		TEXT(" -c i18n.logOutputEncoding=UTF-8 log --follow --max-count=256 --format=%H%x00%an%x00%aI%x00%B%x00 --raw --no-abbrev -z -- ") + Arg(Relative), Bytes, Errors)) return false;
	TArray<FString> Tokens;
	int32 Start = 0;
	for (int32 Index = 0; Index < Bytes.Num(); ++Index)
		if (Bytes[Index] == 0)
		{
			FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Bytes.GetData() + Start), Index - Start);
			Tokens.Emplace(Converted.Length(), Converted.Get()); Start = Index + 1;
		}
	TArray<TSharedPtr<FReadRevision, ESPMode::ThreadSafe>> Parsed;
	int32 Index = 0;
	while (Index < Tokens.Num())
	{
		while (Index < Tokens.Num() && Tokens[Index].TrimStartAndEnd().IsEmpty()) ++Index;
		if (Index + 4 >= Tokens.Num()) break;
		TSharedPtr<FReadRevision, ESPMode::ThreadSafe> Revision = MakeShared<FReadRevision, ESPMode::ThreadSafe>();
		Revision->Binary = Binary; Revision->Repository = Repository;
		Revision->Commit = Tokens[Index++].TrimStartAndEnd(); Revision->User = Tokens[Index++];
		FDateTime::ParseIso8601(*Tokens[Index++], Revision->Date); Revision->Description = Tokens[Index++];
		while (Index < Tokens.Num() && Tokens[Index].TrimStartAndEnd().IsEmpty()) ++Index;
		if (Index + 1 >= Tokens.Num()) break;
		TArray<FString> Raw;
		Tokens[Index++].TrimStartAndEnd().ParseIntoArrayWS(Raw);
		if (Raw.Num() != 5 || !Raw[0].StartsWith(TEXT(":"))) { Errors.Add(TEXT("Unexpected Git history record")); return false; }
		Revision->Blob = Raw[3];
		if (!Hash(Revision->Commit) || !Hash(Revision->Blob)) { Errors.Add(TEXT("Unexpected Git object identifier")); return false; }
		const TCHAR Code = Raw[4].IsEmpty() ? TCHAR('M') : Raw[4][0];
		Revision->Filename = Tokens[Index++];
		if ((Code == TCHAR('R') || Code == TCHAR('C')) && Index < Tokens.Num()) Revision->Filename = Tokens[Index++];
		Revision->Action = Code == TCHAR('D') ? TEXT("delete") : Code == TCHAR('A') ? TEXT("add") :
			Code == TCHAR('R') || Code == TCHAR('C') ? TEXT("branch") : TEXT("edit");
		Parsed.Add(Revision);
	}
	TArray<FString> Blobs;
	for (const auto& Revision : Parsed) if (Revision->Action != TEXT("delete")) Blobs.AddUnique(Revision->Blob);
	TMap<FString, int32> Sizes;
	for (int32 Offset = 0; Offset < Blobs.Num(); Offset += 32)
	{
		// Keep stdin/output batches below the anonymous pipe buffer size.
		FString BlobInput;
		for (int32 BlobIndex = Offset; BlobIndex < FMath::Min(Offset + 32, Blobs.Num()); ++BlobIndex) BlobInput += Blobs[BlobIndex] + TEXT("\n");
		Bytes.Reset();
		if (!Run(Binary, Repository, TEXT("--no-pager -C ") + Arg(Repository) +
			TEXT(" cat-file --batch-check=\"%(objectname) %(objectsize)\""), Bytes, Errors, BlobInput)) return false;
		TArray<FString> Lines; Text(Bytes).ParseIntoArrayLines(Lines);
		for (const FString& Line : Lines)
		{
			TArray<FString> Fields; Line.ParseIntoArrayWS(Fields);
			int64 Size = 0;
			if (Fields.Num() == 2 && LexTryParseString(Size, *Fields[1])) Sizes.Add(Fields[0], static_cast<int32>(FMath::Min<int64>(Size, MAX_int32)));
		}
	}
	for (auto& Revision : Parsed)
		if (Revision->Action != TEXT("delete"))
		{
			const int32* Size = Sizes.Find(Revision->Blob);
			if (!Size) { Errors.Add(TEXT("Could not read committed Git blob size")); return false; }
			Revision->Size = *Size;
		}
	for (int32 Item = 0; Item < Parsed.Num(); ++Item) { Parsed[Item]->Number = Parsed.Num() - Item; Revisions.Add(Parsed[Item]); }
	return true;
}
