#pragma once

#include "CoreMinimal.h"

class UAnimSequence;
struct FAnimationAttributeReq;
struct FAnimationBoneTrackReq;
struct FAnimationTimingReq;
struct FAnimationRichCurveReq;

namespace AnimationSequenceUtils
{
	FString EditFloatCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetFloatCurveComment(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetFloatCurveColor(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetTransformCurveFlag(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetFloatCurveFlag(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RenameFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString ResampleFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString ResampleTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString MoveTransformCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RemoveTransformCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString TransformCurveKeysJson(const UAnimSequence* Sequence,FName Name,int32 Start,int32 Count,bool bUnionTimeline=false);
	FString ReplaceTransformCurveKeys(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetTransformCurveKey(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RenameTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString DuplicateTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString DuplicateFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RemoveTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString CreateTransformCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString EvaluateTransformCurve(const UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString EvaluateTransformChannel(const UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString EvaluateFloatCurve(const UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetTransformChannelExtrapolation(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString SetFloatCurveExtrapolation(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString ReplaceRichTransformChannel(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString ReplaceRichFloatCurve(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RichTransformChannelJson(const UAnimSequence* Sequence,FName CurveName,const FString& Channel,int32 Axis,int32 Start,int32 Count);
	FString OffsetTransformCurveTime(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString OffsetFloatCurveTime(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString ScaleFloatCurveTime(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RemoveTransformCurveKeyRange(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString RemoveFloatCurveKeyRange(UAnimSequence* Sequence,const FAnimationRichCurveReq& R);
	FString FloatCurveRangeJson(const UAnimSequence* Sequence,FName Name);
	FString CurveCatalogJson(const UAnimSequence* Sequence,const FString& Search,int32 Start,int32 Count);
	FString CurveDiagnosticsJson(const UAnimSequence* Sequence);
	FString RichFloatCurveJson(const UAnimSequence* Sequence,FName CurveName,int32 Start,int32 Count);
	FString AttributesJson(const UAnimSequence* Sequence);
	bool EditAttribute(UAnimSequence* Sequence, const FAnimationAttributeReq& Request);
	FString BoneTrackJson(const UAnimSequence* Sequence, FName BoneName, int32 StartFrame, int32 Count);
	bool EditBoneTrack(UAnimSequence* Sequence, const FAnimationBoneTrackReq& Request);
	bool EditTiming(UAnimSequence* Sequence, const FAnimationTimingReq& Request);
	void AppendBoneTrackKeyIssues(const UAnimSequence* Sequence, TArray<FString>& Errors);
}
