#pragma once

#include "CoreMinimal.h"

class UTexture;
struct FTextureImportReq;

namespace TextureImportUtils
{
	FString SourceJson(const UTexture* Texture);
	FString Import(const FTextureImportReq& Request);
	FString Reimport(UTexture* Texture, const FTextureImportReq& Request);
}
