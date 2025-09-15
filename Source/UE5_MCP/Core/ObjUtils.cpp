#include "ObjUtils.h"

TArray<UClass*> ObjUtils::DetailUObjectClassWhitelist = {
	// TODO: Add whitelisted classes here
};

bool ObjUtils::IsInDetailUObjectWhitelist(UClass* Class)
{
	for (UClass* WhitelistedClass : DetailUObjectClassWhitelist)
	{
		if (Class->IsChildOf(WhitelistedClass))
			return true;
	}
	return false;
}

void ObjUtils::SerializeProperty(UObject* obj, TSharedRef<TJsonWriter<>> Writer)
{
	if (!obj || !obj->GetClass())
		return;
	for (TFieldIterator<FProperty> It(obj->GetClass()); It; ++It)
	{
		FProperty* Property = *It;
		if (!Property)
			continue;
		
		if (Property->HasAnyPropertyFlags(CPF_Transient)
			|| Property->HasAnyPropertyFlags(CPF_DuplicateTransient))
			continue;

		FString PropertyName = Property->GetName();
		if (auto SerializerIt = JsonSerializers.Find(Property->GetClass()))
		{
			(*SerializerIt)(Property, obj, Writer, PropertyName);
		} else 
		{
			// Optional: handle unsupported type
			UE_LOG(LogTemp, Warning, TEXT("Unsupported type for object serialization: %s"), *Property->GetClass()->GetName());
		}
	}
}


void ObjUtils::SerializeProperty(const FStructProperty* StructProp, const void* StructPtr,
	TSharedRef<TJsonWriter<>> Writer)
{
	if (!StructProp || !StructPtr || !StructProp->Struct)
		return;
	
	for (TFieldIterator<FProperty> It(StructProp->Struct); It; ++It)
	{
		FProperty* SubProp = *It;
		if (!SubProp)
			continue;
		
		if (SubProp->HasAnyPropertyFlags(CPF_Transient)
			|| SubProp->HasAnyPropertyFlags(CPF_DuplicateTransient))
			continue;

		FString SubPropName = SubProp->GetName();
		if (auto SerializerIt = JsonSerializers.Find(SubProp->GetClass()))
		{
			(*SerializerIt)(SubProp, StructPtr, Writer, SubPropName);
		} else
		{
			// Optional: handle unsupported type
			UE_LOG(LogTemp, Warning, TEXT("Unsupported type for struct serialization: %s"), *SubProp->GetClass()->GetName());
		}
	}
}


void ObjUtils::SerializeProperty(const FArrayProperty* ArrayProp, const void* ArrayPtr,
								 TSharedRef<TJsonWriter<>> Writer)
{
	if (!ArrayProp || !ArrayPtr)
		return;
	FScriptArrayHelper ArrayHelper(ArrayProp, ArrayPtr);
	FProperty* InnerProp = ArrayProp->Inner;

	for (int32 Index = 0; Index < ArrayHelper.Num(); ++Index)
	{
		void* ElementPtr = ArrayHelper.GetElementPtr(Index);
		
		if (!ElementPtr)
			continue;
		
		if (const auto Serializer = JsonArraySerializers.Find(InnerProp->GetClass()))
		{
			(*Serializer)(InnerProp, ElementPtr, Writer);
		}
		else
		{
			// Optional: handle unsupported type
			UE_LOG(LogTemp, Warning, TEXT("Unsupported type for array serialization: %s"), *InnerProp->GetClass()->GetName());
		}
	}
}

void ObjUtils::SerializeProperty(const FSetProperty* SetProp, const void* SetPtr, TSharedRef<TJsonWriter<>> Writer)
{
	if (!SetProp || !SetPtr)
		return;
	FScriptSetHelper SetHelper(SetProp, SetPtr);
	FProperty* InnerProp = SetProp->ElementProp;

	for (int32 i = 0; i < SetHelper.GetMaxIndex(); ++i)
	{
		if (!SetHelper.IsValidIndex(i))
			continue;
		void* ElementPtr = SetHelper.GetElementPtr(i);
		if (!ElementPtr)
			continue;
		if (const auto Serializer = JsonArraySerializers.Find(InnerProp->GetClass()))
		{
			(*Serializer)(InnerProp, ElementPtr, Writer);
		}
		else
		{
			// Optional: handle unsupported type
			UE_LOG(LogTemp, Warning, TEXT("Unsupported type for array serialization: %s"), *InnerProp->GetClass()->GetName());
		}
	}
}

FString ObjUtils::SerializeObjectToJson(UObject* obj)
{
	if (!obj)
		return FString(TEXT("{}"));
	FString ResultString;
	TSharedRef<TJsonWriter<>> Writer =
		TJsonWriterFactory<>::Create(&ResultString);
	Writer->WriteObjectStart();
	SerializeProperty(obj, Writer);
	Writer->WriteObjectEnd();
	Writer->Close();
	return ResultString;
}

void ObjUtils::SetPropertyByPath(UObject* Obj,
                                 const TArray<FString>& PathParts,
                                 FString Value,
                                 int32 Index)
{
	UE_LOG(LogTemp, Log, TEXT("SetPropertyByPath called with Index %d and Path Len %d"), Index, PathParts.Num());
	
	if (!Obj || !Obj->GetClass())
		return;

	if (Index < 0 || Index >= PathParts.Num())
		throw std::runtime_error("Property path index out of range");

	UE_LOG(LogTemp, Log, TEXT("Searching property %s of object %s"), *PathParts[Index], *Obj->GetName());
	
	FString CurrentPart = PathParts[Index];
	for (TFieldIterator<FProperty> It(Obj->GetClass()); It; ++It)
	{
		FProperty* Property = *It;
		if (Property && Property->GetName() == CurrentPart)
		{
			UE_LOG(LogTemp, Log, TEXT("Found property %s of object %s"), *CurrentPart, *Obj->GetName());
			if (auto SetterIt = ObjPropertySetters.Find(Property->GetClass()))
			{
				(*SetterIt)(Property, Obj, Value, PathParts, Index + 1);
			} else
			{
				UE_LOG(LogTemp, Warning, TEXT("Unsupported property type for setting value: %s"), *Property->GetClass()->GetName());
			}
			return;
		}
	}
	throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s not found in object %s"), *CurrentPart, *Obj->GetName())));
}

void ObjUtils::SetPropertyByPath(
	FStructProperty* StructProp,
	void* StructPtr,
	const TArray<FString>& PathParts,
	FString Value, int32 Index)
{
	UE_LOG(LogTemp, Log, TEXT("SetPropertyByPath (struct) called with Index %d and Path Len %d"), Index, PathParts.Num());
	
	if (!StructProp || !StructPtr || !StructProp->Struct)
		return;
	
	if (Index < 0 || Index >= PathParts.Num())
		throw std::runtime_error("Property path index out of range");

	FString CurrentPart = PathParts[Index];
	for (TFieldIterator<FProperty> It(StructProp->Struct); It; ++It)
	{
		FProperty* Property = *It;
		if (Property && Property->GetName() == CurrentPart)
		{
			if (auto SetterIt = ObjPropertySetters.Find(Property->GetClass()))
			{
				(*SetterIt)(Property, StructPtr, Value, PathParts, Index + 1);
			} else
			{
				UE_LOG(LogTemp, Warning, TEXT("Unsupported property type for setting value: %s"), *Property->GetClass()->GetName());
			}
			return;
		}
	}
	throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s not found in struct %s"), *CurrentPart, *StructProp->Struct->GetName())));
}

void ObjUtils::SetPropertyByPath(FArrayProperty* ArrayProp, void* ArrayPtr, const TArray<FString>& PathParts,
	FString Value, int32 PathIndex)
{
	UE_LOG(LogTemp, Log, TEXT("SetPropertyByPath (array) called with Index %d and Path Len %d"), PathIndex, PathParts.Num());
	
	if (PathIndex < 0 || PathIndex >= PathParts.Num())
		throw std::runtime_error("Property path index out of range");
	
	if (!ArrayProp || !ArrayPtr)
		return;
	
	auto InnerProp = ArrayProp->Inner;
	if (!InnerProp)
		return;
				
	FScriptArrayHelper ArrayHelper(ArrayProp, ArrayPtr);
	int32 Index = FCString::Atoi(*PathParts[PathIndex]);
	if (Index < 0)
		throw std::runtime_error("Array index out of range");
	// Expand array if needed
	for (int32 i = ArrayHelper.Num(); i <= Index; ++i)
	{
		ArrayHelper.AddValue();
	}

	void* ElementPtr = ArrayHelper.GetElementPtr(Index);
	if (auto SetterIt = ObjPropertySetters.Find(InnerProp->GetClass()))
	{
		(*SetterIt)(ArrayProp->Inner, ElementPtr, Value, PathParts, PathIndex + 1);
	} else
	{
		UE_LOG(LogTemp, Warning, TEXT("Unsupported property type for setting value: %s"), *InnerProp->GetClass()->GetName());
	}
}

void ObjUtils::SetPropertyValueFromString(UObject* obj, const FString& PropertyPath, const FString& PropertyValue)
{
	if (!obj || !obj->GetClass())
		return;

	TArray<FString> PathParts;
	PropertyPath.ParseIntoArray(PathParts, TEXT("."));
	SetPropertyByPath(obj, PathParts, PropertyValue, 0);
}
