#include "SourceControlUtils.h"
#include "GitReadUtils.h"

#include "UE5_MCP/API/DTO/SourceControlReq.h"
#include "Editor.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "GenericPlatform/GenericPlatformFile.h"
#include "ISourceControlModule.h"
#include "ISourceControlProvider.h"
#include "ISourceControlState.h"
#include "ISourceControlRevision.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Serialization/JsonWriter.h"
#include "SourceControlHelpers.h"
#include "SourceControlOperations.h"
#include "SourceControlPreferences.h"
#include "UObject/Package.h"

#include <stdexcept>

namespace
{
	struct FEntry
	{
		FString AssetPath;
		FString PackageName;
		FString Filename;
		FString RequestedFilePath;
		bool bDirty = false;
		bool bEligible = false;
		FString Reason;
		FSourceControlStatePtr State;
		TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe> RestoreRevision;
		TArray<TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe>> FallbackHistory;
		bool bFallbackHistory = false;
		FString Label() const { return PackageName.IsEmpty() ? RequestedFilePath : PackageName; }
	};

	FSourceControlOperationRef MakeOperation(const FString& Name, const FString& Description)
	{
		if (Name == TEXT("checkout")) return ISourceControlOperation::Create<FCheckOut>();
		if (Name == TEXT("add")) return ISourceControlOperation::Create<FMarkForAdd>();
		if (Name == TEXT("revert")) return ISourceControlOperation::Create<FRevert>();
		if (Name == TEXT("submit"))
		{
			TSharedRef<FCheckIn, ESPMode::ThreadSafe> CheckIn = ISourceControlOperation::Create<FCheckIn>();
			CheckIn->SetDescription(FText::FromString(Description));
			return CheckIn;
		}
		TSharedRef<FUpdateStatus, ESPMode::ThreadSafe> Update = ISourceControlOperation::Create<FUpdateStatus>();
		Update->SetUpdateModifiedState(true);
		Update->SetQuiet(true);
		return Update;
	}

	void WriteProvider(const TSharedRef<TJsonWriter<>>& Writer, ISourceControlModule& Module)
	{
		ISourceControlProvider& Provider = Module.GetProvider();
		Writer->WriteValue(TEXT("provider"), Provider.GetName().ToString());
		Writer->WriteValue(TEXT("enabled"), Module.IsEnabled());
		Writer->WriteValue(TEXT("available"), Module.IsEnabled() && Provider.IsAvailable());
		Writer->WriteValue(TEXT("status"), Provider.GetStatusText().ToString());
		Writer->WriteValue(TEXT("uses_checkout"), Provider.UsesCheckout());
		Writer->WriteValue(TEXT("uses_file_revisions"), Provider.UsesFileRevisions());
	}

	FString CheckedProjectFile(const FString& Input)
	{
		FString Root = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
		FPaths::NormalizeDirectoryName(Root);
		FString Filename = FPaths::ConvertRelativePathToFull(Root, Input.TrimStartAndEnd());
		FPaths::NormalizeFilename(Filename);
		if (!FPaths::CollapseRelativeDirectories(Filename) || !Filename.StartsWith(Root + TEXT("/"), ESearchCase::IgnoreCase))
			throw std::runtime_error("file_paths must stay inside the running project's directory");
		FString Relative = Filename.Mid(Root.Len() + 1);
		TArray<FString> Parts;
		Relative.ParseIntoArray(Parts, TEXT("/"), true);
		if (Parts.IsEmpty()) throw std::runtime_error("file_paths must identify individual project files");
		for (const FString& Part : Parts)
			if (Part.Equals(TEXT(".git"), ESearchCase::IgnoreCase) || Part.Equals(TEXT("Saved"), ESearchCase::IgnoreCase)
				|| Part.Equals(TEXT("Intermediate"), ESearchCase::IgnoreCase) || Part.Equals(TEXT("Binaries"), ESearchCase::IgnoreCase)
				|| Part.Equals(TEXT("DerivedDataCache"), ESearchCase::IgnoreCase) || Part.Contains(TEXT(":")) || Part.Contains(TEXT("\"")))
				throw std::runtime_error("Git metadata and alternate file streams are outside the source-control route scope");
		const FString First = Parts[0].ToLower();
		if (Parts.Num() > 1 && First != TEXT("content") && First != TEXT("config") && First != TEXT("source")
			&& First != TEXT("plugins") && First != TEXT("build"))
			throw std::runtime_error("file_paths must be project root files or files in Content, Config, Source, Plugins, or Build");
		const FString Extension = FPaths::GetExtension(Filename).ToLower();
		const TSet<FString> Allowed = {TEXT("uasset"), TEXT("umap"), TEXT("uproject"), TEXT("uplugin"), TEXT("ini"),
			TEXT("cpp"), TEXT("h"), TEXT("hpp"), TEXT("c"), TEXT("inl"), TEXT("cs"), TEXT("py"), TEXT("json"),
			TEXT("md"), TEXT("txt"), TEXT("toml"), TEXT("yaml"), TEXT("yml"), TEXT("xml"), TEXT("png"), TEXT("jpg"),
			TEXT("jpeg"), TEXT("tga"), TEXT("exr"), TEXT("wav"), TEXT("fbx"), TEXT("obj"), TEXT("gltf"), TEXT("glb")};
		if (!Allowed.Contains(Extension) && FPaths::GetCleanFilename(Filename) != TEXT(".gitignore")
			&& FPaths::GetCleanFilename(Filename) != TEXT(".gitattributes"))
			throw std::runtime_error("file_paths must identify a supported project asset, source, config, or text file");
		IPlatformFile& Physical = FPlatformFileManager::Get().GetPlatformPhysical();
		FString Segment = Root;
		for (const FString& Part : Parts)
		{
			Segment += TEXT("/") + Part;
			if (Physical.IsSymlink(*Segment) != ESymlinkResult::NonSymlink)
				throw std::runtime_error("Source-control file paths must not traverse symlinks, junctions, or unverified link types");
		}
		if (Physical.DirectoryExists(*Filename)) throw std::runtime_error("Source-control file paths must identify individual files, not directories");
		return Filename;
	}

	TArray<FEntry> Resolve(const FSourceControlReq& Request)
	{
		if (Request.AssetPaths.Num() + Request.FilePaths.Num() < 1 || Request.AssetPaths.Num() + Request.FilePaths.Num() > 64)
			throw std::runtime_error("asset_paths and file_paths must identify 1-64 individual project files");
		TArray<FEntry> Entries;
		TSet<FString> Filenames;
		auto AddEntry = [&Entries, &Filenames](const FString& AssetPath, const FString& FilePath, const FString& Package, const FString& Filename)
		{
			if (Filenames.Contains(Filename.ToLower())) return;
			Filenames.Add(Filename.ToLower());
			FEntry& Entry = Entries.AddDefaulted_GetRef();
			Entry.AssetPath = AssetPath;
			Entry.RequestedFilePath = FilePath;
			Entry.PackageName = Package;
			Entry.Filename = Filename;
			if (!Package.IsEmpty()) if (const UPackage* Loaded = FindPackage(nullptr, *Package)) Entry.bDirty = Loaded->IsDirty();
		};
		for (const FString& Path : Request.AssetPaths)
		{
			const FString Package = FPackageName::ObjectPathToPackageName(Path.TrimStartAndEnd());
			if (!Package.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(Package))
				throw std::runtime_error("Source control requests are restricted to valid /Game asset/package paths");
			FString Filename;
			if (!FPackageName::DoesPackageExist(Package, &Filename))
				throw std::runtime_error("asset_paths requires a saved package; use file_paths with its .uasset or .umap filename for deleted packages");
			AddEntry(Path, TEXT(""), Package, CheckedProjectFile(FPaths::ConvertRelativePathToFull(Filename)));
		}
		for (const FString& Path : Request.FilePaths)
		{
			const FString Filename = CheckedProjectFile(Path);
			FString Package;
			const FString Extension = FPaths::GetExtension(Filename).ToLower();
			if (Extension == TEXT("uasset") || Extension == TEXT("umap"))
				if (!FPackageName::TryConvertFilenameToLongPackageName(Filename, Package))
					throw std::runtime_error("Package file_paths must be under a mounted project content directory");
			AddEntry(TEXT(""), Path, Package, Filename);
		}
		return Entries;
	}

	bool Eligible(const FSourceControlStatePtr& State, const FString& Operation)
	{
		if (!State.IsValid() || State->IsUnknown()) return false;
		if (Operation == TEXT("checkout")) return State->CanCheckout();
		if (Operation == TEXT("add")) return State->CanAdd();
		if (Operation == TEXT("revert")) return State->CanRevert();
		if (Operation == TEXT("submit")) return State->CanCheckIn() && !State->IsConflicted() && State->IsCurrent();
		return true;
	}

	bool RestoreMissingGitFiles(const TArray<FEntry>& Entries, TArray<FString>& Errors, TArray<FString>& Restored)
	{
		for (const FEntry& Entry : Entries)
		{
			if (!Entry.RestoreRevision.IsValid() || IFileManager::Get().FileExists(*Entry.Filename)) continue;
			FString Temporary = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()) +
				TEXT("/UE5MCP_SC_Restore_") + FGuid::NewGuid().ToString(EGuidFormats::Digits) + TEXT(".") + FPaths::GetExtension(Entry.Filename);
			bool bRestored = false;
			try
			{
				CheckedProjectFile(Entry.Filename);
				if (Entry.RestoreRevision->Get(Temporary))
				{
					CheckedProjectFile(Entry.Filename);
					IFileManager::Get().MakeDirectory(*FPaths::GetPath(Entry.Filename), true);
					bRestored = IFileManager::Get().Copy(*Entry.Filename, *Temporary, false) == COPY_OK;
				}
			}
			catch (const std::exception& Error) { Errors.Add(UTF8_TO_TCHAR(Error.what())); }
			IFileManager::Get().Delete(*Temporary);
			if (!bRestored)
			{
				Errors.Add(Entry.Label() + TEXT(": failed to restore missing file from its committed revision"));
				return false;
			}
			Restored.Add(Entry.Filename);
		}
		return true;
	}
}

FString SourceControlUtils::ProviderJson()
{
	ISourceControlModule& Module = ISourceControlModule::Get();
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	WriteProvider(Writer, Module);
	TArray<FName> Names;
	Module.GetProviderNames(Names);
	Writer->WriteArrayStart(TEXT("registered_providers"));
	for (const FName Name : Names) Writer->WriteValue(Name.ToString());
	Writer->WriteArrayEnd();
	Writer->WriteObjectStart(TEXT("operations"));
	for (const FString& Name : {FString(TEXT("status")), FString(TEXT("checkout")), FString(TEXT("add")), FString(TEXT("revert")), FString(TEXT("submit"))})
		Writer->WriteValue(Name, Module.IsEnabled() && Module.GetProvider().IsAvailable() &&
			Module.GetProvider().CanExecuteOperation(MakeOperation(Name, TEXT(""))));
	Writer->WriteValue(TEXT("history"), Module.IsEnabled() && Module.GetProvider().IsAvailable() &&
		Module.GetProvider().CanExecuteOperation(MakeOperation(TEXT("status"), TEXT(""))));
	Writer->WriteObjectEnd();
	Writer->WriteValue(TEXT("scope"), TEXT("/Game assets and selected project content/config/source files, including missing files"));
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString SourceControlUtils::HistoryJson(const FSourceControlReq& Request)
{
	if (Request.AssetPaths.Num() + Request.FilePaths.Num() > 16 || Request.MaxHistory < 1 || Request.MaxHistory > 50
		|| Request.HistoryOffset < 0 || Request.HistoryOffset > 10000)
		throw std::runtime_error("History accepts 1-16 selected project files, max_history 1-50, and history_offset 0-10000");
	TArray<FEntry> Entries = Resolve(Request);
	ISourceControlModule& Module = ISourceControlModule::Get();
	ISourceControlProvider& Provider = Module.GetProvider();
	const bool bReady = Module.IsEnabled() && Provider.IsAvailable();
	TSharedRef<FUpdateStatus, ESPMode::ThreadSafe> Update = ISourceControlOperation::Create<FUpdateStatus>();
	Update->SetUpdateHistory(true);
	Update->SetUpdateModifiedState(true);
	Update->SetQuiet(true);
	// UsesFileRevisions describes the provider's revision model, not history availability.
	// Git returns false there while implementing FUpdateStatus::SetUpdateHistory.
	const bool bSupported = bReady && Provider.CanExecuteOperation(Update);
	TArray<FString> Errors, Warnings;
	bool bRefreshed = false;
	if (!bReady) Errors.Add(TEXT("The editor source control provider is disabled or unavailable"));
	else if (!bSupported) Errors.Add(TEXT("The configured provider does not support status/history requests"));
	else
	{
		const bool bGit = Provider.GetName() == FName(TEXT("Git"));
		for (FEntry& Entry : Entries) Entry.bFallbackHistory = bGit && !IFileManager::Get().FileExists(*Entry.Filename);
		if (Request.bRefresh)
		{
			TArray<FString> Files;
			for (const FEntry& Entry : Entries) if (!Entry.bFallbackHistory) Files.Add(Entry.Filename);
			bRefreshed = Files.IsEmpty() || Provider.Execute(Update, Files) == ECommandResult::Succeeded;
			for (const FText& Message : Update->GetResultInfo().ErrorMessages)
				if (bRefreshed) Warnings.Add(Message.ToString()); else Errors.Add(Message.ToString());
			for (const FText& Message : Update->GetResultInfo().InfoMessages) Warnings.Add(Message.ToString());
			if (!bRefreshed && Errors.IsEmpty()) Errors.Add(TEXT("Source control history refresh failed"));
		}
		for (FEntry& Entry : Entries)
		{
			Entry.State = Provider.GetState(Entry.Filename, Entry.bFallbackHistory && Request.bRefresh ? EStateCacheUsage::ForceUpdate : EStateCacheUsage::Use);
			if (Entry.bFallbackHistory)
				if (!GitReadUtils::History(Provider, Entry.Filename, Entry.FallbackHistory, Errors)) bRefreshed = false;
			if ((!Entry.State.IsValid() || Entry.State->IsUnknown()) && Entry.FallbackHistory.IsEmpty())
				Errors.Add(Entry.Label() + TEXT(": provider file state is unknown"));
		}
	}
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart(); WriteProvider(Writer, Module);
	Writer->WriteValue(TEXT("history_supported"), bSupported);
	Writer->WriteValue(TEXT("success"), Errors.IsEmpty());
	Writer->WriteValue(TEXT("changed"), false);
	Writer->WriteValue(TEXT("refreshed"), bRefreshed);
	Writer->WriteValue(TEXT("history_offset"), Request.HistoryOffset);
	Writer->WriteValue(TEXT("max_history"), Request.MaxHistory);
	Writer->WriteArrayStart(TEXT("files"));
	for (const FEntry& Entry : Entries)
	{
		const int32 Total = Entry.bFallbackHistory ? Entry.FallbackHistory.Num() : Entry.State.IsValid() ? Entry.State->GetHistorySize() : 0;
		const int32 Start = FMath::Min(Request.HistoryOffset, Total);
		const int32 End = FMath::Min(Start + Request.MaxHistory, Total);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Entry.AssetPath);
		Writer->WriteValue(TEXT("file_path"), Entry.RequestedFilePath);
		Writer->WriteValue(TEXT("package_path"), Entry.PackageName);
		Writer->WriteValue(TEXT("filename"), Entry.Filename);
		Writer->WriteValue(TEXT("state_known"), Entry.State.IsValid() && !Entry.State->IsUnknown());
		Writer->WriteValue(TEXT("source_controlled"), Entry.State.IsValid() && Entry.State->IsSourceControlled());
		Writer->WriteValue(TEXT("history_total"), Total);
		Writer->WriteValue(TEXT("history_source"), Entry.bFallbackHistory ? TEXT("git_missing_file_adapter") : TEXT("provider"));
		Writer->WriteValue(TEXT("history_may_be_truncated"), Entry.bFallbackHistory && Total == 256);
		Writer->WriteValue(TEXT("has_more"), End < Total);
		Writer->WriteArrayStart(TEXT("revisions"));
		int32 Returned = 0;
		for (int32 Index = Start; Index < End; ++Index)
		{
			TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe> Revision = Entry.bFallbackHistory ? Entry.FallbackHistory[Index] : Entry.State->GetHistoryItem(Index);
			if (!Revision.IsValid()) continue;
			++Returned;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("index"), Index);
			Writer->WriteValue(TEXT("revision"), Revision->GetRevision());
			Writer->WriteValue(TEXT("revision_number"), Revision->GetRevisionNumber());
			Writer->WriteValue(TEXT("checkin_identifier"), Revision->GetCheckInIdentifier());
			Writer->WriteValue(TEXT("description"), Revision->GetDescription().Left(8192));
			Writer->WriteValue(TEXT("description_truncated"), Revision->GetDescription().Len() > 8192);
			Writer->WriteValue(TEXT("user"), Revision->GetUserName());
			Writer->WriteValue(TEXT("client"), Revision->GetClientSpec());
			Writer->WriteValue(TEXT("action"), Revision->GetAction());
			Writer->WriteValue(TEXT("date"), Revision->GetDate().ToIso8601());
			Writer->WriteValue(TEXT("size_bytes"), Revision->GetFileSize());
			Writer->WriteValue(TEXT("filename"), Revision->GetFilename());
			if (TSharedPtr<ISourceControlRevision, ESPMode::ThreadSafe> Branch = Revision->GetBranchSource())
			{
				Writer->WriteObjectStart(TEXT("branch_source"));
				Writer->WriteValue(TEXT("filename"), Branch->GetFilename());
				Writer->WriteValue(TEXT("revision"), Branch->GetRevision());
				Writer->WriteObjectEnd();
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("returned_count"), Returned);
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString SourceControlUtils::AssetsJson(const FSourceControlReq& Request)
{
	const FString OperationName = Request.Operation.TrimStartAndEnd().ToLower();
	if (OperationName != TEXT("status") && OperationName != TEXT("checkout") && OperationName != TEXT("add")
		&& OperationName != TEXT("revert") && OperationName != TEXT("submit"))
		throw std::runtime_error("operation must be status, checkout, add, revert, or submit");
	TArray<FEntry> Entries = Resolve(Request);
	TArray<FString> Files;
	for (const FEntry& Entry : Entries) Files.Add(Entry.Filename);
	TArray<FString> PackageFiles;
	for (const FEntry& Entry : Entries) if (!Entry.PackageName.IsEmpty()) PackageFiles.Add(Entry.Filename);
	ISourceControlModule& Module = ISourceControlModule::Get();
	ISourceControlProvider& Provider = Module.GetProvider();
	const bool bReady = Module.IsEnabled() && Provider.IsAvailable();
	const bool bMutation = OperationName != TEXT("status");
	FSourceControlOperationRef Operation = MakeOperation(OperationName, Request.Description.TrimStartAndEnd());
	const bool bSupported = bReady && Provider.CanExecuteOperation(Operation);
	TArray<FString> Errors;
	TArray<FString> Warnings;
	TArray<FString> RestoredFiles;
	bool bRefreshed = false;
	bool bExecuted = false;
	bool bSucceeded = !bMutation;
	if (!bReady) Errors.Add(TEXT("The editor source control provider is disabled or unavailable"));
	else if (!bSupported) Errors.Add(TEXT("The configured provider does not support this operation"));
	else
	{
		if (Request.bRefresh || bMutation)
		{
			TSharedRef<FUpdateStatus, ESPMode::ThreadSafe> Preflight = StaticCastSharedRef<FUpdateStatus>(MakeOperation(TEXT("status"), TEXT("")));
			bRefreshed = Provider.Execute(Preflight, Files) == ECommandResult::Succeeded;
			if (!bRefreshed) Errors.Add(TEXT("Source control status refresh failed"));
		}
		TArray<FSourceControlStateRef> States;
		for (FEntry& Entry : Entries)
		{
			Entry.State = Provider.GetState(Entry.Filename, EStateCacheUsage::Use);
			Entry.bEligible = Eligible(Entry.State, OperationName);
			if (Entry.State.IsValid()) States.Add(Entry.State.ToSharedRef());
			if (!Entry.bEligible) Entry.Reason = TEXT("Provider state is unknown or does not permit this operation");
			if (bMutation && !Entry.bEligible) Errors.Add(Entry.Label() + TEXT(": ") + Entry.Reason);
			if ((OperationName == TEXT("submit") || OperationName == TEXT("revert")) && Entry.bDirty)
				Errors.Add(Entry.Label() + TEXT(": package has unsaved editor changes"));
			if (OperationName == TEXT("revert"))
			{
				UPackage* Loaded = Entry.PackageName.IsEmpty() ? nullptr : FindPackage(nullptr, *Entry.PackageName);
				if (Loaded && (UWorld::FindWorldInPackage(Loaded) || Entry.PackageName.Contains(TEXT("/__ExternalActors__/")) || Entry.PackageName.Contains(TEXT("/__ExternalObjects__/"))))
					Errors.Add(Entry.PackageName + TEXT(": unload world/external packages before reverting"));
				if (Entry.State.IsValid() && Entry.State->IsAdded() && USourceControlPreferences::ShouldDeleteNewFilesOnRevert())
				{
					Warnings.Add(Entry.Label() + TEXT(": revert may delete this added file under editor/provider preferences"));
					if (!Request.bDryRun && !Request.bConfirmDeleteAdded) Errors.Add(TEXT("confirm_delete_added=true is required for added files that revert will delete"));
				}
				if (Provider.GetName() == FName(TEXT("Git")) && !IFileManager::Get().FileExists(*Entry.Filename)
					&& Entry.State.IsValid() && Entry.State->IsSourceControlled() && !Entry.State->IsAdded())
				{
					if (GitReadUtils::History(Provider, Entry.Filename, Entry.FallbackHistory, Errors) && !Entry.FallbackHistory.IsEmpty())
						Entry.RestoreRevision = Entry.FallbackHistory[0];
					if (!Entry.RestoreRevision.IsValid() || Entry.RestoreRevision->GetAction().Equals(TEXT("delete"), ESearchCase::IgnoreCase))
						Errors.Add(Entry.Label() + TEXT(": no committed contents are available to restore this missing Git file"));
				}
			}
		}
		if (OperationName == TEXT("submit"))
		{
			if (Request.Description.TrimStartAndEnd().IsEmpty() || Request.Description.Len() > 4096)
				Errors.Add(TEXT("Submit requires a nonempty description of at most 4096 characters"));
			auto Validation = Module.GetRegisteredPreSubmitFilesValidation();
			if (Validation.IsBound() && Errors.IsEmpty())
			{
				EDataValidationResult ValidationResult = EDataValidationResult::NotValidated;
				TArray<FText> ValidationErrors, ValidationWarnings;
				Validation.Execute(States, ValidationResult, ValidationErrors, ValidationWarnings);
				for (const FText& Error : ValidationErrors) Errors.Add(Error.ToString());
				for (const FText& Warning : ValidationWarnings) Warnings.Add(Warning.ToString());
				if (ValidationResult == EDataValidationResult::Invalid && ValidationErrors.IsEmpty())
					Errors.Add(TEXT("Registered pre-submit file validation rejected the request"));
			}
		}
		if (!Request.bDryRun && (OperationName == TEXT("revert") || OperationName == TEXT("submit")) && !Request.bConfirm)
			Errors.Add(TEXT("Revert and submit require confirm=true"));
		if (OperationName == TEXT("revert") && GEditor && GEditor->PlayWorld)
			Errors.Add(TEXT("Stop PIE before reverting assets"));
		if (OperationName == TEXT("submit") && !Request.bDryRun && Errors.IsEmpty())
		{
			TArray<FText> Tags, FinalizeErrors;
			PRAGMA_DISABLE_DEPRECATION_WARNINGS
			Module.GetOnPreSubmitFinalize().Broadcast(Files, Tags, FinalizeErrors);
			PRAGMA_ENABLE_DEPRECATION_WARNINGS
			for (const FText& Error : FinalizeErrors) Errors.Add(Error.ToString());
			FString Description = Request.Description.TrimStartAndEnd();
			for (const FText& Tag : Tags) Description += TEXT("\n") + Tag.ToString();
			StaticCastSharedRef<FCheckIn>(Operation)->SetDescription(FText::FromString(Description));
		}
		if (bMutation && !Request.bDryRun && Errors.IsEmpty())
		{
			bExecuted = true;
			if (OperationName == TEXT("revert"))
			{
				auto RevertFiles = [&Provider, &Operation, &Files, &Entries, &Errors, &RestoredFiles](const TArray<FString>&)
					{
						if (!RestoreMissingGitFiles(Entries, Errors, RestoredFiles)) return false;
						const bool bSuccess = Provider.Execute(Operation, Files) == ECommandResult::Succeeded;
						ISourceControlModule::Get().GetOnFilesDeleted().Broadcast(StaticCastSharedRef<FRevert>(Operation)->GetDeletedFiles());
						return bSuccess;
					};
				bSucceeded = PackageFiles.IsEmpty() ? RevertFiles(Files) :
					USourceControlHelpers::ApplyOperationAndReloadPackages(PackageFiles, RevertFiles, false, false);
			}
			else bSucceeded = Provider.Execute(Operation, Files) == ECommandResult::Succeeded;
			// Some providers put successful command progress from stderr in ErrorMessages.
			// Keep that output visible, but use the provider's command result for success.
			for (const FText& Message : Operation->GetResultInfo().ErrorMessages)
				if (bSucceeded) Warnings.Add(Message.ToString());
				else Errors.Add(Message.ToString());
			for (const FText& Info : Operation->GetResultInfo().InfoMessages) Warnings.Add(Info.ToString());
			if (!bSucceeded && Errors.IsEmpty()) Errors.Add(TEXT("Source control operation failed or was cancelled"));
			Provider.Execute(MakeOperation(TEXT("status"), TEXT("")), Files);
			for (FEntry& Entry : Entries) Entry.State = Provider.GetState(Entry.Filename, EStateCacheUsage::Use);
		}
		else if (Request.bDryRun) bSucceeded = Errors.IsEmpty();
	}
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart(); WriteProvider(Writer, Module);
	Writer->WriteValue(TEXT("operation"), OperationName);
	Writer->WriteValue(TEXT("operation_supported"), bSupported);
	Writer->WriteValue(TEXT("success"), bSucceeded && Errors.IsEmpty());
	Writer->WriteValue(TEXT("executed"), bExecuted);
	if (bExecuted && !bSucceeded) Writer->WriteNull(TEXT("changed"));
	else Writer->WriteValue(TEXT("changed"), bExecuted && bSucceeded);
	Writer->WriteValue(TEXT("may_have_changed"), bExecuted);
	Writer->WriteValue(TEXT("dry_run"), Request.bDryRun);
	Writer->WriteValue(TEXT("refreshed"), bRefreshed);
	Writer->WriteValue(TEXT("atomic"), false);
	Writer->WriteValue(TEXT("eligibility_phase"), TEXT("preflight"));
	Writer->WriteValue(TEXT("confirmation_required"), OperationName == TEXT("revert") || OperationName == TEXT("submit"));
	Writer->WriteValue(TEXT("package_reload_requested"), bExecuted && OperationName == TEXT("revert") && !PackageFiles.IsEmpty());
	Writer->WriteArrayStart(TEXT("restored_missing_files")); for (const FString& File : RestoredFiles) Writer->WriteValue(File); Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("files"));
	for (const FEntry& Entry : Entries)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Entry.AssetPath);
		Writer->WriteValue(TEXT("file_path"), Entry.RequestedFilePath);
		Writer->WriteValue(TEXT("kind"), Entry.PackageName.IsEmpty() ? TEXT("project_file") : TEXT("package"));
		Writer->WriteValue(TEXT("package_path"), Entry.PackageName);
		Writer->WriteValue(TEXT("filename"), Entry.Filename);
		Writer->WriteValue(TEXT("exists"), IFileManager::Get().FileExists(*Entry.Filename));
		if (Entry.PackageName.IsEmpty()) Writer->WriteNull(TEXT("dirty")); else Writer->WriteValue(TEXT("dirty"), Entry.bDirty);
		Writer->WriteValue(TEXT("eligible"), Entry.bEligible);
		Writer->WriteValue(TEXT("reason"), Entry.Reason);
		Writer->WriteValue(TEXT("state_known"), Entry.State.IsValid() && !Entry.State->IsUnknown());
		if (Entry.State.IsValid())
		{
			Writer->WriteValue(TEXT("state"), Entry.State->GetDisplayName().ToString());
			Writer->WriteValue(TEXT("source_controlled"), Entry.State->IsSourceControlled());
			Writer->WriteValue(TEXT("checked_out"), Entry.State->IsCheckedOut());
			Writer->WriteValue(TEXT("checked_out_other"), Entry.State->IsCheckedOutOther());
			Writer->WriteValue(TEXT("added"), Entry.State->IsAdded());
			Writer->WriteValue(TEXT("deleted"), Entry.State->IsDeleted());
			Writer->WriteValue(TEXT("modified"), Entry.State->IsModified());
			Writer->WriteValue(TEXT("current"), Entry.State->IsCurrent());
			Writer->WriteValue(TEXT("conflicted"), Entry.State->IsConflicted());
			Writer->WriteValue(TEXT("ignored"), Entry.State->IsIgnored());
			Writer->WriteValue(TEXT("can_checkout"), Entry.State->CanCheckout());
			Writer->WriteValue(TEXT("can_add"), Entry.State->CanAdd());
			Writer->WriteValue(TEXT("can_revert"), Entry.State->CanRevert());
			Writer->WriteValue(TEXT("can_submit"), Entry.State->CanCheckIn() && !Entry.State->IsConflicted() && Entry.State->IsCurrent());
		}
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}
