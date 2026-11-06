#pragma once
#include "HttpResultCallback.h"
#include "HttpServerRequest.h"
#include "HttpServerResponse.h"

#include <stdexcept>

#include "IHttpRouter.h"
#include "HttpRequestHandler.h"
#include "Utils.h"
#include "DTO/HttpContext.h"
#include "Templates/UnrealTemplate.h"

struct FHttpServerRequest;

template<typename TRequest, typename TResponse>
using FHandlerFunc = TFunction<TUniquePtr<FHttpServerResponse>(const FHttpContext<TRequest, TResponse>&)>;

template <typename T>
struct THandlerTraits;

template <typename TRet, typename TClass, typename TArg>
struct THandlerTraits<TRet(TClass::*)(TArg) const> {
	using TContextType = typename TDecay<TArg>::Type;
	using TRequest = typename TContextType::TRequestType;
	using TResponse = typename TContextType::TResponseType;
};

class IRouteHandler
{
	FString Path;
	EHttpServerRequestVerbs Method ;
	FHttpRequestHandler RequestHandler;
	
	virtual bool HandleRequest(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete) const = 0;
	
public:
	IRouteHandler(
		const FString& InPath,
		const EHttpServerRequestVerbs& InMethod,
		const FHttpRequestHandler& InRequestHandler
	);

	virtual ~IRouteHandler() = default;

	FString GetPath() const;

	EHttpServerRequestVerbs GetMethod() const;

	FHttpRequestHandler GetRequestHandler() const;
};

template<typename TRequest, typename TResponse>
class TRouterHandlerImpl: public IRouteHandler
{
public:
	FHandlerFunc<TRequest, TResponse> OnRequestFunc;
	
	TRouterHandlerImpl(
		FHandlerFunc<TRequest, TResponse> InOnRequestFunc,
		const FString& InPath,
		const EHttpServerRequestVerbs& InMethod)
	: IRouteHandler(InPath, InMethod, FHttpRequestHandler::CreateLambda([this](const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete) -> bool
	{
		return this->HandleRequest(Req, OnComplete);
	})), OnRequestFunc(InOnRequestFunc)
	{
	}
	
private:
	virtual bool HandleRequest(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete) const override
	{
		// The engine router falls back to the longest bound prefix, so an unregistered sub-path (or a wrong verb on a
		// registered one) would otherwise run a parent route such as a create handler. Only exact matches leave "/".
		if (Req.RelativePath.GetPath() != TEXT("/"))
		{
			return false;
		}
		try
		{
			UE_LOG(LogTemp, Log, TEXT("Handling request for %s %s"), *VerbToString(GetMethod()), *GetPath());
			FHttpContext<TRequest, TResponse> Context(Req);
			TUniquePtr<FHttpServerResponse> Res = OnRequestFunc(Context);
			OnComplete(MoveTemp(Res));
			return true;
		}
		catch (const FValidationException& e)
		{
			OnComplete(FHttpContext<TRequest, TResponse>::ErrorResponse(
					FString::Printf(TEXT("Validation error: %s"), *e.ErrorMessage),
					TEXT("Validation error"),
					"",
					EHttpServerResponseCodes::BadRequest)
				);
			UE_LOG(LogTemp, Warning, TEXT("Validation error: %s"), *e.ErrorMessage);
			return true;
		} catch (const FHttpException& e)
		{
			OnComplete(FHttpContext<TRequest, TResponse>::ErrorResponse(
					e.ErrorType,
					e.ErrorMessage,
					e.ErrorDetails,
					e.ErrorCode)
				);
			UE_LOG(LogTemp, Error, TEXT("HTTP error: %s - %s"), *e.ErrorType, *e.ErrorMessage);
			return true;
		}
		catch (std::runtime_error& e)
		{
			OnComplete(FHttpContext<TRequest, TResponse>::ErrorResponse(
					TEXT("Runtime error"),
					FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())),
					"",
					EHttpServerResponseCodes::ServerError)
				);
			UE_LOG(LogTemp, Error, TEXT("Runtime error: %s"), UTF8_TO_TCHAR(e.what()));
			return true;
		} catch (std::exception& e)
		{
			OnComplete(FHttpContext<TRequest, TResponse>::ErrorResponse(
					TEXT("Unhandled exception"),
					FString::Printf(TEXT("Error: %s"), UTF8_TO_TCHAR(e.what())),
					"",
					EHttpServerResponseCodes::ServerError)
				);
			UE_LOG(LogTemp, Error, TEXT("Unhandled exception: %s"), UTF8_TO_TCHAR(e.what()));
			return true;
		}
		catch (...)
		{
			OnComplete(FHttpContext<TRequest, TResponse>::ErrorResponse(
					TEXT("Unknown error"),
					TEXT("An unknown error occurred"),
					"",
					EHttpServerResponseCodes::ServerError)
				);
			UE_LOG(LogTemp, Error, TEXT("Unknown error occurred while handling request"));
			return true;
		}
	}
};

class TRawRouterHandlerImpl final : public IRouteHandler
{
public:
	TRawRouterHandlerImpl(const FHttpRequestHandler& InHandler, const FString& InPath, const EHttpServerRequestVerbs& InMethod)
		: IRouteHandler(InPath, InMethod, InHandler)
	{
	}

private:
	virtual bool HandleRequest(const FHttpServerRequest&, const FHttpResultCallback&) const override
	{
		return false;
	}
};

class HttpApp
{
public:
	TArray<TUniquePtr<IRouteHandler>> RouteHandlers;
	TMap<TSharedPtr<IHttpRouter>, TArray<FHttpRouteHandle>> BoundRouters;

	// template<typename TRequest, typename TResponse>
	// void Post(const FString& Path, FHandlerFunc<TRequest, TResponse> Handler)
	// {
	// 	RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
	// 		Handler, Path, EHttpServerRequestVerbs::VERB_POST));
	// }

	// template<typename TRequest, typename TResponse>
	// void Get(const FString& Path, FHandlerFunc<TRequest, TResponse> Handler)
	// {
	// 	RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
	// 		Handler, Path, EHttpServerRequestVerbs::VERB_GET));
	// }
	//
	// template<typename TRequest, typename TResponse>
	// void Put(const FString& Path, FHandlerFunc<TRequest, TResponse> Handler)
	// {
	// 	RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
	// 		Handler, Path, EHttpServerRequestVerbs::VERB_PUT));
	// }
	//
	// template<typename TRequest, typename TResponse>
	// void Delete(const FString& Path, FHandlerFunc<TRequest, TResponse> Handler)
	// {
	// 	RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
	// 		Handler, Path, EHttpServerRequestVerbs::VERB_DELETE));
	// }
	//
	// template<typename TRequest, typename TResponse>
	// void Patch(const FString& Path, FHandlerFunc<TRequest, TResponse> Handler)
	// {
	// 	RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
	// 		Handler, Path, EHttpServerRequestVerbs::VERB_PATCH));
	// }
	//
	// template<typename TRequest, typename TResponse>
	// void Options(const FString& Path, FHandlerFunc<TRequest, TResponse> Handler)
	// {
	// 	RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
	// 		Handler, Path, EHttpServerRequestVerbs::VERB_OPTIONS));
	// }

	template<typename TFunc>
	void Get(const FString& Path, TFunc&& Handler)
	{
		Request(EHttpServerRequestVerbs::VERB_GET, Path, Forward<TFunc>(Handler));
	}

	template<typename TFunc>
	void Post(const FString& Path, TFunc&& Handler)
	{
		Request(EHttpServerRequestVerbs::VERB_POST, Path, Forward<TFunc>(Handler));
	}

	template<typename TFunc>
	void Put(const FString& Path, TFunc&& Handler)
	{
		Request(EHttpServerRequestVerbs::VERB_PUT, Path, Forward<TFunc>(Handler));
	}

	template<typename TFunc>
	void Delete(const FString& Path, TFunc&& Handler)
	{
		Request(EHttpServerRequestVerbs::VERB_DELETE, Path, Forward<TFunc>(Handler));
	}

	template<typename TFunc>
	void Patch(const FString& Path, TFunc&& Handler)
	{
		Request(EHttpServerRequestVerbs::VERB_PATCH, Path, Forward<TFunc>(Handler));
	}

	template<typename TFunc>
	void Options(const FString& Path, TFunc&& Handler)
	{
		Request(EHttpServerRequestVerbs::VERB_OPTIONS, Path, Forward<TFunc>(Handler));
	}

	void Raw(const EHttpServerRequestVerbs Method, const FString& Path, const FHttpRequestHandler& Handler)
	{
		RouteHandlers.Add(MakeUnique<TRawRouterHandlerImpl>(Handler, Path, Method));
	}

	HttpApp();

	void Bind(const TSharedPtr<IHttpRouter> &Router);

	void Unbind(const TSharedPtr<IHttpRouter> &Router);

	virtual ~HttpApp();
	
private:
	template<typename TFunc>
	void Request(
		EHttpServerRequestVerbs Method, 
		const FString& Path,
		TFunc&& Handler)
	{
		using FMethodPtr = decltype(&TDecay<TFunc>::Type::operator());
    
		using TTraits = THandlerTraits<FMethodPtr>;
		using TRequest = typename TTraits::TRequest;
		using TResponse = typename TTraits::TResponse;
		
		RouteHandlers.Add(MakeUnique<TRouterHandlerImpl<TRequest, TResponse>>(
			FHandlerFunc<TRequest, TResponse>(Forward<TFunc>(Handler)), 
			Path, 
			Method
		));
	}
};


