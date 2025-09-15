#pragma once

class IHttpRouter;

class Router
{
public:
	static void Bind(TSharedPtr<IHttpRouter> Router);
};
