#pragma once
#include "HttpServerRequest.h"


bool AddEventToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddVariableToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddFunctionCallToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);;

bool ConnectPinsHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool BreakPinConnectionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool SetPinDefaultValueHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool GetSupportedNodesHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddGenericNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddMakeStructNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddBreakStructNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

// bool AddSwitchEnumNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddDynamicCastNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddClassCastNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddEnumCastNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddMathNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddCommentNodeToGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);