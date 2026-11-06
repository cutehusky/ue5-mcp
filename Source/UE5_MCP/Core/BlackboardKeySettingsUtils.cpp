#include "BlackboardKeySettingsUtils.h"
#include "UE5_MCP/API/DTO/BlackboardKeyReq.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Bool.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Int.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Float.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Name.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_String.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Vector.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Rotator.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Object.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Class.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Enum.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonWriter.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
 template<typename T> bool Is(UBlackboardKeyType* K) { return K && K->GetClass()==T::StaticClass(); }
 FString Kind(UBlackboardKeyType* K)
 {
#define BB_KIND(T) if(Is<UBlackboardKeyType_##T>(K)) return TEXT(#T);
  BB_KIND(Bool) BB_KIND(Int) BB_KIND(Float) BB_KIND(Name) BB_KIND(String)
  BB_KIND(Vector) BB_KIND(Rotator) BB_KIND(Object) BB_KIND(Class) BB_KIND(Enum)
#undef BB_KIND
  return TEXT("unsupported");
 }
 UClass* Class(const FString& Path)
 {
  if(Path.IsEmpty() || Path.Contains(TEXT(":"))) throw std::runtime_error("A full compatible class path is required");
  auto* C=LoadClass<UObject>(nullptr,*Path);
  if(!C || C->HasAnyClassFlags(CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("Class path is missing, deprecated or stale"); return C;
 }
 UObject* Reference(const FString& Path)
 {
  if(Path.IsEmpty()) return nullptr;
  if(Path.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(Path)) throw std::runtime_error("Default object requires an asset or native class object path, without subobjects");
  auto* O=FindObject<UObject>(nullptr,*Path);
  if(!O)
  {
   auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
   if(Path.StartsWith(TEXT("/Script/"))) O=LoadObject<UClass>(nullptr,*Path);
   else if(Registry.GetAssetByObjectPath(FSoftObjectPath(Path)).IsValid()) O=LoadObject<UObject>(nullptr,*Path);
  }
  if(!IsValid(O) || O->HasAnyFlags(RF_Transient|RF_ClassDefaultObject) || (!O->IsAsset() && !O->IsA<UClass>())) throw std::runtime_error("Default object must be an existing persistent asset or native class"); return O;
 }
 UEnum* Enum(const FString& Path,bool Native=false)
 {
  if(Path.IsEmpty() || Path.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(Path) || (Native && !Path.StartsWith(TEXT("/Script/")))) throw std::runtime_error("Enum requires an object path; native name overrides require a full /Script enum path");
  auto* E=FindObject<UEnum>(nullptr,*Path);
  if(!E)
  {
   auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
   if(Path.StartsWith(TEXT("/Script/")) || Registry.GetAssetByObjectPath(FSoftObjectPath(Path)).IsValid()) E=LoadObject<UEnum>(nullptr,*Path);
  }
  if(!IsValid(E)) throw std::runtime_error("Enum path does not identify an existing UEnum"); return E;
 }
 TArray<FName> Properties(UBlackboardKeyType* K)
 {
  if(Is<UBlackboardKeyType_Bool>(K)) return {TEXT("bDefaultValue")};
  if(Is<UBlackboardKeyType_Vector>(K) || Is<UBlackboardKeyType_Rotator>(K)) return {TEXT("DefaultValue"),TEXT("bUseDefaultValue")};
  if(Is<UBlackboardKeyType_Object>(K) || Is<UBlackboardKeyType_Class>(K)) return {TEXT("DefaultValue"),TEXT("BaseClass")};
  if(Is<UBlackboardKeyType_Enum>(K)) return {TEXT("DefaultValue"),TEXT("EnumType"),TEXT("EnumName")};
  if(Kind(K)!=TEXT("unsupported")) return {TEXT("DefaultValue")}; return {};
 }
 void EnumErrors(UBlackboardKeyType_Enum* K,TArray<FString>& E)
 {
  auto* Type=K->EnumType.Get(); if(!Type) { E.Add(TEXT("EnumType is not configured")); return; }
  const int32 Count=Type->NumEnums()-(Type->ContainsExistingMax() ? 1 : 0);
  if(Count<1 || Count>1024) { E.Add(TEXT("Enum member count must be within [1,1024]")); return; }
  for(int32 I=0;I<Count;++I) if(Type->GetValueByIndex(I)<0 || Type->GetValueByIndex(I)>255) { E.Add(TEXT("Enum members must fit the native unsigned byte (excluding generated MAX)")); break; }
  const int32 Index=Type->GetIndexByValue(K->DefaultValue);
  if(!Type->IsValidEnumValueOrBitfield(K->DefaultValue) || (Type->ContainsExistingMax() && Index==Count)) E.Add(TEXT("Enum default is not a member or valid flag combination"));
  if(!K->EnumName.IsEmpty())
  {
   auto* Named=UClass::TryFindTypeSlow<UEnum>(K->EnumName,EFindFirstObjectOptions::ExactClass);
   if(Named!=Type || !K->bIsEnumNameValid) E.Add(TEXT("Native enum name override does not match resolved EnumType"));
  }
 }
}

TArray<FString> BlackboardKeySettingsUtils::Validate(UBlackboardKeyType* K)
{
 TArray<FString> E; if(!IsValid(K)) return {TEXT("Missing key type")};
 if(auto* V=Is<UBlackboardKeyType_Object>(K) ? Cast<UBlackboardKeyType_Object>(K) : nullptr)
 {
  if(!V->BaseClass || V->BaseClass->HasAnyClassFlags(CLASS_Deprecated|CLASS_NewerVersionExists)) E.Add(TEXT("Object BaseClass is missing or stale"));
  else if(V->DefaultValue && !V->DefaultValue->IsA(V->BaseClass)) E.Add(TEXT("Object default is incompatible with BaseClass"));
 }
 if(auto* V=Is<UBlackboardKeyType_Class>(K) ? Cast<UBlackboardKeyType_Class>(K) : nullptr)
 {
  if(!V->BaseClass || V->BaseClass->HasAnyClassFlags(CLASS_Deprecated|CLASS_NewerVersionExists)) E.Add(TEXT("Class BaseClass is missing or stale"));
  else if(V->DefaultValue && !V->DefaultValue->IsChildOf(V->BaseClass)) E.Add(TEXT("Class default is incompatible with BaseClass"));
 }
 if(Is<UBlackboardKeyType_Enum>(K)) EnumErrors(CastChecked<UBlackboardKeyType_Enum>(K),E);
 if(Is<UBlackboardKeyType_Float>(K) && (!FMath::IsFinite(CastChecked<UBlackboardKeyType_Float>(K)->DefaultValue) || FMath::Abs(CastChecked<UBlackboardKeyType_Float>(K)->DefaultValue)>1.e30f)) E.Add(TEXT("Float default must be finite and within +/-1e30"));
 if(Is<UBlackboardKeyType_Name>(K) && CastChecked<UBlackboardKeyType_Name>(K)->DefaultValue.ToString().Len()>128) E.Add(TEXT("Name default exceeds 128 characters"));
 if(Is<UBlackboardKeyType_String>(K) && CastChecked<UBlackboardKeyType_String>(K)->DefaultValue.Len()>4096) E.Add(TEXT("String default exceeds 4096 characters"));
 if(Is<UBlackboardKeyType_Vector>(K)) { const auto& V=CastChecked<UBlackboardKeyType_Vector>(K)->DefaultValue; if(V.ContainsNaN() || V.GetAbsMax()>1.e9) E.Add(TEXT("Vector default must be finite and within +/-1e9")); }
 if(Is<UBlackboardKeyType_Rotator>(K)) { const auto& V=CastChecked<UBlackboardKeyType_Rotator>(K)->DefaultValue; if(V.ContainsNaN() || FMath::Max3(FMath::Abs(V.Pitch),FMath::Abs(V.Yaw),FMath::Abs(V.Roll))>1.e9) E.Add(TEXT("Rotation default must be finite and within +/-1e9 degrees")); }
 return E;
}

TStrongObjectPtr<UBlackboardKeyType> BlackboardKeySettingsUtils::Prepare(UBlackboardKeyType* Source,const FBlackboardTypeSettings& R)
{
 const FString Type=Kind(Source); if(Type==TEXT("unsupported")) throw std::runtime_error("Typed settings support exact native Bool/Int/Float/Name/String/Vector/Rotator/Object/Class/Enum key classes");
 if(R.bSetUseDefault && Type!=TEXT("Vector") && Type!=TEXT("Rotator")) throw std::runtime_error("UseDefault applies only to Vector and Rotator");
 if(R.bSetBaseClass && Type!=TEXT("Object") && Type!=TEXT("Class")) throw std::runtime_error("BaseClass applies only to Object and Class");
 if((R.bSetEnumType || R.bSetNativeEnumName) && Type!=TEXT("Enum")) throw std::runtime_error("Enum fields require the native Enum key type");
 if(Type==TEXT("Enum") && R.bSetEnumType && !R.bSetNativeEnumName && !CastChecked<UBlackboardKeyType_Enum>(Source)->EnumName.IsEmpty()) throw std::runtime_error("Clear the existing native enum name override in the same request when changing EnumType");
 TStrongObjectPtr<UBlackboardKeyType> P(DuplicateObject<UBlackboardKeyType>(Source,GetTransientPackage())); auto* K=P.Get();
 if(R.bSetBaseClass)
 {
  auto* C=Class(R.BaseClass); if(Type==TEXT("Object")) CastChecked<UBlackboardKeyType_Object>(K)->BaseClass=C; else CastChecked<UBlackboardKeyType_Class>(K)->BaseClass=C;
 }
 if(Type==TEXT("Enum"))
 {
  auto* V=CastChecked<UBlackboardKeyType_Enum>(K);
  if(R.bSetEnumType) V->EnumType=Enum(R.EnumTypePath);
  if(R.bSetNativeEnumName) { V->EnumName=R.NativeEnumName; if(!R.NativeEnumName.IsEmpty()) V->EnumType=Enum(R.NativeEnumName,true); }
  V->bIsEnumNameValid=V->EnumType && !V->EnumName.IsEmpty();
 }
 if(R.bSetDefault)
 {
  if(Type==TEXT("Bool")) CastChecked<UBlackboardKeyType_Bool>(K)->bDefaultValue=R.BoolValue;
  else if(Type==TEXT("Int")) { if(R.IntValue<MIN_int32 || R.IntValue>MAX_int32) throw std::runtime_error("Int default must fit signed 32-bit range"); CastChecked<UBlackboardKeyType_Int>(K)->DefaultValue=int32(R.IntValue); }
  else if(Type==TEXT("Float")) { if(!FMath::IsFinite(R.FloatValue) || FMath::Abs(R.FloatValue)>1.e30) throw std::runtime_error("Float default requires finite +/-1e30"); CastChecked<UBlackboardKeyType_Float>(K)->DefaultValue=float(R.FloatValue); }
  else if(Type==TEXT("Name")) { if(R.TextValue.Len()>128) throw std::runtime_error("Name default exceeds 128 characters"); CastChecked<UBlackboardKeyType_Name>(K)->DefaultValue=FName(*R.TextValue); }
  else if(Type==TEXT("String")) { if(R.TextValue.Len()>4096) throw std::runtime_error("String default exceeds 4096 characters"); CastChecked<UBlackboardKeyType_String>(K)->DefaultValue=R.TextValue; }
  else if(Type==TEXT("Vector")) CastChecked<UBlackboardKeyType_Vector>(K)->DefaultValue=R.VectorValue;
  else if(Type==TEXT("Rotator")) CastChecked<UBlackboardKeyType_Rotator>(K)->DefaultValue=R.RotationValue;
  else if(Type==TEXT("Object")) CastChecked<UBlackboardKeyType_Object>(K)->DefaultValue=Reference(R.ReferenceValue);
  else if(Type==TEXT("Class")) CastChecked<UBlackboardKeyType_Class>(K)->DefaultValue=R.ReferenceValue.IsEmpty() ? nullptr : Class(R.ReferenceValue);
  else if(Type==TEXT("Enum")) { if(R.IntValue<0 || R.IntValue>255) throw std::runtime_error("Enum defaults require [0,255]"); CastChecked<UBlackboardKeyType_Enum>(K)->DefaultValue=uint8(R.IntValue); }
 }
 if(R.bSetUseDefault)
 {
  if(Type==TEXT("Vector")) CastChecked<UBlackboardKeyType_Vector>(K)->bUseDefaultValue=R.bUseDefault; else CastChecked<UBlackboardKeyType_Rotator>(K)->bUseDefaultValue=R.bUseDefault;
 }
 const auto E=Validate(K); if(!E.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(E,TEXT("; "))));
 // Range validation above avoids the editor's invalid-enum modal dialog.
 if(Type==TEXT("Enum") && R.bSetNativeEnumName)
 {
  auto* V=CastChecked<UBlackboardKeyType_Enum>(K); auto* Desired=V->EnumType.Get();
  FPropertyChangedEvent Event(FindFProperty<FProperty>(K->GetClass(),TEXT("EnumName")),EPropertyChangeType::ValueSet); K->PostEditChangeProperty(Event);
  if(R.NativeEnumName.IsEmpty())
  {
   V->EnumType=Desired; FPropertyChangedEvent TypeEvent(FindFProperty<FProperty>(K->GetClass(),TEXT("EnumType")),EPropertyChangeType::ValueSet); K->PostEditChangeProperty(TypeEvent);
  }
  const auto NativeErrors=Validate(K); if(!NativeErrors.IsEmpty()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Join(NativeErrors,TEXT("; "))));
 }
 return P;
}
void BlackboardKeySettingsUtils::Copy(UBlackboardKeyType* Target,UBlackboardKeyType* Source)
{
 check(Target && Source && Target->GetClass()==Source->GetClass());
 for(FName Name:Properties(Source)) if(auto* P=FindFProperty<FProperty>(Source->GetClass(),Name)) P->CopyCompleteValue_InContainer(Target,Source);
 FPropertyChangedEvent Event(nullptr,EPropertyChangeType::ValueSet); Target->PostEditChangeProperty(Event);
}
FString BlackboardKeySettingsUtils::Compatibility(UBlackboardKeyType* K)
{
 FString S=GetPathNameSafe(K ? K->GetClass() : nullptr);
 if(Is<UBlackboardKeyType_Object>(K)) S+=GetPathNameSafe(CastChecked<UBlackboardKeyType_Object>(K)->BaseClass);
 if(Is<UBlackboardKeyType_Class>(K)) S+=GetPathNameSafe(CastChecked<UBlackboardKeyType_Class>(K)->BaseClass);
 if(Is<UBlackboardKeyType_Enum>(K)) S+=GetPathNameSafe(CastChecked<UBlackboardKeyType_Enum>(K)->EnumType); return S;
}
FString BlackboardKeySettingsUtils::Snapshot(UBlackboardKeyType* K)
{
 FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); const FString Type=Kind(K);
 auto Number=[&](const TCHAR* Name,double V) { if(FMath::IsFinite(V)) J->WriteValue(Name,V); else J->WriteNull(Name); };
 J->WriteValue(TEXT("supported"),Type!=TEXT("unsupported")); J->WriteValue(TEXT("kind"),Type);
 if(Type==TEXT("Bool")) J->WriteValue(TEXT("default_value"),CastChecked<UBlackboardKeyType_Bool>(K)->bDefaultValue);
 if(Type==TEXT("Int")) J->WriteValue(TEXT("default_value"),CastChecked<UBlackboardKeyType_Int>(K)->DefaultValue);
 if(Type==TEXT("Float")) { const double V=CastChecked<UBlackboardKeyType_Float>(K)->DefaultValue; if(FMath::IsFinite(V)) J->WriteValue(TEXT("default_value"),V); else J->WriteNull(TEXT("default_value")); }
 if(Type==TEXT("Name")) J->WriteValue(TEXT("default_value"),CastChecked<UBlackboardKeyType_Name>(K)->DefaultValue.ToString());
 if(Type==TEXT("String")) { const auto& V=CastChecked<UBlackboardKeyType_String>(K)->DefaultValue; J->WriteValue(TEXT("default_value"),V.Left(4096)); J->WriteValue(TEXT("default_value_length"),V.Len()); J->WriteValue(TEXT("default_value_truncated"),V.Len()>4096); }
 if(Type==TEXT("Vector")) { auto* V=CastChecked<UBlackboardKeyType_Vector>(K); J->WriteValue(TEXT("use_default_value"),V->bUseDefaultValue); J->WriteObjectStart(TEXT("default_value")); Number(TEXT("X"),V->DefaultValue.X); Number(TEXT("Y"),V->DefaultValue.Y); Number(TEXT("Z"),V->DefaultValue.Z); J->WriteObjectEnd(); }
 if(Type==TEXT("Rotator")) { auto* V=CastChecked<UBlackboardKeyType_Rotator>(K); J->WriteValue(TEXT("use_default_value"),V->bUseDefaultValue); J->WriteObjectStart(TEXT("default_value")); Number(TEXT("Pitch"),V->DefaultValue.Pitch); Number(TEXT("Yaw"),V->DefaultValue.Yaw); Number(TEXT("Roll"),V->DefaultValue.Roll); J->WriteObjectEnd(); }
 if(Type==TEXT("Object")) { auto* V=CastChecked<UBlackboardKeyType_Object>(K); J->WriteValue(TEXT("base_class"),GetPathNameSafe(V->BaseClass)); J->WriteValue(TEXT("default_value"),V->DefaultValue ? V->DefaultValue->GetPathName() : FString()); }
 if(Type==TEXT("Class")) { auto* V=CastChecked<UBlackboardKeyType_Class>(K); J->WriteValue(TEXT("base_class"),GetPathNameSafe(V->BaseClass)); J->WriteValue(TEXT("default_value"),V->DefaultValue ? V->DefaultValue->GetPathName() : FString()); }
 if(Type==TEXT("Enum")) { auto* V=CastChecked<UBlackboardKeyType_Enum>(K); J->WriteValue(TEXT("enum_type"),GetPathNameSafe(V->EnumType)); J->WriteValue(TEXT("native_enum_name"),V->EnumName); J->WriteValue(TEXT("enum_name_valid"),bool(V->bIsEnumNameValid)); J->WriteValue(TEXT("default_value"),int32(V->DefaultValue)); }
 J->WriteArrayStart(TEXT("errors")); for(const auto& E:Validate(K)) J->WriteValue(E); J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
