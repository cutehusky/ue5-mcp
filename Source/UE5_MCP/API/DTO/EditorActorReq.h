#pragma once

#include "CoreMinimal.h"
#include "EditorActorReq.generated.h"

USTRUCT()
struct FEditorActorReq
{
	GENERATED_BODY()

	UPROPERTY()
	FString ActorPath;

	UPROPERTY()
	FString ActorClass;

	UPROPERTY()
	FString AssetPath;

	/** Editor command requested by a route that accepts a single explicit action. */
	UPROPERTY()
	FString Operation;

	UPROPERTY()
	FVector Location = FVector::ZeroVector;

	UPROPERTY()
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY()
	FVector Offset = FVector::ZeroVector;

	UPROPERTY()
	bool bConfirm = false;

	UPROPERTY()
	bool bSelect = true;

	UPROPERTY()
	TArray<FString> ActorPaths;

	UPROPERTY()
	FVector Scale = FVector::OneVector;

	UPROPERTY()
	FString Label;

	UPROPERTY()
	FString FolderPath;

	UPROPERTY()
	FString AttachTo;

	UPROPERTY()
	FString AttachSocket;

	UPROPERTY()
	TMap<FString, FString> Properties;

	UPROPERTY()
	bool bSetLocation = false;

	UPROPERTY()
	bool bSetRotation = false;

	UPROPERTY()
	bool bSetScale = false;

	UPROPERTY()
	bool bSetLabel = false;

	UPROPERTY()
	bool bSetFolderPath = false;

	UPROPERTY()
	bool bSetAttachment = false;
};
