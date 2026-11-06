#include "StaticMeshImportUtils.h"

#include "UE5_MCP/API/DTO/StaticMeshImportReq.h"

#include "AssetImportTask.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "EditorReimportHandler.h"
#include "EditorFramework/AssetImportData.h"
#include "Engine/StaticMesh.h"
#include "HAL/FileManager.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/StrongObjectPtr.h"

#include <stdexcept>

namespace
{
	FString CheckedSourceFile(const FString& Path)
	{
		if (Path.IsEmpty() || FPaths::IsRelative(Path))
			throw std::runtime_error("source_file_path must be an absolute OBJ or glTF file path");
		FString Full = FPaths::ConvertRelativePathToFull(Path);
		FPaths::NormalizeFilename(Full);
		const FString Extension = FPaths::GetExtension(Full).ToLower();
		if (Extension != TEXT("obj") && Extension != TEXT("gltf") && Extension != TEXT("glb"))
			throw std::runtime_error("source_file_path must identify an OBJ, glTF, or GLB file");
		if (IFileManager::Get().FileSize(*Full) <= 0)
			throw std::runtime_error("source_file_path must identify a nonempty local file");
		return Full;
	}

	UEditorAssetSubsystem* AssetSubsystem()
	{
		UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!Subsystem) throw std::runtime_error("Editor Asset Subsystem is unavailable");
		return Subsystem;
	}

	FString ActionJson(const UStaticMesh* Mesh, const FString& AssetPath, const FString& Source,
		bool bChanged, bool bDryRun, bool bSaved, bool bReplaced, const FString& DestinationRoot = TEXT(""),
		const TArray<FString>& CreatedAssets = TArray<FString>())
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), AssetPath);
		Writer->WriteValue(TEXT("source_file"), Source);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("replaced"), bReplaced);
		Writer->WriteValue(TEXT("destination_root"), DestinationRoot);
		Writer->WriteArrayStart(TEXT("created_assets"));
		for (const FString& Created : CreatedAssets) Writer->WriteValue(Created);
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("lod_count"), Mesh ? Mesh->GetNumLODs() : 0);
		Writer->WriteValue(TEXT("vertices_lod0"), Mesh && Mesh->GetNumLODs() ? Mesh->GetNumVertices(0) : 0);
		Writer->WriteValue(TEXT("triangles_lod0"), Mesh && Mesh->GetNumLODs() ? Mesh->GetNumTriangles(0) : 0);
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}
}

FString StaticMeshImportUtils::SourceJson(const UStaticMesh* Mesh)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Mesh->GetPathName());
	Writer->WriteValue(TEXT("lod_count"), Mesh->GetNumLODs());
	Writer->WriteArrayStart(TEXT("lods"));
	for (int32 Index = 0; Index < Mesh->GetNumLODs(); ++Index)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("index"), Index);
		Writer->WriteValue(TEXT("vertices"), Mesh->GetNumVertices(Index));
		Writer->WriteValue(TEXT("triangles"), Mesh->GetNumTriangles(Index));
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("source_files"));
	if (const UAssetImportData* ImportData = Mesh->GetAssetImportData())
		for (const FString& Path : ImportData->ExtractFilenames())
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

FString StaticMeshImportUtils::Import(const FStaticMeshImportReq& Request)
{
	const FString Source = CheckedSourceFile(Request.SourceFilePath);
	const FString Destination = Request.DestinationPath.TrimStartAndEnd();
	const FString Name = Request.AssetName.TrimStartAndEnd();
	if (!Destination.StartsWith(TEXT("/Game/")) || Name.IsEmpty() || Name.Contains(TEXT("/")) || Name.Contains(TEXT(".")))
		throw std::runtime_error("destination_path must be under /Game and asset_name must be a simple asset name");
	const FString PackagePath = Destination + TEXT("/") + Name;
	if (!FPackageName::IsValidLongPackageName(PackagePath))
		throw std::runtime_error("destination_path and asset_name are not a valid UE package path");
	const FString Extension = FPaths::GetExtension(Source).ToLower();
	const bool bSceneImport = Extension == TEXT("gltf") || Extension == TEXT("glb");
	const FString ObjectPath = PackagePath + TEXT(".") + Name;
	if (bSceneImport)
	{
		if (AssetSubsystem()->DoesAssetExist(ObjectPath) || !AssetSubsystem()->ListAssets(PackagePath, true, false).IsEmpty())
			throw std::runtime_error("glTF destination already contains assets; reimport the existing mesh or choose a new asset_name");
		if (Request.bDryRun) return ActionJson(nullptr, TEXT(""), Source, false, true, false, false, PackagePath);
	}
	const bool bExisting = AssetSubsystem()->DoesAssetExist(ObjectPath);
	UStaticMesh* ExistingMesh = bExisting ? Cast<UStaticMesh>(StaticLoadObject(UObject::StaticClass(), nullptr, *ObjectPath)) : nullptr;
	if (bExisting && !ExistingMesh) throw std::runtime_error("Existing target is not a Static Mesh asset");
	if (bExisting && (!Request.bReplaceExisting || !Request.bConfirmReplace))
		throw std::runtime_error("Target asset exists; replace_existing=true and confirm_replace=true are required");
	if (Request.bDryRun) return ActionJson(ExistingMesh, ObjectPath, Source, false, true, false, bExisting);
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
	UStaticMesh* Imported = nullptr;
	for (UObject* Object : Task->GetObjects())
		if (UStaticMesh* Mesh = Cast<UStaticMesh>(Object)) { Imported = Mesh; break; }
	if (!Imported) throw std::runtime_error("Mesh import returned no Static Mesh asset");
	if (bSceneImport)
	{
		if (!Imported->GetPathName().StartsWith(PackagePath + TEXT("/")))
			throw std::runtime_error("glTF import returned a mesh outside its destination folder");
		return ActionJson(Imported, Imported->GetPathName(), Source, true, false, Request.bSave, false,
			PackagePath, AssetSubsystem()->ListAssets(PackagePath, true, false));
	}
	if (Imported->GetPathName() != ObjectPath) throw std::runtime_error("Mesh import returned an unexpected asset path");
	return ActionJson(Imported, ObjectPath, Source, true, false, Request.bSave, bExisting,
		TEXT(""), {ObjectPath});
}

FString StaticMeshImportUtils::Reimport(UStaticMesh* Mesh, const FStaticMeshImportReq& Request)
{
	if (!Request.bConfirmReimport) throw std::runtime_error("Static Mesh reimport requires confirm_reimport=true");
	FReimportManager* Manager = FReimportManager::Instance();
	TArray<FString> Registered;
	if (!Manager || !Manager->CanReimport(Mesh, &Registered))
		throw std::runtime_error("No Static Mesh reimport handler or source path is available");
	const UAssetImportData* ImportData = Mesh->GetAssetImportData();
	const FString Existing = ImportData ? ImportData->GetFirstFilename() : TEXT("");
	const FString Source = CheckedSourceFile(Request.SourceFilePath.IsEmpty() ? Existing : Request.SourceFilePath);
	FString ExistingFull = Existing.IsEmpty() ? TEXT("") : FPaths::ConvertRelativePathToFull(Existing);
	FPaths::NormalizeFilename(ExistingFull);
	const bool bSourceChange = ExistingFull.IsEmpty() || !Source.Equals(ExistingFull, ESearchCase::IgnoreCase);
	if (bSourceChange && !Request.bConfirmSourceChange)
		throw std::runtime_error("Changing the Static Mesh source requires confirm_source_change=true");
	if (Request.bDryRun) return ActionJson(Mesh, Mesh->GetPathName(), Source, false, true, false, false);
	Mesh->Modify();
	if (!Manager->Reimport(Mesh, false, false, Source, nullptr, INDEX_NONE, bSourceChange, true))
		throw std::runtime_error("Unreal rejected the Static Mesh reimport");
	Mesh->MarkPackageDirty();
	if (Request.bSave && !AssetSubsystem()->SaveAsset(Mesh->GetPathName(), true))
		throw std::runtime_error("Static Mesh reimport succeeded but saving the asset failed");
	return ActionJson(Mesh, Mesh->GetPathName(), Source, true, false, Request.bSave, false);
}
