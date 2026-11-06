#pragma once
#include "CoreMinimal.h"
#include "NavigationAgentReq.generated.h"
USTRUCT()
struct FNavigationAgentReq
{
	GENERATED_BODY()
	UPROPERTY() FString ProbeId;
	UPROPERTY() FString Operation=TEXT("create");
	UPROPERTY() int32 PIEInstance=-1;
	/** Create projects this feet location to the native default navmesh. */
	UPROPERTY() FVector Location=FVector::ZeroVector;
	UPROPERTY() FVector Destination=FVector::ZeroVector;
	UPROPERTY() float Speed=300;
	UPROPERTY() float DurationSeconds=30;
	UPROPERTY() float AcceptanceRadius=20;
	UPROPERTY() FString FilterClass;
	UPROPERTY() FString SmartLinkPath;
	UPROPERTY() bool bAllowPartial=false;
	UPROPERTY() bool bProjectGoal=true;
	UPROPERTY() bool bDryRun=false;
};
