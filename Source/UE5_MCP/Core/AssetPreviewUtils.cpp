#include "AssetPreviewUtils.h"
#include "UE5_MCP/API/DTO/AssetPreviewReq.h"

#include "Editor.h"
#include "EditorFramework/AssetImportData.h"
#include "Engine/Texture2D.h"
#include "FileHelpers.h"
#include "HAL/FileManager.h"
#include "ImageCore.h"
#include "ImageCoreUtils.h"
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
	if (Source.GetNumSlices() != 1)
	{
		throw std::runtime_error("Multi-slice source is not supported");
	}

	// UDIM textures have several blocks (tiles); multi-layer textures have several layers per block.
	// Every block/layer is resampled by the same scale and the source is rebuilt with InitBlocked.
	const int32 NumBlocks = Source.GetNumBlocks();
	const int32 NumLayers = Source.GetNumLayers();
	TArray<FTextureSourceBlock> OldBlocks;
	OldBlocks.SetNum(NumBlocks);
	int32 Largest = 0;
	for (int32 B = 0; B < NumBlocks; ++B)
	{
		Source.GetBlock(B, OldBlocks[B]);
		if (OldBlocks[B].NumSlices != 1)
		{
			throw std::runtime_error("Multi-slice source block is not supported");
		}
		Largest = FMath::Max(Largest, FMath::Max(OldBlocks[B].SizeX, OldBlocks[B].SizeY));
	}
	const int32 OldW = OldBlocks[0].SizeX;
	const int32 OldH = OldBlocks[0].SizeY;
	int32 OldMips = 0;
	for (const FTextureSourceBlock& Block : OldBlocks)
	{
		OldMips = FMath::Max(OldMips, Block.NumMips);
	}
	if (OldW < 1 || OldH < 1 || Largest < 1)
	{
		throw std::runtime_error("Texture source has an empty block");
	}

	// MaxSize > 0: shrink so the largest side of any block is at most MaxSize (never enlarges; Width/Height ignored).
	// Otherwise Width/Height give block 0's new size and other blocks keep their size ratio to block 0.
	double ScaleX = 1.0;
	double ScaleY = 1.0;
	int32 NewW = OldW;
	int32 NewH = OldH;
	if (R.MaxSize > 0)
	{
		if (R.MaxSize > MaxTextureSourceSize)
		{
			throw std::runtime_error("MaxSize must be 1..16384");
		}
		ScaleX = ScaleY = FMath::Min(1.0, double(R.MaxSize) / double(Largest));
	}
	else
	{
		if (R.Width < 1 || R.Width > MaxTextureSourceSize || R.Height < 0 || R.Height > MaxTextureSourceSize)
		{
			throw std::runtime_error("Width must be 1..16384 and Height 0..16384 (0 keeps aspect ratio), or pass MaxSize");
		}
		NewW = R.Width;
		NewH = R.Height > 0 ? R.Height : FMath::Max(1, FMath::RoundToInt(double(OldH) * double(NewW) / double(OldW)));
		ScaleX = double(NewW) / double(OldW);
		ScaleY = double(NewH) / double(OldH);
	}

	TArray<FTextureSourceBlock> NewBlocks = OldBlocks;
	bool bSameSize = true;
	bool bPow2 = true;
	for (int32 B = 0; B < NumBlocks; ++B)
	{
		FTextureSourceBlock& NB = NewBlocks[B];
		if (B == 0 && R.MaxSize <= 0)
		{
			NB.SizeX = NewW;
			NB.SizeY = NewH;
		}
		else
		{
			NB.SizeX = FMath::Max(1, FMath::RoundToInt(double(OldBlocks[B].SizeX) * ScaleX));
			NB.SizeY = FMath::Max(1, FMath::RoundToInt(double(OldBlocks[B].SizeY) * ScaleY));
		}
		if (NB.SizeX > MaxTextureSourceSize || NB.SizeY > MaxTextureSourceSize)
		{
			throw std::runtime_error("Computed size exceeds 16384");
		}
		NB.NumMips = 1;
		bSameSize &= NB.SizeX == OldBlocks[B].SizeX && NB.SizeY == OldBlocks[B].SizeY;
		bPow2 &= FMath::IsPowerOfTwo(NB.SizeX) && FMath::IsPowerOfTwo(NB.SizeY);
	}
	NewW = NewBlocks[0].SizeX;
	NewH = NewBlocks[0].SizeY;

	FImageCore::EResizeImageFilter Filter = ParseFilter(R.Filter);
	if (Tex->AddressX == TA_Wrap) Filter |= FImageCore::EResizeImageFilter::Flag_WrapX;
	if (Tex->AddressY == TA_Wrap) Filter |= FImageCore::EResizeImageFilter::Flag_WrapY;

	// Legacy Pow22 gamma: the resampler can read Pow22 but can't write it, so those layers are re-encoded
	// to sRGB (the engine's own rule: "Pow22 Source should encode to sRGB Dest") and Use Legacy Gamma is
	// turned off, which leaves the built texture looking the same (platform data is always sRGB anyway).
	bool bLegacyGamma = false;
	FString RawFormat;
	int64 OldBytes = 0;
	int64 NewBytes = 0;
	for (int32 L = 0; L < NumLayers; ++L)
	{
		FImageInfo Info;
		if (Source.GetMipImageInfo(Info, 0, L, 0))
		{
			bLegacyGamma |= Info.GammaSpace == EGammaSpace::Pow22;
			if (L == 0)
			{
				RawFormat = ERawImageFormat::GetName(Info.Format);
			}
		}
		for (int32 B = 0; B < NumBlocks; ++B)
		{
			OldBytes += Source.CalcMipSize(B, L, 0);
			NewBytes += int64(NewBlocks[B].SizeX) * NewBlocks[B].SizeY * Source.GetBytesPerPixel(L);
		}
	}

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
	if (bLegacyGamma && !bSameSize)
	{
		Warnings.Add(TEXT("Source uses legacy Pow22 gamma: it is re-encoded to sRGB and 'sRGB Use Legacy Gamma' is turned off, so it renders the same."));
	}
	if (NumBlocks > 1)
	{
		Warnings.Add(TEXT("UDIM source: every tile is scaled by the same factor."));
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

	bool bSaved = false;
	if (bApply)
	{
		// Resample every block/layer first; nothing is changed if any of them fails.
		TArray<TArray64<uint8>> BlockData;
		BlockData.SetNum(NumBlocks);
		TArray<ETextureSourceFormat> NewFormats;
		NewFormats.SetNum(NumLayers);
		FImage SingleImage;
		for (int32 B = 0; B < NumBlocks; ++B)
		{
			for (int32 L = 0; L < NumLayers; ++L)
			{
				FImage SrcImage;
				if (!Source.GetMipImage(SrcImage, B, L, 0))
				{
					throw std::runtime_error("Could not decode a texture source block/layer");
				}
				const EGammaSpace DstGamma = SrcImage.GammaSpace == EGammaSpace::Pow22 ? EGammaSpace::sRGB : SrcImage.GammaSpace;
				FImage DstImage;
				FImageCore::ResizeImageAllocDest(SrcImage, DstImage, NewBlocks[B].SizeX, NewBlocks[B].SizeY, SrcImage.Format, DstGamma, Filter);
				if (DstImage.SizeX != NewBlocks[B].SizeX || DstImage.SizeY != NewBlocks[B].SizeY || DstImage.RawData.IsEmpty())
				{
					throw std::runtime_error("Resize produced an invalid image");
				}
				const ETextureSourceFormat Fmt = FImageCoreUtils::ConvertToTextureSourceFormat(DstImage.Format);
				if (Fmt == TSF_Invalid || (B > 0 && Fmt != NewFormats[L]))
				{
					throw std::runtime_error("Resized layer format can't be stored as texture source");
				}
				NewFormats[L] = Fmt;
				if (NumBlocks == 1 && NumLayers == 1)
				{
					SingleImage = MoveTemp(DstImage);
				}
				else
				{
					BlockData[B].Append(DstImage.RawData);
				}
			}
		}

		Tex->PreEditChange(nullptr);
		if (NumBlocks == 1 && NumLayers == 1)
		{
			Source.Init(SingleImage);
		}
		else
		{
			TArray<const uint8*> DataPerBlock;
			for (const TArray64<uint8>& Data : BlockData)
			{
				DataPerBlock.Add(Data.GetData());
			}
			Source.InitBlocked(NewFormats.GetData(), NewBlocks.GetData(), NumLayers, NumBlocks, DataPerBlock.GetData());
		}
		if (bLegacyGamma)
		{
			Tex->bUseLegacyGamma = false;
		}
		Tex->PostEditChange();
		Tex->MarkPackageDirty();

		if (Source.GetNumBlocks() != NumBlocks || Source.GetNumLayers() != NumLayers)
		{
			throw std::runtime_error("Source readback block/layer count mismatch after resize");
		}
		NewBytes = 0;
		for (int32 B = 0; B < NumBlocks; ++B)
		{
			FTextureSourceBlock Check;
			Source.GetBlock(B, Check);
			if (Check.SizeX != NewBlocks[B].SizeX || Check.SizeY != NewBlocks[B].SizeY)
			{
				throw std::runtime_error("Source readback size mismatch after resize");
			}
			for (int32 L = 0; L < NumLayers; ++L)
			{
				NewBytes += Source.CalcMipSize(B, L, 0);
			}
		}

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
	J->WriteValue(TEXT("old_largest_side"), Largest);
	J->WriteValue(TEXT("old_source_mips"), OldMips);
	J->WriteValue(TEXT("new_width"), NewW);
	J->WriteValue(TEXT("new_height"), NewH);
	J->WriteValue(TEXT("max_size"), R.MaxSize);
	J->WriteValue(TEXT("num_blocks"), NumBlocks);
	J->WriteValue(TEXT("num_layers"), NumLayers);
	J->WriteValue(TEXT("legacy_gamma"), bLegacyGamma);
	J->WriteValue(TEXT("raw_format"), RawFormat);
	J->WriteValue(TEXT("old_source_bytes"), OldBytes);
	J->WriteValue(TEXT("new_source_bytes"), NewBytes);
	J->WriteValue(TEXT("filter"), R.Filter.IsEmpty() ? FString(TEXT("default")) : R.Filter);
	J->WriteValue(TEXT("power_of_two"), bPow2);
	J->WriteValue(TEXT("same_size_noop"), bSameSize);
	J->WriteValue(TEXT("import_source_file"), SourceFile);
	if (NumBlocks > 1)
	{
		J->WriteArrayStart(TEXT("blocks"));
		for (int32 B = 0; B < FMath::Min(NumBlocks, 64); ++B)
		{
			J->WriteObjectStart();
			J->WriteValue(TEXT("block_x"), OldBlocks[B].BlockX);
			J->WriteValue(TEXT("block_y"), OldBlocks[B].BlockY);
			J->WriteValue(TEXT("old_width"), OldBlocks[B].SizeX);
			J->WriteValue(TEXT("old_height"), OldBlocks[B].SizeY);
			J->WriteValue(TEXT("new_width"), NewBlocks[B].SizeX);
			J->WriteValue(TEXT("new_height"), NewBlocks[B].SizeY);
			J->WriteObjectEnd();
		}
		J->WriteArrayEnd();
	}
	J->WriteArrayStart(TEXT("warnings"));
	for (const FString& W : Warnings) J->WriteValue(W);
	J->WriteArrayEnd();
	J->WriteValue(TEXT("note"), TEXT("Rewrites the authored source pixels stored in the .uasset (not undoable). Use save=true or save_asset to write the smaller file to disk."));
	J->WriteObjectEnd();
	J->Close();
	return Json;
}
