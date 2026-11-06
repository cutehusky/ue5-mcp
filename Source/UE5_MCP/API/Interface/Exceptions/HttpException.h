#pragma once
#include <stdexcept>

#include "HttpServerConstants.h"

struct FHttpException : std::runtime_error
{
	FHttpException(
		EHttpServerResponseCodes InErrorCode,
		const FString& InErrorType,
		const FString& InErrorMessage,
		const FString& InErrorDetails = FString()
	) : std::runtime_error(TCHAR_TO_UTF8(*InErrorMessage)),
	    ErrorCode(InErrorCode),
	    ErrorType(InErrorType),
	    ErrorMessage(InErrorMessage),
	    ErrorDetails(InErrorDetails)
	{
	}
	
	EHttpServerResponseCodes ErrorCode;
	FString ErrorType;
	FString ErrorMessage;
	FString ErrorDetails;
};

struct FValidationException: FHttpException
{
	FValidationException(
		const FString& InErrorMessage,
		const FString& InErrorDetails = FString())
		: FHttpException(EHttpServerResponseCodes::BadRequest, TEXT("Validation error"), InErrorMessage, InErrorDetails)
	{
	}
};