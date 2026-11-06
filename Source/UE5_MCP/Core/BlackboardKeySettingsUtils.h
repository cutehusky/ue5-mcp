#pragma once
#include "CoreMinimal.h"
#include "UObject/StrongObjectPtr.h"
class UBlackboardKeyType;
struct FBlackboardTypeSettings;
namespace BlackboardKeySettingsUtils
{
	TStrongObjectPtr<UBlackboardKeyType> Prepare(UBlackboardKeyType* Source,const FBlackboardTypeSettings& R);
	void Copy(UBlackboardKeyType* Target,UBlackboardKeyType* Source);
	FString Snapshot(UBlackboardKeyType* Key);
	FString Compatibility(UBlackboardKeyType* Key);
	TArray<FString> Validate(UBlackboardKeyType* Key);
}
