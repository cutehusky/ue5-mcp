#pragma once
#include "CoreMinimal.h"
#include "JsonResponse.h"
#include "ErrorResponse.generated.h"

USTRUCT()
struct FErrorResponse
{
	GENERATED_BODY()
	
	UPROPERTY()
	FString ErrorType;
	UPROPERTY()
	FString ErrorMessage;
	UPROPERTY()
	FString ErrorDetails;
	
	UPROPERTY()
	int32 ErrorCode = 500;
};

struct FJsonErrorResponse : FJsonResponse<FErrorResponse>
{
	FJsonErrorResponse(
		const FString& ErrorType,
		const FString& ErrorMessage,
		const FString& ErrorDetails = FString(),
		const EHttpServerResponseCodes ErrorCode = EHttpServerResponseCodes::ServerError,
		TMap<FString, TArray<FString>> InHeaders = TMap<FString, TArray<FString>>(),
		const HttpVersion::EHttpServerHttpVersion InHttpVersion = HttpVersion::EHttpServerHttpVersion::HTTP_VERSION_1_1
	): FJsonResponse(
		FErrorResponse {
			.ErrorType = ErrorType,
			.ErrorMessage = ErrorMessage,
			.ErrorDetails = ErrorDetails,
		},
		ErrorCode,
		MoveTemp(InHeaders),
		InHttpVersion)
	{}
};