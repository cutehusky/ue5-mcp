#pragma once
#include "CoreMinimal.h"
struct FSkeletonSocketReq;
struct FVirtualBoneReq;
struct FBoneRetargetReq;
struct FCompatibleSkeletonReq;
struct FSkeletonCurveReq;
namespace SkeletonUtils
{
 FString CurveMetadataLifecycle(const FSkeletonCurveReq& R);
 FString EditCurveMetadata(const FSkeletonCurveReq& R);
 FString RenameVirtualBone(const FVirtualBoneReq& R);
 FString DeleteVirtualBones(const FVirtualBoneReq& R);
 FString CreateVirtualBone(const FVirtualBoneReq& R);
 FString SetCompatibilityPolicy(const FCompatibleSkeletonReq& R);
 FString CompareHierarchy(const FCompatibleSkeletonReq& R);
 FString EditCompatibility(const FCompatibleSkeletonReq& R);
 FString InspectAnimationRetargetSource(const FBoneRetargetReq& R);
 FString SetAnimationRetargetMesh(const FBoneRetargetReq& R);
 FString SetAnimationRetargetSource(const FBoneRetargetReq& R);
 FString EditStoredRetargetPose(const FBoneRetargetReq& R);
 FString DuplicateRetargetSource(const FBoneRetargetReq& R);
 FString RenameRetargetSource(const FBoneRetargetReq& R);
 FString DeleteRetargetSource(const FBoneRetargetReq& R);
 FString EditRetargetSource(const FBoneRetargetReq& R);
 FString InspectRetargetPose(const FBoneRetargetReq& R);
 FString InspectBlendProfileScales(const FBoneRetargetReq& R);
 FString DeleteBlendProfile(const FBoneRetargetReq& R);
 FString InspectBlendProfileReferences(const FBoneRetargetReq& R);
 FString SetBlendProfileMode(const FBoneRetargetReq& R);
 FString RenameBlendProfile(const FBoneRetargetReq& R);
 FString CreateBlendProfile(const FBoneRetargetReq& R);
 FString ResetBlendProfileEntries(const FBoneRetargetReq& R);
 FString SetBlendProfileScales(const FBoneRetargetReq& R);
 FString SetTranslationRetargeting(const FBoneRetargetReq& R);
 FString EditPreviewAttachment(const FSkeletonSocketReq& R,bool MeshOwned);
 FString InspectRuntimeSocket(const FSkeletonSocketReq& R);
 FString PromoteMeshSocket(const FSkeletonSocketReq& R);
 FString CustomizeMeshSocket(const FSkeletonSocketReq& R);
 FString EditMeshSocket(const FSkeletonSocketReq& R);
 FString DeleteMeshSocket(const FSkeletonSocketReq& R);
 FString RenameMeshSocket(const FSkeletonSocketReq& R);
 FString RenameSocket(const FSkeletonSocketReq& R);
 FString DeleteSocket(const FSkeletonSocketReq& R);
 FString EditSocket(const FSkeletonSocketReq& R);
 FString InspectMeshSockets(const FString& AssetPath);
 FString Inspect(const FString& AssetPath);
}
