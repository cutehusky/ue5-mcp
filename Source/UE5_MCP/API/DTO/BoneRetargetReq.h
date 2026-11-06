#pragma once
#include "CoreMinimal.h"
#include "BoneRetargetReq.generated.h"
USTRUCT()
struct FRetargetPoseBoneReq
{
 GENERATED_BODY()
 UPROPERTY() FString Bone;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY() FVector Scale=FVector::OneVector;
};
USTRUCT()
struct FBoneRetargetReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() TArray<FString> Bones;
 UPROPERTY() FString PoseName;
 UPROPERTY() TArray<FRetargetPoseBoneReq> PoseEdits;
 UPROPERTY() bool bClearSourceMesh=false;
 UPROPERTY() bool bResetReferencePose=false;
 UPROPERTY() FString SourceMeshPath;
 UPROPERTY() FString Operation=TEXT("create");
 UPROPERTY() FString SourceProfileName;
 UPROPERTY() FString ProfileName;
 UPROPERTY() FString NewName;
 UPROPERTY() float Scale=1.f;
 UPROPERTY() FString Mode=TEXT("Animation");
 UPROPERTY() bool bChildren=false;
 UPROPERTY() bool bAllowReferenced=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
