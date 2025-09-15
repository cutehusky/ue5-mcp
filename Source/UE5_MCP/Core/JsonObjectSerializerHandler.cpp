#include "ObjUtils.h"


TMap<FFieldClass*, FJsonSerializerFunc> ObjUtils::JsonSerializers = {
	{
		FByteProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FByteProperty>(Prop))
			{
				const uint8 Value = PropCasted->GetPropertyValue_InContainer(Obj);
				if (PropCasted->Enum)
				{
					Writer->WriteValue(Name, PropCasted->Enum->GetNameByValue(Value).ToString());
				}
				else
				{
					Writer->WriteValue(Name, Value);
				}
			}
		}
	},
	{
		FInt16Property::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FInt16Property>(Prop))
			{
				const int16 Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FIntProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FIntProperty>(Prop))
			{
				const int32 Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FInt64Property::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FInt64Property>(Prop))
			{
				const int64 Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FFloatProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FFloatProperty>(Prop))
			{
				const float Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FDoubleProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FDoubleProperty>(Prop))
			{
				const double Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FBoolProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FBoolProperty>(Prop))
			{
				const bool Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FStrProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FStrProperty>(Prop))
			{
				const FString Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value);
			}
		}
	},
	{
		FNameProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FNameProperty>(Prop))
			{
				const FName Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value.ToString());
			}
		}
	},
	{
		FTextProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FTextProperty>(Prop))
			{
				const FText Value = PropCasted->GetPropertyValue_InContainer(Obj);
				Writer->WriteValue(Name, Value.ToString());
			}
		}
	},
	{
		FObjectProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const auto PropCasted = CastField<FObjectProperty>(Prop))
			{
				if (UObject* Value = PropCasted->GetObjectPropertyValue_InContainer(Obj))
				{
					if (!IsInDetailUObjectWhitelist(Value->GetClass()))
					{
						FString AssetPath = Value->GetPathName();
						Writer->WriteValue(Prop->GetName(), AssetPath);
					} else {
						Writer->WriteObjectStart(Name);
						SerializeProperty(Value, Writer);
						Writer->WriteObjectEnd();
					}
				} else {
					Writer->WriteNull(Name);
				}
			}
		}
	},
	{
		FArrayProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const FArrayProperty* ArrayProp = CastField<FArrayProperty>(Prop))
			{
				Writer->WriteArrayStart(Name);
				if (const void* ArrayPtr = ArrayProp->ContainerPtrToValuePtr<void>(Obj))
				{
					SerializeProperty(ArrayProp, ArrayPtr, Writer);
				}
				Writer->WriteArrayEnd();
			}
		}
	},
	{
		FSetProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const FSetProperty* SetProp = CastField<FSetProperty>(Prop))
			{
				Writer->WriteArrayStart(Name);
				if (const void* SetPtr = SetProp->ContainerPtrToValuePtr<void>(Obj))
				{
					SerializeProperty(SetProp, SetPtr, Writer);
				}
				Writer->WriteArrayEnd();
			}
		}
	},
	{
		FStructProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			if (const FStructProperty* StructProp = CastField<FStructProperty>(Prop))
			{
				if (const void* StructPtr = StructProp->ContainerPtrToValuePtr<void>(Obj))
				{
					Writer->WriteObjectStart(Name);
					SerializeProperty(StructProp, StructPtr, Writer);
					Writer->WriteObjectEnd();
				} else {
					Writer->WriteNull(Name);
				}
			}
		}
	},
	{
		FEnumProperty::StaticClass(),
		[](FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)
		{
			const FEnumProperty* EnumProp = CastField<FEnumProperty>(Prop);
			if (!EnumProp)
				return;
			
			const int64 Value = EnumProp->GetUnderlyingProperty()->GetSignedIntPropertyValue_InContainer(Obj);
			
			if (const UEnum* Enum = EnumProp->GetEnum())
			{
				const FString EnumName = Enum->GetNameByValue(Value).ToString();
				Writer->WriteValue(Name, EnumName);
			}
			else
			{
				Writer->WriteValue(Name, Value);
			}
		}
	}
};