#pragma once
#include "CoreMinimal.h"
#include "NavigationReq.generated.h"

USTRUCT()
struct FNavigationReq
{
	GENERATED_BODY()
	UPROPERTY() FString WorldPath;
	UPROPERTY() FString WorldContext=TEXT("editor");
	UPROPERTY() int32 PIEInstance=-1;
	UPROPERTY() FString Operation = TEXT("path");
	UPROPERTY() FString ActorPath;
	UPROPERTY() FString Label;
	/** Modifier routes use complete area references; empty disables/clears the respective reference. */
	UPROPERTY() FString AreaClass = TEXT("/Script/NavigationSystem.NavArea_Obstacle");
	UPROPERTY() FString AreaClassToReplace;
	UPROPERTY() FVector Location = FVector::ZeroVector;
	UPROPERTY() FVector Extent = FVector(500,500,250);
	UPROPERTY() FVector Start = FVector::ZeroVector;
	UPROPERTY() FVector End = FVector::ZeroVector;
	UPROPERTY() FVector QueryExtent = FVector(100,100,300);
	UPROPERTY() FString NavDataPath;
	UPROPERTY() FString FilterClass;
	UPROPERTY() bool bProjectEndpoints = true;
	UPROPERTY() bool bAllowPartial = false;
	UPROPERTY() int32 MaxSearchNodes = 2048;
	UPROPERTY() int32 MaxPoints = 256;
	UPROPERTY() double CostLimit = 1.e9;
	UPROPERTY() float Radius=500;
	UPROPERTY() int32 SampleCount=1;
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
