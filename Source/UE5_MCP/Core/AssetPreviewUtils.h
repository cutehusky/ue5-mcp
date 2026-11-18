#pragma once
#include "CoreMinimal.h"

struct FAssetPreviewReq;

namespace AssetPreviewUtils
{
	/** Render an asset with the Content Browser thumbnail renderer and write it to an image file (png/jpg/bmp/exr/tga). */
	FString RenderAssetThumbnail(const FAssetPreviewReq& R);

	/** Resample a Texture2D's authored source pixels to a new size, rebuild it and optionally save the .uasset. */
	FString ResizeTextureSource(const FAssetPreviewReq& R);
}
