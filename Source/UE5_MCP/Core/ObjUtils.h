#pragma once

using FJsonSerializerFunc = TFunction<void(FProperty* Prop, const void* Obj, TSharedRef<TJsonWriter<>> Writer, const FString& Name)>;
using FJsonArraySerializerFunc = TFunction<void(FProperty* InnerProp, const void* ElementPtr, TSharedRef<TJsonWriter<>> Writer)>;
using FObjPropertySetterFunc = TFunction<void(FProperty* Prop, void* Obj, const FString& Value, const TArray<FString> &Paths, int32 PathIndex)>;

class ObjUtils
{
	// Whitelist of UObject classes that are allowed to be serialized in json
	// Most UObject classes are not safe to be serialized due to potential circular references and large data
	// Use Asset Path instead for non-whitelisted classes
	static TArray<UClass*> DetailUObjectClassWhitelist;
	static bool IsInDetailUObjectWhitelist(UClass* Class);

	static TMap<FFieldClass*, FJsonSerializerFunc> JsonSerializers;
	static TMap<FFieldClass*, FJsonArraySerializerFunc> JsonArraySerializers;
	static TMap<FFieldClass*, FObjPropertySetterFunc> ObjPropertySetters;
	
	static void SerializeProperty(UObject* obj, TSharedRef<TJsonWriter<>> Writer);
	static void SerializeProperty(const FArrayProperty* ArrayProp, const void* ArrayPtr,
	TSharedRef<TJsonWriter<>> Writer);
	static void SerializeProperty(const FSetProperty* SetProp, const void* SetPtr, TSharedRef<TJsonWriter<>> Writer);
	static void SerializeProperty(const FStructProperty* StructProp, const void* StructPtr,
	TSharedRef<TJsonWriter<>> Writer);
	
	static void SetPropertyByPath(
		UObject* Obj,
		const TArray<FString>& PathParts,
		FString Value, int32 Index = 0);
	
	static void SetPropertyByPath(
		FStructProperty* StructProp, void* StructPtr,
		const TArray<FString>& PathParts,
		FString Value, int32 Index = 0);

	static void SetPropertyByPath(
		FArrayProperty* ArrayProp, void* ArrayPtr,
		const TArray<FString>& PathParts,
		FString Value, int32 Index = 0);
public:
	static FString SerializeObjectToJson(UObject* obj);
	static void SetPropertyValueFromString(UObject* obj, const FString& PropertyPath, const FString& PropertyValue);
};



