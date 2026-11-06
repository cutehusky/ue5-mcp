#include "Utils.h"

#include "HttpServerRequest.h"

FString VerbToString(const EHttpServerRequestVerbs Verb)
{
	switch (Verb)
	{
	case EHttpServerRequestVerbs::VERB_GET:     return TEXT("GET");
	case EHttpServerRequestVerbs::VERB_POST:    return TEXT("POST");
	case EHttpServerRequestVerbs::VERB_PUT:     return TEXT("PUT");
	case EHttpServerRequestVerbs::VERB_DELETE:  return TEXT("DELETE");
	case EHttpServerRequestVerbs::VERB_PATCH:   return TEXT("PATCH");
	case EHttpServerRequestVerbs::VERB_OPTIONS: return TEXT("OPTIONS");
	default: return TEXT("UNKNOWN");
	}
}

FString ToJsonString(const TArray<FString>& Array)
{
	FString OutputString;
		
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);

	Writer->WriteArrayStart();
	for (const FString& Item : Array)
	{
		Writer->WriteValue(Item);
	}
	Writer->WriteArrayEnd();
	Writer->Close();
		
	return OutputString;
}
