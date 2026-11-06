#include "ModulationAuthoringUtils.h"
#include "ModulationUtils.h"
#include "ModulationFileUtils.h"
#include "UE5_MCP/API/DTO/ModulationReq.h"
#include "UE5_MCP/API/DTO/ModulationAuthoringReq.h"
#include "Curves/CurveFloat.h"
#include "Editor.h"
#include "Generators/SoundModulationLFO.h"
#include "Generators/SoundModulationADEnvelope.h"
#include "Generators/SoundModulationEnvelopeFollower.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Sound/AudioBus.h"
#include "SoundControlBus.h"
#include "SoundModulationPatch.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
	FString Path(const UObject* A) { return A ? A->GetPathName() : FString(); }
	template<typename T> T* Reference(const FString& P)
	{
		T* A = P.IsEmpty() ? nullptr : Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, *P));
		if (!A) throw std::runtime_error("Reference has an incompatible asset class"); return A;
	}
	void Require(UObject* A)
	{
		const auto E = ModulationUtils::ValidationErrors(A);
		if (!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(E, TEXT("; "))));
	}
	FString Result(UObject* A, bool Changed, bool Dry, bool Save)
	{
		FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
		J->WriteValue(TEXT("asset_path"), Path(A)); J->WriteValue(TEXT("would_change"), Changed);
		J->WriteValue(TEXT("changed"), Changed && !Dry); J->WriteValue(TEXT("dry_run"), Dry);
		J->WriteValue(TEXT("saved"), Changed && !Dry && Save); J->WriteValue(TEXT("dirty"), A->GetOutermost()->IsDirty());
		J->WriteObjectEnd(); J->Close(); return Json;
	}
	void Commit(UObject* A, UObject* Preview, FName Field, bool Changed, bool Dry, bool Save)
	{
		if (!Changed || Dry) return;
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP", "ModulationAuthoring", "Edit modulation asset")); A->Modify();
		FProperty* F = FindFProperty<FProperty>(A->GetClass(), Field);
		F->CopyCompleteValue_InContainer(A, Preview); FPropertyChangedEvent Event(F, EPropertyChangeType::ValueSet);
		A->PostEditChangeProperty(Event); A->MarkPackageDirty();
		if (Save) { auto* S = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr; if (!S || !S->SaveAsset(Path(A), true)) throw std::runtime_error("Modulation asset changed but saving failed"); }
	}
	struct FParams { UScriptStruct* Type = nullptr; void* Data = nullptr; TMap<FString, FVector2f> Bounds; TArray<FString> Flags; };
	FParams Params(UObject* A)
	{
		FParams P;
		if (auto* L = Cast<USoundModulationGeneratorLFO>(A))
		{
			P.Type = FSoundModulationLFOParams::StaticStruct(); P.Data = &L->Params;
			P.Bounds = {{TEXT("Amplitude"), {0,1}}, {TEXT("Frequency"), {0,20}}, {TEXT("Offset"), {0,1}}, {TEXT("Phase"), {0,1}}, {TEXT("Width"), {0,1}}, {TEXT("ExponentialFactor"), {.000001f,100}}};
			P.Flags = {TEXT("bBypass"), TEXT("bLooping")};
		}
		else if (auto* E = Cast<USoundModulationGeneratorADEnvelope>(A))
		{
			P.Type = FSoundModulationADEnvelopeParams::StaticStruct(); P.Data = &E->Params;
			P.Bounds = {{TEXT("AttackTime"), {0,86400}}, {TEXT("DecayTime"), {0,86400}}, {TEXT("AttackCurve"), {0,100}}, {TEXT("DecayCurve"), {0,100}}};
			P.Flags = {TEXT("bBypass"), TEXT("bLooping")};
		}
		else if (auto* F = Cast<USoundModulationGeneratorEnvelopeFollower>(A))
		{
			P.Type = FEnvelopeFollowerGeneratorParams::StaticStruct(); P.Data = &F->Params;
			P.Bounds = {{TEXT("Gain"), {0,1000}}, {TEXT("AttackTime"), {0,86400}}, {TEXT("ReleaseTime"), {0,86400}}};
			P.Flags = {TEXT("bBypass"), TEXT("bInvert")};
		}
		return P;
	}
	void CurveErrors(const FWaveTableTransform& T, TArray<FString>& E)
	{
		if (static_cast<int32>(T.Curve) >= static_cast<int32>(EWaveTableCurve::Count)) E.Add(TEXT("Invalid transform curve enum"));
		if (!FMath::IsFinite(T.Scalar) || T.Scalar < .1f || T.Scalar > 10.f) E.Add(TEXT("Transform scalar must be in [0.1,10]"));
		if (T.Curve == EWaveTableCurve::Shared && !T.CurveShared) E.Add(TEXT("Shared transform requires a Curve Float"));
		const FRichCurve* C = T.Curve == EWaveTableCurve::Shared && T.CurveShared ? &T.CurveShared->FloatCurve : T.Curve == EWaveTableCurve::Custom ? &T.CurveCustom : nullptr;
		if (C)
		{
			const int32 MaxKeys = ModulationFileUtils::HasSource(T) ? 4097 : 256;
			if (C->GetNumKeys() < 2 || C->GetNumKeys() > MaxKeys) E.Add(TEXT("Transform curve key count is outside its supported range"));
			for (auto It = C->GetKeyIterator(); It; ++It) if (!FMath::IsFinite(It->Time) || !FMath::IsFinite(It->Value) || !FMath::IsFinite(It->ArriveTangent) || !FMath::IsFinite(It->LeaveTangent)) E.Add(TEXT("Transform curve keys and tangents must be finite"));
		}
	}
}

bool ModulationAuthoringUtils::Supports(const UObject* A)
{
	return A && (A->IsA<USoundModulationPatch>() || A->IsA<USoundModulationGeneratorLFO>() || A->IsA<USoundModulationGeneratorADEnvelope>() || A->IsA<USoundModulationGeneratorEnvelopeFollower>() || A->IsA<UAudioBus>());
}

UClass* ModulationAuthoringUtils::GeneratorClass(const FString& Type)
{
	if (Type == TEXT("lfo")) return USoundModulationGeneratorLFO::StaticClass();
	if (Type == TEXT("ad_envelope")) return USoundModulationGeneratorADEnvelope::StaticClass();
	if (Type == TEXT("envelope_follower")) return USoundModulationGeneratorEnvelopeFollower::StaticClass();
	throw std::runtime_error("GeneratorType must be lfo, ad_envelope or envelope_follower");
}

TArray<FString> ModulationAuthoringUtils::Errors(UObject* A)
{
	TArray<FString> E;
	if (auto* Patch = Cast<USoundModulationPatch>(A))
	{
		if (Patch->PatchSettings.OutputParameter) E.Append(ModulationUtils::ValidationErrors(Patch->PatchSettings.OutputParameter));
		if (Patch->PatchSettings.Inputs.Num() > 128) E.Add(TEXT("Patch inputs are limited to 128"));
		TSet<const UObject*> Seen;
		for (const auto& Input : Patch->PatchSettings.Inputs)
		{
			if (!Input.Bus || Seen.Contains(Input.Bus)) E.Add(TEXT("Patch inputs contain missing or duplicate buses"));
			if (Input.Bus) E.Append(ModulationUtils::ValidationErrors(Input.Bus)); Seen.Add(Input.Bus); CurveErrors(Input.Transform, E); E.Append(ModulationFileUtils::Errors(Input.Transform));
		}
	}
	else if (auto* B = Cast<UAudioBus>(A))
	{
		if (!TArray<int32>{1,2,4,6,8}.Contains(B->GetNumChannels())) E.Add(TEXT("Audio Bus channels must be 1,2,4,6 or 8"));
	}
	else
	{
		const FParams P = Params(A);
		if (!P.Type) { E.Add(TEXT("Generator class has no typed adapter")); return E; }
		for (const auto& Pair : P.Bounds)
		{
			const float V = FindFProperty<FFloatProperty>(P.Type, *Pair.Key)->GetPropertyValue_InContainer(P.Data);
			if (!FMath::IsFinite(V) || V < Pair.Value.X || V > Pair.Value.Y) E.Add(Pair.Key + TEXT(" is outside its supported range"));
		}
		if (auto* L = Cast<USoundModulationGeneratorLFO>(A)) if (static_cast<int32>(L->Params.Shape) >= static_cast<int32>(ESoundModulationLFOShape::COUNT)) E.Add(TEXT("Invalid LFO shape"));
		if (auto* AD = Cast<USoundModulationGeneratorADEnvelope>(A)) if (AD->Params.bLooping && AD->Params.AttackTime + AD->Params.DecayTime <= 0.f) E.Add(TEXT("Looping AD envelope requires a positive total duration"));
		if (auto* F = Cast<USoundModulationGeneratorEnvelopeFollower>(A)) if (F->Params.AudioBus) E.Append(Errors(F->Params.AudioBus));
	}
	return E;
}

FString ModulationAuthoringUtils::Inspect(UObject* A)
{
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	J->WriteValue(TEXT("asset_path"), Path(A)); J->WriteValue(TEXT("class_path"), A->GetClass()->GetPathName()); J->WriteValue(TEXT("dirty"), A->GetOutermost()->IsDirty());
	if (auto* Patch = Cast<USoundModulationPatch>(A))
	{
		J->WriteValue(TEXT("bypass"), Patch->PatchSettings.bBypass); J->WriteValue(TEXT("parameter_path"), Path(Patch->PatchSettings.OutputParameter)); J->WriteArrayStart(TEXT("inputs"));
		for (const auto& Input : Patch->PatchSettings.Inputs)
		{
			J->WriteObjectStart(); J->WriteValue(TEXT("bus_path"), Path(Input.Bus)); J->WriteValue(TEXT("sample_and_hold"), static_cast<bool>(Input.bSampleAndHold));
			J->WriteValue(TEXT("curve"), StaticEnum<EWaveTableCurve>()->GetNameStringByValue(static_cast<int64>(Input.Transform.Curve)));
			J->WriteValue(TEXT("scalar"), Input.Transform.Scalar); J->WriteValue(TEXT("curve_path"), Path(Input.Transform.CurveShared)); J->WriteArrayStart(TEXT("keys"));
			for (auto It = Input.Transform.CurveCustom.GetKeyIterator(); It; ++It) { J->WriteObjectStart(); J->WriteValue(TEXT("time"), It->Time); J->WriteValue(TEXT("value"), It->Value); J->WriteValue(TEXT("interpolation"), static_cast<int32>(It->InterpMode)); J->WriteObjectEnd(); }
			J->WriteArrayEnd(); if (ModulationFileUtils::HasSource(Input.Transform)) J->WriteRawJSONValue(TEXT("file_transform"), ModulationFileUtils::SourceJson(Input.Transform)); J->WriteObjectEnd();
		}
		J->WriteArrayEnd();
	}
	else if (auto* B = Cast<UAudioBus>(A)) J->WriteValue(TEXT("channels"), B->GetNumChannels());
	else
	{
		const FParams P = Params(A); if (!P.Type) throw std::runtime_error("Generator class has no typed adapter");
		J->WriteObjectStart(TEXT("numeric")); TArray<FString> Keys; P.Bounds.GetKeys(Keys); Keys.Sort();
		for (const FString& Key : Keys) J->WriteValue(Key, FindFProperty<FFloatProperty>(P.Type, *Key)->GetPropertyValue_InContainer(P.Data)); J->WriteObjectEnd();
		J->WriteObjectStart(TEXT("flags")); for (const FString& Key : P.Flags) J->WriteValue(Key, FindFProperty<FBoolProperty>(P.Type, *Key)->GetPropertyValue_InContainer(P.Data)); J->WriteObjectEnd();
		if (auto* L = Cast<USoundModulationGeneratorLFO>(A)) J->WriteValue(TEXT("shape"), StaticEnum<ESoundModulationLFOShape>()->GetNameStringByValue(static_cast<int64>(L->Params.Shape)));
		if (auto* F = Cast<USoundModulationGeneratorEnvelopeFollower>(A)) { J->WriteValue(TEXT("audio_bus_path"), Path(F->Params.AudioBus)); J->WriteValue(TEXT("has_audio_source"), F->Params.AudioBus != nullptr); }
	}
	J->WriteObjectEnd(); J->Close(); return Json;
}

FString ModulationAuthoringUtils::Edit(UObject* A, const FModulationSettingsReq& R)
{
	if (auto* Patch = Cast<USoundModulationPatch>(A))
	{
		if (!R.Numeric.IsEmpty() || R.bSetUnitDisplayName || R.bSetAddress || R.bSetGenerators || R.bSetRetriggerOnActivation) throw std::runtime_error("Patch settings support parameter and bypass only");
		auto* Preview = CastChecked<USoundModulationPatch>(ModulationUtils::TransientCopy(Patch)); Preview->PatchSettings.Inputs = Patch->PatchSettings.Inputs;
		if (R.bSetParameter) Preview->PatchSettings.OutputParameter = R.ParameterPath.IsEmpty() ? nullptr : Reference<USoundModulationParameter>(R.ParameterPath);
		if (R.bSetBypass) Preview->PatchSettings.bBypass = R.bBypass;
		Require(Preview);
		const bool Changed = Preview->PatchSettings.OutputParameter != Patch->PatchSettings.OutputParameter || Preview->PatchSettings.bBypass != Patch->PatchSettings.bBypass;
		// Preserve input table data when only output metadata changes.
		Preview->PatchSettings.Inputs = Patch->PatchSettings.Inputs;
		Commit(Patch, Preview, TEXT("PatchSettings"), Changed, R.bDryRun, R.bSave); return Result(Patch, Changed, R.bDryRun, R.bSave);
	}
	if (auto* B = Cast<UAudioBus>(A))
	{
		if (R.bSetParameter || R.bSetBypass || R.bSetUnitDisplayName || R.bSetAddress || R.bSetGenerators || R.bSetRetriggerOnActivation) throw std::runtime_error("Audio Bus settings support Channels only");
		auto* Preview = CastChecked<UAudioBus>(ModulationUtils::TransientCopy(B));
		for (const auto& Pair : R.Numeric) { if (Pair.Key != TEXT("Channels") || !TArray<float>{1,2,4,6,8}.Contains(Pair.Value)) throw std::runtime_error("Channels must be 1,2,4,6 or 8"); Preview->AudioBusChannels = AudioBusUtils::ConvertIntToEAudioBusChannels(static_cast<int32>(Pair.Value)); }
		Require(Preview); const bool Changed = Preview->AudioBusChannels != B->AudioBusChannels;
		Commit(B, Preview, TEXT("AudioBusChannels"), Changed, R.bDryRun, R.bSave); return Result(B, Changed, R.bDryRun, R.bSave);
	}
	throw std::runtime_error("Use /audio/modulation/generators/settings to edit generators");
}

FString ModulationAuthoringUtils::EditGenerator(UObject* A, const FModulationGeneratorReq& R)
{
	if (!Params(A).Type) throw std::runtime_error("Asset must be a supported modulation generator");
	UObject* Preview = ModulationUtils::TransientCopy(A); const FParams P = Params(Preview);
	for (const auto& Pair : R.Numeric) { if (!P.Bounds.Contains(Pair.Key)) throw std::runtime_error("Unsupported generator numeric field"); FindFProperty<FFloatProperty>(P.Type, *Pair.Key)->SetPropertyValue_InContainer(P.Data, Pair.Value); }
	for (const auto& Pair : R.Flags) { if (!P.Flags.Contains(Pair.Key)) throw std::runtime_error("Unsupported generator flag"); FindFProperty<FBoolProperty>(P.Type, *Pair.Key)->SetPropertyValue_InContainer(P.Data, Pair.Value); }
	if (!R.Shape.IsEmpty())
	{
		auto* L = Cast<USoundModulationGeneratorLFO>(Preview); if (!L) throw std::runtime_error("Shape applies only to LFO generators");
		const int64 V = StaticEnum<ESoundModulationLFOShape>()->GetValueByNameString(R.Shape); if (V < 0 || V >= static_cast<int64>(ESoundModulationLFOShape::COUNT)) throw std::runtime_error("Unsupported LFO shape"); L->Params.Shape = static_cast<ESoundModulationLFOShape>(V);
	}
	if (R.bSetAudioBus) { auto* F = Cast<USoundModulationGeneratorEnvelopeFollower>(Preview); if (!F) throw std::runtime_error("AudioBusPath applies only to envelope followers"); F->Params.AudioBus = R.AudioBusPath.IsEmpty() ? nullptr : Reference<UAudioBus>(R.AudioBusPath); }
	Require(Preview); FProperty* Field = FindFProperty<FProperty>(A->GetClass(), TEXT("Params")); const bool Changed = !Field->Identical_InContainer(A, Preview);
	Commit(A, Preview, TEXT("Params"), Changed, R.bDryRun, R.bSave); return Result(A, Changed, R.bDryRun, R.bSave);
}

FString ModulationAuthoringUtils::Input(UObject* A, const FModulationInputReq& R)
{
	auto* Patch = Cast<USoundModulationPatch>(A); if (!Patch) throw std::runtime_error("Asset must be a modulation patch");
	const FString Op = R.Operation.ToLower(); if (Op != TEXT("upsert") && Op != TEXT("remove") && Op != TEXT("clear")) throw std::runtime_error("Operation must be upsert, remove or clear");
	if (Op != TEXT("upsert") && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Removing patch inputs requires bConfirm=true");
	auto* Preview = CastChecked<USoundModulationPatch>(ModulationUtils::TransientCopy(Patch)); Preview->PatchSettings.Inputs = Patch->PatchSettings.Inputs;
	auto& Inputs = Preview->PatchSettings.Inputs; USoundControlBus* Bus = Op == TEXT("clear") ? nullptr : Reference<USoundControlBus>(R.BusPath);
	const int32 Index = Inputs.IndexOfByPredicate([Bus](const FSoundControlModulationInput& I) { return I.Bus == Bus; });
	if (Op == TEXT("clear")) Inputs.Reset();
	else if (Op == TEXT("remove")) { if (Index == INDEX_NONE) throw std::runtime_error("Bus has no patch input"); Inputs.RemoveAt(Index); }
	else
	{
		FSoundControlModulationInput Input; Input.Bus = Bus; Input.bSampleAndHold = R.bSampleAndHold;
		const int64 Enum = StaticEnum<EWaveTableCurve>()->GetValueByNameString(R.Curve);
		if (Enum < 0 || Enum >= static_cast<int64>(EWaveTableCurve::File)) throw std::runtime_error("Unsupported transform curve; use /audio/modulation/inputs/import for files");
		Input.Transform.Curve = static_cast<EWaveTableCurve>(Enum); Input.Transform.Scalar = R.Scalar;
		if (Input.Transform.Curve == EWaveTableCurve::Shared) { if (!R.Keys.IsEmpty()) throw std::runtime_error("Shared curves cannot include inline keys"); Input.Transform.CurveShared = Reference<UCurveFloat>(R.CurvePath); }
		else if (Input.Transform.Curve == EWaveTableCurve::Custom)
		{
			if (!R.CurvePath.IsEmpty() || R.Keys.Num() < 2 || R.Keys.Num() > 256) throw std::runtime_error("Custom transform requires 2-256 inline keys and no curve path");
			float Last = -1.f;
			for (const auto& Key : R.Keys)
			{
				if (!FMath::IsFinite(Key.Time) || !FMath::IsFinite(Key.Value) || Key.Time < 0.f || Key.Time > 1.f || Key.Time <= Last || Key.Value < 0.f || Key.Value > 1.f) throw std::runtime_error("Custom keys must be increasing and normalized in [0,1]"); Last = Key.Time;
				const auto Handle = Input.Transform.CurveCustom.AddKey(Key.Time, Key.Value); auto& Native = Input.Transform.CurveCustom.GetKey(Handle);
				if (Key.Interpolation == TEXT("Linear")) Native.InterpMode = RCIM_Linear;
				else if (Key.Interpolation == TEXT("Constant")) Native.InterpMode = RCIM_Constant;
				else if (Key.Interpolation == TEXT("Cubic")) { Native.InterpMode = RCIM_Cubic; Native.TangentMode = RCTM_Auto; }
				else throw std::runtime_error("Interpolation must be Linear, Constant or Cubic");
			}
			Input.Transform.CurveCustom.AutoSetTangents();
		}
		else if (!R.Keys.IsEmpty() || !R.CurvePath.IsEmpty()) throw std::runtime_error("Built-in curves cannot include curve references or keys");
		if (Index == INDEX_NONE) { if (Inputs.Num() >= 128) throw std::runtime_error("Patch inputs are limited to 128"); Inputs.Add(Input); } else Inputs[Index] = Input;
	}
	Require(Preview);
	bool Changed = Inputs.Num() != Patch->PatchSettings.Inputs.Num();
	if (!Changed) for (int32 I = 0; I < Inputs.Num(); ++I)
	{
		const auto& X = Inputs[I]; const auto& Y = Patch->PatchSettings.Inputs[I];
		if (X.Bus != Y.Bus || X.bSampleAndHold != Y.bSampleAndHold || X.Transform.Curve != Y.Transform.Curve || X.Transform.Scalar != Y.Transform.Scalar || X.Transform.CurveShared != Y.Transform.CurveShared || !(X.Transform.CurveCustom == Y.Transform.CurveCustom) || X.Transform.GetTableData().IsEmpty() != Y.Transform.GetTableData().IsEmpty()) Changed = true;
	}
	Commit(Patch, Preview, TEXT("PatchSettings"), Changed, R.bDryRun, R.bSave); return Result(Patch, Changed, R.bDryRun, R.bSave);
}

FString ModulationAuthoringUtils::Sample(UObject* A, const FModulationSampleReq& R)
{
	Require(A); TArray<float> Values; FString Scope;
	if (auto* Patch = Cast<USoundModulationPatch>(A))
	{
		USoundControlBus* Bus = Reference<USoundControlBus>(R.BusPath);
		const auto* Input = Patch->PatchSettings.Inputs.FindByPredicate([Bus](const FSoundControlModulationInput& I) { return I.Bus == Bus; });
		if (!Input) throw std::runtime_error("Bus has no patch input");
		if (R.Values.IsEmpty() || R.Values.Num() > 256) throw std::runtime_error("Values must contain 1-256 normalized inputs");
		for (float V : R.Values) { if (!FMath::IsFinite(V) || V < 0.f || V > 1.f) throw std::runtime_error("Transform inputs must be normalized in [0,1]"); Input->Transform.Apply(V); if (!FMath::IsFinite(V)) throw std::runtime_error("Native transform returned a nonfinite value"); Values.Add(V); }
		Scope = TEXT("native_input_transform_only; excludes patch mixing, output conversion and sample-and-hold state");
	}
	else if (auto* G = Cast<USoundModulationGenerator>(A))
	{
		if (G->IsA<USoundModulationGeneratorEnvelopeFollower>()) throw std::runtime_error("Envelope follower sampling requires a live Audio Bus and audio device");
		if (!R.Values.IsEmpty() || !R.BusPath.IsEmpty()) throw std::runtime_error("Generator sampling uses Samples and StepSeconds only");
		if (R.Samples < 1 || R.Samples > 512 || !FMath::IsFinite(R.StepSeconds) || R.StepSeconds < .0001f || R.StepSeconds > 1.f || R.Samples * R.StepSeconds > 60.f) throw std::runtime_error("Sampling requires 1-512 samples, a 0.0001-1 second step and at most 60 seconds total");
		auto Instance = G->CreateInstance(); if (!Instance) throw std::runtime_error("Native generator instance creation failed");
		for (int32 I = 0; I < R.Samples; ++I) { Instance->Update(R.StepSeconds); const float V = Instance->GetValue(); if (!FMath::IsFinite(V)) throw std::runtime_error("Native generator returned a nonfinite value"); Values.Add(V); }
		Scope = TEXT("fresh_native_generator_instance; samples after each update; no live playback state");
	}
	else throw std::runtime_error("Sampling supports modulation patches or LFO/AD envelope generators");
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"), Path(A)); J->WriteValue(TEXT("scope"), Scope); J->WriteArrayStart(TEXT("values")); for (float V : Values) J->WriteValue(V); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}
