#include "SoundWaveImportUtils.h"

#include "UE5_MCP/API/DTO/SoundWaveImportReq.h"

#include "AssetImportTask.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "EditorFramework/AssetImportData.h"
#include "Factories/SoundFactory.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Serialization/JsonWriter.h"
#include "Sound/SoundWave.h"
#include "SoundFileIO/SoundFileIO.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/StrongObjectPtr.h"

#include <stdexcept>

namespace
{
	TArray<FString> SupportedExtensions()
	{
		TArray<FString> Extensions;
		for (const FString& Format : GetDefault<USoundFactory>()->Formats)
		{
			FString Extension, Description;
			if (Format.Split(TEXT(";"), &Extension, &Description)) Extensions.AddUnique(Extension.ToLower());
		}
		return Extensions;
	}

	FString CheckedSourceFile(const FString& Path)
	{
		if (Path.IsEmpty() || FPaths::IsRelative(Path))
			throw std::runtime_error("source_file_path must be an absolute audio file path");
		FString Full = FPaths::ConvertRelativePathToFull(Path);
		FPaths::NormalizeFilename(Full);
		const FString Extension = FPaths::GetExtension(Full).ToLower();
		if (!SupportedExtensions().Contains(Extension))
			throw std::runtime_error("source_file_path extension is not supported by the installed native Sound Factory; see /audio/waves/import-formats");
		const int64 Size = IFileManager::Get().FileSize(*Full);
		if (Size <= 0)
			throw std::runtime_error("source_file_path must identify a nonempty local file");
		if (Size > MAX_int32) throw std::runtime_error("audio source exceeds the native factory's 2 GB input limit");
		if (Extension != TEXT("wav"))
		{
			TArray<uint8> AudioData, WaveData;
			if (!FFileHelper::LoadFileToArray(AudioData, *Full))
				throw std::runtime_error("could not read the audio source file");
			// UE 5.7's memory reader uses allocated size for EOF. FileHelper adds
			// padding capacity, so remove it before a decoder can seek past Num().
			AudioData.Shrink();
			if (!Audio::SoundFileUtils::ConvertAudioToWav(AudioData, WaveData))
				throw std::runtime_error("native audio decoder rejected the source file");
			FWaveModInfo Info;
			if (!Info.ReadWaveInfo(WaveData.GetData(), WaveData.Num()) || !Info.pChannels || !Info.pSamplesPerSec
				|| *Info.pChannels == 0 || *Info.pSamplesPerSec == 0 || Info.SampleDataSize == 0)
				throw std::runtime_error("decoded audio contains no valid samples, channels, or sample rate");
		}
		return Full;
	}

	UEditorAssetSubsystem* AssetSubsystem()
	{
		UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!Subsystem) throw std::runtime_error("Editor Asset Subsystem is unavailable");
		return Subsystem;
	}

	FString ActionJson(const USoundWave* Wave, const FString& AssetPath, const FString& Source,
		bool bChanged, bool bDryRun, bool bSaved, bool bReplaced)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), AssetPath);
		Writer->WriteValue(TEXT("source_file"), Source);
		Writer->WriteValue(TEXT("source_format"), FPaths::GetExtension(Source).ToLower());
		Writer->WriteValue(TEXT("would_change"), true);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("replaced"), bReplaced);
		Writer->WriteValue(TEXT("duration_seconds"), Wave ? Wave->GetDuration() : 0.0f);
		Writer->WriteValue(TEXT("imported_duration_seconds"), Wave ? Wave->Duration : 0.0f);
		Writer->WriteValue(TEXT("channels"), Wave ? Wave->NumChannels : 0);
		Writer->WriteValue(TEXT("imported_sample_rate"), Wave ? Wave->GetImportedSampleRate() : 0);
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	USoundWave* ImportNativeSource(const FString& Source, const FString& Destination, const FString& Name,
		bool bReplaceExisting, bool bSave)
	{
		TStrongObjectPtr<UAssetImportTask> Task(NewObject<UAssetImportTask>());
		USoundFactory* Factory = NewObject<USoundFactory>(Task.Get());
		Factory->SuppressImportDialogs();
		Task->Factory = Factory;
		Task->Filename = Source;
		Task->DestinationPath = Destination;
		Task->DestinationName = Name;
		Task->bReplaceExisting = bReplaceExisting;
		Task->bReplaceExistingSettings = false;
		Task->bAutomated = true;
		Task->bAsync = false;
		Task->bSave = bSave;
		TArray<UAssetImportTask*> Tasks = { Task.Get() };
		FAssetToolsModule& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		Tools.Get().ImportAssetTasks(Tasks);
		for (UObject* Object : Task->GetObjects())
			if (USoundWave* Wave = Cast<USoundWave>(Object)) return Wave;
		throw std::runtime_error("native audio import returned no Sound Wave asset");
	}
}

FString SoundWaveImportUtils::FormatsJson()
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("factory_class"), USoundFactory::StaticClass()->GetPathName());
	Writer->WriteArrayStart(TEXT("formats"));
	for (const FString& Format : GetDefault<USoundFactory>()->Formats)
	{
		FString Extension, Description;
		if (!Format.Split(TEXT(";"), &Extension, &Description)) continue;
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("extension"), Extension.ToLower());
		Writer->WriteValue(TEXT("description"), Description.TrimStartAndEnd());
		Writer->WriteValue(TEXT("import"), true);
		Writer->WriteValue(TEXT("reimport"), true);
		Writer->WriteValue(TEXT("dry_run_decoder_preflight"), !Extension.Equals(TEXT("wav"), ESearchCase::IgnoreCase));
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString SoundWaveImportUtils::SourceJson(const USoundWave* Wave)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Wave->GetPathName());
	Writer->WriteValue(TEXT("duration_seconds"), Wave->GetDuration());
	Writer->WriteValue(TEXT("imported_duration_seconds"), Wave->Duration);
	Writer->WriteValue(TEXT("channels"), Wave->NumChannels);
	Writer->WriteValue(TEXT("imported_sample_rate"), Wave->GetImportedSampleRate());
	Writer->WriteArrayStart(TEXT("source_files"));
	if (Wave->AssetImportData)
		for (const FString& Path : Wave->AssetImportData->ExtractFilenames())
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("path"), Path);
			Writer->WriteValue(TEXT("format"), FPaths::GetExtension(Path).ToLower());
			const int64 Size = IFileManager::Get().FileSize(*Path);
			Writer->WriteValue(TEXT("exists"), Size >= 0);
			Writer->WriteValue(TEXT("size_bytes"), Size);
			Writer->WriteObjectEnd();
		}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString SoundWaveImportUtils::Import(const FSoundWaveImportReq& Request)
{
	const FString Source = CheckedSourceFile(Request.SourceFilePath);
	const FString Destination = Request.DestinationPath.TrimStartAndEnd();
	const FString Name = Request.AssetName.TrimStartAndEnd();
	if (!Destination.StartsWith(TEXT("/Game/")) || Name.IsEmpty() || Name.Contains(TEXT("/")) || Name.Contains(TEXT(".")))
		throw std::runtime_error("destination_path must be under /Game and asset_name must be a simple asset name");
	const FString PackagePath = Destination + TEXT("/") + Name;
	if (!FPackageName::IsValidLongPackageName(PackagePath))
		throw std::runtime_error("destination_path and asset_name are not a valid UE package path");
	const FString ObjectPath = PackagePath + TEXT(".") + Name;
	const bool bExisting = AssetSubsystem()->DoesAssetExist(ObjectPath);
	USoundWave* ExistingWave = bExisting ? Cast<USoundWave>(StaticLoadObject(UObject::StaticClass(), nullptr, *ObjectPath)) : nullptr;
	if (bExisting && !ExistingWave) throw std::runtime_error("Existing target is not a Sound Wave asset");
	if (bExisting && (!Request.bReplaceExisting || !Request.bConfirmReplace))
		throw std::runtime_error("Target asset exists; replace_existing=true and confirm_replace=true are required");
	if (Request.bDryRun) return ActionJson(ExistingWave, ObjectPath, Source, false, true, false, bExisting);
	USoundWave* Imported = ImportNativeSource(Source, Destination, Name, bExisting, Request.bSave);
	if (Imported->GetPathName() != ObjectPath) throw std::runtime_error("audio import returned an unexpected asset path");
	return ActionJson(Imported, ObjectPath, Source, true, false, Request.bSave, bExisting);
}

FString SoundWaveImportUtils::Reimport(USoundWave* Wave, const FSoundWaveImportReq& Request)
{
	if (!Request.bConfirmReimport) throw std::runtime_error("Sound Wave reimport requires confirm_reimport=true");
	const FString Existing = Wave->AssetImportData ? Wave->AssetImportData->GetFirstFilename() : TEXT("");
	const FString Source = CheckedSourceFile(Request.SourceFilePath.IsEmpty() ? Existing : Request.SourceFilePath);
	FString ExistingFull = Existing.IsEmpty() ? TEXT("") : FPaths::ConvertRelativePathToFull(Existing);
	FPaths::NormalizeFilename(ExistingFull);
	const bool bSourceChange = ExistingFull.IsEmpty() || !Source.Equals(ExistingFull, ESearchCase::IgnoreCase);
	if (bSourceChange && !Request.bConfirmSourceChange)
		throw std::runtime_error("Changing the Sound Wave source requires confirm_source_change=true");
	if (Request.bDryRun) return ActionJson(Wave, Wave->GetPathName(), Source, false, true, false, false);
	Wave->Modify();
	USoundWave* Reimported = ImportNativeSource(Source, FPackageName::GetLongPackagePath(Wave->GetOutermost()->GetName()),
		Wave->GetName(), true, false);
	if (Reimported != Wave) throw std::runtime_error("native reimport did not preserve the existing Sound Wave object");
	if (Wave->AssetImportData) Wave->AssetImportData->Update(Source);
	Wave->InvalidateCompressedData();
	Wave->FreeResources();
	Wave->UpdatePlatformData();
	Wave->MarkPackageDirty();
	if (Request.bSave && !AssetSubsystem()->SaveAsset(Wave->GetPathName(), true))
		throw std::runtime_error("Sound Wave reimport succeeded but saving the asset failed");
	return ActionJson(Wave, Wave->GetPathName(), Source, true, false, Request.bSave, false);
}
