#include "NavigationAreaUtils.h"
#include "UE5_MCP/API/DTO/NavigationAreaReq.h"
#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Factories/BlueprintFactory.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "NavAreas/NavArea.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "Engine/World.h"
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
	struct FSnapshot
	{
		float Cost=0, Entry=0; FColor Color; uint32 Bits=0; TWeakObjectPtr<UClass> Class;
		static FSnapshot Capture(UBlueprint* B)
		{
			auto* A=B->GeneratedClass->GetDefaultObject<UNavArea>();
			return {A->DefaultCost,A->GetFixedAreaEnteringCost(),A->DrawColor,A->SupportedAgents.GetAgentBits(),B->GeneratedClass};
		}
		bool Same(const FSnapshot& Other) const { return Cost==Other.Cost && Entry==Other.Entry && Color==Other.Color && Bits==Other.Bits && Class==Other.Class; }
	};
	TMap<TWeakObjectPtr<UBlueprint>,FSnapshot> Edited;
	FDelegateHandle UndoHook;
	void Refresh(UBlueprint* B)
	{
		if(IsValid(B) && B->ParentClass==UNavArea::StaticClass() && B->GeneratedClass && B->GeneratedClass->ClassGeneratedBy==B)
		{
			UNavigationSystemV1::RequestAreaUnregistering(B->GeneratedClass);
			UNavigationSystemV1::RequestAreaRegistering(B->GeneratedClass);
		}
	}
	void AfterUndoRedo()
	{
		for(auto It=Edited.CreateIterator();It;++It)
		{
			auto* B=It.Key().Get();
			if(!B || B->ParentClass!=UNavArea::StaticClass() || !B->GeneratedClass || !B->GeneratedClass->IsChildOf(UNavArea::StaticClass()) || B->GeneratedClass->ClassGeneratedBy!=B) { It.RemoveCurrent(); continue; }
			const auto Now=FSnapshot::Capture(B);
			if(!Now.Same(It.Value())) { Refresh(B); It.Value()=Now; }
		}
	}
	FString Package(const FString& Path)
	{
		const FString P=FPackageName::ObjectPathToPackageName(Path);
		if(!P.StartsWith(TEXT("/Game/")) || !FPackageName::IsValidLongPackageName(P) || (Path.Contains(TEXT(".")) && Path!=P+TEXT(".")+FPackageName::GetLongPackageAssetName(P))) throw std::runtime_error("AssetPath requires a valid /Game NavArea Blueprint package or matching object path");
		return P;
	}
	UBlueprint* Load(const FString& Path)
	{
		const FString P=Package(Path); const FString ObjectPath=P+TEXT(".")+FPackageName::GetLongPackageAssetName(P);
		auto* B=FindObject<UBlueprint>(nullptr,*ObjectPath);
		if(!IsValid(B))
		{
			if(!FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(ObjectPath)).IsValid()) throw std::runtime_error("Navigation area asset does not exist");
			B=LoadObject<UBlueprint>(nullptr,*ObjectPath);
		}
		if(!B || B->ParentClass!=UNavArea::StaticClass() || !B->GeneratedClass || !B->GeneratedClass->IsChildOf(UNavArea::StaticClass()) || B->GeneratedClass->ClassGeneratedBy!=B) throw std::runtime_error("Select a compiled Blueprint whose direct native parent is NavArea and whose generated class belongs to that Blueprint");
		return B;
	}
	float& Entering(UNavArea* A)
	{
		auto* P=FindFProperty<FFloatProperty>(UNavArea::StaticClass(),TEXT("FixedAreaEnteringCost"));
		if(!P) throw std::runtime_error("Native area entering-cost property unavailable"); return *P->ContainerPtrToValuePtr<float>(A);
	}
	FString Json(UBlueprint* B,UNavArea* A,const FString& Path,bool Changed=false,bool Dry=false,bool Saved=false)
	{
		FString Result; auto J=TJsonWriterFactory<>::Create(&Result); J->WriteObjectStart();
		J->WriteValue(TEXT("asset_path"),B ? B->GetPathName() : Path); J->WriteValue(TEXT("area_class"),B ? B->GeneratedClass->GetPathName() : TEXT(""));
		J->WriteValue(TEXT("changed"),Changed && !Dry); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),B && B->GetOutermost()->IsDirty());
		if(FMath::IsFinite(A->DefaultCost)) J->WriteValue(TEXT("default_cost"),A->DefaultCost); else J->WriteNull(TEXT("default_cost"));
		if(FMath::IsFinite(Entering(A))) J->WriteValue(TEXT("entering_cost"),Entering(A)); else J->WriteNull(TEXT("entering_cost"));
		J->WriteArrayStart(TEXT("draw_color")); for(uint8 V:{A->DrawColor.R,A->DrawColor.G,A->DrawColor.B,A->DrawColor.A}) J->WriteValue(int32(V)); J->WriteArrayEnd();
		J->WriteValue(TEXT("supported_agent_bits"),int64(A->SupportedAgents.GetAgentBits())); J->WriteArrayStart(TEXT("supported_agent_indices")); for(int32 I=0;I<16;++I) if(A->IsSupportingAgent(I)) J->WriteValue(I); J->WriteArrayEnd();
		J->WriteValue(TEXT("area_flags_read_only"),int32(A->GetAreaFlags()));
		J->WriteArrayStart(TEXT("navigation_data_registration")); int32 Count=0;
		auto* W=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		auto* S=W ? Cast<UNavigationSystemV1>(W->GetNavigationSystem()) : nullptr;
		if(B && S) for(ANavigationData* D:S->NavDataSet) if(IsValid(D))
		{
			if(++Count>256) continue; const int32 Id=D->GetAreaID(B->GeneratedClass);
			J->WriteObjectStart(); J->WriteValue(TEXT("nav_data_path"),D->GetPathName()); J->WriteValue(TEXT("area_id"),Id); J->WriteValue(TEXT("registered"),Id!=INDEX_NONE); J->WriteObjectEnd();
		}
		J->WriteArrayEnd(); J->WriteValue(TEXT("registration_row_count"),Count); J->WriteValue(TEXT("registration_rows_truncated"),Count>256);
		J->WriteObjectStart(TEXT("validation")); J->WriteValue(TEXT("valid"),(!B || B->Status!=BS_Error) && FMath::IsFinite(A->DefaultCost) && A->DefaultCost>=0 && A->DefaultCost<=1.e6 && FMath::IsFinite(Entering(A)) && Entering(A)>=0 && Entering(A)<=1.e6);
		J->WriteValue(TEXT("scope"),TEXT("Direct-parent NavArea Blueprint, compile status and finite bounded costs; native registration updates live systems, but region changes may require navmesh generation")); J->WriteObjectEnd();
		J->WriteObjectEnd(); J->Close(); return Result;
	}
}

void NavigationAreaUtils::Shutdown()
{
	if(UndoHook.IsValid()) { FEditorDelegates::PostUndoRedo.Remove(UndoHook); UndoHook.Reset(); } Edited.Reset();
}

FString NavigationAreaUtils::Inspect(const FString& Path)
{
	auto* B=Load(Path); return Json(B,B->GeneratedClass->GetDefaultObject<UNavArea>(),Path);
}

FString NavigationAreaUtils::Control(const FNavigationAreaReq& R)
{
	if(!GEditor || GEditor->PlayWorld || GEditor->bIsSimulatingInEditor) throw std::runtime_error("Stop PIE/simulation before editing navigation area assets");
	const FString P=Package(R.AssetPath); const FString Op=R.Operation.ToLower(); const bool Create=Op==TEXT("create");
	if(!Create && Op!=TEXT("update")) throw std::runtime_error("Navigation area operation must be create or update");
	auto* Assets=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>(); auto* Existing=FindPackage(nullptr,*P);
	if(Create && (Assets->DoesAssetExist(P) || (Existing && !UPackage::IsEmptyPackage(Existing)))) throw std::runtime_error("Navigation area destination already exists");
	auto* B=Create ? nullptr : Load(R.AssetPath); auto* A=B ? B->GeneratedClass->GetDefaultObject<UNavArea>() : GetMutableDefault<UNavArea>();
	for(float V:{R.DefaultCost,R.EnteringCost}) if(!FMath::IsFinite(V) || (V!=-1 && (V<0 || V>1.e6))) throw std::runtime_error("Area costs require -1 (preserve) or finite values in [0,1e6]");
	const float Cost=R.DefaultCost==-1 ? A->DefaultCost : R.DefaultCost; const float Entry=R.EnteringCost==-1 ? Entering(A) : R.EnteringCost;
	if(!FMath::IsFinite(Cost) || Cost<0 || Cost>1.e6 || !FMath::IsFinite(Entry) || Entry<0 || Entry>1.e6) throw std::runtime_error("Existing area costs need valid replacements");
	FColor Color=A->DrawColor;
	if(!R.DrawColor.IsEmpty()) { if(R.DrawColor.Num()!=4) throw std::runtime_error("DrawColor requires exactly four RGBA bytes"); for(int32 C:R.DrawColor) if(C<0 || C>255) throw std::runtime_error("DrawColor channels require [0,255]"); Color=FColor(R.DrawColor[0],R.DrawColor[1],R.DrawColor[2],R.DrawColor[3]); }
	uint32 Bits=A->SupportedAgents.GetAgentBits();
	if(R.bSetSupportedAgents) { Bits=0; for(int32 I:R.SupportedAgentIndices) { if(I<0 || I>15 || (Bits & (1u<<I))) throw std::runtime_error("SupportedAgentIndices requires unique indices in [0,15]"); Bits|=1u<<I; } }
	else if(!R.SupportedAgentIndices.IsEmpty()) throw std::runtime_error("bSetSupportedAgents=true is required to replace agent selections");
	const bool Changed=Create || A->DefaultCost!=Cost || Entering(A)!=Entry || A->DrawColor!=Color || A->SupportedAgents.GetAgentBits()!=Bits;
	if(!R.bDryRun && Changed)
	{
		for(auto It=Edited.CreateIterator();It;++It) if(!It.Key().IsValid()) It.RemoveCurrent();
		FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","NavigationArea","Edit Navigation Area"));
		if(Create)
		{
			auto* Factory=NewObject<UBlueprintFactory>(); Factory->ParentClass=UNavArea::StaticClass();
			B=Cast<UBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get().CreateAsset(FPackageName::GetLongPackageAssetName(P),FPackageName::GetLongPackagePath(P),UBlueprint::StaticClass(),Factory));
			if(!B || !B->GeneratedClass) throw std::runtime_error("Native navigation area Blueprint creation failed"); A=B->GeneratedClass->GetDefaultObject<UNavArea>();
		}
		B->SetFlags(RF_Transactional); B->Modify(); A->SetFlags(RF_Transactional); A->Modify(); A->PreEditChange(nullptr);
		A->DefaultCost=Cost; Entering(A)=Entry; A->DrawColor=Color; A->SupportedAgents=FNavAgentSelector(Bits); A->SupportedAgents.MarkInitialized();
		A->PostEditChange(); FBlueprintEditorUtils::MarkBlueprintAsModified(B); FKismetEditorUtilities::CompileBlueprint(B);
		if(B->Status==BS_Error) throw std::runtime_error("Navigation area changed but Blueprint compilation failed");
		Refresh(B); B->MarkPackageDirty(); Edited.Add(B,FSnapshot::Capture(B));
		if(!UndoHook.IsValid()) UndoHook=FEditorDelegates::PostUndoRedo.AddStatic(&AfterUndoRedo);
		A=B->GeneratedClass->GetDefaultObject<UNavArea>();
	}
	bool Saved=false;
	if(!R.bDryRun && R.bSave && B && B->GetOutermost()->IsDirty()) { if(!Assets->SaveAsset(B->GetPathName(),true)) throw std::runtime_error("Navigation area changed but saving failed"); Saved=true; }
	return Json(B,A,R.AssetPath,Changed,R.bDryRun,Saved);
}
