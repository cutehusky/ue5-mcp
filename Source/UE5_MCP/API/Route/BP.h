#pragma once
#include "HttpServerRequest.h"


bool CreateBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);;

bool GetBPFunctionHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool GetBPVariablesHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool GetGraphHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool CompileBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddVariableToBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool DeleteVariableFromBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool RenameVariableInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool SetVariableDefaultValueInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool AddComponentToBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool GetComponentsOfBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool RemoveComponentFromBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool RenameComponentInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool ReattachComponentInBPHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool GetComponentPropertiesHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);

bool SetComponentPropertyHandler(const FHttpServerRequest& Req, const FHttpResultCallback& OnComplete);