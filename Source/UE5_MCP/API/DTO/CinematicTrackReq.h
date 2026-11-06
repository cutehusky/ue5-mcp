#pragma once

#include "CoreMinimal.h"
#include "CinematicTrackReq.generated.h"

/** Request for generic Movie Scene track, section, and key authoring. */
USTRUCT()
struct FCinematicTrackReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString BindingGuid;

	UPROPERTY()
	FString TrackClass;

	/** Optional event section subtype for add: trigger (default) or repeater. */
	UPROPERTY()
	FString EventSectionType;

	UPROPERTY()
	int32 TrackIndex = -1;

	UPROPERTY()
	int32 SectionIndex = -1;

	UPROPERTY()
	int32 ChannelIndex = -1;

	UPROPERTY()
	int32 KeyIndex = -1;

	UPROPERTY()
	int32 Frame = 0;

	UPROPERTY()
	int32 EndFrame = 1;

	UPROPERTY()
	int32 RowIndex = 0;

	UPROPERTY()
	double Value = 0.0;

	UPROPERTY()
	FString Interpolation = TEXT("auto");

	UPROPERTY()
	FString PropertyName;

	UPROPERTY()
	FString PropertyPath;

	/** Sound or animation asset used when adding an audio or skeletal-animation section. */
	UPROPERTY()
	FString SourceAssetPath;

	/** Skeletal Mesh used to validate an animation section's Skeleton. */
	UPROPERTY()
	FString TargetSkeletalMeshPath;

	UPROPERTY()
	bool bSetAnimationPlayRate = false;

	UPROPERTY()
	double AnimationPlayRate = 1.0;

	UPROPERTY()
	bool bSetAnimationReverse = false;

	UPROPERTY()
	bool bAnimationReverse = false;

	UPROPERTY()
	bool bSetAnimationSlotName = false;

	UPROPERTY()
	FString AnimationSlotName;

	UPROPERTY()
	bool bSetAnimationSkipNotifiers = false;

	UPROPERTY()
	bool bAnimationSkipNotifiers = false;

	UPROPERTY()
	bool bSetAnimationForceCustomMode = false;

	UPROPERTY()
	bool bAnimationForceCustomMode = false;

	UPROPERTY()
	bool bSetAnimationFirstLoopStartOffset = false;

	/** Offsets are Movie Scene tick-resolution frames. */
	UPROPERTY()
	int32 AnimationFirstLoopStartOffset = 0;

	UPROPERTY()
	bool bSetAnimationStartOffset = false;

	UPROPERTY()
	int32 AnimationStartOffset = 0;

	UPROPERTY()
	bool bSetAnimationEndOffset = false;

	UPROPERTY()
	int32 AnimationEndOffset = 0;

	UPROPERTY()
	bool bSetAudioStartOffset = false;

	UPROPERTY()
	int32 AudioStartOffset = 0;

	UPROPERTY()
	bool bSetAudioLooping = false;

	UPROPERTY()
	bool bAudioLooping = false;

	UPROPERTY()
	bool bSetAudioSuppressSubtitles = false;

	UPROPERTY()
	bool bAudioSuppressSubtitles = false;

	UPROPERTY()
	bool bSetAudioOverrideAttenuation = false;

	UPROPERTY()
	bool bAudioOverrideAttenuation = false;

	UPROPERTY()
	bool bSetAudioAttenuationSettings = false;

	UPROPERTY()
	FString AudioAttenuationPath;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bSave = false;

	UPROPERTY()
	bool bConfirm = false;
};
