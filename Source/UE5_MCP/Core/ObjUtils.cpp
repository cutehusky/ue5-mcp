#include "ObjUtils.h"

#include "UObject/UnrealType.h"

TArray<UClass*> ObjUtils::DetailUObjectClassWhitelist = {};
TMap<FFieldClass*, FJsonSerializerFunc> ObjUtils::JsonSerializers = {};
TMap<FFieldClass*, FJsonArraySerializerFunc> ObjUtils::JsonArraySerializers = {};
TMap<FFieldClass*, FObjPropertySetterFunc> ObjUtils::ObjPropertySetters = {};

namespace
{
	FProperty* FindProperty(UStruct* Struct, const FString& Name)
	{
		if (!Struct) return nullptr;
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
			if (*It && (*It)->GetName().Equals(Name, ESearchCase::IgnoreCase)) return *It;
		return nullptr;
	}

	// Likely paths for a property name that was not found, looking one struct level down: BodyInstance.CollisionProfileName.
	FString NotFoundMessage(const FString& Name, UStruct* Struct, const FString& OwnerName)
	{
		TArray<FString> Matches;
		const auto Similar = [&Name](const FString& Candidate)
		{
			return Candidate.Contains(Name) || (Candidate.Len() >= 4 && Name.Contains(Candidate));
		};
		for (TFieldIterator<FProperty> It(Struct); It && Matches.Num() < 5; ++It)
		{
			if (Similar(It->GetName())) Matches.Add(It->GetName());
			if (const FStructProperty* Nested = CastField<FStructProperty>(*It))
				for (TFieldIterator<FProperty> Inner(Nested->Struct); Inner && Matches.Num() < 5; ++Inner)
					if (Similar(Inner->GetName())) Matches.Add(It->GetName() + TEXT(".") + Inner->GetName());
		}
		FString Message = FString::Printf(TEXT("Property %s not found in %s."), *Name, *OwnerName);
		if (!Matches.IsEmpty()) Message += FString::Printf(TEXT(" Did you mean: %s?"), *FString::Join(Matches, TEXT(", ")));
		return Message;
	}

	int32 ParseArrayIndex(const FString& Text)
	{
		int32 Index = INDEX_NONE;
		if (!LexTryParseString(Index, *Text) || Index < 0)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Invalid array index: %s"), *Text)));
		return Index;
	}

	void ImportLeaf(FProperty* Property, void* Container, UObject* Owner, const FString& Value)
	{
		if (!Property || !Container) throw std::runtime_error("Invalid property storage address");
		if (Property->HasAnyPropertyFlags(CPF_Transient | CPF_DuplicateTransient | CPF_Deprecated | CPF_EditConst))
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s is not editable"), *Property->GetName())));
		void* PropertyValue = Property->ContainerPtrToValuePtr<void>(Container);
		FString Input = Value;
		Input.TrimStartAndEndInline();
		const TCHAR* Result = Property->ImportText_Direct(*Input, PropertyValue, Owner, PPF_None, GWarn);
		FString Remaining = Result ? FString(Result) : FString();
		Remaining.TrimStartAndEndInline();
		if (!Result || !Remaining.IsEmpty())
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Invalid value '%s' for property %s of type %s"), *Value, *Property->GetName(), *Property->GetClass()->GetName())));
	}

	void SetRecursive(FProperty* Property, void* Container, UObject* Owner,
		const TArray<FString>& Parts, int32 PartIndex, const FString& Value)
	{
		if (!Property || !Container) throw std::runtime_error("Invalid property path");
		if (PartIndex >= Parts.Num()) { ImportLeaf(Property, Container, Owner, Value); return; }

		if (FStructProperty* StructProperty = CastField<FStructProperty>(Property))
		{
			void* StructValue = StructProperty->ContainerPtrToValuePtr<void>(Container);
			FProperty* Child = FindProperty(StructProperty->Struct, Parts[PartIndex]);
			if (!Child) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s not found in struct %s"), *Parts[PartIndex], *StructProperty->Struct->GetName())));
			SetRecursive(Child, StructValue, Owner, Parts, PartIndex + 1, Value);
			return;
		}

		if (FObjectPropertyBase* ObjectProperty = CastField<FObjectPropertyBase>(Property))
		{
			void* ObjectValue = ObjectProperty->ContainerPtrToValuePtr<void>(Container);
			UObject* SubObject = ObjectProperty->GetObjectPropertyValue(ObjectValue);
			if (!SubObject) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Object property %s is null; nested editing requires an existing object"), *Property->GetName())));
			FProperty* Child = FindProperty(SubObject->GetClass(), Parts[PartIndex]);
			if (!Child) throw std::runtime_error(TCHAR_TO_UTF8(*NotFoundMessage(Parts[PartIndex], SubObject->GetClass(), SubObject->GetName())));
			SetRecursive(Child, SubObject, SubObject, Parts, PartIndex + 1, Value);
			return;
		}

		if (FArrayProperty* ArrayProperty = CastField<FArrayProperty>(Property))
		{
			const int32 Index = ParseArrayIndex(Parts[PartIndex]);
			void* ArrayValue = ArrayProperty->ContainerPtrToValuePtr<void>(Container);
			FScriptArrayHelper ArrayHelper(ArrayProperty, ArrayValue);
			if (Index >= ArrayHelper.Num()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Array index %d is out of range for %s"), Index, *Property->GetName())));
			SetRecursive(ArrayProperty->Inner, ArrayHelper.GetElementPtr(Index), Owner, Parts, PartIndex + 1, Value);
			return;
		}

		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s does not support nested path editing; assign the complete container value"), *Property->GetName())));
	}

	void WritePropertyValue(FProperty* Property, const void* PropertyValue,
		TSharedRef<TJsonWriter<>>& Writer, const FString* Name)
	{
		if (!Property || !PropertyValue) return;
		const bool bNamed = Name != nullptr;
		if (const FByteProperty* P = CastField<FByteProperty>(Property)) { const uint8 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FInt8Property* P = CastField<FInt8Property>(Property)) { const int8 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FInt16Property* P = CastField<FInt16Property>(Property)) { const int16 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FIntProperty* P = CastField<FIntProperty>(Property)) { const int32 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FInt64Property* P = CastField<FInt64Property>(Property)) { const int64 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FUInt16Property* P = CastField<FUInt16Property>(Property)) { const uint16 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FUInt32Property* P = CastField<FUInt32Property>(Property)) { const uint32 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FUInt64Property* P = CastField<FUInt64Property>(Property)) { const uint64 V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FFloatProperty* P = CastField<FFloatProperty>(Property)) { const float V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FDoubleProperty* P = CastField<FDoubleProperty>(Property)) { const double V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FBoolProperty* P = CastField<FBoolProperty>(Property)) { const bool V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FStrProperty* P = CastField<FStrProperty>(Property)) { const FString& V = P->GetPropertyValue(PropertyValue); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FNameProperty* P = CastField<FNameProperty>(Property)) { const FString V = P->GetPropertyValue(PropertyValue).ToString(); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FTextProperty* P = CastField<FTextProperty>(Property)) { const FString V = P->GetPropertyValue(PropertyValue).ToString(); bNamed ? Writer->WriteValue(*Name, V) : Writer->WriteValue(V); return; }
		if (const FEnumProperty* P = CastField<FEnumProperty>(Property))
		{
			const int64 V = P->GetUnderlyingProperty()->GetSignedIntPropertyValue(PropertyValue);
			const FString Text = P->GetEnum() ? P->GetEnum()->GetNameByValue(V).ToString() : LexToString(V);
			bNamed ? Writer->WriteValue(*Name, Text) : Writer->WriteValue(Text); return;
		}
		if (const FObjectPropertyBase* P = CastField<FObjectPropertyBase>(Property))
		{
			if (const UObject* V = P->GetObjectPropertyValue(PropertyValue)) { const FString Text = V->GetPathName(); bNamed ? Writer->WriteValue(*Name, Text) : Writer->WriteValue(Text); }
			else if (bNamed) Writer->WriteNull(*Name); else Writer->WriteNull();
			return;
		}

		if (const FStructProperty* P = CastField<FStructProperty>(Property))
		{
			if (bNamed) Writer->WriteObjectStart(*Name); else Writer->WriteObjectStart();
			for (TFieldIterator<FProperty> It(P->Struct); It; ++It)
			{
				FProperty* Child = *It;
				if (!Child || Child->HasAnyPropertyFlags(CPF_Transient | CPF_DuplicateTransient)) continue;
				const FString ChildName = Child->GetName();
				WritePropertyValue(Child, Child->ContainerPtrToValuePtr<void>(PropertyValue), Writer, &ChildName);
			}
			Writer->WriteObjectEnd(); return;
		}
		if (const FArrayProperty* P = CastField<FArrayProperty>(Property))
		{
			if (bNamed) Writer->WriteArrayStart(*Name); else Writer->WriteArrayStart();
			FScriptArrayHelper H(P, PropertyValue);
			for (int32 I = 0; I < H.Num(); ++I) WritePropertyValue(P->Inner, H.GetElementPtr(I), Writer, nullptr);
			Writer->WriteArrayEnd(); return;
		}
		if (const FSetProperty* P = CastField<FSetProperty>(Property))
		{
			if (bNamed) Writer->WriteArrayStart(*Name); else Writer->WriteArrayStart();
			FScriptSetHelper H(P, PropertyValue);
			for (int32 I = 0; I < H.GetMaxIndex(); ++I)
				if (H.IsValidIndex(I)) WritePropertyValue(P->ElementProp, H.GetElementPtr(I), Writer, nullptr);
			Writer->WriteArrayEnd(); return;
		}
		if (const FMapProperty* P = CastField<FMapProperty>(Property))
		{
			if (bNamed) Writer->WriteArrayStart(*Name); else Writer->WriteArrayStart();
			FScriptMapHelper H(P, PropertyValue);
			for (int32 I = 0; I < H.GetMaxIndex(); ++I)
			{
				if (!H.IsValidIndex(I)) continue;
				Writer->WriteObjectStart();
				const FString KeyName = TEXT("key");
				const FString ValueName = TEXT("value");
				WritePropertyValue(P->KeyProp, H.GetKeyPtr(I), Writer, &KeyName);
				WritePropertyValue(P->ValueProp, H.GetValuePtr(I), Writer, &ValueName);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd(); return;
		}

		FString Exported;
		Property->ExportTextItem_Direct(Exported, PropertyValue, nullptr, nullptr, PPF_None, nullptr);
		bNamed ? Writer->WriteValue(*Name, Exported) : Writer->WriteValue(Exported);
	}
}

bool ObjUtils::IsInDetailUObjectWhitelist(UClass* Class)
{
	if (!Class) return false;
	for (UClass* WhitelistedClass : DetailUObjectClassWhitelist)
		if (WhitelistedClass && Class->IsChildOf(WhitelistedClass)) return true;
	return false;
}

void ObjUtils::SerializeProperty(UObject* Obj, TSharedRef<TJsonWriter<>> Writer)
{
	if (!Obj || !Obj->GetClass()) return;
	for (TFieldIterator<FProperty> It(Obj->GetClass()); It; ++It)
	{
		FProperty* Property = *It;
		if (!Property || Property->HasAnyPropertyFlags(CPF_Transient | CPF_DuplicateTransient)) continue;
		const FString PropertyName = Property->GetName();
		WritePropertyValue(Property, Property->ContainerPtrToValuePtr<void>(Obj), Writer, &PropertyName);
	}
}

void ObjUtils::SerializeProperty(const FStructProperty* StructProp, const void* StructPtr, TSharedRef<TJsonWriter<>> Writer)
{
	if (!StructProp || !StructPtr || !StructProp->Struct) return;
	for (TFieldIterator<FProperty> It(StructProp->Struct); It; ++It)
	{
		FProperty* Property = *It;
		if (!Property || Property->HasAnyPropertyFlags(CPF_Transient | CPF_DuplicateTransient)) continue;
		const FString PropertyName = Property->GetName();
		WritePropertyValue(Property, Property->ContainerPtrToValuePtr<void>(StructPtr), Writer, &PropertyName);
	}
}

void ObjUtils::SerializeProperty(const FArrayProperty* ArrayProp, const void* ArrayPtr, TSharedRef<TJsonWriter<>> Writer)
{
	if (!ArrayProp || !ArrayPtr) return;
	FScriptArrayHelper Helper(ArrayProp, ArrayPtr);
	for (int32 Index = 0; Index < Helper.Num(); ++Index)
	{
		WritePropertyValue(ArrayProp->Inner, Helper.GetElementPtr(Index), Writer, nullptr);
	}
}

void ObjUtils::SerializeProperty(const FSetProperty* SetProp, const void* SetPtr, TSharedRef<TJsonWriter<>> Writer)
{
	if (!SetProp || !SetPtr) return;
	FScriptSetHelper Helper(SetProp, SetPtr);
	for (int32 Index = 0; Index < Helper.GetMaxIndex(); ++Index)
	{
		if (!Helper.IsValidIndex(Index)) continue;
		FString Exported;
		SetProp->ElementProp->ExportTextItem_Direct(Exported, Helper.GetElementPtr(Index), nullptr, nullptr, PPF_None, nullptr);
		Writer->WriteValue(Exported);
	}
}

FString ObjUtils::SerializeObjectToJson(UObject* Obj)
{
	if (!Obj) return TEXT("{}");
	FString Result;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Result);
	Writer->WriteObjectStart();
	SerializeProperty(Obj, Writer);
	Writer->WriteObjectEnd();
	Writer->Close();
	return Result;
}

void ObjUtils::SetPropertyByPath(UObject* Obj, const TArray<FString>& PathParts, const FString& Value, int32 Index)
{
	if (!Obj || PathParts.Num() == 0 || Index < 0 || Index >= PathParts.Num()) throw std::runtime_error("A valid object and non-empty property path are required");
	FProperty* Property = FindProperty(Obj->GetClass(), PathParts[Index]);
	if (!Property) throw std::runtime_error(TCHAR_TO_UTF8(*NotFoundMessage(PathParts[Index], Obj->GetClass(), Obj->GetName())));
	SetRecursive(Property, Obj, Obj, PathParts, Index + 1, Value);
}

void ObjUtils::SetPropertyByPath(const FStructProperty* StructProp, void* StructPtr, const TArray<FString>& PathParts, const FString& Value, int32 Index)
{
	if (!StructProp || !StructPtr || PathParts.Num() <= Index) throw std::runtime_error("Invalid struct property path");
	FProperty* Property = FindProperty(StructProp->Struct, PathParts[Index]);
	if (!Property) throw std::runtime_error(TCHAR_TO_UTF8(*NotFoundMessage(PathParts[Index], StructProp->Struct, StructProp->Struct->GetName())));
	SetRecursive(Property, StructPtr, nullptr, PathParts, Index + 1, Value);
}

void ObjUtils::SetPropertyByPath(const FArrayProperty* ArrayProp, const void* ArrayPtr, const TArray<FString>& PathParts, const FString& Value, int32 PathIndex)
{
	if (!ArrayProp || !ArrayPtr || PathIndex >= PathParts.Num()) throw std::runtime_error("Invalid array property path");
	const int32 Index = ParseArrayIndex(PathParts[PathIndex]);
	FScriptArrayHelper Helper(ArrayProp, ArrayPtr);
	if (Index >= Helper.Num()) throw std::runtime_error("Array index is out of range");
	SetRecursive(ArrayProp->Inner, Helper.GetElementPtr(Index), nullptr, PathParts, PathIndex + 1, Value);
}

void ObjUtils::SetPropertyValueFromString(UObject* Obj, const FString& PropertyPath, const FString& PropertyValue)
{
	if (!Obj) throw std::runtime_error("Object is null");
	TArray<FString> PathParts;
	PropertyPath.ParseIntoArray(PathParts, TEXT("."), true);
	SetPropertyByPath(Obj, PathParts, PropertyValue, 0);
}
