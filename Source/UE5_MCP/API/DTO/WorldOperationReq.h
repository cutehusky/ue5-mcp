#pragma once

#include "CoreMinimal.h"
#include "WorldOperationReq.generated.h"

/** Request shared by guarded editor-world lifecycle operations. */
USTRUCT()
struct FWorldOperationReq
{
	GENERATED_BODY()

	/** Unreal package or object path, for example /Game/Maps/TestMap. */
	UPROPERTY()
	FString WorldPath;

	/** Optional existing map used as the source for map creation. */
	UPROPERTY()
	FString TemplatePath;

	/** fail (default), save, or discard when dirty packages exist. */
	UPROPERTY()
	FString DirtyPolicy;

	/** Required when loading the map may discard dirty packages. */
	UPROPERTY()
	bool bConfirm = false;

	/** Persist a newly created map at WorldPath. */
	UPROPERTY()
	bool bSave = true;

	/** Save the active map under a different WorldPath. */
	UPROPERTY()
	bool bSaveAs = false;

	/** Include Asset Registry dependency existence checks during validation. */
	UPROPERTY()
	bool bLoadDependencies = false;

	/** Run UE Map Check when validating the currently active world. */
	UPROPERTY()
	bool bRunMapCheck = false;
};
