#pragma once
#include "CoreMinimal.h"
#include "NavigationLinkReq.generated.h"
USTRUCT()
struct FNavigationPointLinkReq
{
	GENERATED_BODY()
	UPROPERTY() FVector Left=FVector(-100,0,0);
	UPROPERTY() FVector Right=FVector(100,0,0);
	UPROPERTY() FString Direction=TEXT("BothWays");
	UPROPERTY() FString AreaClass=TEXT("/Script/NavigationSystem.NavArea_Default");
	UPROPERTY() float SnapRadius=50;
	UPROPERTY() bool bUseSnapHeight=true;
	UPROPERTY() float SnapHeight=100;
	UPROPERTY() bool bSnapToCheapestArea=false;
	UPROPERTY() float LeftProjectHeight=0;
	UPROPERTY() float RightProjectHeight=0;
	UPROPERTY() bool bSetSupportedAgents=false;
	UPROPERTY() TArray<int32> SupportedAgentIndices;
};
USTRUCT()
struct FNavigationLinkReq
{
	GENERATED_BODY()
	UPROPERTY() FString ActorPath;
	UPROPERTY() FString WorldPath;
	UPROPERTY() FString WorldContext=TEXT("editor");
	UPROPERTY() int32 PIEInstance=-1;
	UPROPERTY() FString Operation=TEXT("update");
	UPROPERTY() FVector Location=FVector::ZeroVector;
	UPROPERTY() FRotator Rotation=FRotator::ZeroRotator;
	UPROPERTY() FString Label;
	UPROPERTY() TArray<FNavigationPointLinkReq> PointLinks;
	UPROPERTY() FVector SmartLeft=FVector(-100,0,0);
	UPROPERTY() FVector SmartRight=FVector(100,0,0);
	UPROPERTY() FString SmartDirection=TEXT("BothWays");
	UPROPERTY() FString EnabledAreaClass=TEXT("/Script/NavigationSystem.NavArea_Default");
	UPROPERTY() FString DisabledAreaClass=TEXT("/Script/NavigationSystem.NavArea_Null");
	UPROPERTY() bool bSmartLinkRelevant=true;
	UPROPERTY() bool bEnabled=true;
	UPROPERTY() bool bSetSmartAgents=false;
	UPROPERTY() TArray<int32> SmartAgentIndices;
	UPROPERTY() bool bConfirm=false;
	UPROPERTY() bool bDryRun=false;
	UPROPERTY() bool bSave=false;
};
