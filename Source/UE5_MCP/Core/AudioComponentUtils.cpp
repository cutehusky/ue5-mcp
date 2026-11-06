#include "AudioComponentUtils.h"
#include "UE5_MCP/API/DTO/AudioComponentSettingsReq.h"
#include "Components/AudioComponent.h"
#include "Engine/Blueprint.h"
#include "Engine/SCS_Node.h"
#include "Engine/InheritableComponentHandler.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "FileHelpers.h"
#include "Misc/PackageName.h"
#include "Editor.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundConcurrency.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"
#include "UObject/PropertyAccessUtil.h"
#include <stdexcept>
namespace
{
	const TMap<FString, FVector2f> Numeric = {
		{TEXT("VolumeMultiplier"), {0,4}}, {TEXT("PitchMultiplier"), {.125f,4}},
		{TEXT("LowPassFilterFrequency"), {0,20000}}, {TEXT("HighPassFilterFrequency"), {0,20000}},
		{TEXT("Priority"), {0,1000}}, {TEXT("SubtitlePriority"), {0,1000000}}};
	const TArray<FString> Booleans = {TEXT("bAutoActivate"), TEXT("bAutoDestroy"), TEXT("bStopWhenOwnerDestroyed"),
		TEXT("bAllowSpatialization"), TEXT("bIsUISound"), TEXT("bEnableLowPassFilter"), TEXT("bEnableHighPassFilter"),
		TEXT("bOverridePriority"), TEXT("bOverrideSubtitlePriority"), TEXT("bCanPlayMultipleInstances")};
	const TMap<FString,UClass*> ReferenceClasses = {{TEXT("Sound"), USoundBase::StaticClass()},
		{TEXT("AttenuationSettings"), USoundAttenuation::StaticClass()}, {TEXT("SoundClassOverride"), USoundClass::StaticClass()}};
	struct FTarget
	{
		UBlueprint* Blueprint = nullptr;
		USCS_Node* Node = nullptr;
		UAudioComponent* Component = nullptr;
		AActor* Actor = nullptr;
		bool bInherited = false;
		bool bNativeSubobject = false;
		UAudioComponent* OwnOverride() const
		{
			auto* H = bInherited ? Blueprint->GetInheritableComponentHandler(false) : nullptr;
			return H ? Cast<UAudioComponent>(H->GetOverridenComponentTemplate(FComponentKey(Node))) : nullptr;
		}
		UPackage* Package() const { return Blueprint ? Blueprint->GetPackage() : Actor->GetPackage(); }
	};
	FTarget Target(const FString& Path, const FString& Name, const FString& ActorPath)
	{
		if (Path.IsEmpty() == ActorPath.IsEmpty() || Name.IsEmpty()) throw std::runtime_error("Provide exactly one of BpPath/ActorPath, plus ComponentName");
		if (!ActorPath.IsEmpty())
		{
			auto* Actor = FindObject<AActor>(nullptr, *ActorPath);
			if (!IsValid(Actor) || Actor->IsTemplate() || !GEditor || Actor->GetWorld() != GEditor->GetEditorWorldContext().World()) throw std::runtime_error("ActorPath must identify an actor in the current editor world");
			TInlineComponentArray<UActorComponent*> Components(Actor);
			for (auto* C : Components) if (C && C->GetName() == Name)
			{
				auto* Audio = Cast<UAudioComponent>(C);
				if (!IsValid(Audio) || Audio->IsTemplate() || Audio->HasAnyFlags(RF_Transient)) throw std::runtime_error("Component must be a persistent native Audio Component instance");
				FTarget Result; Result.Actor = Actor; Result.Component = Audio; return Result;
			}
			throw std::runtime_error("Audio component instance not found on the selected actor");
		}
		auto* B = LoadObject<UBlueprint>(nullptr, *Path);
		if (!B || Name.IsEmpty()) throw std::runtime_error("BpPath and ComponentName must identify a Blueprint Audio Component");
		if (B->SimpleConstructionScript) for (auto* N : B->SimpleConstructionScript->GetAllNodes()) if (N && N->GetVariableName().ToString() == Name)
		{
			auto* A = Cast<UAudioComponent>(N->ComponentTemplate);
			if (!A) throw std::runtime_error("Selected component is not a native Audio Component");
			return {B,N,A};
		}
		for (UClass* Class = B->ParentClass.Get(); Class; Class = Class->GetSuperClass())
		{
			auto* Parent = Cast<UBlueprint>(Class->ClassGeneratedBy);
			if (!Parent || !Parent->SimpleConstructionScript) continue;
			for (auto* N : Parent->SimpleConstructionScript->GetAllNodes()) if (N && N->GetVariableName().ToString() == Name)
			{
				auto* Generated = Cast<UBlueprintGeneratedClass>(B->GeneratedClass);
				if (!Generated) throw std::runtime_error("Compile the child Blueprint before inspecting inherited components");
				auto* A = Cast<UAudioComponent>(N->GetActualComponentTemplate(Generated));
				if (!A) throw std::runtime_error("Inherited component is not a native Audio Component");
				FTarget Result; Result.Blueprint = B; Result.Node = N; Result.Component = A; Result.bInherited = true; return Result;
			}
		}
		auto* CDO = B->GeneratedClass ? Cast<AActor>(B->GeneratedClass->GetDefaultObject()) : nullptr;
		if (CDO)
		{
			TInlineComponentArray<UActorComponent*> Components(CDO);
			for (auto* C : Components) if (C && C->GetName() == Name)
			{
				auto* A = Cast<UAudioComponent>(C);
				if (!A || !A->HasAnyFlags(RF_DefaultSubObject) || A->GetOuter() != CDO || A->GetPackage() != B->GetPackage()) throw std::runtime_error("Native Audio Component must be a default subobject owned by this Blueprint's CDO");
				FTarget Result; Result.Blueprint = B; Result.Component = A; Result.bNativeSubobject = true; return Result;
			}
		}
		throw std::runtime_error("Audio Component template not found in the Blueprint's SCS hierarchy or native default subobjects");
	}
	template<typename T> T* Property(const FString& Key)
	{
		auto* P = FindFProperty<T>(UAudioComponent::StaticClass(), FName(*Key));
		if (!P) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Native audio component field unavailable: %s"), *Key)));
		return P;
	}
	FFloatProperty* Float(const FString& Key) { return Property<FFloatProperty>(Key); }
	FBoolProperty* Bool(const FString& Key) { return Property<FBoolProperty>(Key); }
	FObjectPropertyBase* Object(const FString& Key) { return Property<FObjectPropertyBase>(Key); }
	TArray<FProperty*> SupportedFields()
	{
		TArray<FProperty*> Fields;
		for (const auto& Pair : Numeric) Fields.Add(Float(Pair.Key));
		for (const auto& Key : Booleans) Fields.Add(Bool(Key));
		for (const auto& Pair : ReferenceClasses) Fields.Add(Object(Pair.Key));
		Fields.Add(Property<FSetProperty>(TEXT("ConcurrencySet"))); return Fields;
	}
	bool HasNativeSettingsOverride(UAudioComponent* A)
	{
		auto* Parent = Cast<UAudioComponent>(A->GetArchetype());
		if (!Parent) throw std::runtime_error("Native Audio Component parent archetype unavailable");
		for (auto* P : SupportedFields()) if (!P->Identical_InContainer(A, Parent)) return true;
		return false;
	}
	FString Path(UObject* O) { return O ? O->GetPathName() : FString(); }
	TArray<FString> Concurrency(UAudioComponent* A)
	{
		TArray<FString> Result; for (const auto& C : A->ConcurrencySet) if (C) Result.Add(C->GetPathName()); Result.Sort(); return Result;
	}
	void Change(UAudioComponent* A, FProperty* P, bool Propagate, TFunctionRef<void()> Set)
	{
		TArray<UObject*> Inheriting;
		if (Propagate) PropertyAccessUtil::GetArchetypeInstancesInheritingPropertyValue(P, A, Inheriting);
		for (auto* Instance : Inheriting)
		{
			Instance->SetFlags(RF_Transactional); Instance->Modify();
			if (auto* C = Cast<UActorComponent>(Instance)) if (auto* Owner = C->GetOwner()) Owner->Modify();
		}
		Set();
		for (auto* Instance : Inheriting)
		{
			P->CopyCompleteValue_InContainer(Instance, A); Instance->MarkPackageDirty();
			if (auto* Class = Instance->GetTypedOuter<UBlueprintGeneratedClass>())
				if (auto* Derived = Cast<UBlueprint>(Class->ClassGeneratedBy)) FBlueprintEditorUtils::MarkBlueprintAsModified(Derived);
		}
	}
}
FString AudioComponentUtils::Inspect(const FString& BlueprintPath, const FString& ComponentName, const FString& ActorPath)
{
	const auto T = Target(BlueprintPath, ComponentName, ActorPath); auto* A = T.Component;
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart();
	J->WriteValue(TEXT("bp_path"), Path(T.Blueprint)); J->WriteValue(TEXT("actor_path"), Path(T.Actor)); J->WriteValue(TEXT("component_name"), ComponentName);
	J->WriteValue(TEXT("template_path"), T.Blueprint ? A->GetPathName() : FString()); J->WriteValue(TEXT("component_path"), A->GetPathName());
	J->WriteValue(TEXT("scope"), T.bNativeSubobject ? TEXT("Blueprint-owned native Audio Component default subobject") : (T.Blueprint ? TEXT("Blueprint SCS Audio Component effective template") : TEXT("Placed editor Audio Component instance")));
	J->WriteValue(TEXT("inherited"), T.bInherited || T.bNativeSubobject); J->WriteValue(TEXT("native_default_subobject"), T.bNativeSubobject);
	J->WriteValue(TEXT("has_local_override"), T.bNativeSubobject ? HasNativeSettingsOverride(A) : T.OwnOverride() != nullptr);
	if (T.bNativeSubobject) { J->WriteValue(TEXT("archetype_path"), Path(A->GetArchetype())); J->WriteValue(TEXT("override_scope"), TEXT("supported audio settings differ from immediate parent archetype")); }
	if (T.Node) J->WriteValue(TEXT("defining_blueprint"), Path(T.Node->GetSCS()->GetBlueprint()));
	J->WriteValue(TEXT("package_path"), T.Package()->GetName()); J->WriteValue(TEXT("dirty"), T.Package()->IsDirty());
	if (T.Blueprint) J->WriteValue(TEXT("blueprint_status"), static_cast<int32>(T.Blueprint->Status));
	J->WriteObjectStart(TEXT("numeric_settings")); for (const auto& Pair : Numeric) J->WriteValue(Pair.Key, Float(Pair.Key)->GetPropertyValue_InContainer(A)); J->WriteObjectEnd();
	J->WriteObjectStart(TEXT("bool_settings")); for (const auto& Key : Booleans) J->WriteValue(Key, Bool(Key)->GetPropertyValue_InContainer(A)); J->WriteObjectEnd();
	J->WriteObjectStart(TEXT("references")); for (const auto& Pair : ReferenceClasses) J->WriteValue(Pair.Key, Path(Object(Pair.Key)->GetObjectPropertyValue_InContainer(A))); J->WriteObjectEnd();
	J->WriteArrayStart(TEXT("concurrency_paths")); for (const auto& P : Concurrency(A)) J->WriteValue(P); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return Json;
}
FString AudioComponentUtils::Edit(const FAudioComponentSettingsReq& R)
{
	const auto T = Target(R.BpPath, R.ComponentName, R.ActorPath); auto* A = T.Component;
	if (R.bResetInheritedOverride && (!(T.bInherited || T.bNativeSubobject) || !R.NumericSettings.IsEmpty() || !R.BoolSettings.IsEmpty() || !R.References.IsEmpty() || R.bSetConcurrency || !R.ConcurrencyPaths.IsEmpty())) throw std::runtime_error("ResetInheritedOverride requires an inherited component and no other settings");
	if ((T.bInherited || T.bNativeSubobject) && !A->IsEditableWhenInherited()) throw std::runtime_error("The inherited component is not editable in child Blueprints");
	bool WouldChange = false; TMap<FString, UObject*> Refs; TSet<TObjectPtr<USoundConcurrency>> NewConcurrency;
	for (const auto& Pair : R.NumericSettings)
	{
		const auto* Range = Numeric.Find(Pair.Key);
		if (!Range || !FMath::IsFinite(Pair.Value) || Pair.Value < Range->X || Pair.Value > Range->Y) throw std::runtime_error("Unsupported numeric setting or value outside its supported finite range");
		WouldChange |= Float(Pair.Key)->GetPropertyValue_InContainer(A) != Pair.Value;
	}
	for (const auto& Pair : R.BoolSettings)
	{
		if (!Booleans.Contains(Pair.Key)) throw std::runtime_error("Unsupported audio component boolean setting");
		WouldChange |= Bool(Pair.Key)->GetPropertyValue_InContainer(A) != Pair.Value;
	}
	for (const auto& Pair : R.References)
	{
		auto* Class = ReferenceClasses.Find(Pair.Key); if (!Class) throw std::runtime_error("References support Sound, AttenuationSettings and SoundClassOverride");
		UObject* Value = Pair.Value.IsEmpty() ? nullptr : StaticLoadObject(*Class, nullptr, *Pair.Value);
		if (!Pair.Value.IsEmpty() && (!Value || !Value->IsAsset() || Value->HasAnyFlags(RF_Transient))) throw std::runtime_error("Audio component references require persistent assets of the expected native type");
		Refs.Add(Pair.Key, Value); WouldChange |= Object(Pair.Key)->GetObjectPropertyValue_InContainer(A) != Value;
	}
	if (!R.bSetConcurrency && !R.ConcurrencyPaths.IsEmpty()) throw std::runtime_error("ConcurrencyPaths requires bSetConcurrency");
	if (R.bSetConcurrency)
	{
		if (R.ConcurrencyPaths.Num() > 32) throw std::runtime_error("ConcurrencyPaths limited to 32 assets");
		for (const auto& P : R.ConcurrencyPaths) { auto* C = LoadObject<USoundConcurrency>(nullptr, *P); if (!C || !C->IsAsset() || C->HasAnyFlags(RF_Transient) || NewConcurrency.Contains(C)) throw std::runtime_error("Concurrency assets must be persistent, have native type and be unique"); NewConcurrency.Add(C); }
		WouldChange |= NewConcurrency.Num() != A->ConcurrencySet.Num();
		for (const auto& C : NewConcurrency) WouldChange |= !A->ConcurrencySet.Contains(C);
	}
	if (R.bResetInheritedOverride) WouldChange = T.bNativeSubobject ? HasNativeSettingsOverride(A) : T.OwnOverride() != nullptr;
	if (!R.bDryRun && (WouldChange || R.bSave) && GEditor && GEditor->PlayWorld) throw std::runtime_error("Stop PIE before editing/saving persistent audio components");
	if (!R.bDryRun && R.bSave && T.Actor && !FPackageName::DoesPackageExist(T.Package()->GetName())) throw std::runtime_error("Save the actor's map first using the world save workflow");
	if (!R.bDryRun && WouldChange)
	{
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AudioComponentSettings", "Edit Audio Component Settings"));
		if (T.Blueprint) { T.Blueprint->Modify(); if (T.Node && !T.bInherited) T.Node->Modify(); }
		if (T.bNativeSubobject) { A->GetOuter()->SetFlags(RF_Transactional); A->GetOuter()->Modify(); }
		if (T.Actor) T.Actor->Modify();
		if (T.bInherited)
		{
			T.Blueprint->GeneratedClass->SetFlags(RF_Transactional); T.Blueprint->GeneratedClass->Modify();
			auto* Handler = T.Blueprint->GetInheritableComponentHandler(true);
			if (!Handler) throw std::runtime_error("Native inheritable component handling is disabled");
			Handler->SetFlags(RF_Transactional); Handler->Modify();
			if (R.bResetInheritedOverride)
			{
				auto* Parent = Cast<UAudioComponent>(Handler->FindBestArchetype(FComponentKey(T.Node)));
				if (!Parent) throw std::runtime_error("Native parent archetype unavailable for reset");
				A->SetFlags(RF_Transactional); A->Modify();
				for (auto* P : SupportedFields()) if (!P->Identical_InContainer(A, Parent)) Change(A, P, true, [&] { P->CopyCompleteValue_InContainer(A, Parent); });
				Handler->RemoveOverridenComponentTemplate(FComponentKey(T.Node));
			}
			else
			{
				A = Cast<UAudioComponent>(Handler->CreateOverridenComponentTemplate(FComponentKey(T.Node)));
				if (!A) throw std::runtime_error("Could not create native child Audio Component override");
			}
		}
		if (R.bResetInheritedOverride && T.bNativeSubobject)
		{
			auto* Parent = Cast<UAudioComponent>(A->GetArchetype());
			A->SetFlags(RF_Transactional); A->Modify();
			for (auto* P : SupportedFields()) if (!P->Identical_InContainer(A, Parent)) Change(A, P, true, [&] { P->CopyCompleteValue_InContainer(A, Parent); });
			A->PostEditChange();
		}
		if (!R.bResetInheritedOverride)
		{
			A->SetFlags(RF_Transactional); A->Modify();
			auto Change = [&](FProperty* P, TFunctionRef<void()> Set)
			{
				::Change(A, P, T.Blueprint != nullptr, Set);
			};
			for (const auto& Pair : R.NumericSettings) { auto* P = Float(Pair.Key); if (P->GetPropertyValue_InContainer(A) != Pair.Value) Change(P, [&] { P->SetPropertyValue_InContainer(A, Pair.Value); }); }
			for (const auto& Pair : R.BoolSettings) { auto* P = Bool(Pair.Key); if (P->GetPropertyValue_InContainer(A) != Pair.Value) Change(P, [&] { P->SetPropertyValue_InContainer(A, Pair.Value); }); }
			for (const auto& Pair : Refs) { auto* P = Object(Pair.Key); if (P->GetObjectPropertyValue_InContainer(A) != Pair.Value) Change(P, [&] { P->SetObjectPropertyValue_InContainer(A, Pair.Value); }); }
			if (R.bSetConcurrency)
			{
				bool Different = NewConcurrency.Num() != A->ConcurrencySet.Num(); for (const auto& C : NewConcurrency) Different |= !A->ConcurrencySet.Contains(C);
				if (Different) Change(Property<FSetProperty>(TEXT("ConcurrencySet")), [&] { A->ConcurrencySet = NewConcurrency; });
			}
			A->PostEditChange();
		}
		if (T.Blueprint) { FBlueprintEditorUtils::MarkBlueprintAsModified(T.Blueprint); FKismetEditorUtilities::CompileBlueprint(T.Blueprint); T.Blueprint->MarkPackageDirty(); }
		else T.Actor->MarkPackageDirty();
	}
	bool Saved = false;
	if (R.bSave && !R.bDryRun)
	{
		if (T.Blueprint)
		{
			if (T.Blueprint->Status == BS_Error) throw std::runtime_error("Blueprint compilation failed; changed settings remain available for repair");
			auto* S = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
			if (!S || !S->SaveLoadedAsset(T.Blueprint, false)) throw std::runtime_error("Could not save Blueprint audio component settings");
		}
		else if (!UEditorLoadingAndSavingUtils::SavePackages({T.Package()}, false)) throw std::runtime_error("Could not save actor package; edits remain available");
		Saved = true;
	}
	FString Json; auto J = TJsonWriterFactory<>::Create(&Json); J->WriteObjectStart(); J->WriteValue(TEXT("bp_path"), Path(T.Blueprint)); J->WriteValue(TEXT("actor_path"), Path(T.Actor)); J->WriteValue(TEXT("component_name"), R.ComponentName);
	J->WriteValue(TEXT("would_change"), WouldChange); J->WriteValue(TEXT("changed"), WouldChange && !R.bDryRun); J->WriteValue(TEXT("dry_run"), R.bDryRun); J->WriteValue(TEXT("saved"), Saved);
	J->WriteValue(TEXT("package_path"), T.Package()->GetName()); J->WriteValue(TEXT("dirty"), T.Package()->IsDirty());
	if (T.Blueprint) J->WriteValue(TEXT("blueprint_status"), static_cast<int32>(T.Blueprint->Status));
	J->WriteObjectEnd(); J->Close(); return Json;
}
