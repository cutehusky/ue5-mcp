#include "NavigationFilterUtils.h"
#include "UE5_MCP/API/DTO/NavigationFilterReq.h"
#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Factories/BlueprintFactory.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "NavFilters/NavigationQueryFilter.h"
#include "NavAreas/NavArea.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"
#include "UObject/Package.h"
#include <stdexcept>

namespace
{
	FString Package(const FString& Path)
	{
		const FString P=FPackageName::ObjectPathToPackageName(Path);
		if(!P.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(P)) throw std::runtime_error("AssetPath requires a valid /Game navigation filter Blueprint package or object path");
		if(Path.Contains(TEXT(".")) && Path!=P+TEXT(".")+FPackageName::GetLongPackageAssetName(P)) throw std::runtime_error("Navigation filter object name must match its package asset name");
		return P;
	}
	UBlueprint* Load(const FString& Path)
	{
		const FString P=Package(Path); const FString ObjectPath=P+TEXT(".")+FPackageName::GetLongPackageAssetName(P);
		auto* B=FindObject<UBlueprint>(nullptr,*ObjectPath);
		if(!IsValid(B))
		{
			// Registry reads work during PIE and do not create failed-load packages.
			if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(ObjectPath)).IsValid()) throw std::runtime_error("Navigation filter asset does not exist");
			B=LoadObject<UBlueprint>(nullptr,*ObjectPath);
		}
		if(!B || B->ParentClass!=UNavigationQueryFilter::StaticClass() || !B->GeneratedClass || !B->GeneratedClass->IsChildOf(UNavigationQueryFilter::StaticClass())) throw std::runtime_error("Select a compiled Blueprint whose direct native parent is NavigationQueryFilter; inherited/custom native filter adapters are separate");
		return B;
	}
	UNavigationQueryFilter* Defaults(UBlueprint* B) { return B->GeneratedClass->GetDefaultObject<UNavigationQueryFilter>(); }
	template<typename T> T* Prop(const TCHAR* Name)
	{
		auto* P=FindFProperty<T>(UNavigationQueryFilter::StaticClass(),Name);
		if(!P) throw std::runtime_error("Native navigation filter property unavailable"); return P;
	}
	TArray<FNavigationFilterArea>& Areas(UNavigationQueryFilter* F) { return *Prop<FArrayProperty>(TEXT("Areas"))->ContainerPtrToValuePtr<TArray<FNavigationFilterArea>>(F); }
	FNavigationFilterFlags& Flags(UNavigationQueryFilter* F,const TCHAR* Name) { return *Prop<FStructProperty>(Name)->ContainerPtrToValuePtr<FNavigationFilterFlags>(F); }
	bool Equal(const TArray<FNavigationFilterArea>& A,const TArray<FNavigationFilterArea>& B)
	{
		if(A.Num()!=B.Num()) return false;
		for(int32 I=0;I<A.Num();++I) { const auto& X=A[I]; const auto& Y=B[I]; if(X.AreaClass!=Y.AreaClass || X.bIsExcluded!=Y.bIsExcluded || X.bOverrideTravelCost!=Y.bOverrideTravelCost || X.bOverrideEnteringCost!=Y.bOverrideEnteringCost || X.TravelCostOverride!=Y.TravelCostOverride || X.EnteringCostOverride!=Y.EnteringCostOverride) return false; }
		return true;
	}
	TArray<FString> Validate(const TArray<FNavigationFilterArea>& Rows)
	{
		TArray<FString> Errors; TSet<UClass*> Seen;
		if(Rows.Num()>64) Errors.Add(TEXT("Area override count exceeds 64"));
		for(const auto& A:Rows)
		{
			auto* C=A.AreaClass.Get();
			if(!IsValid(C) || !C->IsChildOf(UNavArea::StaticClass()) || C->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists) || Seen.Contains(C)) Errors.Add(TEXT("Area classes must be unique, concrete compatible NavArea classes"));
			Seen.Add(C);
			if(!FMath::IsFinite(A.TravelCostOverride) || A.TravelCostOverride<1 || A.TravelCostOverride>1.e6 || !FMath::IsFinite(A.EnteringCostOverride) || A.EnteringCostOverride<0 || A.EnteringCostOverride>1.e6) Errors.Add(TEXT("Area costs are nonfinite or outside supported bounds"));
		}
		return Errors;
	}
	FString Json(UBlueprint* B,UNavigationQueryFilter* F,const FString& Path,bool Changed=false,bool Dry=false,bool Saved=false)
	{
		FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart();
		J->WriteValue(TEXT("asset_path"),B ? B->GetPathName() : Path); J->WriteValue(TEXT("filter_class"),B ? B->GeneratedClass->GetPathName() : TEXT(""));
		J->WriteValue(TEXT("changed"),Changed && !Dry); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),B && B->GetOutermost()->IsDirty());
		J->WriteValue(TEXT("include_flags"),int32(Flags(F,TEXT("IncludeFlags")).Packed)); J->WriteValue(TEXT("exclude_flags"),int32(Flags(F,TEXT("ExcludeFlags")).Packed));
		J->WriteArrayStart(TEXT("areas")); for(const auto& A:Areas(F)) { J->WriteObjectStart(); J->WriteValue(TEXT("area_class"),A.AreaClass ? A.AreaClass->GetPathName() : TEXT("")); J->WriteValue(TEXT("excluded"),bool(A.bIsExcluded)); J->WriteValue(TEXT("override_travel_cost"),bool(A.bOverrideTravelCost)); J->WriteValue(TEXT("travel_cost"),A.TravelCostOverride); J->WriteValue(TEXT("override_entering_cost"),bool(A.bOverrideEnteringCost)); J->WriteValue(TEXT("entering_cost"),A.EnteringCostOverride); J->WriteObjectEnd(); } J->WriteArrayEnd();
		auto Errors=Validate(Areas(F)); if(B && B->Status==BS_Error) Errors.Add(TEXT("Blueprint compilation has errors"));
		J->WriteObjectStart(TEXT("validation")); J->WriteValue(TEXT("valid"),Errors.IsEmpty()); J->WriteArrayStart(TEXT("errors")); for(const auto& Error:Errors) J->WriteValue(Error); J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Direct-parent native filter Blueprint, area class uniqueness/compatibility, bounded finite costs and compile status; query behavior depends on area IDs registered in the selected navigation data")); J->WriteObjectEnd();
		J->WriteObjectEnd(); J->Close(); return Result;
	}
}

FString NavigationFilterUtils::Inspect(const FString& AssetPath)
{
	Package(AssetPath); auto* B=Load(AssetPath); return Json(B,Defaults(B),AssetPath);
}

FString NavigationFilterUtils::Control(const FNavigationFilterReq& R)
{
	if(!GEditor || GEditor->PlayWorld || GEditor->bIsSimulatingInEditor) throw std::runtime_error("Stop PIE/simulation before editing navigation filter assets");
	const FString P=Package(R.AssetPath); const FString Op=R.Operation.ToLower(); const bool Create=Op==TEXT("create");
	if(!Create && Op!=TEXT("update")) throw std::runtime_error("Navigation filter operation must be create or update");
	auto* Assets=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>();
	auto* ExistingPackage=FindPackage(nullptr,*P);
	if(Create && (Assets->DoesAssetExist(P) || (ExistingPackage && !UPackage::IsEmptyPackage(ExistingPackage)))) throw std::runtime_error("Navigation filter destination already exists");
	auto* B=Create ? nullptr : Load(R.AssetPath); auto* F=B ? Defaults(B) : GetMutableDefault<UNavigationQueryFilter>();
	if(R.IncludeFlags < -1 || R.IncludeFlags>65535 || R.ExcludeFlags < -1 || R.ExcludeFlags>65535 || R.Areas.Num()>64) throw std::runtime_error("Flag masks require -1 (preserve) or [0,65535]; at most 64 area overrides");
	if(!R.bSetAreas && !R.Areas.IsEmpty()) throw std::runtime_error("bSetAreas=true is required to replace area overrides");
	TArray<FNavigationFilterArea> Next=R.bSetAreas ? TArray<FNavigationFilterArea>() : Areas(F); TSet<UClass*> Seen;
	for(const auto& A:R.Areas)
	{
		auto* Class=LoadObject<UClass>(nullptr,*A.AreaClass);
		if(!Class || !Class->IsChildOf(UNavArea::StaticClass()) || Class->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists) || Seen.Contains(Class)) throw std::runtime_error("Area overrides require unique concrete compatible NavArea classes");
		if(!FMath::IsFinite(A.TravelCost) || A.TravelCost<1 || A.TravelCost>1.e6 || !FMath::IsFinite(A.EnteringCost) || A.EnteringCost<0 || A.EnteringCost>1.e6) throw std::runtime_error("TravelCost requires [1,1e6] and EnteringCost [0,1e6]");
		Seen.Add(Class); FNavigationFilterArea V; V.AreaClass=Class; V.bIsExcluded=A.bExcluded; V.bOverrideTravelCost=A.bOverrideTravelCost; V.TravelCostOverride=A.TravelCost; V.bOverrideEnteringCost=A.bOverrideEnteringCost; V.EnteringCostOverride=A.EnteringCost; Next.Add(V);
	}
	const auto Errors=Validate(Next); if(!Errors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(Errors,TEXT("; "))));
	const uint16 Include=R.IncludeFlags==-1 ? Flags(F,TEXT("IncludeFlags")).Packed : uint16(R.IncludeFlags);
	const uint16 Exclude=R.ExcludeFlags==-1 ? Flags(F,TEXT("ExcludeFlags")).Packed : uint16(R.ExcludeFlags);
	const bool Changed=Create || !Equal(Areas(F),Next) || Flags(F,TEXT("IncludeFlags")).Packed!=Include || Flags(F,TEXT("ExcludeFlags")).Packed!=Exclude;
	if(!R.bDryRun && Changed)
	{
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","NavigationFilter","Edit Navigation Query Filter"));
		if(Create)
		{
			auto* Factory=NewObject<UBlueprintFactory>(); Factory->ParentClass=UNavigationQueryFilter::StaticClass();
			B=Cast<UBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get().CreateAsset(FPackageName::GetLongPackageAssetName(P),FPackageName::GetLongPackagePath(P),UBlueprint::StaticClass(),Factory));
			if(!B || !B->GeneratedClass) throw std::runtime_error("Native navigation filter Blueprint creation failed"); F=Defaults(B);
		}
		B->SetFlags(RF_Transactional); B->Modify(); F->SetFlags(RF_Transactional); F->Modify();
		F->PreEditChange(nullptr); Areas(F)=Next; Flags(F,TEXT("IncludeFlags")).Packed=Include; Flags(F,TEXT("ExcludeFlags")).Packed=Exclude;
		F->PostEditChange(); // Native filter invalidates cached filters in every live navigation system.
		FBlueprintEditorUtils::MarkBlueprintAsModified(B); FKismetEditorUtilities::CompileBlueprint(B);
		if(B->Status==BS_Error) throw std::runtime_error("Navigation filter changed but Blueprint compilation failed");
		F=Defaults(B); F->PostEditChange(); B->MarkPackageDirty();
	}
	bool Saved=false;
	if(!R.bDryRun && R.bSave && B && B->GetOutermost()->IsDirty()) { if(!Assets->SaveAsset(B->GetPathName(),true)) throw std::runtime_error("Navigation filter changed but saving failed"); Saved=true; }
	return Json(B,F,R.AssetPath,Changed,R.bDryRun,Saved);
}
