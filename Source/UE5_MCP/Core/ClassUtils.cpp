#include "ClassUtils.h"

#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "UObject/SavePackage.h"


UClass* ClassUtils::FindClassByName(const FString& ClassFullName)
{
	// 1. Already loaded?
	UClass* Class = FindObject<UClass>(ANY_PACKAGE, *ClassFullName);
	if (Class)
		return Class;

	// 2. Blueprint-generated class format like /Game/Path/To/Blueprint.Blueprint_C
	FRegexPattern BPPattern(TEXT("^/Game/.+\\..+_C$"));
	FRegexMatcher BPMatcher(BPPattern, ClassFullName);
	if (BPMatcher.FindNext())
	{
		Class = StaticLoadClass(UObject::StaticClass(), nullptr, *ClassFullName);
		UE_LOG(LogTemp, Log, TEXT("Trying to load Blueprint class: %s"), *ClassFullName);
		return Class;
	}

	// 3. C++ class with /Script/Module.Class format
	if (ClassFullName.StartsWith("/Script/"))
	{
		Class = StaticLoadClass(UObject::StaticClass(), nullptr, *ClassFullName);
		UE_LOG(LogTemp, Log, TEXT("Trying to load C++ class: %s"), *ClassFullName);
		return Class;
	}

	// 4. C++ class in ModuleName.ClassName format (prepend /Script/)
	FRegexPattern CppPattern(TEXT("^\\w+\\.\\w+$"));
	FRegexMatcher Matcher(CppPattern, ClassFullName);
	if (Matcher.FindNext())
	{
		Class = StaticLoadClass(UObject::StaticClass(), nullptr, *FString::Printf(TEXT("/Script/%s"), *ClassFullName));
		UE_LOG(LogTemp, Log, TEXT("Trying to load C++ class: /Script/%s"), *ClassFullName);
		return Class;
	}

	// 5. Try adding _C for Blueprint asset path
	int32 LastSlash = -1;
	if (ClassFullName.StartsWith("/Game/") &&
		!ClassFullName.EndsWith("_C") &&
		ClassFullName.FindLastChar('/', LastSlash))
	{
		FString AssetName = ClassFullName.Mid(LastSlash + 1);
		FString BPClassPath = FString::Printf(TEXT("%s.%s_C"), *ClassFullName, *AssetName);
		Class = StaticLoadClass(UObject::StaticClass(), nullptr, *BPClassPath);
		UE_LOG(LogTemp, Log, TEXT("Trying to load Blueprint class: %s"), *BPClassPath);
		return Class;
	}

	return nullptr;
}


FString ClassUtils::CreateBlueprintFromClass(const FString& ParentClassFullName, const FString& BlueprintPath)
{
	UE_LOG(LogTemp, Log, TEXT("Creating Blueprint: %s from Parent Class: %s"), *BlueprintPath, *ParentClassFullName);
	
	UClass* ParentClass = FindClassByName(ParentClassFullName);
	
	if (!ParentClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Class not found: %s"), *ParentClassFullName);
		throw std::runtime_error("Class not found");
	}

	auto lastSlashIndex = -1;
	FString AssetName;
	FString PackageName;
	if (BlueprintPath.FindLastChar('/', lastSlashIndex))
	{
		PackageName = BlueprintPath.Left(lastSlashIndex);
		AssetName = BlueprintPath.Mid(lastSlashIndex + 1);
	}

	FString UniquePackageName;
	FString UniqueAssetName;
	
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);

	// Create package
	UPackage* Package = CreatePackage(*UniquePackageName);

	// Create Blueprint
	UBlueprint* NewBP = FKismetEditorUtilities::CreateBlueprint(
		ParentClass,
		Package,
		*UniqueAssetName,
		EBlueprintType::BPTYPE_Normal,
		UBlueprint::StaticClass(),
		UBlueprintGeneratedClass::StaticClass(),
		FName("BlueprintCreation")
	);

	if (!NewBP)
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to create Blueprint: %s/%s"), *UniquePackageName, *UniqueAssetName);
		throw std::runtime_error("Failed to create Blueprint");
	}
	
	// Notify asset registry & mark dirty
	FAssetRegistryModule::AssetCreated(NewBP);
	if (!Package->MarkPackageDirty())
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to mark package dirty: %s/%s"), *UniquePackageName, *UniqueAssetName);
		throw std::runtime_error("Failed to save Blueprint");
	}

	// Save to disk
	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	SaveArgs.Error = GError;
	SaveArgs.bWarnOfLongFilename = true;

	FString PackageFileName = FPackageName::LongPackageNameToFilename(
		UniquePackageName, FPackageName::GetAssetPackageExtension()
	);

	
	if (!UPackage::SavePackage(Package, NewBP, *PackageFileName, SaveArgs))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to save Blueprint: %s"), *PackageFileName);
		throw std::runtime_error("Failed to save Blueprint");
	}

	UE_LOG(LogTemp, Log, TEXT("Blueprint created: %s"), *PackageFileName);
	return UniquePackageName;
}

