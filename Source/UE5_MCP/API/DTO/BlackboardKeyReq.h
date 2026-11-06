#pragma once

#include "CoreMinimal.h"
#include "BlackboardKeyReq.generated.h"

/** Only flags for the selected native key type may be supplied. */
USTRUCT()
struct FBlackboardTypeSettings
{
	GENERATED_BODY()
	UPROPERTY() bool bSetDefault=false;
	UPROPERTY() bool BoolValue=false;
	UPROPERTY() int64 IntValue=0;
	UPROPERTY() double FloatValue=0;
	UPROPERTY() FString TextValue;
	UPROPERTY() FVector VectorValue=FVector::ZeroVector;
	UPROPERTY() FRotator RotationValue=FRotator::ZeroRotator;
	UPROPERTY() FString ReferenceValue;
	UPROPERTY() bool bSetUseDefault=false;
	UPROPERTY() bool bUseDefault=false;
	UPROPERTY() bool bSetBaseClass=false;
	UPROPERTY() FString BaseClass;
	UPROPERTY() bool bSetEnumType=false;
	UPROPERTY() FString EnumTypePath;
	/** Empty clears the override; nonempty requires a full /Script enum path. */
	UPROPERTY() bool bSetNativeEnumName=false;
	UPROPERTY() FString NativeEnumName;
};

USTRUCT()
struct FBlackboardKeyReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString KeyName;

	UPROPERTY()
	FString KeyType;

	UPROPERTY()
	FString NewKeyName;

	UPROPERTY() bool bSetCategory=false;
	UPROPERTY() FString Category;
	UPROPERTY() bool bSetDescription=false;
	UPROPERTY() FString Description;
	UPROPERTY() bool bSetInstanceSynced=false;
	UPROPERTY() bool bInstanceSynced=false;
	UPROPERTY() bool bSetTypeSettings=false;
	UPROPERTY() FBlackboardTypeSettings TypeSettings;
	UPROPERTY() bool bSetParent=false;
	UPROPERTY() FString ParentPath;
	UPROPERTY() bool bConfirm=false;
	UPROPERTY() bool bDryRun=false;
	UPROPERTY() bool bSave=false;
};
