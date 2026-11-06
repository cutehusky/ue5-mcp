#include "ProjectDiagnosticsUtils.h"
#include "DebugFeedbackUtils.h"

#include <stdexcept>

#include "Animation/AnimInstance.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Blueprint/UserWidget.h"
#include "Dom/JsonObject.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "Engine/DataAsset.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GenericPlatform/GenericPlatformOutputDevices.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "IMessageLogListing.h"
#include "Interfaces/IPluginManager.h"
#include "Interfaces/IProjectManager.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "MessageLogModule.h"
#include "Misc/App.h"
#include "Misc/FileHelper.h"
#include "Misc/OutputDeviceFile.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Misc/StringOutputDevice.h"
#include "ProjectDescriptor.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UObject/UObjectIterator.h"

namespace
{
	[[noreturn]] void Fail(const FString& Message)
	{
		throw std::runtime_error(TCHAR_TO_UTF8(*Message));
	}

	UClass* ResolveClass(const FString& Name)
	{
		if (Name.Contains(TEXT("/")))
		{
			if (UClass* Class = LoadClass<UObject>(nullptr, *Name)) return Class;
			if (UClass* Class = FindObject<UClass>(nullptr, *Name)) return Class;
		}
		else
		{
			if (UClass* Class = FindFirstObject<UClass>(*Name, EFindFirstObjectOptions::None)) return Class;
			// C++ spelling: AActor is the class named Actor.
			if (Name.Len() > 1 && (Name[0] == TCHAR('A') || Name[0] == TCHAR('U')))
				if (UClass* Class = FindFirstObject<UClass>(*Name.RightChop(1), EFindFirstObjectOptions::None)) return Class;
		}
		Fail(FString::Printf(TEXT("Class not found: %s. Use a name such as Actor, or a path such as /Script/Engine.Actor or /Game/Folder/BP_Name.BP_Name_C. list_ue_classes with search finds it."), *Name));
	}

	FString KindOf(const UClass* Class)
	{
		if (!Class) return TEXT("object");
		if (Class->IsChildOf(ACharacter::StaticClass())) return TEXT("character");
		if (Class->IsChildOf(APawn::StaticClass())) return TEXT("pawn");
		if (Class->IsChildOf(APlayerController::StaticClass())) return TEXT("player_controller");
		if (Class->IsChildOf(AGameModeBase::StaticClass())) return TEXT("game_mode");
		if (Class->IsChildOf(AGameStateBase::StaticClass())) return TEXT("game_state");
		if (Class->IsChildOf(APlayerState::StaticClass())) return TEXT("player_state");
		if (Class->IsChildOf(AHUD::StaticClass())) return TEXT("hud");
		if (Class->IsChildOf(AActor::StaticClass())) return TEXT("actor");
		if (Class->IsChildOf(USceneComponent::StaticClass())) return TEXT("scene_component");
		if (Class->IsChildOf(UActorComponent::StaticClass())) return TEXT("actor_component");
		if (Class->IsChildOf(UUserWidget::StaticClass())) return TEXT("widget");
		if (Class->IsChildOf(UAnimInstance::StaticClass())) return TEXT("anim_instance");
		if (Class->IsChildOf(UDataAsset::StaticClass())) return TEXT("data_asset");
		if (Class->IsChildOf(UInterface::StaticClass())) return TEXT("interface");
		return TEXT("object");
	}

	TSet<FString> ProjectModules()
	{
		TSet<FString> Names;
		if (const FProjectDescriptor* Project = IProjectManager::Get().GetCurrentProject())
			for (const FModuleDescriptor& Module : Project->Modules) Names.Add(Module.Name.ToString());
		for (const TSharedRef<IPlugin>& Plugin : IPluginManager::Get().GetEnabledPlugins())
			if (Plugin->GetLoadedFrom() == EPluginLoadedFrom::Project)
				for (const FModuleDescriptor& Module : Plugin->GetDescriptor().Modules) Names.Add(Module.Name.ToString());
		return Names;
	}

	struct FClassRow
	{
		FString Name, Path, Parent, Source, Module, Category;
		bool bAbstract = false, bLoaded = true, bCanBeParent = true;
	};

	FString CurrentLogFile()
	{
		if (GLog) GLog->Flush();
		return FPaths::ConvertRelativePathToFull(FGenericPlatformOutputDevices::GetAbsoluteLogFilename());
	}

	// "[time][frame]LogX: Error: text" gives LogX and Error. Continuation lines have no category.
	void ParseLine(const FString& Line, FString& OutCategory, FString& OutSeverity)
	{
		OutCategory.Empty();
		OutSeverity = TEXT("Log");
		int32 Start = 0;
		Line.FindLastChar(TCHAR(']'), Start);
		const int32 Body = Line.StartsWith(TEXT("[")) ? Start + 1 : 0;
		const int32 Colon = Line.Find(TEXT(": "), ESearchCase::CaseSensitive, ESearchDir::FromStart, Body);
		if (Colon == INDEX_NONE) return;
		const FString Name = Line.Mid(Body, Colon - Body);
		if (Name.IsEmpty() || Name.Contains(TEXT(" ")) || !Name.StartsWith(TEXT("Log"))) return;
		OutCategory = Name;
		const FString Rest = Line.Mid(Colon + 2);
		for (const TCHAR* Level : {TEXT("Fatal"), TEXT("Error"), TEXT("Warning"), TEXT("Display"), TEXT("Verbose")})
			if (Rest.StartsWith(FString(Level) + TEXT(": "))) OutSeverity = Level;
	}

	TArray<FString> ReadLines(const FString& Path)
	{
		FString Contents;
		if (!FFileHelper::LoadFileToString(Contents, *Path, FFileHelper::EHashOptions::None, FILEREAD_AllowWrite)) Fail(FString::Printf(TEXT("Could not read the log at %s."), *Path));
		TArray<FString> Lines;
		Contents.ParseIntoArrayLines(Lines, false);
		if (!Lines.IsEmpty() && Lines.Last().IsEmpty()) Lines.Pop();  // The file ends with a line break.
		return Lines;
	}
}

FString ProjectDiagnosticsUtils::ListClasses(const FClassQuery& Q)
{
	if (Q.Limit < 1 || Q.Limit > 2000) Fail(TEXT("limit must be 1-2000"));
	if (!Q.Source.IsEmpty() && Q.Source != TEXT("engine_cpp") && Q.Source != TEXT("project_cpp") && Q.Source != TEXT("blueprint"))
		Fail(TEXT("source must be engine_cpp, project_cpp or blueprint"));
	UClass* Parent = Q.Parent.IsEmpty() ? nullptr : ResolveClass(Q.Parent);
	const TSet<FString> Project = ProjectModules();
	const auto Matches = [&Q](const FClassRow& Row)
	{
		return (Q.Search.IsEmpty() || Row.Name.Contains(Q.Search)) && (Q.Source.IsEmpty() || Row.Source == Q.Source)
			&& (Q.Module.IsEmpty() || Row.Module.Equals(Q.Module, ESearchCase::IgnoreCase)) && (!Q.bCanBeParent || Row.bCanBeParent);
	};

	TArray<FClassRow> Rows;
	TSet<FString> Seen;
	for (TObjectIterator<UClass> It; It; ++It)
	{
		UClass* Class = *It;
		const FString Name = Class->GetName();
		if (Name.StartsWith(TEXT("SKEL_")) || Name.StartsWith(TEXT("REINST_")) || Name.StartsWith(TEXT("TRASHCLASS_")) || Name.StartsWith(TEXT("PLACEHOLDER"))
			|| Name.StartsWith(TEXT("HOTRELOADED_")) || Class->HasAnyClassFlags(CLASS_NewerVersionExists)) continue;
		if (Parent && !Class->IsChildOf(Parent)) continue;
		if (!Q.bIncludeAbstract && Class->HasAnyClassFlags(CLASS_Abstract)) continue;
		FClassRow Row;
		Row.Name = Name;
		Row.Path = Class->GetPathName();
		Row.Parent = Class->GetSuperClass() ? Class->GetSuperClass()->GetPathName() : FString();
		Row.bAbstract = Class->HasAnyClassFlags(CLASS_Abstract);
		Row.Category = KindOf(Class);
		const FString Package = Class->GetOutermost()->GetName();
		const bool bBlueprint = Class->HasAnyClassFlags(CLASS_CompiledFromBlueprint);
		Row.Module = bBlueprint ? FString() : FPackageName::GetShortName(Package);
		Row.Source = bBlueprint ? TEXT("blueprint") : Project.Contains(Row.Module) ? TEXT("project_cpp") : TEXT("engine_cpp");
		Row.bCanBeParent = FKismetEditorUtilities::CanCreateBlueprintOfClass(Class);
		if (!Q.Category.IsEmpty() && !Row.Category.Equals(Q.Category, ESearchCase::IgnoreCase)
			&& !Class->GetMetaData(TEXT("ClassGroupNames")).Contains(Q.Category) && !Class->GetMetaData(TEXT("Category")).Contains(Q.Category)) continue;
		Seen.Add(Row.Path);
		if (Matches(Row)) Rows.Add(MoveTemp(Row));
	}

	// Blueprints that are not loaded are known only to the Asset Registry.
	if (Q.Source.IsEmpty() || Q.Source == TEXT("blueprint"))
	{
		IAssetRegistry& Registry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
		TSet<FTopLevelAssetPath> Derived;
		if (Parent) Registry.GetDerivedClassNames({Parent->GetClassPathName()}, {}, Derived);
		TArray<FAssetData> Assets;
		Registry.GetAssetsByClass(UBlueprint::StaticClass()->GetClassPathName(), Assets, true);
		for (const FAssetData& Asset : Assets)
		{
			if (!Asset.PackageName.ToString().StartsWith(TEXT("/Game/"))) continue;
			const FString Path = FPackageName::ExportTextPathToObjectPath(Asset.GetTagValueRef<FString>(FBlueprintTags::GeneratedClassPath));
			if (Path.IsEmpty() || Seen.Contains(Path) || (Parent && !Derived.Contains(FTopLevelAssetPath(Path)))) continue;
			FClassRow Row;
			Row.Path = Path;
			Row.Name = FPackageName::ObjectPathToObjectName(Path);
			Row.Parent = FPackageName::ExportTextPathToObjectPath(Asset.GetTagValueRef<FString>(FBlueprintTags::ParentClassPath));
			Row.Source = TEXT("blueprint");
			Row.bLoaded = false;
			const FString Native = FPackageName::ExportTextPathToObjectPath(Asset.GetTagValueRef<FString>(FBlueprintTags::NativeParentClassPath));
			Row.Category = KindOf(Native.IsEmpty() ? nullptr : FindObject<UClass>(nullptr, *Native));
			if ((Q.Category.IsEmpty() || Row.Category.Equals(Q.Category, ESearchCase::IgnoreCase)) && Matches(Row)) Rows.Add(MoveTemp(Row));
		}
	}

	Rows.Sort([](const FClassRow& A, const FClassRow& B) { return A.Name < B.Name; });
	FString Json;
	const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Json);
	J->WriteObjectStart();
	J->WriteValue(TEXT("total"), Rows.Num());
	J->WriteValue(TEXT("truncated"), Rows.Num() > Q.Limit);
	J->WriteArrayStart(TEXT("classes"));
	for (int32 Index = 0; Index < FMath::Min(Rows.Num(), Q.Limit); ++Index)
	{
		const FClassRow& Row = Rows[Index];
		J->WriteObjectStart();
		J->WriteValue(TEXT("name"), Row.Name);
		J->WriteValue(TEXT("path"), Row.Path);
		J->WriteValue(TEXT("parent"), Row.Parent);
		J->WriteValue(TEXT("source"), Row.Source);
		J->WriteValue(TEXT("module"), Row.Module);
		J->WriteValue(TEXT("category"), Row.Category);
		J->WriteValue(TEXT("abstract"), Row.bAbstract);
		J->WriteValue(TEXT("loaded"), Row.bLoaded);
		J->WriteValue(TEXT("can_be_blueprint_parent"), Row.bCanBeParent);
		J->WriteObjectEnd();
	}
	J->WriteArrayEnd();
	J->WriteObjectEnd();
	J->Close();
	return Json;
}

FString ProjectDiagnosticsUtils::ExecuteConsole(const FString& Command, bool bConfirm)
{
	const FString Clean = Command.TrimStartAndEnd();
	if (Clean.IsEmpty()) Fail(TEXT("command is required, such as stat fps or r.ScreenPercentage 100"));
	if (!bConfirm) Fail(TEXT("Console commands can change anything in the editor, and most cannot be undone. Retry with confirm=True."));
	if (Clean.Contains(TEXT("|")) || Clean.Contains(TEXT("\n")) || Clean.Contains(TEXT("\r"))) Fail(TEXT("Send one command at a time, with no | or line breaks."));
	FString First;
	if (!Clean.Split(TEXT(" "), &First, nullptr)) First = Clean;
	First.ToLowerInline();
	// These end the session that serves this API, or run arbitrary code.
	for (const TCHAR* Blocked : {TEXT("quit"), TEXT("exit"), TEXT("debug"), TEXT("crash"), TEXT("py"), TEXT("python")})
		if (First == Blocked) Fail(FString::Printf(TEXT("%s is not allowed here, because it would close or crash the editor or run arbitrary code."), *First));
	if (!GEngine || !GEditor) Fail(TEXT("The Unreal editor is not available"));
	UWorld* World = GEditor->PlayWorld ? GEditor->PlayWorld.Get() : GEditor->GetEditorWorldContext().World();
	FStringOutputDevice Output;
	Output.SetAutoEmitLineTerminator(true);
	UE_LOG(LogTemp, Display, TEXT("UE5_MCP console: %s"), *Clean);
	const bool bHandled = GEngine->Exec(World, *Clean, Output);
	if (!bHandled) Fail(FString::Printf(TEXT("The console did not recognise: %s. Check the spelling; console variables take the form r.ScreenPercentage 100."), *Clean));
	FString Json;
	const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Json);
	J->WriteObjectStart();
	J->WriteValue(TEXT("command"), Clean);
	J->WriteValue(TEXT("world_context"), GEditor->PlayWorld ? TEXT("pie") : TEXT("editor"));
	J->WriteValue(TEXT("output"), FString(Output));
	J->WriteValue(TEXT("note"), TEXT("Some commands print to the Output Log instead; use get_editor_logs."));
	J->WriteObjectEnd();
	J->Close();
	return Json;
}

FString ProjectDiagnosticsUtils::ListBlueprintErrors(const FString& Root, const FString& Search, bool bIncludeWarnings, int32 Limit)
{
	if (Limit < 1 || Limit > 2000) Fail(TEXT("limit must be 1-2000"));
	if (!Root.StartsWith(TEXT("/Game"))) Fail(TEXT("root must be a /Game folder, such as /Game or /Game/RtsDemo"));
	if (GEditor && GEditor->PlayWorld) Fail(TEXT("Stop the play session first, because this compiles Blueprints."));
	IAssetRegistry& Registry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
	FARFilter Filter;
	Filter.PackagePaths.Add(*Root);
	Filter.bRecursivePaths = true;
	Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
	Filter.bRecursiveClasses = true;
	TArray<FAssetData> Assets;
	Registry.GetAssets(Filter, Assets);
	if (!Search.IsEmpty()) Assets.RemoveAll([&Search](const FAssetData& A) { return !A.AssetName.ToString().Contains(Search); });
	Assets.Sort([](const FAssetData& A, const FAssetData& B) { return A.PackageName.LexicalLess(B.PackageName); });

	TArray<TSharedPtr<FJsonValue>> Found;
	int32 Checked = 0, Errors = 0, Warnings = 0;
	for (const FAssetData& Asset : Assets)
	{
		if (Checked >= Limit) break;
		UBlueprint* Blueprint = Cast<UBlueprint>(Asset.GetAsset());
		if (!Blueprint) continue;
		++Checked;
		UPackage* Package = Blueprint->GetOutermost();
		const bool bWasDirty = Package->IsDirty();
		FString One;
		const TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&One);
		W->WriteObjectStart();
		W->WriteValue(TEXT("bp_path"), Blueprint->GetPathName());
		DebugFeedbackUtils::CompileAndWrite(Blueprint, W);
		W->WriteObjectEnd();
		W->Close();
		Package->SetDirtyFlag(bWasDirty);  // Checking must not leave assets looking edited.
		TSharedPtr<FJsonObject> Object;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(One);
		if (!FJsonSerializer::Deserialize(Reader, Object) || !Object) continue;
		const int32 E = Object->GetIntegerField(TEXT("errors")), W2 = Object->GetIntegerField(TEXT("warnings"));
		Errors += E;
		Warnings += W2;
		if (E > 0 || (bIncludeWarnings && W2 > 0)) Found.Add(MakeShared<FJsonValueObject>(Object));
	}
	const TSharedRef<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetBoolField(TEXT("clean"), Errors == 0);
	Out->SetNumberField(TEXT("total_blueprints"), Assets.Num());
	Out->SetNumberField(TEXT("checked"), Checked);
	Out->SetBoolField(TEXT("truncated"), Checked < Assets.Num());
	Out->SetNumberField(TEXT("errors"), Errors);
	Out->SetNumberField(TEXT("warnings"), Warnings);
	Out->SetArrayField(TEXT("blueprints"), Found);
	FString Json;
	const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Json);
	FJsonSerializer::Serialize(Out, J);
	return Json;
}

FString ProjectDiagnosticsUtils::ProjectErrors(int32 Limit)
{
	if (Limit < 1 || Limit > 1000) Fail(TEXT("limit must be 1-1000"));
	FString Json;
	const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Json);
	J->WriteObjectStart();

	// This session's log, repeats folded together.
	const FString Path = CurrentLogFile();
	TMap<FString, int32> Repeats;
	TArray<FString> Order;
	int32 LogErrors = 0, LogWarnings = 0;
	for (const FString& Line : ReadLines(Path))
	{
		FString Category, Severity;
		ParseLine(Line, Category, Severity);
		if (Severity == TEXT("Warning")) ++LogWarnings;
		if (Severity != TEXT("Error") && Severity != TEXT("Fatal")) continue;
		if (Line.Contains(TEXT("LogTemp: Error: Runtime error:"))) continue;  // A rejected API call, already reported to its caller.
		++LogErrors;
		int32 Bracket = INDEX_NONE;
		Line.FindLastChar(TCHAR(']'), Bracket);
		const FString Text = Line.StartsWith(TEXT("[")) ? Line.Mid(Bracket + 1) : Line;
		if (int32* Count = Repeats.Find(Text)) ++*Count;
		else { Repeats.Add(Text, 1); Order.Add(Text); }
	}
	J->WriteObjectStart(TEXT("log"));
	J->WriteValue(TEXT("path"), Path);
	J->WriteValue(TEXT("errors"), LogErrors);
	J->WriteValue(TEXT("warnings"), LogWarnings);
	J->WriteArrayStart(TEXT("error_lines"));
	for (int32 Index = FMath::Max(0, Order.Num() - Limit); Index < Order.Num(); ++Index)
	{
		J->WriteObjectStart();
		J->WriteValue(TEXT("text"), Order[Index]);
		J->WriteValue(TEXT("count"), Repeats[Order[Index]]);
		J->WriteObjectEnd();
	}
	J->WriteArrayEnd();
	J->WriteObjectEnd();

	// The editor's Message Log pages.
	int32 MessageErrors = 0;
	FMessageLogModule& Messages = FModuleManager::LoadModuleChecked<FMessageLogModule>("MessageLog");
	J->WriteArrayStart(TEXT("message_logs"));
	for (const TCHAR* Name : {TEXT("BlueprintLog"), TEXT("LoadErrors"), TEXT("MapCheck"), TEXT("PIE"), TEXT("AssetCheck")})
	{
		if (!Messages.IsRegisteredLogListing(Name)) continue;
		int32 Written = 0;
		for (const TSharedRef<FTokenizedMessage>& Message : Messages.GetLogListing(Name)->GetFilteredMessages())
		{
			const EMessageSeverity::Type Severity = Message->GetSeverity();
			if (Severity != EMessageSeverity::Error && Severity != EMessageSeverity::Warning) continue;
			if (Severity == EMessageSeverity::Error) ++MessageErrors;
			if (++Written > Limit) continue;
			J->WriteObjectStart();
			J->WriteValue(TEXT("log"), Name);
			J->WriteValue(TEXT("severity"), Severity == EMessageSeverity::Error ? TEXT("error") : TEXT("warning"));
			J->WriteValue(TEXT("message"), Message->ToText().ToString());
			J->WriteObjectEnd();
		}
	}
	J->WriteArrayEnd();

	// The last C++ build, from Unreal Build Tool's log.
	const FString BuildLog = FPaths::Combine(FPlatformMisc::GetEnvironmentVariable(TEXT("LOCALAPPDATA")), TEXT("UnrealBuildTool/Log.txt"));
	int32 BuildErrors = 0;
	J->WriteObjectStart(TEXT("cpp_build"));
	FString BuildText;
	const bool bHasBuild = FFileHelper::LoadFileToString(BuildText, *BuildLog, FFileHelper::EHashOptions::None, FILEREAD_AllowWrite);
	J->WriteValue(TEXT("available"), bHasBuild);
	J->WriteValue(TEXT("path"), BuildLog);
	if (bHasBuild)
	{
		J->WriteValue(TEXT("finished_utc"), IFileManager::Get().GetTimeStamp(*BuildLog).ToIso8601());
		TArray<FString> Lines;
		BuildText.ParseIntoArrayLines(Lines);
		J->WriteArrayStart(TEXT("errors"));
		for (const FString& Line : Lines)
		{
			if (!Line.Contains(TEXT(": error ")) && !Line.Contains(TEXT(": fatal error ")) && !Line.Contains(TEXT(": Error: "))) continue;
			if (++BuildErrors <= Limit) J->WriteValue(Line.TrimStartAndEnd());
		}
		J->WriteArrayEnd();
	}
	J->WriteObjectEnd();

	J->WriteValue(TEXT("clean"), LogErrors == 0 && MessageErrors == 0 && BuildErrors == 0);
	J->WriteValue(TEXT("note"), TEXT("Blueprints are not compiled here; list_blueprint_errors checks them."));
	J->WriteObjectEnd();
	J->Close();
	return Json;
}

FString ProjectDiagnosticsUtils::ReadLogs(const FString& Search, const FString& Severity, const FString& Category, int32 SinceLine, int32 Limit)
{
	if (Limit < 1 || Limit > 5000 || SinceLine < 0) Fail(TEXT("limit must be 1-5000, and since_line cannot be negative"));
	if (!Severity.IsEmpty() && !Severity.Equals(TEXT("Fatal"), ESearchCase::IgnoreCase) && !Severity.Equals(TEXT("Error"), ESearchCase::IgnoreCase) && !Severity.Equals(TEXT("Warning"), ESearchCase::IgnoreCase)
		&& !Severity.Equals(TEXT("Display"), ESearchCase::IgnoreCase) && !Severity.Equals(TEXT("Log"), ESearchCase::IgnoreCase) && !Severity.Equals(TEXT("Verbose"), ESearchCase::IgnoreCase))
		Fail(TEXT("severity must be Fatal, Error, Warning, Display, Log or Verbose"));
	const FString Path = CurrentLogFile();
	const TArray<FString> Lines = ReadLines(Path);
	TArray<FString> Matches;
	int32 Total = 0;
	for (int32 Index = Lines.Num() - 1; Index >= SinceLine; --Index)
	{
		const FString& Line = Lines[Index];
		if (!Search.IsEmpty() && !Line.Contains(Search)) continue;
		FString LineCategory, LineSeverity;
		ParseLine(Line, LineCategory, LineSeverity);
		if (!Severity.IsEmpty() && !LineSeverity.Equals(Severity, ESearchCase::IgnoreCase)) continue;
		if (!Category.IsEmpty() && !LineCategory.Equals(Category, ESearchCase::IgnoreCase)) continue;
		if (++Total <= Limit) Matches.Add(Line);
	}
	Algo::Reverse(Matches);
	FString Json;
	const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Json);
	J->WriteObjectStart();
	J->WriteValue(TEXT("log_path"), Path);
	J->WriteValue(TEXT("world_context"), GEditor && GEditor->PlayWorld ? TEXT("pie") : TEXT("editor"));
	J->WriteValue(TEXT("returned"), Matches.Num());
	J->WriteValue(TEXT("matched"), Total);
	J->WriteValue(TEXT("truncated"), Total > Limit);
	J->WriteValue(TEXT("next_line"), Lines.Num());
	J->WriteArrayStart(TEXT("lines"));
	for (const FString& Line : Matches) J->WriteValue(Line);
	J->WriteArrayEnd();
	J->WriteObjectEnd();
	J->Close();
	return Json;
}
