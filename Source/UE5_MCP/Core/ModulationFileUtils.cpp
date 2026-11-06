#include "ModulationFileUtils.h"
#include "ModulationUtils.h"
#include "UE5_MCP/API/DTO/ModulationFileReq.h"
#include "Editor.h"
#include "Curves/CurveFloat.h"
#include "Factories/SoundFactory.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Base64.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"
#include "Sound/SoundWave.h"
#include "SoundControlBus.h"
#include "SoundFileIO/SoundFileIO.h"
#include "SoundModulationPatch.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UnrealType.h"
#include "UObject/MetaData.h"
#include <cmath>
#include <stdexcept>

namespace
{
	const TCHAR* SourceKey = TEXT("UE5MCP.FileTransform.v1");
	FRichCurve Bake(const FWaveTableData& Data)
	{
		TArray<float> Values; Values.SetNumUninitialized(Data.GetNumSamples()); for (int32 I = 0; I < Values.Num(); ++I) Values[I] = I;
		WaveTable::FWaveTableSampler::Interpolate(Data, Values, WaveTable::FWaveTableSampler::EInterpolationMode::Linear);
		FRichCurve Curve;
		for (int32 I = 0; I < Values.Num(); ++I) { const auto H = Curve.AddKey(static_cast<float>(I) / Values.Num(), Values[I]); Curve.GetKey(H).InterpMode = RCIM_Linear; }
		const auto H = Curve.AddKey(1.f, Data.GetFinalValue()); Curve.GetKey(H).InterpMode = RCIM_Linear; return Curve;
	}
	FString Pack(FWaveTableTransform& Transform)
	{
		TArray<uint8> Bytes; FMemoryWriter Writer(Bytes); FObjectAndNameAsStringProxyArchive Archive(Writer, false);
		FWaveTableTransform::StaticStruct()->SerializeItem(Archive, &Transform, nullptr); if (Archive.IsError()) throw std::runtime_error("Could not serialize file transform recipe"); return FBase64::Encode(Bytes);
	}
	void Require(UObject* A) { const auto E = ModulationUtils::ValidationErrors(A); if (!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(E, TEXT("; ")))); }
	bool SameData(const FWaveTableData& A, const FWaveTableData& B) { return A.GetBitDepth() == B.GetBitDepth() && A.GetFinalValue() == B.GetFinalValue() && A.GetRawData() == B.GetRawData(); }
	void FiniteData(const FWaveTableData& Data, TArray<FString>& E)
	{
		if (!FMath::IsFinite(Data.GetFinalValue())) E.Add(TEXT("WaveTable final value must be finite"));
		if (Data.GetBitDepth() == EWaveTableBitDepth::IEEE_Float)
		{
			TArrayView<const float> View;
			if (!Data.GetDataView(View)) E.Add(TEXT("WaveTable float data is invalid"));
			else for (float V : View) if (!FMath::IsFinite(V)) { E.Add(TEXT("WaveTable samples must be finite")); break; }
		}
		else if (Data.GetBitDepth() != EWaveTableBitDepth::PCM_16) E.Add(TEXT("Unsupported WaveTable bit depth"));
	}
	void SettingsErrors(const FWaveTableSettings& S, int32 Resolution, TArray<FString>& E)
	{
		if (Resolution < 16 || Resolution > 4096 || !FMath::IsPowerOfTwo(Resolution)) E.Add(TEXT("Resolution must be a power of two between 16 and 4096"));
		if (S.ChannelIndex < 0 || S.ChannelIndex > 31) E.Add(TEXT("ChannelIndex must be in [0,31]"));
		for (float V : {S.Phase, S.Top, S.Tail, S.FadeIn, S.FadeOut}) if (!FMath::IsFinite(V) || V < 0.f || V > 1.f) E.Add(TEXT("Phase/trim/fade ratios must be finite and in [0,1]"));
		if (S.Top + S.Tail >= 1.f) E.Add(TEXT("Combined trim must be less than 1"));
		if (E.IsEmpty() && S.FadeOut > 0.f)
		{
			const int32 Start = WaveTable::RatioToIndex(1.f - S.FadeOut, Resolution);
			const int32 Count = WaveTable::RatioToIndex(S.FadeOut, Resolution) + 1;
			if (Start + Count > Resolution) E.Add(TEXT("FadeOut reaches the UE 5.7 importer buffer boundary; choose a ratio slightly below this value"));
		}
	}
}

bool ModulationFileUtils::HasSource(const FWaveTableTransform& T)
{
	return T.Curve == EWaveTableCurve::File || (T.Curve == EWaveTableCurve::Shared && T.CurveShared && !T.CurveShared->GetOutermost()->GetMetaData().GetValue(T.CurveShared, SourceKey).IsEmpty());
}

bool ModulationFileUtils::ReadSource(const FWaveTableTransform& T, FWaveTableTransform& File)
{
	if (T.Curve == EWaveTableCurve::File) { File = T; return true; }
	if (!HasSource(T)) return false;
	const FString& Packed = T.CurveShared->GetOutermost()->GetMetaData().GetValue(T.CurveShared, SourceKey);
	TArray<uint8> Bytes; if (Packed.Len() > 8 * 1024 * 1024 || !FBase64::Decode(Packed, Bytes)) return false;
	FMemoryReader Reader(Bytes); FObjectAndNameAsStringProxyArchive Archive(Reader, false); Archive.ArMaxSerializeSize = 16 * 1024 * 1024;
	FWaveTableTransform::StaticStruct()->SerializeItem(Archive, &File, nullptr); return !Archive.IsError() && File.Curve == EWaveTableCurve::File;
}

TArray<FString> ModulationFileUtils::Errors(const FWaveTableTransform& T)
{
	TArray<FString> E; if (!HasSource(T)) return E; FWaveTableTransform File;
	if (!ReadSource(T, File)) { E.Add(TEXT("File transform source metadata is invalid")); return E; }
	const auto& S = File.WaveTableSettings; const int32 Count = File.GetTableData().GetNumSamples();
	SettingsErrors(S, Count, E);
	if (S.SourceData.GetNumSamples() < 2 || S.SourceData.GetNumSamples() > 2000000 || S.SourceSampleRate <= 0) E.Add(TEXT("File transform requires valid bounded imported source samples/rate"));
	if (File.GetTableData().IsEmpty()) E.Add(TEXT("File transform has no processed table"));
	if (!S.SourceData.IsEmpty()) FiniteData(S.SourceData, E);
	if (!File.GetTableData().IsEmpty()) FiniteData(File.GetTableData(), E);
	if (E.IsEmpty()) { int32 Offset, Samples; S.GetEditSourceBounds(Offset, Samples); if (Samples < 2) E.Add(TEXT("Trim must retain at least two source samples")); }
	if (E.IsEmpty() && T.Curve == EWaveTableCurve::Shared && !(T.CurveShared->FloatCurve == Bake(File.GetTableData()))) E.Add(TEXT("Baked runtime curve differs from the imported file recipe; reimport to restore it"));
	return E;
}

FString ModulationFileUtils::SourceJson(const FWaveTableTransform& T)
{
	FWaveTableTransform File; if (!ReadSource(T, File)) return TEXT("{\"valid\":false,\"error\":\"Invalid file recipe metadata\"}"); const auto& S = File.WaveTableSettings;
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	J->WriteValue(TEXT("source_file"), S.FilePath.FilePath); J->WriteValue(TEXT("source_exists"), IFileManager::Get().FileExists(*S.FilePath.FilePath));
	J->WriteValue(TEXT("source_sample_rate"), S.SourceSampleRate); J->WriteValue(TEXT("source_samples"), S.SourceData.GetNumSamples()); J->WriteValue(TEXT("channel_index"), S.ChannelIndex);
	J->WriteValue(TEXT("resolution"), File.GetTableData().GetNumSamples()); J->WriteValue(TEXT("bit_depth"), File.GetTableData().GetBitDepth() == EWaveTableBitDepth::PCM_16 ? TEXT("PCM_16") : TEXT("IEEE_Float"));
	J->WriteValue(TEXT("runtime_representation"), TEXT("baked native Shared CurveFloat; complete source recipe cached in editor metadata"));
	J->WriteValue(TEXT("phase"), S.Phase); J->WriteValue(TEXT("top"), S.Top); J->WriteValue(TEXT("tail"), S.Tail); J->WriteValue(TEXT("fade_in"), S.FadeIn); J->WriteValue(TEXT("fade_out"), static_cast<double>(S.FadeOut));
	J->WriteValue(TEXT("normalize"), S.bNormalize); J->WriteValue(TEXT("remove_offset"), S.bRemoveOffset); J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationFileUtils::Import(USoundModulationPatch* Asset, const FModulationFileReq& R)
{
	if (!Asset) throw std::runtime_error("Asset must be a modulation patch");
	if (R.Operation != TEXT("import") && R.Operation != TEXT("reimport")) throw std::runtime_error("Operation must be import or reimport");
	auto* Bus = Cast<USoundControlBus>(StaticLoadObject(USoundControlBus::StaticClass(), nullptr, *R.BusPath)); if (!Bus) throw std::runtime_error("BusPath must identify a Control Bus"); Require(Bus);
	const int32 Index = Asset->PatchSettings.Inputs.IndexOfByPredicate([Bus](const auto& I) { return I.Bus == Bus; });
	FWaveTableTransform Stored;
	const bool ExistingFile = Index != INDEX_NONE && ReadSource(Asset->PatchSettings.Inputs[Index].Transform, Stored);
	if (R.Operation == TEXT("reimport") && !ExistingFile) throw std::runtime_error("Reimport requires an existing file transform for this bus");
	if (Index != INDEX_NONE && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Replacing or reimporting an input transform requires bConfirm=true");
	if (Index == INDEX_NONE && Asset->PatchSettings.Inputs.Num() >= 128) throw std::runtime_error("Patch inputs are limited to 128");
	if (R.bSave && GEditor && GEditor->PlayWorld && !R.bDryRun) throw std::runtime_error("Stop PIE before saving an imported patch transform");
	FSoundControlModulationInput Input; Input.Bus = Bus;
	if (Index != INDEX_NONE) Input.bSampleAndHold = Asset->PatchSettings.Inputs[Index].bSampleAndHold;
	Input.Transform.Curve = EWaveTableCurve::File; auto& S = Input.Transform.WaveTableSettings;
	int32 Resolution = R.Resolution; EWaveTableBitDepth BitDepth = R.BitDepth == TEXT("IEEE_Float") ? EWaveTableBitDepth::IEEE_Float : EWaveTableBitDepth::PCM_16;
	if (R.BitDepth != TEXT("IEEE_Float") && R.BitDepth != TEXT("PCM_16")) throw std::runtime_error("BitDepth must be IEEE_Float or PCM_16");
	if (R.Operation == TEXT("reimport") && R.bUseStoredSettings)
	{
		S = Stored.WaveTableSettings; Resolution = Stored.GetTableData().GetNumSamples(); BitDepth = Stored.GetTableData().GetBitDepth();
	}
	else { S.ChannelIndex = R.ChannelIndex; S.Phase = R.Phase; S.Top = R.Top; S.Tail = R.Tail; S.FadeIn = R.FadeIn; S.FadeOut = R.FadeOut; S.bNormalize = R.bNormalize; S.bRemoveOffset = R.bRemoveOffset; }
	FString Source = R.SourceFilePath.IsEmpty() && ExistingFile ? Stored.WaveTableSettings.FilePath.FilePath : R.SourceFilePath;
	if (Source.IsEmpty() || FPaths::IsRelative(Source)) throw std::runtime_error("SourceFilePath must be an absolute local audio file");
	Source = FPaths::ConvertRelativePathToFull(Source); FPaths::NormalizeFilename(Source); const FString Extension = FPaths::GetExtension(Source).ToLower();
	bool Supported = false; for (const auto& Format : GetDefault<USoundFactory>()->Formats) { FString Ext, Description; if (Format.Split(TEXT(";"), &Ext, &Description) && Ext.Equals(Extension, ESearchCase::IgnoreCase)) Supported = true; }
	const int64 FileSize = IFileManager::Get().FileSize(*Source); if (!Supported || FileSize <= 0 || FileSize > 64 * 1024 * 1024) throw std::runtime_error("Source must be a native Sound Factory format, nonempty and at most 64 MiB");
	TArray<FString> SettingErrors;
	// Native fade-out includes one endpoint too many at exact sample boundaries.
	// Preserve a safe native setting, reporting its effective value to the caller.
	for (int32 Attempt = 0; Attempt < 4 && S.FadeOut > 0.f && S.FadeOut < 1.f && Resolution >= 16 && Resolution <= 4096; ++Attempt)
	{
		if (WaveTable::RatioToIndex(1.f - S.FadeOut, Resolution) + WaveTable::RatioToIndex(S.FadeOut, Resolution) + 1 <= Resolution) break;
		S.FadeOut = std::nextafter(S.FadeOut, 0.f);
	}
	SettingsErrors(S, Resolution, SettingErrors); if (!SettingErrors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(SettingErrors, TEXT("; "))));
	TArray<uint8> FileData, Decoded; if (!FFileHelper::LoadFileToArray(FileData, *Source)) throw std::runtime_error("Could not read audio source"); FileData.Shrink();
	const TArray<uint8>* WaveData = &FileData;
	if (Extension != TEXT("wav")) { if (!Audio::SoundFileUtils::ConvertAudioToWav(FileData, Decoded)) throw std::runtime_error("Native decoder rejected the audio source"); WaveData = &Decoded; }
	FWaveModInfo Info; if (!Info.ReadWaveInfo(WaveData->GetData(), WaveData->Num()) || !Info.IsFormatSupported() || !Info.IsFormatUncompressed() || !Info.pChannels || !Info.pSamplesPerSec || !Info.pBitsPerSample || !*Info.pChannels || *Info.pChannels > 8 || !*Info.pSamplesPerSec || !TArray<int32>{8,16,24,32}.Contains(*Info.pBitsPerSample) || !Info.SampleDataSize) throw std::runtime_error("Decoded audio metadata is invalid or has unsupported sample encoding");
	const int64 Frames = Info.SampleDataSize / (*Info.pChannels * (*Info.pBitsPerSample / 8)); if (Frames < 2 || Frames > 2000000) throw std::runtime_error("Source must contain 2-2000000 frames");
	if (Info.SampleDataSize % (*Info.pChannels * (*Info.pBitsPerSample / 8))) throw std::runtime_error("Source PCM contains an incomplete sample frame");
	if (*Info.pFormatTag == FWaveModInfo::WAVE_INFO_FORMAT_IEEE_FLOAT)
	{
		if (*Info.pBitsPerSample != 32) throw std::runtime_error("IEEE float sources require 32-bit samples");
		for (uint32 I = 0; I + sizeof(float) <= Info.SampleDataSize; I += sizeof(float)) { float Value; FMemory::Memcpy(&Value, Info.SampleDataStart + I, sizeof(Value)); if (!FMath::IsFinite(Value)) throw std::runtime_error("Audio source samples must be finite"); }
	}
	TStrongObjectPtr<USoundFactory> Factory(NewObject<USoundFactory>()); Factory->bAutoCreateCue = false; Factory->SuppressImportDialogs();
	const uint8* Buffer = FileData.GetData();
	TStrongObjectPtr<USoundWave> Wave(Cast<USoundWave>(Factory->FactoryCreateBinary(USoundWave::StaticClass(), GetTransientPackage(), MakeUniqueObjectName(GetTransientPackage(), USoundWave::StaticClass(), TEXT("MCP_WaveTableSource")), RF_Transient, nullptr, *Extension, Buffer, Buffer + FileData.Num(), GWarn)));
	if (!Wave.IsValid()) throw std::runtime_error("Native Sound Factory did not import the source");
	TArray<uint8> PCM; uint32 Rate; uint16 Channels; Wave->GetImportedSoundWaveData(PCM, Rate, Channels);
	if (!Channels || !Rate || PCM.Num() % (Channels * sizeof(int16)) || PCM.Num() / (Channels * sizeof(int16)) != Frames) throw std::runtime_error("Native imported PCM does not match decoded source metadata");
	TArray<int16> Mono; Mono.SetNumUninitialized(static_cast<int32>(Frames)); const int16* Samples = reinterpret_cast<const int16*>(PCM.GetData()); const int32 Channel = S.ChannelIndex % Channels;
	for (int32 I = 0; I < Mono.Num(); ++I) Mono[I] = Samples[I * Channels + Channel];
	S.SourceData = FWaveTableData(TArrayView<const int16>(Mono), static_cast<float>(Mono.Last()) / 32767.f); S.SourceSampleRate = Rate; S.FilePath.FilePath = Source;
	int32 Offset, Editable; S.GetEditSourceBounds(Offset, Editable); if (Editable < 2) throw std::runtime_error("Trim must retain at least two source samples");
	FWaveTableData Processed(BitDepth); Processed.Zero(Resolution); Input.Transform.CreateWaveTable(Processed, false);
	FStructProperty* Field = FindFProperty<FStructProperty>(FWaveTableTransform::StaticStruct(), TEXT("TableData")); if (!Field || Field->Struct != FWaveTableData::StaticStruct()) throw std::runtime_error("Native transform cache property is unavailable");
	Field->Struct->CopyScriptStruct(Field->ContainerPtrToValuePtr<void>(&Input.Transform), &Processed);
	const auto E = Errors(Input.Transform); if (!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(E, TEXT("; "))));
	bool Changed = !ExistingFile;
	if (ExistingFile)
	{
		const auto& OS = Stored.WaveTableSettings;
		Changed = OS.FilePath.FilePath != Source || OS.ChannelIndex != S.ChannelIndex || OS.SourceSampleRate != S.SourceSampleRate || OS.Phase != S.Phase || OS.Top != S.Top || OS.Tail != S.Tail || OS.FadeIn != S.FadeIn || OS.FadeOut != S.FadeOut || OS.bNormalize != S.bNormalize || OS.bRemoveOffset != S.bRemoveOffset || !SameData(OS.SourceData, S.SourceData) || !SameData(Stored.GetTableData(), Processed);
		const auto& Current = Asset->PatchSettings.Inputs[Index].Transform;
		Changed |= Current.Curve != EWaveTableCurve::Shared || !Current.CurveShared || Current.CurveShared->GetOuter() != Asset || !(Current.CurveShared->FloatCurve == Bake(Processed));
	}
	auto* Preview = CastChecked<USoundModulationPatch>(ModulationUtils::TransientCopy(Asset)); Preview->PatchSettings.Inputs = Asset->PatchSettings.Inputs;
	if (Index == INDEX_NONE) Preview->PatchSettings.Inputs.Add(Input); else Preview->PatchSettings.Inputs[Index] = Input; Require(Preview);
	if (Changed && !R.bDryRun)
	{
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP", "ImportModulationFile", "Import modulation file transform")); Asset->Modify();
		// Each changed recipe owns a new curve. Undo restores the previous input
		// reference together with its immutable editor recipe metadata.
		UCurveFloat* Curve = NewObject<UCurveFloat>(Asset, MakeUniqueObjectName(Asset, UCurveFloat::StaticClass(), TEXT("ImportedFileCurve")), RF_Public | RF_Transactional);
		Curve->Modify(); Curve->FloatCurve = Bake(Processed); const FString Packed = Pack(Input.Transform);
		Curve->GetOutermost()->GetMetaData().SetValue(Curve, SourceKey, *Packed);
		FSoundControlModulationInput RuntimeInput; RuntimeInput.Bus = Bus; RuntimeInput.bSampleAndHold = Input.bSampleAndHold; RuntimeInput.Transform.Curve = EWaveTableCurve::Shared; RuntimeInput.Transform.CurveShared = Curve;
		const int32 RuntimeIndex = Index == INDEX_NONE ? Preview->PatchSettings.Inputs.Num() - 1 : Index; Preview->PatchSettings.Inputs[RuntimeIndex] = RuntimeInput;
		Asset->PatchSettings.Inputs = Preview->PatchSettings.Inputs; FPropertyChangedEvent Event(FindFProperty<FProperty>(Asset->GetClass(), TEXT("PatchSettings")), EPropertyChangeType::ValueSet); Asset->PostEditChangeProperty(Event); Asset->MarkPackageDirty();
		if (R.bSave) { auto* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr; if (!Subsystem || !Subsystem->SaveAsset(Asset->GetPathName(), true)) throw std::runtime_error("File transform imported but saving failed"); }
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), Asset->GetPathName()); J->WriteValue(TEXT("bus_path"), Bus->GetPathName()); J->WriteValue(TEXT("source_file"), Source);
	J->WriteValue(TEXT("source_channels"), Channels); J->WriteValue(TEXT("effective_channel_index"), Channel); J->WriteValue(TEXT("source_samples"), Frames); J->WriteValue(TEXT("resolution"), Resolution); J->WriteValue(TEXT("effective_fade_out"), static_cast<double>(S.FadeOut));
	J->WriteValue(TEXT("would_change"), Changed); J->WriteValue(TEXT("changed"), Changed && !R.bDryRun); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("saved"), Changed && !R.bDryRun && R.bSave); J->WriteObjectEnd(); J->Close(); return Json;
}
