#pragma once
#include <stdexcept>

// Utility functions for manipulating Classes
class ClassUtils
{
public:
	static UClass* FindClassByName(const FString& ClassFullName);
	static FString CreateBlueprintFromClass(const FString& ParentClassFullName, const FString& BlueprintPath);
	static FString CreateWidgetBlueprint(const FString& ParentClassFullName, const FString& BlueprintPath);
	static FString CreateAnimationSequence(const FString& BlueprintPath, const FString& SkeletonPath, const FString& PreviewMeshPath);
	static FString CreateDataAsset(const FString& AssetPath, const FString& AssetClass);
	static FString CreateBehaviorTree(const FString& AssetPath);
	static FString CreateBlackboard(const FString& AssetPath);
	static FString CreateLevelSequence(const FString& AssetPath);
};
