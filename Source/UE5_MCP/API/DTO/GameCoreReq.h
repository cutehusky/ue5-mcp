#pragma once
#include "CoreMinimal.h"
#include "GameCoreReq.generated.h"
USTRUCT()
struct FGameCoreReq
{
 GENERATED_BODY()
 UPROPERTY() FString AssetPath;
 UPROPERTY() FString Kind;
 UPROPERTY() FString SourceFilePath;
 UPROPERTY() bool bImportMaterials=true;
 UPROPERTY() bool bImportAnimations=false;
 UPROPERTY() FString ParentPath;
 UPROPERTY() FString SkeletonPath;
 UPROPERTY() FString StructPath;
 UPROPERTY() FString AnimationPath;
 UPROPERTY() FString PropertyPath;
 UPROPERTY() FString Value;
 UPROPERTY() FString ExpectedValue;
 UPROPERTY() FString Key;
 UPROPERTY() FString Event=TEXT("press");
 UPROPERTY() float Amount=1;
 UPROPERTY() FString Actor;
 UPROPERTY() bool bUseWorldLocation=false;
 UPROPERTY() double WorldX=0;
 UPROPERTY() double WorldY=0;
 UPROPERTY() double WorldZ=0;
 UPROPERTY() double ScreenX=0;
 UPROPERTY() double ScreenY=0;
 UPROPERTY() FString Platform=TEXT("Win64");
 UPROPERTY() FString Configuration=TEXT("Development");
 UPROPERTY() FString NodeId;
 UPROPERTY() FString Operation;
 UPROPERTY() FString ClassName;
 UPROPERTY() FString ModuleName;
 UPROPERTY() int32 TimeoutSeconds=300;
 UPROPERTY() bool bWait=true;
 UPROPERTY() bool bAllowDirty=false;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
