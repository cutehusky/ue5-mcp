#include "UE5_MCP/Core/DebugFeedbackUtils.h"
#include "UE5_MCP/Core/ProjectDiagnosticsUtils.h"
#include "UE5_MCP/API/DTO/GameCoreReq.h"
#include "EditorRoute.h"

#include "UE5_MCP/API/Interface/HttpApp.h"
#include "UE5_MCP/API/Interface/DTO/ActionResponse.h"
#include "UE5_MCP/API/DTO/EditorActorReq.h"
#include "UE5_MCP/API/DTO/WorldOperationReq.h"
#include "UE5_MCP/API/DTO/WorldSettingsReq.h"
#include "UE5_MCP/Core/WorldSettingsUtils.h"
#include "UE5_MCP/API/DTO/NavigationReq.h"
#include "UE5_MCP/Core/NavigationUtils.h"
#include "UE5_MCP/API/DTO/NavigationFilterReq.h"
#include "UE5_MCP/Core/NavigationFilterUtils.h"
#include "UE5_MCP/API/DTO/NavigationAreaReq.h"
#include "UE5_MCP/Core/NavigationAreaUtils.h"
#include "UE5_MCP/API/DTO/NavigationLinkReq.h"
#include "UE5_MCP/Core/NavigationLinkUtils.h"
#include "UE5_MCP/API/DTO/NavigationAgentReq.h"
#include "UE5_MCP/Core/NavigationAgentUtils.h"
#include "UE5_MCP/API/DTO/WorldOperationResponse.h"
#include "UE5_MCP/API/DTO/SceneComponentReq.h"
#include "UE5_MCP/API/DTO/EditorAssetSelectionReq.h"
#include "UE5_MCP/API/DTO/EditorDiagnosticReq.h"
#include "UE5_MCP/API/DTO/WorldStructureReq.h"
#include "UE5_MCP/API/DTO/ProjectValidationReq.h"
#include "UE5_MCP/API/DTO/SourceControlReq.h"
#include "UE5_MCP/API/DTO/LevelInstanceReq.h"
#include "UE5_MCP/API/Interface/Exceptions/HttpException.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/ARFilter.h"
#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"
#include "Editor.h"
#include "PlayInEditorDataTypes.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "Kismet2/DebuggerCommands.h"
#include "Subsystems/UnrealEditorSubsystem.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UnrealType.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Misc/App.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Logging/MessageLog.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Containers/Ticker.h"
#include "UnrealClient.h"
#include "Algo/Reverse.h"
#include "Algo/Unique.h"
#include "EditorLevelUtils.h"
#include "LevelUtils.h"
#include "Engine/Level.h"
#include "Engine/LevelStreaming.h"
#include "Engine/LevelStreamingVolume.h"
#include "Engine/LevelStreamingDynamic.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/DataLayer/DataLayerManager.h"
#include "WorldPartition/DataLayer/DataLayerInstance.h"
#include "DataLayer/DataLayerEditorSubsystem.h"
#include "HAL/PlatformProperties.h"
#include "Engine/Selection.h"
#include "Components/ActorComponent.h"
#include "Components/SceneComponent.h"
#include "FileHelpers.h"
#include "ScopedTransaction.h"
#include "AssetSelection.h"
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "Engine/Blueprint.h"
#include "UObject/ObjectRedirector.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UE5_MCP/Core/ObjUtils.h"
#include "UE5_MCP/Core/SourceControlUtils.h"
#include "UE5_MCP/Core/LevelInstanceUtils.h"

#include <atomic>

namespace
{
	UEditorActorSubsystem* ActorSubsystem()
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		return GEditor->GetEditorSubsystem<UEditorActorSubsystem>();
	}

	UAssetEditorSubsystem* AssetEditorSubsystem()
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		return GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
	}

	AActor* LoadEditorActor(const FString& Path)
	{
		if (Path.IsEmpty()) throw std::runtime_error("actor_path is required");
		AActor* Actor = ActorSubsystem()->GetActorReference(Path);
		if (!Actor) Actor = Cast<AActor>(StaticFindObject(AActor::StaticClass(), nullptr, *Path));
		if (!Actor || Actor->GetWorld() != GEditor->GetEditorWorldContext().World())
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Actor not found in current editor world: %s"), *Path)));
		return Actor;
	}

	UActorComponent* FindActorComponent(AActor* Actor, const FString& Name)
	{
		if (!Actor || Name.IsEmpty())
			throw FValidationException(TEXT("actor_path and component_name are required"));
		TInlineComponentArray<UActorComponent*> Components(Actor);
		UActorComponent** Match = Components.FindByPredicate([&Name](const UActorComponent* Component)
		{
			return Component && Component->GetName().Equals(Name, ESearchCase::CaseSensitive);
		});
		if (!Match)
			throw FValidationException(FString::Printf(TEXT("Component not found: %s"), *Name));
		return *Match;
	}

	UWorld* ActiveEditorWorld()
	{
		UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World) throw std::runtime_error("No editor world is available");
		return World;
	}

	ULevelStreaming* FindStreamingLevel(UWorld* World, const FString& LevelPath)
	{
		if (!World || LevelPath.IsEmpty()) throw FValidationException(TEXT("level_path is required"));
		const FString PackagePath = FPackageName::ObjectPathToPackageName(LevelPath);
		for (ULevelStreaming* Streaming : World->GetStreamingLevels())
			if (Streaming && Streaming->GetWorldAssetPackageName().Equals(PackagePath, ESearchCase::IgnoreCase)) return Streaming;
		throw FValidationException(FString::Printf(TEXT("Sublevel is not attached to the current world: %s"), *PackagePath));
	}

	UDataLayerInstance* FindDataLayer(UWorld* World, const FString& Name)
	{
		if (!World || Name.IsEmpty()) throw FValidationException(TEXT("data_layer_name is required"));
		UDataLayerManager* Manager = World->GetDataLayerManager();
		if (!Manager) throw FValidationException(TEXT("The current world has no Data Layer manager"));
		for (UDataLayerInstance* Layer : Manager->GetDataLayerInstances())
		{
			if (Layer && (Layer->GetDataLayerFName().ToString().Equals(Name, ESearchCase::IgnoreCase)
				|| Layer->GetDataLayerShortName().Equals(Name, ESearchCase::IgnoreCase)
				|| Layer->GetDataLayerFullName().Equals(Name, ESearchCase::IgnoreCase))) return Layer;
		}
		throw FValidationException(FString::Printf(TEXT("Data Layer not found: %s"), *Name));
	}

	std::atomic_bool GWorldMutationInProgress = false;

	struct FWorldMutationGuard
	{
		FWorldMutationGuard()
		{
			if (GWorldMutationInProgress.exchange(true))
				throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("World mutation busy"), TEXT("Another editor-world mutation is already in progress"));
		}

		~FWorldMutationGuard()
		{
			GWorldMutationInProgress.store(false);
		}
	};

	TArray<FString> PackageNames(const TArray<UPackage*>& Packages)
	{
		TArray<FString> Names;
		Names.Reserve(Packages.Num());
		for (const UPackage* Package : Packages)
		{
			if (Package)
				Names.Add(Package->GetName());
		}
		Names.Sort();
		return Names;
	}

	IAssetRegistry& EditorAssetRegistry()
	{
		return FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
	}

	IContentBrowserSingleton& ContentBrowser()
	{
		return FModuleManager::LoadModuleChecked<FContentBrowserModule>(TEXT("ContentBrowser")).Get();
	}

	struct FAutomationRunState
	{
		FString TestName;
		bool bRunning = false;
		bool bComplete = false;
		bool bSuccessful = false;
		double Duration = 0.0;
		int32 Errors = 0;
		int32 Warnings = 0;
		TArray<FString> Entries;
		FTSTicker::FDelegateHandle TickerHandle;
	};

	FAutomationRunState GAutomationRun;
	FString GLastScreenshotPath;

	void FinishAutomationRun(bool bCancel)
	{
		FAutomationTestFramework& Framework = FAutomationTestFramework::Get();
		if (bCancel) Framework.DequeueAllCommands();
		FAutomationTestExecutionInfo Info;
		GAutomationRun.bSuccessful = Framework.StopTest(Info) && !bCancel;
		GAutomationRun.Duration = Info.Duration;
		GAutomationRun.Errors = Info.GetErrorTotal();
		GAutomationRun.Warnings = Info.GetWarningTotal();
		GAutomationRun.Entries.Reset();
		for (const FAutomationExecutionEntry& Entry : Info.GetEntries()) GAutomationRun.Entries.Add(Entry.ToString());
		GAutomationRun.bRunning = false;
		GAutomationRun.bComplete = true;
	}

	FString AutomationStateJson()
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("test_name"), GAutomationRun.TestName);
		Writer->WriteValue(TEXT("running"), GAutomationRun.bRunning);
		Writer->WriteValue(TEXT("complete"), GAutomationRun.bComplete);
		Writer->WriteValue(TEXT("successful"), GAutomationRun.bSuccessful);
		Writer->WriteValue(TEXT("duration_seconds"), GAutomationRun.Duration);
		Writer->WriteValue(TEXT("errors"), GAutomationRun.Errors);
		Writer->WriteValue(TEXT("warnings"), GAutomationRun.Warnings);
		Writer->WriteArrayStart(TEXT("entries"));
		for (const FString& Entry : GAutomationRun.Entries) Writer->WriteValue(Entry);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	FString BlueprintStatusName(EBlueprintStatus Status)
	{
		switch (Status)
		{
		case BS_Unknown: return TEXT("unknown");
		case BS_Dirty: return TEXT("dirty");
		case BS_Error: return TEXT("error");
		case BS_UpToDate: return TEXT("up_to_date");
		case BS_BeingCreated: return TEXT("being_created");
		case BS_UpToDateWithWarnings: return TEXT("up_to_date_with_warnings");
		default: return TEXT("invalid");
		}
	}

	FAssetData FindAssetData(const FString& Path)
	{
		if (Path.IsEmpty()) throw FValidationException(TEXT("asset path cannot be empty"));
		const FString PackagePath = FPackageName::ObjectPathToPackageName(Path);
		TArray<FAssetData> Assets;
		EditorAssetRegistry().GetAssetsByPackageName(FName(*PackagePath), Assets, true);
		const FAssetData* Match = Assets.FindByPredicate([&Path](const FAssetData& Asset)
		{
			return !Path.Contains(TEXT(".")) || Asset.GetObjectPathString().Equals(Path, ESearchCase::IgnoreCase);
		});
		if (!Match) throw FValidationException(FString::Printf(TEXT("Asset not found: %s"), *Path));
		return *Match;
	}

	FAssetData FindWorldAsset(const FString& PackagePath)
	{
		TArray<FAssetData> Assets;
		EditorAssetRegistry().GetAssetsByPackageName(FName(*PackagePath), Assets, true);
		const FAssetData* WorldAsset = Assets.FindByPredicate([](const FAssetData& Asset)
		{
			return Asset.AssetClassPath == UWorld::StaticClass()->GetClassPathName();
		});
		if (!WorldAsset)
			throw FValidationException(FString::Printf(TEXT("Asset is not a UWorld map: %s"), *PackagePath));
		return *WorldAsset;
	}

	FString NormalizeWorldPackagePath(const FString& Path)
	{
		if (Path.IsEmpty())
			throw FValidationException(TEXT("world_path is required"));
		const FString PackagePath = FPackageName::ObjectPathToPackageName(Path);
		if (!FPackageName::IsValidLongPackageName(PackagePath))
			throw FValidationException(TEXT("world_path must be a valid Unreal package or object path"));
		FString Filename;
		if (!FPackageName::TryConvertLongPackageNameToFilename(PackagePath, Filename, FPackageName::GetMapPackageExtension()) || !FPaths::FileExists(Filename))
			throw FValidationException(FString::Printf(TEXT("World map does not exist: %s"), *PackagePath));

		FindWorldAsset(PackagePath);
		return PackagePath;
	}

	FString NormalizeNewWorldPackagePath(const FString& Path)
	{
		if (Path.IsEmpty())
			throw FValidationException(TEXT("world_path is required"));
		const FString PackagePath = FPackageName::ObjectPathToPackageName(Path);
		if (!FPackageName::IsValidLongPackageName(PackagePath) || !PackagePath.StartsWith(TEXT("/Game/")))
			throw FValidationException(TEXT("world_path must be a valid writable /Game package path"));
		return PackagePath;
	}

	void SetWorldState(FWorldOperationResponse& Response, UWorld* World)
	{
		Response.WorldPath = World ? World->GetPathName() : TEXT("");
		Response.PackagePath = World && World->GetOutermost() ? World->GetOutermost()->GetName() : TEXT("");
		Response.MapName = World ? World->GetMapName() : TEXT("");
		Response.bDirty = World && World->GetOutermost() && World->GetOutermost()->IsDirty();
	}

	FString InspectWorldJson(const FString& RequestedPath)
	{
		UWorld* ActiveWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!ActiveWorld)
			throw std::runtime_error("No editor world is available");

		const bool bInspectActive = RequestedPath.IsEmpty();
		const FString PackagePath = bInspectActive
			? ActiveWorld->GetOutermost()->GetName()
			: NormalizeWorldPackagePath(RequestedPath);
		const bool bActive = ActiveWorld->GetOutermost()->GetName() == PackagePath;
		FAssetData AssetData;
		if (!bActive)
			AssetData = FindWorldAsset(PackagePath);

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("world_path"), bActive ? ActiveWorld->GetPathName() : AssetData.GetObjectPathString());
		Writer->WriteValue(TEXT("package_path"), PackagePath);
		Writer->WriteValue(TEXT("map_name"), bActive ? ActiveWorld->GetMapName() : AssetData.AssetName.ToString());
		Writer->WriteValue(TEXT("active"), bActive);
		Writer->WriteValue(TEXT("loaded"), bActive);
		Writer->WriteValue(TEXT("dirty"), bActive && ActiveWorld->GetOutermost()->IsDirty());
		Writer->WriteValue(TEXT("actor_count"), bActive ? ActorSubsystem()->GetAllLevelActors().Num() : -1);
		Writer->WriteValue(TEXT("world_type"), bActive ? static_cast<int32>(ActiveWorld->WorldType) : -1);
		Writer->WriteValue(TEXT("settings_class"), bActive && ActiveWorld->GetWorldSettings() ? ActiveWorld->GetWorldSettings()->GetClass()->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("partitioned"), bActive && ActiveWorld->GetWorldPartition() != nullptr);
		Writer->WriteValue(TEXT("streaming_level_count"), bActive ? ActiveWorld->GetStreamingLevels().Num() : -1);
		Writer->WriteValue(TEXT("persistent_level"), bActive && ActiveWorld->PersistentLevel ? ActiveWorld->PersistentLevel->GetPathName() : TEXT(""));
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}
}

namespace
{
	int32 QueryLimit(const FHttpContextBase& Context, int32 Default = 200)
	{
		int32 Limit = Default;
		const FString Input = Context.Query(TEXT("limit"));
		int32 Parsed = 0;
		if (!Input.IsEmpty() && LexTryParseString(Parsed, *Input)) Limit = Parsed;
		return FMath::Clamp(Limit, 1, 2000);
	}

	UClass* LoadClassFromQuery(const FHttpContextBase& Context)
	{
		const FString Path = Context.Query(TEXT("class_path"));
		if (Path.IsEmpty()) return nullptr;
		UClass* Class = LoadClass<UObject>(nullptr, *Path);
		if (!Class)
			Class = FindObject<UClass>(nullptr, *Path);
		if (!Class)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Class not found: %s"), *Path)));
		return Class;
	}

	void WriteClassFields(TSharedRef<TJsonWriter<>>& Writer, UClass* Class)
	{
		Writer->WriteValue(TEXT("name"), Class->GetName());
		Writer->WriteValue(TEXT("path"), Class->GetPathName());
		Writer->WriteValue(TEXT("parent"), Class->GetSuperClass() ? Class->GetSuperClass()->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("blueprint_type"), Class->HasAnyClassFlags(CLASS_CompiledFromBlueprint));
		Writer->WriteValue(TEXT("abstract"), Class->HasAnyClassFlags(CLASS_Abstract));
		Writer->WriteValue(TEXT("deprecated"), Class->HasAnyClassFlags(CLASS_Deprecated));
		Writer->WriteValue(TEXT("native"), Class->HasAnyClassFlags(CLASS_Native));
		Writer->WriteValue(TEXT("display_name"), Class->GetDisplayNameText().ToString());
		Writer->WriteValue(TEXT("tooltip"), Class->GetToolTipText().ToString());
	}

	void WriteClass(TSharedRef<TJsonWriter<>>& Writer, UClass* Class)
	{
		Writer->WriteObjectStart();
		WriteClassFields(Writer, Class);
		Writer->WriteObjectEnd();
	}

	void WriteFunction(TSharedRef<TJsonWriter<>>& Writer, UFunction* Function)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("name"), Function->GetName());
		Writer->WriteValue(TEXT("path"), Function->GetPathName());
		Writer->WriteValue(TEXT("owner"), Function->GetOuterUClass() ? Function->GetOuterUClass()->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("blueprint_callable"), Function->HasAnyFunctionFlags(FUNC_BlueprintCallable));
		Writer->WriteValue(TEXT("blueprint_pure"), Function->HasAnyFunctionFlags(FUNC_BlueprintPure));
		Writer->WriteValue(TEXT("blueprint_event"), Function->HasAnyFunctionFlags(FUNC_BlueprintEvent));
		Writer->WriteValue(TEXT("static"), Function->HasAnyFunctionFlags(FUNC_Static));
		Writer->WriteValue(TEXT("tooltip"), Function->GetMetaData(TEXT("ToolTip")));
		Writer->WriteArrayStart(TEXT("parameters"));
		for (TFieldIterator<FProperty> It(Function); It; ++It)
		{
			FProperty* Property = *It;
			if (!Property || !Property->HasAnyPropertyFlags(CPF_Parm)) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Property->GetName());
			Writer->WriteValue(TEXT("type"), Property->GetClass()->GetName());
			Writer->WriteValue(TEXT("cpp_type"), Property->GetCPPType());
			Writer->WriteValue(TEXT("return"), Property->HasAnyPropertyFlags(CPF_ReturnParm));
			Writer->WriteValue(TEXT("out"), Property->HasAnyPropertyFlags(CPF_OutParm));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
	}
}

void BuildEditorRouter(TSharedPtr<HttpApp> App)
{
	App->Get(TEXT("/editor/source-control/provider"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(SourceControlUtils::ProviderJson(), TEXT("application/json"));
	});
	App->Post(TEXT("/editor/source-control/status"), [](const FHttpContext<FSourceControlReq, FString>& C)
	{
		FSourceControlReq Body = C.RequestBody();
		Body.Operation = TEXT("status");
		return C.TextResponse(SourceControlUtils::AssetsJson(Body), TEXT("application/json"));
	});
	App->Post(TEXT("/editor/source-control/operation"), [](const FHttpContext<FSourceControlReq, FString>& C)
	{
		return C.TextResponse(SourceControlUtils::AssetsJson(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/editor/source-control/history"), [](const FHttpContext<FSourceControlReq, FString>& C)
	{
		return C.TextResponse(SourceControlUtils::HistoryJson(C.RequestBody()), TEXT("application/json"));
	});
	App->Get(TEXT("/editor/status"), [](const FHttpContext<void, FString>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		UUnrealEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UUnrealEditorSubsystem>();
		UWorld* EditorWorld = EditorSubsystem ? EditorSubsystem->GetEditorWorld() : GEditor->GetEditorWorldContext().World();
		UWorld* GameWorld = EditorSubsystem ? EditorSubsystem->GetGameWorld() : nullptr;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("engine_version"), FEngineVersion::Current().ToString());
		Writer->WriteValue(TEXT("project_name"), FApp::GetProjectName());
		Writer->WriteValue(TEXT("platform"), UTF8_TO_TCHAR(FPlatformProperties::PlatformName()));
		Writer->WriteValue(TEXT("editor_available"), true);
		Writer->WriteValue(TEXT("is_playing"), FPlayWorldCommandCallbacks::HasPlayWorld());
		Writer->WriteValue(TEXT("is_paused"), FPlayWorldCommandCallbacks::HasPlayWorldAndPaused());
		Writer->WriteValue(TEXT("is_running"), FPlayWorldCommandCallbacks::HasPlayWorldAndRunning());
		Writer->WriteValue(TEXT("editor_world"), EditorWorld ? EditorWorld->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("map_name"), EditorWorld ? EditorWorld->GetMapName() : TEXT(""));
		Writer->WriteValue(TEXT("game_world"), GameWorld ? GameWorld->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("selected_actor_count"), GEditor->GetSelectedActors() ? GEditor->GetSelectedActors()->Num() : 0);
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/editor/selection"), [](const FHttpContext<void, FString>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		if (USelection* Selection = GEditor->GetSelectedActors())
		{
			for (FSelectionIterator It(*Selection); It; ++It)
			{
				if (AActor* Actor = Cast<AActor>(*It))
				{
					Writer->WriteObjectStart();
					Writer->WriteValue(TEXT("name"), Actor->GetName());
					Writer->WriteValue(TEXT("path"), Actor->GetPathName());
					Writer->WriteValue(TEXT("class"), Actor->GetClass()->GetPathName());
					Writer->WriteObjectEnd();
				}
			}
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/editor/viewport"), [](const FHttpContext<void, FString>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		UUnrealEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UUnrealEditorSubsystem>();
		FVector Location = FVector::ZeroVector;
		FRotator Rotation = FRotator::ZeroRotator;
		const bool bAvailable = Subsystem && Subsystem->GetLevelViewportCameraInfo(Location, Rotation);
		return C.TextResponse(FString::Printf(TEXT("{\"available\":%s,\"location\":{\"X\":%f,\"Y\":%f,\"Z\":%f},\"rotation\":{\"Pitch\":%f,\"Yaw\":%f,\"Roll\":%f}}"), bAvailable ? TEXT("true") : TEXT("false"), Location.X, Location.Y, Location.Z, Rotation.Pitch, Rotation.Yaw, Rotation.Roll), TEXT("application/json"));
	});

	App->Patch(TEXT("/editor/viewport"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		UUnrealEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UUnrealEditorSubsystem>();
		if (!Subsystem) throw std::runtime_error("Unreal editor subsystem is not available");
		Subsystem->SetLevelViewportCameraInfo(Body.Location, Body.Rotation);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/play"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		const FString Operation = C.RequestBody().Operation.ToLower();
		if (Operation == TEXT("start") || Operation == TEXT("start_here"))
		{
			if (GEditor->PlayWorld || GEditor->IsPlaySessionRequestQueued() || GEditor->IsPlaySessionInProgress()) throw std::runtime_error("A play session is already active");
			if (Operation == TEXT("start_here")) FPlayWorldCommandCallbacks::StartPlayFromHere();
			else
			{
				FRequestPlaySessionParams Params;
				Params.WorldType = EPlaySessionWorldType::PlayInEditor;
				Params.SessionDestination = EPlaySessionDestinationType::InProcess;
				GEditor->RequestPlaySession(Params);
			}
		}
		else if (Operation == TEXT("pause"))
		{
			if (!FPlayWorldCommandCallbacks::HasPlayWorldAndRunning()) throw std::runtime_error("No running play session is available to pause");
			FPlayWorldCommandCallbacks::PausePlaySession_Clicked();
		}
		else if (Operation == TEXT("resume"))
		{
			if (!FPlayWorldCommandCallbacks::HasPlayWorldAndPaused()) throw std::runtime_error("No paused play session is available to resume");
			FPlayWorldCommandCallbacks::ResumePlaySession_Clicked();
		}
		else if (Operation == TEXT("stop"))
		{
			if (!FPlayWorldCommandCallbacks::HasPlayWorld()) throw std::runtime_error("No play session is active");
			GEditor->RequestEndPlayMap();
		}
		else throw std::runtime_error("operation must be one of: start, start_here, pause, resume, stop");
		return C.JsonResponse(FActionResponse {});
	});

	App->Get(TEXT("/editor/logs"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(ProjectDiagnosticsUtils::ReadLogs(C.Query(TEXT("search")), C.Query(TEXT("severity")), C.Query(TEXT("category")),
			FCString::Atoi(*C.Query(TEXT("since_line"), TEXT("0"))), FCString::Atoi(*C.Query(TEXT("limit"), TEXT("200")))), TEXT("application/json"));
	});

	App->Post(TEXT("/editor/map-check"), [](const FHttpContext<void, FString>& C)
	{
		if (!GEditor || !IsInGameThread()) throw std::runtime_error("Map Check requires the Unreal editor game thread");
		UWorld* World = GEditor->GetEditorWorldContext().World();
		if (!World) throw std::runtime_error("No editor world is available");
		GEditor->Exec(World, TEXT("MAP CHECK DONTDISPLAYDIALOG"));
		FMessageLog MapCheckLog(TEXT("MapCheck"));
		const int32 Errors = MapCheckLog.NumMessages(EMessageSeverity::Error);
		const int32 Warnings = FMath::Max(0, MapCheckLog.NumMessages(EMessageSeverity::Warning) - Errors);
		return C.TextResponse(FString::Printf(TEXT("{\"world_path\":\"%s\",\"errors\":%d,\"warnings\":%d,\"valid\":%s}"),
			*World->GetPathName(), Errors, Warnings, Errors == 0 ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Get(TEXT("/editor/automation"), [](const FHttpContext<void, FString>& C)
	{
		FAutomationTestFramework& Framework = FAutomationTestFramework::Get();
		Framework.LoadTestModules();
		TArray<FAutomationTestInfo> Tests;
		Framework.GetValidTestNames(Tests);
		const FString Search = C.Query(TEXT("search"));
		const int32 Limit = QueryLimit(C, 200);
		Tests.RemoveAll([&Search](const FAutomationTestInfo& Test)
		{
			return !Search.IsEmpty() && !Test.GetFullTestPath().Contains(Search, ESearchCase::IgnoreCase)
				&& !Test.GetDisplayName().Contains(Search, ESearchCase::IgnoreCase);
		});
		Tests.Sort([](const FAutomationTestInfo& Left, const FAutomationTestInfo& Right) { return Left.GetFullTestPath() < Right.GetFullTestPath(); });
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("running"), GAutomationRun.bRunning);
		Writer->WriteValue(TEXT("current_test"), GAutomationRun.TestName);
		Writer->WriteValue(TEXT("total"), Tests.Num());
		Writer->WriteArrayStart(TEXT("tests"));
		for (int32 Index = 0; Index < Tests.Num() && Index < Limit; ++Index)
		{
			const FAutomationTestInfo& Test = Tests[Index];
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("display_name"), Test.GetDisplayName());
			Writer->WriteValue(TEXT("full_path"), Test.GetFullTestPath());
			Writer->WriteValue(TEXT("test_name"), Test.GetTestName());
			Writer->WriteValue(TEXT("tags"), Test.GetTestTags());
			Writer->WriteValue(TEXT("participants"), Test.GetNumParticipantsRequired());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/editor/automation/status"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(AutomationStateJson(), TEXT("application/json"));
	});

	App->Post(TEXT("/editor/automation"), [](const FHttpContext<FEditorDiagnosticReq, FString>& C)
	{
		if (!IsInGameThread()) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Automation tests must start on the Unreal game thread"));
		const FEditorDiagnosticReq Body = C.RequestBody();
		const FString Operation = Body.Operation.ToLower();
		if (Operation == TEXT("stop"))
		{
			if (!GAutomationRun.bRunning) throw FValidationException(TEXT("No automation test is running"));
			FinishAutomationRun(true);
			return C.TextResponse(AutomationStateJson(), TEXT("application/json"));
		}
		if (Operation != TEXT("run")) throw FValidationException(TEXT("operation must be run or stop"));
		if (GAutomationRun.bRunning) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Automation busy"), TEXT("An automation test is already running"));
		if (Body.TestName.IsEmpty()) throw FValidationException(TEXT("test_name is required"));

		FAutomationTestFramework& Framework = FAutomationTestFramework::Get();
		Framework.LoadTestModules();
		TArray<FAutomationTestInfo> Tests;
		Framework.GetValidTestNames(Tests);
		const FAutomationTestInfo* Test = Tests.FindByPredicate([&Body](const FAutomationTestInfo& Candidate)
		{
			return Candidate.GetFullTestPath() == Body.TestName || Candidate.GetTestName() == Body.TestName;
		});
		if (!Test) throw FValidationException(TEXT("test_name must exactly match a discovered automation test"));
		if (Test->GetNumParticipantsRequired() > 1) throw FValidationException(TEXT("Multi-participant automation tests are not supported by the local route"));
		FString Reason;
		bool bWarn = false;
		if (!Framework.CanRunTestInEnvironment(Test->GetTestName(), &Reason, &bWarn)) throw FValidationException(Reason);

		GAutomationRun = FAutomationRunState {};
		GAutomationRun.TestName = Test->GetFullTestPath();
		GAutomationRun.bRunning = true;
		Framework.StartTestByName(Test->GetTestName(), 0, Test->GetFullTestPath());
		GAutomationRun.TickerHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
		{
			if (!GAutomationRun.bRunning) return false;
			FAutomationTestFramework& ActiveFramework = FAutomationTestFramework::Get();
			const bool bLatentComplete = ActiveFramework.ExecuteLatentCommands();
			const bool bExecutedNetworkCommand = ActiveFramework.ExecuteNetworkCommands();
			if (bLatentComplete && !bExecutedNetworkCommand && ActiveFramework.IsLatentCommandQueueEmpty())
			{
				FinishAutomationRun(false);
				return false;
			}
			return true;
		}));
		return C.TextResponse(AutomationStateJson(), TEXT("application/json"));
	});

	App->Get(TEXT("/editor/screenshots"), [](const FHttpContext<void, FString>& C)
	{
		const bool bExists = !GLastScreenshotPath.IsEmpty() && FPaths::FileExists(GLastScreenshotPath);
		const int64 Size = bExists ? IFileManager::Get().FileSize(*GLastScreenshotPath) : -1;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("requested"), FScreenshotRequest::IsScreenshotRequested());
		Writer->WriteValue(TEXT("complete"), bExists);
		Writer->WriteValue(TEXT("path"), GLastScreenshotPath);
		Writer->WriteValue(TEXT("size_bytes"), Size);
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/editor/screenshots"), [](const FHttpContext<FEditorDiagnosticReq, FString>& C)
	{
		if (!IsInGameThread()) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Screenshots must be requested on the Unreal game thread"));
		if (FScreenshotRequest::IsScreenshotRequested()) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Screenshot busy"), TEXT("A screenshot request is already pending"));
		const FEditorDiagnosticReq Body = C.RequestBody();
		FString Name = FPaths::GetBaseFilename(Body.Filename.IsEmpty() ? TEXT("UE5MCP_Screenshot") : Body.Filename);
		Name = FPaths::MakeValidFileName(Name, TEXT('_'));
		const FString Directory = FPaths::Combine(FPaths::ScreenShotDir(), TEXT("UE5MCP"));
		IFileManager::Get().MakeDirectory(*Directory, true);
		GLastScreenshotPath = FPaths::Combine(Directory, Name + TEXT(".png"));
		FScreenshotRequest::RequestScreenshot(GLastScreenshotPath, Body.bShowUI, false);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("requested"), true);
		Writer->WriteValue(TEXT("path"), GLastScreenshotPath);
		Writer->WriteValue(TEXT("world_context"), FPlayWorldCommandCallbacks::HasPlayWorld() ? TEXT("pie") : TEXT("editor"));
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/editor/compile"), [](const FHttpContext<FProjectValidationReq, FString>& C)
	{
		if (!IsInGameThread()) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Blueprint compilation must run on the Unreal game thread"));
		const FProjectValidationReq Body = C.RequestBody();
		TArray<FString> Paths = Body.AssetPaths;
		if (Paths.IsEmpty())
		{
			TArray<FAssetData> Selected;
			ContentBrowser().GetSelectedAssets(Selected);
			for (const FAssetData& Asset : Selected) Paths.Add(Asset.GetObjectPathString());
		}
		if (Paths.IsEmpty()) throw FValidationException(TEXT("asset_paths must contain at least one Blueprint, or select Blueprints in the Content Browser"));
		Paths.Sort();
		Paths.SetNum(Algo::Unique(Paths));

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("compile_type"), TEXT("blueprint"));
		Writer->WriteArrayStart(TEXT("results"));
		int32 Failed = 0;
		for (const FString& Path : Paths)
		{
			UBlueprint* Blueprint = Cast<UBlueprint>(StaticLoadObject(UBlueprint::StaticClass(), nullptr, *Path));
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("asset_path"), Path);
			if (!Blueprint)
			{
				Writer->WriteValue(TEXT("success"), false);
				Writer->WriteValue(TEXT("error"), TEXT("Asset is not a Blueprint or could not be loaded"));
				++Failed;
			}
			else
			{
				const bool bSuccess = DebugFeedbackUtils::CompileAndWrite(Blueprint, Writer);
				Writer->WriteValue(TEXT("success"), bSuccess);
				Writer->WriteValue(TEXT("status"), BlueprintStatusName(Blueprint->Status));
				if (!bSuccess) ++Failed;
				if (Body.bSave && bSuccess)
				{
					UEditorAssetSubsystem* Assets = GEditor->GetEditorSubsystem<UEditorAssetSubsystem>();
					Writer->WriteValue(TEXT("saved"), Assets && Assets->SaveLoadedAsset(Blueprint, false));
				}
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("success"), Failed == 0);
		Writer->WriteValue(TEXT("failed"), Failed);
		Writer->WriteValue(TEXT("note"), TEXT("This route compiles Blueprints only and does not claim C++ hot reload status"));
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/editor/build-status"), [](const FHttpContext<void, FString>& C)
	{
		const int32 RemainingAssets = FAssetCompilingManager::Get().GetNumRemainingAssets();
		const int32 RemainingShaders = GShaderCompilingManager ? GShaderCompilingManager->GetNumRemainingJobs() : 0;
		const bool bFixupRunning = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get().IsFixupReferencersInProgress();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_compilation_remaining"), RemainingAssets);
		Writer->WriteValue(TEXT("shader_jobs_remaining"), RemainingShaders);
		Writer->WriteValue(TEXT("redirector_fixup_running"), bFixupRunning);
		Writer->WriteValue(TEXT("automation_running"), GAutomationRun.bRunning);
		Writer->WriteValue(TEXT("pie_running"), FPlayWorldCommandCallbacks::HasPlayWorld());
		Writer->WriteValue(TEXT("busy"), RemainingAssets > 0 || RemainingShaders > 0 || bFixupRunning || GAutomationRun.bRunning);
		Writer->WriteValue(TEXT("cxx_compile_status"), DebugFeedbackUtils::CxxCompileStatus());
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/editor/asset-audit"), [](const FHttpContext<FProjectValidationReq, FString>& C)
	{
		const FProjectValidationReq Body = C.RequestBody();
		TArray<FAssetData> Assets;
		if (!Body.AssetPaths.IsEmpty())
		{
			for (const FString& Path : Body.AssetPaths) Assets.Add(FindAssetData(Path));
		}
		else
		{
			if (!FPackageName::IsValidPath(Body.DirectoryPath)) throw FValidationException(TEXT("directory_path must be a valid mounted Unreal content path"));
			FARFilter Filter;
			Filter.PackagePaths.Add(FName(*Body.DirectoryPath));
			Filter.bRecursivePaths = Body.bRecursive;
			EditorAssetRegistry().GetAssets(Filter, Assets);
		}
		Assets.Sort([](const FAssetData& Left, const FAssetData& Right) { return Left.GetObjectPathString() < Right.GetObjectPathString(); });

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_count"), Assets.Num());
		Writer->WriteArrayStart(TEXT("assets"));
		int32 MissingTotal = 0;
		for (const FAssetData& Asset : Assets)
		{
			TArray<FName> Dependencies;
			TArray<FName> Referencers;
			EditorAssetRegistry().GetDependencies(Asset.PackageName, Dependencies);
			EditorAssetRegistry().GetReferencers(Asset.PackageName, Referencers);
			Dependencies.Sort(FNameLexicalLess());
			Referencers.Sort(FNameLexicalLess());
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("object_path"), Asset.GetObjectPathString());
			Writer->WriteValue(TEXT("package_path"), Asset.PackageName.ToString());
			Writer->WriteValue(TEXT("class"), Asset.AssetClassPath.ToString());
			Writer->WriteValue(TEXT("redirector"), Asset.AssetClassPath == UObjectRedirector::StaticClass()->GetClassPathName());
			Writer->WriteArrayStart(TEXT("dependencies"));
			for (const FName Dependency : Dependencies) Writer->WriteValue(Dependency.ToString());
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("missing_dependencies"));
			for (const FName Dependency : Dependencies)
			{
				const FString DependencyPath = Dependency.ToString();
				if (!DependencyPath.StartsWith(TEXT("/Script/")) && !FPackageName::DoesPackageExist(DependencyPath))
				{
					Writer->WriteValue(DependencyPath);
					++MissingTotal;
				}
			}
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("referencers"));
			for (const FName Referencer : Referencers) Writer->WriteValue(Referencer.ToString());
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("missing_dependency_count"), MissingTotal);
		Writer->WriteValue(TEXT("valid"), MissingTotal == 0);
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/editor/fixup-redirectors"), [](const FHttpContext<FProjectValidationReq, FString>& C)
	{
		const FProjectValidationReq Body = C.RequestBody();
		if (!Body.bConfirm) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Confirmation required"), TEXT("Redirector fix-up modifies referencers and deletes fixed redirectors; bConfirm=true is required"));
		IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get();
		if (AssetTools.IsFixupReferencersInProgress()) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Fix-up busy"), TEXT("A redirector fix-up is already running"));

		TArray<FAssetData> RedirectorAssets;
		if (!Body.AssetPaths.IsEmpty())
		{
			for (const FString& Path : Body.AssetPaths)
			{
				const FAssetData Asset = FindAssetData(Path);
				if (Asset.AssetClassPath != UObjectRedirector::StaticClass()->GetClassPathName()) throw FValidationException(FString::Printf(TEXT("Asset is not a redirector: %s"), *Path));
				RedirectorAssets.Add(Asset);
			}
		}
		else
		{
			FARFilter Filter;
			Filter.PackagePaths.Add(FName(*Body.DirectoryPath));
			Filter.ClassPaths.Add(UObjectRedirector::StaticClass()->GetClassPathName());
			Filter.bRecursivePaths = Body.bRecursive;
			EditorAssetRegistry().GetAssets(Filter, RedirectorAssets);
		}
		TArray<UObjectRedirector*> Redirectors;
		for (const FAssetData& Asset : RedirectorAssets)
			if (UObjectRedirector* Redirector = Cast<UObjectRedirector>(Asset.GetAsset())) Redirectors.Add(Redirector);
		if (!RedirectorAssets.IsEmpty() && Redirectors.IsEmpty()) throw std::runtime_error("Redirectors were discovered but could not be loaded");
		AssetTools.FixupReferencers(Redirectors, false, ERedirectFixupMode::DeleteFixedUpRedirectors);

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("requested"), Redirectors.Num());
		Writer->WriteValue(TEXT("in_progress"), AssetTools.IsFixupReferencersInProgress());
		Writer->WriteValue(TEXT("complete"), !AssetTools.IsFixupReferencersInProgress());
		Writer->WriteValue(TEXT("note"), TEXT("Completion is reported only from AssetTools fix-up state"));
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	// Play-In-Editor control. The engine starts the queued session on its next tick, so callers poll /editor/status
	// (is_playing) after start. In-process PIE; no new window settings are changed.
	App->Post(TEXT("/editor/pie/start"), [](const FHttpContext<void, FActionResponse>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		if (GEditor->PlayWorld || GEditor->IsPlaySessionRequestQueued() || GEditor->IsPlaySessionInProgress()) throw std::runtime_error("A play session is already running or queued");
		FRequestPlaySessionParams Params;
		Params.WorldType = EPlaySessionWorldType::PlayInEditor;
		Params.SessionDestination = EPlaySessionDestinationType::InProcess;
		GEditor->RequestPlaySession(Params);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/pie/stop"), [](const FHttpContext<void, FActionResponse>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		if (!GEditor->PlayWorld && !GEditor->IsPlaySessionRequestQueued()) throw std::runtime_error("No play session is running");
		GEditor->RequestEndPlayMap();
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/transactions/undo"), [](const FHttpContext<void, FActionResponse>& C)
	{
		if (!GEditor || !GEditor->UndoTransaction()) throw std::runtime_error("There is no editor transaction to undo");
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/transactions/redo"), [](const FHttpContext<void, FActionResponse>& C)
	{
		if (!GEditor || !GEditor->RedoTransaction()) throw std::runtime_error("There is no editor transaction to redo");
		return C.JsonResponse(FActionResponse {});
	});

	App->Get(TEXT("/editor/actors"), [](const FHttpContext<void, FString>& C)
	{
		const FString Search = C.Query(TEXT("search"));
		const FString ClassFilter = C.Query(TEXT("class_path"));
		const int32 Limit = QueryLimit(C);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		int32 Count = 0;
		for (AActor* Actor : ActorSubsystem()->GetAllLevelActors())
		{
			if (!Actor || (!Search.IsEmpty() && !Actor->GetActorLabel().Contains(Search, ESearchCase::IgnoreCase) && !Actor->GetName().Contains(Search, ESearchCase::IgnoreCase)) || (!ClassFilter.IsEmpty() && Actor->GetClass()->GetPathName() != ClassFilter)) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Actor->GetName());
			Writer->WriteValue(TEXT("label"), Actor->GetActorLabel());
			Writer->WriteValue(TEXT("path"), Actor->GetPathName());
			Writer->WriteValue(TEXT("class"), Actor->GetClass()->GetPathName());
			Writer->WriteValue(TEXT("level"), Actor->GetLevel() ? Actor->GetLevel()->GetPathName() : TEXT(""));
			const FVector Location = Actor->GetActorLocation();
			const FRotator Rotation = Actor->GetActorRotation();
			Writer->WriteObjectStart(TEXT("location"));
			Writer->WriteValue(TEXT("X"), Location.X); Writer->WriteValue(TEXT("Y"), Location.Y); Writer->WriteValue(TEXT("Z"), Location.Z);
			Writer->WriteObjectEnd();
			Writer->WriteObjectStart(TEXT("rotation"));
			Writer->WriteValue(TEXT("Pitch"), Rotation.Pitch); Writer->WriteValue(TEXT("Yaw"), Rotation.Yaw); Writer->WriteValue(TEXT("Roll"), Rotation.Roll);
			Writer->WriteObjectEnd();
			Writer->WriteObjectEnd();
			if (++Count >= Limit) break;
		}
		Writer->WriteArrayEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/world/inspect"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(InspectWorldJson(TEXT("")), TEXT("application/json"));
	});

	App->Post(TEXT("/worlds/composition/tiles/hierarchy"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::InspectCompositionTileHierarchy(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/composition/tiles/lod-list"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetCompositionTileLODList(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/composition/tiles/lod-distance"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetCompositionTileLODDistance(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/composition/tiles/display"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetCompositionTileDisplay(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/composition/tiles/layer"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetCompositionTileLayer(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/composition/setting"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetCompositionSetting(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/composition/tiles/inspect"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::InspectCompositionTiles(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/method"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODLevelMethod(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/boolean"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODLevelBool(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-string"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedString(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-color"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedColor(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-int-point"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedIntPoint(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-name"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedName(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-object"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedObject(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-enum"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedEnum(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-boolean"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedBool(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/nested-numeric"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODNestedNumeric(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/numeric"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODLevelNumeric(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/fields"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::InspectLegacyHLODFields(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/duplicate"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::DuplicateLegacyHLODLevel(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/reorder"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::ReorderLegacyHLODLevels(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/remove"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::RemoveLegacyHLODLevel(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/reset"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::ResetLegacyHLODLevel(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/add"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::AddLegacyHLODLevel(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-actors/inspect"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::InspectLegacyLODActors(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-setup-classes/inspect"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::InspectLegacyHLODSetupClasses(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-material-override"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODMaterialOverride(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-setup-override"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::SetLegacyHLODSetupOverride(C.RequestBody()),TEXT("application/json")); });
	App->Post(TEXT("/worlds/settings/hlod-levels/inspect"), [](const FHttpContext<FWorldSettingsReq,FString>& C) { return C.TextResponse(WorldSettingsUtils::InspectLegacyHLODLevels(C.RequestBody()),TEXT("application/json")); });
	App->Get(TEXT("/worlds/settings"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(WorldSettingsUtils::Inspect(), TEXT("application/json"));
	});
	App->Get(TEXT("/navigation/inspect"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(NavigationUtils::Inspect(), TEXT("application/json"));
	});
	App->Get(TEXT("/navigation/filters"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(NavigationFilterUtils::Inspect(C.Query(TEXT("asset_path"))), TEXT("application/json"));
	});
	App->Get(TEXT("/navigation/areas"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(NavigationAreaUtils::Inspect(C.Query(TEXT("asset_path"))), TEXT("application/json"));
	});
	App->Get(TEXT("/navigation/links"), [](const FHttpContext<void, FString>& C)
	{
		int32 PIEInstance=-1; if(!LexTryParseString(PIEInstance,*C.Query(TEXT("pie_instance"),TEXT("-1")))) throw std::runtime_error("pie_instance must be an integer");
		return C.TextResponse(NavigationLinkUtils::Inspect(C.Query(TEXT("actor_path")),C.Query(TEXT("world_context"),TEXT("editor")),PIEInstance), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/agents"), [](const FHttpContext<FNavigationAgentReq,FString>& C)
	{
		return C.TextResponse(NavigationAgentUtils::Control(C.RequestBody()),TEXT("application/json"));
	});
	App->Get(TEXT("/navigation/agents"), [](const FHttpContext<void,FString>& C)
	{
		int32 PIEInstance=-1,Limit=100; uint64 After=0;
		const FString Cursor=C.Query(TEXT("after_sequence"),TEXT("0"));
		if(!LexTryParseString(PIEInstance,*C.Query(TEXT("pie_instance"),TEXT("-1"))) || !LexTryParseString(Limit,*C.Query(TEXT("limit"),TEXT("100"))) || Cursor.StartsWith(TEXT("-")) || !LexTryParseString(After,*Cursor)) throw std::runtime_error("Invalid probe paging or PIE instance");
		return C.TextResponse(NavigationAgentUtils::Inspect(C.Query(TEXT("probe_id")),PIEInstance,After,Limit),TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/links"), [](const FHttpContext<FNavigationLinkReq, FString>& C)
	{
		return C.TextResponse(NavigationLinkUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/smart-links"), [](const FHttpContext<FNavigationLinkReq, FString>& C)
	{
		return C.TextResponse(NavigationLinkUtils::Smart(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/areas"), [](const FHttpContext<FNavigationAreaReq, FString>& C)
	{
		return C.TextResponse(NavigationAreaUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/filters"), [](const FHttpContext<FNavigationFilterReq, FString>& C)
	{
		return C.TextResponse(NavigationFilterUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/bounds"), [](const FHttpContext<FNavigationReq, FString>& C)
	{
		return C.TextResponse(NavigationUtils::Bounds(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/modifiers"), [](const FHttpContext<FNavigationReq, FString>& C)
	{
		return C.TextResponse(NavigationUtils::Modifiers(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/build"), [](const FHttpContext<FNavigationReq, FString>& C)
	{
		return C.TextResponse(NavigationUtils::Build(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/navigation/query"), [](const FHttpContext<FNavigationReq, FString>& C)
	{
		return C.TextResponse(NavigationUtils::Query(C.RequestBody()), TEXT("application/json"));
	});
	App->Patch(TEXT("/worlds/settings"), [](const FHttpContext<FWorldSettingsReq, FString>& C)
	{
		return C.TextResponse(WorldSettingsUtils::Update(C.RequestBody()), TEXT("application/json"));
	});

	App->Get(TEXT("/worlds/inspect"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(InspectWorldJson(C.Query(TEXT("world_path"))), TEXT("application/json"));
	});

	App->Get(TEXT("/worlds/list"), [](const FHttpContext<void, FString>& C)
	{
		const FString DirectoryPath = C.Query(TEXT("directory_path"), TEXT("/Game"));
		if (!FPackageName::IsValidPath(DirectoryPath))
			throw FValidationException(TEXT("directory_path must be a valid mounted Unreal content path"));
		const bool bRecursive = C.Query(TEXT("recursive"), TEXT("true")).Equals(TEXT("true"), ESearchCase::IgnoreCase);
		const FString Search = C.Query(TEXT("search"));
		const int32 Limit = QueryLimit(C);
		int32 Offset = 0;
		LexTryParseString(Offset, *C.Query(TEXT("offset"), TEXT("0")));
		Offset = FMath::Max(0, Offset);

		FARFilter Filter;
		Filter.PackagePaths.Add(FName(*DirectoryPath));
		Filter.ClassPaths.Add(UWorld::StaticClass()->GetClassPathName());
		Filter.bRecursivePaths = bRecursive;
		Filter.bRecursiveClasses = true;
		TArray<FAssetData> Assets;
		EditorAssetRegistry().GetAssets(Filter, Assets);
		Assets.RemoveAll([&Search](const FAssetData& Asset)
		{
			return !Search.IsEmpty() && !Asset.AssetName.ToString().Contains(Search, ESearchCase::IgnoreCase)
				&& !Asset.PackageName.ToString().Contains(Search, ESearchCase::IgnoreCase);
		});
		Assets.Sort([](const FAssetData& Left, const FAssetData& Right)
		{
			return Left.PackageName.LexicalLess(Right.PackageName);
		});

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("total"), Assets.Num());
		Writer->WriteValue(TEXT("offset"), Offset);
		Writer->WriteValue(TEXT("limit"), Limit);
		Writer->WriteArrayStart(TEXT("worlds"));
		for (int32 Index = Offset; Index < Assets.Num() && Index < Offset + Limit; ++Index)
		{
			const FAssetData& Asset = Assets[Index];
			FString Filename;
			FPackageName::TryConvertLongPackageNameToFilename(Asset.PackageName.ToString(), Filename, FPackageName::GetMapPackageExtension());
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Asset.AssetName.ToString());
			Writer->WriteValue(TEXT("package_path"), Asset.PackageName.ToString());
			Writer->WriteValue(TEXT("object_path"), Asset.GetObjectPathString());
			Writer->WriteValue(TEXT("mount_point"), FPackageName::GetPackageMountPoint(Asset.PackageName.ToString()).ToString());
			Writer->WriteValue(TEXT("file_exists"), FPaths::FileExists(Filename));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/world/save"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World) throw std::runtime_error("No editor world is available");
		if (!UEditorLoadingAndSavingUtils::SaveMap(World, World->GetOutermost()->GetName()))
			throw std::runtime_error("Failed to save the current editor world");
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/worlds/save"), [](const FHttpContext<FWorldOperationReq, FWorldOperationResponse>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		if (!IsInGameThread())
			throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Editor-world mutations must execute on the Unreal game thread"));
		const FWorldOperationReq Body = C.RequestBody();
		FWorldMutationGuard MutationGuard;
		UWorld* World = GEditor->GetEditorWorldContext().World();
		if (!World) throw std::runtime_error("No editor world is available");

		FWorldOperationResponse Response;
		Response.Operation = Body.bSaveAs ? TEXT("save_as") : TEXT("save");
		Response.PreviousWorldPath = World->GetPathName();
		const FString CurrentPackagePath = World->GetOutermost()->GetName();
		FString PackagePath = CurrentPackagePath;
		if (!Body.WorldPath.IsEmpty())
		{
			PackagePath = NormalizeNewWorldPackagePath(Body.WorldPath);
			if (PackagePath != CurrentPackagePath && !Body.bSaveAs)
				throw FValidationException(TEXT("bSaveAs=true is required when world_path differs from the active map"));
			if (PackagePath != CurrentPackagePath && FPackageName::DoesPackageExist(PackagePath) && !Body.bConfirm)
			{
				Response.Errors.Add(TEXT("The save-as target already exists; retry with bConfirm=true to replace it"));
				SetWorldState(Response, World);
				return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::Conflict);
			}
		}
		if (!UEditorLoadingAndSavingUtils::SaveMap(World, PackagePath))
		{
			Response.Errors.Add(TEXT("Failed to save the current editor world"));
			SetWorldState(Response, World);
			return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::ServerError);
		}
		if (!FPackageName::DoesPackageExist(PackagePath))
			throw std::runtime_error("The editor reported a successful map save but the package does not exist on disk");
		Response.Success = true;
		Response.bSaved = true;
		Response.SavedPackages.Add(PackagePath);
		SetWorldState(Response, GEditor->GetEditorWorldContext().World());
		return C.JsonResponse(MoveTemp(Response));
	});

	App->Post(TEXT("/worlds/create"), [](const FHttpContext<FWorldOperationReq, FWorldOperationResponse>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		if (FPlayWorldCommandCallbacks::HasPlayWorld())
			throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Play session active"), TEXT("Stop the play session before creating another map"));
		if (!IsInGameThread())
			throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Editor-world mutations must execute on the Unreal game thread"));

		const FWorldOperationReq Body = C.RequestBody();
		const FString TargetPackagePath = NormalizeNewWorldPackagePath(Body.WorldPath);
		FString TemplateFilename;
		if (!Body.TemplatePath.IsEmpty())
		{
			const FString TemplatePackagePath = NormalizeWorldPackagePath(Body.TemplatePath);
			FPackageName::TryConvertLongPackageNameToFilename(TemplatePackagePath, TemplateFilename, FPackageName::GetMapPackageExtension());
		}

		FWorldMutationGuard MutationGuard;
		FWorldOperationResponse Response;
		Response.Operation = TEXT("create");
		if (UWorld* CurrentWorld = GEditor->GetEditorWorldContext().World())
			Response.PreviousWorldPath = CurrentWorld->GetPathName();

		if (FPackageName::DoesPackageExist(TargetPackagePath) && !Body.bConfirm)
		{
			Response.Errors.Add(TEXT("The target map already exists; retry with bConfirm=true to replace it"));
			return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::Conflict);
		}

		TArray<UPackage*> DirtyMapPackages;
		TArray<UPackage*> DirtyContentPackages;
		FEditorFileUtils::GetDirtyWorldPackages(DirtyMapPackages);
		FEditorFileUtils::GetDirtyContentPackages(DirtyContentPackages);
		Response.DirtyMapPackages = PackageNames(DirtyMapPackages);
		Response.DirtyContentPackages = PackageNames(DirtyContentPackages);
		const bool bHasDirtyPackages = !Response.DirtyMapPackages.IsEmpty() || !Response.DirtyContentPackages.IsEmpty();
		FString DirtyPolicy = Body.DirtyPolicy.ToLower();
		if (DirtyPolicy.IsEmpty()) DirtyPolicy = Body.bConfirm ? TEXT("discard") : TEXT("fail");
		if (DirtyPolicy != TEXT("fail") && DirtyPolicy != TEXT("save") && DirtyPolicy != TEXT("discard"))
			throw FValidationException(TEXT("dirty_policy must be one of: fail, save, discard"));
		if (bHasDirtyPackages && DirtyPolicy == TEXT("fail"))
		{
			Response.Errors.Add(TEXT("Unsaved packages must be saved or explicitly discarded before creating another map"));
			return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::Conflict);
		}
		if (bHasDirtyPackages && DirtyPolicy == TEXT("discard") && !Body.bConfirm)
		{
			Response.Errors.Add(TEXT("dirty_policy=discard requires bConfirm=true"));
			return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::Conflict);
		}
		if (bHasDirtyPackages && DirtyPolicy == TEXT("save"))
		{
			if (!UEditorLoadingAndSavingUtils::SaveDirtyPackages(true, true))
			{
				Response.Errors.Add(TEXT("One or more dirty packages could not be saved; map creation was aborted"));
				return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::ServerError);
			}
			Response.bSaved = true;
			Response.SavedPackages.Append(Response.DirtyMapPackages);
			Response.SavedPackages.Append(Response.DirtyContentPackages);
		}
		else if (bHasDirtyPackages)
		{
			Response.Warnings.Add(TEXT("The map was created after explicitly accepting the risk of discarding unsaved changes"));
		}

		UWorld* NewWorld = TemplateFilename.IsEmpty()
			? UEditorLoadingAndSavingUtils::NewBlankMap(false)
			: UEditorLoadingAndSavingUtils::NewMapFromTemplate(TemplateFilename, false);
		if (!NewWorld)
			throw std::runtime_error("Failed to create the editor world");
		if (Body.bSave)
		{
			if (!UEditorLoadingAndSavingUtils::SaveMap(NewWorld, TargetPackagePath))
			{
				Response.Errors.Add(TEXT("The map was created but could not be saved at the requested path"));
				SetWorldState(Response, NewWorld);
				return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::ServerError);
			}
			if (!FPackageName::DoesPackageExist(TargetPackagePath))
				throw std::runtime_error("The editor reported a successful map save but the package does not exist on disk");
			Response.bSaved = true;
			Response.SavedPackages.Add(TargetPackagePath);
		}
		Response.Success = true;
		SetWorldState(Response, GEditor->GetEditorWorldContext().World());
		Response.ChangedPackages.Add(Response.PackagePath);
		return C.JsonResponse(MoveTemp(Response));
	});

	App->Post(TEXT("/worlds/validate"), [](const FHttpContext<FWorldOperationReq, FString>& C)
	{
		const FWorldOperationReq Body = C.RequestBody();
		const FString PackagePath = NormalizeWorldPackagePath(Body.WorldPath);
		const FAssetData Asset = FindWorldAsset(PackagePath);
		TArray<FString> Dependencies;
		TArray<FString> MissingDependencies;
		if (Body.bLoadDependencies)
		{
			TArray<FName> DependencyNames;
			EditorAssetRegistry().GetDependencies(FName(*PackagePath), DependencyNames);
			for (const FName DependencyName : DependencyNames)
			{
				const FString Dependency = DependencyName.ToString();
				Dependencies.Add(Dependency);
				if (!Dependency.StartsWith(TEXT("/Script/")) && !FPackageName::DoesPackageExist(Dependency))
					MissingDependencies.Add(Dependency);
			}
			Dependencies.Sort();
			MissingDependencies.Sort();
		}

		int32 MapCheckErrors = 0;
		int32 MapCheckWarnings = 0;
		FString MapCheckNote;
		UWorld* ActiveWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		const bool bActive = ActiveWorld && ActiveWorld->GetOutermost()->GetName() == PackagePath;
		if (Body.bRunMapCheck)
		{
			if (!bActive)
			{
				MapCheckNote = TEXT("Map Check was not run because the requested map is not the active editor world");
			}
			else
			{
				if (!IsInGameThread())
					throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Map Check must execute on the Unreal game thread"));
				GEditor->Exec(ActiveWorld, TEXT("MAP CHECK DONTDISPLAYDIALOG"));
				FMessageLog MapCheckLog(TEXT("MapCheck"));
				MapCheckErrors = MapCheckLog.NumMessages(EMessageSeverity::Error);
				MapCheckWarnings = FMath::Max(0, MapCheckLog.NumMessages(EMessageSeverity::Warning) - MapCheckErrors);
			}
		}

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), MissingDependencies.IsEmpty() && MapCheckErrors == 0);
		Writer->WriteValue(TEXT("package_path"), PackagePath);
		Writer->WriteValue(TEXT("object_path"), Asset.GetObjectPathString());
		Writer->WriteValue(TEXT("active"), bActive);
		Writer->WriteValue(TEXT("map_check_errors"), MapCheckErrors);
		Writer->WriteValue(TEXT("map_check_warnings"), MapCheckWarnings);
		Writer->WriteValue(TEXT("map_check_note"), MapCheckNote);
		Writer->WriteArrayStart(TEXT("dependencies"));
		for (const FString& Dependency : Dependencies) Writer->WriteValue(Dependency);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("missing_dependencies"));
		for (const FString& Missing : MissingDependencies) Writer->WriteValue(Missing);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/worlds/load"), [](const FHttpContext<FWorldOperationReq, FWorldOperationResponse>& C)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		if (FPlayWorldCommandCallbacks::HasPlayWorld())
			throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Play session active"), TEXT("Stop the play session before loading another map"));
		if (!IsInGameThread())
			throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Game thread required"), TEXT("Editor-world mutations must execute on the Unreal game thread"));

		const FWorldOperationReq Body = C.RequestBody();
		const FString PackagePath = NormalizeWorldPackagePath(Body.WorldPath);
		FString DirtyPolicy = Body.DirtyPolicy.ToLower();
		if (DirtyPolicy.IsEmpty())
			DirtyPolicy = Body.bConfirm ? TEXT("discard") : TEXT("fail");
		if (DirtyPolicy != TEXT("fail") && DirtyPolicy != TEXT("save") && DirtyPolicy != TEXT("discard"))
			throw FValidationException(TEXT("dirty_policy must be one of: fail, save, discard"));

		FWorldMutationGuard MutationGuard;
		FWorldOperationResponse Response;
		Response.Operation = TEXT("load");
		if (UWorld* CurrentWorld = GEditor->GetEditorWorldContext().World())
			Response.PreviousWorldPath = CurrentWorld->GetPathName();

		TArray<UPackage*> DirtyMapPackages;
		TArray<UPackage*> DirtyContentPackages;
		FEditorFileUtils::GetDirtyWorldPackages(DirtyMapPackages);
		FEditorFileUtils::GetDirtyContentPackages(DirtyContentPackages);
		Response.DirtyMapPackages = PackageNames(DirtyMapPackages);
		Response.DirtyContentPackages = PackageNames(DirtyContentPackages);
		const bool bHasDirtyPackages = !Response.DirtyMapPackages.IsEmpty() || !Response.DirtyContentPackages.IsEmpty();

		if (bHasDirtyPackages && DirtyPolicy == TEXT("fail"))
		{
			Response.Errors.Add(TEXT("Unsaved packages must be saved or explicitly discarded before loading another map"));
			return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::Conflict);
		}
		if (bHasDirtyPackages && DirtyPolicy == TEXT("discard") && !Body.bConfirm)
		{
			Response.Errors.Add(TEXT("dirty_policy=discard requires bConfirm=true"));
			return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::Conflict);
		}
		if (bHasDirtyPackages && DirtyPolicy == TEXT("save"))
		{
			if (!UEditorLoadingAndSavingUtils::SaveDirtyPackages(true, true))
			{
				Response.Errors.Add(TEXT("One or more dirty packages could not be saved; map loading was aborted"));
				return C.JsonResponse(MoveTemp(Response), EHttpServerResponseCodes::ServerError);
			}
			Response.bSaved = true;
			Response.SavedPackages.Append(Response.DirtyMapPackages);
			Response.SavedPackages.Append(Response.DirtyContentPackages);
		}
		else if (bHasDirtyPackages && DirtyPolicy == TEXT("discard"))
		{
			Response.Warnings.Add(TEXT("The map was loaded after explicitly accepting the risk of discarding unsaved changes"));
		}

		FString Filename;
		FPackageName::TryConvertLongPackageNameToFilename(PackagePath, Filename, FPackageName::GetMapPackageExtension());
		UWorld* LoadedWorld = UEditorLoadingAndSavingUtils::LoadMap(Filename);
		if (!LoadedWorld)
			throw std::runtime_error("Failed to load the requested editor world");
		Response.Success = true;
		SetWorldState(Response, GEditor->GetEditorWorldContext().World());
		return C.JsonResponse(MoveTemp(Response));
	});

	App->Get(TEXT("/worlds/partition"), [](const FHttpContext<void, FString>& C)
	{
		UWorld* World = ActiveEditorWorld();
		UWorldPartition* Partition = World->GetWorldPartition();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("world_path"), World->GetPathName());
		Writer->WriteValue(TEXT("partitioned"), Partition != nullptr);
		Writer->WriteValue(TEXT("streaming_enabled"), Partition && Partition->IsStreamingEnabled());
		Writer->WriteValue(TEXT("partition_path"), Partition ? Partition->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("external_actors"), World->PersistentLevel && World->PersistentLevel->IsUsingExternalActors());
		Writer->WriteValue(TEXT("data_layer_count"), World->GetDataLayerManager() ? World->GetDataLayerManager()->GetDataLayerInstances().Num() : 0);
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/worlds/data-layers"), [](const FHttpContext<void, FString>& C)
	{
		UWorld* World = ActiveEditorWorld();
		UDataLayerManager* Manager = World->GetDataLayerManager();
		TArray<UDataLayerInstance*> Layers = Manager ? Manager->GetDataLayerInstances() : TArray<UDataLayerInstance*>();
		Layers.Sort([](const UDataLayerInstance& Left, const UDataLayerInstance& Right) { return Left.GetDataLayerFullName() < Right.GetDataLayerFullName(); });
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("world_path"), World->GetPathName());
		Writer->WriteArrayStart(TEXT("data_layers"));
		for (UDataLayerInstance* Layer : Layers)
		{
			if (!Layer) continue;
			FText LockReason;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Layer->GetDataLayerFName().ToString());
			Writer->WriteValue(TEXT("short_name"), Layer->GetDataLayerShortName());
			Writer->WriteValue(TEXT("full_name"), Layer->GetDataLayerFullName());
			Writer->WriteValue(TEXT("path"), Layer->GetPathName());
			Writer->WriteValue(TEXT("parent"), Layer->GetParent() ? Layer->GetParent()->GetDataLayerFullName() : TEXT(""));
			Writer->WriteValue(TEXT("loaded_in_editor"), Layer->IsLoadedInEditor());
			Writer->WriteValue(TEXT("effectively_loaded"), Layer->IsEffectiveLoadedInEditor());
			Writer->WriteValue(TEXT("visible"), Layer->IsVisible());
			Writer->WriteValue(TEXT("effectively_visible"), Layer->IsEffectiveVisible());
			Writer->WriteValue(TEXT("runtime"), Layer->IsRuntime());
			Writer->WriteValue(TEXT("read_only"), Layer->IsReadOnly(&LockReason));
			Writer->WriteValue(TEXT("read_only_reason"), LockReason.ToString());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd(); Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/worlds/data-layers"), [](const FHttpContext<FWorldStructureReq, FActionResponse>& C)
	{
		const FWorldStructureReq Body = C.RequestBody();
		UWorld* World = ActiveEditorWorld();
		UDataLayerInstance* Layer = FindDataLayer(World, Body.DataLayerName);
		UDataLayerEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UDataLayerEditorSubsystem>();
		if (!Subsystem) throw std::runtime_error("Data Layer editor subsystem is unavailable");
		const FString Operation = Body.Operation.ToLower();
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditDataLayer", "Edit Data Layer State"));
		bool bChanged = true;
		if (Operation == TEXT("load")) bChanged = Subsystem->SetDataLayerIsLoadedInEditor(Layer, true, true);
		else if (Operation == TEXT("unload")) bChanged = Subsystem->SetDataLayerIsLoadedInEditor(Layer, false, true);
		else if (Operation == TEXT("show")) Subsystem->SetDataLayerVisibility(Layer, true);
		else if (Operation == TEXT("hide")) Subsystem->SetDataLayerVisibility(Layer, false);
		else if (Operation == TEXT("activate"))
		{
			bChanged = Subsystem->SetDataLayerIsLoadedInEditor(Layer, true, true);
			Subsystem->SetDataLayerVisibility(Layer, true);
		}
		else if (Operation == TEXT("deactivate"))
		{
			Subsystem->SetDataLayerVisibility(Layer, false);
			bChanged = Subsystem->SetDataLayerIsLoadedInEditor(Layer, false, true);
		}
		else throw FValidationException(TEXT("operation must be load, unload, show, hide, activate, or deactivate"));
		if (!bChanged && (Operation == TEXT("load") || Operation == TEXT("unload") || Operation == TEXT("activate") || Operation == TEXT("deactivate")))
			throw std::runtime_error("The requested Data Layer loading state could not be changed");
		World->GetOutermost()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Get(TEXT("/levels/instances"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(LevelInstanceUtils::Inspect(ActiveEditorWorld(), C.Query(TEXT("actor_path"))), TEXT("application/json"));
	});
	App->Get(TEXT("/levels/instances/validate"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(LevelInstanceUtils::Inspect(ActiveEditorWorld(), C.Query(TEXT("actor_path")), true), TEXT("application/json"));
	});
	App->Post(TEXT("/levels/instances/create"), [](const FHttpContext<FLevelInstanceReq, FString>& C)
	{
		FLevelInstanceReq Body = C.RequestBody(); Body.Operation = TEXT("create");
		return C.TextResponse(LevelInstanceUtils::Operate(ActiveEditorWorld(), Body), TEXT("application/json"));
	});
	App->Post(TEXT("/levels/instances/operation"), [](const FHttpContext<FLevelInstanceReq, FString>& C)
	{
		return C.TextResponse(LevelInstanceUtils::Operate(ActiveEditorWorld(), C.RequestBody()), TEXT("application/json"));
	});

	App->Get(TEXT("/levels/sublevels"), [](const FHttpContext<void, FString>& C)
	{
		UWorld* World = ActiveEditorWorld();
		TArray<ULevelStreaming*> Levels = World->GetStreamingLevels();
		Levels.Sort([](const ULevelStreaming& Left, const ULevelStreaming& Right) { return Left.GetWorldAssetPackageName() < Right.GetWorldAssetPackageName(); });
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("world_path"), World->GetPathName());
		Writer->WriteValue(TEXT("current_level_path"), GetPathNameSafe(World->GetCurrentLevel()));
		Writer->WriteArrayStart(TEXT("sublevels"));
		for (ULevelStreaming* Streaming : Levels)
		{
			if (!Streaming) continue;
			Writer->WriteObjectStart();
			auto WriteTransform = [&](const TCHAR* Key, const FTransform& T) { Writer->WriteObjectStart(Key); const FVector P=T.GetTranslation(),S=T.GetScale3D(); const FQuat Q=T.GetRotation(); auto Numbers=[&](const TCHAR* Name,std::initializer_list<double> Values) { Writer->WriteArrayStart(Name); for(double V:Values) { if(FMath::IsFinite(V)) Writer->WriteValue(V); else Writer->WriteNull(); } Writer->WriteArrayEnd(); }; Numbers(TEXT("translation"),{P.X,P.Y,P.Z}); Numbers(TEXT("rotation_quaternion_xyzw"),{Q.X,Q.Y,Q.Z,Q.W}); Numbers(TEXT("scale"),{S.X,S.Y,S.Z}); Writer->WriteObjectEnd(); };
			WriteTransform(TEXT("level_transform"), Streaming->LevelTransform);
			Writer->WriteValue(TEXT("streaming_volume_count"), Streaming->EditorStreamingVolumes.Num()); Writer->WriteArrayStart(TEXT("streaming_volume_paths")); for(int32 I=0;I<FMath::Min(128,Streaming->EditorStreamingVolumes.Num());++I) Writer->WriteValue(GetPathNameSafe(Streaming->EditorStreamingVolumes[I].Get())); Writer->WriteArrayEnd(); Writer->WriteValue(TEXT("streaming_volumes_truncated"), Streaming->EditorStreamingVolumes.Num()>128);
			Writer->WriteArrayStart(TEXT("level_color_rgba")); for(float V:{Streaming->LevelColor.R,Streaming->LevelColor.G,Streaming->LevelColor.B,Streaming->LevelColor.A}) { if(FMath::IsFinite(V)) Writer->WriteValue(double(V)); else Writer->WriteNull(); } Writer->WriteArrayEnd();
			Writer->WriteValue(TEXT("block_on_load"),bool(Streaming->bShouldBlockOnLoad)); Writer->WriteValue(TEXT("block_on_unload"),bool(Streaming->bShouldBlockOnUnload)); Writer->WriteValue(TEXT("draw_on_level_status_map"),bool(Streaming->bDrawOnLevelStatusMap));
			Writer->WriteValue(TEXT("streaming_priority"), Streaming->GetPriority());
			if(FMath::IsFinite(Streaming->MinTimeBetweenVolumeUnloadRequests)) Writer->WriteValue(TEXT("volume_unload_cooldown"),double(Streaming->MinTimeBetweenVolumeUnloadRequests)); else Writer->WriteNull(TEXT("volume_unload_cooldown"));
			Writer->WriteValue(TEXT("folder_path"), Streaming->GetFolderPath().IsNone()?FString():Streaming->GetFolderPath().ToString());
			Writer->WriteValue(TEXT("authored_locked"), bool(Streaming->bLocked));
			Writer->WriteValue(TEXT("streaming_path"), Streaming->GetPathName());
			Writer->WriteValue(TEXT("loaded_level_path"), GetPathNameSafe(Streaming->GetLoadedLevel()));
			Writer->WriteValue(TEXT("is_current_level"), Streaming->GetLoadedLevel() && Streaming->GetLoadedLevel() == World->GetCurrentLevel());
			if (ULevel* Loaded = Streaming->GetLoadedLevel())
			{
				Writer->WriteValue(TEXT("editor_visible"), bool(Loaded->bIsVisible));
				Writer->WriteValue(TEXT("locked"), FLevelUtils::IsLevelLocked(Loaded));
			}
			Writer->WriteValue(TEXT("package_path"), Streaming->GetWorldAssetPackageName());
			Writer->WriteValue(TEXT("class"), Streaming->GetClass()->GetPathName());
			Writer->WriteValue(TEXT("loaded"), Streaming->GetLoadedLevel() != nullptr);
			Writer->WriteValue(TEXT("should_be_loaded"), Streaming->ShouldBeLoaded());
			Writer->WriteValue(TEXT("visible"), Streaming->IsLevelVisible());
			Writer->WriteValue(TEXT("should_be_visible"), Streaming->GetShouldBeVisibleFlag());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd(); Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/current"), [](const FHttpContext<FWorldStructureReq, FString>& C)
	{
		const auto R=C.RequestBody(); UWorld* World=ActiveEditorWorld();
		if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || World->IsPartitionedWorld() || World->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world/current world identity required");
		auto* Streaming=FindStreamingLevel(World,R.LevelPath); auto* Level=Streaming->GetLoadedLevel();
		if(!IsValid(Streaming) || Streaming->GetPathName()!=R.ExpectedStreamingPath || !IsValid(Level) || Level->OwningWorld!=World || Level==World->PersistentLevel || Level->IsPersistentLevel() || Level->GetWorldPartition() || FLevelUtils::IsLevelLocked(Level) || GetPathNameSafe(World->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || bool(Level->bIsVisible)!=R.bExpectedVisible) throw std::runtime_error("Already-loaded unlocked ordinary sublevel/streaming/current level/visibility guards required");
		const FString BeforeCurrent=GetPathNameSafe(World->GetCurrentLevel()),TargetPath=Level->GetPathName(); const bool BeforeVisible=Level->bIsVisible,Changed=World->GetCurrentLevel()!=Level || !BeforeVisible;
		auto Actors=[&]() { TSet<FString> Paths; for(TObjectIterator<AActor> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==World) Paths.Add(It->GetPathName()); return Paths; };
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto ActorsBefore=Actors(),DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","MakeSublevelCurrent","Make Streaming Sublevel Current")); World->Modify(false); Level->Modify(false); UEditorLevelUtils::MakeLevelCurrent(Level,false); if(ActiveEditorWorld()!=World || !IsValid(Level) || !IsValid(Streaming) || !World->GetStreamingLevels().Contains(Streaming) || Streaming->GetLoadedLevel()!=Level || World->GetCurrentLevel()!=Level || !Level->bIsVisible) throw std::runtime_error("Native current-level/visibility readback failed; inspect partial editor state"); }
		const auto ActorsAfter=Actors(),DirtyAfter=Dirty(),Added=ActorsAfter.Difference(ActorsBefore),Removed=ActorsBefore.Difference(ActorsAfter); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),World->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("target_level_path"),TargetPath); J->WriteValue(TEXT("previous_current_level_path"),BeforeCurrent); J->WriteValue(TEXT("current_level_path"),GetPathNameSafe(World->GetCurrentLevel())); J->WriteValue(TEXT("previous_visible"),BeforeVisible); J->WriteValue(TEXT("current_visible"),bool(Level->bIsVisible)); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("affected_level_actor_slots"),Level->Actors.Num()); J->WriteValue(TEXT("loaded_actor_addition_count"),Added.Num()); J->WriteValue(TEXT("loaded_actor_removal_count"),Removed.Num()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Paths=[&](const TCHAR* Key,const TSet<FString>& Values) { auto Sorted=Values.Array(); Sorted.Sort(); J->WriteArrayStart(Key); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); }; Paths(TEXT("loaded_actor_additions"),Added); Paths(TEXT("loaded_actor_removals"),Removed); Paths(TEXT("dirty_packages_after"),DirtyAfter); J->WriteArrayStart(TEXT("affected_level_actor_paths")); int32 ActorCount=0; for(AActor* Actor:Level->Actors) if(IsValid(Actor)) { if(ActorCount<128) J->WriteValue(Actor->GetPathName()); ++ActorCount; } J->WriteArrayEnd(); J->WriteValue(TEXT("affected_level_actor_count"),ActorCount); J->WriteValue(TEXT("paths_truncated"),ActorCount>128 || Added.Num()>128 || Removed.Num()>128 || DirtyAfter.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native MakeLevelCurrent for an inspected already-loaded unlocked ordinary attached sublevel. Makes target editor-visible and broadcasts current-level/visibility/selection delegates; actor/dirty snapshots report callback effects. Transaction records world and level without explicit package dirtying; editor current-level selection is session state, native visibility may dirty authored state. No explicit loading/unloading/activation in game/actor reassignment/save; excludes World Partition and unloaded levels. Native callbacks may partially change state, undo/persistence and endpoint compilation unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/locked"), [](const FHttpContext<FWorldStructureReq, FString>& C)
	{
		const auto R=C.RequestBody(); UWorld* World=ActiveEditorWorld();
		if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || World->IsPartitionedWorld() || World->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world/current world identity required");
		auto* Streaming=FindStreamingLevel(World,R.LevelPath); auto* Level=Streaming->GetLoadedLevel();
		if(!IsValid(Streaming) || Streaming->GetPathName()!=R.ExpectedStreamingPath || !IsValid(Level) || Level->OwningWorld!=World || Level==World->PersistentLevel || Level->IsPersistentLevel() || Level->GetWorldPartition() || GetPathNameSafe(World->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || bool(Streaming->bLocked)!=R.bExpectedLocked) throw std::runtime_error("Already-loaded ordinary sublevel/streaming/current level/authored lock guards required");
		const FString BeforeCurrent=GetPathNameSafe(World->GetCurrentLevel()),TargetPath=Level->GetPathName(); const bool BeforeLocked=Streaming->bLocked,BeforeEffectiveLocked=FLevelUtils::IsLevelLocked(Level),Changed=BeforeLocked!=R.bLocked;
		auto Actors=[&]() { TSet<FString> Paths; for(TObjectIterator<AActor> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==World) Paths.Add(It->GetPathName()); return Paths; };
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto ActorsBefore=Actors(),DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelLock","Set Streaming Sublevel Edit Lock")); FLevelUtils::ToggleLevelLock(Level); if(ActiveEditorWorld()!=World || !IsValid(Level) || !IsValid(Streaming) || !World->GetStreamingLevels().Contains(Streaming) || Streaming->GetLoadedLevel()!=Level || bool(Streaming->bLocked)!=R.bLocked || GetPathNameSafe(World->GetCurrentLevel())!=BeforeCurrent) throw std::runtime_error("Native authored lock/current-level readback failed; inspect partial editor state"); }
		const auto ActorsAfter=Actors(),DirtyAfter=Dirty(),Added=ActorsAfter.Difference(ActorsBefore),Removed=ActorsBefore.Difference(ActorsAfter); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),World->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("target_level_path"),TargetPath); J->WriteValue(TEXT("previous_current_level_path"),BeforeCurrent); J->WriteValue(TEXT("current_level_path"),GetPathNameSafe(World->GetCurrentLevel())); J->WriteValue(TEXT("previous_authored_locked"),BeforeLocked); J->WriteValue(TEXT("requested_authored_locked"),R.bLocked); J->WriteValue(TEXT("current_authored_locked"),bool(Streaming->bLocked)); J->WriteValue(TEXT("previous_effective_locked"),BeforeEffectiveLocked); J->WriteValue(TEXT("current_effective_locked"),FLevelUtils::IsLevelLocked(Level)); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("affected_level_actor_slots"),Level->Actors.Num()); J->WriteValue(TEXT("loaded_actor_addition_count"),Added.Num()); J->WriteValue(TEXT("loaded_actor_removal_count"),Removed.Num()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Paths=[&](const TCHAR* Key,const TSet<FString>& Values) { auto Sorted=Values.Array(); Sorted.Sort(); J->WriteArrayStart(Key); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); }; Paths(TEXT("loaded_actor_additions"),Added); Paths(TEXT("loaded_actor_removals"),Removed); Paths(TEXT("dirty_packages_after"),DirtyAfter); J->WriteArrayStart(TEXT("affected_level_actor_paths")); int32 ActorCount=0; for(AActor* Actor:Level->Actors) if(IsValid(Actor)) { if(ActorCount<128) J->WriteValue(Actor->GetPathName()); ++ActorCount; } J->WriteArrayEnd(); J->WriteValue(TEXT("affected_level_actor_count"),ActorCount); J->WriteValue(TEXT("paths_truncated"),ActorCount>128 || Added.Num()>128 || Removed.Num()>128 || DirtyAfter.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native authored sublevel edit lock via FLevelUtils::ToggleLevelLock only when requested flag differs. Exact current ordinary world/attached streaming identity/current editing level/current authored flag; already-loaded target required, unlock permitted when effective lock is true. Native streaming Modify transaction/dirty behavior retained; no manual file permission/source-control/global lock-setting changes. Effective lock also reflects native read-only file policy/cache and can remain true after authored unlock. Reports target actor editability scope and dirty snapshots; no actor property edits, selection cleanup, load/unload or save. Compilation/native transaction/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/streaming-class"), [](const FHttpContext<FWorldStructureReq, FString>& C)
	{
		const auto R=C.RequestBody(); UWorld* World=ActiveEditorWorld();
		if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || World->IsPartitionedWorld() || World->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world/current world identity required");
		auto* Streaming=FindStreamingLevel(World,R.LevelPath); auto* Level=Streaming->GetLoadedLevel();
		if(!IsValid(Streaming) || Streaming->GetPathName()!=R.ExpectedStreamingPath || !IsValid(Level) || Level->OwningWorld!=World || Level==World->PersistentLevel || Level->IsPersistentLevel() || Level->GetWorldPartition() || GetPathNameSafe(World->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || FLevelUtils::IsLevelLocked(Level) || Streaming->GetClass()->GetPathName()!=R.ExpectedStreamingClass) throw std::runtime_error("Already-loaded unlocked ordinary sublevel/streaming/current level/class guards required");
		const FString BeforeCurrent=GetPathNameSafe(World->GetCurrentLevel()),TargetPath=Level->GetPathName(); auto* RequestedClass=(!R.StreamingClass.IsEmpty() && R.StreamingClass.Len()<=2048)?FindObject<UClass>(nullptr,*R.StreamingClass):nullptr; if(!IsValid(RequestedClass) || RequestedClass->GetPathName()!=R.StreamingClass || !RequestedClass->IsChildOf(ULevelStreaming::StaticClass()) || RequestedClass->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists) || RequestedClass->HasAnyFlags(RF_NeedLoad|RF_NeedPostLoad)) throw std::runtime_error("Already-loaded concrete streaming class required"); const bool Changed=Streaming->GetClass()!=RequestedClass,BeforeVisible=Level->bIsVisible; const FTransform BeforeTransform=Streaming->LevelTransform; const FString PackagePath=Streaming->GetWorldAssetPackageName(); ULevelStreaming* CurrentStreaming=Streaming;
		auto Actors=[&]() { TSet<FString> Paths; for(TObjectIterator<AActor> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==World) Paths.Add(It->GetPathName()); return Paths; };
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto ActorsBefore=Actors(),DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { if(!DirtyBefore.IsEmpty()) throw std::runtime_error("Resolve dirty loaded packages before native streaming-class replacement"); FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","ReplaceSublevelStreamingClass","Replace Sublevel Streaming Class")); World->Modify(); Streaming->Modify(); CurrentStreaming=UEditorLevelUtils::SetStreamingClassForLevel(Streaming,RequestedClass); if(ActiveEditorWorld()!=World || !IsValid(CurrentStreaming) || !World->GetStreamingLevels().Contains(CurrentStreaming) || CurrentStreaming->GetClass()!=RequestedClass || CurrentStreaming->GetWorldAssetPackageName()!=PackagePath || !CurrentStreaming->LevelTransform.Equals(BeforeTransform,1.e-6) || !IsValid(CurrentStreaming->GetLoadedLevel())) throw std::runtime_error("Native streaming-class replacement readback failed; inspect partial sublevel state"); World->MarkPackageDirty(); } Level=CurrentStreaming->GetLoadedLevel();
		const auto ActorsAfter=Actors(),DirtyAfter=Dirty(),Added=ActorsAfter.Difference(ActorsBefore),Removed=ActorsBefore.Difference(ActorsAfter); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),World->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("target_level_path"),TargetPath); J->WriteValue(TEXT("previous_current_level_path"),BeforeCurrent); J->WriteValue(TEXT("current_level_path"),GetPathNameSafe(World->GetCurrentLevel())); J->WriteValue(TEXT("previous_streaming_class"),R.ExpectedStreamingClass); J->WriteValue(TEXT("requested_streaming_class"),R.StreamingClass); J->WriteValue(TEXT("current_streaming_class"),CurrentStreaming->GetClass()->GetPathName()); J->WriteValue(TEXT("current_streaming_path"),CurrentStreaming->GetPathName()); J->WriteValue(TEXT("current_loaded_level_path"),GetPathNameSafe(Level)); J->WriteValue(TEXT("previous_visible"),BeforeVisible); J->WriteValue(TEXT("current_visible"),bool(Level->bIsVisible)); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("affected_level_actor_slots"),Level->Actors.Num()); J->WriteValue(TEXT("loaded_actor_addition_count"),Added.Num()); J->WriteValue(TEXT("loaded_actor_removal_count"),Removed.Num()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Paths=[&](const TCHAR* Key,const TSet<FString>& Values) { auto Sorted=Values.Array(); Sorted.Sort(); J->WriteArrayStart(Key); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); }; Paths(TEXT("loaded_actor_additions"),Added); Paths(TEXT("loaded_actor_removals"),Removed); Paths(TEXT("dirty_packages_after"),DirtyAfter); J->WriteArrayStart(TEXT("affected_level_actor_paths")); int32 ActorCount=0; for(AActor* Actor:Level->Actors) if(IsValid(Actor)) { if(ActorCount<128) J->WriteValue(Actor->GetPathName()); ++ActorCount; } J->WriteArrayEnd(); J->WriteValue(TEXT("affected_level_actor_count"),ActorCount); J->WriteValue(TEXT("paths_truncated"),ActorCount>128 || Added.Num()>128 || Removed.Num()>128 || DirtyAfter.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native SetStreamingClassForLevel on exact current ordinary world/already-loaded unlocked attached sublevel with current streaming class/current editing level guards. Requested concrete streaming subclass already loaded; changed execution globally clean loaded packages. Native hides/removes old streaming object/re-adds level and copies transform, volumes, unload interval, color, keywords and folder; remaining subclass-specific properties use native defaults and are not migrated. New streaming identity/visibility/current editing level reported, no assumption they remain unchanged. World/old streaming transaction plus native helper operations; callbacks may load/re-register actors and leave partial state on failure. Actor deltas/affected target actors/global dirty snapshots bounded128; no explicit save. Compilation/native custom class behavior/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/transform"), [](const FHttpContext<FWorldStructureReq, FString>& C)
	{
		const auto R=C.RequestBody(); UWorld* World=ActiveEditorWorld();
		if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || World->IsPartitionedWorld() || World->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world/current world identity required");
		auto* Streaming=FindStreamingLevel(World,R.LevelPath); auto* Level=Streaming->GetLoadedLevel();
		if(!IsValid(Streaming) || Streaming->GetPathName()!=R.ExpectedStreamingPath || !IsValid(Level) || Level->OwningWorld!=World || Level==World->PersistentLevel || Level->IsPersistentLevel() || Level->GetWorldPartition() || GetPathNameSafe(World->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || FLevelUtils::IsLevelLocked(Level)) throw std::runtime_error("Already-loaded unlocked ordinary sublevel/streaming/current editing level guards required");
		const FString BeforeCurrent=GetPathNameSafe(World->GetCurrentLevel()),TargetPath=Level->GetPathName(); const FTransform Before=Streaming->LevelTransform; auto RequireTransform=[](const FTransform& T) { const FVector P=T.GetTranslation(),S=T.GetScale3D(); const FQuat Q=T.GetRotation(); if(T.ContainsNaN() || !Q.IsNormalized()) throw std::runtime_error("Finite normalized transform required"); for(double N:{P.X,P.Y,P.Z}) if(!FMath::IsFinite(N) || FMath::Abs(N)>1.e9) throw std::runtime_error("Translation must be within+/-1e9"); for(double N:{S.X,S.Y,S.Z}) if(!FMath::IsFinite(N) || N<0.001 || N>1000) throw std::runtime_error("Positive scale0.001..1000 required"); }; RequireTransform(Before); RequireTransform(R.ExpectedTransform); RequireTransform(R.Transform); if(!Before.Equals(R.ExpectedTransform,1.e-6)) throw std::runtime_error("Full sublevel transform stale guard failed"); const bool Changed=!Before.Equals(R.Transform);
		auto Actors=[&]() { TSet<FString> Paths; for(TObjectIterator<AActor> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==World) Paths.Add(It->GetPathName()); return Paths; };
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto ActorsBefore=Actors(),DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FLevelUtils::SetEditorTransform(Streaming,R.Transform,true); if(ActiveEditorWorld()!=World || !IsValid(Level) || !IsValid(Streaming) || !World->GetStreamingLevels().Contains(Streaming) || Streaming->GetLoadedLevel()!=Level || !Streaming->LevelTransform.Equals(R.Transform,1.e-6) || GetPathNameSafe(World->GetCurrentLevel())!=BeforeCurrent) throw std::runtime_error("Native transform/current-level readback failed; inspect partial actor/brush state"); }
		const auto ActorsAfter=Actors(),DirtyAfter=Dirty(),Added=ActorsAfter.Difference(ActorsBefore),Removed=ActorsBefore.Difference(ActorsAfter); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),World->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("target_level_path"),TargetPath); J->WriteValue(TEXT("previous_current_level_path"),BeforeCurrent); J->WriteValue(TEXT("current_level_path"),GetPathNameSafe(World->GetCurrentLevel())); auto WriteTransform=[&](const TCHAR* Key,const FTransform& T) { J->WriteObjectStart(Key); const FVector P=T.GetTranslation(),S=T.GetScale3D(); const FQuat Q=T.GetRotation(); auto Numbers=[&](const TCHAR* Name,std::initializer_list<double> Values) { J->WriteArrayStart(Name); for(double N:Values) J->WriteValue(N); J->WriteArrayEnd(); }; Numbers(TEXT("translation"),{P.X,P.Y,P.Z}); Numbers(TEXT("rotation_quaternion_xyzw"),{Q.X,Q.Y,Q.Z,Q.W}); Numbers(TEXT("scale"),{S.X,S.Y,S.Z}); J->WriteObjectEnd(); }; WriteTransform(TEXT("previous_transform"),Before); WriteTransform(TEXT("requested_transform"),R.Transform); WriteTransform(TEXT("current_transform"),Streaming->LevelTransform); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("affected_level_actor_slots"),Level->Actors.Num()); J->WriteValue(TEXT("loaded_actor_addition_count"),Added.Num()); J->WriteValue(TEXT("loaded_actor_removal_count"),Removed.Num()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Paths=[&](const TCHAR* Key,const TSet<FString>& Values) { auto Sorted=Values.Array(); Sorted.Sort(); J->WriteArrayStart(Key); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); }; Paths(TEXT("loaded_actor_additions"),Added); Paths(TEXT("loaded_actor_removals"),Removed); Paths(TEXT("dirty_packages_after"),DirtyAfter); J->WriteArrayStart(TEXT("affected_level_actor_paths")); int32 ActorCount=0; for(AActor* Actor:Level->Actors) if(IsValid(Actor)) { if(ActorCount<128) J->WriteValue(Actor->GetPathName()); ++ActorCount; } J->WriteArrayEnd(); J->WriteValue(TEXT("affected_level_actor_count"),ActorCount); J->WriteValue(TEXT("paths_truncated"),ActorCount>128 || Added.Num()>128 || Removed.Num()>128 || DirtyAfter.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native SetEditorTransform on an inspected already-loaded unlocked ordinary attached sublevel. Full expected transform tolerance1e-6, native Equals no-op tolerance, finite normalized quaternion/translation+/-1e9/positive scale0.001..1000. Native owns transaction/streaming and actor Modify, removes old transform then applies new transform with PostEditMove construction callbacks, redraw and possible BSP rebuild. Reports affected actors/loaded deltas/global dirty snapshots; actor geometry/attachments/physics outcomes not individually validated. No explicit load/unload/save. Failure can leave partial native actor/brush state; compilation/undo/transforms/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/folder"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world identity required"); auto* S=FindStreamingLevel(W,R.LevelPath); if(!IsValid(S) || S->GetPathName()!=R.ExpectedStreamingPath || GetPathNameSafe(W->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || S->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad)) throw std::runtime_error("Attached persistent streaming/current editing level identities required");
		auto Parse=[](const FString& Text) -> FName { if(Text.IsEmpty()) return NAME_None; if(Text.Len()>=NAME_SIZE || Text.Equals(TEXT("None"),ESearchCase::IgnoreCase)) throw std::runtime_error("Empty string represents root; bounded folder path required"); for(TCHAR Ch:Text) if(Ch<32 || Ch==127 || Ch==TEXT('\\')) throw std::runtime_error("Folder controls/backslashes rejected"); TArray<FString> Parts; Text.ParseIntoArray(Parts,TEXT("/"),false); for(const auto& Part:Parts) if(Part.IsEmpty() || Part==TEXT(".") || Part==TEXT("..") || Part.TrimStartAndEnd()!=Part) throw std::runtime_error("Nonempty slash-separated folder segments without edge whitespace required"); return FName(*Text); }; const FName Expected=Parse(R.ExpectedFolderPath),Requested=Parse(R.FolderPath),Before=S->GetFolderPath(); if(Before!=Expected) throw std::runtime_error("Authored folder stale guard failed"); const bool Changed=Before!=Requested;
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelFolder","Set Streaming Sublevel Folder")); S->SetFolderPath(Requested); if(ActiveEditorWorld()!=W || !IsValid(S) || !W->GetStreamingLevels().Contains(S) || S->GetFolderPath()!=Requested) throw std::runtime_error("Native streaming folder readback failed; inspect partial state"); }
		const auto DirtyAfter=Dirty(); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); auto Name=[](FName N) { return N.IsNone()?FString():N.ToString(); }; J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("previous_folder_path"),Name(Before)); J->WriteValue(TEXT("requested_folder_path"),Name(Requested)); J->WriteValue(TEXT("current_folder_path"),Name(S->GetFolderPath())); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("loaded"),S->GetLoadedLevel()!=nullptr); J->WriteValue(TEXT("affected_actor_count"),0); J->WriteValue(TEXT("package_dirty"),S->GetPackage()->IsDirty()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Sorted=DirtyAfter.Array(); Sorted.Sort(); J->WriteArrayStart(TEXT("dirty_packages_after")); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty_packages_truncated"),Sorted.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native streaming-level folder organization only, loaded or unloaded ordinary attached entries; exact world/streaming/current editing level/current FName folder guards. Empty root, FName case-insensitive equality means case-only no-op. Native SetFolderPath Modify inside transaction; does not rename map packages, edit actor folders, move actors, load levels or save. Native setter does not broadcast folder-change UI delegate; UI refresh/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/volume-unload-cooldown"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world identity required"); auto* S=FindStreamingLevel(W,R.LevelPath); if(!IsValid(S) || S->GetPathName()!=R.ExpectedStreamingPath || GetPathNameSafe(W->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || S->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad)) throw std::runtime_error("Attached persistent streaming/current editing level identities required");
		if(S->GetLoadedLevel() && FLevelUtils::IsLevelLocked(S->GetLoadedLevel())) throw std::runtime_error("Loaded target level is locked"); if(!FMath::IsFinite(R.Value) || R.Value<0 || R.Value>1.e6 || !FMath::IsFinite(R.ExpectedValue)) throw std::runtime_error("Finite cooldown seconds0..1e6/current value required"); const float Before=S->MinTimeBetweenVolumeUnloadRequests,Requested=float(R.Value); if(double(Before)!=R.ExpectedValue) throw std::runtime_error("Native cooldown stale guard failed"); auto* Property=FindFProperty<FFloatProperty>(S->GetClass(),TEXT("MinTimeBetweenVolumeUnloadRequests")); if(!Property || !S->CanEditChange(Property)) throw std::runtime_error("Native editable cooldown property required"); const bool Changed=Before!=Requested;
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelUnloadCooldown","Set Sublevel Volume Unload Cooldown")); S->Modify(); S->PreEditChange(Property); if(!IsValid(S) || S->MinTimeBetweenVolumeUnloadRequests!=Before || ActiveEditorWorld()!=W || !W->GetStreamingLevels().Contains(S)) throw std::runtime_error("Pre-edit changed streaming context; inspect partial state"); S->MinTimeBetweenVolumeUnloadRequests=Requested; FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); S->PostEditChangeProperty(Event); if(ActiveEditorWorld()!=W || !IsValid(S) || !W->GetStreamingLevels().Contains(S) || S->MinTimeBetweenVolumeUnloadRequests!=Requested) throw std::runtime_error("Native streaming cooldown readback failed; inspect partial state"); S->MarkPackageDirty(); }
		const auto DirtyAfter=Dirty(); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("previous_seconds"),double(Before)); J->WriteValue(TEXT("requested_seconds"),double(Requested)); J->WriteValue(TEXT("current_seconds"),double(S->MinTimeBetweenVolumeUnloadRequests)); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("loaded"),S->GetLoadedLevel()!=nullptr); J->WriteValue(TEXT("affected_actor_count"),0); J->WriteValue(TEXT("package_dirty"),S->GetPackage()->IsDirty()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Sorted=DirtyAfter.Array(); Sorted.Sort(); J->WriteArrayStart(TEXT("dirty_packages_after")); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty_packages_truncated"),Sorted.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Authored MinTimeBetweenVolumeUnloadRequests seconds on exact ordinary attached streaming object, native float current value guard/finite0..1e6/native editability. Transaction/pre-post property events/readback/dirty/no-op/dry-run. Loaded locked targets rejected, unloaded supported without explicit load. Controls cooldown for volume-based unload requests, not a timer/forced unload/editor residency request. No last-request timestamp reset or game streaming evaluation/save. Native callback side effects not exhaustively enumerated; explicit affected actors0, global dirty snapshots128/count. Compilation/callbacks/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/priority"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world identity required"); auto* S=FindStreamingLevel(W,R.LevelPath); if(!IsValid(S) || S->GetPathName()!=R.ExpectedStreamingPath || GetPathNameSafe(W->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || S->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad)) throw std::runtime_error("Attached persistent streaming/current editing level identities required");
		if(S->GetLoadedLevel() && FLevelUtils::IsLevelLocked(S->GetLoadedLevel())) throw std::runtime_error("Loaded target level is locked"); if(!FMath::IsFinite(R.Value) || !FMath::IsFinite(R.ExpectedValue) || R.Value<-2147483648.0 || R.Value>2147483647.0 || R.ExpectedValue<-2147483648.0 || R.ExpectedValue>2147483647.0 || R.Value!=FMath::FloorToDouble(R.Value) || R.ExpectedValue!=FMath::FloorToDouble(R.ExpectedValue)) throw std::runtime_error("Signed32 integer priority/current value required"); const int32 Before=S->GetPriority(),Requested=int32(R.Value); if(double(Before)!=R.ExpectedValue) throw std::runtime_error("Native priority stale guard failed"); auto* Property=FindFProperty<FIntProperty>(S->GetClass(),TEXT("StreamingPriority")); if(!Property || !S->CanEditChange(Property)) throw std::runtime_error("Native editable priority property required"); const bool Changed=Before!=Requested;
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelPriority","Set Sublevel Streaming Priority")); S->Modify(); S->PreEditChange(Property); if(!IsValid(S) || S->GetPriority()!=Before || ActiveEditorWorld()!=W || !W->GetStreamingLevels().Contains(S)) throw std::runtime_error("Pre-edit changed streaming context; inspect partial state"); S->SetPriority(Requested); FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); S->PostEditChangeProperty(Event); if(ActiveEditorWorld()!=W || !IsValid(S) || !W->GetStreamingLevels().Contains(S) || S->GetPriority()!=Requested) throw std::runtime_error("Native streaming priority readback failed; inspect partial state"); S->MarkPackageDirty(); }
		const auto DirtyAfter=Dirty(); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("previous_priority"),double(Before)); J->WriteValue(TEXT("requested_priority"),double(Requested)); J->WriteValue(TEXT("current_priority"),double(S->GetPriority())); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("loaded"),S->GetLoadedLevel()!=nullptr); J->WriteValue(TEXT("affected_actor_count"),0); J->WriteValue(TEXT("package_dirty"),S->GetPackage()->IsDirty()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Sorted=DirtyAfter.Array(); Sorted.Sort(); J->WriteArrayStart(TEXT("dirty_packages_after")); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty_packages_truncated"),Sorted.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native streaming priority signed32 on exact ordinary attached streaming object/current editing level/current priority/native editability guards. Transaction/pre-post events/SetPriority/native readback/dirty/no-op/dry-run; native setter updates world's streaming consideration priority when eligible. Does not interrupt current level evaluation, force loading or save. Loaded locked targets rejected, unloaded supported. Temporary override backup is not altered or inspected, later native ResetPriorityOverride can restore an earlier value. Explicit actor property edits0, global dirty snapshots128/count; native ordering/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/boolean"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world identity required"); auto* S=FindStreamingLevel(W,R.LevelPath); if(!IsValid(S) || S->GetPathName()!=R.ExpectedStreamingPath || GetPathNameSafe(W->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || S->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad)) throw std::runtime_error("Attached persistent streaming/current editing level identities required");
		if(S->GetLoadedLevel() && FLevelUtils::IsLevelLocked(S->GetLoadedLevel())) throw std::runtime_error("Loaded target level is locked"); if(R.FieldName!=TEXT("bShouldBlockOnLoad") && R.FieldName!=TEXT("bShouldBlockOnUnload") && R.FieldName!=TEXT("bDrawOnLevelStatusMap")) throw std::runtime_error("Field must be bShouldBlockOnLoad, bShouldBlockOnUnload or bDrawOnLevelStatusMap"); if((R.Value!=0 && R.Value!=1) || (R.ExpectedValue!=0 && R.ExpectedValue!=1)) throw std::runtime_error("Bool integer0..1/current value required"); auto* Property=FindFProperty<FBoolProperty>(S->GetClass(),FName(*R.FieldName)); if(!Property || Property->HasAnyPropertyFlags(CPF_Transient) || !S->CanEditChange(Property)) throw std::runtime_error("Native persistent editable boolean property required"); auto Read=[&]() { return Property->GetPropertyValue_InContainer(S); }; const bool Before=Read(),Requested=R.Value!=0; if(int32(Before)!=int32(R.ExpectedValue)) throw std::runtime_error("Native boolean stale guard failed"); const bool Changed=Before!=Requested;
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelBoolean","Set Sublevel Streaming Boolean")); S->Modify(); S->PreEditChange(Property); if(!IsValid(S) || Read()!=Before || ActiveEditorWorld()!=W || !W->GetStreamingLevels().Contains(S)) throw std::runtime_error("Pre-edit changed streaming context; inspect partial state"); Property->SetPropertyValue_InContainer(S,Requested); FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); S->PostEditChangeProperty(Event); if(ActiveEditorWorld()!=W || !IsValid(S) || !W->GetStreamingLevels().Contains(S) || Read()!=Requested) throw std::runtime_error("Native streaming boolean readback failed; inspect partial state"); S->MarkPackageDirty(); }
		const auto DirtyAfter=Dirty(); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("field_name"),R.FieldName); J->WriteValue(TEXT("previous_value"),Before); J->WriteValue(TEXT("requested_value"),Requested); J->WriteValue(TEXT("current_value"),Read()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("loaded"),S->GetLoadedLevel()!=nullptr); J->WriteValue(TEXT("affected_actor_count"),0); J->WriteValue(TEXT("package_dirty"),S->GetPackage()->IsDirty()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Sorted=DirtyAfter.Array(); Sorted.Sort(); J->WriteArrayStart(TEXT("dirty_packages_after")); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty_packages_truncated"),Sorted.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Authored streaming booleans bShouldBlockOnLoad/bShouldBlockOnUnload/bDrawOnLevelStatusMap, exact current ordinary world/streaming/current editing level/current value guards. Native FBoolProperty bitfield storage with transaction/pre-post events/readback/dirty/no-op/dry-run. Loaded locked targets rejected, unloaded supported. Blocking flags configure future streaming behavior and status-map flag configures display eligibility; no immediate load/unload/status-map toggle/game evaluation/save. Excludes transient distance-streaming override and static-level collection policy. Explicit actor property edits0, global dirty snapshots128/count; native callbacks/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/color"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath) throw std::runtime_error("Confirmed stopped ordinary editor world identity required"); auto* S=FindStreamingLevel(W,R.LevelPath); if(!IsValid(S) || S->GetPathName()!=R.ExpectedStreamingPath || GetPathNameSafe(W->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || S->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad)) throw std::runtime_error("Attached persistent streaming/current editing level identities required");
		if(S->GetLoadedLevel() && FLevelUtils::IsLevelLocked(S->GetLoadedLevel())) throw std::runtime_error("Loaded target level is locked"); auto Parse=[](const TArray<double>& Channels) { if(Channels.Num()!=4) throw std::runtime_error("Exactly4 linear RGBA channels required"); for(double V:Channels) if(!FMath::IsFinite(V) || V<0 || V>1) throw std::runtime_error("Finite linear color channels0..1 required"); return FLinearColor(float(Channels[0]),float(Channels[1]),float(Channels[2]),float(Channels[3])); }; const FLinearColor Before=S->LevelColor,Requested=Parse(R.ColorValues); if(Before!=Parse(R.ExpectedColorValues)) throw std::runtime_error("Full current level color stale guard failed"); auto* Property=FindFProperty<FStructProperty>(S->GetClass(),TEXT("LevelColor")); if(!Property || Property->Struct!=TBaseStructure<FLinearColor>::Get() || !S->CanEditChange(Property)) throw std::runtime_error("Native editable linear color property required"); const bool Changed=Before!=Requested;
		auto Dirty=[]() { TSet<FString> Paths; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Paths.Add(It->GetName()); return Paths; }; const auto DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelColor","Set Sublevel Visualization Color")); S->Modify(); S->PreEditChange(Property); if(!IsValid(S) || S->LevelColor!=Before || ActiveEditorWorld()!=W || !W->GetStreamingLevels().Contains(S)) throw std::runtime_error("Pre-edit changed streaming context; inspect partial state"); S->LevelColor=Requested; FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); S->PostEditChangeProperty(Event); if(ActiveEditorWorld()!=W || !IsValid(S) || !W->GetStreamingLevels().Contains(S) || S->LevelColor!=Requested) throw std::runtime_error("Native streaming color readback failed; inspect partial state"); S->MarkPackageDirty(); }
		const auto DirtyAfter=Dirty(); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); auto Color=[&](const TCHAR* Key,const FLinearColor& C) { J->WriteArrayStart(Key); for(float V:{C.R,C.G,C.B,C.A}) J->WriteValue(double(V)); J->WriteArrayEnd(); }; Color(TEXT("previous_color_rgba"),Before); Color(TEXT("requested_color_rgba"),Requested); Color(TEXT("current_color_rgba"),S->LevelColor); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("loaded"),S->GetLoadedLevel()!=nullptr); int32 Affected=0; J->WriteArrayStart(TEXT("affected_actor_paths")); if(auto* L=S->GetLoadedLevel()) for(AActor* A:L->Actors) if(IsValid(A)) { if(Affected<128) J->WriteValue(A->GetPathName()); ++Affected; } J->WriteArrayEnd(); J->WriteValue(TEXT("affected_actor_count"),Affected); J->WriteValue(TEXT("affected_actors_truncated"),Affected>128); J->WriteValue(TEXT("package_dirty"),S->GetPackage()->IsDirty()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Sorted=DirtyAfter.Array(); Sorted.Sort(); J->WriteArrayStart(TEXT("dirty_packages_after")); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty_packages_truncated"),Sorted.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Authored linear LevelColor RGBA0..1 with exact current color/world/streaming/current editing level/native editability guards, transaction/pre-post property events/readback/dirty/no-op/dry-run. Native LevelColor callback marks loaded level component render states dirty. Reports affected loaded target actors128/count and global dirty snapshots; not material/light color editing or proof coloration display mode is enabled. Loaded locked targets rejected, unloaded entries supported without explicit load; no save/render synchronization. Compilation/renderer callbacks/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/streaming-volumes/inspect"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || W->GetPathName()!=R.ExpectedWorldPath || R.Start<0 || R.Count<1 || R.Count>128) throw std::runtime_error("Stopped current editor world identity/offset/page1..128 required"); TArray<ALevelStreamingVolume*> Volumes; for(TObjectIterator<ALevelStreamingVolume> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && !It->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) && It->GetWorld()==W) Volumes.Add(*It); Volumes.Sort([](const ALevelStreamingVolume& A,const ALevelStreamingVolume& B) { return A.GetPathName()<B.GetPathName(); }); if(R.Start>Volumes.Num()) throw std::runtime_error("Streaming volume offset beyond loaded collection"); const int32 End=R.Start+FMath::Min(R.Count,Volumes.Num()-R.Start); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("loaded_volume_count"),Volumes.Num()); J->WriteValue(TEXT("next_start"),End); J->WriteValue(TEXT("has_more"),End<Volumes.Num()); J->WriteArrayStart(TEXT("volumes")); for(int32 I=R.Start;I<End;++I) { auto* V=Volumes[I]; TArray<FName> ExpectedNames; TArray<FString> AssignedPaths; for(auto* Entry:W->GetStreamingLevels()) if(Entry && Entry->EditorStreamingVolumes.Contains(V)) { ExpectedNames.Add(Entry->GetWorldAssetPackageFName()); AssignedPaths.Add(Entry->GetPathName()); } J->WriteObjectStart(); J->WriteValue(TEXT("actor_path"),V->GetPathName()); J->WriteValue(TEXT("actor_guid"),V->GetActorGuid().ToString()); J->WriteValue(TEXT("label"),V->GetActorLabel()); J->WriteValue(TEXT("class_path"),V->GetClass()->GetPathName()); const FBox Box=V->GetComponentsBoundingBox(true); J->WriteValue(TEXT("bounds_valid"),bool(Box.IsValid)); if(Box.IsValid) { auto Vector=[&](const TCHAR* Key,const FVector& P) { J->WriteArrayStart(Key); for(double N:{P.X,P.Y,P.Z}) { if(FMath::IsFinite(N)) J->WriteValue(N); else J->WriteNull(); } J->WriteArrayEnd(); }; Vector(TEXT("bounds_center"),Box.GetCenter()); Vector(TEXT("bounds_extent"),Box.GetExtent()); } J->WriteValue(TEXT("level_path"),GetPathNameSafe(V->GetLevel())); J->WriteValue(TEXT("persistent_level"),V->GetLevel()==W->PersistentLevel); J->WriteValue(TEXT("editable"),V->IsEditable()); J->WriteValue(TEXT("effective_locked"),FLevelUtils::IsLevelLocked(V)); J->WriteValue(TEXT("disabled"),bool(V->bDisabled)); J->WriteValue(TEXT("editor_previs_only"),bool(V->bEditorPreVisOnly)); J->WriteValue(TEXT("streaming_usage"),int32(V->StreamingUsage.GetValue())); J->WriteValue(TEXT("package_path"),V->GetPackage()->GetName()); J->WriteValue(TEXT("package_dirty"),V->GetPackage()->IsDirty()); J->WriteValue(TEXT("reverse_reference_count"),V->StreamingLevelNames.Num()); J->WriteValue(TEXT("assigned_streaming_count"),AssignedPaths.Num()); J->WriteValue(TEXT("reverse_references_match"),ExpectedNames==V->StreamingLevelNames); J->WriteArrayStart(TEXT("reverse_level_package_names")); for(int32 K=0;K<FMath::Min(128,V->StreamingLevelNames.Num());++K) J->WriteValue(V->StreamingLevelNames[K].ToString()); J->WriteArrayEnd(); J->WriteArrayStart(TEXT("assigned_streaming_paths")); for(int32 K=0;K<FMath::Min(128,AssignedPaths.Num());++K) J->WriteValue(AssignedPaths[K]); J->WriteArrayEnd(); J->WriteValue(TEXT("references_truncated"),V->StreamingLevelNames.Num()>128 || AssignedPaths.Num()>128); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Read-only loaded current-world native streaming volumes sorted offset/page1..128 with identity/GUID/label/ownership/editability/authored disabled/previs/usage and derived reverse names versus actual attached streaming assignments. Reverse comparison preserves native world streaming order and does not repair caches. Native usage0 Loading/1 LoadingAndVisibility/2 VisibilityBlockingOnLoad/3 BlockingOnLoad/4 LoadingNotVisible. Unloaded actors absent, collection can change between pages; iteration/assignment scans unbounded by page size. Component bounding box only, not brush containment; no containment query, volume streaming evaluation, reference refresh, load/mutation/save; compilation/coverage unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/streaming-volumes/setting"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); FGuid Guid; auto* V=(!R.ActorPath.IsEmpty() && R.ActorPath.Len()<=2048)?FindObject<ALevelStreamingVolume>(nullptr,*R.ActorPath):nullptr; if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath || !FGuid::Parse(R.ActorGuid,Guid) || !Guid.IsValid() || !IsValid(V) || V->IsTemplate() || V->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || V->GetPathName()!=R.ActorPath || V->GetActorGuid()!=Guid || V->GetWorld()!=W || V->GetLevel()!=W->PersistentLevel || V->GetActorLabel()!=R.ExpectedLabel || !V->IsEditable() || FLevelUtils::IsLevelLocked(V)) throw std::runtime_error("Confirmed stopped ordinary world/loaded editable persistent streaming-volume identity/GUID/label required");
		const bool Disabled=R.FieldName==TEXT("bDisabled"),Previs=R.FieldName==TEXT("bEditorPreVisOnly"),Usage=R.FieldName==TEXT("StreamingUsage"); if(!Disabled && !Previs && !Usage) throw std::runtime_error("Field must be bDisabled, bEditorPreVisOnly or StreamingUsage"); const int32 Maximum=Usage?4:1; if(!FMath::IsFinite(R.Value) || !FMath::IsFinite(R.ExpectedValue) || R.Value<0 || R.Value>Maximum || R.Value!=FMath::FloorToDouble(R.Value) || R.ExpectedValue<0 || R.ExpectedValue>Maximum || R.ExpectedValue!=FMath::FloorToDouble(R.ExpectedValue)) throw std::runtime_error("Native bool0..1/usage0..4 integer values required"); auto* Property=FindFProperty<FProperty>(V->GetClass(),FName(*R.FieldName)); if(!Property || (Usage?!CastField<FByteProperty>(Property):!CastField<FBoolProperty>(Property)) || !V->CanEditChange(Property)) throw std::runtime_error("Native editable typed streaming-volume property required"); auto Read=[&]() { return Usage?int32(V->StreamingUsage.GetValue()):int32(Disabled?bool(V->bDisabled):bool(V->bEditorPreVisOnly)); }; const int32 Before=Read(),Requested=int32(R.Value); if(double(Before)!=R.ExpectedValue) throw std::runtime_error("Streaming volume setting stale guard failed"); const bool Changed=Before!=Requested; const auto ReferencesBefore=V->StreamingLevelNames;
		auto Actors=[&]() { TSet<FString> Values; for(TObjectIterator<AActor> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==W) Values.Add(It->GetPathName()); return Values; }; auto Dirty=[]() { TSet<FString> Values; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Values.Add(It->GetName()); return Values; }; const auto ActorsBefore=Actors(),DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetStreamingVolumeSetting","Set Streaming Volume Setting")); V->Modify(); V->PreEditChange(Property); if(!IsValid(V) || Read()!=Before || V->GetWorld()!=W || V->GetActorGuid()!=Guid) throw std::runtime_error("Pre-edit changed streaming volume context"); if(Usage) V->StreamingUsage=EStreamingVolumeUsage(Requested); else if(Disabled) V->bDisabled=Requested!=0; else V->bEditorPreVisOnly=Requested!=0; FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); V->PostEditChangeProperty(Event); if(ActiveEditorWorld()!=W || !IsValid(V) || V->GetWorld()!=W || V->GetActorGuid()!=Guid || V->GetPathName()!=R.ActorPath || Read()!=Requested || V->StreamingLevelNames!=ReferencesBefore) throw std::runtime_error("Native streaming-volume setting/reference readback failed; inspect partial state"); V->MarkPackageDirty(); }
		const auto ActorsAfter=Actors(),DirtyAfter=Dirty(),Added=ActorsAfter.Difference(ActorsBefore),Removed=ActorsBefore.Difference(ActorsAfter); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("actor_path"),R.ActorPath); J->WriteValue(TEXT("actor_guid"),Guid.ToString()); J->WriteValue(TEXT("field_name"),R.FieldName); J->WriteValue(TEXT("previous_value"),Before); J->WriteValue(TEXT("requested_value"),Requested); J->WriteValue(TEXT("current_value"),Read()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("package_dirty"),V->GetPackage()->IsDirty()); J->WriteValue(TEXT("affected_actor_path"),R.ActorPath); J->WriteValue(TEXT("loaded_actor_addition_count"),Added.Num()); J->WriteValue(TEXT("loaded_actor_removal_count"),Removed.Num()); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Paths=[&](const TCHAR* Key,const TSet<FString>& Values) { auto Sorted=Values.Array(); Sorted.Sort(); J->WriteArrayStart(Key); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); }; Paths(TEXT("loaded_actor_additions"),Added); Paths(TEXT("loaded_actor_removals"),Removed); Paths(TEXT("dirty_packages_after"),DirtyAfter); J->WriteValue(TEXT("paths_truncated"),Added.Num()>128 || Removed.Num()>128 || DirtyAfter.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Native authored streaming-volume disabled/editor-previs-only/usage0..4 with inspected ordinary persistent actor identity/GUID/label/current integer/native property eligibility guards. Transaction/pre-post events/native typed assignment/value and reverse-name preservation readback/dirty/no-op/dry-run. Does not edit volume-level assignments, brush, game state or force streaming evaluation/load/unload/save. Subsequent native editor preview/game streaming may respond to settings; actor/global dirty snapshots describe immediate callback effects only. Compilation/native callbacks/undo/persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/streaming-volumes"), [](const FHttpContext<FWorldStructureReq,FString>& C)
	{
		const auto R=C.RequestBody(); auto* W=ActiveEditorWorld(); if(!IsInGameThread() || GEditor->PlayWorld || !GEditor->Trans || !R.bConfirm || W->IsPartitionedWorld() || W->GetPathName()!=R.ExpectedWorldPath || R.VolumePaths.Num()>64 || R.ExpectedVolumePaths.Num()>64) throw std::runtime_error("Confirmed stopped ordinary world identity/full volume lists<=64 required"); auto* S=FindStreamingLevel(W,R.LevelPath); if(!IsValid(S) || S->GetPathName()!=R.ExpectedStreamingPath || GetPathNameSafe(W->GetCurrentLevel())!=R.ExpectedCurrentLevelPath || S->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || (S->GetLoadedLevel() && FLevelUtils::IsLevelLocked(S->GetLoadedLevel()))) throw std::runtime_error("Attached streaming/current editing level/unlocked loaded target guards required");
		auto Paths=[&]() { TArray<FString> Values; for(const auto& V:S->EditorStreamingVolumes) Values.Add(GetPathNameSafe(V.Get())); return Values; }; const auto Before=Paths(); if(Before!=R.ExpectedVolumePaths) throw std::runtime_error("Full ordered volume assignment stale guard failed"); TArray<TObjectPtr<ALevelStreamingVolume>> Requested; for(const auto& Path:R.VolumePaths) { auto* V=(!Path.IsEmpty() && Path.Len()<=2048)?FindObject<ALevelStreamingVolume>(nullptr,*Path):nullptr; if(!IsValid(V) || V->IsTemplate() || V->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || V->GetPathName()!=Path || V->GetWorld()!=W || V->GetLevel()!=W->PersistentLevel || !V->IsEditable() || FLevelUtils::IsLevelLocked(V) || Requested.Contains(V)) throw std::runtime_error("Unique loaded editable persistent-level streaming volumes required"); Requested.Add(V); }
		TArray<ALevelStreamingVolume*> AllVolumes; for(TObjectIterator<ALevelStreamingVolume> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==W) { if(It->HasAnyFlags(RF_Transient|RF_NeedLoad|RF_NeedPostLoad) || AllVolumes.Num()>=4096) throw std::runtime_error("Bounded complete loaded streaming volume collection required"); AllVolumes.Add(*It); } auto* Property=FindFProperty<FArrayProperty>(S->GetClass(),TEXT("EditorStreamingVolumes")); if(!Property || !S->CanEditChange(Property)) throw std::runtime_error("Native editable streaming-volume array required"); const bool Changed=Before!=R.VolumePaths;
		auto Dirty=[]() { TSet<FString> Values; for(TObjectIterator<UPackage> It;It;++It) if(It->IsDirty() && *It!=GetTransientPackage() && !It->HasAnyFlags(RF_Transient) && !It->HasAnyPackageFlags(PKG_CompiledIn)) Values.Add(It->GetName()); return Values; }; const auto DirtyBefore=Dirty();
		if(Changed && !R.bDryRun) { FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP","SetSublevelStreamingVolumes","Set Sublevel Streaming Volumes")); S->Modify(); for(auto* V:AllVolumes) V->Modify(false); S->PreEditChange(Property); if(!IsValid(S) || ActiveEditorWorld()!=W || Paths()!=Before || !W->GetStreamingLevels().Contains(S)) throw std::runtime_error("Pre-edit changed streaming context; inspect partial state"); S->EditorStreamingVolumes=Requested; FPropertyChangedEvent Event(Property,EPropertyChangeType::ValueSet); S->PostEditChangeProperty(Event); if(!IsValid(S) || ActiveEditorWorld()!=W || !W->GetStreamingLevels().Contains(S) || Paths()!=R.VolumePaths) throw std::runtime_error("Native streaming volume array readback failed; inspect partial state"); for(auto* V:AllVolumes) { if(!IsValid(V)) throw std::runtime_error("Streaming volume destroyed by callback"); TArray<FName> Names; for(auto* Entry:W->GetStreamingLevels()) if(Entry && Entry->EditorStreamingVolumes.Contains(V)) Names.Add(Entry->GetWorldAssetPackageFName()); if(V->StreamingLevelNames!=Names) throw std::runtime_error("Native reverse streaming references mismatch; inspect partial state"); } S->MarkPackageDirty(); }
		const auto DirtyAfter=Dirty(); FString Json; auto J=TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("world_path"),W->GetPathName()); J->WriteValue(TEXT("streaming_path"),R.ExpectedStreamingPath); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); auto Write=[&](const TCHAR* Key,const TArray<FString>& Values) { J->WriteArrayStart(Key); for(const auto& V:Values) J->WriteValue(V); J->WriteArrayEnd(); }; Write(TEXT("previous_volume_paths"),Before); Write(TEXT("requested_volume_paths"),R.VolumePaths); Write(TEXT("current_volume_paths"),Paths()); J->WriteValue(TEXT("reverse_reference_actor_count"),AllVolumes.Num()); J->WriteArrayStart(TEXT("affected_actor_paths")); for(int32 I=0;I<FMath::Min(128,AllVolumes.Num());++I) J->WriteValue(AllVolumes[I]->GetPathName()); J->WriteArrayEnd(); J->WriteValue(TEXT("affected_actors_truncated"),AllVolumes.Num()>128); J->WriteValue(TEXT("dirty_package_count_before"),DirtyBefore.Num()); J->WriteValue(TEXT("dirty_package_count_after"),DirtyAfter.Num()); auto Sorted=DirtyAfter.Array(); Sorted.Sort(); J->WriteArrayStart(TEXT("dirty_packages_after")); for(int32 I=0;I<FMath::Min(128,Sorted.Num());++I) J->WriteValue(Sorted[I]); J->WriteArrayEnd(); J->WriteValue(TEXT("dirty_packages_truncated"),Sorted.Num()>128); J->WriteValue(TEXT("scope"),TEXT("Full ordered streaming-volume assignment<=64 for ordinary attached sublevel; requested loaded persistent-level editable unique volumes only, empty clears. Native property callback removes duplicates and rebuilds reverse StreamingLevelNames on all current-world volumes; transaction records streaming and all bounded4096 loaded volumes before callback, full forward/reverse readback. Existing null/stale paths can be guarded and removed. No brush edits, streaming evaluation, forced load/unload or save. Custom callbacks may leave partial state; native reference rebuilding, undo and persistence unverified.")); J->WriteObjectEnd(); J->Close(); return C.TextResponse(Json,TEXT("application/json"));
	});

	App->Post(TEXT("/levels/sublevels/add"), [](const FHttpContext<FWorldStructureReq, FString>& C)
	{
		const FWorldStructureReq Body = C.RequestBody();
		UWorld* World = ActiveEditorWorld();
		const FString PackagePath = NormalizeWorldPackagePath(Body.LevelPath);
		if (World->GetOutermost()->GetName() == PackagePath) throw FValidationException(TEXT("The persistent map cannot be added as its own sublevel"));
		if (World->GetStreamingLevels().ContainsByPredicate([&PackagePath](const ULevelStreaming* Streaming) { return Streaming && Streaming->GetWorldAssetPackageName() == PackagePath; }))
			throw FValidationException(TEXT("The map is already attached as a sublevel"));
		UClass* StreamingClass = ULevelStreamingDynamic::StaticClass();
		if (!Body.StreamingClass.IsEmpty())
		{
			StreamingClass = LoadClass<ULevelStreaming>(nullptr, *Body.StreamingClass);
			if (!StreamingClass || !StreamingClass->IsChildOf(ULevelStreaming::StaticClass()) || StreamingClass->HasAnyClassFlags(CLASS_Abstract))
				throw FValidationException(TEXT("streaming_class must identify a concrete ULevelStreaming class"));
		}
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddSublevel", "Add Streaming Sublevel"));
		ULevelStreaming* Added = UEditorLevelUtils::AddLevelToWorld(World, *PackagePath, StreamingClass, Body.Transform);
		if (!Added) throw std::runtime_error("Failed to add streaming sublevel");
		World->GetOutermost()->MarkPackageDirty();
		return C.TextResponse(Added->GetWorldAssetPackageName());
	});

	App->Delete(TEXT("/levels/sublevels/remove"), [](const FHttpContext<FWorldStructureReq, FActionResponse>& C)
	{
		const FWorldStructureReq Body = C.RequestBody();
		if (!Body.bConfirm) throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Confirmation required"), TEXT("Sublevel removal requires bConfirm=true"));
		UWorld* World = ActiveEditorWorld();
		ULevelStreaming* Streaming = FindStreamingLevel(World, Body.LevelPath);
		Streaming->SetShouldBeLoaded(true);
		World->FlushLevelStreaming();
		ULevel* LoadedLevel = Streaming->GetLoadedLevel();
		if (!LoadedLevel) throw std::runtime_error("The sublevel could not be loaded for safe removal");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveSublevel", "Remove Streaming Sublevel"));
		if (!UEditorLevelUtils::RemoveLevelFromWorld(LoadedLevel, true, false)) throw std::runtime_error("Failed to remove streaming sublevel");
		World->GetOutermost()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch(TEXT("/levels/visibility"), [](const FHttpContext<FWorldStructureReq, FActionResponse>& C)
	{
		const FWorldStructureReq Body = C.RequestBody();
		UWorld* World = ActiveEditorWorld();
		ULevelStreaming* Streaming = FindStreamingLevel(World, Body.LevelPath);
		Streaming->SetShouldBeVisible(Body.bVisible);
		if (Body.bVisible) Streaming->SetShouldBeLoaded(true);
		World->FlushLevelStreaming();
		if (ULevel* Level = Streaming->GetLoadedLevel()) UEditorLevelUtils::SetLevelVisibility(Level, Body.bVisible, false);
		World->GetOutermost()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/actors/spawn"), [](const FHttpContext<FEditorActorReq, FString>& C)
	{
		auto Body = C.RequestBody();
		AActor* Actor = nullptr;
		if (!Body.ActorClass.IsEmpty())
		{
			UClass* Class = LoadClass<AActor>(nullptr, *Body.ActorClass);
			if (!Class || !Class->IsChildOf(AActor::StaticClass())) throw std::runtime_error("actor_class must be a valid AActor class path");
			if (FApp::CanEverRender())
			{
				Actor = ActorSubsystem()->SpawnActorFromClass(Class, Body.Location, Body.Rotation);
			}
			else
			{
				// Without rendering (-nullrhi) the subsystem's viewport placement reads hit proxies from a zero-size
				// viewport and divides by zero (seen with scene-capture actors), so spawn into the editor world directly.
				UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
				if (!World || !World->GetCurrentLevel()) throw std::runtime_error("No editor world to spawn into");
				FScopedTransaction Transaction(FText::FromString(TEXT("MCP Spawn Actor")));
				World->GetCurrentLevel()->Modify();
				FActorSpawnParameters Params;
				Params.OverrideLevel = World->GetCurrentLevel();
				Params.ObjectFlags |= RF_Transactional;
				const FVector Location = Body.Location;
				const FRotator Rotation = Body.Rotation;
				Actor = World->SpawnActor(Class, &Location, &Rotation, Params);
				if (Actor)
				{
					Actor->PostEditMove(true);
					Actor->MarkPackageDirty();
				}
			}
		}
		else if (!Body.AssetPath.IsEmpty())
		{
			UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *Body.AssetPath);
			if (!Asset) throw std::runtime_error("asset_path could not be loaded");
			Actor = ActorSubsystem()->SpawnActorFromObject(Asset, Body.Location, Body.Rotation);
		}
		else throw std::runtime_error("actor_class or asset_path is required");
		if (!Actor) throw std::runtime_error("Failed to spawn actor");
		return C.TextResponse(Actor->GetPathName());
	});

	App->Post(TEXT("/editor/actors/select"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		TArray<AActor*> Actors;
		for (const FString& Path : Body.ActorPaths) Actors.Add(LoadEditorActor(Path));
		ActorSubsystem()->SetSelectedLevelActors(Actors);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/actors/duplicate"), [](const FHttpContext<FEditorActorReq, FString>& C)
	{
		auto Body = C.RequestBody();
		AActor* Duplicate = ActorSubsystem()->DuplicateActor(LoadEditorActor(Body.ActorPath), nullptr, Body.Offset);
		if (!Duplicate) throw std::runtime_error("Failed to duplicate actor");
		return C.TextResponse(Duplicate->GetPathName());
	});

	App->Patch(TEXT("/editor/actors/transform"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		AActor* Actor = LoadEditorActor(Body.ActorPath);
		Actor->Modify();
		if (Body.bSetLocation) Actor->SetActorLocation(Body.Location);
		if (Body.bSetRotation) Actor->SetActorRotation(Body.Rotation);
		if (Body.bSetScale) Actor->SetActorScale3D(Body.Scale);
		if (Body.bSetLabel) Actor->SetActorLabel(Body.Label);
		if (Body.bSetFolderPath) Actor->SetFolderPath(FName(*Body.FolderPath));
		if (Body.bSetAttachment)
		{
			AActor* Parent = Body.AttachTo.IsEmpty() ? nullptr : LoadEditorActor(Body.AttachTo);
			if (Parent) Actor->AttachToActor(Parent, FAttachmentTransformRules::KeepWorldTransform, FName(*Body.AttachSocket));
			else Actor->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
		}
		if (Body.bSetLocation || Body.bSetRotation || Body.bSetScale || Body.bSetLabel || Body.bSetFolderPath || Body.bSetAttachment)
			Actor->GetLevel()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch(TEXT("/editor/actors/properties"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		AActor* Actor = LoadEditorActor(Body.ActorPath);
		Actor->Modify();
		for (const auto& Property : Body.Properties)
			ObjUtils::SetPropertyValueFromString(Actor, Property.Key, Property.Value);
		Actor->GetLevel()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete(TEXT("/editor/actors"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (!Body.bConfirm) throw std::runtime_error("Actor deletion requires bConfirm=true");
		if (!ActorSubsystem()->DestroyActor(LoadEditorActor(Body.ActorPath))) throw std::runtime_error("Failed to destroy actor");
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/actors/select-all"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		ActorSubsystem()->SelectAll(GEditor->GetEditorWorldContext().World());
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/actors/clear-selection"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		ActorSubsystem()->SelectNothing();
		return C.JsonResponse(FActionResponse {});
	});

	App->Get(TEXT("/scene/actors/query"), [](const FHttpContext<void, FString>& C)
	{
		const FString Search = C.Query(TEXT("search"));
		const FString ClassPath = C.Query(TEXT("class_path"));
		const FString Tag = C.Query(TEXT("tag"));
		const FString Folder = C.Query(TEXT("folder"));
		const FString Level = C.Query(TEXT("level"));
		const int32 Limit = QueryLimit(C);
		UClass* RequiredClass = nullptr;
		if (!ClassPath.IsEmpty())
		{
			RequiredClass = LoadClass<AActor>(nullptr, *ClassPath);
			if (!RequiredClass || !RequiredClass->IsChildOf(AActor::StaticClass()))
				throw FValidationException(TEXT("class_path must identify an AActor class"));
		}

		const bool bHasBounds = !C.Query(TEXT("min_x")).IsEmpty() && !C.Query(TEXT("min_y")).IsEmpty()
			&& !C.Query(TEXT("min_z")).IsEmpty() && !C.Query(TEXT("max_x")).IsEmpty()
			&& !C.Query(TEXT("max_y")).IsEmpty() && !C.Query(TEXT("max_z")).IsEmpty();
		FVector MinBounds = FVector::ZeroVector;
		FVector MaxBounds = FVector::ZeroVector;
		if (bHasBounds)
		{
			LexTryParseString(MinBounds.X, *C.Query(TEXT("min_x")));
			LexTryParseString(MinBounds.Y, *C.Query(TEXT("min_y")));
			LexTryParseString(MinBounds.Z, *C.Query(TEXT("min_z")));
			LexTryParseString(MaxBounds.X, *C.Query(TEXT("max_x")));
			LexTryParseString(MaxBounds.Y, *C.Query(TEXT("max_y")));
			LexTryParseString(MaxBounds.Z, *C.Query(TEXT("max_z")));
			if (MinBounds.X > MaxBounds.X || MinBounds.Y > MaxBounds.Y || MinBounds.Z > MaxBounds.Z)
				throw FValidationException(TEXT("minimum bounds must not exceed maximum bounds"));
		}

		TArray<AActor*> Actors = ActorSubsystem()->GetAllLevelActors();
		Actors.RemoveAll([&](const AActor* Actor)
		{
			if (!Actor) return true;
			if (!Search.IsEmpty() && !Actor->GetName().Contains(Search, ESearchCase::IgnoreCase)
				&& !Actor->GetActorLabel().Contains(Search, ESearchCase::IgnoreCase)) return true;
			if (RequiredClass && !Actor->IsA(RequiredClass)) return true;
			if (!Tag.IsEmpty() && !Actor->Tags.Contains(FName(*Tag))) return true;
			if (!Folder.IsEmpty() && !Actor->GetFolderPath().ToString().Equals(Folder, ESearchCase::IgnoreCase)) return true;
			if (!Level.IsEmpty() && (!Actor->GetLevel() || !Actor->GetLevel()->GetPathName().Equals(Level, ESearchCase::IgnoreCase))) return true;
			return bHasBounds && !FBox(MinBounds, MaxBounds).IsInsideOrOn(Actor->GetActorLocation());
		});
		Actors.Sort([](const AActor& Left, const AActor& Right) { return Left.GetPathName() < Right.GetPathName(); });

		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("total"), Actors.Num());
		Writer->WriteArrayStart(TEXT("actors"));
		for (int32 Index = 0; Index < Actors.Num() && Index < Limit; ++Index)
		{
			AActor* Actor = Actors[Index];
			const FVector Location = Actor->GetActorLocation();
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Actor->GetName());
			Writer->WriteValue(TEXT("label"), Actor->GetActorLabel());
			Writer->WriteValue(TEXT("path"), Actor->GetPathName());
			Writer->WriteValue(TEXT("class"), Actor->GetClass()->GetPathName());
			Writer->WriteValue(TEXT("folder"), Actor->GetFolderPath().ToString());
			Writer->WriteValue(TEXT("level"), Actor->GetLevel() ? Actor->GetLevel()->GetPathName() : TEXT(""));
			Writer->WriteObjectStart(TEXT("location"));
			Writer->WriteValue(TEXT("X"), Location.X); Writer->WriteValue(TEXT("Y"), Location.Y); Writer->WriteValue(TEXT("Z"), Location.Z);
			Writer->WriteObjectEnd();
			Writer->WriteArrayStart(TEXT("tags"));
			for (const FName ActorTag : Actor->Tags) Writer->WriteValue(ActorTag.ToString());
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/scene/actors/components"), [](const FHttpContext<void, FString>& C)
	{
		AActor* Actor = LoadEditorActor(C.Query(TEXT("actor_path")));
		TInlineComponentArray<UActorComponent*> Components(Actor);
		Components.Sort([](const UActorComponent& Left, const UActorComponent& Right) { return Left.GetName() < Right.GetName(); });
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("actor_path"), Actor->GetPathName());
		Writer->WriteArrayStart(TEXT("components"));
		for (UActorComponent* Component : Components)
		{
			if (!Component) continue;
			USceneComponent* SceneComponent = Cast<USceneComponent>(Component);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Component->GetName());
			Writer->WriteValue(TEXT("path"), Component->GetPathName());
			Writer->WriteValue(TEXT("class"), Component->GetClass()->GetPathName());
			Writer->WriteValue(TEXT("registered"), Component->IsRegistered());
			Writer->WriteValue(TEXT("creation_method"), static_cast<int32>(Component->CreationMethod));
			Writer->WriteValue(TEXT("scene_component"), SceneComponent != nullptr);
			Writer->WriteValue(TEXT("parent"), SceneComponent && SceneComponent->GetAttachParent() ? SceneComponent->GetAttachParent()->GetName() : TEXT(""));
			Writer->WriteValue(TEXT("socket"), SceneComponent ? SceneComponent->GetAttachSocketName().ToString() : TEXT(""));
			Writer->WriteValue(TEXT("child_count"), SceneComponent ? SceneComponent->GetAttachChildren().Num() : 0);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/scene/actors/components/properties"), [](const FHttpContext<void, FString>& C)
	{
		AActor* Actor = LoadEditorActor(C.Query(TEXT("actor_path")));
		return C.TextResponse(ObjUtils::SerializeObjectToJson(FindActorComponent(Actor, C.Query(TEXT("component_name")))), TEXT("application/json"));
	});

	App->Post(TEXT("/scene/actors/components"), [](const FHttpContext<FSceneComponentReq, FString>& C)
	{
		const FSceneComponentReq Body = C.RequestBody();
		AActor* Actor = LoadEditorActor(Body.ActorPath);
		if (Body.ComponentName.IsEmpty() || Body.ComponentClass.IsEmpty()) throw FValidationException(TEXT("component_name and component_class are required"));
		TInlineComponentArray<UActorComponent*> ExistingComponents(Actor);
		if (ExistingComponents.ContainsByPredicate([&Body](const UActorComponent* Component) { return Component && Component->GetName() == Body.ComponentName; }))
			throw FValidationException(TEXT("A component with that name already exists on the actor"));
		UClass* ComponentClass = LoadClass<UActorComponent>(nullptr, *Body.ComponentClass);
		if (!ComponentClass || !ComponentClass->IsChildOf(UActorComponent::StaticClass()) || ComponentClass->HasAnyClassFlags(CLASS_Abstract))
			throw FValidationException(TEXT("component_class must identify a concrete UActorComponent class"));

		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "CreateActorComponent", "Create Actor Component"));
		Actor->Modify();
		UActorComponent* Component = NewObject<UActorComponent>(Actor, ComponentClass, FName(*Body.ComponentName), RF_Transactional);
		if (!Component) throw std::runtime_error("Failed to create actor component");
		Actor->AddInstanceComponent(Component);
		Component->OnComponentCreated();
		if (USceneComponent* SceneComponent = Cast<USceneComponent>(Component))
		{
			USceneComponent* Parent = Body.AttachToComponent.IsEmpty() ? Actor->GetRootComponent() : Cast<USceneComponent>(FindActorComponent(Actor, Body.AttachToComponent));
			if (Parent) SceneComponent->SetupAttachment(Parent, FName(*Body.AttachSocket));
			else Actor->SetRootComponent(SceneComponent);
		}
		for (const auto& Property : Body.Properties) ObjUtils::SetPropertyValueFromString(Component, Property.Key, Property.Value);
		Component->RegisterComponent();
		Actor->GetLevel()->MarkPackageDirty();
		return C.TextResponse(Component->GetPathName());
	});

	App->Patch(TEXT("/scene/actors/components"), [](const FHttpContext<FSceneComponentReq, FActionResponse>& C)
	{
		const FSceneComponentReq Body = C.RequestBody();
		AActor* Actor = LoadEditorActor(Body.ActorPath);
		UActorComponent* Component = FindActorComponent(Actor, Body.ComponentName);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AttachActorComponent", "Attach Actor Component"));
		Actor->Modify(); Component->Modify();
		if (Body.bSetAttachment)
		{
			USceneComponent* SceneComponent = Cast<USceneComponent>(Component);
			if (!SceneComponent) throw FValidationException(TEXT("Only scene components can be attached"));
			if (Body.AttachToComponent.IsEmpty()) SceneComponent->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
			else
			{
				USceneComponent* Parent = Cast<USceneComponent>(FindActorComponent(Actor, Body.AttachToComponent));
				if (!Parent) throw FValidationException(TEXT("attach_to_component must identify a scene component"));
				if (Parent == SceneComponent || Parent->IsAttachedTo(SceneComponent)) throw FValidationException(TEXT("Component attachment would create a cycle"));
				SceneComponent->AttachToComponent(Parent, FAttachmentTransformRules::KeepWorldTransform, FName(*Body.AttachSocket));
			}
		}
		Actor->GetLevel()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch(TEXT("/scene/actors/components/properties"), [](const FHttpContext<FSceneComponentReq, FActionResponse>& C)
	{
		const FSceneComponentReq Body = C.RequestBody();
		AActor* Actor = LoadEditorActor(Body.ActorPath);
		UActorComponent* Component = FindActorComponent(Actor, Body.ComponentName);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditActorComponent", "Edit Actor Component"));
		Component->Modify();
		for (const auto& Property : Body.Properties) ObjUtils::SetPropertyValueFromString(Component, Property.Key, Property.Value);
		Actor->GetLevel()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete(TEXT("/scene/actors/components"), [](const FHttpContext<FSceneComponentReq, FActionResponse>& C)
	{
		const FSceneComponentReq Body = C.RequestBody();
		AActor* Actor = LoadEditorActor(Body.ActorPath);
		UActorComponent* Component = FindActorComponent(Actor, Body.ComponentName);
		if (Component == Actor->GetRootComponent()) throw FValidationException(TEXT("The actor root component cannot be removed by this route"));
		if (!Body.bConfirm)
		{
			FString Details;
			if (const USceneComponent* SceneComponent = Cast<USceneComponent>(Component))
			{
				TArray<FString> ChildNames;
				for (const USceneComponent* Child : SceneComponent->GetAttachChildren()) if (Child) ChildNames.Add(Child->GetName());
				Details = ChildNames.IsEmpty() ? TEXT("No attached child components") : FString::Printf(TEXT("Attached children: %s"), *FString::Join(ChildNames, TEXT(", ")));
			}
			throw FHttpException(EHttpServerResponseCodes::Conflict, TEXT("Confirmation required"), TEXT("Component deletion requires bConfirm=true"), Details);
		}

		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "DeleteActorComponent", "Delete Actor Component"));
		Actor->Modify(); Component->Modify();
		if (USceneComponent* SceneComponent = Cast<USceneComponent>(Component))
		{
			USceneComponent* Parent = SceneComponent->GetAttachParent();
			TArray<USceneComponent*> Children = SceneComponent->GetAttachChildren();
			for (USceneComponent* Child : Children)
			{
				if (!Child) continue;
				if (Parent) Child->AttachToComponent(Parent, FAttachmentTransformRules::KeepWorldTransform);
				else Child->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
			}
		}
		Component->UnregisterComponent();
		Actor->RemoveInstanceComponent(Component);
		Component->DestroyComponent();
		Actor->GetLevel()->MarkPackageDirty();
		return C.JsonResponse(FActionResponse {});
	});

	App->Get(TEXT("/editor/assets/selected"), [](const FHttpContext<void, FString>& C)
	{
		TArray<FAssetData> Assets;
		ContentBrowser().GetSelectedAssets(Assets);
		Assets.Sort([](const FAssetData& Left, const FAssetData& Right) { return Left.GetObjectPathString() < Right.GetObjectPathString(); });
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("assets"));
		for (const FAssetData& Asset : Assets)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Asset.AssetName.ToString());
			Writer->WriteValue(TEXT("object_path"), Asset.GetObjectPathString());
			Writer->WriteValue(TEXT("package_path"), Asset.PackageName.ToString());
			Writer->WriteValue(TEXT("class"), Asset.AssetClassPath.ToString());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	auto SyncContentBrowser = [](const FHttpContext<FEditorAssetSelectionReq, FActionResponse>& C, bool bFocus)
	{
		const FEditorAssetSelectionReq Body = C.RequestBody();
		if (Body.AssetPaths.IsEmpty()) throw FValidationException(TEXT("asset_paths must contain at least one asset"));
		TArray<FAssetData> Assets;
		for (const FString& Path : Body.AssetPaths) Assets.Add(FindAssetData(Path));
		ContentBrowser().SyncBrowserToAssets(Assets, false, bFocus);
		return C.JsonResponse(FActionResponse {});
	};

	App->Post(TEXT("/editor/assets/select"), [SyncContentBrowser](const FHttpContext<FEditorAssetSelectionReq, FActionResponse>& C)
	{
		return SyncContentBrowser(C, false);
	});

	App->Post(TEXT("/editor/assets/reveal"), [SyncContentBrowser](const FHttpContext<FEditorAssetSelectionReq, FActionResponse>& C)
	{
		return SyncContentBrowser(C, true);
	});

	App->Post(TEXT("/editor/placement"), [](const FHttpContext<FEditorActorReq, FString>& C)
	{
		const FEditorActorReq Body = C.RequestBody();
		if (Body.ActorClass.IsEmpty() && Body.AssetPath.IsEmpty())
			throw FValidationException(TEXT("actor_class or asset_path is required"));
		if (!Body.ActorClass.IsEmpty() && !Body.AssetPath.IsEmpty())
			throw FValidationException(TEXT("provide actor_class or asset_path, not both"));

		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "PlaceEditorActor", "Place Editor Actor"));
		AActor* Actor = nullptr;
		if (!Body.ActorClass.IsEmpty())
		{
			UClass* ActorClass = LoadClass<AActor>(nullptr, *Body.ActorClass);
			if (!ActorClass || !ActorClass->IsChildOf(AActor::StaticClass()) || ActorClass->HasAnyClassFlags(CLASS_Abstract))
				throw FValidationException(TEXT("actor_class must identify a concrete AActor class"));
			Actor = ActorSubsystem()->SpawnActorFromClass(ActorClass, Body.Location, Body.Rotation);
		}
		else
		{
			UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *Body.AssetPath);
			if (!Asset) throw FValidationException(TEXT("asset_path could not be loaded"));
			UActorFactory* Factory = FActorFactoryAssetProxy::GetFactoryForAssetObject(Asset);
			if (!Factory) throw FValidationException(TEXT("No actor factory supports the requested asset"));
			Actor = FActorFactoryAssetProxy::AddActorForAsset(Asset, Body.bSelect, RF_Transactional, Factory);
		}
		if (!Actor) throw std::runtime_error("Failed to place actor");
		Actor->Modify();
		Actor->SetActorLocationAndRotation(Body.Location, Body.Rotation);
		Actor->SetActorScale3D(Body.Scale);
		if (!Body.Label.IsEmpty()) Actor->SetActorLabel(Body.Label);
		if (!Body.FolderPath.IsEmpty()) Actor->SetFolderPath(FName(*Body.FolderPath));
		Actor->GetLevel()->MarkPackageDirty();
		if (Body.bSelect) ActorSubsystem()->SetSelectedLevelActors({Actor});
		return C.TextResponse(Actor->GetPathName());
	});

	App->Get(TEXT("/editor/assets/status"), [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *C.Query(TEXT("asset_path")));
		if (!Asset) throw std::runtime_error("asset_path could not be loaded");
		IAssetEditorInstance* Editor = AssetEditorSubsystem()->FindEditorForAsset(Asset, false);
		return C.TextResponse(FString::Printf(TEXT("{\"open\":%s,\"editor\":\"%s\"}"), Editor ? TEXT("true") : TEXT("false"), Editor ? *Editor->GetEditorName().ToString() : TEXT("")), TEXT("application/json"));
	});

	App->Post(TEXT("/editor/assets/open"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		if (C.RequestBody().AssetPath.IsEmpty()) throw std::runtime_error("asset_path is required");
		// Editors open windows; the headless application has none and hits an engine fatal error.
		if (!FApp::CanEverRender() || FParse::Param(FCommandLine::Get(), TEXT("RenderOffscreen"))) throw std::runtime_error("Asset editors need a windowed editor; this session is headless");
		AssetEditorSubsystem()->OpenEditorForAsset(C.RequestBody().AssetPath);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post(TEXT("/editor/assets/focus"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *C.RequestBody().AssetPath);
		if (!Asset || !AssetEditorSubsystem()->FindEditorForAsset(Asset, true)) throw std::runtime_error("Asset editor is not open");
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete(TEXT("/editor/assets"), [](const FHttpContext<FEditorActorReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (!Body.bConfirm) throw std::runtime_error("Closing an asset editor requires bConfirm=true");
		UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *Body.AssetPath);
		if (!Asset || AssetEditorSubsystem()->CloseAllEditorsForAsset(Asset) == 0) throw std::runtime_error("No open editor found for asset");
		return C.JsonResponse(FActionResponse {});
	});

	App->Get(TEXT("/ue/classes"), [](const FHttpContext<void, FString>& C)
	{
		ProjectDiagnosticsUtils::FClassQuery Query;
		Query.Search = C.Query(TEXT("search"));
		Query.Parent = C.Query(TEXT("class_path"));
		Query.Category = C.Query(TEXT("category"));
		Query.Source = C.Query(TEXT("source"));
		Query.Module = C.Query(TEXT("module"));
		Query.bCanBeParent = C.Query(TEXT("can_be_parent"), TEXT("false")).Equals(TEXT("true"), ESearchCase::IgnoreCase);
		Query.bIncludeAbstract = C.Query(TEXT("include_abstract"), TEXT("false")).Equals(TEXT("true"), ESearchCase::IgnoreCase);
		Query.Limit = FCString::Atoi(*C.Query(TEXT("limit"), TEXT("200")));
		return C.TextResponse(ProjectDiagnosticsUtils::ListClasses(Query), TEXT("application/json"));
	});

	App->Post(TEXT("/editor/console"), [](const FHttpContext<FGameCoreReq, FString>& C)
	{
		return C.TextResponse(ProjectDiagnosticsUtils::ExecuteConsole(C.RequestBody().Value, C.RequestBody().bConfirm), TEXT("application/json"));
	});

	App->Post(TEXT("/blueprints/errors"), [](const FHttpContext<FGameCoreReq, FString>& C)
	{
		const FGameCoreReq Body = C.RequestBody();
		return C.TextResponse(ProjectDiagnosticsUtils::ListBlueprintErrors(Body.AssetPath, Body.Key, Body.bWait, Body.TimeoutSeconds), TEXT("application/json"));
	});

	App->Get(TEXT("/project/errors"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(ProjectDiagnosticsUtils::ProjectErrors(FCString::Atoi(*C.Query(TEXT("limit"), TEXT("100")))), TEXT("application/json"));
	});

	App->Get(TEXT("/ue/classes/describe"), [](const FHttpContext<void, FString>& C)
	{
		UClass* Class = LoadClassFromQuery(C);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		WriteClassFields(Writer, Class);
		Writer->WriteArrayStart(TEXT("functions"));
		for (TFieldIterator<UFunction> It(Class, EFieldIteratorFlags::IncludeSuper); It; ++It) WriteFunction(Writer, *It);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("properties"));
		for (TFieldIterator<FProperty> It(Class, EFieldIteratorFlags::IncludeSuper); It; ++It)
		{
			FProperty* Property = *It;
			if (!Property) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Property->GetName());
			Writer->WriteValue(TEXT("type"), Property->GetClass()->GetName());
			Writer->WriteValue(TEXT("cpp_type"), Property->GetCPPType());
			Writer->WriteValue(TEXT("blueprint_readable"), Property->HasAnyPropertyFlags(CPF_BlueprintVisible));
			Writer->WriteValue(TEXT("blueprint_writable"), Property->HasAnyPropertyFlags(CPF_BlueprintVisible) && !Property->HasAnyPropertyFlags(CPF_BlueprintReadOnly));
			Writer->WriteValue(TEXT("tooltip"), Property->GetMetaData(TEXT("ToolTip")));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get(TEXT("/ue/blueprint-functions"), [](const FHttpContext<void, FString>& C)
	{
		UClass* Class = LoadClassFromQuery(C);
		const FString Search = C.Query(TEXT("search"));
		const int32 Limit = QueryLimit(C);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		int32 Count = 0;
		if (Class)
		{
			for (TFieldIterator<UFunction> It(Class, EFieldIteratorFlags::IncludeSuper); It && Count < Limit; ++It)
			{
				UFunction* Function = *It;
				if (!Function || !Function->HasAnyFunctionFlags(FUNC_BlueprintCallable | FUNC_BlueprintEvent | FUNC_BlueprintPure) || (!Search.IsEmpty() && !Function->GetName().Contains(Search, ESearchCase::IgnoreCase))) continue;
				WriteFunction(Writer, Function);
				++Count;
			}
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});
}
