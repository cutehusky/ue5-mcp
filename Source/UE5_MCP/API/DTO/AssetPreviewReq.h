#pragma once
#include "CoreMinimal.h"
#include "AssetPreviewReq.generated.h"

/** Request for /assets/thumbnail/render and /textures/source/resize. */
USTRUCT()
struct FAssetPreviewReq
{
	GENERATED_BODY()

	/** Asset object path, e.g. /Game/Meshes/SM_Rock or /Game/Meshes/SM_Rock.SM_Rock. */
	UPROPERTY() FString AssetPath;

	/** Thumbnail: output file. Relative paths resolve under Saved/UE5_MCP/Thumbnails. Empty uses <AssetName>.png. */
	UPROPERTY() FString OutputPath;

	/** Thumbnail: image size. Resize: new source size (Height 0 keeps aspect ratio). */
	UPROPERTY() int32 Width = 512;
	UPROPERTY() int32 Height = 512;

	/** Resize: when > 0, shrink so the largest side of every block (UDIM tile) is at most MaxSize; Width/Height are ignored and smaller textures are left unchanged. */
	UPROPERTY() int32 MaxSize = 0;

	/** Thumbnail: replace an existing output file. */
	UPROPERTY() bool bOverwrite = false;

	/** Resize: filter name (default, box, triangle, bilinear, catmullrom, mitchell, adaptivesharp, adaptivesmooth). */
	UPROPERTY() FString Filter;

	/** Resize: report only, change nothing. */
	UPROPERTY() bool bDryRun = true;

	/** Resize: required to actually rewrite the source pixels. */
	UPROPERTY() bool bConfirm = false;

	/** Resize: save the package to disk after the edit. */
	UPROPERTY() bool bSave = false;
};
