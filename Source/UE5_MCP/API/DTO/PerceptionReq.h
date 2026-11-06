#pragma once
#include "CoreMinimal.h"
#include "PerceptionReq.generated.h"
USTRUCT()
struct FPerceptionReq
{
 GENERATED_BODY()
 UPROPERTY() FString ComponentPath;
 UPROPERTY() FString Operation;
 UPROPERTY() FString SenseClassPath;
 UPROPERTY() FString ConfigClassPath;
 UPROPERTY() TArray<FString> SenseClasses;
 UPROPERTY() TMap<FString,FString> Properties;
 UPROPERTY() FString ActorPath;
 UPROPERTY() FString InstigatorPath;
 UPROPERTY() float DamageAmount=1;
 UPROPERTY() FVector HitLocation=FVector::ZeroVector;
 UPROPERTY() int32 PIEInstance=-1;
 UPROPERTY() FVector Location=FVector::ZeroVector;
 UPROPERTY() bool bUseActorLocation=true;
 UPROPERTY() float Loudness=1;
 UPROPERTY() float MaxRange=0;
 UPROPERTY() FString Tag;
 UPROPERTY() bool bEnabled=true;
 UPROPERTY() bool bConfirm=false;
 UPROPERTY() bool bDryRun=false;
 UPROPERTY() bool bSave=false;
};
