#include "AssetRoute.h"
#include "UE5_MCP/Core/TakeMetadataUtils.h"
#include "UE5_MCP/API/DTO/EditorExtReq.h"
#include "UE5_MCP/Core/WidgetAnimationUtils.h"
#include "UE5_MCP/Core/AssetConsolidationUtils.h"
#include "UE5_MCP/Core/GameFeatureUtils.h"
#include "UE5_MCP/Core/SmartObjectUtils.h"
#include "UE5_MCP/Core/EditorUtilityUtils.h"
#include "UE5_MCP/Core/SequenceBindingTagUtils.h"
#include "UE5_MCP/Core/SequenceFolderUtils.h"
#include "Sections/MovieSceneEventRepeaterSection.h"
#include "Tracks/MovieSceneEventTrack.h"
#include "UE5_MCP/Core/SequenceChannelUtils.h"
#include "UE5_MCP/Core/MaterialMetadataUtils.h"
#include "UE5_MCP/API/DTO/RenderTargetReq.h"
#include "UE5_MCP/Core/RenderTargetUtils.h"
#include "UE5_MCP/API/DTO/DecalReq.h"
#include "UE5_MCP/Core/DecalUtils.h"
#include "UE5_MCP/API/DTO/WorldPartitionReq.h"
#include "UE5_MCP/Core/WorldPartitionUtils.h"
#include "UE5_MCP/API/DTO/FoliageReq.h"
#include "UE5_MCP/Core/FoliageUtils.h"
#include "UE5_MCP/API/DTO/LandscapeReq.h"
#include "UE5_MCP/Core/LandscapeUtils.h"
#include "UE5_MCP/API/DTO/AtmosphereReq.h"
#include "UE5_MCP/Core/AtmosphereUtils.h"
#include "UE5_MCP/API/DTO/CloudReq.h"
#include "UE5_MCP/Core/CloudUtils.h"
#include "UE5_MCP/API/DTO/FogReq.h"
#include "UE5_MCP/Core/FogUtils.h"
#include "UE5_MCP/API/DTO/LightingReq.h"
#include "UE5_MCP/Core/LightingUtils.h"
#include "UE5_MCP/API/DTO/ReflectionCaptureReq.h"
#include "UE5_MCP/Core/ReflectionCaptureUtils.h"
#include "UE5_MCP/API/DTO/VolumeReq.h"
#include "UE5_MCP/Core/VolumeUtils.h"
#include "UE5_MCP/API/DTO/SplineReq.h"
#include "UE5_MCP/Core/SplineUtils.h"
#include "UE5_MCP/API/DTO/GeometryScriptReq.h"
#include "UE5_MCP/Core/GeometryScriptUtils.h"
#include "UE5_MCP/API/DTO/PCGReq.h"
#include "UE5_MCP/Core/PCGUtils.h"
#include "UE5_MCP/API/DTO/NiagaraReq.h"
#include "UE5_MCP/Core/NiagaraUtils.h"
#include "UE5_MCP/API/DTO/PoseSearchReq.h"
#include "UE5_MCP/Core/PoseSearchUtils.h"
#include "UE5_MCP/API/DTO/IKRigReq.h"
#include "UE5_MCP/Core/IKRigUtils.h"
#include "UE5_MCP/API/DTO/AnimationRichCurveReq.h"
#include "UE5_MCP/API/DTO/SkeletonCurveReq.h"
#include "UE5_MCP/API/DTO/CompatibleSkeletonReq.h"
#include "UE5_MCP/API/DTO/BoneRetargetReq.h"
#include "UE5_MCP/API/DTO/VirtualBoneReq.h"
#include "UE5_MCP/API/DTO/SkeletonSocketReq.h"
#include "UE5_MCP/Core/SkeletonUtils.h"
#include "UE5_MCP/Core/StateTreeUtils.h"
#include "UE5_MCP/Core/PerceptionUtils.h"
#include "UE5_MCP/Core/GameplayTagUtils.h"
#include "UE5_MCP/Core/RemoteControlUtils.h"
#include "UE5_MCP/Core/GameCoreUtils.h"
#include "UE5_MCP/Core/DebugFeedbackUtils.h"
#include "UE5_MCP/Core/GraphLayoutUtils.h"
#include "UE5_MCP/API/DTO/GameCoreReq.h"
#include "UE5_MCP/API/DTO/RemoteControlReq.h"
#include "UE5_MCP/Core/AbilitySystemUtils.h"
#include "UE5_MCP/API/DTO/AbilitySystemReq.h"
#include "UE5_MCP/API/DTO/GameplayTagReq.h"
#include "UE5_MCP/API/DTO/PerceptionReq.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "UE5_MCP/Core/EnvironmentQueryRuntimeUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryRuntimeReq.h"
#include "UE5_MCP/Core/EnvironmentQueryUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryReq.h"
#include "UE5_MCP/Core/BlackboardUtils.h"
#include "UE5_MCP/Core/BehaviorTreeGraphUtils.h"
#include "UE5_MCP/API/DTO/BehaviorTreeGraphReq.h"
#include "UE5_MCP/API/DTO/BehaviorTreeRuntimeReq.h"

#include "UE5_MCP/API/DTO/DataTableRowReq.h"
#include "UE5_MCP/API/DTO/BPComponentPropertySetReq.h"
#include "UE5_MCP/API/DTO/AssetParameterReq.h"
#include "UE5_MCP/API/DTO/MaterialInstanceReq.h"
#include "UE5_MCP/API/DTO/MaterialCoreSettingsReq.h"
#include "UE5_MCP/API/DTO/MeshMaterialReq.h"
#include "UE5_MCP/API/DTO/AnimationNotifyReq.h"
#include "UE5_MCP/API/DTO/AnimationSectionReq.h"
#include "UE5_MCP/API/DTO/SkeletalSectionReq.h"
#include "UE5_MCP/API/DTO/AssetActionReq.h"
#include "UE5_MCP/API/DTO/MaterialExpressionReq.h"
#include "UE5_MCP/API/DTO/StaticMeshLodReq.h"
#include "UE5_MCP/API/DTO/StaticMeshSettingsReq.h"
#include "UE5_MCP/API/DTO/WidgetOperationReq.h"
#include "UE5_MCP/API/DTO/AssetPropertyReq.h"
#include "UE5_MCP/API/DTO/AssetBatchReq.h"
#include "UE5_MCP/API/DTO/BlendSpaceReq.h"
#include "UE5_MCP/API/DTO/BlendSpaceSampleIdentityData.h"
#include "UE5_MCP/API/DTO/ControlRigHierarchyReq.h"
#include "UE5_MCP/API/DTO/ControlRigGraphReq.h"
#include "UE5_MCP/API/DTO/ControlRigValidationReq.h"
#include "UE5_MCP/API/DTO/ModularRigReq.h"
#include "UE5_MCP/API/DTO/AnimationCreateReq.h"
#include "UE5_MCP/API/DTO/AnimationCompressionReq.h"
#include "UE5_MCP/API/DTO/AnimationAttributeReq.h"
#include "UE5_MCP/API/DTO/AnimationBoneTrackReq.h"
#include "UE5_MCP/API/DTO/AnimationTimingReq.h"
#include "UE5_MCP/API/DTO/AnimationBlueprintGraphReq.h"
#include "UE5_MCP/API/DTO/AnimationTransitionReq.h"
#include "UE5_MCP/API/DTO/AnimationPoseLinkReq.h"
#include "UE5_MCP/API/DTO/AnimationStateMachineReq.h"
#include "UE5_MCP/API/DTO/TextureImportReq.h"
#include "UE5_MCP/API/DTO/SoundWaveImportReq.h"
#include "UE5_MCP/API/DTO/AudioAttenuationCreateReq.h"
#include "UE5_MCP/API/DTO/AudioAttenuationSettingsReq.h"
#include "UE5_MCP/API/DTO/DialogueReq.h"
#include "UE5_MCP/API/DTO/QuartzReq.h"
#include "UE5_MCP/API/DTO/AudioDiagnosticReq.h"
#include "UE5_MCP/API/DTO/AudioTraceReq.h"
#include "UE5_MCP/Core/AudioTraceUtils.h"
#include "UE5_MCP/Core/AudioDiagnosticUtils.h"
#include "UE5_MCP/API/DTO/QuartzEventReq.h"
#include "UE5_MCP/API/DTO/AudioComponentSettingsReq.h"
#include "UE5_MCP/Core/AudioComponentUtils.h"
#include "UE5_MCP/API/DTO/ModulationReq.h"
#include "UE5_MCP/API/DTO/ModulationAuthoringReq.h"
#include "UE5_MCP/API/DTO/ModulationRuntimeReq.h"
#include "UE5_MCP/API/DTO/ModulationRecordingReq.h"
#include "UE5_MCP/Core/ModulationRecordingUtils.h"
#include "UE5_MCP/API/DTO/ModulationProfileReq.h"
#include "UE5_MCP/API/DTO/ModulationFileReq.h"
#include "UE5_MCP/API/DTO/AudioConcurrencyCreateReq.h"
#include "UE5_MCP/API/DTO/AudioWaveSettingsReq.h"
#include "UE5_MCP/API/DTO/AudioWaveRebuildReq.h"
#include "UE5_MCP/API/DTO/SoundClassSettingsReq.h"
#include "UE5_MCP/API/DTO/SoundMixSettingsReq.h"
#include "UE5_MCP/API/DTO/SoundSubmixSettingsReq.h"
#include "UE5_MCP/API/DTO/SoundCueCreateReq.h"
#include "UE5_MCP/API/DTO/SoundCueGraphReq.h"
#include "UE5_MCP/API/DTO/MetaSoundCreateReq.h"
#include "UE5_MCP/API/DTO/MetaSoundGraphReq.h"
#include "UE5_MCP/API/DTO/StaticMeshImportReq.h"
#include "UE5_MCP/API/DTO/DataAssetCreateReq.h"
#include "UE5_MCP/API/DTO/InputMappingReq.h"
#include "UE5_MCP/API/DTO/AIAssetCreateReq.h"
#include "UE5_MCP/API/DTO/BlackboardKeyReq.h"
#include "UE5_MCP/API/DTO/SequenceCreateReq.h"
#include "UE5_MCP/API/DTO/SequencePlaybackReq.h"
#include "UE5_MCP/API/DTO/CinematicSectionReq.h"
#include "UE5_MCP/API/DTO/CinematicBindingReq.h"
#include "UE5_MCP/API/DTO/CinematicTrackReq.h"
#include "UE5_MCP/API/DTO/CinematicCameraReq.h"
#include "UE5_MCP/API/DTO/PhysicsAssetEditReq.h"
#include "UE5_MCP/API/DTO/PhysicsConstraintReq.h"
#include "UE5_MCP/API/DTO/PhysicsDriveReq.h"
#include "UE5_MCP/API/DTO/PhysicsProfileReq.h"
#include "UE5_MCP/API/DTO/PhysicsBodyProfileReq.h"
#include "UE5_MCP/API/DTO/PhysicsBodySettingsReq.h"
#include "UE5_MCP/API/Interface/DTO/ActionResponse.h"
#include "UE5_MCP/Core/ObjUtils.h"
#include "UE5_MCP/Core/BPUtils.h"
#include "UE5_MCP/Core/ClassUtils.h"
#include "UE5_MCP/Core/AnimationSequenceUtils.h"
#include "UE5_MCP/Core/AnimationBlueprintUtils.h"
#include "UE5_MCP/Core/TextureImportUtils.h"
#include "UE5_MCP/Core/SoundWaveImportUtils.h"
#include "UE5_MCP/Core/MetaSoundGraphUtils.h"
#include "UE5_MCP/Core/AudioTypedSettingsUtils.h"
#include "UE5_MCP/Core/SoundAttenuationUtils.h"
#include "UE5_MCP/Core/DialogueUtils.h"
#include "UE5_MCP/Core/QuartzUtils.h"
#include "UE5_MCP/Core/QuartzEventUtils.h"
#include "UE5_MCP/Core/ModulationUtils.h"
#include "UE5_MCP/Core/ModulationAuthoringUtils.h"
#include "UE5_MCP/Core/ModulationRuntimeUtils.h"
#include "UE5_MCP/Core/ModulationProfileUtils.h"
#include "UE5_MCP/Core/ModulationFileUtils.h"
#include "SoundModulationPatch.h"
#include "UE5_MCP/Core/StaticMeshImportUtils.h"

#include "Blueprint/UserWidget.h"
#include "Engine/DataTable.h"
#include "Engine/DataAsset.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "EnhancedActionKeyMapping.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType.h"
#include "Sound/SoundWave.h"
#include "Sound/SoundCue.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundMix.h"
#include "Sound/SoundSubmix.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundConcurrency.h"
#include "Sound/DialogueVoice.h"
#include "Sound/DialogueWave.h"
#include "Sound/SoundNode.h"
#include "Sound/SoundNodeAttenuation.h"
#include "Sound/SoundNodeWavePlayer.h"
#include "Engine/World.h"
#include "JsonObjectConverter.h"
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimData/AttributeIdentifier.h"
#include "Animation/AnimBoneCompressionSettings.h"
#include "Animation/AnimCurveCompressionSettings.h"
#include "Animation/VariableFrameStrippingSettings.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "AnimationBlueprintLibrary.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "SkeletalMeshEditorSubsystem.h"
#include "StaticMeshEditorSubsystem.h"
#include "MaterialEditingLibrary.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpression.h"
#include "Components/PanelWidget.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "AssetToolsModule.h"
#include "EditorFramework/AssetImportData.h"
#include "Factories/SoundAttenuationFactory.h"
#include "Factories/SoundConcurrencyFactory.h"
#include "Factories/SoundCueFactoryNew.h"
#include "SoundCueGraph/SoundCueGraph.h"
#include "SoundCueGraph/SoundCueGraphNode.h"
#include "SoundCueGraph/SoundCueGraphNode_Base.h"
#include "SoundCueGraph/SoundCueGraphNode_Root.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "Editor.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "GameFramework/Actor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "CineCameraActor.h"
#include "CineCameraComponent.h"
#include "CineCameraSettings.h"
#include "FileHelpers.h"
#include "Interfaces/IPluginManager.h"
#include "UniversalObjectLocatorResolveParams.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstance.h"
#include "Materials/MaterialParameterCollection.h"
#include "Engine/Texture.h"
#include "Engine/Font.h"
#include "VT/RuntimeVirtualTexture.h"
#include "Animation/BlendSpace.h"
#include "Animation/BlendSpace1D.h"
#include "ControlRigAsset.h"
#include "ControlRig.h"
#include "ControlRigGizmoLibrary.h"
#include "ModularRigController.h"
#include "ModularRigModel.h"
#include "ControlRigOverride.h"
#include "Rigs/RigHierarchy.h"
#include "Rigs/RigHierarchyController.h"
#include "Rigs/RigHierarchyElements.h"
#include "RigVMAsset.h"
#include "RigVMBlueprintLegacy.h"
#include "RigVMModel/RigVMGraph.h"
#include "RigVMModel/RigVMNode.h"
#include "RigVMModel/RigVMLink.h"
#include "RigVMModel/RigVMController.h"
#include "RigVMModel/RigVMPin.h"
#include "RigVMModel/Nodes/RigVMCommentNode.h"
#include "RigVMModel/Nodes/RigVMCollapseNode.h"
#include "RigVMModel/Nodes/RigVMFunctionReferenceNode.h"
#include "RigVMModel/Nodes/RigVMInvokeEntryNode.h"
#include "RigVMModel/Nodes/RigVMLibraryNode.h"
#include "RigVMModel/Nodes/RigVMRerouteNode.h"
#include "RigVMModel/Nodes/RigVMTemplateNode.h"
#include "RigVMModel/Nodes/RigVMUnitNode.h"
#include "RigVMModel/Nodes/RigVMVariableNode.h"
#include "RigVMModel/RigVMFunctionLibrary.h"
#include "RigVMCore/RigVMStruct.h"
#include "RigVMCore/RigVMFunction.h"
#include "RigVMCore/RigVMByteCode.h"
#include "UObject/UnrealType.h"
#include "UObject/Package.h"
#include "Misc/SecureHash.h"
#include "Misc/ScopeExit.h"
#include "Misc/FrameRate.h"
#include "Misc/PackageName.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "PhysicsEngine/PhysicsConstraintTemplate.h"
#include "PhysicsAssetUtils.h"
#include "PreviewScene.h"
#include "LevelSequence.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
#include "MovieScene.h"
#include "MovieSceneBinding.h"
#include "MovieSceneObjectBindingID.h"
#include "MovieSceneTimeHelpers.h"
#include "MovieScenePossessable.h"
#include "MovieSceneSpawnable.h"
#include "MovieSceneSequencePlaybackSettings.h"
#include "MovieSceneSequencePlayer.h"
#include "MovieSceneTrack.h"
#include "MovieSceneSection.h"
#include "Channels/MovieSceneChannelProxy.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Sections/MovieSceneCameraCutSection.h"
#include "Tracks/MovieSceneSubTrack.h"
#include "Sections/MovieSceneSubSection.h"
#include "Tracks/MovieSceneCinematicShotTrack.h"
#include "Sections/MovieSceneCinematicShotSection.h"
#include "Tracks/MovieScenePropertyTrack.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Tracks/MovieSceneVisibilityTrack.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "Tracks/MovieSceneByteTrack.h"
#include "Tracks/MovieSceneIntegerTrack.h"
#include "Tracks/MovieSceneObjectPropertyTrack.h"
#include "Tracks/MovieSceneFadeTrack.h"
#include "Tracks/MovieSceneAudioTrack.h"
#include "Sections/MovieSceneAudioSection.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Sound/SoundBase.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/Skeleton.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "ScopedTransaction.h"
#include "UObject/UnrealType.h"
#include "Channels/MovieSceneChannel.h"
#include "Channels/MovieSceneChannelProxy.h"
#include "Channels/MovieSceneFloatChannel.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "Channels/MovieSceneIntegerChannel.h"
#include "Channels/MovieSceneBoolChannel.h"
#include "Channels/MovieSceneByteChannel.h"

namespace
{
	ERigElementType ParseRigElementType(const FString& Type)
	{
		if (Type.Equals(TEXT("bone"), ESearchCase::IgnoreCase)) return ERigElementType::Bone;
		if (Type.Equals(TEXT("null"), ESearchCase::IgnoreCase)) return ERigElementType::Null;
		if (Type.Equals(TEXT("control"), ESearchCase::IgnoreCase)) return ERigElementType::Control;
		if (Type.Equals(TEXT("curve"), ESearchCase::IgnoreCase)) return ERigElementType::Curve;
		if (Type.Equals(TEXT("socket"), ESearchCase::IgnoreCase)) return ERigElementType::Socket;
		if (Type.Equals(TEXT("connector"), ESearchCase::IgnoreCase)) return ERigElementType::Connector;
		if (Type.Equals(TEXT("reference"), ESearchCase::IgnoreCase)) return ERigElementType::Reference;
		throw std::runtime_error("element_type must be bone, null, control, curve, socket, connector, or reference");
	}

	FString RigElementTypeName(ERigElementType Type)
	{
		switch (Type)
		{
		case ERigElementType::Bone: return TEXT("bone");
		case ERigElementType::Null: return TEXT("null");
		case ERigElementType::Control: return TEXT("control");
		case ERigElementType::Curve: return TEXT("curve");
		case ERigElementType::Socket: return TEXT("socket");
		case ERigElementType::Connector: return TEXT("connector");
		case ERigElementType::Reference: return TEXT("reference");
		default: return TEXT("unknown");
		}
	}

	ERigControlType ParseRigControlType(const FString& Type)
	{
		if (Type.Equals(TEXT("float"), ESearchCase::IgnoreCase)) return ERigControlType::Float;
		if (Type.Equals(TEXT("scale_float"), ESearchCase::IgnoreCase)) return ERigControlType::ScaleFloat;
		if (Type.Equals(TEXT("bool"), ESearchCase::IgnoreCase)) return ERigControlType::Bool;
		if (Type.Equals(TEXT("integer"), ESearchCase::IgnoreCase)) return ERigControlType::Integer;
		if (Type.Equals(TEXT("vector2d"), ESearchCase::IgnoreCase)) return ERigControlType::Vector2D;
		if (Type.Equals(TEXT("position"), ESearchCase::IgnoreCase)) return ERigControlType::Position;
		if (Type.Equals(TEXT("scale"), ESearchCase::IgnoreCase)) return ERigControlType::Scale;
		if (Type.Equals(TEXT("rotator"), ESearchCase::IgnoreCase)) return ERigControlType::Rotator;
		if (Type.Equals(TEXT("transform"), ESearchCase::IgnoreCase)) return ERigControlType::Transform;
		if (Type.Equals(TEXT("transform_no_scale"), ESearchCase::IgnoreCase)) return ERigControlType::TransformNoScale;
		if (Type.Equals(TEXT("euler_transform"), ESearchCase::IgnoreCase)) return ERigControlType::EulerTransform;
		throw std::runtime_error("control_type must be float, scale_float, bool, integer, vector2d, position, scale, rotator, transform, transform_no_scale, or euler_transform");
	}

	FString RigControlTypeName(ERigControlType Type)
	{
		switch (Type)
		{
		case ERigControlType::Float: return TEXT("float");
		case ERigControlType::ScaleFloat: return TEXT("scale_float");
		case ERigControlType::Bool: return TEXT("bool");
		case ERigControlType::Integer: return TEXT("integer");
		case ERigControlType::Vector2D: return TEXT("vector2d");
		case ERigControlType::Position: return TEXT("position");
		case ERigControlType::Scale: return TEXT("scale");
		case ERigControlType::Rotator: return TEXT("rotator");
		case ERigControlType::Transform: return TEXT("transform");
		case ERigControlType::TransformNoScale: return TEXT("transform_no_scale");
		case ERigControlType::EulerTransform: return TEXT("euler_transform");
		default: return TEXT("other");
		}
	}

	ERigControlAxis ParseRigControlAxis(const FString& Axis)
	{
		if (Axis.Equals(TEXT("x"), ESearchCase::IgnoreCase)) return ERigControlAxis::X;
		if (Axis.Equals(TEXT("y"), ESearchCase::IgnoreCase)) return ERigControlAxis::Y;
		if (Axis.Equals(TEXT("z"), ESearchCase::IgnoreCase)) return ERigControlAxis::Z;
		throw std::runtime_error("primary_axis must be x, y, or z");
	}

	ERigControlAnimationType ParseRigControlAnimationType(const FString& Type)
	{
		if (Type.Equals(TEXT("animation_control"), ESearchCase::IgnoreCase)) return ERigControlAnimationType::AnimationControl;
		if (Type.Equals(TEXT("animation_channel"), ESearchCase::IgnoreCase)) return ERigControlAnimationType::AnimationChannel;
		if (Type.Equals(TEXT("proxy_control"), ESearchCase::IgnoreCase)) return ERigControlAnimationType::ProxyControl;
		if (Type.Equals(TEXT("visual_cue"), ESearchCase::IgnoreCase)) return ERigControlAnimationType::VisualCue;
		throw std::runtime_error("control_animation_type must be animation_control, animation_channel, proxy_control, or visual_cue");
	}

	FString RigControlAnimationTypeName(ERigControlAnimationType Type)
	{
		switch (Type)
		{
		case ERigControlAnimationType::AnimationControl: return TEXT("animation_control");
		case ERigControlAnimationType::AnimationChannel: return TEXT("animation_channel");
		case ERigControlAnimationType::ProxyControl: return TEXT("proxy_control");
		case ERigControlAnimationType::VisualCue: return TEXT("visual_cue");
		default: return TEXT("unknown");
		}
	}

	ERigControlVisibility ParseRigControlVisibility(const FString& Visibility)
	{
		if (Visibility.Equals(TEXT("user_defined"), ESearchCase::IgnoreCase)) return ERigControlVisibility::UserDefined;
		if (Visibility.Equals(TEXT("based_on_selection"), ESearchCase::IgnoreCase)) return ERigControlVisibility::BasedOnSelection;
		throw std::runtime_error("shape_visibility must be user_defined or based_on_selection");
	}

	FString RigControlVisibilityName(ERigControlVisibility Visibility)
	{
		return Visibility == ERigControlVisibility::BasedOnSelection ? TEXT("based_on_selection") : TEXT("user_defined");
	}

	EEulerRotationOrder ParseRigRotationOrder(const FString& Order)
	{
		if (Order.Equals(TEXT("xyz"), ESearchCase::IgnoreCase)) return EEulerRotationOrder::XYZ;
		if (Order.Equals(TEXT("xzy"), ESearchCase::IgnoreCase)) return EEulerRotationOrder::XZY;
		if (Order.Equals(TEXT("yxz"), ESearchCase::IgnoreCase)) return EEulerRotationOrder::YXZ;
		if (Order.Equals(TEXT("yzx"), ESearchCase::IgnoreCase)) return EEulerRotationOrder::YZX;
		if (Order.Equals(TEXT("zxy"), ESearchCase::IgnoreCase)) return EEulerRotationOrder::ZXY;
		if (Order.Equals(TEXT("zyx"), ESearchCase::IgnoreCase)) return EEulerRotationOrder::ZYX;
		throw std::runtime_error("preferred_rotation_order must be xyz, xzy, yxz, yzx, zxy, or zyx");
	}

	FString RigRotationOrderName(EEulerRotationOrder Order)
	{
		switch (Order)
		{
		case EEulerRotationOrder::XYZ: return TEXT("xyz");
		case EEulerRotationOrder::XZY: return TEXT("xzy");
		case EEulerRotationOrder::YXZ: return TEXT("yxz");
		case EEulerRotationOrder::YZX: return TEXT("yzx");
		case EEulerRotationOrder::ZXY: return TEXT("zxy");
		case EEulerRotationOrder::ZYX: return TEXT("zyx");
		default: return TEXT("xyz");
		}
	}

	FRigControlValue ParseRigControlValue(ERigControlType Type, const FString& Text, const FTransform& Transform,
		ERigControlAxis PrimaryAxis, const UEnum* ControlEnum = nullptr)
	{
		if (Type == ERigControlType::Bool)
		{
			if (Text.Equals(TEXT("true"), ESearchCase::IgnoreCase) || Text == TEXT("1")) return FRigControlValue::Make(true);
			if (Text.Equals(TEXT("false"), ESearchCase::IgnoreCase) || Text == TEXT("0")) return FRigControlValue::Make(false);
			throw std::runtime_error("control_value must be true or false");
		}
		if (Type == ERigControlType::Integer)
		{
			int32 Value;
			if (ControlEnum)
			{
				const int32 EnumIndex = ControlEnum->GetIndexByNameString(Text, EGetByNameFlags::CheckAuthoredName);
				if (EnumIndex == INDEX_NONE || ControlEnum->HasMetaData(TEXT("Hidden"), EnumIndex))
					throw std::runtime_error(TCHAR_TO_UTF8(*(TEXT("control_value must name a visible member of ") + ControlEnum->GetPathName())));
				const FString EnumeratorName = ControlEnum->GetNameStringByIndex(EnumIndex);
				if (EnumeratorName.Equals(TEXT("MAX"), ESearchCase::IgnoreCase)
					|| EnumeratorName.EndsWith(TEXT("_MAX"), ESearchCase::IgnoreCase))
					throw std::runtime_error("control_value cannot select the enum sentinel member");
				const int64 EnumValue = ControlEnum->GetValueByIndex(EnumIndex);
				if (!ControlEnum->IsValidEnumValue(EnumValue)
					|| EnumValue < MIN_int32 || EnumValue > MAX_int32)
					throw std::runtime_error(TCHAR_TO_UTF8(*(TEXT("control_value must name a valid member of ") + ControlEnum->GetPathName())));
				Value = static_cast<int32>(EnumValue);
			}
			else if (!LexTryParseString(Value, *Text)) throw std::runtime_error("control_value must be an integer");
			return FRigControlValue::Make(Value);
		}
		if (Type == ERigControlType::Float || Type == ERigControlType::ScaleFloat)
		{
			float Value;
			if (!LexTryParseString(Value, *Text) || !FMath::IsFinite(Value)) throw std::runtime_error("control_value must be finite");
			return FRigControlValue::Make(Value);
		}
		FRigControlValue Value;
		Value.SetFromTransform(Transform, Type, PrimaryAxis);
		return Value;
	}
	FString BlendSampleFingerprint(const FBlendSample& Sample)
	{
		return FString::Printf(TEXT("%s|%.17g|%.17g|%.17g"),
			Sample.Animation ? *Sample.Animation->GetPathName() : TEXT(""),
			Sample.SampleValue.X, Sample.SampleValue.Y, Sample.SampleValue.Z);
	}

	TArray<FString> BlendSampleFingerprints(const UBlendSpace* BlendSpace)
	{
		TArray<FString> Result;
		TMap<FString, int32> Occurrences;
		for (const FBlendSample& Sample : BlendSpace->GetBlendSamples())
		{
			const FString Base = BlendSampleFingerprint(Sample);
			int32& Occurrence = Occurrences.FindOrAdd(Base);
			Result.Add(FString::Printf(TEXT("%s|occurrence=%d"), *Base, Occurrence++));
		}
		return Result;
	}

	TArray<FGuid> ResolveBlendSampleIds(UBlendSpace* BlendSpace)
	{
		TMap<FString, FGuid> Stored;
		if (const UBlendSpaceSampleIdentityData* Data = Cast<UBlendSpaceSampleIdentityData>(
			BlendSpace->GetAssetUserDataOfClass(UBlendSpaceSampleIdentityData::StaticClass())))
		{
			for (int32 Index = 0; Index < FMath::Min(Data->SampleIds.Num(), Data->SampleFingerprints.Num()); ++Index)
				if (Data->SampleIds[Index].IsValid()) Stored.FindOrAdd(Data->SampleFingerprints[Index]) = Data->SampleIds[Index];
		}
		TArray<FGuid> Result;
		TSet<FGuid> Used;
		for (const FString& Fingerprint : BlendSampleFingerprints(BlendSpace))
		{
			FGuid Id = Stored.FindRef(Fingerprint);
			if (!Id.IsValid() || Used.Contains(Id))
			{
				const FString Seed = BlendSpace->GetPathName() + TEXT("|") + Fingerprint;
				FTCHARToUTF8 Utf8(*Seed);
				const FString Hash = FMD5::HashBytes(reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length());
				if (!FGuid::ParseExact(Hash, EGuidFormats::Digits, Id)) throw std::runtime_error("failed to create Blend Space sample identity");
			}
			if (!Id.IsValid() || Used.Contains(Id)) throw std::runtime_error("Blend Space has duplicate sample identities");
			Used.Add(Id);
			Result.Add(Id);
		}
		return Result;
	}

	void PersistBlendSampleIds(UBlendSpace* BlendSpace, const TArray<FGuid>& Ids)
	{
		if (Ids.Num() != BlendSpace->GetNumberOfBlendSamples()) throw std::runtime_error("Blend Space identity count is inconsistent");
		UBlendSpaceSampleIdentityData* Data = Cast<UBlendSpaceSampleIdentityData>(
			BlendSpace->GetAssetUserDataOfClass(UBlendSpaceSampleIdentityData::StaticClass()));
		if (!Data)
		{
			Data = NewObject<UBlendSpaceSampleIdentityData>(BlendSpace, NAME_None, RF_Transactional);
			BlendSpace->AddAssetUserData(Data);
		}
		Data->Modify();
		Data->SampleIds = Ids;
		Data->SampleFingerprints = BlendSampleFingerprints(BlendSpace);
	}

	FString CinematicActionJson(bool bChanged, bool bDryRun, bool bDirty, bool bSaved, const FGuid& BindingGuid, int32 TrackIndex, int32 SectionIndex, int32 AffectedSections, int32 KeyIndex = -1)
	{
		return FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"dirty\":%s,\"saved\":%s,\"binding_guid\":\"%s\",\"track_index\":%d,\"section_index\":%d,\"key_index\":%d,\"affected_sections\":%d}"),
			bChanged ? TEXT("true") : TEXT("false"), bDryRun ? TEXT("true") : TEXT("false"), bDirty ? TEXT("true") : TEXT("false"), bSaved ? TEXT("true") : TEXT("false"),
			*BindingGuid.ToString(), TrackIndex, SectionIndex, KeyIndex, AffectedSections);
	}

	FGuid ParseCinematicBinding(UMovieScene* MovieScene, const FString& BindingGuid)
	{
		FGuid Guid;
		if (!FGuid::Parse(BindingGuid, Guid) || !Guid.IsValid() || !MovieScene->FindBinding(Guid))
			throw std::runtime_error("binding_guid must identify an existing binding");
		return Guid;
	}

	UClass* CinematicTrackClass(const FString& Name, bool bObjectBound)
	{
        if (Name.Equals(TEXT("event"), ESearchCase::IgnoreCase)) return UMovieSceneEventTrack::StaticClass();
		if (bObjectBound)
		{
			if (Name.Equals(TEXT("transform"), ESearchCase::IgnoreCase)) return UMovieScene3DTransformTrack::StaticClass();
			if (Name.Equals(TEXT("visibility"), ESearchCase::IgnoreCase)) return UMovieSceneVisibilityTrack::StaticClass();
			if (Name.Equals(TEXT("float_property"), ESearchCase::IgnoreCase)) return UMovieSceneFloatTrack::StaticClass();
			if (Name.Equals(TEXT("byte_property"), ESearchCase::IgnoreCase)) return UMovieSceneByteTrack::StaticClass();
			if (Name.Equals(TEXT("integer_property"), ESearchCase::IgnoreCase)) return UMovieSceneIntegerTrack::StaticClass();
			if (Name.Equals(TEXT("object_property"), ESearchCase::IgnoreCase)) return UMovieSceneObjectPropertyTrack::StaticClass();
			if (Name.Equals(TEXT("skeletal_animation"), ESearchCase::IgnoreCase)) return UMovieSceneSkeletalAnimationTrack::StaticClass();
		}
		if (Name.Equals(TEXT("audio"), ESearchCase::IgnoreCase)) return UMovieSceneAudioTrack::StaticClass();
		if (!bObjectBound && Name.Equals(TEXT("fade"), ESearchCase::IgnoreCase)) return UMovieSceneFadeTrack::StaticClass();
		throw std::runtime_error("track_class must be transform, visibility, float_property, byte_property, integer_property, object_property, skeletal_animation, audio or event for a binding; audio, fade or event for a master track");
	}

	TArray<UMovieSceneTrack*> CinematicTracks(UMovieScene* MovieScene, const FString& BindingGuid, FGuid& OutGuid)
	{
		if (BindingGuid.IsEmpty()) return MovieScene->GetTracks();
		OutGuid = ParseCinematicBinding(MovieScene, BindingGuid);
		return MovieScene->FindBinding(OutGuid)->GetTracks();
	}

	bool IsCameraBinding(UMovieScene* MovieScene, const FGuid& Guid)
	{
		const UClass* BoundClass = nullptr;
		if (FMovieSceneSpawnable* Spawnable = MovieScene->FindSpawnable(Guid))
			BoundClass = Spawnable->GetObjectTemplate() ? Spawnable->GetObjectTemplate()->GetClass() : nullptr;
		else if (FMovieScenePossessable* Possessable = MovieScene->FindPossessable(Guid))
			BoundClass = Possessable->GetPossessedObjectClass();
		return BoundClass && (BoundClass->IsChildOf(ACameraActor::StaticClass()) || BoundClass->IsChildOf(UCameraComponent::StaticClass()));
	}

	bool WouldCreateSequenceCycle(UMovieSceneSequence* Parent, UMovieSceneSequence* Child)
	{
		if (Parent == Child) return true;
		UMovieScene* ChildScene = Child ? Child->GetMovieScene() : nullptr;
		if (!ChildScene) return false;
		for (UMovieSceneTrack* Track : ChildScene->GetTracks())
			if (UMovieSceneSubTrack* SubTrack = Cast<UMovieSceneSubTrack>(Track))
				if (SubTrack->ContainsSequence(*Parent, true)) return true;
		return false;
	}

	AActor* FindPlacedEditorActor(const FString& ActorPath)
	{
		if (!GEditor) throw std::runtime_error("Unreal editor is not available");
		UWorld* World = GEditor->GetEditorWorldContext().World();
		AActor* Actor = GEditor->GetEditorSubsystem<UEditorActorSubsystem>()->GetActorReference(ActorPath);
		if (!Actor) Actor = Cast<AActor>(StaticFindObject(AActor::StaticClass(), nullptr, *ActorPath));
		if (!Actor || !World || Actor->GetWorld() != World)
			throw std::runtime_error("actor_path must identify an actor in the current editor world");
		return Actor;
	}

	UObject* LoadAsset(const FString& Path)
	{
		if (Path.IsEmpty())
			throw std::runtime_error("asset_path is required");
		// A failed load of a missing package leaves an empty in-memory package that blocks later creation at that path.
		if (!FindObject<UObject>(nullptr, *Path) && FPackageName::IsValidObjectPath(Path)
			&& !FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(Path)))
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Asset not found: %s"), *Path)));
		UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *Path);
		if (!Asset)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Asset not found: %s"), *Path)));
		return Asset;
	}

	void MarkAssetDirty(UObject* Asset)
	{
		if (Asset && Asset->GetOutermost())
			Asset->GetOutermost()->MarkPackageDirty();
	}

	UEditorAssetSubsystem* AssetSubsystem();

	void SaveIfRequested(UObject* Asset, bool bSave)
	{
		if (bSave && (!Asset || !AssetSubsystem()->SaveAsset(Asset->GetPathName(), true)))
			throw std::runtime_error("Failed to save asset");
	}

	struct FCinematicCameraTarget
	{
		ACineCameraActor* Actor = nullptr;
		ULevelSequence* Sequence = nullptr;
		bool bTemplate = false;
	};

	FCinematicCameraTarget ResolveCinematicCamera(const FString& ActorPath, const FString& AssetPath, const FString& BindingGuid)
	{
		if (!ActorPath.IsEmpty())
		{
			if (!AssetPath.IsEmpty() || !BindingGuid.IsEmpty()) throw std::runtime_error("specify actor_path or asset_path with binding_guid, not both");
			ACineCameraActor* Actor = Cast<ACineCameraActor>(FindPlacedEditorActor(ActorPath));
			if (!Actor) throw std::runtime_error("actor_path must identify a CineCameraActor");
			return {Actor, nullptr, false};
		}
		if (AssetPath.IsEmpty() || BindingGuid.IsEmpty()) throw std::runtime_error("actor_path or asset_path with binding_guid is required");
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(AssetPath));
		UMovieScene* Scene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!Scene) throw std::runtime_error("asset_path must identify a Level Sequence");
		const FGuid Guid = ParseCinematicBinding(Scene, BindingGuid);
		if (FMovieSceneSpawnable* Spawnable = Scene->FindSpawnable(Guid))
		{
			ACineCameraActor* Actor = Cast<ACineCameraActor>(Spawnable->GetObjectTemplate());
			if (!Actor) throw std::runtime_error("binding_guid must identify a CineCameraActor template");
			return {Actor, Sequence, true};
		}
		UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World) throw std::runtime_error("no current editor world is available to resolve the camera binding");
		TArray<UObject*, TInlineAllocator<1>> Objects;
		Sequence->LocateBoundObjects(Guid, UE::UniversalObjectLocator::FResolveParams::SyncFind(World), nullptr, Objects);
		for (UObject* Object : Objects)
			if (ACineCameraActor* Actor = Cast<ACineCameraActor>(Object)) return {Actor, Sequence, false};
		throw std::runtime_error("binding_guid does not resolve to a placed CineCameraActor");
	}

	struct FCinematicCameraSettings
	{
		FCameraLensSettings Lens;
		FCameraFilmbackSettings Filmback;
		FCameraFocusSettings Focus;
		float FocalLength = 0.f;
		float Aperture = 0.f;
	};

	FCinematicCameraSettings PrepareCinematicCameraSettings(UCineCameraComponent* Component, const FCinematicCameraReq& Body)
	{
		if (!Component) throw std::runtime_error("CineCameraComponent is unavailable");
		FCinematicCameraSettings Values {Component->LensSettings, Component->Filmback, Component->FocusSettings,
			Component->CurrentFocalLength, Component->CurrentAperture};
		auto PositiveOrOmitted = [](float Input, float& Target, const char* Name)
		{
			if (!FMath::IsFinite(Input) || (Input != -1.f && Input <= 0.f)) throw std::runtime_error(Name);
			if (Input != -1.f) Target = Input;
		};
		PositiveOrOmitted(Body.MinFocalLength, Values.Lens.MinFocalLength, "min_focal_length must be positive");
		PositiveOrOmitted(Body.MaxFocalLength, Values.Lens.MaxFocalLength, "max_focal_length must be positive");
		PositiveOrOmitted(Body.MinFStop, Values.Lens.MinFStop, "min_f_stop must be positive");
		PositiveOrOmitted(Body.MaxFStop, Values.Lens.MaxFStop, "max_f_stop must be positive");
		PositiveOrOmitted(Body.SensorWidth, Values.Filmback.SensorWidth, "sensor_width must be positive");
		PositiveOrOmitted(Body.SensorHeight, Values.Filmback.SensorHeight, "sensor_height must be positive");
		PositiveOrOmitted(Body.FocalLength, Values.FocalLength, "focal_length must be positive");
		PositiveOrOmitted(Body.Aperture, Values.Aperture, "aperture must be positive");
		if (!FMath::IsFinite(Body.ManualFocusDistance) || (Body.ManualFocusDistance != -1.f && Body.ManualFocusDistance < 0.f))
			throw std::runtime_error("manual_focus_distance must be nonnegative");
		if (Body.ManualFocusDistance != -1.f) Values.Focus.ManualFocusDistance = Body.ManualFocusDistance;
		if (!Body.FocusMethod.IsEmpty())
		{
			if (Body.FocusMethod.Equals(TEXT("manual"), ESearchCase::IgnoreCase)) Values.Focus.FocusMethod = ECameraFocusMethod::Manual;
			else if (Body.FocusMethod.Equals(TEXT("tracking"), ESearchCase::IgnoreCase)) Values.Focus.FocusMethod = ECameraFocusMethod::Tracking;
			else if (Body.FocusMethod.Equals(TEXT("disable"), ESearchCase::IgnoreCase)) Values.Focus.FocusMethod = ECameraFocusMethod::Disable;
			else if (Body.FocusMethod.Equals(TEXT("inherit"), ESearchCase::IgnoreCase)) Values.Focus.FocusMethod = ECameraFocusMethod::DoNotOverride;
			else throw std::runtime_error("focus_method must be manual, tracking, disable, or inherit");
		}
		if (!Body.FocusActorPath.IsEmpty())
		{
			if (Values.Focus.FocusMethod != ECameraFocusMethod::Tracking) throw std::runtime_error("focus_actor_path requires focus_method=tracking");
			Values.Focus.TrackingFocusSettings.ActorToTrack = FindPlacedEditorActor(Body.FocusActorPath);
		}
		if (Values.Focus.FocusMethod == ECameraFocusMethod::Tracking && Values.Focus.TrackingFocusSettings.ActorToTrack.IsNull())
			throw std::runtime_error("tracking focus requires focus_actor_path");
		if (Values.Lens.MinFocalLength > Values.Lens.MaxFocalLength || Values.Lens.MinFStop > Values.Lens.MaxFStop
			|| Values.FocalLength < Values.Lens.MinFocalLength || Values.FocalLength > Values.Lens.MaxFocalLength
			|| Values.Aperture < Values.Lens.MinFStop || Values.Aperture > Values.Lens.MaxFStop)
			throw std::runtime_error("focal_length and aperture must be inside valid lens min/max ranges");
		Values.Filmback.RecalcSensorAspectRatio();
		return Values;
	}

	void ApplyCinematicCameraSettings(UCineCameraComponent* Component, const FCinematicCameraSettings& Values)
	{
		Component->SetLensSettings(Values.Lens);
		Component->SetFilmback(Values.Filmback);
		Component->SetFocusSettings(Values.Focus);
		Component->SetCurrentFocalLength(Values.FocalLength);
		Component->SetCurrentAperture(Values.Aperture);
	}

	FString CinematicCameraJson(const FCinematicCameraTarget& Target, bool bChanged, bool bDryRun, bool bSaved)
	{
		UCineCameraComponent* Component = Target.Actor ? Target.Actor->GetCineCameraComponent() : nullptr;
		if (!Component) throw std::runtime_error("CineCameraComponent is unavailable");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("actor_path"), Target.Actor->GetPathName());
		Writer->WriteValue(TEXT("asset_path"), Target.Sequence ? Target.Sequence->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("is_template"), Target.bTemplate);
		const FVector Location = Target.Actor->GetActorLocation();
		const FRotator Rotation = Target.Actor->GetActorRotation();
		Writer->WriteObjectStart(TEXT("location"));
		Writer->WriteValue(TEXT("X"), Location.X); Writer->WriteValue(TEXT("Y"), Location.Y); Writer->WriteValue(TEXT("Z"), Location.Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectStart(TEXT("rotation"));
		Writer->WriteValue(TEXT("Pitch"), Rotation.Pitch); Writer->WriteValue(TEXT("Yaw"), Rotation.Yaw); Writer->WriteValue(TEXT("Roll"), Rotation.Roll);
		Writer->WriteObjectEnd();
		Writer->WriteValue(TEXT("focal_length"), Component->CurrentFocalLength);
		Writer->WriteValue(TEXT("aperture"), Component->CurrentAperture);
		Writer->WriteValue(TEXT("min_focal_length"), Component->LensSettings.MinFocalLength);
		Writer->WriteValue(TEXT("max_focal_length"), Component->LensSettings.MaxFocalLength);
		Writer->WriteValue(TEXT("min_f_stop"), Component->LensSettings.MinFStop);
		Writer->WriteValue(TEXT("max_f_stop"), Component->LensSettings.MaxFStop);
		Writer->WriteValue(TEXT("sensor_width"), Component->Filmback.SensorWidth);
		Writer->WriteValue(TEXT("sensor_height"), Component->Filmback.SensorHeight);
		Writer->WriteValue(TEXT("manual_focus_distance"), Component->FocusSettings.ManualFocusDistance);
		Writer->WriteValue(TEXT("focus_method"), StaticEnum<ECameraFocusMethod>()->GetNameStringByValue(static_cast<int64>(Component->FocusSettings.FocusMethod)));
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	UPhysicsAsset* LoadPhysicsAsset(const FString& Path)
	{
		UPhysicsAsset* Asset = Cast<UPhysicsAsset>(LoadAsset(Path));
		if (!Asset) throw std::runtime_error("asset_path must identify a Physics Asset");
		return Asset;
	}

	int32 FindPhysicsBody(UPhysicsAsset* Asset, const FString& BoneName)
	{
		if (BoneName.IsEmpty()) throw std::runtime_error("bone_name is required");
		const int32 Index = Asset->FindBodyIndex(FName(*BoneName));
		if (!Asset->SkeletalBodySetups.IsValidIndex(Index) || !Asset->SkeletalBodySetups[Index])
			throw std::runtime_error("bone_name does not identify a Physics Asset body");
		return Index;
	}

	EAggCollisionShape::Type PhysicsShapeType(const FString& ShapeType)
	{
		if (ShapeType.Equals(TEXT("sphere"), ESearchCase::IgnoreCase)) return EAggCollisionShape::Sphere;
		if (ShapeType.Equals(TEXT("box"), ESearchCase::IgnoreCase)) return EAggCollisionShape::Box;
		if (ShapeType.Equals(TEXT("capsule"), ESearchCase::IgnoreCase)) return EAggCollisionShape::Sphyl;
		if (ShapeType.Equals(TEXT("convex"), ESearchCase::IgnoreCase)) return EAggCollisionShape::Convex;
		throw std::runtime_error("shape_type must be sphere, box, capsule, or convex");
	}

	int32 PhysicsShapeCount(const USkeletalBodySetup* Body)
	{
		return Body->AggGeom.SphereElems.Num() + Body->AggGeom.BoxElems.Num()
			+ Body->AggGeom.SphylElems.Num() + Body->AggGeom.ConvexElems.Num();
	}

	void ValidatePhysicsShape(const FPhysicsAssetEditReq& Body)
	{
		const EAggCollisionShape::Type Type = PhysicsShapeType(Body.ShapeType);
		if (Body.Center.ContainsNaN() || Body.Rotation.ContainsNaN()) throw std::runtime_error("shape center and rotation must be finite");
		if (Type == EAggCollisionShape::Convex)
		{
			if (Body.Vertices.Num() < 4 || Body.Vertices.Num() > 64)
				throw std::runtime_error("convex vertices must contain between 4 and 64 points");
			for (int32 Index = 0; Index < Body.Vertices.Num(); ++Index)
			{
				if (Body.Vertices[Index].ContainsNaN()) throw std::runtime_error("convex vertices must be finite");
				for (int32 Prior = 0; Prior < Index; ++Prior)
					if (FVector::DistSquared(Body.Vertices[Index], Body.Vertices[Prior]) < 1.e-8)
						throw std::runtime_error("convex vertices must be distinct");
			}
			const FVector P0 = Body.Vertices[0];
			double MaxDistanceSq = 0.0;
			FVector Edge = FVector::ZeroVector;
			for (int32 Index = 1; Index < Body.Vertices.Num(); ++Index)
			{
				const FVector Candidate = Body.Vertices[Index] - P0;
				if (Candidate.SizeSquared() > MaxDistanceSq) { Edge = Candidate; MaxDistanceSq = Candidate.SizeSquared(); }
			}
			if (MaxDistanceSq < 1.e-8) throw std::runtime_error("convex vertices are degenerate");
			FVector Normal = FVector::ZeroVector;
			for (int32 Index = 1; Index < Body.Vertices.Num(); ++Index)
			{
				const FVector Candidate = FVector::CrossProduct(Edge, Body.Vertices[Index] - P0);
				if (Candidate.SizeSquared() > Normal.SizeSquared()) Normal = Candidate;
			}
			if (Normal.SizeSquared() < MaxDistanceSq * MaxDistanceSq * 1.e-8)
				throw std::runtime_error("convex vertices are collinear");
			double MaxVolume = 0.0;
			for (int32 Index = 1; Index < Body.Vertices.Num(); ++Index)
				MaxVolume = FMath::Max(MaxVolume, FMath::Abs(FVector::DotProduct(Normal, Body.Vertices[Index] - P0)));
			if (MaxVolume < FMath::Pow(MaxDistanceSq, 1.5) * 1.e-6)
				throw std::runtime_error("convex vertices are coplanar");
			USkeletalBodySetup* Probe = NewObject<USkeletalBodySetup>(GetTransientPackage());
			FKConvexElem ProbeShape;
			ProbeShape.VertexData = Body.Vertices;
			ProbeShape.UpdateElemBox();
			ProbeShape.SetTransform(FTransform(Body.Rotation, Body.Center));
			Probe->AggGeom.ConvexElems.Add(ProbeShape);
			Probe->InvalidatePhysicsData();
			Probe->CreatePhysicsMeshes();
			if (Probe->bFailedToCreatePhysicsMeshes || !Probe->AggGeom.ConvexElems[0].GetChaosConvexMesh())
				throw std::runtime_error("Chaos could not cook the convex vertices");
			return;
		}
		if (!FMath::IsFinite(Body.Radius) || !FMath::IsFinite(Body.Length) || Body.Size.ContainsNaN())
			throw std::runtime_error("shape dimensions must be finite");
		if ((Type == EAggCollisionShape::Sphere || Type == EAggCollisionShape::Sphyl) && Body.Radius <= 0.f)
			throw std::runtime_error("radius must be positive");
		if (Type == EAggCollisionShape::Sphyl && Body.Length <= 0.f) throw std::runtime_error("length must be positive");
		if (Type == EAggCollisionShape::Box && (Body.Size.X <= 0 || Body.Size.Y <= 0 || Body.Size.Z <= 0))
			throw std::runtime_error("box size components must be positive");
	}

	FKConvexElem MakePhysicsConvex(const FPhysicsAssetEditReq& Request)
	{
		FKConvexElem Shape;
		Shape.VertexData = Request.Vertices;
		Shape.UpdateElemBox();
		Shape.SetTransform(FTransform(Request.Rotation, Request.Center));
		return Shape;
	}

	int32 AddPhysicsShape(UPhysicsAsset* Asset, int32 BodyIndex, const FPhysicsAssetEditReq& Request)
	{
		USkeletalBodySetup* Body = Asset->SkeletalBodySetups[BodyIndex];
		const EAggCollisionShape::Type Type = PhysicsShapeType(Request.ShapeType);
		int32 ShapeIndex = INDEX_NONE;
		if (Type == EAggCollisionShape::Sphere)
		{
			FKSphereElem Shape(Request.Radius);
			Shape.Center = Request.Center;
			ShapeIndex = Body->AggGeom.SphereElems.Add(Shape);
		}
		else if (Type == EAggCollisionShape::Box)
		{
			FKBoxElem Shape(Request.Size.X, Request.Size.Y, Request.Size.Z);
			Shape.Center = Request.Center;
			Shape.Rotation = Request.Rotation;
			ShapeIndex = Body->AggGeom.BoxElems.Add(Shape);
		}
		else if (Type == EAggCollisionShape::Sphyl)
		{
			FKSphylElem Shape(Request.Radius, Request.Length);
			Shape.Center = Request.Center;
			Shape.Rotation = Request.Rotation;
			ShapeIndex = Body->AggGeom.SphylElems.Add(Shape);
		}
		else if (Type == EAggCollisionShape::Convex)
		{
			ShapeIndex = Body->AggGeom.ConvexElems.Add(MakePhysicsConvex(Request));
		}
		if (ShapeIndex == INDEX_NONE) throw std::runtime_error("failed to add physics shape");
		Asset->SetPrimitiveCollision(BodyIndex, Type, ShapeIndex,
			Request.bEnableCollision ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
		Asset->SetPrimitiveContributeToMass(BodyIndex, Type, ShapeIndex, Request.bContributeToMass);
		Body->InvalidatePhysicsData();
		if (Type == EAggCollisionShape::Convex)
		{
			Body->CreatePhysicsMeshes();
			if (Body->bFailedToCreatePhysicsMeshes || !Body->AggGeom.ConvexElems[ShapeIndex].GetChaosConvexMesh())
				throw std::runtime_error("Chaos failed to create the convex physics mesh");
		}
		return ShapeIndex;
	}

	FString PhysicsEditJson(UPhysicsAsset* Asset, bool bChanged, bool bDryRun, bool bSaved,
		const FString& BoneName, const FString& ShapeType, int32 ShapeIndex,
		const TArray<FString>& AffectedConstraints = {}, const TArray<FString>& AffectedCollisionPairs = {})
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("bone_name"), BoneName);
		Writer->WriteValue(TEXT("shape_type"), ShapeType);
		Writer->WriteValue(TEXT("shape_index"), ShapeIndex);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteArrayStart(TEXT("affected_constraints"));
		for (const FString& Name : AffectedConstraints) Writer->WriteValue(Name);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("affected_collision_pairs"));
		for (const FString& Name : AffectedCollisionPairs) Writer->WriteValue(Name);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	ELinearConstraintMotion ParsePhysicsLinearMotion(const FString& Motion, ELinearConstraintMotion Current)
	{
		if (Motion.IsEmpty()) return Current;
		if (Motion.Equals(TEXT("locked"), ESearchCase::IgnoreCase)) return LCM_Locked;
		if (Motion.Equals(TEXT("limited"), ESearchCase::IgnoreCase)) return LCM_Limited;
		if (Motion.Equals(TEXT("free"), ESearchCase::IgnoreCase)) return LCM_Free;
		throw std::runtime_error("linear_motion must be locked, limited, or free");
	}

	EAngularConstraintMotion ParsePhysicsAngularMotion(const FString& Motion, EAngularConstraintMotion Current)
	{
		if (Motion.IsEmpty()) return Current;
		if (Motion.Equals(TEXT("locked"), ESearchCase::IgnoreCase)) return ACM_Locked;
		if (Motion.Equals(TEXT("limited"), ESearchCase::IgnoreCase)) return ACM_Limited;
		if (Motion.Equals(TEXT("free"), ESearchCase::IgnoreCase)) return ACM_Free;
		throw std::runtime_error("angular_motion must be locked, limited, or free");
	}

	void ValidatePhysicsConstraintSettings(const FPhysicsConstraintReq& Body)
	{
		ParsePhysicsLinearMotion(Body.LinearMotion, LCM_Locked);
		ParsePhysicsAngularMotion(Body.AngularMotion, ACM_Locked);
		for (float Value : {Body.LinearLimit, Body.Swing1Limit, Body.Swing2Limit, Body.TwistLimit})
			if (!FMath::IsFinite(Value) || (Value != -1.f && Value < 0.f))
				throw std::runtime_error("constraint limits must be nonnegative or -1 to retain the current value");
		if (Body.Swing1Limit > 180.f || Body.Swing2Limit > 180.f || Body.TwistLimit > 180.f)
			throw std::runtime_error("angular limits must not exceed 180 degrees");
		if (!Body.Projection.IsEmpty() && !Body.Projection.Equals(TEXT("enabled"), ESearchCase::IgnoreCase)
			&& !Body.Projection.Equals(TEXT("disabled"), ESearchCase::IgnoreCase))
			throw std::runtime_error("projection must be enabled or disabled");
	}

	void ApplyPhysicsConstraintSettings(FConstraintInstance& Instance, const FPhysicsConstraintReq& Body)
	{
		const ELinearConstraintMotion X = ParsePhysicsLinearMotion(Body.LinearMotion, Instance.GetLinearXMotion());
		const ELinearConstraintMotion Y = ParsePhysicsLinearMotion(Body.LinearMotion, Instance.GetLinearYMotion());
		const ELinearConstraintMotion Z = ParsePhysicsLinearMotion(Body.LinearMotion, Instance.GetLinearZMotion());
		Instance.SetLinearLimits(X, Y, Z, Body.LinearLimit >= 0.f ? Body.LinearLimit : Instance.GetLinearLimit());
		Instance.SetAngularSwing1Limit(ParsePhysicsAngularMotion(Body.AngularMotion, Instance.GetAngularSwing1Motion()),
			Body.Swing1Limit >= 0.f ? Body.Swing1Limit : Instance.GetAngularSwing1Limit());
		Instance.SetAngularSwing2Limit(ParsePhysicsAngularMotion(Body.AngularMotion, Instance.GetAngularSwing2Motion()),
			Body.Swing2Limit >= 0.f ? Body.Swing2Limit : Instance.GetAngularSwing2Limit());
		Instance.SetAngularTwistLimit(ParsePhysicsAngularMotion(Body.AngularMotion, Instance.GetAngularTwistMotion()),
			Body.TwistLimit >= 0.f ? Body.TwistLimit : Instance.GetAngularTwistLimit());
		if (Body.Projection.Equals(TEXT("enabled"), ESearchCase::IgnoreCase)) Instance.EnableProjection();
		else if (Body.Projection.Equals(TEXT("disabled"), ESearchCase::IgnoreCase)) Instance.DisableProjection();
	}

	bool ParsePhysicsSettingBool(const FString& Value)
	{
		if (Value.Equals(TEXT("true"), ESearchCase::IgnoreCase) || Value == TEXT("1")) return true;
		if (Value.Equals(TEXT("false"), ESearchCase::IgnoreCase) || Value == TEXT("0")) return false;
		throw std::runtime_error("boolean body settings must be true or false");
	}

	void ApplyPhysicsBodySettings(USkeletalBodySetup* Setup, const TMap<FString, FString>& Settings)
	{
		for (const TPair<FString, FString>& Field : Settings)
		{
			if (Field.Key == TEXT("physics_type"))
			{
				if (Field.Value.Equals(TEXT("default"), ESearchCase::IgnoreCase)) Setup->PhysicsType = PhysType_Default;
				else if (Field.Value.Equals(TEXT("kinematic"), ESearchCase::IgnoreCase)) Setup->PhysicsType = PhysType_Kinematic;
				else if (Field.Value.Equals(TEXT("simulated"), ESearchCase::IgnoreCase)) Setup->PhysicsType = PhysType_Simulated;
				else throw std::runtime_error("physics_type must be default, kinematic, or simulated");
			}
			else if (Field.Key == TEXT("collision_enabled"))
			{
				ECollisionEnabled::Type Mode;
				if (Field.Value.Equals(TEXT("none"), ESearchCase::IgnoreCase)) Mode = ECollisionEnabled::NoCollision;
				else if (Field.Value.Equals(TEXT("query"), ESearchCase::IgnoreCase)) Mode = ECollisionEnabled::QueryOnly;
				else if (Field.Value.Equals(TEXT("physics"), ESearchCase::IgnoreCase)) Mode = ECollisionEnabled::PhysicsOnly;
				else if (Field.Value.Equals(TEXT("query_and_physics"), ESearchCase::IgnoreCase)) Mode = ECollisionEnabled::QueryAndPhysics;
				else throw std::runtime_error("collision_enabled must be none, query, physics, or query_and_physics");
				Setup->DefaultInstance.SetCollisionEnabled(Mode, false);
			}
			else if (Field.Key == TEXT("mass_scale"))
			{
				float Value;
				if (!LexTryParseString(Value, *Field.Value) || !FMath::IsFinite(Value) || Value < 0.001f)
					throw std::runtime_error("mass_scale must be finite and at least 0.001");
				Setup->DefaultInstance.MassScale = Value;
			}
			else if (Field.Key == TEXT("consider_for_bounds")) Setup->bConsiderForBounds = ParsePhysicsSettingBool(Field.Value);
			else if (Field.Key == TEXT("enable_gravity")) Setup->DefaultInstance.bEnableGravity = ParsePhysicsSettingBool(Field.Value);
			else if (Field.Key == TEXT("use_ccd")) Setup->DefaultInstance.bUseCCD = ParsePhysicsSettingBool(Field.Value);
			else if (Field.Key == TEXT("skip_scale_from_animation")) Setup->bSkipScaleFromAnimation = ParsePhysicsSettingBool(Field.Value);
			else throw std::runtime_error("unknown Physics Asset body setting");
		}
	}

	FString PhysicsBodySettingsJson(USkeletalBodySetup* Setup, bool bChanged, bool bDryRun, bool bSaved)
	{
		const ECollisionEnabled::Type Collision = Setup->DefaultInstance.GetCollisionEnabled(false);
		const TCHAR* CollisionName = Collision == ECollisionEnabled::NoCollision ? TEXT("none")
			: Collision == ECollisionEnabled::QueryOnly ? TEXT("query")
			: Collision == ECollisionEnabled::PhysicsOnly ? TEXT("physics") : TEXT("query_and_physics");
		const TCHAR* PhysicsName = Setup->PhysicsType == PhysType_Kinematic ? TEXT("kinematic")
			: Setup->PhysicsType == PhysType_Simulated ? TEXT("simulated") : TEXT("default");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("bone_name"), Setup->BoneName.ToString());
		Writer->WriteValue(TEXT("physics_type"), PhysicsName);
		Writer->WriteValue(TEXT("collision_enabled"), CollisionName);
		Writer->WriteValue(TEXT("mass_scale"), Setup->DefaultInstance.MassScale);
		Writer->WriteValue(TEXT("consider_for_bounds"), static_cast<bool>(Setup->bConsiderForBounds));
		Writer->WriteValue(TEXT("enable_gravity"), static_cast<bool>(Setup->DefaultInstance.bEnableGravity));
		Writer->WriteValue(TEXT("use_ccd"), static_cast<bool>(Setup->DefaultInstance.bUseCCD));
		Writer->WriteValue(TEXT("skip_scale_from_animation"), Setup->bSkipScaleFromAnimation);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	void ValidatePhysicsDrive(const FPhysicsDriveReq& Body)
	{
		if (!Body.DriveType.Equals(TEXT("linear"), ESearchCase::IgnoreCase)
			&& !Body.DriveType.Equals(TEXT("angular"), ESearchCase::IgnoreCase))
			throw std::runtime_error("drive_type must be linear or angular");
		if (Body.DriveType.Equals(TEXT("angular"), ESearchCase::IgnoreCase)
			&& !Body.AngularMode.Equals(TEXT("slerp"), ESearchCase::IgnoreCase)
			&& !Body.AngularMode.Equals(TEXT("twist_swing"), ESearchCase::IgnoreCase))
			throw std::runtime_error("angular_mode must be slerp or twist_swing");
		for (float Value : {Body.Stiffness, Body.Damping, Body.ForceLimit})
			if (!FMath::IsFinite(Value) || Value < 0.f) throw std::runtime_error("drive stiffness, damping, and force_limit must be finite and nonnegative");
		if (Body.PositionTarget.ContainsNaN() || Body.VelocityTarget.ContainsNaN() || Body.OrientationTarget.ContainsNaN())
			throw std::runtime_error("drive targets must be finite");
	}

	void ApplyPhysicsDrive(FConstraintInstance& Instance, const FPhysicsDriveReq& Body)
	{
		if (Body.DriveType.Equals(TEXT("linear"), ESearchCase::IgnoreCase))
		{
			Instance.SetLinearPositionDrive(Body.bPositionX, Body.bPositionY, Body.bPositionZ);
			Instance.SetLinearVelocityDrive(Body.bVelocityX, Body.bVelocityY, Body.bVelocityZ);
			Instance.SetLinearDriveParams(Body.Stiffness, Body.Damping, Body.ForceLimit);
			Instance.SetLinearPositionTarget(Body.PositionTarget);
			Instance.SetLinearVelocityTarget(Body.VelocityTarget);
			Instance.SetLinearDriveAccelerationMode(Body.bAccelerationMode);
		}
		else
		{
			const bool bSlerp = Body.AngularMode.Equals(TEXT("slerp"), ESearchCase::IgnoreCase);
			Instance.SetAngularDriveMode(bSlerp ? EAngularDriveMode::SLERP : EAngularDriveMode::TwistAndSwing);
			Instance.SetOrientationDriveSLERP(bSlerp && Body.bSlerpPosition);
			Instance.SetAngularVelocityDriveSLERP(bSlerp && Body.bSlerpVelocity);
			Instance.SetOrientationDriveTwistAndSwing(!bSlerp && Body.bOrientationTwist, !bSlerp && Body.bOrientationSwing);
			Instance.SetAngularVelocityDriveTwistAndSwing(!bSlerp && Body.bAngularVelocityTwist, !bSlerp && Body.bAngularVelocitySwing);
			Instance.SetAngularDriveParams(Body.Stiffness, Body.Damping, Body.ForceLimit);
			Instance.SetAngularOrientationTarget(Body.OrientationTarget.Quaternion());
			Instance.SetAngularVelocityTarget(Body.VelocityTarget);
			Instance.SetAngularDriveAccelerationMode(Body.bAccelerationMode);
		}
	}

	FString PhysicsDriveJson(UPhysicsAsset* Asset, UPhysicsConstraintTemplate* Constraint,
		bool bChanged, bool bDryRun, bool bSaved)
	{
		FConstraintInstance& Instance = Constraint->DefaultInstance;
		float LinearStiffness, LinearDamping, LinearForceLimit;
		float AngularStiffness, AngularDamping, AngularForceLimit;
		Instance.GetLinearDriveParams(LinearStiffness, LinearDamping, LinearForceLimit);
		Instance.GetAngularDriveParams(AngularStiffness, AngularDamping, AngularForceLimit);
		bool bOrientationTwist, bOrientationSwing, bVelocityTwist, bVelocitySwing;
		Instance.GetOrientationDriveTwistAndSwing(bOrientationTwist, bOrientationSwing);
		Instance.GetAngularVelocityDriveTwistAndSwing(bVelocityTwist, bVelocitySwing);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("constraint_name"), Instance.JointName.ToString());
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectStart(TEXT("linear"));
		Writer->WriteValue(TEXT("position_x"), Instance.IsLinearPositionDriveXEnabled());
		Writer->WriteValue(TEXT("position_y"), Instance.IsLinearPositionDriveYEnabled());
		Writer->WriteValue(TEXT("position_z"), Instance.IsLinearPositionDriveZEnabled());
		Writer->WriteValue(TEXT("velocity_x"), Instance.IsLinearVelocityDriveXEnabled());
		Writer->WriteValue(TEXT("velocity_y"), Instance.IsLinearVelocityDriveYEnabled());
		Writer->WriteValue(TEXT("velocity_z"), Instance.IsLinearVelocityDriveZEnabled());
		Writer->WriteValue(TEXT("acceleration_mode"), Instance.ProfileInstance.LinearDrive.GetAccelerationMode());
		Writer->WriteValue(TEXT("stiffness"), LinearStiffness);
		Writer->WriteValue(TEXT("damping"), LinearDamping);
		Writer->WriteValue(TEXT("force_limit"), LinearForceLimit);
		Writer->WriteValue(TEXT("position_target_x"), Instance.GetLinearPositionTarget().X);
		Writer->WriteValue(TEXT("position_target_y"), Instance.GetLinearPositionTarget().Y);
		Writer->WriteValue(TEXT("position_target_z"), Instance.GetLinearPositionTarget().Z);
		Writer->WriteValue(TEXT("velocity_target_x"), Instance.GetLinearVelocityTarget().X);
		Writer->WriteValue(TEXT("velocity_target_y"), Instance.GetLinearVelocityTarget().Y);
		Writer->WriteValue(TEXT("velocity_target_z"), Instance.GetLinearVelocityTarget().Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectStart(TEXT("angular"));
		Writer->WriteValue(TEXT("mode"), Instance.GetAngularDriveMode() == EAngularDriveMode::SLERP ? TEXT("slerp") : TEXT("twist_swing"));
		Writer->WriteValue(TEXT("slerp_position"), Instance.GetOrientationDriveSLERP());
		Writer->WriteValue(TEXT("slerp_velocity"), Instance.GetAngularVelocityDriveSLERP());
		Writer->WriteValue(TEXT("orientation_twist"), bOrientationTwist);
		Writer->WriteValue(TEXT("orientation_swing"), bOrientationSwing);
		Writer->WriteValue(TEXT("velocity_twist"), bVelocityTwist);
		Writer->WriteValue(TEXT("velocity_swing"), bVelocitySwing);
		Writer->WriteValue(TEXT("acceleration_mode"), Instance.ProfileInstance.AngularDrive.GetAccelerationMode());
		Writer->WriteValue(TEXT("stiffness"), AngularStiffness);
		Writer->WriteValue(TEXT("damping"), AngularDamping);
		Writer->WriteValue(TEXT("force_limit"), AngularForceLimit);
		Writer->WriteValue(TEXT("orientation_pitch"), Instance.GetAngularOrientationTarget().Pitch);
		Writer->WriteValue(TEXT("orientation_yaw"), Instance.GetAngularOrientationTarget().Yaw);
		Writer->WriteValue(TEXT("orientation_roll"), Instance.GetAngularOrientationTarget().Roll);
		Writer->WriteValue(TEXT("velocity_target_x"), Instance.GetAngularVelocityTarget().X);
		Writer->WriteValue(TEXT("velocity_target_y"), Instance.GetAngularVelocityTarget().Y);
		Writer->WriteValue(TEXT("velocity_target_z"), Instance.GetAngularVelocityTarget().Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	FString PhysicsConstraintJson(UPhysicsAsset* Asset, const UPhysicsConstraintTemplate* Constraint,
		bool bChanged, bool bDryRun, bool bSaved)
	{
		const FConstraintInstance& Instance = Constraint->DefaultInstance;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("constraint_name"), Instance.JointName.ToString());
		Writer->WriteValue(TEXT("child_bone"), Instance.ConstraintBone1.ToString());
		Writer->WriteValue(TEXT("parent_bone"), Instance.ConstraintBone2.ToString());
		Writer->WriteValue(TEXT("linear_limit"), Instance.GetLinearLimit());
		Writer->WriteValue(TEXT("swing1_limit"), Instance.GetAngularSwing1Limit());
		Writer->WriteValue(TEXT("swing2_limit"), Instance.GetAngularSwing2Limit());
		Writer->WriteValue(TEXT("twist_limit"), Instance.GetAngularTwistLimit());
		Writer->WriteValue(TEXT("projection_enabled"), Instance.IsProjectionEnabled());
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteArrayStart(TEXT("affected_profiles"));
		for (const FPhysicsConstraintProfileHandle& Profile : Constraint->ProfileHandles) Writer->WriteValue(Profile.ProfileName.ToString());
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	void ApplyAssetProperties(UObject* Asset, const FAssetPropertyReq& Body)
	{
		if (!Asset)
			throw std::runtime_error("asset_path is required");
		if (!Body.AssetClass.IsEmpty())
		{
			UClass* ExpectedClass = LoadClass<UObject>(nullptr, *Body.AssetClass);
			if (!ExpectedClass || !Asset->GetClass()->IsChildOf(ExpectedClass))
				throw std::runtime_error("asset_class does not match the loaded asset");
		}
		if (Body.bDryRun)
			return;
		Asset->Modify();
		for (const auto& Property : Body.Properties)
			ObjUtils::SetPropertyValueFromString(Asset, Property.Key, Property.Value);
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
	}

	FString SoundWaveSettingsJson(const USoundWave* Wave)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Wave->GetPathName());
		Writer->WriteValue(TEXT("compression_type"), StaticEnum<ESoundAssetCompressionType>()->GetNameStringByValue(static_cast<int64>(Wave->GetSoundAssetCompressionTypeEnum())));
		const FIntProperty* CompressionQualityProperty = FindFProperty<FIntProperty>(USoundWave::StaticClass(), FName(TEXT("CompressionQuality")));
		const int32 StoredCompressionQuality = CompressionQualityProperty ? CompressionQualityProperty->GetPropertyValue_InContainer(Wave) : Wave->GetCompressionQuality();
		Writer->WriteValue(TEXT("compression_quality"), StoredCompressionQuality);
		Writer->WriteValue(TEXT("effective_compression_quality"), Wave->GetCompressionQuality());
		const FEnumProperty* SampleRateProperty = FindFProperty<FEnumProperty>(USoundWave::StaticClass(), FName(TEXT("SampleRateQuality")));
		Writer->WriteValue(TEXT("sample_rate_quality"), SampleRateProperty && SampleRateProperty->GetEnum()
			? SampleRateProperty->GetEnum()->GetNameStringByValue(static_cast<int64>(Wave->SampleRateQuality)) : TEXT(""));
		Writer->WriteValue(TEXT("looping"), static_cast<bool>(Wave->bLooping));
		Writer->WriteValue(TEXT("loading_behavior_override"), StaticEnum<ESoundWaveLoadingBehavior>()->GetNameStringByValue(static_cast<int64>(Wave->LoadingBehavior)));
		Writer->WriteValue(TEXT("effective_loading_behavior"), StaticEnum<ESoundWaveLoadingBehavior>()->GetNameStringByValue(static_cast<int64>(Wave->GetLoadingBehavior())));
		Writer->WriteValue(TEXT("cloud_streaming"), Wave->IsCloudStreamingEnabled());
		Writer->WriteValue(TEXT("sound_class_path"), Wave->SoundClassObject ? Wave->SoundClassObject->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("attenuation_path"), Wave->AttenuationSettings ? Wave->AttenuationSettings->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("override_concurrency"), static_cast<bool>(Wave->bOverrideConcurrency));
		TArray<FString> ConcurrencyPaths;
		for (const TObjectPtr<USoundConcurrency>& Concurrency : Wave->ConcurrencySet)
			if (Concurrency) ConcurrencyPaths.Add(Concurrency->GetPathName());
		ConcurrencyPaths.Sort();
		Writer->WriteArrayStart(TEXT("concurrency_paths"));
		for (const FString& Path : ConcurrencyPaths) Writer->WriteValue(Path);
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("duration_seconds"), Wave->GetDuration());
		Writer->WriteValue(TEXT("channels"), Wave->NumChannels);
		Writer->WriteValue(TEXT("imported_sample_rate"), Wave->GetImportedSampleRate());
		Writer->WriteValue(TEXT("dirty"), Wave->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	FString CueGraphNodeId(const UEdGraphNode* Node)
	{
		return Node ? Node->NodeGuid.ToString(EGuidFormats::DigitsWithHyphens) : TEXT("");
	}

	USoundCueGraphNode_Base* FindCueGraphNode(UEdGraph* Graph, const FString& NodeId)
	{
		FGuid Guid;
		if (!Graph || !FGuid::Parse(NodeId, Guid)) return nullptr;
		for (UEdGraphNode* Node : Graph->Nodes)
			if (Node && Node->NodeGuid == Guid) return Cast<USoundCueGraphNode_Base>(Node);
		return nullptr;
	}

	FProperty* FindBatchProperty(UStruct* Struct, const FString& Name);

	void ValidateCueNodePropertyMap(const USoundNode* Node, const TMap<FString, FString>& Properties)
	{
		if (!Node) throw std::runtime_error("sound cue node is missing");
		for (const auto& Entry : Properties)
		{
			TArray<FString> Parts;
			Entry.Key.ParseIntoArray(Parts, TEXT("."), true);
			if (Parts.IsEmpty()) throw std::runtime_error("node property name cannot be empty");
			FProperty* RootProperty = FindBatchProperty(Node->GetClass(), Parts[0]);
			if (!RootProperty || !RootProperty->HasAnyPropertyFlags(CPF_Edit)
				|| RootProperty->HasAnyPropertyFlags(CPF_EditConst | CPF_Transient | CPF_DuplicateTransient | CPF_Deprecated))
				throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Sound Cue node property is not editable: %s"), *Entry.Key)));
		}
	}

	void ApplyCueNodePropertyMap(USoundNode* Node, const TMap<FString, FString>& Properties)
	{
		ValidateCueNodePropertyMap(Node, Properties);
		for (const auto& Entry : Properties)
			ObjUtils::SetPropertyValueFromString(Node, Entry.Key, Entry.Value);
	}

	FString SoundCueGraphJson(USoundCue* Cue)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		UEdGraph* Graph = Cue ? Cue->GetGraph() : nullptr;
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Cue ? Cue->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("graph_exists"), Graph != nullptr);
		Writer->WriteValue(TEXT("first_node_path"), Cue && Cue->FirstNode ? Cue->FirstNode->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("dirty"), Cue && Cue->GetOutermost()->IsDirty());
		Writer->WriteArrayStart(TEXT("nodes"));
		if (Graph)
		{
			for (UEdGraphNode* GraphNode : Graph->Nodes)
			{
				USoundCueGraphNode_Base* CueGraphNode = Cast<USoundCueGraphNode_Base>(GraphNode);
				if (!CueGraphNode) continue;
				USoundCueGraphNode* SoundGraphNode = Cast<USoundCueGraphNode>(GraphNode);
				USoundCueGraphNode_Root* RootNode = Cast<USoundCueGraphNode_Root>(GraphNode);
				USoundNode* SoundNode = SoundGraphNode ? SoundGraphNode->SoundNode : nullptr;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("node_id"), CueGraphNodeId(GraphNode));
				Writer->WriteValue(TEXT("kind"), RootNode ? TEXT("root") : TEXT("sound_node"));
				Writer->WriteValue(TEXT("node_class"), SoundNode ? SoundNode->GetClass()->GetPathName() : TEXT(""));
				Writer->WriteValue(TEXT("sound_node_path"), SoundNode ? SoundNode->GetPathName() : TEXT(""));
				Writer->WriteValue(TEXT("title"), GraphNode->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
				Writer->WriteValue(TEXT("x"), GraphNode->NodePosX);
				Writer->WriteValue(TEXT("y"), GraphNode->NodePosY);
				if (SoundNode)
				{
					const FString PropertiesJson = ObjUtils::SerializeObjectToJson(SoundNode);
					Writer->WriteRawJSONValue(TEXT("settings"), FStringView(PropertiesJson));
				}
				TArray<UEdGraphPin*> InputPins;
				CueGraphNode->GetInputPins(InputPins);
				Writer->WriteArrayStart(TEXT("inputs"));
				for (int32 InputIndex = 0; InputIndex < InputPins.Num(); ++InputIndex)
				{
					UEdGraphPin* InputPin = InputPins[InputIndex];
					UEdGraphNode* LinkedNode = InputPin && InputPin->LinkedTo.Num() > 0 ? InputPin->LinkedTo[0]->GetOwningNode() : nullptr;
					Writer->WriteObjectStart();
					Writer->WriteValue(TEXT("index"), InputIndex);
					Writer->WriteValue(TEXT("name"), InputPin ? InputPin->PinName.ToString() : TEXT(""));
					Writer->WriteValue(TEXT("source_node_id"), CueGraphNodeId(LinkedNode));
					Writer->WriteObjectEnd();
				}
				Writer->WriteArrayEnd();
				Writer->WriteObjectEnd();
			}
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return Json;
	}

	FString SoundCueGraphActionJson(USoundCue* Cue, const FString& Operation, const FString& NodeId,
		bool bChanged, bool bWouldChange, bool bDryRun, bool bSaved)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Cue->GetPathName());
		Writer->WriteValue(TEXT("operation"), Operation);
		Writer->WriteValue(TEXT("node_id"), NodeId);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("would_change"), bWouldChange);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("dirty"), Cue->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	TMap<USoundCueGraphNode_Base*, FIntPoint> BuildSoundCueLayout(USoundCue* Cue)
	{
		TMap<USoundCueGraphNode_Base*, FIntPoint> Layout;
		UEdGraph* Graph = Cue ? Cue->GetGraph() : nullptr;
		if (!Cue || !Graph) return Layout;
		TMap<USoundNode*, int32> DepthBySoundNode;
		TArray<USoundNode*> Queue;
		if (Cue->FirstNode)
		{
			DepthBySoundNode.Add(Cue->FirstNode, 0);
			Queue.Add(Cue->FirstNode);
		}
		int32 MaxDepth = 0;
		for (int32 QueueIndex = 0; QueueIndex < Queue.Num(); ++QueueIndex)
		{
			USoundNode* Current = Queue[QueueIndex];
			const int32 ChildDepth = DepthBySoundNode.FindChecked(Current) + 1;
			MaxDepth = FMath::Max(MaxDepth, ChildDepth);
			for (const TObjectPtr<USoundNode>& Child : Current->ChildNodes)
				if (Child && !DepthBySoundNode.Contains(Child))
				{
					DepthBySoundNode.Add(Child, ChildDepth);
					Queue.Add(Child);
				}
		}
		for (const TObjectPtr<USoundNode>& SoundNode : Cue->AllNodes)
			if (SoundNode && !DepthBySoundNode.Contains(SoundNode))
			{
				const int32 OrphanDepth = FMath::Max(1, MaxDepth + 1);
				DepthBySoundNode.Add(SoundNode, OrphanDepth);
				MaxDepth = FMath::Max(MaxDepth, OrphanDepth);
			}
		TMap<int32, int32> RowByDepth;
		for (UEdGraphNode* GraphNode : Graph->Nodes)
		{
			if (USoundCueGraphNode_Root* RootNode = Cast<USoundCueGraphNode_Root>(GraphNode))
			{
				Layout.Add(RootNode, FIntPoint(0, -58));
				continue;
			}
			USoundCueGraphNode* SoundGraphNode = Cast<USoundCueGraphNode>(GraphNode);
			if (!SoundGraphNode || !SoundGraphNode->SoundNode) continue;
			const int32 Depth = DepthBySoundNode.FindRef(SoundGraphNode->SoundNode);
			const int32 Row = RowByDepth.FindOrAdd(Depth, 0);
			RowByDepth[Depth] = Row + 1;
			Layout.Add(SoundGraphNode, FIntPoint(-300 * (Depth + 1), Row * 150));
		}
		return Layout;
	}

	bool SoundCueNodeHasCycle(const USoundNode* Node, TSet<const USoundNode*>& Visiting,
		TSet<const USoundNode*>& Visited)
	{
		if (!Node) return false;
		if (Visiting.Contains(Node)) return true;
		if (Visited.Contains(Node)) return false;
		Visiting.Add(Node);
		for (const TObjectPtr<USoundNode>& Child : Node->ChildNodes)
			if (SoundCueNodeHasCycle(Child, Visiting, Visited)) return true;
		Visiting.Remove(Node);
		Visited.Add(Node);
		return false;
	}

	FString ValidateSoundCueGraph(USoundCue* Cue)
	{
		TArray<FString> Errors;
		TArray<FString> Warnings;
		UEdGraph* Graph = Cue ? Cue->GetGraph() : nullptr;
		if (!Cue) Errors.Add(TEXT("Sound Cue is unavailable"));
		if (Cue && !Graph) Errors.Add(TEXT("Sound Cue graph is missing"));
		TArray<USoundCueGraphNode_Root*> RootNodes;
		TSet<USoundNode*> GraphSoundNodes;
		int32 ConnectedInputs = 0;
		if (Graph)
		{
			for (UEdGraphNode* GraphNode : Graph->Nodes)
			{
				if (USoundCueGraphNode_Root* Root = Cast<USoundCueGraphNode_Root>(GraphNode))
				{
					RootNodes.Add(Root);
					if (Root->Pins.Num() != 1) Errors.Add(TEXT("Sound Cue root must have exactly one input pin"));
					else if (Root->Pins[0]->LinkedTo.Num() > 0) ++ConnectedInputs;
					continue;
				}
				USoundCueGraphNode* SoundGraphNode = Cast<USoundCueGraphNode>(GraphNode);
				if (!SoundGraphNode)
				{
					Errors.Add(TEXT("Graph contains a node that is not a Sound Cue node or root"));
					continue;
				}
				USoundNode* SoundNode = SoundGraphNode->SoundNode;
				if (!SoundNode)
				{
					Errors.Add(FString::Printf(TEXT("Graph node %s has no Sound Node object"), *CueGraphNodeId(GraphNode)));
					continue;
				}
				GraphSoundNodes.Add(SoundNode);
				TArray<UEdGraphPin*> InputPins;
				SoundGraphNode->GetInputPins(InputPins);
				if (InputPins.Num() != SoundNode->ChildNodes.Num())
					Errors.Add(FString::Printf(TEXT("Sound Node %s input-pin count does not match its child array"), *SoundNode->GetName()));
				for (int32 InputIndex = 0; InputIndex < InputPins.Num(); ++InputIndex)
				{
					UEdGraphPin* InputPin = InputPins[InputIndex];
					if (!InputPin || InputPin->LinkedTo.Num() > 1)
					{
						Errors.Add(FString::Printf(TEXT("Sound Node %s input %d has invalid links"), *SoundNode->GetName(), InputIndex));
						continue;
					}
					USoundNode* LinkedSoundNode = nullptr;
					if (InputPin->LinkedTo.Num() == 1)
					{
						if (USoundCueGraphNode* LinkedGraphNode = Cast<USoundCueGraphNode>(InputPin->LinkedTo[0]->GetOwningNode()))
							LinkedSoundNode = LinkedGraphNode->SoundNode;
						else Errors.Add(FString::Printf(TEXT("Sound Node %s input %d links to a non-sound graph node"), *SoundNode->GetName(), InputIndex));
					}
					if (!SoundNode->ChildNodes.IsValidIndex(InputIndex) || SoundNode->ChildNodes[InputIndex] != LinkedSoundNode)
						Errors.Add(FString::Printf(TEXT("Sound Node %s child %d disagrees with its graph connection"), *SoundNode->GetName(), InputIndex));
				}
				if (USoundNodeWavePlayer* WavePlayer = Cast<USoundNodeWavePlayer>(SoundNode))
					if (!WavePlayer->GetSoundWave()) Errors.Add(FString::Printf(TEXT("Wave Player %s has no Sound Wave"), *SoundNode->GetName()));
			}
		}
		if (Graph && RootNodes.Num() != 1) Errors.Add(TEXT("Sound Cue graph must contain exactly one root"));
		if (Cue && Graph && RootNodes.Num() == 1 && RootNodes[0]->Pins.Num() == 1)
		{
			USoundNode* RootSoundNode = nullptr;
			if (RootNodes[0]->Pins[0]->LinkedTo.Num() == 1)
				if (USoundCueGraphNode* LinkedGraphNode = Cast<USoundCueGraphNode>(RootNodes[0]->Pins[0]->LinkedTo[0]->GetOwningNode()))
					RootSoundNode = LinkedGraphNode->SoundNode;
			if (RootSoundNode != Cue->FirstNode) Errors.Add(TEXT("Cue FirstNode does not match the root graph connection"));
			if (!Cue->FirstNode) Errors.Add(TEXT("Sound Cue root is not connected to a sound node"));
		}
		if (Cue)
		{
			for (const TObjectPtr<USoundNode>& Node : Cue->AllNodes)
				if (Node && !GraphSoundNodes.Contains(Node))
					Errors.Add(FString::Printf(TEXT("Sound Node %s is registered but missing from the graph"), *Node->GetName()));
			for (USoundNode* Node : GraphSoundNodes)
				if (!Cue->AllNodes.Contains(Node))
					Errors.Add(FString::Printf(TEXT("Graph Sound Node %s is missing from the cue's node list"), *Node->GetName()));
			TSet<const USoundNode*> Visiting;
			TSet<const USoundNode*> Visited;
			if (SoundCueNodeHasCycle(Cue->FirstNode, Visiting, Visited)) Errors.Add(TEXT("Sound Cue child graph contains a cycle"));
			if (Cue->FirstNode)
			{
				for (USoundNode* Node : GraphSoundNodes)
					if (!Visited.Contains(Node)) Warnings.Add(FString::Printf(TEXT("Sound Node %s is disconnected from the cue output"), *Node->GetName()));
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Cue ? Cue->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("validation_scope"), TEXT("sound_cue_graph_and_node_references"));
		Writer->WriteValue(TEXT("node_count"), GraphSoundNodes.Num());
		Writer->WriteValue(TEXT("connected_root"), ConnectedInputs > 0);
		Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Cue && Cue->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString SoundCueGraphOperation(USoundCue* Cue, const FSoundCueGraphReq& Body)
	{
		if (!Cue) throw std::runtime_error("Asset is not a Sound Cue");
		UEdGraph* Graph = Cue->GetGraph();
		if (!Graph) throw std::runtime_error("Sound Cue graph is missing");
		const FString Operation = Body.Operation.TrimStartAndEnd().ToLower();
		bool bWouldChange = false;
		bool bChanged = false;
		bool bSaved = false;
		FString ResultNodeId = Body.NodeId;
		USoundCueGraphNode_Base* TargetGraphNode = nullptr;
		USoundCueGraphNode* TargetSoundGraphNode = nullptr;
		USoundNode* TargetSoundNode = nullptr;

		if (Operation == TEXT("add_node"))
		{
			UClass* NodeClass = LoadClass<USoundNode>(nullptr, *Body.NodeClass);
			if (!NodeClass || NodeClass->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated))
				throw std::runtime_error("node_class must identify a concrete USoundNode class");
			const bool bWavePlayerClass = NodeClass->IsChildOf(USoundNodeWavePlayer::StaticClass());
			if (Body.bSetLooping && !bWavePlayerClass) throw std::runtime_error("looping can only be set when adding a SoundNodeWavePlayer");
			USoundWave* Wave = Body.WavePath.IsEmpty() ? nullptr : Cast<USoundWave>(LoadAsset(Body.WavePath));
			if (!Body.WavePath.IsEmpty() && !Wave) throw std::runtime_error("wave_path must identify a Sound Wave asset");
			if (bWavePlayerClass && !Wave) throw std::runtime_error("Wave Player nodes require wave_path");
			if (!bWavePlayerClass && !Body.WavePath.IsEmpty()) throw std::runtime_error("wave_path is only valid for a SoundNodeWavePlayer node");
			if (!Body.Properties.IsEmpty())
			{
				USoundNode* Probe = NewObject<USoundNode>(GetTransientPackage(), NodeClass);
				ValidateCueNodePropertyMap(Probe, Body.Properties);
				ApplyCueNodePropertyMap(Probe, Body.Properties);
			}
			bWouldChange = true;
			if (!Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddSoundCueNode", "Add Sound Cue Node"));
				Cue->Modify(); Graph->Modify();
				USoundNode* NewNode = Cue->ConstructSoundNode<USoundNode>(NodeClass, false);
				if (NewNode->GetMaxChildNodes() > 0 && NewNode->ChildNodes.Num() == 0) NewNode->CreateStartingConnectors();
				if (USoundNodeWavePlayer* WavePlayer = Cast<USoundNodeWavePlayer>(NewNode))
				{
					WavePlayer->SetSoundWave(Wave);
					if (Body.bSetLooping) WavePlayer->bLooping = Body.bLooping;
				}
				if (!Body.Properties.IsEmpty()) ApplyCueNodePropertyMap(NewNode, Body.Properties);
				USoundCueGraphNode* NewGraphNode = Cast<USoundCueGraphNode>(NewNode->GetGraphNode());
				if (!NewGraphNode) throw std::runtime_error("UE failed to create the Sound Cue graph node");
				NewGraphNode->NodePosX = Body.PositionX;
				NewGraphNode->NodePosY = Body.PositionY;
				NewNode->PostEditChange();
				ResultNodeId = CueGraphNodeId(NewGraphNode);
				bChanged = true;
			}
		}
		else if (Operation == TEXT("connect"))
		{
			USoundCueGraphNode_Base* SourceGraphNode = FindCueGraphNode(Graph, Body.SourceNodeId);
			TargetGraphNode = FindCueGraphNode(Graph, Body.TargetNodeId);
			if (!SourceGraphNode || !TargetGraphNode) throw std::runtime_error("source_node_id and target_node_id must identify graph nodes in this cue");
			if (Cast<USoundCueGraphNode_Root>(SourceGraphNode)) throw std::runtime_error("Sound Cue root cannot be used as a connection source");
			UEdGraphPin* OutputPin = SourceGraphNode->GetOutputPin();
			if (!OutputPin) throw std::runtime_error("source node has no output pin");
			if (Body.InputIndex < 0 || Body.InputIndex >= TargetGraphNode->GetInputCount())
				throw std::runtime_error("input_index is outside the target node's input pins");
			UEdGraphPin* InputPin = TargetGraphNode->GetInputPin(Body.InputIndex);
			if (InputPin->LinkedTo.Contains(OutputPin))
				return SoundCueGraphActionJson(Cue, Operation, Body.TargetNodeId, false, false, Body.bDryRun, false);
			if (InputPin->LinkedTo.Num() > 0 && !Body.bReplaceExisting)
				throw std::runtime_error("target input is already connected; set replace_existing=true to replace it");
			const UEdGraphSchema* Schema = Graph->GetSchema();
			if (!Schema) throw std::runtime_error("Sound Cue graph schema is unavailable");
			const FPinConnectionResponse Response = Schema->CanCreateConnection(OutputPin, InputPin);
			if (Response.Response == CONNECT_RESPONSE_DISALLOW)
				throw std::runtime_error(TCHAR_TO_UTF8(*Response.Message.ToString()));
			bWouldChange = true;
			if (!Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "ConnectSoundCueNodes", "Connect Sound Cue Nodes"));
				Cue->Modify(); Graph->Modify(); SourceGraphNode->Modify(); TargetGraphNode->Modify();
				if (!Schema->TryCreateConnection(OutputPin, InputPin)) throw std::runtime_error("Sound Cue schema rejected the connection");
				bChanged = true;
			}
		}
		else if (Operation == TEXT("disconnect"))
		{
			TargetGraphNode = FindCueGraphNode(Graph, Body.NodeId);
			if (!TargetGraphNode) throw std::runtime_error("node_id does not identify a graph node in this cue");
			if (Body.InputIndex < 0 || Body.InputIndex >= TargetGraphNode->GetInputCount())
				throw std::runtime_error("input_index is outside the target node's input pins");
			UEdGraphPin* InputPin = TargetGraphNode->GetInputPin(Body.InputIndex);
			bWouldChange = InputPin->LinkedTo.Num() > 0;
			if (bWouldChange && !Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "DisconnectSoundCueNode", "Disconnect Sound Cue Node"));
				Cue->Modify(); Graph->Modify(); TargetGraphNode->Modify();
				InputPin->BreakAllPinLinks();
				bChanged = true;
			}
		}
		else if (Operation == TEXT("delete_node"))
		{
			TargetGraphNode = FindCueGraphNode(Graph, Body.NodeId);
			TargetSoundGraphNode = Cast<USoundCueGraphNode>(TargetGraphNode);
			TargetSoundNode = TargetSoundGraphNode ? TargetSoundGraphNode->SoundNode : nullptr;
			if (!TargetSoundGraphNode || !TargetSoundNode) throw std::runtime_error("node_id must identify a deletable Sound Node; the root cannot be deleted");
			if (!TargetGraphNode->CanUserDeleteNode()) throw std::runtime_error("Sound Cue node does not allow deletion");
			bWouldChange = true;
			if (!Body.bDryRun && !Body.bConfirm) throw std::runtime_error("deleting a Sound Cue node requires confirm=true");
			if (!Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "DeleteSoundCueNode", "Delete Sound Cue Node"));
				Cue->Modify(); Graph->Modify(); TargetGraphNode->Modify(); TargetSoundNode->Modify();
				for (UEdGraphPin* Pin : TargetGraphNode->Pins) if (Pin) Pin->BreakAllPinLinks();
				Graph->RemoveNode(TargetGraphNode);
				Cue->AllNodes.Remove(TargetSoundNode);
				bChanged = true;
			}
		}
		else if (Operation == TEXT("move_node"))
		{
			TargetGraphNode = FindCueGraphNode(Graph, Body.NodeId);
			if (!TargetGraphNode) throw std::runtime_error("node_id does not identify a graph node in this cue");
			bWouldChange = TargetGraphNode->NodePosX != Body.PositionX || TargetGraphNode->NodePosY != Body.PositionY;
			if (bWouldChange && !Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "MoveSoundCueNode", "Move Sound Cue Node"));
				Cue->Modify(); Graph->Modify(); TargetGraphNode->Modify();
				TargetGraphNode->NodePosX = Body.PositionX;
				TargetGraphNode->NodePosY = Body.PositionY;
				bChanged = true;
			}
		}
		else if (Operation == TEXT("layout"))
		{
			const TMap<USoundCueGraphNode_Base*, FIntPoint> Layout = BuildSoundCueLayout(Cue);
			for (const auto& Entry : Layout)
				if (Entry.Key->NodePosX != Entry.Value.X || Entry.Key->NodePosY != Entry.Value.Y) { bWouldChange = true; break; }
			if (bWouldChange && !Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "LayoutSoundCueGraph", "Layout Sound Cue Graph"));
				Cue->Modify(); Graph->Modify();
				for (const auto& Entry : Layout)
				{
					Entry.Key->Modify();
					Entry.Key->NodePosX = Entry.Value.X;
					Entry.Key->NodePosY = Entry.Value.Y;
				}
				bChanged = true;
			}
		}
		else if (Operation == TEXT("set_node_settings"))
		{
			TargetSoundGraphNode = Cast<USoundCueGraphNode>(FindCueGraphNode(Graph, Body.NodeId));
			TargetSoundNode = TargetSoundGraphNode ? TargetSoundGraphNode->SoundNode : nullptr;
			if (!TargetSoundNode) throw std::runtime_error("node_id must identify a Sound Node graph entry");
			USoundNodeWavePlayer* WavePlayer = Cast<USoundNodeWavePlayer>(TargetSoundNode);
			USoundWave* NewWave = WavePlayer ? WavePlayer->GetSoundWave() : nullptr;
			if (Body.bSetWave)
			{
				if (!WavePlayer) throw std::runtime_error("wave_path can only be set on a SoundNodeWavePlayer");
				NewWave = Body.WavePath.IsEmpty() ? nullptr : Cast<USoundWave>(LoadAsset(Body.WavePath));
				if (!Body.WavePath.IsEmpty() && !NewWave) throw std::runtime_error("wave_path must identify a Sound Wave asset");
			}
			USoundNode* Probe = DuplicateObject<USoundNode>(TargetSoundNode, GetTransientPackage());
			if (!Body.Properties.IsEmpty()) ApplyCueNodePropertyMap(Probe, Body.Properties);
			const bool bPropertiesChanged = !Body.Properties.IsEmpty()
				&& ObjUtils::SerializeObjectToJson(Probe) != ObjUtils::SerializeObjectToJson(TargetSoundNode);
			const bool bWaveChanged = Body.bSetWave && WavePlayer->GetSoundWave() != NewWave;
			const bool bLoopingChanged = Body.bSetLooping && WavePlayer && static_cast<bool>(WavePlayer->bLooping) != Body.bLooping;
			if (Body.bSetLooping && !WavePlayer) throw std::runtime_error("looping can only be set on a SoundNodeWavePlayer");
			bWouldChange = bPropertiesChanged || bWaveChanged || bLoopingChanged;
			if (bWouldChange && !Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetSoundCueNodeSettings", "Set Sound Cue Node Settings"));
				Cue->Modify(); Graph->Modify(); TargetSoundGraphNode->Modify(); TargetSoundNode->Modify();
				if (!Body.Properties.IsEmpty()) ApplyCueNodePropertyMap(TargetSoundNode, Body.Properties);
				if (Body.bSetWave) WavePlayer->SetSoundWave(NewWave);
				if (Body.bSetLooping) WavePlayer->bLooping = Body.bLooping;
				TargetSoundNode->PostEditChange();
				bChanged = true;
			}
		}
		else if (Operation == TEXT("compile"))
		{
			bWouldChange = true;
			if (!Body.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "CompileSoundCueGraph", "Compile Sound Cue Graph"));
				Cue->Modify(); Graph->Modify();
				Cue->CompileSoundNodesFromGraphNodes();
				bChanged = true;
			}
		}
		else
		{
			throw std::runtime_error("operation must be add_node, connect, disconnect, delete_node, move_node, layout, set_node_settings, or compile");
		}

		if (bChanged)
		{
			Cue->CompileSoundNodesFromGraphNodes();
			Cue->CacheAggregateValues();
			Cue->PostEditChange();
			Graph->NotifyGraphChanged();
			MarkAssetDirty(Cue);
			SaveIfRequested(Cue, Body.bSave);
			bSaved = Body.bSave;
		}
		return SoundCueGraphActionJson(Cue, Operation, ResultNodeId, bChanged, bWouldChange, Body.bDryRun, bSaved);
	}

	FProperty* FindBatchProperty(UStruct* Struct, const FString& Name)
	{
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
			if ((*It)->GetName().Equals(Name, ESearchCase::IgnoreCase)) return *It;
		return nullptr;
	}

	void ValidateBatchPropertyPath(UObject* Asset, const FString& Path)
	{
		TArray<FString> Parts;
		Path.ParseIntoArray(Parts, TEXT("."), true);
		if (Parts.IsEmpty()) throw std::runtime_error("property path is empty");
		UStruct* Struct = Asset->GetClass();
		for (int32 Index = 0; Index < Parts.Num() - 1; ++Index)
		{
			FProperty* Property = FindBatchProperty(Struct, Parts[Index]);
			if (!Property) throw std::runtime_error("property path does not exist");
			if (FStructProperty* StructProperty = CastField<FStructProperty>(Property))
			{
				Struct = StructProperty->Struct;
				continue;
			}
			if (FArrayProperty* ArrayProperty = CastField<FArrayProperty>(Property))
			{
				int32 ElementIndex = INDEX_NONE;
				if (!Parts.IsValidIndex(++Index) || !LexTryParseString(ElementIndex, *Parts[Index]) || ElementIndex < 0)
					throw std::runtime_error("batch array property path requires a nonnegative index");
				if (Index == Parts.Num() - 1) return;
				FStructProperty* InnerStruct = CastField<FStructProperty>(ArrayProperty->Inner);
				if (!InnerStruct) throw std::runtime_error("batch nested array editing supports struct elements only");
				Struct = InnerStruct->Struct;
				continue;
			}
			if (CastField<FObjectPropertyBase>(Property))
				throw std::runtime_error("batch nested object references are not supported safely");
			throw std::runtime_error("batch property path cannot traverse this property type");
		}
	}

	TArray<FString> ValidateBatchPropertyValues(UObject* Asset, const FAssetPropertyReq& Operation)
	{
		if (Asset->IsA<UWorld>() || Asset->IsA<ULevel>())
			throw std::runtime_error("world and level edits require dedicated editor routes");
		if (Operation.Properties.IsEmpty()) throw std::runtime_error("properties must contain at least one entry");
		UObject* Probe = DuplicateObject<UObject>(Asset, GetTransientPackage(),
			MakeUniqueObjectName(GetTransientPackage(), Asset->GetClass(), TEXT("UE5MCP_BatchProbe")));
		if (!Probe) throw std::runtime_error("asset could not be duplicated for batch preflight");
		Probe->SetFlags(RF_Transient);
		TArray<FString> Keys;
		Operation.Properties.GetKeys(Keys);
		Keys.Sort();
		for (const FString& Key : Keys)
		{
			ValidateBatchPropertyPath(Asset, Key);
			ObjUtils::SetPropertyValueFromString(Probe, Key, Operation.Properties[Key]);
		}
		return Keys;
	}

	UEditorAssetSubsystem* AssetSubsystem()
	{
		if (!GEditor)
			throw std::runtime_error("Unreal editor is not available");
		return GEditor->GetEditorSubsystem<UEditorAssetSubsystem>();
	}

	UStaticMeshEditorSubsystem* StaticMeshSubsystem()
	{
		if (!GEditor)
			throw std::runtime_error("Unreal editor is not available");
		return GEditor->GetEditorSubsystem<UStaticMeshEditorSubsystem>();
	}

	USkeletalMeshEditorSubsystem* SkeletalMeshSubsystem()
	{
		if (!GEditor)
			throw std::runtime_error("Unreal editor is not available");
		return GEditor->GetEditorSubsystem<USkeletalMeshEditorSubsystem>();
	}

	UMaterialExpression* FindMaterialExpression(UMaterial* Material, const FString& Name)
	{
		if (!Material)
			return nullptr;
		for (UMaterialExpression* Expression : Material->GetExpressions())
			if (Expression && Expression->GetName() == Name)
				return Expression;
		return nullptr;
	}

	UWidgetBlueprint* LoadWidgetBlueprint(const FString& Path)
	{
		UWidgetBlueprint* Blueprint = Cast<UWidgetBlueprint>(LoadAsset(Path));
		if (!Blueprint || !Blueprint->WidgetTree)
			throw std::runtime_error("Asset is not a Widget Blueprint");
		return Blueprint;
	}
}

void BuildAssetRouter(TSharedPtr<HttpApp> App)
{
	App->Get("/assets/capabilities", [](const FHttpContext<void, FString>& C)
	{
		struct FFamily
		{
			const TCHAR* Name;
			bool Generic;
			bool Inspect;
			bool Edit;
			bool Create;
			bool Compile;
			bool Validate;
			const TCHAR* Notes;
		};
		const FFamily Families[] = {
			{TEXT("blueprint"), true, true, true, true, true, false, TEXT("Blueprint graph, variable, function, and component routes")},
			{TEXT("widget_blueprint"), true, true, true, true, true, false, TEXT("Widget tree and Blueprint routes")},
			{TEXT("data_table"), true, true, true, false, false, false, TEXT("Row get, upsert, and delete")},
			{TEXT("data_asset"), true, true, false, true, false, true, TEXT("Typed creation and class validation; property editing is generic")},
			{TEXT("primary_data_asset"), true, true, false, true, false, true, TEXT("No primary bundle or management editor")},
			{TEXT("input_action"), true, true, false, false, false, false, TEXT("Reflected settings only")},
			{TEXT("input_mapping_context"), true, true, true, false, false, false, TEXT("Typed key map, unmap, and replace")},
			{TEXT("behavior_tree"), true, true, true, true, true, true, TEXT("Native graph authoring, compound decorators, static/dynamic subtrees and guarded live PIE replacement; custom providers/Blueprint runtime gates pending")},
			{TEXT("blackboard"), true, true, true, true, false, true, TEXT("Typed local/inherited key and native default settings, structural validation, selector rename, transactions and persistence; custom/struct settings pending")},
			{TEXT("sound_wave"), true, true, true, true, false, true, TEXT("WAV source inspection, guarded import/reimport, reflected settings, and class-level validation")},
			{TEXT("sound_cue"), true, true, false, false, false, true, TEXT("No Sound Cue graph authoring")},
			{TEXT("sound_class"), true, true, false, false, false, true, TEXT("Reflected settings and class-level validation")},
			{TEXT("sound_mix"), true, true, false, false, false, true, TEXT("Reflected settings and class-level validation")},
			{TEXT("sound_submix"), true, true, false, false, false, true, TEXT("Reflected settings and class-level validation")},
			{TEXT("level_sequence"), true, true, true, true, false, true, TEXT("Initial bindings, tracks, keys, cameras, cuts, shots, and subsequences")},
			{TEXT("world"), true, true, true, true, false, true, TEXT("Current-world and map lifecycle adapters")},
			{TEXT("navigation"), false, true, true, true, true, true, TEXT("Ordinary-map native bounds/build and bounded editor-world projection/path queries; partition builders and broader nav authoring pending")},
			{TEXT("navigation_query_filter"), true, true, true, true, true, true, TEXT("Direct-native-parent NavigationQueryFilter Blueprints: area costs/exclusions and flag masks, structural validation, compilation and native cache invalidation; custom/inherited filters pending")},
			{TEXT("navigation_area"), true, true, true, true, true, true, TEXT("Direct-native-parent NavArea Blueprints: costs, color, supported agents, compilation, native registration and undo refresh; custom/inherited area bases pending")},
			{TEXT("level"), false, true, true, false, false, false, TEXT("Streaming sublevel inspection, visibility, add, and remove")},
			{TEXT("level_instance"), false, true, true, true, false, true, TEXT("Native lifecycle, source edit/commit/discard, confirmed break, transforms, and cycle validation; packing/overrides pending")},
			{TEXT("scene"), false, true, true, true, false, false, TEXT("Placed actor and component adapters")},
			{TEXT("material"), true, true, true, false, true, true, TEXT("Expression editing and compile")},
			{TEXT("material_instance"), true, true, true, false, false, true, TEXT("Typed parameters, static switches, parent/reset, and orphaned-override validation")},
			{TEXT("texture"), true, true, true, true, true, true, TEXT("Source inspection, guarded image import/reimport, reflected settings, and resource rebuild")},
			{TEXT("static_mesh"), true, true, true, true, false, false, TEXT("OBJ/glTF/GLB source diagnostics and guarded import/reimport; typed material and LOD settings")},
			{TEXT("skeletal_mesh"), true, false, true, false, false, false, TEXT("Typed material and section settings; inspection is generic")},
			{TEXT("physics_asset"), true, true, true, false, false, true, TEXT("Body settings/profiles, convex and primitive shapes, constraints/drives, and collision-pair editing")},
			{TEXT("animation_sequence"), true, true, true, true, false, true, TEXT("Source tracks, timing, attributes, compression, notifies, curves, and markers")},
			{TEXT("animation_montage"), true, false, true, false, false, false, TEXT("Section editing; inspection is generic")},
			{TEXT("animation_blueprint"), true, true, true, false, true, true, TEXT("Nested graphs, state/transition lifecycle, pose links, layout, compile, and validation")},
			{TEXT("blend_space"), true, true, true, false, false, true, TEXT("Persistent sample IDs, sample and axis editing, triangulation rebuild, and preview")},
			{TEXT("control_rig"), true, true, true, false, true, false, TEXT("Typed hierarchy controls, enum-backed integers, shape/animation settings, proxy drivers, per-dimension limits, space switching, and channel hosts")},
			{TEXT("modular_rig"), true, true, true, false, true, true, TEXT("Module, connector, array-target, override, and binding editing plus recompilation")},
			{TEXT("state_tree"), true, true, true, true, true, true, TEXT("Native hierarchy, transitions, schema-approved struct tasks/conditions/evaluators, scalar settings, compile and transient validation; native execution/undo and cold persistence verified. Root/state scalar, enum and native struct parameter bags and direct bindings supported; Local linked subtrees, inherited parameter overrides/reset and retargeting supported; External linked assets support isolated dependency previews, caller propagation, grouped transactions/save and runtime undo; reference/container parameters, property functions and Blueprint UObject settings pending")},
			{TEXT("environment_query"), true, true, true, true, true, true, TEXT("Native EQS option/test graphs, nested matching-type composite generators, typed scalar/class/provider settings and named parameters; live PIE asynchronous requests/results, typed parameters, cancellation and cleanup; forced item layouts/custom providers pending")},
			{TEXT("data_registry"), true, false, false, false, false, false, TEXT("Generic UObject access only; no registry adapter")},
			{TEXT("metasound"), true, false, false, false, false, false, TEXT("Generic UObject access only when the optional plugin is enabled")},
            {TEXT("material_parameter_collection"), true, true, true, true, false, true, TEXT("Native collection discovery/factory creation/typed scalar-vector defaults/add/rename/reorder/delete/full snapshots, expression collection references and reference paging, structural diagnostics and current Editor/PIE world effective values/overrides/reset; verified live with cold reload (2026-11-02). Loaded-reference preflight is not a complete unloaded dependency audit. Native callbacks may compile/update resources; render output unverified")},
            {TEXT("material_expression_metadata"), false, true, true, false, false, false, TEXT("Native material/function expression discovery/metadata group-sort-description, material group ordering entries, scalar-vector-static-font defaults, scalar UI controls/enumeration refs, instance enumeration slots, primitive-data bindings, channel labels, sample policies and texture references; verified live with cold reload (2026-11-02). Native callbacks can compile/reconstruct pins")},
			{TEXT("render_target"), true, true, true, true, false, false, TEXT("Dedicated loaded 2D/cube/volume/2D-array inspection/discovery, native-factory source-free creation, typed gamma/format/HDR/UAV/mip settings where supported, dimensions and authored clear color, optional native snapshots; verified live. Native conversion create/update and 2D PNG/EXR/HDR and 2D/cube/volume/array DDS export need GPU readback: dry-run metadata and guards verified, real execution refused under -nullrhi and unverified")},
			{TEXT("texture_array"), true, true, true, true, false, false, TEXT("Source-backed Texture2DArray source-header/reference inspection, loaded discovery/direct source consumers, source-header compatibility diagnostics, typed address modes, guarded source-list replacement/reordering with native regeneration callbacks and native-factory creation; verified live with cold reload (2026-11-02). Dedicated import/explicit rebuild/derived-data validation pending; array render targets are a separate render_target subtype")},
            {TEXT("runtime_virtual_texture"), true, true, true, true, false, false, TEXT("RuntimeVirtualTexture native asset inspect/discover/create/duplicate, layer and compression policy, guarded asset settings, component settings/references/per-platform policy, primitive writer lists/LOD/main pass, native volume create/delete/transform and direct material/component/primitive consumers; verified live. Streaming-mip build needs a rendering RHI (dry run and guards verified only); producer residency and rendered output unverified; streaming UTexture and builder containers are separate")},
            {TEXT("virtual_texture_builder"), true, true, true, true, false, false, TEXT("Streaming runtime-VT builder native container inspect/discovery/create and direct component refs verified live. Separate-mobile policy needs the project mobile virtual-texturing setting (only the refusal is verified). Empty container creation does not generate embedded textures; BuildTexture/capture/hash freshness/platform-data/page residency validation pending")},
			{TEXT("landscape"), false, false, false, false, false, false, TEXT("No dedicated Landscape adapter")},
			{TEXT("foliage"), false, false, false, false, false, false, TEXT("No dedicated foliage adapter")},
			{TEXT("niagara"), true, false, false, false, false, false, TEXT("Generic UObject access only when the optional plugin is enabled")},
			{TEXT("pcg"), true, false, false, false, false, false, TEXT("Generic UObject access only when the optional plugin is enabled")},
		};
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("schema_version"), 2);
		Writer->WriteArrayStart(TEXT("asset_families"));
		for (const TCHAR* Family : {TEXT("blueprint"), TEXT("widget_blueprint"), TEXT("data_table"), TEXT("data_asset"),
			TEXT("primary_data_asset"), TEXT("input_action"), TEXT("input_mapping_context"), TEXT("behavior_tree"),
			TEXT("blackboard"), TEXT("sound_wave"), TEXT("sound_cue"), TEXT("sound_class"), TEXT("sound_mix"),
			TEXT("sound_submix"), TEXT("level_sequence"), TEXT("world"), TEXT("navigation_query_filter"), TEXT("navigation_area"), TEXT("material"), TEXT("material_instance"),
			TEXT("texture"), TEXT("static_mesh"), TEXT("skeletal_mesh"), TEXT("physics_asset"),
			TEXT("animation_sequence"), TEXT("animation_montage"), TEXT("animation_blueprint"), TEXT("blend_space"),
			TEXT("control_rig"), TEXT("modular_rig")}) Writer->WriteValue(Family);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("operations"));
		for (const TCHAR* Operation : {TEXT("inspect"), TEXT("validate"), TEXT("set_properties"), TEXT("save"), TEXT("layout"),
			TEXT("cinematic_metadata"), TEXT("cinematic_sections"), TEXT("cinematic_mutation"), TEXT("create_data_asset"),
			TEXT("map_input"), TEXT("unmap_input"), TEXT("create_behavior_tree"), TEXT("create_blackboard"), TEXT("blackboard_keys"), TEXT("audio_settings")})
			Writer->WriteValue(Operation);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("world_operations"));
		for (const TCHAR* Operation : {TEXT("inspect_current"), TEXT("save_current"), TEXT("spawn_actor"), TEXT("edit_actor_transform"), TEXT("edit_actor_properties")})
			Writer->WriteValue(Operation);
		Writer->WriteArrayEnd();
		Writer->WriteObjectStart(TEXT("families"));
		for (const FFamily& Family : Families)
		{
			const FString FamilyName(Family.Name);
			const TCHAR* OptionalPlugin = nullptr;
			if (FamilyName == TEXT("state_tree")) OptionalPlugin = TEXT("StateTree");
			else if (FamilyName == TEXT("metasound")) OptionalPlugin = TEXT("Metasound");
			else if (FamilyName == TEXT("niagara")) OptionalPlugin = TEXT("Niagara");
			else if (FamilyName == TEXT("pcg")) OptionalPlugin = TEXT("PCG");
			const TSharedPtr<IPlugin> Plugin = OptionalPlugin ? IPluginManager::Get().FindPlugin(OptionalPlugin) : nullptr;
			const bool bEngineAvailable = !OptionalPlugin || (Plugin.IsValid() && Plugin->IsEnabled());
			const bool bAdapter = bEngineAvailable && (Family.Inspect || Family.Edit || Family.Create || Family.Compile || Family.Validate);
			Writer->WriteObjectStart(Family.Name);
			Writer->WriteValue(TEXT("generic"), bEngineAvailable && Family.Generic);
			Writer->WriteValue(TEXT("inspect"), bEngineAvailable && Family.Inspect);
			Writer->WriteValue(TEXT("edit"), bEngineAvailable && Family.Edit);
			Writer->WriteValue(TEXT("spawn_or_create"), bEngineAvailable && Family.Create);
			Writer->WriteValue(TEXT("compile_or_rebuild"), bEngineAvailable && Family.Compile);
			Writer->WriteValue(TEXT("validate"), bEngineAvailable && Family.Validate);
			Writer->WriteValue(TEXT("engine_available"), bEngineAvailable);
			Writer->WriteValue(TEXT("adapter_available"), bAdapter);
			Writer->WriteValue(TEXT("support_level"), bAdapter ? TEXT("partial") : bEngineAvailable && Family.Generic ? TEXT("generic") : TEXT("unavailable"));
			Writer->WriteValue(TEXT("notes"), Family.Notes);
			if (FamilyName == TEXT("runtime_virtual_texture") || FamilyName == TEXT("virtual_texture_builder"))
            {
                Writer->WriteValue(TEXT("implementation_status"), TEXT("verified_live_partial"));
                Writer->WriteValue(TEXT("dedicated_adapters_build_verified"), true);
                Writer->WriteValue(TEXT("dedicated_adapters_runtime_verified"), true);
                Writer->WriteValue(TEXT("rendered_output_verified"), false);
                Writer->WriteValue(TEXT("generated_streaming_data_verified"), false);
            }
            if (FamilyName == TEXT("material_parameter_collection") || FamilyName == TEXT("material_expression_metadata"))
            {
                Writer->WriteValue(TEXT("implementation_status"), TEXT("verified_live_partial"));
                Writer->WriteValue(TEXT("dedicated_adapters_build_verified"), true);
                Writer->WriteValue(TEXT("dedicated_adapters_runtime_verified"), true);
                Writer->WriteValue(TEXT("dedicated_adapters_persistence_verified"), true);
                Writer->WriteValue(TEXT("rendered_output_verified"), false);
                Writer->WriteValue(TEXT("asset_mutations_transactional"), true);
                Writer->WriteValue(TEXT("native_callbacks_can_compile"), true);
                Writer->WriteValue(TEXT("dependent_callbacks_atomic"), false);
                if (FamilyName == TEXT("material_parameter_collection"))
                {
                    Writer->WriteValue(TEXT("world_instance_controls"), true);
                    Writer->WriteValue(TEXT("world_instance_controls_transactional"), false);
                    Writer->WriteValue(TEXT("world_inspection_can_initialize_instance"), true);
                    Writer->WriteValue(TEXT("validation_scope"), TEXT("authored_collection_structure_and_loaded_direct_expression_identity"));
                    Writer->WriteValue(TEXT("complete_unloaded_dependency_audit"), false);
                }
            }
			if (FamilyName == TEXT("render_target"))
			{
				Writer->WriteValue(TEXT("implementation_status"), TEXT("verified_live_partial"));
				Writer->WriteValue(TEXT("dedicated_adapters_build_verified"), true);
				Writer->WriteValue(TEXT("dedicated_adapters_runtime_verified"), true);
				Writer->WriteValue(TEXT("gpu_readback_verified"), false);
				Writer->WriteArrayStart(TEXT("dedicated_subtypes"));
				for (const TCHAR* Subtype : {TEXT("2d"), TEXT("cube"), TEXT("volume"), TEXT("2d_array")}) Writer->WriteValue(Subtype);
				Writer->WriteArrayEnd();
			}

			Writer->WriteObjectEnd();
		}
		Writer->WriteObjectEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/assets/dirty-state", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		const bool bDirty = Asset->GetOutermost() && Asset->GetOutermost()->IsDirty();
		return C.TextResponse(FString::Printf(TEXT("{\"asset_path\":\"%s\",\"dirty\":%s}"), *Asset->GetPathName(), bDirty ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Get("/data-assets/inspect", [](const FHttpContext<void, FString>& C)
	{
		UDataAsset* DataAsset = Cast<UDataAsset>(LoadAsset(C.Query("asset_path")));
		if (!DataAsset) throw std::runtime_error("Asset is not a Data Asset");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(DataAsset), TEXT("application/json"));
	});

	App->Post("/data-assets/create", [](const FHttpContext<FDataAssetCreateReq, FString>& C)
	{
		auto Body = C.RequestBody();
		return C.TextResponse(ClassUtils::CreateDataAsset(Body.AssetPath, Body.AssetClass));
	});

	App->Post("/data-assets/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UDataAsset* DataAsset = Cast<UDataAsset>(LoadAsset(Body.AssetPath));
		if (!DataAsset) throw std::runtime_error("Asset is not a Data Asset");
		if (!Body.AssetClass.IsEmpty())
		{
			UClass* ExpectedClass = LoadClass<UObject>(nullptr, *Body.AssetClass);
			if (!ExpectedClass || !DataAsset->GetClass()->IsChildOf(ExpectedClass))
				throw std::runtime_error("asset_class does not match the Data Asset class");
		}
		return C.TextResponse(FString::Printf(TEXT("{\"valid\":true,\"class\":\"%s\",\"primary\":%s}"), *DataAsset->GetClass()->GetPathName(), DataAsset->IsA<UPrimaryDataAsset>() ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

 App->Get("/behavior-trees/runtime", [](const FHttpContext<void, FString>& C)
 {
  int32 Instance=-1; const FString I=C.Query("pie_instance"); if(!I.IsEmpty() && (!LexTryParseString(Instance,*I) || Instance < -1)) throw std::runtime_error("pie_instance requires an integer >= -1");
  return C.TextResponse(BehaviorTreeGraphUtils::Runtime(C.Query("component_path"),Instance),TEXT("application/json"));
 });
 App->Post("/behavior-trees/runtime/dynamic-subtree", [](const FHttpContext<FBehaviorTreeRuntimeReq, FString>& C)
 {
  return C.TextResponse(BehaviorTreeGraphUtils::RuntimeControl(C.RequestBody()),TEXT("application/json"));
 });
 App->Get("/state-trees/bindables", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::InspectBindables(C.Query("asset_path"),C.Query("target_id")),TEXT("application/json")); });
 App->Get("/ai-perception/classes", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PerceptionUtils::Discover(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Post("/ability-system/runtime/cues/execute", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::ExecuteCue(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/effect-definition/evaluate", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::EvaluateEffectDefinition(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ability-system/calculation-definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectCalculation(C.Query("class_path")),TEXT("application/json")); });
 App->Post("/ability-system/runtime/attribute-sets", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::AddAttributeSet(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ability-system/attribute-definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectAttributeClass(C.Query("class_path")),TEXT("application/json")); });
 App->Post("/ability-system/classes/load", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::LoadClassDefinition(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ability-system/ability-definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectAbilityClass(C.Query("class_path")),TEXT("application/json")); });
 App->Get("/ability-system/effect-definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectEffectClass(C.Query("class_path")),TEXT("application/json")); });
 App->Post("/ability-system/runtime/tag-counts", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectTagCounts(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/abilities/check", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::CheckAbility(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/abilities", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::SetAbilityLevel(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/query-effects", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::QueryEffects(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/match-abilities", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::MatchAbilitiesByTags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/cancel-by-tags", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::CancelByTags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/activate-by-tags", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::ActivateByTags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/loose-tags", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::AddLooseTag(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/virtual-bones/name", [](const FHttpContext<FVirtualBoneReq,FString>& C) { return C.TextResponse(SkeletonUtils::RenameVirtualBone(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/skeletons/virtual-bones", [](const FHttpContext<FVirtualBoneReq,FString>& C) { return C.TextResponse(SkeletonUtils::DeleteVirtualBones(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/virtual-bones", [](const FHttpContext<FVirtualBoneReq,FString>& C) { return C.TextResponse(SkeletonUtils::CreateVirtualBone(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/compare", [](const FHttpContext<FCompatibleSkeletonReq,FString>& C) { return C.TextResponse(SkeletonUtils::CompareHierarchy(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/compatibility/policy", [](const FHttpContext<FCompatibleSkeletonReq,FString>& C) { return C.TextResponse(SkeletonUtils::SetCompatibilityPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/compatibility", [](const FHttpContext<FCompatibleSkeletonReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditCompatibility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/animations/retarget-source/query", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::InspectAnimationRetargetSource(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/animations/retarget-source/mesh", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::SetAnimationRetargetMesh(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/animations/retarget-source", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::SetAnimationRetargetSource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/curve-metadata/lifecycle", [](const FHttpContext<FSkeletonCurveReq,FString>& C) { return C.TextResponse(SkeletonUtils::CurveMetadataLifecycle(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/curve-metadata", [](const FHttpContext<FSkeletonCurveReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditCurveMetadata(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/retarget-sources/pose", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditStoredRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/retarget-sources/duplicate", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::DuplicateRetargetSource(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/retarget-sources/name", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::RenameRetargetSource(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/skeletons/retarget-sources", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::DeleteRetargetSource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/retarget-sources", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditRetargetSource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/retarget-sources/pose", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::InspectRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/blend-profiles/scales/query", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::InspectBlendProfileScales(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/skeletons/blend-profiles", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::DeleteBlendProfile(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/blend-profiles/references", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::InspectBlendProfileReferences(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/blend-profiles/mode", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::SetBlendProfileMode(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/blend-profiles/name", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::RenameBlendProfile(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/blend-profiles", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::CreateBlendProfile(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/blend-profiles/reset", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::ResetBlendProfileEntries(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/blend-profiles/scales", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::SetBlendProfileScales(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/translation-retargeting", [](const FHttpContext<FBoneRetargetReq,FString>& C) { return C.TextResponse(SkeletonUtils::SetTranslationRetargeting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/preview-attachments", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditPreviewAttachment(C.RequestBody(),false),TEXT("application/json")); });
 App->Post("/skeletal-meshes/preview-attachments", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditPreviewAttachment(C.RequestBody(),true),TEXT("application/json")); });
 App->Post("/skeletal-meshes/runtime/socket-transform", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::InspectRuntimeSocket(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletal-meshes/sockets/promote", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::PromoteMeshSocket(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletal-meshes/sockets/customize", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::CustomizeMeshSocket(C.RequestBody()),TEXT("application/json")); });
 App->Get("/skeletal-meshes/sockets", [](const FHttpContext<void,FString>& C) { return C.TextResponse(SkeletonUtils::InspectMeshSockets(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/skeletal-meshes/sockets", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditMeshSocket(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/skeletal-meshes/sockets", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::DeleteMeshSocket(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletal-meshes/sockets/name", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::RenameMeshSocket(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/skeletons/sockets/name", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::RenameSocket(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/skeletons/sockets", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::DeleteSocket(C.RequestBody()),TEXT("application/json")); });
 App->Post("/skeletons/sockets", [](const FHttpContext<FSkeletonSocketReq,FString>& C) { return C.TextResponse(SkeletonUtils::EditSocket(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/bones/excluded", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetBoneExcluded(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/evaluate-reference-pose", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::EvaluateRigReferencePose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/readiness", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CheckRigReadiness(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/mesh-compatibility", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CheckMeshCompatibility(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/preview-mesh", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetPreviewMesh(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/solvers/bone", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetSolverBone(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/connections", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectSolverConnections(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/goal-settings/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetSolverGoalSettings(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/solvers/goal-settings/scalar", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetSolverGoalScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/goal-settings/copy", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CopySolverGoalSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/goal-settings/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectSolverGoalSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/settings/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetSolverSettings(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/solvers/settings/scalar", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetSolverScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/settings/copy", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CopySolverSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/settings/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectSolverSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/bone-settings/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetSolverBoneSettings(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/solvers/bone-settings/scalar", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetSolverBoneScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/bone-settings/copy", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CopySolverBoneSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/bone-settings/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectSolverBoneSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/bone-settings", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ChangeSolverBoneSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectSolver(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers/goals", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ConnectGoal(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/solvers/enabled", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetSolverEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/solvers/order", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::MoveSolver(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/ik-rigs/solvers", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RemoveSolver(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/solvers", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AddSolver(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ik-rigs/solver-types", [](const FHttpContext<void,FString>& C) { const FString Limit=C.Query("limit"); return C.TextResponse(IKRigUtils::DiscoverSolvers(C.Query("search"),Limit.IsEmpty() ? 64 : FCString::Atoi(*Limit)),TEXT("application/json")); });
 App->Post("/ik-rigs/goals/transform/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectGoalTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/goals/transform/refresh-initial", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RefreshInitialGoalTransforms(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/goals/transform/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetGoalTransforms(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/goals/transform", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetGoalTransform(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/goals/weights", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetGoalWeights(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/goals/bone", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetGoalBone(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/goals/lifecycle", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::GoalLifecycle(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/goals", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CreateGoal(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/chains", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::EditChain(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/chains/lifecycle", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ChainLifecycle(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-rigs/root", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRoot(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/chains", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CreateChain(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/preview-mesh", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetPreviewMesh(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/poses/bone-rotation", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetBoneRotation(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/poses/root-offset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetRootOffset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/poses/auto-align", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AutoAlignRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/poses/snap-ground", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SnapRetargetPoseToGround(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/poses/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/poses/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/poses/lifecycle", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RetargetPoseLifecycle(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/poses", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CreateRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/poses/current", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetPose(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/rig", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetRig(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/enabled", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetOpEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/ik-retargeters/operations", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RemoveRetargetOp(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/name", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RenameRetargetOp(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/parent", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetOpParent(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/order", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::MoveRetargetOp(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/mapping/refresh", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RefreshRetargetMapping(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/mapping/auto", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AutoMapRetargetChains(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/mapping", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetMapping(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/mapping/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetMapping(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/settings/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetRetargetOpSettings(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/settings/scalar", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetOpScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/settings/copy", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CopyRetargetOpSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/settings/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetOpSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/warning", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetOpWarning(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetOp(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/defaults", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AddDefaultRetargetOps(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/setup", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::RunRetargetOpSetup(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/assign-rig", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AssignRigToRetargetOps(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations/curve-remap/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetCurveRemap(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ik-retargeters/operations/curve-remap", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::SetRetargetCurveRemap(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/chains/settings/reset", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ResetRetargetChainSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/operations", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AddRetargetOp(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ik-retargeters/operation-types", [](const FHttpContext<void,FString>& C) { const FString Limit=C.Query("limit"); return C.TextResponse(IKRigUtils::DiscoverRetargetOps(C.Query("search"),Limit.IsEmpty() ? 64 : FCString::Atoi(*Limit)),TEXT("application/json")); });
 App->Get("/ik-retargeters/operations/hierarchy", [](const FHttpContext<void,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargetHierarchy(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/ik-retargeters/poses/diagnostics", [](const FHttpContext<void,FString>& C) { return C.TextResponse(IKRigUtils::DiagnoseRetargetPoses(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/ik-retargeters/evaluate-reference-pose", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::EvaluateRetargetReferencePose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-retargeters/export-sequences", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::ExportRetargetSequences(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ik-retargeters/readiness", [](const FHttpContext<void,FString>& C) { return C.TextResponse(IKRigUtils::CheckRetargetReadiness(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/ik-retargeters/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(IKRigUtils::InspectRetargeter(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/ik-rigs/skeleton/inspect", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::InspectRigSkeleton(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/auto-fbik", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AutoSetupFBIK(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-rigs/auto-characterize", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::AutoCharacterizeRig(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ik-rigs/diagnostics", [](const FHttpContext<void,FString>& C) { return C.TextResponse(IKRigUtils::DiagnoseRig(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/ik-assets/duplicate", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::DuplicateIKAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ik-assets", [](const FHttpContext<FIKRigReq,FString>& C) { return C.TextResponse(IKRigUtils::CreateIKAsset(C.RequestBody()),TEXT("application/json")); });
 App->Get("/pose-search/channel-types", [](const FHttpContext<void,FString>& C) { const FString Limit=C.Query("limit"); return C.TextResponse(PoseSearchUtils::DiscoverChannels(C.Query("search"),Limit.IsEmpty() ? 64 : FCString::Atoi(*Limit)),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/sample-rate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetSampleRate(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels/inspect", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectChannel(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/order", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::MoveChannel(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/pose-search/schemas/channels", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RemoveChannel(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels/duplicate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::DuplicateChannel(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/scalar", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetChannelScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels/defaults", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddDefaultChannels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddChannel(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/roles/mirror-table", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetRoleMirrorTable(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/roles", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddSkeletonRole(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/normalization-set", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetNormalizationSet(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/normalization-sets/databases", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetNormalizationDatabases(C.RequestBody()),TEXT("application/json")); });
 App->Get("/pose-search/normalization-sets/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectNormalizationSet(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/pose-search/schemas/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectSchema(C.Query("asset_path")),TEXT("application/json")); });
 App->Patch("/pose-search/databases/schema", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetDatabaseSchema(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/flags", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetEntryFlags(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/pose-search/databases/entries", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RemoveEntry(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/blend-sampling", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetBlendSampling(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/composites", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddComposite(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/montages", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddMontage(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/index-tuning", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetIndexTuning(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/tags", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetTags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/assets/duplicate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::DuplicateAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/name", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetChannelName(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/enum", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetChannelEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels/reset-field", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::ResetChannelField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/preprocessor", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetPreprocessor(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/permutations", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetPermutations(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/flags", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetSchemaFlag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/index-request", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RequestIndex(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/roles/skeleton", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetRoleSkeleton(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/roles/order", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::MoveRole(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/pose-search/schemas/roles", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RemoveRole(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/roles/duplicate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::DuplicateRole(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/roles/name", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RenameRole(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/multi-animations", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddMultiAnimation(C.RequestBody()),TEXT("application/json")); });
 App->Get("/pose-search/interactions/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectInteraction(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/pose-search/interactions/items", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddInteractionItem(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/pose-search/interactions/items", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RemoveInteractionItem(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/items/order", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::MoveInteractionItem(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/items/weight", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetInteractionWeight(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/banking-weight", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetInteractionBanking(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/items/origin", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetInteractionOrigin(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/items/animation", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetInteractionAnimation(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/items/preview-mesh", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetInteractionPreview(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/interactions/items/role", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RenameInteractionRole(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/interactions/items/duplicate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::DuplicateInteractionItem(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/interactions/evaluate-warp", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::EvaluateInteractionWarp(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/entries/timing", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectEntryTiming(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/blend-range", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetBlendRange(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/animation", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::ReplaceEntryAnimation(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/vector", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetChannelVector(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/pose-bones", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetPoseBones(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/trajectory-samples", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetTrajectorySamples(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/finalize", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::FinalizeSchema(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels/group-children", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddGroupChild(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/pose-search/schemas/channels/group-children", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::RemoveGroupChild(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/group-children/order", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::MoveGroupChild(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/schemas/channels/group-children/duplicate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::DuplicateGroupChild(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/schemas/channels/color", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetChannelColor(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/preview-mesh", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetDatabasePreview(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/interval", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetDatabaseInterval(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/entries/sampling-points", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectSamplingPoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/entries/sample-root", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SampleEntryRoot(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/assets/reset-field", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::ResetAssetField(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/assets/copy-field", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::CopyAssetField(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/assets/inspect-field", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectAssetField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/enabled", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/name", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RenameEmitter(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/warmup", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetWarmup(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/user-parameters/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetUserScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/user-parameters/vector", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetUserVector(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/user-parameters/color", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetUserColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateSystem(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::CreateSystem(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/compile-request", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RequestCompile(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/enabled", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/renderers/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectRenderer(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/asset", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/name", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererName(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/renderers/reset-field", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetRendererField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/vector", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererVector(C.RequestBody()),TEXT("application/json")); });
 App->Get("/niagara/renderer-types", [](const FHttpContext<void,FString>& C) { return C.TextResponse(NiagaraUtils::DiscoverRenderers(C.Query("search")),TEXT("application/json")); });
 App->Post("/niagara/systems/renderers", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddRenderer(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/systems/renderers", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveRenderer(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/order", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::MoveRenderer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/renderers/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateRenderer(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/renderers/color", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetRendererColor(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/systems/emitters", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveEmitter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateEmitter(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/effect-type", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectType(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/fixed-bounds", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetFixedBounds(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddEmitter(C.RequestBody()),TEXT("application/json")); });
 App->Get("/niagara/emitters/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEmitterAsset(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/niagara/systems/user-parameters/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddUserScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/user-parameters/vector", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddUserVector(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/user-parameters/color", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddUserColor(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/systems/user-parameters", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveUserParameter(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/determinism", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetDeterminism(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/rapid-iteration/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetSystemRapidScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/rapid-iteration/compound", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetSystemRapidCompound(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/systems/rapid-iteration", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveSystemRapidParameter(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/modules/pin-default", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetSystemModulePinDefault(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/modules/pin-compound", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetSystemModulePinCompound(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/modules/reset-pin-default", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetSystemModulePinDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/validation-rule-types", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DiscoverValidationRules(),TEXT("application/json")); });
 App->Post("/niagara/rule-sets/rules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddEffectTypeRule(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::EditEffectTypeRule(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/rule-sets/rules/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEffectTypeRule(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/name", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleName(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/asset", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/vector", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleVector(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/color", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/rule-sets/rules/reset-field", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetEffectTypeRuleField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/text", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleText(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/text", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleText(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/string-array", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleStringArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/string-array", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleStringArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/reference-array", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleReferenceArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/rule-sets/rules/reference-array", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleReferenceArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/simulate-preview", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SimulateSystemPreview(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/validate-rules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ValidateSystemRules(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeScalabilityScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeScalabilityEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/quality", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeScalabilityQuality(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/copy-row", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::CopyEffectTypeScalabilityRow(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/reset-row", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetEffectTypeScalabilityRow(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/conditions", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::EditEffectTypeScalabilityConditions(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/condition-settings", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeScalabilityCondition(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/profile", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeScalabilityProfile(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/reset-field", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetEffectTypeScalabilityField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/scalability/rows", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::EditEffectTypeScalabilityRows(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/scalability/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEffectTypeScalability(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/scalability/active", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectActiveEffectTypeScalability(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/scalability/evaluate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::EvaluateEffectTypeScalability(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/scalability/conflicts", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEffectTypeScalabilityConflicts(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/rule-sets", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::CreateValidationRuleSet(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/rule-sets/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateValidationRuleSet(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/rule-sets/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectValidationRuleSet(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rule-sets", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleSets(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/vector", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleVector(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/color", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/rules/reset-field", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetEffectTypeRuleField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/name", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleName(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/asset", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeRuleScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/rules/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEffectTypeRule(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/rules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::EditEffectTypeRule(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/rules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddEffectTypeRule(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/significance-handlers", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DiscoverSignificanceHandlers(),TEXT("application/json")); });
 App->Post("/niagara/scalability/profiles", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DiscoverScalabilityProfiles(),TEXT("application/json")); });
 App->Post("/pcg/graphs/inspect", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectGraph(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Post("/pcg/graph-interfaces/inspect", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectGraphInterface(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Post("/pcg/graph-interfaces/dependencies", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectDependencies(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Post("/pcg/graph-interfaces/parameters/array/inspect", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectGraphParameterArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/scalar", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/text", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterText(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/asset", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/class", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterClass(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/string-array", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterStringArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/scalar-array", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterScalarArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/vector-array", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterVectorArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/int64", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterInt64(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/parameters/name", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::RenameGraphParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/parameters/remove", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::RemoveGraphParameter(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/vector", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterVector(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/rotator", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterRotator(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/transform", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterTransform(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-interfaces/parameters/enum", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphParameterEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-instances/parameters/override", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::EditGraphParameterOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/validate", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::ValidateGraph(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Post("/pcg/graphs", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::CreateGraph(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/parameters", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::AddGraphParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graph-instances", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::CreateGraphInstance(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graph-instances/parent", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphInstanceParent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/node-classes", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::DiscoverNodeClasses(),TEXT("application/json")); });
 App->Post("/pcg/data-classes", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::DiscoverDataClasses(),TEXT("application/json")); });
 App->Post("/pcg/components/inspect", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectWorldComponents(),TEXT("application/json")); });
 App->Post("/geometry-script/components/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectWorldMeshes(),TEXT("application/json")); });
 App->Post("/splines/components/inspect", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/splines/meshes/up-direction", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshUpDirection(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/forward-axis", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshForwardAxis(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/smooth-interpolation", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshSmoothInterpolation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/asset", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/remove", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::RemoveMeshComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/fit-segment", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::FitMeshSegment(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/add", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::AddMeshComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/sample-slices", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SampleMeshSlices(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/boundaries", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshBoundaries(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/rolls", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshRolls(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/offsets", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshOffsets(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/scales", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshScales(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/endpoints", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetMeshEndpoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/meshes/inspect", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::InspectSplineMeshes(),TEXT("application/json")); });
 App->Post("/splines/closing-key/reset", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::ResetLoopKey(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/closing-key", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetLoopKey(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/segments/inspect", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::InspectSegments(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/inspect", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::InspectPoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/settings/inspect", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::InspectSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/closest-point", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::FindClosest(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/components/remove", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::RemoveActorComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/physics/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectPhysics(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/physics/settings", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPhysicsSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/pain/damage-type", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPainDamageType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/pain/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectPain(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/pain/settings", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPainSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/brush/builder/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectBrushBuilder(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/override-reorder", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ReorderAudioOverrideRows(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/override-remove", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::RemoveAudioOverrideRow(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-reorder", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ReorderAudioSubmixSends(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-remove", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::RemoveAudioSubmixSend(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-target", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendTarget(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-inline-curve/linear-keys", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendLinearKeys(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-inline-curve/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectAudioSendInlineCurve(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-curve", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendExternalCurve(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-control", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendControl(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-numeric", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-add", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::AddAudioSubmixSend(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-row-reorder", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ReorderAudioSendRows(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-row-remove", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::RemoveAudioSendRow(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-row-listener", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendRowListener(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-row-add", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::AddAudioSendRow(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/override-add", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::AddAudioOverrideRow(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/override-target", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioOverrideSubmix(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/override-effects", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioOverrideEffects(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/override-crossfade", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioOverrideCrossfade(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/row-items", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectAudioSubmixRowItems(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectAudioVolumeSubmix(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectAudioVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/reverb-object", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioVolumeReverbObject(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/reverb", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioVolumeReverb(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/interior", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioVolumeInterior(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/control", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioVolumeControl(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-inline-curve/keys", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::EditAudioSendInlineKeys(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/foliage-blocking/inline-falloff/keys", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::EditBlockingFalloffKeys(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-inline-curve/key-setting", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendKeySetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/audio/submix/send-inline-curve/setting", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetAudioSendCurveSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/foliage-blocking/inline-falloff/key-setting", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetBlockingFalloffKeySetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/foliage-blocking/inline-falloff/setting", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetBlockingFalloffCurveSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/foliage-blocking/inline-falloff/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectBlockingFalloffKeys(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/foliage-blocking/inline-falloff/linear-keys", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetBlockingFalloffLinearKeys(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/visibility-override/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectVisibilityOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/visibility-override/levels", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetVisibilityOverrideLevels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/visibility-override/actors", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetVisibilityOverrideActors(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/hlod/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectHLODVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/hlod/policy", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetHLODVolumePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/brush/color", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetBrushColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/brush/replace-shape", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ReplaceBrushShape(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/brush/polygons/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectBrushPolygons(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/create-sphere", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::CreateSphere(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/create-cone", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::CreateCone(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/create-cylinder", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::CreateCylinder(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/create-box", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::CreateBox(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/collision/overlap-events", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetOverlapEvents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/collision/enabled", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetCollisionEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/collision/response", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetCollisionResponse(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/collision/object-type", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetObjectType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/collision/profiles", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectCollisionProfiles(),TEXT("application/json")); });
 App->Post("/volumes/collision/profile", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetCollisionProfile(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/overlaps/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectOverlaps(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/collision/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectCollision(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/delete", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/cull-distance/entry", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetCullEntry(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/cull-distance/enabled", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetCullEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/cull-distance/table", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ReplaceCullTable(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/cull-distance/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectCullDistance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/control", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessControl(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/blendable-remove", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::RemoveBlendable(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/blendable-add", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::AddBlendable(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/blendable-weight", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetBlendableWeight(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/override", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/scalar", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/bool", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/enum", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/object", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessObject(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/vector", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessVector(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/integer", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::SetPostProcessInteger(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/object/reset", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ResetPostProcessObject(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/enum/reset", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ResetPostProcessEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/vector/reset", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ResetPostProcessVector(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/bool/reset", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ResetPostProcessBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/integer/reset", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ResetPostProcessInteger(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/scalar/reset", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::ResetPostProcessScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/fields", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectPostProcessFields(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/post-process/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectPostProcess(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/offset", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetOffset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/component-lists/inspect", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectPlanarComponentLists(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/component-lists/set", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarComponentList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/capture-numeric", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarCaptureNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/inspect-page", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectWorldPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/inspect-page", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectPlanarPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/inspect-page", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectWorldPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/inspect-page", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectSkyPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/view-channels", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCaptureCubeViewChannels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/show-flags/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCaptureCubeShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/show-flags/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCaptureCubeShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/show-flags/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::DiscoverCaptureCubeShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/actor-lists/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCaptureCubeActorLists(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/actor-lists/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCaptureCubeActorList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/component-lists/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCaptureCubeComponentLists(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/component-lists/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCaptureCubeComponentList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/settings/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCaptureCubeSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/settings/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCaptureCubeSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCaptureCubePage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/cube/target", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCaptureCubeTarget(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/collection-writers/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DCollectionWriters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/view-channels", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DViewChannels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/collection-layout/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DCollectionLayout(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/collection-parameter", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DCollectionParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/transform-collection", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DTransformCollection(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/output-name", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DOutputName(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/resolution-divisor", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DResolutionDivisor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/show-flags/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/show-flags/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/show-flags/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::DiscoverCapture2DShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/component-lists/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DComponentLists(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/component-lists/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DComponentList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/actor-lists/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DActorLists(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/actor-lists/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DActorList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/projection-matrix", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DProjectionMatrix(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/clip-plane", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DClipPlane(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/settings/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/settings/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCapture2DPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/scene-captures/2d/target", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCapture2DTarget(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cubes/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedSourceTextureCubes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cubes/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectSourceTextureCube(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedSourceVolumeTextures(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/address", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceVolumeAddress(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectSourceVolumeTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedTexture2DArrays(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/sources/reorder", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ReorderTexture2DArraySources(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/sources/replace", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ReplaceTexture2DArraySources(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSourceTexture2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cube-arrays/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureCubeArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cube-arrays/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSourceTextureCubeArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/source-compatibility/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectArraySourceCompatibility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourceMips(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-layout/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourceLayout(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-identity/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourceIdentity(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/streaming-state/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureStreamingState(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/material-overrides/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureMaterialOverrides(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/expression-references/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureExpressionReferences(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/brush-assets/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureBrushAssets(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/duplicate", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::DuplicateSourceTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/create-2d", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSourceTexture2D(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/virtual-policy/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureVirtualPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/virtual-policy/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetTextureVirtualPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/address", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DAddress(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/settings/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectSourceTexture2DSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/filter", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DFilter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/mip-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DMipPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/lod-limit", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DLODLimit(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/processing-flag", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DProcessingFlag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/adjustment", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DAdjustment(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/mip-load-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DMipLoadPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/padding-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DPaddingPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/build-resize", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DBuildResize(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/2d/padding-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexture2DPaddingColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateRuntimeVirtualTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTexturePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/size", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureSize(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/priority", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTexturePriority(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureComponents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/writers/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureWriters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/material-data", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureMaterialData(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/layout", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureLayout(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/expressions/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureExpressions(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/material-overrides/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureOverrides(C.RequestBody()),TEXT("application/json")); });
 App->Post("/virtual-texture-builders/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectVirtualTextureBuilder(C.RequestBody()),TEXT("application/json")); });
 App->Post("/virtual-texture-builders/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedVirtualTextureBuilders(C.RequestBody()),TEXT("application/json")); });
 App->Post("/virtual-texture-builders/components/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectVirtualTextureBuilderComponents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/virtual-texture-builders/mobile-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetVirtualTextureBuilderMobilePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/virtual-texture-builders/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateVirtualTextureBuilder(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/layers/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/settings/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureComponentSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/flag", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureComponentFlag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/numeric", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureComponentNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/enum", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureComponentEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/fixed-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureComponentFixedColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/reference", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureComponentReference(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/bounds-actor", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureBoundsActor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/platform-enable", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureComponentPlatform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/platform-enable/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureComponentPlatforms(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/writers/settings/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureWriterSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/writers/numeric", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureWriterNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/writers/main-pass", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureWriterMainPass(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/writers/list", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureWriterList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureComponentPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/writers/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureWriterPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/duplicate", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::DuplicateRuntimeVirtualTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/volumes/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateRuntimeVirtualTextureVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/volumes/delete", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::DeleteRuntimeVirtualTextureVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/volumes/transform", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureVolumeTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/bounds-contributors/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureBoundsContributors(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/volumes/align-bounds", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::AlignRuntimeVirtualTextureBounds(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/build-streaming-mips", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::BuildRuntimeVirtualTextureStreamingMips(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/components/streaming-status", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureStreamingStatus(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/expressions/synchronize", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SynchronizeRuntimeVirtualTextureSample(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/expressions/reference", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureSampleReference(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/expressions/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureSample(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/expressions/policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureSamplePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/instance-parameters/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureInstanceParameters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/instance-parameters/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetRuntimeVirtualTextureInstanceParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/instance-parameters/declarations/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureParameterDeclarations(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/instance-parameters/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateRuntimeVirtualTextureInstanceOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/instance-parameters/remove", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::RemoveRuntimeVirtualTextureInstanceOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/instance-parameters/effective/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRuntimeVirtualTextureEffectiveParameters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cubes/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSourceTextureCube(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/create-solid", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSolidSourceVolumeTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/create-solid", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSolidSourceTexture2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cube-arrays/create-solid", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSolidSourceTextureCubeArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/events/endpoints/pins/remove", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::RemoveEventEndpointPin(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/events/endpoints/pins/add", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::AddEventEndpointPin(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/events/repeater", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.Name=TEXT("Repeater"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/events/track-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::EventTrackPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/events/endpoints/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::DiscoverEventEndpoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/channels/key-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::Extrapolation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/channels/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.FieldName=TEXT("Discover"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/channels/default", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::Extrapolation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/channels/integer-interpolation", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.Name=TEXT("Integer"); if(R.FieldName!=TEXT("IntegerInterpolationInspect") && R.FieldName!=TEXT("IntegerInterpolationSet")) throw std::runtime_error("IntegerInterpolationInspect/Set operation required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/cinematic/takes/sources/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(TakeMetadataUtils::Sources(C.RequestBody()),TEXT("application/json")); });
 App->Post("/cinematic/takes/metadata", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(TakeMetadataUtils::Metadata(C.RequestBody()),TEXT("application/json")); });
 App->Post("/widgets/animations", [](const FHttpContext<FEditorExtReq,FString>& C) { return C.TextResponse(WidgetAnimationUtils::Animations(C.RequestBody()),TEXT("application/json")); });
 App->Post("/assets/consolidate", [](const FHttpContext<FEditorExtReq,FString>& C) { return C.TextResponse(AssetConsolidationUtils::Consolidate(C.RequestBody()),TEXT("application/json")); });
 App->Post("/game-features", [](const FHttpContext<FEditorExtReq,FString>& C) { return C.TextResponse(GameFeatureUtils::Plugins(C.RequestBody()),TEXT("application/json")); });
 App->Post("/smart-objects/definition", [](const FHttpContext<FEditorExtReq,FString>& C) { return C.TextResponse(SmartObjectUtils::Definition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/editor-utilities", [](const FHttpContext<FEditorExtReq,FString>& C) { return C.TextResponse(EditorUtilityUtils::Utilities(C.RequestBody()),TEXT("application/json")); });
 App->Post("/cinematic/camera-cuts/range", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.FieldName=TEXT("CutRange"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/cinematic/camera-cuts/track-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::CameraCutTrackPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/cinematic/camera-cuts/metadata", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(!R.FieldName.StartsWith(TEXT("Cut"))) throw std::runtime_error("Typed Cut operation required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/cinematic/shots/metadata", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(!R.FieldName.StartsWith(TEXT("Shot"))) throw std::runtime_error("Typed Shot operation required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/subsections/reference", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("ReferenceInspect") && R.FieldName!=TEXT("ReferenceSet")) throw std::runtime_error("ReferenceInspect/ReferenceSet required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/subsections/origin", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(!R.FieldName.StartsWith(TEXT("Origin"))) throw std::runtime_error("Typed Origin operation required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/subsections/parameters", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(!R.FieldName.StartsWith(TEXT("Sub"))) throw std::runtime_error("Typed Sub operation required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/overlap-priority", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("PriorityInspect") && R.FieldName!=TEXT("PrioritySet")) throw std::runtime_error("PriorityInspect/PrioritySet required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/bindings/tags", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceBindingTagUtils::BindingTags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/folders/validate", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceFolderUtils::Validate(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/folders", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceFolderUtils::Folders(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/marked-frames", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::MarkedFrames(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/tracks/mute", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::TrackMutePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/tracks/evaluation-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::TrackEvaluationPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/level-sequences/sections/pre-post-roll", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("RollInspect") && R.FieldName!=TEXT("RollSet")) throw std::runtime_error("RollInspect/RollSet required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/easing/automatic", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("AutoEasingInspect") && R.FieldName!=TEXT("AutoEasingIn") && R.FieldName!=TEXT("AutoEasingOut")) throw std::runtime_error("AutoEasingInspect/AutoEasingIn/AutoEasingOut required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/easing/external-curve", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("ExternalInspect") && R.FieldName!=TEXT("ExternalIn") && R.FieldName!=TEXT("ExternalOut")) throw std::runtime_error("ExternalInspect/ExternalIn/ExternalOut required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/easing/built-in", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("BuiltInInspect") && R.FieldName!=TEXT("BuiltInIn") && R.FieldName!=TEXT("BuiltInOut")) throw std::runtime_error("BuiltInInspect/BuiltInIn/BuiltInOut required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/easing", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("EasingInspect") && R.FieldName!=TEXT("EasingIn") && R.FieldName!=TEXT("EasingOut")) throw std::runtime_error("EasingInspect/EasingIn/EasingOut required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/completion-mode", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("CompletionInspect") && R.FieldName!=TEXT("CompletionSet")) throw std::runtime_error("CompletionInspect/CompletionSet required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/sections/blend-type", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); if(R.FieldName!=TEXT("BlendInspect") && R.FieldName!=TEXT("BlendSet")) throw std::runtime_error("BlendInspect/BlendSet required"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/channels/duplicate-key", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.FieldName=TEXT("Duplicate"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/channels/offset", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.FieldName=TEXT("Offset"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/channels/sample", [](const FHttpContext<FRenderTargetReq,FString>& C) { auto R=C.RequestBody(); R.FieldName=TEXT("Sample"); if(R.Name!=TEXT("Float") && R.Name!=TEXT("Double") && R.Name!=TEXT("Bool") && R.Name!=TEXT("Byte") && R.Name!=TEXT("Integer") && R.Name!=TEXT("Object")) throw std::runtime_error("Sampling supports Float/Double/Bool/Byte/Integer/Object channels"); return C.TextResponse(SequenceChannelUtils::Extrapolation(R),TEXT("application/json")); });
 App->Post("/level-sequences/channels/extrapolation", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(SequenceChannelUtils::Extrapolation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/references/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InspectCollectionReferences(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/parameters/reorder", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ReorderCollectionParameters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::DiscoverCollections(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/world-values/reset", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ResetCollectionWorldValues(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/world-values/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::SetCollectionWorldValue(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/world-values/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InspectCollectionWorldValues(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/validate-structure", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ValidateCollectionStructure(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/parameters/delete", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::DeleteCollectionParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/parameters/rename", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::RenameCollectionParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/parameters/add", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::AddCollectionParameter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::CreateCollection(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/collections/defaults", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::CollectionDefaults(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/collection-parameter", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::CollectionParameterReference(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/fonts/atlas-inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InspectFontAtlas(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/font-default", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::FontSampleDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/static-parameter-default", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::StaticParameterDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/parameter-default", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ParameterDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/texture-reference", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::SetTextureSampleReference(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/texture-sample-policy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::TextureSamplePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/texture-channel-labels", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::TextureChannelLabels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/vector-channel-labels", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::VectorChannelLabels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/primitive-data-binding", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::PrimitiveDataBinding(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/enumerations/resolve-value", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ResolveEnumerationValue(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/enumerations/entries", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InspectEnumerationEntries(C.RequestBody()),TEXT("application/json")); });
 App->Post("/material-instances/enumeration-slots", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InstanceEnumerations(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/scalar-enumeration", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ScalarEnumerationReference(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/scalar-slider-range", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::ScalarSliderRange(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/metadata/discover", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::DiscoverExpressionMetadata(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/metadata/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InspectExpression(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/expressions/metadata/set", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::SetExpressionMetadata(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/parameter-groups/entry", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::EditGroupEntry(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/parameter-groups/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::InspectGroups(C.RequestBody()),TEXT("application/json")); });
 App->Post("/materials/parameter-groups/priority", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(MaterialMetadataUtils::SetGroupPriority(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/padding-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTexturePaddingColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/build-resize", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTextureBuildResize(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/color-adjustment", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTextureAdjustment(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/downscale/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureDownscaleOverrides(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/downscale/override", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetTextureDownscaleOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/sampling/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectSourceTextureSampling(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/sampling/setting", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTextureSampling(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/compression/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectSourceTextureCompression(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/compression/setting", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTextureCompression(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/alpha-coverage/measure-source", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::MeasureSourceTextureAlphaCoverage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/alpha-coverage/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectSourceTextureAlphaCoverage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/alpha-coverage", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceTextureAlphaCoverage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source/export-image", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ExportTextureSourceImage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source/export-dds", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ExportTextureSourceDDS(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/export-image", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ExportRenderTargetImage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/conversion/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectRenderTargetConversion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/conversion/create-texture", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ConvertRenderTargetToTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/conversion/update-texture", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::UpdateTextureFromRenderTarget(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/fill", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::FillTextureSourceMip(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/pixels/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourcePixels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/pixels/patch", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::PatchTextureSourceMip(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/statistics", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourceMipStatistics(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/compare", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CompareTextureSourceMips(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/copy", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CopyTextureSourceMip(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/validate-payloads", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ValidateTextureSourceMipPayloads(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/linear-pixels/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourceLinearPixels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/textures/source-mips/linear-statistics", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTextureSourceLinearStatistics(C.RequestBody()),TEXT("application/json")); });
 App->Post("/runtime-virtual-textures/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedRuntimeVirtualTextures(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cube-arrays/sources/replace", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ReplaceTextureCubeArraySources(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cube-arrays/sources/reorder", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ReorderTextureCubeArraySources(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-cube-arrays/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedTextureCubeArrays(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/tiles", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceVolumeTiles(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/source", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetSourceVolumeSource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volume-textures/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateSourceVolumeTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/address", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetTexture2DArrayAddress(C.RequestBody()),TEXT("application/json")); });
 App->Post("/texture-arrays/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectTexture2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d-array/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Create2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d-array/setting", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Set2DArraySetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d-array/clear-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Set2DArrayClearColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d-array/resize", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Resize2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d-array/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Inspect2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d-array/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoaded2DArray(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/volume/resize", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::ResizeVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/volume/clear-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetVolumeClearColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/volume/setting", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetVolumeSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/volume/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/volume/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/volume/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedVolume(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/cube/clear-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCubeClearColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/cube/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::CreateCube(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/cube/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoadedCube(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/cube/consumers/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCubeConsumers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/cube/setting", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::SetCubeSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/cube/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectCube(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/create", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Create2D(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::InspectLoaded2D(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/consumers/inspect-page", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Inspect2DConsumers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/clear-color", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Set2DClearColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/resize", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Resize2D(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/inspect", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Inspect2D(C.RequestBody()),TEXT("application/json")); });
 App->Post("/render-targets/2d/setting", [](const FHttpContext<FRenderTargetReq,FString>& C) { return C.TextResponse(RenderTargetUtils::Set2DSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/material-users/inspect-page", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::InspectMaterialUsers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/materials/inspect-page", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::InspectLoadedMaterials(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/mobility/inspect", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::InspectMobility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/mobility", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::SetMobility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/receivers/inspect-page", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::InspectReceivers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/receivers/set", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::SetReceiver(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/create", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/delete", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/placement", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::SetPlacement(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/appearance", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::SetAppearance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/material", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::SetMaterial(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/inspect-page", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::InspectPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/decals/setting", [](const FHttpContext<FDecalReq,FString>& C) { return C.TextResponse(DecalUtils::SetSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/inspect-page", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::InspectWorldPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/inspect-page", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::InspectLocalPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/inspect-page", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::InspectWorldPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/inspect-page", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::InspectWorldPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/world-influence/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectWorldInfluence(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/world-influence/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetWorldInfluence(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/color", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyLightColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/capture-policy/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectSkyCapturePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/capture-policy/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyCapturePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/occlusion/tint", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyOcclusionTint(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/occlusion/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectSkyOcclusion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/sky/occlusion/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyOcclusion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/local-exposure/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectLocalExposure(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/local-exposure/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetLocalExposure(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/ray-policy/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectRayPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/ray-policy/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetRayPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/view-channels/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectViewChannels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/view-channels/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetViewChannels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/shafts/appearance", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetLightShaftAppearance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/shafts/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectLightShafts(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/shafts/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetLightShaftSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/directional-clouds/color", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetDirectionalLuminanceColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/directional-clouds/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectDirectionalClouds(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/directional-clouds/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetDirectionalClouds(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/directional-shadows/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectDirectionalShadows(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/directional-shadows/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetDirectionalShadows(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/lightmass/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectLightmass(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/lightmass/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetLightmass(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/advanced-policy/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectAdvancedPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lights/advanced-policy/set", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetAdvancedPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/show-flags/discover", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::DiscoverPlanarShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/show-flags/inspect", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectPlanarShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/show-flags/set", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarShowFlags(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/capture-policy", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarCapturePolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/actor-lists/inspect", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectPlanarActorLists(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/planar/actor-lists/set", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarActorList(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/source", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetSource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/queue-recapture", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::QueueRecapture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/visible", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/delete", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/create", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/transform", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/reflection-captures/scalar", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/screen-percentage", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarScreenPercentage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/bool", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/scalar", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/delete", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::DeletePlanar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/create", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::CreatePlanar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/visible", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/transform", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::SetPlanarTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/planar-reflections/inspect", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectPlanar(),TEXT("application/json")); });
 App->Post("/lighting/bool", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/color", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/visible", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/transform", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/mobility", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetMobility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/atmosphere-index", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetAtmosphereIndex(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/units-intensity", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetUnitsIntensity(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/texture", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetTexture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/channels", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetChannels(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/function-scale", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetFunctionScale(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/scalar", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/sky/scalar", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/sky/bool", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/sky/source", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkySource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/sky/hemisphere-color", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::SetSkyHemisphereColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/sky/queue-capture", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::QueueSkyCapture(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/sky/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::InspectSky(),TEXT("application/json")); });
 App->Post("/lighting/delete", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/lighting/create", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(LightingUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/scalar", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/transform", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/create", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/delete", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/transform-mode", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetTransformMode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/absorption-tent", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetAbsorptionTent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/visible", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/color", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/ground-albedo", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetGroundAlbedo(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/inspect", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/atmosphere/scalar", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/atmosphere/bool", [](const FHttpContext<FAtmosphereReq,FString>& C) { return C.TextResponse(AtmosphereUtils::SetBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/linked", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODLinkedLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/referencers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectHLODLayerReferencers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/linked/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectHLODLinkedChain(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/object", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderObject(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/enum", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/bool", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/int64", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderInt64(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/data-layer", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLoadedActorDataLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/pin/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectPartitionActorPin(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/pin", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPartitionActorPin(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actors/pin", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPartitionActorPins(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actors/pins/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectPartitionActorPins(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/data-layers/replace", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLoadedActorDataLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/data-layers/move-partition-actor", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::MovePartitionActorDataLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/parent", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerParent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/hierarchy/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectDataLayerHierarchy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-default/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectPartitionHLODDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-options/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectPartitionHLODOptions(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-options", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPartitionHLODOption(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/streaming/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectPartitionStreaming(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectStreamingSourceComponents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/setting", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetStreamingSourceSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/detail", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectEditorRegion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/replace-unloaded", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::ReplaceUnloadedEditorRegion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/private-asset/debug-color", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPrivateDataLayerAssetColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/private-asset/actor-filters", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPrivateDataLayerAssetFilters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/location-volumes/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectLocationVolumes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/location-volumes/debug-color", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLocationVolumeColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/location-volumes/loading", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLocationVolumeLoading(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/cells/detail", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeCellDetail(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/cells/mappings/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeCellMappings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/cells/contents/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeCellContents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/visualization", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetStreamingSourceVisualization(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/create", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::CreateStreamingSourceComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/remove", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::RemoveStreamingSourceComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/shapes/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectStreamingSourceShapes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/shapes/preview", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::PreviewStreamingSourceShapes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/shapes", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetStreamingSourceShapes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/target-grids", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetStreamingSourceTargetGrids(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/sources/target-grids/preview", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::PreviewStreamingSourceGridFilter(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/policies/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectPartitionPolicies(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/policies", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPartitionPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/streaming", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPartitionStreaming(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimePartitionDefinitions(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-grids/eligibility", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeGridEligibility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-grids/hlod-eligibility", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeHLODEligibility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/add", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::AddRuntimeMainDefinition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/classes/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimePartitionClasses(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/class", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::ReplaceRuntimeMainClass(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/remove", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::RemoveRuntimeMainDefinition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/reorder", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::ReorderRuntimeMainDefinitions(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectSpatialHashGrids(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grid-info/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectSpatialHashGridInfoActors(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/settings/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectSpatialHashSettings(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/settings", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetSpatialHashSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/add", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::AddSpatialHashGrid(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/remove", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::RemoveSpatialHashGrid(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/reorder", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::ReorderSpatialHashGrids(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/numeric", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetSpatialHashGridNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/appearance", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetSpatialHashGridAppearance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/spatial-hash/grids/name", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::RenameSpatialHashGrid(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/numeric", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeDefinitionNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/fields/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeDefinitionFields(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-setups/add", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::AddRuntimeHLODSetup(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-setups/reorder", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::ReorderRuntimeHLODSetups(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-setups/normalize-indices", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::NormalizeRuntimeHLODIndices(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-setups/remove", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::RemoveRuntimeHLODSetup(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-setups/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeHLODSetups(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/name", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::RenameRuntimeDefinition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-layer", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeHLODLayerReference(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-layers", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeHLODLayerReferences(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/hlod-layers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeHLODLayerReferences(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/origin", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeDefinitionOrigin(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/debug-color", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeDefinitionColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/bool", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeDefinitionBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/runtime-definitions/bounds-mode", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetRuntimeDefinitionBoundsMode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-default", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetPartitionHLODDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layer-assets/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectDataLayerAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layer-assets/create", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::CreateDataLayerAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/create", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::CreateHLODLayerAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layer-assets/enum", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerAssetEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layer-assets/actor-filters", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerAssetFilters(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layer-assets/debug-color", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerAssetColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/visibility", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerVisibility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/loading", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerLoading(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/delete", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::DeleteDataLayerInstance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/impact", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectDataLayerImpact(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectDataLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/create", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::CreateDataLayerInstance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/create-private", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::CreatePrivateDataLayerInstance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/initial-state", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerInitialState(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/asset", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerInstanceAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/locked", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerLocked(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/filter-included", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerFilterIncluded(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/streaming-setting", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerStreamingSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/data-layers/short-name", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetDataLayerShortName(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/data-layers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectLoadedActorDataLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/string", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderString(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/name", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderName(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/numeric", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODBuilderNumeric(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/settings/fields", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectHLODBuilderFields(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/class", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODLayerClass(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/type", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODLayerType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/parent", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetHLODParentLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/hlod-layers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectHLODLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/hlod-layer", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLoadedActorHLODLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/runtime-grid", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLoadedActorRuntimeGrid(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/spatial", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::SetLoadedActorSpatial(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectActorDescriptor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/references/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectActorReferences(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/references/graph", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectActorReferenceGraph(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actor/referencers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectActorReferencers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/containers/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectContainers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/actors/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectBoxActorDescriptors(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/unload", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::UnloadEditorRegion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/load", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::LoadEditorRegion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/release-unloaded", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::ReleaseUnloadedEditorRegion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/create", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::CreateEditorRegion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/regions/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectEditorRegions(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/cells/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectRuntimeCells(C.RequestBody()),TEXT("application/json")); });
 App->Post("/worlds/partition/actors/inspect", [](const FHttpContext<FWorldPartitionReq,FString>& C) { return C.TextResponse(WorldPartitionUtils::InspectActorDescriptors(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/procedural-scale", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeProceduralScaleRange(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/procedural-bool", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeProceduralBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/procedural-curve", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeProceduralCurve(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/procedural-setting", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeProceduralSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/blocking/falloff", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetBlockingVolumeFalloff(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/blocking/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectBlockingVolumes(),TEXT("application/json")); });
 App->Post("/foliage/procedural/blocking/target", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetBlockingVolumeTarget(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/spawner/terrain-materials", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetSpawnerTerrainMaterials(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/spawner/types", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::ReplaceSpawnerTypes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/components/spawner", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetProceduralSpawner(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/components/overlap", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetProceduralOverlap(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/components/bool", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetProceduralBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/spawner/setting", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetSpawnerSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/procedural/components/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectProceduralComponents(),TEXT("application/json")); });
 App->Post("/foliage/procedural/spawner/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectSpawner(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/landscape-layers", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::ReplaceTypeLandscapeLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/placement-range", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypePlacementRange(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/unregister-empty", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::UnregisterEmptyType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/materials", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::ReplaceTypeMaterials(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/material-slot", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeMaterialSlot(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/mesh", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/cull-range", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeCullRange(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/scaling", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeScaling(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/scale-range", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeScaleRange(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/asset/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectType(C.RequestBody()),TEXT("application/json")); });
	App->Post("/foliage/types/create", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::CreateType(C.RequestBody()),TEXT("application/json")); });
	App->Post("/foliage/procedural/spawner/create", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::CreateSpawner(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/register", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::RegisterType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/instances/add", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::AddInstance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/instances/delete", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::DeleteInstance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/instances/transform", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetInstanceTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/bool", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/types/scalar", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::SetTypeScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/foliage/types/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectTypes(C.RequestBody()),TEXT("application/json")); });
 App->Post("/foliage/instances/inspect", [](const FHttpContext<FFoliageReq,FString>& C) { return C.TextResponse(FoliageUtils::InspectInstances(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/layer-info/debug-color", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetLayerInfoDebugColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/layer-info/spline-mask", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetLayerInfoSplineMask(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/layer-info/asset", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetLayerInfoAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/layer-info/scalar", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetLayerInfoScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/layer-info/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectLayerInfo(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/layer-info/blend", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetLayerInfoBlend(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/weights", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetEditLayerWeights(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/heights", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetEditLayerHeights(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/delete", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::DeleteEditLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/create", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::CreateEditLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/reorder", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::ReorderEditLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/rename", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::RenameEditLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/heights/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectEditLayerHeights(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/weights/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectEditLayerWeights(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/alpha", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetEditLayerAlpha(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectEditLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/edit-layers/bool", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::SetEditLayerBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/weights/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectWeights(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/paint-layers/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectPaintLayers(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/heights/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectHeights(C.RequestBody()),TEXT("application/json")); });
	App->Post("/landscapes/create", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::CreateLandscape(C.RequestBody()),TEXT("application/json")); });
 App->Post("/landscapes/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/landscapes/components/inspect", [](const FHttpContext<FLandscapeReq,FString>& C) { return C.TextResponse(LandscapeUtils::InspectComponents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/transform", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/create", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/delete", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/material", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetMaterial(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/ground-albedo", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetGroundAlbedo(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/visible", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/tracing-mode", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetTracingMode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/inspect", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/clouds/scalar", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/clouds/bool", [](const FHttpContext<FCloudReq,FString>& C) { return C.TextResponse(CloudUtils::SetBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/create", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::CreateLocal(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/delete", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::DeleteLocal(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/visible", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetLocalVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/transform", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetLocalTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/color", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetLocalColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/priority", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetLocalPriority(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/local/inspect", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::InspectLocal(),TEXT("application/json")); });
 App->Post("/fog/local/scalar", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetLocalScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/transform", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetTransform(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/bool", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetBool(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/volumetric-enabled", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetVolumetricEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/second-layer", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetSecondLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/create", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/delete", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::Delete(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/visible", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetVisible(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/color", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/albedo", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetAlbedo(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/cubemap", [](const FHttpContext<FFogReq,FString>& C) { return C.TextResponse(FogUtils::SetCubemap(C.RequestBody()),TEXT("application/json")); });
 App->Post("/fog/height/inspect", [](const FHttpContext<FLightingReq,FString>& C) { return C.TextResponse(FogUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/lighting/components/inspect", [](const FHttpContext<FReflectionCaptureReq,FString>& C) { return C.TextResponse(LightingUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/reflection-captures/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(ReflectionCaptureUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/volumes/inspect-page", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectWorldPage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/volumes/inspect", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::InspectWorld(),TEXT("application/json")); });
 App->Post("/volumes/query-point", [](const FHttpContext<FVolumeReq,FString>& C) { return C.TextResponse(VolumeUtils::QueryPoint(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/components/add", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::AddActorComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/sample-distance", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SampleDistance(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/sample-time", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SampleTime(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/position", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetPointPosition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/default-up", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetDefaultUp(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/rotation", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetPointRotation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/scale", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetPointScale(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/remove", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::RemovePoint(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/insert", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::InsertPoint(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/tangents", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetPointTangents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/type", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetPointType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/closed-loop", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetClosedLoop(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/settings", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::SetSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/clear", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::ClearPoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/splines/points/replace", [](const FHttpContext<FSplineReq,FString>& C) { return C.TextResponse(SplineUtils::ReplacePoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/static-mesh/nanite/components/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectNaniteWorldComponents(),TEXT("application/json")); });
 App->Post("/geometry-script/components", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AddActorComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/append-box", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AppendBox(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/topology", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectTopology(C.RequestBody()),TEXT("application/json")); });
 App->Post("/static-mesh/nanite/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectNanite(C.RequestBody()),TEXT("application/json")); });
 App->Post("/static-mesh/nanite/settings", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetNaniteSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/static-mesh/nanite/settings/reset", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ResetNaniteSetting(C.RequestBody()),TEXT("application/json")); });
 App->Post("/static-mesh/nanite/component-audit", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AuditNaniteComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/static-mesh/nanite/component-force-disable", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetComponentNaniteOverride(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/uvs/measure", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::MeasureUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/faces/find", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::FindRegionFaces(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/polygroups/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectPolygroups(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/materials/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectMaterials(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/materials/set", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetMaterial(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/collision/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectCollision(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/collision/clear", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ClearCollision(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/measure", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::MeasureMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/edges/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectEdges(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/uvs/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/normals/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectNormals(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/vertex-colors/inspect", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InspectVertexColors(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/validate", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ValidateMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/append-sphere", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AppendSphere(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/append-cylinder", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AppendCylinder(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/transform", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::TransformMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/project-uvs", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ProjectUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/recompute-normals", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RecomputeNormals(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/vertex-color", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetVertexColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/selected-vertex-color", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetSelectedVertexColor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/generate-collision", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::GenerateCollision(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/generate-static-mesh-collision", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::GenerateStaticMeshCollision(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/boolean", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::BooleanMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/append-mesh", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AppendMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/plane-cut", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::PlaneCut(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/self-union", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SelfUnion(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/bevel-polygroups", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::BevelPolygroups(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/offset-shell", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::OffsetMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/extrude", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ExtrudeMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/offset-faces", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::OffsetFaces(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/inset-outset", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::InsetFaces(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/convex-hull", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ConvexHull(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/convex-decomposition", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ConvexDecomposition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/swept-hull", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SweptHull(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/copy-from-static-mesh", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::CopyFromStaticMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/copy-to-static-mesh", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::CopyToStaticMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/tessellate", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::Tessellate(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/remesh", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::Remesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/plane-model", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::PlaneModel(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/weld-edges", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::WeldEdges(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/repair-boundaries", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RepairBoundaries(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/remove-small-components", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RemoveSmallComponents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/fill-holes", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::FillHoles(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/simplify", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SimplifyMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/simplify-regions", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SimplifyRegions(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/smooth", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SmoothMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/warp", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::WarpMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/flare", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::FlareMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/wave", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::WaveMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/perlin-noise", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::NoiseMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/generate-polygroups", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::GeneratePolygroups(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/normal-mode", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetNormalMode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/compact", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::CompactMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/remove-unused-vertices", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RemoveUnusedVertices(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/flip-normals", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::FlipNormals(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/flip-selected-normals", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::FlipSelectedNormals(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/selected-polygroup", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetSelectedPolygroup(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/selected-material-ids", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetSelectedMaterialIDs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/material-ids", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetAllMaterialIDs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/copy-polygroup-layer", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::CopyPolygroupLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/clear-polygroup-layer", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ClearPolygroupLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/remap-material-ids", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RemapMaterialIDs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/triangle-material-id", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetTriangleMaterialID(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/vertex-position", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetVertexPosition(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/add-vertex", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AddVertex(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/add-triangle", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AddTriangle(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/delete-triangle", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::DeleteTriangle(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/delete-triangles", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::DeleteTriangles(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/uv-channel-count", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetUVChannelCount(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/polygroup-layer-count", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetPolygroupLayerCount(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/polygroup-layers/add-named", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AddNamedPolygroupLayer(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/clear-uv-channel", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ClearUVChannel(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/repack-uvs", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RepackUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/texel-density", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ScaleTexelDensity(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/auto-generate-uvs", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::AutoGenerateUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/recompute-uvs", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::RecomputeUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/triangle-uvs", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::SetTriangleUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/copy-uv-channel", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::CopyUVChannel(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/transform-uvs", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::TransformUVs(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/compute-tangents", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ComputeTangents(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/split-normals", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ComputeSplitNormals(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/clear", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::ClearMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/geometry-script/meshes/copy", [](const FHttpContext<FGeometryScriptReq,FString>& C) { return C.TextResponse(GeometryScriptUtils::CopyMesh(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::AddActorComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/remove", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::RemoveActorComponent(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/status", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectComponentStatus(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/output", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectComponentOutput(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/output/metadata", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectOutputMetadata(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/output/points", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectOutputPoints(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/resources", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectComponentResources(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/components/settings", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetComponentSettings(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/components/partitioned", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetComponentPartitioned(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/components/graph", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetComponentGraph(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/components/operation", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::RequestComponentOperation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/nodes", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::AddNode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/pins", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::AddGraphPin(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/pins", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::EditGraphPins(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/pins/inspect", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectGraphPins(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/scalar", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetNodeSettingsScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/settings/scalar", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphSettingsScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/settings/reset-field", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::ResetGraphSettingsField(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/settings/text", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphSettingsText(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/settings/enum", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetGraphSettingsEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/enum", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetNodeSettingsEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/text", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetNodeSettingsText(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/subgraph", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetSubgraph(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/string-array", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetNodeSettingsStringArray(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/asset", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetNodeSettingsAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/compound", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::SetNodeSettingsCompound(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/settings/reset-field", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::ResetNodeSettingsField(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/nodes/settings/inspect", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::InspectNodeSettings(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/edges", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::EditEdge(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/nodes/remove", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::RemoveNode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/nodes/duplicate", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::DuplicateNode(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pcg/graphs/nodes/presentation", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::EditNodePresentation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graphs/duplicate", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::DuplicateGraph(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pcg/graph-instances/duplicate", [](const FHttpContext<FPCGReq,FString>& C) { return C.TextResponse(PCGUtils::DuplicateGraphInstance(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/significance-handler", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeSignificance(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/bool", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeBool(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/effect-types/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEffectTypeEnum(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::CreateEffectType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateEffectType(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/effect-types/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEffectType(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Post("/niagara/systems/stack-dependencies", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectSystemStackDependencies(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/modules/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectSystemModule(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/modules/enabled", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetSystemModuleEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/modules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddSystemModule(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/stack-inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectSystemStack(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/rapid-iteration/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectSystemRapidIteration(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/systems/emitters/rapid-iteration", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveEmitterRapidParameter(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/rapid-iteration/compound", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterRapidCompound(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/rapid-iteration/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterRapidScalar(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/rapid-iteration/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEmitterRapidIteration(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/modules/reset-pin-default", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetEmitterModulePinDefault(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/modules/pin-compound", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterModulePinCompound(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/modules/pin-default", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterModulePinDefault(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/modules/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEmitterModule(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/modules/enabled", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterModuleEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/stack-dependencies", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEmitterStackDependencies(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/stack-inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectEmitterStack(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/emitters/modules", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddEmitterModule(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/pin-compound", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptPinCompound(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/outputs", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::EditScriptOutput(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/outputs", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptOutput(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/input-name", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RenameScriptInput(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/input-value", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptInputValue(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/compound-inputs", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptCompoundInput(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/input-priority", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptInputPriority(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/input-exposure", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptInputExposure(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/scalar-inputs", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptScalarInput(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/parameter-maps", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptParameterMap(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/duplicate-node", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateScriptNode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/validate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ValidateScriptGraph(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/comment-box-size", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResizeScriptCommentBox(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/comment-boxes", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptCommentBox(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/operations", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptOperation(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/operation-types", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DiscoverScriptOperations(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/function-calls", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptFunctionCall(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/reroutes", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::AddScriptReroute(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/scripts/graph/nodes", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveScriptNode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/disconnect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DisconnectScriptPins(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/connect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ConnectScriptPins(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/reset-pin-default", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetScriptPinDefault(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/pin-scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptPinScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/node-comment", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptNodeComment(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/graph/node-position", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::MoveScriptNode(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/graph/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectScriptGraph(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/required-dependencies", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptRequiredDependencies(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/deprecation-replacement", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptReplacement(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/usage-contexts", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptUsageContexts(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/provided-dependencies", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptProvidedDependencies(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/bool", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptBool(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/scripts/text", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetScriptText(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::CreateScriptAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/emitters", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::CreateEmitterAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/emitters/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateEmitterAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/duplicate", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::DuplicateScript(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/scripts/inspect", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::InspectScriptAsset(C.RequestBody().AssetPath),TEXT("application/json")); });
 App->Delete("/niagara/systems/event-handlers", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveEventHandler(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/event-handlers/source", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEventSource(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/event-handlers/execution-mode", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEventExecutionMode(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/event-handlers/bool", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEventBool(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/event-handlers/count", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEventCount(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/user-integer-binding", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::BindStageUserInteger(C.RequestBody()),TEXT("application/json")); });
 App->Post("/niagara/systems/simulation-stages/reset-binding", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::ResetStageBinding(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/integer-default", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetStageIntegerDefault(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/state-range", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetStageStateRange(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/bool", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetStageBool(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetStageEnum(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/niagara/systems/simulation-stages", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RemoveStage(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/order", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::MoveStage(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/name", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::RenameStage(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/simulation-stages/enabled", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetStageEnabled(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/fixed-bounds", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterBounds(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/enum", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterEnum(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/emitters/scalar", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetEmitterScalar(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/niagara/systems/fixed-tick", [](const FHttpContext<FNiagaraReq,FString>& C) { return C.TextResponse(NiagaraUtils::SetFixedTick(C.RequestBody()),TEXT("application/json")); });
 App->Get("/niagara/systems/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(NiagaraUtils::InspectSystem(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/pose-search/assets", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::CreateAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/search-mode", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetSearchMode(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/cost-bias", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetCostBias(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/blend-spaces", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddBlendSpace(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/order", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::MoveEntry(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/entries/duplicate", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::DuplicateEntry(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/mirror-policy", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetEntryMirrorPolicy(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/pose-search/databases/entries/sampling-range", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::SetEntrySamplingRange(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/entries/inspect", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectEntry(C.RequestBody()),TEXT("application/json")); });
 App->Post("/pose-search/databases/sequences", [](const FHttpContext<FPoseSearchReq,FString>& C) { return C.TextResponse(PoseSearchUtils::AddSequence(C.RequestBody()),TEXT("application/json")); });
 App->Get("/pose-search/databases/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PoseSearchUtils::InspectDatabase(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/ik-rigs/definition", [](const FHttpContext<void,FString>& C) { return C.TextResponse(IKRigUtils::InspectRig(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/skeletons/structure", [](const FHttpContext<void,FString>& C) { return C.TextResponse(SkeletonUtils::Inspect(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/ability-system/defaults", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectDefaults(C.Query("class_path")),TEXT("application/json")); });
 App->Get("/ability-system/validate", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::ValidateDefinition(C.Query("class_path")),TEXT("application/json")); });
 App->Patch("/ability-system/blueprints/defaults", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::EditBlueprintDefaults(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ability-system/evaluation-channels", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectChannels(),TEXT("application/json")); });
 App->Post("/ability-system/blueprints", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::CreateBlueprintAsset(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/abilities/source-tags", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::SetAbilityTags(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/abilities/input-id", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::SetAbilityInputID(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/input", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::AbilityInput(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/effects/inhibition", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::InhibitEffect(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/effects/magnitudes", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::UpdateEffectMagnitudes(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/effects", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::SetEffectLevel(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/effects", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::ApplyEffect(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/ability-system/runtime/abilities", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::RemoveAbility(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/abilities", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::GrantAbility(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/ability-system/runtime/attributes", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::SetAttribute(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime/events", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::SendEvent(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ability-system/classes", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::Discover(C.Query("kind",TEXT("ability")),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Delete("/ability-system/runtime/effects", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::RemoveEffect(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ability-system/runtime", [](const FHttpContext<FAbilitySystemReq,FString>& C) { return C.TextResponse(AbilitySystemUtils::ControlRuntime(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ability-system/runtime", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AbilitySystemUtils::InspectRuntime(C.Query("component_path"),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100"))),FCString::Atoi(*C.Query("pie_instance",TEXT("-1")))),TEXT("application/json")); });
 App->Post("/gameplay-tags/table-sources", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::RegisterTable(C.RequestBody()),TEXT("application/json")); });
 App->Get("/remote-control/presets", [](const FHttpContext<void,FString>& C) { return C.TextResponse(RemoteControlUtils::List(C.Query(TEXT("search")),C.Query(TEXT("limit")).IsEmpty() ? 100 : FCString::Atoi(*C.Query(TEXT("limit")))),TEXT("application/json")); });
 App->Get("/remote-control/presets/inspect", [](const FHttpContext<void,FString>& C) { return C.TextResponse(RemoteControlUtils::Inspect(C.Query(TEXT("asset_path"))),TEXT("application/json")); });
 App->Post("/remote-control/presets", [](const FHttpContext<FRemoteControlReq,FString>& C) { return C.TextResponse(RemoteControlUtils::Create(C.RequestBody()),TEXT("application/json")); });
 App->Post("/remote-control/presets/expose", [](const FHttpContext<FRemoteControlReq,FString>& C) { return C.TextResponse(RemoteControlUtils::Expose(C.RequestBody()),TEXT("application/json")); });
 App->Post("/remote-control/presets/unexpose", [](const FHttpContext<FRemoteControlReq,FString>& C) { return C.TextResponse(RemoteControlUtils::Unexpose(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/remote-control/presets/value", [](const FHttpContext<FRemoteControlReq,FString>& C) { return C.TextResponse(RemoteControlUtils::SetValue(C.RequestBody()),TEXT("application/json")); });
 App->Get("/blueprints/breakpoints", [](const FHttpContext<void,FString>& C) { return C.TextResponse(DebugFeedbackUtils::ListBreakpoints(C.Query(TEXT("asset_path"))),TEXT("application/json")); });
 App->Post("/blueprints/breakpoints", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(DebugFeedbackUtils::EditBreakpoint(C.RequestBody()),TEXT("application/json")); });
 App->Get("/blueprints/debug/state", [](const FHttpContext<void,FString>& C) { return C.TextResponse(DebugFeedbackUtils::DebugState(C.Query(TEXT("search")),C.Query(TEXT("limit")).IsEmpty() ? 200 : FCString::Atoi(*C.Query(TEXT("limit")))),TEXT("application/json")); });
 App->Post("/blueprints/debug/control", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(DebugFeedbackUtils::DebugControl(C.RequestBody()),TEXT("application/json")); });
 App->Post("/project/cpp-classes", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(DebugFeedbackUtils::CreateCppClass(C.RequestBody()),TEXT("application/json")); });
 App->Get("/build/live-coding", [](const FHttpContext<void,FString>& C) { return C.TextResponse(DebugFeedbackUtils::LiveCodingStatus(),TEXT("application/json")); });
 App->Post("/build/live-coding", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(DebugFeedbackUtils::LiveCodingCompile(C.RequestBody()),TEXT("application/json")); });
 App->Post("/assets/import-fbx", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::ImportFbx(C.RequestBody()),TEXT("application/json")); });
 App->Post("/assets/create", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::CreateAsset(C.RequestBody()),TEXT("application/json")); });
 App->Get("/blueprints/class-defaults", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameCoreUtils::InspectClassDefaults(C.Query(TEXT("asset_path")),C.Query(TEXT("search")),C.Query(TEXT("limit")).IsEmpty() ? 200 : FCString::Atoi(*C.Query(TEXT("limit")))),TEXT("application/json")); });
 App->Patch("/blueprints/class-defaults", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::SetClassDefault(C.RequestBody()),TEXT("application/json")); });
 App->Get("/project/game-settings", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameCoreUtils::InspectGameSettings(),TEXT("application/json")); });
 App->Patch("/project/game-settings", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::SetGameSetting(C.RequestBody()),TEXT("application/json")); });
 App->Get("/play-session", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameCoreUtils::InspectPlaySession(C.Query(TEXT("search")),C.Query(TEXT("limit")).IsEmpty() ? 200 : FCString::Atoi(*C.Query(TEXT("limit")))),TEXT("application/json")); });
 App->Get("/play-session/properties", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameCoreUtils::ReadPlayActorProperties(C.Query(TEXT("actor")),C.Query(TEXT("search")),C.Query(TEXT("limit")).IsEmpty() ? 200 : FCString::Atoi(*C.Query(TEXT("limit")))),TEXT("application/json")); });
 App->Post("/play-session/mouse", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::MovePlayMouse(C.RequestBody()),TEXT("application/json")); });
 App->Post("/play-session/input", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::SendPlayInput(C.RequestBody()),TEXT("application/json")); });
 App->Post("/build/package", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::StartPackage(C.RequestBody()),TEXT("application/json")); });
 App->Get("/build/package", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameCoreUtils::PackageStatus(C.Query(TEXT("log_lines")).IsEmpty() ? 40 : FCString::Atoi(*C.Query(TEXT("log_lines")))),TEXT("application/json")); });
 App->Post("/build/package/cancel", [](const FHttpContext<FGameCoreReq,FString>& C) { return C.TextResponse(GameCoreUtils::CancelPackage(),TEXT("application/json")); });
 App->Patch("/gameplay-tags/table-row", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::EditTableTag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/gameplay-tags/resolve", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::ResolveTags(C.RequestBody()),TEXT("application/json")); });
 App->Get("/gameplay-tags/settings", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::InspectSettings(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Get("/gameplay-tags/runtime/providers", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::InspectProviders(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100"))),FCString::Atoi(*C.Query("pie_instance",TEXT("-1")))),TEXT("application/json")); });
 App->Post("/gameplay-tags/runtime/evaluate", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::EvaluateRuntime(C.RequestBody()),TEXT("application/json")); });
 App->Get("/gameplay-tags/runtime", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::InspectRuntime(C.Query("actor_path"),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100"))),FCString::Atoi(*C.Query("pie_instance",TEXT("-1")))),TEXT("application/json")); });
 App->Get("/gameplay-tags/unused", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::InspectUnused(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Post("/gameplay-tags/move", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::MoveTags(C.RequestBody()),TEXT("application/json")); });
 App->Delete("/gameplay-tags", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::DeleteTag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/gameplay-tags/rename", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::RenameTag(C.RequestBody()),TEXT("application/json")); });
 App->Patch("/gameplay-tags", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::UpdateTag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/gameplay-tags/sources", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::CreateSource(C.RequestBody()),TEXT("application/json")); });
 App->Get("/gameplay-tags/sources", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::InspectSources(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Post("/gameplay-tags", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::CreateTag(C.RequestBody()),TEXT("application/json")); });
 App->Post("/gameplay-tags/asset-query/evaluate", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::EvaluateAsset(C.RequestBody()),TEXT("application/json")); });
 App->Get("/gameplay-tags/asset-properties", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::InspectAsset(C.Query("asset_path")),TEXT("application/json")); });
 App->Patch("/gameplay-tags/asset-property", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::EditAsset(C.RequestBody()),TEXT("application/json")); });
 App->Post("/gameplay-tags/evaluate", [](const FHttpContext<FGameplayTagReq,FString>& C) { return C.TextResponse(GameplayTagUtils::Evaluate(C.RequestBody()),TEXT("application/json")); });
 App->Get("/gameplay-tags", [](const FHttpContext<void,FString>& C) { return C.TextResponse(GameplayTagUtils::Inspect(C.Query("tag"),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100"))),C.Query("dictionary_only",TEXT("true"))!=TEXT("false")),TEXT("application/json")); });
 App->Get("/ai-perception/sources", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PerceptionUtils::InspectSources(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Patch("/ai-perception/sources", [](const FHttpContext<FPerceptionReq,FString>& C) { return C.TextResponse(PerceptionUtils::ConfigureSource(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ai-perception/configuration", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PerceptionUtils::InspectEditor(C.Query("component_path"),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Patch("/ai-perception/configuration", [](const FHttpContext<FPerceptionReq,FString>& C) { return C.TextResponse(PerceptionUtils::ControlEditor(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ai-perception/runtime/sources", [](const FHttpContext<FPerceptionReq,FString>& C) { return C.TextResponse(PerceptionUtils::ControlSource(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ai-perception/runtime/damage", [](const FHttpContext<FPerceptionReq,FString>& C) { return C.TextResponse(PerceptionUtils::ReportDamage(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ai-perception/runtime/noise", [](const FHttpContext<FPerceptionReq,FString>& C) { return C.TextResponse(PerceptionUtils::ReportNoise(C.RequestBody()),TEXT("application/json")); });
 App->Post("/ai-perception/runtime", [](const FHttpContext<FPerceptionReq,FString>& C) { return C.TextResponse(PerceptionUtils::ControlRuntime(C.RequestBody()),TEXT("application/json")); });
 App->Get("/ai-perception/runtime", [](const FHttpContext<void,FString>& C) { return C.TextResponse(PerceptionUtils::InspectRuntime(C.Query("component_path"),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100"))),FCString::Atoi(*C.Query("pie_instance",TEXT("-1")))),TEXT("application/json")); });
 App->Get("/state-trees/schemas", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::DiscoverSchemas(C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Get("/state-trees/node-classes", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::DiscoverClasses(C.Query("asset_path"),C.Query("kind",TEXT("task")),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Get("/state-trees/node-types", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::Discover(C.Query("asset_path"),C.Query("kind",TEXT("task")),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100")))),TEXT("application/json")); });
 App->Post("/state-trees/runtime", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::ControlRuntime(C.RequestBody()),TEXT("application/json")); });
 App->Get("/state-trees/runtime", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::InspectRuntime(C.Query("component_path"),C.Query("search"),FCString::Atoi(*C.Query("limit",TEXT("100"))),FCString::Atoi(*C.Query("pie_instance",TEXT("-1")))),TEXT("application/json")); });
 App->Get("/state-trees/inspect", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::Inspect(C.Query("asset_path"),false),TEXT("application/json")); });
 App->Get("/state-trees/validate", [](const FHttpContext<void,FString>& C) { return C.TextResponse(StateTreeUtils::Inspect(C.Query("asset_path"),true),TEXT("application/json")); });
 App->Patch("/state-trees/schema", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("schema_settings")),TEXT("application/json")); });
 App->Post("/state-trees/create", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("create")),TEXT("application/json")); });
 App->Post("/state-trees/states", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("create_state")),TEXT("application/json")); });
 App->Patch("/state-trees/states", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("update_state")),TEXT("application/json")); });
 App->Delete("/state-trees/states", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("delete_state")),TEXT("application/json")); });
 App->Post("/state-trees/move", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("move_state")),TEXT("application/json")); });
 App->Post("/state-trees/transitions/move", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("move_transition")),TEXT("application/json")); });
 App->Post("/state-trees/transitions", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("create_transition")),TEXT("application/json")); });
 App->Patch("/state-trees/transitions", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("update_transition")),TEXT("application/json")); });
 App->Delete("/state-trees/transitions", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("delete_transition")),TEXT("application/json")); });
 App->Post("/state-trees/functions", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("create_function")),TEXT("application/json")); });
 App->Patch("/state-trees/functions", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("update_function")),TEXT("application/json")); });
 App->Delete("/state-trees/functions", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("delete_function")),TEXT("application/json")); });
 App->Post("/state-trees/nodes/move", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("move_node")),TEXT("application/json")); });
 App->Post("/state-trees/nodes", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("create_node")),TEXT("application/json")); });
 App->Patch("/state-trees/nodes", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("update_node")),TEXT("application/json")); });
 App->Delete("/state-trees/nodes", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("delete_node")),TEXT("application/json")); });
 App->Post("/state-trees/links", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("set_link")),TEXT("application/json")); });
 App->Post("/state-trees/parameters/reset", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("reset_parameter")),TEXT("application/json")); });
 App->Post("/state-trees/parameters/move", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("move_parameter")),TEXT("application/json")); });
 App->Post("/state-trees/parameters/type", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("replace_parameter")),TEXT("application/json")); });
 App->Post("/state-trees/parameters", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("create_parameter")),TEXT("application/json")); });
 App->Patch("/state-trees/parameters", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("update_parameter")),TEXT("application/json")); });
 App->Delete("/state-trees/parameters", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("delete_parameter")),TEXT("application/json")); });
 App->Post("/state-trees/bindings", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("set_binding")),TEXT("application/json")); });
 App->Delete("/state-trees/bindings", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("delete_binding")),TEXT("application/json")); });
 App->Post("/state-trees/compile", [](const FHttpContext<FStateTreeReq,FString>& C) { return C.TextResponse(StateTreeUtils::Control(C.RequestBody(),TEXT("compile")),TEXT("application/json")); });
 App->Get("/environment-queries/runtime", [](const FHttpContext<void,FString>& C) { int32 I=-1; const FString V=C.Query("pie_instance"); if(!V.IsEmpty() && (!LexTryParseString(I,*V) || I < -1)) throw std::runtime_error("pie_instance requires integer >=-1"); return C.TextResponse(EnvironmentQueryRuntimeUtils::Inspect(C.Query("request_id"),I),TEXT("application/json")); });
 App->Get("/environment-queries/runtime/owners", [](const FHttpContext<void,FString>& C) { int32 I=-1,L=100; const FString V=C.Query("pie_instance"),N=C.Query("limit"); if((!V.IsEmpty() && (!LexTryParseString(I,*V) || I < -1)) || (!N.IsEmpty() && !LexTryParseString(L,*N))) throw std::runtime_error("Invalid PIE instance/limit"); return C.TextResponse(EnvironmentQueryRuntimeUtils::Owners(I,C.Query("search"),L),TEXT("application/json")); });
 App->Post("/environment-queries/runtime", [](const FHttpContext<FEnvironmentQueryRuntimeReq,FString>& C) { return C.TextResponse(EnvironmentQueryRuntimeUtils::Control(C.RequestBody()),TEXT("application/json")); });
 App->Get("/environment-queries/inspect", [](const FHttpContext<void,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Inspect(C.Query("asset_path")),TEXT("application/json")); });
 App->Get("/environment-queries/validate", [](const FHttpContext<void,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Inspect(C.Query("asset_path")),TEXT("application/json")); });
 App->Post("/environment-queries/create", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("create")),TEXT("application/json")); });
 App->Post("/environment-queries/graph", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("initialize")),TEXT("application/json")); });
 App->Post("/environment-queries/options", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("create_option")),TEXT("application/json")); });
 App->Patch("/environment-queries/options", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("update_option")),TEXT("application/json")); });
 App->Delete("/environment-queries/options", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("delete_option")),TEXT("application/json")); });
 App->Post("/environment-queries/tests", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("create_test")),TEXT("application/json")); });
 App->Patch("/environment-queries/tests", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("update_test")),TEXT("application/json")); });
 App->Delete("/environment-queries/tests", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("delete_test")),TEXT("application/json")); });
 App->Patch("/environment-queries/generators", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("replace_generators")),TEXT("application/json")); });
 App->Post("/environment-queries/layout", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("layout")),TEXT("application/json")); });
 App->Post("/environment-queries/compile", [](const FHttpContext<FEnvironmentQueryReq,FString>& C) { return C.TextResponse(EnvironmentQueryUtils::Control(C.RequestBody(),TEXT("compile")),TEXT("application/json")); });
	App->Get("/behavior-trees/inspect", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Inspect(C.Query("asset_path")),TEXT("application/json"));
	});
	App->Get("/behavior-trees/validate", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Inspect(C.Query("asset_path")),TEXT("application/json"));
	});

	App->Post("/behavior-trees/create", [](const FHttpContext<FAIAssetCreateReq, FString>& C)
	{
		return C.TextResponse(ClassUtils::CreateBehaviorTree(C.RequestBody().AssetPath));
	});

	App->Post("/behavior-trees/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Inspect(C.RequestBody().AssetPath),TEXT("application/json"));
	});
	App->Post("/behavior-trees/graph", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("initialize")),TEXT("application/json"));
	});
	App->Post("/behavior-trees/nodes", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("create_node")),TEXT("application/json"));
	});
	App->Patch("/behavior-trees/nodes", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("update_node")),TEXT("application/json"));
	});
	App->Delete("/behavior-trees/nodes", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("delete_node")),TEXT("application/json"));
	});
	App->Post("/behavior-trees/links", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("connect")),TEXT("application/json"));
	});
	App->Delete("/behavior-trees/links", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("disconnect")),TEXT("application/json"));
	});
	App->Post("/behavior-trees/layout", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("set_positions")),TEXT("application/json"));
	});
	App->Patch("/behavior-trees/settings", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("set_blackboard")),TEXT("application/json"));
	});
	App->Post("/behavior-trees/decorator-logic", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("create_compound")),TEXT("application/json"));
	});
	App->Patch("/behavior-trees/decorator-logic", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("replace_compound")),TEXT("application/json"));
	});
	App->Post("/behavior-trees/compile", [](const FHttpContext<FBehaviorTreeGraphReq, FString>& C)
	{
		return C.TextResponse(BehaviorTreeGraphUtils::Control(C.RequestBody(),TEXT("compile")),TEXT("application/json"));
	});

	App->Get("/blackboards/inspect", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(BlackboardUtils::Inspect(C.Query("asset_path")),TEXT("application/json"));
	});
	App->Get("/blackboards/validate", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(BlackboardUtils::Inspect(C.Query("asset_path")),TEXT("application/json"));
	});
	App->Patch("/blackboards/keys", [](const FHttpContext<FBlackboardKeyReq, FString>& C)
	{
		return C.TextResponse(BlackboardUtils::Control(C.RequestBody(),TEXT("update")),TEXT("application/json"));
	});
	App->Patch("/blackboards/settings", [](const FHttpContext<FBlackboardKeyReq, FString>& C)
	{
		return C.TextResponse(BlackboardUtils::Control(C.RequestBody(),TEXT("settings")),TEXT("application/json"));
	});

	App->Post("/blackboards/create", [](const FHttpContext<FAIAssetCreateReq, FString>& C)
	{
		return C.TextResponse(ClassUtils::CreateBlackboard(C.RequestBody().AssetPath));
	});

	App->Post("/blackboards/keys", [](const FHttpContext<FBlackboardKeyReq, FString>& C)
	{
		return C.TextResponse(BlackboardUtils::Control(C.RequestBody(),TEXT("add")),TEXT("application/json"));
	});

	App->Post("/audio/attenuations/create", [](const FHttpContext<FAudioAttenuationCreateReq, FString>& C)
	{
		const FAudioAttenuationCreateReq Body = C.RequestBody();
		if (!IsInGameThread()) throw std::runtime_error("Sound Attenuation asset creation requires the editor game thread");
		if (Body.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(Body.AssetPath, false))
			throw std::runtime_error("asset_path must be a valid long package name without an object suffix");
		FString UniquePackageName;
		FString UniqueAssetName;
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		AssetToolsModule.Get().CreateUniqueAssetName(Body.AssetPath, TEXT(""), UniquePackageName, UniqueAssetName);
		const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *UniquePackageName, *UniqueAssetName);
		if (Body.bDryRun)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("would_create"), true);
			Writer->WriteValue(TEXT("asset_path"), ObjectPath);
			Writer->WriteValue(TEXT("dry_run"), true);
			Writer->WriteObjectEnd();
			Writer->Close();
			return C.TextResponse(Json, TEXT("application/json"));
		}
		USoundAttenuationFactory* Factory = NewObject<USoundAttenuationFactory>();
		USoundAttenuation* Asset = Cast<USoundAttenuation>(AssetToolsModule.Get().CreateAsset(
			UniqueAssetName, FPackageName::GetLongPackagePath(UniquePackageName), USoundAttenuation::StaticClass(), Factory));
		if (!Asset) throw std::runtime_error("failed to create Sound Attenuation asset");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(Asset->GetPathName(), TEXT("text/plain"));
	});

	App->Get("/audio/attenuations/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundAttenuation* Asset = Cast<USoundAttenuation>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not Sound Attenuation");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/audio/attenuations/settings", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(SoundAttenuationUtils::SettingsJson(Cast<USoundAttenuation>(LoadAsset(C.Query("asset_path")))), TEXT("application/json"));
	});
	App->Patch("/audio/attenuations/settings", [](const FHttpContext<FAudioAttenuationSettingsReq, FString>& C)
	{
		const FAudioAttenuationSettingsReq Body = C.RequestBody();
		return C.TextResponse(SoundAttenuationUtils::EditSettings(Cast<USoundAttenuation>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Post("/audio/attenuations/curves", [](const FHttpContext<FAudioAttenuationCurveReq, FString>& C)
	{
		const FAudioAttenuationCurveReq Body = C.RequestBody();
		return C.TextResponse(SoundAttenuationUtils::EditCurve(Cast<USoundAttenuation>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Post("/audio/attenuations/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		return C.TextResponse(SoundAttenuationUtils::Validate(Cast<USoundAttenuation>(LoadAsset(C.RequestBody().AssetPath))), TEXT("application/json"));
	});
	App->Post("/audio/attenuations/evaluate", [](const FHttpContext<FAudioAttenuationEvaluateReq, FString>& C)
	{
		const FAudioAttenuationEvaluateReq Body = C.RequestBody();
		return C.TextResponse(SoundAttenuationUtils::Evaluate(Cast<USoundAttenuation>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});

	App->Post("/audio/attenuations/submix-sends", [](const FHttpContext<FAudioAttenuationSubmixSendReq, FString>& C)
	{
		const FAudioAttenuationSubmixSendReq Body = C.RequestBody();
		return C.TextResponse(SoundAttenuationUtils::EditSubmixSend(Cast<USoundAttenuation>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Post("/audio/attenuations/plugins", [](const FHttpContext<FAudioAttenuationPluginReq, FString>& C)
	{
		const FAudioAttenuationPluginReq Body = C.RequestBody();
		return C.TextResponse(SoundAttenuationUtils::EditPlugin(Cast<USoundAttenuation>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Get("/audio/plugin-settings/classes", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(SoundAttenuationUtils::PluginClassesJson(), TEXT("application/json"));
	});
	App->Post("/audio/plugin-settings/create", [](const FHttpContext<FAudioPluginSettingsCreateReq, FString>& C)
	{
		return C.TextResponse(SoundAttenuationUtils::CreatePluginSettings(C.RequestBody()), TEXT("application/json"));
	});

	App->Get(TEXT("/audio/modulation/profiles"), [](const FHttpContext<void, FString>& C)
	{
		const FString Value = C.Query("profile_index"); int32 Index = 0;
		if (!Value.IsEmpty() && !LexTryParseString(Index, *Value)) throw std::runtime_error("profile_index must be an integer");
		return C.TextResponse(ModulationProfileUtils::Inspect(C.Query("asset_path"), Index), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/modulation/profiles"), [](const FHttpContext<FModulationProfileReq, FString>& C)
	{
		return C.TextResponse(ModulationProfileUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/modulation/runtime"), [](const FHttpContext<void, FString>& C)
	{
		const FString Instance = C.Query("pie_instance"); int32 Id = -1;
		if (!Instance.IsEmpty() && (!LexTryParseString(Id, *Instance) || Id < 0)) throw std::runtime_error("pie_instance must be a nonnegative integer");
		return C.TextResponse(ModulationRuntimeUtils::Inspect(C.Query("asset_path"), Id), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/modulation/recordings"), [](const FHttpContext<void, FString>& C)
	{
		int32 Instance = -1, Limit = 128; uint64 After = 0;
		const FString I = C.Query("pie_instance"), L = C.Query("limit"), A = C.Query("after_sequence");
		if ((!I.IsEmpty() && (!LexTryParseString(Instance, *I) || Instance < 0)) || (!L.IsEmpty() && !LexTryParseString(Limit, *L)) || (!A.IsEmpty() && (A.StartsWith(TEXT("-")) || !LexTryParseString(After, *A)))) throw std::runtime_error("Invalid recording instance, limit or sequence query");
		return C.TextResponse(ModulationRecordingUtils::Inspect(C.Query("recording_id"), Instance, After, Limit), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/modulation/recordings"), [](const FHttpContext<FModulationRecordingReq, FString>& C)
	{
		return C.TextResponse(ModulationRecordingUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Post("/audio/modulation/runtime", [](const FHttpContext<FModulationRuntimeReq, FString>& C)
	{
		return C.TextResponse(ModulationRuntimeUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Patch("/audio/modulation/generators/settings", [](const FHttpContext<FModulationGeneratorReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationAuthoringUtils::EditGenerator(LoadAsset(R.AssetPath), R), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/modulation/inputs/import"), [](const FHttpContext<FModulationFileReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationFileUtils::Import(Cast<USoundModulationPatch>(LoadAsset(R.AssetPath)), R), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/modulation/inputs"), [](const FHttpContext<FModulationInputReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationAuthoringUtils::Input(LoadAsset(R.AssetPath), R), TEXT("application/json"));
	});
	App->Post("/audio/modulation/sample", [](const FHttpContext<FModulationSampleReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationAuthoringUtils::Sample(LoadAsset(R.AssetPath), R), TEXT("application/json"));
	});
	App->Post("/audio/modulation/create", [](const FHttpContext<FModulationCreateReq, FString>& C)
	{
		return C.TextResponse(ModulationUtils::Create(C.RequestBody()), TEXT("application/json"));
	});
	App->Get("/audio/modulation/settings", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(ModulationUtils::Inspect(LoadAsset(C.Query("asset_path"))), TEXT("application/json"));
	});
	App->Patch("/audio/modulation/settings", [](const FHttpContext<FModulationSettingsReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationUtils::Edit(LoadAsset(R.AssetPath), R), TEXT("application/json"));
	});
	App->Post("/audio/modulation/stages", [](const FHttpContext<FModulationStageReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationUtils::Stage(LoadAsset(R.AssetPath), R), TEXT("application/json"));
	});
	App->Post("/audio/modulation/convert", [](const FHttpContext<FModulationConvertReq, FString>& C)
	{
		const auto& R = C.RequestBody(); return C.TextResponse(ModulationUtils::Convert(LoadAsset(R.AssetPath), R), TEXT("application/json"));
	});
	App->Post("/audio/modulation/validate", [](const FHttpContext<FModulationSettingsReq, FString>& C)
	{
		return C.TextResponse(ModulationUtils::Validate(LoadAsset(C.RequestBody().AssetPath)), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/profiling/traces"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(AudioTraceUtils::Inspect(C.Query("capture_id")), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/profiling/traces"), [](const FHttpContext<FAudioTraceReq, FString>& C)
	{
		return C.TextResponse(AudioTraceUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/diagnostics/captures"), [](const FHttpContext<void, FString>& C)
	{
		int32 Instance = -1; const FString I = C.Query("pie_instance");
		if (!I.IsEmpty() && (!LexTryParseString(Instance, *I) || Instance < 0)) throw std::runtime_error("pie_instance must be nonnegative");
		return C.TextResponse(AudioDiagnosticUtils::Inspect(C.Query("capture_id"), Instance), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/diagnostics/captures"), [](const FHttpContext<FAudioDiagnosticReq, FString>& C)
	{
		return C.TextResponse(AudioDiagnosticUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/components/settings"), [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(AudioComponentUtils::Inspect(C.Query("bp_path"), C.Query("component_name"), C.Query("actor_path")), TEXT("application/json"));
	});
	App->Patch(TEXT("/audio/components/settings"), [](const FHttpContext<FAudioComponentSettingsReq, FString>& C)
	{
		return C.TextResponse(AudioComponentUtils::Edit(C.RequestBody()), TEXT("application/json"));
	});
	App->Post(TEXT("/audio/quartz/events"), [](const FHttpContext<FQuartzEventReq, FString>& C)
	{
		return C.TextResponse(QuartzEventUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/quartz/events"), [](const FHttpContext<void, FString>& C)
	{
		int32 Instance = -1, Limit = 128; uint64 After = 0;
		const FString I = C.Query("pie_instance"), L = C.Query("limit"), A = C.Query("after_sequence");
		if ((!I.IsEmpty() && (!LexTryParseString(Instance, *I) || Instance < 0)) || (!L.IsEmpty() && !LexTryParseString(Limit, *L)) || (!A.IsEmpty() && (A.StartsWith(TEXT("-")) || !LexTryParseString(After, *A)))) throw std::runtime_error("Invalid PIE instance, limit or sequence query");
		return C.TextResponse(QuartzEventUtils::Inspect(C.Query("event_id"), Instance, After, Limit), TEXT("application/json"));
	});
	App->Get(TEXT("/audio/quartz/clock"), [](const FHttpContext<void, FString>& C)
	{
		const FString Instance = C.Query("pie_instance");
		int32 Id = -1;
		if (!Instance.IsEmpty() && (!LexTryParseString(Id, *Instance) || Id < 0)) throw std::runtime_error("pie_instance must be a nonnegative integer");
		return C.TextResponse(QuartzUtils::Inspect(C.Query("clock_name"), Id), TEXT("application/json"));
	});
	App->Post("/audio/quartz/control", [](const FHttpContext<FQuartzReq, FString>& C)
	{
		return C.TextResponse(QuartzUtils::Control(C.RequestBody()), TEXT("application/json"));
	});
	App->Post("/audio/dialogue/create", [](const FHttpContext<FDialogueCreateReq, FString>& C)
	{
		return C.TextResponse(DialogueUtils::Create(C.RequestBody()), TEXT("application/json"));
	});
	App->Get("/audio/dialogue/voices/settings", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(DialogueUtils::VoiceJson(Cast<UDialogueVoice>(LoadAsset(C.Query("asset_path")))), TEXT("application/json"));
	});
	App->Patch("/audio/dialogue/voices/settings", [](const FHttpContext<FDialogueVoiceSettingsReq, FString>& C)
	{
		const FDialogueVoiceSettingsReq Body = C.RequestBody();
		return C.TextResponse(DialogueUtils::EditVoice(Cast<UDialogueVoice>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Get("/audio/dialogue/waves/settings", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(DialogueUtils::WaveJson(Cast<UDialogueWave>(LoadAsset(C.Query("asset_path")))), TEXT("application/json"));
	});
	App->Patch("/audio/dialogue/waves/settings", [](const FHttpContext<FDialogueWaveSettingsReq, FString>& C)
	{
		const FDialogueWaveSettingsReq Body = C.RequestBody();
		return C.TextResponse(DialogueUtils::EditWave(Cast<UDialogueWave>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Post("/audio/dialogue/contexts", [](const FHttpContext<FDialogueContextReq, FString>& C)
	{
		const FDialogueContextReq Body = C.RequestBody();
		return C.TextResponse(DialogueUtils::EditContext(Cast<UDialogueWave>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Post("/audio/dialogue/resolve", [](const FHttpContext<FDialogueContextReq, FString>& C)
	{
		const FDialogueContextReq Body = C.RequestBody();
		return C.TextResponse(DialogueUtils::Resolve(Cast<UDialogueWave>(LoadAsset(Body.AssetPath)), Body), TEXT("application/json"));
	});
	App->Post("/audio/dialogue/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		return C.TextResponse(DialogueUtils::Validate(LoadAsset(C.RequestBody().AssetPath)), TEXT("application/json"));
	});

	App->Post("/audio/concurrencies/create", [](const FHttpContext<FAudioConcurrencyCreateReq, FString>& C)
	{
		const FAudioConcurrencyCreateReq Body = C.RequestBody();
		if (!IsInGameThread()) throw std::runtime_error("Sound Concurrency asset creation requires the editor game thread");
		if (Body.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(Body.AssetPath, false))
			throw std::runtime_error("asset_path must be a valid long package name without an object suffix");
		FString UniquePackageName;
		FString UniqueAssetName;
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		AssetToolsModule.Get().CreateUniqueAssetName(Body.AssetPath, TEXT(""), UniquePackageName, UniqueAssetName);
		const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *UniquePackageName, *UniqueAssetName);
		if (Body.bDryRun)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("would_create"), true);
			Writer->WriteValue(TEXT("asset_path"), ObjectPath);
			Writer->WriteValue(TEXT("dry_run"), true);
			Writer->WriteObjectEnd();
			Writer->Close();
			return C.TextResponse(Json, TEXT("application/json"));
		}
		USoundConcurrencyFactory* Factory = NewObject<USoundConcurrencyFactory>();
		USoundConcurrency* Asset = Cast<USoundConcurrency>(AssetToolsModule.Get().CreateAsset(
			UniqueAssetName, FPackageName::GetLongPackagePath(UniquePackageName), USoundConcurrency::StaticClass(), Factory));
		if (!Asset) throw std::runtime_error("failed to create Sound Concurrency asset");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(Asset->GetPathName(), TEXT("text/plain"));
	});

	App->Get("/audio/concurrencies/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundConcurrency* Asset = Cast<USoundConcurrency>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not Sound Concurrency");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/audio/waves/settings", [](const FHttpContext<void, FString>& C)
	{
		USoundWave* Wave = Cast<USoundWave>(LoadAsset(C.Query("asset_path")));
		if (!Wave) throw std::runtime_error("Asset is not a Sound Wave");
		return C.TextResponse(SoundWaveSettingsJson(Wave), TEXT("application/json"));
	});

	App->Patch("/audio/waves/settings", [](const FHttpContext<FAudioWaveSettingsReq, FString>& C)
	{
		const FAudioWaveSettingsReq Body = C.RequestBody();
		USoundWave* Wave = Cast<USoundWave>(LoadAsset(Body.AssetPath));
		if (!Wave) throw std::runtime_error("Asset is not a Sound Wave");

		const UEnum* CompressionEnum = StaticEnum<ESoundAssetCompressionType>();
		const FEnumProperty* SampleRateProperty = FindFProperty<FEnumProperty>(USoundWave::StaticClass(), FName(TEXT("SampleRateQuality")));
		const UEnum* SampleRateEnum = SampleRateProperty ? SampleRateProperty->GetEnum() : nullptr;
		const UEnum* LoadingEnum = StaticEnum<ESoundWaveLoadingBehavior>();
		const ESoundAssetCompressionType CurrentCompression = Wave->GetSoundAssetCompressionTypeEnum();
		const ESoundwaveSampleRateSettings CurrentSampleRateQuality = Wave->SampleRateQuality;
		const ESoundWaveLoadingBehavior CurrentLoadingBehavior = Wave->LoadingBehavior;
		ESoundAssetCompressionType NewCompression = CurrentCompression;
		ESoundwaveSampleRateSettings NewSampleRateQuality = CurrentSampleRateQuality;
		ESoundWaveLoadingBehavior NewLoadingBehavior = CurrentLoadingBehavior;
		if (!Body.CompressionType.IsEmpty())
		{
			const int64 Value = CompressionEnum->GetValueByNameString(Body.CompressionType.TrimStartAndEnd());
			if (Value == INDEX_NONE || Value < 0 || Value >= static_cast<int64>(ESoundAssetCompressionType::RADAudio) + 1)
				throw std::runtime_error("compression_type must be a valid ESoundAssetCompressionType name");
			NewCompression = static_cast<ESoundAssetCompressionType>(Value);
		}
		if (!Body.SampleRateQuality.IsEmpty())
		{
			if (!SampleRateEnum) throw std::runtime_error("Sound Wave sample-rate enum metadata is unavailable");
			const int64 Value = SampleRateEnum->GetValueByNameString(Body.SampleRateQuality.TrimStartAndEnd());
			if (Value == INDEX_NONE || Value < 0 || Value > static_cast<int64>(ESoundwaveSampleRateSettings::Min))
				throw std::runtime_error("sample_rate_quality must be Max, High, Medium, Low, or Min");
			NewSampleRateQuality = static_cast<ESoundwaveSampleRateSettings>(Value);
		}
		if (!Body.LoadingBehavior.IsEmpty())
		{
			const int64 Value = LoadingEnum->GetValueByNameString(Body.LoadingBehavior.TrimStartAndEnd());
			if (Value == INDEX_NONE || Value < 0 || Value >= static_cast<int64>(ESoundWaveLoadingBehavior::Uninitialized))
				throw std::runtime_error("loading_behavior must be Inherited, RetainOnLoad, PrimeOnLoad, LoadOnDemand, or ForceInline");
			NewLoadingBehavior = static_cast<ESoundWaveLoadingBehavior>(Value);
		}
		if (Body.bSetCompressionQuality && (Body.CompressionQuality < 1 || Body.CompressionQuality > 100))
			throw std::runtime_error("compression_quality must be between 1 and 100");
		FIntProperty* CompressionQualityProperty = FindFProperty<FIntProperty>(USoundWave::StaticClass(), FName(TEXT("CompressionQuality")));
		if (!CompressionQualityProperty) throw std::runtime_error("Sound Wave compression quality property is unavailable");

		USoundClass* NewSoundClass = Wave->SoundClassObject;
		if (Body.bSetSoundClass)
		{
			NewSoundClass = Body.SoundClassPath.IsEmpty() ? nullptr : Cast<USoundClass>(LoadAsset(Body.SoundClassPath));
			if (!Body.SoundClassPath.IsEmpty() && !NewSoundClass)
				throw std::runtime_error("sound_class_path must identify a loaded Sound Class asset");
		}
		USoundAttenuation* NewAttenuation = Wave->AttenuationSettings;
		if (Body.bSetAttenuation)
		{
			NewAttenuation = Body.AttenuationPath.IsEmpty() ? nullptr : Cast<USoundAttenuation>(LoadAsset(Body.AttenuationPath));
			if (!Body.AttenuationPath.IsEmpty() && !NewAttenuation)
				throw std::runtime_error("attenuation_path must identify a Sound Attenuation asset");
		}
		TSet<TObjectPtr<USoundConcurrency>> NewConcurrencySet = Wave->ConcurrencySet;
		if (Body.bSetConcurrencyPaths)
		{
			NewConcurrencySet.Reset();
			TSet<FString> SeenPaths;
			for (const FString& RawPath : Body.ConcurrencyPaths)
			{
				const FString Path = RawPath.TrimStartAndEnd();
				if (Path.IsEmpty() || SeenPaths.Contains(Path))
					throw std::runtime_error("concurrency_paths must contain nonempty, unique Sound Concurrency asset paths");
				SeenPaths.Add(Path);
				USoundConcurrency* Concurrency = Cast<USoundConcurrency>(LoadAsset(Path));
				if (!Concurrency) throw std::runtime_error("concurrency_paths entries must identify Sound Concurrency assets");
				NewConcurrencySet.Add(Concurrency);
			}
		}
		const int32 CurrentCompressionQuality = CompressionQualityProperty->GetPropertyValue_InContainer(Wave);
		const int32 NewCompressionQuality = Body.bSetCompressionQuality ? Body.CompressionQuality : CurrentCompressionQuality;
		const bool bNewLooping = Body.bSetLooping ? Body.bLooping : static_cast<bool>(Wave->bLooping);
		const bool bNewCloudStreaming = Body.bSetCloudStreaming ? Body.bCloudStreaming : Wave->IsCloudStreamingEnabled();
		const bool bCloudStreamingChanged = Body.bSetCloudStreaming && bNewCloudStreaming != Wave->IsCloudStreamingEnabled();
		if (bNewCloudStreaming && NewLoadingBehavior == ESoundWaveLoadingBehavior::ForceInline)
			throw std::runtime_error("cloud_streaming cannot be enabled while loading_behavior is ForceInline");
		bool bConcurrencySetChanged = NewConcurrencySet.Num() != Wave->ConcurrencySet.Num();
		if (!bConcurrencySetChanged)
			for (const TObjectPtr<USoundConcurrency>& Concurrency : NewConcurrencySet)
				if (!Wave->ConcurrencySet.Contains(Concurrency)) { bConcurrencySetChanged = true; break; }
		const bool bCompressionChanged = NewCompression != CurrentCompression;
		const bool bCompressionQualityChanged = Body.bSetCompressionQuality && NewCompressionQuality != CurrentCompressionQuality;
		const bool bSampleRateQualityChanged = !Body.SampleRateQuality.IsEmpty() && NewSampleRateQuality != CurrentSampleRateQuality;
		const bool bLoadingBehaviorChanged = !Body.LoadingBehavior.IsEmpty() && NewLoadingBehavior != CurrentLoadingBehavior;
		const bool bChanged = bCompressionChanged || bCompressionQualityChanged || bSampleRateQualityChanged
			|| (Body.bSetLooping && bNewLooping != static_cast<bool>(Wave->bLooping))
			|| bLoadingBehaviorChanged || bCloudStreamingChanged
			|| (Body.bSetSoundClass && NewSoundClass != Wave->SoundClassObject)
			|| (Body.bSetAttenuation && NewAttenuation != Wave->AttenuationSettings)
			|| (Body.bSetConcurrencyPaths && bConcurrencySetChanged)
			|| (Body.bSetOverrideConcurrency && Body.bOverrideConcurrency != static_cast<bool>(Wave->bOverrideConcurrency));
		if (bChanged && !Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetSoundWaveSettings", "Set Sound Wave Settings"));
			Wave->Modify();
			if (bCompressionQualityChanged)
				CompressionQualityProperty->SetPropertyValue_InContainer(Wave, NewCompressionQuality);
			if (bSampleRateQualityChanged) Wave->SampleRateQuality = NewSampleRateQuality;
			if (Body.bSetLooping) Wave->bLooping = bNewLooping;
			if (bLoadingBehaviorChanged) Wave->LoadingBehavior = NewLoadingBehavior;
			if (Body.bSetCloudStreaming) Wave->SetCloudStreamingEnabled(bNewCloudStreaming);
			if (Body.bSetSoundClass) Wave->SoundClassObject = NewSoundClass;
			if (Body.bSetAttenuation) Wave->AttenuationSettings = NewAttenuation;
			if (Body.bSetConcurrencyPaths && bConcurrencySetChanged) Wave->ConcurrencySet = MoveTemp(NewConcurrencySet);
			if (Body.bSetOverrideConcurrency) Wave->bOverrideConcurrency = Body.bOverrideConcurrency;
			if (bCompressionChanged)
				Wave->SetSoundAssetCompressionType(NewCompression, true);
			else if (bCompressionQualityChanged || bSampleRateQualityChanged || (bCloudStreamingChanged && !bNewCloudStreaming))
				Wave->InvalidateCompressedData(false, true);
			if (bCloudStreamingChanged && bNewCloudStreaming) Wave->TriggerRecookForCloudStreaming();
			MarkAssetDirty(Wave);
			SaveIfRequested(Wave, Body.bSave);
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Wave->GetPathName());
		Writer->WriteValue(TEXT("changed"), bChanged && !Body.bDryRun);
		Writer->WriteValue(TEXT("would_change"), bChanged);
		Writer->WriteValue(TEXT("dry_run"), Body.bDryRun);
		Writer->WriteValue(TEXT("saved"), bChanged && !Body.bDryRun && Body.bSave);
		Writer->WriteValue(TEXT("dirty"), Wave->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/audio/waves/rebuild", [](const FHttpContext<FAudioWaveRebuildReq, FString>& C)
	{
		const FAudioWaveRebuildReq Body = C.RequestBody();
		USoundWave* Wave = Cast<USoundWave>(LoadAsset(Body.AssetPath));
		if (!Wave) throw std::runtime_error("Asset is not a Sound Wave");
		if (!IsInGameThread()) throw std::runtime_error("Sound Wave platform-data rebuild requires the editor game thread");
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"would_rebuild\":true,\"asset_path\":\"%s\",\"dry_run\":true,\"dirty\":%s}"),
				*Wave->GetPathName(), Wave->GetOutermost()->IsDirty() ? TEXT("true") : TEXT("false")), TEXT("application/json"));
		Wave->ForceRebuildPlatformData();
		Wave->FinishCachePlatformData();
		const bool bComplete = !Wave->IsCompiling();
		if (Body.bSave) SaveIfRequested(Wave, true);
		return C.TextResponse(FString::Printf(TEXT("{\"rebuilt\":true,\"completed\":%s,\"chunk_count\":%d,\"saved\":%s,\"dirty\":%s}"),
			bComplete ? TEXT("true") : TEXT("false"), Wave->GetNumChunks(), Body.bSave ? TEXT("true") : TEXT("false"),
			Wave->GetOutermost()->IsDirty() ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/audio/waves/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		USoundWave* Wave = Cast<USoundWave>(LoadAsset(C.RequestBody().AssetPath));
		if (!Wave) throw std::runtime_error("Asset is not a Sound Wave");
		TArray<FString> Errors;
		TArray<FString> Warnings;
		const ESoundAssetCompressionType CompressionType = Wave->GetSoundAssetCompressionTypeEnum();
		const FIntProperty* CompressionQualityProperty = FindFProperty<FIntProperty>(USoundWave::StaticClass(), FName(TEXT("CompressionQuality")));
		const int32 CompressionQuality = CompressionQualityProperty ? CompressionQualityProperty->GetPropertyValue_InContainer(Wave) : Wave->GetCompressionQuality();
		if (static_cast<uint8>(CompressionType) > static_cast<uint8>(ESoundAssetCompressionType::RADAudio))
			Errors.Add(TEXT("compression_type is not a recognized ESoundAssetCompressionType value"));
		if (CompressionQuality < 1 || CompressionQuality > 100)
			Errors.Add(TEXT("stored compression_quality must be between 1 and 100"));
		if (!FMath::IsFinite(Wave->Volume) || Wave->Volume < 0.0f) Errors.Add(TEXT("volume must be finite and nonnegative"));
		if (!FMath::IsFinite(Wave->Pitch) || Wave->Pitch < 0.125f || Wave->Pitch > 4.0f) Errors.Add(TEXT("pitch must be finite and between 0.125 and 4.0"));
		if (!Wave->bProcedural && !Wave->bIsSourceBus)
		{
			if (!FMath::IsFinite(Wave->GetDuration()) || Wave->GetDuration() <= 0.0f) Errors.Add(TEXT("imported Sound Wave duration must be finite and positive"));
			if (Wave->NumChannels <= 0) Errors.Add(TEXT("imported Sound Wave must have at least one channel"));
			if (Wave->GetImportedSampleRate() <= 0) Errors.Add(TEXT("imported Sound Wave sample rate must be positive"));
			if (!Wave->AssetImportData || Wave->AssetImportData->ExtractFilenames().IsEmpty())
				Warnings.Add(TEXT("Sound Wave has no recorded source file; packaged audio data may still be usable"));
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Wave->GetPathName());
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("validation_scope"), TEXT("sound_wave_settings_and_import_metadata"));
		Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Wave->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/sound-cues/create", [](const FHttpContext<FSoundCueCreateReq, FString>& C)
	{
		const FSoundCueCreateReq Body = C.RequestBody();
		if (!IsInGameThread()) throw std::runtime_error("Sound Cue asset creation requires the editor game thread");
		if (Body.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(Body.AssetPath, false))
			throw std::runtime_error("asset_path must be a valid long package name without an object suffix");
		FString UniquePackageName;
		FString UniqueAssetName;
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		AssetToolsModule.Get().CreateUniqueAssetName(Body.AssetPath, TEXT(""), UniquePackageName, UniqueAssetName);
		const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *UniquePackageName, *UniqueAssetName);
		if (Body.bDryRun)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart(); Writer->WriteValue(TEXT("would_create"), true);
			Writer->WriteValue(TEXT("asset_path"), ObjectPath); Writer->WriteValue(TEXT("dry_run"), true);
			Writer->WriteObjectEnd(); Writer->Close();
			return C.TextResponse(Json, TEXT("application/json"));
		}
		USoundCueFactoryNew* Factory = NewObject<USoundCueFactoryNew>();
		USoundCue* Cue = Cast<USoundCue>(AssetToolsModule.Get().CreateAsset(
			UniqueAssetName, FPackageName::GetLongPackagePath(UniquePackageName), USoundCue::StaticClass(), Factory));
		if (!Cue) throw std::runtime_error("failed to create Sound Cue asset");
		if (!Cue->GetGraph()) Cue->CreateGraph();
		MarkAssetDirty(Cue);
		SaveIfRequested(Cue, Body.bSave);
		return C.TextResponse(Cue->GetPathName(), TEXT("text/plain"));
	});

	App->Get("/sound-cues/graph", [](const FHttpContext<void, FString>& C)
	{
		USoundCue* Cue = Cast<USoundCue>(LoadAsset(C.Query("asset_path")));
		if (!Cue) throw std::runtime_error("Asset is not a Sound Cue");
		return C.TextResponse(SoundCueGraphJson(Cue), TEXT("application/json"));
	});

	App->Post("/sound-cues/graph", [](const FHttpContext<FSoundCueGraphReq, FString>& C)
	{
		const FSoundCueGraphReq Body = C.RequestBody();
		USoundCue* Cue = Cast<USoundCue>(LoadAsset(Body.AssetPath));
		if (!Cue) throw std::runtime_error("Asset is not a Sound Cue");
		return C.TextResponse(SoundCueGraphOperation(Cue, Body), TEXT("application/json"));
	});

	App->Post("/sound-cues/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		USoundCue* Cue = Cast<USoundCue>(LoadAsset(C.RequestBody().AssetPath));
		if (!Cue) throw std::runtime_error("Asset is not a Sound Cue");
		return C.TextResponse(ValidateSoundCueGraph(Cue), TEXT("application/json"));
	});

	App->Post("/metasounds/create", [](const FHttpContext<FMetaSoundCreateReq, FString>& C)
	{
		return C.TextResponse(MetaSoundGraphUtils::Create(C.RequestBody()), TEXT("application/json"));
	});

	App->Get("/metasounds/node-classes", [](const FHttpContext<void, FString>& C)
	{
		const FString LimitText = C.Query("limit");
		const int32 Limit = LimitText.IsEmpty() ? 100 : FCString::Atoi(*LimitText);
		return C.TextResponse(MetaSoundGraphUtils::NodeClasses(C.Query("search"), Limit), TEXT("application/json"));
	});

	App->Get("/metasounds/graph", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		return C.TextResponse(MetaSoundGraphUtils::Inspect(Asset), TEXT("application/json"));
	});

	App->Post("/metasounds/graph", [](const FHttpContext<FMetaSoundGraphReq, FString>& C)
	{
		const FMetaSoundGraphReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		return C.TextResponse(MetaSoundGraphUtils::Mutate(Asset, Body), TEXT("application/json"));
	});

	App->Post("/metasounds/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		UObject* Asset = LoadAsset(C.RequestBody().AssetPath);
		return C.TextResponse(MetaSoundGraphUtils::Validate(Asset), TEXT("application/json"));
	});

	App->Post("/metasounds/compile", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		const FAssetPropertyReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		return C.TextResponse(MetaSoundGraphUtils::Compile(Asset, Body.bDryRun, Body.bSave), TEXT("application/json"));
	});

	App->Get("/audio/waves/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundWave* Asset = Cast<USoundWave>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not a Sound Wave");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/audio/waves/import-formats", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(SoundWaveImportUtils::FormatsJson(), TEXT("application/json"));
	});

	App->Get("/audio/waves/source", [](const FHttpContext<void, FString>& C)
	{
		USoundWave* Wave = Cast<USoundWave>(LoadAsset(C.Query("asset_path")));
		if (!Wave) throw std::runtime_error("Asset is not a Sound Wave");
		return C.TextResponse(SoundWaveImportUtils::SourceJson(Wave), TEXT("application/json"));
	});

	App->Post("/audio/waves/import", [](const FHttpContext<FSoundWaveImportReq, FString>& C)
	{
		return C.TextResponse(SoundWaveImportUtils::Import(C.RequestBody()), TEXT("application/json"));
	});

	App->Post("/audio/waves/reimport", [](const FHttpContext<FSoundWaveImportReq, FString>& C)
	{
		const FSoundWaveImportReq Body = C.RequestBody();
		USoundWave* Wave = Cast<USoundWave>(LoadAsset(Body.AssetPath));
		if (!Wave) throw std::runtime_error("Asset is not a Sound Wave");
		return C.TextResponse(SoundWaveImportUtils::Reimport(Wave, Body), TEXT("application/json"));
	});

	App->Get("/sound-cues/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundCue* Asset = Cast<USoundCue>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not a Sound Cue");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/sound-classes/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundClass* Asset = Cast<USoundClass>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not a Sound Class");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/sound-mixes/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundMix* Asset = Cast<USoundMix>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not a Sound Mix");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/sound-submixes/inspect", [](const FHttpContext<void, FString>& C)
	{
		USoundSubmix* Asset = Cast<USoundSubmix>(LoadAsset(C.Query("asset_path")));
		if (!Asset) throw std::runtime_error("Asset is not a Sound Submix");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/sound-classes/settings", [](const FHttpContext<void, FString>& C)
	{
		USoundClass* Asset = Cast<USoundClass>(LoadAsset(C.Query("asset_path")));
		return C.TextResponse(AudioTypedSettingsUtils::InspectSoundClass(Asset), TEXT("application/json"));
	});

	App->Patch("/sound-classes/settings", [](const FHttpContext<FSoundClassSettingsReq, FString>& C)
	{
		const FSoundClassSettingsReq Body = C.RequestBody();
		USoundClass* Asset = Cast<USoundClass>(LoadAsset(Body.AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::EditSoundClass(Asset, Body), TEXT("application/json"));
	});

	App->Post("/sound-classes/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		USoundClass* Asset = Cast<USoundClass>(LoadAsset(C.RequestBody().AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::ValidateSoundClass(Asset), TEXT("application/json"));
	});

	App->Get("/sound-mixes/settings", [](const FHttpContext<void, FString>& C)
	{
		USoundMix* Asset = Cast<USoundMix>(LoadAsset(C.Query("asset_path")));
		return C.TextResponse(AudioTypedSettingsUtils::InspectSoundMix(Asset), TEXT("application/json"));
	});

	App->Patch("/sound-mixes/settings", [](const FHttpContext<FSoundMixSettingsReq, FString>& C)
	{
		const FSoundMixSettingsReq Body = C.RequestBody();
		USoundMix* Asset = Cast<USoundMix>(LoadAsset(Body.AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::EditSoundMix(Asset, Body), TEXT("application/json"));
	});

	App->Post("/sound-mixes/adjusters", [](const FHttpContext<FSoundMixAdjusterReq, FString>& C)
	{
		const FSoundMixAdjusterReq Body = C.RequestBody();
		USoundMix* Asset = Cast<USoundMix>(LoadAsset(Body.AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::EditSoundMixAdjuster(Asset, Body), TEXT("application/json"));
	});

	App->Post("/sound-mixes/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		USoundMix* Asset = Cast<USoundMix>(LoadAsset(C.RequestBody().AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::ValidateSoundMix(Asset), TEXT("application/json"));
	});

	App->Get("/sound-submixes/settings", [](const FHttpContext<void, FString>& C)
	{
		USoundSubmix* Asset = Cast<USoundSubmix>(LoadAsset(C.Query("asset_path")));
		return C.TextResponse(AudioTypedSettingsUtils::InspectSoundSubmix(Asset), TEXT("application/json"));
	});

	App->Patch("/sound-submixes/settings", [](const FHttpContext<FSoundSubmixSettingsReq, FString>& C)
	{
		const FSoundSubmixSettingsReq Body = C.RequestBody();
		USoundSubmix* Asset = Cast<USoundSubmix>(LoadAsset(Body.AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::EditSoundSubmix(Asset, Body), TEXT("application/json"));
	});

	App->Post("/sound-submixes/effects", [](const FHttpContext<FSoundSubmixEffectReq, FString>& C)
	{
		const FSoundSubmixEffectReq Body = C.RequestBody();
		USoundSubmix* Asset = Cast<USoundSubmix>(LoadAsset(Body.AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::EditSoundSubmixEffect(Asset, Body), TEXT("application/json"));
	});

	App->Post("/sound-submixes/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		USoundSubmix* Asset = Cast<USoundSubmix>(LoadAsset(C.RequestBody().AssetPath));
		return C.TextResponse(AudioTypedSettingsUtils::ValidateSoundSubmix(Asset), TEXT("application/json"));
	});

	App->Patch("/audio/assets/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		if (!Asset->IsA<USoundWave>() && !Asset->IsA<USoundCue>() && !Asset->IsA<USoundClass>() && !Asset->IsA<USoundMix>() && !Asset->IsA<USoundSubmix>() && !Asset->IsA<USoundAttenuation>() && !Asset->IsA<USoundConcurrency>())
			throw std::runtime_error("Asset is not a supported audio asset");
		ApplyAssetProperties(Asset, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/audio/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		UObject* Asset = LoadAsset(C.RequestBody().AssetPath);
		if (ModulationUtils::Supports(Asset)) return C.TextResponse(ModulationUtils::Validate(Asset), TEXT("application/json"));
		if (Asset->IsA<UDialogueVoice>() || Asset->IsA<UDialogueWave>()) return C.TextResponse(DialogueUtils::Validate(Asset), TEXT("application/json"));
		const bool bSupported = Asset->IsA<USoundWave>() || Asset->IsA<USoundCue>() || Asset->IsA<USoundClass>() || Asset->IsA<USoundMix>() || Asset->IsA<USoundSubmix>() || Asset->IsA<USoundAttenuation>() || Asset->IsA<USoundConcurrency>();
		return C.TextResponse(FString::Printf(TEXT("{\"valid\":%s,\"class\":\"%s\"}"), bSupported ? TEXT("true") : TEXT("false"), *Asset->GetClass()->GetPathName()), TEXT("application/json"));
	});

	App->Delete("/blackboards/keys", [](const FHttpContext<FBlackboardKeyReq, FString>& C)
	{
		return C.TextResponse(BlackboardUtils::Control(C.RequestBody(),TEXT("delete")),TEXT("application/json"));
	});

	App->Get("/input-actions/inspect", [](const FHttpContext<void, FString>& C)
	{
		UInputAction* Action = Cast<UInputAction>(LoadAsset(C.Query("asset_path")));
		if (!Action) throw std::runtime_error("Asset is not an Enhanced Input Action");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Action), TEXT("application/json"));
	});

	App->Patch("/input-actions/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UInputAction* Action = Cast<UInputAction>(LoadAsset(Body.AssetPath));
		if (!Action) throw std::runtime_error("Asset is not an Enhanced Input Action");
		ApplyAssetProperties(Action, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/input-mapping-contexts/inspect", [](const FHttpContext<void, FString>& C)
	{
		UInputMappingContext* Context = Cast<UInputMappingContext>(LoadAsset(C.Query("asset_path")));
		if (!Context) throw std::runtime_error("Asset is not an Enhanced Input Mapping Context");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Context->GetPathName());
		Writer->WriteArrayStart(TEXT("mappings"));
		for (const FEnhancedActionKeyMapping& Mapping : Context->GetMappings())
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("action_path"), Mapping.Action ? Mapping.Action->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("key"), Mapping.Key.GetFName().ToString());
			Writer->WriteValue(TEXT("trigger_count"), Mapping.Triggers.Num());
			Writer->WriteValue(TEXT("modifier_count"), Mapping.Modifiers.Num());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/input-mapping-contexts/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UInputMappingContext* Context = Cast<UInputMappingContext>(LoadAsset(Body.AssetPath));
		if (!Context) throw std::runtime_error("Asset is not an Enhanced Input Mapping Context");
		ApplyAssetProperties(Context, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/input-mapping-contexts/mappings", [](const FHttpContext<FInputMappingReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UInputMappingContext* Context = Cast<UInputMappingContext>(LoadAsset(Body.AssetPath));
		UInputAction* Action = Cast<UInputAction>(LoadAsset(Body.ActionPath));
		const FKey Key(FName(*Body.Key));
		if (!Context || !Action || !Key.IsValid())
			throw std::runtime_error("asset_path, action_path, and a valid key name are required");
		Context->Modify();
		Context->MapKey(Action, Key);
		MarkAssetDirty(Context);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/input-mapping-contexts/mappings", [](const FHttpContext<FInputMappingReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UInputMappingContext* Context = Cast<UInputMappingContext>(LoadAsset(Body.AssetPath));
		UInputAction* Action = Cast<UInputAction>(LoadAsset(Body.ActionPath));
		const FKey OldKey(FName(*Body.Key));
		const FKey NewKey(FName(*Body.NewKey));
		if (!Context || !Action || !OldKey.IsValid() || !NewKey.IsValid())
			throw std::runtime_error("asset_path, action_path, key, and new_key are required");
		Context->Modify();
		Context->UnmapKey(Action, OldKey);
		Context->MapKey(Action, NewKey);
		MarkAssetDirty(Context);
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete("/input-mapping-contexts/mappings", [](const FHttpContext<FInputMappingReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UInputMappingContext* Context = Cast<UInputMappingContext>(LoadAsset(Body.AssetPath));
		UInputAction* Action = Cast<UInputAction>(LoadAsset(Body.ActionPath));
		const FKey Key(FName(*Body.Key));
		if (!Context || !Action || !Key.IsValid())
			throw std::runtime_error("asset_path, action_path, and a valid key name are required");
		Context->Modify();
		Context->UnmapKey(Action, Key);
		MarkAssetDirty(Context);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/assets/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		const FAssetPropertyReq Body = C.RequestBody();
		UObject* Asset = nullptr;
		TArray<TPair<FString, FString>> Errors;
		try { Asset = LoadAsset(Body.AssetPath); }
		catch (const std::exception& Error) { Errors.Emplace(TEXT("asset_path"), UTF8_TO_TCHAR(Error.what())); }
		if (Asset && !Body.AssetClass.IsEmpty())
		{
			UClass* ExpectedClass = LoadClass<UObject>(nullptr, *Body.AssetClass);
			if (!ExpectedClass || !Asset->GetClass()->IsChildOf(ExpectedClass))
				Errors.Emplace(TEXT("asset_class"), TEXT("asset_class does not match the loaded asset"));
		}
		TArray<FString> Keys;
		Body.Properties.GetKeys(Keys);
		Keys.Sort();
		int32 CheckedCount = 0;
		if (Asset && Errors.IsEmpty() && !Keys.IsEmpty())
		{
			if (Asset->IsA<UWorld>() || Asset->IsA<ULevel>())
				Errors.Emplace(TEXT("properties"), TEXT("world and level edits require dedicated editor routes"));
			else
			{
				UObject* Probe = DuplicateObject<UObject>(Asset, GetTransientPackage(),
					MakeUniqueObjectName(GetTransientPackage(), Asset->GetClass(), TEXT("UE5MCP_ValidationProbe")));
				if (!Probe) Errors.Emplace(TEXT("properties"), TEXT("asset could not be duplicated for property validation"));
				else
				{
					Probe->SetFlags(RF_Transient);
					for (const FString& Key : Keys)
					{
						try
						{
							ValidateBatchPropertyPath(Asset, Key);
							ObjUtils::SetPropertyValueFromString(Probe, Key, Body.Properties[Key]);
							++CheckedCount;
						}
						catch (const std::exception& Error) { Errors.Emplace(Key, UTF8_TO_TCHAR(Error.what())); }
					}
				}
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("asset_path"), Asset ? Asset->GetPathName() : Body.AssetPath);
		Writer->WriteValue(TEXT("class"), Asset ? Asset->GetClass()->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("property_count"), Keys.Num());
		Writer->WriteValue(TEXT("checked_property_count"), CheckedCount);
		Writer->WriteValue(TEXT("scope"), Keys.IsEmpty() ? TEXT("asset_identity") : TEXT("property_preflight"));
		Writer->WriteArrayStart(TEXT("errors"));
		for (const TPair<FString, FString>& Error : Errors)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("field"), Error.Key);
			Writer->WriteValue(TEXT("message"), Error.Value);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/assets/preview-operation", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		const FAssetPropertyReq Body = C.RequestBody();
		const FString Operation = Body.Operation.IsEmpty() ? TEXT("set_properties") : Body.Operation;
		const bool bSet = Operation.Equals(TEXT("set_properties"), ESearchCase::IgnoreCase);
		const bool bSave = Operation.Equals(TEXT("save"), ESearchCase::IgnoreCase);
		UObject* Asset = nullptr;
		TArray<TPair<FString, FString>> Errors;
		TArray<TPair<FString, bool>> Changes;
		try { Asset = LoadAsset(Body.AssetPath); }
		catch (const std::exception& Error) { Errors.Emplace(TEXT("asset_path"), UTF8_TO_TCHAR(Error.what())); }
		if (!bSet && !bSave) Errors.Emplace(TEXT("operation"), TEXT("operation must be set_properties or save"));
		if (Asset && !Body.AssetClass.IsEmpty())
		{
			UClass* ExpectedClass = LoadClass<UObject>(nullptr, *Body.AssetClass);
			if (!ExpectedClass || !Asset->IsA(ExpectedClass))
				Errors.Emplace(TEXT("asset_class"), TEXT("asset_class does not match the loaded asset"));
		}
		TArray<FString> Keys;
		Body.Properties.GetKeys(Keys);
		Keys.Sort();
		if (bSave && !Keys.IsEmpty()) Errors.Emplace(TEXT("properties"), TEXT("save does not accept properties"));
		if (bSet && Keys.IsEmpty()) Errors.Emplace(TEXT("properties"), TEXT("set_properties requires properties"));
		if (Asset && bSet && Errors.IsEmpty())
		{
			if (Asset->IsA<UWorld>() || Asset->IsA<ULevel>())
				Errors.Emplace(TEXT("properties"), TEXT("world and level edits require dedicated editor routes"));
			else
			{
				UObject* Probe = DuplicateObject<UObject>(Asset, GetTransientPackage(),
					MakeUniqueObjectName(GetTransientPackage(), Asset->GetClass(), TEXT("UE5MCP_PreviewProbe")));
				if (!Probe) Errors.Emplace(TEXT("properties"), TEXT("asset could not be duplicated for preview"));
				else
				{
					Probe->SetFlags(RF_Transient);
					for (const FString& Key : Keys)
					{
						try
						{
							ValidateBatchPropertyPath(Asset, Key);
							FString RootName;
							if (!Key.Split(TEXT("."), &RootName, nullptr)) RootName = Key;
							FProperty* RootProperty = FindBatchProperty(Asset->GetClass(), RootName);
							if (!RootProperty) throw std::runtime_error("property path does not exist");
							FString Before, After;
							RootProperty->ExportTextItem_Direct(Before, RootProperty->ContainerPtrToValuePtr<void>(Probe), nullptr, Probe, PPF_None, nullptr);
							ObjUtils::SetPropertyValueFromString(Probe, Key, Body.Properties[Key]);
							RootProperty->ExportTextItem_Direct(After, RootProperty->ContainerPtrToValuePtr<void>(Probe), nullptr, Probe, PPF_None, nullptr);
							Changes.Emplace(Key, Before != After);
						}
						catch (const std::exception& Error) { Errors.Emplace(Key, UTF8_TO_TCHAR(Error.what())); }
					}
				}
			}
		}
		const bool bDirty = Asset && Asset->GetOutermost() && Asset->GetOutermost()->IsDirty();
		bool bWouldChange = bSave && bDirty;
		for (const TPair<FString, bool>& Change : Changes) bWouldChange |= Change.Value;
		bWouldChange = Errors.IsEmpty() && bWouldChange;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("dry_run"), true);
		Writer->WriteValue(TEXT("changed"), false);
		Writer->WriteValue(TEXT("would_change"), bWouldChange);
		Writer->WriteValue(TEXT("dirty"), bDirty);
		Writer->WriteValue(TEXT("saved"), false);
		Writer->WriteValue(TEXT("asset_path"), Asset ? Asset->GetPathName() : Body.AssetPath);
		Writer->WriteValue(TEXT("operation"), Operation);
		Writer->WriteValue(TEXT("property_count"), Keys.Num());
		Writer->WriteArrayStart(TEXT("changes"));
		for (const TPair<FString, bool>& Change : Changes)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("path"), Change.Key);
			Writer->WriteValue(TEXT("input"), Body.Properties[Change.Key]);
			Writer->WriteValue(TEXT("would_change"), Change.Value);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("errors"));
		for (const TPair<FString, FString>& Error : Errors)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("field"), Error.Key);
			Writer->WriteValue(TEXT("message"), Error.Value);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/assets/batch", [](const FHttpContext<FAssetBatchReq, FString>& C)
	{
		const FAssetBatchReq Body = C.RequestBody();
		if (Body.Operations.IsEmpty() && !Body.AssetPath.IsEmpty())
		{
			FAssetPropertyReq Legacy;
			Legacy.AssetPath = Body.AssetPath;
			Legacy.AssetClass = Body.AssetClass;
			Legacy.Operation = Body.Operation;
			Legacy.Properties = Body.Properties;
			Legacy.bDryRun = Body.bDryRun;
			Legacy.bSave = Body.bSave;
			Legacy.bConfirm = Body.bConfirm;
			ApplyAssetProperties(LoadAsset(Legacy.AssetPath), Legacy);
			return C.TextResponse(TEXT("{\"Success\":true}"), TEXT("application/json"));
		}
		if (Body.Operations.IsEmpty() || Body.Operations.Num() > 128)
			throw std::runtime_error("operations must contain between 1 and 128 entries");
		if (!IsInGameThread()) throw std::runtime_error("batch operations require the editor game thread");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("results"));
		bool bPreviousError = false;
		int32 ChangedCount = 0;
		int32 FailureCount = 0;
		for (int32 Index = 0; Index < Body.Operations.Num(); ++Index)
		{
			const FAssetPropertyReq& Operation = Body.Operations[Index];
			const FString OperationName = Operation.Operation.IsEmpty() ? TEXT("set_properties") : Operation.Operation;
			const bool bDryRun = Body.bDryRun || Operation.bDryRun;
			const bool bSkipped = Body.bStopOnError && bPreviousError;
			bool bChanged = false;
			bool bSaved = false;
			FString Error;
			UObject* Asset = nullptr;
			if (bSkipped) Error = TEXT("skipped after an earlier batch operation failed");
			else try
			{
				Asset = LoadAsset(Operation.AssetPath);
				if (!Operation.AssetClass.IsEmpty())
				{
					UClass* ExpectedClass = LoadClass<UObject>(nullptr, *Operation.AssetClass);
					if (!ExpectedClass || !Asset->IsA(ExpectedClass)) throw std::runtime_error("asset_class does not match the asset");
				}
				if (OperationName.Equals(TEXT("set_properties"), ESearchCase::IgnoreCase))
				{
					const TArray<FString> Keys = ValidateBatchPropertyValues(Asset, Operation);
					if (!bDryRun)
					{
						const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "BatchAssetProperties", "Batch Asset Properties"));
						Asset->Modify();
						for (const FString& Key : Keys)
						{
							ObjUtils::SetPropertyValueFromString(Asset, Key, Operation.Properties[Key]);
							bChanged = true;
						}
						MarkAssetDirty(Asset);
						if (Body.bSave || Operation.bSave)
						{
							SaveIfRequested(Asset, true);
							bSaved = true;
						}
					}
				}
				else if (OperationName.Equals(TEXT("save"), ESearchCase::IgnoreCase))
				{
					if (!Operation.Properties.IsEmpty()) throw std::runtime_error("save operation does not accept properties");
					if (!bDryRun)
					{
						SaveIfRequested(Asset, true);
						bSaved = true;
					}
				}
				else throw std::runtime_error("operation must be set_properties or save");
			}
			catch (const std::exception& Exception)
			{
				Error = UTF8_TO_TCHAR(Exception.what());
			}
			const bool bSuccess = Error.IsEmpty();
			if (!bSuccess) { bPreviousError = true; ++FailureCount; }
			if (bChanged) ++ChangedCount;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("index"), Index);
			Writer->WriteValue(TEXT("asset_path"), Asset ? Asset->GetPathName() : Operation.AssetPath);
			Writer->WriteValue(TEXT("operation"), OperationName);
			Writer->WriteValue(TEXT("success"), bSuccess);
			Writer->WriteValue(TEXT("skipped"), bSkipped);
			Writer->WriteValue(TEXT("dry_run"), bDryRun);
			Writer->WriteValue(TEXT("changed"), bChanged);
			Writer->WriteValue(TEXT("dirty"), Asset && Asset->GetOutermost() && Asset->GetOutermost()->IsDirty());
			Writer->WriteValue(TEXT("saved"), bSaved);
			Writer->WriteValue(TEXT("transaction"), bChanged ? TEXT("editor") : TEXT("none"));
			Writer->WriteArrayStart(TEXT("warnings")); Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("errors"));
			if (!Error.IsEmpty()) Writer->WriteValue(Error);
			Writer->WriteArrayEnd();
			Writer->WriteObjectStart(TEXT("validation"));
			Writer->WriteValue(TEXT("valid"), bSuccess);
			Writer->WriteObjectEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("success"), FailureCount == 0);
		Writer->WriteValue(TEXT("changed_count"), ChangedCount);
		Writer->WriteValue(TEXT("failure_count"), FailureCount);
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/assets/save-all-selected", [](const FHttpContext<FAssetActionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (Body.AssetPath.IsEmpty() || !AssetSubsystem()->SaveAsset(Body.AssetPath, true))
			throw std::runtime_error("asset_path is required and must identify a saveable asset");
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/textures/inspect", [](const FHttpContext<void, FString>& C)
	{
		UTexture* Texture = Cast<UTexture>(LoadAsset(C.Query("asset_path")));
		if (!Texture)
			throw std::runtime_error("Asset is not a texture");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Texture), TEXT("application/json"));
	});

	App->Get("/textures/source", [](const FHttpContext<void, FString>& C)
	{
		UTexture* Texture = Cast<UTexture>(LoadAsset(C.Query("asset_path")));
		if (!Texture) throw std::runtime_error("Asset is not a texture");
		return C.TextResponse(TextureImportUtils::SourceJson(Texture), TEXT("application/json"));
	});

	App->Post("/textures/import", [](const FHttpContext<FTextureImportReq, FString>& C)
	{
		return C.TextResponse(TextureImportUtils::Import(C.RequestBody()), TEXT("application/json"));
	});

	App->Post("/textures/reimport", [](const FHttpContext<FTextureImportReq, FString>& C)
	{
		const FTextureImportReq Body = C.RequestBody();
		UTexture* Texture = Cast<UTexture>(LoadAsset(Body.AssetPath));
		if (!Texture) throw std::runtime_error("Asset is not a texture");
		return C.TextResponse(TextureImportUtils::Reimport(Texture, Body), TEXT("application/json"));
	});

	App->Patch("/textures/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UTexture* Texture = Cast<UTexture>(LoadAsset(Body.AssetPath));
		if (!Texture)
			throw std::runtime_error("Asset is not a texture");
		ApplyAssetProperties(Texture, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/textures/platform-settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UTexture* Texture = Cast<UTexture>(LoadAsset(Body.AssetPath));
		if (!Texture) throw std::runtime_error("Asset is not a texture");
		ApplyAssetProperties(Texture, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/textures/rebuild", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UTexture* Texture = Cast<UTexture>(LoadAsset(Body.AssetPath));
		if (!Texture) throw std::runtime_error("Asset is not a texture");
		Texture->Modify();
		Texture->UpdateResource();
		MarkAssetDirty(Texture);
		SaveIfRequested(Texture, Body.bSave);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/textures/refresh", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UTexture* Texture = Cast<UTexture>(LoadAsset(Body.AssetPath));
		if (!Texture) throw std::runtime_error("Asset is not a texture");
		Texture->UpdateResource();
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/textures/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UTexture* Texture = Cast<UTexture>(LoadAsset(Body.AssetPath));
		if (!Texture)
			throw std::runtime_error("Asset is not a texture");
		const UTexture2D* Texture2D = Cast<UTexture2D>(Texture);
		return C.TextResponse(FString::Printf(TEXT("{\"valid\":true,\"class\":\"%s\",\"size_x\":%d,\"size_y\":%d}"), *Texture->GetClass()->GetPathName(), Texture2D ? Texture2D->GetSizeX() : 0, Texture2D ? Texture2D->GetSizeY() : 0), TEXT("application/json"));
	});

	App->Get("/materials/inspect", [](const FHttpContext<void, FString>& C)
	{
		UMaterialInterface* Material = Cast<UMaterialInterface>(LoadAsset(C.Query("asset_path")));
		if (!Material)
			throw std::runtime_error("Asset is not a material or material instance");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Material), TEXT("application/json"));
	});

	App->Get("/materials/summary", [](const FHttpContext<void, FString>& C)
	{
		UMaterial* Material = Cast<UMaterial>(LoadAsset(C.Query("asset_path")));
		if (!Material) throw std::runtime_error("Asset is not a parent Material");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Material->GetPathName());
		Writer->WriteValue(TEXT("domain"), StaticEnum<EMaterialDomain>()->GetNameStringByValue(Material->MaterialDomain));
		Writer->WriteValue(TEXT("blend_mode"), StaticEnum<EBlendMode>()->GetNameStringByValue(Material->BlendMode));
		Writer->WriteValue(TEXT("two_sided"), Material->IsTwoSided());
		Writer->WriteValue(TEXT("shading_model_from_expression"), Material->IsShadingModelFromMaterialExpression());
		Writer->WriteArrayStart(TEXT("shading_models"));
		const FMaterialShadingModelField Models = Material->GetShadingModels();
		for (int32 Value = 0; Value < MSM_NUM; ++Value)
			if (Models.HasShadingModel(static_cast<EMaterialShadingModel>(Value)))
				Writer->WriteValue(StaticEnum<EMaterialShadingModel>()->GetNameStringByValue(Value));
		Writer->WriteArrayEnd();
		Writer->WriteObjectStart(TEXT("usage_flags"));
		for (TFieldIterator<FBoolProperty> It(UMaterial::StaticClass()); It; ++It)
		{
			const FBoolProperty* Property = *It;
			if (Property->GetName().StartsWith(TEXT("bUsedWith")) && Property->GetName() != TEXT("bUsedWithUI")
				&& !Property->GetName().EndsWith(TEXT("_DEPRECATED")) && !Property->HasAnyPropertyFlags(CPF_Deprecated)
				&& !Property->HasMetaData(TEXT("DeprecatedProperty")))
				Writer->WriteValue(Property->GetName(), Property->GetPropertyValue_InContainer(Material));
		}
		Writer->WriteObjectEnd();
		Writer->WriteValue(TEXT("dirty"), Material->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/materials/core-settings", [](const FHttpContext<FMaterialCoreSettingsReq, FString>& C)
	{
		const FMaterialCoreSettingsReq Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		if (!Material) throw std::runtime_error("Asset is not a parent Material");
		int64 DomainValue = INDEX_NONE;
		int64 BlendValue = INDEX_NONE;
		int64 ShadingValue = INDEX_NONE;
		if (!Body.Domain.IsEmpty())
		{
			DomainValue = StaticEnum<EMaterialDomain>()->GetValueByNameString(Body.Domain);
			if (DomainValue < 0 || DomainValue >= MD_MAX || DomainValue == MD_RuntimeVirtualTexture)
				throw std::runtime_error("domain must be a supported EMaterialDomain name such as MD_Surface");
		}
		if (!Body.BlendMode.IsEmpty())
		{
			BlendValue = StaticEnum<EBlendMode>()->GetValueByNameString(Body.BlendMode);
			if (BlendValue < 0 || BlendValue >= BLEND_MAX)
				throw std::runtime_error("blend_mode must be an EBlendMode name such as BLEND_Masked");
		}
		if (!Body.ShadingModel.IsEmpty())
		{
			ShadingValue = StaticEnum<EMaterialShadingModel>()->GetValueByNameString(Body.ShadingModel);
			if (ShadingValue < 0 || ShadingValue >= MSM_NUM)
				throw std::runtime_error("shading_model must be a concrete EMaterialShadingModel name such as MSM_Unlit");
		}
		TArray<TPair<FBoolProperty*, bool>> UsageChanges;
		for (const auto& Entry : Body.UsageFlags)
		{
			FBoolProperty* Property = FindFProperty<FBoolProperty>(UMaterial::StaticClass(), FName(*Entry.Key));
			if (!Property || !Property->GetName().StartsWith(TEXT("bUsedWith")) || Property->GetName() == TEXT("bUsedWithUI")
				|| Property->GetName().EndsWith(TEXT("_DEPRECATED")) || Property->HasAnyPropertyFlags(CPF_Deprecated)
				|| Property->HasMetaData(TEXT("DeprecatedProperty")))
				throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Unsupported Material usage flag: %s"), *Entry.Key)));
			if (Property->GetPropertyValue_InContainer(Material) != Entry.Value)
				UsageChanges.Emplace(Property, Entry.Value);
		}
		const bool bChanged = (DomainValue != INDEX_NONE && Material->MaterialDomain != DomainValue)
			|| (BlendValue != INDEX_NONE && Material->BlendMode != BlendValue)
			|| (ShadingValue != INDEX_NONE && (!Material->GetShadingModels().HasShadingModel(static_cast<EMaterialShadingModel>(ShadingValue)) || Material->IsShadingModelFromMaterialExpression()))
			|| (Body.bSetTwoSided && static_cast<bool>(Material->TwoSided) != Body.bTwoSided)
			|| !UsageChanges.IsEmpty();
		if (bChanged && !Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetMaterialCoreSettings", "Set Material Core Settings"));
			Material->Modify();
			if (DomainValue != INDEX_NONE) Material->MaterialDomain = static_cast<EMaterialDomain>(DomainValue);
			if (BlendValue != INDEX_NONE) Material->BlendMode = static_cast<EBlendMode>(BlendValue);
			if (ShadingValue != INDEX_NONE) Material->SetShadingModel(static_cast<EMaterialShadingModel>(ShadingValue));
			if (Body.bSetTwoSided) Material->TwoSided = Body.bTwoSided;
			for (const auto& Change : UsageChanges) Change.Key->SetPropertyValue_InContainer(Material, Change.Value);
			UMaterialEditingLibrary::RecompileMaterial(Material);
			MarkAssetDirty(Material);
			SaveIfRequested(Material, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s,\"dirty\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false"), Material->GetOutermost()->IsDirty() ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Get("/materials/parameters", [](const FHttpContext<void, FString>& C)
	{
		UMaterial* Material = Cast<UMaterial>(LoadAsset(C.Query("asset_path")));
		if (!Material) throw std::runtime_error("Asset is not a parent Material");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Material->GetPathName());
		Writer->WriteArrayStart(TEXT("parameters"));
		const EMaterialParameterType Types[] = { EMaterialParameterType::Scalar, EMaterialParameterType::Vector,
			EMaterialParameterType::Texture, EMaterialParameterType::StaticSwitch,
			EMaterialParameterType::Font, EMaterialParameterType::RuntimeVirtualTexture };
		for (EMaterialParameterType Type : Types)
		{
			TMap<FMaterialParameterInfo, FMaterialParameterMetadata> Parameters;
			Material->GetAllParametersOfType(Type, Parameters);
			for (const auto& Entry : Parameters)
			{
				const FMaterialParameterInfo& Info = Entry.Key;
				const FMaterialParameterMetadata& Meta = Entry.Value;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Info.Name.ToString());
				Writer->WriteValue(TEXT("type"), Type == EMaterialParameterType::StaticSwitch ? TEXT("static_switch") :
					Type == EMaterialParameterType::RuntimeVirtualTexture ? TEXT("runtime_virtual_texture") : *MaterialParameterTypeToString(Type).ToLower());
				Writer->WriteValue(TEXT("association"), Info.Association == LayerParameter ? TEXT("layer") : Info.Association == BlendParameter ? TEXT("blend") : TEXT("global"));
				Writer->WriteValue(TEXT("index"), Info.Index);
				Writer->WriteValue(TEXT("group"), Meta.Group.ToString());
				Writer->WriteValue(TEXT("description"), Meta.Description);
				if (Meta.Value.Type == EMaterialParameterType::Scalar) Writer->WriteValue(TEXT("value"), Meta.Value.AsScalar());
				else if (Meta.Value.Type == EMaterialParameterType::Vector) Writer->WriteValue(TEXT("value"), Meta.Value.AsLinearColor().ToString());
				else if (Meta.Value.Type == EMaterialParameterType::StaticSwitch) Writer->WriteValue(TEXT("value"), Meta.Value.AsStaticSwitch());
				else if (Meta.Value.Type == EMaterialParameterType::Texture || Meta.Value.Type == EMaterialParameterType::RuntimeVirtualTexture)
				{
					const UObject* Texture = Meta.Value.AsTextureObject();
					Writer->WriteValue(TEXT("value"), Texture ? Texture->GetPathName() : TEXT(""));
				}
				else if (Meta.Value.Type == EMaterialParameterType::Font)
				{
					Writer->WriteValue(TEXT("value"), Meta.Value.Font.Value ? Meta.Value.Font.Value->GetPathName() : TEXT(""));
					Writer->WriteValue(TEXT("font_page"), Meta.Value.Font.Page);
				}
				Writer->WriteObjectEnd();
			}
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/materials/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		if (!Material)
			throw std::runtime_error("Asset is not a parent Material");
		ApplyAssetProperties(Material, Body);
		if (!Body.bDryRun)
			UMaterialEditingLibrary::RecompileMaterial(Material);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/materials/compile", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		if (!Material) throw std::runtime_error("Asset is not a parent Material");
		UMaterialEditingLibrary::RecompileMaterial(Material);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/materials/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UMaterialInterface* Material = Cast<UMaterialInterface>(LoadAsset(Body.AssetPath));
		if (!Material) throw std::runtime_error("Asset is not a material or material instance");
		FMaterialResource* Resource = Material->GetMaterialResource(GMaxRHIShaderPlatform);
		const TArray<FString>* Errors = Resource ? &Resource->GetCompileErrors() : nullptr;
		const bool bComplete = Resource && Resource->IsGameThreadShaderMapComplete();
		const FString Status = !Resource ? TEXT("unavailable") : Errors && !Errors->IsEmpty() ? TEXT("error") : bComplete ? TEXT("ok") : TEXT("compiling");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Material->GetPathName());
		Writer->WriteValue(TEXT("class"), Material->GetClass()->GetPathName());
		Writer->WriteValue(TEXT("valid"), Status == TEXT("ok"));
		Writer->WriteValue(TEXT("status"), Status);
		Writer->WriteArrayStart(TEXT("compile_errors"));
		if (Errors) for (const FString& Error : *Errors) Writer->WriteValue(Error);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/material-instances/inspect", [](const FHttpContext<void, FString>& C)
	{
		UMaterialInstanceConstant* Material = Cast<UMaterialInstanceConstant>(LoadAsset(C.Query("asset_path")));
		if (!Material)
			throw std::runtime_error("Asset is not a Material Instance Constant");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Material), TEXT("application/json"));
	});

	App->Patch("/material-instances/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterialInstanceConstant* Material = Cast<UMaterialInstanceConstant>(LoadAsset(Body.AssetPath));
		if (!Material)
			throw std::runtime_error("Asset is not a Material Instance Constant");
		ApplyAssetProperties(Material, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/material-instances/parameters", [](const FHttpContext<void, FString>& C)
	{
		UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(LoadAsset(C.Query("asset_path")));
		if (!Instance) throw std::runtime_error("Asset is not a Material Instance Constant");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Instance->GetPathName());
		Writer->WriteValue(TEXT("parent_path"), Instance->Parent ? Instance->Parent->GetPathName() : TEXT(""));
		Writer->WriteArrayStart(TEXT("parameters"));
		const EMaterialParameterType Types[] = { EMaterialParameterType::Scalar, EMaterialParameterType::Vector,
			EMaterialParameterType::Texture, EMaterialParameterType::StaticSwitch,
			EMaterialParameterType::Font, EMaterialParameterType::RuntimeVirtualTexture };
		for (EMaterialParameterType Type : Types)
		{
			TMap<FMaterialParameterInfo, FMaterialParameterMetadata> Parameters;
			Instance->GetAllParametersOfType(Type, Parameters);
			for (const auto& Entry : Parameters)
			{
				const FMaterialParameterInfo& Info = Entry.Key;
				const FMaterialParameterMetadata& Meta = Entry.Value;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Info.Name.ToString());
				Writer->WriteValue(TEXT("type"), Type == EMaterialParameterType::StaticSwitch ? TEXT("static_switch") :
					Type == EMaterialParameterType::RuntimeVirtualTexture ? TEXT("runtime_virtual_texture") : *MaterialParameterTypeToString(Type).ToLower());
				Writer->WriteValue(TEXT("association"), Info.Association == LayerParameter ? TEXT("layer") : Info.Association == BlendParameter ? TEXT("blend") : TEXT("global"));
				Writer->WriteValue(TEXT("index"), Info.Index);
				Writer->WriteValue(TEXT("group"), Meta.Group.ToString());
				Writer->WriteValue(TEXT("description"), Meta.Description);
				Writer->WriteValue(TEXT("overridden"), Meta.bOverride);
				if (Meta.Value.Type == EMaterialParameterType::Scalar)
					Writer->WriteValue(TEXT("value"), Meta.Value.AsScalar());
				else if (Meta.Value.Type == EMaterialParameterType::Vector)
					Writer->WriteValue(TEXT("value"), Meta.Value.AsLinearColor().ToString());
				else if (Meta.Value.Type == EMaterialParameterType::StaticSwitch)
					Writer->WriteValue(TEXT("value"), Meta.Value.AsStaticSwitch());
				else if (Meta.Value.Type == EMaterialParameterType::Texture || Meta.Value.Type == EMaterialParameterType::RuntimeVirtualTexture)
				{
					const UObject* Texture = Meta.Value.AsTextureObject();
					Writer->WriteValue(TEXT("value"), Texture ? Texture->GetPathName() : TEXT(""));
				}
				else if (Meta.Value.Type == EMaterialParameterType::Font)
				{
					Writer->WriteValue(TEXT("value"), Meta.Value.Font.Value ? Meta.Value.Font.Value->GetPathName() : TEXT(""));
					Writer->WriteValue(TEXT("font_page"), Meta.Value.Font.Page);
				}
				Writer->WriteObjectEnd();
			}
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/material-instances/parameters", [](const FHttpContext<FMaterialInstanceReq, FString>& C)
	{
		const FMaterialInstanceReq Body = C.RequestBody();
		UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(LoadAsset(Body.AssetPath));
		if (!Instance) throw std::runtime_error("Asset is not a Material Instance Constant");
		EMaterialParameterType Type = EMaterialParameterType::None;
		if (Body.ParameterType.Equals(TEXT("scalar"), ESearchCase::IgnoreCase)) Type = EMaterialParameterType::Scalar;
		else if (Body.ParameterType.Equals(TEXT("vector"), ESearchCase::IgnoreCase)) Type = EMaterialParameterType::Vector;
		else if (Body.ParameterType.Equals(TEXT("texture"), ESearchCase::IgnoreCase)) Type = EMaterialParameterType::Texture;
		else if (Body.ParameterType.Equals(TEXT("static_switch"), ESearchCase::IgnoreCase)) Type = EMaterialParameterType::StaticSwitch;
		else if (Body.ParameterType.Equals(TEXT("runtime_virtual_texture"), ESearchCase::IgnoreCase)) Type = EMaterialParameterType::RuntimeVirtualTexture;
		else if (Body.ParameterType.Equals(TEXT("font"), ESearchCase::IgnoreCase)) Type = EMaterialParameterType::Font;
		else throw std::runtime_error("parameter_type must be scalar, vector, texture, static_switch, runtime_virtual_texture, or font");
		if (Body.ParameterName.IsEmpty()) throw std::runtime_error("parameter_name is required");
		EMaterialParameterAssociation Association = GlobalParameter;
		if (Body.Association.Equals(TEXT("layer"), ESearchCase::IgnoreCase)) Association = LayerParameter;
		else if (Body.Association.Equals(TEXT("blend"), ESearchCase::IgnoreCase)) Association = BlendParameter;
		else if (!Body.Association.IsEmpty() && !Body.Association.Equals(TEXT("global"), ESearchCase::IgnoreCase))
			throw std::runtime_error("association must be global, layer, or blend");
		if ((Association == GlobalParameter && Body.Index != INDEX_NONE) || (Association != GlobalParameter && Body.Index < 0))
			throw std::runtime_error("index must be -1 for global or nonnegative for layer/blend");
		const FMaterialParameterInfo Info(FName(*Body.ParameterName), Association, Body.Index);
		TMap<FMaterialParameterInfo, FMaterialParameterMetadata> Parameters;
		Instance->GetAllParametersOfType(Type, Parameters);
		if (!Parameters.Contains(Info)) throw std::runtime_error("Parameter does not exist on the material instance or parent");
		float Scalar = 0;
		FLinearColor Color = FLinearColor::Black;
		UTexture* Texture = nullptr;
		URuntimeVirtualTexture* RuntimeTexture = nullptr;
		UFont* Font = nullptr;
		bool bSwitch = false;
		if (Type == EMaterialParameterType::Scalar)
		{
			if (!LexTryParseString(Scalar, *Body.Value) || !FMath::IsFinite(Scalar)) throw std::runtime_error("scalar value must be finite numeric text");
		}
		else if (Type == EMaterialParameterType::Vector)
		{
			if (!Color.InitFromString(Body.Value) || !FMath::IsFinite(Color.R) || !FMath::IsFinite(Color.G) || !FMath::IsFinite(Color.B) || !FMath::IsFinite(Color.A))
				throw std::runtime_error("vector value must use finite R=,G=,B=,A= components");
		}
		else if (Type == EMaterialParameterType::Texture)
		{
			Texture = Cast<UTexture>(LoadAsset(Body.Value));
			if (!Texture) throw std::runtime_error("texture value must identify a Texture asset");
		}
		else if (Type == EMaterialParameterType::RuntimeVirtualTexture)
		{
			RuntimeTexture = Cast<URuntimeVirtualTexture>(LoadAsset(Body.Value));
			if (!RuntimeTexture) throw std::runtime_error("runtime_virtual_texture value must identify a Runtime Virtual Texture asset");
		}
		else if (Type == EMaterialParameterType::Font)
		{
			Font = Cast<UFont>(LoadAsset(Body.Value));
			if (!Font || Body.FontPage < 0 || Body.FontPage >= Font->Textures.Num())
				throw std::runtime_error("font value must identify a Font asset and font_page must be a valid page");
		}
		else
		{
			if (Body.Value.Equals(TEXT("true"), ESearchCase::IgnoreCase) || Body.Value == TEXT("1")) bSwitch = true;
			else if (!Body.Value.Equals(TEXT("false"), ESearchCase::IgnoreCase) && Body.Value != TEXT("0"))
				throw std::runtime_error("static_switch value must be true or false");
		}
		if (!Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetMaterialInstanceParameter", "Set Material Instance Parameter"));
			Instance->Modify();
			if (Type == EMaterialParameterType::Scalar) Instance->SetScalarParameterValueEditorOnly(Info, Scalar);
			else if (Type == EMaterialParameterType::Vector) Instance->SetVectorParameterValueEditorOnly(Info, Color);
			else if (Type == EMaterialParameterType::Texture) Instance->SetTextureParameterValueEditorOnly(Info, Texture);
			else if (Type == EMaterialParameterType::RuntimeVirtualTexture) Instance->SetRuntimeVirtualTextureParameterValueEditorOnly(Info, RuntimeTexture);
			else if (Type == EMaterialParameterType::Font) Instance->SetFontParameterValueEditorOnly(Info, Font, Body.FontPage);
			else Instance->SetStaticSwitchParameterValueEditorOnly(Info, bSwitch);
			Instance->PostEditChange();
			MarkAssetDirty(Instance);
			SaveIfRequested(Instance, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			Body.bDryRun ? TEXT("false") : TEXT("true"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			(!Body.bDryRun && Body.bSave) ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Patch("/material-instances/parent", [](const FHttpContext<FMaterialInstanceReq, FString>& C)
	{
		const FMaterialInstanceReq Body = C.RequestBody();
		UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(LoadAsset(Body.AssetPath));
		UMaterialInterface* Parent = Cast<UMaterialInterface>(LoadAsset(Body.ParentPath));
		if (!Instance || !Parent) throw std::runtime_error("Asset and parent must be material interfaces; asset must be a Material Instance Constant");
		if (Parent == Instance || (Cast<UMaterialInstance>(Parent) && Cast<UMaterialInstance>(Parent)->IsChildOf(Instance)))
			throw std::runtime_error("Parent assignment would create a material instance cycle");
		const bool bChanged = Instance->Parent != Parent;
		if (bChanged && !Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetMaterialInstanceParent", "Set Material Instance Parent"));
			Instance->Modify();
			UMaterialEditingLibrary::SetMaterialInstanceParent(Instance, Parent);
			Instance->PostEditChange();
			MarkAssetDirty(Instance);
			SaveIfRequested(Instance, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/material-instances/reset", [](const FHttpContext<FMaterialInstanceReq, FString>& C)
	{
		const FMaterialInstanceReq Body = C.RequestBody();
		UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(LoadAsset(Body.AssetPath));
		if (!Instance) throw std::runtime_error("Asset is not a Material Instance Constant");
		if (!Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "ResetMaterialInstance", "Reset Material Instance Overrides"));
			Instance->Modify();
			{
				FMaterialInstanceParameterUpdateContext UpdateContext(Instance, EMaterialInstanceClearParameterFlag::All);
			}
			Instance->PostEditChange();
			MarkAssetDirty(Instance);
			SaveIfRequested(Instance, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"dry_run\":%s,\"saved\":%s}"),
			Body.bDryRun ? TEXT("true") : TEXT("false"), !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/material-instances/validate", [](const FHttpContext<FMaterialInstanceReq, FString>& C)
	{
		const FMaterialInstanceReq Body = C.RequestBody();
		UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(LoadAsset(Body.AssetPath));
		if (!Instance) throw std::runtime_error("Asset is not a Material Instance Constant");
		TMap<EMaterialParameterType, TSet<FMaterialParameterInfo>> ParentParameters;
		const EMaterialParameterType Types[] = { EMaterialParameterType::Scalar, EMaterialParameterType::Vector,
			EMaterialParameterType::Texture, EMaterialParameterType::Font,
			EMaterialParameterType::RuntimeVirtualTexture, EMaterialParameterType::StaticSwitch };
		for (EMaterialParameterType Type : Types)
		{
			TMap<FMaterialParameterInfo, FMaterialParameterMetadata> Parameters;
			if (Instance->Parent) Instance->Parent->GetAllParametersOfType(Type, Parameters);
			TSet<FMaterialParameterInfo>& Names = ParentParameters.FindOrAdd(Type);
			for (const auto& Entry : Parameters) Names.Add(Entry.Key);
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Instance->GetPathName());
		Writer->WriteValue(TEXT("parent_path"), Instance->Parent ? Instance->Parent->GetPathName() : TEXT(""));
		Writer->WriteArrayStart(TEXT("orphaned_overrides"));
		int32 OrphanCount = 0;
		auto Check = [&](EMaterialParameterType Type, const FMaterialParameterInfo& Info)
		{
			if (ParentParameters.FindChecked(Type).Contains(Info)) return;
			++OrphanCount;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Info.Name.ToString());
			Writer->WriteValue(TEXT("type"), Type == EMaterialParameterType::StaticSwitch ? TEXT("static_switch") :
				Type == EMaterialParameterType::RuntimeVirtualTexture ? TEXT("runtime_virtual_texture") : *MaterialParameterTypeToString(Type).ToLower());
			Writer->WriteValue(TEXT("association"), Info.Association == LayerParameter ? TEXT("layer") : Info.Association == BlendParameter ? TEXT("blend") : TEXT("global"));
			Writer->WriteValue(TEXT("index"), Info.Index);
			Writer->WriteObjectEnd();
		};
		for (const FScalarParameterValue& P : Instance->ScalarParameterValues) Check(EMaterialParameterType::Scalar, P.ParameterInfo);
		for (const FVectorParameterValue& P : Instance->VectorParameterValues) Check(EMaterialParameterType::Vector, P.ParameterInfo);
		for (const FTextureParameterValue& P : Instance->TextureParameterValues) Check(EMaterialParameterType::Texture, P.ParameterInfo);
		for (const FFontParameterValue& P : Instance->FontParameterValues) Check(EMaterialParameterType::Font, P.ParameterInfo);
		for (const FRuntimeVirtualTextureParameterValue& P : Instance->RuntimeVirtualTextureParameterValues) Check(EMaterialParameterType::RuntimeVirtualTexture, P.ParameterInfo);
		for (const FStaticSwitchParameter& P : Instance->GetStaticParameters().StaticSwitchParameters)
			if (P.bOverride) Check(EMaterialParameterType::StaticSwitch, P.ParameterInfo);
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("valid"), Instance->Parent != nullptr && OrphanCount == 0);
		Writer->WriteValue(TEXT("orphaned_override_count"), OrphanCount);
		if (!Instance->Parent) Writer->WriteValue(TEXT("error"), TEXT("Material instance has no parent"));
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/animation-sequences/inspect", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")));
		if (!Sequence)
			throw std::runtime_error("Asset is not an Animation Sequence");
		const IAnimationDataModel* Model = Sequence->GetDataModel();
		TArray<FName> BoneTracks;
		if (Model) Model->GetBoneTrackNames(BoneTracks);
		const FFrameRate FrameRate = Model ? Model->GetFrameRate() : FFrameRate(0, 1);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
		Writer->WriteValue(TEXT("skeleton_path"), Sequence->GetSkeleton() ? Sequence->GetSkeleton()->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("play_length"), Sequence->GetPlayLength());
		Writer->WriteValue(TEXT("sampled_keys"), Sequence->GetNumberOfSampledKeys());
		Writer->WriteValue(TEXT("source_frames"), Model ? Model->GetNumberOfFrames() : 0);
		Writer->WriteValue(TEXT("source_keys"), Model ? Model->GetNumberOfKeys() : 0);
		Writer->WriteObjectStart(TEXT("frame_rate"));
		Writer->WriteValue(TEXT("numerator"), FrameRate.Numerator);
		Writer->WriteValue(TEXT("denominator"), FrameRate.Denominator);
		Writer->WriteObjectEnd();
		Writer->WriteValue(TEXT("bone_track_count"), BoneTracks.Num());
		Writer->WriteValue(TEXT("float_curve_count"), Model ? Model->GetCurveData().FloatCurves.Num() : 0);
		Writer->WriteValue(TEXT("transform_curve_count"), Model ? Model->GetCurveData().TransformCurves.Num() : 0);
		Writer->WriteValue(TEXT("attribute_count"), Model ? Model->GetAttributes().Num() : 0);
		Writer->WriteValue(TEXT("notify_count"), Sequence->Notifies.Num());
		Writer->WriteValue(TEXT("sync_marker_count"), Sequence->AuthoredSyncMarkers.Num());
		Writer->WriteValue(TEXT("bone_compression_path"), Sequence->BoneCompressionSettings ? Sequence->BoneCompressionSettings->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("curve_compression_path"), Sequence->CurveCompressionSettings ? Sequence->CurveCompressionSettings->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("root_motion_enabled"), Sequence->bEnableRootMotion);
		Writer->WriteValue(TEXT("dirty"), Sequence->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/level-sequences/inspect", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		const UMovieScene* ReadOnlyMovieScene = MovieScene;
		const FFrameRate Tick = MovieScene->GetTickResolution();
		const FFrameRate Display = MovieScene->GetDisplayRate();
		const TRange<FFrameNumber> Playback = MovieScene->GetPlaybackRange();
		const int32 Lower = Playback.HasLowerBound() ? Playback.GetLowerBoundValue().Value : 0;
		const int32 Upper = Playback.HasUpperBound() ? Playback.GetUpperBoundValue().Value : 0;
		return C.TextResponse(FString::Printf(TEXT("{\"asset_path\":\"%s\",\"binding_count\":%d,\"master_track_count\":%d,\"section_count\":%d,\"playback_lower\":%d,\"playback_upper\":%d,\"tick_resolution\":{\"numerator\":%d,\"denominator\":%d},\"display_rate\":{\"numerator\":%d,\"denominator\":%d},\"camera_cut_present\":%s}"),
			*Sequence->GetPathName(), ReadOnlyMovieScene->GetBindings().Num(), ReadOnlyMovieScene->GetTracks().Num(), ReadOnlyMovieScene->GetAllSections().Num(), Lower, Upper,
			Tick.Numerator, Tick.Denominator, Display.Numerator, Display.Denominator, MovieScene->GetCameraCutTrack() ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/level-sequences/create", [](const FHttpContext<FSequenceCreateReq, FString>& C)
	{
		return C.TextResponse(ClassUtils::CreateLevelSequence(C.RequestBody().AssetPath), TEXT("text/plain"));
	});

	App->Patch("/level-sequences/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		ApplyAssetProperties(MovieScene, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/level-sequences/bindings", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		const UMovieScene* ReadOnlyMovieScene = MovieScene;
		UWorld* EditorWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("bindings"));
		for (const FMovieSceneBinding& Binding : ReadOnlyMovieScene->GetBindings())
		{
			FMovieSceneSpawnable* Spawnable = MovieScene->FindSpawnable(Binding.GetObjectGuid());
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("guid"), Binding.GetObjectGuid().ToString());
			Writer->WriteValue(TEXT("name"), ReadOnlyMovieScene->GetObjectDisplayName(Binding.GetObjectGuid()).ToString());
			Writer->WriteValue(TEXT("binding_type"), Spawnable ? TEXT("spawnable") : TEXT("possessable"));
			Writer->WriteValue(TEXT("template_class"), Spawnable && Spawnable->GetObjectTemplate() ? Spawnable->GetObjectTemplate()->GetClass()->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("track_count"), Binding.GetTracks().Num());
			Writer->WriteArrayStart(TEXT("bound_object_paths"));
			if (EditorWorld)
			{
				TArray<UObject*, TInlineAllocator<1>> BoundObjects;
				Sequence->LocateBoundObjects(Binding.GetObjectGuid(), UE::UniversalObjectLocator::FResolveParams::SyncFind(EditorWorld), nullptr, BoundObjects);
				for (UObject* Object : BoundObjects)
					if (Object) Writer->WriteValue(Object->GetPathName());
			}
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/level-sequences/bindings", [](const FHttpContext<FCinematicBindingReq, FString>& C)
	{
		auto Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FGuid BindingGuid;
		int32 AffectedSections = 0;
		if (Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase))
		{
			BindingGuid = ParseCinematicBinding(MovieScene, Body.BindingGuid);
			const bool bSpawnable = MovieScene->FindSpawnable(BindingGuid) != nullptr;
			if (!bSpawnable && !MovieScene->FindPossessable(BindingGuid)) throw std::runtime_error("binding is neither possessable nor spawnable");
			for (int32 Index = 0; Index < MovieScene->GetPossessableCount(); ++Index)
				if (MovieScene->GetPossessable(Index).GetParent() == BindingGuid)
					throw std::runtime_error("remove child possessable bindings before removing this binding");
			for (UMovieSceneTrack* Track : MovieScene->FindBinding(BindingGuid)->GetTracks())
				if (Track) AffectedSections += Track->GetAllSections().Num();
			if (UMovieSceneCameraCutTrack* CameraTrack = Cast<UMovieSceneCameraCutTrack>(MovieScene->GetCameraCutTrack()))
				for (UMovieSceneSection* BaseSection : CameraTrack->GetAllSections())
					if (const UMovieSceneCameraCutSection* Cut = Cast<UMovieSceneCameraCutSection>(BaseSection))
						if (Cut->GetCameraBindingID().GetGuid() == BindingGuid)
							throw std::runtime_error("remove camera cuts referencing this binding before removing the binding");
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, -1, -1, AffectedSections), TEXT("application/json"));
			if (!Body.bConfirm) throw std::runtime_error("binding removal requires confirm=true");
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveSequenceBinding", "Remove Level Sequence Binding"));
			Sequence->Modify();
			MovieScene->Modify();
			if (bSpawnable)
			{
				if (!MovieScene->RemoveSpawnable(BindingGuid)) throw std::runtime_error("failed to remove spawnable binding");
			}
			else
			{
				Sequence->UnbindPossessableObjects(BindingGuid);
				if (!MovieScene->RemovePossessable(BindingGuid)) throw std::runtime_error("failed to remove possessable binding");
			}
		}
		else if (Body.Operation.Equals(TEXT("add_spawnable"), ESearchCase::IgnoreCase))
		{
			AActor* Actor = Body.ActorPath.IsEmpty() ? nullptr : FindPlacedEditorActor(Body.ActorPath);
			UClass* SpawnableClass = Body.ClassPath.IsEmpty() ? nullptr : LoadClass<AActor>(nullptr, *Body.ClassPath);
			if (!Actor && !SpawnableClass) throw std::runtime_error("class_path or actor_path is required to create a spawnable");
			if (!Body.ClassPath.IsEmpty() && !SpawnableClass) throw std::runtime_error("class_path must identify an Actor class");
			if (Actor && SpawnableClass && !Actor->IsA(SpawnableClass)) throw std::runtime_error("class_path does not match actor_path");
			if (Actor) SpawnableClass = Actor->GetClass();
			if (SpawnableClass->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists))
				throw std::runtime_error("spawnable class must be concrete and current");
			if (!Actor && Body.Name.IsEmpty()) throw std::runtime_error("name is required when creating a class-only spawnable");
			if (!Sequence->AllowsSpawnableObjects()) throw std::runtime_error("this Level Sequence does not allow spawnable objects");
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, -1, -1, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddSpawnableBinding", "Add Level Sequence Spawnable"));
			Sequence->Modify();
			MovieScene->Modify();
			const FString SpawnableName = Body.Name.IsEmpty() ? Actor->GetActorLabel() : Body.Name;
			UObject* TemplateSource = Actor ? static_cast<UObject*>(Actor) : SpawnableClass->GetDefaultObject();
			if (!TemplateSource) throw std::runtime_error("failed to resolve the spawnable template source");
			UObject* Template = Sequence->MakeSpawnableTemplateFromInstance(*TemplateSource, FName(*SpawnableName));
			if (!Template) throw std::runtime_error("failed to create the spawnable actor template");
			BindingGuid = MovieScene->AddSpawnable(SpawnableName, *Template);
			if (!BindingGuid.IsValid()) throw std::runtime_error("failed to add spawnable binding");
		}
		else if (Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase))
		{
			AActor* Actor = Body.ActorPath.IsEmpty() ? nullptr : FindPlacedEditorActor(Body.ActorPath);
			if (!Actor && (Body.Name.IsEmpty() || Body.ClassPath.IsEmpty()))
				throw std::runtime_error("name and class_path are required when actor_path is omitted");
			UClass* BindingClass = Body.ClassPath.IsEmpty() ? Actor->GetClass() : LoadClass<UObject>(nullptr, *Body.ClassPath);
			if (!BindingClass || (Actor && !Actor->IsA(BindingClass))) throw std::runtime_error("class_path is invalid or does not match actor_path");
			UWorld* ActorWorld = Actor ? Actor->GetWorld() : nullptr;
			if (Actor && (!Sequence->CanPossessObject(*Actor, ActorWorld) || Sequence->FindPossessableObjectId(*Actor, ActorWorld).IsValid()))
				throw std::runtime_error("actor_path cannot be possessed or is already bound to this sequence");
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, -1, -1, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddSequenceBinding", "Add Level Sequence Binding"));
			Sequence->Modify();
			MovieScene->Modify();
			BindingGuid = MovieScene->AddPossessable(Actor && Body.Name.IsEmpty() ? Actor->GetActorLabel() : Body.Name, BindingClass);
			if (!BindingGuid.IsValid()) throw std::runtime_error("failed to add possessable binding");
			if (Actor) Sequence->BindPossessableObject(BindingGuid, *Actor, ActorWorld);
		}
		else throw std::runtime_error("operation must be add, add_spawnable, or remove");
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, -1, -1, AffectedSections), TEXT("application/json"));
	});

	App->Get("/level-sequences/tracks", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		const UMovieScene* ReadOnlyMovieScene = MovieScene;
		FString Json = TEXT("{\"tracks\":[");
		bool bFirst = true;
		auto AppendTrack = [&Json, &bFirst](UMovieSceneTrack* Track, const FString& BindingId, int32 TrackIndex)
		{
			if (!Track) return;
			if (!bFirst) Json += TEXT(",");
			bFirst = false;
			Json += FString::Printf(TEXT("{\"class\":\"%s\",\"name\":\"%s\",\"binding_guid\":\"%s\",\"track_index\":%d,\"section_count\":%d}"), *Track->GetClass()->GetPathName(), *Track->GetDisplayName().ToString(), *BindingId, TrackIndex, Track->GetAllSections().Num());
		};
		for (int32 Index = 0; Index < MovieScene->GetTracks().Num(); ++Index) AppendTrack(MovieScene->GetTracks()[Index], TEXT(""), Index);
		for (const FMovieSceneBinding& Binding : ReadOnlyMovieScene->GetBindings())
			for (int32 Index = 0; Index < Binding.GetTracks().Num(); ++Index) AppendTrack(Binding.GetTracks()[Index], Binding.GetObjectGuid().ToString(), Index);
		Json += TEXT("]}");
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/level-sequences/tracks", [](const FHttpContext<FCinematicTrackReq, FString>& C)
	{
		const FCinematicTrackReq Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FGuid BindingGuid;
		TArray<UMovieSceneTrack*> Tracks = CinematicTracks(MovieScene, Body.BindingGuid, BindingGuid);
		if (Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase))
		{
			UClass* TrackClass = CinematicTrackClass(Body.TrackClass, BindingGuid.IsValid());
			UEnum* PropertyEnum = nullptr;
			UClass* PropertyObjectClass = nullptr;
			const bool bNamedProperty = TrackClass == UMovieSceneFloatTrack::StaticClass() || TrackClass == UMovieSceneByteTrack::StaticClass()
				|| TrackClass == UMovieSceneIntegerTrack::StaticClass() || TrackClass == UMovieSceneObjectPropertyTrack::StaticClass();
			if (bNamedProperty)
			{
				if (Body.PropertyName.IsEmpty() || Body.PropertyPath != Body.PropertyName)
					throw std::runtime_error("property tracks require a top-level property_name and matching property_path");
				const FMovieScenePossessable* Possessable = MovieScene->FindPossessable(BindingGuid);
				const UClass* BoundClass = Possessable ? Possessable->GetPossessedObjectClass() : nullptr;
				const FProperty* Property = BoundClass ? FindFProperty<FProperty>(BoundClass, FName(*Body.PropertyName)) : nullptr;
				if (TrackClass == UMovieSceneFloatTrack::StaticClass() && !CastField<FFloatProperty>(Property))
					throw std::runtime_error("float_property must name a float property on the possessable class");
				if (TrackClass == UMovieSceneByteTrack::StaticClass())
				{
					if (const FByteProperty* Byte = CastField<FByteProperty>(Property)) PropertyEnum = Byte->Enum;
					else if (const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property); EnumProperty && CastField<FByteProperty>(EnumProperty->GetUnderlyingProperty())) PropertyEnum = EnumProperty->GetEnum();
					else throw std::runtime_error("byte_property must name a uint8 or byte-backed enum property on the possessable class");
				}
				if (TrackClass == UMovieSceneIntegerTrack::StaticClass() && !CastField<FIntProperty>(Property))
					throw std::runtime_error("integer_property must name an int32 property on the possessable class");
				if (TrackClass == UMovieSceneObjectPropertyTrack::StaticClass())
				{
					const FObjectPropertyBase* Object = CastField<FObjectPropertyBase>(Property);
					if (!Object || CastField<FClassProperty>(Property) || CastField<FSoftClassProperty>(Property)) throw std::runtime_error("object_property must name an object reference property on the possessable class");
					PropertyObjectClass = Object->PropertyClass;
				}
			}
			if (TrackClass == UMovieSceneSkeletalAnimationTrack::StaticClass())
			{
				const FMovieScenePossessable* Possessable = MovieScene->FindPossessable(BindingGuid);
				const UClass* BoundClass = Possessable ? Possessable->GetPossessedObjectClass() : nullptr;
				if (!BoundClass || (!BoundClass->IsChildOf(ASkeletalMeshActor::StaticClass())
					&& !BoundClass->IsChildOf(USkeletalMeshComponent::StaticClass())))
					throw std::runtime_error("skeletal_animation requires a SkeletalMeshActor or SkeletalMeshComponent possessable");
			}
			for (UMovieSceneTrack* Existing : Tracks)
				if (Existing && Existing->GetClass() == TrackClass)
					throw std::runtime_error("a track of this class already exists in the selected scope");
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Tracks.Num(), -1, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddSequenceTrack", "Add Level Sequence Track"));
			MovieScene->Modify();
			UMovieSceneTrack* Track = BindingGuid.IsValid() ? MovieScene->AddTrack(TrackClass, BindingGuid) : MovieScene->AddTrack(TrackClass);
			if (!Track) throw std::runtime_error("failed to add Level Sequence track");
			if (UMovieScenePropertyTrack* PropertyTrack = bNamedProperty ? Cast<UMovieScenePropertyTrack>(Track) : nullptr)
			{
				PropertyTrack->SetPropertyNameAndPath(FName(*Body.PropertyName), Body.PropertyPath);
				if (UMovieSceneByteTrack* ByteTrack = Cast<UMovieSceneByteTrack>(Track)) ByteTrack->SetEnum(PropertyEnum);
				if (UMovieSceneObjectPropertyTrack* ObjectTrack = Cast<UMovieSceneObjectPropertyTrack>(Track)) ObjectTrack->PropertyClass = PropertyObjectClass;
			}
			Tracks = CinematicTracks(MovieScene, Body.BindingGuid, BindingGuid);
			const int32 NewIndex = Tracks.IndexOfByKey(Track);
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
			return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, NewIndex, -1, 0), TEXT("application/json"));
		}
		if (!Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be add or remove");
		if (!Tracks.IsValidIndex(Body.TrackIndex) || !Tracks[Body.TrackIndex]) throw std::runtime_error("track_index is invalid for the selected binding");
		UMovieSceneTrack* Track = Tracks[Body.TrackIndex];
		if (Track->GetClass() != UMovieScene3DTransformTrack::StaticClass() && Track->GetClass() != UMovieSceneVisibilityTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneFloatTrack::StaticClass() && Track->GetClass() != UMovieSceneFadeTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneAudioTrack::StaticClass() && Track->GetClass() != UMovieSceneSkeletalAnimationTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneByteTrack::StaticClass() && Track->GetClass() != UMovieSceneIntegerTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneObjectPropertyTrack::StaticClass() && Track->GetClass() != UMovieSceneEventTrack::StaticClass())
			throw std::runtime_error("this track type requires its dedicated editing route");
		const int32 AffectedSections = Track->GetAllSections().Num();
		if (Body.bDryRun)
			return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, -1, AffectedSections), TEXT("application/json"));
		if (!Body.bConfirm) throw std::runtime_error("track removal requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveSequenceTrack", "Remove Level Sequence Track"));
		MovieScene->Modify();
		if (!MovieScene->RemoveTrack(*Track)) throw std::runtime_error("failed to remove Level Sequence track");
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, Body.TrackIndex, -1, AffectedSections), TEXT("application/json"));
	});

	App->Get("/level-sequences/sections", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FString Json = TEXT("{\"sections\":[");
		bool bFirst = true;
		auto AppendSection = [&Json, &bFirst](UMovieSceneSection* Section, UMovieSceneTrack* Track, const FString& BindingId, int32 TrackIndex, int32 SectionIndex)
		{
			if (!Section) return;
			if (!bFirst) Json += TEXT(",");
			bFirst = false;
			const TRange<FFrameNumber> Range = Section->GetRange();
			const int32 Lower = Range.HasLowerBound() ? Range.GetLowerBoundValue().Value : 0;
			const int32 Upper = Range.HasUpperBound() ? Range.GetUpperBoundValue().Value : 0;
			UObject* SourceAsset = nullptr;
			FString AudioSettingsJson = TEXT("null");
			if (const UMovieSceneAudioSection* AudioSection = Cast<UMovieSceneAudioSection>(Section))
			{
				SourceAsset = AudioSection->GetSound();
				FString SettingsJson;
				TSharedRef<TJsonWriter<>> SettingsWriter = TJsonWriterFactory<>::Create(&SettingsJson);
				SettingsWriter->WriteObjectStart();
				SettingsWriter->WriteValue(TEXT("start_offset"), AudioSection->GetStartOffset().Value);
				SettingsWriter->WriteValue(TEXT("looping"), AudioSection->GetLooping());
				SettingsWriter->WriteValue(TEXT("suppress_subtitles"), AudioSection->GetSuppressSubtitles());
				SettingsWriter->WriteValue(TEXT("override_attenuation"), AudioSection->GetOverrideAttenuation());
				SettingsWriter->WriteValue(TEXT("attenuation_path"), AudioSection->GetAttenuationSettings()
					? AudioSection->GetAttenuationSettings()->GetPathName() : TEXT(""));
				SettingsWriter->WriteObjectEnd();
				SettingsWriter->Close();
				AudioSettingsJson = MoveTemp(SettingsJson);
			}
			FString AnimationSettingsJson = TEXT("null");
			if (const UMovieSceneSkeletalAnimationSection* AnimationSection = Cast<UMovieSceneSkeletalAnimationSection>(Section))
			{
				SourceAsset = AnimationSection->GetAnimation();
				const FMovieSceneSkeletalAnimationParams& Params = AnimationSection->Params;
				FString SettingsJson;
				TSharedRef<TJsonWriter<>> SettingsWriter = TJsonWriterFactory<>::Create(&SettingsJson);
				SettingsWriter->WriteObjectStart();
				SettingsWriter->WriteValue(TEXT("play_rate_type"), StaticEnum<EMovieSceneTimeWarpType>()->GetNameStringByValue(static_cast<int64>(Params.PlayRate.GetType())));
				if (Params.PlayRate.GetType() == EMovieSceneTimeWarpType::FixedPlayRate)
					SettingsWriter->WriteValue(TEXT("play_rate"), Params.PlayRate.AsFixedPlayRate());
				SettingsWriter->WriteValue(TEXT("reverse"), static_cast<bool>(Params.bReverse));
				SettingsWriter->WriteValue(TEXT("slot_name"), Params.SlotName.ToString());
				SettingsWriter->WriteValue(TEXT("skip_anim_notifiers"), Params.bSkipAnimNotifiers);
				SettingsWriter->WriteValue(TEXT("force_custom_mode"), Params.bForceCustomMode);
				SettingsWriter->WriteValue(TEXT("first_loop_start_offset"), Params.FirstLoopStartFrameOffset.Value);
				SettingsWriter->WriteValue(TEXT("start_offset"), Params.StartFrameOffset.Value);
				SettingsWriter->WriteValue(TEXT("end_offset"), Params.EndFrameOffset.Value);
				SettingsWriter->WriteObjectEnd();
				SettingsWriter->Close();
				AnimationSettingsJson = MoveTemp(SettingsJson);
			}
			Json += FString::Printf(TEXT("{\"class\":\"%s\",\"track_class\":\"%s\",\"binding_guid\":\"%s\",\"track_index\":%d,\"section_index\":%d,\"row\":%d,\"lower\":%d,\"upper\":%d,\"channel_count\":%d,\"source_asset_path\":\"%s\",\"animation_settings\":%s,\"audio_settings\":%s}"),
				*Section->GetClass()->GetPathName(), Track ? *Track->GetClass()->GetPathName() : TEXT(""), *BindingId, TrackIndex, SectionIndex, Section->GetRowIndex(), Lower, Upper, Section->GetChannelProxy().NumChannels(),
				SourceAsset ? *SourceAsset->GetPathName() : TEXT(""), *AnimationSettingsJson, *AudioSettingsJson);
		};
		for (int32 TrackIndex = 0; TrackIndex < MovieScene->GetTracks().Num(); ++TrackIndex)
			if (UMovieSceneTrack* Track = MovieScene->GetTracks()[TrackIndex])
				for (int32 SectionIndex = 0; SectionIndex < Track->GetAllSections().Num(); ++SectionIndex)
					AppendSection(Track->GetAllSections()[SectionIndex], Track, TEXT(""), TrackIndex, SectionIndex);
		const UMovieScene* ReadOnlyMovieScene = MovieScene;
		for (const FMovieSceneBinding& Binding : ReadOnlyMovieScene->GetBindings())
			for (int32 TrackIndex = 0; TrackIndex < Binding.GetTracks().Num(); ++TrackIndex)
				if (UMovieSceneTrack* Track = Binding.GetTracks()[TrackIndex])
					for (int32 SectionIndex = 0; SectionIndex < Track->GetAllSections().Num(); ++SectionIndex)
						AppendSection(Track->GetAllSections()[SectionIndex], Track, Binding.GetObjectGuid().ToString(), TrackIndex, SectionIndex);
		Json += TEXT("]}");
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/level-sequences/sections", [](const FHttpContext<FCinematicTrackReq, FString>& C)
	{
		const FCinematicTrackReq Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FGuid BindingGuid;
		const TArray<UMovieSceneTrack*> Tracks = CinematicTracks(MovieScene, Body.BindingGuid, BindingGuid);
		if (!Tracks.IsValidIndex(Body.TrackIndex) || !Tracks[Body.TrackIndex]) throw std::runtime_error("track_index is invalid for the selected binding");
		UMovieSceneTrack* Track = Tracks[Body.TrackIndex];
		if (Track->GetClass() != UMovieScene3DTransformTrack::StaticClass() && Track->GetClass() != UMovieSceneVisibilityTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneFloatTrack::StaticClass() && Track->GetClass() != UMovieSceneFadeTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneAudioTrack::StaticClass() && Track->GetClass() != UMovieSceneSkeletalAnimationTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneByteTrack::StaticClass() && Track->GetClass() != UMovieSceneIntegerTrack::StaticClass()
			&& Track->GetClass() != UMovieSceneObjectPropertyTrack::StaticClass() && Track->GetClass() != UMovieSceneEventTrack::StaticClass())
			throw std::runtime_error("section editing for this track type is not supported");
		if (Body.Operation.Equals(TEXT("set_audio"), ESearchCase::IgnoreCase))
		{
			if (Track->GetClass() != UMovieSceneAudioTrack::StaticClass())
				throw std::runtime_error("set_audio requires an audio track");
			if (!Track->GetAllSections().IsValidIndex(Body.SectionIndex))
				throw std::runtime_error("section_index is invalid for the selected track");
			UMovieSceneAudioSection* AudioSection = Cast<UMovieSceneAudioSection>(Track->GetAllSections()[Body.SectionIndex]);
			USoundBase* Sound = AudioSection ? AudioSection->GetSound() : nullptr;
			if (!AudioSection || !Sound) throw std::runtime_error("section_index does not identify an audio section with a sound");
			const bool bAnySetting = Body.bSetAudioStartOffset || Body.bSetAudioLooping
				|| Body.bSetAudioSuppressSubtitles || Body.bSetAudioOverrideAttenuation
				|| Body.bSetAudioAttenuationSettings;
			if (!bAnySetting) throw std::runtime_error("set_audio requires at least one audio setting");
			if (Body.bSetAudioStartOffset)
			{
				if (Body.AudioStartOffset < 0) throw std::runtime_error("audio_start_offset must be a nonnegative tick-resolution frame");
				const double DurationInFrames = Sound->GetDuration() * MovieScene->GetTickResolution().AsDecimal();
				if (!FMath::IsFinite(DurationInFrames) || DurationInFrames <= 0.0 || Body.AudioStartOffset >= DurationInFrames)
					throw std::runtime_error("audio_start_offset must be inside the finite sound duration");
			}
			USoundAttenuation* Attenuation = AudioSection->GetAttenuationSettings();
			if (Body.bSetAudioAttenuationSettings)
			{
				Attenuation = Body.AudioAttenuationPath.IsEmpty()
					? nullptr : Cast<USoundAttenuation>(LoadAsset(Body.AudioAttenuationPath));
				if (!Body.AudioAttenuationPath.IsEmpty() && !Attenuation)
					throw std::runtime_error("audio_attenuation_path must reference a Sound Attenuation asset");
			}
			const int32 NewStartOffset = Body.bSetAudioStartOffset ? Body.AudioStartOffset : AudioSection->GetStartOffset().Value;
			const bool bChanged = (Body.bSetAudioStartOffset && AudioSection->GetStartOffset().Value != NewStartOffset)
				|| (Body.bSetAudioLooping && AudioSection->GetLooping() != Body.bAudioLooping)
				|| (Body.bSetAudioSuppressSubtitles && AudioSection->GetSuppressSubtitles() != Body.bAudioSuppressSubtitles)
				|| (Body.bSetAudioOverrideAttenuation && AudioSection->GetOverrideAttenuation() != Body.bAudioOverrideAttenuation)
				|| (Body.bSetAudioAttenuationSettings && AudioSection->GetAttenuationSettings() != Attenuation);
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0), TEXT("application/json"));
			if (!bChanged)
				return C.TextResponse(CinematicActionJson(false, false, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditAudioSection", "Edit Audio Section"));
			AudioSection->Modify();
			if (Body.bSetAudioStartOffset) AudioSection->SetStartOffset(FFrameNumber(NewStartOffset));
			if (Body.bSetAudioLooping) AudioSection->SetLooping(Body.bAudioLooping);
			if (Body.bSetAudioSuppressSubtitles) AudioSection->SetSuppressSubtitles(Body.bAudioSuppressSubtitles);
			if (Body.bSetAudioOverrideAttenuation) AudioSection->SetOverrideAttenuation(Body.bAudioOverrideAttenuation);
			if (Body.bSetAudioAttenuationSettings) AudioSection->SetAttenuationSettings(Attenuation);
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
			return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0), TEXT("application/json"));
		}
		if (Body.Operation.Equals(TEXT("set_animation"), ESearchCase::IgnoreCase))
		{
			if (Track->GetClass() != UMovieSceneSkeletalAnimationTrack::StaticClass())
				throw std::runtime_error("set_animation requires a skeletal-animation track");
			if (!Track->GetAllSections().IsValidIndex(Body.SectionIndex))
				throw std::runtime_error("section_index is invalid for the selected track");
			UMovieSceneSkeletalAnimationSection* AnimationSection = Cast<UMovieSceneSkeletalAnimationSection>(Track->GetAllSections()[Body.SectionIndex]);
			if (!AnimationSection || !AnimationSection->Params.Animation)
				throw std::runtime_error("section_index does not identify an animation section with an animation asset");
			const bool bAnySetting = Body.bSetAnimationPlayRate || Body.bSetAnimationReverse
				|| Body.bSetAnimationSlotName || Body.bSetAnimationSkipNotifiers
				|| Body.bSetAnimationForceCustomMode || Body.bSetAnimationFirstLoopStartOffset
				|| Body.bSetAnimationStartOffset || Body.bSetAnimationEndOffset;
			if (!bAnySetting) throw std::runtime_error("set_animation requires at least one animation setting");
			const FMovieSceneSkeletalAnimationParams& Current = AnimationSection->Params;
			if (Body.bSetAnimationPlayRate && (!FMath::IsFinite(Body.AnimationPlayRate) || Body.AnimationPlayRate <= 0.0))
				throw std::runtime_error("animation_play_rate must be finite and positive");
		const int32 NewFirstLoopOffset = Body.bSetAnimationFirstLoopStartOffset
				? Body.AnimationFirstLoopStartOffset : Current.FirstLoopStartFrameOffset.Value;
			const int32 NewStartOffset = Body.bSetAnimationStartOffset
				? Body.AnimationStartOffset : Current.StartFrameOffset.Value;
			const int32 NewEndOffset = Body.bSetAnimationEndOffset
				? Body.AnimationEndOffset : Current.EndFrameOffset.Value;
			if ((Body.bSetAnimationFirstLoopStartOffset && Body.AnimationFirstLoopStartOffset < 0)
				|| (Body.bSetAnimationStartOffset && Body.AnimationStartOffset < 0)
				|| (Body.bSetAnimationEndOffset && Body.AnimationEndOffset < 0))
				throw std::runtime_error("animation frame offsets must be nonnegative tick-resolution frames");
			const int64 TotalOffset = static_cast<int64>(NewFirstLoopOffset) + NewStartOffset + NewEndOffset;
			const double ClipDurationFrames = AnimationSection->Params.Animation->GetPlayLength() * MovieScene->GetTickResolution().AsDecimal();
			if (TotalOffset > 0 && (!FMath::IsFinite(ClipDurationFrames) || TotalOffset >= ClipDurationFrames))
				throw std::runtime_error("animation frame offsets must leave at least one frame of the clip");
			const bool bChanged = (Body.bSetAnimationPlayRate
				&& (Current.PlayRate.GetType() != EMovieSceneTimeWarpType::FixedPlayRate
					|| !FMath::IsNearlyEqual(Current.PlayRate.AsFixedPlayRate(), Body.AnimationPlayRate)))
				|| (Body.bSetAnimationReverse && static_cast<bool>(Current.bReverse) != Body.bAnimationReverse)
				|| (Body.bSetAnimationSlotName && Current.SlotName != FName(*Body.AnimationSlotName))
				|| (Body.bSetAnimationSkipNotifiers && Current.bSkipAnimNotifiers != Body.bAnimationSkipNotifiers)
				|| (Body.bSetAnimationForceCustomMode && Current.bForceCustomMode != Body.bAnimationForceCustomMode)
				|| (Body.bSetAnimationFirstLoopStartOffset && Current.FirstLoopStartFrameOffset.Value != NewFirstLoopOffset)
				|| (Body.bSetAnimationStartOffset && Current.StartFrameOffset.Value != NewStartOffset)
				|| (Body.bSetAnimationEndOffset && Current.EndFrameOffset.Value != NewEndOffset);
			TOptional<FFrameNumber> AdjustedSectionEndFrame;
			if (Body.bSetAnimationPlayRate && bChanged
				&& Current.PlayRate.GetType() == EMovieSceneTimeWarpType::FixedPlayRate
				&& Body.AnimationPlayRate > KINDA_SMALL_NUMBER)
			{
				const TRange<FFrameNumber> CurrentRange = AnimationSection->GetRange();
				if (!CurrentRange.HasLowerBound() || !CurrentRange.HasUpperBound())
					throw std::runtime_error("changing animation_play_rate requires a bounded section range");
				const int32 CurrentDuration = UE::MovieScene::DiscreteSize(CurrentRange);
				const int64 NewDuration = FMath::FloorToInt64(static_cast<double>(CurrentDuration)
					* Current.PlayRate.AsFixedPlayRate() / Body.AnimationPlayRate);
				const int64 NewEndFrame = static_cast<int64>(AnimationSection->GetInclusiveStartFrame().Value) + NewDuration;
				if (NewDuration <= 0 || NewEndFrame > TNumericLimits<int32>::Max())
					throw std::runtime_error("animation_play_rate would create an invalid section duration");
				AdjustedSectionEndFrame = FFrameNumber(static_cast<int32>(NewEndFrame));
			}
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0), TEXT("application/json"));
			if (!bChanged)
				return C.TextResponse(CinematicActionJson(false, false, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditSkeletalAnimationSection", "Edit Skeletal Animation Section"));
			AnimationSection->Modify();
			FMovieSceneSkeletalAnimationParams& Params = AnimationSection->Params;
			if (Body.bSetAnimationPlayRate) Params.PlayRate = Body.AnimationPlayRate;
			if (AdjustedSectionEndFrame.IsSet()) AnimationSection->SetEndFrame(AdjustedSectionEndFrame.GetValue());
			if (Body.bSetAnimationReverse) Params.bReverse = Body.bAnimationReverse;
			if (Body.bSetAnimationSlotName) Params.SlotName = FName(*Body.AnimationSlotName);
			if (Body.bSetAnimationSkipNotifiers) Params.bSkipAnimNotifiers = Body.bAnimationSkipNotifiers;
			if (Body.bSetAnimationForceCustomMode) Params.bForceCustomMode = Body.bAnimationForceCustomMode;
			if (Body.bSetAnimationFirstLoopStartOffset) Params.FirstLoopStartFrameOffset = FFrameNumber(NewFirstLoopOffset);
			if (Body.bSetAnimationStartOffset) Params.StartFrameOffset = FFrameNumber(NewStartOffset);
			if (Body.bSetAnimationEndOffset) Params.EndFrameOffset = FFrameNumber(NewEndOffset);
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
			return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0), TEXT("application/json"));
		}
		if (Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase))
		{
			if (Body.EndFrame <= Body.Frame) throw std::runtime_error("end_frame must be greater than frame");
            const bool bEventTrack=Track->IsA<UMovieSceneEventTrack>();
            if (!Body.EventSectionType.IsEmpty() && (!bEventTrack || (!Body.EventSectionType.Equals(TEXT("trigger"),ESearchCase::IgnoreCase) && !Body.EventSectionType.Equals(TEXT("repeater"),ESearchCase::IgnoreCase)))) throw std::runtime_error("event_section_type requires event track and trigger/repeater");
            const bool bRepeater=bEventTrack && Body.EventSectionType.Equals(TEXT("repeater"),ESearchCase::IgnoreCase);
            // UMovieSceneEventTrack::SupportsType only names the legacy UMovieSceneEventSection; the native event track editor creates repeaters directly.
			if (Body.RowIndex < 0 || (Body.RowIndex > 0 && !Track->SupportsMultipleRows())) throw std::runtime_error("row_index is invalid for this track");
			USoundBase* Sound = nullptr;
			UAnimSequenceBase* Animation = nullptr;
			if (Track->IsA<UMovieSceneAudioTrack>())
			{
				Sound = Cast<USoundBase>(LoadAsset(Body.SourceAssetPath));
				if (!Sound) throw std::runtime_error("source_asset_path must reference a Sound asset");
			}
			if (Track->IsA<UMovieSceneSkeletalAnimationTrack>())
			{
				Animation = Cast<UAnimSequenceBase>(LoadAsset(Body.SourceAssetPath));
				if (!Animation || !Animation->GetSkeleton()) throw std::runtime_error("source_asset_path must reference an animation with a Skeleton");
				USkeletalMesh* TargetMesh = Cast<USkeletalMesh>(LoadAsset(Body.TargetSkeletalMeshPath));
				if (!TargetMesh || !Animation->GetSkeleton()->IsCompatibleMesh(TargetMesh))
					throw std::runtime_error("target_skeletal_mesh_path must reference a Skeletal Mesh compatible with the animation Skeleton");
			}
			const int32 NewIndex = Track->GetAllSections().Num();
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, NewIndex, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddSequenceSection", "Add Level Sequence Section"));
			Track->Modify();
			UMovieSceneSection* Section = Sound ? CastChecked<UMovieSceneAudioTrack>(Track)->AddNewSoundOnRow(Sound, FFrameNumber(Body.Frame), Body.RowIndex)
				: Animation ? CastChecked<UMovieSceneSkeletalAnimationTrack>(Track)->AddNewAnimationOnRow(FFrameNumber(Body.Frame), Animation, Body.RowIndex)
				: bRepeater ? NewObject<UMovieSceneEventRepeaterSection>(Track,NAME_None,RF_Transactional) : Track->CreateNewSection();
			if (!Section) throw std::runtime_error("failed to create section for this track");
			Section->Modify();
			Section->SetRange(TRange<FFrameNumber>(FFrameNumber(Body.Frame), FFrameNumber(Body.EndFrame)));
			Section->SetRowIndex(Body.RowIndex);
			if (!Sound && !Animation) Track->AddSection(*Section);
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
			return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, Body.TrackIndex, Track->GetAllSections().IndexOfByKey(Section), 0), TEXT("application/json"));
		}
		if (!Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be add or remove");
		if (!Track->GetAllSections().IsValidIndex(Body.SectionIndex) || !Track->GetAllSections()[Body.SectionIndex])
			throw std::runtime_error("section_index is invalid for this track");
		if (Body.bDryRun)
			return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, Body.SectionIndex, 1), TEXT("application/json"));
		if (!Body.bConfirm) throw std::runtime_error("section removal requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveSequenceSection", "Remove Level Sequence Section"));
		Track->Modify();
		Track->RemoveSection(*Track->GetAllSections()[Body.SectionIndex]);
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, Body.TrackIndex, Body.SectionIndex, 1), TEXT("application/json"));
	});

	App->Get("/level-sequences/keys", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		if (C.Query("track_index").IsEmpty() || C.Query("section_index").IsEmpty())
			throw std::runtime_error("track_index and section_index are required");
		FGuid BindingGuid;
		const TArray<UMovieSceneTrack*> Tracks = CinematicTracks(MovieScene, C.Query("binding_guid"), BindingGuid);
		const int32 TrackIndex = FCString::Atoi(*C.Query("track_index"));
		const int32 SectionIndex = FCString::Atoi(*C.Query("section_index"));
		if (!Tracks.IsValidIndex(TrackIndex) || !Tracks[TrackIndex] || !Tracks[TrackIndex]->GetAllSections().IsValidIndex(SectionIndex))
			throw std::runtime_error("track_index or section_index is invalid");
		UMovieSceneTrack* Track = Tracks[TrackIndex];
		UMovieSceneSection* Section = Track->GetAllSections()[SectionIndex];
		if (!Section) throw std::runtime_error("section_index is invalid");
		TArray<FString> Keys;
		if (Track->IsA<UMovieSceneFloatTrack>() || Track->IsA<UMovieSceneFadeTrack>()
			|| Track->IsA<UMovieSceneAudioTrack>() || Track->IsA<UMovieSceneSkeletalAnimationTrack>())
		{
			int32 ChannelIndex = 0;
			for (FMovieSceneFloatChannel* Channel : Section->GetChannelProxy().GetChannels<FMovieSceneFloatChannel>())
			{
				const FMovieSceneFloatChannel* ReadOnlyChannel = Channel;
				const auto Data = ReadOnlyChannel->GetData();
				for (int32 KeyIndex = 0; KeyIndex < Data.GetTimes().Num(); ++KeyIndex)
					Keys.Add(FString::Printf(TEXT("{\"channel_type\":\"float\",\"channel_index\":%d,\"key_index\":%d,\"frame\":%d,\"value\":%s}"),
						ChannelIndex, KeyIndex, Data.GetTimes()[KeyIndex].Value, *FString::SanitizeFloat(Data.GetValues()[KeyIndex].Value)));
				++ChannelIndex;
			}
		}
		else if (Track->IsA<UMovieScene3DTransformTrack>())
		{
			int32 ChannelIndex = 0;
			for (FMovieSceneDoubleChannel* Channel : Section->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>())
			{
				const FMovieSceneDoubleChannel* ReadOnlyChannel = Channel;
				const auto Data = ReadOnlyChannel->GetData();
				for (int32 KeyIndex = 0; KeyIndex < Data.GetTimes().Num(); ++KeyIndex)
					Keys.Add(FString::Printf(TEXT("{\"channel_type\":\"double\",\"channel_index\":%d,\"key_index\":%d,\"frame\":%d,\"value\":%s}"),
						ChannelIndex, KeyIndex, Data.GetTimes()[KeyIndex].Value, *FString::SanitizeFloat(Data.GetValues()[KeyIndex].Value)));
				++ChannelIndex;
			}
		}
		else if (Track->IsA<UMovieSceneVisibilityTrack>())
		{
			int32 ChannelIndex = 0;
			for (FMovieSceneBoolChannel* Channel : Section->GetChannelProxy().GetChannels<FMovieSceneBoolChannel>())
			{
				const FMovieSceneBoolChannel* ReadOnlyChannel = Channel;
				const auto Data = ReadOnlyChannel->GetData();
				for (int32 KeyIndex = 0; KeyIndex < Data.GetTimes().Num(); ++KeyIndex)
					Keys.Add(FString::Printf(TEXT("{\"channel_type\":\"bool\",\"channel_index\":%d,\"key_index\":%d,\"frame\":%d,\"value\":%s}"),
						ChannelIndex, KeyIndex, Data.GetTimes()[KeyIndex].Value, Data.GetValues()[KeyIndex] ? TEXT("true") : TEXT("false")));
				++ChannelIndex;
			}
		}
		else throw std::runtime_error("key inspection for this track type is not supported");
		return C.TextResponse(FString::Printf(TEXT("{\"keys\":[%s]}"), *FString::Join(Keys, TEXT(","))), TEXT("application/json"));
	});

	App->Post("/level-sequences/keys", [](const FHttpContext<FCinematicTrackReq, FString>& C)
	{
		const FCinematicTrackReq Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FGuid BindingGuid;
		const TArray<UMovieSceneTrack*> Tracks = CinematicTracks(MovieScene, Body.BindingGuid, BindingGuid);
		if (!Tracks.IsValidIndex(Body.TrackIndex) || !Tracks[Body.TrackIndex] || !Tracks[Body.TrackIndex]->GetAllSections().IsValidIndex(Body.SectionIndex))
			throw std::runtime_error("track_index or section_index is invalid");
		UMovieSceneTrack* Track = Tracks[Body.TrackIndex];
		UMovieSceneSection* Section = Track->GetAllSections()[Body.SectionIndex];
		if (!Section) throw std::runtime_error("section_index is invalid");
		const bool bSet = Body.Operation.Equals(TEXT("set"), ESearchCase::IgnoreCase);
		const bool bRemove = Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase);
		if (!bSet && !bRemove) throw std::runtime_error("operation must be set or remove");
		if (bSet && (!FMath::IsFinite(Body.Value) || !Section->GetRange().Contains(FFrameNumber(Body.Frame))))
			throw std::runtime_error("value must be finite and frame must be inside the section range");
		if (bSet && !Body.Interpolation.Equals(TEXT("auto"), ESearchCase::IgnoreCase)
			&& !Body.Interpolation.Equals(TEXT("linear"), ESearchCase::IgnoreCase)
			&& !Body.Interpolation.Equals(TEXT("constant"), ESearchCase::IgnoreCase))
			throw std::runtime_error("interpolation must be auto, linear, or constant");
		if (Body.ChannelIndex < 0) throw std::runtime_error("channel_index must be nonnegative");
		auto ApplyKey = [&](auto* Channel, auto NewValue) -> int32
		{
			auto Data = Channel->GetData();
			if (bRemove && (Body.KeyIndex < 0 || Body.KeyIndex >= Data.GetTimes().Num()))
				throw std::runtime_error("key_index is invalid");
			if (Body.bDryRun) return bSet ? Data.FindKey(FFrameNumber(Body.Frame)) : Body.KeyIndex;
			if (bRemove && !Body.bConfirm) throw std::runtime_error("key removal requires confirm=true");
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditSequenceKey", "Edit Level Sequence Key"));
			Section->Modify();
			if (bSet)
			{
				Data.UpdateOrAddKey(FFrameNumber(Body.Frame), NewValue);
				return Data.FindKey(FFrameNumber(Body.Frame));
			}
			Data.RemoveKey(Body.KeyIndex);
			return Body.KeyIndex;
		};
		int32 KeyIndex = -1;
		if (Track->IsA<UMovieSceneFloatTrack>() || Track->IsA<UMovieSceneFadeTrack>()
			|| Track->IsA<UMovieSceneAudioTrack>() || Track->IsA<UMovieSceneSkeletalAnimationTrack>())
		{
			const auto Channels = Section->GetChannelProxy().GetChannels<FMovieSceneFloatChannel>();
			if (Body.ChannelIndex >= Channels.Num()) throw std::runtime_error("channel_index is invalid for this float section");
			if (bSet && FMath::Abs(Body.Value) > static_cast<double>(TNumericLimits<float>::Max()))
				throw std::runtime_error("value is outside the supported float range");
			if (bSet && Track->IsA<UMovieSceneAudioTrack>() && Body.Value < 0.0)
				throw std::runtime_error("audio volume or pitch value must be nonnegative");
			if (bSet && Track->IsA<UMovieSceneSkeletalAnimationTrack>() && (Body.Value < 0.0 || Body.Value > 1.0))
				throw std::runtime_error("skeletal animation weight must be between 0 and 1");
			FMovieSceneFloatValue Value(static_cast<float>(Body.Value));
			Value.InterpMode = Body.Interpolation.Equals(TEXT("linear"), ESearchCase::IgnoreCase) ? RCIM_Linear
				: Body.Interpolation.Equals(TEXT("constant"), ESearchCase::IgnoreCase) ? RCIM_Constant : RCIM_Cubic;
			KeyIndex = ApplyKey(Channels[Body.ChannelIndex], Value);
		}
		else if (Track->IsA<UMovieScene3DTransformTrack>())
		{
			const auto Channels = Section->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
			if (Body.ChannelIndex >= Channels.Num()) throw std::runtime_error("channel_index is invalid for this transform section");
			FMovieSceneDoubleValue Value(Body.Value);
			Value.InterpMode = Body.Interpolation.Equals(TEXT("linear"), ESearchCase::IgnoreCase) ? RCIM_Linear
				: Body.Interpolation.Equals(TEXT("constant"), ESearchCase::IgnoreCase) ? RCIM_Constant : RCIM_Cubic;
			KeyIndex = ApplyKey(Channels[Body.ChannelIndex], Value);
		}
		else if (Track->IsA<UMovieSceneVisibilityTrack>())
		{
			const auto Channels = Section->GetChannelProxy().GetChannels<FMovieSceneBoolChannel>();
			if (Body.ChannelIndex >= Channels.Num()) throw std::runtime_error("channel_index is invalid for this visibility section");
			if (bSet && Body.Value != 0.0 && Body.Value != 1.0) throw std::runtime_error("visibility value must be 0 or 1");
			KeyIndex = ApplyKey(Channels[Body.ChannelIndex], Body.Value != 0.0);
		}
		else throw std::runtime_error("key editing for this track type is not supported");
		if (Body.bDryRun)
			return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0, KeyIndex), TEXT("application/json"));
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, BindingGuid, Body.TrackIndex, Body.SectionIndex, 0, KeyIndex), TEXT("application/json"));
	});

	App->Get("/cinematic/cameras", [](const FHttpContext<void, FString>& C)
	{
		const FCinematicCameraTarget Target = ResolveCinematicCamera(C.Query("actor_path"), C.Query("asset_path"), C.Query("binding_guid"));
		return C.TextResponse(CinematicCameraJson(Target, false, false, false), TEXT("application/json"));
	});

	App->Post("/cinematic/cameras", [](const FHttpContext<FCinematicCameraReq, FString>& C)
	{
		const FCinematicCameraReq Body = C.RequestBody();
		if (!Body.Operation.Equals(TEXT("create"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be create");
		if (!Body.ActorPath.IsEmpty() || !Body.AssetPath.IsEmpty() || !Body.BindingGuid.IsEmpty())
			throw std::runtime_error("create does not accept an existing camera target");
		if (!GEditor || !IsInGameThread()) throw std::runtime_error("camera creation requires the editor game thread");
		UWorld* World = GEditor->GetEditorWorldContext().World();
		if (!World) throw std::runtime_error("no current editor world is available");
		if (Body.Location.ContainsNaN() || Body.Rotation.ContainsNaN()) throw std::runtime_error("location and rotation must be finite");
		ACineCameraActor* DefaultCamera = GetMutableDefault<ACineCameraActor>();
		const FCinematicCameraSettings Settings = PrepareCinematicCameraSettings(DefaultCamera->GetCineCameraComponent(), Body);
		if (Body.bDryRun) return C.TextResponse(TEXT("{\"changed\":false,\"dry_run\":true,\"would_create\":true}"), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "CreateCinematicCamera", "Create Cinematic Camera"));
		FActorSpawnParameters SpawnParameters;
		SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		SpawnParameters.ObjectFlags |= RF_Transactional;
		ACineCameraActor* Actor = World->SpawnActor<ACineCameraActor>(Body.Location, Body.Rotation, SpawnParameters);
		if (!Actor || !Actor->GetCineCameraComponent()) throw std::runtime_error("failed to create CineCameraActor");
		Actor->Modify();
		Actor->GetCineCameraComponent()->Modify();
		if (!Body.Label.IsEmpty()) Actor->SetActorLabel(Body.Label);
		ApplyCinematicCameraSettings(Actor->GetCineCameraComponent(), Settings);
		Actor->GetLevel()->MarkPackageDirty();
		if (Body.bSave && !UEditorLoadingAndSavingUtils::SaveMap(World, World->GetOutermost()->GetName()))
			throw std::runtime_error("failed to save the editor map after camera creation");
		return C.TextResponse(CinematicCameraJson({Actor, nullptr, false}, true, false, Body.bSave), TEXT("application/json"));
	});

	App->Patch("/cinematic/cameras", [](const FHttpContext<FCinematicCameraReq, FString>& C)
	{
		const FCinematicCameraReq Body = C.RequestBody();
		if (!Body.Operation.Equals(TEXT("set"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be set");
		if (!IsInGameThread()) throw std::runtime_error("camera editing requires the editor game thread");
		const FCinematicCameraTarget Target = ResolveCinematicCamera(Body.ActorPath, Body.AssetPath, Body.BindingGuid);
		const bool bSettingsRequested = Body.FocalLength != -1.f || Body.Aperture != -1.f || Body.MinFocalLength != -1.f
			|| Body.MaxFocalLength != -1.f || Body.MinFStop != -1.f || Body.MaxFStop != -1.f
			|| Body.SensorWidth != -1.f || Body.SensorHeight != -1.f || Body.ManualFocusDistance != -1.f
			|| !Body.FocusMethod.IsEmpty() || !Body.FocusActorPath.IsEmpty();
		if (!bSettingsRequested && !Body.bSetTransform && Body.Label.IsEmpty()) throw std::runtime_error("no camera changes were requested");
		if (Target.bTemplate && (Body.bSetTransform || !Body.Label.IsEmpty()))
			throw std::runtime_error("transform and label editing require a placed CineCameraActor");
		if (Body.bSetTransform && (Body.Location.ContainsNaN() || Body.Rotation.ContainsNaN()))
			throw std::runtime_error("location and rotation must be finite");
		const FCinematicCameraSettings Settings = PrepareCinematicCameraSettings(Target.Actor->GetCineCameraComponent(), Body);
		if (Body.bDryRun) return C.TextResponse(CinematicCameraJson(Target, false, true, false), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditCinematicCamera", "Edit Cinematic Camera"));
		if (Target.bTemplate && Target.Sequence) Target.Sequence->Modify();
		Target.Actor->Modify();
		Target.Actor->GetCineCameraComponent()->Modify();
		if (Body.bSetTransform) Target.Actor->SetActorLocationAndRotation(Body.Location, Body.Rotation);
		if (!Body.Label.IsEmpty()) Target.Actor->SetActorLabel(Body.Label);
		if (bSettingsRequested) ApplyCinematicCameraSettings(Target.Actor->GetCineCameraComponent(), Settings);
		if (Target.bTemplate)
		{
			MarkAssetDirty(Target.Sequence);
			SaveIfRequested(Target.Sequence, Body.bSave);
		}
		else
		{
			UWorld* World = Target.Actor->GetWorld();
			if (!World) throw std::runtime_error("placed camera has no editor world");
			Target.Actor->GetLevel()->MarkPackageDirty();
			if (Body.bSave && !UEditorLoadingAndSavingUtils::SaveMap(World, World->GetOutermost()->GetName()))
				throw std::runtime_error("failed to save the editor map after camera editing");
		}
		return C.TextResponse(CinematicCameraJson(Target, true, false, Body.bSave), TEXT("application/json"));
	});

	auto GetCameraCuts = [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		UMovieSceneCameraCutTrack* CameraTrack = MovieScene ? Cast<UMovieSceneCameraCutTrack>(MovieScene->GetCameraCutTrack()) : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("camera_cuts"));
		if (CameraTrack) for (int32 Index = 0; Index < CameraTrack->GetAllSections().Num(); ++Index)
		{
			UMovieSceneCameraCutSection* Section = Cast<UMovieSceneCameraCutSection>(CameraTrack->GetAllSections()[Index]);
			if (!Section) continue;
			const TRange<FFrameNumber> Range = Section->GetRange();
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("section_index"), Index);
			Writer->WriteValue(TEXT("camera_binding_guid"), Section->GetCameraBindingID().GetGuid().ToString());
			Writer->WriteValue(TEXT("row"), Section->GetRowIndex());
			Writer->WriteValue(TEXT("lower"), Range.HasLowerBound() ? Range.GetLowerBoundValue().Value : 0);
			Writer->WriteValue(TEXT("upper"), Range.HasUpperBound() ? Range.GetUpperBoundValue().Value : 0);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	};
	App->Get("/level-sequences/camera-cuts", GetCameraCuts);
	App->Get("/cinematic/camera-cuts", GetCameraCuts);

	auto EditCameraCut = [](const FHttpContext<FCinematicSectionReq, FString>& C)
	{
		const FCinematicSectionReq Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		UMovieSceneCameraCutTrack* CameraTrack = Cast<UMovieSceneCameraCutTrack>(MovieScene->GetCameraCutTrack());
		if (Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase))
		{
			if (!CameraTrack || Body.SectionIndex < 0 || Body.SectionIndex >= CameraTrack->GetAllSections().Num()) throw std::runtime_error("camera cut section_index is invalid");
			if (Body.bDryRun) return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false,
				FGuid(), -1, Body.SectionIndex, 1), TEXT("application/json"));
			if (!Body.bConfirm) throw std::runtime_error("camera cut removal requires confirm=true");
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveCameraCut", "Remove Camera Cut"));
			MovieScene->Modify();
			CameraTrack->Modify();
			CameraTrack->RemoveSectionAt(Body.SectionIndex);
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
			return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave,
				FGuid(), -1, Body.SectionIndex, 1), TEXT("application/json"));
		}
		if (!Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be add or remove");
		FGuid CameraGuid;
		if (!FGuid::Parse(Body.CameraBindingGuid, CameraGuid) || !CameraGuid.IsValid() || !MovieScene->FindBinding(CameraGuid)
			|| !IsCameraBinding(MovieScene, CameraGuid)) throw std::runtime_error("camera_binding_guid must identify a camera actor or camera component binding");
		if (Body.Duration <= 0 || Body.Frame > MAX_int32 - Body.Duration) throw std::runtime_error("duration must be positive and its frame range must not overflow");
		const TRange<FFrameNumber> NewRange(FFrameNumber(Body.Frame), FFrameNumber(Body.Frame + Body.Duration));
		if (CameraTrack) for (UMovieSceneSection* Existing : CameraTrack->GetAllSections())
			if (Existing && Existing->GetRange().Overlaps(NewRange)) throw std::runtime_error("camera cut range overlaps an existing camera cut");
		const int32 NewIndex = CameraTrack ? CameraTrack->GetAllSections().Num() : 0;
		if (Body.bDryRun) return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false,
			CameraGuid, -1, NewIndex, 0), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddCameraCut", "Add Camera Cut"));
		MovieScene->Modify();
		if (!CameraTrack) CameraTrack = Cast<UMovieSceneCameraCutTrack>(MovieScene->AddCameraCutTrack(UMovieSceneCameraCutTrack::StaticClass()));
		if (!CameraTrack) throw std::runtime_error("failed to create camera cut track");
		CameraTrack->Modify();
		UMovieSceneCameraCutSection* Section = CameraTrack->AddNewCameraCut(FMovieSceneObjectBindingID(), FFrameNumber(Body.Frame));
		if (!Section) throw std::runtime_error("failed to create camera cut section");
		Section->SetCameraGuid(CameraGuid);
		Section->SetRange(NewRange);
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave,
			CameraGuid, -1, CameraTrack->GetAllSections().IndexOfByKey(Section), 0), TEXT("application/json"));
	};
	App->Post("/level-sequences/camera-cuts", EditCameraCut);
	App->Post("/cinematic/camera-cuts", EditCameraCut);

	App->Get("/level-sequences/subsequences", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FString Json = TEXT("{\"subsequences\":[");
		bool bFirst = true;
		for (UMovieSceneTrack* BaseTrack : MovieScene->GetTracks())
		{
			UMovieSceneSubTrack* SubTrack = Cast<UMovieSceneSubTrack>(BaseTrack);
			if (!SubTrack || SubTrack->GetClass() != UMovieSceneSubTrack::StaticClass()) continue;
			for (UMovieSceneSection* BaseSection : SubTrack->GetAllSections())
			{
				UMovieSceneSubSection* Section = Cast<UMovieSceneSubSection>(BaseSection);
				if (!Section) continue;
				if (!bFirst) Json += TEXT(",");
				bFirst = false;
				const TRange<FFrameNumber> Range = Section->GetRange();
				const int32 Lower = Range.HasLowerBound() ? Range.GetLowerBoundValue().Value : 0;
				const int32 Upper = Range.HasUpperBound() ? Range.GetUpperBoundValue().Value : 0;
				UMovieSceneSequence* SubSequence = Section->GetSequence();
				Json += FString::Printf(TEXT("{\"track_class\":\"%s\",\"sequence_path\":\"%s\",\"row\":%d,\"lower\":%d,\"upper\":%d}"), *SubTrack->GetClass()->GetPathName(), SubSequence ? *SubSequence->GetPathName() : TEXT(""), Section->GetRowIndex(), Lower, Upper);
			}
		}
		Json += TEXT("]}");
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/level-sequences/subsequences", [](const FHttpContext<FCinematicSectionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		// Exact class: cinematic shot tracks derive from UMovieSceneSubTrack and must not receive plain subsequences.
		UMovieSceneSubTrack* SubTrack = nullptr;
		for (UMovieSceneTrack* Track : MovieScene->GetTracks())
			if (Track && Track->GetClass() == UMovieSceneSubTrack::StaticClass()) { SubTrack = CastChecked<UMovieSceneSubTrack>(Track); break; }
		if (Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase))
		{
			if (!Body.bConfirm) throw std::runtime_error("subsequence removal requires confirm=true");
			if (!SubTrack || Body.SectionIndex < 0 || Body.SectionIndex >= SubTrack->GetAllSections().Num()) throw std::runtime_error("subsequence section_index is invalid");
			if (Body.bDryRun) return C.JsonResponse(FActionResponse {});
			MovieScene->Modify();
			SubTrack->RemoveSectionAt(Body.SectionIndex);
		}
		else
		{
			UMovieSceneSequence* NestedSequence = Cast<UMovieSceneSequence>(LoadAsset(Body.SequencePath));
			if (!NestedSequence) throw std::runtime_error("sequence_path must reference a Movie Scene sequence asset");
			if (Body.Duration <= 0 || Body.Frame > MAX_int32 - Body.Duration) throw std::runtime_error("duration must be positive and its frame range must not overflow");
			if (Body.RowIndex < 0) throw std::runtime_error("row_index must be nonnegative");
			if (WouldCreateSequenceCycle(Sequence, NestedSequence)) throw std::runtime_error("subsequence would create a cycle");
			if (Body.bDryRun) return C.JsonResponse(FActionResponse {});
			MovieScene->Modify();
			if (!SubTrack) SubTrack = MovieScene->AddTrack<UMovieSceneSubTrack>();
			if (!SubTrack) throw std::runtime_error("failed to create sub-sequence track");
			if (!SubTrack->AddSequenceOnRow(NestedSequence, FFrameNumber(Body.Frame), Body.Duration, Body.RowIndex)) throw std::runtime_error("failed to create sub-sequence section");
		}
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/cinematic/shots", [](const FHttpContext<void, FString>& C)
	{
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(C.Query("asset_path")));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("shots"));
		for (int32 TrackIndex = 0; TrackIndex < MovieScene->GetTracks().Num(); ++TrackIndex)
		{
			UMovieSceneCinematicShotTrack* ShotTrack = Cast<UMovieSceneCinematicShotTrack>(MovieScene->GetTracks()[TrackIndex]);
			if (!ShotTrack) continue;
			for (int32 SectionIndex = 0; SectionIndex < ShotTrack->GetAllSections().Num(); ++SectionIndex)
			{
				UMovieSceneCinematicShotSection* Shot = Cast<UMovieSceneCinematicShotSection>(ShotTrack->GetAllSections()[SectionIndex]);
				if (!Shot) continue;
				const TRange<FFrameNumber> Range = Shot->GetRange();
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("track_index"), TrackIndex);
				Writer->WriteValue(TEXT("section_index"), SectionIndex);
				Writer->WriteValue(TEXT("shot_name"), Shot->GetShotDisplayName());
				Writer->WriteValue(TEXT("sequence_path"), Shot->GetSequence() ? Shot->GetSequence()->GetPathName() : TEXT(""));
				Writer->WriteValue(TEXT("row"), Shot->GetRowIndex());
				Writer->WriteValue(TEXT("lower"), Range.HasLowerBound() ? Range.GetLowerBoundValue().Value : 0);
				Writer->WriteValue(TEXT("upper"), Range.HasUpperBound() ? Range.GetUpperBoundValue().Value : 0);
				Writer->WriteObjectEnd();
			}
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/cinematic/shots", [](const FHttpContext<FCinematicSectionReq, FString>& C)
	{
		const FCinematicSectionReq Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		UMovieSceneCinematicShotTrack* ShotTrack = Cast<UMovieSceneCinematicShotTrack>(MovieScene->FindTrack<UMovieSceneCinematicShotTrack>());
		const bool bAdd = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
		const bool bRemove = Body.Operation.Equals(TEXT("remove"), ESearchCase::IgnoreCase);
		const bool bRename = Body.Operation.Equals(TEXT("rename"), ESearchCase::IgnoreCase);
		if (!bAdd && !bRemove && !bRename) throw std::runtime_error("operation must be add, remove, or rename");
		UMovieSceneCinematicShotSection* Shot = nullptr;
		if (bAdd)
		{
			ULevelSequence* NestedSequence = Cast<ULevelSequence>(LoadAsset(Body.SequencePath));
			if (!NestedSequence) throw std::runtime_error("sequence_path must reference a Level Sequence");
			if (Body.Duration <= 0 || Body.Frame > MAX_int32 - Body.Duration) throw std::runtime_error("duration must be positive and its frame range must not overflow");
			if (Body.RowIndex < 0) throw std::runtime_error("row_index must be nonnegative");
			if (WouldCreateSequenceCycle(Sequence, NestedSequence)) throw std::runtime_error("shot would create a sequence cycle");
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, FGuid(),
					ShotTrack ? MovieScene->GetTracks().IndexOfByKey(ShotTrack) : MovieScene->GetTracks().Num(), ShotTrack ? ShotTrack->GetAllSections().Num() : 0, 0), TEXT("application/json"));
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddCinematicShot", "Add Cinematic Shot"));
			MovieScene->Modify();
			if (!ShotTrack) ShotTrack = MovieScene->AddTrack<UMovieSceneCinematicShotTrack>();
			if (!ShotTrack) throw std::runtime_error("failed to create cinematic shot track");
			ShotTrack->Modify();
			Shot = Cast<UMovieSceneCinematicShotSection>(ShotTrack->AddSequenceOnRow(NestedSequence, FFrameNumber(Body.Frame), Body.Duration, Body.RowIndex));
			if (!Shot) throw std::runtime_error("failed to create cinematic shot section");
			if (!Body.ShotName.IsEmpty()) Shot->SetShotDisplayName(Body.ShotName);
		}
		else
		{
			if (!ShotTrack || !ShotTrack->GetAllSections().IsValidIndex(Body.SectionIndex)) throw std::runtime_error("section_index is invalid for the shot track");
			Shot = Cast<UMovieSceneCinematicShotSection>(ShotTrack->GetAllSections()[Body.SectionIndex]);
			if (!Shot) throw std::runtime_error("section_index does not identify a cinematic shot");
			if (bRename && Body.ShotName.IsEmpty()) throw std::runtime_error("shot_name is required to rename a shot");
			if (Body.bDryRun)
				return C.TextResponse(CinematicActionJson(false, true, Sequence->GetOutermost()->IsDirty(), false, FGuid(),
					MovieScene->GetTracks().IndexOfByKey(ShotTrack), Body.SectionIndex, bRemove ? 1 : 0), TEXT("application/json"));
			if (bRemove && !Body.bConfirm) throw std::runtime_error("shot removal requires confirm=true");
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditCinematicShot", "Edit Cinematic Shot"));
			ShotTrack->Modify();
			if (bRemove) ShotTrack->RemoveSectionAt(Body.SectionIndex);
			else Shot->SetShotDisplayName(Body.ShotName);
		}
		MarkAssetDirty(Sequence);
		SaveIfRequested(Sequence, Body.bSave);
		return C.TextResponse(CinematicActionJson(true, false, Sequence->GetOutermost()->IsDirty(), Body.bSave, FGuid(),
			MovieScene->GetTracks().IndexOfByKey(ShotTrack), bAdd ? ShotTrack->GetAllSections().IndexOfByKey(Shot) : Body.SectionIndex, bRemove ? 1 : 0), TEXT("application/json"));
	});

	App->Post("/level-sequences/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		auto Body = C.RequestBody();
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		const UMovieScene* ReadOnlyMovieScene = MovieScene;
		const bool bValidRange = MovieScene->GetPlaybackRange().HasLowerBound() && MovieScene->GetPlaybackRange().HasUpperBound();
		return C.TextResponse(FString::Printf(TEXT("{\"valid\":%s,\"binding_count\":%d,\"track_count\":%d,\"reason\":\"%s\"}"), bValidRange ? TEXT("true") : TEXT("false"), ReadOnlyMovieScene->GetBindings().Num(), ReadOnlyMovieScene->GetTracks().Num(), bValidRange ? TEXT("") : TEXT("playback range is unbounded")), TEXT("application/json"));
	});

	App->Post("/level-sequences/evaluate", [](const FHttpContext<FSequencePlaybackReq, FString>& C)
	{
		const FSequencePlaybackReq Body = C.RequestBody();
		if (!IsInGameThread()) throw std::runtime_error("Level Sequence evaluation requires the editor game thread");
		ULevelSequence* Sequence = Cast<ULevelSequence>(LoadAsset(Body.AssetPath));
		UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
		if (!MovieScene) throw std::runtime_error("Asset is not a Level Sequence or has no Movie Scene");
		const UMovieScene* ReadOnlyMovieScene = MovieScene;
		if (ReadOnlyMovieScene->GetBindings().Num() != 1 || ReadOnlyMovieScene->GetTracks().Num() != 0 || MovieScene->GetCameraCutTrack())
			throw std::runtime_error("frame evaluation supports one actor binding and no master tracks or camera cuts");

		const FGuid BindingGuid = ParseCinematicBinding(MovieScene, Body.BindingGuid);
		if (MovieScene->FindSpawnable(BindingGuid)) throw std::runtime_error("frame evaluation requires a possessable actor binding");
		const FMovieScenePossessable* Possessable = MovieScene->FindPossessable(BindingGuid);
		const FMovieSceneBinding* Binding = MovieScene->FindBinding(BindingGuid);
		const UClass* PossessedClass = Possessable ? Possessable->GetPossessedObjectClass() : nullptr;
		if (!PossessedClass || !PossessedClass->IsChildOf(AActor::StaticClass()))
			throw std::runtime_error("frame evaluation requires a possessable actor class");
		if (!PossessedClass->HasAnyClassFlags(CLASS_Native)
			|| PossessedClass->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists))
			throw std::runtime_error("frame evaluation only instantiates concrete native actor classes in its isolated preview world");
		AActor* SourceActor = nullptr;
		FTransform SourceActorTransform = FTransform::Identity;
		if (!Body.ActorPath.IsEmpty())
		{
			SourceActor = FindPlacedEditorActor(Body.ActorPath);
			if (!SourceActor->IsA(PossessedClass)) throw std::runtime_error("actor_path class does not match the possessable binding");
			UWorld* EditorWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!EditorWorld) throw std::runtime_error("no current editor world is available to resolve actor_path");
			TArray<UObject*, TInlineAllocator<1>> SourceBoundObjects;
			Sequence->LocateBoundObjects(BindingGuid, UE::UniversalObjectLocator::FResolveParams::SyncFind(EditorWorld), nullptr, SourceBoundObjects);
			if (!SourceBoundObjects.Contains(SourceActor)) throw std::runtime_error("actor_path is not currently resolved by binding_guid");
			SourceActorTransform = SourceActor->GetActorTransform();
		}
		if (!Binding || Binding->GetTracks().Num() < 1 || Binding->GetTracks().Num() > 3)
			throw std::runtime_error("frame evaluation supports one transform track plus optional visibility and float-property tracks");

		UMovieScene3DTransformSection* TransformSection = nullptr;
		UMovieSceneSection* VisibilitySection = nullptr;
		UMovieSceneSection* FloatPropertySection = nullptr;
		UMovieSceneFloatTrack* FloatPropertyTrack = nullptr;
		const FFloatProperty* FloatProperty = nullptr;
		int32 TransformKeyCount = 0;
		int32 VisibilityKeyCount = 0;
		int32 FloatPropertyKeyCount = 0;
		TArray<FString> EvaluatedTrackClasses;
		for (UMovieSceneTrack* Track : Binding->GetTracks())
		{
			if (!Track) throw std::runtime_error("binding contains a null track");
			EvaluatedTrackClasses.Add(Track->GetClass()->GetPathName());
			if (Track->GetClass() == UMovieScene3DTransformTrack::StaticClass())
			{
				if (TransformSection || Track->GetAllSections().Num() != 1)
					throw std::runtime_error("frame evaluation requires exactly one transform section");
				TransformSection = Cast<UMovieScene3DTransformSection>(Track->GetAllSections()[0]);
				if (!TransformSection) throw std::runtime_error("transform track has an unsupported section type");
				for (const FMovieSceneDoubleChannel* Channel : TransformSection->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>())
					if (Channel) TransformKeyCount += Channel->GetData().GetTimes().Num();
			}
			else if (Track->GetClass() == UMovieSceneVisibilityTrack::StaticClass())
			{
				if (VisibilitySection || Track->GetAllSections().Num() != 1)
					throw std::runtime_error("frame evaluation supports one visibility section");
				VisibilitySection = Track->GetAllSections()[0];
				for (const FMovieSceneBoolChannel* Channel : VisibilitySection->GetChannelProxy().GetChannels<FMovieSceneBoolChannel>())
					if (Channel) VisibilityKeyCount += Channel->GetData().GetTimes().Num();
			}
			else if (Track->GetClass() == UMovieSceneFloatTrack::StaticClass())
			{
				if (FloatPropertyTrack || Track->GetAllSections().Num() != 1)
					throw std::runtime_error("frame evaluation supports one float-property section");
				FloatPropertyTrack = Cast<UMovieSceneFloatTrack>(Track);
				FloatPropertySection = Track->GetAllSections()[0];
				if (!FloatPropertyTrack || FloatPropertyTrack->GetPropertyName().IsNone()
					|| FloatPropertyTrack->GetPropertyPath() != FloatPropertyTrack->GetPropertyName())
					throw std::runtime_error("float-property playback requires a top-level property binding");
				FloatProperty = FindFProperty<FFloatProperty>(PossessedClass, FloatPropertyTrack->GetPropertyName());
				if (!FloatProperty) throw std::runtime_error("float-property playback binding is not a float on the actor class");
				for (const FMovieSceneFloatChannel* Channel : FloatPropertySection->GetChannelProxy().GetChannels<FMovieSceneFloatChannel>())
					if (Channel) FloatPropertyKeyCount += Channel->GetData().GetTimes().Num();
			}
			else throw std::runtime_error("frame evaluation supports only transform, visibility, and float-property tracks");
		}
		if (!TransformSection || TransformKeyCount == 0) throw std::runtime_error("transform section has no keys to evaluate");
		if (VisibilitySection && VisibilityKeyCount == 0) throw std::runtime_error("visibility section has no keys to evaluate");
		if (FloatPropertySection && FloatPropertyKeyCount == 0) throw std::runtime_error("float-property section has no keys to evaluate");
		const bool bSourceActorWasHidden = SourceActor && SourceActor->IsHidden();
		const float SourceActorFloatPropertyBefore = SourceActor && FloatProperty
			? FloatProperty->GetPropertyValue_InContainer(SourceActor) : 0.0f;
		auto RequireFrameInSection = [&Body](const UMovieSceneSection* Section, const TCHAR* TrackName)
		{
			const TRange<FFrameNumber> Range = Section ? Section->GetRange() : TRange<FFrameNumber>::Empty();
			if (!Range.HasLowerBound() || !Range.HasUpperBound() || !Range.Contains(FFrameNumber(Body.Frame)))
				throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("frame must be inside the %s section range"), TrackName)));
			return Range;
		};
		const TRange<FFrameNumber> TransformRange = RequireFrameInSection(TransformSection, TEXT("transform"));
		if (VisibilitySection) RequireFrameInSection(VisibilitySection, TEXT("visibility"));
		if (FloatPropertySection) RequireFrameInSection(FloatPropertySection, TEXT("float-property"));

		const FFrameRate TickResolution = MovieScene->GetTickResolution();
		const FFrameRate DisplayRate = MovieScene->GetDisplayRate();
		if (!TickResolution.IsValid() || !DisplayRate.IsValid()) throw std::runtime_error("Level Sequence frame rates are invalid");
		const FFrameTime DisplayFrame = FFrameRate::TransformTime(FFrameTime(Body.Frame), TickResolution, DisplayRate);
		const FFrameTime StartDisplayFrame = FFrameRate::TransformTime(FFrameTime(TransformRange.GetLowerBoundValue()), TickResolution, DisplayRate);
		const double DisplayFramesToEvaluate = DisplayFrame.AsDecimal() - StartDisplayFrame.AsDecimal();
		if (!FMath::IsFinite(DisplayFramesToEvaluate) || DisplayFramesToEvaluate < 0.0 || DisplayFramesToEvaluate > 600.0)
			throw std::runtime_error("bounded preview playback supports at most 600 display frames from the transform section start");
		const int32 PlaybackSteps = FMath::CeilToInt(DisplayFramesToEvaluate);
		if (Body.bPlayOnEditorActor && !SourceActor)
			throw std::runtime_error("play_on_editor_actor requires actor_path for the placed possessable");

		FPreviewScene::ConstructionValues PreviewValues;
		PreviewValues.SetCreateDefaultLighting(false).SetCreatePhysicsScene(false).SetForceMipsResident(false)
			.SetTransactional(false).SetEditor(false);
		TUniquePtr<FPreviewScene> PreviewScene;
		UWorld* EvaluationWorld = nullptr;
		if (Body.bPlayOnEditorActor)
		{
			EvaluationWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!EvaluationWorld || SourceActor->GetWorld() != EvaluationWorld)
				throw std::runtime_error("actor_path must identify an actor in the current editor world");
		}
		else
		{
			PreviewScene = MakeUnique<FPreviewScene>(PreviewValues);
			EvaluationWorld = PreviewScene->GetWorld();
			if (!EvaluationWorld) throw std::runtime_error("failed to create an isolated preview world");
		}
		const int64 TickFramesPerDisplayFrame = FMath::Max<int64>(1, FMath::CeilToInt64(TickResolution.AsDecimal() / DisplayRate.AsDecimal()));
		const int64 PreviewStartValue = FMath::Min<int64>(TransformRange.GetLowerBoundValue().Value, Body.Frame);
		const int64 RequestedEndValue = static_cast<int64>(Body.Frame) + TickFramesPerDisplayFrame;
		const int64 PreviewEndValue = FMath::Max<int64>(TransformRange.GetUpperBoundValue().Value, RequestedEndValue);
		const int64 PreviewDurationValue = PreviewEndValue - PreviewStartValue;
		if (PreviewDurationValue <= 0 || PreviewDurationValue > TNumericLimits<int32>::Max()
			|| PreviewStartValue < TNumericLimits<int32>::Min() || PreviewEndValue > TNumericLimits<int32>::Max())
			throw std::runtime_error("transform section range is too large for preview evaluation");
		const FName PreviewSequenceName = MakeUniqueObjectName(GetTransientPackage(), ULevelSequence::StaticClass(),
			FName(*FString::Printf(TEXT("%s_Evaluation"), *Sequence->GetName())));
		ULevelSequence* PreviewSequence = DuplicateObject<ULevelSequence>(Sequence, GetTransientPackage(), PreviewSequenceName);
		if (PreviewSequence) PreviewSequence->SetFlags(RF_Transient);
		UMovieScene* PreviewMovieScene = PreviewSequence ? PreviewSequence->GetMovieScene() : nullptr;
		if (!PreviewMovieScene || PreviewMovieScene == MovieScene)
			throw std::runtime_error("failed to create an independent Level Sequence preview copy");
		PreviewMovieScene->SetPlaybackRange(FFrameNumber(static_cast<int32>(PreviewStartValue)), static_cast<int32>(PreviewDurationValue), false);

		AActor* TargetActor = Body.bPlayOnEditorActor ? SourceActor : nullptr;
		ALevelSequenceActor* SequenceActor = nullptr;
		ULevelSequencePlayer* Player = nullptr;
		UPackage* SourcePackage = SourceActor ? SourceActor->GetOutermost() : nullptr;
		const bool bSourcePackageWasDirty = SourcePackage && SourcePackage->IsDirty();
		bool bEvaluationCleanedUp = false;
		auto CleanupEvaluation = [&]()
		{
			if (bEvaluationCleanedUp) return;
			bEvaluationCleanedUp = true;
			if (Player)
			{
				Player->Stop();
				Player->RestoreState();
			}
			if (Body.bPlayOnEditorActor && SourceActor && IsValid(SourceActor))
			{
				SourceActor->SetActorTransform(SourceActorTransform, false, nullptr, ETeleportType::TeleportPhysics);
				if (VisibilitySection) SourceActor->SetActorHiddenInGame(bSourceActorWasHidden);
				if (FloatProperty)
				{
					FloatProperty->SetPropertyValue_InContainer(SourceActor, SourceActorFloatPropertyBefore);
					FPropertyChangedEvent PropertyChanged(const_cast<FFloatProperty*>(FloatProperty));
					SourceActor->PostEditChangeProperty(PropertyChanged);
				}
			}
			if (SequenceActor && IsValid(SequenceActor)) EvaluationWorld->DestroyActor(SequenceActor);
			if (!Body.bPlayOnEditorActor && TargetActor && IsValid(TargetActor)) EvaluationWorld->DestroyActor(TargetActor);
			if (Body.bPlayOnEditorActor && SourcePackage && SourcePackage->IsDirty() != bSourcePackageWasDirty)
				SourcePackage->SetDirtyFlag(bSourcePackageWasDirty);
		};
		ON_SCOPE_EXIT
		{
			CleanupEvaluation();
		};

		if (!Body.bPlayOnEditorActor)
		{
			FActorSpawnParameters SpawnParams;
			SpawnParams.ObjectFlags |= RF_Transient;
			SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			TargetActor = EvaluationWorld->SpawnActor<AActor>(const_cast<UClass*>(PossessedClass), FTransform::Identity, SpawnParams);
		}
		if (!TargetActor || !TargetActor->GetRootComponent())
			throw std::runtime_error(Body.bPlayOnEditorActor
				? "bound editor actor has no root component"
				: "possessable actor class did not create a root component in the preview world");
		if (SourceActor && !Body.bPlayOnEditorActor)
			TargetActor->SetActorTransform(SourceActorTransform, false, nullptr, ETeleportType::TeleportPhysics);

		FMovieSceneSequencePlaybackSettings PlaybackSettings;
		PlaybackSettings.bAutoPlay = false;
		PlaybackSettings.bDisableCameraCuts = true;
		PlaybackSettings.FinishCompletionStateOverride = EMovieSceneCompletionModeOverride::ForceRestoreState;
		Player = ULevelSequencePlayer::CreateLevelSequencePlayer(EvaluationWorld, PreviewSequence, PlaybackSettings, SequenceActor);
		if (!Player || !SequenceActor) throw std::runtime_error("failed to create a Level Sequence player for evaluation");
		Player->SetDisableCameraCuts(true);
		TArray<AActor*> BoundActors;
		BoundActors.Add(TargetActor);
		const FMovieSceneObjectBindingID PlaybackBindingId{UE::MovieScene::FRelativeObjectBindingID(BindingGuid)};
		SequenceActor->SetBinding(PlaybackBindingId, BoundActors, false);
		const TArray<UObject*> ResolvedBoundObjects = Player->GetBoundObjects(PlaybackBindingId);
		if (!ResolvedBoundObjects.Contains(TargetActor))
			throw std::runtime_error("Level Sequence player did not resolve the preview actor binding");
		Player->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(StartDisplayFrame, EUpdatePositionMethod::Jump));
		Player->Play();
		const float PlaybackDeltaSeconds = 1.0f / static_cast<float>(DisplayRate.AsDecimal());
		for (int32 Step = 0; Step < PlaybackSteps; ++Step)
		{
			Player->Update(PlaybackDeltaSeconds);
			if (Step + 1 < PlaybackSteps && !Player->IsPlaying())
				throw std::runtime_error("Level Sequence playback stopped before reaching the requested frame");
		}
		const FQualifiedFrameTime SampleTime = Player->GetCurrentTime();
		if (SampleTime.Time.AsDecimal() + 0.05 < DisplayFrame.AsDecimal())
			throw std::runtime_error("Level Sequence player did not advance through the requested display frame");
		if (SampleTime.Time.AsDecimal() - DisplayFrame.AsDecimal() > 1.05)
			throw std::runtime_error("Level Sequence player advanced more than one display frame beyond the requested sample");

		const FTransform AppliedTransform = TargetActor->GetActorTransform();
		if (AppliedTransform.ContainsNaN()) throw std::runtime_error("Level Sequence evaluation produced a non-finite actor transform");
		const FVector Location = AppliedTransform.GetLocation();
		const FRotator Rotation = AppliedTransform.Rotator();
		const FVector Scale = AppliedTransform.GetScale3D();
		const bool bActorHidden = TargetActor->IsHidden();
		const float FloatPropertyValue = FloatProperty ? FloatProperty->GetPropertyValue_InContainer(TargetActor) : 0.0f;
		CleanupEvaluation();
		if (SourceActor && !SourceActor->GetActorTransform().Equals(SourceActorTransform, 0.01f))
			throw std::runtime_error("Level Sequence evaluation did not restore the bound editor actor transform");
		if (Body.bPlayOnEditorActor && SourceActor && VisibilitySection
			&& SourceActor->IsHidden() != bSourceActorWasHidden)
			throw std::runtime_error("Level Sequence evaluation did not restore the bound editor actor visibility");
		if (Body.bPlayOnEditorActor && SourceActor && FloatProperty
			&& !FMath::IsNearlyEqual(FloatProperty->GetPropertyValue_InContainer(SourceActor), SourceActorFloatPropertyBefore, 0.0001f))
			throw std::runtime_error("Level Sequence evaluation did not restore the bound editor actor float property");
		if (Body.bPlayOnEditorActor && SourcePackage && SourcePackage->IsDirty() != bSourcePackageWasDirty)
			throw std::runtime_error("Level Sequence evaluation did not restore the editor actor package dirty state");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("evaluated"), true);
		Writer->WriteValue(TEXT("isolated_preview"), !Body.bPlayOnEditorActor);
		Writer->WriteValue(TEXT("evaluation_mode"), Body.bPlayOnEditorActor ? TEXT("editor_actor") : TEXT("preview_actor"));
		Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
		Writer->WriteValue(TEXT("binding_guid"), BindingGuid.ToString());
		Writer->WriteValue(TEXT("source_actor_path"), SourceActor ? SourceActor->GetPathName() : TEXT(""));
		if (SourceActor) Writer->WriteValue(TEXT("source_actor_unchanged"), true);
		if (Body.bPlayOnEditorActor && VisibilitySection) Writer->WriteValue(TEXT("source_actor_visibility_restored"), true);
		if (Body.bPlayOnEditorActor && FloatProperty) Writer->WriteValue(TEXT("source_actor_float_property_restored"), true);
		if (Body.bPlayOnEditorActor) Writer->WriteValue(TEXT("source_package_dirty_restored"), true);
		Writer->WriteValue(TEXT("actor_class"), PossessedClass->GetPathName());
		Writer->WriteValue(TEXT("tick_frame"), Body.Frame);
		Writer->WriteValue(TEXT("display_frame"), DisplayFrame.AsDecimal());
		Writer->WriteValue(TEXT("sampled_display_frame"), SampleTime.Time.AsDecimal());
		Writer->WriteValue(TEXT("playback_steps"), PlaybackSteps);
		Writer->WriteValue(TEXT("transform_key_count"), TransformKeyCount);
		Writer->WriteValue(TEXT("visibility_key_count"), VisibilityKeyCount);
		Writer->WriteValue(TEXT("float_property_key_count"), FloatPropertyKeyCount);
		Writer->WriteValue(TEXT("actor_hidden"), bActorHidden);
		Writer->WriteArrayStart(TEXT("evaluated_track_classes"));
		for (const FString& TrackClass : EvaluatedTrackClasses) Writer->WriteValue(TrackClass);
		Writer->WriteArrayEnd();
		if (FloatPropertyTrack)
		{
			Writer->WriteValue(TEXT("float_property_name"), FloatPropertyTrack->GetPropertyName().ToString());
			Writer->WriteValue(TEXT("float_property_value"), FloatPropertyValue);
		}
		Writer->WriteObjectStart(TEXT("transform"));
		Writer->WriteObjectStart(TEXT("location"));
		Writer->WriteValue(TEXT("x"), Location.X);
		Writer->WriteValue(TEXT("y"), Location.Y);
		Writer->WriteValue(TEXT("z"), Location.Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectStart(TEXT("rotation"));
		Writer->WriteValue(TEXT("pitch"), Rotation.Pitch);
		Writer->WriteValue(TEXT("yaw"), Rotation.Yaw);
		Writer->WriteValue(TEXT("roll"), Rotation.Roll);
		Writer->WriteObjectEnd();
		Writer->WriteObjectStart(TEXT("scale"));
		Writer->WriteValue(TEXT("x"), Scale.X);
		Writer->WriteValue(TEXT("y"), Scale.Y);
		Writer->WriteValue(TEXT("z"), Scale.Z);
		Writer->WriteObjectEnd();
		Writer->WriteObjectEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/animation-sequences/create", [](const FHttpContext<FAnimationCreateReq, FString>& C)
	{
		auto Body = C.RequestBody();
		return C.TextResponse(ClassUtils::CreateAnimationSequence(Body.AssetPath, Body.SkeletonPath, Body.PreviewMeshPath));
	});

	App->Patch("/animation-sequences/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(Body.AssetPath));
		if (!Sequence)
			throw std::runtime_error("Asset is not an Animation Sequence");
		ApplyAssetProperties(Sequence, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/animation-sequences/compression", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
		Writer->WriteValue(TEXT("bone_settings_path"), Sequence->BoneCompressionSettings ? Sequence->BoneCompressionSettings->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("curve_settings_path"), Sequence->CurveCompressionSettings ? Sequence->CurveCompressionSettings->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("variable_frame_stripping_path"), Sequence->VariableFrameStrippingSettings ? Sequence->VariableFrameStrippingSettings->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("allow_frame_stripping"), Sequence->bAllowFrameStripping);
		Writer->WriteValue(TEXT("error_threshold_scale"), Sequence->CompressionErrorThresholdScale);
		Writer->WriteValue(TEXT("compressed_data_out_of_date"), Sequence->IsCompressedDataOutOfDate());
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/animation-sequences/compression", [](const FHttpContext<FAnimationCompressionReq, FString>& C)
	{
		const FAnimationCompressionReq Body = C.RequestBody();
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(Body.AssetPath));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		UAnimBoneCompressionSettings* Bone = nullptr;
		UAnimCurveCompressionSettings* Curve = nullptr;
		UVariableFrameStrippingSettings* Stripping = nullptr;
		if (!Body.BoneSettingsPath.IsEmpty())
		{
			Bone = Cast<UAnimBoneCompressionSettings>(LoadAsset(Body.BoneSettingsPath));
			if (!Bone || !Bone->AreSettingsValid()) throw std::runtime_error("bone_settings_path must identify valid Bone Compression Settings");
		}
		if (!Body.CurveSettingsPath.IsEmpty())
		{
			Curve = Cast<UAnimCurveCompressionSettings>(LoadAsset(Body.CurveSettingsPath));
			if (!Curve || !Curve->AreSettingsValid()) throw std::runtime_error("curve_settings_path must identify valid Curve Compression Settings");
		}
		if (!Body.VariableFrameStrippingPath.IsEmpty())
		{
			Stripping = Cast<UVariableFrameStrippingSettings>(LoadAsset(Body.VariableFrameStrippingPath));
			if (!Stripping) throw std::runtime_error("variable_frame_stripping_path must identify Variable Frame Stripping Settings");
		}
		if (Body.bSetErrorThresholdScale && (!FMath::IsFinite(Body.ErrorThresholdScale) || Body.ErrorThresholdScale <= 0.0f))
			throw std::runtime_error("error_threshold_scale must be finite and positive");
		const bool bBoneChanged = Bone && Sequence->BoneCompressionSettings != Bone;
		const bool bCurveChanged = Curve && Sequence->CurveCompressionSettings != Curve;
		const bool bStrippingChanged = Stripping && Sequence->VariableFrameStrippingSettings != Stripping;
		const bool bAllowChanged = Body.bSetAllowFrameStripping && Sequence->bAllowFrameStripping != Body.bAllowFrameStripping;
		const bool bScaleChanged = Body.bSetErrorThresholdScale && Sequence->CompressionErrorThresholdScale != Body.ErrorThresholdScale;
		const bool bChanged = bBoneChanged || bCurveChanged || bStrippingChanged || bAllowChanged || bScaleChanged;
		if (bChanged && !Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetAnimationCompression", "Set Animation Compression"));
			Sequence->Modify();
			if (bBoneChanged) UAnimationBlueprintLibrary::SetBoneCompressionSettings(Sequence, Bone);
			if (bCurveChanged) UAnimationBlueprintLibrary::SetCurveCompressionSettings(Sequence, Curve);
			if (bStrippingChanged) UAnimationBlueprintLibrary::SetVariableFrameStrippingSettings(Sequence, Stripping);
			if (bAllowChanged) Sequence->bAllowFrameStripping = Body.bAllowFrameStripping;
			if (bScaleChanged) Sequence->CompressionErrorThresholdScale = Body.ErrorThresholdScale;
			const FName ChangedName = bBoneChanged ? GET_MEMBER_NAME_CHECKED(UAnimSequence, BoneCompressionSettings)
				: bCurveChanged ? GET_MEMBER_NAME_CHECKED(UAnimSequence, CurveCompressionSettings)
				: bStrippingChanged ? GET_MEMBER_NAME_CHECKED(UAnimSequence, VariableFrameStrippingSettings)
				: bAllowChanged ? GET_MEMBER_NAME_CHECKED(UAnimSequence, bAllowFrameStripping)
				: GET_MEMBER_NAME_CHECKED(UAnimSequence, CompressionErrorThresholdScale);
			FProperty* ChangedProperty = FindFProperty<FProperty>(UAnimSequence::StaticClass(), ChangedName);
			FPropertyChangedEvent ChangedEvent(ChangedProperty);
			Sequence->PostEditChangeProperty(ChangedEvent);
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Get("/animation-sequences/tracks", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const IAnimationDataModel* Model = Sequence->GetDataModel();
		TArray<FName> BoneTracks;
		if (Model) Model->GetBoneTrackNames(BoneTracks);
		const USkeleton* Skeleton = Sequence->GetSkeleton();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
		Writer->WriteValue(TEXT("source_keys"), Model ? Model->GetNumberOfKeys() : 0);
		Writer->WriteArrayStart(TEXT("bone_tracks"));
		for (const FName& Name : BoneTracks)
		{
			PRAGMA_DISABLE_DEPRECATION_WARNINGS
			const FBoneAnimationTrack* Track = Model->FindBoneTrackByName(Name);
			PRAGMA_ENABLE_DEPRECATION_WARNINGS
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Name.ToString());
			Writer->WriteValue(TEXT("skeleton_bone_index"), Skeleton ? Skeleton->GetReferenceSkeleton().FindBoneIndex(Name) : INDEX_NONE);
			Writer->WriteValue(TEXT("storage"), Track ? TEXT("raw") : TEXT("sequencer"));
			if (Track)
			{
				Writer->WriteValue(TEXT("position_keys"), Track->InternalTrackData.PosKeys.Num());
				Writer->WriteValue(TEXT("rotation_keys"), Track->InternalTrackData.RotKeys.Num());
				Writer->WriteValue(TEXT("scale_keys"), Track->InternalTrackData.ScaleKeys.Num());
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/animation-sequences/bone-track-keys", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const FString BoneName = C.Query("bone_name");
		if (BoneName.IsEmpty()) throw std::runtime_error("bone_name is required");
		int32 StartFrame = 0;
		int32 Count = 100;
		const FString StartText = C.Query("start_frame", TEXT("0"));
		const FString CountText = C.Query("count", TEXT("100"));
		if (!LexTryParseString(StartFrame, *StartText) || !LexTryParseString(Count, *CountText))
			throw std::runtime_error("start_frame and count must be integers");
		return C.TextResponse(AnimationSequenceUtils::BoneTrackJson(Sequence, FName(*BoneName), StartFrame, Count), TEXT("application/json"));
	});

	App->Patch("/animation-sequences/bone-tracks", [](const FHttpContext<FAnimationBoneTrackReq, FString>& C)
	{
		const FAnimationBoneTrackReq Body = C.RequestBody();
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(Body.AssetPath));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const bool bChanged = AnimationSequenceUtils::EditBoneTrack(Sequence, Body);
		if (bChanged && !Body.bDryRun)
		{
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Patch("/animation-sequences/timing", [](const FHttpContext<FAnimationTimingReq, FString>& C)
	{
		const FAnimationTimingReq Body = C.RequestBody();
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(Body.AssetPath));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const bool bChanged = AnimationSequenceUtils::EditTiming(Sequence, Body);
		if (bChanged && !Body.bDryRun)
		{
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Get("/animation-sequences/timeline", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const IAnimationDataModel* Model = Sequence->GetDataModel();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
		Writer->WriteArrayStart(TEXT("notify_tracks"));
		for (const FAnimNotifyTrack& Track : Sequence->AnimNotifyTracks) Writer->WriteValue(Track.TrackName.ToString());
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("notifies"));
		for (const FAnimNotifyEvent& Notify : Sequence->Notifies)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Notify.NotifyName.ToString());
			Writer->WriteValue(TEXT("time"), Notify.GetTriggerTime());
			Writer->WriteValue(TEXT("duration"), Notify.GetDuration());
			Writer->WriteValue(TEXT("track_index"), Notify.TrackIndex);
			Writer->WriteValue(TEXT("notify_class"), Notify.Notify ? Notify.Notify->GetClass()->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("state_class"), Notify.NotifyStateClass ? Notify.NotifyStateClass->GetClass()->GetPathName() : TEXT(""));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("sync_markers"));
		for (const FAnimSyncMarker& Marker : Sequence->AuthoredSyncMarkers)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Marker.MarkerName.ToString());
			Writer->WriteValue(TEXT("time"), Marker.Time);
			Writer->WriteValue(TEXT("track_index"), Marker.TrackIndex);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("float_curves"));
		if (Model) for (const FFloatCurve& Curve : Model->GetCurveData().FloatCurves)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Curve.GetName().ToString());
			Writer->WriteValue(TEXT("key_count"), Curve.FloatCurve.GetNumKeys());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("transform_curves"));
		if (Model) for (const FTransformCurve& Curve : Model->GetCurveData().TransformCurves)
			Writer->WriteValue(Curve.GetName().ToString());
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("attributes"));
		if (Model) for (const FAnimatedBoneAttribute& Attribute : Model->GetAttributes())
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Attribute.Identifier.GetName().ToString());
			Writer->WriteValue(TEXT("bone_name"), Attribute.Identifier.GetBoneName().ToString());
			Writer->WriteValue(TEXT("bone_index"), Attribute.Identifier.GetBoneIndex());
			Writer->WriteValue(TEXT("type"), Attribute.Identifier.GetType() ? Attribute.Identifier.GetType()->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("key_count"), Attribute.Curve.GetNumKeys());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/animation-sequences/attributes", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		return C.TextResponse(AnimationSequenceUtils::AttributesJson(Sequence), TEXT("application/json"));
	});

	App->Patch("/animation-sequences/attributes", [](const FHttpContext<FAnimationAttributeReq, FString>& C)
	{
		const FAnimationAttributeReq Body = C.RequestBody();
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(Body.AssetPath));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const bool bChanged = AnimationSequenceUtils::EditAttribute(Sequence, Body);
		if (bChanged && !Body.bDryRun)
		{
			MarkAssetDirty(Sequence);
			SaveIfRequested(Sequence, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/animation-sequences/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UAnimSequence* Sequence = Cast<UAnimSequence>(LoadAsset(Body.AssetPath));
		if (!Sequence) throw std::runtime_error("Asset is not an Animation Sequence");
		const IAnimationDataModel* Model = Sequence->GetDataModel();
		const USkeleton* Skeleton = Sequence->GetSkeleton();
		const float Length = Sequence->GetPlayLength();
		TArray<FString> Errors;
		if (!Model) Errors.Add(TEXT("Animation data model is missing"));
		if (!Skeleton) Errors.Add(TEXT("Skeleton is missing"));
		if (!FMath::IsFinite(Length) || Length < 0.0f) Errors.Add(TEXT("Play length is invalid"));
		if (Model)
		{
			const FFrameRate Rate = Model->GetFrameRate();
			if (Rate.Numerator <= 0 || Rate.Denominator <= 0) Errors.Add(TEXT("Source frame rate is invalid"));
			if (Model->GetNumberOfKeys() <= 0 || Model->GetNumberOfFrames() < 0) Errors.Add(TEXT("Source key/frame count is invalid"));
			TArray<FName> BoneTracks;
			Model->GetBoneTrackNames(BoneTracks);
			TSet<FName> Seen;
			for (const FName& Name : BoneTracks)
			{
				if (Seen.Contains(Name)) Errors.Add(FString::Printf(TEXT("Duplicate bone track: %s"), *Name.ToString()));
				Seen.Add(Name);
				if (!Skeleton || Skeleton->GetReferenceSkeleton().FindBoneIndex(Name) == INDEX_NONE)
					Errors.Add(FString::Printf(TEXT("Bone track has no matching skeleton bone: %s"), *Name.ToString()));
			}
			for (const FAnimatedBoneAttribute& Attribute : Model->GetAttributes())
			{
				const FAnimationAttributeIdentifier& Id = Attribute.Identifier;
				if (!Id.IsValid() || !Skeleton || Skeleton->GetReferenceSkeleton().FindBoneIndex(Id.GetBoneName()) != Id.GetBoneIndex())
					Errors.Add(FString::Printf(TEXT("Invalid animated attribute: %s"), *Id.GetName().ToString()));
			}
			AnimationSequenceUtils::AppendBoneTrackKeyIssues(Sequence, Errors);
		}
		for (const FAnimNotifyEvent& Notify : Sequence->Notifies)
		{
			const float Time = Notify.GetTriggerTime();
			const float Duration = Notify.GetDuration();
			if (!FMath::IsFinite(Time) || !FMath::IsFinite(Duration) || Time < 0.0f || Duration < 0.0f || Time + Duration > Length + KINDA_SMALL_NUMBER)
				Errors.Add(FString::Printf(TEXT("Notify lies outside sequence range: %s"), *Notify.NotifyName.ToString()));
			if (Notify.TrackIndex < 0 || Notify.TrackIndex >= Sequence->AnimNotifyTracks.Num())
				Errors.Add(FString::Printf(TEXT("Notify has invalid track index: %s"), *Notify.NotifyName.ToString()));
		}
		for (const FAnimSyncMarker& Marker : Sequence->AuthoredSyncMarkers)
		{
			if (!FMath::IsFinite(Marker.Time) || Marker.Time < 0.0f || Marker.Time > Length + KINDA_SMALL_NUMBER)
				Errors.Add(FString::Printf(TEXT("Sync marker lies outside sequence range: %s"), *Marker.MarkerName.ToString()));
			if (Marker.TrackIndex < 0 || Marker.TrackIndex >= Sequence->AnimNotifyTracks.Num())
				Errors.Add(FString::Printf(TEXT("Sync marker has invalid track index: %s"), *Marker.MarkerName.ToString()));
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Sequence->GetPathName());
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("sampled_keys"), Sequence->GetNumberOfSampledKeys());
		Writer->WriteValue(TEXT("play_length"), Length);
		Writer->WriteArrayStart(TEXT("errors"));
		for (const FString& Error : Errors) Writer->WriteValue(Error);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/animation-blueprints/inspect", [](const FHttpContext<void, FString>& C)
	{
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(C.Query("asset_path")));
		if (!Blueprint)
			throw std::runtime_error("Asset is not an Animation Blueprint");
		return C.TextResponse(AnimationBlueprintUtils::InspectJson(Blueprint), TEXT("application/json"));
	});

	App->Patch("/animation-blueprints/settings", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(Body.AssetPath));
		if (!Blueprint)
			throw std::runtime_error("Asset is not an Animation Blueprint");
		ApplyAssetProperties(Blueprint, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/animation-blueprints/graphs", [](const FHttpContext<void, FString>& C)
	{
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(C.Query("asset_path")));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		const FString GraphPath = C.Query("graph_path");
		return C.TextResponse(GraphPath.IsEmpty() ? AnimationBlueprintUtils::GraphsJson(Blueprint)
			: AnimationBlueprintUtils::GraphJson(Blueprint, AnimationBlueprintUtils::FindGraph(Blueprint, GraphPath)), TEXT("application/json"));
	});

	App->Get("/animation-blueprints/state-machines", [](const FHttpContext<void, FString>& C)
	{
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(C.Query("asset_path")));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		return C.TextResponse(AnimationBlueprintUtils::StateMachinesJson(Blueprint), TEXT("application/json"));
	});

	App->Patch("/animation-blueprints/state-machines", [](const FHttpContext<FAnimationStateMachineReq, FString>& C)
	{
		const FAnimationStateMachineReq Body = C.RequestBody();
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(Body.AssetPath));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		FGuid NodeId;
		const bool bChanged = AnimationBlueprintUtils::EditStateMachine(Blueprint, Body, NodeId);
		if (bChanged && !Body.bDryRun)
		{
			MarkAssetDirty(Blueprint);
			SaveIfRequested(Blueprint, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s,\"node_id\":\"%s\"}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false"), *NodeId.ToString(EGuidFormats::DigitsWithHyphens)), TEXT("application/json"));
	});

	App->Get("/animation-blueprints/variables", [](const FHttpContext<void, FString>& C)
	{
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(C.Query("asset_path")));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		return C.TextResponse(AnimationBlueprintUtils::VariablesJson(Blueprint), TEXT("application/json"));
	});

	App->Patch("/animation-blueprints/transitions", [](const FHttpContext<FAnimationTransitionReq, FString>& C)
	{
		const FAnimationTransitionReq Body = C.RequestBody();
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(Body.AssetPath));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		const bool bChanged = AnimationBlueprintUtils::EditTransition(Blueprint, Body);
		if (bChanged && !Body.bDryRun)
		{
			MarkAssetDirty(Blueprint);
			SaveIfRequested(Blueprint, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Patch("/animation-blueprints/pose-links", [](const FHttpContext<FAnimationPoseLinkReq, FString>& C)
	{
		const FAnimationPoseLinkReq Body = C.RequestBody();
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(Body.AssetPath));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		const bool bChanged = AnimationBlueprintUtils::EditPoseLink(Blueprint, Body);
		if (bChanged && !Body.bDryRun)
		{
			MarkAssetDirty(Blueprint);
			SaveIfRequested(Blueprint, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			bChanged && !Body.bDryRun ? TEXT("true") : TEXT("false"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			bChanged && !Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/animation-blueprints/layout", [](const FHttpContext<FAnimationBlueprintGraphReq, FString>& C)
	{
		const FAnimationBlueprintGraphReq Body = C.RequestBody();
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(Body.AssetPath));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		UEdGraph* Graph = AnimationBlueprintUtils::FindGraph(Blueprint, Body.GraphPath);
		if (!Body.bDryRun)
		{
			const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "LayoutAnimationGraph", "Layout Animation Blueprint Graph"));
			Blueprint->Modify(); Graph->Modify();
			GraphLayoutUtils::Format(Blueprint, Graph, {}, Body.ColumnSpacing, Body.RowSpacing, false);
			MarkAssetDirty(Blueprint);
			SaveIfRequested(Blueprint, Body.bSave);
		}
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":%s,\"dry_run\":%s,\"saved\":%s}"),
			Body.bDryRun ? TEXT("false") : TEXT("true"), Body.bDryRun ? TEXT("true") : TEXT("false"),
			!Body.bDryRun && Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/animation-blueprints/validate", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(C.RequestBody().AssetPath));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		return C.TextResponse(AnimationBlueprintUtils::ValidateJson(Blueprint), TEXT("application/json"));
	});

	App->Post("/animation-blueprints/compile", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UAnimBlueprint* Blueprint = Cast<UAnimBlueprint>(LoadAsset(Body.AssetPath));
		if (!Blueprint) throw std::runtime_error("Asset is not an Animation Blueprint");
		FKismetEditorUtilities::CompileBlueprint(Blueprint);
		SaveIfRequested(Blueprint, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"status\":%d,\"valid\":%s,\"saved\":%s}"),
			static_cast<int32>(Blueprint->Status), Blueprint->Status == BS_Error ? TEXT("false") : TEXT("true"),
			Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Get("/blend-spaces/samples", [](const FHttpContext<void, FString>& C)
	{
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(C.Query("asset_path")));
		if (!BlendSpace)
			throw std::runtime_error("Asset is not a Blend Space");
		const TArray<FGuid> Ids = ResolveBlendSampleIds(BlendSpace);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		const TArray<FBlendSample>& Samples = BlendSpace->GetBlendSamples();
		for (int32 Index = 0; Index < Samples.Num(); ++Index)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("index"), Index);
			Writer->WriteValue(TEXT("id"), Ids[Index].ToString(EGuidFormats::DigitsWithHyphens));
			Writer->WriteValue(TEXT("animation"), Samples[Index].Animation ? Samples[Index].Animation->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("x"), Samples[Index].SampleValue.X);
			Writer->WriteValue(TEXT("y"), Samples[Index].SampleValue.Y);
			Writer->WriteValue(TEXT("z"), Samples[Index].SampleValue.Z);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/blend-spaces/inspect", [](const FHttpContext<void, FString>& C)
	{
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(C.Query("asset_path")));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(BlendSpace), TEXT("application/json"));
	});

	App->Get("/blend-spaces/axes", [](const FHttpContext<void, FString>& C)
	{
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(C.Query("asset_path")));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		const int32 AxisCount = BlendSpace->IsA<UBlendSpace1D>() ? 1 : 2;
		for (int32 Index = 0; Index < AxisCount; ++Index)
		{
			const FBlendParameter& Axis = BlendSpace->GetBlendParameter(Index);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("index"), Index);
			Writer->WriteValue(TEXT("display_name"), Axis.DisplayName);
			Writer->WriteValue(TEXT("min"), Axis.Min);
			Writer->WriteValue(TEXT("max"), Axis.Max);
			Writer->WriteValue(TEXT("grid_num"), Axis.GridNum);
			Writer->WriteValue(TEXT("snap_to_grid"), Axis.bSnapToGrid);
			Writer->WriteValue(TEXT("wrap_input"), Axis.bWrapInput);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/blend-spaces/axes", [](const FHttpContext<FBlendSpaceReq, FString>& C)
	{
		const FBlendSpaceReq Body = C.RequestBody();
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(Body.AssetPath));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		const int32 AxisCount = BlendSpace->IsA<UBlendSpace1D>() ? 1 : 2;
		if (Body.AxisIndex < 0 || Body.AxisIndex >= AxisCount) throw std::runtime_error("axis_index is invalid for this Blend Space");
		if (Body.Properties.IsEmpty()) throw std::runtime_error("properties must contain an axis field");
		FBlendParameter Proposed = BlendSpace->GetBlendParameter(Body.AxisIndex);
		bool bGridChanged = false;
		for (const TPair<FString, FString>& Field : Body.Properties)
		{
			if (Field.Key == TEXT("display_name")) Proposed.DisplayName = Field.Value;
			else if (Field.Key == TEXT("min"))
			{
				if (!LexTryParseString(Proposed.Min, *Field.Value) || !FMath::IsFinite(Proposed.Min)) throw std::runtime_error("min must be finite");
			}
			else if (Field.Key == TEXT("max"))
			{
				if (!LexTryParseString(Proposed.Max, *Field.Value) || !FMath::IsFinite(Proposed.Max)) throw std::runtime_error("max must be finite");
			}
			else if (Field.Key == TEXT("grid_num"))
			{
				if (!LexTryParseString(Proposed.GridNum, *Field.Value)) throw std::runtime_error("grid_num must be an integer");
				bGridChanged = true;
			}
			else if (Field.Key == TEXT("snap_to_grid") || Field.Key == TEXT("wrap_input"))
			{
				const bool bValue = Field.Value.Equals(TEXT("true"), ESearchCase::IgnoreCase) || Field.Value == TEXT("1");
				if (!bValue && !Field.Value.Equals(TEXT("false"), ESearchCase::IgnoreCase) && Field.Value != TEXT("0"))
					throw std::runtime_error("boolean axis fields must be true or false");
				if (Field.Key == TEXT("snap_to_grid")) Proposed.bSnapToGrid = bValue;
				else Proposed.bWrapInput = bValue;
			}
			else throw std::runtime_error("unknown Blend Space axis field");
		}
		if (Proposed.Min >= Proposed.Max || Proposed.GridNum < 1 || Proposed.GridNum > 1000)
			throw std::runtime_error("axis requires min < max and grid_num between 1 and 1000");
		for (const FBlendSample& Sample : BlendSpace->GetBlendSamples())
		{
			const double Value = Sample.SampleValue[Body.AxisIndex];
			if (Value < Proposed.Min || Value > Proposed.Max)
				throw std::runtime_error("axis range would exclude an existing sample");
		}
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"axis_index\":%d}"), Body.AxisIndex), TEXT("application/json"));
		const TArray<FGuid> Ids = ResolveBlendSampleIds(BlendSpace);
		FStructProperty* AxisProperty = FindFProperty<FStructProperty>(UBlendSpace::StaticClass(), TEXT("BlendParameters"));
		if (!AxisProperty || AxisProperty->ArrayDim <= Body.AxisIndex) throw std::runtime_error("Blend Space axis property is unavailable");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditBlendSpaceAxis", "Edit Blend Space Axis"));
		BlendSpace->Modify();
		BlendSpace->PreEditChange(AxisProperty);
		*AxisProperty->ContainerPtrToValuePtr<FBlendParameter>(BlendSpace, Body.AxisIndex) = Proposed;
		FProperty* ChangedProperty = bGridChanged ? FindFProperty<FProperty>(FBlendParameter::StaticStruct(), TEXT("GridNum")) : AxisProperty;
		FPropertyChangedEvent ChangedEvent(ChangedProperty, EPropertyChangeType::ValueSet);
		ChangedEvent.MemberProperty = AxisProperty;
		BlendSpace->PostEditChangeProperty(ChangedEvent);
		BlendSpace->ResampleData();
		PersistBlendSampleIds(BlendSpace, Ids);
		MarkAssetDirty(BlendSpace);
		SaveIfRequested(BlendSpace, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":true,\"dry_run\":false,\"saved\":%s,\"axis_index\":%d}"), Body.bSave ? TEXT("true") : TEXT("false"), Body.AxisIndex), TEXT("application/json"));
	});

	App->Post("/blend-spaces/rebuild", [](const FHttpContext<FBlendSpaceReq, FString>& C)
	{
		const FBlendSpaceReq Body = C.RequestBody();
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(Body.AssetPath));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"sample_count\":%d}"), BlendSpace->GetNumberOfBlendSamples()), TEXT("application/json"));
		const TArray<FGuid> Ids = ResolveBlendSampleIds(BlendSpace);
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RebuildBlendSpace", "Rebuild Blend Space Triangulation"));
		BlendSpace->Modify();
		BlendSpace->ResampleData();
		PersistBlendSampleIds(BlendSpace, Ids);
		MarkAssetDirty(BlendSpace);
		SaveIfRequested(BlendSpace, Body.bSave);
		const FBlendSpaceData& Data = BlendSpace->GetBlendSpaceData();
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":true,\"saved\":%s,\"segments\":%d,\"triangles\":%d}"), Body.bSave ? TEXT("true") : TEXT("false"), Data.Segments.Num(), Data.Triangles.Num()), TEXT("application/json"));
	});

	App->Post("/blend-spaces/preview", [](const FHttpContext<FBlendSpaceReq, FString>& C)
	{
		const FBlendSpaceReq Body = C.RequestBody();
		const UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(Body.AssetPath));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		if (Body.SampleValue.ContainsNaN()) throw std::runtime_error("sample_value must be finite");
		TArray<FBlendSampleData> Samples;
		int32 CachedIndex = INDEX_NONE;
		const bool bValid = BlendSpace->GetSamplesFromBlendInput(Body.SampleValue, Samples, CachedIndex, false);
		const FVector Effective = BlendSpace->GetClampedAndWrappedBlendInput(Body.SampleValue);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), bValid);
		Writer->WriteObjectStart(TEXT("effective_input"));
		Writer->WriteValue(TEXT("x"), Effective.X);
		Writer->WriteValue(TEXT("y"), Effective.Y);
		Writer->WriteValue(TEXT("z"), Effective.Z);
		Writer->WriteObjectEnd();
		Writer->WriteArrayStart(TEXT("samples"));
		for (const FBlendSampleData& Sample : Samples)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("sample_index"), Sample.SampleDataIndex);
			Writer->WriteValue(TEXT("animation"), Sample.Animation ? Sample.Animation->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("weight"), Sample.TotalWeight);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/blend-spaces/validate", [](const FHttpContext<FBlendSpaceReq, FString>& C)
	{
		const FBlendSpaceReq Body = C.RequestBody();
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(Body.AssetPath));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		TArray<FString> Errors;
		TArray<FString> Warnings;
		const int32 AxisCount = BlendSpace->IsA<UBlendSpace1D>() ? 1 : 2;
		if (!BlendSpace->GetSkeleton()) Errors.Add(TEXT("Blend Space has no Skeleton"));
		for (int32 AxisIndex = 0; AxisIndex < AxisCount; ++AxisIndex)
		{
			const FBlendParameter& Axis = BlendSpace->GetBlendParameter(AxisIndex);
			if (!FMath::IsFinite(Axis.Min) || !FMath::IsFinite(Axis.Max) || Axis.Min >= Axis.Max)
				Errors.Add(FString::Printf(TEXT("axis %d has an invalid range"), AxisIndex));
			if (Axis.GridNum < 1 || Axis.GridNum > 1000)
				Errors.Add(FString::Printf(TEXT("axis %d has invalid grid divisions"), AxisIndex));
		}
		const TArray<FBlendSample>& Samples = BlendSpace->GetBlendSamples();
		if (Samples.IsEmpty()) Errors.Add(TEXT("Blend Space has no samples"));
		for (int32 Index = 0; Index < Samples.Num(); ++Index)
		{
			const FBlendSample& Sample = Samples[Index];
			const FString Prefix = FString::Printf(TEXT("sample %d"), Index);
			if (!Sample.Animation)
				Errors.Add(Prefix + TEXT(" has no animation"));
			else if (!BlendSpace->ValidateAnimationSequence(Sample.Animation))
				Errors.Add(Prefix + TEXT(" has an incompatible animation or Skeleton"));
			if (Sample.SampleValue.ContainsNaN())
				Errors.Add(Prefix + TEXT(" has a nonfinite coordinate"));
			else
			{
				if (FMath::Abs(Sample.SampleValue.Z) > KINDA_SMALL_NUMBER
					|| (AxisCount == 1 && FMath::Abs(Sample.SampleValue.Y) > KINDA_SMALL_NUMBER))
					Errors.Add(Prefix + TEXT(" uses a coordinate outside the Blend Space dimensions"));
				if (!BlendSpace->IsSampleWithinBounds(Sample.SampleValue))
					Errors.Add(Prefix + TEXT(" is outside the axis range"));
				if (BlendSpace->IsTooCloseToExistingSamplePoint(Sample.SampleValue, Index))
					Errors.Add(Prefix + TEXT(" overlaps another sample"));
				if (!BlendSpace->ValidateSampleValue(Sample.SampleValue, Index))
					Warnings.Add(Prefix + TEXT(" failed an editor sample check"));
			}
			if (!FMath::IsFinite(Sample.RateScale) || Sample.RateScale <= 0)
				Errors.Add(Prefix + TEXT(" has an invalid rate scale"));
		}
		const FBlendSpaceData& Data = BlendSpace->GetBlendSpaceData();
		if (Samples.Num() > 1 && Data.IsEmpty()) Errors.Add(TEXT("Blend Space interpolation data is empty; rebuild is required"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("asset_path"), BlendSpace->GetPathName());
		Writer->WriteValue(TEXT("axis_count"), AxisCount);
		Writer->WriteValue(TEXT("sample_count"), Samples.Num());
		Writer->WriteValue(TEXT("segments"), Data.Segments.Num());
		Writer->WriteValue(TEXT("triangles"), Data.Triangles.Num());
		Writer->WriteArrayStart(TEXT("errors"));
		for (const FString& Error : Errors) Writer->WriteValue(Error);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings"));
		for (const FString& Warning : Warnings) Writer->WriteValue(Warning);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/blend-spaces/samples", [](const FHttpContext<FBlendSpaceReq, FString>& C)
	{
		const FBlendSpaceReq Body = C.RequestBody();
		UBlendSpace* BlendSpace = Cast<UBlendSpace>(LoadAsset(Body.AssetPath));
		if (!BlendSpace) throw std::runtime_error("Asset is not a Blend Space");
		if (Body.SampleValue.ContainsNaN()) throw std::runtime_error("sample_value must be finite");
		const bool bAdd = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
		const bool bUpdate = Body.Operation.Equals(TEXT("update"), ESearchCase::IgnoreCase);
		const bool bMove = Body.Operation.Equals(TEXT("move"), ESearchCase::IgnoreCase);
		const bool bDelete = Body.Operation.Equals(TEXT("delete"), ESearchCase::IgnoreCase);
		if (!bAdd && !bUpdate && !bMove && !bDelete) throw std::runtime_error("operation must be add, update, move, or delete");
		if ((bAdd || bMove) && (FMath::Abs(Body.SampleValue.Z) > KINDA_SMALL_NUMBER
			|| (BlendSpace->IsA<UBlendSpace1D>() && FMath::Abs(Body.SampleValue.Y) > KINDA_SMALL_NUMBER)))
			throw std::runtime_error("sample_value has a nonzero coordinate outside the Blend Space dimensions");
		UAnimSequence* Sequence = nullptr;
		if (bAdd || bUpdate)
		{
			Sequence = Cast<UAnimSequence>(LoadAsset(Body.AnimationPath));
			if (!Sequence || !Sequence->GetSkeleton() || !BlendSpace->GetSkeleton()
				|| !BlendSpace->GetSkeleton()->IsCompatibleForEditor(Sequence->GetSkeleton()))
				throw std::runtime_error("animation_path must be an Animation Sequence compatible with the Blend Space Skeleton");
		}
		int32 Index = Body.SampleIndex;
		TArray<FGuid> Ids = ResolveBlendSampleIds(BlendSpace);
		if (!Body.SampleId.IsEmpty())
		{
			if (bAdd) throw std::runtime_error("sample_id cannot be supplied when adding a sample");
			FGuid RequestedId;
			if (!FGuid::Parse(Body.SampleId, RequestedId) || !RequestedId.IsValid()) throw std::runtime_error("sample_id is invalid");
			const int32 ResolvedIndex = Ids.IndexOfByKey(RequestedId);
			if (ResolvedIndex == INDEX_NONE) throw std::runtime_error("sample_id does not identify a current sample");
			if (Index != INDEX_NONE && Index != ResolvedIndex) throw std::runtime_error("sample_id and sample_index identify different samples");
			Index = ResolvedIndex;
		}
		if (bUpdate && Index == INDEX_NONE)
		{
			for (int32 Candidate = 0; Candidate < BlendSpace->GetNumberOfBlendSamples(); ++Candidate)
				if (BlendSpace->GetBlendSample(Candidate).SampleValue.Equals(Body.SampleValue, KINDA_SMALL_NUMBER))
				{
					if (Index != INDEX_NONE) throw std::runtime_error("sample_value matches multiple samples; provide sample_index");
					Index = Candidate;
				}
		}
		if ((bUpdate || bMove || bDelete) && (Index < 0 || Index >= BlendSpace->GetNumberOfBlendSamples()))
			throw std::runtime_error("sample_index is invalid or sample_value did not identify a sample");
		if ((bAdd || bMove) && !BlendSpace->ValidateSampleValue(Body.SampleValue, bMove ? Index : INDEX_NONE))
			throw std::runtime_error("sample_value is out of range or duplicates another sample");
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"sample_index\":%d,\"sample_id\":\"%s\"}"),
				bAdd ? BlendSpace->GetNumberOfBlendSamples() : Index, bAdd ? TEXT("") : *Ids[Index].ToString(EGuidFormats::DigitsWithHyphens)), TEXT("application/json"));
		if (bDelete && !Body.bConfirm) throw std::runtime_error("Blend Space sample deletion requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditBlendSpaceSample", "Edit Blend Space Sample"));
		BlendSpace->Modify();
		if (bAdd)
		{
			Index = BlendSpace->AddSample(Sequence, Body.SampleValue);
			if (Index == INDEX_NONE) throw std::runtime_error("failed to add Blend Space sample");
			Ids.Insert(FGuid::NewGuid(), Index);
		}
		else if (bUpdate && !BlendSpace->ReplaceSampleAnimation(Index, Sequence)) throw std::runtime_error("failed to update Blend Space sample");
		else if (bMove && !BlendSpace->EditSampleValue(Index, Body.SampleValue)) throw std::runtime_error("failed to move Blend Space sample");
		else if (bDelete && !BlendSpace->DeleteSample(Index)) throw std::runtime_error("failed to delete Blend Space sample");
		const FGuid ResultId = Ids[Index];
		if (bDelete) Ids.RemoveAt(Index);
		PersistBlendSampleIds(BlendSpace, Ids);
		MarkAssetDirty(BlendSpace);
		SaveIfRequested(BlendSpace, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":true,\"dry_run\":false,\"saved\":%s,\"sample_index\":%d,\"sample_id\":\"%s\"}"),
			Body.bSave ? TEXT("true") : TEXT("false"), Index, *ResultId.ToString(EGuidFormats::DigitsWithHyphens)), TEXT("application/json"));
	});

	App->Get("/physics-assets/inspect", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* PhysicsAsset = Cast<UPhysicsAsset>(LoadAsset(C.Query("asset_path")));
		if (!PhysicsAsset)
			throw std::runtime_error("Asset is not a Physics Asset");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(PhysicsAsset), TEXT("application/json"));
	});

	App->Get("/physics-assets/bodies", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* PhysicsAsset = Cast<UPhysicsAsset>(LoadAsset(C.Query("asset_path")));
		if (!PhysicsAsset)
			throw std::runtime_error("Asset is not a Physics Asset");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		for (int32 Index = 0; Index < PhysicsAsset->SkeletalBodySetups.Num(); ++Index)
		{
			const USkeletalBodySetup* Body = PhysicsAsset->SkeletalBodySetups[Index];
			if (!Body) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("index"), Index);
			Writer->WriteValue(TEXT("bone"), Body->BoneName.ToString());
			Writer->WriteValue(TEXT("sphere_count"), Body->AggGeom.SphereElems.Num());
			Writer->WriteValue(TEXT("box_count"), Body->AggGeom.BoxElems.Num());
			Writer->WriteValue(TEXT("sphyl_count"), Body->AggGeom.SphylElems.Num());
			Writer->WriteValue(TEXT("convex_count"), Body->AggGeom.ConvexElems.Num());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/physics-assets/body-settings", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		USkeletalBodySetup* Setup = Asset->SkeletalBodySetups[FindPhysicsBody(Asset, C.Query("bone_name"))];
		return C.TextResponse(PhysicsBodySettingsJson(Setup, false, false, false), TEXT("application/json"));
	});

	App->Patch("/physics-assets/body-settings", [](const FHttpContext<FPhysicsBodySettingsReq, FString>& C)
	{
		const FPhysicsBodySettingsReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		USkeletalBodySetup* Setup = Asset->SkeletalBodySetups[FindPhysicsBody(Asset, Body.BoneName)];
		if (Body.Settings.IsEmpty()) throw std::runtime_error("settings must contain a body setting");
		USkeletalBodySetup* Probe = DuplicateObject<USkeletalBodySetup>(Setup, GetTransientPackage());
		if (!Probe) throw std::runtime_error("body setup could not be duplicated for preflight");
		Probe->SetFlags(RF_Transient);
		ApplyPhysicsBodySettings(Probe, Body.Settings);
		if (Body.bDryRun) return C.TextResponse(PhysicsBodySettingsJson(Probe, false, true, false), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditPhysicsBodySettings", "Edit Physics Asset Body Settings"));
		Asset->Modify();
		Setup->Modify();
		ApplyPhysicsBodySettings(Setup, Body.Settings);
		Asset->UpdateBoundsBodiesArray();
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsBodySettingsJson(Setup, true, false, Body.bSave), TEXT("application/json"));
	});

	App->Post("/physics-assets/bodies", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		const FPhysicsAssetEditReq Body = C.RequestBody();
		if (!Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be add");
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		if (Body.BoneName.IsEmpty()) throw std::runtime_error("bone_name is required");
		if (Asset->FindBodyIndex(FName(*Body.BoneName)) != INDEX_NONE) throw std::runtime_error("a body already exists for bone_name");
		USkeletalMesh* Mesh = Body.SkeletalMeshPath.IsEmpty() ? Asset->GetPreviewMesh() : Cast<USkeletalMesh>(LoadAsset(Body.SkeletalMeshPath));
		if (!Mesh || Mesh->GetRefSkeleton().FindBoneIndex(FName(*Body.BoneName)) == INDEX_NONE)
			throw std::runtime_error("bone_name must exist in the Physics Asset preview mesh or skeletal_mesh_path");
		ValidatePhysicsShape(Body);
		if (Body.bDryRun) return C.TextResponse(PhysicsEditJson(Asset, false, true, false, Body.BoneName, Body.ShapeType, 0), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddPhysicsBody", "Add Physics Asset Body"));
		Asset->Modify();
		FPhysAssetCreateParams Params;
		Params.bCreateConstraints = false;
		const int32 BodyIndex = FPhysicsAssetUtils::CreateNewBody(Asset, FName(*Body.BoneName), Params);
		if (!Asset->SkeletalBodySetups.IsValidIndex(BodyIndex) || !Asset->SkeletalBodySetups[BodyIndex])
			throw std::runtime_error("failed to create Physics Asset body");
		Asset->SkeletalBodySetups[BodyIndex]->Modify();
		const int32 ShapeIndex = AddPhysicsShape(Asset, BodyIndex, Body);
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsEditJson(Asset, true, false, Body.bSave, Body.BoneName, Body.ShapeType, ShapeIndex), TEXT("application/json"));
	});

	App->Delete("/physics-assets/bodies", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		const FPhysicsAssetEditReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 BodyIndex = FindPhysicsBody(Asset, Body.BoneName);
		TArray<int32> ConstraintIndices;
		Asset->BodyFindConstraints(BodyIndex, ConstraintIndices);
		TArray<FString> AffectedConstraints;
		for (int32 Index : ConstraintIndices)
			if (Asset->ConstraintSetup.IsValidIndex(Index) && Asset->ConstraintSetup[Index])
				AffectedConstraints.Add(Asset->ConstraintSetup[Index]->DefaultInstance.JointName.ToString());
		TArray<FString> AffectedCollisionPairs;
		for (int32 Index = 0; Index < Asset->SkeletalBodySetups.Num(); ++Index)
			if (Index != BodyIndex && Asset->SkeletalBodySetups[Index] && !Asset->IsCollisionEnabled(BodyIndex, Index))
				AffectedCollisionPairs.Add(Asset->SkeletalBodySetups[Index]->BoneName.ToString());
		AffectedConstraints.Sort();
		AffectedCollisionPairs.Sort();
		if (Body.bDryRun) return C.TextResponse(PhysicsEditJson(Asset, false, true, false, Body.BoneName, TEXT(""), -1,
			AffectedConstraints, AffectedCollisionPairs), TEXT("application/json"));
		if (!Body.bConfirm) throw std::runtime_error("body deletion requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemovePhysicsBody", "Remove Physics Asset Body"));
		Asset->Modify();
		FPhysicsAssetUtils::DestroyBody(Asset, BodyIndex);
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsEditJson(Asset, true, false, Body.bSave, Body.BoneName, TEXT(""), -1,
			AffectedConstraints, AffectedCollisionPairs), TEXT("application/json"));
	});

	App->Get("/physics-assets/shapes", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		const int32 BodyIndex = FindPhysicsBody(Asset, C.Query("bone_name"));
		const USkeletalBodySetup* Body = Asset->SkeletalBodySetups[BodyIndex];
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("bone_name"), Body->BoneName.ToString());
		Writer->WriteArrayStart(TEXT("shapes"));
		auto WriteCommon = [&Writer, Asset, BodyIndex](const TCHAR* Type, int32 Index, EAggCollisionShape::Type Shape)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("shape_type"), Type);
			Writer->WriteValue(TEXT("shape_index"), Index);
			Writer->WriteValue(TEXT("collision_enabled"), Asset->GetPrimitiveCollision(BodyIndex, Shape, Index) != ECollisionEnabled::NoCollision);
			Writer->WriteValue(TEXT("contributes_to_mass"), Asset->GetPrimitiveContributeToMass(BodyIndex, Shape, Index));
		};
		for (int32 Index = 0; Index < Body->AggGeom.SphereElems.Num(); ++Index)
		{
			const FKSphereElem& Shape = Body->AggGeom.SphereElems[Index];
			WriteCommon(TEXT("sphere"), Index, EAggCollisionShape::Sphere);
			Writer->WriteValue(TEXT("radius"), Shape.Radius);
			Writer->WriteValue(TEXT("center"), Shape.Center.ToString());
			Writer->WriteObjectEnd();
		}
		for (int32 Index = 0; Index < Body->AggGeom.BoxElems.Num(); ++Index)
		{
			const FKBoxElem& Shape = Body->AggGeom.BoxElems[Index];
			WriteCommon(TEXT("box"), Index, EAggCollisionShape::Box);
			Writer->WriteValue(TEXT("size"), FVector(Shape.X, Shape.Y, Shape.Z).ToString());
			Writer->WriteValue(TEXT("center"), Shape.Center.ToString());
			Writer->WriteValue(TEXT("rotation"), Shape.Rotation.ToString());
			Writer->WriteObjectEnd();
		}
		for (int32 Index = 0; Index < Body->AggGeom.SphylElems.Num(); ++Index)
		{
			const FKSphylElem& Shape = Body->AggGeom.SphylElems[Index];
			WriteCommon(TEXT("capsule"), Index, EAggCollisionShape::Sphyl);
			Writer->WriteValue(TEXT("radius"), Shape.Radius);
			Writer->WriteValue(TEXT("length"), Shape.Length);
			Writer->WriteValue(TEXT("center"), Shape.Center.ToString());
			Writer->WriteValue(TEXT("rotation"), Shape.Rotation.ToString());
			Writer->WriteObjectEnd();
		}
		for (int32 Index = 0; Index < Body->AggGeom.ConvexElems.Num(); ++Index)
		{
			const FKConvexElem& Shape = Body->AggGeom.ConvexElems[Index];
			WriteCommon(TEXT("convex"), Index, EAggCollisionShape::Convex);
			Writer->WriteValue(TEXT("vertex_count"), Shape.VertexData.Num());
			Writer->WriteArrayStart(TEXT("vertices"));
			for (const FVector& Vertex : Shape.VertexData)
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("x"), Vertex.X);
				Writer->WriteValue(TEXT("y"), Vertex.Y);
				Writer->WriteValue(TEXT("z"), Vertex.Z);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteValue(TEXT("center"), Shape.GetTransform().GetTranslation().ToString());
			Writer->WriteValue(TEXT("rotation"), Shape.GetTransform().Rotator().ToString());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/physics-assets/shapes", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		const FPhysicsAssetEditReq Body = C.RequestBody();
		if (!Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be add");
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 BodyIndex = FindPhysicsBody(Asset, Body.BoneName);
		ValidatePhysicsShape(Body);
		const USkeletalBodySetup* Setup = Asset->SkeletalBodySetups[BodyIndex];
		const EAggCollisionShape::Type Type = PhysicsShapeType(Body.ShapeType);
		const int32 PredictedIndex = Type == EAggCollisionShape::Sphere ? Setup->AggGeom.SphereElems.Num()
			: Type == EAggCollisionShape::Box ? Setup->AggGeom.BoxElems.Num()
			: Type == EAggCollisionShape::Sphyl ? Setup->AggGeom.SphylElems.Num() : Setup->AggGeom.ConvexElems.Num();
		if (Body.bDryRun) return C.TextResponse(PhysicsEditJson(Asset, false, true, false, Body.BoneName, Body.ShapeType, PredictedIndex), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddPhysicsShape", "Add Physics Asset Shape"));
		Asset->Modify();
		Asset->SkeletalBodySetups[BodyIndex]->Modify();
		const int32 ShapeIndex = AddPhysicsShape(Asset, BodyIndex, Body);
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsEditJson(Asset, true, false, Body.bSave, Body.BoneName, Body.ShapeType, ShapeIndex), TEXT("application/json"));
	});

	App->Patch("/physics-assets/shapes", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		const FPhysicsAssetEditReq Body = C.RequestBody();
		if (!Body.Operation.Equals(TEXT("replace_vertices"), ESearchCase::IgnoreCase))
			throw std::runtime_error("operation must be replace_vertices");
		if (!Body.ShapeType.Equals(TEXT("convex"), ESearchCase::IgnoreCase))
			throw std::runtime_error("replace_vertices only supports shape_type convex");
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 BodyIndex = FindPhysicsBody(Asset, Body.BoneName);
		USkeletalBodySetup* Setup = Asset->SkeletalBodySetups[BodyIndex];
		if (Body.ShapeIndex < 0 || Body.ShapeIndex >= Setup->AggGeom.ConvexElems.Num())
			throw std::runtime_error("shape_index does not identify a convex shape");

		const FKConvexElem& Existing = Setup->AggGeom.ConvexElems[Body.ShapeIndex];
		const FTransform ExistingTransform = Existing.GetTransform();
		FPhysicsAssetEditReq Validation = Body;
		Validation.Center = ExistingTransform.GetTranslation();
		Validation.Rotation = ExistingTransform.Rotator();
		ValidatePhysicsShape(Validation);

		USkeletalBodySetup* Probe = DuplicateObject<USkeletalBodySetup>(Setup, GetTransientPackage());
		FKConvexElem& ProbeShape = Probe->AggGeom.ConvexElems[Body.ShapeIndex];
		ProbeShape.VertexData = Body.Vertices;
		ProbeShape.UpdateElemBox();
		Probe->InvalidatePhysicsData();
		Probe->CreatePhysicsMeshes();
		if (Probe->bFailedToCreatePhysicsMeshes || !ProbeShape.GetChaosConvexMesh())
			throw std::runtime_error("Chaos could not cook the replacement convex topology with the body's other shapes");

		if (Body.bDryRun)
			return C.TextResponse(PhysicsEditJson(Asset, false, true, false, Body.BoneName, Body.ShapeType, Body.ShapeIndex), TEXT("application/json"));

		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "ReplacePhysicsConvexVertices", "Replace Physics Asset Convex Vertices"));
		Asset->Modify();
		Setup->Modify();
		FKConvexElem& Shape = Setup->AggGeom.ConvexElems[Body.ShapeIndex];
		Shape.VertexData = Body.Vertices;
		Shape.UpdateElemBox();
		Setup->InvalidatePhysicsData();
		Setup->CreatePhysicsMeshes();
		if (Setup->bFailedToCreatePhysicsMeshes || !Shape.GetChaosConvexMesh())
			throw std::runtime_error("Physics body failed to rebuild after replacing convex topology");
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsEditJson(Asset, true, false, Body.bSave, Body.BoneName, Body.ShapeType, Body.ShapeIndex), TEXT("application/json"));
	});

	App->Delete("/physics-assets/shapes", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		const FPhysicsAssetEditReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 BodyIndex = FindPhysicsBody(Asset, Body.BoneName);
		USkeletalBodySetup* Setup = Asset->SkeletalBodySetups[BodyIndex];
		const EAggCollisionShape::Type Type = PhysicsShapeType(Body.ShapeType);
		const int32 Count = Type == EAggCollisionShape::Sphere ? Setup->AggGeom.SphereElems.Num()
			: Type == EAggCollisionShape::Box ? Setup->AggGeom.BoxElems.Num()
			: Type == EAggCollisionShape::Sphyl ? Setup->AggGeom.SphylElems.Num() : Setup->AggGeom.ConvexElems.Num();
		if (Body.ShapeIndex < 0 || Body.ShapeIndex >= Count) throw std::runtime_error("shape_index is invalid");
		if (PhysicsShapeCount(Setup) <= 1) throw std::runtime_error("deleting the last shape requires deleting the body instead");
		if (Body.bDryRun) return C.TextResponse(PhysicsEditJson(Asset, false, true, false, Body.BoneName, Body.ShapeType, Body.ShapeIndex), TEXT("application/json"));
		if (!Body.bConfirm) throw std::runtime_error("shape deletion requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemovePhysicsShape", "Remove Physics Asset Shape"));
		Asset->Modify(); Setup->Modify();
		if (Type == EAggCollisionShape::Sphere) Setup->AggGeom.SphereElems.RemoveAt(Body.ShapeIndex);
		else if (Type == EAggCollisionShape::Box) Setup->AggGeom.BoxElems.RemoveAt(Body.ShapeIndex);
		else if (Type == EAggCollisionShape::Sphyl) Setup->AggGeom.SphylElems.RemoveAt(Body.ShapeIndex);
		else Setup->AggGeom.ConvexElems.RemoveAt(Body.ShapeIndex);
		Setup->InvalidatePhysicsData();
		if (Type == EAggCollisionShape::Convex) Setup->CreatePhysicsMeshes();
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsEditJson(Asset, true, false, Body.bSave, Body.BoneName, Body.ShapeType, Body.ShapeIndex), TEXT("application/json"));
	});

	App->Get("/physics-assets/constraints", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("constraints"));
		for (int32 Index = 0; Index < Asset->ConstraintSetup.Num(); ++Index)
		{
			const UPhysicsConstraintTemplate* Constraint = Asset->ConstraintSetup[Index];
			if (!Constraint) continue;
			const FConstraintInstance& Instance = Constraint->DefaultInstance;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("index"), Index);
			Writer->WriteValue(TEXT("name"), Instance.JointName.ToString());
			Writer->WriteValue(TEXT("child_bone"), Instance.ConstraintBone1.ToString());
			Writer->WriteValue(TEXT("parent_bone"), Instance.ConstraintBone2.ToString());
			Writer->WriteValue(TEXT("linear_limit"), Instance.GetLinearLimit());
			Writer->WriteValue(TEXT("swing1_limit"), Instance.GetAngularSwing1Limit());
			Writer->WriteValue(TEXT("swing2_limit"), Instance.GetAngularSwing2Limit());
			Writer->WriteValue(TEXT("twist_limit"), Instance.GetAngularTwistLimit());
			Writer->WriteValue(TEXT("projection_enabled"), Instance.IsProjectionEnabled());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd(); Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/physics-assets/body-profiles", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		const FString BoneName = C.Query("bone_name");
		const USkeletalBodySetup* Selected = nullptr;
		if (!BoneName.IsEmpty()) Selected = Asset->SkeletalBodySetups[FindPhysicsBody(Asset, BoneName)];
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("current"), Asset->CurrentPhysicalAnimationProfileName.ToString());
		Writer->WriteArrayStart(TEXT("profiles"));
		for (const FName Name : Asset->GetPhysicalAnimationProfileNames())
		{
			int32 Covered = 0;
			for (const USkeletalBodySetup* Body : Asset->SkeletalBodySetups)
				if (Body && Body->FindPhysicalAnimationProfile(Name)) ++Covered;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Name.ToString());
			Writer->WriteValue(TEXT("body_count"), Covered);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		if (Selected)
		{
			Writer->WriteValue(TEXT("bone_name"), Selected->BoneName.ToString());
			Writer->WriteArrayStart(TEXT("body_profiles"));
			for (const FPhysicalAnimationProfile& Profile : Selected->GetPhysicalAnimationProfiles())
			{
				const FPhysicalAnimationData& Data = Profile.PhysicalAnimationData;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Profile.ProfileName.ToString());
				Writer->WriteValue(TEXT("local_simulation"), static_cast<bool>(Data.bIsLocalSimulation));
				Writer->WriteValue(TEXT("orientation_strength"), Data.OrientationStrength);
				Writer->WriteValue(TEXT("angular_velocity_strength"), Data.AngularVelocityStrength);
				Writer->WriteValue(TEXT("position_strength"), Data.PositionStrength);
				Writer->WriteValue(TEXT("velocity_strength"), Data.VelocityStrength);
				Writer->WriteValue(TEXT("max_linear_force"), Data.MaxLinearForce);
				Writer->WriteValue(TEXT("max_angular_force"), Data.MaxAngularForce);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
		}
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/physics-assets/body-profiles", [](const FHttpContext<FPhysicsBodyProfileReq, FString>& C)
	{
		const FPhysicsBodyProfileReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const bool bAdd = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
		const bool bDuplicate = Body.Operation.Equals(TEXT("duplicate"), ESearchCase::IgnoreCase);
		const bool bRename = Body.Operation.Equals(TEXT("rename"), ESearchCase::IgnoreCase);
		const bool bDelete = Body.Operation.Equals(TEXT("delete"), ESearchCase::IgnoreCase);
		const bool bEdit = Body.Operation.Equals(TEXT("edit"), ESearchCase::IgnoreCase);
		if (!bAdd && !bDuplicate && !bRename && !bDelete && !bEdit)
			throw std::runtime_error("operation must be add, duplicate, rename, delete, or edit");
		if (Body.ProfileName.IsEmpty() || Body.ProfileName.Equals(TEXT("None"), ESearchCase::IgnoreCase))
			throw std::runtime_error("profile_name is required");
		const FName Name(*Body.ProfileName);
		const bool bExists = Asset->PhysicalAnimationProfiles.Contains(Name);
		const FName SourceName(*Body.SourceProfileName);
		const FName NewName(*Body.NewName);
		if (bAdd && bExists) throw std::runtime_error("profile_name already exists");
		if (!bAdd && !bDuplicate && !bExists) throw std::runtime_error("profile_name does not exist");
		if (bDuplicate && (!Asset->PhysicalAnimationProfiles.Contains(SourceName) || bExists))
			throw std::runtime_error("source_profile_name must exist and profile_name must be new");
		if (bRename && (NewName.IsNone() || Asset->PhysicalAnimationProfiles.Contains(NewName)))
			throw std::runtime_error("new_name must be a new profile name");
		USkeletalBodySetup* Selected = nullptr;
		if (bEdit)
		{
			Selected = Asset->SkeletalBodySetups[FindPhysicsBody(Asset, Body.BoneName)];
			if (!Selected || !Selected->FindPhysicalAnimationProfile(Name))
				throw std::runtime_error("body does not contain profile_name");
			for (float Value : {Body.OrientationStrength, Body.AngularVelocityStrength,
				Body.PositionStrength, Body.VelocityStrength, Body.MaxLinearForce, Body.MaxAngularForce})
				if (!FMath::IsFinite(Value) || Value < 0.f)
					throw std::runtime_error("physical animation strengths and force limits must be finite and nonnegative");
		}
		TArray<FString> Affected;
		for (const USkeletalBodySetup* Setup : Asset->SkeletalBodySetups)
		{
			if (!Setup || (bEdit && Setup != Selected)) continue;
			if (bDuplicate && !Setup->FindPhysicalAnimationProfile(SourceName))
				throw std::runtime_error("source profile is missing from a body");
			Affected.Add(Setup->BoneName.ToString());
		}
		auto Response = [&](bool bChanged, bool bDryRun, bool bSaved)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("changed"), bChanged);
			Writer->WriteValue(TEXT("dry_run"), bDryRun);
			Writer->WriteValue(TEXT("saved"), bSaved);
			Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
			Writer->WriteValue(TEXT("profile_name"), Body.ProfileName);
			Writer->WriteArrayStart(TEXT("affected_bodies"));
			for (const FString& Bone : Affected) Writer->WriteValue(Bone);
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
			Writer->Close();
			return Json;
		};
		if (Body.bDryRun) return C.TextResponse(Response(false, true, false), TEXT("application/json"));
		if (bDelete && !Body.bConfirm) throw std::runtime_error("body profile deletion requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditPhysicalAnimationProfile", "Edit Physical Animation Profile"));
		Asset->Modify();
		for (USkeletalBodySetup* Setup : Asset->SkeletalBodySetups)
		{
			if (!Setup || (bEdit && Setup != Selected)) continue;
			Setup->Modify();
			if (bAdd)
			{
				Setup->AddPhysicalAnimationProfile(Name);
				if (FPhysicalAnimationProfile* Profile = Setup->FindPhysicalAnimationProfile(Name))
					Profile->PhysicalAnimationData.BodyName = Setup->BoneName;
			}
			else if (bDuplicate) Setup->DuplicatePhysicalAnimationProfile(SourceName, Name);
			else if (bRename) Setup->RenamePhysicalAnimationProfile(Name, NewName);
			else if (bDelete) Setup->RemovePhysicalAnimationProfile(Name);
			else if (FPhysicalAnimationProfile* Profile = Setup->FindPhysicalAnimationProfile(Name))
			{
				FPhysicalAnimationData& Data = Profile->PhysicalAnimationData;
				Data.BodyName = Setup->BoneName;
				Data.bIsLocalSimulation = Body.bLocalSimulation;
				Data.OrientationStrength = Body.OrientationStrength;
				Data.AngularVelocityStrength = Body.AngularVelocityStrength;
				Data.PositionStrength = Body.PositionStrength;
				Data.VelocityStrength = Body.VelocityStrength;
				Data.MaxLinearForce = Body.MaxLinearForce;
				Data.MaxAngularForce = Body.MaxAngularForce;
			}
		}
		if (bAdd || bDuplicate) Asset->PhysicalAnimationProfiles.Add(Name);
		else if (bRename)
		{
			Asset->PhysicalAnimationProfiles[Asset->PhysicalAnimationProfiles.IndexOfByKey(Name)] = NewName;
			if (Asset->CurrentPhysicalAnimationProfileName == Name) Asset->CurrentPhysicalAnimationProfileName = NewName;
		}
		else if (bDelete)
		{
			Asset->PhysicalAnimationProfiles.Remove(Name);
			if (Asset->CurrentPhysicalAnimationProfileName == Name) Asset->CurrentPhysicalAnimationProfileName = NAME_None;
		}
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(Response(true, false, Body.bSave), TEXT("application/json"));
	});

	App->Get("/physics-assets/profiles", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("current"), Asset->CurrentConstraintProfileName.ToString());
		Writer->WriteArrayStart(TEXT("profiles"));
		for (const FName ProfileName : Asset->GetConstraintProfileNames())
		{
			int32 Covered = 0;
			for (const UPhysicsConstraintTemplate* Constraint : Asset->ConstraintSetup)
				if (Constraint && Constraint->ContainsConstraintProfile(ProfileName)) ++Covered;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), ProfileName.ToString());
			Writer->WriteValue(TEXT("constraint_count"), Covered);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		const FString ConstraintName = C.Query("constraint_name");
		if (!ConstraintName.IsEmpty())
		{
			const int32 Index = Asset->FindConstraintIndex(FName(*ConstraintName));
			if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index])
				throw std::runtime_error("constraint_name was not found");
			Writer->WriteArrayStart(TEXT("constraint_profiles"));
			for (const FPhysicsConstraintProfileHandle& Handle : Asset->ConstraintSetup[Index]->ProfileHandles)
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Handle.ProfileName.ToString());
				Writer->WriteValue(TEXT("linear_stiffness_x"), Handle.ProfileProperties.LinearDrive.XDrive.Stiffness);
				Writer->WriteValue(TEXT("angular_stiffness_slerp"), Handle.ProfileProperties.AngularDrive.SlerpDrive.Stiffness);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
		}
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/physics-assets/profiles", [](const FHttpContext<FPhysicsProfileReq, FString>& C)
	{
		const FPhysicsProfileReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const bool bAdd = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
		const bool bDuplicate = Body.Operation.Equals(TEXT("duplicate"), ESearchCase::IgnoreCase);
		const bool bRename = Body.Operation.Equals(TEXT("rename"), ESearchCase::IgnoreCase);
		const bool bDelete = Body.Operation.Equals(TEXT("delete"), ESearchCase::IgnoreCase);
		const bool bCapture = Body.Operation.Equals(TEXT("capture"), ESearchCase::IgnoreCase);
		if (!bAdd && !bDuplicate && !bRename && !bDelete && !bCapture)
			throw std::runtime_error("operation must be add, duplicate, rename, delete, or capture");
		if (Body.ProfileName.IsEmpty() || Body.ProfileName.Equals(TEXT("None"), ESearchCase::IgnoreCase))
			throw std::runtime_error("profile_name is required");
		const FName Name(*Body.ProfileName);
		const bool bExists = Asset->ConstraintProfiles.Contains(Name);
		const FName NewName(*Body.NewName);
		const FName SourceName(*Body.SourceProfileName);
		if (bAdd && bExists) throw std::runtime_error("profile_name already exists");
		if (!bAdd && !bDuplicate && !bExists) throw std::runtime_error("profile_name does not exist");
		if (bDuplicate && (!Asset->ConstraintProfiles.Contains(SourceName) || bExists))
			throw std::runtime_error("source_profile_name must exist and profile_name must be new");
		if (bRename && (NewName.IsNone() || Asset->ConstraintProfiles.Contains(NewName)))
			throw std::runtime_error("new_name must be a new profile name");
		UPhysicsConstraintTemplate* Selected = nullptr;
		if (bCapture)
		{
			const int32 Index = Asset->FindConstraintIndex(FName(*Body.ConstraintName));
			if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index])
				throw std::runtime_error("constraint_name was not found");
			Selected = Asset->ConstraintSetup[Index];
			if (!Selected->ContainsConstraintProfile(Name)) throw std::runtime_error("constraint does not contain profile_name");
		}
		TArray<FString> Affected;
		for (const UPhysicsConstraintTemplate* Constraint : Asset->ConstraintSetup)
		{
			if (!Constraint || (bCapture && Constraint != Selected)) continue;
			if (bDuplicate && !Constraint->ContainsConstraintProfile(SourceName))
				throw std::runtime_error("source profile is missing from a constraint");
			Affected.Add(Constraint->DefaultInstance.JointName.ToString());
		}
		auto Response = [&](bool bChanged, bool bDryRun, bool bSaved)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("changed"), bChanged);
			Writer->WriteValue(TEXT("dry_run"), bDryRun);
			Writer->WriteValue(TEXT("saved"), bSaved);
			Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
			Writer->WriteValue(TEXT("profile_name"), Body.ProfileName);
			Writer->WriteArrayStart(TEXT("affected_constraints"));
			for (const FString& ConstraintName : Affected) Writer->WriteValue(ConstraintName);
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
			Writer->Close();
			return Json;
		};
		if (Body.bDryRun) return C.TextResponse(Response(false, true, false), TEXT("application/json"));
		if (bDelete && !Body.bConfirm) throw std::runtime_error("constraint profile deletion requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditPhysicsConstraintProfile", "Edit Physics Constraint Profile"));
		Asset->Modify();
		for (UPhysicsConstraintTemplate* Constraint : Asset->ConstraintSetup)
		{
			if (!Constraint || (bCapture && Constraint != Selected)) continue;
			Constraint->Modify();
			if (bAdd) Constraint->AddConstraintProfile(Name);
			else if (bDuplicate) Constraint->DuplicateConstraintProfile(SourceName, Name);
			else if (bRename) Constraint->RenameConstraintProfile(Name, NewName);
			else if (bDelete) Constraint->RemoveConstraintProfile(Name);
			else
				for (FPhysicsConstraintProfileHandle& Handle : Constraint->ProfileHandles)
					if (Handle.ProfileName == Name) { Handle.ProfileProperties = Constraint->DefaultInstance.ProfileInstance; break; }
		}
		if (bAdd || bDuplicate) Asset->ConstraintProfiles.Add(Name);
		else if (bRename)
		{
			Asset->ConstraintProfiles[Asset->ConstraintProfiles.IndexOfByKey(Name)] = NewName;
			if (Asset->CurrentConstraintProfileName == Name) Asset->CurrentConstraintProfileName = NewName;
		}
		else if (bDelete)
		{
			Asset->ConstraintProfiles.Remove(Name);
			if (Asset->CurrentConstraintProfileName == Name) Asset->CurrentConstraintProfileName = NAME_None;
		}
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(Response(true, false, Body.bSave), TEXT("application/json"));
	});

	App->Get("/physics-assets/drives", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		const int32 Index = Asset->FindConstraintIndex(FName(*C.Query("constraint_name")));
		if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index])
			throw std::runtime_error("constraint_name was not found");
		return C.TextResponse(PhysicsDriveJson(Asset, Asset->ConstraintSetup[Index], false, false, false), TEXT("application/json"));
	});

	App->Patch("/physics-assets/drives", [](const FHttpContext<FPhysicsDriveReq, FString>& C)
	{
		const FPhysicsDriveReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 Index = Asset->FindConstraintIndex(FName(*Body.ConstraintName));
		if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index])
			throw std::runtime_error("constraint_name was not found");
		ValidatePhysicsDrive(Body);
		UPhysicsConstraintTemplate* Constraint = Asset->ConstraintSetup[Index];
		if (Body.bDryRun)
		{
			UPhysicsConstraintTemplate* Probe = DuplicateObject<UPhysicsConstraintTemplate>(Constraint, GetTransientPackage());
			if (!Probe) throw std::runtime_error("constraint could not be duplicated for drive preview");
			Probe->SetFlags(RF_Transient);
			ApplyPhysicsDrive(Probe->DefaultInstance, Body);
			return C.TextResponse(PhysicsDriveJson(Asset, Probe, false, true, false), TEXT("application/json"));
		}
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditPhysicsDrive", "Edit Physics Asset Drive"));
		Asset->Modify();
		Constraint->Modify();
		ApplyPhysicsDrive(Constraint->DefaultInstance, Body);
		Constraint->UpdateProfileInstance();
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsDriveJson(Asset, Constraint, true, false, Body.bSave), TEXT("application/json"));
	});

	App->Post("/physics-assets/constraints", [](const FHttpContext<FPhysicsConstraintReq, FString>& C)
	{
		const FPhysicsConstraintReq Body = C.RequestBody();
		if (!Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase)) throw std::runtime_error("operation must be add");
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		if (Body.ConstraintName.IsEmpty() || Body.ConstraintName.Equals(TEXT("None"), ESearchCase::IgnoreCase))
			throw std::runtime_error("constraint_name is required");
		if (Asset->FindConstraintIndex(FName(*Body.ConstraintName)) != INDEX_NONE)
			throw std::runtime_error("constraint_name already exists");
		const int32 Child = FindPhysicsBody(Asset, Body.ChildBone);
		const int32 Parent = FindPhysicsBody(Asset, Body.ParentBone);
		if (Child == Parent) throw std::runtime_error("constraint child and parent bodies must differ");
		for (const UPhysicsConstraintTemplate* Existing : Asset->ConstraintSetup)
			if (Existing && Existing->DefaultInstance.ConstraintBone1 == FName(*Body.ChildBone)
				&& Existing->DefaultInstance.ConstraintBone2 == FName(*Body.ParentBone))
				throw std::runtime_error("a constraint already connects these bodies in this direction");
		ValidatePhysicsConstraintSettings(Body);
		if (Body.bDryRun)
		{
			UPhysicsConstraintTemplate* Probe = NewObject<UPhysicsConstraintTemplate>(GetTransientPackage());
			Probe->DefaultInstance.JointName = FName(*Body.ConstraintName);
			Probe->DefaultInstance.ConstraintBone1 = FName(*Body.ChildBone);
			Probe->DefaultInstance.ConstraintBone2 = FName(*Body.ParentBone);
			ApplyPhysicsConstraintSettings(Probe->DefaultInstance, Body);
			return C.TextResponse(PhysicsConstraintJson(Asset, Probe, false, true, false), TEXT("application/json"));
		}
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddPhysicsConstraint", "Add Physics Asset Constraint"));
		Asset->Modify();
		const int32 Index = FPhysicsAssetUtils::CreateNewConstraint(Asset, FName(*Body.ConstraintName));
		if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index])
			throw std::runtime_error("failed to create Physics Asset constraint");
		UPhysicsConstraintTemplate* Constraint = Asset->ConstraintSetup[Index];
		Constraint->Modify();
		Constraint->DefaultInstance.ConstraintBone1 = FName(*Body.ChildBone);
		Constraint->DefaultInstance.ConstraintBone2 = FName(*Body.ParentBone);
		ApplyPhysicsConstraintSettings(Constraint->DefaultInstance, Body);
		Constraint->UpdateProfileInstance();
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsConstraintJson(Asset, Constraint, true, false, Body.bSave), TEXT("application/json"));
	});

	App->Patch("/physics-assets/constraints", [](const FHttpContext<FPhysicsConstraintReq, FString>& C)
	{
		const FPhysicsConstraintReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 Index = Asset->FindConstraintIndex(FName(*Body.ConstraintName));
		if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index]) throw std::runtime_error("constraint_name was not found");
		UPhysicsConstraintTemplate* Constraint = Asset->ConstraintSetup[Index];
		const bool bChangeBones = !Body.ChildBone.IsEmpty() || !Body.ParentBone.IsEmpty();
		if (bChangeBones)
		{
			if (Body.ChildBone.IsEmpty() || Body.ParentBone.IsEmpty()) throw std::runtime_error("both child_bone and parent_bone are required when changing bodies");
			if (FindPhysicsBody(Asset, Body.ChildBone) == FindPhysicsBody(Asset, Body.ParentBone))
				throw std::runtime_error("constraint child and parent bodies must differ");
			for (const UPhysicsConstraintTemplate* Existing : Asset->ConstraintSetup)
				if (Existing && Existing != Constraint && Existing->DefaultInstance.ConstraintBone1 == FName(*Body.ChildBone)
					&& Existing->DefaultInstance.ConstraintBone2 == FName(*Body.ParentBone))
					throw std::runtime_error("another constraint already connects these bodies in this direction");
		}
		ValidatePhysicsConstraintSettings(Body);
		if (!bChangeBones && Body.LinearMotion.IsEmpty() && Body.AngularMotion.IsEmpty()
			&& Body.LinearLimit == -1.f && Body.Swing1Limit == -1.f && Body.Swing2Limit == -1.f
			&& Body.TwistLimit == -1.f && Body.Projection.IsEmpty())
			throw std::runtime_error("no constraint changes were requested");
		if (Body.bDryRun) return C.TextResponse(PhysicsConstraintJson(Asset, Constraint, false, true, false), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditPhysicsConstraint", "Edit Physics Asset Constraint"));
		Asset->Modify(); Constraint->Modify();
		if (bChangeBones)
		{
			Constraint->DefaultInstance.ConstraintBone1 = FName(*Body.ChildBone);
			Constraint->DefaultInstance.ConstraintBone2 = FName(*Body.ParentBone);
		}
		ApplyPhysicsConstraintSettings(Constraint->DefaultInstance, Body);
		Constraint->UpdateProfileInstance();
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsConstraintJson(Asset, Constraint, true, false, Body.bSave), TEXT("application/json"));
	});

	App->Delete("/physics-assets/constraints", [](const FHttpContext<FPhysicsConstraintReq, FString>& C)
	{
		const FPhysicsConstraintReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 Index = Asset->FindConstraintIndex(FName(*Body.ConstraintName));
		if (!Asset->ConstraintSetup.IsValidIndex(Index) || !Asset->ConstraintSetup[Index]) throw std::runtime_error("constraint_name was not found");
		UPhysicsConstraintTemplate* Constraint = Asset->ConstraintSetup[Index];
		if (Body.bDryRun) return C.TextResponse(PhysicsConstraintJson(Asset, Constraint, false, true, false), TEXT("application/json"));
		if (!Body.bConfirm) throw std::runtime_error("constraint deletion requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemovePhysicsConstraint", "Remove Physics Asset Constraint"));
		Asset->Modify();
		FPhysicsAssetUtils::DestroyConstraint(Asset, Index);
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsConstraintJson(Asset, Constraint, true, false, Body.bSave), TEXT("application/json"));
	});

	App->Get("/physics-assets/collision-pairs", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("disabled_pairs"));
		for (int32 First = 0; First < Asset->SkeletalBodySetups.Num(); ++First)
			for (int32 Second = First + 1; Second < Asset->SkeletalBodySetups.Num(); ++Second)
				if (Asset->SkeletalBodySetups[First] && Asset->SkeletalBodySetups[Second] && !Asset->IsCollisionEnabled(First, Second))
				{
					Writer->WriteObjectStart();
					Writer->WriteValue(TEXT("bone_name"), Asset->SkeletalBodySetups[First]->BoneName.ToString());
					Writer->WriteValue(TEXT("other_bone_name"), Asset->SkeletalBodySetups[Second]->BoneName.ToString());
					Writer->WriteObjectEnd();
				}
		Writer->WriteArrayEnd(); Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/physics-assets/collision-pairs", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		const FPhysicsAssetEditReq Body = C.RequestBody();
		UPhysicsAsset* Asset = LoadPhysicsAsset(Body.AssetPath);
		const int32 First = FindPhysicsBody(Asset, Body.BoneName);
		const int32 Second = FindPhysicsBody(Asset, Body.OtherBoneName);
		if (First == Second) throw std::runtime_error("collision pair bodies must be different");
		TArray<FString> Pair {Body.OtherBoneName};
		const bool bCurrent = Asset->IsCollisionEnabled(First, Second);
		if (Body.bDryRun || bCurrent == Body.bEnableCollision)
			return C.TextResponse(PhysicsEditJson(Asset, false, Body.bDryRun, false, Body.BoneName, TEXT(""), -1, {}, Pair), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditPhysicsCollisionPair", "Edit Physics Asset Collision Pair"));
		Asset->Modify();
		if (Body.bEnableCollision) Asset->EnableCollision(First, Second);
		else Asset->DisableCollision(First, Second);
		Asset->RefreshPhysicsAssetChange();
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(PhysicsEditJson(Asset, true, false, Body.bSave, Body.BoneName, TEXT(""), -1, {}, Pair), TEXT("application/json"));
	});

	App->Get("/physics-assets/validate", [](const FHttpContext<void, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.Query("asset_path"));
		const bool bIncludeRuntimeCook = C.Query("include_runtime_cook").Equals(TEXT("true"), ESearchCase::IgnoreCase);
		const bool bIncludeStabilityTest = C.Query("include_stability_test").Equals(TEXT("true"), ESearchCase::IgnoreCase);
		const FString SimulationStepsText = C.Query("simulation_steps");
		int32 SimulationStepsRequested = bIncludeStabilityTest ? 600 : 1;
		if (!SimulationStepsText.IsEmpty()
			&& (!LexTryParseString(SimulationStepsRequested, *SimulationStepsText)
				|| SimulationStepsRequested < 1 || SimulationStepsRequested > 600))
			throw std::runtime_error("simulation_steps must be an integer from 1 through 600");
		FVector SimulationImpulse = FVector::ZeroVector;
		auto ParseImpulseAxis = [&C](const TCHAR* AxisName, double& OutValue)
		{
			const FString Text = C.Query(AxisName);
			if (Text.IsEmpty()) return false;
			if (!LexTryParseString(OutValue, *Text) || !FMath::IsFinite(OutValue))
				throw std::runtime_error("simulation impulse components must be finite numbers");
			return true;
		};
		const bool bImpulseSpecified = ParseImpulseAxis(TEXT("simulation_impulse_x"), SimulationImpulse.X)
			| ParseImpulseAxis(TEXT("simulation_impulse_y"), SimulationImpulse.Y)
			| ParseImpulseAxis(TEXT("simulation_impulse_z"), SimulationImpulse.Z);
		if (bImpulseSpecified && SimulationImpulse.IsNearlyZero())
			throw std::runtime_error("simulation impulse must have a nonzero component");
		const bool bIncludeSimulationStep = bIncludeStabilityTest
			|| C.Query("include_simulation_step").Equals(TEXT("true"), ESearchCase::IgnoreCase)
			|| !SimulationStepsText.IsEmpty() || bImpulseSpecified;
		const bool bIncludeRuntimeState = bIncludeSimulationStep
			|| C.Query("include_runtime_state").Equals(TEXT("true"), ESearchCase::IgnoreCase);
		auto IsFiniteVector = [](const FVector& Value)
		{
			return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
		};
		auto IsFiniteTransform = [&IsFiniteVector](const FTransform& Transform)
		{
			const FQuat& Rotation = Transform.GetRotation();
			return IsFiniteVector(Transform.GetLocation()) && IsFiniteVector(Transform.GetScale3D())
				&& FMath::IsFinite(Rotation.X) && FMath::IsFinite(Rotation.Y)
				&& FMath::IsFinite(Rotation.Z) && FMath::IsFinite(Rotation.W);
		};
		struct FBodyRuntimeCookStatus
		{
			FName BoneName;
			int32 ConvexCount = 0;
			int32 CookedConvexCount = 0;
			bool bPhysicsMeshesCreated = false;
			bool bReady = false;
		};
		struct FBodyPhysicsStateStatus
		{
			FName BoneName;
			bool bValid = false;
			bool bValidAfterStep = false;
			bool bSimulatingAfterStep = false;
			bool bFiniteAfterStep = false;
			bool bValidThroughout = true;
			bool bSimulatingThroughout = true;
			bool bFiniteThroughout = true;
			FVector SimulationStartLocation = FVector::ZeroVector;
			double MaxLinearSpeedCmPerSecond = 0.0;
			double MaxAngularSpeedRadiansPerSecond = 0.0;
			double MaxDisplacementCm = 0.0;
		};
		struct FConstraintPhysicsStateStatus
		{
			FName JointName;
			bool bValid = false;
			bool bValidAfterStep = false;
			bool bValidThroughout = true;
		};
		TArray<FString> Errors;
		TArray<FString> Warnings;
		TArray<FBodyRuntimeCookStatus> RuntimeCookStatuses;
		TArray<FBodyPhysicsStateStatus> RuntimeBodyStatuses;
		TArray<FConstraintPhysicsStateStatus> RuntimeConstraintStatuses;
		bool bRuntimeReady = true;
		bool bRuntimeStateChecked = false;
		bool bRuntimeStateReady = false;
		bool bSimulationStepChecked = false;
		bool bSimulationStepReady = false;
		bool bSimulationStabilityChecked = false;
		bool bSimulationStabilityReady = false;
		int32 SimulationStepsCompleted = 0;
		int32 SimulationBodySamplesChecked = 0;
		int32 SimulationConstraintSamplesChecked = 0;
		double SimulationMaxLinearSpeedCmPerSecond = 0.0;
		double SimulationMaxAngularSpeedRadiansPerSecond = 0.0;
		double SimulationMaxDisplacementCm = 0.0;
		FString SimulationStepSkipReason;
		bool bSimulationImpulseApplied = false;
		FName SimulationImpulseBoneName = NAME_None;
		FVector SimulationImpulseStart = FVector::ZeroVector;
		FVector SimulationImpulseEnd = FVector::ZeroVector;
		FString RuntimeStateSkipReason;
		TSet<FName> SeenBones;
		TSet<FName> SeenConstraintProfiles;
		TSet<FName> SeenBodyProfiles;
		for (const FName Profile : Asset->GetConstraintProfileNames())
		{
			if (Profile.IsNone() || SeenConstraintProfiles.Contains(Profile)) Errors.Add(TEXT("constraint profile names must be unique and nonempty"));
			SeenConstraintProfiles.Add(Profile);
		}
		for (const FName Profile : Asset->GetPhysicalAnimationProfileNames())
		{
			if (Profile.IsNone() || SeenBodyProfiles.Contains(Profile)) Errors.Add(TEXT("body profile names must be unique and nonempty"));
			SeenBodyProfiles.Add(Profile);
		}
		int32 ShapeCount = 0;
		int32 ConvexCount = 0;
		for (const USkeletalBodySetup* Body : Asset->SkeletalBodySetups)
		{
			if (!Body) { Errors.Add(TEXT("null body setup")); continue; }
			if (SeenBones.Contains(Body->BoneName)) Errors.Add(FString::Printf(TEXT("duplicate body bone: %s"), *Body->BoneName.ToString()));
			SeenBones.Add(Body->BoneName);
			const FString Prefix = FString::Printf(TEXT("body %s"), *Body->BoneName.ToString());
			ShapeCount += PhysicsShapeCount(Body);
			ConvexCount += Body->AggGeom.ConvexElems.Num();
			if (PhysicsShapeCount(Body) == 0) Errors.Add(Prefix + TEXT(" has no collision shape"));
			if (!FMath::IsFinite(Body->DefaultInstance.MassScale) || Body->DefaultInstance.MassScale < 0.001f)
				Errors.Add(Prefix + TEXT(" has invalid mass scale"));
			if (bIncludeRuntimeCook)
			{
				USkeletalBodySetup* Probe = DuplicateObject<USkeletalBodySetup>(Body, GetTransientPackage());
				Probe->InvalidatePhysicsData();
				Probe->bFailedToCreatePhysicsMeshes = false;
				Probe->CreatePhysicsMeshes();
				FBodyRuntimeCookStatus Status;
				Status.BoneName = Body->BoneName;
				Status.ConvexCount = Probe->AggGeom.ConvexElems.Num();
				Status.bPhysicsMeshesCreated = Probe->bCreatedPhysicsMeshes;
				for (const FKConvexElem& Shape : Probe->AggGeom.ConvexElems)
					if (Shape.GetChaosConvexMesh()) ++Status.CookedConvexCount;
				Status.bReady = !Probe->bFailedToCreatePhysicsMeshes
					&& Status.CookedConvexCount == Status.ConvexCount;
				if (!Status.bReady)
				{
					Errors.Add(Prefix + TEXT(" failed runtime physics-mesh cooking"));
					bRuntimeReady = false;
				}
				RuntimeCookStatuses.Add(Status);
			}
			for (const FKSphereElem& Shape : Body->AggGeom.SphereElems)
				if (!FMath::IsFinite(Shape.Radius) || Shape.Radius <= 0.f || Shape.Center.ContainsNaN())
					Errors.Add(Prefix + TEXT(" has an invalid sphere"));
			for (const FKBoxElem& Shape : Body->AggGeom.BoxElems)
				if (!FMath::IsFinite(Shape.X) || !FMath::IsFinite(Shape.Y) || !FMath::IsFinite(Shape.Z)
					|| Shape.X <= 0.f || Shape.Y <= 0.f || Shape.Z <= 0.f
					|| Shape.Center.ContainsNaN() || Shape.Rotation.ContainsNaN())
					Errors.Add(Prefix + TEXT(" has an invalid box"));
			for (const FKSphylElem& Shape : Body->AggGeom.SphylElems)
				if (!FMath::IsFinite(Shape.Radius) || !FMath::IsFinite(Shape.Length)
					|| Shape.Radius <= 0.f || Shape.Length <= 0.f
					|| Shape.Center.ContainsNaN() || Shape.Rotation.ContainsNaN())
					Errors.Add(Prefix + TEXT(" has an invalid capsule"));
			for (const FKConvexElem& Shape : Body->AggGeom.ConvexElems)
			{
				if (Shape.VertexData.Num() < 4 || Shape.GetTransform().ContainsNaN())
				{
					Errors.Add(Prefix + TEXT(" has an invalid convex hull"));
					continue;
				}
				bool bNonFinite = false;
				for (const FVector& Vertex : Shape.VertexData) bNonFinite |= Vertex.ContainsNaN();
				if (bNonFinite) Errors.Add(Prefix + TEXT(" has nonfinite convex vertices"));
			}
			TSet<FName> ProfileNames;
			for (const FPhysicalAnimationProfile& Profile : Body->GetPhysicalAnimationProfiles())
			{
				if (ProfileNames.Contains(Profile.ProfileName)) Errors.Add(Prefix + TEXT(" has duplicate Physical Animation profile names"));
				ProfileNames.Add(Profile.ProfileName);
				if (!SeenBodyProfiles.Contains(Profile.ProfileName)) Warnings.Add(Prefix + TEXT(" has a profile absent from the asset profile list"));
				const FPhysicalAnimationData& Data = Profile.PhysicalAnimationData;
				for (float Value : {Data.OrientationStrength, Data.AngularVelocityStrength, Data.PositionStrength,
					Data.VelocityStrength, Data.MaxLinearForce, Data.MaxAngularForce})
					if (!FMath::IsFinite(Value) || Value < 0.f) { Errors.Add(Prefix + TEXT(" has invalid Physical Animation data")); break; }
			}
			for (const FName Profile : SeenBodyProfiles)
				if (!ProfileNames.Contains(Profile)) Warnings.Add(Prefix + TEXT(" is missing Physical Animation profile ") + Profile.ToString());
		}
		USkeletalMesh* Mesh = Asset->GetPreviewMesh();
		if (!Mesh) Warnings.Add(TEXT("Physics Asset has no preview Skeletal Mesh"));
		else for (const USkeletalBodySetup* Body : Asset->SkeletalBodySetups)
			if (Body && Mesh->GetRefSkeleton().FindBoneIndex(Body->BoneName) == INDEX_NONE)
				Errors.Add(FString::Printf(TEXT("body bone is not in preview mesh: %s"), *Body->BoneName.ToString()));
		TSet<FName> SeenConstraints;
		for (const UPhysicsConstraintTemplate* Constraint : Asset->ConstraintSetup)
		{
			if (!Constraint) { Errors.Add(TEXT("null constraint setup")); continue; }
			const FConstraintInstance& Instance = Constraint->DefaultInstance;
			const FString Prefix = FString::Printf(TEXT("constraint %s"), *Instance.JointName.ToString());
			if (Instance.JointName.IsNone() || SeenConstraints.Contains(Instance.JointName))
				Errors.Add(Prefix + TEXT(" has a missing or duplicate name"));
			SeenConstraints.Add(Instance.JointName);
			if (!SeenBones.Contains(Instance.ConstraintBone1) || !SeenBones.Contains(Instance.ConstraintBone2))
				Errors.Add(FString::Printf(TEXT("constraint references missing body: %s"), *Instance.JointName.ToString()));
			if (Instance.ConstraintBone1 == Instance.ConstraintBone2) Errors.Add(Prefix + TEXT(" connects a body to itself"));
			for (float Limit : {Instance.GetLinearLimit(), Instance.GetAngularSwing1Limit(),
				Instance.GetAngularSwing2Limit(), Instance.GetAngularTwistLimit()})
				if (!FMath::IsFinite(Limit) || Limit < 0.f) { Errors.Add(Prefix + TEXT(" has invalid limits")); break; }
			const FConstraintProfileProperties& Properties = Instance.ProfileInstance;
			auto DriveValid = [](const FConstraintDrive& Drive)
			{
				return FMath::IsFinite(Drive.Stiffness) && FMath::IsFinite(Drive.Damping) && FMath::IsFinite(Drive.MaxForce)
					&& Drive.Stiffness >= 0.f && Drive.Damping >= 0.f && Drive.MaxForce >= 0.f;
			};
			if (!DriveValid(Properties.LinearDrive.XDrive) || !DriveValid(Properties.LinearDrive.YDrive)
				|| !DriveValid(Properties.LinearDrive.ZDrive) || !DriveValid(Properties.AngularDrive.SlerpDrive)
				|| !DriveValid(Properties.AngularDrive.TwistDrive) || !DriveValid(Properties.AngularDrive.SwingDrive))
				Errors.Add(Prefix + TEXT(" has invalid drive parameters"));
			TSet<FName> ProfileNames;
			for (const FPhysicsConstraintProfileHandle& Profile : Constraint->ProfileHandles)
			{
				if (ProfileNames.Contains(Profile.ProfileName)) Errors.Add(Prefix + TEXT(" has duplicate profile names"));
				ProfileNames.Add(Profile.ProfileName);
				if (!SeenConstraintProfiles.Contains(Profile.ProfileName)) Warnings.Add(Prefix + TEXT(" has a profile absent from the asset profile list"));
			}
			for (const FName Profile : SeenConstraintProfiles)
				if (!ProfileNames.Contains(Profile)) Warnings.Add(Prefix + TEXT(" is missing constraint profile ") + Profile.ToString());
		}
		for (const TPair<FRigidBodyIndexPair, bool>& Pair : Asset->CollisionDisableTable)
			if (Pair.Key.Indices[0] < 0 || Pair.Key.Indices[1] >= Asset->SkeletalBodySetups.Num()
				|| Pair.Key.Indices[0] == Pair.Key.Indices[1])
				Errors.Add(TEXT("collision disable table contains an invalid body pair"));
		if (bIncludeRuntimeState)
		{
			if (!Errors.IsEmpty())
			{
				RuntimeStateSkipReason = TEXT("fix structural validation errors before creating a runtime physics state");
			}
			else if (!Mesh)
			{
				RuntimeStateSkipReason = TEXT("a preview Skeletal Mesh is required to create a runtime physics state");
			}
			else
			{
				FPreviewScene RuntimePreview(FPreviewScene::ConstructionValues()
					.SetCreateDefaultLighting(false)
					.SetForceMipsResident(false)
					.SetCreatePhysicsScene(true)
					.ShouldSimulatePhysics(bIncludeSimulationStep)
					.SetTransactional(false)
					.SetEditor(false));
				USkeletalMeshComponent* Component = NewObject<USkeletalMeshComponent>(GetTransientPackage());
				Component->SetSkeletalMesh(Mesh, false);
				Component->SetPhysicsAsset(Asset, true);
				Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
				RuntimePreview.AddComponent(Component, FTransform::Identity);
				bRuntimeStateChecked = true;
				bRuntimeStateReady = Component->IsPhysicsStateCreated();
				if (!bRuntimeStateReady)
					Errors.Add(TEXT("preview Skeletal Mesh Component did not create a physics state"));
				for (int32 Index = 0; Index < Asset->SkeletalBodySetups.Num(); ++Index)
				{
					const USkeletalBodySetup* Body = Asset->SkeletalBodySetups[Index];
					FBodyInstance* Instance = Component->Bodies.IsValidIndex(Index) ? Component->Bodies[Index] : nullptr;
					const bool bBodyValid = Instance && Instance->IsValidBodyInstance();
					FBodyPhysicsStateStatus Status;
					Status.BoneName = Body->BoneName;
					Status.bValid = bBodyValid;
					RuntimeBodyStatuses.Add(Status);
					if (!bBodyValid)
					{
						bRuntimeStateReady = false;
						Errors.Add(FString::Printf(TEXT("runtime physics body was not created: %s"), *Body->BoneName.ToString()));
					}
				}
				for (int32 Index = 0; Index < Asset->ConstraintSetup.Num(); ++Index)
				{
					const UPhysicsConstraintTemplate* Constraint = Asset->ConstraintSetup[Index];
					FConstraintInstance* Instance = Component->GetConstraintInstanceByIndex(Index);
					const bool bConstraintValid = Instance && Instance->IsValidConstraintInstance();
					FConstraintPhysicsStateStatus Status;
					Status.JointName = Constraint->DefaultInstance.JointName;
					Status.bValid = bConstraintValid;
					RuntimeConstraintStatuses.Add(Status);
					if (!bConstraintValid)
					{
						bRuntimeStateReady = false;
						Errors.Add(FString::Printf(TEXT("runtime constraint was not created: %s"), *Constraint->DefaultInstance.JointName.ToString()));
					}
				}
				if (bIncludeSimulationStep)
				{
					if (!bRuntimeStateReady)
					{
						RuntimeStateSkipReason = TEXT("runtime simulation requires every body and constraint to initialize");
					}
					else if (!RuntimePreview.GetWorld() || !RuntimePreview.GetWorld()->GetPhysicsScene())
					{
						SimulationStepSkipReason = TEXT("the transient preview physics scene is unavailable");
					}
					else
					{
						Component->SetAllBodiesSimulatePhysics(true);
						for (int32 Index = 0; Index < RuntimeBodyStatuses.Num(); ++Index)
						{
							FBodyInstance* Instance = Component->Bodies.IsValidIndex(Index) ? Component->Bodies[Index] : nullptr;
							FBodyPhysicsStateStatus& Status = RuntimeBodyStatuses[Index];
							if (Instance && Instance->IsValidBodyInstance())
							{
								const FTransform StartTransform = Instance->GetUnrealWorldTransform(false, true);
								Status.SimulationStartLocation = StartTransform.GetLocation();
								Status.bFiniteThroughout = IsFiniteTransform(StartTransform);
							}
							else
							{
								Status.bValidThroughout = false;
								Status.bFiniteThroughout = false;
							}
						}
						int32 ImpulseBodyIndex = Component->FindRootBodyIndex();
						if (!Component->Bodies.IsValidIndex(ImpulseBodyIndex)
							|| !Component->Bodies[ImpulseBodyIndex]
							|| !Component->Bodies[ImpulseBodyIndex]->IsValidBodyInstance())
						{
							ImpulseBodyIndex = INDEX_NONE;
							for (int32 Index = 0; Index < Component->Bodies.Num(); ++Index)
								if (Component->Bodies[Index] && Component->Bodies[Index]->IsValidBodyInstance())
									{ ImpulseBodyIndex = Index; break; }
						}
						if (bImpulseSpecified && Asset->SkeletalBodySetups.IsValidIndex(ImpulseBodyIndex))
						{
							FBodyInstance* ImpulseBody = Component->Bodies[ImpulseBodyIndex];
							SimulationImpulseBoneName = Asset->SkeletalBodySetups[ImpulseBodyIndex]->BoneName;
							SimulationImpulseStart = ImpulseBody->GetUnrealWorldTransform(false, true).GetLocation();
							Component->AddImpulse(SimulationImpulse, SimulationImpulseBoneName, true);
							bSimulationImpulseApplied = true;
						}
						else if (bImpulseSpecified)
						{
							Errors.Add(TEXT("no valid runtime body is available for the simulation impulse"));
						}
						bSimulationStepReady = !bImpulseSpecified || bSimulationImpulseApplied;
						for (int32 Step = 0; Step < SimulationStepsRequested; ++Step)
						{
							RuntimePreview.GetWorld()->Tick(LEVELTICK_All, 1.f / 60.f);
							++SimulationStepsCompleted;
							for (int32 Index = 0; Index < RuntimeBodyStatuses.Num(); ++Index)
							{
								FBodyInstance* Instance = Component->Bodies.IsValidIndex(Index) ? Component->Bodies[Index] : nullptr;
								FBodyPhysicsStateStatus& Status = RuntimeBodyStatuses[Index];
								const bool bBodyValid = Instance && Instance->IsValidBodyInstance();
								const bool bBodySimulating = bBodyValid && Component->IsSimulatingPhysics(Status.BoneName);
								Status.bValidThroughout &= bBodyValid;
								Status.bSimulatingThroughout &= bBodySimulating;
								++SimulationBodySamplesChecked;
								if (!bBodyValid) { Status.bFiniteThroughout = false; continue; }

								const FTransform Transform = Instance->GetUnrealWorldTransform(false, true);
								const FVector LinearVelocity = Instance->GetUnrealWorldVelocity();
								const FVector AngularVelocity = Instance->GetUnrealWorldAngularVelocityInRadians();
								const FVector Location = Transform.GetLocation();
								const double LinearSpeed = LinearVelocity.Size();
								const double AngularSpeed = AngularVelocity.Size();
								const double Displacement = FVector::Distance(Status.SimulationStartLocation, Location);
								const bool bFiniteSample = IsFiniteTransform(Transform)
									&& IsFiniteVector(LinearVelocity) && IsFiniteVector(AngularVelocity)
									&& FMath::IsFinite(LinearSpeed) && FMath::IsFinite(AngularSpeed)
									&& FMath::IsFinite(Displacement);
								Status.bFiniteThroughout &= bFiniteSample;
								if (!bFiniteSample) continue;

								Status.MaxLinearSpeedCmPerSecond = FMath::Max(Status.MaxLinearSpeedCmPerSecond, LinearSpeed);
								Status.MaxAngularSpeedRadiansPerSecond = FMath::Max(Status.MaxAngularSpeedRadiansPerSecond, AngularSpeed);
								Status.MaxDisplacementCm = FMath::Max(Status.MaxDisplacementCm, Displacement);
								SimulationMaxLinearSpeedCmPerSecond = FMath::Max(SimulationMaxLinearSpeedCmPerSecond, LinearSpeed);
								SimulationMaxAngularSpeedRadiansPerSecond = FMath::Max(SimulationMaxAngularSpeedRadiansPerSecond, AngularSpeed);
								SimulationMaxDisplacementCm = FMath::Max(SimulationMaxDisplacementCm, Displacement);
							}
							for (int32 Index = 0; Index < RuntimeConstraintStatuses.Num(); ++Index)
							{
								FConstraintInstance* Instance = Component->GetConstraintInstanceByIndex(Index);
								RuntimeConstraintStatuses[Index].bValidThroughout &= Instance && Instance->IsValidConstraintInstance();
								++SimulationConstraintSamplesChecked;
							}
						}
						bSimulationStepChecked = true;
						bSimulationStabilityChecked = bIncludeStabilityTest;
						for (int32 Index = 0; Index < RuntimeBodyStatuses.Num(); ++Index)
						{
							FBodyInstance* Instance = Component->Bodies.IsValidIndex(Index) ? Component->Bodies[Index] : nullptr;
							FBodyPhysicsStateStatus& Status = RuntimeBodyStatuses[Index];
							Status.bValidAfterStep = Instance && Instance->IsValidBodyInstance();
							Status.bSimulatingAfterStep = Component->IsSimulatingPhysics(Status.BoneName);
							Status.bFiniteAfterStep = Status.bValidAfterStep
								&& IsFiniteTransform(Instance->GetUnrealWorldTransform(false, true))
								&& IsFiniteVector(Instance->GetUnrealWorldVelocity())
								&& IsFiniteVector(Instance->GetUnrealWorldAngularVelocityInRadians());
							if (!Status.bValidAfterStep || !Status.bSimulatingAfterStep || !Status.bFiniteAfterStep
								|| !Status.bValidThroughout || !Status.bSimulatingThroughout || !Status.bFiniteThroughout)
							{
								bSimulationStepReady = false;
								Errors.Add(FString::Printf(TEXT("runtime body failed a simulation sample or returned a nonfinite state: %s"), *Status.BoneName.ToString()));
							}
						}
						for (int32 Index = 0; Index < RuntimeConstraintStatuses.Num(); ++Index)
						{
							FConstraintInstance* Instance = Component->GetConstraintInstanceByIndex(Index);
							FConstraintPhysicsStateStatus& Status = RuntimeConstraintStatuses[Index];
							Status.bValidAfterStep = Instance && Instance->IsValidConstraintInstance();
							if (!Status.bValidAfterStep || !Status.bValidThroughout)
							{
								bSimulationStepReady = false;
								Errors.Add(FString::Printf(TEXT("runtime constraint failed a simulation sample: %s"), *Status.JointName.ToString()));
							}
						}
						if (bSimulationImpulseApplied && Component->Bodies.IsValidIndex(ImpulseBodyIndex)
							&& Component->Bodies[ImpulseBodyIndex] && Component->Bodies[ImpulseBodyIndex]->IsValidBodyInstance())
						{
							SimulationImpulseEnd = Component->Bodies[ImpulseBodyIndex]->GetUnrealWorldTransform(false, true).GetLocation();
							if (SimulationImpulseEnd.ContainsNaN() || SimulationImpulseStart.ContainsNaN())
							{
								bSimulationStepReady = false;
								Errors.Add(TEXT("simulation impulse produced a nonfinite body position"));
							}
						}
						bSimulationStabilityReady = bSimulationStabilityChecked && bSimulationStepReady;
					}
				}
			}
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("body_count"), Asset->SkeletalBodySetups.Num());
		Writer->WriteValue(TEXT("constraint_count"), Asset->ConstraintSetup.Num());
		Writer->WriteValue(TEXT("shape_count"), ShapeCount);
		Writer->WriteValue(TEXT("convex_count"), ConvexCount);
		Writer->WriteValue(TEXT("body_profile_count"), SeenBodyProfiles.Num());
		Writer->WriteValue(TEXT("constraint_profile_count"), SeenConstraintProfiles.Num());
		Writer->WriteValue(TEXT("preview_mesh_path"), Mesh ? Mesh->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("runtime_cook_checked"), bIncludeRuntimeCook);
		if (bIncludeRuntimeCook) Writer->WriteValue(TEXT("runtime_ready"), bRuntimeReady);
		Writer->WriteValue(TEXT("runtime_state_requested"), bIncludeRuntimeState);
		Writer->WriteValue(TEXT("runtime_state_checked"), bRuntimeStateChecked);
		if (bRuntimeStateChecked) Writer->WriteValue(TEXT("runtime_state_ready"), bRuntimeStateReady);
		Writer->WriteValue(TEXT("simulation_step_requested"), bIncludeSimulationStep);
		Writer->WriteValue(TEXT("simulation_step_checked"), bSimulationStepChecked);
		Writer->WriteValue(TEXT("simulation_steps_requested"), bIncludeSimulationStep ? SimulationStepsRequested : 0);
		Writer->WriteValue(TEXT("simulation_steps_completed"), SimulationStepsCompleted);
		if (bSimulationStepChecked) Writer->WriteValue(TEXT("simulation_step_ready"), bSimulationStepReady);
		Writer->WriteValue(TEXT("simulation_stability_requested"), bIncludeStabilityTest);
		Writer->WriteValue(TEXT("simulation_stability_checked"), bSimulationStabilityChecked);
		if (bSimulationStabilityChecked)
		{
			Writer->WriteValue(TEXT("simulation_stability_ready"), bSimulationStabilityReady);
			Writer->WriteValue(TEXT("simulation_body_samples_checked"), SimulationBodySamplesChecked);
			Writer->WriteValue(TEXT("simulation_constraint_samples_checked"), SimulationConstraintSamplesChecked);
			Writer->WriteValue(TEXT("simulation_max_linear_speed_cm_s"), SimulationMaxLinearSpeedCmPerSecond);
			Writer->WriteValue(TEXT("simulation_max_angular_speed_rad_s"), SimulationMaxAngularSpeedRadiansPerSecond);
			Writer->WriteValue(TEXT("simulation_max_displacement_cm"), SimulationMaxDisplacementCm);
		}
		if (!RuntimeStateSkipReason.IsEmpty()) Writer->WriteValue(TEXT("runtime_state_skip_reason"), RuntimeStateSkipReason);
		if (!SimulationStepSkipReason.IsEmpty()) Writer->WriteValue(TEXT("simulation_step_skip_reason"), SimulationStepSkipReason);
		Writer->WriteValue(TEXT("simulation_impulse_applied"), bSimulationImpulseApplied);
		if (bImpulseSpecified)
		{
			Writer->WriteObjectStart(TEXT("simulation_impulse"));
			Writer->WriteValue(TEXT("x"), SimulationImpulse.X);
			Writer->WriteValue(TEXT("y"), SimulationImpulse.Y);
			Writer->WriteValue(TEXT("z"), SimulationImpulse.Z);
			Writer->WriteObjectEnd();
		}
		if (bSimulationImpulseApplied)
		{
			Writer->WriteValue(TEXT("simulation_impulse_bone"), SimulationImpulseBoneName.ToString());
			Writer->WriteValue(TEXT("simulation_impulse_start"), SimulationImpulseStart.ToString());
			Writer->WriteValue(TEXT("simulation_impulse_end"), SimulationImpulseEnd.ToString());
			Writer->WriteValue(TEXT("simulation_impulse_displacement"), FVector::Distance(SimulationImpulseStart, SimulationImpulseEnd));
		}
		Writer->WriteArrayStart(TEXT("body_runtime_states"));
		for (const FBodyRuntimeCookStatus& Status : RuntimeCookStatuses)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("bone_name"), Status.BoneName.ToString());
			Writer->WriteValue(TEXT("physics_meshes_created"), Status.bPhysicsMeshesCreated);
			Writer->WriteValue(TEXT("convex_count"), Status.ConvexCount);
			Writer->WriteValue(TEXT("cooked_convex_count"), Status.CookedConvexCount);
			Writer->WriteValue(TEXT("ready"), Status.bReady);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("runtime_body_instances"));
		for (const FBodyPhysicsStateStatus& Status : RuntimeBodyStatuses)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("bone_name"), Status.BoneName.ToString());
			Writer->WriteValue(TEXT("valid"), Status.bValid);
			if (bSimulationStepChecked)
			{
				Writer->WriteValue(TEXT("valid_after_step"), Status.bValidAfterStep);
				Writer->WriteValue(TEXT("simulating_after_step"), Status.bSimulatingAfterStep);
				Writer->WriteValue(TEXT("finite_after_step"), Status.bFiniteAfterStep);
				Writer->WriteValue(TEXT("valid_throughout"), Status.bValidThroughout);
				Writer->WriteValue(TEXT("simulating_throughout"), Status.bSimulatingThroughout);
				Writer->WriteValue(TEXT("finite_throughout"), Status.bFiniteThroughout);
				Writer->WriteValue(TEXT("max_linear_speed_cm_s"), Status.MaxLinearSpeedCmPerSecond);
				Writer->WriteValue(TEXT("max_angular_speed_rad_s"), Status.MaxAngularSpeedRadiansPerSecond);
				Writer->WriteValue(TEXT("max_displacement_cm"), Status.MaxDisplacementCm);
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("runtime_constraint_instances"));
		for (const FConstraintPhysicsStateStatus& Status : RuntimeConstraintStatuses)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("joint_name"), Status.JointName.ToString());
			Writer->WriteValue(TEXT("valid"), Status.bValid);
			if (bSimulationStepChecked)
			{
				Writer->WriteValue(TEXT("valid_after_step"), Status.bValidAfterStep);
				Writer->WriteValue(TEXT("valid_throughout"), Status.bValidThroughout);
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("unrepresented_bones"));
		if (Mesh) for (int32 Index = 0; Index < Mesh->GetRefSkeleton().GetRawBoneNum(); ++Index)
		{
			const FName Bone = Mesh->GetRefSkeleton().GetBoneName(Index);
			if (!SeenBones.Contains(Bone)) Writer->WriteValue(Bone.ToString());
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd(); Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/physics-assets/refresh", [](const FHttpContext<FPhysicsAssetEditReq, FString>& C)
	{
		UPhysicsAsset* Asset = LoadPhysicsAsset(C.RequestBody().AssetPath);
		Asset->UpdateBodySetupIndexMap();
		Asset->UpdateBoundsBodiesArray();
		Asset->RefreshPhysicsAssetChange();
		return C.TextResponse(PhysicsEditJson(Asset, false, false, false, TEXT(""), TEXT(""), -1), TEXT("application/json"));
	});

	App->Get("/control-rigs/inspect", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		if (!Cast<IControlRigAssetInterface>(Asset)) throw std::runtime_error("Asset is not a Control Rig asset");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/control-rigs/hierarchy", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		URigHierarchy* Hierarchy = Rig ? Rig->GetHierarchy() : nullptr;
		if (!Hierarchy) throw std::runtime_error("Asset is not a Control Rig with a hierarchy");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		for (const FRigElementKey& Key : Hierarchy->GetAllKeys())
		{
			const FRigElementKey Parent = Hierarchy->GetFirstParent(Key);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Key.Name.ToString());
			Writer->WriteValue(TEXT("type"), RigElementTypeName(Key.Type));
			Writer->WriteValue(TEXT("parent_name"), Parent.IsValid() ? Parent.Name.ToString() : TEXT(""));
			Writer->WriteValue(TEXT("parent_type"), Parent.IsValid() ? RigElementTypeName(Parent.Type) : TEXT(""));
			Writer->WriteValue(TEXT("child_count"), Hierarchy->GetChildren(Key).Num());
			if (Key.Type == ERigElementType::Bone || Key.Type == ERigElementType::Null
				|| Key.Type == ERigElementType::Control || Key.Type == ERigElementType::Socket)
			{
				auto WriteGlobalTransform = [&Writer](const FString& Field, const FTransform& Transform)
				{
					const FVector Translation = Transform.GetTranslation();
					const FRotator Rotation = Transform.Rotator();
					const FVector Scale = Transform.GetScale3D();
					Writer->WriteObjectStart(Field);
					Writer->WriteValue(TEXT("x"), Translation.X); Writer->WriteValue(TEXT("y"), Translation.Y); Writer->WriteValue(TEXT("z"), Translation.Z);
					Writer->WriteValue(TEXT("pitch"), Rotation.Pitch); Writer->WriteValue(TEXT("yaw"), Rotation.Yaw); Writer->WriteValue(TEXT("roll"), Rotation.Roll);
					Writer->WriteValue(TEXT("scale_x"), Scale.X); Writer->WriteValue(TEXT("scale_y"), Scale.Y); Writer->WriteValue(TEXT("scale_z"), Scale.Z);
					Writer->WriteObjectEnd();
				};
				WriteGlobalTransform(TEXT("initial_global_transform"), Hierarchy->GetInitialGlobalTransform(Key));
				WriteGlobalTransform(TEXT("current_global_transform"), Hierarchy->GetGlobalTransform(Key, false));
			}
			if (Key.Type == ERigElementType::Control)
				if (const FRigControlElement* Control = Hierarchy->Find<FRigControlElement>(Key))
				{
				const ERigControlType ControlType = Control->Settings.ControlType;
				const FRigElementKey ActiveParent = Hierarchy->GetActiveParent(Key);
				Writer->WriteValue(TEXT("restrict_space_switching"), Control->Settings.bRestrictSpaceSwitching);
				Writer->WriteValue(TEXT("active_parent_name"), ActiveParent.IsValid() ? ActiveParent.Name.ToString() : TEXT(""));
				Writer->WriteValue(TEXT("active_parent_type"), ActiveParent.IsValid() ? RigElementTypeName(ActiveParent.Type) : TEXT(""));
				Writer->WriteArrayStart(TEXT("available_spaces"));
				for (const FRigElementKeyWithLabel& Space : Control->Settings.Customization.AvailableSpaces)
				{
					Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Space.Key.Name.ToString());
					Writer->WriteValue(TEXT("type"), RigElementTypeName(Space.Key.Type));
					Writer->WriteValue(TEXT("label"), Space.Label.ToString()); Writer->WriteObjectEnd();
				}
				Writer->WriteArrayEnd();
				Writer->WriteArrayStart(TEXT("removed_spaces"));
				for (const FRigElementKey& Space : Control->Settings.Customization.RemovedSpaces)
				{
					Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Space.Name.ToString());
					Writer->WriteValue(TEXT("type"), RigElementTypeName(Space.Type)); Writer->WriteObjectEnd();
				}
				Writer->WriteArrayEnd();
				Writer->WriteValue(TEXT("display_name"), Control->Settings.DisplayName.ToString());
				Writer->WriteValue(TEXT("control_animation_type"), RigControlAnimationTypeName(Control->Settings.AnimationType));
				Writer->WriteValue(TEXT("shape_name"), Control->Settings.ShapeName.ToString());
				Writer->WriteValue(TEXT("shape_color"), Control->Settings.ShapeColor.ToString());
				Writer->WriteValue(TEXT("shape_visibility"), RigControlVisibilityName(Control->Settings.ShapeVisibility));
				Writer->WriteValue(TEXT("shape_visible"), Control->Settings.bShapeVisible);
				Writer->WriteValue(TEXT("draw_limits"), Control->Settings.bDrawLimits);
				Writer->WriteValue(TEXT("group_with_parent_control"), Control->Settings.bGroupWithParentControl);
				Writer->WriteValue(TEXT("uses_preferred_rotation_order"), Control->Settings.bUsePreferredRotationOrder);
				Writer->WriteValue(TEXT("preferred_rotation_order"), RigRotationOrderName(Control->Settings.PreferredRotationOrder));
				const FTransform ShapeTransform = Hierarchy->GetLocalControlShapeTransform(Key);
				const FVector ShapeTranslation = ShapeTransform.GetTranslation(), ShapeScale = ShapeTransform.GetScale3D();
				const FRotator ShapeRotation = ShapeTransform.Rotator();
				Writer->WriteObjectStart(TEXT("shape_transform"));
				Writer->WriteObjectStart(TEXT("translation")); Writer->WriteValue(TEXT("x"), ShapeTranslation.X); Writer->WriteValue(TEXT("y"), ShapeTranslation.Y); Writer->WriteValue(TEXT("z"), ShapeTranslation.Z); Writer->WriteObjectEnd();
				Writer->WriteObjectStart(TEXT("rotation")); Writer->WriteValue(TEXT("pitch"), ShapeRotation.Pitch); Writer->WriteValue(TEXT("yaw"), ShapeRotation.Yaw); Writer->WriteValue(TEXT("roll"), ShapeRotation.Roll); Writer->WriteObjectEnd();
				Writer->WriteObjectStart(TEXT("scale")); Writer->WriteValue(TEXT("x"), ShapeScale.X); Writer->WriteValue(TEXT("y"), ShapeScale.Y); Writer->WriteValue(TEXT("z"), ShapeScale.Z); Writer->WriteObjectEnd();
				Writer->WriteObjectEnd();
				Writer->WriteArrayStart(TEXT("driven_controls"));
				for (const FRigElementKey& Driven : Control->Settings.DrivenControls)
				{
					Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Driven.Name.ToString());
					Writer->WriteValue(TEXT("type"), RigElementTypeName(Driven.Type)); Writer->WriteObjectEnd();
				}
				Writer->WriteArrayEnd();
				Writer->WriteValue(TEXT("control_type"), RigControlTypeName(ControlType));
				Writer->WriteValue(TEXT("primary_axis"), Control->Settings.PrimaryAxis == ERigControlAxis::X ? TEXT("x")
					: Control->Settings.PrimaryAxis == ERigControlAxis::Y ? TEXT("y") : TEXT("z"));
				if (Control->Settings.ControlEnum)
				{
					const UEnum* Enum = Control->Settings.ControlEnum;
					Writer->WriteValue(TEXT("control_enum_path"), Enum->GetPathName());
					const FRigControlValue Initial = Hierarchy->GetControlValue(Key, ERigControlValueType::Initial);
					const FRigControlValue Current = Hierarchy->GetControlValue(Key, ERigControlValueType::Current);
					Writer->WriteValue(TEXT("initial_enum_value"), Enum->GetNameStringByValue(Initial.Get<int32>()));
					Writer->WriteValue(TEXT("current_enum_value"), Enum->GetNameStringByValue(Current.Get<int32>()));
					Writer->WriteArrayStart(TEXT("enum_members"));
					for (int32 EnumIndex = 0; EnumIndex < Enum->NumEnums(); ++EnumIndex)
					{
						const int64 EnumValue = Enum->GetValueByIndex(EnumIndex);
						const FString EnumeratorName = Enum->GetNameStringByIndex(EnumIndex);
						if (Enum->HasMetaData(TEXT("Hidden"), EnumIndex) || EnumeratorName.Equals(TEXT("MAX"), ESearchCase::IgnoreCase)
							|| EnumeratorName.EndsWith(TEXT("_MAX"), ESearchCase::IgnoreCase) || !Enum->IsValidEnumValue(EnumValue)
							|| EnumValue < MIN_int32 || EnumValue > MAX_int32) continue;
						Writer->WriteObjectStart();
						Writer->WriteValue(TEXT("name"), Enum->GetNameStringByIndex(EnumIndex));
						Writer->WriteValue(TEXT("value"), static_cast<int32>(EnumValue));
						Writer->WriteObjectEnd();
					}
					Writer->WriteArrayEnd();
				}
				const FRigControlValue Value = Hierarchy->GetControlValue(Key, ERigControlValueType::Initial);
				auto WriteControlValue = [&Writer, ControlType, &Control](const FString& Field, const FRigControlValue& ControlValue)
				{
					if (ControlType == ERigControlType::Float || ControlType == ERigControlType::ScaleFloat) Writer->WriteValue(Field, ControlValue.Get<float>());
					else if (ControlType == ERigControlType::Bool) Writer->WriteValue(Field, ControlValue.Get<bool>());
					else if (ControlType == ERigControlType::Integer) Writer->WriteValue(Field, ControlValue.Get<int32>());
					else
					{
						const FTransform Transform = ControlValue.GetAsTransform(ControlType, Control->Settings.PrimaryAxis);
						const FVector Translation = Transform.GetTranslation(), Scale = Transform.GetScale3D();
						const FRotator Rotation = Transform.Rotator();
						Writer->WriteObjectStart(Field);
						Writer->WriteObjectStart(TEXT("translation")); Writer->WriteValue(TEXT("x"), Translation.X); Writer->WriteValue(TEXT("y"), Translation.Y); Writer->WriteValue(TEXT("z"), Translation.Z); Writer->WriteObjectEnd();
						Writer->WriteObjectStart(TEXT("rotation")); Writer->WriteValue(TEXT("pitch"), Rotation.Pitch); Writer->WriteValue(TEXT("yaw"), Rotation.Yaw); Writer->WriteValue(TEXT("roll"), Rotation.Roll); Writer->WriteObjectEnd();
						Writer->WriteObjectStart(TEXT("scale")); Writer->WriteValue(TEXT("x"), Scale.X); Writer->WriteValue(TEXT("y"), Scale.Y); Writer->WriteValue(TEXT("z"), Scale.Z); Writer->WriteObjectEnd();
						Writer->WriteObjectEnd();
					}
				};
				WriteControlValue(TEXT("initial_value"), Value);
				WriteControlValue(TEXT("current_value"), Hierarchy->GetControlValue(Key, ERigControlValueType::Current));
					if (Control->Settings.LimitEnabled.IsValidIndex(0))
					{
						Writer->WriteObjectStart(TEXT("limits"));
						Writer->WriteValue(TEXT("minimum_enabled"), Control->Settings.LimitEnabled[0].bMinimum);
						Writer->WriteValue(TEXT("maximum_enabled"), Control->Settings.LimitEnabled[0].bMaximum);
						Writer->WriteArrayStart(TEXT("enabled_dimensions"));
						for (int32 Index = 0; Index < Control->Settings.LimitEnabled.Num(); ++Index)
							if (Control->Settings.LimitEnabled[Index].IsOn()) Writer->WriteValue(Index);
						Writer->WriteArrayEnd();
						if (ControlType == ERigControlType::Float || ControlType == ERigControlType::ScaleFloat)
						{
							Writer->WriteValue(TEXT("minimum"), Control->Settings.MinimumValue.Get<float>());
							Writer->WriteValue(TEXT("maximum"), Control->Settings.MaximumValue.Get<float>());
						}
						else if (ControlType == ERigControlType::Integer)
						{
							Writer->WriteValue(TEXT("minimum"), Control->Settings.MinimumValue.Get<int32>());
							Writer->WriteValue(TEXT("maximum"), Control->Settings.MaximumValue.Get<int32>());
						}
						else if (ControlType != ERigControlType::Bool)
						{
							WriteControlValue(TEXT("minimum"), Control->Settings.MinimumValue);
							WriteControlValue(TEXT("maximum"), Control->Settings.MaximumValue);
						}
						Writer->WriteObjectEnd();
					}
				}
			if (Key.Type == ERigElementType::Connector)
				if (const FRigConnectorElement* Connector = Hierarchy->Find<FRigConnectorElement>(Key))
				{
					Writer->WriteValue(TEXT("connector_type"), Connector->Settings.Type == EConnectorType::Primary ? TEXT("primary") : TEXT("secondary"));
					Writer->WriteValue(TEXT("optional"), Connector->Settings.bOptional);
					Writer->WriteValue(TEXT("array"), Connector->Settings.bIsArray);
					Writer->WriteValue(TEXT("description"), Connector->Settings.Description);
				}
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/control-rigs/templates", [](const FHttpContext<void, FString>& C)
	{
		const FString Search = C.Query("search");
		const TArray<FString> RegisteredTemplates = URigVMController::GetRegisteredTemplates();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("templates"));
		int32 Count = 0;
		for (const FString& Notation : RegisteredTemplates)
		{
			if (!Search.IsEmpty() && !Notation.Contains(Search, ESearchCase::IgnoreCase)) continue;
			++Count;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("notation"), Notation);
			Writer->WriteArrayStart(TEXT("unit_struct_paths"));
			for (const UScriptStruct* UnitStruct : URigVMController::GetUnitStructsForTemplate(FName(*Notation)))
				if (UnitStruct) Writer->WriteValue(UnitStruct->GetPathName());
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("count"), Count);
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/control-rigs/graphs", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		FRigVMAssetInterfacePtr VM = Rig ? Rig->GetRigVMAssetInterface() : FRigVMAssetInterfacePtr();
		if (!VM) throw std::runtime_error("Asset is not a Control Rig with a RigVM model");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		auto PinDirectionName = [](ERigVMPinDirection Direction) -> const TCHAR*
		{
			switch (Direction)
			{
			case ERigVMPinDirection::Input: return TEXT("input");
			case ERigVMPinDirection::Output: return TEXT("output");
			case ERigVMPinDirection::IO: return TEXT("io");
			case ERigVMPinDirection::Visible: return TEXT("visible");
			case ERigVMPinDirection::Hidden: return TEXT("hidden");
			default: return TEXT("invalid");
			}
		};
		TFunction<void(const URigVMPin*)> WritePin;
		WritePin = [&Writer, &PinDirectionName, &WritePin](const URigVMPin* Pin)
		{
			if (!Pin) return;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Pin->GetName());
			Writer->WriteValue(TEXT("path"), Pin->GetPinPath());
			Writer->WriteValue(TEXT("type"), Pin->GetCPPType());
			Writer->WriteValue(TEXT("direction"), PinDirectionName(Pin->GetDirection()));
			Writer->WriteValue(TEXT("default"), Pin->GetDefaultValue());
			Writer->WriteValue(TEXT("constant"), Pin->IsDefinedAsConstant());
			Writer->WriteValue(TEXT("wildcard"), Pin->IsWildCard());
			Writer->WriteValue(TEXT("array"), Pin->IsArray());
			Writer->WriteValue(TEXT("array_element"), Pin->IsArrayElement());
			Writer->WriteValue(TEXT("display_name"), Pin->GetDisplayName().ToString());
			Writer->WriteValue(TEXT("expanded"), Pin->IsExpanded());
			Writer->WriteValue(TEXT("watched"), Pin->RequiresWatch());
			Writer->WriteValue(TEXT("injected_node_count"), Pin->GetInjectedNodes().Num());
			Writer->WriteArrayStart(TEXT("sub_pins"));
			for (const URigVMPin* SubPin : Pin->GetSubPins()) WritePin(SubPin);
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		};
		for (const URigVMGraph* Graph : VM->GetAllModels())
		{
			if (!Graph) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Graph->GetGraphName());
			Writer->WriteValue(TEXT("path"), Graph->GetNodePath());
			Writer->WriteArrayStart(TEXT("event_names"));
			for (const FName EventName : Graph->GetEventNames()) Writer->WriteValue(EventName.ToString());
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("nodes"));
			for (const URigVMNode* Node : Graph->GetNodes())
			{
				if (!Node) continue;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Node->GetName());
				Writer->WriteValue(TEXT("path"), Node->GetNodePath());
				Writer->WriteValue(TEXT("title"), Node->GetNodeTitle());
				Writer->WriteValue(TEXT("class"), Node->GetClass()->GetName());
				Writer->WriteValue(TEXT("x"), Node->GetPosition().X);
				Writer->WriteValue(TEXT("y"), Node->GetPosition().Y);
				if (const URigVMCommentNode* CommentNode = Cast<URigVMCommentNode>(Node))
					Writer->WriteValue(TEXT("comment_text"), CommentNode->GetCommentText());
				Writer->WriteValue(TEXT("pin_count"), Node->GetPins().Num());
				if (const URigVMVariableNode* VariableNode = Cast<URigVMVariableNode>(Node))
				{
					Writer->WriteValue(TEXT("variable_name"), VariableNode->GetVariableName().ToString());
					Writer->WriteValue(TEXT("variable_getter"), VariableNode->IsGetter());
					Writer->WriteValue(TEXT("variable_local"), VariableNode->IsLocalVariable());
					Writer->WriteValue(TEXT("variable_cpp_type"), VariableNode->GetCPPType());
					Writer->WriteValue(TEXT("variable_default"), VariableNode->GetDefaultValue());
				}
				if (const URigVMFunctionReferenceNode* FunctionReference = Cast<URigVMFunctionReferenceNode>(Node))
					Writer->WriteValue(TEXT("function_name"), FunctionReference->GetReferencedFunctionHeader().Name.ToString());
				if (const URigVMCollapseNode* CollapseNode = Cast<URigVMCollapseNode>(Node))
					if (const URigVMGraph* ContainedGraph = CollapseNode->GetContainedGraph())
					{
						Writer->WriteValue(TEXT("contained_graph_path"), ContainedGraph->GetNodePath());
						Writer->WriteValue(TEXT("contained_node_count"), ContainedGraph->GetNodes().Num());
					}
				if (const URigVMInvokeEntryNode* InvokeEntry = Cast<URigVMInvokeEntryNode>(Node))
					Writer->WriteValue(TEXT("entry_name"), InvokeEntry->GetEntryName().ToString());
				if (const URigVMTemplateNode* TemplateNode = Cast<URigVMTemplateNode>(Node))
				{
					Writer->WriteValue(TEXT("template_notation"), TemplateNode->GetNotation().ToString());
					Writer->WriteValue(TEXT("template_resolved"), TemplateNode->IsResolved());
					if (TemplateNode->GetTemplate())
						Writer->WriteValue(TEXT("template_fully_unresolved"), TemplateNode->IsFullyUnresolved());
				}
				if (const URigVMInjectionInfo* Injection = Node->GetInjectionInfo())
				{
					Writer->WriteValue(TEXT("injected"), true);
					Writer->WriteValue(TEXT("injection_pin_path"), Injection->GetPin() ? Injection->GetPin()->GetPinPath() : TEXT(""));
					Writer->WriteValue(TEXT("injected_as_input"), Injection->bInjectedAsInput);
				}
				Writer->WriteArrayStart(TEXT("pins"));
				for (const URigVMPin* Pin : Node->GetPins())
					WritePin(Pin);
				Writer->WriteArrayEnd();
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("links"));
			for (const URigVMLink* Link : Graph->GetLinks())
			{
				if (!Link) continue;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("source"), Link->GetSourcePinPath());
				Writer->WriteValue(TEXT("target"), Link->GetTargetPinPath());
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("input_arguments"));
			for (const FRigVMGraphVariableDescription& Argument : Graph->GetInputArguments())
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Argument.Name.ToString());
				Writer->WriteValue(TEXT("cpp_type"), Argument.CPPType);
				Writer->WriteValue(TEXT("default"), Argument.DefaultValue);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("output_arguments"));
			for (const FRigVMGraphVariableDescription& Argument : Graph->GetOutputArguments())
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Argument.Name.ToString());
				Writer->WriteValue(TEXT("cpp_type"), Argument.CPPType);
				Writer->WriteValue(TEXT("default"), Argument.DefaultValue);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("local_variables"));
			for (const FRigVMGraphVariableDescription& Variable : Graph->GetLocalVariables())
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Variable.Name.ToString());
				Writer->WriteValue(TEXT("cpp_type"), Variable.CPPType);
				Writer->WriteValue(TEXT("cpp_type_object_path"), Variable.CPPTypeObjectPath.IsNone() ? FString() : Variable.CPPTypeObjectPath.ToString());
				Writer->WriteValue(TEXT("default"), Variable.DefaultValue);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/control-rigs/graphs", [](const FHttpContext<FControlRigGraphReq, FString>& C)
	{
		const FControlRigGraphReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		FRigVMAssetInterfacePtr VM = Rig ? Rig->GetRigVMAssetInterface() : FRigVMAssetInterfacePtr();
		if (!VM) throw std::runtime_error("Asset is not a Control Rig with a RigVM model");
		if (Body.GraphPath.IsEmpty()) throw std::runtime_error("graph_path is required");
		URigVMGraph* Graph = nullptr;
		for (URigVMGraph* Candidate : VM->GetAllModels())
			if (Candidate && Candidate->GetNodePath() == Body.GraphPath) { Graph = Candidate; break; }
		if (!Graph) throw std::runtime_error("graph_path does not identify a RigVM model graph");
		URigVMController* Controller = VM->GetController(Graph);
		if (!Controller) throw std::runtime_error("RigVM graph controller is unavailable");
		const bool bAddUnit = Body.Operation.Equals(TEXT("add_unit"), ESearchCase::IgnoreCase);
		const bool bAddBranch = Body.Operation.Equals(TEXT("add_branch"), ESearchCase::IgnoreCase);
		const bool bAddComment = Body.Operation.Equals(TEXT("add_comment"), ESearchCase::IgnoreCase);
		const bool bAddConstant = Body.Operation.Equals(TEXT("add_constant"), ESearchCase::IgnoreCase);
		const bool bAddMakeStruct = Body.Operation.Equals(TEXT("add_make_struct"), ESearchCase::IgnoreCase);
		const bool bAddBreakStruct = Body.Operation.Equals(TEXT("add_break_struct"), ESearchCase::IgnoreCase);
		const bool bAddConstantOnPin = Body.Operation.Equals(TEXT("add_constant_on_pin"), ESearchCase::IgnoreCase);
		const bool bAddMakeStructOnPin = Body.Operation.Equals(TEXT("add_make_struct_on_pin"), ESearchCase::IgnoreCase);
		const bool bAddBreakStructOnPin = Body.Operation.Equals(TEXT("add_break_struct_on_pin"), ESearchCase::IgnoreCase);
		const bool bAddRerouteOnPin = Body.Operation.Equals(TEXT("add_reroute_on_pin"), ESearchCase::IgnoreCase);
		const bool bAddNodeOnPin = bAddConstantOnPin || bAddMakeStructOnPin || bAddBreakStructOnPin || bAddRerouteOnPin;
		const bool bAddIf = Body.Operation.Equals(TEXT("add_if"), ESearchCase::IgnoreCase);
		const bool bAddSelect = Body.Operation.Equals(TEXT("add_select"), ESearchCase::IgnoreCase);
		const bool bAddEnum = Body.Operation.Equals(TEXT("add_enum"), ESearchCase::IgnoreCase);
		const bool bAddArray = Body.Operation.Equals(TEXT("add_array"), ESearchCase::IgnoreCase);
		const bool bAddArrayPin = Body.Operation.Equals(TEXT("add_array_pin"), ESearchCase::IgnoreCase);
		const bool bInsertArrayPin = Body.Operation.Equals(TEXT("insert_array_pin"), ESearchCase::IgnoreCase);
		const bool bDuplicateArrayPin = Body.Operation.Equals(TEXT("duplicate_array_pin"), ESearchCase::IgnoreCase);
		const bool bRemoveArrayPin = Body.Operation.Equals(TEXT("remove_array_pin"), ESearchCase::IgnoreCase);
		const bool bClearArrayPin = Body.Operation.Equals(TEXT("clear_array_pin"), ESearchCase::IgnoreCase);
		const bool bSetArrayPinSize = Body.Operation.Equals(TEXT("set_array_pin_size"), ESearchCase::IgnoreCase);
		const bool bArrayPinOperation = bAddArrayPin || bInsertArrayPin || bDuplicateArrayPin
			|| bRemoveArrayPin || bClearArrayPin || bSetArrayPinSize;
		const bool bAddLocalVariable = Body.Operation.Equals(TEXT("add_local_variable"), ESearchCase::IgnoreCase);
		const bool bRenameLocalVariable = Body.Operation.Equals(TEXT("rename_local_variable"), ESearchCase::IgnoreCase);
		const bool bSetLocalVariableDefault = Body.Operation.Equals(TEXT("set_local_variable_default"), ESearchCase::IgnoreCase);
		const bool bRemoveLocalVariable = Body.Operation.Equals(TEXT("remove_local_variable"), ESearchCase::IgnoreCase);
		const bool bAddVariableNode = Body.Operation.Equals(TEXT("add_variable_node"), ESearchCase::IgnoreCase);
		const bool bAddReroute = Body.Operation.Equals(TEXT("add_reroute"), ESearchCase::IgnoreCase);
		const bool bAddFreeReroute = Body.Operation.Equals(TEXT("add_free_reroute"), ESearchCase::IgnoreCase);
		const bool bAddFunctionReference = Body.Operation.Equals(TEXT("add_function_reference"), ESearchCase::IgnoreCase);
		const bool bAddInvokeEntry = Body.Operation.Equals(TEXT("add_invoke_entry"), ESearchCase::IgnoreCase);
		const bool bAddInjectedNode = Body.Operation.Equals(TEXT("add_injected_node"), ESearchCase::IgnoreCase);
		const bool bRemoveInjectedNode = Body.Operation.Equals(TEXT("remove_injected_node"), ESearchCase::IgnoreCase);
		const bool bAddTemplateNode = Body.Operation.Equals(TEXT("add_template_node"), ESearchCase::IgnoreCase);
		const bool bResolveWildcardPin = Body.Operation.Equals(TEXT("resolve_wildcard_pin"), ESearchCase::IgnoreCase);
		const bool bCollapseNodes = Body.Operation.Equals(TEXT("collapse_nodes"), ESearchCase::IgnoreCase);
		const bool bExpandLibraryNode = Body.Operation.Equals(TEXT("expand_library_node"), ESearchCase::IgnoreCase);
		const bool bAddFunction = Body.Operation.Equals(TEXT("add_function"), ESearchCase::IgnoreCase);
		const bool bRemoveFunction = Body.Operation.Equals(TEXT("remove_function"), ESearchCase::IgnoreCase);
		const bool bFunctionDefinitionOperation = bAddFunction || bRemoveFunction;
		const bool bAddExposedPin = Body.Operation.Equals(TEXT("add_exposed_pin"), ESearchCase::IgnoreCase);
		const bool bRemoveExposedPin = Body.Operation.Equals(TEXT("remove_exposed_pin"), ESearchCase::IgnoreCase);
		const bool bExposedPinOperation = bAddExposedPin || bRemoveExposedPin;
		const bool bLocalVariableOperation = bAddLocalVariable || bRenameLocalVariable || bSetLocalVariableDefault
			|| bRemoveLocalVariable || bAddVariableNode;
		const bool bRemoveNode = Body.Operation.Equals(TEXT("remove_node"), ESearchCase::IgnoreCase);
		const bool bSetPosition = Body.Operation.Equals(TEXT("set_position"), ESearchCase::IgnoreCase);
		const bool bSetPin = Body.Operation.Equals(TEXT("set_pin_default"), ESearchCase::IgnoreCase);
		const bool bSetPinExpansion = Body.Operation.Equals(TEXT("set_pin_expansion"), ESearchCase::IgnoreCase);
		const bool bSetPinWatched = Body.Operation.Equals(TEXT("set_pin_watched"), ESearchCase::IgnoreCase);
		const bool bSetPinDisplayName = Body.Operation.Equals(TEXT("set_pin_display_name"), ESearchCase::IgnoreCase);
		const bool bPinEditOperation = bSetPin || bSetPinExpansion || bSetPinWatched || bSetPinDisplayName;
		const bool bAddLink = Body.Operation.Equals(TEXT("add_link"), ESearchCase::IgnoreCase);
		const bool bBreakLink = Body.Operation.Equals(TEXT("break_link"), ESearchCase::IgnoreCase);
		if (!bAddUnit && !bAddBranch && !bAddComment && !bAddConstant && !bAddMakeStruct && !bAddBreakStruct && !bAddNodeOnPin && !bAddIf && !bAddSelect && !bAddEnum && !bAddArray && !bArrayPinOperation && !bLocalVariableOperation && !bAddReroute && !bAddFreeReroute && !bAddFunctionReference && !bAddInvokeEntry && !bAddInjectedNode && !bRemoveInjectedNode && !bAddTemplateNode && !bResolveWildcardPin && !bCollapseNodes && !bExpandLibraryNode && !bExposedPinOperation && !bFunctionDefinitionOperation
			&& !bRemoveNode && !bSetPosition && !bPinEditOperation && !bAddLink && !bBreakLink)
			throw std::runtime_error("operation must add a supported RigVM node, edit a local variable or node, or edit/remove an existing node or link");
		if (!FMath::IsFinite(Body.Position.X) || !FMath::IsFinite(Body.Position.Y)) throw std::runtime_error("position must be finite");
		if (bAddComment && (Body.CommentText.IsEmpty() || !FMath::IsFinite(Body.NodeSize.X)
			|| !FMath::IsFinite(Body.NodeSize.Y) || Body.NodeSize.X <= 0.f || Body.NodeSize.Y <= 0.f))
			throw std::runtime_error("add_comment requires nonempty comment_text and positive finite node_size dimensions");
		ERigVMOpCode ArrayOpCode = ERigVMOpCode::Invalid;
		if (bAddArray)
		{
			if (Body.ArrayOperation.Equals(TEXT("reset"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayReset;
			else if (Body.ArrayOperation.Equals(TEXT("get_num"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayGetNum;
			else if (Body.ArrayOperation.Equals(TEXT("set_num"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArraySetNum;
			else if (Body.ArrayOperation.Equals(TEXT("get_at_index"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayGetAtIndex;
			else if (Body.ArrayOperation.Equals(TEXT("set_at_index"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArraySetAtIndex;
			else if (Body.ArrayOperation.Equals(TEXT("add"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayAdd;
			else if (Body.ArrayOperation.Equals(TEXT("insert"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayInsert;
			else if (Body.ArrayOperation.Equals(TEXT("remove"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayRemove;
			else if (Body.ArrayOperation.Equals(TEXT("find"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayFind;
			else if (Body.ArrayOperation.Equals(TEXT("append"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayAppend;
			else if (Body.ArrayOperation.Equals(TEXT("clone"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayClone;
			else if (Body.ArrayOperation.Equals(TEXT("iterator"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayIterator;
			else if (Body.ArrayOperation.Equals(TEXT("union"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayUnion;
			else if (Body.ArrayOperation.Equals(TEXT("difference"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayDifference;
			else if (Body.ArrayOperation.Equals(TEXT("intersection"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayIntersection;
			else if (Body.ArrayOperation.Equals(TEXT("reverse"), ESearchCase::IgnoreCase)) ArrayOpCode = ERigVMOpCode::ArrayReverse;
			if (ArrayOpCode == ERigVMOpCode::Invalid)
				throw std::runtime_error("array_operation must be reset, get_num, set_num, get_at_index, set_at_index, add, insert, remove, find, append, clone, iterator, union, difference, intersection, or reverse");
			if (Body.CPPType.IsEmpty()) throw std::runtime_error("cpp_type is required for array nodes");
		}
		if (bAddFreeReroute)
		{
			if (Cast<URigVMFunctionLibrary>(Graph)) throw std::runtime_error("reroute nodes cannot be added to the function library graph");
			if (Body.CPPType.IsEmpty()) throw std::runtime_error("cpp_type is required for add_free_reroute");
			if (!Body.CPPTypeObjectPath.IsEmpty() && !LoadObject<UObject>(nullptr, *Body.CPPTypeObjectPath))
				throw std::runtime_error("cpp_type_object_path must reference a loaded type object for add_free_reroute");
		}
		if (bAddEnum && (Body.CPPTypeObjectPath.IsEmpty() || !LoadObject<UEnum>(nullptr, *Body.CPPTypeObjectPath)))
			throw std::runtime_error("cpp_type_object_path must identify a loaded enum for add_enum");
		if (bAddInvokeEntry && (Body.EntryName.IsEmpty() || !Controller->GetAllEventNames().Contains(FName(*Body.EntryName))))
			throw std::runtime_error("entry_name must identify an existing Control Rig event");
		if (bAddTemplateNode)
		{
			const TArray<FString> RegisteredTemplates = URigVMController::GetRegisteredTemplates();
			if (Body.TemplateNotation.IsEmpty() || !RegisteredTemplates.Contains(Body.TemplateNotation))
				throw std::runtime_error("template_notation must identify a registered RigVM template");
			if (!Body.NodeName.IsEmpty() && Graph->FindNode(Body.NodeName))
				throw std::runtime_error("node_name already exists");
		}
		URigVMPin* WildcardPin = nullptr;
		FString WildcardNodeName;
		if (bResolveWildcardPin)
		{
			WildcardPin = Body.PinPath.IsEmpty() ? nullptr : Graph->FindPin(Body.PinPath);
			if (!WildcardPin) throw std::runtime_error("pin_path must identify a graph pin");
			if (!WildcardPin->IsWildCard()) throw std::runtime_error("pin_path must identify an unresolved wildcard pin");
			if (!Cast<URigVMTemplateNode>(WildcardPin->GetNode()))
				throw std::runtime_error("pin_path must identify a wildcard pin on a RigVM template node");
			if (Body.CPPType.IsEmpty()) throw std::runtime_error("cpp_type is required to resolve a wildcard pin");
			if (!Body.CPPTypeObjectPath.IsEmpty() && !LoadObject<UObject>(nullptr, *Body.CPPTypeObjectPath))
				throw std::runtime_error("cpp_type_object_path must reference a loaded type object");
			if (WildcardPin->GetNode()) WildcardNodeName = WildcardPin->GetNode()->GetName();
		}
		URigVMPin* ArrayPin = nullptr;
		URigVMPin* ArrayElementPin = nullptr;
		FString ArrayPinPath;
		FString ArrayElementResultPath;
		FString ArrayNodeName;
		int32 ArraySizeBefore = 0;
		int32 ArraySizeAfter = 0;
		bool bArrayPinRemovalRequiresConfirm = false;
		if (bArrayPinOperation)
		{
			if (bRemoveArrayPin || bDuplicateArrayPin)
			{
				ArrayElementPin = Body.PinPath.IsEmpty() ? nullptr : Graph->FindPin(Body.PinPath);
				if (!ArrayElementPin || !ArrayElementPin->IsArrayElement())
					throw std::runtime_error("pin_path must identify an array element pin");
				ArrayPin = ArrayElementPin->GetParentPin();
			}
			else
			{
				ArrayPin = Body.PinPath.IsEmpty() ? nullptr : Graph->FindPin(Body.PinPath);
			}
			if (!ArrayPin || !ArrayPin->IsArray())
				throw std::runtime_error("pin_path must identify an array pin or one of its elements");
			ArrayPinPath = ArrayPin->GetPinPath();
			ArrayNodeName = ArrayPin->GetNode() ? ArrayPin->GetNode()->GetName() : FString();
			ArraySizeBefore = ArrayPin->GetSubPins().Num();
			ArraySizeAfter = ArraySizeBefore;
			if (bAddArrayPin || bDuplicateArrayPin) ArraySizeAfter++;
			else if (bInsertArrayPin)
			{
				if (Body.ArrayIndex < INDEX_NONE || Body.ArrayIndex > ArraySizeBefore)
					throw std::runtime_error("array_index must be -1 to append or a valid insertion index");
				ArraySizeAfter++;
			}
			else if (bRemoveArrayPin)
			{
				if (ArrayPin->IsFixedSizeArray() && ArraySizeBefore <= 1)
					throw std::runtime_error("cannot remove the last element of a fixed-size array");
				ArraySizeAfter--;
				bArrayPinRemovalRequiresConfirm = true;
			}
			else if (bClearArrayPin)
			{
				if (ArrayPin->IsFixedSizeArray() && ArraySizeBefore > 0)
					throw std::runtime_error("cannot clear a fixed-size array pin");
				ArraySizeAfter = 0;
				bArrayPinRemovalRequiresConfirm = ArraySizeAfter < ArraySizeBefore;
			}
			else if (bSetArrayPinSize)
			{
				if (Body.ArraySize < 0 || Body.ArraySize > 256)
					throw std::runtime_error("array_size must be an integer from 0 through 256");
				if (ArrayPin->IsFixedSizeArray() && Body.ArraySize == 0 && ArraySizeBefore > 0)
					throw std::runtime_error("cannot resize a fixed-size array pin to zero elements");
				ArraySizeAfter = Body.ArraySize;
				bArrayPinRemovalRequiresConfirm = ArraySizeAfter < ArraySizeBefore;
			}
			if (bRemoveArrayPin || bClearArrayPin || (bSetArrayPinSize && ArraySizeAfter < ArraySizeBefore))
				bArrayPinRemovalRequiresConfirm |= ArraySizeAfter < ArraySizeBefore;
		}
		URigVMPin* NodeOnPinTarget = nullptr;
		FString NodeOnPinTargetPath;
		int32 NodeOnPinAffectedLinks = 0;
		bool bNodeOnPinRequiresConfirm = false;
		if (bAddNodeOnPin)
		{
			NodeOnPinTarget = Body.PinPath.IsEmpty() ? nullptr : Graph->FindPin(Body.PinPath);
			if (!NodeOnPinTarget) throw std::runtime_error("pin_path must identify a graph pin");
			NodeOnPinTargetPath = NodeOnPinTarget->GetPinPath();
			if (!Body.NodeName.IsEmpty() && Graph->FindNode(Body.NodeName))
				throw std::runtime_error("node_name already exists");
			if (bAddConstantOnPin || bAddMakeStructOnPin)
			{
				if (NodeOnPinTarget->GetDirection() != ERigVMPinDirection::Input
					&& NodeOnPinTarget->GetDirection() != ERigVMPinDirection::IO)
					throw std::runtime_error("constant and make-struct nodes require an input or IO pin");
			}
			if (bAddBreakStructOnPin && NodeOnPinTarget->GetDirection() != ERigVMPinDirection::Output
				&& NodeOnPinTarget->GetDirection() != ERigVMPinDirection::IO)
				throw std::runtime_error("break-struct nodes require an output or IO pin");
			if (bAddMakeStructOnPin || bAddBreakStructOnPin)
				if (!NodeOnPinTarget->IsStruct()) throw std::runtime_error("make/break-struct nodes require a struct pin");
			if (bAddRerouteOnPin)
			{
				const ERigVMPinDirection RequiredDirection = Body.bRerouteAsInput
					? ERigVMPinDirection::Input : ERigVMPinDirection::Output;
				if (NodeOnPinTarget->GetDirection() != RequiredDirection
					&& NodeOnPinTarget->GetDirection() != ERigVMPinDirection::IO)
					throw std::runtime_error("reroute_as_input must match the pin direction");
				if (Cast<URigVMFunctionLibrary>(Graph))
					throw std::runtime_error("reroute nodes cannot be added to the function library graph");
			}
			const FString DescendantPrefix = NodeOnPinTargetPath + TEXT(".");
			for (const URigVMLink* Link : Graph->GetLinks())
				if (Link && (Link->GetTargetPinPath() == NodeOnPinTargetPath
					|| Link->GetTargetPinPath().StartsWith(DescendantPrefix, ESearchCase::CaseSensitive)))
					++NodeOnPinAffectedLinks;
			bNodeOnPinRequiresConfirm = NodeOnPinAffectedLinks > 0
				&& (bAddConstantOnPin || bAddMakeStructOnPin || (bAddRerouteOnPin && Body.bRerouteAsInput));
		}
		TArray<FName> NodeNamesToCollapse;
		TSet<FName> NodeNamesToCollapseSet;
		int32 CollapseInternalLinkCount = 0;
		int32 CollapseBoundaryLinkCount = 0;
		if (bCollapseNodes)
		{
			if (Cast<URigVMFunctionLibrary>(Graph))
				throw std::runtime_error("nodes cannot be collapsed inside the function library graph");
			if (Body.NodeNames.IsEmpty()) throw std::runtime_error("node_names must contain at least one graph node");
			if (!Body.NodeName.IsEmpty() && Graph->FindNode(Body.NodeName))
				throw std::runtime_error("node_name already exists");
			for (const FString& RequestedNodeName : Body.NodeNames)
			{
				const FName RequestedName(*RequestedNodeName);
				if (RequestedName.IsNone() || NodeNamesToCollapseSet.Contains(RequestedName))
					throw std::runtime_error("node_names must contain unique, nonempty node names");
				URigVMNode* RequestedNode = Graph->FindNodeByName(RequestedName);
				if (!RequestedNode) throw std::runtime_error("node_names contains a name that is not in graph_path");
				if (RequestedNode->IsEvent() || RequestedNode->IsA<URigVMFunctionInterfaceNode>())
					throw std::runtime_error("event and function-interface nodes cannot be collapsed");
				if (const URigVMVariableNode* VariableNode = Cast<URigVMVariableNode>(RequestedNode))
					if (VariableNode->IsInputArgument())
						throw std::runtime_error("function input arguments cannot be collapsed");
				NodeNamesToCollapseSet.Add(RequestedName);
				NodeNamesToCollapse.Add(RequestedName);
			}
			for (const URigVMLink* Link : Graph->GetLinks())
			{
				if (!Link || !Link->GetSourcePin() || !Link->GetTargetPin()) continue;
				const bool bSourceSelected = NodeNamesToCollapseSet.Contains(Link->GetSourcePin()->GetNode()->GetFName());
				const bool bTargetSelected = NodeNamesToCollapseSet.Contains(Link->GetTargetPin()->GetNode()->GetFName());
				if (bSourceSelected && bTargetSelected) ++CollapseInternalLinkCount;
				else if (bSourceSelected || bTargetSelected) ++CollapseBoundaryLinkCount;
			}
		}
		URigVMCollapseNode* CollapseNodeToExpand = nullptr;
		int32 ExpandContainedNodeCount = 0;
		if (bExpandLibraryNode)
		{
			if (Body.NodeName.IsEmpty() || !(CollapseNodeToExpand = Cast<URigVMCollapseNode>(Graph->FindNode(Body.NodeName))))
				throw std::runtime_error("node_name must identify a collapse node in graph_path");
			const URigVMGraph* ContainedGraph = CollapseNodeToExpand->GetContainedGraph();
			if (!ContainedGraph) throw std::runtime_error("collapse node has no contained RigVM graph");
			for (const URigVMNode* ContainedNode : ContainedGraph->GetNodes())
			{
				if (!ContainedNode || ContainedNode->IsInjected()
					|| ContainedNode->IsA<URigVMFunctionEntryNode>()
					|| ContainedNode->IsA<URigVMFunctionReturnNode>()) continue;
				if (const URigVMVariableNode* VariableNode = Cast<URigVMVariableNode>(ContainedNode))
					if (VariableNode->IsInputArgument()) continue;
				++ExpandContainedNodeCount;
			}
			if (ExpandContainedNodeCount == 0) throw std::runtime_error("collapse node has no contained nodes to expand");
		}
		UScriptStruct* InjectionUnitStruct = nullptr;
		URigVMPin* InjectionPin = nullptr;
		URigVMInjectionInfo* InjectionToRemove = nullptr;
		int32 InjectionCount = 0;
		if (bAddInjectedNode || bRemoveInjectedNode)
		{
			if (Cast<URigVMFunctionLibrary>(Graph)) throw std::runtime_error("injected nodes cannot be edited in the function library graph");
			if (Body.PinPath.IsEmpty() || !(InjectionPin = Graph->FindPin(Body.PinPath)))
				throw std::runtime_error("pin_path must identify the pin to inject into");
			if (bAddInjectedNode)
			{
				if (InjectionPin->IsArray()) throw std::runtime_error("injected nodes cannot be added to array pins");
				if (Body.InjectionInputPinName.IsEmpty() || Body.InjectionOutputPinName.IsEmpty())
					throw std::runtime_error("injection_input_pin_name and injection_output_pin_name are required");
				if (Body.bInjectedAsInput && InjectionPin->GetDirection() != ERigVMPinDirection::Input
					&& InjectionPin->GetDirection() != ERigVMPinDirection::IO)
					throw std::runtime_error("an input injection requires an input or IO pin");
				if (!Body.bInjectedAsInput && InjectionPin->GetDirection() != ERigVMPinDirection::Output)
					throw std::runtime_error("an output injection requires an output pin");
				InjectionUnitStruct = LoadObject<UScriptStruct>(nullptr, *Body.UnitStructPath);
				if (!InjectionUnitStruct || !InjectionUnitStruct->IsChildOf(FRigVMStruct::StaticStruct()))
					throw std::runtime_error("unit_struct_path must reference a RigVM unit struct");
				const FName MethodName = Body.MethodName.IsEmpty() ? FName(TEXT("Execute")) : FName(*Body.MethodName);
				if (MethodName.IsNone()) throw std::runtime_error("method_name is required for injected nodes");
				const FProperty* InputProperty = InjectionUnitStruct->FindPropertyByName(FName(*Body.InjectionInputPinName));
				const FProperty* OutputProperty = InjectionUnitStruct->FindPropertyByName(FName(*Body.InjectionOutputPinName));
				if (!InputProperty || !InputProperty->HasMetaData(FRigVMStruct::InputMetaName))
					throw std::runtime_error("injection_input_pin_name must identify an input property on the unit struct");
				if (!OutputProperty || !OutputProperty->HasMetaData(FRigVMStruct::OutputMetaName))
					throw std::runtime_error("injection_output_pin_name must identify an output property on the unit struct");
				const bool bInputArray = CastField<FArrayProperty>(InputProperty) != nullptr;
				const bool bOutputArray = CastField<FArrayProperty>(OutputProperty) != nullptr;
				if (InputProperty->GetCPPType() != OutputProperty->GetCPPType() || bInputArray != bOutputArray
					|| InputProperty->GetCPPType() != InjectionPin->GetCPPType() || bInputArray != InjectionPin->IsArray())
					throw std::runtime_error("injected unit input/output types must match each other and the target pin");
				if (!Body.NodeName.IsEmpty() && Graph->FindNode(Body.NodeName)) throw std::runtime_error("node_name already exists");
			}
			else
			{
				const TArray<URigVMInjectionInfo*> Injections = InjectionPin->GetInjectedNodes();
				InjectionCount = Injections.Num();
				if (Injections.IsEmpty()) throw std::runtime_error("pin_path has no injected node to remove");
				InjectionToRemove = Injections.Last();
				if (!InjectionToRemove || InjectionToRemove->bInjectedAsInput != Body.bInjectedAsInput)
					throw std::runtime_error("b_injected_as_input does not match the last injected node on pin_path");
			}
		}
		ERigVMPinDirection ExposedPinDirection = ERigVMPinDirection::Invalid;
		URigVMCollapseNode* FunctionNode = nullptr;
		if (bExposedPinOperation)
		{
			if (Body.ExposedPinName.IsEmpty()) throw std::runtime_error("exposed_pin_name is required");
			FunctionNode = Cast<URigVMCollapseNode>(Graph->GetOuter());
			if (!FunctionNode || FunctionNode->GetContainedGraph() != Graph)
				throw std::runtime_error("exposed pin operations require a function graph");
			const URigVMPin* ExistingExposedPin = FunctionNode->FindPin(Body.ExposedPinName);
			if (bAddExposedPin)
			{
				if (ExistingExposedPin) throw std::runtime_error("exposed_pin_name already exists on this function");
				if (Body.CPPType.IsEmpty()) throw std::runtime_error("cpp_type is required for add_exposed_pin");
				for (const FRigVMGraphVariableDescription& Variable : Graph->GetLocalVariables(true))
					if (Variable.Name == FName(*Body.ExposedPinName)) throw std::runtime_error("exposed_pin_name conflicts with a local variable or argument");
				if (Body.PinDirection.Equals(TEXT("input"), ESearchCase::IgnoreCase)) ExposedPinDirection = ERigVMPinDirection::Input;
				else if (Body.PinDirection.Equals(TEXT("output"), ESearchCase::IgnoreCase)) ExposedPinDirection = ERigVMPinDirection::Output;
				else throw std::runtime_error("pin_direction must be input or output");
			}
			else if (!ExistingExposedPin || (ExistingExposedPin->GetDirection() != ERigVMPinDirection::Input
				&& ExistingExposedPin->GetDirection() != ERigVMPinDirection::Output))
				throw std::runtime_error("exposed_pin_name does not identify an input or output function pin");
		}
		URigVMLink* LinkToReroute = nullptr;
		if (bAddReroute)
		{
			if (Body.SourcePinPath.IsEmpty() || Body.TargetPinPath.IsEmpty())
				throw std::runtime_error("add_reroute requires source_pin_path and target_pin_path");
			if (Cast<URigVMFunctionLibrary>(Graph)) throw std::runtime_error("reroute nodes cannot be added to the function library graph");
			for (URigVMLink* Candidate : Graph->GetLinks())
				if (Candidate && Candidate->GetSourcePinPath() == Body.SourcePinPath && Candidate->GetTargetPinPath() == Body.TargetPinPath)
					{ LinkToReroute = Candidate; break; }
			if (!LinkToReroute) throw std::runtime_error("source_pin_path and target_pin_path must identify an existing link");
		}
		URigVMLibraryNode* FunctionDefinition = nullptr;
		if (bAddFunctionReference)
		{
			if (Body.FunctionName.IsEmpty()) throw std::runtime_error("function_name is required");
			for (URigVMGraph* CandidateGraph : VM->GetAllModels())
			{
				if (!CandidateGraph || !Cast<URigVMFunctionLibrary>(CandidateGraph)) continue;
				FunctionDefinition = Cast<URigVMLibraryNode>(CandidateGraph->FindNode(Body.FunctionName));
				if (FunctionDefinition) break;
			}
			if (!FunctionDefinition) throw std::runtime_error("function_name must identify an existing RigVM function in the library");
			if (FunctionDefinition->GetContainedGraph() == Graph)
				throw std::runtime_error("a RigVM function cannot reference itself");
		}
		URigVMFunctionLibrary* FunctionLibraryGraph = nullptr;
		int32 AffectedFunctionReferences = 0;
		if (bFunctionDefinitionOperation)
		{
			FunctionLibraryGraph = Cast<URigVMFunctionLibrary>(Graph);
			if (!FunctionLibraryGraph) throw std::runtime_error("function definitions can only be added or removed from the function library graph");
			if (Body.FunctionName.IsEmpty()) throw std::runtime_error("function_name is required");
			const URigVMLibraryNode* ExistingFunction = FunctionLibraryGraph->FindFunction(FName(*Body.FunctionName));
			if (bAddFunction && ExistingFunction) throw std::runtime_error("function_name already exists in this library");
			if (bRemoveFunction && !ExistingFunction) throw std::runtime_error("function_name does not identify a function in this library");
			if (bRemoveFunction)
				FunctionLibraryGraph->ForEachReference(FName(*Body.FunctionName), [&AffectedFunctionReferences](URigVMFunctionReferenceNode*)
					{ ++AffectedFunctionReferences; });
		}
		TArray<FRigVMGraphVariableDescription> LocalVariables;
		const FRigVMGraphVariableDescription* LocalVariable = nullptr;
		int32 AffectedVariableNodes = 0;
		if (bLocalVariableOperation)
		{
			const URigVMCollapseNode* FunctionNodeForVariable = Cast<URigVMCollapseNode>(Graph->GetOuter());
			if (!FunctionNodeForVariable || FunctionNodeForVariable->GetContainedGraph() != Graph)
				throw std::runtime_error("local variable operations require a function graph");
			if (Body.VariableName.IsEmpty()) throw std::runtime_error("variable_name is required");
			LocalVariables = Graph->GetLocalVariables();
			LocalVariable = LocalVariables.FindByPredicate([&Body](const FRigVMGraphVariableDescription& Candidate)
				{ return Candidate.Name == FName(*Body.VariableName); });
			if (bAddLocalVariable)
			{
				if (LocalVariable) throw std::runtime_error("a local variable with variable_name already exists");
				if (Body.CPPType.IsEmpty()) throw std::runtime_error("cpp_type is required for add_local_variable");
			}
			else if (!LocalVariable)
				throw std::runtime_error("variable_name does not identify a local variable in this function graph");
			if (bRenameLocalVariable)
			{
				if (Body.NewVariableName.IsEmpty() || Body.NewVariableName == Body.VariableName)
					throw std::runtime_error("new_variable_name must be a nonempty name different from variable_name");
				for (const FRigVMGraphVariableDescription& Candidate : Graph->GetLocalVariables(true))
					if (Candidate.Name == FName(*Body.NewVariableName)) throw std::runtime_error("new_variable_name already exists in this function graph");
			}
			if (bAddVariableNode)
			{
				if (!Body.NodeName.IsEmpty() && Graph->FindNode(Body.NodeName)) throw std::runtime_error("node_name already exists");
			}
			if (bRemoveLocalVariable)
			{
				for (const URigVMNode* Candidate : Graph->GetNodes())
					if (const URigVMVariableNode* VariableNode = Cast<URigVMVariableNode>(Candidate))
						AffectedVariableNodes += VariableNode->GetVariableName() == LocalVariable->Name ? 1 : 0;
			}
		}
		URigVMNode* Node = nullptr;
		if (bRemoveNode || bSetPosition)
		{
			for (URigVMNode* Candidate : Graph->GetNodes())
				if (Candidate && Candidate->GetName() == Body.NodeName) { Node = Candidate; break; }
			if (!Node) throw std::runtime_error("node_name does not identify a graph node");
		}
		UScriptStruct* UnitStruct = nullptr;
		if (bAddUnit || bAddBranch || bAddComment || bAddConstant || bAddMakeStruct || bAddBreakStruct || bAddIf || bAddSelect || bAddEnum || bAddArray || bAddVariableNode || bAddReroute || bAddFreeReroute || bAddFunctionReference || bAddInvokeEntry || bAddInjectedNode || bAddTemplateNode)
		{
			if (bAddUnit)
			{
				UnitStruct = LoadObject<UScriptStruct>(nullptr, *Body.UnitStructPath);
				if (!UnitStruct || !UnitStruct->IsChildOf(FRigVMStruct::StaticStruct()))
					throw std::runtime_error("unit_struct_path must reference a RigVM unit struct");
			}
			if ((bAddConstant || bAddMakeStruct || bAddBreakStruct || bAddIf || bAddSelect) && Body.CPPType.IsEmpty())
				throw std::runtime_error("cpp_type is required for typed RigVM nodes");
			if ((bAddMakeStruct || bAddBreakStruct) && !LoadObject<UScriptStruct>(nullptr, *Body.CPPTypeObjectPath))
				throw std::runtime_error("cpp_type_object_path must reference a loaded struct for make/break struct nodes");
			if (!Body.NodeName.IsEmpty() && Graph->FindNode(Body.NodeName))
				throw std::runtime_error("node_name already exists");
		}
		URigVMPin* PinToEdit = nullptr;
		if (bPinEditOperation)
		{
			PinToEdit = Body.PinPath.IsEmpty() ? nullptr : Graph->FindPin(Body.PinPath);
			if (!PinToEdit) throw std::runtime_error("pin_path does not identify a graph pin");
			if (bSetPinExpansion && PinToEdit->GetSubPins().IsEmpty())
				throw std::runtime_error("set_pin_expansion requires a pin with subpins");
			if (bSetPinWatched)
			{
				if (PinToEdit->GetParentPin()) throw std::runtime_error("set_pin_watched requires a root pin");
				if (PinToEdit->RequiresWatch() == Body.bPinWatched)
					throw std::runtime_error("pin watched state already matches b_pin_watched");
			}
		}
		if (bAddLink || bBreakLink)
		{
			if (!Graph->FindPin(Body.SourcePinPath) || !Graph->FindPin(Body.TargetPinPath))
				throw std::runtime_error("source_pin_path and target_pin_path must identify graph pins");
			const bool bExists = Graph->GetLinks().ContainsByPredicate([&Body](const URigVMLink* Link)
				{ return Link && Link->GetSourcePinPath() == Body.SourcePinPath && Link->GetTargetPinPath() == Body.TargetPinPath; });
			if (bAddLink && bExists) throw std::runtime_error("link already exists");
			if (bBreakLink && !bExists) throw std::runtime_error("link does not exist");
		}
		if (Body.bDryRun)
		{
			if (bCollapseNodes)
			{
				FString Preview;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Preview);
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("changed"), false);
				Writer->WriteValue(TEXT("dry_run"), true);
				Writer->WriteValue(TEXT("would_change"), true);
				Writer->WriteValue(TEXT("selected_node_count"), NodeNamesToCollapse.Num());
				Writer->WriteValue(TEXT("internal_link_count"), CollapseInternalLinkCount);
				Writer->WriteValue(TEXT("boundary_link_count"), CollapseBoundaryLinkCount);
				Writer->WriteObjectEnd();
				Writer->Close();
				return C.TextResponse(Preview, TEXT("application/json"));
			}
			if (bExpandLibraryNode)
				return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"would_change\":true,\"node_name\":\"%s\",\"expanded_node_count\":%d}"), *Body.NodeName, ExpandContainedNodeCount), TEXT("application/json"));
			if (bAddNodeOnPin)
			{
				FString Preview;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Preview);
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("changed"), false);
				Writer->WriteValue(TEXT("dry_run"), true);
				Writer->WriteValue(TEXT("would_change"), true);
				Writer->WriteValue(TEXT("pin_path"), NodeOnPinTargetPath);
				Writer->WriteValue(TEXT("affected_pin_links"), NodeOnPinAffectedLinks);
				Writer->WriteValue(TEXT("requires_confirmation"), bNodeOnPinRequiresConfirm);
				Writer->WriteObjectEnd();
				Writer->Close();
				return C.TextResponse(Preview, TEXT("application/json"));
			}
			if (bArrayPinOperation)
			{
				FString Preview;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Preview);
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("changed"), false);
				Writer->WriteValue(TEXT("dry_run"), true);
				Writer->WriteValue(TEXT("would_change"), ArraySizeAfter != ArraySizeBefore);
				Writer->WriteValue(TEXT("node_name"), ArrayNodeName);
				Writer->WriteValue(TEXT("array_pin_path"), ArrayPinPath);
				Writer->WriteValue(TEXT("array_size_before"), ArraySizeBefore);
				Writer->WriteValue(TEXT("array_size_after"), ArraySizeAfter);
				Writer->WriteValue(TEXT("affected_array_elements"), FMath::Abs(ArraySizeAfter - ArraySizeBefore));
				Writer->WriteObjectEnd();
				Writer->Close();
				return C.TextResponse(Preview, TEXT("application/json"));
			}
			if (bRemoveInjectedNode)
			{
				FString Preview;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Preview);
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("changed"), false);
				Writer->WriteValue(TEXT("dry_run"), true);
				Writer->WriteValue(TEXT("affected_injected_nodes"), 1);
				Writer->WriteValue(TEXT("injected_node_count"), InjectionCount);
				Writer->WriteObjectEnd();
				Writer->Close();
				return C.TextResponse(Preview, TEXT("application/json"));
			}
			if (bRemoveLocalVariable)
				return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"affected_variable_nodes\":%d}"), AffectedVariableNodes), TEXT("application/json"));
			if (bRemoveExposedPin)
				return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"exposed_pin_name\":\"%s\"}"), *Body.ExposedPinName), TEXT("application/json"));
			if (bRemoveFunction)
				return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"function_name\":\"%s\",\"affected_function_references\":%d}"), *Body.FunctionName, AffectedFunctionReferences), TEXT("application/json"));
			return C.TextResponse(TEXT("{\"changed\":false,\"dry_run\":true}"), TEXT("application/json"));
		}
		if (bRemoveFunction && AffectedFunctionReferences > 0)
			throw std::runtime_error("remove references to this function before removing its definition");
		if ((bRemoveNode || bRemoveLocalVariable || bRemoveExposedPin || bRemoveFunction
			|| bRemoveInjectedNode || bArrayPinRemovalRequiresConfirm || bNodeOnPinRequiresConfirm
			|| bExpandLibraryNode) && !Body.bConfirm)
			throw std::runtime_error(bRemoveInjectedNode ? "injected node removal requires confirm=true"
				: bRemoveLocalVariable ? "local variable removal requires confirm=true"
				: bRemoveExposedPin ? "exposed pin removal requires confirm=true"
				: bRemoveFunction ? "function removal requires confirm=true"
				: bArrayPinRemovalRequiresConfirm ? "array pin removal or shrink requires confirm=true"
				: bNodeOnPinRequiresConfirm ? "replacing pin links requires confirm=true"
				: bExpandLibraryNode ? "expanding a collapse node requires confirm=true"
				: "RigVM node removal requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditControlRigGraph", "Edit Control Rig Graph"));
		Asset->Modify();
		Graph->Modify();
		FString ResultNode = Body.NodeName;
		if (bRemoveInjectedNode && InjectionToRemove->Node) ResultNode = InjectionToRemove->Node->GetName();
		FString CollapseContainedGraphPath;
		TArray<FString> ExpandedNodeNames;
		bool bChanged = false;
		if (bCollapseNodes)
		{
			URigVMCollapseNode* CollapseNode = Controller->CollapseNodes(
				NodeNamesToCollapse, Body.NodeName, false, false, false);
			if (!CollapseNode) throw std::runtime_error("RigVM controller rejected the selected nodes for collapse");
			ResultNode = CollapseNode->GetName();
			if (const URigVMGraph* ContainedGraph = CollapseNode->GetContainedGraph())
				CollapseContainedGraphPath = ContainedGraph->GetNodePath();
			bChanged = true;
		}
		else if (bExpandLibraryNode)
		{
			const TArray<URigVMNode*> ExpandedNodes = Controller->ExpandLibraryNode(FName(*Body.NodeName), false, false);
			if (ExpandedNodes.IsEmpty()) throw std::runtime_error("RigVM controller failed to expand the collapse node");
			for (const URigVMNode* ExpandedNode : ExpandedNodes)
				if (ExpandedNode) ExpandedNodeNames.Add(ExpandedNode->GetName());
			ResultNode = Body.NodeName;
			bChanged = true;
		}
		else if (bAddNodeOnPin)
		{
			const bool bSetupUndoRedo = bNodeOnPinRequiresConfirm;
			URigVMNode* NewNode = nullptr;
			if (bAddConstantOnPin)
				NewNode = Controller->AddConstantNodeOnPin(NodeOnPinTargetPath, Body.Position, Body.NodeName, bSetupUndoRedo);
			else if (bAddMakeStructOnPin)
				NewNode = Controller->AddMakeStructNodeOnPin(NodeOnPinTargetPath, Body.Position, Body.NodeName, bSetupUndoRedo);
			else if (bAddBreakStructOnPin)
				NewNode = Controller->AddBreakStructNodeOnPin(NodeOnPinTargetPath, Body.Position, Body.NodeName, bSetupUndoRedo);
			else NewNode = Controller->AddRerouteNodeOnPin(NodeOnPinTargetPath, Body.bRerouteAsInput,
				Body.Position, Body.NodeName, bSetupUndoRedo, false);
			if (!NewNode) throw std::runtime_error("RigVM controller failed to add a node on the pin");
			ResultNode = NewNode->GetName();
			bChanged = true;
		}
		else if (bArrayPinOperation)
		{
			ResultNode = ArrayNodeName;
			if (bAddArrayPin)
				ArrayElementResultPath = Controller->AddArrayPin(ArrayPinPath, Body.DefaultValue, true, false);
			else if (bInsertArrayPin)
				ArrayElementResultPath = Controller->InsertArrayPin(ArrayPinPath, Body.ArrayIndex, Body.DefaultValue, true, false);
			else if (bDuplicateArrayPin)
				ArrayElementResultPath = Controller->DuplicateArrayPin(Body.PinPath, true, false);
			else if (bRemoveArrayPin)
				bChanged = Controller->RemoveArrayPin(Body.PinPath, true, false);
			else if (bClearArrayPin)
				bChanged = Controller->ClearArrayPin(ArrayPinPath, true, false);
			else bChanged = Controller->SetArrayPinSize(ArrayPinPath, Body.ArraySize, Body.DefaultValue, true, false);
			if (!ArrayElementResultPath.IsEmpty()) bChanged = true;
		}
		else if (bAddUnit || bAddBranch || bAddComment || bAddConstant || bAddMakeStruct || bAddBreakStruct || bAddIf || bAddSelect || bAddEnum || bAddArray || bAddVariableNode || bAddReroute || bAddFreeReroute || bAddFunctionReference || bAddInvokeEntry || bAddInjectedNode || bAddTemplateNode)
		{
			URigVMNode* NewNode = nullptr;
			if (bAddUnit)
			{
				const FName Method = Body.MethodName.IsEmpty() ? FName(TEXT("Execute")) : FName(*Body.MethodName);
				NewNode = Controller->AddUnitNode(UnitStruct, Method, Body.Position, Body.NodeName, false, false);
			}
			else if (bAddBranch)
				NewNode = Controller->AddBranchNode(Body.Position, Body.NodeName, false, false);
			else if (bAddComment)
				NewNode = Controller->AddCommentNode(Body.CommentText, Body.Position, Body.NodeSize,
					FLinearColor::Black, Body.NodeName, false, false);
			else if (bAddConstant)
				NewNode = Controller->AddConstantNode(Body.CPPType, FName(*Body.CPPTypeObjectPath),
					Body.DefaultValue, Body.Position, Body.NodeName, false);
			else if (bAddMakeStruct)
				NewNode = Controller->AddMakeStructNode(Body.CPPType, FName(*Body.CPPTypeObjectPath),
					Body.DefaultValue, Body.Position, Body.NodeName, false);
			else if (bAddBreakStruct)
				NewNode = Controller->AddBreakStructNode(Body.CPPType, FName(*Body.CPPTypeObjectPath),
					Body.DefaultValue, Body.Position, Body.NodeName, false);
			else if (bAddIf)
				NewNode = Controller->AddIfNode(Body.CPPType, FName(*Body.CPPTypeObjectPath), Body.Position, Body.NodeName, false, false);
			else if (bAddSelect)
				NewNode = Controller->AddSelectNode(Body.CPPType, FName(*Body.CPPTypeObjectPath), Body.Position, Body.NodeName, false, false);
			else if (bAddEnum)
				NewNode = Controller->AddEnumNode(FName(*Body.CPPTypeObjectPath), Body.Position, Body.NodeName, false, false);
			else if (bAddArray)
				NewNode = Controller->AddArrayNodeFromObjectPath(ArrayOpCode, Body.CPPType,
					Body.CPPTypeObjectPath, Body.Position, Body.NodeName, false, false);
			else if (bAddReroute)
				NewNode = Controller->AddRerouteNodeOnLink(LinkToReroute, Body.Position, Body.NodeName, false, false);
			else if (bAddFreeReroute)
				NewNode = Controller->AddFreeRerouteNode(Body.CPPType, FName(*Body.CPPTypeObjectPath),
					Body.bRerouteConstant, FName(*Body.CustomWidgetName), Body.DefaultValue,
					Body.Position, Body.NodeName, false);
			else if (bAddFunctionReference)
				NewNode = Controller->AddFunctionReferenceNode(FunctionDefinition, Body.Position, Body.NodeName, false, false);
			else if (bAddInvokeEntry)
				NewNode = Controller->AddInvokeEntryNode(FName(*Body.EntryName), Body.Position, Body.NodeName, false, false);
			else if (bAddTemplateNode)
				NewNode = Controller->AddTemplateNode(FName(*Body.TemplateNotation), Body.Position, Body.NodeName, false, false);
			else if (bAddInjectedNode)
			{
				const FName Method = Body.MethodName.IsEmpty() ? FName(TEXT("Execute")) : FName(*Body.MethodName);
				URigVMInjectionInfo* AddedInjection = Controller->AddInjectedNode(Body.PinPath,
					Body.bInjectedAsInput, InjectionUnitStruct, Method, FName(*Body.InjectionInputPinName),
					FName(*Body.InjectionOutputPinName), Body.NodeName, false, false);
				if (AddedInjection) NewNode = AddedInjection->Node;
			}
			else
			{
				const FString VariableTypeObjectPath = LocalVariable->CPPTypeObjectPath.IsNone()
					? FString() : LocalVariable->CPPTypeObjectPath.ToString();
				NewNode = Controller->AddVariableNodeFromObjectPath(LocalVariable->Name, LocalVariable->CPPType,
					VariableTypeObjectPath, Body.bIsGetter, LocalVariable->DefaultValue,
					Body.Position, Body.NodeName, false, false);
			}
			if (!NewNode) throw std::runtime_error("failed to add RigVM node");
			ResultNode = NewNode->GetName();
			bChanged = true;
		}
		else if (bAddLocalVariable)
		{
			const FRigVMGraphVariableDescription Added = Controller->AddLocalVariableFromObjectPath(
				FName(*Body.VariableName), Body.CPPType, Body.CPPTypeObjectPath, Body.DefaultValue, false);
			if (Added.Name != FName(*Body.VariableName)) throw std::runtime_error("failed to add the requested local variable");
			bChanged = true;
		}
		else if (bRenameLocalVariable) bChanged = Controller->RenameLocalVariable(FName(*Body.VariableName), FName(*Body.NewVariableName), false, false);
		else if (bSetLocalVariableDefault) bChanged = Controller->SetLocalVariableDefaultValue(FName(*Body.VariableName), Body.DefaultValue, false, false);
		else if (bRemoveLocalVariable) bChanged = Controller->RemoveLocalVariable(FName(*Body.VariableName), false, false);
		else if (bAddExposedPin)
			bChanged = Controller->AddExposedPin(FName(*Body.ExposedPinName), ExposedPinDirection, Body.CPPType,
				FName(*Body.CPPTypeObjectPath), Body.DefaultValue, false, false) == FName(*Body.ExposedPinName);
		else if (bRemoveExposedPin) bChanged = Controller->RemoveExposedPin(FName(*Body.ExposedPinName), false, false);
		else if (bAddFunction)
		{
			URigVMLibraryNode* AddedFunction = Controller->AddFunctionToLibrary(FName(*Body.FunctionName), Body.bFunctionMutable, Body.Position, false, false);
			if (!AddedFunction) throw std::runtime_error("failed to add RigVM function definition");
			ResultNode = AddedFunction->GetName();
			bChanged = true;
		}
		else if (bRemoveFunction) bChanged = Controller->RemoveFunctionFromLibrary(FName(*Body.FunctionName), false, false);
		else if (bRemoveInjectedNode) bChanged = Controller->RemoveInjectedNode(Body.PinPath, Body.bInjectedAsInput, false, false);
		else if (bResolveWildcardPin)
		{
			ResultNode = WildcardNodeName;
			bChanged = Controller->ResolveWildCardPin(Body.PinPath, Body.CPPType, FName(*Body.CPPTypeObjectPath), false, false);
		}
		else if (bRemoveNode) bChanged = Controller->RemoveNode(Node, false, false);
		else if (bSetPosition) bChanged = Controller->SetNodePosition(Node, Body.Position, false, false, false);
		else if (bSetPin) bChanged = Controller->SetPinDefaultValue(Body.PinPath, Body.DefaultValue, true, false, false, false, false);
		else if (bSetPinExpansion) bChanged = Controller->SetPinExpansion(Body.PinPath, Body.bPinExpanded, false, false);
		else if (bSetPinWatched) bChanged = Controller->SetPinIsWatched(Body.PinPath, Body.bPinWatched, false);
		else if (bSetPinDisplayName) bChanged = Controller->SetPinDisplayName(Body.PinPath, Body.PinDisplayName, false, false);
		else if (bAddLink) bChanged = Controller->AddLink(Body.SourcePinPath, Body.TargetPinPath, false, false);
		else bChanged = Controller->BreakLink(Body.SourcePinPath, Body.TargetPinPath, false, false);
		if (!bChanged) throw std::runtime_error("RigVM controller rejected the graph operation");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("changed"), true);
		Writer->WriteValue(TEXT("dry_run"), false);
		Writer->WriteValue(TEXT("saved"), Body.bSave);
		Writer->WriteValue(TEXT("graph_path"), Graph->GetNodePath());
		Writer->WriteValue(TEXT("node_name"), ResultNode);
		if (bCollapseNodes)
		{
			Writer->WriteValue(TEXT("collapsed_node_count"), NodeNamesToCollapse.Num());
			Writer->WriteValue(TEXT("contained_graph_path"), CollapseContainedGraphPath);
			Writer->WriteValue(TEXT("internal_link_count"), CollapseInternalLinkCount);
			Writer->WriteValue(TEXT("boundary_link_count"), CollapseBoundaryLinkCount);
		}
		if (bExpandLibraryNode)
		{
			Writer->WriteValue(TEXT("expanded_node_count"), ExpandedNodeNames.Num());
			Writer->WriteArrayStart(TEXT("expanded_node_names"));
			for (const FString& ExpandedNodeName : ExpandedNodeNames) Writer->WriteValue(ExpandedNodeName);
			Writer->WriteArrayEnd();
		}
		if (bAddInjectedNode || bRemoveInjectedNode)
		{
			Writer->WriteValue(TEXT("pin_path"), Body.PinPath);
			Writer->WriteValue(TEXT("injected_as_input"), Body.bInjectedAsInput);
			Writer->WriteValue(TEXT("remaining_injected_node_count"), InjectionPin->GetInjectedNodes().Num());
		}
		if (bAddTemplateNode) Writer->WriteValue(TEXT("template_notation"), Body.TemplateNotation);
		if (bResolveWildcardPin)
		{
			Writer->WriteValue(TEXT("pin_path"), Body.PinPath);
			Writer->WriteValue(TEXT("cpp_type"), Body.CPPType);
		}
		if (bAddNodeOnPin)
		{
			Writer->WriteValue(TEXT("pin_path"), NodeOnPinTargetPath);
			Writer->WriteValue(TEXT("affected_pin_links"), NodeOnPinAffectedLinks);
			if (bAddRerouteOnPin) Writer->WriteValue(TEXT("reroute_as_input"), Body.bRerouteAsInput);
		}
		if (bArrayPinOperation)
		{
			const URigVMPin* UpdatedArrayPin = Graph->FindPin(ArrayPinPath);
			Writer->WriteValue(TEXT("array_pin_path"), ArrayPinPath);
			Writer->WriteValue(TEXT("array_size_before"), ArraySizeBefore);
			Writer->WriteValue(TEXT("array_size_after"), UpdatedArrayPin ? UpdatedArrayPin->GetSubPins().Num() : 0);
			if (!ArrayElementResultPath.IsEmpty()) Writer->WriteValue(TEXT("array_element_path"), ArrayElementResultPath);
			Writer->WriteArrayStart(TEXT("array_element_paths"));
			if (UpdatedArrayPin)
				for (const URigVMPin* ElementPin : UpdatedArrayPin->GetSubPins())
					if (ElementPin) Writer->WriteValue(ElementPin->GetPinPath());
			Writer->WriteArrayEnd();
		}
		if (bLocalVariableOperation)
			Writer->WriteValue(TEXT("variable_name"), bRenameLocalVariable ? Body.NewVariableName : Body.VariableName);
		if (bExposedPinOperation) Writer->WriteValue(TEXT("exposed_pin_name"), Body.ExposedPinName);
		if (bRemoveLocalVariable) Writer->WriteValue(TEXT("affected_variable_nodes"), AffectedVariableNodes);
		if (bFunctionDefinitionOperation)
		{
			Writer->WriteValue(TEXT("function_name"), bAddFunction ? ResultNode : Body.FunctionName);
			if (bAddFunction)
			{
				if (const URigVMLibraryNode* AddedFunction = FunctionLibraryGraph->FindFunction(FName(*ResultNode)))
					if (const URigVMGraph* ContainedGraph = AddedFunction->GetContainedGraph())
						Writer->WriteValue(TEXT("function_graph_path"), ContainedGraph->GetNodePath());
			}
			if (bRemoveFunction) Writer->WriteValue(TEXT("affected_function_references"), AffectedFunctionReferences);
		}
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/control-rigs/compile", [](const FHttpContext<FAssetPropertyReq, FString>& C)
	{
		const FAssetPropertyReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		FRigVMAssetInterfacePtr VM = Rig ? Rig->GetRigVMAssetInterface() : FRigVMAssetInterfacePtr();
		if (!VM) throw std::runtime_error("Asset is not a Control Rig with a RigVM compiler");
		if (Body.bDryRun)
			return C.TextResponse(TEXT("{\"compiled\":false,\"dry_run\":true}"), TEXT("application/json"));
		URigVMBlueprint* Blueprint = Cast<URigVMBlueprint>(Asset);
		if (!Blueprint) throw std::runtime_error("this Control Rig asset does not expose a public VM compile operation");
		Blueprint->RecompileVM();
		const FCompilerResultsLog& Result = VM->GetCompileLog();
		const bool bSuccess = Result.NumErrors == 0 && VM->GetAssetStatus() != RVMA_Error;
		if (bSuccess) SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"compiled\":true,\"valid\":%s,\"errors\":%d,\"warnings\":%d,\"saved\":%s}"),
			bSuccess ? TEXT("true") : TEXT("false"), Result.NumErrors, Result.NumWarnings,
			(bSuccess && Body.bSave) ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/control-rigs/validate", [](const FHttpContext<FControlRigValidationReq, FString>& C)
	{
		const FControlRigValidationReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		FRigVMAssetInterfacePtr VM = Rig ? Rig->GetRigVMAssetInterface() : FRigVMAssetInterfacePtr();
		if (!VM) throw std::runtime_error("Asset is not a Control Rig with a RigVM model");
		struct FGraphValidationSummary
		{
			FString Path;
			int32 NodeCount = 0;
			int32 PinCount = 0;
			int32 LinkCount = 0;
		};
		TArray<URigVMGraph*> Graphs;
		for (URigVMGraph* Graph : VM->GetAllModels())
		{
			if (!Graph) continue;
			if (Body.GraphPath.IsEmpty() || Graph->GetNodePath() == Body.GraphPath) Graphs.Add(Graph);
		}
		if (Graphs.IsEmpty())
			throw std::runtime_error(Body.GraphPath.IsEmpty()
				? "Control Rig has no RigVM model graphs"
				: "graph_path does not identify a RigVM model graph");

		TArray<FGraphValidationSummary> GraphSummaries;
		TArray<FString> Errors;
		TArray<FString> Warnings;
		int32 TotalNodes = 0;
		int32 TotalPins = 0;
		int32 TotalLinks = 0;
		auto IsOutputDirection = [](ERigVMPinDirection Direction)
		{
			return Direction == ERigVMPinDirection::Output || Direction == ERigVMPinDirection::IO;
		};
		auto IsInputDirection = [](ERigVMPinDirection Direction)
		{
			return Direction == ERigVMPinDirection::Input || Direction == ERigVMPinDirection::IO;
		};
		for (const URigVMGraph* Graph : Graphs)
		{
			FGraphValidationSummary Summary;
			Summary.Path = Graph->GetNodePath();
			TSet<FName> NodeNames;
			TSet<FString> PinPaths;
			TSet<const URigVMPin*> VisitedPins;
			TFunction<void(const URigVMPin*, const URigVMNode*)> ValidatePin;
			ValidatePin = [&ValidatePin, &VisitedPins, &PinPaths, &Errors, &Warnings, &Summary, Graph]
				(const URigVMPin* Pin, const URigVMNode* OwnerNode)
			{
				if (!Pin)
				{
					Errors.Add(FString::Printf(TEXT("graph %s contains a null pin"), *Graph->GetNodePath()));
					return;
				}
				if (VisitedPins.Contains(Pin))
				{
					Errors.Add(FString::Printf(TEXT("graph %s contains a cyclic or repeated pin reference"), *Graph->GetNodePath()));
					return;
				}
				VisitedPins.Add(Pin);
				++Summary.PinCount;
				const FString PinPath = Pin->GetPinPath();
				if (PinPath.IsEmpty())
					Errors.Add(FString::Printf(TEXT("graph %s contains a pin with an empty path"), *Graph->GetNodePath()));
				else if (PinPaths.Contains(PinPath))
					Errors.Add(FString::Printf(TEXT("graph %s contains duplicate pin path %s"), *Graph->GetNodePath(), *PinPath));
				PinPaths.Add(PinPath);
				if (Pin->GetNode() != OwnerNode || Pin->GetGraph() != Graph)
					Errors.Add(FString::Printf(TEXT("pin %s is not owned by its containing graph node"), *PinPath));
				if (Pin->IsWildCard())
					Warnings.Add(FString::Printf(TEXT("pin %s remains an unresolved wildcard"), *PinPath));
				for (const URigVMPin* SubPin : Pin->GetSubPins()) ValidatePin(SubPin, OwnerNode);
			};

			for (const URigVMNode* Node : Graph->GetNodes())
			{
				if (!Node)
				{
					Errors.Add(FString::Printf(TEXT("graph %s contains a null node"), *Summary.Path));
					continue;
				}
				++Summary.NodeCount;
				if (Node->GetFName().IsNone())
					Errors.Add(FString::Printf(TEXT("graph %s contains a node with an empty name"), *Summary.Path));
				else if (NodeNames.Contains(Node->GetFName()))
					Errors.Add(FString::Printf(TEXT("graph %s contains duplicate node name %s"), *Summary.Path, *Node->GetName()));
				NodeNames.Add(Node->GetFName());
				const FVector2D Position = Node->GetPosition();
				if (!FMath::IsFinite(Position.X) || !FMath::IsFinite(Position.Y))
					Errors.Add(FString::Printf(TEXT("node %s has a nonfinite graph position"), *Node->GetName()));
				for (const URigVMPin* Pin : Node->GetPins()) ValidatePin(Pin, Node);
				for (const URigVMPin* OrphanPin : Node->GetOrphanedPins())
					if (OrphanPin)
						Warnings.Add(FString::Printf(TEXT("node %s has an orphaned pin %s"), *Node->GetName(), *OrphanPin->GetPinPath()));
				if (const URigVMTemplateNode* TemplateNode = Cast<URigVMTemplateNode>(Node))
				{
					if (!TemplateNode->GetTemplate())
						Warnings.Add(FString::Printf(TEXT("template node %s uses a notation not registered in this editor"), *Node->GetName()));
					else if (TemplateNode->IsFullyUnresolved())
						Warnings.Add(FString::Printf(TEXT("template node %s has no resolved wildcard arguments"), *Node->GetName()));
				}
				if (const URigVMCollapseNode* CollapseNode = Cast<URigVMCollapseNode>(Node))
					if (!CollapseNode->GetContainedGraph())
						Errors.Add(FString::Printf(TEXT("collapse node %s has no contained graph"), *Node->GetName()));
			}
			TSet<FString> LinkPairs;
			for (const URigVMLink* Link : Graph->GetLinks())
			{
				++Summary.LinkCount;
				if (!Link)
				{
					Errors.Add(FString::Printf(TEXT("graph %s contains a null link"), *Summary.Path));
					continue;
				}
				const FString SourcePath = Link->GetSourcePinPath();
				const FString TargetPath = Link->GetTargetPinPath();
				const URigVMPin* SourcePin = Graph->FindPin(SourcePath);
				const URigVMPin* TargetPin = Graph->FindPin(TargetPath);
				if (!SourcePin || !TargetPin)
				{
					Errors.Add(FString::Printf(TEXT("link in graph %s references a missing pin (%s -> %s)"),
						*Summary.Path, *SourcePath, *TargetPath));
					continue;
				}
				if (!IsOutputDirection(SourcePin->GetDirection()) || !IsInputDirection(TargetPin->GetDirection()))
					Errors.Add(FString::Printf(TEXT("link in graph %s connects pins with invalid directions (%s -> %s)"),
						*Summary.Path, *SourcePath, *TargetPath));
				const FString PairKey = SourcePath + TEXT("->") + TargetPath;
				if (LinkPairs.Contains(PairKey))
					Errors.Add(FString::Printf(TEXT("graph %s contains a duplicate link (%s -> %s)"),
						*Summary.Path, *SourcePath, *TargetPath));
				LinkPairs.Add(PairKey);
				FString FailureReason;
				if (!URigVMPin::CanLink(SourcePin, TargetPin, &FailureReason, nullptr,
					ERigVMPinDirection::IO, true, true)
					&& !FailureReason.Equals(TEXT("Source and target pins are already connected."), ESearchCase::IgnoreCase))
					Errors.Add(FString::Printf(TEXT("link in graph %s is invalid (%s -> %s): %s"),
						*Summary.Path, *SourcePath, *TargetPath, *FailureReason));
			}
			TotalNodes += Summary.NodeCount;
			TotalPins += Summary.PinCount;
			TotalLinks += Summary.LinkCount;
			GraphSummaries.Add(Summary);
		}

		bool bCompileValid = true;
		int32 CompileErrors = 0;
		int32 CompileWarnings = 0;
		if (Body.bCompile)
		{
			URigVMBlueprint* Blueprint = Cast<URigVMBlueprint>(Asset);
			if (!Blueprint) throw std::runtime_error("this Control Rig asset does not expose a public VM compile operation");
			Blueprint->RecompileVM();
			const FCompilerResultsLog& CompileLog = VM->GetCompileLog();
			CompileErrors = CompileLog.NumErrors;
			CompileWarnings = CompileLog.NumWarnings;
			bCompileValid = CompileErrors == 0 && VM->GetAssetStatus() != RVMA_Error;
		}
		const bool bValid = Errors.IsEmpty() && (!Body.bCompile || bCompileValid);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("valid"), bValid);
		Writer->WriteValue(TEXT("graph_count"), GraphSummaries.Num());
		Writer->WriteValue(TEXT("node_count"), TotalNodes);
		Writer->WriteValue(TEXT("pin_count"), TotalPins);
		Writer->WriteValue(TEXT("link_count"), TotalLinks);
		Writer->WriteValue(TEXT("compile_checked"), Body.bCompile);
		if (Body.bCompile)
		{
			Writer->WriteValue(TEXT("compile_valid"), bCompileValid);
			Writer->WriteValue(TEXT("compile_errors"), CompileErrors);
			Writer->WriteValue(TEXT("compile_warnings"), CompileWarnings);
		}
		Writer->WriteArrayStart(TEXT("graphs"));
		for (const FGraphValidationSummary& Summary : GraphSummaries)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("path"), Summary.Path);
			Writer->WriteValue(TEXT("node_count"), Summary.NodeCount);
			Writer->WriteValue(TEXT("pin_count"), Summary.PinCount);
			Writer->WriteValue(TEXT("link_count"), Summary.LinkCount);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("errors"));
		for (const FString& Error : Errors) Writer->WriteValue(Error);
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings"));
		for (const FString& Warning : Warnings) Writer->WriteValue(Warning);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/control-rigs/hierarchy", [](const FHttpContext<FControlRigHierarchyReq, FString>& C)
	{
		const FControlRigHierarchyReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		URigHierarchy* Hierarchy = Rig ? Rig->GetHierarchy() : nullptr;
		if (!Hierarchy) throw std::runtime_error("Asset is not a Control Rig with a hierarchy");
		const bool bAdd = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
		const bool bRename = Body.Operation.Equals(TEXT("rename"), ESearchCase::IgnoreCase);
		const bool bDelete = Body.Operation.Equals(TEXT("delete"), ESearchCase::IgnoreCase);
		const bool bSetTransform = Body.Operation.Equals(TEXT("set_transform"), ESearchCase::IgnoreCase);
		const bool bSetControlValue = Body.Operation.Equals(TEXT("set_control_value"), ESearchCase::IgnoreCase);
		const bool bSetControlLimits = Body.Operation.Equals(TEXT("set_control_limits"), ESearchCase::IgnoreCase);
		const bool bSetControlSettings = Body.Operation.Equals(TEXT("set_control_settings"), ESearchCase::IgnoreCase);
		const bool bSetSpaceRestriction = Body.Operation.Equals(TEXT("set_space_restriction"), ESearchCase::IgnoreCase);
		const bool bSpaceOperation = Body.Operation.Equals(TEXT("add_available_space"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("remove_available_space"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("label_available_space"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("reorder_available_space"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("switch_parent"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_channel_host"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("remove_channel_host"), ESearchCase::IgnoreCase);
		if (!bAdd && !bRename && !bDelete && !bSetTransform && !bSetControlValue && !bSetControlLimits && !bSetControlSettings && !bSpaceOperation && !bSetSpaceRestriction)
			throw std::runtime_error("unsupported Control Rig hierarchy operation");
		const ERigElementType Type = ParseRigElementType(Body.ElementType);
		if (Body.Name.IsEmpty()) throw std::runtime_error("name is required");
		const FRigElementKey Key(FName(*Body.Name), Type);
		if (bAdd && Type != ERigElementType::Null && Type != ERigElementType::Bone && Type != ERigElementType::Curve
			&& Type != ERigElementType::Control && Type != ERigElementType::Socket && Type != ERigElementType::Connector)
			throw std::runtime_error("adding this element type is not yet supported");
		if (bAdd && Hierarchy->Contains(Key)) throw std::runtime_error("an element with this name and type already exists");
		if (!bAdd && !Hierarchy->Contains(Key)) throw std::runtime_error("element does not exist");
		if (bRename && Body.NewName.IsEmpty()) throw std::runtime_error("new_name is required");
		if (bRename && Hierarchy->Contains(FRigElementKey(FName(*Body.NewName), Type)))
			throw std::runtime_error("new_name already exists for this element type");
		if (Body.Translation.ContainsNaN() || Body.Rotation.ContainsNaN() || Body.Scale.ContainsNaN()
			|| !FMath::IsFinite(Body.CurveValue) || Body.MinimumTransform.ContainsNaN() || Body.MaximumTransform.ContainsNaN())
			throw std::runtime_error("transform, control limits, and curve_value must be finite");
		FRigControlValue NewControlValue;
		ERigControlType NewControlType = ERigControlType::Float;
		FRigControlSettings NewControlSettings;
		ERigControlAxis PrimaryAxis = ERigControlAxis::X;
		UEnum* ControlEnum = nullptr;
		if ((bAdd && Type == ERigElementType::Control) || bSetControlValue || bSetControlSettings || bSetSpaceRestriction)
		{
			if (Type != ERigElementType::Control) throw std::runtime_error("Control Rig value/settings operations require a control element");
			if (bAdd)
			{
				NewControlType = ParseRigControlType(Body.ControlType);
				PrimaryAxis = ParseRigControlAxis(Body.PrimaryAxis);
				NewControlSettings.ControlType = NewControlType;
				NewControlSettings.PrimaryAxis = PrimaryAxis;
				if (!Body.ControlEnumPath.IsEmpty())
				{
					if (NewControlType != ERigControlType::Integer) throw std::runtime_error("control_enum_path is only valid for integer controls");
					ControlEnum = LoadObject<UEnum>(nullptr, *Body.ControlEnumPath);
					if (!ControlEnum) throw std::runtime_error("control_enum_path must identify a loaded UEnum");
				}
				NewControlSettings.ControlEnum = ControlEnum;
			}
			else
			{
				const FRigControlElement* Control = Hierarchy->Find<FRigControlElement>(Key);
				if (!Control) throw std::runtime_error("control element is unavailable");
				NewControlType = Control->Settings.ControlType;
				PrimaryAxis = Control->Settings.PrimaryAxis;
				ControlEnum = Control->Settings.ControlEnum;
				NewControlSettings = Control->Settings;
				if (!Body.ControlEnumPath.IsEmpty()) throw std::runtime_error("control_enum_path can only be set when adding an integer control");
				if (RigControlTypeName(NewControlType) == TEXT("other")) throw std::runtime_error("this control value type is not supported by the typed route");
			}
			if (bAdd || bSetControlValue)
				NewControlValue = ParseRigControlValue(NewControlType, Body.ControlValue,
					FTransform(Body.Rotation, Body.Translation, Body.Scale), PrimaryAxis, ControlEnum);
		}
		if (bSetControlLimits)
		{
			if (Type != ERigElementType::Control) throw std::runtime_error("set_control_limits requires a control element");
			const FRigControlElement* Control = Hierarchy->Find<FRigControlElement>(Key);
			if (!Control) throw std::runtime_error("control element is unavailable");
			NewControlType = Control->Settings.ControlType;
			if (Control->Settings.ControlEnum) throw std::runtime_error("enum-backed integer controls use declared members and do not accept numeric limits");
			PrimaryAxis = Control->Settings.PrimaryAxis;
			const bool bScalarLimit = NewControlType == ERigControlType::Float || NewControlType == ERigControlType::ScaleFloat || NewControlType == ERigControlType::Integer;
			const int32 DimensionCount = NewControlType == ERigControlType::Vector2D ? 2
				: NewControlType == ERigControlType::Position || NewControlType == ERigControlType::Scale || NewControlType == ERigControlType::Rotator ? 3
				: NewControlType == ERigControlType::TransformNoScale ? 6
				: NewControlType == ERigControlType::Transform || NewControlType == ERigControlType::EulerTransform ? 9
				: bScalarLimit ? 1 : 0;
			if (DimensionCount == 0) throw std::runtime_error("this control type does not support typed limits");
			if (bScalarLimit && (Body.MinimumValue.IsEmpty() || Body.MaximumValue.IsEmpty()))
				throw std::runtime_error("minimum_value and maximum_value are required for scalar controls");
			if (!bScalarLimit && (Body.MinimumTransform.ContainsNaN() || Body.MaximumTransform.ContainsNaN()))
				throw std::runtime_error("minimum_transform and maximum_transform must be finite");
			NewControlSettings = Control->Settings;
			NewControlSettings.SetupLimitArrayForType(true, true, true);
			TSet<int32> Dimensions;
			if (Body.LimitDimensions.IsEmpty()) for (int32 Index = 0; Index < DimensionCount; ++Index) Dimensions.Add(Index);
			else for (int32 Index : Body.LimitDimensions)
			{
				if (Index < 0 || Index >= DimensionCount)
				{
					const FString Reason = FString::Printf(TEXT("limit_dimensions values must be between 0 and %d for this control type"), DimensionCount - 1);
					throw std::runtime_error(TCHAR_TO_UTF8(*Reason));
				}
				Dimensions.Add(Index);
			}
			if (Dimensions.IsEmpty()) throw std::runtime_error("limit_dimensions must contain at least one enabled dimension");
			for (int32 Index = 0; Index < DimensionCount; ++Index)
				NewControlSettings.LimitEnabled[Index] = FRigControlLimitEnabled(
					Body.bMinimumEnabled && Dimensions.Contains(Index), Body.bMaximumEnabled && Dimensions.Contains(Index));
			if (bScalarLimit)
			{
				NewControlSettings.MinimumValue = ParseRigControlValue(NewControlType, Body.MinimumValue, FTransform::Identity, PrimaryAxis);
				NewControlSettings.MaximumValue = ParseRigControlValue(NewControlType, Body.MaximumValue, FTransform::Identity, PrimaryAxis);
				const double Minimum = NewControlType == ERigControlType::Integer ? NewControlSettings.MinimumValue.Get<int32>() : NewControlSettings.MinimumValue.Get<float>();
				const double Maximum = NewControlType == ERigControlType::Integer ? NewControlSettings.MaximumValue.Get<int32>() : NewControlSettings.MaximumValue.Get<float>();
				if (Minimum > Maximum) throw std::runtime_error("minimum_value must not exceed maximum_value");
			}
			else
			{
				NewControlSettings.MinimumValue = ParseRigControlValue(NewControlType, TEXT(""), Body.MinimumTransform, PrimaryAxis);
				NewControlSettings.MaximumValue = ParseRigControlValue(NewControlType, TEXT(""), Body.MaximumTransform, PrimaryAxis);
				auto CheckRange = [&Dimensions](int32 Index, double Minimum, double Maximum)
				{
					if (Dimensions.Contains(Index) && Minimum > Maximum) throw std::runtime_error("a minimum control limit exceeds its matching maximum");
				};
				if (NewControlType == ERigControlType::Position || NewControlType == ERigControlType::Scale ||
					NewControlType == ERigControlType::Rotator || NewControlType == ERigControlType::Vector2D)
				{
					const FVector3f Minimum = NewControlSettings.MinimumValue.Get<FVector3f>();
					const FVector3f Maximum = NewControlSettings.MaximumValue.Get<FVector3f>();
					CheckRange(0, Minimum.X, Maximum.X); CheckRange(1, Minimum.Y, Maximum.Y);
					if (DimensionCount > 2) CheckRange(2, Minimum.Z, Maximum.Z);
				}
				else
				{
					const FTransform Minimum = NewControlSettings.MinimumValue.GetAsTransform(NewControlType, PrimaryAxis);
					const FTransform Maximum = NewControlSettings.MaximumValue.GetAsTransform(NewControlType, PrimaryAxis);
					const FVector MinLocation = Minimum.GetLocation(), MaxLocation = Maximum.GetLocation();
					const FVector MinScale = Minimum.GetScale3D(), MaxScale = Maximum.GetScale3D();
					const FRotator MinRotation = Minimum.Rotator(), MaxRotation = Maximum.Rotator();
					CheckRange(0, MinLocation.X, MaxLocation.X); CheckRange(1, MinLocation.Y, MaxLocation.Y); CheckRange(2, MinLocation.Z, MaxLocation.Z);
					CheckRange(3, MinRotation.Pitch, MaxRotation.Pitch); CheckRange(4, MinRotation.Yaw, MaxRotation.Yaw); CheckRange(5, MinRotation.Roll, MaxRotation.Roll);
					if (DimensionCount == 9) { CheckRange(6, MinScale.X, MaxScale.X); CheckRange(7, MinScale.Y, MaxScale.Y); CheckRange(8, MinScale.Z, MaxScale.Z); }
				}
			}
		}
		const bool bAnyControlSettingsRequested = bAdd || !Body.ControlDisplayName.IsEmpty() || !Body.ControlAnimationType.IsEmpty()
			|| !Body.ShapeName.IsEmpty() || !Body.ShapeColor.IsEmpty() || !Body.ShapeVisibility.IsEmpty()
			|| Body.bSetShapeVisible || Body.bSetDrawLimits || Body.bSetGroupWithParentControl
			|| Body.bSetControlShapeTransform || Body.bSetPreferredRotationOrder || !Body.PreferredRotationOrder.IsEmpty()
			|| Body.bSetDrivenControls || !Body.DrivenControlNames.IsEmpty() || Body.bSetRestrictSpaceSwitching || bSetSpaceRestriction;
		if (bSetControlSettings && !bAnyControlSettingsRequested)
			throw std::runtime_error("set_control_settings requires at least one setting to change");
		if ((bAdd && Type == ERigElementType::Control) || bSetControlSettings || bSetSpaceRestriction)
		{
			if (!Body.ControlDisplayName.IsEmpty()) NewControlSettings.DisplayName = FName(*Body.ControlDisplayName);
			if (!Body.ControlAnimationType.IsEmpty()) NewControlSettings.AnimationType = ParseRigControlAnimationType(Body.ControlAnimationType);
			if (!Body.ShapeName.IsEmpty())
			{
				const FName ShapeName(*Body.ShapeName);
				TArray<TSoftObjectPtr<UControlRigShapeLibrary>>& ShapeLibraries = Rig->GetShapeLibraries();
				for (TSoftObjectPtr<UControlRigShapeLibrary>& Library : ShapeLibraries)
					if (!Library.IsValid() && !Library.IsNull()) Library.LoadSynchronous();
				TMap<FString, FString> NoNameRemapping;
			bool bShapeExists = ShapeName == FName(TEXT("Default"))
				|| UControlRigShapeLibrary::GetShapeByName(ShapeName, ShapeLibraries, NoNameRemapping, false) != nullptr;
			for (const TSoftObjectPtr<UControlRigShapeLibrary>& Library : ShapeLibraries)
				if (const UControlRigShapeLibrary* Loaded = Library.Get())
					bShapeExists |= Loaded->DefaultShape.ShapeName == ShapeName || Loaded->GetShapeByName(ShapeName, false) != nullptr;
			if (!bShapeExists)
					throw std::runtime_error("shape_name must identify a shape in one of this Control Rig's shape libraries");
				NewControlSettings.ShapeName = ShapeName;
			}
			if (!Body.ShapeColor.IsEmpty())
			{
				FLinearColor Color;
				if (!Color.InitFromString(Body.ShapeColor) || !FMath::IsFinite(Color.R) || !FMath::IsFinite(Color.G)
					|| !FMath::IsFinite(Color.B) || !FMath::IsFinite(Color.A) || Color.R < 0.f || Color.R > 1.f
					|| Color.G < 0.f || Color.G > 1.f || Color.B < 0.f || Color.B > 1.f || Color.A < 0.f || Color.A > 1.f)
					throw std::runtime_error("shape_color must be a finite linear color with channels between 0 and 1");
				NewControlSettings.ShapeColor = Color;
			}
			if (!Body.ShapeVisibility.IsEmpty()) NewControlSettings.ShapeVisibility = ParseRigControlVisibility(Body.ShapeVisibility);
			if (Body.bSetShapeVisible) NewControlSettings.bShapeVisible = Body.bShapeVisible;
			if (Body.bSetDrawLimits) NewControlSettings.bDrawLimits = Body.bDrawLimits;
			if (Body.bSetGroupWithParentControl) NewControlSettings.bGroupWithParentControl = Body.bGroupWithParentControl;
			if (Body.bSetRestrictSpaceSwitching || bSetSpaceRestriction)
				NewControlSettings.bRestrictSpaceSwitching = Body.bRestrictSpaceSwitching;
			if (NewControlSettings.bRestrictSpaceSwitching)
			{
				const FRigControlElement* Control = Hierarchy->Find<FRigControlElement>(Key);
				const FRigElementKey ActiveParent = Hierarchy->GetActiveParent(Key);
				const bool bParentAvailable = Control->Settings.Customization.AvailableSpaces.FindByKey(ActiveParent) != nullptr;
				const bool bDefaultParent = Hierarchy->GetDefaultParent(Key) == ActiveParent || ActiveParent == URigHierarchy::GetDefaultParentKey();
				if (ActiveParent.IsValid() && !bParentAvailable && !bDefaultParent)
					throw std::runtime_error("space restriction would exclude the control's active parent");
			}
			if (Body.bSetPreferredRotationOrder || !Body.PreferredRotationOrder.IsEmpty())
			{
				if (NewControlType != ERigControlType::Rotator && NewControlType != ERigControlType::Transform
					&& NewControlType != ERigControlType::TransformNoScale && NewControlType != ERigControlType::EulerTransform)
					throw std::runtime_error("preferred rotation order requires a rotator or transform control");
				NewControlSettings.bUsePreferredRotationOrder = !Body.bSetPreferredRotationOrder || Body.bUsePreferredRotationOrder;
				if (NewControlSettings.bUsePreferredRotationOrder)
					NewControlSettings.PreferredRotationOrder = ParseRigRotationOrder(Body.PreferredRotationOrder);
			}
			if (Body.bSetDrivenControls || !Body.DrivenControlNames.IsEmpty() || bAdd)
			{
				NewControlSettings.DrivenControls.Reset();
				for (const FString& DrivenName : Body.DrivenControlNames)
				{
					const FRigElementKey DrivenKey(FName(*DrivenName), ERigElementType::Control);
					if (DrivenName.IsEmpty() || DrivenKey == Key || !Hierarchy->Contains(DrivenKey))
						throw std::runtime_error("driven_control_names must identify other existing control elements");
					if (NewControlSettings.DrivenControls.Contains(DrivenKey))
						throw std::runtime_error("driven_control_names cannot contain duplicates");
					NewControlSettings.DrivenControls.Add(DrivenKey);
				}
			}
			if (NewControlSettings.AnimationType == ERigControlAnimationType::ProxyControl && NewControlSettings.DrivenControls.IsEmpty())
				throw std::runtime_error("proxy_control requires at least one driven control name");
			if (NewControlSettings.AnimationType != ERigControlAnimationType::ProxyControl && !NewControlSettings.DrivenControls.IsEmpty())
				throw std::runtime_error("driven_control_names are only valid for proxy_control");
			if (NewControlSettings.AnimationType == ERigControlAnimationType::ProxyControl)
			{
				for (const FRigElementKey& Driven : NewControlSettings.DrivenControls)
				{
					TSet<FRigElementKey> Visited;
					TArray<FRigElementKey> Pending = {Driven};
					while (!Pending.IsEmpty())
					{
						const FRigElementKey Node = Pending.Pop(EAllowShrinking::No);
						if (Node == Key) throw std::runtime_error("proxy driven-control links cannot create a cycle");
						if (Visited.Contains(Node)) continue;
						if (Visited.Num() >= 4096) throw std::runtime_error("proxy cycle validation exceeded its 4096-control bound");
					Visited.Add(Node);
					if (const FRigControlElement* Existing = Hierarchy->Find<FRigControlElement>(Node))
						Pending.Append(Existing->Settings.DrivenControls);
					}
				}
			}
			const bool bShapeChange = !Body.ShapeName.IsEmpty() || !Body.ShapeColor.IsEmpty() || !Body.ShapeVisibility.IsEmpty()
				|| (Body.bSetShapeVisible && Body.bShapeVisible) || Body.bSetControlShapeTransform;
			if (bShapeChange && !NewControlSettings.SupportsShape())
				throw std::runtime_error("this control type/animation mode does not support a visible shape");
			if (Body.bSetControlShapeTransform && (Body.ControlShapeTransform.ContainsNaN()
				|| FMath::Abs(Body.ControlShapeTransform.GetScale3D().X) < SMALL_NUMBER
				|| FMath::Abs(Body.ControlShapeTransform.GetScale3D().Y) < SMALL_NUMBER
				|| FMath::Abs(Body.ControlShapeTransform.GetScale3D().Z) < SMALL_NUMBER))
				throw std::runtime_error("control_shape_transform must be finite with nonzero scale");
		}
		if (bSetTransform && Type != ERigElementType::Bone && Type != ERigElementType::Null
			&& Type != ERigElementType::Control && Type != ERigElementType::Socket)
			throw std::runtime_error("set_transform requires a bone, null, control, or socket");
		FRigElementKey Parent;
		if (bAdd && !Body.ParentName.IsEmpty())
		{
			if (Type == ERigElementType::Curve) throw std::runtime_error("a curve cannot have a parent");
			if (Body.ParentType.IsEmpty()) throw std::runtime_error("parent_type is required with parent_name");
			Parent = FRigElementKey(FName(*Body.ParentName), ParseRigElementType(Body.ParentType));
			if (!Hierarchy->Contains(Parent)) throw std::runtime_error("parent does not exist");
		}
		if (bAdd && Type == ERigElementType::Socket && !Parent.IsValid())
			throw std::runtime_error("a socket requires an existing parent");
		FRigElementKey SpaceKey;
		const bool bSpaceManagement = bSpaceOperation && !bSetSpaceRestriction;
		if (bSpaceManagement || bSetSpaceRestriction)
		{
			if (Type != ERigElementType::Control || !Hierarchy->Find<FRigControlElement>(Key))
				throw std::runtime_error("space and channel-host operations require a control element");
		}
		if (bSpaceManagement)
		{
			if (Body.SpaceName.IsEmpty() || Body.SpaceType.IsEmpty()) throw std::runtime_error("space_name and space_type are required");
			SpaceKey = FRigElementKey(FName(*Body.SpaceName), ParseRigElementType(Body.SpaceType));
			const bool bDefaultParentRequest = SpaceKey == URigHierarchy::GetDefaultParentKey();
			const bool bSwitchParent = Body.Operation.Equals(TEXT("switch_parent"), ESearchCase::IgnoreCase);
			if (!(bSwitchParent && bDefaultParentRequest) && !Hierarchy->Find<FRigTransformElement>(SpaceKey))
				throw std::runtime_error("space must identify an existing transform element");
			const FRigControlElement* Control = Hierarchy->Find<FRigControlElement>(Key);
			const bool bAvailable = Control->Settings.Customization.AvailableSpaces.FindByKey(SpaceKey) != nullptr;
			const bool bDefaultParent = Hierarchy->GetDefaultParent(Key) == SpaceKey || SpaceKey == URigHierarchy::GetDefaultParentKey();
			if (Body.Operation.Equals(TEXT("add_available_space"), ESearchCase::IgnoreCase))
			{
				if (bAvailable) throw std::runtime_error("space is already available for this control");
				if (Hierarchy->GetParents(Key).Contains(SpaceKey)) throw std::runtime_error("the control's existing default parent cannot be added as an available space");
				if (Control->IsAnimationChannel() && SpaceKey.Type != ERigElementType::Control)
					throw std::runtime_error("animation-channel spaces must be control elements");
				if (const FRigControlElement* SpaceControl = Hierarchy->Find<FRigControlElement>(SpaceKey))
					if (SpaceControl->IsAnimationChannel()) throw std::runtime_error("an animation channel cannot be used as a space");
			}
			else if (Body.Operation.Equals(TEXT("remove_available_space"), ESearchCase::IgnoreCase)
				|| Body.Operation.Equals(TEXT("label_available_space"), ESearchCase::IgnoreCase))
			{
				if (!bAvailable) throw std::runtime_error("space is not listed as available for this control");
				if (Body.Operation.Equals(TEXT("remove_available_space"), ESearchCase::IgnoreCase)
					&& Hierarchy->GetActiveParent(Key) == SpaceKey)
					throw std::runtime_error("switch away from the active space before removing it");
				if (Body.Operation.Equals(TEXT("label_available_space"), ESearchCase::IgnoreCase) && Body.SpaceLabel.IsEmpty())
					throw std::runtime_error("space_label is required");
			}
			else if (Body.Operation.Equals(TEXT("reorder_available_space"), ESearchCase::IgnoreCase))
			{
				const int32 SpaceCount = Control->Settings.Customization.AvailableSpaces.Num();
				if (!bAvailable) throw std::runtime_error("space is not listed as available for this control");
				if (Body.SpaceIndex < 0 || Body.SpaceIndex >= SpaceCount) throw std::runtime_error("space_index must be within the available-space list");
			}
			else if (Body.Operation.Equals(TEXT("switch_parent"), ESearchCase::IgnoreCase))
			{
				if (Control->Settings.bRestrictSpaceSwitching && !bAvailable && !bDefaultParent)
					throw std::runtime_error("this control only allows switching to its registered available spaces");
				FString Reason;
				if (!Hierarchy->CanSwitchToParent(Key, SpaceKey, FEmptyRigDependenciesProvider(), &Reason))
					throw std::runtime_error(TCHAR_TO_UTF8(*Reason));
			}
			else if (Body.Operation.Equals(TEXT("add_channel_host"), ESearchCase::IgnoreCase))
			{
				if (!Control->IsAnimationChannel()) throw std::runtime_error("add_channel_host requires an animation_channel control");
				if (SpaceKey.Type != ERigElementType::Control) throw std::runtime_error("animation-channel hosts must be controls");
			}
			else if (Body.Operation.Equals(TEXT("remove_channel_host"), ESearchCase::IgnoreCase)
				&& (!Control->IsAnimationChannel() || SpaceKey.Type != ERigElementType::Control))
				throw std::runtime_error("remove_channel_host requires an animation_channel and control host");
			if ((Body.Operation.Equals(TEXT("add_channel_host"), ESearchCase::IgnoreCase)
				|| Body.Operation.Equals(TEXT("remove_channel_host"), ESearchCase::IgnoreCase))
				&& Hierarchy->GetParents(Key).Contains(SpaceKey))
				throw std::runtime_error("the channel's existing parent cannot be added as a channel host");
		}
		FRigConnectorSettings ConnectorSettings;
		if (bAdd && Type == ERigElementType::Connector)
		{
			if (!Body.ParentName.IsEmpty()) throw std::runtime_error("a connector cannot have a hierarchy parent");
			if (Body.ConnectorType.Equals(TEXT("primary"), ESearchCase::IgnoreCase))
			{
				if (Body.bOptional || Body.bIsArray) throw std::runtime_error("a primary connector cannot be optional or an array");
				ConnectorSettings.Type = EConnectorType::Primary;
			}
			else if (Body.ConnectorType.Equals(TEXT("secondary"), ESearchCase::IgnoreCase)) ConnectorSettings.Type = EConnectorType::Secondary;
			else throw std::runtime_error("connector_type must be primary or secondary");
			ConnectorSettings.bOptional = Body.bOptional;
			ConnectorSettings.bIsArray = Body.bIsArray;
			ConnectorSettings.Description = Body.Description;
		}
		const int32 AffectedChildren = bDelete ? Hierarchy->GetChildren(Key, true).Num() : 0;
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"affected_children\":%d}"), AffectedChildren), TEXT("application/json"));
		if (bDelete && !Body.bConfirm) throw std::runtime_error("Control Rig element deletion requires confirm=true");
		URigHierarchyController* Controller = Rig->GetHierarchyController();
		if (!Controller) throw std::runtime_error("Control Rig hierarchy controller is unavailable");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditControlRigHierarchy", "Edit Control Rig Hierarchy"));
		Asset->Modify();
		Hierarchy->Modify();
		FRigElementKey Result = Key;
		if (bAdd)
		{
			const FTransform Transform(Body.Rotation, Body.Translation, Body.Scale);
			if (Type == ERigElementType::Null) Result = Controller->AddNull(Key.Name, Parent, Transform, true, false, false);
			else if (Type == ERigElementType::Bone) Result = Controller->AddBone(Key.Name, Parent, Transform, true, ERigBoneType::User, false, false);
			else if (Type == ERigElementType::Curve) Result = Controller->AddCurve(Key.Name, Body.CurveValue, false, false);
			else if (Type == ERigElementType::Socket) Result = Controller->AddSocket(Key.Name, Parent, Transform, true, FLinearColor::White, TEXT(""), false, false);
			else if (Type == ERigElementType::Connector) Result = Controller->AddConnector(Key.Name, ConnectorSettings, false, false);
			else
			{
				if (NewControlSettings.DisplayName.IsNone()) NewControlSettings.DisplayName = Key.Name;
				const FTransform ShapeTransform = Body.bSetControlShapeTransform ? Body.ControlShapeTransform : FTransform::Identity;
				Result = Controller->AddControl(Key.Name, Parent, NewControlSettings, NewControlValue, Transform, ShapeTransform, false, false);
			}
			if (!Result.IsValid()) throw std::runtime_error("failed to add Control Rig element");
		}
		else if (bRename)
		{
			Result = Controller->RenameElement(Key, FName(*Body.NewName), false, false, true);
			if (!Result.IsValid()) throw std::runtime_error("failed to rename Control Rig element");
		}
		else if (bDelete && !Controller->RemoveElement(Key, false, false)) throw std::runtime_error("failed to delete Control Rig element");
		else if (bSetControlSettings)
		{
			if (!Controller->SetControlSettings(Key, NewControlSettings, false)) throw std::runtime_error("failed to set Control Rig control settings");
			if (Body.bSetControlShapeTransform)
				Hierarchy->SetControlShapeTransform(Key, Body.ControlShapeTransform, Body.bInitial, false);
		}
		else if (bSetSpaceRestriction)
		{
			if (!Controller->SetControlSettings(Key, NewControlSettings, false)) throw std::runtime_error("failed to change space-switch restriction");
		}
		else if (bSpaceManagement)
		{
			bool bSpaceChanged = false;
			if (Body.Operation.Equals(TEXT("add_available_space"), ESearchCase::IgnoreCase))
				bSpaceChanged = Controller->AddAvailableSpace(Key, SpaceKey, FName(*Body.SpaceLabel), false, false);
			else if (Body.Operation.Equals(TEXT("remove_available_space"), ESearchCase::IgnoreCase))
				bSpaceChanged = Controller->RemoveAvailableSpace(Key, SpaceKey, false, false);
			else if (Body.Operation.Equals(TEXT("label_available_space"), ESearchCase::IgnoreCase))
				bSpaceChanged = Controller->SetAvailableSpaceLabel(Key, SpaceKey, FName(*Body.SpaceLabel), false, false);
			else if (Body.Operation.Equals(TEXT("reorder_available_space"), ESearchCase::IgnoreCase))
				bSpaceChanged = Controller->SetAvailableSpaceIndex(Key, SpaceKey, Body.SpaceIndex, false, false);
			else if (Body.Operation.Equals(TEXT("add_channel_host"), ESearchCase::IgnoreCase))
				bSpaceChanged = Controller->AddChannelHost(Key, SpaceKey, false, false);
			else if (Body.Operation.Equals(TEXT("remove_channel_host"), ESearchCase::IgnoreCase))
				bSpaceChanged = Controller->RemoveChannelHost(Key, SpaceKey, false, false);
			else if (Body.Operation.Equals(TEXT("switch_parent"), ESearchCase::IgnoreCase))
			{
				FString Reason;
				const FTransform PreviousGlobalTransform = Hierarchy->GetGlobalTransform(Key, Body.bInitial);
				const FRigElementKey PreviousParent = Hierarchy->GetActiveParent(Key);
				const TArray<FRigElementKey> PreviousParents = Hierarchy->GetParents(Key);
				bSpaceChanged = Hierarchy->SwitchToParent(Key, SpaceKey, Body.bInitial, Body.bAffectChildren,
					FEmptyRigDependenciesProvider(), &Reason);
				if (!bSpaceChanged) throw std::runtime_error(TCHAR_TO_UTF8(*Reason));
				if (Body.bMaintainGlobalTransform)
				{
					Hierarchy->SetGlobalTransform(Key, PreviousGlobalTransform, Body.bInitial, Body.bAffectChildren, false, false);
					const FTransform PreservedGlobalTransform = Hierarchy->GetGlobalTransform(Key, Body.bInitial);
					if (!PreservedGlobalTransform.Equals(PreviousGlobalTransform, 0.001f))
					{
						const FString PreservationFailure = FString::Printf(
							TEXT("the control could not represent its previous global transform after the space switch (expected %s, got %s, local %s)"),
							*PreviousGlobalTransform.ToString(), *PreservedGlobalTransform.ToString(),
							*Hierarchy->GetLocalTransform(Key, Body.bInitial).ToString());
						if (PreviousParent.IsValid()) Hierarchy->SwitchToParent(Key, PreviousParent, Body.bInitial, Body.bAffectChildren);
						if (!PreviousParents.Contains(SpaceKey)) Controller->RemoveParent(Key, SpaceKey, false, false);
						Hierarchy->SetGlobalTransform(Key, PreviousGlobalTransform, Body.bInitial, Body.bAffectChildren, false, false);
						throw std::runtime_error(TCHAR_TO_UTF8(*PreservationFailure));
					}
				}
			}
			if (!bSpaceChanged) throw std::runtime_error("UE rejected the Control Rig space operation");
		}
		else if (bSetTransform)
			Hierarchy->SetGlobalTransform(Key, FTransform(Body.Rotation, Body.Translation, Body.Scale), Body.bInitial, true, false, false);
		else if (bSetControlValue)
			Hierarchy->SetControlValue(Key, NewControlValue, Body.bInitial ? ERigControlValueType::Initial : ERigControlValueType::Current, false, false);
		else if (bSetControlLimits && !Controller->SetControlSettings(Key, NewControlSettings, false))
			throw std::runtime_error("failed to set Control Rig control limits");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("changed"), true);
		Writer->WriteValue(TEXT("dry_run"), false);
		Writer->WriteValue(TEXT("saved"), Body.bSave);
		Writer->WriteValue(TEXT("name"), Result.Name.ToString());
		Writer->WriteValue(TEXT("type"), RigElementTypeName(Result.Type));
		Writer->WriteValue(TEXT("affected_children"), AffectedChildren);
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/modular-rigs/inspect", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		return C.TextResponse(ObjUtils::SerializeObjectToJson(Asset), TEXT("application/json"));
	});

	App->Get("/modular-rigs/modules", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		const FModularRigModel& Model = Rig->GetModularRigModel();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		for (const FRigModuleReference& Module : Model.Modules)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Module.Name.ToString());
			Writer->WriteValue(TEXT("parent"), Module.ParentModuleName.ToString());
			Writer->WriteValue(TEXT("class"), Module.Class.ToSoftObjectPath().ToString());
			Writer->WriteValue(TEXT("child_count"), Module.CachedChildren.Num());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/modular-rigs/dependencies", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		UModularRigController* Controller = Rig->GetModularRigController();
		const FModularRigModel& Model = Rig->GetModularRigModel();
		const URigHierarchy* Hierarchy = Rig->GetHierarchy();
		if (!Controller || !Hierarchy) throw std::runtime_error("Modular Rig hierarchy/controller is unavailable");
		TMap<FRigElementKey, FName> ConnectorOwners;
		for (const FRigModuleReference& Module : Model.Modules)
			for (const FRigElementKey& Connector : Controller->GetConnectorsForModule(Module.Name))
				ConnectorOwners.Add(Connector, Module.Name);

		int32 DependencyCount = 0;
		int32 ParentDependencyCount = 0;
		int32 ConnectorDependencyCount = 0;
		int32 BindingDependencyCount = 0;
		int32 UnresolvedCount = 0;
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("dependencies"));
		for (const FRigModuleReference& Module : Model.Modules)
		{
			if (!Module.ParentModuleName.IsNone())
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("type"), TEXT("module_parent"));
				Writer->WriteValue(TEXT("source_module"), Module.ParentModuleName.ToString());
				Writer->WriteValue(TEXT("target_module"), Module.Name.ToString());
				Writer->WriteObjectEnd();
				++DependencyCount;
				++ParentDependencyCount;
			}
			for (const TPair<FName, FString>& Binding : Module.Bindings)
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("type"), TEXT("variable_binding"));
				Writer->WriteValue(TEXT("module"), Module.Name.ToString());
				Writer->WriteValue(TEXT("variable"), Binding.Key.ToString());
				Writer->WriteValue(TEXT("source_path"), Binding.Value);
				Writer->WriteObjectEnd();
				++DependencyCount;
				++BindingDependencyCount;
			}
		}
		for (const FModularRigSingleConnection& Connection : Model.Connections.GetConnectionList())
		{
			const FName* Owner = ConnectorOwners.Find(Connection.Connector);
			for (const FRigElementKey& Target : Connection.Targets)
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("type"), TEXT("connector_target"));
				Writer->WriteValue(TEXT("connector_module"), Owner ? Owner->ToString() : TEXT(""));
				Writer->WriteValue(TEXT("connector"), Connection.Connector.Name.ToString());
				Writer->WriteValue(TEXT("target_name"), Target.Name.ToString());
				Writer->WriteValue(TEXT("target_type"), RigElementTypeName(Target.Type));
				Writer->WriteObjectEnd();
				++DependencyCount;
				++ConnectorDependencyCount;
			}
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("config_overrides"));
		for (const FRigModuleReference& Module : Model.Modules)
			for (const FControlRigOverrideValue& Override : Module.ConfigOverrides)
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("module"), Module.Name.ToString());
				Writer->WriteValue(TEXT("path"), Override.GetPath());
				Writer->WriteValue(TEXT("value"), Override.ToString());
				Writer->WriteObjectEnd();
			}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("unresolved_connectors"));
		for (const FRigElementKey& Key : Hierarchy->GetAllKeys(false, ERigElementType::Connector))
		{
			if (Model.Connections.HasConnection(Key)) continue;
			const FRigConnectorElement* Connector = Hierarchy->Find<FRigConnectorElement>(Key);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Key.Name.ToString());
			if (const FName* Owner = ConnectorOwners.Find(Key)) Writer->WriteValue(TEXT("module"), Owner->ToString());
			Writer->WriteValue(TEXT("required"), Connector ? !Connector->Settings.bOptional : true);
			Writer->WriteObjectEnd();
			++UnresolvedCount;
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("module_count"), Model.Modules.Num());
		Writer->WriteValue(TEXT("dependency_count"), DependencyCount);
		Writer->WriteValue(TEXT("parent_dependency_count"), ParentDependencyCount);
		Writer->WriteValue(TEXT("connector_dependency_count"), ConnectorDependencyCount);
		Writer->WriteValue(TEXT("binding_dependency_count"), BindingDependencyCount);
		Writer->WriteValue(TEXT("unresolved_connector_count"), UnresolvedCount);
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/modular-rigs/connections", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		const FModularRigModel& Model = Rig->GetModularRigModel();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteArrayStart(TEXT("connections"));
		for (const FModularRigSingleConnection& Connection : Model.Connections.GetConnectionList())
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("connector"), Connection.Connector.Name.ToString());
			Writer->WriteArrayStart(TEXT("targets"));
			for (const FRigElementKey& Target : Connection.Targets)
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Target.Name.ToString());
				Writer->WriteValue(TEXT("type"), RigElementTypeName(Target.Type));
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("unresolved"));
		if (const URigHierarchy* Hierarchy = Rig->GetHierarchy())
			for (const FRigElementKey& Key : Hierarchy->GetAllKeys(false, ERigElementType::Connector))
			{
				if (Model.Connections.HasConnection(Key)) continue;
				const FRigConnectorElement* Connector = Hierarchy->Find<FRigConnectorElement>(Key);
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("name"), Key.Name.ToString());
				Writer->WriteValue(TEXT("required"), Connector ? !Connector->Settings.bOptional : true);
				Writer->WriteObjectEnd();
			}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/modular-rigs/modules", [](const FHttpContext<FModularRigReq, FString>& C)
	{
		const FModularRigReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		FModularRigModel& Model = Rig->GetModularRigModel();
		UModularRigController* Controller = Rig->GetModularRigController();
		if (!Controller) throw std::runtime_error("Modular Rig controller is unavailable");
		const bool bAdd = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase);
		const bool bRename = Body.Operation.Equals(TEXT("rename"), ESearchCase::IgnoreCase);
		const bool bReparent = Body.Operation.Equals(TEXT("reparent"), ESearchCase::IgnoreCase);
		const bool bDelete = Body.Operation.Equals(TEXT("delete"), ESearchCase::IgnoreCase);
		if (!bAdd && !bRename && !bReparent && !bDelete)
			throw std::runtime_error("operation must be add, rename, reparent, or delete");
		if (Body.ModuleName.IsEmpty()) throw std::runtime_error("module_name is required");
		const FName Name(*Body.ModuleName);
		const FRigModuleReference* Existing = Model.FindModule(Name);
		if (bAdd && Existing) throw std::runtime_error("module_name already exists");
		if (!bAdd && !Existing) throw std::runtime_error("module_name does not exist");
		if ((bAdd || bReparent) && !Body.ParentName.IsEmpty() && !Model.FindModule(FName(*Body.ParentName)))
			throw std::runtime_error("parent_name does not identify a module");
		if (bReparent && Body.ParentName == Body.ModuleName) throw std::runtime_error("module cannot parent itself");
		UClass* ModuleClass = nullptr;
		if (bAdd)
		{
			ModuleClass = LoadClass<UControlRig>(nullptr, *Body.ModuleClassPath);
			if (!ModuleClass) throw std::runtime_error("module_class_path must reference a Control Rig class");
		}
		if (bRename)
		{
			if (Body.NewName.IsEmpty()) throw std::runtime_error("new_name is required");
			FText Reason;
			if (!Controller->CanRenameModule(Name, FName(*Body.NewName), Reason))
				throw std::runtime_error(TCHAR_TO_UTF8(*Reason.ToString()));
		}
		const int32 AffectedChildren = bDelete ? Existing->CachedChildren.Num() : 0;
		const int32 AffectedConnectors = bDelete ? Controller->GetConnectorsForModule(Name).Num() : 0;
		int32 ConnectedConnectors = 0;
		if (bDelete)
			for (const FRigElementKey& Connector : Controller->GetConnectorsForModule(Name))
				if (Model.Connections.HasConnection(Connector)) ++ConnectedConnectors;
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"affected_children\":%d,\"affected_connectors\":%d,\"connected_connectors\":%d}"),
				AffectedChildren, AffectedConnectors, ConnectedConnectors), TEXT("application/json"));
		if (bDelete && !Body.bConfirm) throw std::runtime_error("Modular Rig module deletion requires confirm=true");
		if (bDelete && ConnectedConnectors > 0) throw std::runtime_error("disconnect the module's connectors before deletion");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditModularRigModule", "Edit Modular Rig Module"));
		Asset->Modify();
		FName ResultName = Name;
		bool bChanged = false;
		if (bAdd)
		{
			ResultName = Controller->AddModule(Name, ModuleClass, FName(*Body.ParentName), false);
			bChanged = !ResultName.IsNone();
		}
		else if (bRename)
		{
			ResultName = Controller->RenameModule(Name, FName(*Body.NewName), false);
			bChanged = !ResultName.IsNone();
		}
		else if (bReparent) bChanged = Controller->ReparentModule(Name, FName(*Body.ParentName), false);
		else
		{
			// UE 5.7 returns false after a successful removal; inspect the model instead.
			Controller->DeleteModule(Name, false);
			bChanged = Model.FindModule(Name) == nullptr;
		}
		if (!bChanged) throw std::runtime_error("Modular Rig controller rejected the module operation");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":true,\"saved\":%s,\"module_name\":\"%s\",\"affected_children\":%d,\"affected_connectors\":%d}"),
			Body.bSave ? TEXT("true") : TEXT("false"), *ResultName.ToString(), AffectedChildren, AffectedConnectors), TEXT("application/json"));
	});

	App->Post("/modular-rigs/connections", [](const FHttpContext<FModularRigReq, FString>& C)
	{
		const FModularRigReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		UModularRigController* Controller = Rig->GetModularRigController();
		URigHierarchy* Hierarchy = Rig->GetHierarchy();
		if (!Controller || !Hierarchy) throw std::runtime_error("Modular Rig hierarchy/controller is unavailable");
		const bool bConnect = Body.Operation.Equals(TEXT("connect"), ESearchCase::IgnoreCase);
		const bool bDisconnect = Body.Operation.Equals(TEXT("disconnect"), ESearchCase::IgnoreCase);
		const bool bSetTargets = Body.Operation.Equals(TEXT("set_targets"), ESearchCase::IgnoreCase);
		const bool bAddTarget = Body.Operation.Equals(TEXT("add_target"), ESearchCase::IgnoreCase);
		const bool bRemoveTarget = Body.Operation.Equals(TEXT("remove_target"), ESearchCase::IgnoreCase);
		if (!bConnect && !bDisconnect && !bSetTargets && !bAddTarget && !bRemoveTarget)
			throw std::runtime_error("operation must be connect, disconnect, set_targets, add_target, or remove_target");
		const FRigElementKey Connector(FName(*Body.ConnectorName), ERigElementType::Connector);
		if (!Hierarchy->Contains(Connector)) throw std::runtime_error("connector_name does not identify a connector");
		const FRigConnectorElement* ConnectorElement = Hierarchy->Find<FRigConnectorElement>(Connector);
		if (!ConnectorElement) throw std::runtime_error("connector element is unavailable");
		const FModularRigConnections& Connections = Rig->GetModularRigModel().Connections;
		const bool bExisting = Connections.HasConnection(Connector);
		if ((bSetTargets || bAddTarget || bRemoveTarget) && !ConnectorElement->Settings.bIsArray)
			throw std::runtime_error("array target operations require an array connector");
		TArray<FRigElementKey> Targets = Connections.FindTargetsFromConnector(Connector);
		auto ParseTarget = [Hierarchy](const FString& Name, const FString& Type)
		{
			if (Name.IsEmpty()) throw std::runtime_error("target_name is required");
			const FRigElementKey Target(FName(*Name), ParseRigElementType(Type));
			if (!Hierarchy->Contains(Target)) throw std::runtime_error("target does not exist in the Modular Rig hierarchy");
			return Target;
		};
		FRigElementKey SingleTarget;
		if (bConnect || bAddTarget || bRemoveTarget)
		{
			SingleTarget = ParseTarget(Body.TargetName, Body.TargetType);
			if (bConnect) Targets = {SingleTarget};
			else if (bAddTarget)
			{
				if (Targets.Contains(SingleTarget)) throw std::runtime_error("target is already connected");
				Targets.Add(SingleTarget);
			}
			else
			{
				if (!Targets.RemoveSingle(SingleTarget)) throw std::runtime_error("target is not connected");
				if (Targets.IsEmpty()) throw std::runtime_error("disconnect the connector to remove its last target");
			}
		}
		else if (bSetTargets)
		{
			Targets.Reset();
			for (const FModularRigTargetReq& Item : Body.Targets)
			{
				const FRigElementKey Target = ParseTarget(Item.Name, Item.Type);
				if (Targets.Contains(Target)) throw std::runtime_error("targets contain a duplicate element");
				Targets.Add(Target);
			}
		}
		else if (!bExisting) throw std::runtime_error("connector is not connected");
		if (!bDisconnect)
		{
			if (Targets.IsEmpty() || Targets.Num() > 64) throw std::runtime_error("targets must contain between 1 and 64 elements");
			FText Reason;
			if (!Controller->CanConnectConnectorToElements(Connector, Targets, Reason))
				throw std::runtime_error(TCHAR_TO_UTF8(*Reason.ToString()));
		}
		if (Body.bDryRun)
			return C.TextResponse(FString::Printf(TEXT("{\"changed\":false,\"dry_run\":true,\"target_count\":%d}"),
				bDisconnect ? 0 : Targets.Num()), TEXT("application/json"));
		if (bDisconnect && !Body.bConfirm) throw std::runtime_error("Modular Rig connector disconnection requires confirm=true");
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditModularRigConnection", "Edit Modular Rig Connection"));
		Asset->Modify();
		const bool bChanged = bDisconnect ? Controller->DisconnectConnector(Connector, false, false)
			: bAddTarget ? Controller->AddTargetToArrayConnector(Connector, SingleTarget, false, false, true)
			: Controller->ConnectConnectorToElements(Connector, Targets, false, false, true);
		if (!bChanged) throw std::runtime_error("Modular Rig controller rejected the connection operation");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":true,\"saved\":%s,\"target_count\":%d}"),
			Body.bSave ? TEXT("true") : TEXT("false"), bDisconnect ? 0 : Targets.Num()), TEXT("application/json"));
	});

	App->Get("/modular-rigs/validate", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		const FModularRigModel& Model = Rig->GetModularRigModel();
		const URigHierarchy* Hierarchy = Rig->GetHierarchy();
		TArray<FString> Errors;
		for (const FRigModuleReference& Module : Model.Modules)
		{
			if (Module.Class.IsNull()) Errors.Add(FString::Printf(TEXT("module %s has no class"), *Module.Name.ToString()));
			if (!Module.ParentModuleName.IsNone() && !Model.FindModule(Module.ParentModuleName))
				Errors.Add(FString::Printf(TEXT("module %s has a missing parent"), *Module.Name.ToString()));
		}
		int32 RequiredUnresolved = 0;
		if (Hierarchy)
			for (const FRigElementKey& Key : Hierarchy->GetAllKeys(false, ERigElementType::Connector))
			{
				if (Model.Connections.HasConnection(Key)) continue;
				const FRigConnectorElement* Connector = Hierarchy->Find<FRigConnectorElement>(Key);
				if (!Connector || !Connector->Settings.bOptional)
				{
					++RequiredUnresolved;
					Errors.Add(FString::Printf(TEXT("required connector %s is unresolved"), *Key.Name.ToString()));
				}
			}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("module_count"), Model.Modules.Num());
		Writer->WriteValue(TEXT("connection_count"), Model.Connections.Num());
		Writer->WriteValue(TEXT("required_unresolved"), RequiredUnresolved);
		Writer->WriteArrayStart(TEXT("errors"));
		for (const FString& Error : Errors) Writer->WriteValue(Error);
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/modular-rigs/variables", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		const FName ModuleName(*C.Query("module_name"));
		const FRigModuleReference* Module = Rig->GetModularRigModel().FindModule(ModuleName);
		if (!Module) throw std::runtime_error("module_name does not identify a module");
		UClass* ModuleClass = Module->Class.LoadSynchronous();
		if (!ModuleClass) throw std::runtime_error("module class could not be loaded");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("module_name"), ModuleName.ToString());
		Writer->WriteArrayStart(TEXT("variables"));
		for (TFieldIterator<FProperty> It(ModuleClass); It; ++It)
		{
			const FProperty* Property = *It;
			if (Property->GetOwnerUObject() != ModuleClass || !Property->HasAnyPropertyFlags(CPF_Edit | CPF_BlueprintVisible)) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Property->GetName());
			Writer->WriteValue(TEXT("type"), Property->GetCPPType());
			Writer->WriteValue(TEXT("read_only"), Property->HasAnyPropertyFlags(CPF_BlueprintReadOnly | CPF_DisableEditOnInstance));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("overrides"));
		for (const FControlRigOverrideValue& Override : Module->ConfigOverrides)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("path"), Override.GetPath());
			Writer->WriteValue(TEXT("value"), Override.ToString());
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("bindings"));
		for (const TPair<FName, FString>& Binding : Module->Bindings)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("variable"), Binding.Key.ToString());
			Writer->WriteValue(TEXT("source"), Binding.Value);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		const FString VariableName = C.Query("variable_name");
		if (!VariableName.IsEmpty())
		{
			UModularRigController* Controller = Rig->GetModularRigController();
			Writer->WriteArrayStart(TEXT("possible_bindings"));
			if (Controller)
				for (const FString& Path : Controller->GetPossibleBindings(ModuleName, FName(*VariableName)))
					Writer->WriteValue(Path);
			Writer->WriteArrayEnd();
		}
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/modular-rigs/variables", [](const FHttpContext<FModularRigReq, FString>& C)
	{
		const FModularRigReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		if (Body.VariablePath.IsEmpty()) throw std::runtime_error("variable_path is required");
		const FName ModuleName(*Body.ModuleName);
		FRigModuleReference* Module = Rig->GetModularRigModel().FindModule(ModuleName);
		if (!Module) throw std::runtime_error("module_name does not identify a module");
		UClass* ModuleClass = Module->Class.LoadSynchronous();
		if (!ModuleClass) throw std::runtime_error("module class could not be loaded");
		UModularRigController* Controller = Rig->GetModularRigController();
		if (!Controller) throw std::runtime_error("Modular Rig controller is unavailable");
		const bool bSet = Body.Operation.Equals(TEXT("set_override"), ESearchCase::IgnoreCase);
		const bool bReset = Body.Operation.Equals(TEXT("reset_override"), ESearchCase::IgnoreCase);
		const bool bBind = Body.Operation.Equals(TEXT("bind_variable"), ESearchCase::IgnoreCase);
		const bool bUnbind = Body.Operation.Equals(TEXT("unbind_variable"), ESearchCase::IgnoreCase);
		if (!bSet && !bReset && !bBind && !bUnbind)
			throw std::runtime_error("operation must be set_override, reset_override, bind_variable, or unbind_variable");
		FControlRigOverrideValue Override;
		if (bSet)
		{
			Override = FControlRigOverrideValue(Body.VariablePath, ModuleClass, Body.Value, ModuleName);
			if (!Override.IsValid()) throw std::runtime_error("variable_path or value is invalid for the module class");
		}
		if (bReset && !Module->ConfigOverrides.Contains(Body.VariablePath, ModuleName))
			throw std::runtime_error("variable_path has no override to reset");
		if (bBind || bUnbind)
		{
			if (Body.VariablePath.Contains(TEXT("->")) || Body.VariablePath.Contains(TEXT(".")))
				throw std::runtime_error("bindings require a top-level variable name");
			if (bBind)
			{
				if (Body.SourcePath.IsEmpty()) throw std::runtime_error("source_path is required");
				FText Reason;
				if (!Controller->CanBindModuleVariable(ModuleName, FName(*Body.VariablePath), Body.SourcePath, Reason))
					throw std::runtime_error(TCHAR_TO_UTF8(*Reason.ToString()));
			}
			else if (!Module->Bindings.Contains(FName(*Body.VariablePath)))
				throw std::runtime_error("variable is not bound");
		}
		if (Body.bDryRun) return C.TextResponse(TEXT("{\"changed\":false,\"dry_run\":true}"), TEXT("application/json"));
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditModularRigVariable", "Edit Modular Rig Variable"));
		Asset->Modify();
		const bool bChanged = bSet ? Controller->SetConfigValueInModule(ModuleName, Override, false)
			: bReset ? Controller->ResetConfigValueInModule(ModuleName, Body.VariablePath, true, false)
			: bBind ? Controller->BindModuleVariable(ModuleName, FName(*Body.VariablePath), Body.SourcePath, false)
			: Controller->UnBindModuleVariable(ModuleName, FName(*Body.VariablePath), false);
		if (!bChanged) throw std::runtime_error("Modular Rig controller rejected the variable operation");
		MarkAssetDirty(Asset);
		SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"changed\":true,\"saved\":%s}"), Body.bSave ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Post("/modular-rigs/compile", [](const FHttpContext<FModularRigReq, FString>& C)
	{
		const FModularRigReq Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		IControlRigAssetInterface* Rig = Cast<IControlRigAssetInterface>(Asset);
		if (!Rig || Rig->GetControlRigType() != EControlRigType::ModularRig)
			throw std::runtime_error("Asset is not a Modular Rig");
		URigVMBlueprint* Blueprint = Cast<URigVMBlueprint>(Asset);
		if (!Blueprint) throw std::runtime_error("this Modular Rig asset does not expose a public VM compile operation");
		if (Body.bDryRun) return C.TextResponse(TEXT("{\"compiled\":false,\"dry_run\":true}"), TEXT("application/json"));
		Rig->RecompileModularRig();
		Blueprint->RecompileVM();
		FRigVMAssetInterfacePtr VM = Rig->GetRigVMAssetInterface();
		const FCompilerResultsLog& Result = VM->GetCompileLog();
		const bool bSuccess = Result.NumErrors == 0 && VM->GetAssetStatus() != RVMA_Error;
		if (bSuccess) SaveIfRequested(Asset, Body.bSave);
		return C.TextResponse(FString::Printf(TEXT("{\"compiled\":true,\"valid\":%s,\"errors\":%d,\"warnings\":%d,\"saved\":%s}"),
			bSuccess ? TEXT("true") : TEXT("false"), Result.NumErrors, Result.NumWarnings,
			(bSuccess && Body.bSave) ? TEXT("true") : TEXT("false")), TEXT("application/json"));
	});

	App->Patch("/control-rigs/properties", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		ApplyAssetProperties(Asset, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/modular-rigs/properties", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		ApplyAssetProperties(Asset, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/assets/describe", [](const FHttpContext<void, FString>& C)
	{
		UObject* Asset = LoadAsset(C.Query("asset_path"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("class"), Asset->GetClass()->GetPathName());
		Writer->WriteValue(TEXT("package"), Asset->GetOutermost()->GetName());
		if (UBlueprint* Blueprint = Cast<UBlueprint>(Asset))
		{
			Writer->WriteValue(TEXT("is_blueprint"), true);
			Writer->WriteValue(TEXT("blueprint_type"), StaticEnum<EBlueprintType>()->GetNameStringByValue((int64)Blueprint->BlueprintType));
			Writer->WriteValue(TEXT("parent_class"), Blueprint->ParentClass ? Blueprint->ParentClass->GetPathName() : TEXT(""));
			if (UWidgetBlueprint* WidgetBlueprint = Cast<UWidgetBlueprint>(Blueprint))
			{
				Writer->WriteArrayStart(TEXT("widgets"));
				if (WidgetBlueprint->WidgetTree)
				{
					WidgetBlueprint->WidgetTree->ForEachWidget([&Writer](UWidget* Widget)
					{
						Writer->WriteObjectStart();
						Writer->WriteValue(TEXT("name"), Widget->GetName());
						Writer->WriteValue(TEXT("class"), Widget->GetClass()->GetPathName());
						Writer->WriteObjectEnd();
					});
				}
				Writer->WriteArrayEnd();
			}
		}
		else
		{
			Writer->WriteValue(TEXT("is_blueprint"), false);
		}
		if (UAnimSequence* Sequence = Cast<UAnimSequence>(Asset))
		{
			Writer->WriteValue(TEXT("asset_family"), TEXT("animation"));
			Writer->WriteValue(TEXT("duration_seconds"), Sequence->GetPlayLength());
			Writer->WriteValue(TEXT("frame_count"), Sequence->GetNumberOfSampledKeys());
			Writer->WriteValue(TEXT("skeleton"), Sequence->GetSkeleton() ? Sequence->GetSkeleton()->GetPathName() : TEXT(""));
		}
		else if (UAnimMontage* Montage = Cast<UAnimMontage>(Asset))
		{
			Writer->WriteValue(TEXT("asset_family"), TEXT("animation"));
			Writer->WriteValue(TEXT("duration_seconds"), Montage->GetPlayLength());
			Writer->WriteValue(TEXT("skeleton"), Montage->GetSkeleton() ? Montage->GetSkeleton()->GetPathName() : TEXT(""));
		}
		else if (UStaticMesh* Mesh = Cast<UStaticMesh>(Asset))
		{
			Writer->WriteValue(TEXT("asset_family"), TEXT("static_mesh"));
			Writer->WriteValue(TEXT("lod_count"), Mesh->GetNumLODs());
			Writer->WriteValue(TEXT("vertex_count_lod0"), Mesh->GetNumVertices(0));
			Writer->WriteValue(TEXT("bounds_radius"), Mesh->GetBounds().SphereRadius);
		}
		else if (USkeletalMesh* SkeletalMesh = Cast<USkeletalMesh>(Asset))
		{
			Writer->WriteValue(TEXT("asset_family"), TEXT("skeletal_mesh"));
			Writer->WriteValue(TEXT("lod_count"), SkeletalMesh->GetLODNum());
			Writer->WriteValue(TEXT("bone_count"), SkeletalMesh->GetRefSkeleton().GetNum());
			Writer->WriteValue(TEXT("skeleton"), SkeletalMesh->GetSkeleton() ? SkeletalMesh->GetSkeleton()->GetPathName() : TEXT(""));
		}
		else if (UTexture2D* Texture = Cast<UTexture2D>(Asset))
		{
			Writer->WriteValue(TEXT("asset_family"), TEXT("texture"));
			Writer->WriteValue(TEXT("width"), Texture->GetSizeX());
			Writer->WriteValue(TEXT("height"), Texture->GetSizeY());
			Writer->WriteValue(TEXT("srgb"), Texture->SRGB);
		}
		else if (UMaterialInterface* Material = Cast<UMaterialInterface>(Asset))
		{
			Writer->WriteValue(TEXT("asset_family"), TEXT("material"));
			TArray<FMaterialParameterInfo> ScalarInfos;
			TArray<FGuid> ScalarIds;
			Material->GetAllScalarParameterInfo(ScalarInfos, ScalarIds);
			Writer->WriteObjectStart(TEXT("scalar_parameters"));
			for (const FMaterialParameterInfo& Info : ScalarInfos)
			{
				float Value = 0.0f;
				if (Material->GetScalarParameterValue(Info, Value))
					Writer->WriteValue(Info.Name.ToString(), Value);
			}
			Writer->WriteObjectEnd();
		}
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Get("/data-tables/rows", [](const FHttpContext<void, FString>& C)
	{
		UDataTable* Table = Cast<UDataTable>(LoadAsset(C.Query("asset_path")));
		if (!Table)
			throw std::runtime_error("Asset is not a DataTable");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("row_struct"), Table->GetRowStruct() ? Table->GetRowStruct()->GetPathName() : TEXT(""));
		Writer->WriteArrayStart(TEXT("rows"));
		for (const FName& RowName : Table->GetRowNames())
		{
			const uint8* const* RowPtr = Table->GetRowMap().Find(RowName);
			FString RowJson;
			if (RowPtr && *RowPtr && Table->GetRowStruct())
				FJsonObjectConverter::UStructToJsonObjectString(Table->GetRowStruct(), *RowPtr, RowJson, 0, 0);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), RowName.ToString());
			Writer->WriteRawJSONValue(TEXT("data"), RowJson.IsEmpty() ? TEXT("{}") : RowJson);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Put("/data-tables/rows", [](const FHttpContext<FDataTableRowReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UDataTable* Table = Cast<UDataTable>(LoadAsset(Body.AssetPath));
		if (!Table || !Table->GetRowStruct())
			throw std::runtime_error("Asset is not a DataTable with a row struct");
		if (Body.RowName.IsEmpty() || Body.RowJson.IsEmpty())
			throw std::runtime_error("row_name and row_json are required");

		void* RowData = FMemory::Malloc(Table->GetRowStruct()->GetStructureSize());
		Table->GetRowStruct()->InitializeStruct(RowData);
		TSharedPtr<FJsonObject> RowObject;
		TSharedRef<TJsonReader<>> RowReader = TJsonReaderFactory<>::Create(Body.RowJson);
		const bool bParsed = FJsonSerializer::Deserialize(RowReader, RowObject) && RowObject.IsValid()
			&& FJsonObjectConverter::JsonObjectToUStruct(RowObject.ToSharedRef(), Table->GetRowStruct(), RowData, 0, 0, true);
		if (!bParsed)
		{
			Table->GetRowStruct()->DestroyStruct(RowData);
			FMemory::Free(RowData);
			throw std::runtime_error("row_json does not match the DataTable row struct");
		}
		Table->RemoveRow(FName(*Body.RowName));
		Table->AddRow(FName(*Body.RowName), *static_cast<FTableRowBase*>(RowData));
		Table->GetRowStruct()->DestroyStruct(RowData);
		FMemory::Free(RowData);
		MarkAssetDirty(Table);
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete("/data-tables/rows", [](const FHttpContext<FDataTableRowReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UDataTable* Table = Cast<UDataTable>(LoadAsset(Body.AssetPath));
		if (!Table)
			throw std::runtime_error("Asset is not a DataTable");
		Table->RemoveRow(FName(*Body.RowName));
		MarkAssetDirty(Table);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/assets/properties", [](const FHttpContext<void, FString>& C)
	{
		return C.TextResponse(ObjUtils::SerializeObjectToJson(LoadAsset(C.Query("asset_path"))), TEXT("application/json"));
	});

	App->Get("/assets/list", [](const FHttpContext<void, FString>& C)
	{
		const FString Directory = C.Query("directory_path", TEXT("/Game"));
		const bool bRecursive = C.Query("recursive", TEXT("true")).Equals(TEXT("true"), ESearchCase::IgnoreCase);
		const TArray<FString> Assets = AssetSubsystem()->ListAssets(Directory, bRecursive, false);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		for (const FString& Asset : Assets)
			Writer->WriteValue(Asset);
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/assets/save", [](const FHttpContext<FAssetActionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (!AssetSubsystem()->SaveAsset(Body.AssetPath, true))
			throw std::runtime_error("Failed to save asset");
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/assets/duplicate", [](const FHttpContext<FAssetActionReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UObject* Duplicate = AssetSubsystem()->DuplicateAsset(Body.AssetPath, Body.DestinationPath);
		if (!Duplicate)
			throw std::runtime_error("Failed to duplicate asset");
		return C.TextResponse(Duplicate->GetPathName());
	});

	App->Post("/assets/rename", [](const FHttpContext<FAssetActionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (!AssetSubsystem()->RenameAsset(Body.AssetPath, Body.DestinationPath))
			throw std::runtime_error("Failed to rename asset");
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/assets/referencers", [](const FHttpContext<void, FString>& C)
	{
		const TArray<FString> Referencers = AssetSubsystem()->FindPackageReferencersForAsset(C.Query("asset_path"), false);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		for (const FString& Referencer : Referencers)
			Writer->WriteValue(Referencer);
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/assets/delete", [](const FHttpContext<FAssetActionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		if (Body.AssetPath.IsEmpty())
			throw std::runtime_error("asset_path is required");
		// Deleting the package of an open world (or one of its loaded levels) crashes the editor; load another map first.
		const FString Package = FPackageName::ObjectPathToPackageName(Body.AssetPath);
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			const UWorld* World = Context.World();
			if (!IsValid(World))
				continue;
			for (const ULevel* Level : World->GetLevels())
			{
				if (IsValid(Level) && Level->GetOutermost()->GetName() == Package)
					throw std::runtime_error("Asset is a world or level that is currently open; load another map before deleting it");
			}
		}
		if (!AssetSubsystem()->DeleteAsset(Body.AssetPath))
			throw std::runtime_error("Failed to delete asset");
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/assets/properties", [](const FHttpContext<FAssetPropertyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UObject* Asset = LoadAsset(Body.AssetPath);
		ApplyAssetProperties(Asset, Body);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/widget-blueprints/widgets", [](const FHttpContext<void, FString>& C)
	{
		UWidgetBlueprint* Blueprint = LoadWidgetBlueprint(C.Query("asset_path"));
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		Blueprint->WidgetTree->ForEachWidget([&Writer](UWidget* Widget)
		{
			int32 ChildIndex = INDEX_NONE;
			UPanelWidget* Parent = UWidgetTree::FindWidgetParent(Widget, ChildIndex);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Widget->GetName());
			Writer->WriteValue(TEXT("class"), Widget->GetClass()->GetPathName());
			Writer->WriteValue(TEXT("parent"), Parent ? Parent->GetName() : TEXT(""));
			Writer->WriteValue(TEXT("child_index"), ChildIndex);
			Writer->WriteObjectEnd();
		});
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/widget-blueprints/widgets", [](const FHttpContext<FWidgetOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UWidgetBlueprint* Blueprint = LoadWidgetBlueprint(Body.AssetPath);
		UClass* WidgetClass = LoadClass<UWidget>(nullptr, *Body.WidgetClass);
		if (!WidgetClass || !WidgetClass->IsChildOf(UWidget::StaticClass()))
			throw std::runtime_error("widget_class must be a valid UWidget class path");
		if (Body.WidgetName.IsEmpty())
			throw std::runtime_error("widget_name is required");
		if (Blueprint->WidgetTree->FindWidget(FName(*Body.WidgetName)))
			throw std::runtime_error("A widget with this name already exists");
		UWidget* Widget = NewObject<UWidget>(Blueprint->WidgetTree, WidgetClass, FName(*Body.WidgetName), RF_Transactional);
		if (!Widget)
			throw std::runtime_error("Failed to create widget");
		if (Body.ParentName.IsEmpty())
		{
			if (Blueprint->WidgetTree->RootWidget)
				throw std::runtime_error("A Widget Blueprint can only have one root widget");
			Blueprint->WidgetTree->RootWidget = Widget;
		}
		else
		{
			UPanelWidget* Parent = Cast<UPanelWidget>(Blueprint->WidgetTree->FindWidget(FName(*Body.ParentName)));
			if (!Parent || !Parent->AddChild(Widget))
				throw std::runtime_error("parent_name must identify a panel widget");
		}
		Blueprint->OnVariableAdded(Widget->GetFName());  // The widget compiler expects every widget to have a variable GUID.
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete("/widget-blueprints/widgets", [](const FHttpContext<FWidgetOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UWidgetBlueprint* Blueprint = LoadWidgetBlueprint(Body.AssetPath);
		UWidget* Widget = Blueprint->WidgetTree->FindWidget(FName(*Body.WidgetName));
		if (!Widget || !Blueprint->WidgetTree->RemoveWidget(Widget))
			throw std::runtime_error("Widget not found or could not be removed");
		Blueprint->OnVariableRemoved(Widget->GetFName());
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/widget-blueprints/widgets/properties", [](const FHttpContext<FWidgetOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UWidgetBlueprint* Blueprint = LoadWidgetBlueprint(Body.AssetPath);
		UWidget* Widget = Blueprint->WidgetTree->FindWidget(FName(*Body.WidgetName));
		if (!Widget)
			throw std::runtime_error("Widget not found");
		for (const auto& Property : Body.Properties)
			ObjUtils::SetPropertyValueFromString(Widget, Property.Key, Property.Value);
		FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/widget-blueprints/widgets/reparent", [](const FHttpContext<FWidgetOperationReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UWidgetBlueprint* Blueprint = LoadWidgetBlueprint(Body.AssetPath);
		UWidget* Widget = Blueprint->WidgetTree->FindWidget(FName(*Body.WidgetName));
		UPanelWidget* NewParent = Cast<UPanelWidget>(Blueprint->WidgetTree->FindWidget(FName(*Body.NewParentName)));
		if (!Widget || !NewParent || Widget == NewParent)
			throw std::runtime_error("Widget or new parent panel was not found");
		int32 ChildIndex = INDEX_NONE;
		UPanelWidget* OldParent = UWidgetTree::FindWidgetParent(Widget, ChildIndex);
		if (OldParent)
			OldParent->RemoveChild(Widget);
		if (!NewParent->AddChild(Widget))
			throw std::runtime_error("Failed to add widget to new parent");
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/materials/parameters", [](const FHttpContext<FAssetParameterReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterialInstanceConstant* Material = Cast<UMaterialInstanceConstant>(LoadAsset(Body.AssetPath));
		if (!Material)
			throw std::runtime_error("Material parameter editing requires a Material Instance Constant");
		if (Body.ParameterName.IsEmpty() || Body.ParameterType.IsEmpty())
			throw std::runtime_error("parameter_name and parameter_type are required");

		const FName ParameterName(*Body.ParameterName);
		if (Body.ParameterType.Equals(TEXT("scalar"), ESearchCase::IgnoreCase))
		{
			float Value = 0.0f;
			if (!LexTryParseString(Value, *Body.Value))
				throw std::runtime_error("scalar parameter value must be numeric");
			Material->SetScalarParameterValueEditorOnly(ParameterName, Value);
		}
		else if (Body.ParameterType.Equals(TEXT("vector"), ESearchCase::IgnoreCase))
		{
			FLinearColor Color;
			if (!Color.InitFromString(Body.Value))
				throw std::runtime_error("vector parameter value must use R=,G=,B=,A= syntax");
			Material->SetVectorParameterValueEditorOnly(ParameterName, Color);
		}
		else if (Body.ParameterType.Equals(TEXT("texture"), ESearchCase::IgnoreCase))
		{
			UTexture* Texture = Cast<UTexture>(StaticLoadObject(UTexture::StaticClass(), nullptr, *Body.Value));
			if (!Texture)
				throw std::runtime_error("texture parameter value must be a valid texture asset path");
			Material->SetTextureParameterValueEditorOnly(ParameterName, Texture);
		}
		else
		{
			throw std::runtime_error("parameter_type must be scalar, vector, or texture");
		}
		MarkAssetDirty(Material);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/materials/expressions", [](const FHttpContext<void, FString>& C)
	{
		UMaterial* Material = Cast<UMaterial>(LoadAsset(C.Query("asset_path")));
		if (!Material)
			throw std::runtime_error("Asset is not a parent Material");
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteArrayStart();
		for (UMaterialExpression* Expression : Material->GetExpressions())
		{
			if (!Expression)
				continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Expression->GetName());
			Writer->WriteValue(TEXT("class"), Expression->GetClass()->GetPathName());
			Writer->WriteValue(TEXT("x"), Expression->MaterialExpressionEditorX);
			Writer->WriteValue(TEXT("y"), Expression->MaterialExpressionEditorY);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Post("/materials/expressions", [](const FHttpContext<FMaterialExpressionReq, FString>& C)
	{
		auto Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		UClass* ExpressionClass = FindObject<UClass>(nullptr, *Body.ExpressionClass);
		if (!ExpressionClass)
			ExpressionClass = LoadClass<UMaterialExpression>(nullptr, *Body.ExpressionClass);
		if (!Material || !ExpressionClass || !ExpressionClass->IsChildOf(UMaterialExpression::StaticClass()))
			throw std::runtime_error("A valid parent material and material expression class are required");
		UMaterialExpression* Expression = UMaterialEditingLibrary::CreateMaterialExpression(Material, ExpressionClass, Body.NodePosX, Body.NodePosY);
		if (!Expression)
			throw std::runtime_error("Failed to create material expression");
		if (!Body.ExpressionName.IsEmpty())
			Expression->Rename(*Body.ExpressionName, Material, REN_DontCreateRedirectors);
		MarkAssetDirty(Material);
		return C.TextResponse(Expression->GetName());
	});

	App->Post("/materials/expressions/connect", [](const FHttpContext<FMaterialExpressionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		UMaterialExpression* From = FindMaterialExpression(Material, Body.FromExpression);
		UMaterialExpression* To = FindMaterialExpression(Material, Body.ToExpression);
		if (!Material || !From || !To)
			throw std::runtime_error("Material or expression name not found");
		if (!UMaterialEditingLibrary::ConnectMaterialExpressions(From, Body.FromOutput, To, Body.ToInput))
			throw std::runtime_error("Failed to connect material expressions");
		UMaterialEditingLibrary::RecompileMaterial(Material);
		MarkAssetDirty(Material);
		return C.JsonResponse(FActionResponse {});
	});

	App->Delete("/materials/expressions", [](const FHttpContext<FMaterialExpressionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		UMaterialExpression* Expression = FindMaterialExpression(Material, Body.ExpressionName);
		if (!Material || !Expression)
			throw std::runtime_error("Material or expression name not found");
		UMaterialEditingLibrary::DeleteMaterialExpression(Material, Expression);
		MarkAssetDirty(Material);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/materials/layout", [](const FHttpContext<FAssetActionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UMaterial* Material = Cast<UMaterial>(LoadAsset(Body.AssetPath));
		if (!Material)
			throw std::runtime_error("Asset is not a parent Material");
		UMaterialEditingLibrary::LayoutMaterialExpressions(Material);
		MarkAssetDirty(Material);
		return C.JsonResponse(FActionResponse {});
	});

	App->Get("/static-meshes/source", [](const FHttpContext<void, FString>& C)
	{
		UStaticMesh* Mesh = Cast<UStaticMesh>(LoadAsset(C.Query("asset_path")));
		if (!Mesh) throw std::runtime_error("Asset is not a Static Mesh");
		return C.TextResponse(StaticMeshImportUtils::SourceJson(Mesh), TEXT("application/json"));
	});

	App->Post("/static-meshes/import", [](const FHttpContext<FStaticMeshImportReq, FString>& C)
	{
		return C.TextResponse(StaticMeshImportUtils::Import(C.RequestBody()), TEXT("application/json"));
	});

	App->Post("/static-meshes/reimport", [](const FHttpContext<FStaticMeshImportReq, FString>& C)
	{
		const FStaticMeshImportReq Body = C.RequestBody();
		UStaticMesh* Mesh = Cast<UStaticMesh>(LoadAsset(Body.AssetPath));
		if (!Mesh) throw std::runtime_error("Asset is not a Static Mesh");
		return C.TextResponse(StaticMeshImportUtils::Reimport(Mesh, Body), TEXT("application/json"));
	});

	App->Patch("/static-meshes/materials", [](const FHttpContext<FMeshMaterialReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UStaticMesh* Mesh = Cast<UStaticMesh>(LoadAsset(Body.AssetPath));
		UMaterialInterface* Material = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, *Body.MaterialPath));
		if (!Mesh || !Material)
			throw std::runtime_error("A valid static mesh and material asset are required");
		if (Body.SlotIndex < 0 || Body.SlotIndex >= Mesh->GetStaticMaterials().Num())
			throw std::runtime_error("Static mesh material slot index is out of range");
		Mesh->SetMaterial(Body.SlotIndex, Material);
		Mesh->Modify();
		MarkAssetDirty(Mesh);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/static-meshes/lod-screen-sizes", [](const FHttpContext<FStaticMeshLodReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UStaticMesh* Mesh = Cast<UStaticMesh>(LoadAsset(Body.AssetPath));
		if (!Mesh || Body.ScreenSizes.Num() == 0)
			throw std::runtime_error("A static mesh and non-empty screen_sizes are required");
		if (!StaticMeshSubsystem()->SetLodScreenSizes(Mesh, Body.ScreenSizes))
			throw std::runtime_error("Failed to set static mesh LOD screen sizes");
		MarkAssetDirty(Mesh);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/static-meshes/lod-group", [](const FHttpContext<FStaticMeshLodReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UStaticMesh* Mesh = Cast<UStaticMesh>(LoadAsset(Body.AssetPath));
		if (!Mesh || Body.LODGroup.IsEmpty())
			throw std::runtime_error("A static mesh and lod_group are required");
		if (!StaticMeshSubsystem()->SetLODGroup(Mesh, FName(*Body.LODGroup), true))
			throw std::runtime_error("Failed to set static mesh LOD group");
		MarkAssetDirty(Mesh);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/static-meshes/settings", [](const FHttpContext<FStaticMeshSettingsReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UStaticMesh* Mesh = Cast<UStaticMesh>(LoadAsset(Body.AssetPath));
		if (!Mesh)
			throw std::runtime_error("Asset is not a static mesh");
		if (Body.Property.Equals(TEXT("generate_lightmap_uvs"), ESearchCase::IgnoreCase))
		{
			if (!StaticMeshSubsystem()->SetGenerateLightmapUVs(Mesh, Body.bValue))
				throw std::runtime_error("Failed to set static mesh lightmap UV setting");
		}
		else if (Body.Property.Equals(TEXT("allow_cpu_access"), ESearchCase::IgnoreCase))
		{
			StaticMeshSubsystem()->SetAllowCPUAccess(Mesh, Body.bValue);
		}
		else
		{
			throw std::runtime_error("property must be generate_lightmap_uvs or allow_cpu_access");
		}
		MarkAssetDirty(Mesh);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/skeletal-meshes/materials", [](const FHttpContext<FMeshMaterialReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		USkeletalMesh* Mesh = Cast<USkeletalMesh>(StaticLoadObject(USkeletalMesh::StaticClass(), nullptr, *Body.AssetPath));
		UMaterialInterface* Material = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, *Body.MaterialPath));
		if (!Mesh || !Material)
			throw std::runtime_error("A valid skeletal mesh and material asset are required");
		TArray<FSkeletalMaterial> Materials = Mesh->GetMaterials();
		if (Body.SlotIndex < 0 || Body.SlotIndex >= Materials.Num())
			throw std::runtime_error("Skeletal mesh material slot index is out of range");
		Materials[Body.SlotIndex].MaterialInterface = Material;
		Mesh->SetMaterials(Materials);
		Mesh->Modify();
		MarkAssetDirty(Mesh);
		return C.JsonResponse(FActionResponse {});
	});

	App->Patch("/skeletal-meshes/sections", [](const FHttpContext<FSkeletalSectionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		USkeletalMesh* Mesh = Cast<USkeletalMesh>(StaticLoadObject(USkeletalMesh::StaticClass(), nullptr, *Body.AssetPath));
		if (!Mesh)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Asset is not a skeletal mesh: %s"), *Body.AssetPath)));
		bool bSuccess = false;
		if (Body.Property.Equals(TEXT("recompute_tangent"), ESearchCase::IgnoreCase))
			bSuccess = SkeletalMeshSubsystem()->SetSectionRecomputeTangent(Mesh, Body.LODIndex, Body.SectionIndex, Body.bValue);
		else if (Body.Property.Equals(TEXT("cast_shadow"), ESearchCase::IgnoreCase))
			bSuccess = SkeletalMeshSubsystem()->SetSectionCastShadow(Mesh, Body.LODIndex, Body.SectionIndex, Body.bValue);
		else if (Body.Property.Equals(TEXT("visible_in_ray_tracing"), ESearchCase::IgnoreCase))
			bSuccess = SkeletalMeshSubsystem()->SetSectionVisibleInRayTracing(Mesh, Body.LODIndex, Body.SectionIndex, Body.bValue);
		else
			throw std::runtime_error("property must be recompute_tangent, cast_shadow, or visible_in_ray_tracing");
		if (!bSuccess)
			throw std::runtime_error("Invalid skeletal mesh LOD or section index");
		MarkAssetDirty(Mesh);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/animations/notifies", [](const FHttpContext<FAnimationNotifyReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UAnimSequenceBase* Animation = Cast<UAnimSequenceBase>(LoadAsset(Body.AssetPath));
		if (!Animation)
			throw std::runtime_error("Asset is not an animation sequence or montage");
		const bool bTimed = Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_state"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_float_key"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_vector_key"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_sync_marker"), ESearchCase::IgnoreCase);
		if (bTimed && (!FMath::IsFinite(Body.Time) || Body.Time < 0.0f || Body.Time > Animation->GetPlayLength()))
			throw std::runtime_error("time must be finite and within the animation play range");
		if (Body.Operation.Equals(TEXT("add_state"), ESearchCase::IgnoreCase)
			&& (!FMath::IsFinite(Body.Duration) || Body.Duration <= 0.0f || Body.Time + Body.Duration > Animation->GetPlayLength()))
			throw std::runtime_error("notify-state duration must be positive and within the animation play range");
		// notify_track is optional when adding: use the first track, creating the engine's default "1" on a sequence with none.
		if (Body.NotifyTrack.IsEmpty() && (Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase) || Body.Operation.Equals(TEXT("add_state"), ESearchCase::IgnoreCase) || Body.Operation.Equals(TEXT("add_sync_marker"), ESearchCase::IgnoreCase)))
		{
			if (Animation->AnimNotifyTracks.IsEmpty()) UAnimationBlueprintLibrary::AddAnimationNotifyTrack(Animation, TEXT("1"));
			Body.NotifyTrack = Animation->AnimNotifyTracks[0].TrackName.ToString();
		}
		if ((Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_state"), ESearchCase::IgnoreCase)
			|| Body.Operation.Equals(TEXT("add_sync_marker"), ESearchCase::IgnoreCase))
			&& !UAnimationBlueprintLibrary::IsValidAnimNotifyTrackName(Animation, FName(*Body.NotifyTrack)))
			throw std::runtime_error("notify_track must identify an existing notify track");
		if (Body.Operation.Equals(TEXT("add"), ESearchCase::IgnoreCase))
		{
			UClass* NotifyClass = LoadClass<UAnimNotify>(nullptr, *Body.NotifyClass);
			if (!NotifyClass || !NotifyClass->IsChildOf(UAnimNotify::StaticClass()))
				throw std::runtime_error("notify_class must be a valid UAnimNotify class path");
			UAnimationBlueprintLibrary::AddAnimationNotifyEvent(Animation, FName(*Body.NotifyTrack), Body.Time, NotifyClass);
		}
		else if (Body.Operation.Equals(TEXT("add_state"), ESearchCase::IgnoreCase))
		{
			UClass* NotifyClass = LoadClass<UAnimNotifyState>(nullptr, *Body.NotifyClass);
			if (!NotifyClass || !NotifyClass->IsChildOf(UAnimNotifyState::StaticClass()))
				throw std::runtime_error("notify_class must be a valid UAnimNotifyState class path");
			UAnimationBlueprintLibrary::AddAnimationNotifyStateEvent(Animation, FName(*Body.NotifyTrack), Body.Time, Body.Duration, NotifyClass);
		}
		else if (Body.Operation.Equals(TEXT("remove_name"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::RemoveAnimationNotifyEventsByName(Animation, FName(*Body.NotifyName));
		}
		else if (Body.Operation.Equals(TEXT("remove_track"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::RemoveAnimationNotifyEventsByTrack(Animation, FName(*Body.NotifyTrack));
		}
		else if (Body.Operation.Equals(TEXT("add_track"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::AddAnimationNotifyTrack(Animation, FName(*Body.NotifyTrack));
		}
		else if (Body.Operation.Equals(TEXT("remove_notify_track"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::RemoveAnimationNotifyTrack(Animation, FName(*Body.NotifyTrack));
		}
		else if (Body.Operation.Equals(TEXT("add_curve"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::AddCurve(Animation, FName(*Body.NotifyName));
		}
		else if (Body.Operation.Equals(TEXT("remove_curve"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::RemoveCurve(Animation, FName(*Body.NotifyName));
		}
		else if (Body.Operation.Equals(TEXT("add_float_key"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::AddFloatCurveKey(Animation, FName(*Body.NotifyName), Body.Time, Body.Value);
		}
		else if (Body.Operation.Equals(TEXT("add_vector_key"), ESearchCase::IgnoreCase))
		{
			UAnimationBlueprintLibrary::AddVectorCurveKey(Animation, FName(*Body.NotifyName), Body.Time, Body.VectorValue);
		}
		else if (Body.Operation.Equals(TEXT("add_sync_marker"), ESearchCase::IgnoreCase))
		{
			UAnimSequence* Sequence = Cast<UAnimSequence>(Animation);
			if (!Sequence)
				throw std::runtime_error("Sync markers require an animation sequence");
			if (Body.NotifyName.IsEmpty()) throw std::runtime_error("notify_name is required for a sync marker");
			const int32 Before = Sequence->AuthoredSyncMarkers.Num();
			UAnimationBlueprintLibrary::AddAnimationSyncMarker(Sequence, FName(*Body.NotifyName), Body.Time, FName(*Body.NotifyTrack));
			if (Sequence->AuthoredSyncMarkers.Num() != Before + 1)
				throw std::runtime_error("Unreal did not add the sync marker");
		}
		else if (Body.Operation.Equals(TEXT("remove_sync_marker"), ESearchCase::IgnoreCase))
		{
			UAnimSequence* Sequence = Cast<UAnimSequence>(Animation);
			if (!Sequence)
				throw std::runtime_error("Sync markers require an animation sequence");
			UAnimationBlueprintLibrary::RemoveAnimationSyncMarkersByName(Sequence, FName(*Body.NotifyName));
		}
		else
		{
			throw std::runtime_error("unsupported animation operation");
		}
		Animation->Modify();
		MarkAssetDirty(Animation);
		return C.JsonResponse(FActionResponse {});
	});

	App->Post("/animations/curves/key", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::EditFloatCurveKey(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/transform/time-offset", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::OffsetTransformCurveTime(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/time-offset", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::OffsetFloatCurveTime(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Get("/animations/curves/range", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AnimationSequenceUtils::FloatCurveRangeJson(Cast<UAnimSequence>(LoadAsset(C.Query("asset_path"))),FName(*C.Query("curve_name"))),TEXT("application/json")); });
	App->Patch("/animations/curves/comment", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetFloatCurveComment(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/color", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetFloatCurveColor(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/flag", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetFloatCurveFlag(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/name", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::RenameFloatCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/duplicate", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::DuplicateFloatCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/evaluate", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::EvaluateFloatCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/extrapolation", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetFloatCurveExtrapolation(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/rich", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::ReplaceRichFloatCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/time-scale", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::ScaleFloatCurveTime(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Delete("/animations/curves/transform/key-range", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::RemoveTransformCurveKeyRange(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Delete("/animations/curves/key-range", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::RemoveFloatCurveKeyRange(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Get("/animations/curves/catalog", [](const FHttpContext<void,FString>& C) { const FString Start=C.Query("start"),Count=C.Query("count"); return C.TextResponse(AnimationSequenceUtils::CurveCatalogJson(Cast<UAnimSequence>(LoadAsset(C.Query("asset_path"))),C.Query("search"),Start.IsEmpty() ? 0 : FCString::Atoi(*Start),Count.IsEmpty() ? 256 : FCString::Atoi(*Count)),TEXT("application/json")); });
	App->Get("/animations/curves/diagnostics", [](const FHttpContext<void,FString>& C) { return C.TextResponse(AnimationSequenceUtils::CurveDiagnosticsJson(Cast<UAnimSequence>(LoadAsset(C.Query("asset_path")))),TEXT("application/json")); });
	App->Post("/animations/curves/resample", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::ResampleFloatCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/transform/resample", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::ResampleTransformCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/transform/key/time", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::MoveTransformCurveKey(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Get("/animations/curves/transform/keys", [](const FHttpContext<void,FString>& C) { const FString Start=C.Query("start"),Count=C.Query("count"); return C.TextResponse(AnimationSequenceUtils::TransformCurveKeysJson(Cast<UAnimSequence>(LoadAsset(C.Query("asset_path"))),FName(*C.Query("curve_name")),Start.IsEmpty() ? 0 : FCString::Atoi(*Start),Count.IsEmpty() ? 256 : FCString::Atoi(*Count),C.Query("union_timeline")==TEXT("true")),TEXT("application/json")); });
	App->Patch("/animations/curves/transform/keys", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::ReplaceTransformCurveKeys(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/transform/flag", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetTransformCurveFlag(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Delete("/animations/curves/transform/key", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::RemoveTransformCurveKey(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/transform/key", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetTransformCurveKey(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/transform/name", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::RenameTransformCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/transform/duplicate", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::DuplicateTransformCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Delete("/animations/curves/transform", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::RemoveTransformCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/transform", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::CreateTransformCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/transform/evaluate", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::EvaluateTransformCurve(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/transform-channel/extrapolation", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::SetTransformChannelExtrapolation(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Post("/animations/curves/transform-channel/evaluate", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::EvaluateTransformChannel(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Patch("/animations/curves/transform-channel", [](const FHttpContext<FAnimationRichCurveReq,FString>& C) { const auto R=C.RequestBody(); return C.TextResponse(AnimationSequenceUtils::ReplaceRichTransformChannel(Cast<UAnimSequence>(LoadAsset(R.AssetPath)),R),TEXT("application/json")); });
	App->Get("/animations/curves/transform-channel", [](const FHttpContext<void,FString>& C) { const FString Start=C.Query("start"),Count=C.Query("count"),Axis=C.Query("axis"); return C.TextResponse(AnimationSequenceUtils::RichTransformChannelJson(Cast<UAnimSequence>(LoadAsset(C.Query("asset_path"))),FName(*C.Query("curve_name")),C.Query("channel"),Axis.IsEmpty() ? 0 : FCString::Atoi(*Axis),Start.IsEmpty() ? 0 : FCString::Atoi(*Start),Count.IsEmpty() ? 256 : FCString::Atoi(*Count)),TEXT("application/json")); });
	App->Get("/animations/curves/rich", [](const FHttpContext<void,FString>& C) { const FString Start=C.Query("start"),Count=C.Query("count"); return C.TextResponse(AnimationSequenceUtils::RichFloatCurveJson(Cast<UAnimSequence>(LoadAsset(C.Query("asset_path"))),FName(*C.Query("curve_name")),Start.IsEmpty() ? 0 : FCString::Atoi(*Start),Count.IsEmpty() ? 256 : FCString::Atoi(*Count)),TEXT("application/json")); });
	App->Get("/animations/curves", [](const FHttpContext<void, FString>& C)
	{
		UAnimSequenceBase* Animation = Cast<UAnimSequenceBase>(LoadAsset(C.Query("asset_path")));
		if (!Animation)
			throw std::runtime_error("Asset is not an animation sequence or montage");
		const FName CurveName(*C.Query("curve_name"));
		TArray<float> Times;
		TArray<float> Values;
		UAnimationBlueprintLibrary::GetFloatKeys(Animation, CurveName, Times, Values);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("curve"), CurveName.ToString());
		Writer->WriteArrayStart(TEXT("keys"));
		for (int32 Index = 0; Index < Times.Num() && Index < Values.Num(); ++Index)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("time"), Times[Index]);
			Writer->WriteValue(TEXT("value"), Values[Index]);
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
		Writer->Close();
		return C.TextResponse(Json, TEXT("application/json"));
	});

	App->Patch("/animations/montage-sections", [](const FHttpContext<FAnimationSectionReq, FActionResponse>& C)
	{
		auto Body = C.RequestBody();
		UAnimMontage* Montage = Cast<UAnimMontage>(LoadAsset(Body.AssetPath));
		if (!Montage || Body.SectionName.IsEmpty())
			throw std::runtime_error("A montage and section_name are required");
		int32 SectionIndex = Montage->CompositeSections.IndexOfByPredicate([&Body](const FCompositeSection& Section)
		{
			return Section.SectionName == FName(*Body.SectionName);
		});
		if (Body.bDelete)
		{
			if (SectionIndex != INDEX_NONE)
				Montage->DeleteAnimCompositeSection(SectionIndex);
		}
		else
		{
			if (SectionIndex == INDEX_NONE)
			{
				const int32 NewIndex = Montage->AddAnimCompositeSection(FName(*Body.SectionName), Body.StartTime);
				if (NewIndex == INDEX_NONE)
					throw std::runtime_error("Failed to add montage section");
				Montage->CompositeSections[NewIndex].NextSectionName = FName(*Body.NextSectionName);
			}
			else
			{
				FCompositeSection& Section = Montage->CompositeSections[SectionIndex];
				Section.SetTime(Body.StartTime);
				Section.NextSectionName = FName(*Body.NextSectionName);
			}
		}
		Montage->Modify();
		MarkAssetDirty(Montage);
		return C.JsonResponse(FActionResponse {});
	});
}
