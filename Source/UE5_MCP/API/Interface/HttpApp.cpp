#include "HttpApp.h"

IRouteHandler::IRouteHandler(const FString& InPath, const EHttpServerRequestVerbs& InMethod,
	const FHttpRequestHandler& InRequestHandler): Path(InPath), Method(InMethod), RequestHandler(InRequestHandler)
{
}

FString IRouteHandler::GetPath() const
{
	return Path;
}

EHttpServerRequestVerbs IRouteHandler::GetMethod() const
{
	return Method;
}

FHttpRequestHandler IRouteHandler::GetRequestHandler() const
{
	return RequestHandler;
}

HttpApp::HttpApp()
{
}

void HttpApp::Bind(const TSharedPtr<IHttpRouter>& Router)
{
	for (const auto& HandlerPtr : RouteHandlers)
	{
		IRouteHandler* RawPtr = HandlerPtr.Get();
		const auto Res = Router->BindRoute(
			FHttpPath(RawPtr->GetPath()),
			RawPtr->GetMethod(),
			RawPtr->GetRequestHandler()
		);
		if (!Res.IsValid())
		{
			UE_LOG(LogTemp, Error, TEXT("Failed to bind route %s %s"), *RawPtr->GetPath(), *VerbToString(RawPtr->GetMethod()));
		}
		BoundRouters.FindOrAdd(Router).Add(Res);
	}
}

void HttpApp::Unbind(const TSharedPtr<IHttpRouter>& Router)
{
	const auto* Handles = BoundRouters.Find(Router);
	if (Handles)
	{
		for (const auto& Handle : *Handles)
		{
			Router->UnbindRoute(Handle);
		}
		BoundRouters.Remove(Router);
	}
}

HttpApp::~HttpApp()
{
	for (const auto& Pair : BoundRouters)
	{
		const auto& Router = Pair.Key;
		const auto& Handles = Pair.Value;
		for (const auto& Handle : Handles)
		{
			Router->UnbindRoute(Handle);
		}
	}
}
