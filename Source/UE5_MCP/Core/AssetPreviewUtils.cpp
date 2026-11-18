#include "AssetPreviewUtils.h"
#include "UE5_MCP/API/DTO/AssetPreviewReq.h"

#include "Editor.h"
#include "EditorFramework/AssetImportData.h"
#include "Engine/Texture2D.h"
#include "FileHelpers.h"
#include "HAL/FileManager.h"
#include "ImageCore.h"
#include "ImageUtils.h"
#include "Misc/ObjectThumbnail.h"
#include "Misc/Paths.h"
#include "ObjectTools.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonWriter.h"
#include "ThumbnailRendering/ThumbnailManager.h"
#include "UnrealEdGlobals.h"
#include "Editor/UnrealEdEngine.h"

#include <stdexcept>

namespace
{
	constexpr int32 MaxThumbnailSize = 2048;
	constexpr int32 MaxTextureSourceSize = 16384;

	using FJsonWriterRef = TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>>;

	void RequireEditorIdle()
	{
		if (!IsInGameThread() || !GEditor)
		{
			throw std::runtime_error("Must run on the editor game thread");
		}
		if (GEditor->PlayWorld)
		{
			throw std::runtime_error("Stop the Play-In-Editor session first");
		}
	}

	/** Accepts /Game/Dir/Name or /Game/Dir/Name.Name and loads the asset. */
	UObject* LoadAssetObject(const FString& InPath)
	{
		FString Path = InPath.TrimStartAndEnd();
		if (Path.IsEmpty() || Path.Len() > 1024 || !Path.StartsWith(TEXT("/")))
		{
			throw std::runtime_error("AssetPath must be a package path such as /Game/Folder/AssetName");
		}
		if (!Path.Contains(TEXT(".")))
		{
			Path += TEXT(".") + FPackageName::GetShortName(Path);
		}
		UObject* Object = StaticLoadObject(UObject::StaticClass(), nullptr, *Path, nullptr, LOAD_NoWarn);
		if (!IsValid(Object) || !Object->IsAsset())
		{
			throw std::runtime_error("Asset not found or not loadable");
		}
		return Object;
	}

	/** Resolve the output file and reject anything that is not an image extension FImageUtils can write. */
	FString ResolveThumbnailPath(const FAssetPreviewReq& R, const UObject* Asset)
	{
		const FString BaseDir = FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UE5_MCP/Thumbnails")));
		FString Out = R.OutputPath.TrimStartAndEnd();
		if (Out.IsEmpty())
		{
			Out = Asset->GetName() + TEXT(".png");
		}
		if (FPaths::IsRelative(Out))
		{
			Out = FPaths::Combine(BaseDir, Out);
		}
		Out = FPaths::ConvertRelativePathToFull(Out);
		FPaths::NormalizeFilename(Out);

		const FString Ext = FPaths::GetExtension(Out).ToLower();
		if (Ext.IsEmpty())
		{
			Out += TEXT(".png");
		}
		else if (Ext != TEXT("png") && Ext != TEXT("jpg") && Ext != TEXT("jpeg") && Ext != TEXT("bmp") && Ext != TEXT("tga") && Ext != TEXT("exr"))
		{
			throw std::runtime_error("OutputPath extension must be png, jpg, bmp, tga or exr");
		}
		return Out;
	}

	FImageCore::EResizeImageFilter ParseFilter(const FString& InName)
	{
		const FString Name = InName.TrimStartAndEnd().ToLower();
		if (Name.IsEmpty() || Name == TEXT("default")) return FImageCore::EResizeImageFilter::Default;
		if (Name == TEXT("point") || Name == TEXT("pointsample")) return FImageCore::EResizeImageFilter::PointSample;
		if (Name == TEXT("box")) return FImageCore::EResizeImageFilter::Box;
		if (Name == TEXT("triangle") || Name == TEXT("bilinear")) return FImageCore::EResizeImageFilter::Triangle;
		if (Name == TEXT("gaussian") || Name == TEXT("cubicgaussian")) return FImageCore::EResizeImageFilter::CubicGaussian;
		if (Name == TEXT("catmullrom") || Name == TEXT("cubicsharp")) return FImageCore::EResizeImageFilter::CubicSharp;
		if (Name == TEXT("mitchell") || Name == TEXT("cubicmitchell")) return FImageCore::EResizeImageFilter::CubicMitchell;
		if (Name == TEXT("adaptivesharp")) return FImageCore::EResizeImageFilter::AdaptiveSharp;
		if (Name == TEXT("adaptivesmooth")) return FImageCore::EResizeImageFilter::AdaptiveSmooth;
		if (Name == TEXT("lanczos4")) return FImageCore::EResizeImageFilter::Lanczos4;
		if (Name == TEXT("lanczos5")) return FImageCore::EResizeImageFilter::Lanczos5;
		throw std::runtime_error("Unknown Filter; use default, point, box, bilinear, gaussian, catmullrom, mitchell, adaptivesharp, adaptivesmooth, lanczos4 or lanczos5");
	}
}

FString AssetPreviewUtils::RenderAssetThumbnail(const FAssetPreviewReq& R)
{
	RequireEditorIdle();
	if (R.Width < 1 || R.Height < 1 || R.Width > MaxThumbnailSize || R.Height > MaxThumbnailSize)
	{
		throw std::runtime_error("Width and Height must be 1..2048");
	}
	if (!GUnrealEd || !GUnrealEd->GetThumbnailManager())
	{
		throw std::runtime_error("Thumbnail manager unavailable");
	}

	UObject* Asset = LoadAssetObject(R.AssetPath);
	FThumbnailRenderingInfo* Info = GUnrealEd->GetThumbnailManager()->GetRenderingInfo(Asset);
	if (!Info || !Info->Renderer)
	{
		throw std::runtime_error("This asset type has no thumbnail renderer");
	}

	const FString OutFile = ResolveThumbnailPath(R, Asset);
	if (!R.bOverwrite && IFileManager::Get().FileExists(*OutFile))
	{
		throw std::runtime_error("Output file already exists; pass overwrite=true to replace it");
	}

	FObjectThumbnail Thumb;
	ThumbnailTools::RenderThumbnail(Asset, uint32(R.Width), uint32(R.Height), ThumbnailTools::EThumbnailTextureFlushMode::AlwaysFlush, nullptr, &Thumb);

	const int32 W = Thumb.GetImageWidth();
	const int32 H = Thumb.GetImageHeight();
	TArray<uint8>& Pixels = Thumb.AccessImageData();
	if (W < 1 || H < 1 || Pixels.Num() != W * H * int32(sizeof(FColor)))
	{
		throw std::runtime_error("Thumbnail render produced no pixels (renderer unavailable or headless editor)");
	}

	// Render target alpha is not meaningful for thumbnails; make the image opaque.
	FColor* Colors = reinterpret_cast<FColor*>(Pixels.GetData());
	for (int32 I = 0; I < W * H; ++I)
	{
		Colors[I].A = 255;
	}

	if (!IFileManager::Get().MakeDirectory(*FPaths::GetPath(OutFile), true))
	{
		throw std::runtime_error("Could not create output directory");
	}
	const FImageView View(Colors, W, H, EGammaSpace::sRGB);
	if (!FImageUtils::SaveImageByExtension(*OutFile, View))
	{
		throw std::runtime_error("Image encode or write failed");
	}

	FString Json;
	FJsonWriterRef J = TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Json);
	J->WriteObjectStart();
	J->WriteValue(TEXT("asset_path"), Asset->GetPathName());
	J->WriteValue(TEXT("asset_class"), Asset->GetClass()->GetName());
	J->WriteValue(TEXT("renderer"), Info->Renderer->GetClass()->GetName());
	J->WriteValue(TEXT("output_path"), OutFile);
	J->WriteValue(TEXT("requested_width"), R.Width);
	J->WriteValue(TEXT("requested_height"), R.Height);
	J->WriteValue(TEXT("width"), W);
	J->WriteValue(TEXT("height"), H);
	J->WriteValue(TEXT("file_bytes"), IFileManager::Get().FileSize(*OutFile));
	J->WriteValue(TEXT("note"), TEXT("Rendered with the Content Browser thumbnail renderer (same camera/lighting as the asset tile). Textures and materials may render smaller than requested to keep their aspect ratio."));
	J->WriteObjectEnd();
	J->Close();
	return Json;
}

FString AssetPreviewUtils::ResizeTextureSource(const FAssetPreviewReq& R)
{
	RequireEditorIdle();

	UObject* Object = LoadAssetObject(R.AssetPath);
	UTexture2D* Tex = Cast<UTexture2D>(Object);
	if (!Tex || Tex->GetClass() != UTexture2D::StaticClass())
	{
		throw std::runtime_error("Asset must be a plain Texture2D (not a render target, cube, array, volume or virtual-texture subclass)");
	}
	FTextureSource& Source = Tex->Source;
	if (!Source.IsValid())
	{
		throw std::runtime_error("Texture has no editable source data");
	}
	if (Source.GetNumBlocks() != 1 || Source.GetNumLayers() != 1 || Source.GetNumSlices() != 1)
	{
		throw std::runtime_error("UDIM, multi-layer or multi-slice source is not supported");
	}

	const int32 OldW = Source.GetSizeX();
	const int32 OldH = Source.GetSizeY();
	const int32 OldMips = Source.GetNumMips();
	if (R.Width < 1 || R.Width > MaxTextureSourceSize || R.Height < 0 || R.Height > MaxTextureSourceSize)
	{
		throw std::runtime_error("Width must be 1..16384 and Height 0..16384 (0 keeps aspect ratio)");
	}
	const int32 NewW = R.Width;
	const int32 NewH = R.Height > 0 ? R.Height : FMath::Max(1, FMath::RoundToInt(double(OldH) * double(NewW) / double(OldW)));
	if (NewH > MaxTextureSourceSize)
	{
		throw std::runtime_error("Computed height exceeds 16384");
	}

	FImageCore::EResizeImageFilter Filter = ParseFilter(R.Filter);
	if (Tex->AddressX == TA_Wrap) Filter |= FImageCore::EResizeImageFilter::Flag_WrapX;
	if (Tex->AddressY == TA_Wrap) Filter |= FImageCore::EResizeImageFilter::Flag_WrapY;

	const bool bPow2 = FMath::IsPowerOfTwo(NewW) && FMath::IsPowerOfTwo(NewH);
	const bool bSameSize = NewW == OldW && NewH == OldH;
	TArray<FString> Warnings;
	if (!bPow2 && Tex->PowerOfTwoMode == ETexturePowerOfTwoSetting::None)
	{
		Warnings.Add(TEXT("New size is not a power of two: the texture will not get mips or stream."));
	}
	if (OldMips > 1)
	{
		Warnings.Add(TEXT("Authored source mips will be discarded; mips are regenerated from the new top level."));
	}
	if (Tex->MipGenSettings == TMGS_LeaveExistingMips)
	{
		Warnings.Add(TEXT("MipGenSettings is LeaveExistingMips; with a single source mip the texture will have no mips."));
	}
	if (Tex->MaxTextureSize > 0 || Tex->LODBias != 0)
	{
		Warnings.Add(TEXT("MaxTextureSize/LODBias still apply on top of the new source size."));
	}
	const FString SourceFile = Tex->AssetImportData ? Tex->AssetImportData->GetFirstFilename() : FString();
	if (!SourceFile.IsEmpty())
	{
		Warnings.Add(TEXT("The asset still points at its original import file; a Reimport would restore the old size."));
	}

	const bool bApply = !R.bDryRun && !bSameSize;
	if (!R.bDryRun && !R.bConfirm)
	{
		throw std::runtime_error("Pass confirm=true (with dry_run=false) to rewrite the texture source");
	}

	int64 OldBytes = Source.CalcMipSize(0);
	int64 NewBytes = OldBytes;
	bool bSaved = false;
	FString RawFormat;

	{
		FImageInfo Info;
		if (Source.GetMipImageInfo(Info, 0, 0, 0))
		{
			// The engine's resampler asserts on legacy Pow22 gamma output (ImageCore.cpp), which would crash the editor: refuse it here.
			if (Info.GammaSpace == EGammaSpace::Pow22)
			{
				throw std::runtime_error("Texture source uses legacy Pow22 gamma (Use Legacy Gamma); the engine resampler can't write it, so it is left unchanged");
			}
			RawFormat = ERawImageFormat::GetName(Info.Format);
			NewBytes = int64(NewW) * NewH * ERawImageFormat::GetBytesPerPixel(Info.Format);
		}
	}

	if (bApply)
	{
		FImage SrcImage;
		if (!Source.GetMipImage(SrcImage, 0))
		{
			throw std::runtime_error("Could not decode texture source mip 0");
		}

		if (SrcImage.GammaSpace == EGammaSpace::Pow22)
		{
			throw std::runtime_error("Texture source uses legacy Pow22 gamma; left unchanged");
		}
		FImage DstImage;
		FImageCore::ResizeImageAllocDest(SrcImage, DstImage, NewW, NewH, SrcImage.Format, SrcImage.GammaSpace, Filter);
		if (DstImage.SizeX != NewW || DstImage.SizeY != NewH || DstImage.RawData.IsEmpty())
		{
			throw std::runtime_error("Resize produced an invalid image");
		}

		Tex->PreEditChange(nullptr);
		Source.Init(DstImage);
		Tex->PostEditChange();
		Tex->MarkPackageDirty();

		if (Source.GetSizeX() != NewW || Source.GetSizeY() != NewH)
		{
			throw std::runtime_error("Source readback size mismatch after resize");
		}
		NewBytes = Source.CalcMipSize(0);

		if (R.bSave)
		{
			bSaved = UEditorLoadingAndSavingUtils::SavePackages({ Tex->GetPackage() }, false);
			if (!bSaved)
			{
				throw std::runtime_error("Resize applied in memory but saving the package failed");
			}
		}
	}

	FString Json;
	FJsonWriterRef J = TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Json);
	J->WriteObjectStart();
	J->WriteValue(TEXT("asset_path"), Tex->GetPathName());
	J->WriteValue(TEXT("dry_run"), R.bDryRun);
	J->WriteValue(TEXT("applied"), bApply);
	J->WriteValue(TEXT("saved"), bSaved);
	J->WriteValue(TEXT("package_dirty"), Tex->GetPackage()->IsDirty());
	J->WriteValue(TEXT("old_width"), OldW);
	J->WriteValue(TEXT("old_height"), OldH);
	J->WriteValue(TEXT("old_source_mips"), OldMips);
	J->WriteValue(TEXT("new_width"), NewW);
	J->WriteValue(TEXT("new_height"), NewH);
	J->WriteValue(TEXT("raw_format"), RawFormat);
	J->WriteValue(TEXT("old_source_bytes"), OldBytes);
	J->WriteValue(TEXT("new_source_bytes"), NewBytes);
	J->WriteValue(TEXT("filter"), R.Filter.IsEmpty() ? FString(TEXT("default")) : R.Filter);
	J->WriteValue(TEXT("power_of_two"), bPow2);
	J->WriteValue(TEXT("same_size_noop"), bSameSize);
	J->WriteValue(TEXT("import_source_file"), SourceFile);
	J->WriteArrayStart(TEXT("warnings"));
	for (const FString& W : Warnings) J->WriteValue(W);
	J->WriteArrayEnd();
	J->WriteValue(TEXT("note"), TEXT("Rewrites the authored source pixels stored in the .uasset (not undoable). Use save=true or save_asset to write the smaller file to disk."));
	J->WriteObjectEnd();
	J->Close();
	return Json;
}
