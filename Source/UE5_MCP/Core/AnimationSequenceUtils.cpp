#include "AnimationSequenceUtils.h"
#include "UE5_MCP/API/DTO/AnimationRichCurveReq.h"
#include "Editor.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/Package.h"

#include "UE5_MCP/API/DTO/AnimationAttributeReq.h"
#include "UE5_MCP/API/DTO/AnimationBoneTrackReq.h"
#include "UE5_MCP/API/DTO/AnimationTimingReq.h"

#include "Animation/AnimSequence.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/AnimData/AttributeIdentifier.h"
#include "Animation/BuiltInAttributeTypes.h"
#include "Animation/AttributeCurve.h"
#include "Animation/Skeleton.h"
#include "UObject/StructOnScope.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"

#include <stdexcept>

namespace
{
	UScriptStruct* AttributeStruct(const FString& Type)
	{
		if (Type.Equals(TEXT("float"), ESearchCase::IgnoreCase)) return FFloatAnimationAttribute::StaticStruct();
		if (Type.Equals(TEXT("integer"), ESearchCase::IgnoreCase)) return FIntegerAnimationAttribute::StaticStruct();
		if (Type.Equals(TEXT("string"), ESearchCase::IgnoreCase)) return FStringAnimationAttribute::StaticStruct();
		if (Type.Equals(TEXT("vector"), ESearchCase::IgnoreCase)) return FVectorAnimationAttribute::StaticStruct();
		if (Type.Equals(TEXT("transform"), ESearchCase::IgnoreCase)) return FTransformAnimationAttribute::StaticStruct();
		if (UScriptStruct* Struct = LoadObject<UScriptStruct>(nullptr, *Type)) return Struct;
		throw std::runtime_error("attribute_type must be float, integer, string, vector, transform, or a registered ScriptStruct path");
	}

	FString AttributeTypeName(const UScriptStruct* Struct)
	{
		if (Struct == FFloatAnimationAttribute::StaticStruct()) return TEXT("float");
		if (Struct == FIntegerAnimationAttribute::StaticStruct()) return TEXT("integer");
		if (Struct == FStringAnimationAttribute::StaticStruct()) return TEXT("string");
		if (Struct == FVectorAnimationAttribute::StaticStruct()) return TEXT("vector");
		if (Struct == FTransformAnimationAttribute::StaticStruct()) return TEXT("transform");
		return Struct ? Struct->GetPathName() : TEXT("");
	}

	const FBoneAnimationTrack* FindSourceBoneTrack(const IAnimationDataModel* Model, FName BoneName)
	{
		PRAGMA_DISABLE_DEPRECATION_WARNINGS
		const FBoneAnimationTrack* Track = Model->FindBoneTrackByName(BoneName);
		PRAGMA_ENABLE_DEPRECATION_WARNINGS
		return Track;
	}

	bool ValidComponentKeyCount(int32 Count, int32 SourceKeys)
	{
		return Count == 0 || Count == 1 || Count == SourceKeys;
	}

	void ExpandBoneTrack(const UAnimSequence* Sequence, FName BoneName, TArray<FTransform>& OutTransforms)
	{
		const IAnimationDataModel* Model = Sequence->GetDataModel();
		const FBoneAnimationTrack* Track = FindSourceBoneTrack(Model, BoneName);
		const int32 Count = Model->GetNumberOfKeys();
		if (!Track)
		{
			if (!Model->IsValidBoneTrackName(BoneName)) throw std::runtime_error("Bone track was not found");
			TArray<FFrameNumber> Frames;
			Frames.Reserve(Count);
			for (int32 Index = 0; Index < Count; ++Index) Frames.Add(FFrameNumber(Index));
			OutTransforms.Reset(Count);
			Model->GetBoneTrackTransforms(BoneName, Frames, OutTransforms);
			if (OutTransforms.Num() != Count) throw std::runtime_error("Sequencer bone track did not evaluate every source frame");
			return;
		}
		const FRawAnimSequenceTrack& Raw = Track->InternalTrackData;
		if (!ValidComponentKeyCount(Raw.PosKeys.Num(), Count) || !ValidComponentKeyCount(Raw.RotKeys.Num(), Count)
			|| !ValidComponentKeyCount(Raw.ScaleKeys.Num(), Count))
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Bone track has inconsistent component key counts: %s"), *BoneName.ToString())));
		FTransform Reference = FTransform::Identity;
		if (const USkeleton* Skeleton = Sequence->GetSkeleton())
		{
			const int32 BoneIndex = Skeleton->GetReferenceSkeleton().FindBoneIndex(BoneName);
			if (BoneIndex != INDEX_NONE) Reference = Skeleton->GetReferenceSkeleton().GetRefBonePose()[BoneIndex];
		}
		OutTransforms.Reset(Count);
		for (int32 Index = 0; Index < Count; ++Index)
		{
			const FVector Position = Raw.PosKeys.IsEmpty() ? Reference.GetTranslation()
				: FVector(Raw.PosKeys[Raw.PosKeys.Num() == 1 ? 0 : Index]);
			const FQuat Rotation = Raw.RotKeys.IsEmpty() ? Reference.GetRotation()
				: FQuat(Raw.RotKeys[Raw.RotKeys.Num() == 1 ? 0 : Index]);
			const FVector Scale = Raw.ScaleKeys.IsEmpty() ? Reference.GetScale3D()
				: FVector(Raw.ScaleKeys[Raw.ScaleKeys.Num() == 1 ? 0 : Index]);
			OutTransforms.Add(FTransform(Rotation, Position, Scale));
		}
	}
}

FString AnimationSequenceUtils::AttributesJson(const UAnimSequence* Sequence)
{
	const IAnimationDataModel* Model = Sequence ? Sequence->GetDataModel() : nullptr;
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Sequence ? Sequence->GetPathName() : TEXT(""));
	Writer->WriteArrayStart(TEXT("attributes"));
	if (Model) for (const FAnimatedBoneAttribute& Attribute : Model->GetAttributes())
	{
		const UScriptStruct* Struct = Attribute.Identifier.GetType();
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("name"), Attribute.Identifier.GetName().ToString());
		Writer->WriteValue(TEXT("bone_name"), Attribute.Identifier.GetBoneName().ToString());
		Writer->WriteValue(TEXT("bone_index"), Attribute.Identifier.GetBoneIndex());
		Writer->WriteValue(TEXT("type"), AttributeTypeName(Struct));
		Writer->WriteArrayStart(TEXT("keys"));
		for (auto It = Attribute.Curve.GetKeyIterator(); It; ++It)
		{
			const FAttributeKey& Key = *It;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("time"), Key.Time);
			if (Struct == FFloatAnimationAttribute::StaticStruct())
			{
				if (const auto* Value = Key.GetValuePtr<FFloatAnimationAttribute>()) Writer->WriteValue(TEXT("value"), Value->Value);
			}
			else if (Struct == FIntegerAnimationAttribute::StaticStruct())
			{
				if (const auto* Value = Key.GetValuePtr<FIntegerAnimationAttribute>()) Writer->WriteValue(TEXT("value"), Value->Value);
			}
			else if (Struct == FStringAnimationAttribute::StaticStruct())
			{
				if (const auto* Value = Key.GetValuePtr<FStringAnimationAttribute>()) Writer->WriteValue(TEXT("value"), Value->Value);
			}
			else if (Struct == FVectorAnimationAttribute::StaticStruct())
			{
				if (const auto* Value = Key.GetValuePtr<FVectorAnimationAttribute>()) Writer->WriteValue(TEXT("value"), Value->Value.ToString());
			}
			else if (Struct == FTransformAnimationAttribute::StaticStruct())
			{
				if (const auto* Value = Key.GetValuePtr<FTransformAnimationAttribute>()) Writer->WriteValue(TEXT("value"), Value->Value.ToString());
			}
			else if (Struct)
			{
				FString Exported;
				Struct->ExportText(Exported, Key.GetValuePtr<uint8>(), nullptr, nullptr, PPF_None, nullptr);
				Writer->WriteValue(TEXT("value_text"), Exported);
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd();
	Writer->Close();
	return Json;
}

bool AnimationSequenceUtils::EditAttribute(UAnimSequence* Sequence, const FAnimationAttributeReq& Request)
{
	if (!Sequence || !Sequence->GetDataModel()) throw std::runtime_error("Animation Sequence data model is missing");
	if (Request.AttributeName.IsEmpty() || Request.BoneName.IsEmpty())
		throw std::runtime_error("attribute_name and bone_name are required");
	const bool bAdd = Request.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
	const bool bSetKey = Request.Operation.Equals(TEXT("set_key"), ESearchCase::IgnoreCase);
	const bool bRemoveKey = Request.Operation.Equals(TEXT("remove_key"), ESearchCase::IgnoreCase);
	const bool bRemove = Request.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase);
	if (!bAdd && !bSetKey && !bRemoveKey && !bRemove)
		throw std::runtime_error("operation must be add, set_key, remove_key, or remove");
	UScriptStruct* Struct = AttributeStruct(Request.AttributeType);
	const FAnimationAttributeIdentifier Id = UAnimationAttributeIdentifierExtensions::CreateAttributeIdentifier(
		Sequence, FName(*Request.AttributeName), FName(*Request.BoneName), Struct);
	if (!Id.IsValid()) throw std::runtime_error("Attribute type is unsupported or bone is absent from the Sequence Skeleton");
	const FAnimatedBoneAttribute* Existing = nullptr;
	for (const FAnimatedBoneAttribute& Attribute : Sequence->GetDataModel()->GetAttributes())
		if (Attribute.Identifier.GetName() == Id.GetName() && Attribute.Identifier.GetBoneName() == Id.GetBoneName())
		{
			Existing = &Attribute;
			break;
		}
	if (bAdd && Existing) throw std::runtime_error("Attribute already exists on this bone");
	if (!bAdd && (!Existing || Existing->Identifier.GetType() != Struct))
		throw std::runtime_error("Attribute with this name, bone, and type was not found");
	if ((bSetKey || bRemoveKey) && (!FMath::IsFinite(Request.Time) || Request.Time < 0.0f || Request.Time > Sequence->GetPlayLength()))
		throw std::runtime_error("time must be finite and within the Animation Sequence");
	if (bRemoveKey && !Existing->Curve.FindKey(Request.Time).IsValid())
		throw std::runtime_error("Attribute key was not found at the requested time");
	FFloatAnimationAttribute FloatValue;
	FIntegerAnimationAttribute IntegerValue;
	FStringAnimationAttribute StringValue;
	FVectorAnimationAttribute VectorValue;
	FTransformAnimationAttribute TransformValue;
	TUniquePtr<FStructOnScope> CustomValue;
	if (bSetKey)
	{
		if (Struct == FFloatAnimationAttribute::StaticStruct())
		{
			if (!LexTryParseString(FloatValue.Value, *Request.Value) || !FMath::IsFinite(FloatValue.Value))
				throw std::runtime_error("float attribute value must be finite numeric text");
		}
		else if (Struct == FIntegerAnimationAttribute::StaticStruct())
		{
			if (!LexTryParseString(IntegerValue.Value, *Request.Value)) throw std::runtime_error("integer attribute value must be an integer");
		}
		else if (Struct == FStringAnimationAttribute::StaticStruct()) StringValue.Value = Request.Value;
		else if (Struct == FVectorAnimationAttribute::StaticStruct())
		{
			if (!VectorValue.Value.InitFromString(Request.Value) || !FMath::IsFinite(VectorValue.Value.X)
				|| !FMath::IsFinite(VectorValue.Value.Y) || !FMath::IsFinite(VectorValue.Value.Z))
				throw std::runtime_error("vector attribute value must use finite X=,Y=,Z= components");
		}
		else if (Struct == FTransformAnimationAttribute::StaticStruct())
		{
			if (!TransformValue.Value.InitFromString(Request.Value) || TransformValue.Value.ContainsNaN())
				throw std::runtime_error("transform attribute value must use finite translation|rotation|scale triples");
		}
		else
		{
			CustomValue = MakeUnique<FStructOnScope>(Struct);
			if (!Struct->ImportText(*Request.Value, CustomValue->GetStructMemory(), Sequence, PPF_None, GWarn, Struct->GetName()))
				throw std::runtime_error("attribute value is not valid native struct text for the requested type");
		}
	}
	if (Request.bDryRun) return true;
	IAnimationDataController& Controller = Sequence->GetController();
	IAnimationDataController::FScopedBracket Bracket(Controller, NSLOCTEXT("UE5_MCP", "EditAnimationAttribute", "Edit Animation Attribute"));
	Sequence->Modify();
	bool bChanged = false;
	if (bAdd) bChanged = Controller.AddAttribute(Id);
	else if (bRemove) bChanged = Controller.RemoveAttribute(Id);
	else if (bRemoveKey) bChanged = Controller.RemoveAttributeKey(Id, Request.Time);
	else if (Struct == FFloatAnimationAttribute::StaticStruct()) bChanged = Controller.SetTypedAttributeKey(Id, Request.Time, FloatValue);
	else if (Struct == FIntegerAnimationAttribute::StaticStruct()) bChanged = Controller.SetTypedAttributeKey(Id, Request.Time, IntegerValue);
	else if (Struct == FStringAnimationAttribute::StaticStruct()) bChanged = Controller.SetTypedAttributeKey(Id, Request.Time, StringValue);
	else if (Struct == FVectorAnimationAttribute::StaticStruct()) bChanged = Controller.SetTypedAttributeKey(Id, Request.Time, VectorValue);
	else if (Struct == FTransformAnimationAttribute::StaticStruct()) bChanged = Controller.SetTypedAttributeKey(Id, Request.Time, TransformValue);
	else bChanged = Controller.SetAttributeKey(Id, Request.Time, CustomValue->GetStructMemory(), Struct);
	if (!bChanged) throw std::runtime_error("Animation data controller rejected the attribute edit");
	return bChanged;
}

FString AnimationSequenceUtils::BoneTrackJson(const UAnimSequence* Sequence, FName BoneName, int32 StartFrame, int32 Count)
{
	const IAnimationDataModel* Model = Sequence ? Sequence->GetDataModel() : nullptr;
	if (!Model || !Model->IsValidBoneTrackName(BoneName)) throw std::runtime_error("Bone track was not found");
	if (StartFrame < 0 || Count < 1 || Count > 1000 || StartFrame >= Model->GetNumberOfKeys())
		throw std::runtime_error("start_frame or count is outside the track; count must be 1..1000");
	TArray<FTransform> Transforms;
	ExpandBoneTrack(Sequence, BoneName, Transforms);
	const int32 End = FMath::Min(StartFrame + Count, Transforms.Num());
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
	Writer->WriteValue(TEXT("bone_name"), BoneName.ToString());
	Writer->WriteValue(TEXT("total_keys"), Transforms.Num());
	Writer->WriteValue(TEXT("start_frame"), StartFrame);
	Writer->WriteArrayStart(TEXT("keys"));
	for (int32 Index = StartFrame; Index < End; ++Index)
	{
		const FTransform& Transform = Transforms[Index];
		const FVector Translation = Transform.GetTranslation();
		const FQuat Rotation = Transform.GetRotation();
		const FVector Scale = Transform.GetScale3D();
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("frame"), Index);
		Writer->WriteObjectStart(TEXT("translation"));
		Writer->WriteValue(TEXT("x"), Translation.X); Writer->WriteValue(TEXT("y"), Translation.Y); Writer->WriteValue(TEXT("z"), Translation.Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectStart(TEXT("rotation_quat"));
		Writer->WriteValue(TEXT("x"), Rotation.X); Writer->WriteValue(TEXT("y"), Rotation.Y);
		Writer->WriteValue(TEXT("z"), Rotation.Z); Writer->WriteValue(TEXT("w"), Rotation.W);
		Writer->WriteObjectEnd();
		Writer->WriteObjectStart(TEXT("scale"));
		Writer->WriteValue(TEXT("x"), Scale.X); Writer->WriteValue(TEXT("y"), Scale.Y); Writer->WriteValue(TEXT("z"), Scale.Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd();
	Writer->Close();
	return Json;
}

bool AnimationSequenceUtils::EditBoneTrack(UAnimSequence* Sequence, const FAnimationBoneTrackReq& Request)
{
	const IAnimationDataModel* Model = Sequence ? Sequence->GetDataModel() : nullptr;
	const USkeleton* Skeleton = Sequence ? Sequence->GetSkeleton() : nullptr;
	if (!Model || !Skeleton) throw std::runtime_error("Animation Sequence requires a data model and Skeleton");
	if (Request.BoneName.IsEmpty()) throw std::runtime_error("bone_name is required");
	const FName BoneName(*Request.BoneName);
	const int32 BoneIndex = Skeleton->GetReferenceSkeleton().FindBoneIndex(BoneName);
	if (BoneIndex == INDEX_NONE) throw std::runtime_error("bone_name does not exist in the Sequence Skeleton");
	const bool bAdd = Request.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
	const bool bRemove = Request.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase);
	const bool bSetKey = Request.Operation.Equals(TEXT("set_key"), ESearchCase::IgnoreCase);
	if (!bAdd && !bRemove && !bSetKey) throw std::runtime_error("operation must be add, remove, or set_key");
	const bool bExists = Model->IsValidBoneTrackName(BoneName);
	if (bAdd && bExists) throw std::runtime_error("Bone track already exists");
	if (!bAdd && !bExists) throw std::runtime_error("Bone track does not exist");
	if (Model->GetNumberOfKeys() <= 0) throw std::runtime_error("Animation data model has no source keys");
	if (bSetKey && (Request.FrameIndex < 0 || Request.FrameIndex >= Model->GetNumberOfKeys()))
		throw std::runtime_error("frame_index is outside the source key range");
	const FVector& Translation = Request.Translation;
	const FVector& Scale = Request.Scale;
	const FRotator& Rotation = Request.Rotation;
	if (bSetKey && (!FMath::IsFinite(Translation.X) || !FMath::IsFinite(Translation.Y) || !FMath::IsFinite(Translation.Z)
		|| !FMath::IsFinite(Scale.X) || !FMath::IsFinite(Scale.Y) || !FMath::IsFinite(Scale.Z)
		|| Rotation.ContainsNaN())) throw std::runtime_error("translation, rotation, and scale must be finite");
	TArray<FTransform> Transforms;
	if (bSetKey) ExpandBoneTrack(Sequence, BoneName, Transforms);
	if (bSetKey && Transforms.Num() != Model->GetNumberOfKeys()) throw std::runtime_error("Bone track key count does not match source model");
	const FTransform NewTransform(Rotation, Translation, Scale);
	if (bSetKey && Transforms[Request.FrameIndex].Equals(NewTransform, KINDA_SMALL_NUMBER)) return false;
	if (Request.bDryRun) return true;
	IAnimationDataController& Controller = Sequence->GetController();
	IAnimationDataController::FScopedBracket Bracket(Controller, NSLOCTEXT("UE5_MCP", "EditAnimationBoneTrack", "Edit Animation Bone Track"));
	Sequence->Modify();
	if (bRemove)
	{
		if (!Controller.RemoveBoneTrack(BoneName)) throw std::runtime_error("Animation data controller rejected track removal");
		return true;
	}
	if (bAdd)
	{
		if (!Controller.AddBoneCurve(BoneName)) throw std::runtime_error("Animation data controller rejected track creation");
		Transforms.Init(Skeleton->GetReferenceSkeleton().GetRefBonePose()[BoneIndex], Model->GetNumberOfKeys());
	}
	else Transforms[Request.FrameIndex] = NewTransform;
	TArray<FVector> Positions;
	TArray<FQuat> Rotations;
	TArray<FVector> Scales;
	Positions.Reserve(Transforms.Num()); Rotations.Reserve(Transforms.Num()); Scales.Reserve(Transforms.Num());
	for (const FTransform& Transform : Transforms)
	{
		Positions.Add(Transform.GetTranslation());
		Rotations.Add(Transform.GetRotation());
		Scales.Add(Transform.GetScale3D());
	}
	if (!Controller.SetBoneTrackKeys(BoneName, Positions, Rotations, Scales))
	{
		if (bAdd) Controller.RemoveBoneTrack(BoneName);
		throw std::runtime_error("Animation data controller rejected bone track keys");
	}
	return true;
}

bool AnimationSequenceUtils::EditTiming(UAnimSequence* Sequence, const FAnimationTimingReq& Request)
{
	const IAnimationDataModel* Model = Sequence ? Sequence->GetDataModel() : nullptr;
	if (!Model) throw std::runtime_error("Animation Sequence data model is missing");
	const bool bRate = Request.Operation.Equals(TEXT("set_frame_rate"), ESearchCase::IgnoreCase);
	const bool bResize = Request.Operation.Equals(TEXT("resize"), ESearchCase::IgnoreCase);
	if (!bRate && !bResize) throw std::runtime_error("operation must be set_frame_rate or resize");
	const int32 OldFrames = Model->GetNumberOfFrames();
	const int32 OldKeyCount = Model->GetNumberOfKeys();
	const FFrameRate OldRate = Model->GetFrameRate();
	if (OldFrames < 1 || OldKeyCount != OldFrames + 1 || !OldRate.IsValid())
		throw std::runtime_error("Existing source frame count or frame rate is invalid");
	FFrameRate NewRate = OldRate;
	int32 NewFrames = OldFrames;
	if (bRate)
	{
		NewRate = FFrameRate(Request.FrameRateNumerator, Request.FrameRateDenominator);
		if (!NewRate.IsValid() || Request.FrameRateNumerator <= 0 || Request.FrameRateDenominator <= 0)
			throw std::runtime_error("frame rate numerator and denominator must be positive");
		if (NewRate == OldRate) return false;
		if (!NewRate.IsMultipleOf(OldRate) && !NewRate.IsFactorOf(OldRate))
			throw std::runtime_error("frame rate must be an exact multiple or factor of the source rate");
		const FFrameTime Converted = FFrameRate::TransformTime(FFrameNumber(OldFrames), OldRate, NewRate);
		if (!FMath::IsNearlyZero(Converted.GetSubFrame()))
			throw std::runtime_error("frame rate would produce a fractional end frame");
		NewFrames = Converted.GetFrame().Value;
	}
	else
	{
		NewFrames = Request.SourceFrames;
		if (NewFrames < 1) throw std::runtime_error("source_frames must be at least one");
		if (NewFrames == OldFrames) return false;
		if (NewFrames < OldFrames && !Request.bConfirmTrim)
			throw std::runtime_error("shortening source frames requires confirm_trim=true");
		if (NewFrames < OldFrames)
		{
			const double NewLength = OldRate.AsSeconds(FFrameNumber(NewFrames));
			for (const FAnimNotifyEvent& Notify : Sequence->Notifies)
				if (Notify.GetTriggerTime() + Notify.GetDuration() > NewLength + KINDA_SMALL_NUMBER)
					throw std::runtime_error("A notify extends beyond the requested shorter sequence");
		}
	}
	TArray<FName> Names;
	Model->GetBoneTrackNames(Names);
	if (NewFrames < 1 || NewFrames > 100000 || static_cast<int64>(NewFrames + 1) * FMath::Max(1, Names.Num()) > 2000000)
		throw std::runtime_error("requested timing would exceed the supported source-key budget");
	struct FTrackKeys
	{
		FName Name;
		TArray<FTransform> Transforms;
	};
	TArray<FTrackKeys> Rewritten;
	Rewritten.Reserve(Names.Num());
	for (FName Name : Names)
	{
		TArray<FTransform> OldKeys;
		ExpandBoneTrack(Sequence, Name, OldKeys);
		if (OldKeys.Num() != OldKeyCount) throw std::runtime_error("Bone track key count does not match source model");
		FTrackKeys& Track = Rewritten.AddDefaulted_GetRef();
		Track.Name = Name;
		Track.Transforms.Reserve(NewFrames + 1);
		if (bRate)
		{
			const double Ratio = OldRate.AsDecimal() / NewRate.AsDecimal();
			for (int32 Index = 0; Index <= NewFrames; ++Index)
			{
				const double Position = FMath::Clamp(static_cast<double>(Index) * Ratio, 0.0, static_cast<double>(OldFrames));
				const int32 A = FMath::FloorToInt(Position);
				const int32 B = FMath::Min(A + 1, OldFrames);
				FTransform Blended;
				Blended.Blend(OldKeys[A], OldKeys[B], static_cast<float>(Position - A));
				Track.Transforms.Add(Blended);
			}
		}
		else
		{
			for (int32 Index = 0; Index <= NewFrames; ++Index)
				Track.Transforms.Add(OldKeys[FMath::Min(Index, OldFrames)]);
		}
	}
	if (Request.bDryRun) return true;
	IAnimationDataController& Controller = Sequence->GetController();
	IAnimationDataController::FScopedBracket Bracket(Controller, NSLOCTEXT("UE5_MCP", "EditAnimationTiming", "Edit Animation Timing"));
	Sequence->Modify();
	if (bRate) Controller.SetFrameRate(NewRate);
	else Controller.ResizeInFrames(FFrameNumber(NewFrames), FFrameNumber(FMath::Min(OldFrames, NewFrames)),
		FFrameNumber(FMath::Max(OldFrames, NewFrames)));
	if (Sequence->GetDataModel()->GetNumberOfFrames() != NewFrames || Sequence->GetDataModel()->GetNumberOfKeys() != NewFrames + 1)
		throw std::runtime_error("Animation data controller did not apply the requested timing");
	for (const FTrackKeys& Track : Rewritten)
	{
		TArray<FVector> Positions;
		TArray<FQuat> Rotations;
		TArray<FVector> Scales;
		Positions.Reserve(Track.Transforms.Num()); Rotations.Reserve(Track.Transforms.Num()); Scales.Reserve(Track.Transforms.Num());
		for (const FTransform& Transform : Track.Transforms)
		{
			Positions.Add(Transform.GetTranslation());
			Rotations.Add(Transform.GetRotation());
			Scales.Add(Transform.GetScale3D());
		}
		if (!Controller.SetBoneTrackKeys(Track.Name, Positions, Rotations, Scales))
			throw std::runtime_error("Animation data controller rejected resampled bone keys");
	}
	return true;
}

void AnimationSequenceUtils::AppendBoneTrackKeyIssues(const UAnimSequence* Sequence, TArray<FString>& Errors)
{
	const IAnimationDataModel* Model = Sequence ? Sequence->GetDataModel() : nullptr;
	if (!Model) return;
	TArray<FName> Names;
	Model->GetBoneTrackNames(Names);
	for (FName Name : Names)
	{
		const FBoneAnimationTrack* Track = FindSourceBoneTrack(Model, Name);
		if (!Track) continue; // Sequencer-backed models have no legacy raw-track array.
		const FRawAnimSequenceTrack& Raw = Track->InternalTrackData;
		const int32 Count = Model->GetNumberOfKeys();
		if (!ValidComponentKeyCount(Raw.PosKeys.Num(), Count) || !ValidComponentKeyCount(Raw.RotKeys.Num(), Count)
			|| !ValidComponentKeyCount(Raw.ScaleKeys.Num(), Count))
			Errors.Add(FString::Printf(TEXT("Bone track component key counts do not match source keys: %s"), *Name.ToString()));
	}
}

FString AnimationSequenceUtils::RichFloatCurveJson(const UAnimSequence* Sequence,FName CurveName,int32 Start,int32 Count)
{
 if(!IsInGameThread() || !IsValid(Sequence) || CurveName.IsNone() || CurveName.ToString().Len()>128 || Start<0 || Count<1 || Count>512) throw std::runtime_error("Rich curve inspection requires sequence, bounded name/start and count [1,512]");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FFloatCurve* Curve=nullptr; for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==CurveName) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Float curve does not exist");
 const auto& Keys=Curve->FloatCurve.GetConstRefOfKeys(); if(Start>Keys.Num()) throw std::runtime_error("Start exceeds curve key count");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),CurveName.ToString()); J->WriteValue(TEXT("key_count"),Keys.Num()); J->WriteValue(TEXT("curve_flags"),Curve->GetCurveTypeFlags()); J->WriteValue(TEXT("comment"),Curve->Comment.Left(4096)); J->WriteValue(TEXT("comment_truncated"),Curve->Comment.Len()>4096); const auto Color=Curve->GetColor(); J->WriteArrayStart(TEXT("color_rgba")); for(float Channel:{Color.R,Color.G,Color.B,Color.A}) { if(FMath::IsFinite(Channel)) J->WriteValue(Channel); else J->WriteNull(); } J->WriteArrayEnd(); J->WriteValue(TEXT("start"),Start); J->WriteValue(TEXT("truncated"),Keys.Num()-Start>Count); J->WriteValue(TEXT("pre_extrapolation"),int32(Curve->FloatCurve.PreInfinityExtrap)); J->WriteValue(TEXT("post_extrapolation"),int32(Curve->FloatCurve.PostInfinityExtrap)); J->WriteArrayStart(TEXT("keys"));
 for(int32 Index=Start;Index<Keys.Num() && Index-Start<Count;++Index)
 {
  const auto& Key=Keys[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("index"),Index); auto Number=[&](const TCHAR* Name,float Value) { if(FMath::IsFinite(Value)) J->WriteValue(Name,Value); else J->WriteNull(Name); }; Number(TEXT("time"),Key.Time); Number(TEXT("value"),Key.Value); Number(TEXT("arrive_tangent"),Key.ArriveTangent); Number(TEXT("leave_tangent"),Key.LeaveTangent); Number(TEXT("arrive_weight"),Key.ArriveTangentWeight); Number(TEXT("leave_weight"),Key.LeaveTangentWeight); J->WriteValue(TEXT("interpolation"),int32(Key.InterpMode)); J->WriteValue(TEXT("tangent_mode"),int32(Key.TangentMode)); J->WriteValue(TEXT("weight_mode"),int32(Key.TangentWeightMode)); J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::ReplaceRichFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Keys.Num()>4096) throw std::runtime_error("Rich curve replacement requires stopped PIE, confirmed /Game sequence and bounded curve/keys");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing float curve required");
 TArray<FRichCurveKey> Keys; float Previous=-1.f;
 for(const auto& Row:R.Keys)
 {
  auto Bounded=[](float Value) { return FMath::IsFinite(Value) && FMath::Abs(Value)<=1.e8; };
  if(!Bounded(Row.Time) || Row.Time<0 || Row.Time>Sequence->GetPlayLength() || Row.Time<=Previous || !Bounded(Row.Value) || !Bounded(Row.ArriveTangent) || !Bounded(Row.LeaveTangent) || !Bounded(Row.ArriveWeight) || !Bounded(Row.LeaveWeight) || Row.ArriveWeight<0 || Row.LeaveWeight<0 || Row.Interpolation<0 || Row.Interpolation>2 || Row.TangentMode<0 || Row.TangentMode>4 || Row.WeightMode<0 || Row.WeightMode>3) throw std::runtime_error("Rich keys require strictly ordered in-range times, finite bounded data and valid native modes");
  FRichCurveKey Key(Row.Time,Row.Value); Key.InterpMode=ERichCurveInterpMode(Row.Interpolation); Key.TangentMode=ERichCurveTangentMode(Row.TangentMode); Key.TangentWeightMode=ERichCurveTangentWeightMode(Row.WeightMode); Key.ArriveTangent=Row.ArriveTangent; Key.LeaveTangent=Row.LeaveTangent; Key.ArriveTangentWeight=Row.ArriveWeight; Key.LeaveTangentWeight=Row.LeaveWeight; Keys.Add(Key); Previous=Row.Time;
 }
 bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Replace Rich Float Curve"))); Sequence->Modify(); const FAnimationCurveIdentifier Identifier(Name,ERawCurveTrackTypes::RCT_Float); if(!Controller.SetCurveKeys(Identifier,Keys)) throw std::runtime_error("Native controller rejected rich curve keys"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Rich curve replaced but animation save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("requested_key_count"),Keys.Num()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("replaced"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Replaces existing source float curve keys through native controller; automatic tangent recalculation follows engine behavior. Extrapolation and curve metadata are unchanged.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::SetFloatCurveExtrapolation(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.PreExtrapolation<0 || R.PreExtrapolation>4 || R.PostExtrapolation<0 || R.PostExtrapolation>4) throw std::runtime_error("Curve extrapolation requires stopped PIE, confirmed /Game sequence and native modes [0,4]");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing float curve required");
 const int32 BeforePre=int32(Existing->FloatCurve.PreInfinityExtrap),BeforePost=int32(Existing->FloatCurve.PostInfinityExtrap); const bool Changed=BeforePre!=R.PreExtrapolation || BeforePost!=R.PostExtrapolation; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Float Curve Extrapolation"))); Sequence->Modify(); FCurveAttributes Attributes; Attributes.SetPreExtrapolation(ERichCurveExtrapolation(R.PreExtrapolation)); Attributes.SetPostExtrapolation(ERichCurveExtrapolation(R.PostExtrapolation)); if(!Controller.SetCurveAttributes(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),Attributes)) throw std::runtime_error("Native controller rejected extrapolation attributes"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Extrapolation edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),R.CurveName); J->WriteValue(TEXT("before_pre"),BeforePre); J->WriteValue(TEXT("before_post"),BeforePost); J->WriteValue(TEXT("requested_pre"),R.PreExtrapolation); J->WriteValue(TEXT("requested_post"),R.PostExtrapolation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::EvaluateFloatCurve(const UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !IsValid(Sequence) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Times.IsEmpty() || R.Times.Num()>512 || !FMath::IsFinite(R.DefaultValue) || FMath::Abs(R.DefaultValue)>1.e8) throw std::runtime_error("Curve evaluation requires sequence, bounded curve name, 1..512 times and finite default");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Curve=nullptr; for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing float curve required");
 for(const float Time:R.Times) if(!FMath::IsFinite(Time) || FMath::Abs(Time)>1.e6) throw std::runtime_error("Evaluation times must be finite within [-1000000,1000000]");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("key_count"),Curve->FloatCurve.GetNumKeys()); J->WriteArrayStart(TEXT("samples"));
 for(const float Time:R.Times) { const float Value=Curve->FloatCurve.Eval(Time,R.DefaultValue); J->WriteObjectStart(); J->WriteValue(TEXT("time"),Time); J->WriteValue(TEXT("finite"),FMath::IsFinite(Value)); if(FMath::IsFinite(Value)) J->WriteValue(TEXT("value"),Value); else J->WriteNull(TEXT("value")); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native source FRichCurve evaluation with interpolation/extrapolation/default semantics; not compressed animation, runtime curve blending or material/morph evaluation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::DuplicateFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Curve duplication requires stopped PIE, confirmed /Game sequence and bounded source/destination names");
 const FName Source(*R.CurveName),Destination(*R.NewName); if(Source.IsNone() || Destination.IsNone() || Source==Destination) throw std::runtime_error("Curve names must be distinct and non-None");
 const auto* Model=Sequence->GetDataModel(); if(!Model || Model->GetFloatCurves().Num()>=1024) throw std::runtime_error("Source data model required with <1024 float curves"); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) { if(Curve.GetName()==Destination) throw std::runtime_error("Destination float curve already exists"); if(Curve.GetName()==Source) Existing=&Curve; } if(!Existing || Existing->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Source float curve required with <=4096 keys"); const int32 KeyCount=Existing->FloatCurve.GetNumKeys(); const FLinearColor SourceColor=Existing->GetColor(); const FString SourceComment=Existing->Comment; if(SourceComment.Len()>4096) throw std::runtime_error("Source comment exceeds bounded duplication metadata"); for(float Value:{SourceColor.R,SourceColor.G,SourceColor.B,SourceColor.A}) if(!FMath::IsFinite(Value)) throw std::runtime_error("Source curve display color is nonfinite"); bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Duplicate Float Curve"))); Sequence->Modify(); if(!Controller.DuplicateCurve(FAnimationCurveIdentifier(Source,ERawCurveTrackTypes::RCT_Float),FAnimationCurveIdentifier(Destination,ERawCurveTrackTypes::RCT_Float))) throw std::runtime_error("Native controller rejected curve duplication"); const FAnimationCurveIdentifier NewId(Destination,ERawCurveTrackTypes::RCT_Float); if(!Controller.SetCurveColor(NewId,SourceColor) || !Controller.SetCurveComment(NewId,SourceComment)) throw std::runtime_error("Curve duplicated but editor metadata copy failed; inspect undo transaction"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve duplicated but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("source_curve"),Source.ToString()); J->WriteValue(TEXT("new_curve"),Destination.ToString()); J->WriteValue(TEXT("key_count"),KeyCount); J->WriteValue(TEXT("editor_metadata_copied"),!R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native source float curve duplication; Skeleton curve metadata and external consumer names are not copied or migrated explicitly.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::RenameFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Curve rename requires stopped PIE, confirmed /Game sequence and bounded source/destination names");
 const FName Source(*R.CurveName),Destination(*R.NewName); if(Source.IsNone() || Destination.IsNone() || Source==Destination) throw std::runtime_error("Curve names must be distinct and non-None");
 const auto* Model=Sequence->GetDataModel(); if(!Model || Model->GetFloatCurves().Num()>1024) throw std::runtime_error("Source data model required with <=1024 float curves"); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) { if(Curve.GetName()==Destination) throw std::runtime_error("Destination float curve already exists"); if(Curve.GetName()==Source) Existing=&Curve; } if(!Existing || Existing->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Source float curve required with <=4096 keys"); const int32 KeyCount=Existing->FloatCurve.GetNumKeys(); bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Rename Float Curve"))); Sequence->Modify(); if(!Controller.RenameCurve(FAnimationCurveIdentifier(Source,ERawCurveTrackTypes::RCT_Float),FAnimationCurveIdentifier(Destination,ERawCurveTrackTypes::RCT_Float))) throw std::runtime_error("Native controller rejected curve rename"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve renamed but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("source_curve"),Source.ToString()); J->WriteValue(TEXT("new_curve"),Destination.ToString()); J->WriteValue(TEXT("key_count"),KeyCount); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("renamed"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native source float curve rename; Skeleton curve metadata and external consumer names are not copied or migrated explicitly.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::SetFloatCurveFlag(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128) throw std::runtime_error("Curve flag editing requires stopped PIE, confirmed /Game sequence and bounded curve name");
 EAnimAssetCurveFlags Flag; if(R.Flag==TEXT("Editable")) Flag=AACF_Editable; else if(R.Flag==TEXT("Metadata")) Flag=AACF_Metadata; else if(R.Flag==TEXT("Disabled")) Flag=AACF_Disabled; else throw std::runtime_error("Supported curve flags are Editable, Metadata and Disabled");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing float curve required");
 const int32 Before=Existing->GetCurveTypeFlags(); const bool Changed=((Before & int32(Flag))!=0)!=R.bFlagEnabled; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Float Curve Flag"))); Sequence->Modify(); if(!Controller.SetCurveFlag(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),Flag,R.bFlagEnabled)) throw std::runtime_error("Native controller rejected curve flag"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve flag edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("flag"),R.Flag); J->WriteValue(TEXT("enabled"),R.bFlagEnabled); J->WriteValue(TEXT("before_flags"),Before); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native per-animation curve flag only; Metadata flag is distinct from Skeleton curve metadata. Native controller defines any key-data side effects.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::SetFloatCurveColor(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128) throw std::runtime_error("Curve color editing requires stopped PIE, confirmed /Game sequence and bounded curve name");
 for(float Channel:{R.Color.R,R.Color.G,R.Color.B,R.Color.A}) if(!FMath::IsFinite(Channel) || Channel<0 || Channel>1) throw std::runtime_error("Display color channels require finite values [0,1]");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing float curve required");
 const FLinearColor Before=Existing->GetColor(); const bool Changed=Before!=R.Color; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Float Curve Color"))); Sequence->Modify(); if(!Controller.SetCurveColor(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),R.Color)) throw std::runtime_error("Native controller rejected curve color"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve color edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteArrayStart(TEXT("requested_rgba")); for(float Channel:{R.Color.R,R.Color.G,R.Color.B,R.Color.A}) J->WriteValue(Channel); J->WriteArrayEnd(); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native editor display color only; no curve-key or material/morph parameter change.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::EditFloatCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || (R.Operation!=TEXT("set") && R.Operation!=TEXT("remove") && R.Operation!=TEXT("move"))) throw std::runtime_error("Rich key editing requires stopped PIE, confirmed /Game sequence and bounded curve/keys");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing float curve required");
 const auto& Row=R.Key; auto Bounded=[](float Value) { return FMath::IsFinite(Value) && FMath::Abs(Value)<=1.e8; };
 if(!Bounded(Row.Time) || Row.Time<0 || Row.Time>Sequence->GetPlayLength()) throw std::runtime_error("Key time requires finite value within sequence duration");
 FRichCurveKey Key(Row.Time,Row.Value);
 if(R.Operation==TEXT("set"))
 {
  if(!Bounded(Row.Value) || !Bounded(Row.ArriveTangent) || !Bounded(Row.LeaveTangent) || !Bounded(Row.ArriveWeight) || !Bounded(Row.LeaveWeight) || Row.ArriveWeight<0 || Row.LeaveWeight<0 || Row.Interpolation<0 || Row.Interpolation>2 || Row.TangentMode<0 || Row.TangentMode>4 || Row.WeightMode<0 || Row.WeightMode>3) throw std::runtime_error("Rich key requires finite bounded fields and valid modes");
  Key.InterpMode=ERichCurveInterpMode(Row.Interpolation); Key.TangentMode=ERichCurveTangentMode(Row.TangentMode); Key.TangentWeightMode=ERichCurveTangentWeightMode(Row.WeightMode); Key.ArriveTangent=Row.ArriveTangent; Key.LeaveTangent=Row.LeaveTangent; Key.ArriveTangentWeight=Row.ArriveWeight; Key.LeaveTangentWeight=Row.LeaveWeight;
 }
 const auto& Current=Existing->FloatCurve.GetConstRefOfKeys(); bool Found=false; int32 Match=INDEX_NONE; for(int32 Index=0;Index<Current.Num();++Index) if(Current[Index].Time==Row.Time) { Found=true; Match=Index; break; }
 if(Current.Num()>4096 || (R.Operation==TEXT("set") && !Found && Current.Num()>=4096)) throw std::runtime_error("Curve key count exceeds bound");
 if(R.Operation!=TEXT("set") && !Found) throw std::runtime_error("No key matches requested exact native float time");
 TArray<FRichCurveKey> Prepared=Current;
 if(R.Operation==TEXT("set")) { if(Found) Prepared[Match]=Key; else { Prepared.Add(Key); Prepared.Sort([](const FRichCurveKey& A,const FRichCurveKey& B) { return A.Time<B.Time; }); } }
 if(R.Operation==TEXT("move"))
 {
  if(!Bounded(R.NewTime) || R.NewTime<0 || R.NewTime>Sequence->GetPlayLength()) throw std::runtime_error("New key time requires finite value within duration");
  for(int32 Index=0;Index<Current.Num();++Index) if(Index!=Match && Current[Index].Time==R.NewTime) throw std::runtime_error("Move destination already contains a key");
  Prepared[Match].Time=R.NewTime; Prepared.Sort([](const FRichCurveKey& A,const FRichCurveKey& B) { return A.Time<B.Time; });
 }
 bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Edit Rich Float Key"))); Sequence->Modify(); const FAnimationCurveIdentifier Identifier(Name,ERawCurveTrackTypes::RCT_Float); /* Removal also goes through SetCurveKeys with the key dropped: the 5.7 sequencer controller's RemoveCurveKey deletes the
   rich key but can miss the mirrored control-channel key, and the curve is rebuilt from that channel, so the key returned. */
   if(R.Operation==TEXT("remove")) Prepared.RemoveAt(Match); if(!Controller.SetCurveKeys(Identifier,Prepared)) throw std::runtime_error("Native controller rejected rich curve keys"); if(R.Operation==TEXT("remove") && Existing->FloatCurve.GetConstRefOfKeys().ContainsByPredicate([&](const FRichCurveKey& K){ return K.Time==Row.Time; })) throw std::runtime_error("Native removal reported success but the key is still present"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Rich curve replaced but animation save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("operation"),R.Operation); J->WriteValue(TEXT("time"),Row.Time); if(R.Operation==TEXT("move")) J->WriteValue(TEXT("new_time"),R.NewTime); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("submitted"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Edits one existing source float curve key through native controller; automatic tangent recalculation follows engine behavior. Extrapolation and curve metadata are unchanged.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::RichTransformChannelJson(const UAnimSequence* Sequence,FName CurveName,const FString& Channel,int32 Axis,int32 Start,int32 Count)
{
 if(!IsInGameThread() || !IsValid(Sequence) || CurveName.IsNone() || CurveName.ToString().Len()>128 || Start<0 || Count<1 || Count>512) throw std::runtime_error("Rich curve inspection requires sequence, bounded name/start and count [1,512]");
 if(Axis<0 || Axis>2) throw std::runtime_error("Transform channel axis requires 0,1 or 2");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FTransformCurve* Definition=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==CurveName) { Definition=&Candidate; break; } if(!Definition) throw std::runtime_error("Transform curve does not exist");
 const FRichCurve* Curve=nullptr; if(Channel==TEXT("translation")) Curve=&Definition->TranslationCurve.FloatCurves[Axis]; else if(Channel==TEXT("rotation")) Curve=&Definition->RotationCurve.FloatCurves[Axis]; else if(Channel==TEXT("scale")) Curve=&Definition->ScaleCurve.FloatCurves[Axis]; else throw std::runtime_error("Channel requires translation, rotation or scale");
 const auto& Keys=Curve->GetConstRefOfKeys(); if(Start>Keys.Num()) throw std::runtime_error("Start exceeds curve key count");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),CurveName.ToString()); J->WriteValue(TEXT("channel"),Channel); J->WriteValue(TEXT("axis"),Axis); J->WriteValue(TEXT("key_count"),Keys.Num()); J->WriteValue(TEXT("curve_flags"),Definition->GetCurveTypeFlags()); const auto Color=Definition->GetColor(); J->WriteArrayStart(TEXT("color_rgba")); for(float Channel:{Color.R,Color.G,Color.B,Color.A}) { if(FMath::IsFinite(Channel)) J->WriteValue(Channel); else J->WriteNull(); } J->WriteArrayEnd(); J->WriteValue(TEXT("start"),Start); J->WriteValue(TEXT("truncated"),Keys.Num()-Start>Count); J->WriteValue(TEXT("pre_extrapolation"),int32(Curve->PreInfinityExtrap)); J->WriteValue(TEXT("post_extrapolation"),int32(Curve->PostInfinityExtrap)); J->WriteArrayStart(TEXT("keys"));
 for(int32 Index=Start;Index<Keys.Num() && Index-Start<Count;++Index)
 {
  const auto& Key=Keys[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("index"),Index); auto Number=[&](const TCHAR* Name,float Value) { if(FMath::IsFinite(Value)) J->WriteValue(Name,Value); else J->WriteNull(Name); }; Number(TEXT("time"),Key.Time); Number(TEXT("value"),Key.Value); Number(TEXT("arrive_tangent"),Key.ArriveTangent); Number(TEXT("leave_tangent"),Key.LeaveTangent); Number(TEXT("arrive_weight"),Key.ArriveTangentWeight); Number(TEXT("leave_weight"),Key.LeaveTangentWeight); J->WriteValue(TEXT("interpolation"),int32(Key.InterpMode)); J->WriteValue(TEXT("tangent_mode"),int32(Key.TangentMode)); J->WriteValue(TEXT("weight_mode"),int32(Key.TangentWeightMode)); J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::ReplaceRichTransformChannel(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Keys.Num()>4096) throw std::runtime_error("Rich curve replacement requires stopped PIE, confirmed /Game sequence and bounded curve/keys");
 if(R.Axis<0 || R.Axis>2) throw std::runtime_error("Axis requires 0,1 or 2"); ETransformCurveChannel Channel;
 if(R.Channel==TEXT("translation")) Channel=ETransformCurveChannel::Position; else if(R.Channel==TEXT("rotation")) Channel=ETransformCurveChannel::Rotation; else if(R.Channel==TEXT("scale")) Channel=ETransformCurveChannel::Scale; else throw std::runtime_error("Channel requires translation, rotation or scale");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); bool Found=false; for(const auto& Curve:Model->GetCurveData().TransformCurves) if(Curve.GetName()==Name) Found=true; if(!Found) throw std::runtime_error("Existing transform curve required");
 TArray<FRichCurveKey> Keys; float Previous=-1.f;
 for(const auto& Row:R.Keys)
 {
  auto Bounded=[](float Value) { return FMath::IsFinite(Value) && FMath::Abs(Value)<=1.e8; };
  if(!Bounded(Row.Time) || Row.Time<0 || Row.Time>Sequence->GetPlayLength() || Row.Time<=Previous || !Bounded(Row.Value) || !Bounded(Row.ArriveTangent) || !Bounded(Row.LeaveTangent) || !Bounded(Row.ArriveWeight) || !Bounded(Row.LeaveWeight) || Row.ArriveWeight<0 || Row.LeaveWeight<0 || Row.Interpolation<0 || Row.Interpolation>2 || Row.TangentMode<0 || Row.TangentMode>4 || Row.WeightMode<0 || Row.WeightMode>3) throw std::runtime_error("Rich keys require strictly ordered in-range times, finite bounded data and valid native modes");
  FRichCurveKey Key(Row.Time,Row.Value); Key.InterpMode=ERichCurveInterpMode(Row.Interpolation); Key.TangentMode=ERichCurveTangentMode(Row.TangentMode); Key.TangentWeightMode=ERichCurveTangentWeightMode(Row.WeightMode); Key.ArriveTangent=Row.ArriveTangent; Key.LeaveTangent=Row.LeaveTangent; Key.ArriveTangentWeight=Row.ArriveWeight; Key.LeaveTangentWeight=Row.LeaveWeight; Keys.Add(Key); Previous=Row.Time;
 }
 bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Replace Transform Curve Channel"))); Sequence->Modify(); FAnimationCurveIdentifier Identifier(Name,ERawCurveTrackTypes::RCT_Transform); Identifier.Channel=Channel; Identifier.Axis=EVectorCurveChannel(R.Axis); if(!Controller.SetCurveKeys(Identifier,Keys)) throw std::runtime_error("Native controller rejected rich curve keys"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Rich curve replaced but animation save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("channel"),R.Channel); J->WriteValue(TEXT("axis"),R.Axis); J->WriteValue(TEXT("requested_key_count"),Keys.Num()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("replaced"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Replaces one source transform curve channel rich keys through native controller; automatic tangent recalculation follows engine behavior. Extrapolation and curve metadata are unchanged.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::EvaluateTransformChannel(const UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !IsValid(Sequence) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Times.IsEmpty() || R.Times.Num()>512 || !FMath::IsFinite(R.DefaultValue) || FMath::Abs(R.DefaultValue)>1.e8) throw std::runtime_error("Curve evaluation requires sequence, bounded curve name, 1..512 times and finite default");
 if(R.Axis<0 || R.Axis>2) throw std::runtime_error("Axis requires 0,1 or 2");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FName Name(*R.CurveName); const FTransformCurve* Definition=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Definition=&Candidate; break; } if(!Definition) throw std::runtime_error("Existing transform curve required");
 const FRichCurve* Curve=nullptr; if(R.Channel==TEXT("translation")) Curve=&Definition->TranslationCurve.FloatCurves[R.Axis]; else if(R.Channel==TEXT("rotation")) Curve=&Definition->RotationCurve.FloatCurves[R.Axis]; else if(R.Channel==TEXT("scale")) Curve=&Definition->ScaleCurve.FloatCurves[R.Axis]; else throw std::runtime_error("Channel requires translation, rotation or scale");
 for(const float Time:R.Times) if(!FMath::IsFinite(Time) || FMath::Abs(Time)>1.e6) throw std::runtime_error("Evaluation times must be finite within [-1000000,1000000]");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("channel"),R.Channel); J->WriteValue(TEXT("axis"),R.Axis); J->WriteValue(TEXT("key_count"),Curve->GetNumKeys()); J->WriteArrayStart(TEXT("samples"));
 for(const float Time:R.Times) { const float Value=Curve->Eval(Time,R.DefaultValue); J->WriteObjectStart(); J->WriteValue(TEXT("time"),Time); J->WriteValue(TEXT("finite"),FMath::IsFinite(Value)); if(FMath::IsFinite(Value)) J->WriteValue(TEXT("value"),Value); else J->WriteNull(TEXT("value")); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native source transform-channel FRichCurve evaluation with interpolation/extrapolation/default semantics; not compressed animation, runtime curve blending or material/morph evaluation.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::SetTransformChannelExtrapolation(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.PreExtrapolation<0 || R.PreExtrapolation>4 || R.PostExtrapolation<0 || R.PostExtrapolation>4) throw std::runtime_error("Curve extrapolation requires stopped PIE, confirmed /Game sequence and native modes [0,4]");
 if(R.Axis<0 || R.Axis>2) throw std::runtime_error("Axis requires 0,1 or 2"); ETransformCurveChannel Channel;
 if(R.Channel==TEXT("translation")) Channel=ETransformCurveChannel::Position; else if(R.Channel==TEXT("rotation")) Channel=ETransformCurveChannel::Rotation; else if(R.Channel==TEXT("scale")) Channel=ETransformCurveChannel::Scale; else throw std::runtime_error("Channel requires translation, rotation or scale");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FName Name(*R.CurveName); const FTransformCurve* Definition=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Definition=&Candidate; break; } if(!Definition) throw std::runtime_error("Existing transform curve required");
 const FRichCurve* Existing=Channel==ETransformCurveChannel::Position ? &Definition->TranslationCurve.FloatCurves[R.Axis] : Channel==ETransformCurveChannel::Rotation ? &Definition->RotationCurve.FloatCurves[R.Axis] : &Definition->ScaleCurve.FloatCurves[R.Axis];
 FAnimationCurveIdentifier Identifier(Name,ERawCurveTrackTypes::RCT_Transform); Identifier.Channel=Channel; Identifier.Axis=EVectorCurveChannel(R.Axis);
 const int32 BeforePre=int32(Existing->PreInfinityExtrap),BeforePost=int32(Existing->PostInfinityExtrap); const bool Changed=BeforePre!=R.PreExtrapolation || BeforePost!=R.PostExtrapolation; bool Saved=false; if(Changed) throw std::runtime_error("Transform-channel extrapolation is not supported on UE 5.7: the sequencer animation controller's SetCurveAttributes only edits float curves");
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Transform Channel Extrapolation"))); Sequence->Modify(); FCurveAttributes Attributes; Attributes.SetPreExtrapolation(ERichCurveExtrapolation(R.PreExtrapolation)); Attributes.SetPostExtrapolation(ERichCurveExtrapolation(R.PostExtrapolation)); if(!Controller.SetCurveAttributes(Identifier,Attributes)) throw std::runtime_error("Native controller rejected extrapolation attributes"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Extrapolation edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),R.CurveName); J->WriteValue(TEXT("channel"),R.Channel); J->WriteValue(TEXT("axis"),R.Axis); J->WriteValue(TEXT("before_pre"),BeforePre); J->WriteValue(TEXT("before_post"),BeforePost); J->WriteValue(TEXT("requested_pre"),R.PreExtrapolation); J->WriteValue(TEXT("requested_post"),R.PostExtrapolation); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::EvaluateTransformCurve(const UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !IsValid(Sequence) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Times.IsEmpty() || R.Times.Num()>256 || !FMath::IsFinite(R.BlendWeight) || R.BlendWeight<0 || R.BlendWeight>1) throw std::runtime_error("Transform curve evaluation requires sequence, bounded name, 1..256 times and weight [0,1]");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FTransformCurve* Curve=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==FName(*R.CurveName)) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 for(float Time:R.Times) if(!FMath::IsFinite(Time) || FMath::Abs(Time)>1.e6) throw std::runtime_error("Sample times require finite values within +/-1000000");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),R.CurveName); J->WriteValue(TEXT("blend_weight"),R.BlendWeight); J->WriteArrayStart(TEXT("samples"));
 for(float Time:R.Times)
 {
  const auto Transform=Curve->Evaluate(Time,R.BlendWeight); const auto Q=Transform.GetRotation(); J->WriteObjectStart(); J->WriteValue(TEXT("time"),Time); J->WriteValue(TEXT("finite"),!Transform.ContainsNaN()); auto Number=[&](double Value) { if(FMath::IsFinite(Value)) J->WriteValue(Value); else J->WriteNull(); }; auto Vector=[&](const TCHAR* Name,const FVector& V) { J->WriteArrayStart(Name); Number(V.X); Number(V.Y); Number(V.Z); J->WriteArrayEnd(); }; Vector(TEXT("location"),Transform.GetLocation()); Vector(TEXT("scale"),Transform.GetScale3D()); J->WriteArrayStart(TEXT("quaternion_xyzw")); Number(Q.X); Number(Q.Y); Number(Q.Z); Number(Q.W); J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native FTransformCurve source evaluation and blend-weight semantics, including Euler rotation conversion/default channels; not skeleton/component/world pose or compressed animation evaluation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::CreateTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128) throw std::runtime_error("Transform curve creation requires stopped PIE, confirmed /Game sequence and bounded bone name");
 const FName Name(*R.CurveName); auto* Skeleton=Sequence->GetSkeleton(); if(!IsValid(Skeleton) || Name.IsNone() || Skeleton->GetReferenceSkeleton().FindBoneIndex(Name)==INDEX_NONE) throw std::runtime_error("Transform curve must name existing sequence Skeleton bone");
 const auto* Model=Sequence->GetDataModel(); if(!Model || Model->GetCurveData().TransformCurves.Num()>=1024) throw std::runtime_error("Source model required with <1024 transform curves"); for(const auto& Curve:Model->GetCurveData().TransformCurves) if(Curve.GetName()==Name) throw std::runtime_error("Transform curve already exists"); bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Create Transform Curve"))); Sequence->Modify(); if(!Controller.AddCurve(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform),AACF_Editable|AACF_DriveTrack)) throw std::runtime_error("Native controller rejected transform curve creation"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Transform curve created but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native empty editable drive-track transform curve; no keys or explicit bone-track bake requested. Native model notifications may update derived data.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::RemoveTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128) throw std::runtime_error("Transform curve removal requires stopped PIE, confirmed /Game sequence and bounded bone name");
 const FName Name(*R.CurveName); if(Name.IsNone()) throw std::runtime_error("Curve name cannot be None");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model required"); bool Found=false; int32 KeyCount=0;
 for(const auto& Curve:Model->GetCurveData().TransformCurves) if(Curve.GetName()==Name) { Found=true; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve.GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) KeyCount+=Vector->FloatCurves[Axis].GetNumKeys(); }
 if(!Found) throw std::runtime_error("Existing transform curve required"); bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Remove Transform Curve"))); Sequence->Modify(); if(!Controller.RemoveCurve(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform))) throw std::runtime_error("Native controller rejected transform curve removal"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Transform curve removed but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("removed_key_count"),KeyCount); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("removed"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Removes native source transform curve and all nine channel key sets; does not restore previously baked bone tracks or migrate external references. Native derived-data notifications apply.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::DuplicateTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Curve duplication requires stopped PIE, confirmed /Game sequence and bounded source/destination names");
 const FName Source(*R.CurveName),Destination(*R.NewName); if(Source.IsNone() || Destination.IsNone() || Source==Destination) throw std::runtime_error("Curve names must be distinct and non-None");
 auto* Skeleton=Sequence->GetSkeleton(); if(!IsValid(Skeleton) || Skeleton->GetReferenceSkeleton().FindBoneIndex(Destination)==INDEX_NONE) throw std::runtime_error("Destination must name existing Skeleton bone");
 const auto* Model=Sequence->GetDataModel(); if(!Model || Model->GetCurveData().TransformCurves.Num()>=1024) throw std::runtime_error("Source model required with <1024 transform curves"); const FTransformCurve* Existing=nullptr; for(const auto& Curve:Model->GetCurveData().TransformCurves) { if(Curve.GetName()==Destination) throw std::runtime_error("Destination transform curve already exists"); if(Curve.GetName()==Source) Existing=&Curve; } if(!Existing) throw std::runtime_error("Source transform curve required"); int32 KeyCount=0; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Existing->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { const int32 Count=Vector->FloatCurves[Axis].GetNumKeys(); if(Count>4096) throw std::runtime_error("Source channel exceeds 4096 keys"); KeyCount+=Count; } bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Duplicate Transform Curve"))); Sequence->Modify(); if(!Controller.DuplicateCurve(FAnimationCurveIdentifier(Source,ERawCurveTrackTypes::RCT_Transform),FAnimationCurveIdentifier(Destination,ERawCurveTrackTypes::RCT_Transform))) throw std::runtime_error("Native controller rejected curve duplication"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve duplicated but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("source_curve"),Source.ToString()); J->WriteValue(TEXT("new_curve"),Destination.ToString()); J->WriteValue(TEXT("key_count"),KeyCount); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("created"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native source transform curve duplication; All nine native channels copy to destination bone; no explicit bone-track baking or external consumer migration.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::RenameTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.NewName.IsEmpty() || R.NewName.Len()>128) throw std::runtime_error("Curve rename requires stopped PIE, confirmed /Game sequence and bounded source/destination names");
 const FName Source(*R.CurveName),Destination(*R.NewName); if(Source.IsNone() || Destination.IsNone() || Source==Destination) throw std::runtime_error("Curve names must be distinct and non-None");
 auto* Skeleton=Sequence->GetSkeleton(); if(!IsValid(Skeleton) || Skeleton->GetReferenceSkeleton().FindBoneIndex(Destination)==INDEX_NONE) throw std::runtime_error("Destination must name existing Skeleton bone");
 const auto* Model=Sequence->GetDataModel(); if(!Model || Model->GetCurveData().TransformCurves.Num()>=1024) throw std::runtime_error("Source model required with <1024 transform curves"); const FTransformCurve* Existing=nullptr; for(const auto& Curve:Model->GetCurveData().TransformCurves) { if(Curve.GetName()==Destination) throw std::runtime_error("Destination transform curve already exists"); if(Curve.GetName()==Source) Existing=&Curve; } if(!Existing) throw std::runtime_error("Source transform curve required"); int32 KeyCount=0; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Existing->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { const int32 Count=Vector->FloatCurves[Axis].GetNumKeys(); if(Count>4096) throw std::runtime_error("Source channel exceeds 4096 keys"); KeyCount+=Count; } bool Saved=false;
 if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Rename Transform Curve"))); Sequence->Modify(); if(!Controller.RenameCurve(FAnimationCurveIdentifier(Source,ERawCurveTrackTypes::RCT_Transform),FAnimationCurveIdentifier(Destination,ERawCurveTrackTypes::RCT_Transform))) throw std::runtime_error("Native controller rejected curve rename"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve renamed but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("source_curve"),Source.ToString()); J->WriteValue(TEXT("new_curve"),Destination.ToString()); J->WriteValue(TEXT("key_count"),KeyCount); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("renamed"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native source transform curve rename; All nine native channels move to destination bone; no explicit bone-track baking or external consumer migration.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::SetTransformCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.Key.Time) || R.Key.Time<0 || R.Key.Time>Sequence->GetPlayLength()) throw std::runtime_error("Transform key edit requires stopped PIE, confirmed /Game sequence, bounded curve and in-duration time");
 auto Bounded=[](const FVector& V,double Limit) { return !V.ContainsNaN() && FMath::Abs(V.X)<=Limit && FMath::Abs(V.Y)<=Limit && FMath::Abs(V.Z)<=Limit; };
 if(!Bounded(R.Location,1.e8) || !Bounded(R.Scale,1.e4) || R.Rotation.ContainsNaN() || FMath::Abs(R.Rotation.Pitch)>360000 || FMath::Abs(R.Rotation.Yaw)>360000 || FMath::Abs(R.Rotation.Roll)>360000) throw std::runtime_error("Transform key values require finite bounded data");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FName Name(*R.CurveName); const FTransformCurve* Curve=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { const auto& Keys=Vector->FloatCurves[Axis].GetConstRefOfKeys(); bool Found=false; for(const auto& Key:Keys) if(Key.Time==R.Key.Time) Found=true; if(Keys.Num()>4096 || (!Found && Keys.Num()>=4096)) throw std::runtime_error("Transform channel key count exceeds bound"); }
 bool Saved=false; if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Transform Curve Key"))); Sequence->Modify(); if(!Controller.SetTransformCurveKey(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform),R.Key.Time,FTransform(R.Rotation,R.Location,R.Scale))) throw std::runtime_error("Native controller rejected transform key"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Transform key edited but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("time"),R.Key.Time); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("submitted"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native whole-transform key setter; Euler conversion, key matching and tangent insertion follow engine behavior. Use rich-channel editing for explicit tangents/weights. No explicit bone-track bake.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::RemoveTransformCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.Key.Time) || R.Key.Time<0 || R.Key.Time>Sequence->GetPlayLength()) throw std::runtime_error("Transform key edit requires stopped PIE, confirmed /Game sequence, bounded curve and in-duration time");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation data model unavailable"); const FName Name(*R.CurveName); const FTransformCurve* Curve=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 TArray<FAnimationCurveIdentifier> Matches;
 for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { const auto& Keys=Vector->FloatCurves[Axis].GetConstRefOfKeys(); if(Keys.Num()>4096) throw std::runtime_error("Channel exceeds 4096 keys"); for(const auto& Key:Keys) if(Key.Time==R.Key.Time) { FAnimationCurveIdentifier Id(Name,ERawCurveTrackTypes::RCT_Transform); Id.Channel=ETransformCurveChannel(Channel); Id.Axis=EVectorCurveChannel(Axis); Matches.Add(Id); break; } }
 if(Matches.IsEmpty()) throw std::runtime_error("No transform channel has key at exact native float time");
 bool Saved=false; if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Remove Transform Curve Key"))); Sequence->Modify(); for(const auto& Id:Matches) if(!Controller.RemoveCurveKey(Id,R.Key.Time)) throw std::runtime_error("Native controller rejected transform key"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Transform keys removed but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("time"),R.Key.Time); J->WriteValue(TEXT("matching_channel_count"),Matches.Num()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("submitted"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Removes only matching exact-time keys across nine transform channels via native child controller APIs; sparse channels are preserved. No explicit bone-track bake.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::SetTransformCurveFlag(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128) throw std::runtime_error("Curve flag editing requires stopped PIE, confirmed /Game sequence and bounded curve name");
 EAnimAssetCurveFlags Flag; if(R.Flag==TEXT("Editable")) Flag=AACF_Editable; else if(R.Flag==TEXT("DriveTrack")) Flag=AACF_DriveTrack; else if(R.Flag==TEXT("Disabled")) Flag=AACF_Disabled; else throw std::runtime_error("Supported curve flags are Editable, DriveTrack and Disabled");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FTransformCurve* Existing=nullptr; for(const auto& Curve:Model->GetCurveData().TransformCurves) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing transform curve required");
 const int32 Before=Existing->GetCurveTypeFlags(); const bool Changed=((Before & int32(Flag))!=0)!=R.bFlagEnabled; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Transform Curve Flag"))); Sequence->Modify(); if(!Controller.SetCurveFlag(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform),Flag,R.bFlagEnabled)) throw std::runtime_error("Native controller rejected curve flag"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve flag edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("flag"),R.Flag); J->WriteValue(TEXT("enabled"),R.bFlagEnabled); J->WriteValue(TEXT("before_flags"),Before); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native transform-curve flag only; DriveTrack affects native track workflows. No explicit bone-track bake or restoration requested.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::ReplaceTransformCurveKeys(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.TransformKeys.Num()>4096) throw std::runtime_error("Transform key replacement requires stopped PIE, confirmed /Game sequence and <=4096 keys");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source data model unavailable"); const FName Name(*R.CurveName); bool Found=false; for(const auto& Curve:Model->GetCurveData().TransformCurves) if(Curve.GetName()==Name) Found=true; if(!Found) throw std::runtime_error("Existing transform curve required");
 TArray<FTransform> Values; TArray<float> Times; float Previous=-1.f;
 for(const auto& Row:R.TransformKeys)
 {
  auto Bounded=[](const FVector& V,double Limit) { return !V.ContainsNaN() && FMath::Abs(V.X)<=Limit && FMath::Abs(V.Y)<=Limit && FMath::Abs(V.Z)<=Limit; };
  if(!FMath::IsFinite(Row.Time) || Row.Time<0 || Row.Time>Sequence->GetPlayLength() || Row.Time<=Previous || !Bounded(Row.Location,1.e8) || !Bounded(Row.Scale,1.e4) || Row.Rotation.ContainsNaN() || FMath::Abs(Row.Rotation.Pitch)>360000 || FMath::Abs(Row.Rotation.Yaw)>360000 || FMath::Abs(Row.Rotation.Roll)>360000) throw std::runtime_error("Transform keys require strictly ordered in-duration times and finite bounded transforms");
  Times.Add(Row.Time); Values.Emplace(Row.Rotation,Row.Location,Row.Scale); Previous=Row.Time;
 }
 bool Saved=false; if(!R.bDryRun) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Replace Transform Curve Keys"))); Sequence->Modify(); if(!Controller.SetTransformCurveKeys(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform),Values,Times)) throw std::runtime_error("Native controller rejected transform keys"); } Sequence->MarkPackageDirty(); if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Transform keys replaced but sequence save failed"); } }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("requested_key_count"),Values.Num()); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("replaced"),!R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native transform-key replacement rebuilds all nine channel key sets using native Euler/tangent conventions; previous custom rich tangents are replaced. No explicit bone-track bake.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::TransformCurveKeysJson(const UAnimSequence* Sequence,FName Name,int32 Start,int32 Count,bool bUnionTimeline)
{
 if(!IsInGameThread() || !IsValid(Sequence) || Name.IsNone() || Name.ToString().Len()>128 || Start<0 || Count<1 || Count>256) throw std::runtime_error("Transform key readback requires sequence, bounded name/start and count [1,256]");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FTransformCurve* Curve=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required"); int32 Total=0; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { Total+=Vector->FloatCurves[Axis].GetNumKeys(); if(Total>36864) throw std::runtime_error("Transform curve source keys exceed bounded readback"); }
 TArray<float> Times; TArray<FTransform> Values;
 if(bUnionTimeline) { TSet<float> Unique; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) for(const auto& Key:Vector->FloatCurves[Axis].GetConstRefOfKeys()) { if(!FMath::IsFinite(Key.Time)) throw std::runtime_error("Union timeline contains nonfinite key time"); Unique.Add(Key.Time); } Times=Unique.Array(); Times.Sort(); Values.Reserve(Times.Num()); for(float Time:Times) Values.Add(Curve->Evaluate(Time,1.f)); }
 else Curve->GetKeys(Times,Values); if(Times.Num()!=Values.Num() || Start>Times.Num()) throw std::runtime_error("Native transform key readback mismatch or invalid start");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("key_count"),Times.Num()); J->WriteValue(TEXT("timeline"),bUnionTimeline ? TEXT("union_all_channels") : TEXT("native_densest_channel")); J->WriteValue(TEXT("start"),Start); J->WriteValue(TEXT("truncated"),Times.Num()-Start>Count); J->WriteArrayStart(TEXT("keys"));
 for(int32 Index=Start;Index<Times.Num() && Index-Start<Count;++Index) { const auto& Transform=Values[Index]; const auto Q=Transform.GetRotation(); J->WriteObjectStart(); J->WriteValue(TEXT("index"),Index); auto Number=[&](const TCHAR* Label,double Value) { if(FMath::IsFinite(Value)) J->WriteValue(Label,Value); else J->WriteNull(Label); }; Number(TEXT("time"),Times[Index]); J->WriteValue(TEXT("finite"),!Transform.ContainsNaN()); auto Vector=[&](const TCHAR* Label,const FVector& V) { J->WriteObjectStart(Label); Number(TEXT("X"),V.X); Number(TEXT("Y"),V.Y); Number(TEXT("Z"),V.Z); J->WriteObjectEnd(); }; Vector(TEXT("location"),Transform.GetLocation()); Vector(TEXT("scale"),Transform.GetScale3D()); J->WriteObjectStart(TEXT("quaternion")); Number(TEXT("X"),Q.X); Number(TEXT("Y"),Q.Y); Number(TEXT("Z"),Q.Z); Number(TEXT("W"),Q.W); J->WriteObjectEnd(); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Default native GetKeys selects densest channel times; optional union includes all exact float channel times. Transforms evaluate natively at chosen times. Rich interpolation metadata is available separately by channel.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::MoveTransformCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.Key.Time) || !FMath::IsFinite(R.NewTime) || R.Key.Time<0 || R.NewTime<0 || R.Key.Time>Sequence->GetPlayLength() || R.NewTime>Sequence->GetPlayLength()) throw std::runtime_error("Transform key move requires stopped PIE, confirmed /Game sequence and bounded in-duration times");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FName Name(*R.CurveName); const FTransformCurve* Curve=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 struct FPreparedChannel { FAnimationCurveIdentifier Id; TArray<FRichCurveKey> Keys; }; TArray<FPreparedChannel> Prepared;
 for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis)
 {
  const auto& Keys=Vector->FloatCurves[Axis].GetConstRefOfKeys(); if(Keys.Num()>4096) throw std::runtime_error("Source channel exceeds 4096 keys"); int32 Match=INDEX_NONE; bool Collision=false;
  for(int32 Index=0;Index<Keys.Num();++Index) { if(Keys[Index].Time==R.Key.Time) Match=Index; else if(Keys[Index].Time==R.NewTime) Collision=true; }
  if(Match==INDEX_NONE) continue; if(Collision) throw std::runtime_error("Move destination collides in matching transform channel"); auto& Row=Prepared.AddDefaulted_GetRef(); Row.Id=FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform); Row.Id.Channel=ETransformCurveChannel(Channel); Row.Id.Axis=EVectorCurveChannel(Axis); Row.Keys=Keys; Row.Keys[Match].Time=R.NewTime; Row.Keys.Sort([](const FRichCurveKey& A,const FRichCurveKey& B) { return A.Time<B.Time; });
 }
 if(Prepared.IsEmpty()) throw std::runtime_error("No transform channel key matches exact source time"); const bool Changed=R.Key.Time!=R.NewTime; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Move Transform Curve Key"))); Sequence->Modify(); for(const auto& Row:Prepared) if(!Controller.SetCurveKeys(Row.Id,Row.Keys)) throw std::runtime_error("Native channel move rejected; inspect undo transaction for partial controller failure"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Transform key moved but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("time"),R.Key.Time); J->WriteValue(TEXT("new_time"),R.NewTime); J->WriteValue(TEXT("matching_channel_count"),Prepared.Num()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Moves exact-time keys only in matching channels, retaining supplied rich fields via native key-array setters; automatic tangent behavior remains native. No explicit bone-track bake.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::ResampleTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Times.IsEmpty() || R.Times.Num()>4096) throw std::runtime_error("Transform resampling requires stopped PIE, confirmed /Game sequence and 1..4096 times");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FTransformCurve* Curve=nullptr; for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==FName(*R.CurveName)) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 int32 SourceKeys=0; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { SourceKeys+=Vector->FloatCurves[Axis].GetNumKeys(); if(SourceKeys>36864) throw std::runtime_error("Source key count exceeds 36864"); }
 FAnimationRichCurveReq Prepared=R; Prepared.TransformKeys.Empty(); float Previous=-1.f;
 for(float Time:R.Times)
 {
  if(!FMath::IsFinite(Time) || Time<0 || Time>Sequence->GetPlayLength() || Time<=Previous) throw std::runtime_error("Resample times require strictly ordered values within duration"); const FTransform Transform=Curve->Evaluate(Time,1.f); if(Transform.ContainsNaN()) throw std::runtime_error("Native transform sample is nonfinite"); auto& Key=Prepared.TransformKeys.AddDefaulted_GetRef(); Key.Time=Time; Key.Location=Transform.GetLocation(); Key.Rotation=Transform.Rotator(); Key.Scale=Transform.GetScale3D(); Previous=Time;
 }
 return ReplaceTransformCurveKeys(Sequence,Prepared);
}

FString AnimationSequenceUtils::ResampleFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Times.IsEmpty() || R.Times.Num()>4096 || !FMath::IsFinite(R.DefaultValue) || FMath::Abs(R.DefaultValue)>1.e8) throw std::runtime_error("Float resampling requires stopped PIE, confirmed /Game sequence, bounded default and 1..4096 times");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FFloatCurve* Curve=nullptr; for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==FName(*R.CurveName)) { Curve=&Candidate; break; } if(!Curve || Curve->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Existing float curve with <=4096 keys required");
 FAnimationRichCurveReq Prepared=R; Prepared.Keys.Empty(); float Previous=-1.f;
 for(float Time:R.Times)
 {
  if(!FMath::IsFinite(Time) || Time<0 || Time>Sequence->GetPlayLength() || Time<=Previous) throw std::runtime_error("Resample times require strictly ordered values within duration"); const float Value=Curve->FloatCurve.Eval(Time,R.DefaultValue); if(!FMath::IsFinite(Value) || FMath::Abs(Value)>1.e8) throw std::runtime_error("Native sample exceeds finite value bounds"); auto& Key=Prepared.Keys.AddDefaulted_GetRef(); Key.Time=Time; Key.Value=Value; Key.Interpolation=int32(RCIM_Linear); Key.TangentMode=int32(RCTM_Auto); Previous=Time;
 }
 return ReplaceRichFloatCurve(Sequence,Prepared);
}

FString AnimationSequenceUtils::CurveDiagnosticsJson(const UAnimSequence* Sequence)
{
 if(!IsInGameThread() || !IsValid(Sequence)) throw std::runtime_error("Curve diagnostics require game thread and AnimSequence"); const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable");
 TArray<FString> Issues; int32 IssueCount=0,Channels=0,KeysChecked=0; bool Complete=true; auto Issue=[&](const FString& Text) { ++IssueCount; if(Issues.Num()<128) Issues.Add(Text.Left(1024)); };
 auto Inspect=[&](const FRichCurve& Curve,const FString& Label)
 {
  if(Channels>=1024 || KeysChecked>=65536) { Complete=false; return; } ++Channels; const auto& Keys=Curve.GetConstRefOfKeys(); float Previous=-MAX_flt;
  if(int32(Curve.PreInfinityExtrap)>int32(RCCE_None) || int32(Curve.PostInfinityExtrap)>int32(RCCE_None)) Issue(Label+TEXT(": invalid extrapolation mode"));
  for(int32 Index=0;Index<Keys.Num();++Index)
  {
   if(KeysChecked>=65536) { Complete=false; break; } ++KeysChecked; const auto& Key=Keys[Index]; const FString Prefix=Label+FString::Printf(TEXT(" key %d: "),Index);
   if(!FMath::IsFinite(Key.Time) || Key.Time<0 || Key.Time>Sequence->GetPlayLength()) Issue(Prefix+TEXT("time nonfinite or outside animation duration"));
   if(Index>0 && Key.Time<=Previous) Issue(Prefix+TEXT("times not strictly increasing")); Previous=Key.Time;
   if(!FMath::IsFinite(Key.Value) || !FMath::IsFinite(Key.ArriveTangent) || !FMath::IsFinite(Key.LeaveTangent) || !FMath::IsFinite(Key.ArriveTangentWeight) || !FMath::IsFinite(Key.LeaveTangentWeight)) Issue(Prefix+TEXT("nonfinite value/tangent/weight"));
   if(Key.ArriveTangentWeight<0 || Key.LeaveTangentWeight<0) Issue(Prefix+TEXT("negative tangent weight"));
   if(int32(Key.InterpMode)>int32(RCIM_Cubic) || int32(Key.TangentMode)>int32(RCTM_SmartAuto) || int32(Key.TangentWeightMode)>int32(RCTWM_WeightedBoth)) Issue(Prefix+TEXT("unsupported native rich-key mode"));
  }
 };
 TSet<FName> FloatNames,TransformNames; for(const auto& Curve:Model->GetFloatCurves()) { if(Channels>=1024 || KeysChecked>=65536) { Complete=false; break; } if(Curve.GetName().IsNone() || FloatNames.Contains(Curve.GetName())) Issue(TEXT("Missing/duplicate float curve name")); FloatNames.Add(Curve.GetName()); Inspect(Curve.FloatCurve,Curve.GetName().ToString()); }
 for(const auto& Curve:Model->GetCurveData().TransformCurves) { if(Channels>=1024 || KeysChecked>=65536) { Complete=false; break; } if(Curve.GetName().IsNone() || TransformNames.Contains(Curve.GetName())) Issue(TEXT("Missing/duplicate transform curve name")); TransformNames.Add(Curve.GetName()); for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve.GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) Inspect(Vector->FloatCurves[Axis],Curve.GetName().ToString()+FString::Printf(TEXT("/%d/%d"),Channel,Axis)); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("complete"),Complete); J->WriteValue(TEXT("structurally_valid"),Complete && IssueCount==0); J->WriteValue(TEXT("channels_checked"),Channels); J->WriteValue(TEXT("keys_checked"),KeysChecked); J->WriteValue(TEXT("issue_count"),IssueCount); J->WriteValue(TEXT("issues_truncated"),IssueCount>Issues.Num()); J->WriteArrayStart(TEXT("issues")); for(const auto& Text:Issues) J->WriteValue(Text); J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Bounded source float/transform rich-curve structural checks only; outside-duration keys are flagged for authoring compatibility, not a native runtime validity verdict. No compression, evaluation or mutation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::CurveCatalogJson(const UAnimSequence* Sequence,const FString& Search,int32 Start,int32 Count)
{
 if(!IsInGameThread() || !IsValid(Sequence) || Search.Len()>128 || Start<0 || Count<1 || Count>256) throw std::runtime_error("Curve catalog requires sequence and bounded search/start/count"); const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable");
 struct FRow { FString Name,Type; int32 Flags; int64 Keys; }; TArray<FRow> Rows;
 if(Model->GetFloatCurves().Num()+Model->GetCurveData().TransformCurves.Num()>8192) throw std::runtime_error("Source curve catalog exceeds 8192 curves");
 for(const auto& Curve:Model->GetFloatCurves()) if(Search.IsEmpty() || Curve.GetName().ToString().Contains(Search)) Rows.Add({Curve.GetName().ToString(),TEXT("float"),Curve.GetCurveTypeFlags(),Curve.FloatCurve.GetNumKeys()});
 for(const auto& Curve:Model->GetCurveData().TransformCurves) if(Search.IsEmpty() || Curve.GetName().ToString().Contains(Search)) { int64 Keys=0; for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve.GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) Keys+=Vector->FloatCurves[Axis].GetNumKeys(); Rows.Add({Curve.GetName().ToString(),TEXT("transform"),Curve.GetCurveTypeFlags(),Keys}); }
 Rows.Sort([](const FRow& A,const FRow& B) { return A.Name==B.Name ? A.Type<B.Type : A.Name<B.Name; }); if(Start>Rows.Num()) throw std::runtime_error("Start exceeds filtered curve count");
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("match_count"),Rows.Num()); J->WriteValue(TEXT("start"),Start); J->WriteValue(TEXT("truncated"),Rows.Num()-Start>Count); J->WriteArrayStart(TEXT("curves")); for(int32 Index=Start;Index<Rows.Num() && Index-Start<Count;++Index) { const auto& Row=Rows[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("name"),Row.Name); J->WriteValue(TEXT("type"),Row.Type); J->WriteValue(TEXT("flags"),Row.Flags); J->WriteValue(TEXT("total_channel_key_count"),Row.Keys); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Source float/transform curve catalog; transform key count sums nine channels, not merged timeline length. No curve evaluation or mutation.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::RemoveFloatCurveKeyRange(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.RangeStart) || !FMath::IsFinite(R.RangeEnd) || R.RangeStart<0 || R.RangeEnd<R.RangeStart || R.RangeEnd>Sequence->GetPlayLength()) throw std::runtime_error("Curve range removal requires stopped PIE, confirmed /Game sequence and ordered in-duration range");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FFloatCurve* Curve=nullptr; const FName Name(*R.CurveName); for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve || Curve->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Existing source float curve with <=4096 keys required");
 TArray<FRichCurveKey> Keep; int32 Removed=0; for(const auto& Key:Curve->FloatCurve.GetConstRefOfKeys()) { if(Key.Time>=R.RangeStart && Key.Time<=R.RangeEnd) ++Removed; else Keep.Add(Key); } bool Saved=false;
 if(!R.bDryRun && Removed>0) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Remove Float Curve Key Range"))); Sequence->Modify(); if(!Controller.SetCurveKeys(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),Keep)) throw std::runtime_error("Native controller rejected range removal"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve range edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("range_start"),R.RangeStart); J->WriteValue(TEXT("range_end"),R.RangeEnd); J->WriteValue(TEXT("removed_key_count"),Removed); J->WriteValue(TEXT("remaining_key_count"),Keep.Num()); J->WriteValue(TEXT("would_change"),Removed>0); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Inclusive source key-time removal; retained rich fields copied through native setter, automatic tangents remain engine-defined. No boundary samples inserted or outside-range shape guarantee.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::RemoveTransformCurveKeyRange(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.RangeStart) || !FMath::IsFinite(R.RangeEnd) || R.RangeStart<0 || R.RangeEnd<R.RangeStart || R.RangeEnd>Sequence->GetPlayLength()) throw std::runtime_error("Curve range removal requires stopped PIE, confirmed /Game sequence and ordered in-duration range");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FTransformCurve* Curve=nullptr; const FName Name(*R.CurveName); for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 struct FChannel { FAnimationCurveIdentifier Id; TArray<FRichCurveKey> Keep; int32 Removed=0; }; TArray<FChannel> Prepared; int32 Removed=0,Remaining=0;
 for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis) { const auto& Keys=Vector->FloatCurves[Axis].GetConstRefOfKeys(); if(Keys.Num()>4096) throw std::runtime_error("Source channel exceeds 4096 keys"); auto& Row=Prepared.AddDefaulted_GetRef(); Row.Id=FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform); Row.Id.Channel=ETransformCurveChannel(Channel); Row.Id.Axis=EVectorCurveChannel(Axis); for(const auto& Key:Keys) { if(Key.Time>=R.RangeStart && Key.Time<=R.RangeEnd) ++Row.Removed; else Row.Keep.Add(Key); } Removed+=Row.Removed; Remaining+=Row.Keep.Num(); } bool Saved=false;
 if(!R.bDryRun && Removed>0) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Remove Transform Key Range"))); Sequence->Modify(); for(const auto& Row:Prepared) if(Row.Removed>0 && !Controller.SetCurveKeys(Row.Id,Row.Keep)) throw std::runtime_error("Native controller rejected range removal"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve range edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("range_start"),R.RangeStart); J->WriteValue(TEXT("range_end"),R.RangeEnd); J->WriteValue(TEXT("removed_key_count"),Removed); J->WriteValue(TEXT("remaining_key_count"),Remaining); J->WriteArrayStart(TEXT("channels")); for(const auto& Row:Prepared) { J->WriteObjectStart(); J->WriteValue(TEXT("channel"),int32(Row.Id.Channel)); J->WriteValue(TEXT("axis"),int32(Row.Id.Axis)); J->WriteValue(TEXT("removed_key_count"),Row.Removed); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("would_change"),Removed>0); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Inclusive source key-time removal; retained rich fields copied through native setter, automatic tangents remain engine-defined. No boundary samples inserted or outside-range shape guarantee.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::ScaleFloatCurveTime(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.TimeOrigin) || FMath::Abs(R.TimeOrigin)>1.e6 || !FMath::IsFinite(R.TimeFactor) || R.TimeFactor<0.001f || R.TimeFactor>1000.f) throw std::runtime_error("Curve retiming requires stopped PIE, confirmed /Game sequence, bounded origin and positive factor [0.001,1000]");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FFloatCurve* Curve=nullptr; const FName Name(*R.CurveName); for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve || Curve->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Existing float curve with <=4096 keys required");
 FRichCurve Prepared=Curve->FloatCurve; Prepared.ScaleCurve(R.TimeOrigin,R.TimeFactor); float Previous=-1.f; for(const auto& Key:Prepared.GetConstRefOfKeys()) { if(!FMath::IsFinite(Key.Time) || Key.Time<0 || Key.Time>Sequence->GetPlayLength() || Key.Time<=Previous) throw std::runtime_error("Native retimed keys collide or exceed animation duration"); Previous=Key.Time; }
 const bool Changed=R.TimeFactor!=1.f && Curve->FloatCurve.GetNumKeys()>0; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Scale Float Curve Time"))); Sequence->Modify(); if(!Controller.ScaleCurve(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),R.TimeOrigin,R.TimeFactor)) throw std::runtime_error("Native curve retiming rejected"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve retimed but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("origin"),R.TimeOrigin); J->WriteValue(TEXT("factor"),R.TimeFactor); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native ScaleCurve time mapping on source float curve; tangent/weight semantics and inverse undo follow engine implementation. Animation duration and other tracks unchanged.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::SetFloatCurveComment(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || R.Comment.Len()>4096) throw std::runtime_error("Curve comment editing requires stopped PIE, confirmed /Game sequence and bounded curve name");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Animation source data model unavailable"); const FName Name(*R.CurveName); const FFloatCurve* Existing=nullptr; for(const auto& Curve:Model->GetFloatCurves()) if(Curve.GetName()==Name) { Existing=&Curve; break; } if(!Existing) throw std::runtime_error("Existing float curve required");
 const FString Before=Existing->Comment; const bool Changed=Before!=R.Comment; bool Saved=false;
 if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Float Curve Comment"))); Sequence->Modify(); if(!Controller.SetCurveComment(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),R.Comment)) throw std::runtime_error("Native controller rejected curve comment"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve comment edited but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("comment"),R.Comment); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Native editor curve comment only; no curve-key or material/morph parameter change.")); J->WriteObjectEnd(); J->Close(); return Result;
}


FString AnimationSequenceUtils::FloatCurveRangeJson(const UAnimSequence* Sequence,FName Name)
{
 if(!IsInGameThread() || !IsValid(Sequence) || Name.IsNone() || Name.ToString().Len()>128) throw std::runtime_error("Curve range inspection requires sequence and bounded curve name"); const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FFloatCurve* Curve=nullptr; for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve || Curve->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Existing source float curve with <=4096 keys required");
 bool Finite=true; for(const auto& Key:Curve->FloatCurve.GetConstRefOfKeys()) if(!FMath::IsFinite(Key.Time) || !FMath::IsFinite(Key.Value) || !FMath::IsFinite(Key.ArriveTangent) || !FMath::IsFinite(Key.LeaveTangent) || !FMath::IsFinite(Key.ArriveTangentWeight) || !FMath::IsFinite(Key.LeaveTangentWeight)) Finite=false;
 float MinTime=0,MaxTime=0,MinValue=0,MaxValue=0; const bool Available=Finite && Curve->FloatCurve.GetNumKeys()>0; if(Available) { Curve->FloatCurve.GetTimeRange(MinTime,MaxTime); Curve->FloatCurve.GetValueRange(MinValue,MaxValue); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("key_count"),Curve->FloatCurve.GetNumKeys()); J->WriteValue(TEXT("source_fields_finite"),Finite); J->WriteValue(TEXT("range_available"),Available); auto Number=[&](const TCHAR* Label,float Value) { if(Available && FMath::IsFinite(Value)) J->WriteValue(Label,Value); else J->WriteNull(Label); }; Number(TEXT("min_time"),MinTime); Number(TEXT("max_time"),MaxTime); Number(TEXT("min_value"),MinValue); Number(TEXT("max_value"),MaxValue); J->WriteValue(TEXT("scope"),TEXT("Native FRichCurve time/value range methods over source keys; value range follows engine interpolation implementation, not an exhaustive extrapolation or weighted-curve extrema proof.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::OffsetFloatCurveTime(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.TimeOffset) || FMath::Abs(R.TimeOffset)>1.e6) throw std::runtime_error("Curve offset requires stopped PIE, confirmed /Game sequence and finite bounded offset");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FFloatCurve* Curve=nullptr; const FName Name(*R.CurveName); for(const auto& Candidate:Model->GetFloatCurves()) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve || Curve->FloatCurve.GetNumKeys()>4096) throw std::runtime_error("Existing float curve with <=4096 keys required");
 TArray<FRichCurveKey> Prepared=Curve->FloatCurve.GetConstRefOfKeys(); float Previous=-1.f; bool Changed=false;
 for(auto& Key:Prepared) { const float Time=Key.Time+R.TimeOffset; if(!FMath::IsFinite(Time) || Time<0 || Time>Sequence->GetPlayLength() || Time<=Previous) throw std::runtime_error("Offset keys collide or exceed duration"); Changed |= Time!=Key.Time; Key.Time=Time; Previous=Time; }
 bool Saved=false; if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Offset Float Curve Time"))); Sequence->Modify(); if(!Controller.SetCurveKeys(FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Float),Prepared)) throw std::runtime_error("Native controller rejected curve offset"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve shifted but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("time_offset"),R.TimeOffset); J->WriteValue(TEXT("key_count"),Prepared.Num()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Offsets source key times with float arithmetic; retains rich fields through native setter, whose auto-tangent behavior applies. Other tracks, duration and extrapolation unchanged.")); J->WriteObjectEnd(); J->Close(); return Result;
}

FString AnimationSequenceUtils::OffsetTransformCurveTime(UAnimSequence* Sequence,const FAnimationRichCurveReq& R)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || !R.bConfirm || !IsValid(Sequence) || Sequence->HasAnyFlags(RF_Transient) || !Sequence->GetPathName().StartsWith(TEXT("/Game/")) || R.CurveName.IsEmpty() || R.CurveName.Len()>128 || !FMath::IsFinite(R.TimeOffset) || FMath::Abs(R.TimeOffset)>1.e6) throw std::runtime_error("Curve offset requires stopped PIE, confirmed /Game sequence and finite bounded offset");
 const auto* Model=Sequence->GetDataModel(); if(!Model) throw std::runtime_error("Source model unavailable"); const FTransformCurve* Curve=nullptr; const FName Name(*R.CurveName); for(const auto& Candidate:Model->GetCurveData().TransformCurves) if(Candidate.GetName()==Name) { Curve=&Candidate; break; } if(!Curve) throw std::runtime_error("Existing transform curve required");
 struct FChannel { FAnimationCurveIdentifier Id; TArray<FRichCurveKey> Keys; bool Changed=false; }; TArray<FChannel> Prepared; int32 KeyCount=0,ChangedChannels=0;
 for(int32 Channel=0;Channel<3;++Channel) if(const auto* Vector=Curve->GetVectorCurveByIndex(Channel)) for(int32 Axis=0;Axis<3;++Axis)
 {
  const auto& Keys=Vector->FloatCurves[Axis].GetConstRefOfKeys(); if(Keys.Num()>4096) throw std::runtime_error("Source channel exceeds 4096 keys"); auto& Row=Prepared.AddDefaulted_GetRef(); Row.Id=FAnimationCurveIdentifier(Name,ERawCurveTrackTypes::RCT_Transform); Row.Id.Channel=ETransformCurveChannel(Channel); Row.Id.Axis=EVectorCurveChannel(Axis); Row.Keys=Keys; KeyCount+=Keys.Num(); float Previous=-1.f;
  for(auto& Key:Row.Keys) { const float Time=Key.Time+R.TimeOffset; if(!FMath::IsFinite(Time) || Time<0 || Time>Sequence->GetPlayLength() || Time<=Previous) throw std::runtime_error("Offset channel keys collide or exceed duration"); Row.Changed |= Time!=Key.Time; Key.Time=Time; Previous=Time; } if(Row.Changed) ++ChangedChannels;
 }
 const bool Changed=ChangedChannels>0;
 bool Saved=false; if(!R.bDryRun && Changed) { auto& Controller=Sequence->GetController(); { IAnimationDataController::FScopedBracket Bracket(Controller,FText::FromString(TEXT("MCP Offset Transform Curve Time"))); Sequence->Modify(); for(const auto& Row:Prepared) if(Row.Changed && !Controller.SetCurveKeys(Row.Id,Row.Keys)) throw std::runtime_error("Native controller rejected curve offset"); } Sequence->MarkPackageDirty(); }
 if(!R.bDryRun && R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Sequence,false); if(!Saved) throw std::runtime_error("Curve shifted but sequence save failed"); }
 FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Sequence->GetPathName()); J->WriteValue(TEXT("curve_name"),Name.ToString()); J->WriteValue(TEXT("time_offset"),R.TimeOffset); J->WriteValue(TEXT("key_count"),KeyCount); J->WriteValue(TEXT("changed_channel_count"),ChangedChannels); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("scope"),TEXT("Offsets source key times with float arithmetic; retains rich fields through native setter, whose auto-tangent behavior applies. Other tracks, duration and extrapolation unchanged.")); J->WriteObjectEnd(); J->Close(); return Result;
}
