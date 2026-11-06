#include "ClassUtils.h"

#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "UObject/SavePackage.h"
#include "WidgetBlueprintFactory.h"
#include "WidgetBlueprint.h"
#include "Blueprint/UserWidget.h"
#include "Factories/AnimSequenceFactory.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMesh.h"
#include "Factories/DataAssetFactory.h"
#include "Engine/DataAsset.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTreeFactory.h"
#include "BlackboardDataFactory.h"
#include "LevelSequence.h"
#include "MovieScene.h"


UClass* ClassUtils::FindClassByName(const FString& ClassFullName)
{
	// 1. Already loaded?
	UClass* Class = FindFirstObject<UClass>(*ClassFullName);
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

	// 3. C++ class with /Script/ModuleName.ClassName format
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

FString ClassUtils::CreateWidgetBlueprint(const FString& ParentClassFullName, const FString& BlueprintPath)
{
	UClass* ParentClass = FindClassByName(ParentClassFullName);
	if (!ParentClass || !ParentClass->IsChildOf(UUserWidget::StaticClass()))
		throw std::runtime_error("Widget Blueprint parent must derive from UUserWidget");

	int32 LastSlashIndex = INDEX_NONE;
	if (!BlueprintPath.FindLastChar('/', LastSlashIndex) || LastSlashIndex <= 0)
		throw std::runtime_error("Widget Blueprint path must include a package path");

	const FString PackageName = BlueprintPath.Left(LastSlashIndex);
	const FString AssetName = BlueprintPath.Mid(LastSlashIndex + 1);
	FString UniquePackageName;
	FString UniqueAssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);

	UWidgetBlueprintFactory* Factory = NewObject<UWidgetBlueprintFactory>();
	Factory->ParentClass = ParentClass;
	Factory->BlueprintType = BPTYPE_Normal;
	UObject* Created = AssetToolsModule.Get().CreateAsset(
		UniqueAssetName,
		FPackageName::GetLongPackagePath(UniquePackageName),
		UWidgetBlueprint::StaticClass(),
		Factory);
	UWidgetBlueprint* WidgetBlueprint = Cast<UWidgetBlueprint>(Created);
	if (!WidgetBlueprint)
		throw std::runtime_error("Failed to create Widget Blueprint");

	WidgetBlueprint->MarkPackageDirty();
	return WidgetBlueprint->GetOutermost()->GetName();
}

FString ClassUtils::CreateAnimationSequence(const FString& BlueprintPath, const FString& SkeletonPath, const FString& PreviewMeshPath)
{
	USkeleton* Skeleton = Cast<USkeleton>(StaticLoadObject(USkeleton::StaticClass(), nullptr, *SkeletonPath));
	if (!Skeleton)
		throw std::runtime_error("skeleton_path must identify a valid USkeleton asset");

	USkeletalMesh* PreviewMesh = nullptr;
	if (!PreviewMeshPath.IsEmpty())
	{
		PreviewMesh = Cast<USkeletalMesh>(StaticLoadObject(USkeletalMesh::StaticClass(), nullptr, *PreviewMeshPath));
		if (!PreviewMesh)
			throw std::runtime_error("preview_mesh_path must identify a valid USkeletalMesh asset");
	}

	int32 LastSlashIndex = INDEX_NONE;
	if (!BlueprintPath.FindLastChar('/', LastSlashIndex) || LastSlashIndex <= 0)
		throw std::runtime_error("animation asset path must include a package path");

	const FString PackageName = BlueprintPath.Left(LastSlashIndex);
	const FString AssetName = BlueprintPath.Mid(LastSlashIndex + 1);
	FString UniquePackageName;
	FString UniqueAssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);

	UAnimSequenceFactory* Factory = NewObject<UAnimSequenceFactory>();
	Factory->TargetSkeleton = Skeleton;
	Factory->PreviewSkeletalMesh = PreviewMesh;
	UObject* Created = AssetToolsModule.Get().CreateAsset(
		UniqueAssetName,
		FPackageName::GetLongPackagePath(UniquePackageName),
		UAnimSequence::StaticClass(),
		Factory);
	UAnimSequence* Animation = Cast<UAnimSequence>(Created);
	if (!Animation)
		throw std::runtime_error("Failed to create Animation Sequence");
	Animation->MarkPackageDirty();
	return Animation->GetOutermost()->GetName();
}

FString ClassUtils::CreateDataAsset(const FString& AssetPath, const FString& AssetClass)
{
	UClass* DataClass = FindClassByName(AssetClass);
	if (!DataClass || !DataClass->IsChildOf(UDataAsset::StaticClass()) || DataClass->HasAnyClassFlags(CLASS_Abstract))
		throw std::runtime_error("asset_class must be a non-abstract UDataAsset-derived class");

	int32 LastSlashIndex = INDEX_NONE;
	if (!AssetPath.FindLastChar('/', LastSlashIndex) || LastSlashIndex <= 0)
		throw std::runtime_error("data asset path must include a package path");

	const FString PackageName = AssetPath.Left(LastSlashIndex);
	const FString AssetName = AssetPath.Mid(LastSlashIndex + 1);
	FString UniquePackageName;
	FString UniqueAssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);

	UDataAssetFactory* Factory = NewObject<UDataAssetFactory>();
	Factory->DataAssetClass = DataClass;
	UObject* Created = AssetToolsModule.Get().CreateAsset(
		UniqueAssetName,
		FPackageName::GetLongPackagePath(UniquePackageName),
		UDataAsset::StaticClass(),
		Factory);
	UDataAsset* DataAsset = Cast<UDataAsset>(Created);
	if (!DataAsset)
		throw std::runtime_error("Failed to create Data Asset");
	DataAsset->MarkPackageDirty();
	return DataAsset->GetOutermost()->GetName();
}

FString ClassUtils::CreateBehaviorTree(const FString& AssetPath)
{
	int32 LastSlashIndex = INDEX_NONE;
	if (!AssetPath.FindLastChar('/', LastSlashIndex) || LastSlashIndex <= 0)
		throw std::runtime_error("behavior tree path must include a package path");
	const FString PackageName = AssetPath.Left(LastSlashIndex);
	const FString AssetName = AssetPath.Mid(LastSlashIndex + 1);
	FString UniquePackageName;
	FString UniqueAssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);
	UBehaviorTreeFactory* Factory = NewObject<UBehaviorTreeFactory>();
	UObject* Created = AssetToolsModule.Get().CreateAsset(UniqueAssetName, FPackageName::GetLongPackagePath(UniquePackageName), UBehaviorTree::StaticClass(), Factory);
	UBehaviorTree* BehaviorTree = Cast<UBehaviorTree>(Created);
	if (!BehaviorTree) throw std::runtime_error("Failed to create Behavior Tree");
	BehaviorTree->MarkPackageDirty();
	return BehaviorTree->GetOutermost()->GetName();
}

FString ClassUtils::CreateBlackboard(const FString& AssetPath)
{
	int32 LastSlashIndex = INDEX_NONE;
	if (!AssetPath.FindLastChar('/', LastSlashIndex) || LastSlashIndex <= 0)
		throw std::runtime_error("blackboard path must include a package path");
	const FString PackageName = AssetPath.Left(LastSlashIndex);
	const FString AssetName = AssetPath.Mid(LastSlashIndex + 1);
	FString UniquePackageName;
	FString UniqueAssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);
	UBlackboardDataFactory* Factory = NewObject<UBlackboardDataFactory>();
	UObject* Created = AssetToolsModule.Get().CreateAsset(UniqueAssetName, FPackageName::GetLongPackagePath(UniquePackageName), UBlackboardData::StaticClass(), Factory);
	UBlackboardData* Blackboard = Cast<UBlackboardData>(Created);
	if (!Blackboard) throw std::runtime_error("Failed to create Blackboard");
	Blackboard->MarkPackageDirty();
	return Blackboard->GetOutermost()->GetName();
}

FString ClassUtils::CreateLevelSequence(const FString& AssetPath)
{
	int32 LastSlashIndex = INDEX_NONE;
	if (!AssetPath.FindLastChar('/', LastSlashIndex) || LastSlashIndex <= 0)
		throw std::runtime_error("level sequence path must include a package path");
	const FString PackageName = AssetPath.Left(LastSlashIndex);
	const FString AssetName = AssetPath.Mid(LastSlashIndex + 1);
	FString UniquePackageName;
	FString UniqueAssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	AssetToolsModule.Get().CreateUniqueAssetName(PackageName + "/" + AssetName, TEXT(""), UniquePackageName, UniqueAssetName);
	UPackage* Package = CreatePackage(*UniquePackageName);
	ULevelSequence* Sequence = NewObject<ULevelSequence>(Package, ULevelSequence::StaticClass(), *UniqueAssetName, RF_Public | RF_Standalone | RF_Transactional);
	if (!Sequence) throw std::runtime_error("Failed to create Level Sequence");
	Sequence->Initialize();
	FAssetRegistryModule::AssetCreated(Sequence);
	Package->MarkPackageDirty();
	return Sequence->GetOutermost()->GetName();
}

