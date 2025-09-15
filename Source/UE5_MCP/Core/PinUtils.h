#pragma once
#include "K2Node_FunctionEntry.h"
#include "K2Node_FunctionResult.h"

// Utility functions for manipulating Blueprint pins
class PinUtils
{
public:
	
	static bool ResolvePinTypeByName(const FString& TypeStr, FEdGraphPinType& OutPinType);

	static void SetupFunctionPins(UK2Node_FunctionTerminator* Node, const FString& Signature, bool bIsInput);

	static void CleanFunctionPins(UK2Node_FunctionEntry* EntryNode, UK2Node_FunctionResult* ReturnNode);

	static bool SplitTypeVar(const FString& Signature, FString& OutType, FString& OutVar);
};
