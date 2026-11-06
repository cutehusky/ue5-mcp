#pragma once

#include "CoreMinimal.h"
#include "WidgetOperationReq.generated.h"

USTRUCT()
struct FWidgetOperationReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString WidgetName;

	UPROPERTY()
	FString WidgetClass;

	UPROPERTY()
	FString ParentName;

	UPROPERTY()
	FString NewParentName;

	UPROPERTY()
	TMap<FString, FString> Properties;
};
