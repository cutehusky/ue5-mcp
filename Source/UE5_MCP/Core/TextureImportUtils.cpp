#include "TextureImportUtils.h"

#include "UE5_MCP/API/DTO/TextureImportReq.h"

#include "AssetImportTask.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "EditorReimportHandler.h"
#include "EditorFramework/AssetImportData.h"
#include "Engine/Texture.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/StrongObjectPtr.h"

#include <stdexcept>

namespace
{
	FString CheckedSourceFile(const FString& Source)
	{
		if (Source.IsEmpty() || FPaths::IsRelative(Source)) throw std::runtime_error("source_file_path must be an absolute file path");
		FString Full = FPaths::ConvertRelativePathToFull(Source);
		FPaths::NormalizeFilename(Full);
		const FString Extension = FPaths::GetExtension(Full).ToLower();
		if (Extension != TEXT("png") && Extension != TEXT("jpg") && Extension != TEXT("jpeg")
			&& Extension != TEXT("tga") && Extension != TEXT("bmp") && Extension != TEXT("tif")
			&& Extension != TEXT("tiff") && Extension != TEXT("exr") && Extension != TEXT("hdr")
			&& Extension != TEXT("dds") && Extension != TEXT("ies"))
			throw std::runtime_error("source_file_path must use a supported texture-source extension");
		if (IFileManager::Get().FileSize(*Full) <= 0) throw std::runtime_error("source_file_path must identify a nonempty local file");
		return Full;
	}

	UEditorAssetSubsystem* AssetSubsystem()
	{
		UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!Subsystem) throw std::runtime_error("Editor Asset Subsystem is unavailable");
		return Subsystem;
	}

	FString ActionJson(const UTexture* Texture, const FString& Source, bool bChanged, bool bDryRun, bool bSaved, bool bReplaced)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Texture ? Texture->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("source_file"), Source);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("replaced"), bReplaced);
		Writer->WriteValue(TEXT("source_id"), Texture && Texture->Source.IsValid() ? Texture->Source.GetId().ToString() : TEXT(""));
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}
}

FString TextureImportUtils::SourceJson(const UTexture* Texture)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Texture->GetPathName());
	Writer->WriteValue(TEXT("source_valid"), Texture->Source.IsValid());
	Writer->WriteValue(TEXT("source_id"), Texture->Source.IsValid() ? Texture->Source.GetId().ToString() : TEXT(""));
	Writer->WriteValue(TEXT("width"), Texture->Source.IsValid() ? Texture->Source.GetSizeX() : 0);
	Writer->WriteValue(TEXT("height"), Texture->Source.IsValid() ? Texture->Source.GetSizeY() : 0);
	Writer->WriteValue(TEXT("source_mips"), Texture->Source.IsValid() ? Texture->Source.GetNumMips() : 0);
	Writer->WriteValue(TEXT("source_format"), Texture->Source.IsValid() ? static_cast<int32>(Texture->Source.GetFormat()) : INDEX_NONE);
	Writer->WriteArrayStart(TEXT("source_files"));
	if (Texture->AssetImportData)
		for (const FString& Path : Texture->AssetImportData->ExtractFilenames())
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("path"), Path);
			const int64 Size = IFileManager::Get().FileSize(*Path);
			Writer->WriteValue(TEXT("exists"), Size >= 0);
			Writer->WriteValue(TEXT("size_bytes"), Size);
			Writer->WriteObjectEnd();
		}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString TextureImportUtils::Import(const FTextureImportReq& Request)
{
	const FString Source = CheckedSourceFile(Request.SourceFilePath);
	const FString Destination = Request.DestinationPath.TrimStartAndEnd();
	const FString Name = Request.AssetName.TrimStartAndEnd();
	if (!Destination.StartsWith(TEXT("/Game/")) || Name.IsEmpty() || Name.Contains(TEXT("/")) || Name.Contains(TEXT(".")))
		throw std::runtime_error("destination_path must be under /Game and asset_name must be a simple asset name");
	const FString PackagePath = Destination + TEXT("/") + Name;
	if (!FPackageName::IsValidLongPackageName(PackagePath)) throw std::runtime_error("destination_path and asset_name are not a valid UE package path");
	const FString ObjectPath = PackagePath + TEXT(".") + Name;
	const bool bExisting = AssetSubsystem()->DoesAssetExist(ObjectPath);
	UTexture* ExistingTexture = bExisting ? Cast<UTexture>(StaticLoadObject(UObject::StaticClass(), nullptr, *ObjectPath)) : nullptr;
	if (bExisting && !ExistingTexture) throw std::runtime_error("Existing target is not a Texture asset");
	if (bExisting && (!Request.bReplaceExisting || !Request.bConfirmReplace))
		throw std::runtime_error("Target asset exists; replace_existing=true and confirm_replace=true are required");
	if (Request.bDryRun) return ActionJson(ExistingTexture, Source, false, true, false, bExisting);
	TStrongObjectPtr<UAssetImportTask> Task(NewObject<UAssetImportTask>());
	Task->Filename = Source;
	Task->DestinationPath = Destination;
	Task->DestinationName = Name;
	Task->bReplaceExisting = bExisting;
	Task->bReplaceExistingSettings = false;
	Task->bAutomated = true;
	Task->bAsync = false;
	Task->bSave = Request.bSave;
	TArray<UAssetImportTask*> Tasks;
	Tasks.Add(Task.Get());
	FAssetToolsModule& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
	Tools.Get().ImportAssetTasks(Tasks);
	UTexture* Imported = nullptr;
	for (UObject* Object : Task->GetObjects())
		if (UTexture* Texture = Cast<UTexture>(Object)) { Imported = Texture; break; }
	if (!Imported) throw std::runtime_error("Texture import returned no Texture asset");
	if (Imported->GetPathName() != ObjectPath) throw std::runtime_error("Texture import returned an unexpected asset path");
	return ActionJson(Imported, Source, true, false, Request.bSave, bExisting);
}

FString TextureImportUtils::Reimport(UTexture* Texture, const FTextureImportReq& Request)
{
	if (!Request.bConfirmReimport) throw std::runtime_error("Texture reimport requires confirm_reimport=true");
	FReimportManager* Manager = FReimportManager::Instance();
	TArray<FString> Registered;
	if (!Manager || !Manager->CanReimport(Texture, &Registered)) throw std::runtime_error("No texture reimport handler or source path is available");
	const FString Existing = Texture->AssetImportData ? Texture->AssetImportData->GetFirstFilename() : TEXT("");
	const FString Source = CheckedSourceFile(Request.SourceFilePath.IsEmpty() ? Existing : Request.SourceFilePath);
	const bool bSourceChange = !Existing.IsEmpty() && !Source.Equals(FPaths::ConvertRelativePathToFull(Existing), ESearchCase::IgnoreCase);
	if (bSourceChange && !Request.bConfirmSourceChange)
		throw std::runtime_error("Changing the texture source requires confirm_source_change=true");
	if (Request.bDryRun) return ActionJson(Texture, Source, false, true, false, true);
	Texture->Modify();
	if (!Manager->Reimport(Texture, false, false, Source, nullptr, INDEX_NONE, bSourceChange, true))
		throw std::runtime_error("Unreal rejected the texture reimport");
	Texture->MarkPackageDirty();
	if (Request.bSave && !AssetSubsystem()->SaveAsset(Texture->GetPathName(), true))
		throw std::runtime_error("Texture reimport succeeded but saving the asset failed");
	return ActionJson(Texture, Source, true, false, Request.bSave, true);
}
