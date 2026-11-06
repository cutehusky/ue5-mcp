#pragma once

#include "CoreMinimal.h"
#include "ControlRigGraphReq.generated.h"

USTRUCT()
struct FControlRigGraphReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString AssetPath;

	UPROPERTY()
	FString GraphPath;

	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FString NodeName;

	UPROPERTY()
	TArray<FString> NodeNames;

	UPROPERTY()
	FString UnitStructPath;

	UPROPERTY()
	FString TemplateNotation;

	UPROPERTY()
	FString InjectionInputPinName;

	UPROPERTY()
	FString InjectionOutputPinName;

	UPROPERTY()
	FString CommentText;

	UPROPERTY()
	FString CPPType;

	UPROPERTY()
	FString CPPTypeObjectPath;

	UPROPERTY()
	FString ArrayOperation;

	UPROPERTY()
	int32 ArrayIndex = INDEX_NONE;

	UPROPERTY()
	int32 ArraySize = INDEX_NONE;

	UPROPERTY()
	FString CustomWidgetName;

	UPROPERTY()
	FString VariableName;

	UPROPERTY()
	FString NewVariableName;

	UPROPERTY()
	FString FunctionName;

	UPROPERTY()
	FString EntryName;

	UPROPERTY()
	FString ExposedPinName;

	UPROPERTY()
	FString PinDirection;

	UPROPERTY()
	bool bFunctionMutable = false;

	UPROPERTY()
	FString MethodName = TEXT("Execute");

	UPROPERTY()
	FString PinPath;

	UPROPERTY()
	FString PinDisplayName;

	UPROPERTY()
	bool bPinExpanded = false;

	UPROPERTY()
	bool bPinWatched = false;

	UPROPERTY()
	FString DefaultValue;

	UPROPERTY()
	FString SourcePinPath;

	UPROPERTY()
	FString TargetPinPath;

	UPROPERTY()
	FVector2D Position = FVector2D::ZeroVector;

	UPROPERTY()
	FVector2D NodeSize = FVector2D(400.f, 300.f);

	UPROPERTY()
	bool bIsGetter = true;

	UPROPERTY()
	bool bInjectedAsInput = true;

	UPROPERTY()
	bool bRerouteConstant = false;

	UPROPERTY()
	bool bRerouteAsInput = true;

	UPROPERTY()
	bool bDryRun = false;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSave = false;
};
