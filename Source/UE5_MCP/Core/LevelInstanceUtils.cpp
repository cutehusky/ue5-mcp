#include "LevelInstanceUtils.h"

#include "UE5_MCP/API/DTO/LevelInstanceReq.h"
#include "Editor.h"
#include "Engine/Brush.h"
#include "Engine/Level.h"
#include "Engine/LevelScriptBlueprint.h"
#include "GameFramework/WorldSettings.h"
#include "Engine/World.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "LevelInstance/LevelInstanceActor.h"
#include "LevelInstance/LevelInstanceInterface.h"
#include "LevelInstance/LevelInstanceSubsystem.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "UObject/UObjectHash.h"

#include <stdexcept>

namespace
{
	void Fail(const FString& Message) { throw std::runtime_error(TCHAR_TO_UTF8(*Message)); }
	ULevelInstanceSubsystem* Subsystem(UWorld* World)
	{
		ULevelInstanceSubsystem* Result = World ? World->GetSubsystem<ULevelInstanceSubsystem>() : nullptr;
		if (!Result) Fail(TEXT("The editor world has no Level Instance subsystem"));
		return Result;
	}
	FString AssetPath(const FString& Input)
	{
		const FString Package = FPackageName::ObjectPathToPackageName(Input.TrimStartAndEnd());
		if (!Package.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(Package) || !FPackageName::DoesPackageExist(Package))
			Fail(TEXT("world_asset_path must identify a saved /Game map"));
		const FString Object = Package + TEXT(".") + FPackageName::GetShortName(Package);
		if (!Cast<UWorld>(StaticLoadObject(UWorld::StaticClass(), nullptr, *Object))) Fail(TEXT("world_asset_path is not a World asset"));
		return Object;
	}
	void CheckMapTree(const FString& Object, const TSet<FString>& Forbidden, TSet<FString>& Stack, TSet<FString>& Visited)
	{
		const FString Package = FPackageName::ObjectPathToPackageName(Object);
		if (Forbidden.Contains(Package) || Stack.Contains(Package)) Fail(TEXT("The Level Instance map reference would create a map cycle: ") + Package);
		if (Visited.Contains(Package)) return;
		if (Visited.Num() + Stack.Num() >= 128) Fail(TEXT("Level Instance validation exceeded its 128-map traversal bound"));
		UWorld* Asset = Cast<UWorld>(StaticLoadObject(UWorld::StaticClass(), nullptr, *Object));
		if (!Asset || !Asset->PersistentLevel) Fail(TEXT("Could not inspect a referenced Level Instance source map: ") + Object);
		Stack.Add(Package);
		for (AActor* Actor : Asset->PersistentLevel->Actors)
			if (ILevelInstanceInterface* Child = Actor ? Cast<ILevelInstanceInterface>(Actor) : nullptr)
				if (!Child->GetWorldAsset().IsNull()) CheckMapTree(AssetPath(Child->GetWorldAsset().ToSoftObjectPath().ToString()), Forbidden, Stack, Visited);
		Stack.Remove(Package); Visited.Add(Package);
	}
	void CheckTarget(UWorld* World, AActor* Actor, const FString& Object)
	{
		TSet<FString> Forbidden = {World->GetPackage()->GetName()};
		ULevel* Owner = Actor ? Actor->GetLevel() : World->GetCurrentLevel();
		if (Owner) Forbidden.Add(Owner->GetPackage()->GetName());
		TSet<FString> Stack, Visited;
		CheckMapTree(Object, Forbidden, Stack, Visited);
		if (Actor)
		{
			FString Reason;
			if (!ULevelInstanceSubsystem::CanUseWorldAsset(CastChecked<ILevelInstanceInterface>(Actor), TSoftObjectPtr<UWorld>(FSoftObjectPath(Object)), &Reason)) Fail(Reason);
		}
	}
	AActor* Resolve(UWorld* World, const FString& Path)
	{
		AActor* Actor = Cast<AActor>(StaticFindObject(AActor::StaticClass(), nullptr, *Path));
		if (!Actor || Actor->GetWorld() != World || !Cast<ILevelInstanceInterface>(Actor)) Fail(TEXT("actor_path must identify a Level Instance in the active editor world"));
		return Actor;
	}
	void WriteVector(const TSharedRef<TJsonWriter<>>& Writer, const FString& Name, const FVector& Value)
	{
		Writer->WriteObjectStart(Name);
		Writer->WriteValue(TEXT("x"), Value.X); Writer->WriteValue(TEXT("y"), Value.Y); Writer->WriteValue(TEXT("z"), Value.Z);
		Writer->WriteObjectEnd();
	}
	void WriteTransform(const TSharedRef<TJsonWriter<>>& Writer, const FTransform& Value)
	{
		Writer->WriteObjectStart(TEXT("transform"));
		WriteVector(Writer, TEXT("location"), Value.GetLocation());
		WriteVector(Writer, TEXT("scale"), Value.GetScale3D());
		const FRotator Rotation = Value.Rotator();
		Writer->WriteObjectStart(TEXT("rotation"));
		Writer->WriteValue(TEXT("pitch"), Rotation.Pitch); Writer->WriteValue(TEXT("yaw"), Rotation.Yaw); Writer->WriteValue(TEXT("roll"), Rotation.Roll);
		Writer->WriteObjectEnd(); Writer->WriteObjectEnd();
	}
	int32 LoadedActors(ULevelInstanceSubsystem* System, ILevelInstanceInterface* Instance)
	{
		int32 Count = 0;
		System->ForEachActorInLevelInstance(Instance, [&Count](AActor*) { ++Count; return true; });
		return Count;
	}
	TArray<UPackage*> EditPackages(ULevelInstanceSubsystem* System, ILevelInstanceInterface* Instance)
	{
		TArray<UPackage*> Result;
		if (!Instance->IsEditing()) return Result;
		ULevel* Level = System->GetLevelInstanceLevel(Instance);
		const UWorld* EditingWorld = Level ? Level->GetTypedOuter<UWorld>() : nullptr;
		if (!EditingWorld) return Result;
		FEditorFileUtils::GetDirtyPackages(Result, [EditingWorld](UPackage* Package)
		{
			if (Package == EditingWorld->GetOutermost()) return false;
			bool bIgnore = true;
			ForEachObjectWithPackage(Package, [EditingWorld, &bIgnore](UObject* Object)
			{
				if (Object->GetOutermostObject() == EditingWorld) bIgnore = false;
				return bIgnore;
			});
			return bIgnore;
		});
		return Result;
	}
	void WriteState(const TSharedRef<TJsonWriter<>>& Writer, UWorld* World, AActor* Actor, bool bValidate)
	{
		ILevelInstanceInterface* Instance = CastChecked<ILevelInstanceInterface>(Actor);
		ULevelInstanceSubsystem* System = Subsystem(World);
		Writer->WriteValue(TEXT("actor_path"), Actor->GetPathName());
		Writer->WriteValue(TEXT("label"), Actor->GetActorLabel());
		Writer->WriteValue(TEXT("class"), Actor->GetClass()->GetPathName());
		Writer->WriteValue(TEXT("owner_package"), Actor->GetLevel()->GetPackage()->GetName());
		Writer->WriteValue(TEXT("world_asset"), Instance->GetWorldAsset().ToSoftObjectPath().ToString());
		Writer->WriteValue(TEXT("guid"), Instance->GetLevelInstanceGuid().ToString());
		Writer->WriteValue(TEXT("runtime_id"), LexToString(Instance->GetLevelInstanceID().GetHash()));
		Writer->WriteValue(TEXT("loaded"), System->IsLoaded(Instance));
		Writer->WriteValue(TEXT("loading"), System->IsLoading(Instance));
		Writer->WriteValue(TEXT("loading_enabled"), Instance->IsLoadingEnabled());
		Writer->WriteValue(TEXT("editing"), Instance->IsInAnyEditMode());
		Writer->WriteValue(TEXT("editing_source"), Instance->IsEditing());
		Writer->WriteValue(TEXT("editing_dirty"), Instance->IsDirty());
		Writer->WriteValue(TEXT("native_can_break"), System->CanBreakLevelInstance(Instance));
		Writer->WriteValue(TEXT("has_loaded_content"), System->GetLevelInstanceLevel(Instance) != nullptr);
		FText EnterReason, CommitReason, DiscardReason;
		const bool bCanEnter = FModuleManager::Get().IsModuleLoaded(TEXT("LevelInstanceEditor")) && Instance->CanEnterEdit(&EnterReason);
		Writer->WriteValue(TEXT("can_enter_edit"), bCanEnter);
		Writer->WriteValue(TEXT("enter_edit_reason"), EnterReason.ToString());
		Writer->WriteValue(TEXT("can_commit_edit"), Instance->CanExitEdit(false, &CommitReason));
		Writer->WriteValue(TEXT("can_discard_edit"), Instance->CanExitEdit(true, &DiscardReason));
		Writer->WriteValue(TEXT("discard_edit_reason"), DiscardReason.ToString());
		Writer->WriteArrayStart(TEXT("edit_dirty_packages")); for (UPackage* Package : EditPackages(System, Instance)) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Actor->GetPackage()->IsDirty());
		Writer->WriteValue(TEXT("runtime_behavior"), Instance->GetDesiredRuntimeBehavior() == ELevelInstanceRuntimeBehavior::LevelStreaming ? TEXT("standalone") : TEXT("embedded"));
		WriteTransform(Writer, Actor->GetActorTransform());
		Writer->WriteValue(TEXT("loaded_actor_count"), LoadedActors(System, Instance));
		Writer->WriteArrayStart(TEXT("loaded_actors"));
		int32 Returned = 0;
		System->ForEachActorInLevelInstance(Instance, [&Writer, &Returned](AActor* Child)
		{
			if (!Child || Returned >= 256) return Returned < 256;
			++Returned; Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("actor_path"), Child->GetPathName());
			Writer->WriteValue(TEXT("label"), Child->GetActorLabel());
			Writer->WriteValue(TEXT("class"), Child->GetClass()->GetPathName());
			WriteVector(Writer, TEXT("location"), Child->GetActorLocation());
			Writer->WriteObjectEnd(); return true;
		});
		Writer->WriteArrayEnd();
		if (bValidate)
		{
			TArray<FString> Errors;
			if (!Instance->GetLevelInstanceGuid().IsValid()) Errors.Add(TEXT("Level Instance GUID is invalid"));
			try { CheckTarget(World, Actor, AssetPath(Instance->GetWorldAsset().ToSoftObjectPath().ToString())); }
			catch (const std::exception& Error) { Errors.Add(UTF8_TO_TCHAR(Error.what())); }
			Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
			Writer->WriteArrayStart(TEXT("validation_errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		}
	}
	void CheckMutable(UWorld* World, AActor* Actor)
	{
		if (!GEditor || GEditor->PlayWorld || !IsInGameThread()) Fail(TEXT("Level Instance mutations require the editor game thread with PIE stopped"));
		ULevelInstanceSubsystem* System = Subsystem(World);
		if (System->GetEditingLevelInstance()) Fail(TEXT("Finish the active Level Instance editing session before this operation"));
		if (Actor)
		{
			ILevelInstanceInterface* Instance = CastChecked<ILevelInstanceInterface>(Actor);
			if (!Actor->IsUserManaged() || Instance->IsInAnyEditMode() || Instance->HasParentEdit() || Instance->HasChildEdit())
				Fail(TEXT("This Level Instance cannot be changed outside its owning editing context"));
		}
		else if (World->GetCurrentLevel() && System->GetOwningLevelInstance(World->GetCurrentLevel()))
			Fail(TEXT("Create Level Instances in a normal editor level, not in a loaded instance copy"));
	}
	void CheckUnload(ULevelInstanceSubsystem* System, ILevelInstanceInterface* Instance)
	{
		if (Instance->IsDirty() || Instance->HasDirtyChildren()) Fail(TEXT("Save or finish dirty Level Instance edits before unloading its content"));
		if (ULevel* Level = System->GetLevelInstanceLevel(Instance))
			if (Level->GetPackage()->IsDirty()) Fail(TEXT("Loaded Level Instance content has unsaved changes"));
	}
	void UnloadNow(ULevelInstanceSubsystem* System, ILevelInstanceInterface* Instance)
	{
		System->RequestUnloadLevelInstance(Instance);
		// UE's BlockUnload helper only waits while loads are pending. Drain unloads explicitly.
		TGuardValue<decltype(GUndo)> TransactionGuard(GUndo, nullptr);
		System->OnUpdateStreamingState();
		System->GetWorld()->FlushLevelStreaming();
	}
	struct FBreakItem
	{
		FString Path, Label, Class, Map;
	};
	void PreviewBreakMap(ULevelInstanceSubsystem* System, const FString& Object, int32 Depth, TArray<FBreakItem>& Items, int32& TraversedActors)
	{
		UWorld* Source = CastChecked<UWorld>(StaticLoadObject(UWorld::StaticClass(), nullptr, *Object));
		ULevel* Level = Source->PersistentLevel;
		if (Source->GetWorldPartition() || Level->IsUsingExternalActors())
			Fail(TEXT("Breaking World Partition or external-actor source maps is not supported yet"));
		if (ULevelScriptBlueprint* Script = Level->GetLevelScriptBlueprint(false))
		{
			TArray<UEdGraph*> Graphs; Script->GetAllGraphs(Graphs);
			for (UEdGraph* Graph : Graphs) if (Graph) for (UEdGraphNode* Node : Graph->Nodes)
				if (Node && !Node->IsAutomaticallyPlacedGhostNode()) Fail(TEXT("Level Instances with authored Level Script nodes cannot be broken: ") + Object);
		}
		for (AActor* Actor : Level->Actors)
		{
			if (!Actor || Actor->HasAnyFlags(RF_Transient) || Actor == Level->GetDefaultBrush() || Actor->IsA<AWorldSettings>() || Actor->IsMainWorldOnly()) continue;
			FText Reason;
			if (!System->CanMoveActorToLevel(Actor, &Reason))
			{
				if (!Reason.IsEmpty()) Fail(Reason.ToString());
				continue;
			}
			if (++TraversedActors > 512) Fail(TEXT("Break preview exceeds the 512-actor traversal bound"));
			if (ILevelInstanceInterface* Child = Cast<ILevelInstanceInterface>(Actor))
			{
				if (Actor->GetExternalDataLayerAsset()) Fail(TEXT("Breaking Level Instances in external Data Layers is not supported by the native move API"));
				if (Depth > 1)
				{
					if (Child->GetWorldAsset().IsNull()) Fail(TEXT("A nested Level Instance has no source map to break"));
					PreviewBreakMap(System, AssetPath(Child->GetWorldAsset().ToSoftObjectPath().ToString()), Depth - 1, Items, TraversedActors);
					continue;
				}
			}
			Items.Add({Actor->GetPathName(), Actor->GetActorLabel(), Actor->GetClass()->GetPathName(), Source->GetPackage()->GetName()});
		}
	}
	FString Break(UWorld* World, const FLevelInstanceReq& Request)
	{
		if (Request.BreakDepth < 1 || Request.BreakDepth > 8) Fail(TEXT("break_depth must be between 1 and 8"));
		if (!Request.bWait) Fail(TEXT("Native Level Instance break requires wait=true"));
		AActor* Actor = Resolve(World, Request.ActorPath);
		CheckMutable(World, Actor);
		if (World->GetWorldPartition() || Actor->GetLevel()->IsUsingExternalActors() || Actor->IsPackageExternal())
			Fail(TEXT("Breaking into World Partition or external-actor levels is not supported yet"));
		if (GUndo) Fail(TEXT("Finish the current editor transaction before breaking a Level Instance"));
		ULevelInstanceSubsystem* System = Subsystem(World);
		ILevelInstanceInterface* Instance = CastChecked<ILevelInstanceInterface>(Actor);
		CheckUnload(System, Instance);
		const FString Target = AssetPath(Instance->GetWorldAsset().ToSoftObjectPath().ToString());
		CheckTarget(World, Actor, Target);
		TArray<FBreakItem> Preview;
		int32 TraversedActors = 0;
		PreviewBreakMap(System, Target, Request.BreakDepth, Preview, TraversedActors);
		if (!System->CanBreakLevelInstance(Instance)) Fail(TEXT("Unreal does not permit breaking this Level Instance in its current state"));
		if (!Request.bDryRun && !Request.bConfirm) Fail(TEXT("Breaking a Level Instance copies its actors and clears undo history; confirm=true is required"));
		const FString OriginalPath = Actor->GetPathName();
		const FString OriginalPackage = Actor->GetPackage()->GetName();
		ULevel* OwnerLevel = Actor->GetLevel();
		TArray<UPackage*> Packages = {OwnerLevel->GetPackage()};
		TArray<AActor*> Moved;
		TArray<FString> Errors;
		bool bRemoved = false, bSaved = false, bNativeResult = false, bAttempted = false;
		if (!Request.bDryRun)
		{
			TSet<AActor*> Before;
			for (AActor* Existing : OwnerLevel->Actors) if (Existing) Before.Add(Existing);
			System->BlockLoadLevelInstance(Instance);
			CheckUnload(System, Instance);
			if (!System->CanBreakLevelInstance(Instance)) Fail(TEXT("Loaded source content prevents native break"));
			System->ForEachActorInLevelInstance(Instance, [System](AActor* Child)
			{
				if (!Child || Child == Child->GetLevel()->GetDefaultBrush() || Child->IsA<AWorldSettings>() || Child->IsMainWorldOnly()) return true;
				FText Reason;
				if (!System->CanMoveActorToLevel(Child, &Reason) && !Reason.IsEmpty()) Fail(Reason.ToString());
				return true;
			});
			OwnerLevel->Modify(); Actor->Modify();
			bAttempted = true;
			{
				TGuardValue<bool> UnattendedScriptGuard(GIsRunningUnattendedScript, true);
				bNativeResult = System->BreakLevelInstance(Instance, Request.BreakDepth, &Moved,
					Request.bKeepFolders ? ELevelInstanceBreakFlags::KeepFolders : ELevelInstanceBreakFlags::None);
			}
			bRemoved = !IsValid(Actor) || Actor->IsActorBeingDestroyed();
			System->OnUpdateStreamingState(); World->FlushLevelStreaming();
			// Native recursive break omits a copied child from its output when that
			// child's break fails. Include every surviving actor created in the owner.
			for (AActor* Result : OwnerLevel->Actors)
				if (IsValid(Result) && !Result->IsActorBeingDestroyed() && !Result->HasAnyFlags(RF_Transient) && !Before.Contains(Result)) Moved.AddUnique(Result);
			if (!bRemoved) Errors.Add(TEXT("Native break did not remove the selected instance; inspect the reported actor changes before retrying"));
			if (!bNativeResult && !Preview.IsEmpty()) Errors.Add(TEXT("Native break did not complete all requested actor copies"));
			if (Moved.Num() != Preview.Num()) Errors.Add(TEXT("Native break actor count differs from the source preview; inspect the partial result before retrying"));
			TMap<FString, int32> ExpectedClasses, ActualClasses;
			for (const FBreakItem& Item : Preview) ++ExpectedClasses.FindOrAdd(Item.Class);
			for (AActor* Result : Moved) if (IsValid(Result)) ++ActualClasses.FindOrAdd(Result->GetClass()->GetPathName());
			if (!ExpectedClasses.OrderIndependentCompareEqual(ActualClasses)) Errors.Add(TEXT("Native break actor classes differ from the source preview; nested instances may remain unbroken"));
			for (AActor* Result : Moved) if (IsValid(Result)) { Result->MarkPackageDirty(); Packages.AddUnique(Result->GetPackage()); }
			if (bRemoved || !Moved.IsEmpty()) for (UPackage* Package : Packages) Package->MarkPackageDirty();
			if (Request.bSave && Errors.IsEmpty())
			{
				bSaved = UEditorLoadingAndSavingUtils::SavePackages(Packages, true);
				if (!bSaved) Errors.Add(TEXT("Break completed, but the owning packages could not be saved"));
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart(); Writer->WriteValue(TEXT("operation"), TEXT("break"));
		Writer->WriteValue(TEXT("actor_path"), OriginalPath); Writer->WriteValue(TEXT("source_world_asset"), Target);
		Writer->WriteValue(TEXT("success"), Errors.IsEmpty()); Writer->WriteValue(TEXT("changed"), bRemoved || !Moved.IsEmpty());
		Writer->WriteValue(TEXT("dry_run"), Request.bDryRun); Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("break_depth"), Request.BreakDepth); Writer->WriteValue(TEXT("keep_folders"), Request.bKeepFolders);
		Writer->WriteValue(TEXT("confirmation_required"), true); Writer->WriteValue(TEXT("undoable"), false);
		Writer->WriteValue(TEXT("resets_undo_history"), true); Writer->WriteValue(TEXT("break_attempted"), bAttempted);
		Writer->WriteValue(TEXT("native_result"), bNativeResult); Writer->WriteValue(TEXT("instance_removed"), bRemoved);
		Writer->WriteValue(TEXT("atomic"), false); Writer->WriteValue(TEXT("may_have_changed"), bAttempted);
		Writer->WriteValue(TEXT("breakable_actor_count"), Preview.Num());
		Writer->WriteValue(TEXT("traversed_actor_count"), TraversedActors);
		Writer->WriteArrayStart(TEXT("source_actors"));
		for (const FBreakItem& Item : Preview)
		{
			Writer->WriteObjectStart(); Writer->WriteValue(TEXT("source_actor_path"), Item.Path);
			Writer->WriteValue(TEXT("label"), Item.Label); Writer->WriteValue(TEXT("class"), Item.Class);
			Writer->WriteValue(TEXT("source_map"), Item.Map); Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd(); Writer->WriteValue(TEXT("moved_actor_count"), Moved.Num());
		Writer->WriteValue(TEXT("moved_actors_truncated"), Moved.Num() > 512);
		Writer->WriteArrayStart(TEXT("moved_actors"));
		for (int32 Index = 0; Index < FMath::Min(Moved.Num(), 512); ++Index) if (IsValid(Moved[Index]))
		{
			AActor* Result = Moved[Index]; Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("actor_path"), Result->GetPathName()); Writer->WriteValue(TEXT("label"), Result->GetActorLabel());
			Writer->WriteValue(TEXT("class"), Result->GetClass()->GetPathName()); Writer->WriteValue(TEXT("folder"), Result->GetFolderPath().ToString());
			Writer->WriteValue(TEXT("owner_level"), Result->GetLevel()->GetPathName()); WriteTransform(Writer, Result->GetActorTransform());
			Writer->WriteValue(TEXT("transient"), Result->HasAnyFlags(RF_Transient));
			Writer->WriteValue(TEXT("in_owner_level"), OwnerLevel->Actors.Contains(Result));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd(); Writer->WriteArrayStart(TEXT("changed_packages"));
		if (bRemoved || !Moved.IsEmpty()) for (UPackage* Package : Packages) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("would_change_packages"));
		if (Request.bDryRun) for (UPackage* Package : Packages) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("removed_actor_package"), bRemoved && OriginalPackage != OwnerLevel->GetPackage()->GetName() ? OriginalPackage : TEXT(""));
		Writer->WriteArrayStart(TEXT("dirty_packages")); for (UPackage* Package : Packages) if (Package->IsDirty()) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		Writer->WriteObjectEnd(); Writer->Close(); return Json;
	}
	FString Edit(UWorld* World, const FLevelInstanceReq& Request)
	{
		if (!GEditor || GEditor->PlayWorld || !IsInGameThread()) Fail(TEXT("Level Instance editing requires the editor game thread with PIE stopped"));
		if (!Request.bWait) Fail(TEXT("Native Level Instance edit/commit operations require wait=true"));
		if (!FModuleManager::Get().LoadModulePtr<IModuleInterface>(TEXT("LevelInstanceEditor"))) Fail(TEXT("The Level Instance editor module is unavailable"));
		AActor* Actor = Resolve(World, Request.ActorPath);
		ILevelInstanceInterface* Instance = CastChecked<ILevelInstanceInterface>(Actor);
		ULevelInstanceSubsystem* System = Subsystem(World);
		for (TActorIterator<AActor> It(World); It; ++It)
			if (ILevelInstanceInterface* Other = Cast<ILevelInstanceInterface>(*It))
				if (Other->IsEditingPropertyOverrides()) Fail(TEXT("Finish property-override editing before source-level edit/commit operations"));
		const FString Operation = Request.Operation.ToLower();
		const bool bEnter = Operation == TEXT("enter_edit");
		const bool bDiscard = Operation == TEXT("discard");
		const bool bEditingBefore = Instance->IsEditing();
		const bool bDirtyBefore = Instance->IsDirty();
		const FString Source = Instance->GetWorldAsset().ToSoftObjectPath().ToString();
		const FString ActorPath = Actor->GetPathName();
		const FLevelInstanceID ID = Instance->GetLevelInstanceID();
		TArray<FString> DirtyBefore;
		for (UPackage* Package : EditPackages(System, Instance)) DirtyBefore.Add(Package->GetName());
		if ((bEnter || bDiscard) && Request.bSave) Fail(TEXT("enter_edit/discard does not save; use commit with save=true to persist source changes"));
		FText Reason;
		if (bEnter)
		{
			if (System->GetEditingLevelInstance() && System->GetEditingLevelInstance() != Instance)
				Fail(TEXT("Finish the current Level Instance editing session before entering another"));
			if (!bEditingBefore)
			{
				if (!Instance->CanEnterEdit(&Reason)) Fail(Reason.ToString());
				CheckTarget(World, Actor, AssetPath(Source)); CheckUnload(System, Instance);
			}
		}
		else
		{
			if (System->GetEditingLevelInstance() != Instance || !Instance->CanExitEdit(bDiscard, &Reason))
				Fail(Reason.IsEmpty() ? TEXT("This Level Instance is not the active source editing session") : Reason.ToString());
			if (!Request.bDryRun && bDiscard && !Request.bConfirm) Fail(TEXT("Discarding a Level Instance editing session requires confirm=true"));
			if (!Request.bDryRun && !bDiscard && bDirtyBefore && !Request.bSave)
				Fail(TEXT("The editing session has unsaved source changes; commit requires save=true or choose confirmed discard"));
		}
		TArray<FString> Errors;
		bool bChanged = false, bSaved = false, bSaveAttempted = false, bCommitAttempted = false;
		if (!Request.bDryRun)
		{
			if (bEnter && !bEditingBefore)
			{
				System->EditLevelInstance(Instance);
				bChanged = Instance->IsEditing();
				if (!bChanged) Errors.Add(TEXT("Unreal could not enter the Level Instance editing session"));
			}
			else if (!bEnter)
			{
				if (!bDiscard && bDirtyBefore && Request.bSave)
				{
					const TArray<UPackage*> Packages = EditPackages(System, Instance);
					if (Packages.IsEmpty()) Errors.Add(TEXT("Dirty editing packages could not be identified for an explicit save"));
					else
					{
						bSaveAttempted = true;
						bSaved = UEditorLoadingAndSavingUtils::SavePackages(Packages, true);
						if (!bSaved) Errors.Add(TEXT("Source package save failed; the editing session was kept active"));
						else if (Instance->IsDirty()) Errors.Add(TEXT("The editing context still has pending packages after save; resolve them before committing"));
					}
				}
				if (Errors.IsEmpty())
				{
					bCommitAttempted = true;
					TGuardValue<bool> UnattendedScriptGuard(GIsRunningUnattendedScript, true);
					const bool bCommitted = System->CommitLevelInstance(Instance, bDiscard);
					if (!bCommitted) Errors.Add(TEXT("Native Level Instance commit/discard failed; the editing session may remain active"));
					Instance = System->GetLevelInstance(ID);
					Actor = Instance ? Cast<AActor>(Instance) : nullptr;
					bChanged = bCommitted && (!Instance || !Instance->IsEditing());
				}
				bChanged |= bSaved;
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart(); Writer->WriteValue(TEXT("operation"), Operation);
		Writer->WriteValue(TEXT("actor_path"), Actor ? Actor->GetPathName() : ActorPath);
		Writer->WriteValue(TEXT("source_world_asset"), Source);
		Writer->WriteValue(TEXT("success"), Errors.IsEmpty());
		if (bSaveAttempted && !bSaved) Writer->WriteNull(TEXT("changed")); else Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), Request.bDryRun); Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("editing_before"), bEditingBefore); Writer->WriteValue(TEXT("source_dirty_before"), bDirtyBefore);
		Writer->WriteValue(TEXT("save_required"), !bEnter && !bDiscard && bDirtyBefore);
		Writer->WriteValue(TEXT("confirmation_required"), bDiscard);
		Writer->WriteValue(TEXT("discarded_changes"), bDiscard && bChanged && bDirtyBefore);
		Writer->WriteValue(TEXT("atomic"), false);
		Writer->WriteValue(TEXT("may_have_saved_packages"), bSaveAttempted);
		Writer->WriteValue(TEXT("commit_attempted"), bCommitAttempted);
		Writer->WriteArrayStart(TEXT("dirty_packages_before")); for (const FString& Name : DirtyBefore) Writer->WriteValue(Name); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("saved_packages")); if (bSaved) for (const FString& Name : DirtyBefore) Writer->WriteValue(Name); Writer->WriteArrayEnd();
		if (Actor && IsValid(Actor)) { Writer->WriteObjectStart(TEXT("instance")); WriteState(Writer, World, Actor, false); Writer->WriteObjectEnd(); }
		Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		Writer->WriteObjectEnd(); Writer->Close(); return Json;
	}
}

FString LevelInstanceUtils::Inspect(UWorld* World, const FString& ActorPath, bool bValidate)
{
	Subsystem(World);
	TArray<AActor*> Actors;
	if (!ActorPath.IsEmpty()) Actors.Add(Resolve(World, ActorPath));
	else for (TActorIterator<AActor> It(World); It; ++It) if (Cast<ILevelInstanceInterface>(*It)) Actors.Add(*It);
	Actors.Sort([](const AActor& Left, const AActor& Right) { return Left.GetPathName() < Right.GetPathName(); });
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart(); Writer->WriteValue(TEXT("world_path"), World->GetPathName());
	Writer->WriteValue(TEXT("instance_count"), Actors.Num()); Writer->WriteValue(TEXT("truncated"), Actors.Num() > 256);
	Writer->WriteArrayStart(TEXT("instances"));
	for (int32 Index = 0; Index < FMath::Min(Actors.Num(), 256); ++Index)
	{
		Writer->WriteObjectStart(); WriteState(Writer, World, Actors[Index], bValidate); Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd(); Writer->WriteObjectEnd(); Writer->Close(); return Json;
}

FString LevelInstanceUtils::Operate(UWorld* World, const FLevelInstanceReq& Request)
{
	const FString Operation = Request.Operation.ToLower();
	if (Operation == TEXT("enter_edit") || Operation == TEXT("commit") || Operation == TEXT("discard")) return Edit(World, Request);
	if (Operation == TEXT("break")) return Break(World, Request);
	if (Operation != TEXT("create") && Operation != TEXT("load") && Operation != TEXT("unload")
		&& Operation != TEXT("set_asset") && Operation != TEXT("transform") && Operation != TEXT("remove"))
		Fail(TEXT("operation must be create, load, unload, set_asset, transform, remove, enter_edit, commit, discard, or break"));
	AActor* Actor = Operation == TEXT("create") ? nullptr : Resolve(World, Request.ActorPath);
	CheckMutable(World, Actor);
	ULevelInstanceSubsystem* System = Subsystem(World);
	ILevelInstanceInterface* Instance = Actor ? CastChecked<ILevelInstanceInterface>(Actor) : nullptr;
	const FString PreviousAsset = Instance ? Instance->GetWorldAsset().ToSoftObjectPath().ToString() : TEXT("");
	const bool bWasLoaded = Instance && System->IsLoaded(Instance);
	const int32 AffectedActors = Instance ? LoadedActors(System, Instance) : 0;
	FString Target;
	if (Operation == TEXT("create") || Operation == TEXT("set_asset") || Operation == TEXT("load"))
	{
		Target = AssetPath(Operation == TEXT("load") ? PreviousAsset : Request.WorldAssetPath);
		CheckTarget(World, Actor, Target);
	}
	if ((Operation == TEXT("create") || Operation == TEXT("transform")) &&
		(Request.Transform.ContainsNaN() || !Request.Transform.GetRotation().IsNormalized() ||
		FMath::Abs(Request.Transform.GetScale3D().X) < SMALL_NUMBER || FMath::Abs(Request.Transform.GetScale3D().Y) < SMALL_NUMBER || FMath::Abs(Request.Transform.GetScale3D().Z) < SMALL_NUMBER))
		Fail(TEXT("transform must be finite, with a normalized rotation and nonzero scale"));
	if (Operation == TEXT("unload") || Operation == TEXT("remove") || Operation == TEXT("set_asset")) CheckUnload(System, Instance);
	if (Operation == TEXT("remove")) { FText Reason; if (!Actor->CanDeleteSelectedActor(Reason)) Fail(Reason.ToString()); }
	const bool bConfirmation = Operation == TEXT("remove") || Operation == TEXT("set_asset") || (Operation == TEXT("unload") && bWasLoaded);
	if (!Request.bDryRun && bConfirmation && !Request.bConfirm) Fail(TEXT("This Level Instance operation requires confirm=true"));
	TArray<UPackage*> Packages;
	ULevel* OwnerLevel = Actor ? Actor->GetLevel() : World->GetCurrentLevel();
	if (OwnerLevel) Packages.AddUnique(OwnerLevel->GetPackage());
	FString ActorPath = Actor ? Actor->GetPathName() : TEXT("");
	bool bChanged = false, bSaved = false, bTransaction = false;
	TArray<FString> Errors;
	const bool bStructural = Operation == TEXT("create") || Operation == TEXT("set_asset") || Operation == TEXT("transform") || Operation == TEXT("remove");
	if (!Request.bDryRun)
	{
		if (bStructural)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "LevelInstanceOperation", "Edit Level Instance"));
			bTransaction = true;
			if (OwnerLevel) OwnerLevel->Modify();
			if (Actor) Actor->Modify();
			if (Operation == TEXT("create"))
			{
				Actor = GEditor->GetEditorSubsystem<UEditorActorSubsystem>()->SpawnActorFromClass(ALevelInstance::StaticClass(), Request.Transform.GetLocation(), Request.Transform.Rotator());
				if (!Actor) Fail(TEXT("Could not spawn the Level Instance actor"));
				Instance = CastChecked<ILevelInstanceInterface>(Actor);
				Instance->SetDesiredRuntimeBehavior(ELevelInstanceRuntimeBehavior::LevelStreaming);
				if (!Instance->SetWorldAsset(TSoftObjectPtr<UWorld>(FSoftObjectPath(Target)))) { GEditor->GetEditorSubsystem<UEditorActorSubsystem>()->DestroyActor(Actor); Fail(TEXT("Unreal rejected the Level Instance map")); }
				Actor->SetActorTransform(Request.Transform); if (!Request.Label.IsEmpty()) Actor->SetActorLabel(Request.Label);
				ActorPath = Actor->GetPathName();
			}
			else if (Operation == TEXT("set_asset"))
			{
				UnloadNow(System, Instance);
				if (!Instance->SetWorldAsset(TSoftObjectPtr<UWorld>(FSoftObjectPath(Target)))) Fail(TEXT("Unreal rejected the Level Instance map"));
			}
			else if (Operation == TEXT("transform")) { Actor->SetActorTransform(Request.Transform); Actor->PostEditMove(true); }
			else
			{
				UnloadNow(System, Instance);
				if (!GEditor->GetEditorSubsystem<UEditorActorSubsystem>()->DestroyActor(Actor)) Fail(TEXT("Could not remove the Level Instance actor"));
				Actor = nullptr; Instance = nullptr;
			}
			if (Actor) { Actor->MarkPackageDirty(); Packages.AddUnique(Actor->GetPackage()); }
			for (UPackage* Package : Packages) Package->MarkPackageDirty();
			bChanged = true;
			if (Instance && (Operation == TEXT("create") || Operation == TEXT("set_asset")) && Request.bLoad)
				if (Request.bWait) System->BlockLoadLevelInstance(Instance); else Instance->LoadLevelInstance();
			if (Request.bSave)
			{
				bSaved = UEditorLoadingAndSavingUtils::SavePackages(Packages, true);
				if (!bSaved) Errors.Add(TEXT("Level Instance changed, but its owning packages could not be saved"));
			}
		}
		else
		{
			if (!Instance->IsLoadingEnabled()) Fail(TEXT("This Level Instance does not support standalone editor loading"));
			if (Operation == TEXT("load")) { if (Request.bWait) System->BlockLoadLevelInstance(Instance); else Instance->LoadLevelInstance(); }
			else { if (Request.bWait) UnloadNow(System, Instance); else Instance->UnloadLevelInstance(); }
			bChanged = bWasLoaded != System->IsLoaded(Instance) || System->IsLoading(Instance);
		}
		if (Instance && Request.bWait && (Operation == TEXT("load") || Operation == TEXT("unload") ||
			((Operation == TEXT("create") || Operation == TEXT("set_asset")) && Request.bLoad)))
			if (System->IsLoaded(Instance) != (Operation != TEXT("unload"))) Errors.Add(TEXT("The native streaming operation did not reach the requested loaded state"));
	}
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart(); Writer->WriteValue(TEXT("operation"), Operation);
	Writer->WriteValue(TEXT("actor_path"), ActorPath); Writer->WriteValue(TEXT("world_asset"), Target.IsEmpty() ? PreviousAsset : Target);
	Writer->WriteValue(TEXT("previous_world_asset"), PreviousAsset);
	Writer->WriteValue(TEXT("success"), Errors.IsEmpty());
	Writer->WriteValue(TEXT("changed"), bChanged); Writer->WriteValue(TEXT("dry_run"), Request.bDryRun); Writer->WriteValue(TEXT("saved"), bSaved);
	Writer->WriteValue(TEXT("transaction_created"), bTransaction); Writer->WriteValue(TEXT("confirmation_required"), bConfirmation);
	Writer->WriteValue(TEXT("affected_actor_count"), AffectedActors); Writer->WriteValue(TEXT("editor_load_state_persistent"), false);
	if (Operation == TEXT("create") || Operation == TEXT("transform")) WriteTransform(Writer, Request.Transform);
	Writer->WriteValue(TEXT("request_queued"), !Request.bDryRun && !Request.bWait && Operation != TEXT("remove") && Operation != TEXT("transform"));
	Writer->WriteArrayStart(TEXT("would_change_packages")); if (Request.bDryRun && bStructural) for (UPackage* Package : Packages) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("changed_packages")); if (bChanged && bStructural) for (UPackage* Package : Packages) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("dirty_packages")); for (UPackage* Package : Packages) if (Package->IsDirty()) Writer->WriteValue(Package->GetName()); Writer->WriteArrayEnd();
	if (Actor) { Writer->WriteObjectStart(TEXT("instance")); WriteState(Writer, World, Actor, false); Writer->WriteObjectEnd(); }
	Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close(); return Json;
}
