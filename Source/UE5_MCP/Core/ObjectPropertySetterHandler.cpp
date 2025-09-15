#include "ObjUtils.h"

// Value property should have PathIndex == Paths.Num()
// Container property should have PathIndex < Paths.Num() and next path should be index/key
TMap<FFieldClass*, FObjPropertySetterFunc> ObjUtils::ObjPropertySetters = {
	// Value property
	{
		FByteProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FByteProperty>(Prop))
			{
				if (PropCasted->Enum)
				{
					int64 EnumValue = PropCasted->Enum->GetValueByNameString(Value);
					if (EnumValue != INDEX_NONE)
					{
						PropCasted->SetPropertyValue_InContainer(Obj, static_cast<uint8>(EnumValue));
						return;
					}
				}
				
				uint8 ByteValue = static_cast<uint8>(FCString::Atoi(*Value));
				PropCasted->SetPropertyValue_InContainer(Obj, ByteValue);
			}
		}
	},
	{
		FInt16Property::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FInt16Property>(Prop))
			{
				int16 Int16Value = static_cast<int16>(FCString::Atoi(*Value));
				PropCasted->SetPropertyValue_InContainer(Obj, Int16Value);
			}
		}
	},
	{
		FInt64Property::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FInt64Property>(Prop))
			{
				int64 Int64Value = FCString::Atoi64(*Value);
				PropCasted->SetPropertyValue_InContainer(Obj, Int64Value);
			}
		}
	},
	{
		FIntProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FIntProperty>(Prop))
			{
				int32 IntValue = FCString::Atoi(*Value);
				PropCasted->SetPropertyValue_InContainer(Obj, IntValue);
			}
		}
	},
	{
		FFloatProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FFloatProperty>(Prop))
			{
				float FloatValue = FCString::Atof(*Value);
				PropCasted->SetPropertyValue_InContainer(Obj, FloatValue);
			}
		}
	},
	{
		FDoubleProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FDoubleProperty>(Prop))
			{
				double DoubleValue = FCString::Atod(*Value);
				PropCasted->SetPropertyValue_InContainer(Obj, DoubleValue);
			}
		}
	},
	{
		FBoolProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FBoolProperty>(Prop))
			{
				bool BoolValue = Value.ToBool();
				PropCasted->SetPropertyValue_InContainer(Obj, BoolValue);
			}
		}
	},
	
	{
		FStrProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FStrProperty>(Prop))
			{
				PropCasted->SetPropertyValue_InContainer(Obj, Value);
			}
		}
	},
	{
		FNameProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FNameProperty>(Prop))
			{
				FName NameValue(*Value);
				PropCasted->SetPropertyValue_InContainer(Obj, NameValue);
			}
		}
	},
	{
		FTextProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FTextProperty>(Prop))
			{
				FText TextValue = FText::FromString(Value);
				PropCasted->SetPropertyValue_InContainer(Obj, TextValue);
			}
		}
	},
	{
		FEnumProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex != Paths.Num())
				throw std::runtime_error("Can't set sub-property of non-struct, non-object and non-conntainer property");
			
			if (const auto PropCasted = CastField<FEnumProperty>(Prop))
			{
				if (const auto UnderlyingProp = CastField<FByteProperty>(PropCasted->GetUnderlyingProperty()))
				{
					if (PropCasted->GetEnum())
					{
						int64 EnumValue = PropCasted->GetEnum()->GetValueByNameString(Value);
						if (EnumValue != INDEX_NONE)
						{
							UnderlyingProp->SetPropertyValue_InContainer(Obj, static_cast<uint8>(EnumValue));
						}
					}
				}
			}
		}
	},
	// Container property
	{
		FObjectProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (const auto PropCasted = CastField<FObjectProperty>(Prop))
			{
				if (PathIndex > Paths.Num())
					throw std::runtime_error("Property path index out of range");

				if (PathIndex == Paths.Num())
				{
					UObject* Asset = StaticLoadObject(PropCasted->PropertyClass, nullptr, *Value);
					if (!Asset)
						throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Failed to load asset at path: %s"), *Value)));
					PropCasted->SetObjectPropertyValue_InContainer(Obj, Asset);
					return;
				}
				
				auto SubObj = PropCasted->GetObjectPropertyValue_InContainer(Obj);
				if (!SubObj && PropCasted->PropertyClass) // Create new object if not exists
				{
					SubObj = NewObject<UObject>(GetTransientPackage(), PropCasted->PropertyClass);
					PropCasted->SetObjectPropertyValue_InContainer(Obj, SubObj);
				}
				if (!SubObj)
					return;
				SetPropertyByPath(SubObj, Paths, Value, PathIndex);
			}
		}
	},
	{
		FStructProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (const auto PropCasted = CastField<FStructProperty>(Prop))
			{
				if (PathIndex > Paths.Num())
					throw std::runtime_error("Property path index out of range");

				if (PathIndex == Paths.Num())
				{
					TArray<FString> StructKVPairs;
					Value.ParseIntoArray(StructKVPairs, TEXT(","), true);
					for (const auto& KVP : StructKVPairs)
					{
						FString Key, Val;
						if (KVP.Split(TEXT("="), &Key, &Val))
						{
							Key = Key.TrimStartAndEnd();
							Val = Val.TrimStartAndEnd();
							
							TArray SinglePath = { Key };
							try
							{
								SetPropertyByPath(PropCasted, PropCasted->ContainerPtrToValuePtr<void>(Obj), SinglePath, Val, 0);
							} catch (const std::runtime_error& e)
							{
								UE_LOG(LogTemp, Warning, TEXT("Failed to set struct property %s: %s"), *Key, *FString(e.what()));
							}
						}
					}
					return;
				}
				
				void* StructPtr = PropCasted->ContainerPtrToValuePtr<void>(Obj);
				if (!StructPtr)
					return;
				SetPropertyByPath(PropCasted, StructPtr, Paths, Value, PathIndex);
			}
		}
	}, {
		FArrayProperty::StaticClass(),
		[](FProperty* Prop, void* Obj, const FString& Value, const TArray<FString>& Paths, int32 PathIndex)
		{
			if (PathIndex >= Paths.Num())
				throw std::runtime_error("Property path index out of range");

			if (const auto PropCasted = CastField<FArrayProperty>(Prop))
			{
				void* ArrayPtr = PropCasted->ContainerPtrToValuePtr<void>(Obj);
				if (!ArrayPtr)
					return;
				SetPropertyByPath(PropCasted, ArrayPtr, Paths, Value, PathIndex);
			}
		}
	},
};