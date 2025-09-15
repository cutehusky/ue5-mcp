#include "ObjUtils.h"

TMap<FFieldClass*, FJsonArraySerializerFunc> ObjUtils::JsonArraySerializers {
	{
		FByteProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FByteProperty>(InnerProp))
			{
				const uint8 Value = Prop->GetPropertyValue(ElementPtr);
				if (Prop->Enum)
				{
					Writer->WriteValue(Prop->Enum->GetNameByValue(Value).ToString());
				}
				else
				{
					Writer->WriteValue(Value);
				}
			}
		}
	},
	{
		FInt16Property::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FInt16Property>(InnerProp))
			{
				const int16 Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FIntProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FIntProperty>(InnerProp))
			{
				const int32 Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FInt64Property::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FInt64Property>(InnerProp))
			{
				const int64 Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FFloatProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FFloatProperty>(InnerProp))
			{
				const float Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FDoubleProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FDoubleProperty>(InnerProp))
			{
				const double Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FBoolProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FBoolProperty>(InnerProp))
			{
				const bool Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FStrProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FStrProperty>(InnerProp))
			{
				const FString Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value);
			}
		}
	},
	{
		FNameProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FNameProperty>(InnerProp))
			{
				const FName Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value.ToString());
			} 
		}
	},
	{
		FTextProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FTextProperty>(InnerProp))
			{
				const FText Value = Prop->GetPropertyValue(ElementPtr);
				Writer->WriteValue(Value.ToString());
			}
		}
	},
	{
		FObjectProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (auto Prop = CastField<FObjectProperty>(InnerProp))
			{
				if (UObject* Value = Prop->GetObjectPropertyValue(ElementPtr))
				{
					if (!IsInDetailUObjectWhitelist(Value->GetClass()))
					{
						FString AssetPath = Value->GetPathName();
						Writer->WriteValue(Prop->GetName(), AssetPath);
					} else {
						Writer->WriteObjectStart();
						SerializeProperty(Value, Writer);
						Writer->WriteObjectEnd();
					}
				} else {
					Writer->WriteNull();
				}
			}
		}
	},
	{
		FStructProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const FStructProperty* StructProp = CastField<FStructProperty>(InnerProp))
			{
				if (const void* StructPtr = StructProp->ContainerPtrToValuePtr<void>(ElementPtr))
				{
					Writer->WriteObjectStart();
					SerializeProperty(StructProp, StructPtr, Writer);
					Writer->WriteObjectEnd();
				} else {
					Writer->WriteNull();
				}
			}
		}
	},
	{
		FArrayProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const FArrayProperty* ArrayProp = CastField<FArrayProperty>(InnerProp))
			{
				Writer->WriteArrayStart();
				if (const void* ArrayPtr = ArrayProp->ContainerPtrToValuePtr<void>(ElementPtr))
				{
					SerializeProperty(ArrayProp, ArrayPtr, Writer);
				}
				Writer->WriteArrayEnd();
			}
		}
	},
	{
		FSetProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const FSetProperty* SetProp = CastField<FSetProperty>(InnerProp))
			{
				Writer->WriteArrayStart();
				if (const void* SetPtr = SetProp->ContainerPtrToValuePtr<void>(ElementPtr))
				{
					SerializeProperty(SetProp, SetPtr, Writer);
				} 
				Writer->WriteArrayEnd();
			}
		}
	},
	{
		FEnumProperty::StaticClass(),
		[](FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)
		{
			if (const auto Prop = CastField<FEnumProperty>(InnerProp))
			{
				const int64 Value = Prop->GetUnderlyingProperty()->GetSignedIntPropertyValue(ElementPtr);
				if (Prop->GetEnum())
				{
					Writer->WriteValue(Prop->GetEnum()->GetNameByValue(Value).ToString());
				}
				else
				{
					Writer->WriteValue(Value);
				}
			}
		}
	}
};