#pragma once
#include "HttpResultCallback.h"
#include "HttpServerRequest.h"


bool CreateFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);;

bool EditFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);;

bool DeleteFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);;
