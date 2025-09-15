#include "Utils.h"

FString Utils::ToJsonString(const TArray<FString> array)
{
	FString OutputString;
		
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);

	Writer->WriteArrayStart();
	for (const FString& Item : array)
	{
		Writer->WriteValue(Item);
	}
	Writer->WriteArrayEnd();
	Writer->Close();
		
	return OutputString;
}
