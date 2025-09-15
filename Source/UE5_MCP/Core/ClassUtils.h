#pragma once

// Utility functions for manipulating Classes
class ClassUtils
{
public:
	static UClass* FindClassByName(const FString& ClassFullName);
	static FString CreateBlueprintFromClass(const FString& ParentClassFullName, const FString& BlueprintPath);
};
